import React from 'react';
import styles from './EmptyState.module.css';

/**
 * Reusable empty state component.
 *
 * Props:
 *   icon      — Lucide icon component (e.g. FolderOpen)
 *   title     — Main heading string
 *   hint      — Optional secondary text
 *   action    — Optional { label: string, onClick: fn }
 *   size      — 'sm' | 'md' | 'lg' (default: 'md')
 */
export default function EmptyState({ icon: Icon, title, hint, action, size = 'md' }) {
  return (
    <div className={`${styles.root} ${styles[size]}`}>
      {Icon && (
        <div className={styles.iconWrap}>
          <Icon className={styles.icon} />
        </div>
      )}
      <p className={styles.title}>{title}</p>
      {hint && <p className={styles.hint}>{hint}</p>}
      {action && (
        <button className={styles.action} onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
}
