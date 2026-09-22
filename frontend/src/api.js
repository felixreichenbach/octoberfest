const BASE_URL = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const error = new Error(`Request to ${path} failed with ${response.status}`)
    error.status = response.status
    throw error
  }

  if (response.status === 204) return null
  return response.json()
}

export const api = {
  login: (username, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
  listProducts: () => request('/products'),
  getCart: () => request('/cart'),
  addToCart: (productId) =>
    request('/cart/items', { method: 'POST', body: JSON.stringify({ product_id: productId }) }),
  removeFromCart: (itemId) => request(`/cart/items/${itemId}`, { method: 'DELETE' }),
  submitOrder: () => request('/orders', { method: 'POST' }),
  getOrder: (orderId) => request(`/orders/${orderId}`),
}
