import { forwardRef } from 'react';
import type { ReviewResponse } from '../../types/api';
import { StarRating } from '../../components/StarRating/StarRating';
import { ColdStartBadge } from '../../components/ColdStartBadge/ColdStartBadge';
import { formatAvgRating, formatCategories } from '../../utils/formatters';
import styles from './ReviewResult.module.css';

interface ReviewResultProps {
  result: ReviewResponse;
}

export const ReviewResult = forwardRef<HTMLDivElement, ReviewResultProps>(
  ({ result }, ref) => {
    const { rating, review, persona_summary } = result;

    return (
      <div className={styles.result} ref={ref} tabIndex={-1}>
        {persona_summary.cold_start && <ColdStartBadge feature="review" />}

        {/* Star rating */}
        <div className={styles.ratingRow}>
          <span className={styles.ratingLabel}>Predicted Rating</span>
          <StarRating rating={rating} showNumeric />
        </div>

        {/* Review text */}
        <div className={styles.reviewSection}>
          <p className={styles.sectionLabel}>Generated Review</p>
          <blockquote className={styles.reviewText}>{review}</blockquote>
        </div>

        {/* Persona summary */}
        <div className={styles.reviewSection}>
          <p className={styles.sectionLabel}>Reader Persona</p>
          <div className={styles.personaCard}>
            <p className={styles.personaTitle}>📊 User Profile Summary</p>
            <div className={styles.personaGrid}>
              <div className={styles.personaItem}>
                <span className={styles.personaKey}>Avg Rating</span>
                <span className={styles.personaValue}>
                  {formatAvgRating(persona_summary.avg_rating)} / 5.0
                </span>
              </div>
              <div className={styles.personaItem}>
                <span className={styles.personaKey}>Tone</span>
                <span className={styles.personaValue}>{persona_summary.tone}</span>
              </div>
              <div className={styles.personaItem}>
                <span className={styles.personaKey}>Sentiment</span>
                <span className={styles.personaValue}>
                  {persona_summary.sentiment_tendency}
                </span>
              </div>
              <div className={styles.personaItem}>
                <span className={styles.personaKey}>Cold Start</span>
                <span
                  className={`${styles.coldStartBool} ${
                    persona_summary.cold_start ? styles.coldStartTrue : styles.coldStartFalse
                  }`}
                >
                  {persona_summary.cold_start ? '⚠ Yes' : '✓ No'}
                </span>
              </div>
              {persona_summary.top_categories.length > 0 && (
                <div className={styles.personaItem} style={{ gridColumn: '1 / -1' }}>
                  <span className={styles.personaKey}>Top Categories</span>
                  <span className={styles.personaValue}>
                    {formatCategories(persona_summary.top_categories)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
);

ReviewResult.displayName = 'ReviewResult';
