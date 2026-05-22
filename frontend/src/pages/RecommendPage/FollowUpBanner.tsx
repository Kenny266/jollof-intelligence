import styles from './FollowUpBanner.module.css';

interface FollowUpBannerProps {
  followUp: string;
}

export function FollowUpBanner({ followUp }: FollowUpBannerProps) {
  if (!followUp) return null;

  return (
    <div className={styles.banner} role="note" aria-label="Follow-up question">
      <span className={styles.icon} aria-hidden="true">💬</span>
      <div className={styles.text}>
        <span className={styles.label}>The oracle wants to know:</span>
        {followUp}
      </div>
    </div>
  );
}
