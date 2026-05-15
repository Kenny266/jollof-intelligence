"""
Cold-start fallback strategy.
Used when a user has no review history.
Strategies:
  1. Popularity-based: return globally top-rated items
  2. Context-based: use the request context string to retrieve items
  3. Cross-domain: if history exists in another domain, transfer preferences
"""
from typing import List, Dict, Any
from shared.retrieval.vectorstore import search


def cold_start_recommend(context: str, top_k: int = 10) -> List[Dict[str, Any]]:
    """
    When no user history: retrieve items purely by context query.
    Falls back to empty list if vector store not yet built.
    """
    if not context:
        context = "popular highly rated items"
    try:
        return search(context, top_k=top_k)
    except RuntimeError:
        return []
