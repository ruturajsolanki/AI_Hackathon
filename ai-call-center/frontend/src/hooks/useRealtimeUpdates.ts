import { useEffect, useState, useCallback } from 'react'
import { wsService } from '../services/websocket'

interface RealtimeEvent {
  type: string
  timestamp: string
  data: unknown
}

/**
 * Hook for subscribing to real-time updates.
 * 
 * @param eventTypes - Array of event types to subscribe to
 * @returns Object with latest events and connection status
 */
export function useRealtimeUpdates(eventTypes: string[]) {
  const [events, setEvents] = useState<RealtimeEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)

  const handleEvent = useCallback((event: RealtimeEvent) => {
    setEvents(prev => [...prev.slice(-99), event]) // Keep last 100 events
  }, [])

  useEffect(() => {
    // Connect to WebSocket
    wsService.connect()
    setIsConnected(wsService.isConnected())

    // Subscribe to event types
    const unsubscribers = eventTypes.map(type =>
      wsService.subscribe(type, handleEvent)
    )

    return () => {
      unsubscribers.forEach(unsub => unsub())
    }
  }, [eventTypes, handleEvent])

  const clearEvents = useCallback(() => {
    setEvents([])
  }, [])

  return {
    events,
    isConnected,
    clearEvents,
    latestEvent: events[events.length - 1] || null,
  }
}
