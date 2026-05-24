"""
Task B orchestrator — Recommendation Agent.

Pipeline:
1. Build persona from history (warm) or detect cold-start (no history).
2. Warm path:  compute user vector by mean-pooling their review embeddings from
               the `user_reviews` ChromaDB collection, then query the `items`
               collection via cosine similarity.
   Cold path:  embed the free-text `context` description on-the-fly and query
               the `items` collection directly — no LLM heuristic needed.
3. LLM reranks candidates + generates conversational Nigerian English explanations.
4. Post-rerank grounding: filter out any item_id not in the candidate set and
   hydrate all metadata fields from the retrieval results (not from LLM output).
5. Generate follow-up question for multi-turn refinement.
"""
import asyncio
import logging
from pathlib import Path
from typing import Any

from shared.llm.client import generate, extract_json_block
from shared.llm.nigerian_context import get_system_prompt
from shared.persona.builder import build_persona
from shared.retrieval.rag import build_recommendation_context
from shared.retrieval.vectorstore import (
    get_user_vector,
    embed_text,
    search_by_vector,
    get_collection,
)
from src.config import get_settings
from task_b.dialogue import generate_follow_up, refine_query_from_conversation

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "v1" / "recommend_prompt.txt"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


class RecommendationAgent:
    """
    Orchestrates the full Task B pipeline.
    Handles warm/cold-start routing, grounded vector-similarity retrieval,
    LLM-constrained reranking, and multi-turn dialogue.
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

        settings = get_settings()
        items_collection = settings.chroma_items_collection
        user_reviews_collection = settings.chroma_user_reviews_collection

        # Route: warm vs cold — both ultimately query the `items` collection
        if persona.get("cold_start"):
            candidates = await self._cold_retrieval(
                context=effective_query,
                top_k=top_k * 4,
                items_collection=items_collection,
            )
        else:
            candidates = await self._warm_retrieval(
                user_id=user_id,
                user_request=effective_query,
                top_k=top_k * 4,
                items_collection=items_collection,
                user_reviews_collection=user_reviews_collection,
            )

        if not candidates:
            logger.warning("No candidates retrieved for user %s", user_id)
            return {"user_id": user_id, "recommendations": [], "follow_up": None}

        # Build context string for the prompt (uses up to 20 candidates)
        context_str = build_recommendation_context(persona, effective_query, candidates[:20])

        # Rerank + generate explanations via LLM (constrained to candidate set)
        recommendations = await self._rerank(
            context_str=context_str,
            conversation=conversation,
            user_request=effective_query,
            top_k=top_k,
            candidates=candidates[:20],
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
        user_id: str,
        user_request: str,
        top_k: int,
        items_collection: str,
        user_reviews_collection: str,
    ) -> list[dict[str, Any]]:
        """
        Warm-start retrieval via user preference vector.

        1. Mean-pool the user's review embeddings from the `user_reviews` collection.
        2. Query the `items` collection using that vector (cosine similarity).
        3. Fall back to embedding the request text directly if the user vector is
           unavailable (e.g. reviews not yet indexed in the new collection).
        """
        loop = asyncio.get_event_loop()

        # Compute user preference vector from stored review embeddings
        user_vector = await loop.run_in_executor(
            None,
            lambda: get_user_vector(user_id, user_reviews_collection, limit=50),
        )

        if user_vector is not None:
            logger.info(
                "Warm retrieval: using aggregated user vector for user=%s", user_id
            )
            results = await loop.run_in_executor(
                None,
                lambda: search_by_vector(
                    user_vector,
                    top_k=top_k,
                    collection_name=items_collection,
                ),
            )
            if results:
                return results
            logger.warning(
                "User vector search returned nothing for user=%s; falling back to request text",
                user_id,
            )

        # Fallback: embed the request text directly (e.g. user_reviews not yet indexed)
        logger.info(
            "Warm retrieval fallback: embedding request text for user=%s", user_id
        )
        return await self._vector_search_from_text(
            user_request, top_k, items_collection
        )

    async def _cold_retrieval(
        self,
        context: str,
        top_k: int,
        items_collection: str,
    ) -> list[dict[str, Any]]:
        """
        Cold-start retrieval: embed the context description on-the-fly and query
        the `items` collection.  Falls back to a popularity query when context is
        too short to be meaningful.
        """
        query = context if context and len(context.strip()) > 10 else (
            "popular highly rated books bestseller acclaimed"
        )
        logger.info("Cold-start retrieval: query=%r", query[:80])
        return await self._vector_search_from_text(query, top_k, items_collection)

    @staticmethod
    async def _vector_search_from_text(
        text: str,
        top_k: int,
        collection_name: str,
    ) -> list[dict[str, Any]]:
        """Embed `text` and search `collection_name` by the resulting vector."""
        loop = asyncio.get_event_loop()
        try:
            vector = await loop.run_in_executor(None, lambda: embed_text(text))
            results = await loop.run_in_executor(
                None,
                lambda: search_by_vector(vector, top_k=top_k, collection_name=collection_name),
            )
            return results
        except Exception as exc:
            logger.error("Vector search from text failed: %s", exc)
            return []

    async def _rerank(
        self,
        context_str: str,
        conversation: list[dict[str, str]],
        user_request: str,
        top_k: int,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        LLM reranks candidate items and generates per-item explanations.

        After the LLM responds:
        - Any item_id not present in the candidate set is discarded (grounding).
        - All structured fields (title, author, categories, price) are hydrated
          from the retrieval results — not trusted from LLM output — so metadata
          is always accurate.
        - Falls back to returning candidates ordered by similarity_score on
          parse failure or if no valid items survive grounding.
        """
        from task_b.dialogue import format_conversation
        conv_str = format_conversation(conversation) if conversation else "(No prior conversation)"

        # Build a lookup map for fast grounding and hydration
        candidate_map: dict[str, dict[str, Any]] = {}
        for item in candidates:
            asin = item.get("parent_asin") or item.get("id", "")
            if asin:
                candidate_map[asin] = item

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

            # Ground: keep only items whose item_id is in the candidate set
            grounded: list[dict[str, Any]] = []
            for r in recs:
                if not isinstance(r, dict):
                    continue
                item_id = r.get("item_id", "")
                if item_id not in candidate_map:
                    logger.debug("Dropping hallucinated item_id=%r from rerank output", item_id)
                    continue
                if not r.get("reason"):
                    continue

                # Hydrate metadata from retrieval results
                source = candidate_map[item_id]
                grounded.append({
                    "item_id": item_id,
                    "title": source.get("item_title") or source.get("title") or r.get("title", ""),
                    "author": source.get("author") or r.get("author", ""),
                    "categories": source.get("categories") or r.get("categories", ""),
                    "price": source.get("price") or r.get("price", "N/A"),
                    "score": float(r.get("score", source.get("similarity_score", 0.5))),
                    "reason": str(r.get("reason", "")),
                })

            if grounded:
                logger.info(
                    "Reranking: %d/%d candidates survived grounding", len(grounded), len(recs)
                )
                return grounded[:top_k]

            logger.warning("Reranking: no grounded items survived — using similarity fallback")

        except Exception as exc:
            logger.error("Reranking failed: %s — returning unranked candidates", exc)

        return _fallback_recommendations(candidates, top_k)


def _fallback_recommendations(
    candidates: list[dict[str, Any]],
    top_k: int,
) -> list[dict[str, Any]]:
    """Map retrieval candidates to recommendation dicts when LLM rerank fails."""
    sorted_candidates = sorted(
        candidates,
        key=lambda c: c.get("similarity_score", 0.0),
        reverse=True,
    )
    results: list[dict[str, Any]] = []
    for item in sorted_candidates[:top_k]:
        title = item.get("item_title") or item.get("title") or item.get("name") or "Unknown"
        results.append({
            "item_id": item.get("parent_asin") or item.get("id", ""),
            "title": title,
            "author": item.get("author", ""),
            "categories": item.get("categories") or item.get("category", ""),
            "price": item.get("price", "N/A"),
            "score": float(item.get("similarity_score", 0.5)),
            "reason": f"Based on your request, {title} looks like a strong match from our catalogue.",
        })
    return results
