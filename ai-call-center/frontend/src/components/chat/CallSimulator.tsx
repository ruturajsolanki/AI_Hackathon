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
  
  // Escalation state
  const [showEscalationPanel, setShowEscalationPanel] = useState(false)
  const [isEscalated, setIsEscalated] = useState(false)
  
  // Continuous voice mode state
  const [continuousVoiceMode, setContinuousVoiceMode] = useState(true) // Enable by default
  
  // Ref to track if we should auto-restart listening
  const shouldAutoRestartRef = useRef(false)
  
  // Speech Recognition Hook - simplified, we control restart manually
  const {
    isListening,
    isSupported: isSTTSupported,
    transcript,
    interimTranscript,
    finalTranscript,
    capturedText,  // This persists after speech ends!
    error: speechError,
    permissionDenied,
    startListening,
    stopListening,
    clearTranscript,
  } = useSpeechRecognition({
    language: 'en-US',
    continuous: false, // We'll manage restart manually for better control
    interimResults: true,
    autoRestart: false, // Manual control
    autoSendDelay: 0, // Disabled - we handle it ourselves
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

  // Track transcription and update input field for visual feedback
  useEffect(() => {
    // Use capturedText (most reliable) or fall back to other transcripts
    const currentText = capturedText || finalTranscript || transcript || interimTranscript
    
    if (currentText && currentText.trim()) {
      const textToSave = currentText.trim()
      lastInterimRef.current = textToSave
      // Update input field so user can see it
      setInput(textToSave)
      console.log('[Transcript Tracker] Input updated to:', textToSave)
    }
  }, [capturedText, interimTranscript, transcript, finalTranscript])

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
    if (!ttsEnabled || !isTTSSupported()) {
      // If TTS is disabled, still restart listening in continuous mode (but not if escalated)
      if (continuousVoiceMode && isCallActive && !isEscalated) {
        setTimeout(() => {
          clearTranscript()
          startListening()
        }, 500)
      }
      return
    }
    
    try {
      await speak(text, {
        rate: 0.95, // Slightly slower for more natural sound
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
          // Auto-restart listening after AI finishes speaking in continuous mode
          if (continuousVoiceMode && isCallActive && !prev.shouldEscalate) {
            setTimeout(() => {
              clearTranscript()
              startListening()
            }, 500) // Small delay before restarting
          }
        },
      })
    } catch {
      // TTS failed, still restart listening in continuous mode (but not if escalated)
      if (continuousVoiceMode && isCallActive && !isEscalated) {
        setTimeout(() => {
          clearTranscript()
          startListening()
        }, 500)
      }
    }
  }, [ttsEnabled, continuousVoiceMode, isCallActive, isEscalated, clearTranscript, startListening])

  // ---------------------------------------------------------------------------
  // Voice Handlers
  // ---------------------------------------------------------------------------

  // Handle voice message (from speech recognition) - defined first so other functions can use it
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

  // Send a voice message directly (bypasses input state)
  const sendVoiceMessage = useCallback(async (messageText: string) => {
    if (!messageText.trim() || !callId) {
      console.log('[sendVoiceMessage] Invalid - no text or no callId')
      return
    }

    console.log('[sendVoiceMessage] Sending:', messageText)
    
    // STOP listening while we process - prevents overlapping speech
    if (isListening) {
      stopListening()
    }
    stopSpeech() // Stop any current TTS
    
    // Clear the input and transcripts
    setInput('')
    clearTranscript()
    
    // Add customer message to UI
    addMessage({
      role: 'customer',
      content: messageText,
    })

    // Set processing state - shows "Getting response..." indicator
    setAgentState(prev => ({ ...prev, status: 'processing' }))
    setIsLoading(true)

    const startTime = Date.now()

    // Call API
    console.log('[sendVoiceMessage] Calling API with message:', messageText)
    const result = await sendMessage(callId, messageText)
    
    const processingTime = Date.now() - startTime
    setIsLoading(false)

    console.log('[sendVoiceMessage] API Response:', result)

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

      // Add agent response
      if (data.responseContent) {
        addMessage({
          role: 'agent',
          content: data.responseContent,
          metadata: {
            confidence: confidenceScore,
            processingTime,
          },
        })

        // Speak the response (speakResponse handles auto-restart of listening)
        await speakResponse(data.responseContent)
      } else {
        // No response content, restart listening manually (but not if escalated)
        if (continuousVoiceMode && isCallActive && !isEscalated) {
          setTimeout(() => {
            clearTranscript()
            startListening()
          }, 500)
        }
      }

      // Handle escalation
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
  }, [callId, addMessage, speakResponse, getConfidenceLevel, getConfidenceScore])

  // Auto-send when speech recognition stops (naturally or by clicking mic)
  useEffect(() => {
    console.log('[Auto-send Effect] isListening:', isListening, 'wasListening:', wasListeningRef.current, 'capturedText:', capturedText)
    
    // Detect when isListening changes from true to false
    if (wasListeningRef.current && !isListening) {
      // Speech just stopped - use capturedText (most reliable) or fallback to input/ref
      const textToSend = capturedText || lastInterimRef.current || input
      console.log('[Auto-send Effect] Speech stopped! Text to send:', textToSend)
      console.log('[Auto-send Effect] Conditions - isCallActive:', isCallActive, 'callId:', callId, 'status:', agentState.status)
      
      if (textToSend && textToSend.trim() && isCallActive && callId && agentState.status !== 'processing') {
        console.log('[Auto-send Effect] ✅ SENDING MESSAGE:', textToSend.trim())
        sendVoiceMessage(textToSend.trim())
        // Clear after sending
        setTimeout(() => {
          lastInterimRef.current = ''
          setInput('')
          clearTranscript()
        }, 100)
      } else {
        console.log('[Auto-send Effect] ❌ Not sending - conditions not met')
      }
    }
    wasListeningRef.current = isListening
  }, [isListening, isCallActive, callId, agentState.status, sendVoiceMessage, clearTranscript, input, capturedText])

  const toggleMicrophone = useCallback(() => {
    if (!isSTTSupported) {
      setError('Speech recognition is not supported in this browser.')
      return
    }

    if (isListening) {
      // STOPPING - grab the text from ref and auto-send
      const textToSend = lastInterimRef.current
      console.log('[Mic] Stopping. Text to send:', textToSend)
      
      stopListening()
      
      if (textToSend && textToSend.trim() && isCallActive && callId) {
        const message = textToSend.trim()
        console.log('[Mic] Auto-sending message:', message)
        // Call handleSendMessage with the text directly
        sendVoiceMessage(message)
      } else {
        console.log('[Mic] No text to send or call not active')
      }
      
      clearTranscript()
      lastInterimRef.current = ''
      setInput('')
    } else {
      // STARTING
      stopSpeech()
      clearTranscript()
      lastInterimRef.current = ''
      setInput('')
      startListening()
      console.log('[Mic] Started listening')
    }
  }, [isSTTSupported, isListening, startListening, stopListening, clearTranscript, isCallActive, callId])

  const toggleTTS = useCallback(() => {
    if (!ttsEnabled) {
      setTtsEnabled(true)
    } else {
      stopSpeech()
      setTtsEnabled(false)
    }
  }, [ttsEnabled])

  // wasListeningRef is used to detect when speech stops
  const wasListeningRef = useRef(false)

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
      // Backend returns interactionId (transformed from interaction_id)
      const newCallId = (result.data as any).interactionId || (result.data as any).callId
      const initialResponse = result.data.initialResponse
      console.log('[StartCall] Response:', result.data, 'Using callId:', newCallId)
      setCallId(newCallId)
      
      // Clear connecting message and add success
      setMessages([
        {
          id: 'connected',
          role: 'system',
          content: continuousVoiceMode 
            ? 'Call connected. Hands-free mode enabled - just speak naturally!'
            : 'Call connected. AI Agent is ready. Click the microphone to speak.',
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

  // Customer session URL for escalation
  const [customerSessionUrl, setCustomerSessionUrl] = useState<string | null>(null)

  // Handle escalation to human agent
  const handleEscalateToHuman = async () => {
    // IMMEDIATELY stop everything
    stopSpeech()
    stopListening()
    setContinuousVoiceMode(false) // Disable auto-listening permanently
    
    // Mark as escalated FIRST to prevent any new messages
    setIsEscalated(true)
    setIsCallActive(false) // End the call immediately
    
    // Update agent state
    setAgentState(prev => ({
      ...prev,
      status: 'idle',
      shouldEscalate: true,
    }))
    
    addMessage({
      role: 'system',
      content: '🔄 Transferring to human agent...',
    })
    
    // End the AI call session
    const currentCallId = callId
    if (currentCallId) {
      try {
        await endCall(currentCallId)
      } catch (e) {
        console.error('Error ending call:', e)
      }
    }
    
    // Generate customer session URL
    const sessionId = currentCallId || crypto.randomUUID()
    const sessionUrl = `${window.location.origin}/customer-session/${sessionId}`
    setCustomerSessionUrl(sessionUrl)
    
    addMessage({
      role: 'system',
      content: `✅ Call transferred! A ticket has been created for a human agent.`,
    })
    
    // Clear call state
    setCallId(null)
    setShowEscalationPanel(true)
  }
  
  // Close escalation panel and continue with human
  const handleAcceptHumanHandoff = () => {
    setShowEscalationPanel(false)
    addMessage({
      role: 'system',
      content: '📞 You are now connected with a human agent.',
    })
  }

  const handleEndCall = async () => {
    // Stop any ongoing speech/listening
    stopSpeech()
    if (isListening) stopListening()

    if (!callId) {
      setIsCallActive(false)
      setIsEscalated(false)
      setShowEscalationPanel(false)
      return
    }

    setIsLoading(true)
    
    const result = await endCall(callId)
    
    setIsLoading(false)
    setIsCallActive(false)
    setCallId(null)
    setIsEscalated(false)
    setShowEscalationPanel(false)

    const endStatus = isEscalated ? 'Resolved by human agent' : 'Resolved by AI'
    addMessage({
      role: 'system',
      content: result.success 
        ? `Call ended. ${endStatus}. Duration: ${formatDuration(agentState.sessionDuration)}. ${agentState.turnCount} turns processed.`
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

      // Handle escalation automatically - no manual button needed
      if (data.shouldEscalate && !isEscalated) {
        addMessage({
          role: 'system',
          content: `⚠️ Escalation triggered: ${data.escalationReason || 'Complex issue detected'}`,
        })
        
        // Auto-transfer to human agent after brief notification
        setTimeout(() => {
          addMessage({
            role: 'system',
            content: '🔄 Automatically transferring to human agent...',
          })
          // Trigger the escalation
          handleEscalateToHuman()
        }, 2000)
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
              {/* Customer Session Panel - shown after escalation */}
              {isEscalated && customerSessionUrl && (
                <div className={styles.escalationPanel}>
                  <div className={styles.escalationIcon}>✅</div>
                  <h3>Call Transferred to Human Agent</h3>
                  <p>A ticket has been created. To continue chatting with the human agent, open the customer session:</p>
                  <div className={styles.sessionLinkContainer}>
                    <input 
                      type="text" 
                      value={customerSessionUrl} 
                      readOnly 
                      className={styles.sessionLinkInput}
                    />
                    <button 
                      className={styles.copyLinkButton}
                      onClick={() => {
                        navigator.clipboard.writeText(customerSessionUrl)
                        alert('Link copied!')
                      }}
                    >
                      Copy
                    </button>
                  </div>
                  <button 
                    className={styles.openSessionButton}
                    onClick={() => window.open(customerSessionUrl, '_blank')}
                  >
                    📱 Open Customer Session (New Tab)
                  </button>
                  <p className={styles.sessionHint}>
                    Or go to <strong>Tickets</strong> page to accept the ticket as a human agent.
                  </p>
                </div>
              )}
              
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
                
                {/* Processing indicator - shows while waiting for AI response */}
                {agentState.status === 'processing' && (
                  <div className={`${styles.message} ${styles.agent}`}>
                    <div className={styles.messageAvatar}>
                      <Bot size={16} />
                    </div>
                    <div className={styles.messageContent}>
                      <div className={styles.processing}>
                        <Loader2 size={16} className={styles.spinning} />
                        <span className={styles.processingText}>Getting AI response...</span>
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
                    placeholder={isListening ? '🎤 Speak now...' : 'Type or click mic to speak...'}
                    className={styles.input}
                    disabled={agentState.status === 'processing' || agentState.status === 'error'}
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
                    onClick={() => {
                      console.log('[Send Button] Clicked! input:', input, 'callId:', callId, 'status:', agentState.status)
                      handleSendMessage()
                    }}
                    disabled={!input.trim() || agentState.status === 'processing' || !callId}
                    title={`input: "${input}", callId: ${callId ? 'yes' : 'no'}, status: ${agentState.status}`}
                    aria-label={isLoading ? 'Sending message...' : 'Send message'}
                  >
                    {isLoading ? <Loader2 size={18} className={styles.spinning} aria-hidden="true" /> : <Send size={18} aria-hidden="true" />}
                  </button>
                </div>
                
                {/* Show escalation button when AI recommends it */}
                {agentState.shouldEscalate && !isEscalated ? (
                  <div className={styles.escalationButtons}>
                    <button 
                      className={styles.escalateButton} 
                      onClick={handleEscalateToHuman}
                      disabled={isLoading}
                      aria-label="Transfer to human agent"
                    >
                      <User size={18} aria-hidden="true" />
                      Transfer to Human
                    </button>
                    <button 
                      className={styles.endButton} 
                      onClick={handleEndCall}
                      disabled={isLoading}
                      aria-label="End call anyway"
                    >
                      <PhoneOff size={18} aria-hidden="true" />
                      End Call
                    </button>
                  </div>
                ) : (
                  <button 
                    className={styles.endButton} 
                    onClick={handleEndCall}
                    disabled={isLoading}
                    aria-label="End call"
                  >
                    <PhoneOff size={18} aria-hidden="true" />
                    End Call
                  </button>
                )}
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
                {agentState.status === 'connecting' && '◌ Connecting...'}
                {agentState.status === 'listening' && '● Listening for speech'}
                {agentState.status === 'processing' && '◌ Getting AI response...'}
                {agentState.status === 'speaking' && '◉ AI Speaking'}
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
              {isEscalated ? (
                <span className={styles.humanConnected}>
                  <User size={14} />
                  Connected to Human Agent
                </span>
              ) : agentState.shouldEscalate ? (
                <>
                  <span className={styles.escalationBadge}>
                    <AlertTriangle size={12} />
                    {agentState.escalationType || 'Escalation Recommended'}
                  </span>
                  <span className={styles.escalationReason}>
                    {agentState.escalationReason}
                  </span>
                  <button 
                    className={styles.transferButton}
                    onClick={handleEscalateToHuman}
                    disabled={isLoading}
                  >
                    <User size={14} />
                    Transfer Now
                  </button>
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
