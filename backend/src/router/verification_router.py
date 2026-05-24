from fastapi import APIRouter, Query

from src.controllers.verification_controller import (
    handle_get_item,
    handle_get_recommendation,
    handle_get_user_profile,
    handle_list_generated_reviews,
    handle_list_recommendations,
    handle_list_reviews,
    handle_verify_items,
)
from src.models.verification import (
    ItemResponse,
    ItemVerifyRequest,
    ItemVerifyResponse,
    RecommendationListResponse,
    RecommendationLogResponse,
    ReviewListResponse,
    UserProfileResponse,
)

router = APIRouter(tags=["Verification"])


@router.get(
    "/users/{user_id}",
    response_model=UserProfileResponse,
    summary="Get user profile and existence summary",
)
async def get_user_profile(user_id: str) -> UserProfileResponse:
    return await handle_get_user_profile(user_id)


@router.get(
    "/users/{user_id}/reviews",
    response_model=ReviewListResponse,
    summary="List review history for a user",
)
async def list_user_reviews(
    user_id: str,
    source: str | None = Query(default=None, description="Filter by source: dataset | generated | api"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> ReviewListResponse:
    return await handle_list_reviews(user_id, source=source, limit=limit, offset=offset)


@router.get(
    "/users/{user_id}/reviews/generated",
    response_model=ReviewListResponse,
    summary="List Task A generated reviews for a user",
)
async def list_generated_reviews(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=200),
) -> ReviewListResponse:
    return await handle_list_generated_reviews(user_id, limit=limit)


@router.get(
    "/items/{parent_asin}",
    response_model=ItemResponse,
    summary="Look up a catalogue item by ASIN",
)
async def get_item(parent_asin: str) -> ItemResponse:
    return await handle_get_item(parent_asin)


@router.post(
    "/items/verify",
    response_model=ItemVerifyResponse,
    summary="Batch-verify ASINs against the catalogue",
)
async def verify_items(req: ItemVerifyRequest) -> ItemVerifyResponse:
    return await handle_verify_items(req)


@router.get(
    "/users/{user_id}/recommendations",
    response_model=RecommendationListResponse,
    summary="List persisted Task B recommendation runs for a user",
)
async def list_user_recommendations(
    user_id: str,
    limit: int = Query(default=20, ge=1, le=100),
) -> RecommendationListResponse:
    return await handle_list_recommendations(user_id, limit=limit)


@router.get(
    "/recommendations/{request_id}",
    response_model=RecommendationLogResponse,
    summary="Get a persisted recommendation run with catalogue verification",
)
async def get_recommendation_run(request_id: str) -> RecommendationLogResponse:
    return await handle_get_recommendation(request_id)
