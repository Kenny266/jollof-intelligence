"""
Shared database query helpers.
Both Task A and Task B import from here.
All queries map to the final schema:
  users / categories / item_metadata / user_to_products
"""
import os
from typing import List, Dict, Any, Optional

import psycopg2
import psycopg2.extras

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://hackathon:hackathon@localhost:5432/hackathon",
)


def get_conn():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


# ── USER queries ──────────────────────────────────────────────

def get_user_persona(user_id: str) -> Optional[Dict]:
    """
    Returns pre-computed persona from the materialized view.
    Includes avg_rating, rating_std, categories, positivity_rate, avg_review_length.
    """
    sql = "SELECT * FROM user_personas WHERE user_id = %s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            return cur.fetchone()


def get_user_history(user_id: str, limit: int = 20, split: str = "train") -> List[Dict]:
    """
    Fetch a user's review history with item and category info.
    Returns: rating, review_text, comment, item_name, item_id, category_name, reviewed_at
    """
    sql = """
        SELECT
            r.rating,
            r.review_text,
            r.comment,
            r.reviewed_at,
            r.split,
            i.item_id,
            i.name        AS item_name,
            i.avg_rating  AS item_avg_rating,
            c.name        AS category_name,
            c.domain
        FROM user_to_products r
        JOIN item_metadata i ON r.item_id = i.item_id
        JOIN categories c    ON i.category_id = c.category_id
        WHERE r.user_id = %s
          AND r.split = %s
        ORDER BY r.reviewed_at DESC NULLS LAST
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, split, limit))
            return cur.fetchall()


# ── ITEM queries ──────────────────────────────────────────────

def get_items_by_category(category_name: str, limit: int = 100) -> List[Dict]:
    """Top-rated items in a category — used for cold-start and re-ranking."""
    sql = """
        SELECT
            i.item_id, i.name, i.description, i.price,
            i.avg_rating, i.review_count,
            c.name AS category_name, c.domain
        FROM item_metadata i
        JOIN categories c ON i.category_id = c.category_id
        WHERE c.name = %s
          AND i.review_count >= 5
        ORDER BY i.avg_rating DESC, i.review_count DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (category_name, limit))
            return cur.fetchall()


def get_popular_items(limit: int = 50) -> List[Dict]:
    """Global popularity fallback — used when user has no history at all."""
    sql = """
        SELECT
            i.item_id, i.name, i.description, i.price,
            i.avg_rating, i.review_count,
            c.name AS category_name, c.domain
        FROM item_metadata i
        JOIN categories c ON i.category_id = c.category_id
        WHERE i.review_count >= 10
        ORDER BY i.avg_rating DESC, i.review_count DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            return cur.fetchall()


def get_item_by_id(item_id: str) -> Optional[Dict]:
    sql = """
        SELECT i.*, c.name AS category_name, c.domain
        FROM item_metadata i
        JOIN categories c ON i.category_id = c.category_id
        WHERE i.item_id = %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (item_id,))
            return cur.fetchone()


def get_items_by_domain(domain: str, limit: int = 50) -> List[Dict]:
    """Cross-domain retrieval — fetch items from a different domain."""
    sql = """
        SELECT
            i.item_id, i.name, i.description, i.price,
            i.avg_rating, i.review_count,
            c.name AS category_name, c.domain
        FROM item_metadata i
        JOIN categories c ON i.category_id = c.category_id
        WHERE c.domain = %s
          AND i.review_count >= 5
        ORDER BY i.avg_rating DESC, i.review_count DESC
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (domain, limit))
            return cur.fetchall()


# ── CATEGORIES ────────────────────────────────────────────────

def get_all_categories() -> List[Dict]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT category_id, name, domain FROM categories ORDER BY name")
            return cur.fetchall()


# ── EVAL queries ──────────────────────────────────────────────

def get_test_users(limit: int = 200) -> List[str]:
    """Users who have test-split reviews — used as eval set."""
    sql = """
        SELECT DISTINCT user_id
        FROM user_to_products
        WHERE split = 'test'
        LIMIT %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            return [row["user_id"] for row in cur.fetchall()]


def get_ground_truth(user_id: str, min_rating: int = 4) -> List[str]:
    """
    Ground truth item_ids from the test split for a user.
    Only includes items rated >= min_rating (positive interactions).
    """
    sql = """
        SELECT item_id
        FROM user_to_products
        WHERE user_id = %s
          AND split = 'test'
          AND rating >= %s
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (user_id, min_rating))
            return [row["item_id"] for row in cur.fetchall()]
