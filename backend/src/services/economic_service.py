from datetime import date, datetime, timezone

import numpy as np
import pandas as pd

from model.economic_data.interest import InterestRate
from model.economic_data.inflation import Inflation
from model.economic_data.app import EconomicDataExtraction
from model.utilities import add_months_to_date

from schemas.curves import (
    INTEREST_CURVE_SETS,
    CurvePoint,
    CurveRunKpis,
    CurveRunResult,
    ScenarioCurve,
    TemplateCurveRunResult,
)
from schemas.market_data import (
    InflationCurveInput,
    InterestRateCurveInput,
    HicpObservation,
)
from schemas.parameters import ParameterSet, ShockTablePoint
from schemas.scenarios import CurveSet

EIOPA_LAST_LIQUID_POINT_YEARS = 20


def liquid_rates_to_df(curve: InterestRateCurveInput) -> pd.DataFrame:

    rows = [{"tenor": int(p.tenor_years), "swap_rate": p.rate} for p in curve.points]
    return pd.DataFrame(rows).sort_values("tenor").reset_index(drop=True)


def inflation_swap_rates_to_df(curve: InflationCurveInput) -> pd.DataFrame:

    rows = [
        {
            "tenor": int(p.tenor_years),
            "cmpl_pricing": p.rate * 100.0,
            "bgn_pricing": p.rate * 100.0,
        }
        for p in curve.points
    ]
    return pd.DataFrame(rows).sort_values("tenor").reset_index(drop=True)


def hicp_observations_to_df(observations: list[HicpObservation]) -> pd.DataFrame:
    rows = [
        {
            "date": pd.Timestamp(o.month),
            "date_month": pd.Timestamp(o.month).to_period("M").to_timestamp(),
            "hicp": o.hicp,
        }
        for o in observations
    ]
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True)


DEFAULT_INTEREST_SHOCK_TABLE: list[tuple[float, float, float]] = [
    # (maturity_years, up, down) relative shocks, decimals
    (1, 0.70, 0.75),
    (5, 0.70, 0.46),
    (10, 0.56, 0.31),
    (15, 0.52, 0.27),
    (20, 0.49, 0.26),
    (90, 0.20, 0.20),
]


def build_eiopa_shocks_df(
    parameters: ParameterSet, max_year: int = 120
) -> pd.DataFrame:

    table = [
        (p.maturity_years, p.up, p.down) for p in parameters.interest_shocks.table
    ] or DEFAULT_INTEREST_SHOCK_TABLE
    table = sorted(table, key=lambda t: t[0])

    rows = []
    for year in range(1, max_year + 1):
        point = table[0]
        for candidate in table:
            if candidate[0] <= year:
                point = candidate
        rows.append(
            {"year": year, "eiopa_shock_up": point[1], "eiopa_shock_down": point[2]}
        )
    return pd.DataFrame(rows)


def build_eiopa_parameters_df(parameters: ParameterSet) -> pd.DataFrame:

    p = parameters.eiopa
    ufr_bp = p.ufr * 10000.0
    cra_bp = p.cra * 10000.0
    va_bp = (p.va * 10000.0) if p.include_va else 0.0

    values = {
        "EIOPA_coupon_frequency": float(p.coupon_frequency),
        "EIOPA_covergance_years": float(p.convergence_years),
        "EIOPA_CRA": cra_bp,
        "EIOPA_UFR": ufr_bp,
        "EIOPA_UFR_15Down": ufr_bp - 15.0,
        "UFR200": 200.0,  # placeholder stand-in for the historical "UFR220" sensitivity scenario
        "EIOPA_no_VA": 0.0,
        "EIOPA_VA": va_bp,
        "EIOPA_VA_01Down": max(0.0, va_bp - 1.0),
        "EIOPA_VA_10Up": va_bp + 10.0,
        "EIOPA_VA_20Up": va_bp + 20.0,
        "EIOPA_VA_30Up": va_bp + 30.0,
        "EIOPA_VA_50Up": va_bp + 50.0,
        "EIOPA_VA_70Up": va_bp + 70.0,
        "EIOPA_VA_90Up": va_bp + 90.0,
        "EIOPA_VA_110Up": va_bp + 110.0,
    }
    values.update(p.advanced_overrides)
    return pd.DataFrame([values])


