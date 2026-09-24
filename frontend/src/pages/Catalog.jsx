import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import LogoutButton from '../LogoutButton.jsx'

export default function Catalog() {
  const [products, setProducts] = useState([])
  const [error, setError] = useState('')
  const [addedId, setAddedId] = useState(null)

  useEffect(() => {
    api.listProducts().then(setProducts).catch(() => setError('Could not load products.'))
  }, [])

  const handleAdd = async (productId) => {
    try {
      await api.addToCart(productId)
      setAddedId(productId)
      setTimeout(() => setAddedId(null), 1200)
    } catch {
      setError('Could not add item to cart.')
    }
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1>Products</h1>
        <div className="header-actions">
          <Link to="/cart" className="button-link">
            View cart
          </Link>
          <LogoutButton />
        </div>
      </header>
      {error && <p className="error">{error}</p>}
      <div className="grid">
        {products.map((product) => (
          <div className="card" key={product.id}>
            <h2>{product.name}</h2>
            <p>{product.description}</p>
            <p className="price">€{product.price}</p>
            <button onClick={() => handleAdd(product.id)}>
              {addedId === product.id ? 'Added!' : 'Add to cart'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
