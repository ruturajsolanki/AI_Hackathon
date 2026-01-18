/**
 * API Client
 * 
 * Centralized API abstraction for the AI Call Center SaaS.
 * Handles all HTTP communication with the backend.
 */

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

export interface ApiConfig {
  baseUrl: string
  timeout?: number
  headers?: Record<string, string>
}

export interface ApiError {
  code: string
  message: string
  status: number
  details?: Record<string, unknown>
}

export interface ApiResult<T> {
  data: T | null
  error: ApiError | null
  success: boolean
}

// Call Types
export interface StartCallParams {
  customerId?: string
  channel?: 'voice' | 'chat'
  initialMessage?: string
  metadata?: Record<string, unknown>
}

export interface StartCallResponse {
  interactionId: string  // Backend returns interaction_id → interactionId
  callId?: string        // Alias for backwards compatibility
  status: string
  channel: string
  startedAt: string
  initialResponse: string | null
  message?: string
}

export interface SendMessageParams {
  content: string
  metadata?: Record<string, unknown>
}

export interface SendMessageResponse {
  callId: string
  messageProcessed: boolean
  responseContent: string | null
  shouldEscalate: boolean
  escalationType: string | null
  escalationReason: string | null
  confidenceLevel: 'high' | 'medium' | 'low' | null
  processingTimeMs: number
  agentDecisions?: AgentDecision[]
}

export interface AgentDecision {
  agentType: 'primary' | 'supervisor' | 'escalation'
  confidence: number
  action: string
  reasoning?: string
  timestamp: string
}

export interface EndCallParams {
  reason?: string
  feedback?: {
    rating?: number
    comment?: string
  }
}

export interface EndCallResponse {
  callId: string
  endedAt: string
  duration: number
  turnCount: number
  wasEscalated: boolean
  resolutionStatus: 'resolved' | 'escalated' | 'abandoned'
}

export interface CallsPerHourItem {
  hour: number
  count: number
}

export interface AnalyticsResponse {
  totalInteractions: number
  activeInteractions: number
  resolutionRate: number
  escalationRate: number
  averageConfidence: number
  averageCsat: number
  averageResolutionTime: number
  callsPerHour: CallsPerHourItem[]
}

// History Types
export interface InteractionSummary {
  interactionId: string
  customerId: string | null
  channel: string
  status: string
  startedAt: string
  endedAt: string | null
  durationSeconds: number | null
  messageCount: number
  wasEscalated: boolean
}

