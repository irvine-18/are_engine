
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

ExtrapolationMethod = Literal["smith_wilson"]


class EiopaCurveParameters(BaseModel):

    ufr: float = Field(default=0.033, description="Ultimate Forward Rate, decimal.")
    cra: float = Field(default=0.0010, description="Credit Risk Adjustment, decimal.")
    va: float = Field(default=0.0, description="Volatility Adjustment, decimal.")
    include_va: bool = True
    convergence_years: int = Field(default=60, gt=0)
    coupon_frequency: int = Field(default=1, ge=0)
    advanced_overrides: dict[str, float] = Field(default_factory=dict)


class ExtrapolationSettings(BaseModel):
    method: ExtrapolationMethod = "smith_wilson"
    last_liquid_point_years: int = Field(default=20, gt=0)
    alpha_auto_solve: bool = True
    alpha_manual: float | None = None
    alpha_lower_bound: float = 0.05
    convergence_tolerance_bp: float = 1.0


class ShockTablePoint(BaseModel):
    maturity_years: float = Field(gt=0)
    up: float = Field(description="Relative up shock, decimal (0.70 = +70%).")
    down: float = Field(description="Relative down shock, decimal (0.30 = -30%).")


class InterestShockSettings(BaseModel):
    methodology: Literal["standard_formula", "revised_2026", "custom"] = "standard_formula"
    table: list[ShockTablePoint] = Field(default_factory=list)
    sensitivity_bump_bp: float = Field(default=1.0, description="DV01/IR01 bump size in bp.")


class InflationSettings(BaseModel):
    interpolation: Literal["cubic_spline"] = "cubic_spline"
    cost_inflation_ufr: float = 0.02
    cost_inflation_llp_years: int = 50
    sensitivity_bump_bp: float = Field(default=1.0, description="INF01 bump size in bp.")


class CqsMappingRow(BaseModel):
    rating: str
    cqs: int = Field(ge=0, le=6)


class SpreadCoefficientRow(BaseModel):
    cqs: int = Field(ge=0, le=6)
    duration_bucket: float
    a: float
    b: float


class EquitySettings(BaseModel):
    type1_base_shock: float = 0.39
    type2_base_shock: float = 0.49
    symmetric_adjustment_override: float | None = None


class ParameterSet(BaseModel):
    id: str | None = None
    valuation_date: date
    version: int = 1
    currency: str = "EUR"
    projection_horizon_years: int = 120

    eiopa: EiopaCurveParameters = EiopaCurveParameters()
    extrapolation: ExtrapolationSettings = ExtrapolationSettings()
    interest_shocks: InterestShockSettings = InterestShockSettings()
    inflation: InflationSettings = InflationSettings()
    cqs_mapping: list[CqsMappingRow] = Field(default_factory=list)
    spread_coefficients: list[SpreadCoefficientRow] = Field(default_factory=list)
    equity: EquitySettings = EquitySettings()
