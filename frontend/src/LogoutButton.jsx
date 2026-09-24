import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext.jsx'

export default function LogoutButton() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return <button onClick={handleLogout}>Log out</button>
}
