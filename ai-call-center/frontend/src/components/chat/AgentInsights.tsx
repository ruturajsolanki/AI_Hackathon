import { Brain, Eye, ArrowUpRight, Activity, Shield, Zap } from 'lucide-react'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import styles from './AgentInsights.module.css'

interface Message {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  intent?: string
  emotion?: string
  confidence?: number
}

interface AgentInsightsProps {
  messages: Message[]
}

export function AgentInsights({ messages }: AgentInsightsProps) {
  const agentMessages = messages.filter(m => m.role === 'agent')
  const lastAgent = agentMessages[agentMessages.length - 1]
  
  const avgConfidence = agentMessages.length > 0
    ? agentMessages.reduce((sum, m) => sum + (m.confidence || 0), 0) / agentMessages.length
    : 0

  return (
    <div className={styles.insights}>
      <Card title="Agent Pipeline" subtitle="Real-time decision flow">
        <div className={styles.pipeline}>
          <PipelineStep
            icon={<Brain size={18} />}
            name="Primary Agent"
            status={lastAgent ? 'completed' : 'idle'}
            detail={lastAgent?.intent?.replace('_', ' ') || 'Awaiting input'}
          />
          <div className={styles.pipelineConnector} />
          <PipelineStep
            icon={<Eye size={18} />}
            name="Supervisor Review"
            status={lastAgent ? 'completed' : 'idle'}
            detail={lastAgent ? 'Approved' : 'Awaiting decision'}
          />
          <div className={styles.pipelineConnector} />
          <PipelineStep
            icon={<ArrowUpRight size={18} />}
            name="Escalation Check"
            status={lastAgent ? 'completed' : 'idle'}
            detail={lastAgent ? 'No escalation needed' : 'Awaiting evaluation'}
          />
        </div>
      </Card>
      
      <Card title="Current Analysis">
        <div className={styles.analysis}>
          <AnalysisItem
            label="Detected Intent"
            value={lastAgent?.intent?.replace('_', ' ') || 'N/A'}
            icon={<Zap size={14} />}
          />
          <AnalysisItem
            label="Emotional State"
            value={lastAgent?.emotion || 'neutral'}
            icon={<Activity size={14} />}
          />
          <AnalysisItem
            label="Confidence"
            value={lastAgent ? `${(lastAgent.confidence! * 100).toFixed(0)}%` : 'N/A'}
            icon={<Shield size={14} />}
          />
          <AnalysisItem
            label="Session Avg"
            value={avgConfidence > 0 ? `${(avgConfidence * 100).toFixed(0)}%` : 'N/A'}
            icon={<Brain size={14} />}
          />
        </div>
      </Card>
      
      <Card title="Decision Log">
        <div className={styles.log}>
          {agentMessages.length === 0 ? (
            <p className={styles.emptyLog}>No decisions yet</p>
          ) : (
            agentMessages.slice(-5).reverse().map((msg, index) => (
              <div key={msg.id} className={styles.logEntry}>
                <div className={styles.logHeader}>
                  <Badge variant={
                    (msg.confidence || 0) >= 0.8 ? 'success' :
                    (msg.confidence || 0) >= 0.6 ? 'info' : 'warning'
                  }>
                    {((msg.confidence || 0) * 100).toFixed(0)}%
                  </Badge>
                  <span className={styles.logIntent}>{msg.intent?.replace('_', ' ')}</span>
                </div>
                <p className={styles.logContent}>{msg.content.slice(0, 60)}...</p>
              </div>
            ))
          )}
        </div>
      </Card>
    </div>
  )
}

function PipelineStep({ 
  icon, 
  name, 
  status, 
  detail 
}: { 
  icon: React.ReactNode
  name: string
  status: 'idle' | 'processing' | 'completed'
  detail: string 
}) {
  return (
    <div className={`${styles.step} ${styles[status]}`}>
      <div className={styles.stepIcon}>{icon}</div>
      <div className={styles.stepInfo}>
        <span className={styles.stepName}>{name}</span>
        <span className={styles.stepDetail}>{detail}</span>
      </div>
      <Badge variant={
        status === 'completed' ? 'success' :
        status === 'processing' ? 'info' : 'neutral'
      }>
        {status}
      </Badge>
    </div>
  )
}

function AnalysisItem({ 
  label, 
  value, 
  icon 
}: { 
  label: string
  value: string
  icon: React.ReactNode 
}) {
  return (
    <div className={styles.analysisItem}>
      <div className={styles.analysisIcon}>{icon}</div>
      <div className={styles.analysisContent}>
        <span className={styles.analysisLabel}>{label}</span>
        <span className={styles.analysisValue}>{value}</span>
      </div>
    </div>
  )
}
