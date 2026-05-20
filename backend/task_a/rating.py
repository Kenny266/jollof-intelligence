"""
LLM-guided rating predictor for Task A.
Predicts the star rating a user would assign to an unseen item
before conditioning the review text on that rating.
"""
import logging
import re
from typing import Any

from shared.llm.client import generate

logger = logging.getLogger(__name__)

RATING_PROMPT = """
You are predicting what star rating a specific user would give to a product.

USER STATS:
- Average rating they give: {avg_rating} / 5
- Rating standard deviation: {rating_std}
- Preferred categories: {top_categories}
- Sentiment tendency: {sentiment_tendency}

PRODUCT:
- Title: {item_title}
- Author: {author}
- Categories: {categories}
- Price: ${price}

Based on how well this product matches the user's typical preferences, predict their rating.
Think step by step:
1. Does this product fall in their preferred categories?
2. Is the price point typical for items they rate well?
3. Given their average ({avg_rating}) and tendency ({sentiment_tendency}), where would this land?

Respond with a single JSON object: {{"rating": <integer 1 to 5>}}
No other text.
"""


async def predict_rating(persona: dict[str, Any], product: dict[str, Any]) -> int:
    """
    Use the LLM to predict a star rating (1–5) conditioned on persona + product.

    Falls back to a heuristic based on avg_rating if LLM output cannot be parsed.
    """
    prompt = RATING_PROMPT.format(
        avg_rating=persona.get("avg_rating", 3.5),
        rating_std=persona.get("rating_std", 1.0),
        top_categories=", ".join(persona.get("top_categories", [])) or "various",
        sentiment_tendency=persona.get("sentiment_tendency", "balanced"),
        item_title=product.get("item_title") or product.get("name", "Unknown"),
        author=product.get("author", ""),
        categories=product.get("categories", "Books"),
        price=product.get("price", "N/A"),
    )

    try:
        raw = await generate(prompt, max_tokens=64, temperature=0.3, think=False)
        # Accept both {"rating": 4} and plain integer responses
        match = re.search(r'"rating"\s*:\s*([1-5])', raw)
        if match:
            return int(match.group(1))
        # Fallback: look for a bare integer 1-5
        bare = re.search(r'\b([1-5])\b', raw)
        if bare:
            return int(bare.group(1))
    except Exception as exc:
        logger.error("Rating prediction failed, using heuristic fallback: %s", exc)

    # Heuristic fallback: sample from N(avg, 0.5*std) clipped to [1,5]
    import random
    avg = persona.get("avg_rating", 3.5)
    std = persona.get("rating_std", 1.0)
    sampled = avg + random.gauss(0, std * 0.5)
    return max(1, min(5, round(sampled)))
