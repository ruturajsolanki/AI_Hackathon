/**
 * Text-to-Speech Utility
 * 
 * Browser-based speech synthesis using Web Speech API.
 * Handles text-to-speech with queue management and controls.
 * Enhanced with natural-sounding voice selection.
 */

// -----------------------------------------------------------------------------
// Types
// -----------------------------------------------------------------------------

export interface SpeechOptions {
  /** Voice to use (by name or index) */
  voice?: string | number
  /** Speech rate (0.1 to 10, default: 1) */
  rate?: number
  /** Speech pitch (0 to 2, default: 1) */
  pitch?: number
  /** Speech volume (0 to 1, default: 1) */
  volume?: number
  /** Language code (e.g., 'en-US') */
  lang?: string
  /** Callback when speech starts */
  onStart?: () => void
  /** Callback when speech ends */
  onEnd?: () => void
  /** Callback on error */
  onError?: (error: string) => void
}

export interface SpeechState {
  isSpeaking: boolean
  isPaused: boolean
  isSupported: boolean
}

export interface VoiceInfo {
  name: string
  lang: string
  default: boolean
  localService: boolean
  voiceURI: string
}

// -----------------------------------------------------------------------------
// State
// -----------------------------------------------------------------------------

let currentUtterance: SpeechSynthesisUtterance | null = null
let speechQueue: Array<{ text: string; options: SpeechOptions }> = []
let isProcessingQueue = false
let preferredVoice: SpeechSynthesisVoice | null = null
let voicesLoaded = false

// -----------------------------------------------------------------------------
// Natural Voice Selection
// -----------------------------------------------------------------------------

// Priority list of natural-sounding voices (most human-like first)
const PREFERRED_VOICES = [
  // Premium voices (macOS/iOS)
  'Samantha',        // macOS - very natural female
  'Karen',           // macOS - Australian female
  'Daniel',          // macOS - British male
  'Moira',           // macOS - Irish female
  'Tessa',           // macOS - South African female
  'Fiona',           // macOS - Scottish female
  
  // Google voices (Chrome)
  'Google UK English Female',
  'Google UK English Male', 
  'Google US English',
  
  // Microsoft voices (Edge/Windows)
  'Microsoft Zira',       // Female
  'Microsoft David',      // Male
  'Microsoft Jenny',      // Neural voice
  'Microsoft Aria',       // Neural voice
  
  // Enhanced voices
  'Siri Female',
  'Siri Male',
  'Alex',
  
  // Fallback natural voices
  'English (America)',
  'English (United Kingdom)',
]

/**
 * Find the best natural-sounding voice.
 */
function findBestVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (voices.length === 0) return null
  
  // Try to find a preferred voice
  for (const preferredName of PREFERRED_VOICES) {
    const voice = voices.find(v => 
      v.name.toLowerCase().includes(preferredName.toLowerCase())
    )
    if (voice) {
      console.log('[TTS] Selected voice:', voice.name)
      return voice
    }
  }
  
  // Look for any English voice that's not robotic
  const englishVoice = voices.find(v => 
    v.lang.startsWith('en') && 
    !v.name.toLowerCase().includes('compact') &&
    !v.name.toLowerCase().includes('espeak')
  )
  if (englishVoice) {
    console.log('[TTS] Selected English voice:', englishVoice.name)
    return englishVoice
  }
  
  // Last resort: use default or first voice
  const defaultVoice = voices.find(v => v.default)
  console.log('[TTS] Using default voice:', defaultVoice?.name || voices[0]?.name)
  return defaultVoice || voices[0] || null
}

/**
 * Initialize voice selection.
 */
function initializeVoices(): void {
  if (!isSupported()) return
  
  const loadVoices = () => {
    const voices = window.speechSynthesis.getVoices()
    if (voices.length > 0) {
      preferredVoice = findBestVoice(voices)
      voicesLoaded = true
    }
  }
  
  // Voices may be loaded already or need to wait
  loadVoices()
  
  if (!voicesLoaded) {
    window.speechSynthesis.addEventListener('voiceschanged', loadVoices)
  }
}

