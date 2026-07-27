from __future__ import annotations

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import MovementKind


# --- Category ---
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=280)


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --- Product ---
class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    unit_price: float = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    category_id: int | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    """All fields optional — only provided values are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    unit_price: float | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)
    category_id: int | None = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ProductWithStock(ProductRead):
    on_hand: int


# --- Stock movements ---
class MovementCreate(BaseModel):
    kind: MovementKind
    quantity: int = Field(
        description=(
            "Positive magnitude for receipts and shipments; "
            "signed non-zero delta for adjustments"
        )
    )
    note: str | None = Field(default=None, max_length=280)

    @model_validator(mode="after")
    def validate_quantity_direction(self) -> Self:
        if self.kind == MovementKind.ADJUSTMENT:
            if self.quantity == 0:
                raise ValueError("Adjustment quantity must be non-zero")
        elif self.quantity <= 0:
            raise ValueError("Receipt and shipment quantities must be positive")
        return self


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    product_id: int
    kind: MovementKind
    quantity: int
    note: str | None
    created_at: datetime
