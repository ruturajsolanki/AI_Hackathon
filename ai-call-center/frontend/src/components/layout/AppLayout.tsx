import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import styles from './AppLayout.module.css'

export function AppLayout() {
  return (
    <div className={styles.layout}>
      {/* Skip link for keyboard navigation */}
      <a href="#main-content" className={styles.skipLink}>
        Skip to main content
      </a>
      
      <Sidebar />
      
      <div className={styles.main}>
        <Header />
        <main 
          id="main-content" 
          className={styles.content}
          role="main"
          aria-label="Main content"
          tabIndex={-1}
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
