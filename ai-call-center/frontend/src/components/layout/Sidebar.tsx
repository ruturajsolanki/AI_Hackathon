import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  MessageSquare, 
  Users, 
  BarChart3, 
  Settings,
  Headphones,
  Zap
} from 'lucide-react'
import styles from './Sidebar.module.css'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/demo', icon: MessageSquare, label: 'Live Demo' },
  { to: '/interactions', icon: Headphones, label: 'Interactions', disabled: true },
  { to: '/agents', icon: Users, label: 'Agents', disabled: true },
  { to: '/analytics', icon: BarChart3, label: 'Analytics', disabled: true },
  { to: '/settings', icon: Settings, label: 'Settings', disabled: true },
]

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <div className={styles.logoIcon}>
          <Zap size={24} />
        </div>
        <div className={styles.logoText}>
          <span className={styles.logoTitle}>AI Call Center</span>
          <span className={styles.logoSubtitle}>Autonomous Agents</span>
        </div>
      </div>
      
      <nav className={styles.nav}>
        {navItems.map(({ to, icon: Icon, label, disabled }) => (
          <NavLink
            key={to}
            to={disabled ? '#' : to}
            className={({ isActive }) => 
              `${styles.navItem} ${isActive && !disabled ? styles.active : ''} ${disabled ? styles.disabled : ''}`
            }
            onClick={disabled ? (e) => e.preventDefault() : undefined}
          >
            <Icon size={20} />
            <span>{label}</span>
            {disabled && <span className={styles.badge}>Soon</span>}
          </NavLink>
        ))}
      </nav>
      
      <div className={styles.footer}>
        <div className={styles.status}>
          <span className={styles.statusDot} />
          <span>System Operational</span>
        </div>
      </div>
    </aside>
  )
}
