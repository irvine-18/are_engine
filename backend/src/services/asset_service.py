import logging
from datetime import date

import pandas as pd

from model.asset_risk.asset_model import Asset

from schemas.assets import (
    AssetPropertiesInput,
    CashflowRow,
    ScenarioResult,
    ScrBreakdown,
    SingleAssetResult,
)
from schemas.parameters import ParameterSet

logger = logging.getLogger(__name__)


def build_equity_adjustment_df(
    parameters: ParameterSet, market_data_value: float | None
) -> pd.DataFrame:
    value = parameters.equity.symmetric_adjustment_override
    if value is None:
        value = market_data_value if market_data_value is not None else 0.0
    return pd.DataFrame({"eiopa_equity_adjustment": [value]})


def build_cqs_mapping_df(
    parameters: ParameterSet, default: pd.DataFrame
) -> pd.DataFrame:
    if not parameters.cqs_mapping:
        return default
    return pd.DataFrame([row.model_dump() for row in parameters.cqs_mapping])


def build_spread_coefficients_df(
    parameters: ParameterSet, default: pd.DataFrame
) -> pd.DataFrame:
    if not parameters.spread_coefficients:
        return default
    return pd.DataFrame([row.model_dump() for row in parameters.spread_coefficients])


def calculate_single_asset(
    valuation_date: date,
    asset: AssetPropertiesInput,
    df_rates: pd.DataFrame,
    df_modelling_properties: pd.DataFrame,
    df_cqs_rating_mapping: pd.DataFrame,
    df_spread_risk_coefficients: pd.DataFrame,
    df_eiopa_equity_adjustment: pd.DataFrame,
    scenarios: list[str] | None = None,
) -> SingleAssetResult:

    asset_properties = asset.model_dump()

    for key in ("issue_date", "maturity_date", "first_call_date", "next_coupon_date"):
        if key in asset_properties and asset_properties[key] is not None:
            asset_properties[key] = pd.Timestamp(asset_properties[key])

    engine_asset = Asset(
        valuation_date=pd.Timestamp(valuation_date),
        asset_properties=asset_properties,
        df_rates=df_rates,
        df_eiopa_equity_adjustment=df_eiopa_equity_adjustment,
        df_modelling_properties=df_modelling_properties,
        df_cqs_rating_mapping=df_cqs_rating_mapping,
        df_spread_risk_coefficients=df_spread_risk_coefficients,
    )

    target_scenarios = (
        list(scenarios) if scenarios else list(df_rates["scenario"].unique())
    )
    scenario_errors: list[str] = []
    for scenario in target_scenarios:
        try:
            engine_asset.calc_sensitivities_scr_risk(scenarios=[scenario])
        except (
            Exception
        ) as exc:  # noqa: BLE001 -- isolate one bad scenario, not the whole calc
            logger.warning(
                "Couldn't price scenario %r for %s: %s",
                scenario,
                asset.position_id,
                exc,
            )
            scenario_errors.append(f"{scenario}: {exc}")

    df_scr = engine_asset.df_scr_risk
    if df_scr is None or df_scr.empty:
        raise RuntimeError(
            f"Couldn't price any scenario for {asset.position_id} "
            f"({'; '.join(scenario_errors) if scenario_errors else 'no scenarios available'})"
        )
    base_row = (
        df_scr[df_scr["scenario"] == "Base"].iloc[0]
        if "Base" in df_scr["scenario"].values
        else df_scr.iloc[0]
    )

    scenario_results = []
    base_mv = float(
        base_row.get("shocked_mv_base", base_row.get("market_value", 0.0)) or 0.0
    )
    for _, row in df_scr.iterrows():
        mv = float(row.get("shocked_mv_base", row.get("market_value", 0.0)) or 0.0)
        delta = mv - base_mv
        scenario_results.append(
            ScenarioResult(
                scenario=row["scenario"],
                market_value=mv,
                delta_vs_base=delta,
                delta_vs_base_pct=(delta / base_mv) if base_mv else None,
            )
        )

    cashflows: list[CashflowRow] = []
    if engine_asset.df_asset_cashflows is not None:
        df_cf = engine_asset.df_asset_cashflows
        if scenarios:
            df_cf = df_cf[df_cf["scenario"].isin(scenarios)]
        for _, row in df_cf.iterrows():
            cashflows.append(
                CashflowRow(
                    month=int(row["month"]),
                    date=row["date_month"].date(),
                    scenario=row["scenario"],
                    shock=row["shock"],
                    coupon_payment=float(row["coupon_payment"]),
                    maturity_payment=float(row["maturity_payment"]),
                    cashflow=float(row["cashflow"]),
                    discount_factor=float(row.get("discount_factor", 0.0) or 0.0),
                    discounted_cashflow=float(row["discounted_cashflow"]),
                )
            )

    return SingleAssetResult(
        position_id=asset.position_id,
        market_value=base_mv,
        z_spread_bp=float(engine_asset.z_spread or 0.0),
        dv01=float(base_row.get("ir01", 0.0) or 0.0),
        inf01=float(base_row.get("inf01", 0.0) or 0.0),
        scr=ScrBreakdown(
            interest_down=float(base_row.get("scr_interest_down_risk", 0.0) or 0.0),
            interest_up=float(base_row.get("scr_interest_up_risk", 0.0) or 0.0),
            spread=float(base_row.get("scr_spread_risk", 0.0) or 0.0),
            equity=float(base_row.get("scr_equity_risk", 0.0) or 0.0),
        ),
        scenario_results=scenario_results,
        cashflows=cashflows,
        scenario_errors=scenario_errors,
    )
