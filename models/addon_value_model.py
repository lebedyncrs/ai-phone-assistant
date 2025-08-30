from __future__ import annotations

from pydantic import BaseModel, Field


class AddonValue(BaseModel):
    """Represents a single addon value option."""
    addon_id: str = Field(..., min_length=1, description="Unique addon value identifier")
    name: str = Field(..., min_length=1, description="Addon value name")
