from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Product
from app.schemas import ProductOut

router = APIRouter()


@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), _user=Depends(get_current_user)):
    return db.query(Product).filter(Product.active.is_(True)).order_by(Product.name).all()
