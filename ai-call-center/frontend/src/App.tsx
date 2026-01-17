import { Routes, Route } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { DashboardPage } from './components/dashboard/DashboardPage'
import { ChatDemoPage } from './components/chat/ChatDemoPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="demo" element={<ChatDemoPage />} />
      </Route>
    </Routes>
  )
}

export default App
