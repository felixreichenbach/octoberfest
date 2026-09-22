import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api.js'

export default function Cart() {
  const [cart, setCart] = useState({ items: [], total: 0 })
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const loadCart = () => api.getCart().then(setCart).catch(() => setError('Could not load cart.'))

  useEffect(() => {
    loadCart()
  }, [])

  const handleRemove = async (itemId) => {
    try {
      await api.removeFromCart(itemId)
      loadCart()
    } catch {
      setError('Could not remove item.')
    }
  }

  const handleSubmit = async () => {
    try {
      const order = await api.submitOrder()
      navigate(`/confirmation/${order.id}`)
    } catch {
      setError('Could not submit purchase. Is your cart empty?')
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>Your cart</h1>
        <Link to="/catalog" className="button-link">
          ← Back to products
        </Link>
      </header>
      {error && <p className="error">{error}</p>}
      {cart.items.length === 0 ? (
        <p className="status">Your cart is empty.</p>
      ) : (
        <>
          <table className="cart-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Qty</th>
                <th>Unit price</th>
                <th>Line total</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cart.items.map((item) => (
                <tr key={item.id}>
                  <td>{item.product.name}</td>
                  <td>{item.quantity}</td>
                  <td>€{item.product.price}</td>
                  <td>€{item.line_total}</td>
                  <td>
                    <button onClick={() => handleRemove(item.id)}>Remove</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="total">Total: €{cart.total}</p>
          <button className="primary" onClick={handleSubmit}>
            Submit purchase
          </button>
        </>
      )}
    </div>
  )
}
