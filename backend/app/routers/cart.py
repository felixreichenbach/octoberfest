from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CartItem, Product, User
from app.schemas import AddCartItemRequest, CartItemOut, CartOut

router = APIRouter()


def _serialize(cart_items: list[CartItem]) -> CartOut:
    items = [
        CartItemOut(
            id=item.id,
            product=item.product,
            quantity=item.quantity,
            line_total=item.product.price * item.quantity,
        )
        for item in cart_items
    ]
    total = sum((item.line_total for item in items), start=0)
    return CartOut(items=items, total=total)


@router.get("", response_model=CartOut)
def get_cart(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    return _serialize(cart_items)


@router.post("/items", response_model=CartOut)
def add_item(
    payload: AddCartItemRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    product = db.get(Product, payload.product_id)
    if product is None or not product.active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    cart_item = (
        db.query(CartItem)
        .filter(CartItem.user_id == user.id, CartItem.product_id == product.id)
        .first()
    )
    if cart_item is None:
        cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=payload.quantity)
        db.add(cart_item)
    else:
        cart_item.quantity += payload.quantity

    db.commit()

    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    return _serialize(cart_items)


@router.delete("/items/{item_id}", response_model=CartOut)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cart_item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == user.id)
        .first()
    )
    if cart_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

    db.delete(cart_item)
    db.commit()

    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    return _serialize(cart_items)
