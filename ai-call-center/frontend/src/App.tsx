import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { CallSimulator } from './components/chat/CallSimulator'
import { InteractionsPage } from './components/interactions/InteractionsPage'
import { InteractionDetailPage } from './components/interactions/InteractionDetailPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="demo" element={<CallSimulator />} />
        <Route path="interactions" element={<InteractionsPage />} />
        <Route path="interactions/:interactionId" element={<InteractionDetailPage />} />
      </Route>
    </Routes>
  )
}

export default App
