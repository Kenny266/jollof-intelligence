from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ReviewHistory(BaseModel):
    item_name: str
    category: str
    rating: float
    review_text: str
    date: Optional[str] = None


class Product(BaseModel):
    name: str
    category: str
    location: Optional[str] = None
    description: Optional[str] = None


class ReviewRequest(BaseModel):
    user_id: str
    user_history: List[ReviewHistory] = []
    product: Product


class ReviewResponse(BaseModel):
    user_id: str
    rating: int
    review: str
    confidence: Optional[float] = None
