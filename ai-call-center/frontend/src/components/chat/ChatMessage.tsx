import { User, Bot, Info } from 'lucide-react'
import styles from './ChatMessage.module.css'

interface MessageProps {
  message: {
    id: string
    role: 'customer' | 'agent' | 'system'
    content: string
    timestamp: string
    intent?: string
    emotion?: string
    confidence?: number
  }
}

export function ChatMessage({ message }: MessageProps) {
  const isCustomer = message.role === 'customer'
  const isSystem = message.role === 'system'
  
  const Icon = isCustomer ? User : isSystem ? Info : Bot
  
  return (
    <div className={`${styles.message} ${styles[message.role]}`}>
      <div className={styles.avatar}>
        <Icon size={16} />
      </div>
      <div className={styles.content}>
        <div className={styles.header}>
          <span className={styles.role}>
            {isCustomer ? 'Customer' : isSystem ? 'System' : 'AI Agent'}
          </span>
          <span className={styles.time}>
            {new Date(message.timestamp).toLocaleTimeString([], { 
              hour: '2-digit', 
              minute: '2-digit' 
            })}
          </span>
        </div>
        <p className={styles.text}>{message.content}</p>
        {message.role === 'agent' && message.confidence && (
          <div className={styles.meta}>
            <span className={styles.metaItem}>
              Intent: <strong>{message.intent?.replace('_', ' ')}</strong>
            </span>
            <span className={styles.metaItem}>
              Confidence: <strong>{(message.confidence * 100).toFixed(0)}%</strong>
            </span>
          </div>
        )}
      </div>
    </div>
  )
}
