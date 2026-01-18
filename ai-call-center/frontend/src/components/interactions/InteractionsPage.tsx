/**
 * Interactions Page
 * 
 * Enterprise SaaS view for browsing call history.
 * Displays interactions in a professional table format.
 */

import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchInteractions, InteractionSummary } from '../../services/apiClient'
import styles from './InteractionsPage.module.css'

interface TableState {
  page: number
  pageSize: number
  total: number
  hasMore: boolean
}

export function InteractionsPage() {
  const navigate = useNavigate()
  const [interactions, setInteractions] = useState<InteractionSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tableState, setTableState] = useState<TableState>({
    page: 1,
    pageSize: 15,
    total: 0,
    hasMore: false,
  })

  const loadInteractions = useCallback(async (page: number) => {
    setIsLoading(true)
    setError(null)

    const result = await fetchInteractions({ page, pageSize: tableState.pageSize })

    if (result.success && result.data) {
      setInteractions(result.data.interactions)
      setTableState(prev => ({
        ...prev,
        page: result.data!.page,
        total: result.data!.total,
        hasMore: result.data!.hasMore,
      }))
    } else {
      setError(result.error?.message || 'Failed to load interactions')
    }

    setIsLoading(false)
  }, [tableState.pageSize])

  useEffect(() => {
    loadInteractions(1)
  }, [loadInteractions])

  const handleRowClick = (interactionId: string) => {
    navigate(`/interactions/${interactionId}`)
  }

  const handlePrevPage = () => {
    if (tableState.page > 1) {
      loadInteractions(tableState.page - 1)
    }
  }

  const handleNextPage = () => {
    if (tableState.hasMore) {
      loadInteractions(tableState.page + 1)
    }
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

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'initiated':
      case 'in_progress':
        return styles.statusActive
      case 'completed':
        return styles.statusCompleted
      case 'escalated':
        return styles.statusEscalated
      case 'abandoned':
        return styles.statusAbandoned
      default:
        return ''
    }
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      initiated: 'Active',
      in_progress: 'In Progress',
      completed: 'Completed',
      escalated: 'Escalated',
      abandoned: 'Abandoned',
    }
    return labels[status] || status
  }

  const getResolution = (interaction: InteractionSummary) => {
    if (interaction.wasEscalated) {
      return <span className={styles.resolutionNo}>Escalated</span>
    }
    if (interaction.status === 'completed') {
      return <span className={styles.resolutionYes}>✓ Resolved</span>
    }
    return <span className={styles.resolutionNo}>—</span>
  }

  const formatCallId = (id: string) => {
    return id.substring(0, 8).toUpperCase()
  }

  // Loading State
  if (isLoading && interactions.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <span>Loading interactions...</span>
        </div>
      </div>
    )
  }

  // Error State
  if (error && interactions.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <span className={styles.errorIcon}>⚠️</span>
          <h2>Failed to load interactions</h2>
          <p>{error}</p>
          <button className={styles.pageBtn} onClick={() => loadInteractions(1)}>
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <h1>Interactions</h1>
        <p>{tableState.total} total call{tableState.total !== 1 ? 's' : ''} • Page {tableState.page}</p>
      </header>

      {/* Empty State */}
      {interactions.length === 0 ? (
        <div className={styles.empty}>
          <span className={styles.emptyIcon}>📞</span>
          <h2>No interactions yet</h2>
          <p>Start a call from the Demo page to see interactions here.</p>
        </div>
      ) : (
        <>
          {/* Table */}
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Call ID</th>
                  <th>Started</th>
                  <th>Channel</th>
                  <th>Status</th>
                  <th>Resolution</th>
                  <th>Messages</th>
                </tr>
              </thead>
              <tbody>
                {interactions.map((interaction) => (
                  <tr
                    key={interaction.interactionId}
                    onClick={() => handleRowClick(interaction.interactionId)}
                  >
                    <td className={styles.idCell}>{formatCallId(interaction.interactionId)}</td>
                    <td>{formatDate(interaction.startedAt)}</td>
                    <td>
                      <span className={styles.channel}>
                        {interaction.channel === 'voice' ? '🎙️' : '💬'} {interaction.channel}
                      </span>
                    </td>
                    <td>
                      <span className={`${styles.status} ${getStatusClass(interaction.status)}`}>
                        {getStatusLabel(interaction.status)}
                      </span>
                    </td>
                    <td className={styles.resolution}>{getResolution(interaction)}</td>
                    <td>{interaction.messageCount}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            <div className={styles.pagination}>
              <span className={styles.pageInfo}>
                Showing {interactions.length} of {tableState.total} interactions
              </span>
              <div className={styles.pageButtons}>
                <button
                  className={styles.pageBtn}
                  onClick={handlePrevPage}
                  disabled={tableState.page <= 1 || isLoading}
                >
                  ← Previous
                </button>
                <button
                  className={styles.pageBtn}
                  onClick={handleNextPage}
                  disabled={!tableState.hasMore || isLoading}
                >
                  Next →
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
