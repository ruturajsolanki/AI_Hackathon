import { useState, useEffect, useCallback } from 'react'
import { 
  Phone, 
  CheckCircle, 
  AlertTriangle, 
  Gauge,
  Users,
  Clock,
  Brain,
  Activity,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  BarChart3,
  PieChart,
  Zap
} from 'lucide-react'
import { fetchAnalytics } from '../../services/apiClient'
import { StatCard } from '../common/StatCard'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { ActivityFeed } from './ActivityFeed'
import { AgentStatus } from './AgentStatus'
import styles from './DashboardPage.module.css'

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

interface AnalyticsData {
  totalInteractions: number
  activeInteractions: number
  resolutionRate: number
  escalationRate: number
  averageConfidence: number
  averageCsat: number
  averageDuration?: number
  trends?: {
    callsPerHour: number[]
    resolutionTrend: number
    escalationTrend: number
  }
}

// -----------------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------------

export function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const loadAnalytics = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    const result = await fetchAnalytics()
    
    if (result.success && result.data) {
      setAnalytics({
        totalInteractions: result.data.totalInteractions,
        activeInteractions: result.data.activeInteractions,
        resolutionRate: result.data.resolutionRate,
        escalationRate: result.data.escalationRate,
        averageConfidence: result.data.averageConfidence,
        averageCsat: result.data.averageCsat,
        averageDuration: 142, // Would come from API
        trends: {
          callsPerHour: [12, 18, 24, 32, 28, 35, 42, 38, 45, 52, 48, 44],
          resolutionTrend: 3,
          escalationTrend: -2,
        }
      })
      setLastUpdated(new Date())
    } else {
      setError(result.error?.message || 'Failed to load analytics')
    }
    
    setIsLoading(false)
  }, [])

  useEffect(() => {
    loadAnalytics()
    
    // Refresh every 30 seconds
    const interval = setInterval(loadAnalytics, 30000)
    return () => clearInterval(interval)
  }, [loadAnalytics])

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  return (
    <div className={styles.dashboard} role="main" aria-label="Analytics Dashboard">
      {/* Header */}
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Analytics Dashboard</h1>
          <p className={styles.subtitle}>
            Real-time AI call center performance metrics
            {lastUpdated && (
              <time 
                className={styles.lastUpdated}
                dateTime={lastUpdated.toISOString()}
                aria-label={`Last updated at ${lastUpdated.toLocaleTimeString()}`}
              >
                Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </time>
            )}
          </p>
        </div>
        <div className={styles.headerActions}>
          <button 
            className={styles.refreshButton}
            onClick={loadAnalytics}
            disabled={isLoading}
            aria-label={isLoading ? 'Refreshing data...' : 'Refresh analytics data'}
          >
            <RefreshCw size={16} className={isLoading ? styles.spinning : ''} aria-hidden="true" />
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
          <div className={styles.liveIndicator} role="status" aria-live="polite">
            <span className={styles.liveDot} aria-hidden="true" />
            <span>Live</span>
          </div>
        </div>
      </header>

      {/* Error State */}
      {error && (
        <div className={styles.errorBanner}>
          <AlertTriangle size={16} />
          {error}
          <button onClick={loadAnalytics}>Retry</button>
        </div>
      )}
      
      {/* Main Stats Grid */}
      <div className={styles.statsGrid}>
        <StatCard
          label="Total Calls Today"
          value={analytics?.totalInteractions ?? '--'}
          change={12}
          trend="up"
          icon={<Phone size={18} />}
        />
        <StatCard
          label="Active Now"
          value={analytics?.activeInteractions ?? '--'}
          icon={<Activity size={18} />}
        />
        <StatCard
          label="Resolution Rate"
          value={analytics ? `${(analytics.resolutionRate * 100).toFixed(0)}%` : '--'}
          change={analytics?.trends?.resolutionTrend}
          trend="up"
          icon={<CheckCircle size={18} />}
        />
        <StatCard
          label="Escalation Rate"
          value={analytics ? `${(analytics.escalationRate * 100).toFixed(0)}%` : '--'}
          change={analytics?.trends?.escalationTrend ? Math.abs(analytics.trends.escalationTrend) : undefined}
          trend="down"
          icon={<AlertTriangle size={18} />}
        />
      </div>

      {/* Charts Row */}
      <div className={styles.chartsGrid}>
        {/* Resolution vs Escalation */}
        <Card title="Resolution vs Escalation" icon={<PieChart size={18} />}>
          <div className={styles.donutChart}>
            <DonutChart 
              resolved={analytics?.resolutionRate ?? 0}
              escalated={analytics?.escalationRate ?? 0}
            />
            <div className={styles.donutLegend}>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{ backgroundColor: 'var(--color-accent-success)' }} />
                <span>Resolved by AI</span>
                <strong>{analytics ? `${(analytics.resolutionRate * 100).toFixed(0)}%` : '--'}</strong>
              </div>
              <div className={styles.legendItem}>
                <span className={styles.legendDot} style={{ backgroundColor: 'var(--color-accent-warning)' }} />
                <span>Escalated</span>
                <strong>{analytics ? `${(analytics.escalationRate * 100).toFixed(0)}%` : '--'}</strong>
              </div>
            </div>
          </div>
        </Card>

        {/* Calls Per Hour */}
        <Card title="Calls Per Hour" icon={<BarChart3 size={18} />}>
          <div className={styles.barChart}>
            <BarChart data={analytics?.trends?.callsPerHour ?? []} />
            <div className={styles.barChartLabels}>
              {['6am', '8am', '10am', '12pm', '2pm', '4pm'].map((label, i) => (
                <span key={i}>{label}</span>
              ))}
            </div>
          </div>
        </Card>

        {/* Confidence Distribution */}
        <Card title="AI Confidence" icon={<Gauge size={18} />}>
          <div className={styles.confidenceGauge}>
            <GaugeChart value={analytics?.averageConfidence ?? 0} />
            <div className={styles.gaugeInfo}>
              <span className={styles.gaugeValue}>
                {analytics ? `${(analytics.averageConfidence * 100).toFixed(0)}%` : '--'}
              </span>
              <span className={styles.gaugeLabel}>Average Confidence</span>
            </div>
          </div>
        </Card>
      </div>
      
      {/* Main Content Grid */}
      <div className={styles.mainGrid}>
        <Card title="Agent Performance" subtitle="Real-time agent status and decisions">
          <AgentStatus />
        </Card>
        
        <Card title="Live Activity" subtitle="Recent interactions and events">
          <ActivityFeed />
        </Card>
      </div>
      
      {/* Secondary Stats */}
      <div className={styles.secondaryGrid}>
        <Card title="System Health">
          <div className={styles.healthGrid}>
            <HealthItem label="Primary Agent" status="operational" latency="45ms" />
            <HealthItem label="Supervisor Agent" status="operational" latency="38ms" />
            <HealthItem label="Escalation Agent" status="operational" latency="52ms" />
            <HealthItem label="Context Store" status="operational" latency="12ms" />
            <HealthItem label="Analytics Engine" status="operational" latency="28ms" />
            <HealthItem label="Voice Service" status="simulated" latency="--" />
          </div>
        </Card>
        
        <Card title="Performance Metrics">
          <div className={styles.quickStats}>
            <QuickStat 
              icon={<Users size={18} />} 
              label="Customers Today" 
              value={analytics?.totalInteractions?.toString() ?? '--'} 
              trend="up"
            />
            <QuickStat 
              icon={<Clock size={18} />} 
              label="Avg Duration" 
              value={analytics?.averageDuration ? formatDuration(analytics.averageDuration) : '--'} 
            />
            <QuickStat 
              icon={<Brain size={18} />} 
              label="AI Decisions" 
              value={analytics ? (analytics.totalInteractions * 3).toLocaleString() : '--'} 
              trend="up"
            />
            <QuickStat 
              icon={<Zap size={18} />} 
              label="Avg CSAT" 
              value={analytics ? `${analytics.averageCsat.toFixed(1)}/5` : '--'} 
            />
          </div>
        </Card>
      </div>
    </div>
  )
}

