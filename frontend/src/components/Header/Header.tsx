import { NavTabs } from '../NavTabs/NavTabs';
import styles from './Header.module.css';

export function Header() {
  return (
    <header className={styles.header} role="banner">
      <div className={styles.inner}>
        <div className={styles.brand}>
          <span className={styles.logo} aria-hidden="true">🍛</span>
          <h1 className={styles.title}>
            Jollof <span className={styles.titleAccent}>Intelligence</span>
          </h1>
        </div>
        <p className={styles.tagline}>
          Your Naija Book Oracle — E go sweet you, I promise!
        </p>
        <NavTabs />
      </div>
    </header>
  );
}