# ---------------------------------------------------------------------------
# Curve building
# ---------------------------------------------------------------------------


def resolve_interest_scenarios(
    df_interest_scenarios: pd.DataFrame, parameters: ParameterSet
) -> pd.DataFrame:

    df_eiopa_parameters = build_eiopa_parameters_df(parameters)
    extraction = EconomicDataExtraction(
        valuation_date=pd.Timestamp(parameters.valuation_date),
        files={
            k: None
            for k in (
                "refinitiv_swap_rates",
                "inflation_swap_rates",
                "hicp",
                "eiopa_rfr",
                "eiopa_equity_adjustment",
            )
        },
        settings=_SettingsShim(df_interest_scenarios=df_interest_scenarios),
    )
    return extraction.create_rates_scenarios(
        df_eiopa_parameters=df_eiopa_parameters,
        df_interest_scenarios=df_interest_scenarios,
    )


def apply_interest_sw_parameters(
    parameters: ParameterSet, sw_parameters: dict
) -> ParameterSet:

    return parameters.model_copy(
        update={
            "eiopa": parameters.eiopa.model_copy(
                update={
                    "ufr": sw_parameters["ufr"],
                    "cra": sw_parameters["cra"],
                    "va": sw_parameters["va"],
                    "include_va": sw_parameters["includeVA"],
                    "convergence_years": sw_parameters["convergenceYears"],
                }
            )
        }
    )


def apply_interest_scr_shocks(
    parameters: ParameterSet, scr_shocks: dict
) -> ParameterSet:

    table = scr_shocks.get("table") or []
    if not table:
        return parameters
    return parameters.model_copy(
        update={
            "interest_shocks": parameters.interest_shocks.model_copy(
                update={"table": [ShockTablePoint.model_validate(row) for row in table]}
            )
        }
    )


def run_interest_curves(
    valuation_date: date,
    interest_input: InterestRateCurveInput,
    parameters: ParameterSet,
    df_interest_scenarios: pd.DataFrame,
) -> dict:

    df_liquid = liquid_rates_to_df(interest_input)
    df_eiopa_shocks = build_eiopa_shocks_df(parameters)
    df_interest_rate_scenarios = resolve_interest_scenarios(
        df_interest_scenarios, parameters
    )

    interest = InterestRate(
        valuation_date=pd.Timestamp(valuation_date),
        df_interest_swap_rates=df_liquid,
        df_eiopa_shocks=df_eiopa_shocks,
        df_interest_rate_scenarios=df_interest_rate_scenarios,
    )
    interest.get_all_interest_rates()
    return interest.interest_data


def _apply_interest_shock(base: pd.Series, shock: dict) -> pd.Series:

    shock_type = shock.get("type", "none")
    if shock_type == "none":
        return base
    if shock_type == "parallel_bps":
        return base + shock["shiftBps"] / 10_000.0
    if shock_type == "relative_percent":
        return base * (1 + shock["shiftPercent"] / 100.0)
    if shock_type == "custom_per_tenor":
        rows = sorted(shock.get("rows", []), key=lambda r: r["maturityYears"])
        if not rows:
            return base
        shift_bp = pd.Series(index=base.index, dtype=float)
        for year in base.index:
            point = rows[0]["shiftBps"]
            for r in rows:
                if r["maturityYears"] <= year:
                    point = r["shiftBps"]
            shift_bp.loc[year] = point
        return base + shift_bp / 10_000.0
    return base


