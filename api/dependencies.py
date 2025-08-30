from __future__ import annotations

"""
FastAPI dependencies for the Personal Voice Assistant API.
Common dependencies that can be reused across different route modules.
"""

import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def get_logger():
    """Dependency to provide logger instance to route handlers."""
    return logger


def validate_date_format(date_str: str) -> str:
    """Validate ISO date format (YYYY-MM-DD)."""
    try:
        from datetime import datetime
        datetime.fromisoformat(date_str)
        return date_str
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Expected ISO format (YYYY-MM-DD)"
        )
