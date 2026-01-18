/**
 * useSpeechRecognition Hook
 * 
 * Custom React hook for browser-based speech recognition using Web Speech API.
 * Handles microphone permissions, transcription, and error states.
 * Supports continuous listening mode for hands-free operation.
 */

import { useState, useEffect, useRef, useCallback } from 'react'

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

export interface SpeechRecognitionOptions {
  /** Language for recognition (default: 'en-US') */
  language?: string
  /** Enable continuous listening (default: false) */
  continuous?: boolean
  /** Return interim results while speaking (default: true) */
  interimResults?: boolean
  /** Maximum alternatives to return (default: 1) */
  maxAlternatives?: number
  /** Auto-restart on end (default: false) */
  autoRestart?: boolean
  /** Auto-send after silence (milliseconds, 0 = disabled) */
  autoSendDelay?: number
  /** Callback when speech ends naturally (for auto-send) */
  onSpeechEnd?: (transcript: string) => void
}

export interface SpeechRecognitionState {
  /** Whether the microphone is currently listening */
  isListening: boolean
  /** Whether the browser supports speech recognition */
  isSupported: boolean
  /** Current transcribed text */
  transcript: string
  /** Interim transcript (while still speaking) */
  interimTranscript: string
  /** Final confirmed transcript */
  finalTranscript: string
  /** Current error message */
  error: string | null
  /** Whether microphone permission was denied */
  permissionDenied: boolean
}

export interface SpeechRecognitionControls {
  /** Start listening */
  startListening: () => void
  /** Stop listening */
  stopListening: () => void
  /** Toggle listening state */
  toggleListening: () => void
  /** Clear all transcripts */
  clearTranscript: () => void
  /** Reset error state */
  clearError: () => void
}

export type UseSpeechRecognitionReturn = SpeechRecognitionState & SpeechRecognitionControls & {
  /** The last captured text (persists after recognition ends) */
  capturedText: string
}

// -----------------------------------------------------------------------------
// Browser API Types
// -----------------------------------------------------------------------------

interface SpeechRecognitionEvent extends Event {
  resultIndex: number
  results: SpeechRecognitionResultList
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string
  message?: string
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  start: () => void
  stop: () => void
  abort: () => void
  onstart: ((event: Event) => void) | null
  onend: ((event: Event) => void) | null
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onspeechend: ((event: Event) => void) | null
  onnomatch: ((event: Event) => void) | null
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance
  }
}

// -----------------------------------------------------------------------------
// Hook Implementation
// -----------------------------------------------------------------------------

