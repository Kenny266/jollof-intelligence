"""
SQLAlchemy ORM models for the Jollof Intelligence relational store.

Tables:
    users        — one row per known user_id
    user_reviews — canonical review history, populated by seed_db + generated write-backs
    items        — product catalogue (parent_asin lookup for Task A/B)
"""
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    is_cold_start: Mapped[bool] = mapped_column(Boolean, default=True)


class UserReview(Base):
    __tablename__ = "user_reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "parent_asin", "source", name="uq_user_asin_source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    parent_asin: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    item_title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_date: Mapped[str | None] = mapped_column(String, nullable=True)
    # 'dataset' | 'generated' | 'api'
    source: Mapped[str] = mapped_column(String, nullable=False, default="dataset")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


class Item(Base):
    __tablename__ = "items"

    parent_asin: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    author: Mapped[str | None] = mapped_column(String, nullable=True)
    categories: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    average_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