export interface InteractionListResponse {
  interactions: InteractionSummary[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface MessageItem {
  messageId: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: string
  intent: string | null
  emotion: string | null
  confidence: number | null
}

export interface DecisionItem {
  decisionId: string
  agentType: 'primary' | 'supervisor' | 'escalation'
  summary: string
  confidence: number
  confidenceLevel: string
  timestamp: string
  processingTimeMs: number
}

export interface InteractionDetail {
  interactionId: string
  customerId: string | null
  channel: string
  status: string
  startedAt: string
  endedAt: string | null
  durationSeconds: number | null
  messages: MessageItem[]
  decisions: DecisionItem[]
  wasEscalated: boolean
  resolutionSummary: string | null
}

// Agent Types
export interface AgentCapability {
  name: string
  description: string
}

export interface DecisionScope {
  autonomousActions: string[]
  requiresReview: string[]
  cannotPerform: string[]
}

export interface AgentMetadata {
  agentId: string
  name: string
  type: string
  description: string
  status: string
  responsibilities: string[]
  capabilities: AgentCapability[]
  decisionScope: DecisionScope
  metrics: {
    totalDecisions: number
    averageConfidence: number
    decisionsLast24h?: number
  }
}

export interface AgentListResponse {
  agents: AgentMetadata[]
  total: number
}

export interface AnonymizedDecision {
  decisionType: string
  summary: string
  confidence: number
  confidenceLevel: string
  processingTimeMs: number
  timestamp: string
}

export interface AgentDetailResponse {
  agent: AgentMetadata
  recentDecisions: AnonymizedDecision[]
  totalDecisions: number
}

// Analytics Types
export interface AnalyticsSummary {
  totalInteractions: number
  activeInteractions: number
  completedInteractions: number
  escalatedInteractions: number
  resolutionRate: number
  escalationRate: number
  averageConfidence: number
  averageDurationSeconds: number
  averageMessagesPerCall: number
}

export interface CallsPerHourItem {
  hour: number
  count: number
}

export interface ChannelBreakdown {
  channel: string
  count: number
  percentage: number
}

export interface StatusBreakdown {
  status: string
  count: number
  percentage: number
}

export interface AgentPerformanceItem {
  agentType: string
  totalDecisions: number
  averageConfidence: number
  averageProcessingMs: number
}

export interface AnalyticsOverviewResponse {
  summary: AnalyticsSummary
  callsPerHour: CallsPerHourItem[]
  channelBreakdown: ChannelBreakdown[]
  statusBreakdown: StatusBreakdown[]
  agentPerformance: AgentPerformanceItem[]
  periodStart: string
  periodEnd: string
}

export interface DailyTrendItem {
  date: string
  total: number
  resolved: number
  escalated: number
  averageConfidence: number
}

export interface AnalyticsTrendsResponse {
  daily: DailyTrendItem[]
  periodStart: string
  periodEnd: string
  totalDays: number
}

// -----------------------------------------------------------------------------
// API Client Class
// -----------------------------------------------------------------------------

class ApiClient {
  private baseUrl: string
  private timeout: number
  private defaultHeaders: Record<string, string>

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, '')
    this.timeout = config.timeout ?? 30000
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    }
  }

  // ---------------------------------------------------------------------------
  // Private Methods
  // ---------------------------------------------------------------------------

  private async request<T>(
    method: string,
    endpoint: string,
    body?: unknown
  ): Promise<ApiResult<T>> {
    const url = `${this.baseUrl}${endpoint}`
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.timeout)

    try {
      const response = await fetch(url, {
        method,
        headers: this.defaultHeaders,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      const contentType = response.headers.get('content-type')
      const isJson = contentType?.includes('application/json')
      const data = isJson ? await response.json() : null

      if (!response.ok) {
        return {
          data: null,
          error: {
            code: data?.code ?? 'API_ERROR',
            message: data?.detail ?? data?.message ?? response.statusText,
            status: response.status,
            details: data,
          },
          success: false,
        }
      }

      return {
        data: this.transformResponse<T>(data),
        error: null,
        success: true,
      }
    } catch (err) {
      clearTimeout(timeoutId)

      if (err instanceof Error && err.name === 'AbortError') {
        return {
          data: null,
          error: {
            code: 'TIMEOUT',
            message: 'Request timed out',
            status: 408,
          },
          success: false,
        }
      }

      return {
        data: null,
        error: {
          code: 'NETWORK_ERROR',
          message: err instanceof Error ? err.message : 'Network request failed',
          status: 0,
        },
        success: false,
      }
    }
  }

  private transformResponse<T>(data: unknown): T {
    // Transform snake_case to camelCase for frontend consumption
    if (data === null || data === undefined) {
      return data as T
    }

    if (Array.isArray(data)) {
      return data.map((item) => this.transformResponse(item)) as T
    }

    if (typeof data === 'object') {
      const transformed: Record<string, unknown> = {}
      for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
        const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
        transformed[camelKey] = this.transformResponse(value)
      }
      return transformed as T
    }

    return data as T
  }

  // ---------------------------------------------------------------------------
  // Public API Methods
  // ---------------------------------------------------------------------------

  /**
   * Start a new call session.
   */
  async startCall(params: StartCallParams = {}): Promise<ApiResult<StartCallResponse>> {
    return this.request<StartCallResponse>('POST', '/api/interactions/start', {
      customer_id: params.customerId,
      channel: params.channel ?? 'chat',
      initial_message: params.initialMessage,
      metadata: params.metadata,
    })
  }

  /**
   * Send a message in an active call.
   */
  async sendMessage(
    callId: string,
    message: string,
    params: Omit<SendMessageParams, 'content'> = {}
  ): Promise<ApiResult<SendMessageResponse>> {
    if (!callId) {
      return {
        data: null,
        error: {
          code: 'INVALID_PARAMS',
          message: 'Call ID is required',
          status: 400,
        },
        success: false,
      }
    }

    return this.request<SendMessageResponse>(
      'POST',
      `/api/interactions/${callId}/message`,
      {
        content: message,
        metadata: params.metadata,
      }
    )
  }

  /**
   * End an active call.
   */
  async endCall(
    callId: string,
    params: EndCallParams = {}
  ): Promise<ApiResult<EndCallResponse>> {
    if (!callId) {
      return {
        data: null,
        error: {
          code: 'INVALID_PARAMS',
          message: 'Call ID is required',
          status: 400,
        },
        success: false,
      }
    }

    return this.request<EndCallResponse>(
      'POST',
      `/api/interactions/${callId}/end`,
      {
        reason: params.reason,
        feedback: params.feedback,
      }
    )
  }

  /**
   * Fetch analytics data.
   */
  async fetchAnalytics(): Promise<ApiResult<AnalyticsResponse>> {
    return this.request<AnalyticsResponse>('GET', '/api/analytics/metrics')
  }

  /**
   * Get call status.
   */
  async getCallStatus(callId: string): Promise<ApiResult<{
    callId: string
    phase: string
    turnCount: number
    isEscalated: boolean
    isCompleted: boolean
    currentIntent: string | null
    currentEmotion: string | null
    lastUpdated: string
  }>> {
    if (!callId) {
      return {
        data: null,
        error: {
          code: 'INVALID_PARAMS',
          message: 'Call ID is required',
          status: 400,
        },
        success: false,
      }
    }

    return this.request('GET', `/api/interactions/${callId}/status`)
  }

  /**
   * Health check.
   */
  async healthCheck(): Promise<ApiResult<{ status: string; version: string }>> {
    return this.request('GET', '/health')
  }

  /**
   * Fetch interaction history list.
   */
  async fetchInteractions(params: {
    page?: number
    pageSize?: number
    status?: string
  } = {}): Promise<ApiResult<InteractionListResponse>> {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.set('page', params.page.toString())
    if (params.pageSize) queryParams.set('page_size', params.pageSize.toString())
    if (params.status) queryParams.set('status', params.status)
    
    const queryString = queryParams.toString()
    const endpoint = `/api/history/interactions${queryString ? `?${queryString}` : ''}`
    return this.request<InteractionListResponse>('GET', endpoint)
  }

  /**
   * Fetch single interaction details.
   */
  async fetchInteractionDetail(interactionId: string): Promise<ApiResult<InteractionDetail>> {
    if (!interactionId) {
      return {
        data: null,
        error: {
          code: 'INVALID_PARAMS',
          message: 'Interaction ID is required',
          status: 400,
        },
        success: false,
      }
    }
    return this.request<InteractionDetail>('GET', `/api/history/interactions/${interactionId}`)
  }

  /**
   * Fetch all agents.
   */
  async fetchAgents(): Promise<ApiResult<AgentListResponse>> {
    return this.request<AgentListResponse>('GET', '/api/agents')
  }

  /**
   * Fetch single agent details with recent decisions.
   */
  async fetchAgentDetail(agentId: string): Promise<ApiResult<AgentDetailResponse>> {
    if (!agentId) {
      return {
        data: null,
        error: {
          code: 'INVALID_PARAMS',
          message: 'Agent ID is required',
          status: 400,
        },
        success: false,
      }
    }
    return this.request<AgentDetailResponse>('GET', `/api/agents/${agentId}`)
  }

  /**
   * Fetch analytics overview.
   */
  async fetchAnalyticsOverview(days: number = 7): Promise<ApiResult<AnalyticsOverviewResponse>> {
    return this.request<AnalyticsOverviewResponse>('GET', `/api/analytics/overview?days=${days}`)
  }

  /**
   * Fetch analytics trends.
   */
  async fetchAnalyticsTrends(days: number = 7): Promise<ApiResult<AnalyticsTrendsResponse>> {
    return this.request<AnalyticsTrendsResponse>('GET', `/api/analytics/trends?days=${days}`)
  }
}

