import styles from './ColdStartBadge.module.css';

interface ColdStartBadgeProps {
  feature: 'review' | 'recommend';
}

const COPY: Record<ColdStartBadgeProps['feature'], string> = {
  review:
    'This review was generated without prior reading history for this user. ' +
    'The result is based on the book details you provided.',
  recommend:
    'These recommendations were generated without prior reading history for this user. ' +
    'Results are based on the context you provided.',
};

export function ColdStartBadge({ feature }: ColdStartBadgeProps) {
  return (
    <div className={styles.badge} role="note" aria-label="Cold start notice">
      <span className={styles.icon} aria-hidden="true">ℹ️</span>
      <p className={styles.text}>
        <strong>No reading history found.</strong> {COPY[feature]}
      </p>
    </div>
  );
}
