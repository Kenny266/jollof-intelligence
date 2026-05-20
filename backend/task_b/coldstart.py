"""
Cold-start recommendation strategies for Task B.

Three-tier fallback:
  Tier 1 — Context-based: LLM extracts preference tags from user's description text.
  Tier 2 — Popularity-based: Return highly-rated items matching request keywords.
  Tier 3 — Bare popularity: Return globally top-rated items if nothing else works.
"""
import logging
from typing import Any

from shared.llm.client import generate, extract_json_block
from shared.retrieval.vectorstore import search

logger = logging.getLogger(__name__)

PREFERENCE_EXTRACTION_PROMPT = """
A new user described themselves as follows:
"{user_description}"

Extract their likely book preferences from this description. Think about:
- Genre preferences (e.g. "science fiction", "self-help", "mystery")
- Likely reading level and vocabulary preferences
- Mood or purpose (escapism, learning, entertainment)
- Price sensitivity if mentioned
- Any cultural or geographical preferences

Return ONLY this JSON (no other text):
{{
  "genres": ["<genre1>", "<genre2>"],
  "mood": "<reading mood>",
  "search_query": "<optimized semantic search string for finding matching books>"
}}
"""


async def extract_cold_start_preferences(user_description: str) -> dict[str, Any]:
    """
    Tier 1: LLM extracts structured preferences from a user's text description.

    Args:
        user_description: Free-text description, e.g. "22-year-old Nigerian student who loves sci-fi"

    Returns:
        Dict with genres, mood, and search_query keys.
    """
    if not user_description or not user_description.strip():
        return {"genres": [], "mood": "general", "search_query": "popular highly rated books"}

    prompt = PREFERENCE_EXTRACTION_PROMPT.format(user_description=user_description)
    try:
        raw = await generate(prompt, max_tokens=200, temperature=0.3, think=True)
        prefs = extract_json_block(raw)
        return prefs
    except Exception as exc:
        logger.warning("Preference extraction failed: %s", exc)
        return {"genres": [], "mood": "general", "search_query": user_description}


async def cold_start_candidates(
    context: str,
    top_k: int = 20,
) -> list[dict[str, Any]]:
    """
    Cold-start candidate retrieval with three-tier fallback.

    Tier 1: LLM-extracted preference search query
    Tier 2: Direct semantic search on the context string
    Tier 3: Generic "popular highly rated books" fallback
    """
    # Tier 1: LLM-guided preference extraction
    if context and len(context.strip()) > 10:
        prefs = await extract_cold_start_preferences(context)
        search_query = prefs.get("search_query", context)
        candidates = await _vector_search(search_query, top_k)
        if candidates:
            logger.info("Cold-start Tier 1: %d candidates via LLM preference extraction", len(candidates))
            return candidates

    # Tier 2: Direct context-based search
    if context and context.strip():
        candidates = await _vector_search(context, top_k)
        if candidates:
            logger.info("Cold-start Tier 2: %d candidates via direct context search", len(candidates))
            return candidates

    # Tier 3: Popularity fallback
    logger.info("Cold-start Tier 3: falling back to popularity-based search")
    return await _vector_search("popular highly rated books bestseller acclaimed", top_k)


async def _vector_search(query: str, top_k: int) -> list[dict[str, Any]]:
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        results = await loop.run_in_executor(None, lambda: search(query, top_k=top_k))
        return results
    except Exception as exc:
        logger.error("Vector search failed: %s", exc)
        return []
