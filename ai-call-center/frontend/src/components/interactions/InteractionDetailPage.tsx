/**
 * Interaction Detail Page
 * 
 * Displays full interaction details with unified conversation timeline.
 * Shows messages and agent decisions inline, highlights escalation events.
 */

import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  fetchInteractionDetail, 
  InteractionDetail, 
  MessageItem, 
  DecisionItem 
} from '../../services/apiClient'
import styles from './InteractionDetailPage.module.css'

// Unified timeline event type
interface TimelineEvent {
  id: string
  type: 'message' | 'decision' | 'escalation'
  timestamp: string
  data: MessageItem | DecisionItem
}

export function InteractionDetailPage() {
  const { interactionId } = useParams<{ interactionId: string }>()
  const navigate = useNavigate()
  const [interaction, setInteraction] = useState<InteractionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!interactionId) return

    const loadDetail = async () => {
      setIsLoading(true)
      setError(null)

      const result = await fetchInteractionDetail(interactionId)

      if (result.success && result.data) {
        setInteraction(result.data)
      } else {
        setError(result.error?.message || 'Failed to load interaction')
      }

      setIsLoading(false)
    }

    loadDetail()
  }, [interactionId])

  // Create unified timeline from messages and decisions
  const timeline = useMemo(() => {
    if (!interaction) return []

    const events: TimelineEvent[] = []

    // Add messages
    interaction.messages.forEach((msg) => {
      events.push({
        id: msg.messageId,
        type: 'message',
        timestamp: msg.timestamp,
        data: msg,
      })
    })

    // Add decisions
    interaction.decisions.forEach((dec) => {
      // Check if this is an escalation decision
      const isEscalation = 
        dec.agentType === 'escalation' && 
        (dec.summary.toLowerCase().includes('escalat') || 
         dec.summary.toLowerCase().includes('human') ||
         dec.summary.toLowerCase().includes('ticket'))

      events.push({
        id: dec.decisionId,
        type: isEscalation ? 'escalation' : 'decision',
        timestamp: dec.timestamp,
        data: dec,
      })
    })

    // Sort by timestamp
    events.sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    )

    return events
  }, [interaction])

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '—'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'
    if (confidence >= 0.6) return '#f59e0b'
    return '#ef4444'
  }

  const getAgentIcon = (agentType: string) => {
    switch (agentType) {
      case 'primary': return '🤖'
      case 'supervisor': return '👁️'
      case 'escalation': return '⚡'
      default: return '⚙️'
    }
  }

  const getAgentLabel = (agentType: string) => {
    switch (agentType) {
      case 'primary': return 'Primary Agent'
      case 'supervisor': return 'Supervisor'
      case 'escalation': return 'Escalation Handler'
      default: return agentType
    }
  }

  const renderMessageEvent = (msg: MessageItem) => {
    const isCustomer = msg.role === 'customer'
    const isSystem = msg.role === 'system'

    return (
      <div className={`${styles.messageEvent} ${styles[msg.role]}`}>
        <div className={styles.messageAvatar}>
          {isCustomer ? '👤' : isSystem ? '⚙️' : '🤖'}
        </div>
        <div className={styles.messageBody}>
          <div className={styles.messageHeader}>
            <span className={styles.messageSender}>
              {isCustomer ? 'Customer' : isSystem ? 'System' : 'AI Agent'}
            </span>
            <span className={styles.messageTime}>{formatTime(msg.timestamp)}</span>
          </div>
          <div className={styles.messageContent}>{msg.content}</div>
          {(msg.intent || msg.confidence !== null) && (
            <div className={styles.messageMetadata}>
              {msg.intent && (
                <span className={styles.intentTag}>
                  Intent: {msg.intent.replace(/_/g, ' ')}
                </span>
              )}
              {msg.confidence !== null && (
                <span 
                  className={styles.confidenceTag}
                  style={{ color: getConfidenceColor(msg.confidence) }}
                >
                  {(msg.confidence * 100).toFixed(0)}% confidence
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderDecisionEvent = (dec: DecisionItem, isEscalation: boolean) => {
    return (
      <div className={`${styles.decisionEvent} ${isEscalation ? styles.escalationEvent : ''}`}>
        <div className={styles.decisionIcon}>
          {isEscalation ? '🚨' : getAgentIcon(dec.agentType)}
        </div>
        <div className={styles.decisionBody}>
          <div className={styles.decisionHeader}>
            <span className={styles.decisionAgent}>
              {isEscalation ? 'Escalation Triggered' : getAgentLabel(dec.agentType)}
            </span>
            <span className={styles.decisionTime}>{formatTime(dec.timestamp)}</span>
          </div>
          <div className={styles.decisionContent}>
            <span className={styles.decisionSummary}>{dec.summary}</span>
            <div className={styles.decisionStats}>
              <span 
                className={styles.confidencePill}
                style={{ 
                  backgroundColor: `${getConfidenceColor(dec.confidence)}20`,
                  color: getConfidenceColor(dec.confidence),
                }}
              >
                {(dec.confidence * 100).toFixed(0)}%
              </span>
              <span className={styles.processingTime}>
                ⚡ {dec.processingTimeMs}ms
              </span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <span>Loading interaction...</span>
      </div>
    )
  }

  if (error || !interaction) {
    return (
      <div className={styles.errorContainer}>
        <span className={styles.errorIcon}>⚠️</span>
        <h2>Failed to load interaction</h2>
        <p>{error || 'Interaction not found'}</p>
        <button onClick={() => navigate('/interactions')}>
          ← Back to Interactions
        </button>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <button className={styles.backButton} onClick={() => navigate('/interactions')}>
          ← Back
        </button>
        <div className={styles.headerInfo}>
          <div className={styles.headerTop}>
            <h1 className={styles.title}>
              <code>{interaction.interactionId.substring(0, 8).toUpperCase()}</code>
            </h1>
            <span className={`${styles.statusBadge} ${styles[interaction.status]}`}>
              {interaction.status.replace(/_/g, ' ')}
            </span>
            {interaction.wasEscalated && (
              <span className={styles.escalatedBadge}>
                🚨 Escalated
              </span>
            )}
          </div>
          <div className={styles.headerMeta}>
            <span>{interaction.channel === 'voice' ? '🎙️' : '💬'} {interaction.channel}</span>
            <span>•</span>
            <span>{formatDate(interaction.startedAt)}</span>
            <span>•</span>
            <span>{formatDuration(interaction.durationSeconds)}</span>
            <span>•</span>
            <span>{interaction.messages.length} messages</span>
          </div>
        </div>
      </header>

      {/* Summary Cards */}
      <div className={styles.summaryCards}>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Total Messages</div>
          <div className={styles.summaryValue}>{interaction.messages.length}</div>
        </div>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Agent Decisions</div>
          <div className={styles.summaryValue}>{interaction.decisions.length}</div>
        </div>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Duration</div>
          <div className={styles.summaryValue}>{formatDuration(interaction.durationSeconds)}</div>
        </div>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Resolution</div>
          <div className={styles.summaryValue}>
            {interaction.resolutionSummary || (interaction.wasEscalated ? 'Escalated' : 'In Progress')}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className={styles.timelineSection}>
        <h2 className={styles.sectionTitle}>Conversation Timeline</h2>
        <div className={styles.timeline}>
          {timeline.length === 0 ? (
            <div className={styles.emptyState}>
              No events recorded for this interaction
            </div>
          ) : (
            timeline.map((event) => (
              <div key={event.id} className={styles.timelineItem}>
                <div className={styles.timelineLine} />
                {event.type === 'message' 
                  ? renderMessageEvent(event.data as MessageItem)
                  : renderDecisionEvent(event.data as DecisionItem, event.type === 'escalation')
                }
              </div>
            ))
          )}
        </div>
      </div>

      {/* Escalation Alert (if applicable) */}
      {interaction.wasEscalated && (
        <div className={styles.escalationAlert}>
          <div className={styles.alertIcon}>🚨</div>
          <div className={styles.alertContent}>
            <strong>This interaction was escalated</strong>
            <p>The AI determined this case required human intervention based on customer request or complexity.</p>
          </div>
        </div>
      )}
    </div>
  )
}
