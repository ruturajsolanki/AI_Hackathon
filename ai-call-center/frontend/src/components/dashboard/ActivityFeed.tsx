import { MessageSquare, ArrowUpRight, CheckCircle, AlertCircle } from 'lucide-react'
import styles from './ActivityFeed.module.css'

// Simulated activity data
const activities = [
  {
    id: '1',
    type: 'message',
    title: 'New interaction started',
    description: 'Customer inquiry about billing',
    time: '2 min ago',
    status: 'active',
  },
  {
    id: '2',
    type: 'resolved',
    title: 'Interaction resolved',
    description: 'Technical support - password reset',
    time: '5 min ago',
    status: 'success',
  },
  {
    id: '3',
    type: 'escalated',
    title: 'Escalated to human',
    description: 'Complex complaint - high emotion detected',
    time: '8 min ago',
    status: 'warning',
  },
  {
    id: '4',
    type: 'message',
    title: 'New interaction started',
    description: 'Order status inquiry',
    time: '12 min ago',
    status: 'active',
  },
  {
    id: '5',
    type: 'resolved',
    title: 'Interaction resolved',
    description: 'Product information request',
    time: '15 min ago',
    status: 'success',
  },
]

const iconMap = {
  message: MessageSquare,
  resolved: CheckCircle,
  escalated: ArrowUpRight,
}

export function ActivityFeed() {
  return (
    <div className={styles.feed}>
      {activities.map((activity, index) => {
        const Icon = iconMap[activity.type as keyof typeof iconMap] || AlertCircle
        
        return (
          <div 
            key={activity.id} 
            className={styles.item}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className={`${styles.icon} ${styles[activity.status]}`}>
              <Icon size={16} />
            </div>
            <div className={styles.content}>
              <span className={styles.title}>{activity.title}</span>
              <span className={styles.description}>{activity.description}</span>
            </div>
            <span className={styles.time}>{activity.time}</span>
          </div>
        )
      })}
    </div>
  )
}
