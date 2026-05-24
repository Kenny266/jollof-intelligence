from typing import Optional

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    user_id: str
    exists: bool
    in_users_table: bool
    review_count: int
    is_cold_start: bool
    dataset_reviews: int
    generated_reviews: int


class ReviewRecord(BaseModel):
    id: int
    parent_asin: Optional[str] = None
    item_title: str
    author: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    review_text: Optional[str] = None
    review_date: Optional[str] = None
    source: str
    created_at: Optional[str] = None


class ReviewListResponse(BaseModel):
    user_id: str
    total: int
    reviews: list[ReviewRecord]


class ItemResponse(BaseModel):
    parent_asin: str
    title: Optional[str] = None
    author: Optional[str] = None
    categories: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    average_rating: Optional[float] = None


class ItemVerifyRequest(BaseModel):
    parent_asins: list[str] = Field(..., min_length=1, description="ASINs to verify against catalogue")


class ItemVerifyResponse(BaseModel):
    requested: list[str]
    found: list[str]
    missing: list[str]


class RecommendationRunSummary(BaseModel):
    request_id: str
    context: str
    cold_start: bool
    top_k: int
    created_at: Optional[str] = None


class RecommendationListResponse(BaseModel):
    user_id: str
    total: int
    runs: list[RecommendationRunSummary]


class VerifiedRecommendationItem(BaseModel):
    rank: int
    item_id: str
    parent_asin: Optional[str] = None
    title: str
    author: Optional[str] = None
    categories: Optional[str] = None
    price: Optional[str] = None
    score: float
    reason: str
    catalogue_verified: bool


class RecommendationLogResponse(BaseModel):
    request_id: str
    user_id: str
    context: str
    cold_start: bool
    follow_up: Optional[str] = None
    top_k: int
    created_at: Optional[str] = None
    recommendations: list[VerifiedRecommendationItem]
