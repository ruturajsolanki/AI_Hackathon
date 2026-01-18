/**
 * Interaction Detail Page
 * 
 * Displays full details of a single interaction including
 * messages and agent decisions.
 */

import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchInteractionDetail, InteractionDetail, MessageItem, DecisionItem } from '../../services/apiClient'
import styles from './InteractionDetailPage.module.css'

export function InteractionDetailPage() {
  const { interactionId } = useParams<{ interactionId: string }>()
  const navigate = useNavigate()
  const [interaction, setInteraction] = useState<InteractionDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'messages' | 'decisions'>('messages')

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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    }).format(date)
  }

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '—'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; variant: string }> = {
      initiated: { label: 'Active', variant: 'info' },
      in_progress: { label: 'In Progress', variant: 'warning' },
      completed: { label: 'Completed', variant: 'success' },
      escalated: { label: 'Escalated', variant: 'danger' },
      abandoned: { label: 'Abandoned', variant: 'muted' },
    }
    const config = statusMap[status] || { label: status, variant: 'muted' }
    return (
      <span className={`${styles.badge} ${styles[config.variant]}`}>
        {config.label}
      </span>
    )
  }

  const getAgentBadge = (agentType: string) => {
    const agentMap: Record<string, { label: string; color: string }> = {
      primary: { label: 'Primary', color: '#3b82f6' },
      supervisor: { label: 'Supervisor', color: '#8b5cf6' },
      escalation: { label: 'Escalation', color: '#f59e0b' },
    }
    const config = agentMap[agentType] || { label: agentType, color: '#6b7280' }
    return (
      <span 
        className={styles.agentBadge} 
        style={{ backgroundColor: `${config.color}20`, color: config.color }}
      >
        {config.label}
      </span>
    )
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'
    if (confidence >= 0.6) return '#f59e0b'
    return '#ef4444'
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
      {/* Back Button */}
      <button className={styles.backButton} onClick={() => navigate('/interactions')}>
        ← Back to Interactions
      </button>

      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerMain}>
          <h1 className={styles.title}>
            <code>{interaction.interactionId.substring(0, 8).toUpperCase()}</code>
          </h1>
          {getStatusBadge(interaction.status)}
        </div>
        <p className={styles.subtitle}>
          {interaction.channel === 'voice' ? '🎙️' : '💬'} {interaction.channel} call
          {interaction.wasEscalated && ' • Escalated to human'}
        </p>
      </header>

      {/* Metadata */}
      <div className={styles.metadata}>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Started</span>
          <span className={styles.metaValue}>{formatDate(interaction.startedAt)}</span>
        </div>
        {interaction.endedAt && (
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Ended</span>
            <span className={styles.metaValue}>{formatDate(interaction.endedAt)}</span>
          </div>
        )}
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Duration</span>
          <span className={styles.metaValue}>{formatDuration(interaction.durationSeconds)}</span>
        </div>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Messages</span>
          <span className={styles.metaValue}>{interaction.messages.length}</span>
        </div>
        <div className={styles.metaItem}>
          <span className={styles.metaLabel}>Decisions</span>
          <span className={styles.metaValue}>{interaction.decisions.length}</span>
        </div>
        {interaction.resolutionSummary && (
          <div className={styles.metaItem}>
            <span className={styles.metaLabel}>Resolution</span>
            <span className={styles.metaValue}>{interaction.resolutionSummary}</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'messages' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          Messages ({interaction.messages.length})
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'decisions' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('decisions')}
        >
          Agent Decisions ({interaction.decisions.length})
        </button>
      </div>

      {/* Content */}
      <div className={styles.content}>
        {activeTab === 'messages' && (
          <div className={styles.messagesContainer}>
            {interaction.messages.length === 0 ? (
              <div className={styles.emptyState}>No messages in this interaction</div>
            ) : (
              interaction.messages.map((message: MessageItem) => (
                <div
                  key={message.messageId}
                  className={`${styles.message} ${styles[message.role]}`}
                >
                  <div className={styles.messageHeader}>
                    <span className={styles.messageRole}>
                      {message.role === 'customer' ? '👤 Customer' : 
                       message.role === 'agent' ? '🤖 AI Agent' : '⚙️ System'}
                    </span>
                    <span className={styles.messageTime}>
                      {formatDate(message.timestamp)}
                    </span>
                  </div>
                  <div className={styles.messageContent}>{message.content}</div>
                  {(message.intent || message.confidence) && (
                    <div className={styles.messageMeta}>
                      {message.intent && (
                        <span className={styles.intent}>Intent: {message.intent}</span>
                      )}
                      {message.confidence !== null && (
                        <span 
                          className={styles.confidence}
                          style={{ color: getConfidenceColor(message.confidence) }}
                        >
                          Confidence: {(message.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'decisions' && (
          <div className={styles.decisionsContainer}>
            {interaction.decisions.length === 0 ? (
              <div className={styles.emptyState}>No agent decisions recorded</div>
            ) : (
              interaction.decisions.map((decision: DecisionItem) => (
                <div key={decision.decisionId} className={styles.decision}>
                  <div className={styles.decisionHeader}>
                    {getAgentBadge(decision.agentType)}
                    <span className={styles.decisionTime}>
                      {formatDate(decision.timestamp)}
                    </span>
                  </div>
                  <div className={styles.decisionSummary}>{decision.summary}</div>
                  <div className={styles.decisionMeta}>
                    <div className={styles.confidenceBar}>
                      <span className={styles.confidenceLabel}>Confidence</span>
                      <div className={styles.confidenceTrack}>
                        <div
                          className={styles.confidenceFill}
                          style={{
                            width: `${decision.confidence * 100}%`,
                            backgroundColor: getConfidenceColor(decision.confidence),
                          }}
                        />
                      </div>
                      <span 
                        className={styles.confidenceValue}
                        style={{ color: getConfidenceColor(decision.confidence) }}
                      >
                        {(decision.confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                    <span className={styles.processingTime}>
                      ⚡ {decision.processingTimeMs}ms
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
