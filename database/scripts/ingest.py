"""
Amazon Reviews 2023 — Multi-category ingestion pipeline
Categories: Electronics, All_Beauty, Food_and_Drink

Tables populated:
  users  →  item_metadata  →  user_to_products
  (categories are seeded by the SQL migration)

Usage:
    python -m database.scripts.ingest

Env vars:
    DATABASE_URL  — postgres connection string
    MAX_ROWS      — max reviews per category (default: 50000)
"""
import os
import json
import logging
from datetime import datetime
from typing import Iterator, Dict, Any, List

import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://hackathon:hackathon@localhost:5432/hackathon",
)
MAX_ROWS = int(os.getenv("MAX_ROWS", 50_000))

CATEGORIES = [
    "Electronics",
    "All_Beauty",
    "Food_and_Drink",
]


# ── DB helpers ────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(DATABASE_URL)


def get_category_id(conn, category_name: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT category_id FROM categories WHERE name = %s", (category_name,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Category '{category_name}' not found. Check migration seeding.")
        return row[0]


# ── Dataset streaming ─────────────────────────────────────────

def stream_metadata(category: str) -> Iterator[Dict[str, Any]]:
    log.info(f"[{category}] Downloading item metadata...")
    ds = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_meta_{category}",
        split="full",
        trust_remote_code=True,
        streaming=True,
    )
    for row in ds:
        yield row


def stream_reviews(category: str, max_rows: int) -> Iterator[Dict[str, Any]]:
    log.info(f"[{category}] Downloading reviews (max {max_rows:,})...")
    ds = load_dataset(
        "McAuley-Lab/Amazon-Reviews-2023",
        f"raw_review_{category}",
        split="full",
        trust_remote_code=True,
        streaming=True,
    )
    for i, row in enumerate(ds):
        if i >= max_rows:
            break
        yield row


# ── Upsert: item_metadata ─────────────────────────────────────

def upsert_items(conn, rows: List[Dict], category_id: int):
    sql = """
        INSERT INTO item_metadata (item_id, name, category_id, description, price, features)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (item_id) DO UPDATE SET
            name        = EXCLUDED.name,
            description = EXCLUDED.description,
            price       = EXCLUDED.price,
            features    = EXCLUDED.features
    """
    data = []
    for r in rows:
        item_id = r.get("parent_asin") or r.get("asin", "")
        if not item_id:
            continue

        price = None
        raw_price = r.get("price")
        if raw_price:
            try:
                price = float(str(raw_price).replace("$", "").replace(",", ""))
            except ValueError:
                pass

        desc = r.get("description", "")
        if isinstance(desc, list):
            desc = " ".join(desc)

        data.append((
            item_id,
            (r.get("title") or "Unnamed")[:500],
            category_id,
            (desc or "")[:2000],
            price,
            json.dumps(r.get("features") or []),
        ))

    if data:
        with conn.cursor() as cur:
            execute_batch(cur, sql, data, page_size=500)
        conn.commit()


# ── Upsert: users ─────────────────────────────────────────────

def upsert_users(conn, user_ids: set):
    sql = """
        INSERT INTO users (user_id)
        VALUES (%s)
        ON CONFLICT (user_id) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_batch(cur, sql, [(uid,) for uid in user_ids], page_size=1000)
    conn.commit()


# ── Insert: user_to_products ──────────────────────────────────

def insert_user_to_products(conn, rows: List[Dict], category_name: str):
    sql = """
        INSERT INTO user_to_products
            (user_id, item_id, rating, review_text, comment, verified, helpful_votes, reviewed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """
    data = []
    for r in rows:
        user_id = r.get("user_id", "")
        item_id = r.get("parent_asin") or r.get("asin", "")
        if not user_id or not item_id:
            continue

        ts = None
        raw_ts = r.get("timestamp")
        if raw_ts:
            try:
                ts = datetime.fromtimestamp(int(raw_ts) / 1000)
            except Exception:
                pass

        data.append((
            user_id,
            item_id,
            max(1, min(5, int(r.get("rating", 3)))),
            (r.get("text") or "")[:5000],
            (r.get("title") or "")[:500],         # short comment / title
            bool(r.get("verified_purchase", False)),
            int(r.get("helpful_vote", 0) or 0),
            ts,
        ))

    if data:
        with conn.cursor() as cur:
            execute_batch(cur, sql, data, page_size=500)
        conn.commit()


# ── Train / val / test split (80/10/10) ───────────────────────

def assign_splits(conn):
    log.info("Assigning train/val/test splits (80/10/10 per user by time)...")
    sql = """
        UPDATE user_to_products utp
        SET split = sub.split
        FROM (
            SELECT
                id,
                CASE
                    WHEN rn::FLOAT / total <= 0.8 THEN 'train'
                    WHEN rn::FLOAT / total <= 0.9 THEN 'val'
                    ELSE 'test'
                END AS split
            FROM (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY user_id ORDER BY reviewed_at NULLS LAST, created_at
                    ) AS rn,
                    COUNT(*) OVER (PARTITION BY user_id) AS total
                FROM user_to_products
            ) ranked
        ) sub
        WHERE utp.id = sub.id
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    log.info("Splits assigned.")


