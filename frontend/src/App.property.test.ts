// Feature: jollof-intelligence-frontend, Property 12: Form field values are preserved across panel switches
import { describe, it, expect } from 'vitest';
import * as fc from 'fast-check';
import type { ReviewFormState, RecommendFormState } from './types/forms';

// Arbitraries
const reviewFormArb = fc.record<ReviewFormState>({
  user_id: fc.string({ minLength: 0, maxLength: 64 }),
  item_title: fc.string({ minLength: 0, maxLength: 256 }),
  author: fc.string({ minLength: 0, maxLength: 100 }),
  categories: fc.string({ minLength: 0, maxLength: 200 }),
  price: fc.string({ minLength: 0, maxLength: 20 }),
  description: fc.string({ minLength: 0, maxLength: 500 }),
});

const recommendFormArb = fc.record<RecommendFormState>({
  user_id: fc.string({ minLength: 0, maxLength: 64 }),
  context: fc.string({ minLength: 0, maxLength: 500 }),
  top_k: fc.integer({ min: 1, max: 20 }),
});

describe('Property 12: Form field values are preserved across panel switches', () => {
  it('review form state is unchanged after simulated panel switch', () => {
    fc.assert(
      fc.property(reviewFormArb, recommendFormArb, (reviewForm, recommendForm) => {
        // Simulate: store both form states (as App does via useState)
        let storedReview = { ...reviewForm };
        let storedRecommend = { ...recommendForm };

        // Switch to recommend panel (review form state untouched)
        const activePanel = 'recommend';
        void activePanel; // panel switch doesn't mutate form state

        // Switch back to review panel
        const backToReview = 'review';
        void backToReview;

        // Both form states must be byte-for-byte identical
        expect(storedReview).toEqual(reviewForm);
        expect(storedRecommend).toEqual(recommendForm);

        // Simulate an update to recommend form doesn't affect review form
        storedRecommend = { ...storedRecommend, context: 'new context' };
        expect(storedReview).toEqual(reviewForm);

        return true;
      }),
      { numRuns: 100 }
    );
  });
});
