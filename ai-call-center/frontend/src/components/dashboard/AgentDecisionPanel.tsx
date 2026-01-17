import { useState, useEffect } from 'react'
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
  Activity
} from 'lucide-react'
import styles from './AgentDecisionPanel.module.css'

// Types
interface AgentDecision {
  agentType: 'primary' | 'supervisor' | 'escalation'
  timestamp: Date
  status: 'pending' | 'processing' | 'completed'
  processingTimeMs?: number
  decision?: {
    type: string
    summary: string
    confidence: number
    confidenceLevel: 'high' | 'medium' | 'low' | 'uncertain'
    reasoning: string[]
  }
  // Primary Agent specific
  intent?: string
  emotion?: string
  responseGenerated?: boolean
  // Supervisor Agent specific
  approved?: boolean
  adjustedConfidence?: number
  flags?: string[]
  riskLevel?: 'none' | 'low' | 'medium' | 'high' | 'critical'
  // Escalation Agent specific
  shouldEscalate?: boolean
  escalationType?: string
  escalationReason?: string
  priority?: number
}

interface PipelineState {
  currentPhase: 'idle' | 'primary' | 'supervisor' | 'escalation' | 'complete'
  decisions: AgentDecision[]
  overallConfidence: number
  finalOutcome?: 'respond' | 'escalate' | 'error'
}

interface AgentDecisionPanelProps {
  // Optional: receive pipeline state from parent
  pipelineState?: PipelineState
  // Optional: for demo mode
  demoMode?: boolean
}

// Demo data generator
function generateDemoDecisions(): AgentDecision[] {
  return [
    {
      agentType: 'primary',
      timestamp: new Date(Date.now() - 2500),
      status: 'completed',
      processingTimeMs: 342,
      decision: {
        type: 'respond',
        summary: 'Responding to billing inquiry',
        confidence: 0.87,
        confidenceLevel: 'high',
        reasoning: [
          'Clear intent detected: billing_inquiry',
          'Keywords matched: "bill", "charge", "payment"',
          'Customer emotion: neutral',
          'Context available from previous turn',
        ],
      },
      intent: 'billing_inquiry',
      emotion: 'neutral',
      responseGenerated: true,
    },
    {
      agentType: 'supervisor',
      timestamp: new Date(Date.now() - 1800),
      status: 'completed',
      processingTimeMs: 156,
      decision: {
        type: 'approve',
        summary: 'Decision approved with minor adjustment',
        confidence: 0.89,
        confidenceLevel: 'high',
        reasoning: [
          'Quality assessment: 0.92',
          'Tone appropriate for context',
          'No compliance violations',
          'Risk level: low',
        ],
      },
      approved: true,
      adjustedConfidence: 0.89,
      flags: [],
      riskLevel: 'low',
    },
    {
      agentType: 'escalation',
      timestamp: new Date(Date.now() - 1200),
      status: 'completed',
      processingTimeMs: 98,
      decision: {
        type: 'no_escalation',
        summary: 'No escalation required',
        confidence: 0.94,
        confidenceLevel: 'high',
        reasoning: [
          'Decision approved by supervisor',
          'Risk level acceptable',
          'Confidence above threshold',
          'No emotional distress detected',
        ],
      },
      shouldEscalate: false,
      priority: 5,
    },
  ]
}

