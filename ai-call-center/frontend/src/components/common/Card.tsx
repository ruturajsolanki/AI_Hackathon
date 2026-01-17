import type { CardProps } from '../../types'
import styles from './Card.module.css'

interface ExtendedCardProps extends CardProps {
  /** Optional icon to display in header */
  icon?: React.ReactNode
}

export function Card({ title, subtitle, icon, children, className = '' }: ExtendedCardProps) {
  return (
    <section 
      className={`${styles.card} ${className}`}
      aria-labelledby={title ? `card-${title.toLowerCase().replace(/\s+/g, '-')}` : undefined}
    >
      {(title || subtitle) && (
        <header className={styles.header}>
          <div className={styles.headerContent}>
            {icon && <span className={styles.headerIcon} aria-hidden="true">{icon}</span>}
            <div className={styles.headerText}>
              {title && (
                <h3 
                  className={styles.title}
                  id={`card-${title.toLowerCase().replace(/\s+/g, '-')}`}
                >
                  {title}
                </h3>
              )}
              {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
            </div>
          </div>
        </header>
      )}
      <div className={styles.content}>
        {children}
      </div>
    </section>
  )
}
