import logging

from fastapi import HTTPException

from shared.db.verification_repo import verification_repo
from src.models.verification import (
    ItemResponse,
    ItemVerifyRequest,
    ItemVerifyResponse,
    RecommendationListResponse,
    RecommendationLogResponse,
    RecommendationRunSummary,
    ReviewListResponse,
    ReviewRecord,
    UserProfileResponse,
    VerifiedRecommendationItem,
)

logger = logging.getLogger(__name__)


async def handle_get_user_profile(user_id: str) -> UserProfileResponse:
    profile = await verification_repo.get_user_profile(user_id)
    return UserProfileResponse(**profile)


async def handle_list_reviews(
    user_id: str,
    source: str | None,
    limit: int,
    offset: int,
) -> ReviewListResponse:
    data = await verification_repo.list_reviews(
        user_id=user_id,
        source=source,
        limit=limit,
        offset=offset,
    )
    return ReviewListResponse(
        user_id=data["user_id"],
        total=data["total"],
        reviews=[ReviewRecord(**r) for r in data["reviews"]],
    )


async def handle_list_generated_reviews(user_id: str, limit: int) -> ReviewListResponse:
    data = await verification_repo.list_generated_reviews(user_id, limit=limit)
    return ReviewListResponse(
        user_id=data["user_id"],
        total=data["total"],
        reviews=[ReviewRecord(**r) for r in data["reviews"]],
    )


async def handle_get_item(parent_asin: str) -> ItemResponse:
    item = await verification_repo.get_item(parent_asin)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item not found: {parent_asin}")
    return ItemResponse(
        parent_asin=item["parent_asin"],
        title=item.get("title"),
        author=item.get("author"),
        categories=item.get("categories"),
        price=item.get("price"),
        description=item.get("description"),
        average_rating=item.get("average_rating"),
    )


async def handle_verify_items(req: ItemVerifyRequest) -> ItemVerifyResponse:
    result = await verification_repo.verify_items(req.parent_asins)
    return ItemVerifyResponse(**result)


async def handle_list_recommendations(user_id: str, limit: int) -> RecommendationListResponse:
    data = await verification_repo.list_recommendations(user_id, limit=limit)
    return RecommendationListResponse(
        user_id=data["user_id"],
        total=data["total"],
        runs=[RecommendationRunSummary(**r) for r in data["runs"]],
    )


async def handle_get_recommendation(request_id: str) -> RecommendationLogResponse:
    data = await verification_repo.get_recommendation(request_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"Recommendation run not found: {request_id}")
    return RecommendationLogResponse(
        request_id=data["request_id"],
        user_id=data["user_id"],
        context=data["context"],
        cold_start=data["cold_start"],
        follow_up=data.get("follow_up"),
        top_k=data["top_k"],
        created_at=data.get("created_at"),
        recommendations=[VerifiedRecommendationItem(**r) for r in data["recommendations"]],
    )
