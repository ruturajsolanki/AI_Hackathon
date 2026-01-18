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
  
  // Quick reply suggestions
  suggestedReplies?: string[]
  detectedIntent?: string
  detectedEmotion?: string
  
  // Source attribution for transparency
  sourceAttribution?: string | null
  
  // Sentiment tracking
  sentimentTrend?: 'improving' | 'declining' | 'stable' | null
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

// Streaming Types
export interface StreamingEventStatus {
  event: 'status'
  data: {
    phase: string
    message: string
  }
}

export interface StreamingEventToken {
  event: 'token'
  data: {
    token: string
    accumulated: string
    progress: number
  }
}

export interface StreamingEventComplete {
  event: 'complete'
  data: {
    response: string
    shouldEscalate: boolean
    processingTimeMs: number
    escalationType: string | null
    escalationReason: string | null
    confidenceLevel: string | null
    confidenceScore: number | null
    intent: string | null
    emotion: string | null
  }
}

export interface StreamingEventError {
  event: 'error'
  data: {
    message: string
  }
}

export type StreamingEvent = 
  | StreamingEventStatus 
  | StreamingEventToken 
  | StreamingEventComplete 
  | StreamingEventError

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
   * Send a message and receive streaming response via SSE.
   * 
   * Returns an async generator that yields streaming events:
   * - status: Processing status updates
   * - token: Individual response tokens  
   * - complete: Final result with metadata
   * - error: Error information
   */
  async *sendMessageStream(
    callId: string,
    message: string,
    params: Omit<SendMessageParams, 'content'> = {}
  ): AsyncGenerator<StreamingEvent> {
    if (!callId) {
      yield {
        event: 'error',
        data: { message: 'Call ID is required' }
      }
      return
    }

    const url = `${this.baseUrl}/api/interactions/${callId}/message/stream`
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: this.defaultHeaders,
        body: JSON.stringify({
          content: message,
          metadata: params.metadata,
        }),
      })

      if (!response.ok) {
        yield {
          event: 'error',
          data: { message: `HTTP ${response.status}: ${response.statusText}` }
        }
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        yield {
          event: 'error',
          data: { message: 'Stream not supported' }
        }
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        
        // Parse SSE events from buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6))
              yield this.transformResponse<StreamingEvent>(eventData)
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }
    } catch (err) {
      yield {
        event: 'error',
        data: { message: err instanceof Error ? err.message : 'Stream failed' }
      }
    }
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

  // ===========================================================================
  // Configuration APIs
  // ===========================================================================

  /**
   * Set the LLM API key.
   * The key is stored in-memory on the server and never returned.
   */
  async setLlmApiKey(apiKey: string, provider: string = 'openai'): Promise<ApiResult<SetApiKeyResponse>> {
    return this.request<SetApiKeyResponse>('POST', '/api/config/llm', {
      api_key: apiKey,
      provider,
    })
  }

  /**
   * Get the LLM configuration status.
   */
  async getLlmStatus(): Promise<ApiResult<LlmStatusResponse>> {
    return this.request<LlmStatusResponse>('GET', '/api/config/llm/status')
  }

  /**
   * Validate the configured LLM API key.
   */
  async validateLlmKey(): Promise<ApiResult<LlmValidationResponse>> {
    return this.request<LlmValidationResponse>('POST', '/api/config/llm/validate')
  }

  /**
   * Clear the configured LLM API key.
   */
  async clearLlmKey(): Promise<ApiResult<void>> {
    return this.request<void>('DELETE', '/api/config/llm')
  }

  // ===========================================================================
  // Agent Configuration APIs
  // ===========================================================================

  /**
   * Fetch all agent configurations.
   */
  async fetchAgentConfigs(): Promise<ApiResult<AgentConfigSummary[]>> {
    return this.request<AgentConfigSummary[]>('GET', '/api/agent-config')
  }

  /**
   * Fetch single agent configuration.
   */
  async fetchAgentConfig(agentId: string): Promise<ApiResult<AgentConfigDetail>> {
    return this.request<AgentConfigDetail>('GET', `/api/agent-config/${agentId}`)
  }

  /**
   * Update agent configuration.
   */
  async updateAgentConfig(
    agentId: string,
    params: UpdateAgentConfigParams
  ): Promise<ApiResult<AgentConfigDetail>> {
    const body: Record<string, unknown> = {}
    if (params.systemPrompt !== undefined) body.system_prompt = params.systemPrompt
    if (params.userPromptTemplate !== undefined) body.user_prompt_template = params.userPromptTemplate
    if (params.model !== undefined) body.model = params.model
    if (params.temperature !== undefined) body.temperature = params.temperature
    if (params.maxTokens !== undefined) body.max_tokens = params.maxTokens
    if (params.topP !== undefined) body.top_p = params.topP
    if (params.confidenceThreshold !== undefined) body.confidence_threshold = params.confidenceThreshold
    if (params.fallbackEnabled !== undefined) body.fallback_enabled = params.fallbackEnabled
    if (params.outputSchema !== undefined) body.output_schema = params.outputSchema

    return this.request<AgentConfigDetail>('PUT', `/api/agent-config/${agentId}`, body)
  }

  /**
   * Reset agent configuration to defaults.
   */
  async resetAgentConfig(agentId: string): Promise<ApiResult<AgentConfigDetail>> {
    return this.request<AgentConfigDetail>('POST', `/api/agent-config/${agentId}/reset`)
  }

  /**
   * Test a prompt configuration.
   */
  async testPrompt(agentId: string, params: TestPromptParams): Promise<ApiResult<TestPromptResponse>> {
    return this.request<TestPromptResponse>('POST', `/api/agent-config/${agentId}/test`, {
      system_prompt: params.systemPrompt,
      user_prompt: params.userPrompt,
      model: params.model ?? 'gpt-4o-mini',
      temperature: params.temperature ?? 0.3,
      test_input: params.testInput ?? 'Hello, I have a question.',
    })
  }

  /**
   * Fetch agent configuration history.
   */
  async fetchAgentConfigHistory(agentId: string, limit: number = 10): Promise<ApiResult<Array<{
    agentId: string
    action: string
    timestamp: string
    previous?: Record<string, unknown>
  }>>> {
    return this.request('GET', `/api/agent-config/${agentId}/history?limit=${limit}`)
  }

  // ===========================================================================
  // Authentication APIs
  // ===========================================================================

  /**
   * Login and get tokens.
   */
  async login(params: LoginParams): Promise<ApiResult<AuthTokens>> {
    // OAuth2 expects form data, but we use JSON
    const formData = new URLSearchParams()
    formData.append('username', params.email)
    formData.append('password', params.password)

    const url = `${this.baseUrl}/api/auth/login`
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      })

      const data = await response.json()

      if (!response.ok) {
        return {
          data: null,
          error: {
            code: 'AUTH_ERROR',
            message: data?.detail ?? 'Login failed',
            status: response.status,
          },
          success: false,
        }
      }

      return {
        data: this.transformResponse<AuthTokens>(data),
        error: null,
        success: true,
      }
    } catch {
      return {
        data: null,
        error: {
          code: 'NETWORK_ERROR',
          message: 'Network request failed',
          status: 0,
        },
        success: false,
      }
    }
  }

  /**
   * Refresh access token.
   */
  async refreshToken(refreshToken: string): Promise<ApiResult<AuthTokens>> {
    return this.request<AuthTokens>('POST', '/api/auth/refresh', {
      refresh_token: refreshToken,
    })
  }

  /**
   * Register new user.
   */
  async register(params: RegisterParams): Promise<ApiResult<UserInfo>> {
    return this.request<UserInfo>('POST', '/api/auth/register', {
      email: params.email,
      password: params.password,
      full_name: params.fullName,
    })
  }

  /**
   * Get current user info.
   */
  async getCurrentUser(): Promise<ApiResult<UserInfo>> {
    return this.request<UserInfo>('GET', '/api/auth/me')
  }

  /**
   * Check auth status.
   */
  async getAuthStatus(): Promise<ApiResult<AuthStatusResponse>> {
    return this.request<AuthStatusResponse>('GET', '/api/auth/status')
  }

  /**
   * Set auth token for subsequent requests.
   */
  setAuthToken(token: string): void {
    this.defaultHeaders['Authorization'] = `Bearer ${token}`
  }

  /**
   * Clear auth token.
   */
  clearAuthToken(): void {
    delete this.defaultHeaders['Authorization']
  }
}

