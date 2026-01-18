import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import styles from './CustomerSession.module.css'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { speak, stop as stopSpeech } from '../../utils/speechSynthesis'

interface Message {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: Date
  isHuman?: boolean
}

const API_BASE = 'http://localhost:8000/api'

export function CustomerSession() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isWaiting, setIsWaiting] = useState(true)
  const [agentName, setAgentName] = useState<string | null>(null)
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Voice input
  const {
    isListening,
    interimTranscript,
    capturedText,
    startListening,
    stopListening,
    error: voiceError,
  } = useSpeechRecognition({
    continuous: false,
    autoRestart: false,
  })

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check session status
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/session/${sessionId}/status`)
        if (response.ok) {
          const data = await response.json()
          setIsConnected(data.is_active)
          setIsWaiting(!data.agent_connected)
          if (data.agent_name) {
            setAgentName(data.agent_name)
          }
        }
      } catch (err) {
        console.error('Failed to check session status:', err)
      }
    }

    checkSession()
    const interval = setInterval(checkSession, 3000)
    return () => clearInterval(interval)
  }, [sessionId])

  // Poll for new messages
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const response = await fetch(`${API_BASE}/session/${sessionId}/messages`)
        if (response.ok) {
          const data = await response.json()
          if (data.messages && data.messages.length > 0) {
            setMessages(data.messages.map((m: any) => ({
              id: m.id || crypto.randomUUID(),
              role: m.role,
              content: m.content,
              timestamp: new Date(m.timestamp),
              isHuman: m.is_human,
            })))
          }
        }
      } catch (err) {
        console.error('Failed to fetch messages:', err)
      }
    }

    fetchMessages()
    const interval = setInterval(fetchMessages, 2000)
    return () => clearInterval(interval)
  }, [sessionId])

  // Handle voice input
  useEffect(() => {
    if (capturedText && !isListening) {
      setInput(capturedText)
    }
  }, [capturedText, isListening])

  // Speak agent messages
  useEffect(() => {
    const lastMessage = messages[messages.length - 1]
    if (lastMessage && lastMessage.role === 'agent' && lastMessage.isHuman) {
      speak(lastMessage.content)
    }
  }, [messages])

  const addMessage = (message: Omit<Message, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date(),
    }])
  }

  const handleSend = async () => {
    if (!input.trim() || isSending) return

    const messageText = input.trim()
    setInput('')
    setIsSending(true)

    // Add customer message locally
    addMessage({
      role: 'customer',
      content: messageText,
    })

    try {
      // Send to backend
      await fetch(`${API_BASE}/session/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: 'customer',
          content: messageText,
        }),
      })
    } catch (err) {
      console.error('Failed to send message:', err)
      addMessage({
        role: 'system',
        content: 'Failed to send message. Please try again.',
      })
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const toggleVoice = () => {
    if (isListening) {
      stopListening()
    } else {
      stopSpeech()
      startListening()
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.sessionCard}>
        {/* Header */}
        <header className={styles.header}>
          <div className={styles.headerInfo}>
            <h1>Support Session</h1>
            <p className={styles.sessionId}>Session: {sessionId?.slice(0, 8)}...</p>
          </div>
          <div className={styles.connectionStatus}>
            {isWaiting ? (
              <span className={styles.waiting}>
                <span className={styles.pulse}></span>
                Waiting for agent...
              </span>
            ) : (
              <span className={styles.connected}>
                <span className={styles.dot}></span>
                Connected{agentName ? ` with ${agentName}` : ''}
              </span>
            )}
          </div>
        </header>

        {/* Messages */}
        <div className={styles.messagesContainer}>
          {isWaiting && messages.length === 0 && (
            <div className={styles.waitingMessage}>
              <div className={styles.waitingIcon}>🎧</div>
              <h2>Your call has been escalated</h2>
              <p>A human support agent will join shortly.</p>
              <p className={styles.waitingHint}>Please keep this window open.</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`${styles.message} ${styles[message.role]}`}
            >
              <div className={styles.messageHeader}>
                <span className={styles.messageRole}>
                  {message.role === 'customer' ? '👤 You' : 
                   message.role === 'agent' ? '🧑‍💼 Agent' : '📢 System'}
                </span>
                <span className={styles.messageTime}>
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className={styles.messageContent}>{message.content}</p>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className={styles.inputArea}>
          {voiceError && (
            <div className={styles.voiceError}>{voiceError}</div>
          )}
          
          <div className={styles.inputRow}>
            <button
              className={`${styles.voiceButton} ${isListening ? styles.listening : ''}`}
              onClick={toggleVoice}
              title={isListening ? 'Stop listening' : 'Start voice input'}
            >
              {isListening ? '🔴' : '🎤'}
            </button>
            
            <input
              type="text"
              className={styles.input}
              placeholder={isWaiting ? 'Waiting for agent to connect...' : 'Type your message...'}
              value={isListening ? interimTranscript : input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isWaiting || isSending}
            />
            
            <button
              className={styles.sendButton}
              onClick={handleSend}
              disabled={!input.trim() || isWaiting || isSending}
            >
              {isSending ? '...' : 'Send'}
            </button>
          </div>
          
          {isListening && (
            <div className={styles.listeningIndicator}>
              🎤 Listening... Speak now
            </div>
          )}
        </div>
      </div>

      {/* Share Link */}
      <div className={styles.shareSection}>
        <p>Session Link (share if needed):</p>
        <code className={styles.shareLink}>
          {window.location.href}
        </code>
        <button
          className={styles.copyButton}
          onClick={() => {
            navigator.clipboard.writeText(window.location.href)
            alert('Link copied!')
          }}
        >
          Copy Link
        </button>
      </div>
    </div>
  )
}
