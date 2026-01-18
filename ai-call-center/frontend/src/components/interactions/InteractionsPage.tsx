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

  const getResolution = (interaction: InteractionSummary) => {
    if (interaction.wasEscalated) {
      return <span className={styles.escalated}>Escalated</span>
    }
    if (interaction.status === 'completed') {
      return <span className={styles.resolved}>Resolved by AI</span>
    }
    if (interaction.status === 'initiated' || interaction.status === 'in_progress') {
      return <span className={styles.pending}>In Progress</span>
    }
    return <span className={styles.unknown}>—</span>
  }

  const formatCallId = (id: string) => {
    return id.substring(0, 8).toUpperCase()
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>Interactions</h1>
          <p className={styles.subtitle}>
            {tableState.total} total call{tableState.total !== 1 ? 's' : ''}
          </p>
        </div>
        <button 
          className={styles.refreshButton}
          onClick={() => loadInteractions(tableState.page)}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
      </header>

      {/* Error State */}
      {error && (
        <div className={styles.errorBanner}>
          <span className={styles.errorIcon}>⚠️</span>
          <span>{error}</span>
          <button onClick={() => loadInteractions(tableState.page)}>Retry</button>
        </div>
      )}

      {/* Table */}
      <div className={styles.tableContainer}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Call ID</th>
              <th>Start Time</th>
              <th>Status</th>
              <th>Resolution</th>
              <th className={styles.hideMobile}>Channel</th>
              <th className={styles.hideMobile}>Messages</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && interactions.length === 0 ? (
              <tr>
                <td colSpan={6} className={styles.loadingRow}>
                  <div className={styles.spinner} />
                  <span>Loading interactions...</span>
                </td>
              </tr>
            ) : interactions.length === 0 ? (
              <tr>
                <td colSpan={6} className={styles.emptyRow}>
                  <span className={styles.emptyIcon}>📞</span>
                  <span>No interactions found</span>
                </td>
              </tr>
            ) : (
              interactions.map((interaction) => (
                <tr
                  key={interaction.interactionId}
                  onClick={() => handleRowClick(interaction.interactionId)}
                  className={styles.clickableRow}
                >
                  <td>
                    <code className={styles.callId}>
                      {formatCallId(interaction.interactionId)}
                    </code>
                  </td>
                  <td className={styles.dateCell}>
                    {formatDate(interaction.startedAt)}
                  </td>
                  <td>{getStatusBadge(interaction.status)}</td>
                  <td>{getResolution(interaction)}</td>
                  <td className={styles.hideMobile}>
                    <span className={styles.channel}>
                      {interaction.channel === 'voice' ? '🎙️' : '💬'} {interaction.channel}
                    </span>
                  </td>
                  <td className={styles.hideMobile}>
                    <span className={styles.messageCount}>
                      {interaction.messageCount}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {interactions.length > 0 && (
        <div className={styles.pagination}>
          <button
            className={styles.paginationButton}
            onClick={handlePrevPage}
            disabled={tableState.page <= 1 || isLoading}
          >
            ← Previous
          </button>
          <span className={styles.pageInfo}>
            Page {tableState.page} of {Math.ceil(tableState.total / tableState.pageSize) || 1}
          </span>
          <button
            className={styles.paginationButton}
            onClick={handleNextPage}
            disabled={!tableState.hasMore || isLoading}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
