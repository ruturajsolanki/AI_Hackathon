import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { CallSimulator } from './components/chat/CallSimulator'
import { InteractionsPage } from './components/interactions/InteractionsPage'
import { InteractionDetailPage } from './components/interactions/InteractionDetailPage'
import { AgentsPage } from './components/agents/AgentsPage'
import { AgentProgrammingPage } from './components/agent-programming/AgentProgrammingPage'
import { AnalyticsPage } from './components/analytics/AnalyticsPage'
import { SettingsPage } from './components/settings/SettingsPage'
import { TicketsDashboard } from './components/tickets/TicketsDashboard'
import { LiveSession } from './components/session/LiveSession'
import { CustomerSession } from './components/session/CustomerSession'
import { LoginPage } from './components/auth/LoginPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()
  
  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100vh',
        background: 'var(--color-bg-primary)',
        color: 'var(--color-text-primary)'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⚡</div>
          <p>Loading...</p>
        </div>
      </div>
    )
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/customer-session/:sessionId" element={<CustomerSession />} />
      
      {/* Protected routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <AppLayout />
        </ProtectedRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="demo" element={<CallSimulator />} />
        <Route path="interactions" element={<InteractionsPage />} />
        <Route path="interactions/:interactionId" element={<InteractionDetailPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="agent-programming" element={<AgentProgrammingPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="tickets" element={<TicketsDashboard />} />
        <Route path="session/:sessionId" element={<LiveSession />} />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App