def run_eiopa_published_interest_curves(
    valuation_date: date,
    base_curves: dict[str, pd.Series],
    scr_shock_bp: pd.DataFrame | None,
    scenarios: list[dict],
) -> dict:

    shock_lookup = (
        scr_shock_bp.set_index("maturity")[["scr_up_shock", "scr_down_shock"]]
        if scr_shock_bp is not None
        else None
    )

    active = [s for s in scenarios if s.get("active", True)]
    scenario_defs = [
        s for s in active if s["interestShock"].get("type") != "regulatory"
    ]
    if not any(s["interestShock"].get("type") == "none" for s in scenario_defs):
        scenario_defs = [
            {"id": "base", "name": "Base", "interestShock": {"type": "none"}}
        ] + scenario_defs

    rows = []
    for curve_set, base in base_curves.items():
        for scenario_def in scenario_defs:
            scenario_curve = _apply_interest_shock(base, scenario_def["interestShock"])
            meta = {
                "rates": curve_set,
                "scenario": scenario_def["name"],
                "scenario_id": f"{curve_set} ({scenario_def['name']})",
                "shock_type": "postante",
                "instrument": "n/a",
                "coupon_frequency": 1,
                "convergence_years": 0,
                "cra_bp": 0.0,
                "ufr_bp": 0.0,
                "va_bp": 0.0,
                "shock_bp": 0.0,
            }

            for shock_label, curve in [
                ("base", scenario_curve),
                ("ir01", scenario_curve + 1.0 / 10_000.0),
            ]:
                for year, rate in curve.items():
                    rows.append(
                        {
                            **meta,
                            "shock": shock_label,
                            "year": year,
                            "liquid_tenor_rate": (
                                rate if year <= EIOPA_LAST_LIQUID_POINT_YEARS else None
                            ),
                            "interest_rate": rate,
                        }
                    )
            if shock_lookup is not None:
                shocked = pd.DataFrame({"interest_rate": scenario_curve}).join(
                    shock_lookup, how="inner"
                )
                for shock_label, shock_col in [
                    ("scr_interest_up", "scr_up_shock"),
                    ("scr_interest_down", "scr_down_shock"),
                ]:
                    for year, shocked_row in shocked.iterrows():
                        rows.append(
                            {
                                **meta,
                                "shock": shock_label,
                                "year": year,
                                "liquid_tenor_rate": None,
                                "interest_rate": shocked_row["interest_rate"]
                                + shocked_row[shock_col] / 10_000.0,
                            }
                        )

    df_annual = pd.DataFrame(rows)

    year_zero = df_annual[df_annual["year"] == 1].copy()
    year_zero["year"] = 0
    year_zero["liquid_tenor_rate"] = None
    df_annual = pd.concat([year_zero, df_annual], ignore_index=True)

    df_annual["valuation_date"] = pd.Timestamp(valuation_date)
    df_annual["valuation_date_month"] = (
        df_annual["valuation_date"].dt.to_period("M").dt.to_timestamp()
    )
    df_annual["date_month"] = add_months_to_date(
        date_column=df_annual["valuation_date_month"],
        months_column=df_annual["year"] * 12,
    )
    df_annual["discount_factor"] = (1 + df_annual["interest_rate"]) ** (
        -df_annual["year"]
    )

    df_annual = df_annual.sort_values(["scenario_id", "shock", "year"])
    df_annual["discount_factor_lagged"] = df_annual.groupby(["scenario_id", "shock"])[
        "discount_factor"
    ].shift(1)
    df_annual["forward_rate"] = np.where(
        df_annual["year"] == 0,
        df_annual["interest_rate"],
        (df_annual["discount_factor_lagged"] / df_annual["discount_factor"]) - 1,
    )
    df_annual = df_annual.drop(columns=["discount_factor_lagged"])

    df_annual = df_annual[
        [
            "valuation_date",
            "rates",
            "scenario",
            "scenario_id",
            "shock",
            "shock_type",
            "instrument",
            "coupon_frequency",
            "convergence_years",
            "cra_bp",
            "ufr_bp",
            "va_bp",
            "shock_bp",
            "valuation_date_month",
            "date_month",
            "year",
            "liquid_tenor_rate",
            "discount_factor",
            "forward_rate",
            "interest_rate",
        ]
    ]

    interest = InterestRate(
        valuation_date=None,
        df_interest_swap_rates=None,
        df_eiopa_shocks=None,
        df_interest_rate_scenarios=None,
    )
    df_monthly = interest.get_monthly_rates(df_interest_rates_annual=df_annual)

    return {"interest_rates_annual": df_annual, "interest_rates_monthly": df_monthly}


