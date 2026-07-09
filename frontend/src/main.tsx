import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { getToken } from './api'
import Login from './pages/Login'
import Chat from './pages/Chat'
import Reports from './pages/Reports'
import ReviewConsole from './pages/ReviewConsole'
import Knowledge from './pages/Knowledge'
import './styles.css'

function RequireAuth({ children }: { children: React.ReactNode }) {
  return getToken() ? <>{children}</> : <Navigate to="/login" replace />
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Chat /></RequireAuth>} />
        <Route path="/reports" element={<RequireAuth><Reports /></RequireAuth>} />
        <Route path="/review" element={<RequireAuth><ReviewConsole /></RequireAuth>} />
        <Route path="/knowledge" element={<RequireAuth><Knowledge /></RequireAuth>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