export function useSpeechRecognition(
  options: SpeechRecognitionOptions = {}
): UseSpeechRecognitionReturn {
  const {
    language = 'en-US',
    continuous = false,
    interimResults = true,
    maxAlternatives = 1,
    autoRestart = false,
    autoSendDelay = 0,
    onSpeechEnd,
  } = options

  // State
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [finalTranscript, setFinalTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [permissionDenied, setPermissionDenied] = useState(false)
  
  // This stores the LAST captured text - never cleared by state updates
  const [capturedText, setCapturedText] = useState('')

  // Refs
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const isStoppingRef = useRef(false)
  const lastCapturedRef = useRef('')
  const autoSendTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const currentTranscriptRef = useRef('')
  const shouldAutoRestartRef = useRef(autoRestart)

  // Update ref when option changes
  useEffect(() => {
    shouldAutoRestartRef.current = autoRestart
  }, [autoRestart])

  // Check browser support
  const isSupported = typeof window !== 'undefined' && 
    !!(window.SpeechRecognition || window.webkitSpeechRecognition)

  // Clear auto-send timer
  const clearAutoSendTimer = useCallback(() => {
    if (autoSendTimerRef.current) {
      clearTimeout(autoSendTimerRef.current)
      autoSendTimerRef.current = null
    }
  }, [])

  // Initialize recognition instance
  useEffect(() => {
    if (!isSupported) return

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    
    recognition.continuous = continuous
    recognition.interimResults = interimResults
    recognition.lang = language
    recognition.maxAlternatives = maxAlternatives

    // Event handlers
    recognition.onstart = () => {
      setIsListening(true)
      setError(null)
      currentTranscriptRef.current = ''
    }

    recognition.onend = () => {
      console.log('[SpeechRecognition] Recognition ended')
      setIsListening(false)
      
      // If we have text and auto-send is enabled, trigger callback
      if (autoSendDelay > 0 && currentTranscriptRef.current && onSpeechEnd) {
        clearAutoSendTimer()
        autoSendTimerRef.current = setTimeout(() => {
          if (currentTranscriptRef.current) {
            onSpeechEnd(currentTranscriptRef.current)
            currentTranscriptRef.current = ''
          }
        }, autoSendDelay)
      }
      
      // Auto-restart if enabled and not manually stopped
      if (shouldAutoRestartRef.current && !isStoppingRef.current) {
        setTimeout(() => {
          try {
            recognition.start()
          } catch {
            // Ignore restart errors
          }
        }, 500) // Small delay before restart
      }
      isStoppingRef.current = false
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = ''
      let final = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcriptText = result[0].transcript

        if (result.isFinal) {
          final += transcriptText
        } else {
          interim += transcriptText
        }
      }
      
      if (final) {
        setFinalTranscript(prev => prev + final)
        setTranscript(prev => prev + final)
        lastCapturedRef.current = final
        setCapturedText(final)
        currentTranscriptRef.current = final
        console.log('[SpeechRecognition] Final:', final)
      }
      
      if (interim) {
        setInterimTranscript(interim)
        // Also track interim for auto-send
        currentTranscriptRef.current = interim
        lastCapturedRef.current = interim
        setCapturedText(interim)
      }
    }

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      const errorMessages: Record<string, string> = {
        'not-allowed': 'Microphone permission denied. Please allow microphone access.',
        'no-speech': 'No speech detected. Please try again.',
        'audio-capture': 'No microphone found. Please check your audio input device.',
        'network': 'Network error occurred. Please check your connection.',
        'aborted': 'Speech recognition was aborted.',
        'service-not-allowed': 'Speech recognition service is not allowed.',
      }

      const errorMessage = errorMessages[event.error] || `Speech recognition error: ${event.error}`
      
      // Don't set error for 'no-speech' in continuous mode - just restart
      if (event.error === 'no-speech' && shouldAutoRestartRef.current) {
        console.log('[SpeechRecognition] No speech, will restart...')
        return
      }
      
      setError(errorMessage)
      setIsListening(false)

      if (event.error === 'not-allowed') {
        setPermissionDenied(true)
      }
    }

    recognition.onspeechend = () => {
      console.log('[SpeechRecognition] Speech ended')
      // In non-continuous mode, this triggers before onend
      // In continuous mode, recognition keeps going
    }

    recognition.onnomatch = () => {
      // Don't show error in continuous mode
      if (!shouldAutoRestartRef.current) {
        setError('No speech was recognized. Please try again.')
      }
    }

    recognitionRef.current = recognition

    // Cleanup
    return () => {
      clearAutoSendTimer()
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {
          // Ignore abort errors
        }
      }
    }
  }, [language, continuous, interimResults, maxAlternatives, isSupported, autoSendDelay, onSpeechEnd, clearAutoSendTimer])

  // Update language dynamically
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = language
    }
  }, [language])

  // Start listening
  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser.')
      return
    }

    if (!recognitionRef.current) {
      setError('Speech recognition not initialized.')
      return
    }

    if (isListening) return

    setError(null)
    setPermissionDenied(false)
    isStoppingRef.current = false
    clearAutoSendTimer()

    try {
      recognitionRef.current.start()
    } catch (err) {
      if (err instanceof Error && err.message.includes('already started')) {
        // Already listening, ignore
      } else {
        setError('Failed to start speech recognition.')
      }
    }
  }, [isSupported, isListening, clearAutoSendTimer])

  // Stop listening
  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) return

    console.log('[SpeechRecognition] stopListening called')
    isStoppingRef.current = true
    shouldAutoRestartRef.current = false // Disable auto-restart when manually stopped
    clearAutoSendTimer()

    try {
      recognitionRef.current.stop()
    } catch {
      // Ignore stop errors
    }

    setIsListening(false)
  }, [isListening, clearAutoSendTimer])

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  // Clear transcript
  const clearTranscript = useCallback(() => {
    setTranscript('')
    setInterimTranscript('')
    setFinalTranscript('')
    currentTranscriptRef.current = ''
  }, [])

  // Clear error
  const clearError = useCallback(() => {
    setError(null)
    setPermissionDenied(false)
  }, [])

  return {
    // State
    isListening,
    isSupported,
    transcript,
    interimTranscript,
    finalTranscript,
    capturedText,
    error,
    permissionDenied,
    // Controls
    startListening,
    stopListening,
    toggleListening,
    clearTranscript,
    clearError,
  }
}

export default useSpeechRecognition
