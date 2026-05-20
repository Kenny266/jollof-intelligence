from typing import Optional

from pydantic import BaseModel, Field


class ProductDetails(BaseModel):
    parent_asin: Optional[str] = Field(
        default=None,
        description="ASIN used to look up item metadata from the catalogue. "
                    "When provided, controller fetches title/author/categories from DB; "
                    "any fields below act as overrides.",
    )
    item_title: str = Field(..., description="Title of the product to review")
    author: Optional[str] = Field(default="", description="Author/creator name")
    categories: Optional[str] = Field(default="Books", description="Product categories")
    price: Optional[str] = Field(default="N/A", description="Product price")
    description: Optional[str] = Field(default="", description="Product description")


class ReviewRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    product: ProductDetails = Field(..., description="Details of the product to simulate a review for")


class PersonaSummary(BaseModel):
    avg_rating: float
    top_categories: list[str]
    tone: str
    sentiment_tendency: str
    cold_start: bool


class ReviewResponse(BaseModel):
    user_id: str
    rating: int = Field(..., ge=1, le=5, description="Predicted star rating (1-5)")
    review: str = Field(..., description="Simulated review text")
    persona_summary: Optional[PersonaSummary] = None
    rag_metrics: Optional[dict] = None
