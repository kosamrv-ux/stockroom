from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas, services
from ..database import get_db
from ..dependencies import require_api_key

router = APIRouter(prefix="/products/{product_id}/movements", tags=["stock"])


def _get_or_404(db: Session, product_id: int) -> models.Product:
    product = db.get(models.Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


@router.get("", response_model=list[schemas.MovementRead])
def list_movements(product_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, product_id)
    stmt = (
        select(models.StockMovement)
        .where(models.StockMovement.product_id == product_id)
        .order_by(models.StockMovement.created_at.desc(), models.StockMovement.id.desc())
    )
    return db.execute(stmt).scalars().all()


@router.post(
    "",
    response_model=schemas.MovementRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def create_movement(
    product_id: int, payload: schemas.MovementCreate, db: Session = Depends(get_db)
):
    product = _get_or_404(db, product_id)
    try:
        return services.record_movement(db, product, payload)
    except services.StockError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
