import styles from './StarRating.module.css';

interface StarRatingProps {
  rating: number; // 1–5
  showNumeric?: boolean;
}

export function StarRating({ rating, showNumeric = true }: StarRatingProps) {
  const clampedRating = Math.min(5, Math.max(1, Math.round(rating)));

  return (
    <div
      className={styles.wrapper}
      role="img"
      aria-label={`Rating: ${clampedRating} out of 5 stars`}
    >
      <span className={styles.stars}>
        {Array.from({ length: 5 }, (_, i) => {
          const filled = i < clampedRating;
          return (
            <span
              key={i}
              className={`${styles.star} ${filled ? styles.starFilled : styles.starEmpty}`}
              data-testid={filled ? 'star-filled' : 'star-empty'}
              aria-hidden="true"
            >
              {filled ? '★' : '☆'}
            </span>
          );
        })}
      </span>
      {showNumeric && (
        <span className={styles.numeric} aria-hidden="true">
          {clampedRating}/5
        </span>
      )}
    </div>
  );
}
