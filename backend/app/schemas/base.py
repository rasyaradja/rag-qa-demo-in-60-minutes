"""
Base Pydantic schema for shared fields and configuration.

- Provides common config for all API schemas (ORM mode, UUID handling, etc).
- Defines a reusable base class for inheritance in other schema modules.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

class APIModel(BaseModel):
    """
    Base schema for API models.

    - Enables ORM mode for SQLAlchemy compatibility.
    - Provides JSON encoders for UUID and datetime.
    - Used as a parent for all other schemas.
    """

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        json_encoders = {
            uuid.UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v,
        }
        anystr_strip_whitespace = True
        extra = "forbid"

class IDModel(APIModel):
    """
    Schema with only an 'id' field (UUID).
    """
    id: uuid.UUID = Field(..., description="Unique identifier (UUID)")

class TimestampModel(APIModel):
    """
    Schema with created_at timestamp.
    """
    created_at: datetime = Field(..., description="Creation timestamp (UTC ISO8601)")

class ErrorResponse(APIModel):
    """
    Standard error response schema.
    """
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code identifier")
