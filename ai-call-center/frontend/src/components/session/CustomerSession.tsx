import { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Send, Mic, MicOff, Volume2, VolumeX, Headphones } from 'lucide-react'
import styles from './CustomerSession.module.css'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { speak, stop as stopSpeech, isSupported as isTTSSupported } from '../../utils/speechSynthesis'

interface Message {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: Date
  is_human?: boolean
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
  const [ttsEnabled, setTtsEnabled] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const lastMessageCountRef = useRef(0)
  
  // Voice input
  const {
    isListening,
    isSupported: isSTTSupported,
    interimTranscript,
    capturedText,
    startListening,
    stopListening,
    clearTranscript,
    error: voiceError,
  } = useSpeechRecognition({
    continuous: false,
    autoRestart: false,
  })

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check session status and poll for agent connection
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch(`${API_BASE}/session/${sessionId}/status`)
        if (response.ok) {
          const data = await response.json()
          setIsConnected(data.is_active)
          
          const agentConnected = data.agent_connected
          setIsWaiting(!agentConnected)
          
          if (data.agent_name) {
            setAgentName(data.agent_name)
          }
        }
      } catch (err) {
        console.error('Failed to check session status:', err)
      }
    }

    checkSession()
    const interval = setInterval(checkSession, 2000)
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
            const newMessages = data.messages.map((m: any) => ({
              id: m.id || crypto.randomUUID(),
              role: m.role as 'customer' | 'agent' | 'system',
              content: m.content,
              timestamp: new Date(m.timestamp),
              is_human: m.is_human,
            }))
            
            setMessages(newMessages)
            
            // Speak new agent messages
            if (ttsEnabled && newMessages.length > lastMessageCountRef.current) {
              const lastMessage = newMessages[newMessages.length - 1]
              if (lastMessage.role === 'agent') {
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
  }, [sessionId, ttsEnabled])

  // Handle voice input capture
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
      await fetch(`${API_BASE}/session/${sessionId}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          role: 'customer',
          content: message,
        }),
      })
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

  const toggleMicrophone = () => {
    if (isListening) {
      stopListening()
    } else {
      stopSpeech()
      clearTranscript()
      startListening()
    }
  }

  return (
    <div className={styles.container}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerIcon}>
          <Headphones size={24} />
        </div>
        <div className={styles.headerInfo}>
          <h1>Support Session</h1>
          <p className={styles.sessionId}>Session: {sessionId?.slice(0, 8)}...</p>
        </div>
        {isWaiting ? (
          <div className={styles.waitingBadge}>
            <span className={styles.waitingDot} />
            Waiting for agent...
          </div>
        ) : (
          <div className={styles.connectedBadge}>
            <span className={styles.connectedDot} />
            {agentName || 'Agent'} connected
          </div>
        )}
      </header>

      {/* Waiting Overlay */}
      {isWaiting && (
        <div className={styles.waitingOverlay}>
          <div className={styles.waitingContent}>
            <div className={styles.waitingSpinner} />
            <h2>Connecting you to a human agent...</h2>
            <p>Please wait while an agent accepts your ticket.</p>
            <p className={styles.waitingHint}>You can start typing your message below.</p>
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className={styles.chatArea}>
        {/* Messages */}
        <div className={styles.messages}>
          {messages.length === 0 && !isWaiting ? (
            <div className={styles.emptyState}>
              <p>No messages yet. Say hello to the agent!</p>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${styles[message.role]}`}
              >
                <div className={styles.messageHeader}>
                  <span className={styles.messageRole}>
                    {message.role === 'customer' ? '👤 You' : 
                     message.role === 'agent' ? `🧑‍💼 ${agentName || 'Agent'}` : '📢 System'}
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
          {isTTSSupported() && (
            <button
              className={`${styles.controlButton} ${!ttsEnabled ? styles.muted : ''}`}
              onClick={() => {
                if (ttsEnabled) stopSpeech()
                setTtsEnabled(!ttsEnabled)
              }}
              title={ttsEnabled ? 'Mute agent voice' : 'Unmute agent voice'}
            >
              {ttsEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
            </button>
          )}
          
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
            placeholder={isListening ? 'Listening...' : 'Type your message...'}
            className={styles.input}
            disabled={isSending}
          />
          <button
            className={styles.sendButton}
            onClick={handleSendMessage}
            disabled={!input.trim() || isSending}
          >
            <Send size={20} />
          </button>
        </div>
        
        {isListening && (
          <div className={styles.listeningIndicator}>
            🎤 Recording... Click mic to stop
          </div>
        )}
        
        {voiceError && (
          <div className={styles.errorIndicator}>
            ⚠️ {voiceError}
          </div>
        )}
      </div>
    </div>
  )
}
