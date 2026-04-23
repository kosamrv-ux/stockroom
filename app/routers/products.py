from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas, services
from ..database import get_db
from ..dependencies import require_api_key

router = APIRouter(prefix="/products", tags=["products"])


def _get_or_404(db: Session, product_id: int) -> models.Product:
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


@router.get("", response_model=list[schemas.ProductWithStock])
def list_products(
    db: Session = Depends(get_db),
    category_id: int | None = Query(default=None),
    search: str | None = Query(default=None, description="Match against SKU or name"),
):
    stmt = select(models.Product)
    if category_id is not None:
        stmt = stmt.where(models.Product.category_id == category_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(models.Product.sku.ilike(like) | models.Product.name.ilike(like))

    products = db.execute(stmt.order_by(models.Product.name)).scalars().all()
    return [
        schemas.ProductWithStock(
            **schemas.ProductRead.model_validate(p).model_dump(),
            on_hand=services.on_hand(db, p.id),
        )
        for p in products
    ]


@router.get("/low-stock", response_model=list[schemas.ProductWithStock])
def low_stock(db: Session = Depends(get_db)):
    return [
        schemas.ProductWithStock(
            **schemas.ProductRead.model_validate(p).model_dump(), on_hand=qty
        )
        for p, qty in services.low_stock(db)
    ]


@router.get("/{product_id}", response_model=schemas.ProductWithStock)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_or_404(db, product_id)
    return schemas.ProductWithStock(
        **schemas.ProductRead.model_validate(product).model_dump(),
        on_hand=services.on_hand(db, product.id),
    )


@router.post(
    "",
    response_model=schemas.ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**payload.model_dump())
    db.add(product)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists") from exc
    db.refresh(product)
    return product


@router.patch(
    "/{product_id}",
    response_model=schemas.ProductRead,
    dependencies=[Depends(require_api_key)],
)
def update_product(
    product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    product = _get_or_404(db, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_or_404(db, product_id)
    db.delete(product)
    db.commit()
