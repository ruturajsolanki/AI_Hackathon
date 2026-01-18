/**
 * VoiceVisualizer Component
 * 
 * Displays a real-time audio waveform visualization during voice input.
 * Uses the Web Audio API to analyze microphone input and render
 * frequency bars that respond to speech volume.
 */

import { useEffect, useRef, useState } from 'react'
import styles from './VoiceVisualizer.module.css'

interface VoiceVisualizerProps {
  isListening: boolean
  barCount?: number
  className?: string
}

export function VoiceVisualizer({ 
  isListening, 
  barCount = 5,
  className = '' 
}: VoiceVisualizerProps) {
  const [bars, setBars] = useState<number[]>(Array(barCount).fill(0.3))
  const animationRef = useRef<number | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  
  useEffect(() => {
    if (!isListening) {
      // Stop visualization when not listening
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
        animationRef.current = null
      }
      
      // Clean up audio resources
      if (sourceRef.current) {
        sourceRef.current.disconnect()
        sourceRef.current = null
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }
      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close()
        audioContextRef.current = null
      }
      
      // Reset bars to idle state
      setBars(Array(barCount).fill(0.3))
      return
    }
    
    // Start visualization
    const startVisualization = async () => {
      try {
        // Get microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        streamRef.current = stream
        
        // Create audio context and analyser
        const audioContext = new AudioContext()
        audioContextRef.current = audioContext
        
        const analyser = audioContext.createAnalyser()
        analyser.fftSize = 64
        analyser.smoothingTimeConstant = 0.7
        analyserRef.current = analyser
        
        const source = audioContext.createMediaStreamSource(stream)
        source.connect(analyser)
        sourceRef.current = source
        
        // Start animation loop
        const dataArray = new Uint8Array(analyser.frequencyBinCount)
        
        const animate = () => {
          if (!analyserRef.current) return
          
          analyserRef.current.getByteFrequencyData(dataArray)
          
          // Calculate average volumes for each bar
          const step = Math.floor(dataArray.length / barCount)
          const newBars = []
          
          for (let i = 0; i < barCount; i++) {
            let sum = 0
            for (let j = 0; j < step; j++) {
              sum += dataArray[i * step + j]
            }
            // Normalize to 0.1-1.0 range
            const average = sum / step / 255
            newBars.push(Math.max(0.15, Math.min(1, average * 1.5 + 0.15)))
          }
          
          setBars(newBars)
          animationRef.current = requestAnimationFrame(animate)
        }
        
        animate()
      } catch (error) {
        console.warn('Could not access microphone for visualization:', error)
        // Fallback to animated bars
        startFallbackAnimation()
      }
    }
    
    const startFallbackAnimation = () => {
      // Animate with random values when mic access fails
      const animate = () => {
        const newBars = Array(barCount).fill(0).map(() => 
          0.3 + Math.random() * 0.5
        )
        setBars(newBars)
        animationRef.current = requestAnimationFrame(() => {
          setTimeout(() => animate(), 150)
        })
      }
      animate()
    }
    
    startVisualization()
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [isListening, barCount])
  
  return (
    <div 
      className={`${styles.visualizer} ${isListening ? styles.active : ''} ${className}`}
      role="presentation"
      aria-label={isListening ? "Listening to your voice" : "Voice input inactive"}
    >
      {bars.map((height, index) => (
        <div 
          key={index}
          className={styles.bar}
          style={{ 
            height: `${height * 100}%`,
            animationDelay: `${index * 50}ms`,
          }}
        />
      ))}
    </div>
  )
}

export default VoiceVisualizer