def apply_cost_inflation_sw_parameters(
    df_inflation_scenarios: pd.DataFrame, sw_parameters: dict
) -> pd.DataFrame:

    df = df_inflation_scenarios.copy()
    df["ufr_bp"] = sw_parameters["ufr"] * 10000.0
    df["cra_bp"] = sw_parameters["cra"] * 10000.0
    df["convergence_years"] = sw_parameters["convergenceYears"]
    return df


def run_inflation_curves(
    valuation_date: date,
    inflation_input: InflationCurveInput | None,
    hicp_observations: list[HicpObservation],
    df_inflation_scenarios: pd.DataFrame,
) -> dict | None:

    if inflation_input is None:
        return None

    inflation = Inflation(
        valuation_date=pd.Timestamp(valuation_date),
        df_inflation_swap_rates=inflation_swap_rates_to_df(inflation_input),
        df_inflation_scenarios=df_inflation_scenarios,
        df_hicp=(
            hicp_observations_to_df(hicp_observations)
            if hicp_observations
            else pd.DataFrame(columns=["date", "date_month", "hicp"])
        ),
    )
    inflation.get_all_inflation()
    return inflation.inflation_data


class _SettingsShim:

    def __init__(self, df_interest_scenarios: pd.DataFrame):
        self.data_specs = {}
        self.parameters = {
            "interest_scenarios": df_interest_scenarios,
            "inflation_scenarios": pd.DataFrame(),
        }


def _float_or_none(value) -> float | None:

    return float(value) if pd.notna(value) else None


def _points(df: pd.DataFrame, year_col: str, rate_col: str) -> list[CurvePoint]:
    points = []
    for _, row in df.iterrows():
        points.append(
            CurvePoint(
                year=_float_or_none(row.get(year_col)) if year_col in row else None,
                month=(
                    int(row["month"])
                    if "month" in row and pd.notna(row.get("month"))
                    else None
                ),
                discount_factor=_float_or_none(row.get("discount_factor")),
                spot_rate=_float_or_none(row.get(rate_col)),
                forward_rate=_float_or_none(row.get("forward_rate")),
                liquid_tenor_rate=_float_or_none(row.get("liquid_tenor_rate")),
            )
        )
    return points


def to_curve_run_result(
    curve_run_id: str,
    valuation_date: date,
    curve_set: CurveSet,
    interest_data: dict,
) -> CurveRunResult:

    rate_col = "interest_rate"
    df_annual = interest_data["interest_rates_annual"]
    df_monthly = interest_data["interest_rates_monthly"]

    df_annual = (
        df_annual[df_annual["rates"] == curve_set]
        if "rates" in df_annual.columns
        else df_annual
    )
    df_monthly = (
        df_monthly[df_monthly["rates"] == curve_set]
        if "rates" in df_monthly.columns
        else df_monthly
    )

    scenarios: list[ScenarioCurve] = []
    base_spot_10y = base_spot_20y = base_spot_30y = base_fwd_60y = None

    for (scenario, scenario_id, shock), df_group in df_annual.groupby(
        ["scenario", "scenario_id", "shock"]
    ):
        annual_points = _points(df_group.sort_values("year"), "year", rate_col)
        df_m = df_monthly[
            (df_monthly["scenario"] == scenario)
            & (df_monthly["scenario_id"] == scenario_id)
            & (df_monthly["shock"] == shock)
        ].sort_values("month")
        monthly_points = _points(df_m, "month", "interest_rate")

        scenarios.append(
            ScenarioCurve(
                scenario=scenario,
                scenario_id=scenario_id,
                shock=shock,
                annual=annual_points,
                monthly=monthly_points,
            )
        )

        if shock == "base" and scenario == "Base":
            by_year = {p.year: p.spot_rate for p in annual_points}
            base_spot_10y = by_year.get(10.0, base_spot_10y)
            base_spot_20y = by_year.get(20.0, base_spot_20y)
            base_spot_30y = by_year.get(30.0, base_spot_30y)
            by_year_fwd = {p.year: p.forward_rate for p in annual_points}
            base_fwd_60y = by_year_fwd.get(60.0, base_fwd_60y)

    return CurveRunResult(
        curve_run_id=curve_run_id,
        valuation_date=valuation_date,
        curve_set=curve_set,
        scenarios=scenarios,
        kpis=CurveRunKpis(
            spot_10y=base_spot_10y,
            spot_20y=base_spot_20y,
            spot_30y=base_spot_30y,
            forward_60y=base_fwd_60y,
        ),
    )


