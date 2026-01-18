/**
 * useSpeechRecognition Hook
 * 
 * Custom React hook for browser-based speech recognition using Web Speech API.
 * Handles microphone permissions, transcription, and error states.
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

export type UseSpeechRecognitionReturn = SpeechRecognitionState & SpeechRecognitionControls

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
  } = options

  // State
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [finalTranscript, setFinalTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [permissionDenied, setPermissionDenied] = useState(false)

  // Refs
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null)
  const isStoppingRef = useRef(false)

  // Check browser support
  const isSupported = typeof window !== 'undefined' && 
    !!(window.SpeechRecognition || window.webkitSpeechRecognition)

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
    }

    recognition.onend = () => {
      console.log('[SpeechRecognition] Recognition ended')
      setIsListening(false)
      // Don't clear interim transcript here - let the caller handle it
      
      // Auto-restart if enabled and not manually stopped
      if (autoRestart && !isStoppingRef.current) {
        try {
          recognition.start()
        } catch {
          // Ignore restart errors
        }
      }
      isStoppingRef.current = false
    }

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      console.log('[SpeechRecognition] onresult event received')
      let interim = ''
      let final = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcriptText = result[0].transcript
        console.log('[SpeechRecognition] Result:', transcriptText, 'isFinal:', result.isFinal)

        if (result.isFinal) {
          final += transcriptText
        } else {
          interim += transcriptText
        }
      }

      console.log('[SpeechRecognition] Setting - final:', final, 'interim:', interim)
      
      if (final) {
        setFinalTranscript(prev => prev + final)
        setTranscript(prev => prev + final)
      }
      
      setInterimTranscript(interim)
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
      
      setError(errorMessage)
      setIsListening(false)

      if (event.error === 'not-allowed') {
        setPermissionDenied(true)
      }
    }

    recognition.onspeechend = () => {
      // Don't auto-stop - let the user click the mic button to stop
      // This gives us time to capture the final transcript
      console.log('[SpeechRecognition] Speech ended')
    }

    recognition.onnomatch = () => {
      setError('No speech was recognized. Please try again.')
    }

    recognitionRef.current = recognition

    // Cleanup
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {
          // Ignore abort errors
        }
      }
    }
  }, [language, continuous, interimResults, maxAlternatives, autoRestart, isSupported])

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

    try {
      recognitionRef.current.start()
    } catch (err) {
      if (err instanceof Error && err.message.includes('already started')) {
        // Already listening, ignore
      } else {
        setError('Failed to start speech recognition.')
      }
    }
  }, [isSupported, isListening])

  // Stop listening
  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) return

    console.log('[SpeechRecognition] stopListening called')
    isStoppingRef.current = true

    try {
      recognitionRef.current.stop()
    } catch {
      // Ignore stop errors
    }

    setIsListening(false)
    // DON'T clear transcripts here - let the caller grab them first
    // The caller should call clearTranscript() after using the transcript
  }, [isListening])

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
