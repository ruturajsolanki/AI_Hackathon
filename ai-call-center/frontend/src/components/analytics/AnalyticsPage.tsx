/**
 * Analytics Dashboard Page
 * 
 * Displays key metrics, trends, and breakdowns.
 * Clean SaaS layout optimized for judge demonstrations.
 */

import { useEffect, useState } from 'react'
import {
  fetchAnalyticsOverview,
  fetchAnalyticsTrends,
  AnalyticsOverviewResponse,
  AnalyticsTrendsResponse,
  DailyTrendItem,
} from '../../services/apiClient'
import styles from './AnalyticsPage.module.css'

export function AnalyticsPage() {
  const [overview, setOverview] = useState<AnalyticsOverviewResponse | null>(null)
  const [trends, setTrends] = useState<AnalyticsTrendsResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(7)

  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true)
      setError(null)

      const [overviewResult, trendsResult] = await Promise.all([
        fetchAnalyticsOverview(days),
        fetchAnalyticsTrends(days),
      ])

      if (overviewResult.success && overviewResult.data) {
        setOverview(overviewResult.data)
      } else {
        setError(overviewResult.error?.message || 'Failed to load analytics')
      }

      if (trendsResult.success && trendsResult.data) {
        setTrends(trendsResult.data)
      }

      setIsLoading(false)
    }

    loadData()
  }, [days])

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loadingContainer}>
          <div className={styles.spinner} />
          <span>Loading analytics...</span>
        </div>
      </div>
    )
  }

  if (error || !overview) {
    return (
      <div className={styles.container}>
        <div className={styles.errorContainer}>
          <span className={styles.errorIcon}>⚠️</span>
          <h2>Failed to load analytics</h2>
          <p>{error || 'No data available'}</p>
        </div>
      </div>
    )
  }

  const { summary } = overview

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerText}>
          <h1>Analytics</h1>
          <p>AI call center performance metrics and insights</p>
        </div>
        <div className={styles.periodSelector}>
          <button 
            className={`${styles.periodBtn} ${days === 7 ? styles.active : ''}`}
            onClick={() => setDays(7)}
          >
            7 Days
          </button>
          <button 
            className={`${styles.periodBtn} ${days === 14 ? styles.active : ''}`}
            onClick={() => setDays(14)}
          >
            14 Days
          </button>
          <button 
            className={`${styles.periodBtn} ${days === 30 ? styles.active : ''}`}
            onClick={() => setDays(30)}
          >
            30 Days
          </button>
        </div>
      </header>

      {/* Metrics Grid */}
      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={`${styles.metricIcon} ${styles.metricIconBlue}`}>📞</div>
            <span className={`${styles.metricTrend} ${styles.trendNeutral}`}>Last {days} days</span>
          </div>
          <div className={styles.metricValue}>{summary.totalInteractions}</div>
          <div className={styles.metricLabel}>Total Calls</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={`${styles.metricIcon} ${styles.metricIconGreen}`}>✓</div>
            <span className={`${styles.metricTrend} ${styles.trendUp}`}>
              {formatPercentage(summary.resolutionRate)}
            </span>
          </div>
          <div className={styles.metricValue}>{summary.resolvedCount}</div>
          <div className={styles.metricLabel}>Resolved by AI</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={`${styles.metricIcon} ${styles.metricIconOrange}`}>↗</div>
            <span className={`${styles.metricTrend} ${styles.trendDown}`}>
              {formatPercentage(summary.escalationRate)}
            </span>
          </div>
          <div className={styles.metricValue}>{summary.escalatedCount}</div>
          <div className={styles.metricLabel}>Escalated</div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricHeader}>
            <div className={`${styles.metricIcon} ${styles.metricIconPurple}`}>⏱</div>
          </div>
          <div className={styles.metricValue}>{formatDuration(summary.averageDurationSeconds)}</div>
          <div className={styles.metricLabel}>Avg Duration</div>
        </div>
      </div>

      {/* Charts Section */}
      <div className={styles.chartsSection}>
        {/* Call Volume Trend */}
        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Call Volume Trend</h3>
          <div className={styles.chartArea}>
            {trends?.dailyTrends && trends.dailyTrends.length > 0 ? (
              trends.dailyTrends.map((day, i) => (
                <BarGroup key={i} day={day} maxCalls={Math.max(...trends.dailyTrends.map(d => d.totalCalls))} />
              ))
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100%', color: 'rgba(255,255,255,0.4)' }}>
                No trend data available
              </div>
            )}
          </div>
        </div>

        {/* Resolution Distribution */}
        <div className={styles.chartCard}>
          <h3 className={styles.chartTitle}>Resolution Distribution</h3>
          <div className={styles.donutContainer}>
            <DonutChart 
              resolved={summary.resolvedCount} 
              escalated={summary.escalatedCount}
              other={summary.totalInteractions - summary.resolvedCount - summary.escalatedCount}
            />
            <div className={styles.donutLegend}>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: '#10b981' }} />
                <span className={styles.legendText}>Resolved</span>
              </div>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: '#f59e0b' }} />
                <span className={styles.legendText}>Escalated</span>
              </div>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{ background: '#6366f1' }} />
                <span className={styles.legendText}>In Progress</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Table */}
      <div className={styles.tableSection}>
        <h3 className={styles.tableTitle}>Agent Performance Summary</h3>
        <table className={styles.simpleTable}>
          <thead>
            <tr>
              <th>Agent</th>
              <th>Decisions</th>
              <th>Avg Confidence</th>
              <th>Avg Time</th>
            </tr>
          </thead>
          <tbody>
            {overview.agentPerformance.map((agent, i) => (
              <tr key={i}>
                <td>{agent.agentType}</td>
                <td>{agent.totalDecisions}</td>
                <td>{formatPercentage(agent.averageConfidence)}</td>
                <td>{agent.averageProcessingTime}ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Bar chart component
function BarGroup({ day, maxCalls }: { day: DailyTrendItem; maxCalls: number }) {
  const height = maxCalls > 0 ? (day.totalCalls / maxCalls) * 180 : 0
  const date = new Date(day.date)
  const label = new Intl.DateTimeFormat('en-US', { weekday: 'short' }).format(date)

  return (
    <div className={styles.barGroup}>
      <div 
        className={styles.bar} 
        style={{ height: `${Math.max(height, 4)}px` }}
        title={`${day.totalCalls} calls`}
      />
      <span className={styles.barLabel}>{label}</span>
    </div>
  )
}

// Donut chart component
function DonutChart({ resolved, escalated, other }: { resolved: number; escalated: number; other: number }) {
  const total = resolved + escalated + other
  if (total === 0) {
    return (
      <div className={styles.donutChart}>
        <svg width="160" height="160" viewBox="0 0 160 160">
          <circle cx="80" cy="80" r="60" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="20" />
        </svg>
        <div className={styles.donutCenter}>
          <span className={styles.donutValue}>0</span>
          <span className={styles.donutLabel}>calls</span>
        </div>
      </div>
    )
  }

  const resolvedPct = (resolved / total) * 100
  const escalatedPct = (escalated / total) * 100
  
  // Calculate stroke dash arrays for donut segments
  const circumference = 2 * Math.PI * 60
  const resolvedDash = (resolvedPct / 100) * circumference
  const escalatedDash = (escalatedPct / 100) * circumference
  const otherDash = circumference - resolvedDash - escalatedDash

  return (
    <div className={styles.donutChart}>
      <svg width="160" height="160" viewBox="0 0 160 160">
        {/* Resolved */}
        <circle 
          cx="80" cy="80" r="60" 
          fill="none" 
          stroke="#10b981" 
          strokeWidth="20"
          strokeDasharray={`${resolvedDash} ${circumference - resolvedDash}`}
          strokeDashoffset="0"
        />
        {/* Escalated */}
        <circle 
          cx="80" cy="80" r="60" 
          fill="none" 
          stroke="#f59e0b" 
          strokeWidth="20"
          strokeDasharray={`${escalatedDash} ${circumference - escalatedDash}`}
          strokeDashoffset={-resolvedDash}
        />
        {/* Other */}
        <circle 
          cx="80" cy="80" r="60" 
          fill="none" 
          stroke="#6366f1" 
          strokeWidth="20"
          strokeDasharray={`${otherDash} ${circumference - otherDash}`}
          strokeDashoffset={-(resolvedDash + escalatedDash)}
        />
      </svg>
      <div className={styles.donutCenter}>
        <span className={styles.donutValue}>{total}</span>
        <span className={styles.donutLabel}>calls</span>
      </div>
    </div>
  )
}
