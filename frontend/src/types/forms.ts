import type { ApiError } from './api';

// ── Form state types ─────────────────────────────────────────────

export interface ReviewFormState {
  user_id: string;
  item_title: string;
  author: string;
  categories: string;
  price: string;
  description: string;
}

export interface RecommendFormState {
  user_id: string;
  context: string;
  top_k: number;
}

// ── Validation error types ───────────────────────────────────────

export interface ReviewValidationErrors {
  user_id?: string;
  item_title?: string;
}

export interface RecommendValidationErrors {
  user_id?: string;
  context?: string;
  top_k?: string;
}

// ── Request state types ──────────────────────────────────────────

export type RequestStatus = 'idle' | 'loading' | 'success' | 'error';

export interface RequestState<T> {
  status: RequestStatus;
  data: T | null;
  error: ApiError | null;
}

// ── Default form values ──────────────────────────────────────────

export const DEFAULT_REVIEW_FORM: ReviewFormState = {
  user_id: '',
  item_title: '',
  author: '',
  categories: '',
  price: '',
  description: '',
};

export const DEFAULT_RECOMMEND_FORM: RecommendFormState = {
  user_id: '',
  context: '',
  top_k: 5,
};