// -----------------------------------------------------------------------------
// Singleton Instance
// -----------------------------------------------------------------------------

const apiClient = new ApiClient({
  baseUrl: import.meta.env.VITE_API_URL ?? '',
  timeout: 30000,
})

// -----------------------------------------------------------------------------
// Exported Functions
// -----------------------------------------------------------------------------

export const startCall = (params?: StartCallParams) => apiClient.startCall(params)

export const sendMessage = (callId: string, message: string) =>
  apiClient.sendMessage(callId, message)

export const endCall = (callId: string, params?: EndCallParams) =>
  apiClient.endCall(callId, params)

export const fetchAnalytics = () => apiClient.fetchAnalytics()

export const getCallStatus = (callId: string) => apiClient.getCallStatus(callId)

export const healthCheck = () => apiClient.healthCheck()

export const fetchInteractions = (params?: { page?: number; pageSize?: number; status?: string }) =>
  apiClient.fetchInteractions(params)

export const fetchInteractionDetail = (interactionId: string) =>
  apiClient.fetchInteractionDetail(interactionId)

export const fetchAgents = () => apiClient.fetchAgents()

export const fetchAgentDetail = (agentId: string) => apiClient.fetchAgentDetail(agentId)

export const fetchAnalyticsOverview = (days?: number) => apiClient.fetchAnalyticsOverview(days)

export const fetchAnalyticsTrends = (days?: number) => apiClient.fetchAnalyticsTrends(days)

export { apiClient }
export default apiClient
