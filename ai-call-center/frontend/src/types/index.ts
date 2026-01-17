/**
 * Core type definitions for the AI Call Center frontend.
 */

// Interaction Types
export interface Interaction {
  id: string
  customerId?: string
  channel: 'voice' | 'chat'
  status: 'active' | 'resolved' | 'escalated' | 'abandoned'
  startedAt: string
  endedAt?: string
  turnCount: number
}

// Message Types
export interface Message {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: string
  intent?: string
  emotion?: string
  confidence?: number
}

// Agent Decision Types
export interface AgentDecision {
  id: string
  agentType: 'primary' | 'supervisor' | 'escalation'
  decisionType: string
  summary: string
  confidenceLevel: 'high' | 'medium' | 'low' | 'uncertain'
  confidenceScore: number
  reasoning: string[]
  timestamp: string
}

// Metrics Types
export interface DashboardMetrics {
  totalInteractions: number
  activeInteractions: number
  resolutionRate: number
  escalationRate: number
  averageConfidence: number
  averageCsat: number
  averageDuration: number
}

export interface InteractionMetrics {
  interactionId: string
  duration: number
  turnCount: number
  escalationCount: number
  confidence: number
  csat: number
}

// Real-time Event Types
export interface RealtimeEvent {
  type: 'interaction_started' | 'message_received' | 'decision_made' | 'interaction_ended'
  timestamp: string
  data: unknown
}

// Component Props Types
export interface CardProps {
  title?: string
  subtitle?: string
  children: React.ReactNode
  className?: string
}

export interface StatCardProps {
  label: string
  value: string | number
  change?: number
  trend?: 'up' | 'down' | 'neutral'
  icon?: React.ReactNode
}

export interface BadgeProps {
  variant: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  children: React.ReactNode
}
