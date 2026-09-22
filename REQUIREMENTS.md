# Oktoberfest Shop — Requirements Document

## 1. Overview

A simple online shop for Oktoberfest booth items (Bretzels, sweets, and similar basic goods). The application is built as a 3-tier system — web frontend, backend API, and database — with each tier running as its own Docker container. No payment processing is included; purchases are recorded directly.

Guiding principle: **keep it simple**. Favor a small, well-understood feature set and a clean separation between tiers so that features (payment, order history, admin panel, etc.) can be added later without a rewrite.

## 2. Architecture

### 2.1 Tiers

| Tier | Responsibility |
|---|---|
| Frontend | Renders pages, calls backend API, holds no business logic or direct DB access |
| Backend | REST API, authentication/session handling, business logic, DB access |
| Database | Persists users, products, cart, and order data |

### 2.2 Containers

- `frontend` — serves the web UI
- `backend` — serves the API
- `db` — PostgreSQL instance

All three run as separate Docker containers (e.g. via `docker-compose`), each with its own image and independently restartable. Frontend and backend communicate over HTTP within the Docker network; only the frontend (and optionally the backend, for debugging) is exposed to the host.

### 2.3 Stack

- Frontend: React or a lightweight server-rendered framework
- Backend: Python with FastAPI
- Database: PostgreSQL

## 3. Functional Requirements

### 3.1 Authentication

- A **login page** where a user enters username/email and password.
- Credentials are checked against user records stored in the database (backend validates, never the frontend).
- Passwords are stored hashed (e.g. bcrypt), never in plain text.
- On success, a session is established (e.g. session cookie or JWT) so the backend can identify the logged-in user on subsequent requests.
- No self-service registration is required for v1 — users can be seeded directly in the database. (Explicit non-goal, revisit later if needed.)
- Sessions expire after a period of inactivity; an expired session is treated the same as "not logged in" (see 3.5).

### 3.2 Product Catalog Page

- Displays all available products (e.g. name, description, price, maybe an image).
- Each product has an **"Add to cart"** button.
- Adding a product adds it to the current user's shopping cart (or increments quantity if already present).
- Accessible only to logged-in users; an unauthenticated visit redirects to the login page.

### 3.3 Shopping Cart Page

- Lists all items currently in the logged-in user's cart: product name, quantity, unit price, line total.
- Each line item has a **"Remove"** button that removes that item from the cart.
- A **"Submit purchase"** button finalizes the order:
  - Creates an order record (and associated order line items) in the database.
  - Clears the cart.
  - No payment step — submitting is equivalent to placing/confirming the order.

### 3.4 Order Confirmation Page

- Shown immediately after a successful purchase submission.
- Displays a simple confirmation (e.g. order number, items purchased, total).
- Contains one button:
  - If the session is still valid → returns to the **Product Catalog** page.
  - If the session has expired → returns to the **Login** page.

### 3.5 Session Handling (cross-cutting)

- Any page/action requiring authentication checks session validity server-side before proceeding.
- On an expired/invalid session, the user is redirected to the login page instead of being shown protected content or allowed to submit actions.

## 4. Data Model (initial, minimal)

- **User**: id, username/email, password_hash, created_at
- **Product**: id, name, description, price, (optional) image_url, active flag
- **CartItem**: id, user_id, product_id, quantity
- **Order**: id, user_id, created_at, total
- **OrderItem**: id, order_id, product_id, quantity, unit_price (price captured at purchase time)

Kept intentionally normalized and small so it's easy to extend (e.g. adding order status, stock levels, categories later).

## 5. Non-Functional Requirements

- **Simplicity**: minimal features, minimal dependencies, straightforward code — this is a foundation to build on, not a finished product.
- **Extensibility**: clear separation of concerns (frontend/backend/DB) so new features (payments, registration, order history, inventory, admin tools) can be added without restructuring the tiers.
- **Containerization**: each tier runs and can be rebuilt/redeployed independently via Docker; a single `docker-compose.yml` should bring up the full stack for local development.
- **Security basics**: hashed passwords, server-side session/authorization checks, no secrets committed to the repo (use environment variables / `.env` for DB credentials, session secret, etc.).

## 6. Explicit Non-Goals (v1)

- Payment processing / payment gateway integration
- User self-registration or password reset flows
- Order history page
- Inventory/stock tracking
- Admin/management UI for products
- Multi-language / multi-currency support

These are natural candidates for later iterations given the extensible architecture, but are out of scope for the initial build.

## 7. Page Flow Summary

```
Login page
   │  (successful login)
   ▼
Product Catalog page ──(add to cart)──► (stays on Catalog, cart updated)
   │
   │ (navigate to cart)
   ▼
Shopping Cart page ──(remove item)──► (stays on Cart, item removed)
   │
   │ (submit purchase)
   ▼
Order Confirmation page
   │
   ├─ session valid   ──► back to Product Catalog page
   └─ session expired ──► back to Login page
```
