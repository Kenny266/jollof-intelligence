import asyncio
import logging
from uuid import uuid4

from fastapi import HTTPException

from shared.db.user_history import user_history_repo
from shared.db.verification_repo import verification_repo
from src.models.task_b import RecommendRequest, RecommendResponse, RecommendedItem
from task_b.agent import RecommendationAgent

logger = logging.getLogger(__name__)
_agent = RecommendationAgent()


async def handle_recommend(req: RecommendRequest) -> RecommendResponse:
    """
    Controller for POST /api/v1/task-b/recommend.

    1. Fetch user history from DB — no history in request body.
    2. Delegate to RecommendationAgent (cold-start detected by empty history).
    3. Map agent output to the response model.
    4. Persist run to DB asynchronously for verification.
    """
    request_id = str(uuid4())
    try:
        await user_history_repo.ensure_user(req.user_id)

        history = await user_history_repo.get_history(req.user_id)
        logger.info(
            "Task B: user=%s history_len=%d cold_start=%s context=%r request_id=%s",
            req.user_id,
            len(history),
            len(history) == 0,
            req.context[:80],
            request_id,
        )

        conversation_dicts = [
            {"role": t.role, "content": t.content}
            for t in req.conversation
        ]

        result = await _agent.run(
            user_id=req.user_id,
            history=history,
            context=req.context,
            conversation=conversation_dicts,
            top_k=req.top_k,
        )

        rec_dicts = result.get("recommendations", [])
        items = [
            RecommendedItem(
                item_id=str(r.get("item_id") or r.get("parent_asin") or ""),
                title=str(r.get("title", "")),
                author=str(r.get("author", "")),
                categories=str(r.get("categories", "")),
                price=str(r.get("price", "N/A")),
                score=float(r.get("score", 0.5)),
                reason=str(r.get("reason", "")),
            )
            for r in rec_dicts
        ]

        asyncio.create_task(
            _write_back_recommendation(
                request_id=request_id,
                user_id=req.user_id,
                context=req.context,
                cold_start=result.get("cold_start", False),
                follow_up=result.get("follow_up"),
                top_k=req.top_k,
                recommendations=rec_dicts,
            )
        )

        return RecommendResponse(
            user_id=result["user_id"],
            request_id=request_id,
            recommendations=items,
            follow_up=result.get("follow_up"),
            cold_start=result.get("cold_start", False),
        )
    except Exception as exc:
        logger.error(
            "Task B recommendation failed",
            extra={"user_id": req.user_id, "request_id": request_id, "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {exc}") from exc


async def _write_back_recommendation(
    request_id: str,
    user_id: str,
    context: str,
    cold_start: bool,
    follow_up: str | None,
    top_k: int,
    recommendations: list[dict],
) -> None:
    """Persist recommendation run for verification. Errors are logged only."""
    try:
        await verification_repo.save_recommendation(
            request_id=request_id,
            user_id=user_id,
            context=context,
            cold_start=cold_start,
            follow_up=follow_up,
            top_k=top_k,
            recommendations=recommendations,
        )
        logger.info("Write-back: saved recommendation run request_id=%s user=%s", request_id, user_id)
    except Exception as exc:
        logger.error("Write-back recommendation failed request_id=%s: %s", request_id, exc)
