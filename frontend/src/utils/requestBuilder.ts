import type { ReviewRequest, RecommendRequest, ConversationTurn } from '../types/api';
import type { ReviewFormState, RecommendFormState } from '../types/forms';

/**
 * Builds a ReviewRequest from form state.
 * Empty optional fields are omitted from the product object — not sent as empty strings.
 */
export function buildReviewRequest(form: ReviewFormState): ReviewRequest {
  const product: ReviewRequest['product'] = {
    item_title: form.item_title.trim(),
  };

  if (form.author.trim()) product.author = form.author.trim();
  if (form.categories.trim()) product.categories = form.categories.trim();
  if (form.price.trim()) product.price = form.price.trim();
  if (form.description.trim()) product.description = form.description.trim();

  return {
    user_id: form.user_id.trim(),
    product,
  };
}

/**
 * Builds a RecommendRequest from form state and current conversation history.
 */
export function buildRecommendRequest(
  form: RecommendFormState,
  conversation: ConversationTurn[]
): RecommendRequest {
  return {
    user_id: form.user_id.trim(),
    context: form.context.trim(),
    conversation,
    top_k: form.top_k,
  };
}
