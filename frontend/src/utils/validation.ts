// Validation utilities — Jollof Intelligence Frontend

const USER_ID_PATTERN = /^[A-Za-z0-9_-]+$/;
const USER_ID_MAX_LENGTH = 64;
const ITEM_TITLE_MAX_LENGTH = 256;
const TOP_K_MIN = 1;
const TOP_K_MAX = 20;

/**
 * Validates a user_id field.
 * Rules: non-empty, only alphanumeric/hyphens/underscores, max 64 chars.
 * Returns an error message string, or null if valid.
 */
export function validateUserId(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return 'User ID is required';
  }
  if (!USER_ID_PATTERN.test(trimmed)) {
    return 'User ID may only contain letters, numbers, hyphens, and underscores';
  }
  if (trimmed.length > USER_ID_MAX_LENGTH) {
    return `User ID must be ${USER_ID_MAX_LENGTH} characters or fewer`;
  }
  return null;
}

/**
 * Validates an item_title field.
 * Rules: non-empty, max 256 chars.
 * Returns an error message string, or null if valid.
 */
export function validateItemTitle(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return 'Book title is required';
  }
  if (trimmed.length > ITEM_TITLE_MAX_LENGTH) {
    return `Book title must be ${ITEM_TITLE_MAX_LENGTH} characters or fewer`;
  }
  return null;
}

/**
 * Validates a context field.
 * Rules: non-empty.
 * Returns an error message string, or null if valid.
 */
export function validateContext(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length === 0) {
    return 'Context is required';
  }
  return null;
}

/**
 * Validates a top_k field.
 * Rules: integer in range [1, 20].
 * Returns an error message string, or null if valid.
 */
export function validateTopK(value: number): string | null {
  if (!Number.isInteger(value) || value < TOP_K_MIN || value > TOP_K_MAX) {
    return `Number of recommendations must be between ${TOP_K_MIN} and ${TOP_K_MAX}`;
  }
  return null;
}