# ── Aggregate stats ───────────────────────────────────────────

def update_item_stats(conn):
    log.info("Updating item_metadata avg_rating and review_count...")
    sql = """
        UPDATE item_metadata i
        SET
            avg_rating   = sub.avg_r,
            review_count = sub.cnt
        FROM (
            SELECT
                item_id,
                ROUND(AVG(rating)::NUMERIC, 2) AS avg_r,
                COUNT(*) AS cnt
            FROM user_to_products
            GROUP BY item_id
        ) sub
        WHERE i.item_id = sub.item_id
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def update_user_stats(conn):
    log.info("Updating users avg_rating, review_count, top_categories...")
    sql = """
        UPDATE users u
        SET
            review_count   = sub.cnt,
            avg_rating     = sub.avg_r,
            top_categories = sub.cats
        FROM (
            SELECT
                r.user_id,
                COUNT(*)                            AS cnt,
                ROUND(AVG(r.rating)::NUMERIC, 2)   AS avg_r,
                ARRAY_AGG(DISTINCT c.name)          AS cats
            FROM user_to_products r
            JOIN item_metadata i  ON r.item_id = i.item_id
            JOIN categories c     ON i.category_id = c.category_id
            GROUP BY r.user_id
        ) sub
        WHERE u.user_id = sub.user_id
    """
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def refresh_personas(conn):
    log.info("Refreshing user_personas materialized view...")
    with conn.cursor() as cur:
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY user_personas;")
    conn.commit()


# ── Per-category ingestion ────────────────────────────────────

def ingest_category(conn, category: str):
    log.info(f"{'='*50}")
    log.info(f"Ingesting: {category}")
    log.info(f"{'='*50}")

    category_id = get_category_id(conn, category)

    # Step 1: item_metadata
    meta_batch = []
    meta_total = 0
    for row in stream_metadata(category):
        meta_batch.append(row)
        if len(meta_batch) >= 500:
            upsert_items(conn, meta_batch, category_id)
            meta_total += len(meta_batch)
            meta_batch = []
    if meta_batch:
        upsert_items(conn, meta_batch, category_id)
        meta_total += len(meta_batch)
    log.info(f"[{category}] Items loaded: {meta_total:,}")

    # Step 2: users + user_to_products
    review_buffer = []
    user_ids = set()
    total = 0

    for row in stream_reviews(category, MAX_ROWS):
        uid = row.get("user_id", "")
        if uid:
            user_ids.add(uid)
        review_buffer.append(row)
        total += 1

        if len(review_buffer) >= 1000:
            upsert_users(conn, user_ids)
            insert_user_to_products(conn, review_buffer, category)
            review_buffer = []
            user_ids = set()
            if total % 10_000 == 0:
                log.info(f"[{category}] {total:,} reviews inserted...")

    if review_buffer:
        upsert_users(conn, user_ids)
        insert_user_to_products(conn, review_buffer, category)

    log.info(f"[{category}] Reviews loaded: {total:,}")


# ── Main ──────────────────────────────────────────────────────

def main():
    log.info("Connecting to PostgreSQL...")
    conn = get_conn()

    for category in CATEGORIES:
        ingest_category(conn, category)

    # Post-ingestion steps
    assign_splits(conn)
    update_item_stats(conn)
    update_user_stats(conn)
    refresh_personas(conn)

    # Summary report
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users")
        n_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM item_metadata")
        n_items = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_to_products")
        n_reviews = cur.fetchone()[0]
        cur.execute("""
            SELECT c.name, COUNT(r.id)
            FROM user_to_products r
            JOIN item_metadata i ON r.item_id = i.item_id
            JOIN categories c    ON i.category_id = c.category_id
            GROUP BY c.name ORDER BY c.name
        """)
        breakdown = cur.fetchall()
        cur.execute("""
            SELECT split, COUNT(*)
            FROM user_to_products
            GROUP BY split ORDER BY split
        """)
        splits = cur.fetchall()

    log.info("")
    log.info("╔══════════════════════════════╗")
    log.info("║   INGESTION COMPLETE         ║")
    log.info("╠══════════════════════════════╣")
    log.info(f"║  Users:    {n_users:>10,}        ║")
    log.info(f"║  Items:    {n_items:>10,}        ║")
    log.info(f"║  Reviews:  {n_reviews:>10,}        ║")
    log.info("╠══════════════════════════════╣")
    log.info("║  By category:                ║")
    for cat, cnt in breakdown:
        log.info(f"║    {cat:<15} {cnt:>8,}    ║")
    log.info("╠══════════════════════════════╣")
    log.info("║  By split:                   ║")
    for split, cnt in splits:
        log.info(f"║    {split:<10} {cnt:>13,}    ║")
    log.info("╚══════════════════════════════╝")

    conn.close()


if __name__ == "__main__":
    main()
