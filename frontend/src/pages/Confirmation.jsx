import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useAuth } from '../AuthContext.jsx'

export default function Confirmation() {
  const { orderId } = useParams()
  const [order, setOrder] = useState(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const { refresh } = useAuth()

  useEffect(() => {
    api.getOrder(orderId).then(setOrder).catch(() => setError('Could not load order details.'))
  }, [orderId])

  const handleContinue = async () => {
    const current = await refresh()
    navigate(current ? '/catalog' : '/login')
  }

  if (error) {
    return (
      <div className="page page-narrow">
        <p className="error">{error}</p>
        <button className="primary" onClick={handleContinue}>
          Continue
        </button>
      </div>
    )
  }

  if (!order) return <p className="status">Loading...</p>

  return (
    <div className="page page-narrow">
      <h1>Order confirmed</h1>
      <div className="card">
        <p>Order #{order.id}</p>
        <ul>
          {order.items.map((item) => (
            <li key={item.product_id}>
              {item.quantity} × {item.product_name} — €{item.line_total}
            </li>
          ))}
        </ul>
        <p className="total">Total: €{order.total}</p>
      </div>
      <button className="primary" onClick={handleContinue}>
        Back to products
      </button>
    </div>
  )
}
