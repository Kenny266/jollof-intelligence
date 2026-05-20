"""
Task B orchestrator — Recommendation Agent.

Pipeline:
1. Validate history: warm path (has history) vs cold-start path.
2. Warm: build persona + generate semantic query from preferences + conversation.
   Cold: LLM extracts preference tags from context description.
3. Semantic search over ChromaDB for candidate items.
4. Cross-domain expansion if user has narrow category history.
5. LLM reranks candidates + generates conversational explanations.
6. Generate follow-up question for multi-turn refinement.
"""
import asyncio
import json
import logging
import re
from pathlib import Path
from typing import Any

from shared.llm.client import generate, extract_json_block
from shared.llm.nigerian_context import get_system_prompt
from shared.persona.builder import build_persona
from shared.retrieval.rag import build_recommendation_context
from shared.retrieval.vectorstore import search
from task_b.coldstart import cold_start_candidates
from task_b.cross_domain import expand_search_space
from task_b.dialogue import generate_follow_up, refine_query_from_conversation

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "v1" / "recommend_prompt.txt"
QUERY_GEN_PROMPT = """
A user has the following preferences:
- Favourite categories: {top_categories}
- Average rating they give: {avg_rating} / 5
- Review style: {tone}, {sentiment_tendency}

Their current request: "{user_request}"

Generate a specific, targeted semantic search query (1-2 sentences) that would
retrieve the most relevant book items from a vector database for this user.
Return ONLY the search query string, nothing else.
"""


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


class RecommendationAgent:
    """
    Orchestrates the full Task B pipeline.
    Handles warm/cold-start routing, cross-domain reasoning, multi-turn dialogue,
    and LLM-based reranking with explanations.
    """

    async def run(
        self,
        user_id: str,
        history: list[dict[str, Any]],
        context: str,
        conversation: list[dict[str, str]],
        top_k: int = 5,
    ) -> dict[str, Any]:
        """
        Generate personalized recommendations.

        Args:
            user_id: User identifier.
            history: Past review dicts fetched from the relational DB by the controller.
            context: Free-text request or user description.
            conversation: List of prior turns [{"role": "user"|"assistant", "content": "..."}].
            top_k: Number of recommendations to return.

        Returns:
            Dict with recommendations list and follow_up question.
        """
        persona = build_persona(user_id, history)
        logger.info(
            "Recommendation run: user=%s cold_start=%s context=%r",
            user_id,
            persona.get("cold_start"),
            context[:80],
        )

        # Refine query if multi-turn conversation exists
        effective_query = context
        if conversation:
            effective_query = await refine_query_from_conversation(conversation, context)
            logger.info("Multi-turn refined query: %r", effective_query)

        # Route: warm vs cold
        if persona.get("cold_start"):
            candidates = await cold_start_candidates(effective_query, top_k=top_k * 4)
        else:
            candidates = await self._warm_retrieval(persona, effective_query, top_k=top_k * 4)

        if not candidates:
            logger.warning("No candidates retrieved for user %s", user_id)
            return {"user_id": user_id, "recommendations": [], "follow_up": None}

        # Build context string for the prompt
        context_str = build_recommendation_context(persona, effective_query, candidates[:20])

        # Rerank + generate explanations via LLM
        recommendations = await self._rerank(
            context_str=context_str,
            conversation=conversation,
            user_request=effective_query,
            top_k=top_k,
        )

        # Generate follow-up question
        follow_up = await generate_follow_up(effective_query, recommendations)

        return {
            "user_id": user_id,
            "recommendations": recommendations,
            "follow_up": follow_up,
            "cold_start": persona.get("cold_start", False),
        }

    async def _warm_retrieval(
        self,
        persona: dict[str, Any],
        user_request: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        Warm-start retrieval:
        1. LLM generates an optimised search query from persona.
        2. Standard semantic search for primary candidates.
        3. Cross-domain expansion for additional diversity.
        """
        # LLM-generated search query
        query_prompt = QUERY_GEN_PROMPT.format(
            top_categories=", ".join(persona.get("top_categories", [])) or "various",
            avg_rating=persona["avg_rating"],
            tone=persona.get("tone", "concise"),
            sentiment_tendency=persona.get("sentiment_tendency", "balanced"),
            user_request=user_request,
        )
        try:
            llm_query = await generate(query_prompt, max_tokens=100, temperature=0.3, think=False)
            llm_query = llm_query.strip().strip('"')
        except Exception as exc:
            logger.warning("Query generation failed: %s — using raw request", exc)
            llm_query = user_request

        loop = asyncio.get_event_loop()
        primary = await loop.run_in_executor(None, lambda: search(llm_query, top_k=top_k // 2))

        # Cross-domain expansion (only when user has established preferences)
        cross = []
        if persona.get("top_categories"):
            cross = await expand_search_space(persona, user_request, top_k=top_k // 2)

        # Deduplicate
        seen: set[str] = set()
        combined: list[dict[str, Any]] = []
        for item in primary + cross:
            iid = item.get("parent_asin") or item.get("id", "")
            if iid not in seen:
                seen.add(iid)
                combined.append(item)

        return combined[:top_k]

    async def _rerank(
        self,
        context_str: str,
        conversation: list[dict[str, str]],
        user_request: str,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """
        LLM reranks candidate items and generates per-item explanations.
        Falls back to returning candidates ordered by similarity_score on parse failure.
        """
        from task_b.dialogue import format_conversation
        conv_str = format_conversation(conversation) if conversation else "(No prior conversation)"

        template = _load_prompt()
        prompt = template.format(
            context=context_str,
            conversation_history=conv_str,
            top_k=top_k,
            user_request=user_request,
        )

        try:
            raw = await generate(
                prompt,
                system=get_system_prompt(),
                max_tokens=1000,
                temperature=0.6,
                think=True,
            )
            data = extract_json_block(raw)
            recs = data.get("recommendations", [])
            # Validate structure
            valid = [
                r for r in recs
                if isinstance(r, dict) and r.get("title") and r.get("reason")
            ]
            return valid[:top_k]
        except Exception as exc:
            logger.error("Reranking failed: %s — returning unranked candidates", exc)
            return []
