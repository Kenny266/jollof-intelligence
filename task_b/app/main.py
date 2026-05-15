"""
Task B — Recommendation FastAPI app
POST /recommend  →  { recommendations, follow_up }
"""
from fastapi import FastAPI, HTTPException
from task_b.app.models import RecommendRequest, RecommendResponse, RecommendedItem
from task_b.app.recommender import recommend
from task_b.app.dialogue import generate_follow_up

app = FastAPI(
    title="DSN-BCT Task B — Recommendation Agent",
    description="Delivers personalised recommendations with cold-start, cross-domain, and multi-turn support.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "task": "B"}


@app.post("/recommend", response_model=RecommendResponse)
def recommend_endpoint(req: RecommendRequest):
    try:
        history_dicts = [h.model_dump() for h in req.user_history]

        results = recommend(
            user_id=req.user_id,
            history=history_dicts,
            context=req.context or "",
            top_k=5,
        )

        items = [RecommendedItem(**r) for r in results]
        follow_up = generate_follow_up(req.context or "", results) if results else None

        return RecommendResponse(
            user_id=req.user_id,
            recommendations=items,
            follow_up=follow_up,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
