import { 
  Phone, 
  CheckCircle, 
  AlertTriangle, 
  Gauge,
  Users,
  Clock,
  Brain,
  Activity
} from 'lucide-react'
import { StatCard } from '../common/StatCard'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { ActivityFeed } from './ActivityFeed'
import { AgentStatus } from './AgentStatus'
import styles from './DashboardPage.module.css'

// Simulated metrics for demo
const metrics = {
  activeInteractions: 12,
  resolutionRate: 87,
  escalationRate: 13,
  averageConfidence: 0.84,
  averageCsat: 4.2,
  averageDuration: 142,
}

export function DashboardPage() {
  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Dashboard</h1>
          <p className={styles.subtitle}>Real-time overview of AI call center operations</p>
        </div>
        <div className={styles.liveIndicator}>
          <span className={styles.liveDot} />
          <span>Live</span>
        </div>
      </div>
      
      <div className={styles.statsGrid}>
        <StatCard
          label="Active Interactions"
          value={metrics.activeInteractions}
          change={8}
          trend="up"
          icon={<Phone size={18} />}
        />
        <StatCard
          label="Resolution Rate"
          value={`${metrics.resolutionRate}%`}
          change={3}
          trend="up"
          icon={<CheckCircle size={18} />}
        />
        <StatCard
          label="Escalation Rate"
          value={`${metrics.escalationRate}%`}
          change={2}
          trend="down"
          icon={<AlertTriangle size={18} />}
        />
        <StatCard
          label="Avg Confidence"
          value={`${(metrics.averageConfidence * 100).toFixed(0)}%`}
          change={1}
          trend="up"
          icon={<Gauge size={18} />}
        />
      </div>
      
      <div className={styles.mainGrid}>
        <Card title="Agent Performance" subtitle="Real-time agent status and decisions">
          <AgentStatus />
        </Card>
        
        <Card title="Live Activity" subtitle="Recent interactions and events">
          <ActivityFeed />
        </Card>
      </div>
      
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
        
        <Card title="Quick Stats">
          <div className={styles.quickStats}>
            <QuickStat icon={<Users size={18} />} label="Customers Today" value="347" />
            <QuickStat icon={<Clock size={18} />} label="Avg Duration" value="2m 22s" />
            <QuickStat icon={<Brain size={18} />} label="AI Decisions" value="1,284" />
            <QuickStat icon={<Activity size={18} />} label="Avg CSAT" value="4.2/5" />
          </div>
        </Card>
      </div>
    </div>
  )
}

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
  
  return (
    <div className={styles.healthItem}>
      <span className={styles.healthLabel}>{label}</span>
      <Badge variant={variant}>{status}</Badge>
      <span className={styles.healthLatency}>{latency}</span>
    </div>
  )
}

function QuickStat({ 
  icon, 
  label, 
  value 
}: { 
  icon: React.ReactNode
  label: string
  value: string 
}) {
  return (
    <div className={styles.quickStat}>
      <div className={styles.quickStatIcon}>{icon}</div>
      <div className={styles.quickStatContent}>
        <span className={styles.quickStatValue}>{value}</span>
        <span className={styles.quickStatLabel}>{label}</span>
      </div>
    </div>
  )
}
