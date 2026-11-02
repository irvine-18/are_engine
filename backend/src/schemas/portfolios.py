from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from schemas.assets import AssetPropertiesInput

PositionStatus = Literal["ok", "warning", "error"]


class PortfolioCreate(BaseModel):
    name: str
    currency: str = "EUR"


class PortfolioRename(BaseModel):
    name: str


class Portfolio(BaseModel):
    id: str
    name: str
    currency: str = "EUR"
    position_count: int = 0
    total_market_value: float = 0
    last_run_at: datetime | None = None
    created_at: datetime
    created_by: str | None = None


class PositionCreate(BaseModel):

    name: str
    modelling_class: str
    rating: str | None = None
    nominal: float | None = None
    market_value: float
    maturity_date: date | None = None
    currency: str = "EUR"
    asset_detail: AssetPropertiesInput | None = None


class Position(BaseModel):
    id: str
    portfolio_id: str
    name: str
    modelling_class: str
    cic: str
    currency: str = "EUR"
    nominal: float | None = None
    market_value: float
    rating: str | None = None
    cqs: int | None = None
    maturity_date: date | None = None
    issuer: str = "Manual entry"
    country: str = "NL"
    included: bool = True
    status: PositionStatus = "ok"
    asset_detail: AssetPropertiesInput | None = None


class ValidationIssue(BaseModel):

    severity: Literal["error", "warning"]
    position: str
    field: str
    message: str


class TptImportResult(BaseModel):
    portfolio_id: str
    upload_id: str
    blob_path: str
    filename: str
    positions_imported: int
    positions: list[Position]
    validation_issues: list[ValidationIssue] = Field(default_factory=list)
