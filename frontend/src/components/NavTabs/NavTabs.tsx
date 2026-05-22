import { NavLink } from 'react-router-dom';
import styles from './NavTabs.module.css';

const TABS = [
  { to: '/review', label: 'Book Review Simulator', icon: '✍️' },
  { to: '/recommend', label: 'Book Recommender', icon: '📚' },
] as const;

export function NavTabs() {
  return (
    <nav aria-label="Main navigation" className={styles.nav} role="navigation">
      {TABS.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) =>
            `${styles.tab} ${isActive ? styles.tabActive : ''}`
          }
          aria-label={label}
          end
        >
          {({ isActive }) => (
            <>
              <span
                className={styles.tabIcon}
                aria-hidden="true"
              >
                {icon}
              </span>
              <span aria-current={isActive ? 'page' : undefined}>
                {label}
              </span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
