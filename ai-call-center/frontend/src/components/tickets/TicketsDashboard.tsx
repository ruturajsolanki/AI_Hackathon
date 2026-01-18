import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import styles from './TicketsDashboard.module.css'

interface Ticket {
  ticket_id: string
  interaction_id: string
  status: 'pending' | 'accepted' | 'in_progress' | 'resolved' | 'abandoned'
  priority: 'critical' | 'high' | 'medium' | 'low'
  issue_summary: string
  escalation_reason: string
  customer_name: string | null
  created_at: string
  wait_time_seconds: number
}

interface TicketDetail {
  ticket_id: string
  interaction_id: string
  status: string
  priority: string
  customer_id: string | null
  customer_name: string | null
  issue_summary: string
  ai_attempts: number
  escalation_reason: string
  detected_intent: string | null
  detected_emotion: string | null
  message_count: number
  last_customer_message: string | null
  conversation_history: Array<{
    role: string
    content: string
    timestamp: string | null
  }>
  ai_decisions: Array<{
    agent_type: string
    decision_type: string
    summary: string
    confidence: number
    timestamp: string | null
  }>
  suggested_actions: string[]
  created_at: string
  wait_time_seconds: number
  session_url: string | null
}

const API_BASE = 'http://localhost:8000/api'

export function TicketsDashboard() {
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedTicket, setSelectedTicket] = useState<TicketDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [accepting, setAccepting] = useState(false)
  const [filter, setFilter] = useState<'all' | 'pending' | 'accepted'>('pending')

  const fetchTickets = useCallback(async () => {
    try {
      const endpoint = filter === 'pending' 
        ? `${API_BASE}/tickets/pending`
        : `${API_BASE}/tickets`
      
      const response = await fetch(endpoint)
      if (response.ok) {
        const data = await response.json()
        setTickets(data)
      }
    } catch (err) {
      console.error('Failed to fetch tickets:', err)
    }
  }, [filter])

  const fetchTicketDetail = async (ticketId: string) => {
    try {
      const response = await fetch(`${API_BASE}/tickets/${ticketId}`)
      if (response.ok) {
        const data = await response.json()
        setSelectedTicket(data)
      }
    } catch (err) {
      console.error('Failed to fetch ticket detail:', err)
    }
  }

  const handleAcceptTicket = async (ticketId: string) => {
    setAccepting(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE}/tickets/${ticketId}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: 'human-agent-1',
          agent_name: 'Human Agent',
        }),
      })
      
      if (response.ok) {
        const data = await response.json()
        // The session ID is the interaction_id (same as customer uses)
        const sessionId = data.session_url?.split('/').pop() || ticketId
        // Navigate to the live session
        navigate(`/session/${sessionId}`)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || 'Failed to accept ticket')
      }
    } catch (err) {
      setError('Failed to accept ticket. Please try again.')
    } finally {
      setAccepting(false)
    }
  }
  
  // Open session directly if already accepted
  const handleOpenSession = (sessionUrl: string | null) => {
    if (sessionUrl) {
      const sessionId = sessionUrl.split('/').pop()
      navigate(`/session/${sessionId}`)
    }
  }

  useEffect(() => {
    fetchTickets()
    setLoading(false)
    
    // Poll for new tickets every 5 seconds
    const interval = setInterval(fetchTickets, 5000)
    return () => clearInterval(interval)
  }, [fetchTickets])

  const formatWaitTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
  }

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'critical': return '#ef4444'
      case 'high': return '#f59e0b'
      case 'medium': return '#3b82f6'
      case 'low': return '#6b7280'
      default: return '#6b7280'
    }
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading tickets...</div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>🎫 Tickets Dashboard</h1>
          <p className={styles.subtitle}>Escalated calls waiting for human agents</p>
        </div>
        <div className={styles.headerActions}>
          <div className={styles.filterTabs}>
            <button
              className={`${styles.filterTab} ${filter === 'pending' ? styles.active : ''}`}
              onClick={() => setFilter('pending')}
            >
              Pending ({tickets.filter(t => t.status === 'pending').length})
            </button>
            <button
              className={`${styles.filterTab} ${filter === 'all' ? styles.active : ''}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className={styles.errorBanner}>
          <span>⚠️</span> {error}
        </div>
      )}

      <div className={styles.content}>
        {/* Tickets List */}
        <div className={styles.ticketsList}>
          {tickets.length === 0 ? (
            <div className={styles.emptyState}>
              <span className={styles.emptyIcon}>✅</span>
              <h3>No pending tickets</h3>
              <p>All escalated calls have been handled</p>
            </div>
          ) : (
            tickets.map((ticket) => (
              <div
                key={ticket.ticket_id}
                className={`${styles.ticketCard} ${selectedTicket?.ticket_id === ticket.ticket_id ? styles.selected : ''}`}
                onClick={() => fetchTicketDetail(ticket.ticket_id)}
              >
                <div className={styles.ticketHeader}>
                  <span
                    className={styles.priorityBadge}
                    style={{ backgroundColor: getPriorityColor(ticket.priority) }}
                  >
                    {ticket.priority.toUpperCase()}
                  </span>
                  <span className={styles.waitTime}>
                    ⏱️ {formatWaitTime(ticket.wait_time_seconds)}
                  </span>
                </div>
                
                <h3 className={styles.ticketTitle}>
                  {ticket.customer_name || 'Unknown Customer'}
                </h3>
                
                <p className={styles.ticketSummary}>{ticket.issue_summary}</p>
                
                <div className={styles.ticketFooter}>
                  <span className={styles.escalationReason}>
                    ⚠️ {ticket.escalation_reason}
                  </span>
                  <span className={`${styles.statusBadge} ${styles[ticket.status]}`}>
                    {ticket.status}
                  </span>
                </div>
                
                {/* Quick Actions on Card */}
                <div className={styles.ticketActions}>
                  {ticket.status === 'pending' && (
                    <button
                      className={styles.acceptButtonSmall}
                      onClick={(e) => {
                        e.stopPropagation() // Prevent card click
                        handleAcceptTicket(ticket.ticket_id)
                      }}
                      disabled={accepting}
                    >
                      {accepting ? 'Accepting...' : '✓ Accept'}
                    </button>
                  )}
                  <button
                    className={styles.viewButton}
                    onClick={(e) => {
                      e.stopPropagation()
                      fetchTicketDetail(ticket.ticket_id)
                    }}
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Ticket Detail Panel */}
        {selectedTicket && (
          <div className={styles.detailPanel}>
            <div className={styles.detailHeader}>
              <div>
                <h2>{selectedTicket.customer_name || 'Customer'}</h2>
                <p className={styles.detailSubtitle}>
                  Ticket #{selectedTicket.ticket_id.slice(0, 8)}
                </p>
              </div>
              {selectedTicket.status === 'pending' ? (
                <button
                  className={styles.acceptButton}
                  onClick={() => handleAcceptTicket(selectedTicket.ticket_id)}
                  disabled={accepting}
                >
                  {accepting ? 'Accepting...' : '✓ Accept Ticket'}
                </button>
              ) : selectedTicket.status === 'accepted' && selectedTicket.session_url ? (
                <button
                  className={styles.openSessionButton}
                  onClick={() => handleOpenSession(selectedTicket.session_url)}
                >
                  📞 Open Live Session
                </button>
              ) : null}
            </div>

            {/* Customer Session Link */}
            <section className={styles.detailSection}>
              <h3>📱 Customer Session</h3>
              <p className={styles.sessionHint}>
                Share this link with the customer to continue the conversation:
              </p>
              <div className={styles.sessionLinkRow}>
                <input
                  type="text"
                  readOnly
                  value={`${window.location.origin}/customer-session/${selectedTicket.interaction_id}`}
                  className={styles.sessionLinkInput}
                />
                <button
                  className={styles.copyButton}
                  onClick={() => {
                    navigator.clipboard.writeText(
                      `${window.location.origin}/customer-session/${selectedTicket.interaction_id}`
                    )
                    alert('Link copied!')
                  }}
                >
                  Copy
                </button>
                <button
                  className={styles.openButton}
                  onClick={() => window.open(
                    `${window.location.origin}/customer-session/${selectedTicket.interaction_id}`,
                    '_blank'
                  )}
                >
                  Open
                </button>
              </div>
            </section>

            {/* Issue Summary */}
            <section className={styles.detailSection}>
              <h3>📋 Issue Summary</h3>
              <p className={styles.issueSummary}>{selectedTicket.issue_summary}</p>
              <div className={styles.metaGrid}>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>Escalation Reason</span>
                  <span className={styles.metaValue}>{selectedTicket.escalation_reason}</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>Detected Intent</span>
                  <span className={styles.metaValue}>{selectedTicket.detected_intent || '—'}</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>Customer Emotion</span>
                  <span className={styles.metaValue}>{selectedTicket.detected_emotion || '—'}</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>AI Attempts</span>
                  <span className={styles.metaValue}>{selectedTicket.ai_attempts}</span>
                </div>
              </div>
            </section>

            {/* Suggested Actions */}
            <section className={styles.detailSection}>
              <h3>💡 Suggested Actions</h3>
              <ul className={styles.actionsList}>
                {selectedTicket.suggested_actions.map((action, idx) => (
                  <li key={idx}>{action}</li>
                ))}
              </ul>
            </section>

            {/* Conversation History */}
            <section className={styles.detailSection}>
              <h3>💬 Conversation History ({selectedTicket.message_count} messages)</h3>
              <div className={styles.conversationList}>
                {selectedTicket.conversation_history.slice(-5).map((msg, idx) => (
                  <div
                    key={idx}
                    className={`${styles.message} ${styles[msg.role]}`}
                  >
                    <span className={styles.messageRole}>
                      {msg.role === 'customer' ? '👤' : '🤖'} {msg.role}
                    </span>
                    <p>{msg.content}</p>
                  </div>
                ))}
              </div>
            </section>

            {/* AI Decision Trail */}
            <section className={styles.detailSection}>
              <h3>🧠 AI Decision Trail</h3>
              <div className={styles.decisionsList}>
                {selectedTicket.ai_decisions.slice(-3).map((decision, idx) => (
                  <div key={idx} className={styles.decision}>
                    <div className={styles.decisionHeader}>
                      <span className={styles.decisionAgent}>{decision.agent_type}</span>
                      <span className={styles.decisionConfidence}>
                        {(decision.confidence * 100).toFixed(0)}% confident
                      </span>
                    </div>
                    <p className={styles.decisionSummary}>{decision.summary}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}

export default TicketsDashboard
