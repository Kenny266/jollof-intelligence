import styles from './LoadingSpinner.module.css';

interface LoadingSpinnerProps {
  label?: string;
}

export function LoadingSpinner({ label = 'Loading…' }: LoadingSpinnerProps) {
  return (
    <div className={styles.wrapper}>
      <div
        className={styles.spinner}
        role="status"
        aria-label={label}
      />
      <span className={styles.label} aria-hidden="true">
        {label}
      </span>
    </div>
  );
}
