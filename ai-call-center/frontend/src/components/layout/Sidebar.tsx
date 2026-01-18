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
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', description: 'View analytics overview' },
  { to: '/demo', icon: MessageSquare, label: 'Live Demo', description: 'Interactive call simulation' },
  { to: '/interactions', icon: Headphones, label: 'Interactions', description: 'View call history' },
  { to: '/agents', icon: Users, label: 'Agents', disabled: true, description: 'Coming soon' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics', disabled: true, description: 'Coming soon' },
  { to: '/settings', icon: Settings, label: 'Settings', disabled: true, description: 'Coming soon' },
]

export function Sidebar() {
  return (
    <aside className={styles.sidebar} role="navigation" aria-label="Main navigation">
      <div className={styles.logo}>
        <div className={styles.logoIcon} aria-hidden="true">
          <Zap size={24} />
        </div>
        <div className={styles.logoText}>
          <span className={styles.logoTitle}>AI Call Center</span>
          <span className={styles.logoSubtitle}>Autonomous Agents</span>
        </div>
      </div>
      
      <nav className={styles.nav} aria-label="Primary">
        {navItems.map(({ to, icon: Icon, label, disabled, description }) => (
          <NavLink
            key={to}
            to={disabled ? '#' : to}
            className={({ isActive }) => 
              `${styles.navItem} ${isActive && !disabled ? styles.active : ''} ${disabled ? styles.disabled : ''}`
            }
            onClick={disabled ? (e) => e.preventDefault() : undefined}
            aria-disabled={disabled}
            aria-current={!disabled ? 'page' : undefined}
            title={description}
          >
            <Icon size={20} aria-hidden="true" />
            <span>{label}</span>
            {disabled && (
              <span className={styles.badge} aria-label="Coming soon">
                Soon
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      
      <div className={styles.footer}>
        <div className={styles.status} role="status" aria-live="polite">
          <span className={styles.statusDot} aria-hidden="true" />
          <span>System Operational</span>
        </div>
      </div>
    </aside>
  )
}
