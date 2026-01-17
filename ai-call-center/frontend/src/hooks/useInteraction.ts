import { useState, useCallback } from 'react'
import * as api from '../services/api'
import type { Message } from '../types'

interface UseInteractionResult {
  interactionId: string | null
  messages: Message[]
  isLoading: boolean
  isConnected: boolean
  error: string | null
  startInteraction: (channel: 'voice' | 'chat') => Promise<void>
  sendMessage: (content: string) => Promise<void>
  endInteraction: () => Promise<void>
}

/**
 * Hook for managing an interaction session.
 */
export function useInteraction(): UseInteractionResult {
  const [interactionId, setInteractionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const startInteraction = useCallback(async (channel: 'voice' | 'chat') => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await api.startInteraction({ channel })
      if (response.success) {
        setInteractionId(response.data.interactionId)
        setIsConnected(true)
        setMessages([{
          id: 'system-1',
          role: 'system',
          content: 'Connected to AI Call Center. How can I help you today?',
          timestamp: new Date().toISOString(),
        }])
      } else {
        setError(response.error || 'Failed to start interaction')
      }
    } catch (err) {
      setError('Connection failed')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const sendMessage = useCallback(async (content: string) => {
    if (!interactionId) return
    
    // Add customer message
    const customerMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'customer',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages(prev => [...prev, customerMessage])
    setIsLoading(true)

    try {
      const response = await api.sendMessage({
        interactionId,
        content,
      })
      
      if (response.success) {
        const agentMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          role: 'agent',
          content: response.data.responseContent,
          timestamp: new Date().toISOString(),
          confidence: 0.85, // Placeholder
        }
        setMessages(prev => [...prev, agentMessage])
      }
    } catch (err) {
      setError('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }, [interactionId])

  const endInteraction = useCallback(async () => {
    if (!interactionId) return
    
    try {
      await api.endInteraction({ interactionId })
      setIsConnected(false)
      setInteractionId(null)
    } catch (err) {
      setError('Failed to end interaction')
    }
  }, [interactionId])

  return {
    interactionId,
    messages,
    isLoading,
    isConnected,
    error,
    startInteraction,
    sendMessage,
    endInteraction,
  }
}
