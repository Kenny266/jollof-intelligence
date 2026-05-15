"""
Core recommendation logic.
1. Build persona from history
2. Retrieve candidates via RAG
3. Re-rank by contextual relevance using LLM
4. Return top-k with explanations
"""
from shared.persona.builder import build_persona
from shared.retrieval.rag import build_context
from shared.retrieval.vectorstore import search
from shared.llm.client import generate
from shared.llm.nigerian_context import inject
from task_b.app.coldstart import cold_start_recommend
from typing import List, Dict, Any
import json


RERANK_PROMPT = """
You are a recommendation engine. Given a user profile and a list of candidate items,
return the top {top_k} most relevant items for this user in this context.

User profile:
{persona_context}

User's current request: "{user_context}"

Candidate items (JSON):
{candidates}

Return ONLY a JSON array of item objects with keys: item_id, name, category, score (0-1), reason.
No explanation, no preamble. JSON only.
"""


def recommend(
    user_id: str,
    history: List[Dict],
    context: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    persona = build_persona(user_id, history)

    if persona.get("cold_start"):
        candidates = cold_start_recommend(context, top_k=top_k * 2)
    else:
        query = context or " ".join(persona["top_categories"])
        candidates = search(query, top_k=top_k * 2)

    if not candidates:
        return []

    persona_context = build_context(persona, context or "general recommendations")

    prompt = RERANK_PROMPT.format(
        top_k=top_k,
        persona_context=persona_context,
        user_context=context or "general recommendations",
        candidates=json.dumps(candidates[:10], indent=2),
    )
    prompt = inject(prompt)
    raw = generate(prompt, max_new_tokens=600)

    try:
        # Strip any markdown code fences if present
        clean = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        results = json.loads(clean)
        return results[:top_k]
    except Exception:
        # Graceful degradation: return raw candidates with default scores
        return [
            {
                "item_id": str(i),
                "name": c.get("name", "Unknown"),
                "category": c.get("category", ""),
                "score": c.get("similarity_score", 0.5),
                "reason": "Based on your preferences",
            }
            for i, c in enumerate(candidates[:top_k])
        ]