// Initialize on import
if (typeof window !== 'undefined') {
  // Delay initialization to ensure DOM is ready
  setTimeout(initializeVoices, 100)
}

// -----------------------------------------------------------------------------
// Support Check
// -----------------------------------------------------------------------------

/**
 * Check if speech synthesis is supported in the browser.
 */
export function isSupported(): boolean {
  return typeof window !== 'undefined' && 
    'speechSynthesis' in window &&
    'SpeechSynthesisUtterance' in window
}

// -----------------------------------------------------------------------------
// Voice Management
// -----------------------------------------------------------------------------

/**
 * Get available voices.
 * Note: Voices may load asynchronously, call this after a short delay or on voiceschanged event.
 */
export function getVoices(): VoiceInfo[] {
  if (!isSupported()) return []
  
  return window.speechSynthesis.getVoices().map(voice => ({
    name: voice.name,
    lang: voice.lang,
    default: voice.default,
    localService: voice.localService,
    voiceURI: voice.voiceURI,
  }))
}

/**
 * Get voices for a specific language.
 */
export function getVoicesForLanguage(lang: string): VoiceInfo[] {
  return getVoices().filter(voice => 
    voice.lang.toLowerCase().startsWith(lang.toLowerCase())
  )
}

/**
 * Get the currently selected preferred voice.
 */
export function getPreferredVoice(): VoiceInfo | null {
  if (!preferredVoice) return null
  return {
    name: preferredVoice.name,
    lang: preferredVoice.lang,
    default: preferredVoice.default,
    localService: preferredVoice.localService,
    voiceURI: preferredVoice.voiceURI,
  }
}

/**
 * Wait for voices to load (they load asynchronously in some browsers).
 */
export function waitForVoices(timeout = 3000): Promise<VoiceInfo[]> {
  return new Promise((resolve) => {
    if (!isSupported()) {
      resolve([])
      return
    }

    const voices = getVoices()
    if (voices.length > 0) {
      resolve(voices)
      return
    }

    const handleVoicesChanged = () => {
      window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged)
      resolve(getVoices())
    }

    window.speechSynthesis.addEventListener('voiceschanged', handleVoicesChanged)

    // Timeout fallback
    setTimeout(() => {
      window.speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged)
      resolve(getVoices())
    }, timeout)
  })
}

// -----------------------------------------------------------------------------
// Core Functions
// -----------------------------------------------------------------------------

/**
 * Speak text using browser speech synthesis.
 * Uses the best available natural-sounding voice.
 */
export function speak(text: string, options: SpeechOptions = {}): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!isSupported()) {
      const error = 'Speech synthesis is not supported in this browser.'
      options.onError?.(error)
      reject(new Error(error))
      return
    }

    if (!text.trim()) {
      resolve()
      return
    }

    // Cancel any current speech
    stop()

    const utterance = new SpeechSynthesisUtterance(text)
    currentUtterance = utterance

    // Apply options - use slightly slower rate for more natural speech
    utterance.rate = Math.max(0.1, Math.min(10, options.rate ?? 0.95))
    utterance.pitch = Math.max(0, Math.min(2, options.pitch ?? 1.0))
    utterance.volume = Math.max(0, Math.min(1, options.volume ?? 1))

    if (options.lang) {
      utterance.lang = options.lang
    }

    // Set voice - use preferred voice if no specific voice requested
    if (options.voice !== undefined) {
      const voices = window.speechSynthesis.getVoices()
      
      if (typeof options.voice === 'number') {
        if (options.voice >= 0 && options.voice < voices.length) {
          utterance.voice = voices[options.voice]
        }
      } else if (typeof options.voice === 'string') {
        const matchedVoice = voices.find(v => 
          v.name.toLowerCase().includes(options.voice!.toString().toLowerCase())
        )
        if (matchedVoice) {
          utterance.voice = matchedVoice
        }
      }
    } else if (preferredVoice) {
      // Use our preferred natural-sounding voice
      utterance.voice = preferredVoice
    }

    // Event handlers
    utterance.onstart = () => {
      options.onStart?.()
    }

    utterance.onend = () => {
      currentUtterance = null
      options.onEnd?.()
      resolve()
      processQueue()
    }

    utterance.onerror = (event) => {
      currentUtterance = null
      const errorMessage = `Speech synthesis error: ${event.error}`
      options.onError?.(errorMessage)
      
      // Don't reject on 'canceled' - it's expected when stop() is called
      if (event.error === 'canceled') {
        resolve()
      } else {
        reject(new Error(errorMessage))
      }
      
      processQueue()
    }

    // Speak
    window.speechSynthesis.speak(utterance)
  })
}

