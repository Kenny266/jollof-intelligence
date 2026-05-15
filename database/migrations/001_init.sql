-- ============================================================
-- DSN x BCT Hackathon — PostgreSQL Schema v2
-- Tables: users, categories, item_metadata, user_to_products
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── 1. USERS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,
    name            TEXT,
    email           TEXT,
    review_count    INTEGER DEFAULT 0,
    avg_rating      NUMERIC(3,2) DEFAULT 0,
    top_categories  TEXT[] DEFAULT '{}',
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ── 2. CATEGORIES ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    category_id     SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    domain          TEXT NOT NULL,          -- e.g. Electronics, Beauty, Food
    embedding       FLOAT[],                -- category-level embedding for cross-domain retrieval
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Seed the three Amazon domains we are using
INSERT INTO categories (name, domain) VALUES
    ('Electronics',    'Electronics'),
    ('All_Beauty',     'Beauty'),
    ('Food_and_Drink', 'Food')
ON CONFLICT (name) DO NOTHING;

-- ── 3. ITEM_METADATA ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS item_metadata (
    item_id         TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    category_id     INTEGER REFERENCES categories(category_id) ON DELETE SET NULL,
    avg_rating      NUMERIC(3,2) DEFAULT 0,
    review_count    INTEGER DEFAULT 0,
    description     TEXT,
    price           NUMERIC(10,2),
    embedding       FLOAT[],                -- item-level embedding for FAISS / vector search
    features        JSONB DEFAULT '[]',
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ── 4. USER_TO_PRODUCTS ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_to_products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id         TEXT NOT NULL REFERENCES item_metadata(item_id) ON DELETE CASCADE,
    rating          SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text     TEXT,
    comment         TEXT,                   -- review title / short comment
    verified        BOOLEAN DEFAULT FALSE,
    helpful_votes   INTEGER DEFAULT 0,
    split           TEXT DEFAULT 'train' CHECK (split IN ('train', 'val', 'test')),
    reviewed_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ── INDEXES ──────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_utp_user_id      ON user_to_products(user_id);
CREATE INDEX IF NOT EXISTS idx_utp_item_id      ON user_to_products(item_id);
CREATE INDEX IF NOT EXISTS idx_utp_rating       ON user_to_products(rating);
CREATE INDEX IF NOT EXISTS idx_utp_split        ON user_to_products(split);
CREATE INDEX IF NOT EXISTS idx_utp_reviewed_at  ON user_to_products(reviewed_at);
CREATE INDEX IF NOT EXISTS idx_item_category    ON item_metadata(category_id);
CREATE INDEX IF NOT EXISTS idx_item_avg_rating  ON item_metadata(avg_rating DESC);

-- ── MATERIALIZED VIEW: user persona signals ───────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS user_personas AS
SELECT
    u.user_id,
    u.name,
    COUNT(r.id)                                         AS review_count,
    ROUND(AVG(r.rating)::NUMERIC, 2)                   AS avg_rating,
    ROUND(STDDEV(r.rating)::NUMERIC, 2)                AS rating_std,
    ARRAY_AGG(DISTINCT c.domain ORDER BY c.domain)     AS domains,
    ARRAY_AGG(DISTINCT cat.name ORDER BY cat.name)     AS categories,
    ROUND(
        SUM(CASE WHEN r.rating >= 4 THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(r.id), 0), 2
    )                                                   AS positivity_rate,
    ROUND(
        AVG(CHAR_LENGTH(COALESCE(r.review_text, '')))::NUMERIC, 0
    )                                                   AS avg_review_length
FROM users u
JOIN user_to_products r    ON u.user_id = r.user_id
JOIN item_metadata i       ON r.item_id = i.item_id
JOIN categories cat        ON i.category_id = cat.category_id
JOIN categories c          ON i.category_id = c.category_id
GROUP BY u.user_id, u.name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_personas_uid ON user_personas(user_id);
