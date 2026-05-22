import { forwardRef } from 'react';
import type { Recommendation } from '../../types/api';
import { formatScore } from '../../utils/formatters';
import styles from './RecommendationCard.module.css';

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export const RecommendationCard = forwardRef<HTMLDivElement, RecommendationCardProps>(
  ({ recommendation }, ref) => {
    const { title, author, categories, price, score, reason } = recommendation;

    return (
      <div className={styles.card} ref={ref} tabIndex={-1}>
        <div className={styles.cardHeader}>
          <div className={styles.titleBlock}>
            <h3 className={styles.title}>{title}</h3>
            <p className={styles.author}>by {author}</p>
          </div>
          <span className={styles.scoreBadge} aria-label={`Relevance score: ${formatScore(score)}`}>
            {formatScore(score)}
          </span>
        </div>

        <div className={styles.meta}>
          {categories && (
            <span className={styles.metaTag}>📂 {categories}</span>
          )}
          {price && (
            <span className={styles.metaTag}>💰 ${price}</span>
          )}
        </div>

        <p className={styles.reason}>
          <span className={styles.reasonLabel}>Why this book:</span>
          {reason}
        </p>
      </div>
    );
  }
);

RecommendationCard.displayName = 'RecommendationCard';