// -----------------------------------------------------------------------------
// Configuration Types
// -----------------------------------------------------------------------------

export interface SetApiKeyResponse {
  success: boolean
  message: string
  configuredAt: string
}

export interface LlmStatusResponse {
  configured: boolean
  provider: string
  configuredAt: string | null
  validated: boolean | null
  lastValidatedAt: string | null
  message: string
}

export interface LlmValidationResponse {
  valid: boolean
  message: string
  testedAt: string
}

// Agent Configuration Types
export interface AgentConfigSummary {
  agentId: string
  agentName: string
  agentType: 'primary' | 'supervisor' | 'escalation'
  description: string
  model: string
  temperature: number
  confidenceThreshold: number
  isCustom: boolean
  version: number
  updatedAt: string
}

export interface AgentConfigDetail extends AgentConfigSummary {
  systemPrompt: string
  userPromptTemplate: string
  outputSchema: Record<string, unknown>
  maxTokens: number
  topP: number
  fallbackEnabled: boolean
  createdAt: string
  updatedBy: string | null
}

export interface UpdateAgentConfigParams {
  systemPrompt?: string
  userPromptTemplate?: string
  model?: string
  temperature?: number
  maxTokens?: number
  topP?: number
  confidenceThreshold?: number
  fallbackEnabled?: boolean
  outputSchema?: Record<string, unknown>
}

