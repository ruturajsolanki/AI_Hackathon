import { useState, useRef, useEffect, useCallback } from 'react'
import { 
  Phone, 
  PhoneOff, 
  Mic, 
  MicOff, 
  Send,
  Volume2,
  VolumeX,
  AlertTriangle,
  CheckCircle,
  Clock,
  Brain,
  Shield,
  TrendingUp,
  User,
  Bot,
  Wifi,
  Loader2,
  XCircle
} from 'lucide-react'
import { startCall, sendMessage, endCall } from '../../services/apiClient'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { speak, stop as stopSpeech, isSupported as isTTSSupported } from '../../utils/speechSynthesis'
import styles from './CallSimulator.module.css'

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

interface CallMessage {
  id: string
  role: 'customer' | 'agent' | 'system' | 'error'
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
  status: 'idle' | 'connecting' | 'listening' | 'processing' | 'speaking' | 'error'
  confidence: number
  confidenceLevel: 'high' | 'medium' | 'low'
  intent: string
  emotion: string
  shouldEscalate: boolean
  escalationReason?: string
  escalationType?: string
  turnCount: number
  sessionDuration: number
}

// -----------------------------------------------------------------------------
// Component
// -----------------------------------------------------------------------------

export function CallSimulator() {
  // State
  const [callId, setCallId] = useState<string | null>(null)
  const [isCallActive, setIsCallActive] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [messages, setMessages] = useState<CallMessage[]>([])
  const [input, setInput] = useState('')
  const [ttsEnabled, setTtsEnabled] = useState(true)
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
  
  // Speech Recognition Hook
  const {
    isListening,
    isSupported: isSTTSupported,
    transcript,
    interimTranscript,
    finalTranscript,
    error: speechError,
    permissionDenied,
    startListening,
    stopListening,
    clearTranscript,
  } = useSpeechRecognition({
    language: 'en-US',
    continuous: false,
    interimResults: true,
  })

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastTranscriptRef = useRef<string>('')
  const lastInterimRef = useRef<string>('')

  // ---------------------------------------------------------------------------
  // Effects
  // ---------------------------------------------------------------------------

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Session timer
  useEffect(() => {
    if (isCallActive && agentState.status !== 'error') {
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
  }, [isCallActive, agentState.status])

  // Handle speech recognition errors
  useEffect(() => {
    if (speechError && !permissionDenied) {
      setError(speechError)
    }
  }, [speechError, permissionDenied])

  // Track interim transcript for fallback
  useEffect(() => {
    if (interimTranscript) {
      lastInterimRef.current = interimTranscript
    }
  }, [interimTranscript])

  // Stop TTS when call ends
  useEffect(() => {
    if (!isCallActive) {
      stopSpeech()
    }
  }, [isCallActive])

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getConfidenceLevel = (level: string | null): 'high' | 'medium' | 'low' => {
    if (level === 'high') return 'high'
    if (level === 'medium') return 'medium'
    return 'low'
  }

  const getConfidenceScore = (level: string | null): number => {
    if (level === 'high') return 0.85
    if (level === 'medium') return 0.65
    return 0.45
  }

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high': return 'var(--color-accent-success)'
      case 'medium': return 'var(--color-accent-warning)'
      case 'low': return 'var(--color-accent-danger)'
      default: return 'var(--color-text-muted)'
    }
  }

  const addMessage = useCallback((message: Omit<CallMessage, 'id' | 'timestamp'>) => {
    setMessages(prev => [...prev, {
      ...message,
      id: `${message.role}-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      timestamp: new Date(),
    }])
  }, [])

  // Speak AI response using TTS
  const speakResponse = useCallback(async (text: string) => {
    if (!ttsEnabled || !isTTSSupported()) return
    
    try {
      await speak(text, {
        rate: 1.0,
        pitch: 1.0,
        volume: 0.9,
        onStart: () => {
          setAgentState(prev => ({ ...prev, status: 'speaking' }))
        },
        onEnd: () => {
          setAgentState(prev => ({ 
            ...prev, 
            status: prev.shouldEscalate ? 'speaking' : 'listening' 
          }))
        },
      })
    } catch {
      // TTS failed, just continue
    }
  }, [ttsEnabled])

  // ---------------------------------------------------------------------------
  // Voice Handlers
  // ---------------------------------------------------------------------------

  const toggleMicrophone = useCallback(() => {
    if (!isSTTSupported) {
      setError('Speech recognition is not supported in this browser.')
      return
    }

    if (isListening) {
      stopListening()
    } else {
      stopSpeech() // Stop any ongoing TTS
      clearTranscript()
      lastTranscriptRef.current = ''
      startListening()
    }
  }, [isSTTSupported, isListening, startListening, stopListening, clearTranscript])

  const toggleTTS = useCallback(() => {
    if (!ttsEnabled) {
      setTtsEnabled(true)
    } else {
      stopSpeech()
      setTtsEnabled(false)
    }
  }, [ttsEnabled])

  // Handle voice message (from speech recognition)
  const handleVoiceMessage = useCallback(async (voiceText: string) => {
    console.log('[handleVoiceMessage] Called with:', voiceText)
    console.log('[handleVoiceMessage] isCallActive:', isCallActive, 'callId:', callId, 'status:', agentState.status)
    
    if (!voiceText.trim() || !isCallActive || !callId || agentState.status === 'processing') {
      console.log('[handleVoiceMessage] ❌ Early return - conditions not met')
      return
    }

    console.log('[handleVoiceMessage] ✅ Proceeding with API call')
    setError(null)
    
    // Add customer message
    addMessage({
      role: 'customer',
      content: voiceText,
    })

    // Set processing state
    setAgentState(prev => ({ ...prev, status: 'processing' }))
    setIsLoading(true)

    const startTime = Date.now()

    // Call API
    console.log('[handleVoiceMessage] Calling sendMessage API...')
    const result = await sendMessage(callId, voiceText)
    console.log('[handleVoiceMessage] API Response:', result)
    
    const processingTime = Date.now() - startTime
    setIsLoading(false)

    if (result.success && result.data) {
      console.log('[handleVoiceMessage] ✅ Success! Response content:', result.data.responseContent)
      const data = result.data
      const confidenceLevel = getConfidenceLevel(data.confidenceLevel)
      const confidenceScore = getConfidenceScore(data.confidenceLevel)

      // Update agent state
      setAgentState(prev => ({
        ...prev,
        status: 'speaking',
        confidence: confidenceScore,
        confidenceLevel,
        intent: 'detected',
        emotion: 'analyzed',
        shouldEscalate: data.shouldEscalate,
        escalationReason: data.escalationReason || undefined,
        escalationType: data.escalationType || undefined,
        turnCount: prev.turnCount + 1,
      }))

      // Add agent response and speak it
      if (data.responseContent) {
        addMessage({
          role: 'agent',
          content: data.responseContent,
          metadata: {
            confidence: confidenceScore,
            processingTime,
          },
        })

        // Speak the response
        await speakResponse(data.responseContent)
      }

      // Add escalation notice if needed
      if (data.shouldEscalate) {
        addMessage({
          role: 'system',
          content: `⚠️ Escalation triggered: ${data.escalationReason || 'Complex issue detected'}`,
        })
      }

    } else {
      // Handle error
      setError(result.error?.message || 'Failed to send message')
      setAgentState(prev => ({ ...prev, status: 'listening' }))
      
      addMessage({
        role: 'error',
        content: `Error: ${result.error?.message || 'Failed to process message'}`,
      })
    }
  }, [callId, isCallActive, agentState.status, addMessage, speakResponse])

  // Auto-send transcribed text when speech ends
  useEffect(() => {
    console.log('[Speech Effect] isListening:', isListening, 'transcript:', transcript, 'finalTranscript:', finalTranscript, 'lastInterim:', lastInterimRef.current)
    
    if (!isListening) {
      // Use finalTranscript, or fall back to transcript, or last interim
      const textToSend = (finalTranscript || transcript || lastInterimRef.current).trim()
      
      console.log('[Speech Effect] textToSend:', textToSend, 'lastRef:', lastTranscriptRef.current)
      
      if (textToSend && textToSend !== lastTranscriptRef.current) {
        lastTranscriptRef.current = textToSend
        
        console.log('[Speech Effect] Conditions - isCallActive:', isCallActive, 'callId:', callId, 'status:', agentState.status)
        
        // Add a small delay to ensure all state is settled
        const timer = setTimeout(() => {
          if (isCallActive && callId && agentState.status !== 'processing') {
            console.log('[Speech Effect] ✅ Sending voice message:', textToSend)
            handleVoiceMessage(textToSend)
          } else {
            console.log('[Speech Effect] ❌ Not sending - conditions not met')
          }
          clearTranscript()
          lastInterimRef.current = ''
        }, 150)
        
        return () => clearTimeout(timer)
      }
    }
  }, [isListening, transcript, finalTranscript, isCallActive, callId, agentState.status, handleVoiceMessage, clearTranscript])

  // ---------------------------------------------------------------------------
  // API Handlers
  // ---------------------------------------------------------------------------

  const handleStartCall = async () => {
    setIsLoading(true)
    setError(null)
    setIsCallActive(true)
    setAgentState(prev => ({ ...prev, status: 'connecting' }))
    
    addMessage({
      role: 'system',
      content: 'Connecting to AI Agent...',
    })

    const result = await startCall({
      channel: 'voice',
    })

    setIsLoading(false)

    if (result.success && result.data) {
      const { callId: newCallId, initialResponse } = result.data
      setCallId(newCallId)
      
      // Clear connecting message and add success
      setMessages([
        {
          id: 'connected',
          role: 'system',
          content: 'Call connected. AI Agent is ready. Click the microphone to speak.',
          timestamp: new Date(),
        },
      ])

      const greeting = initialResponse || 
        "Hello! Thank you for calling. I'm your AI assistant. How can I help you today?"

      addMessage({
        role: 'agent',
        content: greeting,
        metadata: {
          intent: 'greeting',
          confidence: 0.95,
        },
      })

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

      // Speak the greeting
      await speakResponse(greeting)

    } else {
      setError(result.error?.message || 'Failed to start call')
      setAgentState(prev => ({ ...prev, status: 'error' }))
      
      setMessages([{
        id: 'error',
        role: 'error',
        content: `Connection failed: ${result.error?.message || 'Unknown error'}`,
        timestamp: new Date(),
      }])
    }
  }

  const handleEndCall = async () => {
    // Stop any ongoing speech/listening
    stopSpeech()
    if (isListening) stopListening()

    if (!callId) {
      setIsCallActive(false)
      return
    }

    setIsLoading(true)
    
    const result = await endCall(callId)
    
    setIsLoading(false)
    setIsCallActive(false)
    setCallId(null)

    addMessage({
      role: 'system',
      content: result.success 
        ? `Call ended. Duration: ${formatDuration(agentState.sessionDuration)}. ${agentState.turnCount} turns processed.`
        : `Call ended (with error: ${result.error?.message})`,
    })

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

  const handleSendMessage = async () => {
    if (!input.trim() || !isCallActive || !callId || agentState.status === 'processing') {
      return
    }

    const userMessage = input.trim()
    setInput('')
    setError(null)
    
    // Stop any ongoing TTS
    stopSpeech()
    
    // Add customer message
    addMessage({
      role: 'customer',
      content: userMessage,
    })

    // Set processing state
    setAgentState(prev => ({ ...prev, status: 'processing' }))
    setIsLoading(true)

    const startTime = Date.now()

    // Call API
    const result = await sendMessage(callId, userMessage)
    
    const processingTime = Date.now() - startTime
    setIsLoading(false)

    if (result.success && result.data) {
      const data = result.data
      const confidenceLevel = getConfidenceLevel(data.confidenceLevel)
      const confidenceScore = getConfidenceScore(data.confidenceLevel)

      // Update agent state
      setAgentState(prev => ({
        ...prev,
        status: 'speaking',
        confidence: confidenceScore,
        confidenceLevel,
        intent: 'detected',
        emotion: 'analyzed',
        shouldEscalate: data.shouldEscalate,
        escalationReason: data.escalationReason || undefined,
        escalationType: data.escalationType || undefined,
        turnCount: prev.turnCount + 1,
      }))

      // Add agent response and speak it
      if (data.responseContent) {
        addMessage({
          role: 'agent',
          content: data.responseContent,
          metadata: {
            confidence: confidenceScore,
            processingTime,
          },
        })

        // Speak the response
        await speakResponse(data.responseContent)
      }

      // Add escalation notice if needed
      if (data.shouldEscalate) {
        addMessage({
          role: 'system',
          content: `⚠️ Escalation triggered: ${data.escalationReason || 'Complex issue detected'}`,
        })
      }

    } else {
      setError(result.error?.message || 'Failed to send message')
      setAgentState(prev => ({ ...prev, status: 'listening' }))
      
      addMessage({
        role: 'error',
        content: `Error: ${result.error?.message || 'Failed to process message'}`,
      })
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // ---------------------------------------------------------------------------
  // Render
  // ---------------------------------------------------------------------------

  return (
    <div className={styles.simulator} role="application" aria-label="AI Call Simulator">
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerInfo}>
          <h2 className={styles.title}>Call Simulator</h2>
          <p className={styles.subtitle}>
            Interactive AI agent demonstration
            {isCallActive && callId && (
              <span className={styles.connectionStatus} role="status" aria-live="polite">
                <Wifi size={12} aria-hidden="true" /> Connected
              </span>
            )}
          </p>
        </div>
        {isCallActive && (
          <div className={styles.callStatus} role="status" aria-live="polite">
            <span className={styles.liveIndicator}>
              <span className={styles.liveDot} aria-hidden="true" />
              <span aria-label="Call is live">LIVE</span>
            </span>
            <span className={styles.duration} aria-label={`Call duration: ${formatDuration(agentState.sessionDuration)}`}>
              <Clock size={14} aria-hidden="true" />
              <time>{formatDuration(agentState.sessionDuration)}</time>
            </span>
          </div>
        )}
      </header>

      <div className={styles.content}>
        {/* Main Call Area */}
        <div className={styles.callArea}>
          {!isCallActive ? (
            <div className={styles.startScreen}>
              <div className={styles.startIcon}>
                <Phone size={48} />
              </div>
              <h3>Start a Voice Call</h3>
              <p>Experience the AI-powered call center with voice</p>
              <button 
                className={styles.startButton} 
                onClick={handleStartCall}
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 size={20} className={styles.spinning} />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Phone size={20} />
                    Start Call
                  </>
                )}
              </button>
              <div className={styles.hints}>
                <span className={styles.hint}>🎤 Click microphone to speak</span>
                <span className={styles.hint}>🔊 AI will respond with voice</span>
                <span className={styles.hint}>⌨️ Or type your message</span>
              </div>
            </div>
          ) : (
            <>
              {/* Messages */}
              <div 
                className={styles.messages}
                role="log"
                aria-label="Conversation messages"
                aria-live="polite"
              >
                {messages.map((message) => (
                  <article 
                    key={message.id} 
                    className={`${styles.message} ${styles[message.role]}`}
                    aria-label={`${message.role === 'customer' ? 'You' : message.role === 'agent' ? 'AI Agent' : message.role === 'error' ? 'Error' : 'System'} said: ${message.content}`}
                  >
                    <div className={styles.messageAvatar} aria-hidden="true">
                      {message.role === 'customer' && <User size={16} />}
                      {message.role === 'agent' && <Bot size={16} />}
                      {message.role === 'system' && <Volume2 size={16} />}
                      {message.role === 'error' && <XCircle size={16} />}
                    </div>
                    <div className={styles.messageContent}>
                      <div className={styles.messageHeader}>
                        <span className={styles.messageRole}>
                          {message.role === 'customer' ? 'You' : 
                           message.role === 'agent' ? 'AI Agent' : 
                           message.role === 'error' ? 'Error' : 'System'}
                        </span>
                        <time 
                          className={styles.messageTime}
                          dateTime={message.timestamp.toISOString()}
                        >
                          {message.timestamp.toLocaleTimeString([], { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                          })}
                        </time>
                      </div>
                      <p className={styles.messageText}>{message.content}</p>
                      {message.metadata && (
                        <div className={styles.messageMeta} aria-label="Message details">
                          {message.metadata.intent && (
                            <span className={styles.metaTag} title="Detected intent">
                              {message.metadata.intent.replace(/_/g, ' ')}
                            </span>
                          )}
                          {message.metadata.confidence !== undefined && (
                            <span className={styles.metaConfidence} title="AI confidence level">
                              {(message.metadata.confidence * 100).toFixed(0)}% confident
                            </span>
                          )}
                          {message.metadata.processingTime !== undefined && (
                            <span className={styles.metaTime} title="Processing time">
                              {message.metadata.processingTime}ms
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </article>
                ))}
                
                {/* Processing indicator */}
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

                {/* Live transcription indicator */}
                {isListening && (
                  <div className={`${styles.message} ${styles.customer}`}>
                    <div className={styles.messageAvatar}>
                      <User size={16} />
                    </div>
                    <div className={styles.messageContent}>
                      <div className={styles.transcribing}>
                        <span className={styles.transcribingDot} />
                        <span className={styles.transcribingText}>
                          {interimTranscript || 'Listening...'}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className={styles.inputArea}>
                {error && (
                  <div className={styles.errorBanner}>
                    <XCircle size={14} />
                    {error}
                  </div>
                )}
                
                {permissionDenied && (
                  <div className={styles.errorBanner}>
                    <MicOff size={14} />
                    Microphone access denied. Please allow microphone access or type your message.
                  </div>
                )}

                <div className={styles.inputWrapper}>
                  <label htmlFor="message-input" className={styles.srOnly}>
                    Type your message
                  </label>
                  <input
                    id="message-input"
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={isListening ? 'Listening...' : 'Type or click mic to speak...'}
                    className={styles.input}
                    disabled={agentState.status === 'processing' || agentState.status === 'error' || isListening}
                    aria-describedby={error ? 'input-error' : undefined}
                  />
                  
                  {/* TTS Toggle */}
                  <button 
                    className={`${styles.ttsButton} ${!ttsEnabled ? styles.muted : ''}`}
                    onClick={toggleTTS}
                    title={ttsEnabled ? 'Mute AI voice' : 'Enable AI voice'}
                    aria-label={ttsEnabled ? 'Mute AI voice responses' : 'Enable AI voice responses'}
                    aria-pressed={ttsEnabled}
                  >
                    {ttsEnabled ? <Volume2 size={18} aria-hidden="true" /> : <VolumeX size={18} aria-hidden="true" />}
                  </button>
                  
                  {/* Microphone Button */}
                  <button 
                    className={`${styles.micButton} ${isListening ? styles.recording : ''} ${permissionDenied ? styles.disabled : ''}`}
                    onClick={toggleMicrophone}
                    disabled={agentState.status === 'processing' || permissionDenied}
                    title={isListening ? 'Stop listening' : 'Start voice input'}
                    aria-label={isListening ? 'Stop listening' : 'Start voice input'}
                    aria-pressed={isListening}
                  >
                    {isListening ? (
                      <div className={styles.micRecording}>
                        <Mic size={18} aria-hidden="true" />
                      </div>
                    ) : (
                      <Mic size={18} aria-hidden="true" />
                    )}
                  </button>
                  
                  {/* Send Button */}
                  <button 
                    className={styles.sendButton}
                    onClick={handleSendMessage}
                    disabled={!input.trim() || agentState.status === 'processing' || !callId}
                    aria-label={isLoading ? 'Sending message...' : 'Send message'}
                  >
                    {isLoading ? <Loader2 size={18} className={styles.spinning} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
                  </button>
                </div>
                
                <button 
                  className={styles.endButton} 
                  onClick={handleEndCall}
                  disabled={isLoading}
                  aria-label="End call"
                >
                  <PhoneOff size={18} aria-hidden="true" />
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
                {agentState.status === 'connecting' && '◌ Connecting'}
                {agentState.status === 'listening' && '● Listening'}
                {agentState.status === 'processing' && '◌ Processing'}
                {agentState.status === 'speaking' && '◉ Speaking'}
                {agentState.status === 'error' && '✕ Error'}
              </span>
            </div>
          </div>

          {/* Voice Status */}
          <div className={styles.statusCard}>
            <div className={styles.cardLabel}>
              <Mic size={14} />
              Voice Status
            </div>
            <div className={styles.voiceStatus}>
              <div className={styles.voiceIndicator}>
                <span className={`${styles.voiceDot} ${isListening ? styles.active : ''}`} />
                <span>{isListening ? 'Recording' : 'Ready'}</span>
              </div>
              <div className={styles.voiceIndicator}>
                <span className={`${styles.voiceDot} ${ttsEnabled ? styles.active : ''}`} />
                <span>{ttsEnabled ? 'TTS On' : 'TTS Off'}</span>
              </div>
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
                  {agentState.intent?.replace(/_/g, ' ') || '—'}
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
                    {agentState.escalationType || 'Escalation Recommended'}
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

          {/* Call ID */}
          {callId && (
            <div className={styles.statusCard}>
              <div className={styles.cardLabel}>
                <Wifi size={14} />
                Call ID
              </div>
              <div className={styles.callIdValue}>
                {callId.slice(0, 8)}...
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
