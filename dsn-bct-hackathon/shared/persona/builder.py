"""
Persona builder.
Priority:
  1. DB materialized view (user_personas) — fast, pre-computed
  2. Build from raw history list — used when DB unavailable or for new users
"""
from collections import Counter
from typing import List, Dict, Any, Optional


def build_persona_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch persona from the user_personas materialized view."""
    try:
        from database.scripts.db import get_user_persona, get_user_history
        row = get_user_persona(user_id)
        if not row:
            return None
        history = get_user_history(user_id, limit=5)
        return {
            "user_id": user_id,
            "name": row.get("name") or "",
            "avg_rating": float(row.get("avg_rating") or 3.5),
            "rating_std": float(row.get("rating_std") or 1.0),
            "top_categories": list(row.get("categories") or []),
            "domains": list(row.get("domains") or []),
            "tone": "detailed" if (row.get("avg_review_length") or 0) > 50 else "concise",
            "sentiment_tendency": _sentiment(float(row.get("positivity_rate") or 0.5)),
            "review_count": int(row.get("review_count") or 0),
            "sample_reviews": [r["review_text"] for r in history if r.get("review_text")][:3],
            "cold_start": False,
        }
    except Exception:
        return None


def build_persona(user_id: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build persona from a list of review dicts.
    Each dict should have: item_name, category_name, rating, review_text.
    Falls back to DB lookup if history is empty.
    """
    if not history:
        db_persona = build_persona_from_db(user_id)
        if db_persona:
            return db_persona
        return _cold_start_persona(user_id)

    ratings = [r.get("rating", 3) for r in history]
    categories = [r.get("category_name") or r.get("category", "unknown") for r in history]
    avg_rating = sum(ratings) / len(ratings)
    variance = sum((r - avg_rating) ** 2 for r in ratings) / len(ratings)
    rating_std = variance ** 0.5

    top_categories = [cat for cat, _ in Counter(categories).most_common(3)]

    avg_len = sum(len((r.get("review_text") or "").split()) for r in history) / len(history)
    tone = "detailed" if avg_len > 50 else "concise"

    positivity = sum(1 for r in ratings if r >= 4) / len(ratings)

    return {
        "user_id": user_id,
        "avg_rating": round(avg_rating, 2),
        "rating_std": round(rating_std, 2),
        "top_categories": top_categories,
        "domains": list(set(r.get("domain", "") for r in history if r.get("domain"))),
        "tone": tone,
        "sentiment_tendency": _sentiment(positivity),
        "review_count": len(history),
        "sample_reviews": [r.get("review_text", "") for r in history[:3]],
        "cold_start": False,
    }


def _sentiment(positivity_rate: float) -> str:
    if positivity_rate > 0.6:
        return "positive"
    if positivity_rate < 0.3:
        return "critical"
    return "balanced"


def _cold_start_persona(user_id: str) -> Dict[str, Any]:
    return {
        "user_id": user_id,
        "avg_rating": 3.5,
        "rating_std": 1.0,
        "top_categories": [],
        "domains": [],
        "tone": "concise",
        "sentiment_tendency": "balanced",
        "review_count": 0,
        "sample_reviews": [],
        "cold_start": True,
    }
