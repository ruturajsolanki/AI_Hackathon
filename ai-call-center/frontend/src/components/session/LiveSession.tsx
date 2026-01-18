import { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Phone, PhoneOff, Send, Mic, MicOff, Volume2, VolumeX, ArrowLeft } from 'lucide-react'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { speak, stop as stopSpeech, isSupported as isTTSSupported } from '../../utils/speechSynthesis'
import styles from './LiveSession.module.css'

interface Message {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: Date
  is_human?: boolean
}

const API_BASE = 'http://localhost:8000/api'

export function LiveSession() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [customerName, setCustomerName] = useState<string>('Customer')
  const [issueSummary, setIssueSummary] = useState<string>('')
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastMessageCountRef = useRef(0)
  
  // Speech recognition for human agent voice input
  const {
    isListening,
    isSupported: isSTTSupported,
    interimTranscript,
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

  // Join session and mark agent as connected
  useEffect(() => {
    const joinSession = async () => {
      if (!sessionId) return
      
      try {
        // First, mark agent as joined
        await fetch(`${API_BASE}/session/${sessionId}/agent-join?agent_name=Human Agent`, {
          method: 'POST',
        })
        
        // Get session status
        const statusResponse = await fetch(`${API_BASE}/session/${sessionId}/status`)
        if (statusResponse.ok) {
          const statusData = await statusResponse.json()
          setIsConnected(true)
          setCustomerName(statusData.customer_name || 'Customer')
        }
        
        // Try to get ticket details for context
        try {
          // The sessionId is the interaction_id, so we can get ticket info
          const ticketsResponse = await fetch(`${API_BASE}/tickets/pending`)
          if (ticketsResponse.ok) {
            const tickets = await ticketsResponse.json()
            const ticket = tickets.find((t: any) => 
              t.interaction_id === sessionId || 
              t.ticket_id === sessionId
            )
            if (ticket) {
              setCustomerName(ticket.customer_name || 'Customer')
              setIssueSummary(ticket.issue_summary || '')
            }
          }
        } catch {
          // Ignore ticket fetch errors
        }
        
        setLoading(false)
      } catch (err) {
        console.error('Failed to join session:', err)
        setError('Failed to connect to session')
        setLoading(false)
      }
    }
    
    joinSession()
  }, [sessionId])

  // Poll for messages from customer
  useEffect(() => {
    if (!sessionId || !isConnected) return
    
    const fetchMessages = async () => {
      try {
        const response = await fetch(`${API_BASE}/session/${sessionId}/messages`)
        if (response.ok) {
          const data = await response.json()
          if (data.messages && data.messages.length > 0) {
            const newMessages = data.messages.map((m: any) => ({
              id: m.id || crypto.randomUUID(),
              role: m.role as 'customer' | 'agent' | 'system',
              content: m.content,
              timestamp: new Date(m.timestamp),
              is_human: m.is_human,
            }))
            
            setMessages(newMessages)
            
            // Speak new customer messages
            if (ttsEnabled && newMessages.length > lastMessageCountRef.current) {
              const lastMessage = newMessages[newMessages.length - 1]
              if (lastMessage.role === 'customer') {
                speak(lastMessage.content)
              }
            }
            lastMessageCountRef.current = newMessages.length
          }
        }
      } catch (err) {
        console.error('Failed to fetch messages:', err)
      }
    }
    
    fetchMessages()
    const interval = setInterval(fetchMessages, 1500)
    return () => clearInterval(interval)
  }, [sessionId, isConnected, ttsEnabled])

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

  const handleSendMessage = async () => {
    if (!input.trim() || isSending) return
    
    const message = input.trim()
    setInput('')
    setIsSending(true)
    
    try {
      // Send message via API
      await fetch(`${API_BASE}/session/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: 'agent',
          content: message,
        }),
      })
      
      // Speak if TTS enabled
      if (ttsEnabled && isTTSSupported()) {
        speak(message)
      }
    } catch (err) {
      console.error('Failed to send message:', err)
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleEndSession = async () => {
    try {
      await fetch(`${API_BASE}/session/${sessionId}/end?resolution=resolved`, {
        method: 'POST',
      })
      
      setIsConnected(false)
      
      setTimeout(() => {
        navigate('/tickets')
      }, 1500)
    } catch {
      setError('Failed to end session')
    }
  }

  const toggleMicrophone = () => {
    if (isListening) {
      stopListening()
    } else {
      stopSpeech()
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
        <button className={styles.backButton} onClick={() => navigate('/tickets')}>
          <ArrowLeft size={20} />
          Back
        </button>
        
        <div className={styles.headerInfo}>
          <h1>Live Session with {customerName}</h1>
          <p className={styles.sessionId}>Session: {sessionId?.slice(0, 8)}...</p>
          {issueSummary && (
            <p className={styles.issueSummary}>Issue: {issueSummary}</p>
          )}
        </div>
        
        <div className={styles.connectionStatus}>
          {isConnected ? (
            <span className={styles.connected}>
              <span className={styles.dot} />
              Connected
            </span>
          ) : (
            <span className={styles.disconnected}>
              Disconnected
            </span>
          )}
        </div>
      </header>

      {/* Chat Area */}
      <div className={styles.chatArea}>
        {/* Welcome Banner */}
        <div className={styles.welcomeBanner}>
          <p>👋 You are now connected as a human agent. The customer can see your messages.</p>
        </div>
        
        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              <p>No messages yet. The customer will appear here when they connect.</p>
              <p className={styles.hint}>Send a greeting to start the conversation!</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${styles[message.role]}`}
              >
                <div className={styles.messageHeader}>
                  <span className={styles.messageRole}>
                    {message.role === 'customer' ? `👤 ${customerName}` : 
                     message.role === 'agent' ? '🧑‍💼 You (Agent)' : '📢 System'}
                  </span>
                  <span className={styles.messageTime}>
                    {message.timestamp.toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                </div>
                <p className={styles.messageContent}>{message.content}</p>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className={styles.inputArea}>
        <div className={styles.inputControls}>
          {/* TTS Toggle */}
          <button
            className={`${styles.controlButton} ${!ttsEnabled ? styles.muted : ''}`}
            onClick={() => {
              if (ttsEnabled) stopSpeech()
              setTtsEnabled(!ttsEnabled)
            }}
            title={ttsEnabled ? 'Mute customer voice' : 'Unmute customer voice'}
          >
            {ttsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
          </button>
          
          {/* Mic Button */}
          {isSTTSupported && (
            <button
              className={`${styles.controlButton} ${isListening ? styles.listening : ''}`}
              onClick={toggleMicrophone}
              title={isListening ? 'Stop recording' : 'Start voice input'}
            >
              {isListening ? <MicOff size={20} /> : <Mic size={20} />}
            </button>
          )}
        </div>
        
        <div className={styles.inputRow}>
          <input
            type="text"
            value={isListening ? interimTranscript || input : input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isListening ? 'Listening...' : 'Type your message to the customer...'}
            className={styles.input}
            disabled={!isConnected || isSending}
          />
          <button
            className={styles.sendButton}
            onClick={handleSendMessage}
            disabled={!input.trim() || !isConnected || isSending}
          >
            <Send size={20} />
          </button>
        </div>
        
        {isListening && (
          <div className={styles.listeningIndicator}>
            🎤 Recording... Click mic to stop
          </div>
        )}
      </div>

      {/* End Session Button */}
      <div className={styles.footer}>
        <button
          className={styles.endButton}
          onClick={handleEndSession}
          disabled={!isConnected}
        >
          <PhoneOff size={18} />
          End Session & Resolve Ticket
        </button>
      </div>
    </div>
  )
}
