import { useEffect } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { faro } from './faro.js'
import { AuthProvider, useAuth } from './AuthContext.jsx'
import Login from './pages/Login.jsx'
import Catalog from './pages/Catalog.jsx'
import Cart from './pages/Cart.jsx'
import Confirmation from './pages/Confirmation.jsx'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) return <p className="status">Loading...</p>
  if (!user) return <Navigate to="/login" replace />
  return children
}

// Report each client-side navigation to Faro as a view, using the route pattern
// (e.g. /confirmation/:orderId) so order IDs don't fragment the page list.
function usePageViews() {
  const { pathname } = useLocation()
  useEffect(() => {
    if (!faro) return
    const name = pathname.replace(/^\/confirmation\/[^/]+/, '/confirmation/:orderId')
    faro.api.setView({ name })
  }, [pathname])
}

function AppRoutes() {
  usePageViews()
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/catalog"
        element={
          <ProtectedRoute>
            <Catalog />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cart"
        element={
          <ProtectedRoute>
            <Cart />
          </ProtectedRoute>
        }
      />
      <Route
        path="/confirmation/:orderId"
        element={
          <ProtectedRoute>
            <Confirmation />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/catalog" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