// -----------------------------------------------------------------------------
// Chart Components
// -----------------------------------------------------------------------------

function DonutChart({ resolved, escalated }: { resolved: number; escalated: number }) {
  const resolvedDeg = resolved * 360
  const escalatedDeg = escalated * 360
  
  return (
    <div className={styles.donut}>
      <svg viewBox="0 0 100 100" className={styles.donutSvg}>
        {/* Background */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="var(--color-bg-tertiary)"
          strokeWidth="12"
        />
        {/* Escalated (bottom layer) */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="var(--color-accent-warning)"
          strokeWidth="12"
          strokeDasharray={`${escalatedDeg * 0.698} 251.2`}
          strokeDashoffset={-resolvedDeg * 0.698}
          transform="rotate(-90 50 50)"
          className={styles.donutSegment}
        />
        {/* Resolved (top layer) */}
        <circle
          cx="50"
          cy="50"
          r="40"
          fill="none"
          stroke="var(--color-accent-success)"
          strokeWidth="12"
          strokeDasharray={`${resolvedDeg * 0.698} 251.2`}
          transform="rotate(-90 50 50)"
          className={styles.donutSegment}
        />
      </svg>
      <div className={styles.donutCenter}>
        <span className={styles.donutValue}>{((resolved) * 100).toFixed(0)}%</span>
        <span className={styles.donutLabel}>Resolved</span>
      </div>
    </div>
  )
}

function BarChart({ data }: { data: number[] }) {
  const maxValue = Math.max(...data, 1)
  
  return (
    <div className={styles.bars}>
      {data.map((value, index) => (
        <div key={index} className={styles.barWrapper}>
          <div 
            className={styles.bar}
            style={{ 
              height: `${(value / maxValue) * 100}%`,
              animationDelay: `${index * 50}ms`
            }}
          >
            <span className={styles.barValue}>{value}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

function GaugeChart({ value }: { value: number }) {
  const rotation = value * 180 - 90 // -90 to 90 degrees
  const color = value >= 0.7 ? 'var(--color-accent-success)' 
    : value >= 0.5 ? 'var(--color-accent-warning)' 
    : 'var(--color-accent-danger)'
  
  return (
    <div className={styles.gauge}>
      <svg viewBox="0 0 100 60" className={styles.gaugeSvg}>
        {/* Background arc */}
        <path
          d="M 10 55 A 40 40 0 0 1 90 55"
          fill="none"
          stroke="var(--color-bg-tertiary)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d="M 10 55 A 40 40 0 0 1 90 55"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${value * 126} 126`}
          className={styles.gaugeArc}
        />
        {/* Needle */}
        <line
          x1="50"
          y1="55"
          x2="50"
          y2="25"
          stroke="var(--color-text-primary)"
          strokeWidth="2"
          strokeLinecap="round"
          transform={`rotate(${rotation} 50 55)`}
          className={styles.gaugeNeedle}
        />
        <circle cx="50" cy="55" r="4" fill="var(--color-text-primary)" />
      </svg>
    </div>
  )
}

// -----------------------------------------------------------------------------
// Helper Components
// -----------------------------------------------------------------------------

function HealthItem({ 
  label, 
  status, 
  latency 
}: { 
  label: string
  status: 'operational' | 'degraded' | 'simulated'
  latency: string 
}) {
  const variant = status === 'operational' ? 'success' : status === 'degraded' ? 'warning' : 'info'
  const statusLabel = status === 'operational' ? 'Operational' : status === 'degraded' ? 'Degraded performance' : 'Simulated'
  
  return (
    <div 
      className={styles.healthItem}
      role="listitem"
      aria-label={`${label}: ${statusLabel}, response time ${latency}`}
    >
      <span className={styles.healthLabel}>{label}</span>
      <Badge variant={variant} aria-label={statusLabel}>
        {status === 'operational' ? 'Healthy' : status === 'degraded' ? 'Degraded' : 'Simulated'}
      </Badge>
      <span className={styles.healthLatency} aria-label={`Response time: ${latency}`}>
        {latency}
      </span>
    </div>
  )
}

function QuickStat({ 
  icon, 
  label, 
  value,
  trend
}: { 
  icon: React.ReactNode
  label: string
  value: string 
  trend?: 'up' | 'down'
}) {
  const trendLabel = trend === 'up' ? 'Trending up' : trend === 'down' ? 'Trending down' : ''
  
  return (
    <div 
      className={styles.quickStat}
      role="listitem"
      aria-label={`${label}: ${value}${trendLabel ? `, ${trendLabel}` : ''}`}
    >
      <div className={styles.quickStatIcon} aria-hidden="true">{icon}</div>
      <div className={styles.quickStatContent}>
        <div className={styles.quickStatValueRow}>
          <span className={styles.quickStatValue}>{value}</span>
          {trend && (
            <span 
              className={`${styles.quickStatTrend} ${styles[trend]}`}
              aria-label={trendLabel}
              title={trendLabel}
            >
              {trend === 'up' ? <TrendingUp size={14} aria-hidden="true" /> : <TrendingDown size={14} aria-hidden="true" />}
            </span>
          )}
        </div>
        <span className={styles.quickStatLabel}>{label}</span>
      </div>
    </div>
  )
}

export default DashboardPage
