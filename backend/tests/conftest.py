import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Product, User  # noqa: E402
from app.security import hash_password  # noqa: E402

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user(db_session):
    user = User(username="tester", password_hash=hash_password("secret123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_products(db_session):
    products = [
        Product(name="Brezel", description="Classic Bavarian pretzel", price="3.50"),
        Product(name="Lebkuchenherz", description="Decorated gingerbread heart", price="8.00"),
    ]
    db_session.add_all(products)
    db_session.commit()
    for product in products:
        db_session.refresh(product)
    return products


@pytest.fixture
def logged_in_client(client, test_user):
    response = client.post("/api/auth/login", json={"username": "tester", "password": "secret123"})
    assert response.status_code == 200
    return client
