// API contract types — mirrors the Jollof Intelligence FastAPI backend exactly

// ── Task A — Book Review Simulator ──────────────────────────────

export interface ReviewRequest {
  user_id: string;
  product: {
    item_title: string;
    author?: string;
    categories?: string;
    price?: string;
    description?: string;
    parent_asin?: string;
  };
}

export interface PersonaSummaryData {
  avg_rating: number;
  top_categories: string[];
  tone: string;
  sentiment_tendency: string;
  cold_start: boolean;
}

export interface ReviewResponse {
  user_id: string;
  rating: number; // 1–5 integer
  review: string;
  persona_summary: PersonaSummaryData;
}

// ── Task B — Personalised Book Recommender ──────────────────────

export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface RecommendRequest {
  user_id: string;
  context: string;
  conversation: ConversationTurn[];
  top_k?: number; // 1–20, default 5
}

export interface Recommendation {
  item_id: string;
  title: string;
  author: string;
  categories: string;
  price: string;
  score: number; // 0.0–1.0
  reason: string;
}

export interface RecommendResponse {
  user_id: string;
  request_id: string;
  recommendations: Recommendation[];
  follow_up?: string;
  cold_start: boolean;
}

// ── API Client types ─────────────────────────────────────────────

export interface ApiClientConfig {
  baseUrl: string;    // from VITE_API_BASE_URL, default http://localhost:8000
  timeoutMs: number;  // 120_000
}

export interface ApiError {
  kind: 'client' | 'server' | 'network' | 'timeout' | 'parse';
  status?: number;
  message: string;
}

export type ApiResult<T> =
  | { ok: true; data: T }
  | { ok: false; error: ApiError };
