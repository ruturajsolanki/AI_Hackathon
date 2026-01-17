import { useState, useRef, useEffect } from 'react'
import { 
  Phone, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Send,
  Volume2,
  AlertTriangle,
  CheckCircle,
  Clock,
  Brain,
  Shield,
  TrendingUp,
  User,
  Bot,
  Wifi,
  WifiOff
} from 'lucide-react'
import { startInteraction, sendMessage, endInteraction } from '../../services/api'
import styles from './CallSimulator.module.css'

// Types
interface CallMessage {
  id: string
  role: 'customer' | 'agent' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    intent?: string
    emotion?: string
    confidence?: number
    processingTime?: number
  }
}

interface AgentState {
  status: 'idle' | 'listening' | 'processing' | 'speaking'
  confidence: number
  confidenceLevel: 'high' | 'medium' | 'low'
  intent: string
  emotion: string
  shouldEscalate: boolean
  escalationReason?: string
  turnCount: number
  sessionDuration: number
}

export function CallSimulator() {
  const [isCallActive, setIsCallActive] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isConnected, setIsConnected] = useState(true)
  const [interactionId, setInteractionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<CallMessage[]>([])
  const [input, setInput] = useState('')
  const [agentState, setAgentState] = useState<AgentState>({
    status: 'idle',
    confidence: 0,
    confidenceLevel: 'high',
    intent: '',
    emotion: '',
    shouldEscalate: false,
    turnCount: 0,
    sessionDuration: 0,
  })
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Session timer
  useEffect(() => {
    if (isCallActive) {
      timerRef.current = setInterval(() => {
        setAgentState(prev => ({
          ...prev,
          sessionDuration: prev.sessionDuration + 1,
        }))
      }, 1000)
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isCallActive])

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getConfidenceLevel = (score: number): 'high' | 'medium' | 'low' => {
    if (score >= 0.7) return 'high'
    if (score >= 0.5) return 'medium'
    return 'low'
  }

  const startCall = async () => {
    setIsCallActive(true)
    setAgentState(prev => ({ ...prev, status: 'processing' }))
    
    // Add system message
    setMessages([{
      id: 'connecting',
      role: 'system',
      content: 'Connecting to AI Agent...',
      timestamp: new Date(),
    }])

    // Call the real API
    const response = await startInteraction({
      channel: 'chat',
      initialMessage: "Hello, I need some help.",
    })

    if (response.success && response.data) {
      setInteractionId(response.data.interaction_id)
      setIsConnected(true)
      
      const greeting = response.data.initial_response || 
        "Hello! Thank you for calling. I'm your AI assistant. How can I help you today?"
      
      setMessages([
        {
          id: 'welcome',
          role: 'system',
          content: 'Call connected. AI Agent is ready.',
          timestamp: new Date(),
        },
        {
          id: 'greeting',
          role: 'agent',
          content: greeting,
          timestamp: new Date(),
          metadata: {
            intent: 'greeting',
            emotion: 'neutral',
            confidence: 0.95,
            processingTime: 150,
          },
        },
      ])
      
      setAgentState({
        status: 'listening',
        confidence: 0.95,
        confidenceLevel: 'high',
        intent: 'greeting',
        emotion: 'neutral',
        shouldEscalate: false,
        turnCount: 1,
        sessionDuration: 0,
      })
    } else {
      // Fallback to simulated mode
      setIsConnected(false)
      setMessages([
        {
          id: 'welcome',
          role: 'system',
          content: 'Call connected (Simulation Mode - Backend unavailable)',
          timestamp: new Date(),
        },
        {
          id: 'greeting',
          role: 'agent',
          content: "Hello! Thank you for calling. I'm your AI assistant. How can I help you today?",
          timestamp: new Date(),
          metadata: {
            intent: 'greeting',
            emotion: 'neutral',
            confidence: 0.98,
            processingTime: 120,
          },
        },
      ])
      
      setAgentState({
        status: 'listening',
        confidence: 0.98,
        confidenceLevel: 'high',
        intent: 'greeting',
        emotion: 'neutral',
        shouldEscalate: false,
        turnCount: 1,
        sessionDuration: 0,
      })
    }
  }

  const endCall = async () => {
    if (interactionId) {
      await endInteraction({ interactionId })
    }
    
    setIsCallActive(false)
    setInteractionId(null)
    setMessages(prev => [...prev, {
      id: 'goodbye',
      role: 'system',
      content: `Call ended. Duration: ${formatDuration(agentState.sessionDuration)}. ${agentState.turnCount} turns processed.`,
      timestamp: new Date(),
    }])
    setAgentState({
      status: 'idle',
      confidence: 0,
      confidenceLevel: 'high',
      intent: '',
      emotion: '',
      shouldEscalate: false,
      turnCount: 0,
      sessionDuration: 0,
    })
  }

  const handleSend = async () => {
    if (!input.trim() || !isCallActive || agentState.status === 'processing') return

    const customerMessage: CallMessage = {
      id: `customer-${Date.now()}`,
      role: 'customer',
      content: input,
      timestamp: new Date(),
    }
    
    setMessages(prev => [...prev, customerMessage])
    const userInput = input
    setInput('')
    setAgentState(prev => ({ ...prev, status: 'processing' }))

    const startTime = Date.now()

    if (interactionId && isConnected) {
      // Use real API
      const response = await sendMessage({
        interactionId,
        content: userInput,
      })

      const processingTime = Date.now() - startTime

      if (response.success && response.data) {
        const data = response.data
        const confidenceScore = data.confidence_level === 'high' ? 0.85 :
                               data.confidence_level === 'medium' ? 0.65 : 0.45

        setAgentState(prev => ({
          ...prev,
          status: 'speaking',
          confidence: confidenceScore,
          confidenceLevel: getConfidenceLevel(confidenceScore),
          intent: 'detected',
          emotion: 'analyzed',
          shouldEscalate: data.should_escalate,
          escalationReason: data.escalation_reason || undefined,
          turnCount: prev.turnCount + 1,
        }))

        const agentMessage: CallMessage = {
          id: `agent-${Date.now()}`,
          role: 'agent',
          content: data.response_content || "I understand. Let me help you with that.",
          timestamp: new Date(),
          metadata: {
            intent: 'response',
            confidence: confidenceScore,
            processingTime,
          },
        }
        
        setMessages(prev => [...prev, agentMessage])

        if (data.should_escalate) {
          setMessages(prev => [...prev, {
            id: `escalation-${Date.now()}`,
            role: 'system',
            content: `⚠️ Escalation triggered: ${data.escalation_reason || 'Complex issue detected'}`,
            timestamp: new Date(),
          }])
        }
      } else {
        // API error, add error message
        setMessages(prev => [...prev, {
          id: `error-${Date.now()}`,
          role: 'system',
          content: `Error: ${response.error || 'Failed to process message'}`,
          timestamp: new Date(),
        }])
      }
    } else {
      // Simulation mode
      await simulateResponse(userInput, startTime)
    }

    // Return to listening after "speaking"
    setTimeout(() => {
      setAgentState(prev => ({ ...prev, status: 'listening' }))
    }, 1000)
  }

  const simulateResponse = async (userInput: string, startTime: number) => {
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 500))
    
    const processingTime = Date.now() - startTime
    const lower = userInput.toLowerCase()
    
    let response = {
      content: "Thank you for reaching out. I'm here to help with billing questions, order tracking, account management, and more.",
      intent: 'general_inquiry',
      emotion: 'neutral',
      confidence: 0.88,
      shouldEscalate: false,
      escalationReason: undefined as string | undefined,
    }

    if (lower.includes('angry') || lower.includes('furious') || lower.includes('unacceptable')) {
      response = {
        content: "I sincerely apologize for the frustration you're experiencing. Let me connect you with a specialist who can give this the attention it deserves.",
        intent: 'complaint',
        emotion: 'angry',
        confidence: 0.65,
        shouldEscalate: true,
        escalationReason: 'High emotional distress detected',
      }
    } else if (lower.includes('bill') || lower.includes('charge') || lower.includes('payment')) {
      response = {
        content: "I can see your account details. Your current balance is $142.50. I notice there's a recent charge - would you like me to explain that?",
        intent: 'billing_inquiry',
        emotion: 'neutral',
        confidence: 0.92,
        shouldEscalate: false,
        escalationReason: undefined,
      }
    } else if (lower.includes('cancel')) {
      response = {
        content: "I understand you're considering cancellation. Before we proceed, is there something specific we could help address? We value your business.",
        intent: 'cancellation',
        emotion: 'neutral',
        confidence: 0.78,
        shouldEscalate: false,
        escalationReason: undefined,
      }
    }

    setAgentState(prev => ({
      ...prev,
      status: 'speaking',
      confidence: response.confidence,
      confidenceLevel: getConfidenceLevel(response.confidence),
      intent: response.intent,
      emotion: response.emotion,
      shouldEscalate: response.shouldEscalate,
      escalationReason: response.escalationReason,
      turnCount: prev.turnCount + 1,
    }))

    setMessages(prev => [...prev, {
      id: `agent-${Date.now()}`,
      role: 'agent',
      content: response.content,
      timestamp: new Date(),
      metadata: {
        intent: response.intent,
        emotion: response.emotion,
        confidence: response.confidence,
        processingTime,
      },
    }])

    if (response.shouldEscalate) {
      setMessages(prev => [...prev, {
        id: `escalation-${Date.now()}`,
        role: 'system',
        content: `⚠️ Escalation triggered: ${response.escalationReason}`,
        timestamp: new Date(),
      }])
    }
  }

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high': return 'var(--color-accent-success)'
      case 'medium': return 'var(--color-accent-warning)'
      case 'low': return 'var(--color-accent-danger)'
      default: return 'var(--color-text-muted)'
    }
  }

  return (
    <div className={styles.simulator}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h2 className={styles.title}>Call Simulator</h2>
          <p className={styles.subtitle}>
            Interactive AI agent demonstration
            {isCallActive && (
              <span className={styles.connectionStatus}>
                {isConnected ? (
                  <><Wifi size={12} /> Live Backend</>
                ) : (
                  <><WifiOff size={12} /> Simulation Mode</>
                )}
              </span>
            )}
          </p>
        </div>
        {isCallActive && (
          <div className={styles.callStatus}>
            <span className={styles.liveIndicator}>
              <span className={styles.liveDot} />
              LIVE
            </span>
            <span className={styles.duration}>
              <Clock size={14} />
              {formatDuration(agentState.sessionDuration)}
            </span>
          </div>
        )}
      </div>

      <div className={styles.content}>
        {/* Main Call Area */}
        <div className={styles.callArea}>
          {!isCallActive ? (
            <div className={styles.startScreen}>
              <div className={styles.startIcon}>
                <Phone size={48} />
              </div>
              <h3>Start a Simulated Call</h3>
              <p>Experience the AI-powered call center in action</p>
              <button className={styles.startButton} onClick={startCall}>
                <Phone size={20} />
                Start Call
              </button>
              <div className={styles.hints}>
                <span className={styles.hint}>Try: "I have a question about my bill"</span>
                <span className={styles.hint}>Try: "Where is my order?"</span>
                <span className={styles.hint}>Try: "I'm very angry about this!"</span>
              </div>
            </div>
          ) : (
            <>
              {/* Messages */}
              <div className={styles.messages}>
                {messages.map((message) => (
                  <div 
                    key={message.id} 
                    className={`${styles.message} ${styles[message.role]}`}
                  >
                    <div className={styles.messageAvatar}>
                      {message.role === 'customer' && <User size={16} />}
                      {message.role === 'agent' && <Bot size={16} />}
                      {message.role === 'system' && <Volume2 size={16} />}
                    </div>
                    <div className={styles.messageContent}>
                      <div className={styles.messageHeader}>
                        <span className={styles.messageRole}>
                          {message.role === 'customer' ? 'You' : 
                           message.role === 'agent' ? 'AI Agent' : 'System'}
                        </span>
                        <span className={styles.messageTime}>
                          {message.timestamp.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </span>
                      </div>
                      <p className={styles.messageText}>{message.content}</p>
                      {message.metadata && (
                        <div className={styles.messageMeta}>
                          <span className={styles.metaTag}>
                            {message.metadata.intent?.replace('_', ' ')}
                          </span>
                          {message.metadata.confidence && (
                            <span className={styles.metaConfidence}>
                              {(message.metadata.confidence * 100).toFixed(0)}% confident
                            </span>
                          )}
                          {message.metadata.processingTime && (
                            <span className={styles.metaTime}>
                              {message.metadata.processingTime}ms
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {agentState.status === 'processing' && (
                  <div className={`${styles.message} ${styles.agent}`}>
                    <div className={styles.messageAvatar}>
                      <Bot size={16} />
                    </div>
                    <div className={styles.messageContent}>
                      <div className={styles.processing}>
                        <span className={styles.processingDot} />
                        <span className={styles.processingDot} />
                        <span className={styles.processingDot} />
                        <span className={styles.processingText}>Processing...</span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className={styles.inputArea}>
                <div className={styles.inputWrapper}>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="Type your message..."
                    className={styles.input}
                    disabled={agentState.status === 'processing'}
                  />
                  <button 
                    className={`${styles.micButton} ${isMuted ? styles.muted : ''}`}
                    onClick={() => setIsMuted(!isMuted)}
                  >
                    {isMuted ? <MicOff size={18} /> : <Mic size={18} />}
                  </button>
                  <button 
                    className={styles.sendButton}
                    onClick={handleSend}
                    disabled={!input.trim() || agentState.status === 'processing'}
                  >
                    <Send size={18} />
                  </button>
                </div>
                <button className={styles.endButton} onClick={endCall}>
                  <PhoneOff size={18} />
                  End Call
                </button>
              </div>
            </>
          )}
        </div>

        {/* Agent Status Panel */}
        <div className={styles.statusPanel}>
          <h3 className={styles.panelTitle}>Agent Status</h3>
          
          {/* Status Indicator */}
          <div className={styles.statusCard}>
            <div className={styles.statusHeader}>
              <span className={`${styles.statusBadge} ${styles[agentState.status]}`}>
                {agentState.status === 'idle' && 'Idle'}
                {agentState.status === 'listening' && '● Listening'}
                {agentState.status === 'processing' && '◌ Processing'}
                {agentState.status === 'speaking' && '◉ Speaking'}
              </span>
            </div>
          </div>

          {/* Confidence Meter */}
          <div className={styles.statusCard}>
            <div className={styles.cardLabel}>
              <Shield size={14} />
              Confidence Level
            </div>
            <div className={styles.confidenceMeter}>
              <div 
                className={styles.confidenceFill}
                style={{ 
                  width: `${agentState.confidence * 100}%`,
                  backgroundColor: getConfidenceColor(agentState.confidenceLevel),
                }}
              />
            </div>
            <div className={styles.confidenceValue}>
              <span style={{ color: getConfidenceColor(agentState.confidenceLevel) }}>
                {(agentState.confidence * 100).toFixed(0)}%
              </span>
              <span className={styles.confidenceLabel}>{agentState.confidenceLevel}</span>
            </div>
          </div>

          {/* Intent & Emotion */}
          <div className={styles.statusCard}>
            <div className={styles.cardLabel}>
              <Brain size={14} />
              Detection
            </div>
            <div className={styles.detectionGrid}>
              <div className={styles.detectionItem}>
                <span className={styles.detectionLabel}>Intent</span>
                <span className={styles.detectionValue}>
                  {agentState.intent?.replace('_', ' ') || '—'}
                </span>
              </div>
              <div className={styles.detectionItem}>
                <span className={styles.detectionLabel}>Emotion</span>
                <span className={styles.detectionValue}>
                  {agentState.emotion || '—'}
                </span>
              </div>
            </div>
          </div>

          {/* Escalation Status */}
          <div className={`${styles.statusCard} ${agentState.shouldEscalate ? styles.escalated : ''}`}>
            <div className={styles.cardLabel}>
              {agentState.shouldEscalate ? (
                <AlertTriangle size={14} color="var(--color-accent-warning)" />
              ) : (
                <CheckCircle size={14} color="var(--color-accent-success)" />
              )}
              Escalation Status
            </div>
            <div className={styles.escalationStatus}>
              {agentState.shouldEscalate ? (
                <>
                  <span className={styles.escalationBadge}>
                    <AlertTriangle size={12} />
                    Escalation Recommended
                  </span>
                  <span className={styles.escalationReason}>
                    {agentState.escalationReason}
                  </span>
                </>
              ) : (
                <span className={styles.noEscalation}>
                  <CheckCircle size={14} />
                  Handling autonomously
                </span>
              )}
            </div>
          </div>

          {/* Session Stats */}
          <div className={styles.statusCard}>
            <div className={styles.cardLabel}>
              <TrendingUp size={14} />
              Session Stats
            </div>
            <div className={styles.statsGrid}>
              <div className={styles.statItem}>
                <span className={styles.statValue}>{agentState.turnCount}</span>
                <span className={styles.statLabel}>Turns</span>
              </div>
              <div className={styles.statItem}>
                <span className={styles.statValue}>
                  {formatDuration(agentState.sessionDuration)}
                </span>
                <span className={styles.statLabel}>Duration</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
