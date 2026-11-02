from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

ModellingClass = Literal[
    "gvt_bond_fixed_coupon",
    "gvt_bond_inflation_linked",
    "corp_bond_fixed_coupon",
    "corp_bond_floating_interest",
    "irs_fixed",
    "irs_floating",
    "ils_fixed",
    "ils_floating",
    "fx_forward",
    "equity",
    "cash",
]


class AssetPropertiesInput(BaseModel):

    model_config = ConfigDict(extra="allow")

    position_id: str
    portfolio: str
    asset_id: str
    modelling_class: ModellingClass
    storage_class: str | None = None
    internal_class: str | None = None
    fixed_or_floating: str | None = None
    counterparty: str | None = None
    country_of_issuer: str | None = None
    rating: str | None = None
    management_style: str | None = None
    quotation_currency: str = "EUR"
    exchange_rate: float = 1.0

    nominal: float | None = None
    market_value: float
    modified_duration: float | None = None

    issue_date: date | None = None
    maturity_date: date | None = None
    first_call_date: date | None = None
    next_coupon_date: date | None = None
    coupon_frequency: int | None = None

    annual_fixed_coupon_rate: float | None = None
    annual_nominal_coupon_rate: float | None = None
    annual_floating_coupon_rate: float | None = None
    annual_coupon_spread: float | None = None
    annual_fixed_interest_rate: float | None = None
    annual_floating_interest_rate: float | None = None
    annual_interest_rate: float | None = None
    swap_term: int | None = None

    inflation_index: str | None = None
    inflation_index_start: float | None = None
    inflation_index_lag: int | None = None
    current_indexation_coefficient: float | None = None

    equity_type: int | None = None
    nominal_quotation_currency: float | None = None
    nominal_portfolio_currency: float | None = None


class SampleAsset(BaseModel):

    id: str
    modelling_class: ModellingClass
    name: str
    asset: AssetPropertiesInput


class SingleAssetRequest(BaseModel):
    valuation_date: date
    asset: AssetPropertiesInput
    curve_run_id: str
    scenarios: list[str] | None = None


class ScrBreakdown(BaseModel):
    interest_down: float = 0
    interest_up: float = 0
    spread: float = 0
    equity: float = 0
    currency: None = None  # not implemented -- see CODE_OVERVIEW.md known gaps


class ScenarioResult(BaseModel):
    scenario: str
    market_value: float
    delta_vs_base: float
    delta_vs_base_pct: float | None = None


class CashflowRow(BaseModel):
    month: int
    date: date
    scenario: str
    shock: str
    coupon_payment: float
    maturity_payment: float
    cashflow: float
    discount_factor: float
    discounted_cashflow: float


class SingleAssetResult(BaseModel):
    position_id: str
    market_value: float
    z_spread_bp: float
    dv01: float | None = None
    inf01: float | None = None
    scr: ScrBreakdown
    scenario_results: list[ScenarioResult]
    cashflows: list[CashflowRow]
    scenario_errors: list[str] = []
