from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from schemas.curves import CurveRunKpis


class TemplateLastRun(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    ran_at: str = Field(alias="ranAt")
    status: str
    curve_run_id: str = Field(alias="curveRunId")
    kpis: dict[str, CurveRunKpis] = Field(default_factory=dict)
    equity_symmetric_adjustment: float | None = Field(
        default=None, alias="equitySymmetricAdjustment"
    )
    inflation_warning: str | None = Field(default=None, alias="inflationWarning")


class EconomicDataTemplate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    valuation_date: str = Field(alias="valuationDate")
    currency: str = "EUR"
    projection_horizon_years: int = Field(default=120, alias="projectionHorizonYears")
    created_at: str = Field(alias="createdAt")
    is_default: bool | None = Field(default=None, alias="isDefault")
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    interest: dict[str, Any] = Field(default_factory=dict)
    inflation: dict[str, Any] = Field(default_factory=dict)
    hicp: dict[str, Any] = Field(default_factory=dict)
    equity: dict[str, Any] = Field(default_factory=dict)
    credit_spread: dict[str, Any] = Field(default_factory=dict, alias="creditSpread")
    last_run: TemplateLastRun | None = Field(default=None, alias="lastRun")


class EconomicDataTemplateInput(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    name: str
    valuation_date: str = Field(alias="valuationDate")
    currency: str = "EUR"
    projection_horizon_years: int = Field(default=120, alias="projectionHorizonYears")
    is_default: bool | None = Field(default=None, alias="isDefault")
    scenarios: list[dict[str, Any]] = Field(default_factory=list)
    interest: dict[str, Any] = Field(default_factory=dict)
    inflation: dict[str, Any] = Field(default_factory=dict)
    hicp: dict[str, Any] = Field(default_factory=dict)
    equity: dict[str, Any] = Field(default_factory=dict)
    credit_spread: dict[str, Any] = Field(default_factory=dict, alias="creditSpread")
