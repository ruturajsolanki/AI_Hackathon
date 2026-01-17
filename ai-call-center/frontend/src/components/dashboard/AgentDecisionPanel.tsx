import { useState } from 'react'
import { 
  Brain, 
  Eye, 
  ArrowUpRight, 
  CheckCircle, 
  XCircle,
  AlertTriangle,
  ChevronRight,
  Clock,
  Shield,
  Zap,
  MessageSquare,
  TrendingUp,
  Activity,
  Inbox
} from 'lucide-react'
import styles from './AgentDecisionPanel.module.css'

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

export interface AgentDecisionData {
  agentType: 'primary' | 'supervisor' | 'escalation'
  timestamp: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  processingTimeMs?: number
  confidence?: number
  confidenceLevel?: 'high' | 'medium' | 'low'
  summary?: string
  reasoning?: string[]
  
  // Primary Agent
  intent?: string
  emotion?: string
  responseGenerated?: boolean
  
  // Supervisor Agent
  approved?: boolean
  qualityScore?: number
  toneAppropriate?: boolean
  compliancePass?: boolean
  riskLevel?: 'none' | 'low' | 'medium' | 'high' | 'critical'
  flags?: string[]
  
  // Escalation Agent
  shouldEscalate?: boolean
  escalationType?: 'human' | 'ticket' | 'retry' | 'none'
  escalationReason?: string
  priority?: number
}

export interface PipelineState {
  phase: 'idle' | 'primary' | 'supervisor' | 'escalation' | 'complete' | 'error'
  decisions: AgentDecisionData[]
  overallConfidence?: number
  totalProcessingTime?: number
  finalOutcome?: 'respond' | 'escalate' | 'error'
}

interface AgentDecisionPanelProps {
  /** Current pipeline state with all decisions */
  pipelineState: PipelineState
  /** Show turn count */
  turnCount?: number
}

// -----------------------------------------------------------------------------
// Main Component
// -----------------------------------------------------------------------------

