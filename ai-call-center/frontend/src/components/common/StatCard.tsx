import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { StatCardProps } from '../../types'
import styles from './StatCard.module.css'

export function StatCard({ label, value, change, trend = 'neutral', icon }: StatCardProps) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  const trendLabel = trend === 'up' ? 'increased' : trend === 'down' ? 'decreased' : 'unchanged'
  
  return (
    <article className={styles.card} aria-label={`${label}: ${value}`}>
      <div className={styles.header}>
        <h3 className={styles.label}>{label}</h3>
        {icon && <div className={styles.icon} aria-hidden="true">{icon}</div>}
      </div>
      <div className={styles.value} aria-live="polite">{value}</div>
      {change !== undefined && (
        <div 
          className={`${styles.change} ${styles[trend]}`}
          aria-label={`${trendLabel} by ${Math.abs(change)} percent compared to last hour`}
        >
          <TrendIcon size={14} aria-hidden="true" />
          <span>{Math.abs(change)}%</span>
          <span className={styles.period}>vs last hour</span>
        </div>
      )}
    </article>
  )
}