def to_inflation_scenario_curves(
    inflation_data: dict, rates: str
) -> list[ScenarioCurve]:

    df_annual = inflation_data["inflation_rates_annual"]
    df_monthly = inflation_data["inflation_rates_monthly"]
    df_annual = df_annual[df_annual["rates"] == rates]
    df_monthly = df_monthly[df_monthly["rates"] == rates]

    scenarios: list[ScenarioCurve] = []
    for (scenario, scenario_id, shock), df_group in df_annual.groupby(
        ["scenario", "scenario_id", "shock"]
    ):
        annual_points = _points(df_group.sort_values("year"), "year", "spot_inflation")
        df_m = df_monthly[
            (df_monthly["scenario"] == scenario)
            & (df_monthly["scenario_id"] == scenario_id)
            & (df_monthly["shock"] == shock)
        ].sort_values("month")
        monthly_points = _points(df_m, "month", "spot_inflation")
        scenarios.append(
            ScenarioCurve(
                scenario=scenario,
                scenario_id=scenario_id,
                shock=shock,
                annual=annual_points,
                monthly=monthly_points,
            )
        )
    return scenarios


def to_template_curve_run_result(
    template_id: str,
    valuation_date: date,
    interest_data: dict,
    inflation_data: dict | None,
    inflation_warning: str | None = None,
) -> TemplateCurveRunResult:

    curve_sets: dict[str, list[ScenarioCurve]] = {}
    kpis: dict[str, CurveRunKpis] = {}
    for curve_set in INTEREST_CURVE_SETS:
        sliced = to_curve_run_result(
            curve_run_id=template_id,
            valuation_date=valuation_date,
            curve_set=curve_set,
            interest_data=interest_data,
        )
        curve_sets[curve_set] = sliced.scenarios
        kpis[curve_set] = sliced.kpis

    return TemplateCurveRunResult(
        template_id=template_id,
        valuation_date=valuation_date,
        ran_at=datetime.now(timezone.utc).isoformat(),
        curve_sets=curve_sets,
        kpis=kpis,
        inflation=(
            to_inflation_scenario_curves(inflation_data, "Inflation")
            if inflation_data is not None
            else []
        ),
        cost_inflation=(
            to_inflation_scenario_curves(inflation_data, "Cost Inflation")
            if inflation_data is not None
            else []
        ),
        inflation_warning=inflation_warning,
    )


_INTEREST_SHOCK_COLUMNS = {
    "base": "spot_interest",
    "scr_interest_down": "scr_interest_down",
    "scr_interest_up": "scr_interest_up",
    "ir01": "spot_interest01",
}
_INFLATION_SHOCK_COLUMNS = {"base": "spot_inflation", "inf01": "spot_inflation01"}
_HICP_SHOCK_COLUMNS = {"base": "hicp", "inf01": "hicp01"}


def _pivot_shock(
    df: pd.DataFrame, value_col: str, shock_map: dict[str, str]
) -> pd.DataFrame:
    df = df[df["shock"].isin(shock_map.keys())].copy()
    df["shock_name"] = df["shock"].map(shock_map)
    pivoted = df.pivot_table(
        index=["scenario", "month"],
        columns="shock_name",
        values=value_col,
        aggfunc="first",
    )
    return pivoted.reset_index()