export function AgentDecisionPanel({ 
  pipelineState, 
  demoMode = true 
}: AgentDecisionPanelProps) {
  const [decisions, setDecisions] = useState<AgentDecision[]>([])
  const [currentPhase, setCurrentPhase] = useState<string>('idle')
  const [isAnimating, setIsAnimating] = useState(false)

  // Initialize with demo data or props
  useEffect(() => {
    if (pipelineState) {
      setDecisions(pipelineState.decisions)
      setCurrentPhase(pipelineState.currentPhase)
    } else if (demoMode) {
      setDecisions(generateDemoDecisions())
      setCurrentPhase('complete')
    }
  }, [pipelineState, demoMode])

  // Demo animation
  const runDemoAnimation = () => {
    setIsAnimating(true)
    setDecisions([])
    setCurrentPhase('primary')

    // Simulate Primary Agent
    setTimeout(() => {
      setDecisions([{
        agentType: 'primary',
        timestamp: new Date(),
        status: 'processing',
      }])
    }, 100)

    setTimeout(() => {
      setDecisions([generateDemoDecisions()[0]])
      setCurrentPhase('supervisor')
    }, 1500)

    // Simulate Supervisor Agent
    setTimeout(() => {
      setDecisions(prev => [...prev, {
        agentType: 'supervisor',
        timestamp: new Date(),
        status: 'processing',
      }])
    }, 1600)

    setTimeout(() => {
      setDecisions([
        generateDemoDecisions()[0],
        generateDemoDecisions()[1],
      ])
      setCurrentPhase('escalation')
    }, 2500)

    // Simulate Escalation Agent
    setTimeout(() => {
      setDecisions(prev => [...prev, {
        agentType: 'escalation',
        timestamp: new Date(),
        status: 'processing',
      }])
    }, 2600)

    setTimeout(() => {
      setDecisions(generateDemoDecisions())
      setCurrentPhase('complete')
      setIsAnimating(false)
    }, 3200)
  }

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'primary': return Brain
      case 'supervisor': return Eye
      case 'escalation': return ArrowUpRight
      default: return Brain
    }
  }

  const getAgentColor = (type: string) => {
    switch (type) {
      case 'primary': return 'var(--color-accent-primary)'
      case 'supervisor': return 'var(--color-accent-secondary)'
      case 'escalation': return 'var(--color-accent-warning)'
      default: return 'var(--color-text-muted)'
    }
  }

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high': return 'var(--color-accent-success)'
      case 'medium': return 'var(--color-accent-warning)'
      case 'low': return 'var(--color-accent-danger)'
      default: return 'var(--color-text-muted)'
    }
  }

  const primaryDecision = decisions.find(d => d.agentType === 'primary')
  const supervisorDecision = decisions.find(d => d.agentType === 'supervisor')
  const escalationDecision = decisions.find(d => d.agentType === 'escalation')

  const overallConfidence = escalationDecision?.decision?.confidence 
    || supervisorDecision?.adjustedConfidence 
    || primaryDecision?.decision?.confidence 
    || 0

  return (
    <div className={styles.panel}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h2 className={styles.title}>Agent Decision Pipeline</h2>
          <p className={styles.subtitle}>Real-time AI decision transparency</p>
        </div>
        {demoMode && (
          <button 
            className={styles.demoButton}
            onClick={runDemoAnimation}
            disabled={isAnimating}
          >
            <Activity size={16} />
            {isAnimating ? 'Running...' : 'Run Demo'}
          </button>
        )}
      </div>

      {/* Pipeline Overview */}
      <div className={styles.pipelineOverview}>
        <PipelineStep 
          icon={Brain}
          label="Primary"
          status={getPipelineStatus('primary', currentPhase, primaryDecision)}
          isActive={currentPhase === 'primary'}
        />
        <div className={styles.connector}>
          <ChevronRight size={16} />
        </div>
        <PipelineStep 
          icon={Eye}
          label="Supervisor"
          status={getPipelineStatus('supervisor', currentPhase, supervisorDecision)}
          isActive={currentPhase === 'supervisor'}
        />
        <div className={styles.connector}>
          <ChevronRight size={16} />
        </div>
        <PipelineStep 
          icon={ArrowUpRight}
          label="Escalation"
          status={getPipelineStatus('escalation', currentPhase, escalationDecision)}
          isActive={currentPhase === 'escalation'}
        />
      </div>

      {/* Overall Confidence */}
      {currentPhase === 'complete' && (
        <div className={styles.overallConfidence}>
          <div className={styles.confidenceHeader}>
            <Shield size={16} />
            <span>Overall Confidence</span>
          </div>
          <div className={styles.confidenceDisplay}>
            <div className={styles.confidenceBar}>
              <div 
                className={styles.confidenceFill}
                style={{ 
                  width: `${overallConfidence * 100}%`,
                  backgroundColor: getConfidenceColor(
                    overallConfidence >= 0.8 ? 'high' : 
                    overallConfidence >= 0.6 ? 'medium' : 'low'
                  ),
                }}
              />
            </div>
            <span className={styles.confidenceValue}>
              {(overallConfidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      )}

      {/* Agent Decision Cards */}
      <div className={styles.decisions}>
        {/* Primary Agent */}
        <AgentDecisionCard
          title="Primary Agent"
          subtitle="Initial response generation"
          icon={Brain}
          color={getAgentColor('primary')}
          decision={primaryDecision}
          isActive={currentPhase === 'primary'}
        >
          {primaryDecision?.status === 'completed' && primaryDecision.decision && (
            <>
              <DecisionDetail 
                icon={<Zap size={14} />}
                label="Intent Detected"
                value={primaryDecision.intent?.replace('_', ' ') || 'Unknown'}
              />
              <DecisionDetail 
                icon={<MessageSquare size={14} />}
                label="Emotion"
                value={primaryDecision.emotion || 'Neutral'}
              />
              <DecisionDetail 
                icon={<Shield size={14} />}
                label="Confidence"
                value={`${(primaryDecision.decision.confidence * 100).toFixed(0)}%`}
                valueColor={getConfidenceColor(primaryDecision.decision.confidenceLevel)}
              />
              <ReasoningList reasoning={primaryDecision.decision.reasoning} />
            </>
          )}
        </AgentDecisionCard>

        {/* Supervisor Agent */}
        <AgentDecisionCard
          title="Supervisor Agent"
          subtitle="Quality & compliance review"
          icon={Eye}
          color={getAgentColor('supervisor')}
          decision={supervisorDecision}
          isActive={currentPhase === 'supervisor'}
        >
          {supervisorDecision?.status === 'completed' && supervisorDecision.decision && (
            <>
              <DecisionDetail 
                icon={supervisorDecision.approved ? 
                  <CheckCircle size={14} color="var(--color-accent-success)" /> : 
                  <XCircle size={14} color="var(--color-accent-danger)" />
                }
                label="Approval Status"
                value={supervisorDecision.approved ? 'Approved' : 'Rejected'}
                valueColor={supervisorDecision.approved ? 
                  'var(--color-accent-success)' : 'var(--color-accent-danger)'
                }
              />
              <DecisionDetail 
                icon={<TrendingUp size={14} />}
                label="Adjusted Confidence"
                value={`${((supervisorDecision.adjustedConfidence || 0) * 100).toFixed(0)}%`}
                valueColor={getConfidenceColor(supervisorDecision.decision.confidenceLevel)}
              />
              <DecisionDetail 
                icon={<AlertTriangle size={14} />}
                label="Risk Level"
                value={supervisorDecision.riskLevel || 'None'}
                valueColor={getRiskColor(supervisorDecision.riskLevel)}
              />
              <ReasoningList reasoning={supervisorDecision.decision.reasoning} />
            </>
          )}
        </AgentDecisionCard>

        {/* Escalation Agent */}
        <AgentDecisionCard
          title="Escalation Agent"
          subtitle="Routing decision"
          icon={ArrowUpRight}
          color={getAgentColor('escalation')}
          decision={escalationDecision}
          isActive={currentPhase === 'escalation'}
        >
          {escalationDecision?.status === 'completed' && escalationDecision.decision && (
            <>
              <DecisionDetail 
                icon={escalationDecision.shouldEscalate ? 
                  <AlertTriangle size={14} color="var(--color-accent-warning)" /> : 
                  <CheckCircle size={14} color="var(--color-accent-success)" />
                }
                label="Escalation Required"
                value={escalationDecision.shouldEscalate ? 'Yes' : 'No'}
                valueColor={escalationDecision.shouldEscalate ? 
                  'var(--color-accent-warning)' : 'var(--color-accent-success)'
                }
              />
              {escalationDecision.shouldEscalate && (
                <>
                  <DecisionDetail 
                    icon={<ArrowUpRight size={14} />}
                    label="Escalation Type"
                    value={escalationDecision.escalationType?.replace('_', ' ') || 'Human'}
                  />
                  <DecisionDetail 
                    icon={<AlertTriangle size={14} />}
                    label="Reason"
                    value={escalationDecision.escalationReason || 'N/A'}
                  />
                </>
              )}
              <DecisionDetail 
                icon={<Activity size={14} />}
                label="Priority"
                value={`P${escalationDecision.priority || 5}`}
              />
              <ReasoningList reasoning={escalationDecision.decision.reasoning} />
            </>
          )}
        </AgentDecisionCard>
      </div>

      {/* Final Outcome */}
      {currentPhase === 'complete' && (
        <div className={styles.outcome}>
          <div className={styles.outcomeIcon}>
            {escalationDecision?.shouldEscalate ? (
              <AlertTriangle size={20} />
            ) : (
              <CheckCircle size={20} />
            )}
          </div>
          <div className={styles.outcomeContent}>
            <span className={styles.outcomeLabel}>Final Decision</span>
            <span className={styles.outcomeValue}>
              {escalationDecision?.shouldEscalate 
                ? 'Escalate to Human Agent'
                : 'Deliver AI Response'
              }
            </span>
          </div>
          <div className={styles.outcomeMeta}>
            <Clock size={14} />
            <span>
              Total: {decisions.reduce((sum, d) => sum + (d.processingTimeMs || 0), 0)}ms
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper Components
function PipelineStep({ 
  icon: Icon, 
  label, 
  status, 
  isActive 
}: { 
  icon: React.ComponentType<{ size?: number }>
  label: string
  status: 'pending' | 'processing' | 'completed'
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
    </div>
  )
}

function AgentDecisionCard({
  title,
  subtitle,
  icon: Icon,
  color,
  decision,
  isActive,
  children,
}: {
  title: string
  subtitle: string
  icon: React.ComponentType<{ size?: number }>
  color: string
  decision?: AgentDecision
  isActive: boolean
  children?: React.ReactNode
}) {
  const isProcessing = decision?.status === 'processing'
  const isCompleted = decision?.status === 'completed'

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
        {isCompleted && decision?.processingTimeMs && (
          <div className={styles.cardTiming}>
            <Clock size={12} />
            {decision.processingTimeMs}ms
          </div>
        )}
      </div>
      
      {isCompleted && (
        <div className={styles.cardContent}>
          {decision?.decision && (
            <div className={styles.decisionSummary}>
              <span className={styles.summaryBadge}>
                {decision.decision.type.replace('_', ' ')}
              </span>
              <span className={styles.summaryText}>
                {decision.decision.summary}
              </span>
            </div>
          )}
          {children}
        </div>
      )}
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
  
  return (
    <div className={styles.reasoning}>
      <button 
        className={styles.reasoningToggle}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <ChevronRight 
          size={14} 
          style={{ transform: isExpanded ? 'rotate(90deg)' : 'none' }} 
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

// Helper functions
function getPipelineStatus(
  agent: string, 
  currentPhase: string, 
  decision?: AgentDecision
): 'pending' | 'processing' | 'completed' {
  if (decision?.status === 'completed') return 'completed'
  if (decision?.status === 'processing') return 'processing'
  
  const order = ['primary', 'supervisor', 'escalation']
  const agentIndex = order.indexOf(agent)
  const currentIndex = order.indexOf(currentPhase)
  
  if (agentIndex < currentIndex) return 'completed'
  if (agentIndex === currentIndex) return 'processing'
  return 'pending'
}

function getRiskColor(level?: string) {
  switch (level) {
    case 'critical': return 'var(--color-accent-danger)'
    case 'high': return 'var(--color-accent-danger)'
    case 'medium': return 'var(--color-accent-warning)'
    case 'low': return 'var(--color-accent-success)'
    default: return 'var(--color-text-muted)'
  }
}