/**
 * Add text to speech queue (speaks after current speech ends).
 */
export function enqueue(text: string, options: SpeechOptions = {}): void {
  speechQueue.push({ text, options })
  
  if (!isProcessingQueue && !isSpeaking()) {
    processQueue()
  }
}

/**
 * Process the speech queue.
 */
async function processQueue(): Promise<void> {
  if (isProcessingQueue || speechQueue.length === 0) return
  
  isProcessingQueue = true
  
  while (speechQueue.length > 0) {
    const item = speechQueue.shift()
    if (item) {
      try {
        await speak(item.text, item.options)
      } catch {
        // Continue with next item on error
      }
    }
  }
  
  isProcessingQueue = false
}

/**
 * Stop current speech and clear queue.
 */
export function stop(): void {
  if (!isSupported()) return
  
  // Clear queue
  speechQueue = []
  isProcessingQueue = false
  
  // Cancel current speech
  window.speechSynthesis.cancel()
  currentUtterance = null
}

/**
 * Pause current speech.
 */
export function pause(): void {
  if (!isSupported()) return
  window.speechSynthesis.pause()
}

/**
 * Resume paused speech.
 */
export function resume(): void {
  if (!isSupported()) return
  window.speechSynthesis.resume()
}

// -----------------------------------------------------------------------------
// State Queries
// -----------------------------------------------------------------------------

/**
 * Check if currently speaking.
 */
export function isSpeaking(): boolean {
  if (!isSupported()) return false
  return window.speechSynthesis.speaking
}

/**
 * Check if speech is paused.
 */
export function isPaused(): boolean {
  if (!isSupported()) return false
  return window.speechSynthesis.paused
}

/**
 * Check if there are items in the queue.
 */
export function hasQueuedItems(): boolean {
  return speechQueue.length > 0
}

/**
 * Get current speech state.
 */
export function getState(): SpeechState {
  return {
    isSpeaking: isSpeaking(),
    isPaused: isPaused(),
    isSupported: isSupported(),
  }
}

/**
 * Get queue length.
 */
export function getQueueLength(): number {
  return speechQueue.length
}

/**
 * Clear the queue without stopping current speech.
 */
export function clearQueue(): void {
  speechQueue = []
}

// -----------------------------------------------------------------------------
// Convenience Functions
// -----------------------------------------------------------------------------

/**
 * Speak text with a specific language.
 */
export function speakInLanguage(text: string, lang: string, options: Omit<SpeechOptions, 'lang'> = {}): Promise<void> {
  return speak(text, { ...options, lang })
}

/**
 * Speak text slowly (rate: 0.8).
 */
export function speakSlowly(text: string, options: Omit<SpeechOptions, 'rate'> = {}): Promise<void> {
  return speak(text, { ...options, rate: 0.8 })
}

/**
 * Speak text quickly (rate: 1.3).
 */
export function speakQuickly(text: string, options: Omit<SpeechOptions, 'rate'> = {}): Promise<void> {
  return speak(text, { ...options, rate: 1.3 })
}

// -----------------------------------------------------------------------------
// Default Export
// -----------------------------------------------------------------------------

export default {
  speak,
  enqueue,
  stop,
  pause,
  resume,
  isSpeaking,
  isPaused,
  isSupported,
  getVoices,
  getVoicesForLanguage,
  getPreferredVoice,
  waitForVoices,
  getState,
  getQueueLength,
  hasQueuedItems,
  clearQueue,
  speakInLanguage,
  speakSlowly,
  speakQuickly,
}
