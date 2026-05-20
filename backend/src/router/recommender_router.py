from fastapi import APIRouter

from src.controllers.recommender_controller import handle_recommend
from src.models.task_b import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/task-b", tags=["Task B — Recommendation"])


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Get personalized book recommendations",
    description=(
        "Returns personalized book recommendations for a user. "
        "Handles cold-start (no history), warm-start (history provided), "
        "cross-category reasoning, and multi-turn conversational refinement."
    ),
)
async def recommend(req: RecommendRequest) -> RecommendResponse:
    return await handle_recommend(req)
