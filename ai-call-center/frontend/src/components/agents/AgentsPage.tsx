/**
 * Agents Overview Page
 * 
 * Displays AI agent cards with roles, decision scope, and recent decisions.
 * Enterprise-grade explainable AI interface.
 */

import { useEffect, useState, useCallback } from 'react'
import {
  fetchAgents,
  fetchAgentDetail,
  AgentMetadata,
  AgentDetailResponse,
  AnonymizedDecision,
} from '../../services/apiClient'
import styles from './AgentsPage.module.css'

export function AgentsPage() {
  const [agents, setAgents] = useState<AgentMetadata[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<AgentDetailResponse | null>(null)
  const [isLoadingDetail, setIsLoadingDetail] = useState(false)

  useEffect(() => {
    const loadAgents = async () => {
      setIsLoading(true)
      setError(null)

      const result = await fetchAgents()

      if (result.success && result.data) {
        setAgents(result.data.agents)
      } else {
        setError(result.error?.message || 'Failed to load agents')
      }

      setIsLoading(false)
    }

    loadAgents()
  }, [])

  const handleAgentClick = useCallback(async (agentId: string) => {
    if (selectedAgent?.agent.agentId === agentId) {
      setSelectedAgent(null)
      return
    }

    setIsLoadingDetail(true)
    const result = await fetchAgentDetail(agentId)

    if (result.success && result.data) {
      setSelectedAgent(result.data)
    }

    setIsLoadingDetail(false)
  }, [selectedAgent])

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'primary': return '🤖'
      case 'supervisor': return '👁️'
      case 'escalation': return '⚡'
      default: return '⚙️'
    }
  }

  const getAgentColor = (type: string) => {
    switch (type) {
      case 'primary': return '#3b82f6'
      case 'supervisor': return '#8b5cf6'
      case 'escalation': return '#f59e0b'
      default: return '#6b7280'
    }
  }

  const getTypeClass = (type: string) => {
    switch (type) {
      case 'primary': return styles.typePrimary
      case 'supervisor': return styles.typeSupervisor
      case 'escalation': return styles.typeEscalation
      default: return ''
    }
  }

  // Loading State
  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <span>Loading agents...</span>
        </div>
      </div>
    )
  }

  // Error State
  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠️</span>
          <h2>Failed to load agents</h2>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <h1>AI Agents</h1>
        <p>Autonomous agents powering the call center with transparent, explainable decisions</p>
      </header>

      {/* Agent Grid */}
      <div className={styles.grid}>
        {agents.map((agent) => (
          <div
            key={agent.agentId}
            className={`${styles.card} ${selectedAgent?.agent.agentId === agent.agentId ? styles.selected : ''}`}
            onClick={() => handleAgentClick(agent.agentId)}
          >
            {/* Card Header */}
            <div className={styles.cardHeader}>
              <div 
                className={styles.iconWrapper}
                style={{ backgroundColor: `${getAgentColor(agent.type)}20` }}
              >
                {getAgentIcon(agent.type)}
              </div>
              <div className={styles.cardTitle}>
                <h3>{agent.name}</h3>
                <span className={`${styles.cardType} ${getTypeClass(agent.type)}`}>
                  {agent.type}
                </span>
              </div>
            </div>

            {/* Description */}
            <p className={styles.description}>{agent.description}</p>

            {/* Responsibilities */}
            <div className={styles.responsibilities}>
              <div className={styles.responsibilitiesTitle}>Responsibilities</div>
              <div className={styles.responsibilityList}>
                {agent.responsibilities.slice(0, 3).map((resp, i) => (
                  <span key={i} className={styles.responsibility}>{resp}</span>
                ))}
              </div>
            </div>

            {/* Metrics */}
            <div className={styles.metrics}>
              <div className={styles.metric}>
                <span className={styles.metricValue}>{agent.metrics.totalDecisions}</span>
                <span className={styles.metricLabel}>Decisions</span>
              </div>
              <div className={styles.metric}>
                <span className={styles.metricValue}>
                  {(agent.metrics.averageConfidence * 100).toFixed(0)}%
                </span>
                <span className={styles.metricLabel}>Avg Confidence</span>
              </div>
            </div>

            {/* Expanded Details */}
            {selectedAgent?.agent.agentId === agent.agentId && (
              <div className={styles.details}>
                {isLoadingDetail ? (
                  <div className={styles.detailsLoading}>Loading decisions...</div>
                ) : (
                  <>
                    <div className={styles.decisionsTitle}>Recent Decisions</div>
                    {selectedAgent.recentDecisions.length === 0 ? (
                      <div className={styles.noDecisions}>No recent decisions</div>
                    ) : (
                      <div className={styles.decisionsList}>
                        {selectedAgent.recentDecisions.map((decision, i) => (
                          <DecisionItem key={i} decision={decision} />
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function DecisionItem({ decision }: { decision: AnonymizedDecision }) {
  const getConfidenceClass = (confidence: number) => {
    if (confidence >= 0.8) return styles.confidenceHigh
    if (confidence >= 0.6) return styles.confidenceMedium
    return styles.confidenceLow
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  return (
    <div className={styles.decisionItem}>
      <span className={styles.decisionSummary}>{decision.summary}</span>
      <div className={styles.decisionMeta}>
        <span className={`${styles.confidence} ${getConfidenceClass(decision.confidence)}`}>
          {(decision.confidence * 100).toFixed(0)}%
        </span>
        <span className={styles.decisionTime}>{formatTime(decision.timestamp)}</span>
      </div>
    </div>
  )
}
