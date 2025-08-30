from __future__ import annotations

from pydantic import BaseModel, Field, computed_field
from .addon_value_model import AddonValue


class ProductAddon(BaseModel):
    """Represents an addon group for a product."""
    name: str = Field(..., min_length=1, description="Addon group name")
    values: list[AddonValue] = Field(default_factory=list, description="Available addon values")
    price: float = Field(default=0, ge=0, description="Addon price")
    type: str = Field(default="checkbox", description="Addon type")
    reference_id: str | None = Field(default=None, description="Reference ID for global addons")

    def find_addon_value_by_id(self, addon_id: str) -> AddonValue | None:
        """Find a specific addon value by exact ID match."""
        for value in self.values:
            if value.addon_id == addon_id:
                return value
        return None
    
    @computed_field
    @property
    def is_free(self) -> bool:
        """Check if this addon is free."""
        return self.price == 0 and (len(self.values) == 0 or (len(self.values) > 0 and self.values[0].price == 0))