import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext.jsx'

export default function Login() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  if (user) return <Navigate to="/catalog" replace />

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await login(username, password)
      navigate('/catalog')
    } catch {
      setError('Invalid username or password.')
    }
  }

  return (
    <div className="page page-narrow">
      <h1>Oktoberfest Shop</h1>
      <form className="card" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Log in</button>
      </form>
    </div>
  )
}
