import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Phone, PhoneOff, Send, Mic, MicOff, Volume2, VolumeX } from 'lucide-react'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { speak, stop as stopSpeech, isSupported as isTTSSupported } from '../../utils/speechSynthesis'
import styles from './LiveSession.module.css'

interface Message {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: Date
}

interface SessionInfo {
  session_id: string
  ticket_id: string
  interaction_id: string
  customer_name: string | null
  issue_summary: string
  agent_name: string | null
  active: boolean
}

const API_BASE = 'http://localhost:8000/api'

export function LiveSession() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Speech recognition for human agent voice input
  const {
    isListening,
    isSupported: isSTTSupported,
    capturedText,
    startListening,
    stopListening,
    clearTranscript,
  } = useSpeechRecognition({
    continuous: false,
    autoRestart: false,
  })

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // Fetch session info
  useEffect(() => {
    const fetchSession = async () => {
      if (!sessionId) return
      
      try {
        const response = await fetch(`${API_BASE}/tickets/session/${sessionId}`)
        if (response.ok) {
          const data = await response.json()
          setSessionInfo(data)
          setIsConnected(data.active)
          
          // Add welcome message
          setMessages([
            {
              id: 'welcome',
              role: 'system',
              content: `Connected to session. Customer: ${data.customer_name || 'Unknown'}. Issue: ${data.issue_summary}`,
              timestamp: new Date(),
            },
            {
              id: 'intro',
              role: 'agent',
              content: "Hi! I'm a human agent. I've reviewed your conversation with our AI assistant. How can I help you today?",
              timestamp: new Date(),
            },
          ])
        } else {
          setError('Session not found')
        }
      } catch (err) {
        setError('Failed to load session')
      } finally {
        setLoading(false)
      }
    }
    
    fetchSession()
  }, [sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Handle voice input
  useEffect(() => {
    if (capturedText && !isListening) {
      setInput(capturedText)
      clearTranscript()
    }
  }, [capturedText, isListening, clearTranscript])

  const addMessage = (role: 'customer' | 'agent' | 'system', content: string) => {
    setMessages(prev => [...prev, {
      id: `${role}-${Date.now()}`,
      role,
      content,
      timestamp: new Date(),
    }])
  }

  const handleSendMessage = async () => {
    if (!input.trim()) return
    
    const message = input.trim()
    setInput('')
    
    // Add agent message
    addMessage('agent', message)
    
    // Speak if TTS enabled (for customer to hear)
    if (ttsEnabled && isTTSSupported()) {
      await speak(message)
    }
    
    // Simulate customer response (in real app, this would come from WebSocket)
    setTimeout(() => {
      addMessage('customer', "Thank you for helping me with this. I really appreciate you taking the time.")
    }, 2000 + Math.random() * 2000)
  }

  const handleEndSession = async () => {
    if (!sessionInfo) return
    
    try {
      await fetch(`${API_BASE}/tickets/${sessionInfo.ticket_id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resolution_notes: 'Resolved by human agent',
          resolution_type: 'resolved',
        }),
      })
      
      addMessage('system', 'Session ended. Ticket marked as resolved.')
      setIsConnected(false)
      
      setTimeout(() => {
        navigate('/tickets')
      }, 2000)
    } catch {
      setError('Failed to end session')
    }
  }

  const toggleMicrophone = () => {
    if (isListening) {
      stopListening()
    } else {
      clearTranscript()
      startListening()
    }
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>
          <div className={styles.spinner} />
          <p>Connecting to session...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          <h2>❌ {error}</h2>
          <button onClick={() => navigate('/tickets')}>
            Back to Tickets
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInfo}>
          <h1>
            <Phone className={styles.phoneIcon} />
            Live Session
          </h1>
          <p>
            {sessionInfo?.customer_name || 'Customer'} • 
            {isConnected ? ' 🟢 Connected' : ' 🔴 Disconnected'}
          </p>
        </div>
        
        <div className={styles.headerActions}>
          <button
            className={styles.ttsButton}
            onClick={() => setTtsEnabled(!ttsEnabled)}
            title={ttsEnabled ? 'Disable TTS' : 'Enable TTS'}
          >
            {ttsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
          </button>
          
          <button
            className={styles.endButton}
            onClick={handleEndSession}
          >
            <PhoneOff size={18} />
            End & Resolve
          </button>
        </div>
      </header>

      {/* Issue Summary Banner */}
      {sessionInfo && (
        <div className={styles.summaryBanner}>
          <span className={styles.summaryLabel}>Issue:</span>
          <span className={styles.summaryText}>{sessionInfo.issue_summary}</span>
        </div>
      )}

      {/* Messages */}
      <div className={styles.messagesContainer}>
        <div className={styles.messages}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`${styles.message} ${styles[msg.role]}`}
            >
              <div className={styles.messageHeader}>
                <span className={styles.messageRole}>
                  {msg.role === 'customer' ? '👤 Customer' : 
                   msg.role === 'agent' ? '🧑‍💼 You (Human Agent)' : '📢 System'}
                </span>
                <span className={styles.messageTime}>
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className={styles.messageContent}>{msg.content}</p>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      {isConnected && (
        <div className={styles.inputArea}>
          <div className={styles.inputRow}>
            <button
              className={`${styles.micButton} ${isListening ? styles.listening : ''}`}
              onClick={toggleMicrophone}
              disabled={!isSTTSupported}
              title={isListening ? 'Stop listening' : 'Start voice input'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
            
            <input
              type="text"
              className={styles.input}
              placeholder="Type a message to the customer..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            
            <button
              className={styles.sendButton}
              onClick={handleSendMessage}
              disabled={!input.trim()}
            >
              <Send size={20} />
            </button>
          </div>
          
          {isListening && (
            <div className={styles.listeningIndicator}>
              <span className={styles.pulse} />
              Listening... Speak now
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default LiveSession
