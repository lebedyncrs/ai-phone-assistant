from __future__ import annotations

from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    """Represents a product variant with specific pricing."""
    name: str = Field(..., min_length=1, description="Variant name")
    price: float = Field(..., gt=0, description="Variant price")
    variant_id: str = Field(..., min_length=1, description="Unique variant identifier")
