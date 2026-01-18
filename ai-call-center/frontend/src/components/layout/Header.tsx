import { useState } from 'react'
import { Bell, Search, User, LogOut, ChevronDown } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import styles from './Header.module.css'

export function Header() {
  const { user, logout } = useAuth()
  const [showDropdown, setShowDropdown] = useState(false)

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
        
        <div className={styles.profileWrapper}>
          <button 
            className={styles.profile}
            aria-label="User profile menu"
            title="User profile"
            onClick={() => setShowDropdown(!showDropdown)}
          >
            <div className={styles.avatar} aria-hidden="true">
              <User size={18} />
            </div>
            <div className={styles.profileInfo}>
              <span className={styles.profileName}>{user?.fullName || 'User'}</span>
              <span className={styles.profileRole}>{user?.role === 'admin' ? 'Administrator' : 'User'}</span>
            </div>
            <ChevronDown size={16} className={styles.chevron} />
          </button>
          
          {showDropdown && (
            <div className={styles.dropdown}>
              <div className={styles.dropdownHeader}>
                <span className={styles.dropdownEmail}>{user?.email}</span>
              </div>
              <button className={styles.dropdownItem} onClick={logout}>
                <LogOut size={16} />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
