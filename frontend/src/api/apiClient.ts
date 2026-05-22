import type {
  ReviewRequest,
  ReviewResponse,
  RecommendRequest,
  RecommendResponse,
  ApiClientConfig,
  ApiError,
  ApiResult,
} from '../types/api';

const DEFAULT_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const DEFAULT_TIMEOUT_MS = 120_000;

const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: DEFAULT_BASE_URL,
  timeoutMs: DEFAULT_TIMEOUT_MS,
};

// ── Error classification ─────────────────────────────────────────

/**
 * Classifies an HTTP status code into an ApiError kind.
 * 4xx → 'client', 5xx → 'server'
 */
export function classifyApiError(status: number): ApiError {
  if (status >= 400 && status < 500) {
    return {
      kind: 'client',
      status,
      message: 'Invalid request — check your inputs',
    };
  }
  return {
    kind: 'server',
    status,
    message: 'The server encountered an error — please try again',
  };
}

// ── Core fetch wrapper ───────────────────────────────────────────

async function apiFetch<T>(
  url: string,
  body: unknown,
  config: ApiClientConfig
): Promise<ApiResult<T>> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), config.timeoutMs);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Parse response body as JSON
    let parsed: unknown;
    try {
      parsed = await response.json();
    } catch {
      return {
        ok: false,
        error: {
          kind: 'parse',
          status: response.status,
          message: 'Received an unexpected response from the server',
        },
      };
    }

    // Handle HTTP errors
    if (!response.ok) {
      const base = classifyApiError(response.status);
      // Try to extract detail from FastAPI error body
      let message = base.message;
      if (parsed && typeof parsed === 'object') {
        const obj = parsed as Record<string, unknown>;
        if (typeof obj['detail'] === 'string') {
          message = obj['detail'];
        } else if (obj['detail'] !== undefined) {
          message = JSON.stringify(obj['detail']);
        } else {
          message = JSON.stringify(parsed);
        }
      }
      return {
        ok: false,
        error: { ...base, message },
      };
    }

    return { ok: true, data: parsed as T };
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    // AbortController fired → timeout
    if (err instanceof DOMException && err.name === 'AbortError') {
      return {
        ok: false,
        error: {
          kind: 'timeout',
          message: 'The request timed out — please try again',
        },
      };
    }

    // Network failure
    return {
      ok: false,
      error: {
        kind: 'network',
        message: 'Could not reach the server — check your connection',
      },
    };
  }
}

// ── Public API ───────────────────────────────────────────────────

/**
 * Calls POST /api/v1/task-a/generate-review
 */
export async function generateReview(
  request: ReviewRequest,
  config: Partial<ApiClientConfig> = {}
): Promise<ApiResult<ReviewResponse>> {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  const url = `${cfg.baseUrl}/api/v1/task-a/generate-review`;
  return apiFetch<ReviewResponse>(url, request, cfg);
}

/**
 * Calls POST /api/v1/task-b/recommend
 */
export async function getRecommendations(
  request: RecommendRequest,
  config: Partial<ApiClientConfig> = {}
): Promise<ApiResult<RecommendResponse>> {
  const cfg = { ...DEFAULT_CONFIG, ...config };
  const url = `${cfg.baseUrl}/api/v1/task-b/recommend`;
  return apiFetch<RecommendResponse>(url, request, cfg);
}
