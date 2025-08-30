from __future__ import annotations

from pydantic import BaseModel, Field, computed_field
from .product_variant_model import ProductVariant
from .product_addon_model import ProductAddon


class Product(BaseModel):
    """Represents a menu product."""
    category_id: str = Field(..., min_length=1, description="Category ID this product belongs to")
    product_id: str = Field(..., min_length=1, description="Unique product identifier")
    product_name: str = Field(..., min_length=1, description="Product name")
    product_description: str | None = Field(None, description="Product description")
    product_variants: list[ProductVariant] = Field(default_factory=list, description="Available variants")
    product_addons: list[ProductAddon] = Field(default_factory=list, description="Available addons")
    product_price: float | None = Field(None, ge=0, description="Fixed price for products without variants")

    @computed_field
    @property
    def has_variants(self) -> bool:
        """Check if product has variants."""
        return len(self.product_variants) > 0

    @computed_field
    @property
    def base_price(self) -> float | None:
        """Get the base price - either fixed price or minimum variant price."""
        if self.product_price is not None:
            return self.product_price
        
        if self.product_variants:
            return min(variant.price for variant in self.product_variants)
        
        return None

    def find_variant_by_id(self, variant_id: str) -> ProductVariant | None:
        """Find a specific variant by exact ID match."""
        for variant in self.product_variants:
            if variant.variant_id == variant_id:
                return variant
        return None

    def find_addon_value_by_id(self, addon_id: str) -> tuple[ProductAddon, AddonValue] | None:
        """Find a specific addon value by exact ID match."""
        for addon in self.product_addons:
            addon_value = addon.find_addon_value_by_id(addon_id)
            if addon_value:
                return addon, addon_value
        return None
