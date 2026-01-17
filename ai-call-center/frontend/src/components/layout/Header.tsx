import { Bell, Search, User } from 'lucide-react'
import styles from './Header.module.css'

export function Header() {
  return (
    <header className={styles.header} role="banner">
      <div className={styles.search}>
        <Search size={18} className={styles.searchIcon} aria-hidden="true" />
        <label htmlFor="global-search" className={styles.srOnly}>
          Search interactions, agents, and metrics
        </label>
        <input 
          id="global-search"
          type="search" 
          placeholder="Search interactions, agents, metrics..." 
          className={styles.searchInput}
          aria-label="Search interactions, agents, and metrics"
        />
      </div>
      
      <div className={styles.actions}>
        <button 
          className={styles.iconButton}
          aria-label="Notifications (3 unread)"
          title="Notifications"
        >
          <Bell size={20} aria-hidden="true" />
          <span className={styles.notificationDot} aria-hidden="true" />
          <span className={styles.srOnly}>3 unread notifications</span>
        </button>
        
        <div className={styles.divider} role="separator" aria-orientation="vertical" />
        
        <button 
          className={styles.profile}
          aria-label="User profile menu"
          title="User profile"
        >
          <div className={styles.avatar} aria-hidden="true">
            <User size={18} />
          </div>
          <div className={styles.profileInfo}>
            <span className={styles.profileName}>Demo User</span>
            <span className={styles.profileRole}>Administrator</span>
          </div>
        </button>
      </div>
    </header>
  )
}
