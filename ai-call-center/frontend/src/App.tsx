import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { CallSimulator } from './components/chat/CallSimulator'
import { InteractionsPage } from './components/interactions/InteractionsPage'
import { InteractionDetailPage } from './components/interactions/InteractionDetailPage'
import { AgentsPage } from './components/agents/AgentsPage'
import { AnalyticsPage } from './components/analytics/AnalyticsPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="demo" element={<CallSimulator />} />
        <Route path="interactions" element={<InteractionsPage />} />
        <Route path="interactions/:interactionId" element={<InteractionDetailPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
      </Route>
    </Routes>
  )
}

export default App
