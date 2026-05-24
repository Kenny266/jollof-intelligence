"""
Cold-start retrieval for Task B.

Embeds the user's free-text context description on-the-fly and queries the
`items` ChromaDB collection via cosine similarity.  This replaces the former
3-tier LLM heuristic with a single, deterministic vector search that is both
faster and grounded in the real item catalogue.
"""
import asyncio
import logging
from typing import Any

from shared.retrieval.vectorstore import embed_text, search_by_vector
from src.config import get_settings

logger = logging.getLogger(__name__)

_POPULARITY_FALLBACK = "popular highly rated books bestseller acclaimed"


async def cold_start_candidates(
    context: str,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """
    Retrieve candidate items for a cold-start user.

    Embeds `context` (the user's self-description or request) and returns the
    top-K most similar items from the `items` ChromaDB collection.  When the
    context string is too short to be useful, a generic popularity query is
    used as a fallback.

    Args:
        context: Free-text user description or request, e.g.
                 "22-year-old Nigerian student who loves sci-fi".
        top_k: Number of candidate items to return.

    Returns:
        List of item metadata dicts with a `similarity_score` field.
    """
    query = context.strip() if context and len(context.strip()) > 10 else _POPULARITY_FALLBACK
    logger.info("Cold-start retrieval: query=%r (top_k=%d)", query[:80], top_k)

    items_collection = get_settings().chroma_items_collection
    loop = asyncio.get_event_loop()

    try:
        vector = await loop.run_in_executor(None, lambda: embed_text(query))
        results = await loop.run_in_executor(
            None,
            lambda: search_by_vector(vector, top_k=top_k, collection_name=items_collection),
        )
        if results:
            logger.info("Cold-start: %d candidates retrieved", len(results))
            return results
    except Exception as exc:
        logger.error("Cold-start vector search failed: %s", exc)

    # Last resort: popularity fallback if query embedding also failed
    if query != _POPULARITY_FALLBACK:
        logger.info("Cold-start: retrying with popularity fallback query")
        try:
            vector = await loop.run_in_executor(
                None, lambda: embed_text(_POPULARITY_FALLBACK)
            )
            results = await loop.run_in_executor(
                None,
                lambda: search_by_vector(
                    vector, top_k=top_k, collection_name=items_collection
                ),
            )
            return results
        except Exception as exc:
            logger.error("Cold-start popularity fallback failed: %s", exc)

    return []
