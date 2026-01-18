/**
 * Login Page
 * 
 * Modern, professional authentication page for the AI Call Center.
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      const result = await login({ email, password })
      
      if (result.success && result.data) {
        localStorage.setItem('access_token', result.data.accessToken)
        localStorage.setItem('refresh_token', result.data.refreshToken)
        setAuthToken(result.data.accessToken)
        navigate('/')
      } else {
        setError(result.error?.message || 'Invalid credentials')
      }
    } catch {
      setError('Connection failed. Please try again.')
    }
    
    setIsLoading(false)
  }

  const handleDemoLogin = () => {
    setEmail('demo@example.com')
    setPassword('demo123')
  }

  return (
    <div className={styles.page}>
      {/* Left side - Branding */}
      <div className={styles.branding}>
        <div className={styles.brandingContent}>
          <div className={styles.logoMark}>
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect width="48" height="48" rx="12" fill="url(#gradient)" />
              <path d="M24 12L34 20V28L24 36L14 28V20L24 12Z" stroke="white" strokeWidth="2" fill="none" />
              <circle cx="24" cy="24" r="4" fill="white" />
              <defs>
                <linearGradient id="gradient" x1="0" y1="0" x2="48" y2="48">
                  <stop stopColor="#6366f1" />
                  <stop offset="1" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          
          <h1 className={styles.brandTitle}>AI Call Center</h1>
          <p className={styles.brandTagline}>Autonomous Agent Platform</p>
          
          <div className={styles.features}>
            <div className={styles.feature}>
              <span className={styles.featureIcon}>🎯</span>
              <div>
                <h3>Intelligent Routing</h3>
                <p>AI-powered call handling with real-time intent detection</p>
              </div>
            </div>
            <div className={styles.feature}>
              <span className={styles.featureIcon}>🤖</span>
              <div>
                <h3>Autonomous Agents</h3>
                <p>Three-tier agent system for quality assurance</p>
              </div>
            </div>
            <div className={styles.feature}>
              <span className={styles.featureIcon}>📊</span>
              <div>
                <h3>Real-time Analytics</h3>
                <p>Track performance, confidence, and resolution rates</p>
              </div>
            </div>
          </div>
        </div>
        
        <div className={styles.brandingFooter}>
          <p>Enterprise-grade AI for customer service</p>
        </div>
      </div>

      {/* Right side - Login Form */}
      <div className={styles.formSide}>
        <div className={styles.formContainer}>
          <div className={styles.formHeader}>
            <h2>Welcome back</h2>
            <p>Sign in to access your dashboard</p>
          </div>

          {error && (
            <div className={styles.error}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.field}>
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className={styles.field}>
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isLoading}
            >
              {isLoading ? (
                <span className={styles.spinner} />
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <div className={styles.divider}>
            <span>Demo Access</span>
          </div>

          <button
            type="button"
            className={styles.demoBtn}
            onClick={handleDemoLogin}
          >
            Fill Demo Credentials
          </button>
          
          <p className={styles.demoNote}>
            Use <strong>demo@example.com</strong> with password <strong>demo123</strong>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
