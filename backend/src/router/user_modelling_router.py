from fastapi import APIRouter

from src.controllers.user_modelling_controller import handle_generate_review
from src.models.task_a import ReviewRequest, ReviewResponse

router = APIRouter(prefix="/task-a", tags=["Task A — User Modeling"])


@router.post(
    "/generate-review",
    response_model=ReviewResponse,
    summary="Generate a simulated review and star rating",
    description=(
        "Given a user's review history and an unseen product, simulate the review and "
        "star rating this user would write. Outputs authentic Nigerian-inflected text."
    ),
)
async def generate_review(req: ReviewRequest) -> ReviewResponse:
    return await handle_generate_review(req)
