from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CartItem, Order, OrderItem, User
from app.schemas import OrderItemOut, OrderOut

router = APIRouter()


def _serialize(order: Order) -> OrderOut:
    items = [
        OrderItemOut(
            product_id=item.product_id,
            product_name=item.product.name,
            quantity=item.quantity,
            unit_price=item.unit_price,
            line_total=item.unit_price * item.quantity,
        )
        for item in order.items
    ]
    return OrderOut(id=order.id, created_at=order.created_at, total=order.total, items=items)


@router.post("", response_model=OrderOut)
def submit_order(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == user.id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

    total = sum(item.product.price * item.quantity for item in cart_items)
    order = Order(user_id=user.id, total=total)
    db.add(order)
    db.flush()

    for item in cart_items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
        )
        db.delete(item)

    db.commit()
    db.refresh(order)
    return _serialize(order)


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return _serialize(order)
