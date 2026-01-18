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
    // Toggle off if already selected
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'
    if (confidence >= 0.6) return '#f59e0b'
    return '#ef4444'
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

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner} />
        <span>Loading agents...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <span className={styles.errorIcon}>⚠️</span>
        <h2>Failed to load agents</h2>
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>AI Agents</h1>
          <p className={styles.subtitle}>
            Autonomous agents powering the call center with transparent, explainable decisions
          </p>
        </div>
      </header>

      {/* Agent Cards */}
      <div className={styles.agentGrid}>
        {agents.map((agent) => (
          <div
            key={agent.agentId}
            className={`${styles.agentCard} ${selectedAgent?.agent.agentId === agent.agentId ? styles.selected : ''}`}
            onClick={() => handleAgentClick(agent.agentId)}
            style={{ '--agent-color': getAgentColor(agent.type) } as React.CSSProperties}
          >
            {/* Card Header */}
            <div className={styles.cardHeader}>
              <div className={styles.agentIcon}>{getAgentIcon(agent.type)}</div>
              <div className={styles.agentInfo}>
                <h3 className={styles.agentName}>{agent.name}</h3>
                <span className={styles.agentType}>{agent.type} agent</span>
              </div>
              <span 
                className={styles.statusBadge}
                style={{ backgroundColor: agent.status === 'active' ? '#10b98120' : '#6b728020' }}
              >
                <span 
                  className={styles.statusDot}
                  style={{ backgroundColor: agent.status === 'active' ? '#10b981' : '#6b7280' }}
                />
                {agent.status}
              </span>
            </div>

            {/* Description */}
            <p className={styles.description}>{agent.description}</p>

            {/* Metrics */}
            <div className={styles.metrics}>
              <div className={styles.metric}>
                <span className={styles.metricValue}>{agent.metrics.totalDecisions}</span>
                <span className={styles.metricLabel}>Decisions</span>
              </div>
              <div className={styles.metric}>
                <span 
                  className={styles.metricValue}
                  style={{ color: getConfidenceColor(agent.metrics.averageConfidence) }}
                >
                  {(agent.metrics.averageConfidence * 100).toFixed(0)}%
                </span>
                <span className={styles.metricLabel}>Avg Confidence</span>
              </div>
            </div>

            {/* Decision Scope */}
            <div className={styles.scopeSection}>
              <h4 className={styles.scopeTitle}>Decision Scope</h4>
              <div className={styles.scopeGrid}>
                <div className={styles.scopeColumn}>
                  <span className={styles.scopeLabel}>
                    <span className={styles.scopeIcon}>✓</span> Autonomous
                  </span>
                  <ul className={styles.scopeList}>
                    {agent.decisionScope.autonomousActions.slice(0, 2).map((action, i) => (
                      <li key={i}>{action}</li>
                    ))}
                    {agent.decisionScope.autonomousActions.length > 2 && (
                      <li className={styles.moreItems}>
                        +{agent.decisionScope.autonomousActions.length - 2} more
                      </li>
                    )}
                  </ul>
                </div>
                <div className={styles.scopeColumn}>
                  <span className={styles.scopeLabel}>
                    <span className={styles.scopeIcon}>⚠️</span> Requires Review
                  </span>
                  <ul className={styles.scopeList}>
                    {agent.decisionScope.requiresReview.slice(0, 2).map((action, i) => (
                      <li key={i}>{action}</li>
                    ))}
                    {agent.decisionScope.requiresReview.length > 2 && (
                      <li className={styles.moreItems}>
                        +{agent.decisionScope.requiresReview.length - 2} more
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            </div>

            {/* Click hint */}
            <div className={styles.clickHint}>
              {selectedAgent?.agent.agentId === agent.agentId 
                ? 'Click to collapse' 
                : 'Click to view recent decisions'}
            </div>
          </div>
        ))}
      </div>

      {/* Recent Decisions Panel */}
      {selectedAgent && (
        <div className={styles.decisionsPanel}>
          <div className={styles.panelHeader}>
            <h2 className={styles.panelTitle}>
              {getAgentIcon(selectedAgent.agent.type)} {selectedAgent.agent.name}
              <span className={styles.panelSubtitle}>Recent Decisions</span>
            </h2>
            <button 
              className={styles.closeButton}
              onClick={() => setSelectedAgent(null)}
              aria-label="Close panel"
            >
              ×
            </button>
          </div>

          {isLoadingDetail ? (
            <div className={styles.panelLoading}>
              <div className={styles.spinner} />
              <span>Loading decisions...</span>
            </div>
          ) : selectedAgent.recentDecisions.length === 0 ? (
            <div className={styles.emptyDecisions}>
              No recent decisions recorded
            </div>
          ) : (
            <div className={styles.decisionsList}>
              {selectedAgent.recentDecisions.map((decision, index) => (
                <DecisionCard key={index} decision={decision} />
              ))}
            </div>
          )}

          {/* Capabilities */}
          <div className={styles.capabilitiesSection}>
            <h3 className={styles.sectionTitle}>Capabilities</h3>
            <div className={styles.capabilitiesGrid}>
              {selectedAgent.agent.capabilities.map((cap, i) => (
                <div key={i} className={styles.capabilityCard}>
                  <span className={styles.capabilityName}>{cap.name}</span>
                  <span className={styles.capabilityDesc}>{cap.description}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Responsibilities */}
          <div className={styles.responsibilitiesSection}>
            <h3 className={styles.sectionTitle}>Responsibilities</h3>
            <ul className={styles.responsibilitiesList}>
              {selectedAgent.agent.responsibilities.map((resp, i) => (
                <li key={i}>{resp}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}

// Decision Card Component
function DecisionCard({ decision }: { decision: AnonymizedDecision }) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return '#10b981'
    if (confidence >= 0.6) return '#f59e0b'
    return '#ef4444'
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
    <div className={styles.decisionCard}>
      <div className={styles.decisionHeader}>
        <span className={styles.decisionType}>{decision.decisionType}</span>
        <span className={styles.decisionTime}>{formatTime(decision.timestamp)}</span>
      </div>
      <p className={styles.decisionSummary}>{decision.summary}</p>
      <div className={styles.decisionMeta}>
        <span 
          className={styles.confidenceBadge}
          style={{ 
            backgroundColor: `${getConfidenceColor(decision.confidence)}20`,
            color: getConfidenceColor(decision.confidence),
          }}
        >
          {(decision.confidence * 100).toFixed(0)}% confidence
        </span>
        <span className={styles.processingTime}>⚡ {decision.processingTimeMs}ms</span>
      </div>
    </div>
  )
}
