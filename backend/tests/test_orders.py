from decimal import Decimal

from app.models import Product, User
from app.security import hash_password


def test_submit_order_requires_nonempty_cart(logged_in_client):
    response = logged_in_client.post("/api/orders")
    assert response.status_code == 400


def test_submit_order_success_and_clears_cart(logged_in_client, test_products):
    product = test_products[0]
    logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 2})

    response = logged_in_client.post("/api/orders")
    assert response.status_code == 200
    order = response.json()
    assert Decimal(order["total"]) == Decimal("7.00")
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 2

    cart = logged_in_client.get("/api/cart").json()
    assert cart["items"] == []
    assert Decimal(cart["total"]) == Decimal("0")


def test_submit_order_uses_current_price_at_checkout(logged_in_client, test_products, db_session):
    """Changing a product's price after it's in the cart but before checkout should be
    reflected on the order — the order records the price at purchase time, not at
    add-to-cart time."""
    product = test_products[0]
    logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 1})

    db_product = db_session.get(Product, product.id)
    db_product.price = "99.00"
    db_session.commit()

    order = logged_in_client.post("/api/orders").json()
    assert Decimal(order["items"][0]["unit_price"]) == Decimal("99.00")


def test_order_unit_price_is_frozen_after_checkout(logged_in_client, test_products, db_session):
    """Once an order is placed, later price changes must not retroactively change it."""
    product = test_products[0]
    logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 1})
    order = logged_in_client.post("/api/orders").json()

    db_product = db_session.get(Product, product.id)
    db_product.price = "99.00"
    db_session.commit()

    refetched = logged_in_client.get(f"/api/orders/{order['id']}").json()
    assert Decimal(refetched["items"][0]["unit_price"]) == Decimal("3.50")


def test_get_order_returns_own_order(logged_in_client, test_products):
    logged_in_client.post("/api/cart/items", json={"product_id": test_products[0].id, "quantity": 1})
    order = logged_in_client.post("/api/orders").json()

    response = logged_in_client.get(f"/api/orders/{order['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == order["id"]


def test_get_unknown_order_returns_404(logged_in_client):
    response = logged_in_client.get("/api/orders/9999")
    assert response.status_code == 404


def test_get_order_belonging_to_another_user_is_not_found(client, db_session, test_products):
    user_a = User(username="alice", password_hash=hash_password("pw12345"))
    user_b = User(username="bob", password_hash=hash_password("pw12345"))
    db_session.add_all([user_a, user_b])
    db_session.commit()

    client.post("/api/auth/login", json={"username": "alice", "password": "pw12345"})
    client.post("/api/cart/items", json={"product_id": test_products[0].id, "quantity": 1})
    order = client.post("/api/orders").json()
    client.post("/api/auth/logout")

    client.post("/api/auth/login", json={"username": "bob", "password": "pw12345"})
    response = client.get(f"/api/orders/{order['id']}")
    assert response.status_code == 404


def test_order_endpoints_require_auth(client):
    assert client.post("/api/orders").status_code == 401
    assert client.get("/api/orders/1").status_code == 401
