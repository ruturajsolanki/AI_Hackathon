import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { StatCardProps } from '../../types'
import styles from './StatCard.module.css'

export function StatCard({ label, value, change, trend = 'neutral', icon }: StatCardProps) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus
  
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.label}>{label}</span>
        {icon && <div className={styles.icon}>{icon}</div>}
      </div>
      <div className={styles.value}>{value}</div>
      {change !== undefined && (
        <div className={`${styles.change} ${styles[trend]}`}>
          <TrendIcon size={14} />
          <span>{Math.abs(change)}%</span>
          <span className={styles.period}>vs last hour</span>
        </div>
      )}
    </div>
  )
}
