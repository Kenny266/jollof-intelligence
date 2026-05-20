"""
Seed the relational database (SQLite by default) from the preprocessed Parquet file.

Populates:
    users        — one row per distinct user_id
    user_reviews — one row per review with source='dataset'
    items        — one row per distinct parent_asin

Idempotent: rows are upserted via INSERT OR IGNORE / ON CONFLICT DO NOTHING.
Safe to re-run after adding new data.

Usage:
    python -m data.pipeline.seed_db
    python -m data.pipeline.seed_db --batch-size 1000
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.db.engine import init_db
from shared.db.models import Item, User, UserReview

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROCESSED_DIR = Path("data/processed")
MERGED_FILE = PROCESSED_DIR / "merged.parquet"


def _safe_str(v: object) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def _safe_float(v: object) -> float | None:
    try:
        f = float(v)  # type: ignore[arg-type]
        return f if f == f else None  # filter NaN
    except (TypeError, ValueError):
        return None


async def _seed(batch_size: int) -> None:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession

    from shared.db.engine import _get_engine

    if not MERGED_FILE.exists():
        raise FileNotFoundError(f"Missing {MERGED_FILE}. Run preprocess.py first.")

    logger.info("Initialising database schema…")
    await init_db()

    logger.info("Loading merged.parquet…")
    df = pd.read_parquet(MERGED_FILE)
    logger.info("Loaded %d rows", len(df))

    engine = _get_engine()

    # ── Seed items ──────────────────────────────────────────────────────────
    meta_cols = ["parent_asin", "item_title", "author", "categories", "price", "description", "average_rating"]
    available = [c for c in meta_cols if c in df.columns]
    items_df = df[available].drop_duplicates(subset=["parent_asin"])
    logger.info("Seeding %d items…", len(items_df))

    async with engine.begin() as conn:
        for start in tqdm(range(0, len(items_df), batch_size), desc="items"):
            batch = items_df.iloc[start : start + batch_size]
            rows = [
                {
                    "parent_asin": _safe_str(row.get("parent_asin")) or "",
                    "title": _safe_str(row.get("item_title")),
                    "author": _safe_str(row.get("author")),
                    "categories": _safe_str(row.get("categories")),
                    "price": _safe_str(row.get("price")),
                    "description": _safe_str(row.get("description")),
                    "average_rating": _safe_float(row.get("average_rating")),
                }
                for _, row in batch.iterrows()
                if _safe_str(row.get("parent_asin"))
            ]
            if rows:
                await conn.execute(
                    text(
                        "INSERT OR IGNORE INTO items "
                        "(parent_asin, title, author, categories, price, description, average_rating) "
                        "VALUES (:parent_asin, :title, :author, :categories, :price, :description, :average_rating)"
                    ),
                    rows,
                )

    # ── Seed users ───────────────────────────────────────────────────────────
    distinct_users = df["user_id"].dropna().unique()
    logger.info("Seeding %d users…", len(distinct_users))

    async with engine.begin() as conn:
        for start in tqdm(range(0, len(distinct_users), batch_size), desc="users"):
            batch = distinct_users[start : start + batch_size]
            rows = [{"user_id": str(uid), "is_cold_start": False} for uid in batch if uid]
            if rows:
                await conn.execute(
                    text(
                        "INSERT OR IGNORE INTO users (user_id, is_cold_start) "
                        "VALUES (:user_id, :is_cold_start)"
                    ),
                    rows,
                )

    # ── Seed user_reviews ────────────────────────────────────────────────────
    review_cols = [
        "user_id", "parent_asin", "item_title", "author", "categories",
        "rating", "text", "timestamp",
    ]
    available_rev = [c for c in review_cols if c in df.columns]
    logger.info("Seeding %d reviews…", len(df))

    async with engine.begin() as conn:
        for start in tqdm(range(0, len(df), batch_size), desc="reviews"):
            batch = df.iloc[start : start + batch_size]
            rows = []
            for _, row in batch.iterrows():
                uid = _safe_str(row.get("user_id"))
                title = _safe_str(row.get("item_title"))
                if not uid or not title:
                    continue
                rows.append({
                    "user_id": uid,
                    "parent_asin": _safe_str(row.get("parent_asin")),
                    "item_title": title,
                    "author": _safe_str(row.get("author")),
                    "category": _safe_str(row.get("categories")),
                    "rating": _safe_float(row.get("rating")),
                    "review_text": _safe_str(row.get("text")),
                    "review_date": _safe_str(row.get("timestamp")),
                    "source": "dataset",
                })
            if rows:
                await conn.execute(
                    text(
                        "INSERT OR IGNORE INTO user_reviews "
                        "(user_id, parent_asin, item_title, author, category, "
                        " rating, review_text, review_date, source) "
                        "VALUES (:user_id, :parent_asin, :item_title, :author, :category, "
                        "        :rating, :review_text, :review_date, :source)"
                    ),
                    rows,
                )

    # ── Summary ──────────────────────────────────────────────────────────────
    async with engine.connect() as conn:
        n_reviews = (await conn.execute(text("SELECT COUNT(*) FROM user_reviews"))).scalar()
        n_items = (await conn.execute(text("SELECT COUNT(*) FROM items"))).scalar()
        n_users = (await conn.execute(text("SELECT COUNT(*) FROM users"))).scalar()

    logger.info("Seed complete — users: %d | reviews: %d | items: %d", n_users, n_reviews, n_items)


def run(batch_size: int = 500) -> None:
    asyncio.run(_seed(batch_size))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed relational DB from merged.parquet")
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()
    run(batch_size=args.batch_size)
