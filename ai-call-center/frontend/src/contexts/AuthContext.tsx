/**
 * Authentication Context
 * 
 * Provides authentication state and methods across the app.
 * Handles token storage, refresh, and protected routes.
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
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
  login: (accessToken: string, refreshToken: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  // Check for existing token on mount
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token')
      
      if (token) {
        setAuthToken(token)
        
        // Verify token is still valid
        const result = await getCurrentUser()
        
        if (result.success && result.data) {
          setUser(result.data)
        } else {
          // Try to refresh token
          const refreshTokenStr = localStorage.getItem('refresh_token')
          if (refreshTokenStr) {
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
                // Token refresh failed, clear auth
                clearAuth()
              }
            } else {
              clearAuth()
            }
          } else {
            clearAuth()
          }
        }
      }
      
      setIsLoading(false)
    }

    initAuth()
  }, [])

  // Redirect to login if not authenticated and not on login page
  useEffect(() => {
    if (!isLoading && !user && location.pathname !== '/login') {
      navigate('/login', { replace: true })
    }
  }, [isLoading, user, location.pathname, navigate])

  const clearAuth = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    clearAuthToken()
    setUser(null)
  }

  const login = async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    setAuthToken(accessToken)
    
    // Get user info
    const result = await getCurrentUser()
    if (result.success && result.data) {
      setUser(result.data)
    }
  }

  const logout = () => {
    clearAuth()
    navigate('/login', { replace: true })
  }

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
