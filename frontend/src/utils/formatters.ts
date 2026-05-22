// Formatting utilities — Jollof Intelligence Frontend

/**
 * Formats a recommendation score as "Score: X.XX".
 * Score is a float in [0.0, 1.0], rounded to two decimal places.
 */
export function formatScore(score: number): string {
  return `Score: ${score.toFixed(2)}`;
}

/**
 * Formats an average rating to one decimal place.
 */
export function formatAvgRating(avg: number): string {
  return avg.toFixed(1);
}

/**
 * Formats a list of categories as a comma-separated string.
 */
export function formatCategories(categories: string[]): string {
  return categories.join(', ');
}
