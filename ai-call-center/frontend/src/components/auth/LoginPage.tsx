/**
 * Login Page
 * 
 * Authentication page for the AI Call Center.
 * Supports email/password login with demo credentials.
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, setAuthToken } from '../../services/apiClient'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showPassword, setShowPassword] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const result = await login({ email, password })
      
      if (result.success && result.data) {
        // Store tokens
        localStorage.setItem('access_token', result.data.accessToken)
        localStorage.setItem('refresh_token', result.data.refreshToken)
        
        // Set auth header for future requests
        setAuthToken(result.data.accessToken)
        
        // Redirect to dashboard
        navigate('/')
      } else {
        setError(result.error?.message || 'Login failed. Please check your credentials.')
      }
    } catch {
      setError('An unexpected error occurred. Please try again.')
    }
    
    setIsLoading(false)
  }

  const handleDemoLogin = () => {
    setEmail('demo@example.com')
    setPassword('demo123')
  }

  return (
    <div className={styles.container}>
      <div className={styles.loginCard}>
        {/* Logo */}
        <div className={styles.logo}>
          <div className={styles.logoIcon}>⚡</div>
          <h1 className={styles.logoTitle}>AI Call Center</h1>
          <p className={styles.logoSubtitle}>Autonomous Agent Platform</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className={styles.form}>
          <h2 className={styles.formTitle}>Sign In</h2>
          
          {error && (
            <div className={styles.error}>
              <span>⚠️</span> {error}
            </div>
          )}

          <div className={styles.inputGroup}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="password">Password</label>
            <div className={styles.passwordInput}>
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                className={styles.showPassword}
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
              >
                {showPassword ? '👁️' : '👁️‍🗨️'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo Credentials */}
        <div className={styles.demoSection}>
          <div className={styles.divider}>
            <span>or try the demo</span>
          </div>
          
          <button
            type="button"
            className={styles.demoButton}
            onClick={handleDemoLogin}
          >
            🎮 Use Demo Credentials
          </button>
          
          <p className={styles.demoHint}>
            Demo: <code>demo@example.com</code> / <code>demo123</code>
          </p>
        </div>

        {/* Footer */}
        <div className={styles.footer}>
          <p>Powered by Autonomous AI Agents</p>
        </div>
      </div>

      {/* Background decoration */}
      <div className={styles.bgDecoration}>
        <div className={styles.bgCircle1} />
        <div className={styles.bgCircle2} />
        <div className={styles.bgCircle3} />
      </div>
    </div>
  )
}

export default LoginPage
