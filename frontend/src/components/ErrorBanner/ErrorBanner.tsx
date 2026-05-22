import { useEffect } from 'react';
import styles from './ErrorBanner.module.css';

interface ErrorBannerProps {
  message: string;
  onRetry: () => void;
  liveRegionId?: string;
}

export function ErrorBanner({ message, onRetry, liveRegionId }: ErrorBannerProps) {
  // Write message into the ARIA live region on mount so screen readers announce it
  useEffect(() => {
    if (!liveRegionId) return;
    const region = document.getElementById(liveRegionId);
    if (region) {
      region.textContent = message;
    }
    return () => {
      if (region) region.textContent = '';
    };
  }, [message, liveRegionId]);

  return (
    <div className={styles.banner} role="alert">
      <span className={styles.icon} aria-hidden="true">⚠️</span>
      <div className={styles.content}>
        <p className={styles.message}>{message}</p>
        <button
          type="button"
          className={styles.retryButton}
          onClick={onRetry}
          aria-label="Retry the request"
        >
          ↺ Retry
        </button>
      </div>
    </div>
  );
}
