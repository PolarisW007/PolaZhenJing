/**
 * =============================================================================
 * Module: App.tsx
 * Description: Root application component with routing and protected routes.
 *              根应用组件 - 包含路由配置和受保护路由。
 * Created: 2026-04-06
 * Author: PolaZhenjing Team
 * Dependencies: react-router-dom, stores/authStore
 * =============================================================================
 */

import { useEffect } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import useAuthStore from './stores/authStore'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ThoughtEditor from './pages/ThoughtEditor'
import Settings from './pages/Settings'
import DeepResearch from './pages/DeepResearch'

/**
 * ProtectedRoute wrapper – redirects to /login if not authenticated.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default function App() {
  const { fetchUser } = useAuthStore()

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/thought/new"
          element={
            <ProtectedRoute>
              <ThoughtEditor />
            </ProtectedRoute>
          }
        />
        <Route
          path="/thought/:id"
          element={
            <ProtectedRoute>
              <ThoughtEditor />
            </ProtectedRoute>
          }
        />
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <Settings />
            </ProtectedRoute>
          }
        />
        <Route
          path="/research/new"
          element={
            <ProtectedRoute>
              <DeepResearch />
            </ProtectedRoute>
          }
        />
        <Route
          path="/research/:id"
          element={
            <ProtectedRoute>
              <DeepResearch />
            </ProtectedRoute>
          }
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
