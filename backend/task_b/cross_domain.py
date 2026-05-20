"""
Cross-domain (cross-subcategory) reasoning for Task B.

Within the Amazon Books dataset, "cross-domain" means reasoning across
subcategories. E.g. if a user loves "Science Fiction", the agent infers
they might also enjoy "Popular Science" or "Science & Math".

This module uses chain-of-thought prompting to expand the search space.
"""
import logging
from typing import Any

from shared.llm.client import generate, extract_json_block
from shared.retrieval.vectorstore import search

logger = logging.getLogger(__name__)

CROSS_DOMAIN_PROMPT = """
A user primarily reads books in these categories: {user_categories}

Their reading style: {tone}, {sentiment_tendency}
Their context/request: "{user_request}"

Using step-by-step reasoning:
1. What related book categories might this user also enjoy?
2. What search queries would find books that bridge their current preferences
   with new but compatible categories?

Return ONLY this JSON (no other text):
{{
  "reasoning": "<2-3 sentence chain-of-thought>",
  "expanded_categories": ["<category1>", "<category2>", "<category3>"],
  "search_queries": ["<query1>", "<query2>"]
}}
"""


async def expand_search_space(
    persona: dict[str, Any],
    user_request: str,
    top_k: int = 15,
) -> list[dict[str, Any]]:
    """
    Perform cross-subcategory retrieval by having the LLM reason about
    related categories and generate expanded search queries.

    Returns a deduplicated list of candidate items spanning original and
    related subcategories.
    """
    user_categories = ", ".join(persona.get("top_categories", [])) or "general books"

    prompt = CROSS_DOMAIN_PROMPT.format(
        user_categories=user_categories,
        tone=persona.get("tone", "concise"),
        sentiment_tendency=persona.get("sentiment_tendency", "balanced"),
        user_request=user_request,
    )

    expanded_queries: list[str] = []
    try:
        raw = await generate(prompt, max_tokens=300, temperature=0.4, think=True)
        data = extract_json_block(raw)
        expanded_queries = data.get("search_queries", [])
        logger.info(
            "Cross-domain expansion: %s -> %s",
            user_categories,
            data.get("expanded_categories", []),
        )
    except Exception as exc:
        logger.warning("Cross-domain expansion failed: %s", exc)
        expanded_queries = [user_request]

    # Collect results from all expanded queries (deduplicate by parent_asin)
    seen_ids: set[str] = set()
    all_candidates: list[dict[str, Any]] = []

    import asyncio
    loop = asyncio.get_event_loop()

    for query in expanded_queries[:3]:
        try:
            results = await loop.run_in_executor(None, lambda q=query: search(q, top_k=top_k // len(expanded_queries or [1])))
            for item in results:
                item_id = item.get("parent_asin") or item.get("id", "")
                if item_id not in seen_ids:
                    seen_ids.add(item_id)
                    all_candidates.append(item)
        except Exception as exc:
            logger.error("Query '%s' failed: %s", query, exc)

    return all_candidates[:top_k]
