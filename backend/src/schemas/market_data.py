from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

RateUnit = Literal["decimal", "pct", "bp"]
InstrumentType = Literal["swap_par", "zero", "government_bond"]
InterestBasis = Literal["6M_EURIBOR", "ESTR_OIS"]
InflationIndex = Literal["HICPxT", "HICP"]
MarketDataSource = Literal["manual", "upload", "eiopa_rfr", "ecb_yield_curve", "ecb_estr"]


class LiquidRatePoint(BaseModel):

    tenor_years: float = Field(gt=0)
    rate: float
    liquid: bool = True
    source: str | None = None


def normalise_rate(value: float, unit: RateUnit) -> float:
    if unit == "pct":
        return value / 100.0
    if unit == "bp":
        return value / 10000.0
    return value


class InterestRateCurveInput(BaseModel):
    basis: InterestBasis = "6M_EURIBOR"
    instrument_type: InstrumentType = "swap_par"
    points: list[LiquidRatePoint] = Field(min_length=1)


class InflationCurveInput(BaseModel):
    index: InflationIndex = "HICPxT"
    points: list[LiquidRatePoint] = Field(min_length=1)


class HicpObservation(BaseModel):
    month: date
    hicp: float


class OtherMarketInputs(BaseModel):
    eiopa_equity_adjustment: float | None = Field(
        default=None, description="EIOPA equity symmetric adjustment, decimal (e.g. -0.02)."
    )
    latest_hicp: HicpObservation | None = None


class MarketDataSetCreate(BaseModel):
    valuation_date: date
    source: MarketDataSource = "manual"
    interest: InterestRateCurveInput | None = None
    inflation: InflationCurveInput | None = None
    hicp_observations: list[HicpObservation] = []
    other: OtherMarketInputs = OtherMarketInputs()


class MarketDataSet(MarketDataSetCreate):
    id: str
    version: int
    created_at: datetime
    created_by: str | None = None
