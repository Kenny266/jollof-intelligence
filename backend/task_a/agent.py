"""
Task A orchestrator — User Modeling Agent.

Pipeline:
1. Build persona from user history.
2. Query ChromaDB for this user's past reviews (RAG context).
3. Predict rating via LLM.
4. Generate review text conditioned on rating + Nigerian persona.
5. Parse and return structured output.
"""
import logging
import re
from pathlib import Path
from typing import Any

from shared.llm.client import generate, extract_json_block
from shared.llm.nigerian_context import get_system_prompt
from shared.persona.builder import build_persona
from shared.retrieval.rag import build_user_context
from task_a.rating import predict_rating

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "v1" / "review_prompt.txt"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


class UserModelingAgent:
    """
    Orchestrates the full Task A pipeline.
    All I/O is async to avoid blocking the FastAPI event loop during LLM calls.
    """

    async def run(
        self,
        user_id: str,
        history: list[dict[str, Any]],
        product: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a simulated review and star rating for an unseen product.

        Args:
            user_id: The user's identifier.
            history: Past review dicts fetched from the relational DB by the controller.
            product: Dict with product details (item_title, author, categories, price, description).

        Returns:
            Dict with keys: rating (int), review (str), persona_summary (dict).
        """
        # Step 1: Build behavioural persona from DB-sourced history
        logger.info("Building persona for user %s", user_id)
        persona = build_persona(user_id, history)
        logger.info("Persona built for user %s (cold_start=%s)", user_id, persona.get("cold_start"))

        # Step 2: RAG retrieval — fetch user's past reviews from ChromaDB
        search_query = (
            f"{product.get('item_title', '')} {product.get('categories', '')} {product.get('author', '')}"
        ).strip()
        retrieved_context, rag_metrics = await _async_rag(persona, search_query, user_id)

        # Step 3: LLM-guided rating prediction
        rating = await predict_rating(persona, product)

        # Step 4: Generate review text
        template = _load_prompt()
        sample_block = "\n".join(
            f'  - "{rev[:200]}"' for rev in persona.get("sample_reviews", [])[:3]
        ) or "  (no past reviews available)"

        prompt = template.format(
            avg_rating=persona["avg_rating"],
            rating_std=persona.get("rating_std", 1.0),
            top_categories=", ".join(persona.get("top_categories", [])) or "various",
            tone=persona.get("tone", "concise"),
            sentiment_tendency=persona.get("sentiment_tendency", "balanced"),
            review_count=persona.get("review_count", 0),
            sample_reviews=sample_block,
            retrieved_context=retrieved_context,
            item_title=product.get("item_title") or product.get("name", "Unknown"),
            author=product.get("author", ""),
            categories=product.get("categories", "Books"),
            price=product.get("price", "N/A"),
            description=str(product.get("description", ""))[:300],
        )

        system_prompt = get_system_prompt()
        raw_output = await generate(prompt, system=system_prompt, max_tokens=600, think=False)

        # Step 5: Parse output
        result = _parse_output(raw_output, rating)

        return {
            "user_id": user_id,
            "rating": result["rating"],
            "review": result["review"],
            "persona_summary": {
                "avg_rating": persona["avg_rating"],
                "top_categories": persona.get("top_categories", []),
                "tone": persona.get("tone"),
                "sentiment_tendency": persona.get("sentiment_tendency"),
                "cold_start": persona.get("cold_start", False),
            },
            "rag_metrics": rag_metrics,
        }


async def _async_rag(
    persona: dict[str, Any], query: str, user_id: str
) -> tuple[str, dict]:
    """Wrap the synchronous RAG call for async usage."""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, build_user_context, persona, query, 5, user_id
    )


def _parse_output(raw: str, fallback_rating: int) -> dict[str, Any]:
    """
    Extract rating and review from LLM output.
    Attempts JSON parse first; falls back to regex extraction.
    """
    try:
        data = extract_json_block(raw)
        rating = int(data.get("rating", fallback_rating))
        review = str(data.get("review", "")).strip()
        if 1 <= rating <= 5 and review:
            return {"rating": rating, "review": review}
    except (ValueError, KeyError) as exc:
        logger.warning("JSON parse failed (%s), falling back to regex", exc)

    # Regex fallback
    rating_match = re.search(r'"rating"\s*:\s*([1-5])', raw)
    parsed_rating = int(rating_match.group(1)) if rating_match else fallback_rating

    review_match = re.search(r'"review"\s*:\s*"(.*?)"(?:\s*[},]|$)', raw, re.DOTALL)
    if review_match:
        review_text = review_match.group(1).replace("\\n", "\n").replace('\\"', '"')
    else:
        # Last resort: use everything after the last colon that looks like text
        lines = [l.strip() for l in raw.splitlines() if len(l.strip()) > 20]
        review_text = lines[-1] if lines else "Review generation failed."

    return {"rating": parsed_rating, "review": review_text}
