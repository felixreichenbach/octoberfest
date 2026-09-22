from app.database import SessionLocal
from app.models import Product, User
from app.security import hash_password

DEMO_USER = {"username": "demo", "password": "demo123"}

PRODUCTS = [
    {"name": "Brezel", "description": "Classic Bavarian pretzel", "price": "3.50"},
    {"name": "Gebrannte Mandeln", "description": "Roasted sugared almonds, 100g cup", "price": "5.00"},
    {"name": "Lebkuchenherz", "description": "Decorated gingerbread heart", "price": "8.00"},
    {"name": "Zuckerwatte", "description": "Cotton candy on a stick", "price": "4.00"},
    {"name": "Schokofruechte", "description": "Chocolate-covered fruit skewer", "price": "4.50"},
    {"name": "Mandelhoernchen", "description": "Almond croissant pastry", "price": "3.00"},
    {"name": "Weisswurst", "description": "Bavarian white sausage, pair", "price": "6.50"},
    {"name": "Currywurst", "description": "Sausage with curry ketchup and fries", "price": "7.50"},
]


def seed_data() -> None:
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(username=DEMO_USER["username"], password_hash=hash_password(DEMO_USER["password"])))

        if db.query(Product).count() == 0:
            db.add_all(Product(**item) for item in PRODUCTS)

        db.commit()
    finally:
        db.close()
