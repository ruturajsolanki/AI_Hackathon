/**
 * Human Agent Handoff Summary
 * 
 * Displays comprehensive information for human agents
 * taking over from AI. Shows everything needed for a
 * smooth transition.
 */

import { useState, useEffect } from 'react'
import { 
  AlertTriangle, 
  User, 
  MessageSquare, 
  TrendingUp,
  Clock,
  Target,
  Lightbulb,
  FileText,
  ChevronDown,
  ChevronUp,
  Phone,
  Bot
} from 'lucide-react'
import styles from './HandoffSummary.module.css'

interface HandoffData {
  interaction_id: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  priority_reason: string
  customer_intent: string
  current_emotion: string
  emotion_trajectory: string
  total_messages: number
  ai_response_count: number
  conversation_duration_seconds: number
  issue_summary: string
  key_points: string[]
  customer_requests: string[]
  ai_attempts: number
  average_confidence: number
  escalation_reason: string
  what_ai_tried: string[]
  suggested_actions: string[]
  relevant_policies: string[]
  transcript: Array<{
    role: string
    content: string
    timestamp: string
  }>
}

interface HandoffSummaryProps {
  interactionId: string
  onAccept?: () => void
  onDecline?: () => void
}

export function HandoffSummary({ interactionId, onAccept, onDecline }: HandoffSummaryProps) {
  const [data, setData] = useState<HandoffData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTranscript, setShowTranscript] = useState(false)

  useEffect(() => {
    fetchHandoffData()
  }, [interactionId])

  const fetchHandoffData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/history/interactions/${interactionId}/handoff`)
      if (!response.ok) {
        throw new Error('Failed to load handoff data')
      }
      const result = await response.json()
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getPriorityConfig = (priority: string) => {
    const configs = {
      critical: { color: '#ef4444', bg: 'rgba(239, 68, 68, 0.1)', label: '🔴 CRITICAL' },
      high: { color: '#f97316', bg: 'rgba(249, 115, 22, 0.1)', label: '🟠 HIGH' },
      medium: { color: '#eab308', bg: 'rgba(234, 179, 8, 0.1)', label: '🟡 MEDIUM' },
      low: { color: '#22c55e', bg: 'rgba(34, 197, 94, 0.1)', label: '🟢 LOW' },
    }
    return configs[priority as keyof typeof configs] || configs.medium
  }

  const getEmotionEmoji = (emotion: string) => {
    const emojis: Record<string, string> = {
      angry: '😠',
      frustrated: '😤',
      anxious: '😰',
      confused: '😕',
      neutral: '😐',
      satisfied: '😊',
      happy: '😄',
    }
    return emojis[emotion.toLowerCase()] || '😐'
  }

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <Phone className={styles.loadingIcon} />
          <span>Loading handoff summary...</span>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <AlertTriangle size={24} />
          <span>{error || 'Failed to load handoff data'}</span>
        </div>
      </div>
    )
  }

  const priorityConfig = getPriorityConfig(data.priority)

  return (
    <div className={styles.container}>
      {/* Header with Priority */}
      <header className={styles.header} style={{ borderColor: priorityConfig.color }}>
        <div className={styles.headerTop}>
          <div 
            className={styles.priorityBadge}
            style={{ background: priorityConfig.bg, color: priorityConfig.color }}
          >
            {priorityConfig.label}
          </div>
          <span className={styles.callId}>Call #{data.interaction_id.slice(0, 8)}</span>
        </div>
        <h1 className={styles.title}>Human Agent Required</h1>
        <p className={styles.priorityReason}>{data.priority_reason}</p>
      </header>

      {/* Quick Stats */}
      <div className={styles.statsGrid}>
        <div className={styles.statCard}>
          <Clock size={20} />
          <div>
            <span className={styles.statValue}>{formatDuration(data.conversation_duration_seconds)}</span>
            <span className={styles.statLabel}>Duration</span>
          </div>
        </div>
        <div className={styles.statCard}>
          <MessageSquare size={20} />
          <div>
            <span className={styles.statValue}>{data.total_messages}</span>
            <span className={styles.statLabel}>Messages</span>
          </div>
        </div>
        <div className={styles.statCard}>
          <Bot size={20} />
          <div>
            <span className={styles.statValue}>{data.ai_attempts}</span>
            <span className={styles.statLabel}>AI Attempts</span>
          </div>
        </div>
        <div className={styles.statCard}>
          <TrendingUp size={20} />
          <div>
            <span className={styles.statValue}>{(data.average_confidence * 100).toFixed(0)}%</span>
            <span className={styles.statLabel}>Avg Confidence</span>
          </div>
        </div>
      </div>

      {/* Customer Context */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <User size={18} />
          Customer Context
        </h2>
        <div className={styles.contextGrid}>
          <div className={styles.contextItem}>
            <span className={styles.contextLabel}>Intent</span>
            <span className={styles.contextValue}>{data.customer_intent.replace(/_/g, ' ')}</span>
          </div>
          <div className={styles.contextItem}>
            <span className={styles.contextLabel}>Current Emotion</span>
            <span className={styles.contextValue}>
              {getEmotionEmoji(data.current_emotion)} {data.current_emotion}
            </span>
          </div>
          <div className={styles.contextItem}>
            <span className={styles.contextLabel}>Emotion Journey</span>
            <span className={styles.emotionTrajectory}>{data.emotion_trajectory}</span>
          </div>
        </div>
      </section>

      {/* Issue Summary */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <FileText size={18} />
          Issue Summary
        </h2>
        <p className={styles.issueSummary}>{data.issue_summary}</p>
        
        {data.key_points.length > 0 && (
          <div className={styles.keyPoints}>
            <h3>Key Points:</h3>
            <ul>
              {data.key_points.map((point, i) => (
                <li key={i}>{point}</li>
              ))}
            </ul>
          </div>
        )}
      </section>

      {/* What AI Tried */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <Bot size={18} />
          What AI Tried
        </h2>
        <div className={styles.aiAttempts}>
          <p className={styles.escalationReason}>
            <strong>Escalation Reason:</strong> {data.escalation_reason}
          </p>
          {data.what_ai_tried.length > 0 && (
            <ul className={styles.attemptsList}>
              {data.what_ai_tried.map((attempt, i) => (
                <li key={i}>{attempt}</li>
              ))}
            </ul>
          )}
        </div>
      </section>

      {/* Suggested Actions */}
      <section className={styles.section}>
        <h2 className={styles.sectionTitle}>
          <Lightbulb size={18} />
          Suggested Actions
        </h2>
        <ul className={styles.suggestions}>
          {data.suggested_actions.map((action, i) => (
            <li key={i} className={styles.suggestionItem}>
              <Target size={14} />
              {action}
            </li>
          ))}
        </ul>
        
        {data.relevant_policies.length > 0 && (
          <div className={styles.policies}>
            <h3>Relevant Policies:</h3>
            {data.relevant_policies.map((policy, i) => (
              <span key={i} className={styles.policyTag}>{policy}</span>
            ))}
          </div>
        )}
      </section>

      {/* Transcript Toggle */}
      <section className={styles.section}>
        <button 
          className={styles.transcriptToggle}
          onClick={() => setShowTranscript(!showTranscript)}
        >
          <MessageSquare size={18} />
          <span>Full Transcript ({data.transcript.length} messages)</span>
          {showTranscript ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
        
        {showTranscript && (
          <div className={styles.transcript}>
            {data.transcript.map((msg, i) => (
              <div 
                key={i} 
                className={`${styles.transcriptMessage} ${styles[msg.role]}`}
              >
                <span className={styles.transcriptRole}>
                  {msg.role === 'customer' ? '👤 Customer' : '🤖 AI Agent'}
                </span>
                <p className={styles.transcriptContent}>{msg.content}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Action Buttons */}
      <footer className={styles.footer}>
        <button className={styles.acceptButton} onClick={onAccept}>
          <Phone size={18} />
          Accept Call
        </button>
        <button className={styles.declineButton} onClick={onDecline}>
          Transfer to Another Agent
        </button>
      </footer>
    </div>
  )
}

export default HandoffSummary
