from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Entity(BaseModel):
    id: str
    type: str
    schema_version: int = 1
    created_at: datetime
    created_by: str | None = None


class ValuationDateParam(BaseModel):
    valuation_date: date
