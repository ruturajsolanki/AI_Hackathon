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
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <span>Loading analytics...</span>
      </div>
    )
  }

  if (error || !overview) {
    return (
      <div className={styles.errorContainer}>
        <span className={styles.errorIcon}>⚠️</span>
        <h2>Failed to load analytics</h2>
        <p>{error || 'No data available'}</p>
      </div>
    )
  }

  const { summary } = overview

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Analytics Dashboard</h1>
          <p className={styles.subtitle}>
            AI Call Center performance metrics and insights
          </p>
        </div>
        <div className={styles.periodSelector}>
          <label htmlFor="period">Period:</label>
          <select
            id="period"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className={styles.select}
          >
            <option value={7}>Last 7 days</option>
            <option value={14}>Last 14 days</option>
            <option value={30}>Last 30 days</option>
          </select>
        </div>
      </header>

      {/* Key Metrics Cards */}
      <section className={styles.metricsSection}>
        <h2 className={styles.sectionTitle}>Key Metrics</h2>
        <div className={styles.metricsGrid}>
          <MetricCard
            label="Total Calls"
            value={summary.totalInteractions}
            icon="📞"
            description="Total interactions received"
          />
          <MetricCard
            label="AI Resolution Rate"
            value={formatPercentage(summary.resolutionRate)}
            icon="✅"
            description="Resolved without human intervention"
            highlight={summary.resolutionRate > 0.7 ? 'success' : 'warning'}
          />
          <MetricCard
            label="Escalation Rate"
            value={formatPercentage(summary.escalationRate)}
            icon="⬆️"
            description="Escalated to human agents"
            highlight={summary.escalationRate < 0.3 ? 'success' : 'warning'}
          />
          <MetricCard
            label="AI Confidence"
            value={formatPercentage(summary.averageConfidence)}
            icon="🎯"
            description="Average agent confidence score"
            highlight={summary.averageConfidence > 0.7 ? 'success' : 'warning'}
          />
          <MetricCard
            label="Avg Duration"
            value={formatDuration(summary.averageDurationSeconds)}
            icon="⏱️"
            description="Average call duration"
          />
          <MetricCard
            label="Active Calls"
            value={summary.activeInteractions}
            icon="🔄"
            description="Currently in progress"
          />
        </div>
      </section>

      {/* Trend Chart */}
      {trends && trends.daily.length > 0 && (
        <section className={styles.chartSection}>
          <h2 className={styles.sectionTitle}>Call Volume Trend</h2>
          <p className={styles.chartDescription}>
            Daily call volume over the selected period
          </p>
          <TrendChart data={trends.daily} />
        </section>
      )}

      {/* Breakdowns */}
      <div className={styles.breakdownsGrid}>
        {/* Channel Breakdown */}
        <section className={styles.breakdownCard}>
          <h3 className={styles.breakdownTitle}>By Channel</h3>
          <div className={styles.breakdownList}>
            {overview.channelBreakdown.map((item) => (
              <div key={item.channel} className={styles.breakdownItem}>
                <div className={styles.breakdownLabel}>
                  <span className={styles.channelIcon}>
                    {item.channel === 'voice' ? '🎙️' : '💬'}
                  </span>
                  <span>{item.channel}</span>
                </div>
                <div className={styles.breakdownValue}>
                  <span className={styles.count}>{item.count}</span>
                  <span className={styles.percentage}>{item.percentage}%</span>
                </div>
                <div className={styles.progressBar}>
                  <div 
                    className={styles.progressFill}
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Status Breakdown */}
        <section className={styles.breakdownCard}>
          <h3 className={styles.breakdownTitle}>By Status</h3>
          <div className={styles.breakdownList}>
            {overview.statusBreakdown.map((item) => (
              <div key={item.status} className={styles.breakdownItem}>
                <div className={styles.breakdownLabel}>
                  <span className={styles.statusDot} data-status={item.status} />
                  <span>{item.status.replace(/_/g, ' ')}</span>
                </div>
                <div className={styles.breakdownValue}>
                  <span className={styles.count}>{item.count}</span>
                  <span className={styles.percentage}>{item.percentage}%</span>
                </div>
                <div className={styles.progressBar}>
                  <div 
                    className={`${styles.progressFill} ${styles[item.status]}`}
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Agent Performance */}
        <section className={styles.breakdownCard}>
          <h3 className={styles.breakdownTitle}>Agent Performance</h3>
          <div className={styles.agentList}>
            {overview.agentPerformance.map((agent) => (
              <div key={agent.agentType} className={styles.agentItem}>
                <div className={styles.agentHeader}>
                  <span className={styles.agentIcon}>
                    {agent.agentType === 'primary' ? '🤖' : 
                     agent.agentType === 'supervisor' ? '👁️' : '⚡'}
                  </span>
                  <span className={styles.agentName}>
                    {agent.agentType.charAt(0).toUpperCase() + agent.agentType.slice(1)}
                  </span>
                </div>
                <div className={styles.agentStats}>
                  <div className={styles.agentStat}>
                    <span className={styles.statValue}>{agent.totalDecisions}</span>
                    <span className={styles.statLabel}>Decisions</span>
                  </div>
                  <div className={styles.agentStat}>
                    <span className={styles.statValue}>
                      {(agent.averageConfidence * 100).toFixed(0)}%
                    </span>
                    <span className={styles.statLabel}>Confidence</span>
                  </div>
                  <div className={styles.agentStat}>
                    <span className={styles.statValue}>{agent.averageProcessingMs}ms</span>
                    <span className={styles.statLabel}>Avg Time</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {/* Hourly Distribution */}
      <section className={styles.hourlySection}>
        <h2 className={styles.sectionTitle}>Hourly Distribution</h2>
        <p className={styles.chartDescription}>
          Call volume by hour of day
        </p>
        <HourlyChart data={overview.callsPerHour} />
      </section>
    </div>
  )
}

// Metric Card Component
function MetricCard({ 
  label, 
  value, 
  icon, 
  description, 
  highlight 
}: { 
  label: string
  value: string | number
  icon: string
  description: string
  highlight?: 'success' | 'warning' | 'danger'
}) {
  return (
    <div className={`${styles.metricCard} ${highlight ? styles[highlight] : ''}`}>
      <div className={styles.metricIcon}>{icon}</div>
      <div className={styles.metricContent}>
        <span className={styles.metricValue}>{value}</span>
        <span className={styles.metricLabel}>{label}</span>
        <span className={styles.metricDescription}>{description}</span>
      </div>
    </div>
  )
}

// Simple Trend Chart Component (CSS-only)
function TrendChart({ data }: { data: DailyTrendItem[] }) {
  const maxValue = Math.max(...data.map(d => d.total), 1)
  
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return new Intl.DateTimeFormat('en-US', { 
      month: 'short', 
      day: 'numeric' 
    }).format(date)
  }

  return (
    <div className={styles.trendChart}>
      <div className={styles.chartBars}>
        {data.map((item, index) => (
          <div key={index} className={styles.barColumn}>
            <div className={styles.barContainer}>
              <div 
                className={styles.bar}
                style={{ height: `${(item.total / maxValue) * 100}%` }}
              >
                <span className={styles.barValue}>{item.total}</span>
              </div>
            </div>
            <span className={styles.barLabel}>{formatDate(item.date)}</span>
          </div>
        ))}
      </div>
      <div className={styles.chartLegend}>
        <span className={styles.legendItem}>
          <span className={styles.legendDot} /> Total Calls
        </span>
      </div>
    </div>
  )
}

// Hourly Chart Component
function HourlyChart({ data }: { data: { hour: number; count: number }[] }) {
  const maxValue = Math.max(...data.map(d => d.count), 1)
  
  const formatHour = (hour: number) => {
    if (hour === 0) return '12am'
    if (hour === 12) return '12pm'
    return hour < 12 ? `${hour}am` : `${hour - 12}pm`
  }

  return (
    <div className={styles.hourlyChart}>
      <div className={styles.hourlyBars}>
        {data.map((item) => (
          <div key={item.hour} className={styles.hourlyColumn}>
            <div 
              className={styles.hourlyBar}
              style={{ height: `${(item.count / maxValue) * 100}%` }}
              title={`${formatHour(item.hour)}: ${item.count} calls`}
            />
            {item.hour % 3 === 0 && (
              <span className={styles.hourlyLabel}>{formatHour(item.hour)}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
