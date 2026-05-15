from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ReviewHistory(BaseModel):
    item_name: str
    category: str
    rating: float
    review_text: str


class ConversationTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class RecommendRequest(BaseModel):
    user_id: str
    user_history: List[ReviewHistory] = []
    context: Optional[str] = ""
    conversation: List[ConversationTurn] = []


class RecommendedItem(BaseModel):
    item_id: str
    name: str
    category: str
    score: float
    reason: str


class RecommendResponse(BaseModel):
    user_id: str
    recommendations: List[RecommendedItem]
    follow_up: Optional[str] = None
