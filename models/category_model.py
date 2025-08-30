from __future__ import annotations

from pydantic import BaseModel, Field
from .product_model import Product


class Category(BaseModel):
    """Represents a menu category."""
    id: str = Field(..., min_length=1, description="Unique category identifier")
    name: str = Field(..., min_length=1, description="Category name")
    products: list[Product] = Field(default_factory=list, description="Products in this category")

    def find_product_by_id(self, product_id: str) -> Product | None:
        """Find a product by exact ID match."""
        for product in self.products:
            if product.product_id == product_id:
                return product
        return None
