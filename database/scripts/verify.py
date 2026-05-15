"""
Post-ingestion sanity check.
Usage: python -m database.scripts.verify
"""
import logging
from database.scripts.db import get_conn

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

def main():
    conn = get_conn()
    log.info("\n========== DATABASE VERIFICATION ==========\n")

    checks = [
        ("Users",                  "SELECT COUNT(*) FROM users"),
        ("Items",                  "SELECT COUNT(*) FROM item_metadata"),
        ("Reviews (total)",        "SELECT COUNT(*) FROM user_to_products"),
        ("Categories",             "SELECT COUNT(*) FROM categories"),
    ]
    for label, sql in checks:
        with conn.cursor() as cur:
            cur.execute(sql)
            val = list(cur.fetchone().values())[0]
            log.info(f"  {label:<30} {val:>12,}")

    log.info("")
    log.info("  Reviews by category:")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.name, COUNT(r.id)
            FROM user_to_products r
            JOIN item_metadata i ON r.item_id = i.item_id
            JOIN categories c    ON i.category_id = c.category_id
            GROUP BY c.name ORDER BY c.name
        """)
        for row in cur.fetchall():
            vals = list(row.values())
            log.info(f"    {str(vals[0]):<25} {vals[1]:>10,}")

    log.info("")
    log.info("  Train / val / test split:")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT split, COUNT(*)
            FROM user_to_products
            GROUP BY split ORDER BY split
        """)
        for row in cur.fetchall():
            vals = list(row.values())
            log.info(f"    {str(vals[0]):<10} {vals[1]:>15,}")

    log.info("")
    log.info("  Avg rating by category:")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.name, ROUND(AVG(r.rating)::NUMERIC,2)
            FROM user_to_products r
            JOIN item_metadata i ON r.item_id = i.item_id
            JOIN categories c    ON i.category_id = c.category_id
            GROUP BY c.name ORDER BY c.name
        """)
        for row in cur.fetchall():
            vals = list(row.values())
            log.info(f"    {str(vals[0]):<25} {vals[1]:>10}")

    log.info("")
    log.info("  Users with persona data:  ", end="")
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM user_personas")
        log.info(f"{list(cur.fetchone().values())[0]:,}")

    log.info("")
    log.info("  Cold-start users (0 reviews):")
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_to_products r WHERE r.user_id = u.user_id
            )
        """)
        log.info(f"    {list(cur.fetchone().values())[0]:,}")

    log.info("\n===========================================\n")
    conn.close()

if __name__ == "__main__":
    main()
