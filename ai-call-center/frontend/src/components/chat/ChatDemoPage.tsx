import { useState } from 'react'
import { Send, Mic, Phone, PhoneOff, RotateCcw } from 'lucide-react'
import { Card } from '../common/Card'
import { Badge } from '../common/Badge'
import { ChatMessage } from './ChatMessage'
import { AgentInsights } from './AgentInsights'
import styles from './ChatDemoPage.module.css'

// Demo messages
const initialMessages = [
  {
    id: '1',
    role: 'system' as const,
    content: 'Connected to AI Call Center. How can I help you today?',
    timestamp: new Date().toISOString(),
  },
]

export function ChatDemoPage() {
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)

  const handleSend = () => {
    if (!input.trim() || isProcessing) return
    
    // Add customer message
    const customerMessage = {
      id: Date.now().toString(),
      role: 'customer' as const,
      content: input,
      timestamp: new Date().toISOString(),
    }
    
    setMessages(prev => [...prev, customerMessage])
    setInput('')
    setIsProcessing(true)
    
    // Simulate AI response
    setTimeout(() => {
      const agentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent' as const,
        content: getSimulatedResponse(input),
        timestamp: new Date().toISOString(),
        intent: detectIntent(input),
        emotion: detectEmotion(input),
        confidence: 0.85 + Math.random() * 0.1,
      }
      setMessages(prev => [...prev, agentMessage])
      setIsProcessing(false)
    }, 1000 + Math.random() * 500)
  }

  const handleReset = () => {
    setMessages(initialMessages)
    setInput('')
  }

  return (
    <div className={styles.page} role="region" aria-label="Live Demo">
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Live Demo</h1>
          <p className={styles.subtitle}>Interactive demonstration of autonomous AI agents</p>
        </div>
        <div className={styles.controls}>
          <Badge 
            variant={isConnected ? 'success' : 'danger'}
            aria-label={isConnected ? 'Connection status: Connected' : 'Connection status: Disconnected'}
          >
            {isConnected ? 'Connected' : 'Disconnected'}
          </Badge>
          <button 
            className={styles.controlButton}
            onClick={() => setIsConnected(!isConnected)}
            aria-label={isConnected ? 'Disconnect call' : 'Connect call'}
            title={isConnected ? 'Disconnect' : 'Connect'}
          >
            {isConnected ? <PhoneOff size={18} aria-hidden="true" /> : <Phone size={18} aria-hidden="true" />}
          </button>
          <button 
            className={styles.controlButton} 
            onClick={handleReset}
            aria-label="Reset conversation"
            title="Reset conversation"
          >
            <RotateCcw size={18} aria-hidden="true" />
          </button>
        </div>
      </header>
      
      <div className={styles.content}>
        <div className={styles.chatSection}>
          <Card className={styles.chatCard}>
            <div className={styles.chatHeader}>
              <div className={styles.chatInfo}>
                <span className={styles.chatTitle}>Customer Chat</span>
                <span className={styles.chatMeta}>Session ID: demo-{Date.now().toString(36)}</span>
              </div>
              <Badge variant="info">Chat</Badge>
            </div>
            
            <div className={styles.messagesContainer}>
              <div className={styles.messages}>
                {messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))}
                {isProcessing && (
                  <div className={styles.typing}>
                    <span className={styles.typingDot} />
                    <span className={styles.typingDot} />
                    <span className={styles.typingDot} />
                  </div>
                )}
              </div>
            </div>
            
            <div className={styles.inputContainer}>
              <label htmlFor="chat-input" className={styles.srOnly}>
                Type your message
              </label>
              <input
                id="chat-input"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Type your message..."
                className={styles.input}
                disabled={!isConnected || isProcessing}
                aria-label="Type your message"
              />
              <button 
                className={styles.voiceButton} 
                disabled
                aria-label="Voice input (coming soon)"
                title="Voice input coming soon"
              >
                <Mic size={18} aria-hidden="true" />
              </button>
              <button 
                className={styles.sendButton}
                onClick={handleSend}
                disabled={!input.trim() || !isConnected || isProcessing}
                aria-label="Send message"
              >
                <Send size={18} aria-hidden="true" />
              </button>
            </div>
          </Card>
        </div>
        
        <div className={styles.insightsSection}>
          <AgentInsights messages={messages} />
        </div>
      </div>
    </div>
  )
}

// Simulated response logic
function getSimulatedResponse(input: string): string {
  const lower = input.toLowerCase()
  
  if (lower.includes('bill') || lower.includes('charge') || lower.includes('payment')) {
    return "I can help you with your billing inquiry. I've retrieved your account information and can see your current balance is $142.50 with a payment due on the 15th. Would you like me to explain any specific charges or help you set up a payment?"
  }
  
  if (lower.includes('order') || lower.includes('shipping') || lower.includes('delivery')) {
    return "I'd be happy to help you track your order. I can see your most recent order #12847 was shipped yesterday and is currently in transit. Expected delivery is within 2-3 business days. Would you like the tracking number?"
  }
  
  if (lower.includes('cancel') || lower.includes('refund')) {
    return "I understand you'd like to discuss cancellation. Before we proceed, I'd like to understand your concerns better. Could you tell me what's prompting this request? I may be able to help address any issues."
  }
  
  if (lower.includes('help') || lower.includes('support')) {
    return "I'm here to help! I can assist you with billing inquiries, order tracking, account management, technical support, and more. What would you like help with today?"
  }
  
  return "Thank you for your message. I'm here to assist you. Could you provide more details about what you need help with? I can assist with billing, orders, account issues, and more."
}

function detectIntent(input: string): string {
  const lower = input.toLowerCase()
  if (lower.includes('bill') || lower.includes('payment')) return 'billing_inquiry'
  if (lower.includes('order') || lower.includes('track')) return 'order_status'
  if (lower.includes('cancel') || lower.includes('refund')) return 'cancellation'
  if (lower.includes('help') || lower.includes('support')) return 'general_inquiry'
  return 'general_inquiry'
}

function detectEmotion(input: string): string {
  const lower = input.toLowerCase()
  if (lower.includes('frustrated') || lower.includes('annoying')) return 'frustrated'
  if (lower.includes('angry') || lower.includes('unacceptable')) return 'angry'
  if (lower.includes('thank') || lower.includes('great')) return 'satisfied'
  return 'neutral'
}