export interface TestPromptParams {
  systemPrompt: string
  userPrompt: string
  model?: string
  temperature?: number
  testInput?: string
}

export interface TestPromptResponse {
  success: boolean
  output?: string
  parsedOutput?: Record<string, unknown>
  latencyMs: number
  tokensUsed?: number
  error?: string
}

// Authentication Types
export interface LoginParams {
  email: string
  password: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  tokenType: string
  expiresIn: number
}

export interface UserInfo {
  userId: string
  email: string
  fullName: string
  role: 'admin' | 'user'
  isActive: boolean
  createdAt: string
}

export interface RegisterParams {
  email: string
  password: string
  fullName: string
}

export interface AuthStatusResponse {
  available: boolean
  demoCredentials?: {
    email: string
    password: string
  }
  message: string
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

export const sendMessageStream = (callId: string, message: string) =>
  apiClient.sendMessageStream(callId, message)

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

// Configuration exports
export const setLlmApiKey = (apiKey: string, provider?: string) => 
  apiClient.setLlmApiKey(apiKey, provider)

export const getLlmStatus = () => apiClient.getLlmStatus()

export const validateLlmKey = () => apiClient.validateLlmKey()

export const clearLlmKey = () => apiClient.clearLlmKey()

// Agent Configuration exports
export const fetchAgentConfigs = () => apiClient.fetchAgentConfigs()

export const fetchAgentConfig = (agentId: string) => apiClient.fetchAgentConfig(agentId)

export const updateAgentConfig = (agentId: string, params: UpdateAgentConfigParams) =>
  apiClient.updateAgentConfig(agentId, params)

export const resetAgentConfig = (agentId: string) => apiClient.resetAgentConfig(agentId)

export const testPrompt = (agentId: string, params: TestPromptParams) =>
  apiClient.testPrompt(agentId, params)

export const fetchAgentConfigHistory = (agentId: string, limit?: number) =>
  apiClient.fetchAgentConfigHistory(agentId, limit)

// Authentication exports
export const login = (params: LoginParams) => apiClient.login(params)

export const refreshToken = (token: string) => apiClient.refreshToken(token)

export const register = (params: RegisterParams) => apiClient.register(params)

export const getCurrentUser = () => apiClient.getCurrentUser()

export const getAuthStatus = () => apiClient.getAuthStatus()

export const setAuthToken = (token: string) => apiClient.setAuthToken(token)

export const clearAuthToken = () => apiClient.clearAuthToken()

export { apiClient }
export default apiClient
