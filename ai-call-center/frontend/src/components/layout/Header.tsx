import { Bell, Search, User } from 'lucide-react'
import styles from './Header.module.css'

export function Header() {
  return (
    <header className={styles.header}>
      <div className={styles.search}>
        <Search size={18} className={styles.searchIcon} />
        <input 
          type="text" 
          placeholder="Search interactions, agents, metrics..." 
          className={styles.searchInput}
        />
      </div>
      
      <div className={styles.actions}>
        <button className={styles.iconButton}>
          <Bell size={20} />
          <span className={styles.notificationDot} />
        </button>
        
        <div className={styles.divider} />
        
        <button className={styles.profile}>
          <div className={styles.avatar}>
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
