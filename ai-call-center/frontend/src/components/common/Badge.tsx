import type { BadgeProps } from '../../types'
import styles from './Badge.module.css'

interface ExtendedBadgeProps extends BadgeProps {
  /** Accessible label for the badge */
  'aria-label'?: string
}

export function Badge({ variant, children, 'aria-label': ariaLabel }: ExtendedBadgeProps) {
  return (
    <span 
      className={`${styles.badge} ${styles[variant]}`}
      role="status"
      aria-label={ariaLabel}
    >
      {children}
    </span>
  )
}
