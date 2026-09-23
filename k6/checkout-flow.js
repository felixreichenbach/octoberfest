import http from 'k6/http';
import { check, fail } from 'k6';

// Synthetic check for the Oktoberfest shop's core flow: login -> browse
// products -> add to cart -> submit purchase -> fetch confirmation -> logout.
//
// Runs as a single iteration by default (k6's default with no `options`),
// matching how a Synthetic Monitoring "Scripted" check executes it. Can also
// be run directly for local smoke testing:
//
//   k6 run k6/checkout-flow.js
//   k6 run -e BASE_URL=https://your-deployed-host k6/checkout-flow.js
//
// Note: each successful run places a real order against the target's database.

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const USERNAME = __ENV.SHOP_USERNAME || 'demo';
const PASSWORD = __ENV.SHOP_PASSWORD || 'demo123';

// Without this, k6 exits 0 even when a check fails — only threshold
// breaches affect the exit code.
export const options = {
  thresholds: {
    checks: ['rate==1.0'],
  },
};

export default function () {
  const login = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ username: USERNAME, password: PASSWORD }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  if (!check(login, { 'login succeeded': (r) => r.status === 200 })) {
    fail(`login failed: ${login.status} ${login.body}`);
  }

  const products = http.get(`${BASE_URL}/api/products`);
  if (
    !check(products, {
      'products loaded': (r) => r.status === 200,
      'at least one product': (r) => r.json().length > 0,
    })
  ) {
    fail(`products request failed: ${products.status} ${products.body}`);
  }
  const firstProduct = products.json()[0];

  const addToCart = http.post(
    `${BASE_URL}/api/cart/items`,
    JSON.stringify({ product_id: firstProduct.id, quantity: 1 }),
    { headers: { 'Content-Type': 'application/json' } }
  );
  if (
    !check(addToCart, {
      'item added to cart': (r) => r.status === 200,
      'cart is not empty': (r) => r.json('items').length > 0,
    })
  ) {
    fail(`add to cart failed: ${addToCart.status} ${addToCart.body}`);
  }

  const order = http.post(`${BASE_URL}/api/orders`);
  if (
    !check(order, {
      'purchase submitted': (r) => r.status === 200,
      'order has an id': (r) => r.json('id') > 0,
    })
  ) {
    fail(`order submission failed: ${order.status} ${order.body}`);
  }
  const orderId = order.json('id');

  const confirmation = http.get(`${BASE_URL}/api/orders/${orderId}`);
  check(confirmation, {
    'confirmation retrievable': (r) => r.status === 200,
  });

  http.post(`${BASE_URL}/api/auth/logout`);
}
