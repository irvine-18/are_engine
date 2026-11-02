from datetime import date

from pydantic import BaseModel, Field

from schemas.market_data import (
    HicpObservation,
    InflationCurveInput,
    InterestRateCurveInput,
)
from schemas.parameters import ParameterSet
from schemas.scenarios import CurveSet


class CurveRunRequest(BaseModel):
    valuation_date: date
    curve_set: CurveSet = "EIOPA_incl_VA"
    interest: InterestRateCurveInput
    inflation: InflationCurveInput | None = None
    hicp_observations: list[HicpObservation] = []
    parameters: ParameterSet
    scenario_names: list[str] | None = Field(
        default=None,
        description="None = run every 'exante' scenario defined for curve_set.",
    )


class CurvePoint(BaseModel):
    year: float | None = None
    month: int | None = None
    discount_factor: float | None
    spot_rate: float | None
    forward_rate: float | None
    liquid_tenor_rate: float | None = None


class ScenarioCurve(BaseModel):
    scenario: str
    scenario_id: str
    shock: str
    annual: list[CurvePoint]
    monthly: list[CurvePoint]


class CurveRunKpis(BaseModel):
    spot_10y: float | None = None
    spot_20y: float | None = None
    spot_30y: float | None = None
    forward_60y: float | None = None
    alpha: float | None = None


class CurveRunResult(BaseModel):
    curve_run_id: str
    valuation_date: date
    curve_set: CurveSet
    scenarios: list[ScenarioCurve]
    kpis: CurveRunKpis
    inflation: list[ScenarioCurve] = []
    cost_inflation: list[ScenarioCurve] = []
    inflation_warning: str | None = None


INTEREST_CURVE_SETS: list[CurveSet] = ["EIOPA_no_VA", "EIOPA_incl_VA"]


class TemplateCurveRunResult(BaseModel):
    template_id: str
    valuation_date: date
    ran_at: str
    curve_sets: dict[CurveSet, list[ScenarioCurve]]
    kpis: dict[CurveSet, CurveRunKpis]
    inflation: list[ScenarioCurve] = []
    cost_inflation: list[ScenarioCurve] = []
    equity_symmetric_adjustment: float | None = None
    inflation_warning: str | None = None
