from decimal import Decimal

from app.security import hash_password
from app.models import User


def test_cart_starts_empty(logged_in_client):
    response = logged_in_client.get("/api/cart")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert Decimal(body["total"]) == Decimal("0")


def test_add_item_to_cart(logged_in_client, test_products):
    product = test_products[0]
    response = logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 2})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2
    assert Decimal(body["total"]) == Decimal("7.00")


def test_adding_same_product_twice_increments_quantity(logged_in_client, test_products):
    product = test_products[0]
    logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 1})
    response = logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 2})
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 3


def test_add_unknown_product_returns_404(logged_in_client):
    response = logged_in_client.post("/api/cart/items", json={"product_id": 9999, "quantity": 1})
    assert response.status_code == 404


def test_remove_item_from_cart(logged_in_client, test_products):
    product = test_products[0]
    add_response = logged_in_client.post("/api/cart/items", json={"product_id": product.id, "quantity": 1})
    item_id = add_response.json()["items"][0]["id"]

    response = logged_in_client.delete(f"/api/cart/items/{item_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert Decimal(body["total"]) == Decimal("0")


def test_remove_unknown_item_returns_404(logged_in_client):
    response = logged_in_client.delete("/api/cart/items/9999")
    assert response.status_code == 404


def test_cart_endpoints_require_auth(client):
    assert client.get("/api/cart").status_code == 401
    assert client.post("/api/cart/items", json={"product_id": 1}).status_code == 401
    assert client.delete("/api/cart/items/1").status_code == 401


def test_cart_is_isolated_per_user(client, db_session, test_products):
    user_a = User(username="alice", password_hash=hash_password("pw12345"))
    user_b = User(username="bob", password_hash=hash_password("pw12345"))
    db_session.add_all([user_a, user_b])
    db_session.commit()

    client.post("/api/auth/login", json={"username": "alice", "password": "pw12345"})
    client.post("/api/cart/items", json={"product_id": test_products[0].id, "quantity": 1})
    client.post("/api/auth/logout")

    client.post("/api/auth/login", json={"username": "bob", "password": "pw12345"})
    response = client.get("/api/cart")
    body = response.json()
    assert body["items"] == []
    assert Decimal(body["total"]) == Decimal("0")
