/**
 * Authentication Context
 * 
 * Provides authentication state and methods across the app.
 * Handles token storage, refresh, and protected routes.
 */

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { 
  getCurrentUser, 
  setAuthToken, 
  clearAuthToken, 
  refreshToken as refreshTokenApi,
  UserInfo 
} from '../services/apiClient'

interface AuthContextType {
  user: UserInfo | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (accessToken: string, refreshToken: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  const clearAuth = useCallback(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    clearAuthToken()
    setUser(null)
  }, [])

  // Login function - stores tokens and fetches user
  const login = useCallback(async (accessToken: string, refreshToken: string) => {
    try {
      // Store tokens
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
      setAuthToken(accessToken)
      
      // Get user info
      const result = await getCurrentUser()
      if (result.success && result.data) {
        setUser(result.data)
      } else {
        // If we can't get user info, clear everything
        console.error('Failed to get user after login:', result.error)
        clearAuth()
      }
    } catch (err) {
      console.error('Login error:', err)
      clearAuth()
    }
  }, [clearAuth])

  const logout = useCallback(() => {
    clearAuth()
    navigate('/login', { replace: true })
  }, [clearAuth, navigate])

  // Check for existing token on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token')
      
      if (!token) {
        setIsLoading(false)
        return
      }

      setAuthToken(token)
      
      // Verify token is still valid
      const result = await getCurrentUser()
      
      if (result.success && result.data) {
        setUser(result.data)
        setIsLoading(false)
        return
      }

      // Token invalid, try to refresh
      const refreshTokenStr = localStorage.getItem('refresh_token')
      if (!refreshTokenStr) {
        clearAuth()
        setIsLoading(false)
        return
      }

      const refreshResult = await refreshTokenApi(refreshTokenStr)
      if (refreshResult.success && refreshResult.data) {
        localStorage.setItem('access_token', refreshResult.data.accessToken)
        localStorage.setItem('refresh_token', refreshResult.data.refreshToken)
        setAuthToken(refreshResult.data.accessToken)
        
        // Try getting user again
        const userResult = await getCurrentUser()
        if (userResult.success && userResult.data) {
          setUser(userResult.data)
        } else {
          clearAuth()
        }
      } else {
        clearAuth()
      }
      
      setIsLoading(false)
    }

    initAuth()
  }, [clearAuth])

  // Redirect to login if not authenticated and not on login page
  useEffect(() => {
    if (!isLoading && !user && location.pathname !== '/login') {
      navigate('/login', { replace: true })
    }
  }, [isLoading, user, location.pathname, navigate])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export default AuthContext
