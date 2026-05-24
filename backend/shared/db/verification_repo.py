"""
Verification repository — read/query helpers for judges and audit endpoints.

Covers user profiles, review history, catalogue lookups, and persisted
Task B recommendation runs.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select

from shared.db.engine import get_async_session
from shared.db.models import Item, RecommendationItem, RecommendationLog, User, UserReview

logger = logging.getLogger(__name__)


class VerificationRepository:
    """Async repository for verification and audit queries."""

    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        """Return user existence summary and review source breakdown."""
        async with get_async_session() as session:
            user_row = await session.get(User, user_id)
            in_users_table = user_row is not None
            is_cold_start = user_row.is_cold_start if user_row else True

            total_stmt = select(func.count()).select_from(UserReview).where(
                UserReview.user_id == user_id
            )
            total_reviews = (await session.execute(total_stmt)).scalar_one()

            dataset_stmt = select(func.count()).select_from(UserReview).where(
                UserReview.user_id == user_id,
                UserReview.source == "dataset",
            )
            dataset_reviews = (await session.execute(dataset_stmt)).scalar_one()

            generated_stmt = select(func.count()).select_from(UserReview).where(
                UserReview.user_id == user_id,
                UserReview.source == "generated",
            )
            generated_reviews = (await session.execute(generated_stmt)).scalar_one()

        exists = in_users_table or total_reviews > 0
        if total_reviews > 0:
            is_cold_start = False

        return {
            "user_id": user_id,
            "exists": exists,
            "in_users_table": in_users_table,
            "review_count": total_reviews,
            "is_cold_start": is_cold_start,
            "dataset_reviews": dataset_reviews,
            "generated_reviews": generated_reviews,
        }

    async def list_reviews(
        self,
        user_id: str,
        source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Paginated review history for a user."""
        async with get_async_session() as session:
            base = select(UserReview).where(UserReview.user_id == user_id)
            if source:
                base = base.where(UserReview.source == source)

            count_stmt = select(func.count()).select_from(base.subquery())
            total = (await session.execute(count_stmt)).scalar_one()

            stmt = (
                base.order_by(
                    UserReview.review_date.desc().nullslast(),
                    UserReview.created_at.desc(),
                )
                .offset(offset)
                .limit(limit)
            )
            rows = (await session.execute(stmt)).scalars().all()

        reviews = [
            {
                "id": row.id,
                "parent_asin": row.parent_asin,
                "item_title": row.item_title,
                "author": row.author,
                "category": row.category,
                "rating": row.rating,
                "review_text": row.review_text,
                "review_date": row.review_date,
                "source": row.source,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
        return {"user_id": user_id, "total": total, "reviews": reviews}

    async def list_generated_reviews(self, user_id: str, limit: int = 50) -> dict[str, Any]:
        """Shortcut for Task A write-back reviews."""
        return await self.list_reviews(user_id, source="generated", limit=limit, offset=0)

    async def get_item(self, parent_asin: str) -> dict[str, Any] | None:
        """Fetch catalogue item by ASIN."""
        async with get_async_session() as session:
            item = await session.get(Item, parent_asin)
            if item is None:
                return None
            return {
                "parent_asin": item.parent_asin,
                "title": item.title,
                "author": item.author,
                "categories": item.categories,
                "price": item.price,
                "description": item.description,
                "average_rating": item.average_rating,
            }

    async def verify_items(self, parent_asins: list[str]) -> dict[str, Any]:
        """Batch-check which ASINs exist in the items catalogue."""
        if not parent_asins:
            return {"requested": [], "found": [], "missing": []}

        unique_asins = list(dict.fromkeys(parent_asins))
        async with get_async_session() as session:
            stmt = select(Item.parent_asin).where(Item.parent_asin.in_(unique_asins))
            found_set = set((await session.execute(stmt)).scalars().all())

        found = [a for a in unique_asins if a in found_set]
        missing = [a for a in unique_asins if a not in found_set]
        return {"requested": unique_asins, "found": found, "missing": missing}

    async def save_recommendation(
        self,
        request_id: str,
        user_id: str,
        context: str,
        cold_start: bool,
        follow_up: str | None,
        top_k: int,
        recommendations: list[dict[str, Any]],
    ) -> None:
        """Persist a Task B recommendation run and its ranked items."""
        async with get_async_session() as session:
            log = RecommendationLog(
                request_id=request_id,
                user_id=user_id,
                context=context,
                cold_start=cold_start,
                follow_up=follow_up,
                top_k=top_k,
                created_at=datetime.now(timezone.utc),
            )
            session.add(log)

            for rank, rec in enumerate(recommendations, start=1):
                item = RecommendationItem(
                    request_id=request_id,
                    parent_asin=str(rec.get("item_id") or rec.get("parent_asin") or "") or None,
                    title=str(rec.get("title", "Unknown")),
                    author=str(rec.get("author", "")) or None,
                    categories=str(rec.get("categories", "")) or None,
                    price=str(rec.get("price", "N/A")) or None,
                    score=float(rec.get("score", 0.0)),
                    reason=str(rec.get("reason", "")),
                    rank=rank,
                )
                session.add(item)

            try:
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.error(
                    "save_recommendation failed request_id=%s user=%s: %s",
                    request_id,
                    user_id,
                    exc,
                )

    async def get_recommendation(self, request_id: str) -> dict[str, Any] | None:
        """Fetch a single recommendation run with catalogue verification per item."""
        async with get_async_session() as session:
            log = await session.get(RecommendationLog, request_id)
            if log is None:
                return None

            stmt = (
                select(RecommendationItem)
                .where(RecommendationItem.request_id == request_id)
                .order_by(RecommendationItem.rank)
            )
            items = (await session.execute(stmt)).scalars().all()

        asins = [i.parent_asin for i in items if i.parent_asin]
        verify = await self.verify_items(asins)
        found_set = set(verify["found"])

        return {
            "request_id": log.request_id,
            "user_id": log.user_id,
            "context": log.context,
            "cold_start": log.cold_start,
            "follow_up": log.follow_up,
            "top_k": log.top_k,
            "created_at": log.created_at.isoformat() if log.created_at else None,
            "recommendations": [
                {
                    "rank": item.rank,
                    "item_id": item.parent_asin or "",
                    "parent_asin": item.parent_asin,
                    "title": item.title,
                    "author": item.author,
                    "categories": item.categories,
                    "price": item.price,
                    "score": item.score,
                    "reason": item.reason,
                    "catalogue_verified": bool(item.parent_asin and item.parent_asin in found_set),
                }
                for item in items
            ],
        }

    async def list_recommendations(
        self,
        user_id: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List recent recommendation runs for a user."""
        async with get_async_session() as session:
            count_stmt = select(func.count()).select_from(RecommendationLog).where(
                RecommendationLog.user_id == user_id
            )
            total = (await session.execute(count_stmt)).scalar_one()

            stmt = (
                select(RecommendationLog)
                .where(RecommendationLog.user_id == user_id)
                .order_by(RecommendationLog.created_at.desc())
                .limit(limit)
            )
            logs = (await session.execute(stmt)).scalars().all()

        return {
            "user_id": user_id,
            "total": total,
            "runs": [
                {
                    "request_id": log.request_id,
                    "context": log.context[:120] if log.context else "",
                    "cold_start": log.cold_start,
                    "top_k": log.top_k,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
        }


verification_repo = VerificationRepository()