export function AgentDecisionPanel({ 
  pipelineState,
  turnCount = 0,
}: AgentDecisionPanelProps) {
  const { phase, decisions, overallConfidence, totalProcessingTime, finalOutcome } = pipelineState

  const primaryDecision = decisions.find(d => d.agentType === 'primary')
  const supervisorDecision = decisions.find(d => d.agentType === 'supervisor')
  const escalationDecision = decisions.find(d => d.agentType === 'escalation')

  const computedConfidence = overallConfidence 
    ?? escalationDecision?.confidence 
    ?? supervisorDecision?.confidence 
    ?? primaryDecision?.confidence 
    ?? 0

  const computedProcessingTime = totalProcessingTime 
    ?? decisions.reduce((sum, d) => sum + (d.processingTimeMs || 0), 0)

  const isIdle = phase === 'idle' && decisions.length === 0
  const hasDecisions = decisions.length > 0

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h2 className={styles.title}>Agent Decision Pipeline</h2>
          <p className={styles.subtitle}>
            {isIdle ? 'Waiting for interaction...' : `Turn ${turnCount} • Real-time decisions`}
          </p>
        </div>
        {hasDecisions && (
          <div className={styles.headerMeta}>
            <Clock size={14} />
            <span>{computedProcessingTime}ms</span>
          </div>
        )}
      </div>

      {/* Empty State */}
      {isIdle && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>
            <Inbox size={48} />
          </div>
          <h3>No Active Decisions</h3>
          <p>Start a call and send a message to see the agent decision pipeline in action.</p>
        </div>
      )}

      {/* Pipeline Overview */}
      {!isIdle && (
        <>
          <div className={styles.pipelineOverview}>
            <PipelineStep 
              icon={Brain}
              label="Primary"
              status={getStepStatus('primary', phase, primaryDecision)}
              isActive={phase === 'primary'}
            />
            <div className={styles.connector}>
              <ChevronRight size={16} />
            </div>
            <PipelineStep 
              icon={Eye}
              label="Supervisor"
              status={getStepStatus('supervisor', phase, supervisorDecision)}
              isActive={phase === 'supervisor'}
            />
            <div className={styles.connector}>
              <ChevronRight size={16} />
            </div>
            <PipelineStep 
              icon={ArrowUpRight}
              label="Escalation"
              status={getStepStatus('escalation', phase, escalationDecision)}
              isActive={phase === 'escalation'}
            />
          </div>

          {/* Overall Confidence */}
          {phase === 'complete' && computedConfidence > 0 && (
            <div className={styles.overallConfidence}>
              <div className={styles.confidenceHeader}>
                <Shield size={16} />
                <span>Overall Confidence</span>
              </div>
              <ConfidenceBar confidence={computedConfidence} />
            </div>
          )}

          {/* Agent Decision Cards */}
          <div className={styles.decisions}>
            {/* Primary Agent */}
            <PrimaryAgentCard 
              decision={primaryDecision} 
              isActive={phase === 'primary'}
            />

            {/* Supervisor Agent */}
            <SupervisorAgentCard 
              decision={supervisorDecision} 
              isActive={phase === 'supervisor'}
            />

            {/* Escalation Agent */}
            <EscalationAgentCard 
              decision={escalationDecision} 
              isActive={phase === 'escalation'}
            />
          </div>

          {/* Final Outcome */}
          {phase === 'complete' && finalOutcome && (
            <div className={`${styles.outcome} ${styles[finalOutcome]}`}>
              <div className={styles.outcomeIcon}>
                {finalOutcome === 'escalate' ? (
                  <AlertTriangle size={20} />
                ) : finalOutcome === 'error' ? (
                  <XCircle size={20} />
                ) : (
                  <CheckCircle size={20} />
                )}
              </div>
              <div className={styles.outcomeContent}>
                <span className={styles.outcomeLabel}>Final Decision</span>
                <span className={styles.outcomeValue}>
                  {finalOutcome === 'escalate' 
                    ? 'Escalate to Human Agent'
                    : finalOutcome === 'error'
                    ? 'Error - Fallback Response'
                    : 'Deliver AI Response'
                  }
                </span>
              </div>
              <div className={styles.outcomeMeta}>
                <Activity size={14} />
                <span>
                  {(computedConfidence * 100).toFixed(0)}% confidence
                </span>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Agent Cards
// -----------------------------------------------------------------------------

function PrimaryAgentCard({ 
  decision, 
  isActive 
}: { 
  decision?: AgentDecisionData
  isActive: boolean 
}) {
  const isCompleted = decision?.status === 'completed'
  const isProcessing = decision?.status === 'processing'

  return (
    <AgentCard
      title="Primary Agent"
      subtitle="Intent detection & response"
      icon={Brain}
      color="var(--color-accent-primary)"
      isActive={isActive}
      isProcessing={isProcessing}
      isCompleted={isCompleted}
      processingTime={decision?.processingTimeMs}
    >
      {isCompleted && (
        <>
          {decision.summary && (
            <div className={styles.decisionSummary}>
              <span className={styles.summaryBadge}>
                {decision.responseGenerated ? 'Response Generated' : 'Analyzed'}
              </span>
              <span className={styles.summaryText}>{decision.summary}</span>
            </div>
          )}
          
          <DecisionDetail 
            icon={<Zap size={14} />}
            label="Intent"
            value={formatValue(decision.intent)}
          />
          <DecisionDetail 
            icon={<MessageSquare size={14} />}
            label="Emotion"
            value={formatValue(decision.emotion)}
          />
          <DecisionDetail 
            icon={<Shield size={14} />}
            label="Confidence"
            value={formatConfidence(decision.confidence)}
            valueColor={getConfidenceColor(decision.confidenceLevel)}
          />
          
          {decision.reasoning && decision.reasoning.length > 0 && (
            <ReasoningList reasoning={decision.reasoning} />
          )}
        </>
      )}
      
      {!decision && !isActive && (
        <div className={styles.pendingState}>
          <span>Waiting for input...</span>
        </div>
      )}
    </AgentCard>
  )
}

function SupervisorAgentCard({ 
  decision, 
  isActive 
}: { 
  decision?: AgentDecisionData
  isActive: boolean 
}) {
  const isCompleted = decision?.status === 'completed'
  const isProcessing = decision?.status === 'processing'

  return (
    <AgentCard
      title="Supervisor Agent"
      subtitle="Quality & compliance review"
      icon={Eye}
      color="var(--color-accent-secondary)"
      isActive={isActive}
      isProcessing={isProcessing}
      isCompleted={isCompleted}
      processingTime={decision?.processingTimeMs}
    >
      {isCompleted && (
        <>
          {decision.summary && (
            <div className={styles.decisionSummary}>
              <span className={`${styles.summaryBadge} ${decision.approved ? styles.approved : styles.rejected}`}>
                {decision.approved ? 'Approved' : 'Flagged'}
              </span>
              <span className={styles.summaryText}>{decision.summary}</span>
            </div>
          )}
          
          <DecisionDetail 
            icon={decision.approved ? 
              <CheckCircle size={14} color="var(--color-accent-success)" /> : 
              <XCircle size={14} color="var(--color-accent-danger)" />
            }
            label="Status"
            value={decision.approved ? 'Approved' : 'Needs Review'}
            valueColor={decision.approved ? 'var(--color-accent-success)' : 'var(--color-accent-danger)'}
          />
          
          {decision.qualityScore !== undefined && (
            <DecisionDetail 
              icon={<TrendingUp size={14} />}
              label="Quality Score"
              value={`${(decision.qualityScore * 100).toFixed(0)}%`}
            />
          )}
          
          <DecisionDetail 
            icon={<AlertTriangle size={14} />}
            label="Risk Level"
            value={formatValue(decision.riskLevel)}
            valueColor={getRiskColor(decision.riskLevel)}
          />
          
          {decision.flags && decision.flags.length > 0 && (
            <div className={styles.flagsList}>
              {decision.flags.map((flag, i) => (
                <span key={i} className={styles.flag}>{flag}</span>
              ))}
            </div>
          )}
          
          {decision.reasoning && decision.reasoning.length > 0 && (
            <ReasoningList reasoning={decision.reasoning} />
          )}
        </>
      )}
      
      {!decision && !isActive && (
        <div className={styles.pendingState}>
          <span>Waiting for primary...</span>
        </div>
      )}
    </AgentCard>
  )
}

function EscalationAgentCard({ 
  decision, 
  isActive 
}: { 
  decision?: AgentDecisionData
  isActive: boolean 
}) {
  const isCompleted = decision?.status === 'completed'
  const isProcessing = decision?.status === 'processing'

  return (
    <AgentCard
      title="Escalation Agent"
      subtitle="Routing decision"
      icon={ArrowUpRight}
      color="var(--color-accent-warning)"
      isActive={isActive}
      isProcessing={isProcessing}
      isCompleted={isCompleted}
      processingTime={decision?.processingTimeMs}
    >
      {isCompleted && (
        <>
          <div className={styles.decisionSummary}>
            <span className={`${styles.summaryBadge} ${decision.shouldEscalate ? styles.escalate : styles.noEscalate}`}>
              {decision.shouldEscalate ? 'Escalate' : 'No Escalation'}
            </span>
            {decision.summary && (
              <span className={styles.summaryText}>{decision.summary}</span>
            )}
          </div>
          
          <DecisionDetail 
            icon={decision.shouldEscalate ? 
              <AlertTriangle size={14} color="var(--color-accent-warning)" /> : 
              <CheckCircle size={14} color="var(--color-accent-success)" />
            }
            label="Decision"
            value={decision.shouldEscalate ? 'Escalation Required' : 'AI Can Handle'}
            valueColor={decision.shouldEscalate ? 'var(--color-accent-warning)' : 'var(--color-accent-success)'}
          />
          
          {decision.shouldEscalate && (
            <>
              <DecisionDetail 
                icon={<ArrowUpRight size={14} />}
                label="Type"
                value={formatValue(decision.escalationType)}
              />
              {decision.escalationReason && (
                <DecisionDetail 
                  icon={<MessageSquare size={14} />}
                  label="Reason"
                  value={decision.escalationReason}
                />
              )}
            </>
          )}
          
          <DecisionDetail 
            icon={<Activity size={14} />}
            label="Priority"
            value={`P${decision.priority ?? 5}`}
          />
          
          {decision.reasoning && decision.reasoning.length > 0 && (
            <ReasoningList reasoning={decision.reasoning} />
          )}
        </>
      )}
      
      {!decision && !isActive && (
        <div className={styles.pendingState}>
          <span>Waiting for supervisor...</span>
        </div>
      )}
    </AgentCard>
  )
}

// -----------------------------------------------------------------------------
// Shared Components
// -----------------------------------------------------------------------------

function PipelineStep({ 
  icon: Icon, 
  label, 
  status, 
  isActive 
}: { 
  icon: React.ComponentType<{ size?: number }>
  label: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  isActive: boolean
}) {
  return (
    <div className={`${styles.pipelineStep} ${styles[status]} ${isActive ? styles.active : ''}`}>
      <div className={styles.stepIcon}>
        <Icon size={18} />
      </div>
      <span className={styles.stepLabel}>{label}</span>
      {status === 'processing' && (
        <span className={styles.processingIndicator} />
      )}
      {status === 'completed' && (
        <CheckCircle size={14} className={styles.completedIcon} />
      )}
      {status === 'error' && (
        <XCircle size={14} className={styles.errorIcon} />
      )}
    </div>
  )
}

function AgentCard({
  title,
  subtitle,
  icon: Icon,
  color,
  isActive,
  isProcessing,
  isCompleted,
  processingTime,
  children,
}: {
  title: string
  subtitle: string
  icon: React.ComponentType<{ size?: number }>
  color: string
  isActive: boolean
  isProcessing?: boolean
  isCompleted?: boolean
  processingTime?: number
  children?: React.ReactNode
}) {
  return (
    <div className={`${styles.decisionCard} ${isActive ? styles.active : ''} ${isCompleted ? styles.completed : ''}`}>
      <div className={styles.cardHeader}>
        <div className={styles.cardIcon} style={{ backgroundColor: `${color}20`, color }}>
          <Icon size={18} />
        </div>
        <div className={styles.cardInfo}>
          <h3 className={styles.cardTitle}>{title}</h3>
          <p className={styles.cardSubtitle}>{subtitle}</p>
        </div>
        {isProcessing && (
          <div className={styles.cardStatus}>
            <span className={styles.processingDots}>
              <span />
              <span />
              <span />
            </span>
          </div>
        )}
        {isCompleted && processingTime !== undefined && (
          <div className={styles.cardTiming}>
            <Clock size={12} />
            {processingTime}ms
          </div>
        )}
      </div>
      
      {(isCompleted || children) && (
        <div className={styles.cardContent}>
          {children}
        </div>
      )}
    </div>
  )
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const level = confidence >= 0.7 ? 'high' : confidence >= 0.5 ? 'medium' : 'low'
  
  return (
    <div className={styles.confidenceDisplay}>
      <div className={styles.confidenceBar}>
        <div 
          className={styles.confidenceFill}
          style={{ 
            width: `${confidence * 100}%`,
            backgroundColor: getConfidenceColor(level),
          }}
        />
      </div>
      <span className={styles.confidenceValue}>
        {(confidence * 100).toFixed(0)}%
      </span>
    </div>
  )
}

function DecisionDetail({
  icon,
  label,
  value,
  valueColor,
}: {
  icon: React.ReactNode
  label: string
  value: string
  valueColor?: string
}) {
  return (
    <div className={styles.detail}>
      <div className={styles.detailIcon}>{icon}</div>
      <span className={styles.detailLabel}>{label}</span>
      <span className={styles.detailValue} style={{ color: valueColor }}>
        {value}
      </span>
    </div>
  )
}

function ReasoningList({ reasoning }: { reasoning: string[] }) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  if (reasoning.length === 0) return null
  
  return (
    <div className={styles.reasoning}>
      <button 
        className={styles.reasoningToggle}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <ChevronRight 
          size={14} 
          style={{ transform: isExpanded ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }} 
        />
        Reasoning ({reasoning.length} factors)
      </button>
      {isExpanded && (
        <ul className={styles.reasoningList}>
          {reasoning.map((reason, index) => (
            <li key={index}>{reason}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Helper Functions
// -----------------------------------------------------------------------------

function getStepStatus(
  agent: string, 
  currentPhase: string, 
  decision?: AgentDecisionData
): 'pending' | 'processing' | 'completed' | 'error' {
  if (decision?.status === 'completed') return 'completed'
  if (decision?.status === 'error') return 'error'
  if (decision?.status === 'processing') return 'processing'
  
  const order = ['primary', 'supervisor', 'escalation']
  const agentIndex = order.indexOf(agent)
  const currentIndex = order.indexOf(currentPhase)
  
  if (currentPhase === 'complete') return 'completed'
  if (agentIndex < currentIndex) return 'completed'
  if (agentIndex === currentIndex) return 'processing'
  return 'pending'
}

function getConfidenceColor(level?: string) {
  switch (level) {
    case 'high': return 'var(--color-accent-success)'
    case 'medium': return 'var(--color-accent-warning)'
    case 'low': return 'var(--color-accent-danger)'
    default: return 'var(--color-text-muted)'
  }
}

function getRiskColor(level?: string) {
  switch (level) {
    case 'critical': return 'var(--color-accent-danger)'
    case 'high': return 'var(--color-accent-danger)'
    case 'medium': return 'var(--color-accent-warning)'
    case 'low': return 'var(--color-accent-success)'
    case 'none': return 'var(--color-accent-success)'
    default: return 'var(--color-text-muted)'
  }
}

function formatValue(value?: string): string {
  if (!value) return '—'
  return value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function formatConfidence(value?: number): string {
  if (value === undefined) return '—'
  return `${(value * 100).toFixed(0)}%`
}

export default AgentDecisionPanel
