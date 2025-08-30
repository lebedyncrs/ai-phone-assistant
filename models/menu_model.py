from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any
from .category_model import Category
from .product_model import Product
from .product_variant_model import ProductVariant
from .product_addon_model import ProductAddon
from .addon_value_model import AddonValue


class Menu(BaseModel):
    """Represents the complete menu structure with ID-based search capabilities."""
    categories: list[Category] = Field(default_factory=list, description="Menu categories")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Menu:
        """Create a Menu instance from dictionary data using Pydantic validation."""
        return cls.model_validate(data)

    def find_category_by_id(self, category_id: str) -> Category | None:
        """Find a category by exact ID match."""
        for category in self.categories:
            if category.id == category_id:
                return category
        return None

    def find_product_by_id(self, product_id: str) -> tuple[Category, Product] | None:
        """Find a product by exact ID match."""
        for category in self.categories:
            product = category.find_product_by_id(product_id)
            if product:
                return category, product
        return None

    def find_variant_by_id(self, variant_id: str) -> tuple[Category, Product, ProductVariant] | None:
        """Find a product variant by exact ID match."""
        for category in self.categories:
            for product in category.products:
                variant = product.find_variant_by_id(variant_id)
                if variant:
                    return category, product, variant
        return None

    def find_addon_value_by_id(self, addon_id: str) -> tuple[Category, Product, ProductAddon, AddonValue] | None:
        """Find an addon value by exact ID match."""
        for category in self.categories:
            for product in category.products:
                addon_result = product.find_addon_value_by_id(addon_id)
                if addon_result:
                    addon, addon_value = addon_result
                    return category, product, addon, addon_value
        return None