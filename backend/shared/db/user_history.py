"""
UserHistoryRepository — async CRUD for the user_reviews and users tables.

All methods return plain dicts in the shape that build_persona() expects:
    {item_name, category, rating, review_text, date}

This keeps the persona builder decoupled from SQLAlchemy ORM objects.
"""
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from shared.db.engine import get_async_session
from shared.db.models import Item, User, UserReview

logger = logging.getLogger(__name__)


class UserHistoryRepository:
    """
    Async repository for user review history.
    Each method opens its own session so callers do not need to manage sessions.
    """

    async def get_history(
        self,
        user_id: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch all stored reviews for a user, ordered newest-first.

        Returns dicts compatible with build_persona():
            {item_name, category, rating, review_text, date}
        """
        async with get_async_session() as session:
            stmt = (
                select(UserReview)
                .where(UserReview.user_id == user_id)
                .order_by(UserReview.review_date.desc().nullslast(), UserReview.created_at.desc())
            )
            if limit is not None:
                stmt = stmt.limit(limit)
            rows = (await session.execute(stmt)).scalars().all()

        return [
            {
                "item_name": row.item_title,
                "category": row.category or "Books",
                "rating": row.rating or 3.0,
                "review_text": row.review_text or "",
                "date": row.review_date,
                "parent_asin": row.parent_asin,
            }
            for row in rows
        ]

    async def count_reviews(self, user_id: str) -> int:
        """Return the total number of reviews stored for a user."""
        async with get_async_session() as session:
            stmt = select(func.count()).where(UserReview.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalar_one()

    async def user_exists(self, user_id: str) -> bool:
        """Return True if the user has at least one review in the DB."""
        return await self.count_reviews(user_id) > 0

    async def save_review(
        self,
        user_id: str,
        review: dict[str, Any],
        source: str = "generated",
    ) -> None:
        """
        Persist a single review row.

        Args:
            user_id: Target user identifier.
            review:  Dict with keys: item_title, author, category, rating,
                     review_text, review_date, parent_asin (all optional except item_title).
            source:  'dataset' | 'generated' | 'api'
        """
        async with get_async_session() as session:
            row = UserReview(
                user_id=user_id,
                parent_asin=review.get("parent_asin"),
                item_title=review.get("item_title") or review.get("item_name", "Unknown"),
                author=review.get("author"),
                category=review.get("category"),
                rating=review.get("rating"),
                review_text=review.get("review_text"),
                review_date=review.get("review_date") or review.get("date"),
                source=source,
                created_at=datetime.now(timezone.utc),
            )
            session.add(row)
            try:
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.warning(
                    "save_review skipped for user=%s asin=%s source=%s: %s",
                    user_id,
                    review.get("parent_asin"),
                    source,
                    exc,
                )

    async def ensure_user(self, user_id: str) -> None:
        """
        Insert a user record if it does not already exist.
        Updates is_cold_start=False once they have reviews.
        """
        count = await self.count_reviews(user_id)
        async with get_async_session() as session:
            stmt = sqlite_insert(User).values(
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                is_cold_start=(count == 0),
            ).on_conflict_do_update(
                index_elements=["user_id"],
                set_={"is_cold_start": count == 0},
            )
            await session.execute(stmt)
            await session.commit()

    async def get_item(self, parent_asin: str) -> dict[str, Any] | None:
        """Fetch item metadata by ASIN. Returns None if not found."""
        async with get_async_session() as session:
            item = await session.get(Item, parent_asin)
            if item is None:
                return None
            return {
                "parent_asin": item.parent_asin,
                "item_title": item.title,
                "author": item.author,
                "categories": item.categories,
                "price": item.price,
                "description": item.description,
                "average_rating": item.average_rating,
            }


# Module-level singleton — controllers import this directly
user_history_repo = UserHistoryRepository()
