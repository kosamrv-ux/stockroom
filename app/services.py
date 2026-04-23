"""Business logic for inventory, kept separate from the HTTP layer."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import models, schemas


class StockError(Exception):
    """Raised when a stock operation is not allowed (e.g. negative on-hand)."""


def on_hand(db: Session, product_id: int) -> int:
    """Current quantity on hand = sum of all signed movements."""
    total = db.execute(
        select(func.coalesce(func.sum(models.StockMovement.quantity), 0)).where(
            models.StockMovement.product_id == product_id
        )
    ).scalar_one()
    return int(total)


def signed_delta(kind: models.MovementKind, quantity: int) -> int:
    """Translate a (kind, magnitude) pair into a signed change in on-hand stock."""
    if kind == models.MovementKind.SHIPMENT:
        return -quantity
    # RECEIPT and positive ADJUSTMENT both increase stock.
    return quantity


def record_movement(
    db: Session, product: models.Product, payload: schemas.MovementCreate
) -> models.StockMovement:
    """Apply a movement, refusing any operation that would drive stock negative."""
    delta = signed_delta(payload.kind, payload.quantity)
    if on_hand(db, product.id) + delta < 0:
        raise StockError("Movement would result in negative stock on hand")

    movement = models.StockMovement(
        product_id=product.id,
        kind=payload.kind,
        quantity=delta,
        note=payload.note,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement


def low_stock(db: Session) -> list[tuple[models.Product, int]]:
    """Products whose on-hand quantity is at or below their reorder level."""
    products = db.execute(select(models.Product)).scalars().all()
    result = [(p, on_hand(db, p.id)) for p in products]
    return [(p, qty) for p, qty in result if qty <= p.reorder_level]
