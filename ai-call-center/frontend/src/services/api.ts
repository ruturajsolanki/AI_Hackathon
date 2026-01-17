/**
 * API Service
 * 
 * Handles all communication with the backend.
 */

const API_BASE = '/api'

export interface ApiResponse<T> {
  data: T
  success: boolean
  error?: string
}

export interface StartInteractionResponse {
  interaction_id: string
  status: string
  channel: string
  started_at: string
  initial_response: string | null
  message: string
}

export interface SendMessageResponse {
  interaction_id: string
  message_processed: boolean
  response_content: string | null
  should_escalate: boolean
  escalation_type: string | null
  escalation_reason: string | null
  confidence_level: string | null
  processing_time_ms: number
}

export interface InteractionStatus {
  interaction_id: string
  phase: string
  turn_count: number
  is_escalated: boolean
  is_completed: boolean
  current_intent: string | null
  current_emotion: string | null
  last_updated: string
}

/**
 * Start a new interaction session.
 */
export async function startInteraction(params: {
  customerId?: string
  channel: 'voice' | 'chat'
  initialMessage?: string
}): Promise<ApiResponse<StartInteractionResponse>> {
  try {
    const response = await fetch(`${API_BASE}/interactions/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        customer_id: params.customerId,
        channel: params.channel,
        initial_message: params.initialMessage,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      return {
        data: null as any,
        success: false,
        error: error.detail || 'Failed to start interaction',
      }
    }

    const data = await response.json()
    return {
      data,
      success: true,
    }
  } catch (error) {
    return {
      data: null as any,
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Send a message in an active interaction.
 */
export async function sendMessage(params: {
  interactionId: string
  content: string
}): Promise<ApiResponse<SendMessageResponse>> {
  try {
    const response = await fetch(
      `${API_BASE}/interactions/${params.interactionId}/message`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: params.content,
        }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return {
        data: null as any,
        success: false,
        error: error.detail || 'Failed to send message',
      }
    }

    const data = await response.json()
    return {
      data,
      success: true,
    }
  } catch (error) {
    return {
      data: null as any,
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * End an interaction session.
 */
export async function endInteraction(params: {
  interactionId: string
  reason?: string
}): Promise<ApiResponse<{ success: boolean }>> {
  try {
    const response = await fetch(
      `${API_BASE}/interactions/${params.interactionId}/end`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason: params.reason,
        }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return {
        data: { success: false },
        success: false,
        error: error.detail || 'Failed to end interaction',
      }
    }

    return {
      data: { success: true },
      success: true,
    }
  } catch (error) {
    return {
      data: { success: false },
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Get current interaction status.
 */
export async function getInteractionStatus(
  interactionId: string
): Promise<ApiResponse<InteractionStatus>> {
  try {
    const response = await fetch(
      `${API_BASE}/interactions/${interactionId}/status`
    )

    if (!response.ok) {
      const error = await response.json()
      return {
        data: null as any,
        success: false,
        error: error.detail || 'Failed to get status',
      }
    }

    const data = await response.json()
    return {
      data,
      success: true,
    }
  } catch (error) {
    return {
      data: null as any,
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    }
  }
}

/**
 * Get dashboard metrics.
 */
export async function getDashboardMetrics(): Promise<ApiResponse<{
  totalInteractions: number
  activeInteractions: number
  resolutionRate: number
  escalationRate: number
  averageConfidence: number
  averageCsat: number
}>> {
  // For now, return mock data since we don't have a metrics endpoint yet
  return {
    data: {
      totalInteractions: 347,
      activeInteractions: 12,
      resolutionRate: 0.87,
      escalationRate: 0.13,
      averageConfidence: 0.84,
      averageCsat: 4.2,
    },
    success: true,
  }
}

/**
 * Check backend health.
 */
export async function checkHealth(): Promise<ApiResponse<{
  status: string
  version: string
}>> {
  try {
    const response = await fetch('/health')
    
    if (!response.ok) {
      return {
        data: null as any,
        success: false,
        error: 'Backend unhealthy',
      }
    }

    const data = await response.json()
    return {
      data,
      success: true,
    }
  } catch (error) {
    return {
      data: null as any,
      success: false,
      error: 'Backend unreachable',
    }
  }
}
