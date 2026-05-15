"""
Task A — User Modeling FastAPI app
POST /generate-review  →  { rating, review }
"""
from fastapi import FastAPI, HTTPException
from task_a.app.models import ReviewRequest, ReviewResponse
from task_a.app.rating import predict_rating
from task_a.app.generator import generate_review
from shared.persona.builder import build_persona

app = FastAPI(
    title="DSN-BCT Task A — User Modeling",
    description="Simulates star ratings and written reviews from user persona and product details.",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok", "task": "A"}


@app.post("/generate-review", response_model=ReviewResponse)
def generate_review_endpoint(req: ReviewRequest):
    try:
        history_dicts = [h.model_dump() for h in req.user_history]
        persona = build_persona(req.user_id, history_dicts)

        product_dict = req.product.model_dump()
        rating = predict_rating(persona, product_dict)
        review_text = generate_review(persona, product_dict, rating)

        return ReviewResponse(
            user_id=req.user_id,
            rating=rating,
            review=review_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