def build_asset_rates_table(
    interest_data: dict,
    inflation_data: dict | None,
    interest_curve_set: CurveSet = "EIOPA_incl_VA",
) -> pd.DataFrame:

    df_interest_monthly = interest_data["interest_rates_monthly"]
    df_interest_monthly = df_interest_monthly[
        df_interest_monthly["rates"] == interest_curve_set
    ]
    interest_wide = _pivot_shock(
        df_interest_monthly, "interest_rate", _INTEREST_SHOCK_COLUMNS
    )

    if inflation_data is None:
        for col in ("spot_inflation", "spot_inflation01", "hicp", "hicp01"):
            interest_wide[col] = 0.0
        interest_wide["month"] = interest_wide["month"].astype(int)
        return interest_wide

    df_cost_inflation_monthly = inflation_data["inflation_rates_monthly"]
    df_cost_inflation_monthly = df_cost_inflation_monthly[
        df_cost_inflation_monthly["rates"] == "Cost Inflation"
    ]
    inflation_wide = _pivot_shock(
        df_cost_inflation_monthly, "spot_inflation", _INFLATION_SHOCK_COLUMNS
    )

    df_hicp = inflation_data["hicp"]
    hicp_wide = _pivot_shock(df_hicp, "hicp", _HICP_SHOCK_COLUMNS)

    base_inflation = inflation_wide[inflation_wide["scenario"] == "Base"][
        ["month", "spot_inflation", "spot_inflation01"]
    ]
    base_hicp = hicp_wide[hicp_wide["scenario"] == "Base"][["month", "hicp", "hicp01"]]

    interest_rows = interest_wide.merge(base_inflation, on="month", how="left").merge(
        base_hicp, on="month", how="left"
    )

    base_interest = interest_wide[interest_wide["scenario"] == "Base"].drop(
        columns=["scenario"]
    )
    # `inflation_wide` comes from the static inflation-parameters scenario sheet, not
    # from the template's own scenario list (`interest_wide["scenario"]`, built from
    # `doc["scenarios"]`) -- restrict to scenarios the template actually defines so
    # unrelated parameter-file scenarios don't leak into asset pricing results.
    template_scenarios = interest_wide["scenario"]
    inflation_rows = inflation_wide[
        (inflation_wide["scenario"] != "Base")
        & (inflation_wide["scenario"].isin(template_scenarios))
    ].merge(base_interest, on="month", how="left")
    inflation_rows = inflation_rows.merge(
        hicp_wide[["scenario", "month", "hicp", "hicp01"]],
        on=["scenario", "month"],
        how="left",
    )

    combined = pd.concat([interest_rows, inflation_rows], ignore_index=True)
    combined["month"] = combined["month"].astype(int)
    combined = combined.fillna(0.0)
    return combined


def filter_asset_rates_to_template_scenarios(
    df_asset_rates: pd.DataFrame, scenarios: list[dict]
) -> pd.DataFrame:
    """Keep only the scenario rows the template's own Scenarios editor defines.

    Both interest-curve code paths can smuggle in scenario names the user never
    selected: the EIOPA-published path merges in the static cost-inflation
    scenario sheet (see `build_asset_rates_table`'s own `isin` filter, which only
    covers that merge), and the custom swap-curve path (`run_interest_curves` ->
    `create_rates_scenarios`) runs every row of the static interest-scenario
    library regardless of `doc["scenarios"]`. Trim the final table down to the
    template's own active scenario names so downstream asset pricing (Single
    Asset's "Scenario impact vs Base", etc.) never surfaces a scenario the user
    didn't configure.
    """
    allowed = {s["name"] for s in scenarios if s.get("active", True)}
    if not allowed or "scenario" not in df_asset_rates.columns:
        return df_asset_rates
    return df_asset_rates[df_asset_rates["scenario"].isin(allowed)].reset_index(
        drop=True
    )
