from app.models import Product


def test_list_products_requires_auth(client):
    response = client.get("/api/products")
    assert response.status_code == 401


def test_list_products_returns_only_active_products(logged_in_client, test_products, db_session):
    inactive = Product(name="Aardvark Snack", description="discontinued", price="1.00", active=False)
    db_session.add(inactive)
    db_session.commit()

    response = logged_in_client.get("/api/products")
    assert response.status_code == 200

    names = [p["name"] for p in response.json()]
    assert "Aardvark Snack" not in names
    assert set(names) == {"Brezel", "Lebkuchenherz"}


def test_list_products_is_sorted_by_name(logged_in_client, test_products):
    response = logged_in_client.get("/api/products")
    names = [p["name"] for p in response.json()]
    assert names == sorted(names)
