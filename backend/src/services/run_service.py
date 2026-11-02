from __future__ import annotations

import logging
from datetime import date
from typing import Any

import pandas as pd

import services.asset_service as asset_service
from schemas.assets import AssetPropertiesInput

logger = logging.getLogger(__name__)


def _scr_total(
    interest_up: float, interest_down: float, spread: float, equity: float
) -> float:
    return round(max(interest_up, interest_down) + spread + equity, 2)


def price_portfolio(
    positions: list[dict[str, Any]],
    valuation_date: date,
    df_rates: pd.DataFrame,
    df_modelling_properties: pd.DataFrame,
    df_cqs_rating_mapping: pd.DataFrame,
    df_spread_risk_coefficients: pd.DataFrame,
    df_eiopa_equity_adjustment: pd.DataFrame,
    scenarios: list[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:

    position_results: list[dict[str, Any]] = []
    errors: list[str] = []

    for position in positions:
        label = f"{position['id']} ({position.get('name', position['id'])})"

        asset_detail = position.get("asset_detail")
        if not asset_detail:
            errors.append(
                f"{label}: no pricing detail captured for this position -- add it via "
                "'Manually Add Positions' (full TPT column mapping is a follow-up)."
            )
            continue

        try:
            asset = AssetPropertiesInput.model_validate(asset_detail)
            result = asset_service.calculate_single_asset(
                valuation_date=valuation_date,
                asset=asset,
                df_rates=df_rates,
                df_modelling_properties=df_modelling_properties,
                df_cqs_rating_mapping=df_cqs_rating_mapping,
                df_spread_risk_coefficients=df_spread_risk_coefficients,
                df_eiopa_equity_adjustment=df_eiopa_equity_adjustment,
                scenarios=scenarios,
            )
        except (
            Exception
        ) as exc:  # noqa: BLE001 -- isolate one bad position, not the whole run
            logger.warning(
                "Couldn't price position %s: %s", position["id"], exc, exc_info=True
            )
            errors.append(f"{label}: {exc}")
            continue

        position_results.append(
            {
                "position_id": position["id"],
                "name": position.get("name", position["id"]),
                "modelling_class": position["modelling_class"],
                "market_value": result.market_value,
                "scr_interest_up": result.scr.interest_up,
                "scr_interest_down": result.scr.interest_down,
                "scr_spread": result.scr.spread,
                "scr_equity": result.scr.equity,
                "scr_total": _scr_total(
                    result.scr.interest_up,
                    result.scr.interest_down,
                    result.scr.spread,
                    result.scr.equity,
                ),
            }
        )

    return position_results, errors


def summarise(
    position_results: list[dict[str, Any]], positions_total: int, positions_errored: int
) -> dict[str, Any]:
    total_market_value = sum(r["market_value"] for r in position_results)
    return {
        "positions_total": positions_total,
        "positions_errored": positions_errored,
        "total_market_value": round(total_market_value, 2),
        "scr_total": round(sum(r["scr_total"] for r in position_results), 2),
        "scr_interest_up": round(
            sum(r["scr_interest_up"] for r in position_results), 2
        ),
        "scr_interest_down": round(
            sum(r["scr_interest_down"] for r in position_results), 2
        ),
        "scr_spread": round(sum(r["scr_spread"] for r in position_results), 2),
        "scr_equity": round(sum(r["scr_equity"] for r in position_results), 2),
    }
