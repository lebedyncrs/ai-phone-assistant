from __future__ import annotations

from pydantic import BaseModel, Field
from .addon_value_model import AddonValue


class ProductAddon(BaseModel):
    """Represents an addon group for a product."""
    name: str = Field(..., min_length=1, description="Addon group name")
    values: list[AddonValue] = Field(default_factory=list, description="Available addon values")
    is_for_free: bool = Field(default=False, description="Whether this addon is free")

    def find_addon_value_by_id(self, addon_id: str) -> AddonValue | None:
        """Find a specific addon value by exact ID match."""
        for value in self.values:
            if value.addon_id == addon_id:
                return value
        return None
