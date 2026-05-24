from typing import Optional

from pydantic import BaseModel, Field


class ConversationTurn(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$", description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class RecommendRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    context: str = Field(
        default="",
        description=(
            "Free-text request or user description. "
            "For cold-start users, describe the user (e.g. '22-year-old student who loves sci-fi'). "
            "For warm users, state the current recommendation request."
        ),
    )
    conversation: list[ConversationTurn] = Field(
        default_factory=list,
        description="Prior conversation turns for multi-turn refinement.",
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Number of recommendations to return")


class RecommendedItem(BaseModel):
    item_id: str = Field(default="")
    title: str
    author: Optional[str] = Field(default="")
    categories: Optional[str] = Field(default="")
    price: Optional[str] = Field(default="N/A")
    score: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., description="Conversational explanation for why this item was recommended")


class RecommendResponse(BaseModel):
    user_id: str
    request_id: str = Field(..., description="UUID for verifying this run via GET /recommendations/{request_id}")
    recommendations: list[RecommendedItem]
    follow_up: Optional[str] = Field(default=None, description="Follow-up question for multi-turn refinement")
    cold_start: bool = Field(default=False)
