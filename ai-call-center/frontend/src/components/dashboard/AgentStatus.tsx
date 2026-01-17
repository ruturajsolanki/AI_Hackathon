import { Brain, Eye, ArrowUpRight, Activity } from 'lucide-react'
import { Badge } from '../common/Badge'
import styles from './AgentStatus.module.css'

const agents = [
  {
    name: 'Primary Agent',
    icon: Brain,
    status: 'processing',
    decisions: 847,
    avgConfidence: 0.86,
    description: 'Handles initial customer interactions',
  },
  {
    name: 'Supervisor Agent',
    icon: Eye,
    status: 'reviewing',
    decisions: 423,
    avgConfidence: 0.92,
    description: 'Reviews and validates decisions',
  },
  {
    name: 'Escalation Agent',
    icon: ArrowUpRight,
    status: 'idle',
    decisions: 54,
    avgConfidence: 0.94,
    description: 'Determines escalation paths',
  },
]

export function AgentStatus() {
  return (
    <div className={styles.grid}>
      {agents.map((agent) => {
        const Icon = agent.icon
        const statusVariant = 
          agent.status === 'processing' ? 'success' : 
          agent.status === 'reviewing' ? 'info' : 'neutral'
        
        return (
          <div key={agent.name} className={styles.agent}>
            <div className={styles.header}>
              <div className={styles.iconWrapper}>
                <Icon size={20} />
              </div>
              <div className={styles.info}>
                <span className={styles.name}>{agent.name}</span>
                <span className={styles.description}>{agent.description}</span>
              </div>
              <Badge variant={statusVariant}>{agent.status}</Badge>
            </div>
            
            <div className={styles.stats}>
              <div className={styles.stat}>
                <Activity size={14} />
                <span className={styles.statValue}>{agent.decisions.toLocaleString()}</span>
                <span className={styles.statLabel}>decisions</span>
              </div>
              <div className={styles.stat}>
                <span className={styles.statValue}>{(agent.avgConfidence * 100).toFixed(0)}%</span>
                <span className={styles.statLabel}>avg confidence</span>
              </div>
            </div>
            
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill} 
                style={{ width: `${agent.avgConfidence * 100}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
