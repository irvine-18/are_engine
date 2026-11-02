import calendar
import logging
import uuid
from datetime import date, datetime, timedelta, timezone

import azure.functions as func
import pandas as pd

from api._common import ApiError, handle, json_response, parse_body
from api.curves import load_curve_run_document, save_curve_run_document
from config import get_model_settings
from schemas.curves import INTEREST_CURVE_SETS
from schemas.economic_data import (
    EconomicDataTemplate,
    EconomicDataTemplateInput,
    TemplateLastRun,
)
from schemas.market_data import (
    HicpObservation,
    InflationCurveInput,
    InterestRateCurveInput,
    LiquidRatePoint,
)
from schemas.parameters import ParameterSet
from storage import store
import services.economic_service as economic_service

bp = func.Blueprint()

COLLECTION = "ede-templates"

logger = logging.getLogger(__name__)


_FALLBACK_INTEREST_TENORS = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    15,
    20,
    25,
    30,
    40,
    50,
]

EIOPA_RFR_SPOT_RATES_COLLECTION = "rfr_spot_rates"
EIOPA_SCR_SHOCKS_COLLECTION = "scr_shocks"
EIOPA_EQUITY_COLLECTION = "equity_symmetric_adjustment"


@bp.route(route="economic-data/get-templates", methods=["GET"])
@handle
def get_templates(req: func.HttpRequest) -> func.HttpResponse:
    items = store.query_items(COLLECTION)
    templates = [EconomicDataTemplate.model_validate(i) for i in items]
    templates.sort(key=lambda t: t.created_at)
    return json_response([t.model_dump(mode="json", by_alias=True) for t in templates])


@bp.route(route="economic-data/create-ede-template", methods=["POST"])
@handle
def create_ede_template(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, EconomicDataTemplateInput)
    template = EconomicDataTemplate(
        id=f"template-{uuid.uuid4()}",
        created_at=datetime.now(timezone.utc).isoformat(),
        **body.model_dump(),
    )
    store.upsert_item(COLLECTION, template.model_dump(mode="json", by_alias=True))
    return json_response(template.model_dump(mode="json", by_alias=True), 201)


@bp.route(route="economic-data/edit-ede-template/{template_id}", methods=["PUT"])
@handle
def edit_ede_template(req: func.HttpRequest) -> func.HttpResponse:
    template_id = req.route_params["template_id"]
    existing = store.read_item(COLLECTION, template_id, template_id)
    if existing is None:
        raise ApiError(404, "not_found", f"No template {template_id}")
    body = parse_body(req, EconomicDataTemplateInput)
    template = EconomicDataTemplate(
        id=template_id,
        created_at=existing.get("createdAt") or existing.get("created_at"),
        **body.model_dump(),
    )
    store.upsert_item(COLLECTION, template.model_dump(mode="json", by_alias=True))
    return json_response(template.model_dump(mode="json", by_alias=True))


@bp.route(route="economic-data/delete-ede-template/{template_id}", methods=["DELETE"])
@handle
def delete_ede_template(req: func.HttpRequest) -> func.HttpResponse:
    template_id = req.route_params["template_id"]
    existing = store.read_item(COLLECTION, template_id, template_id)
    if existing is None:
        raise ApiError(404, "not_found", f"No template {template_id}")
    store.delete_item(COLLECTION, template_id, template_id)
    return func.HttpResponse(status_code=204)


def _liquid_points(points: list[dict]) -> list[LiquidRatePoint]:
    return [
        LiquidRatePoint(
            tenor_years=p["tenor_years"],
            rate=p["rate"],
            liquid=p.get("liquid", True),
            source=p.get("source"),
        )
        for p in points
    ]


def _eiopa_month_end(publication_month: str) -> str:
    year, month = (int(p) for p in publication_month.split("-"))
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-{last_day:02d}"


def _eiopa_published_base_curves(publication_month: str) -> dict[str, pd.Series] | None:
    valuation_date = _eiopa_month_end(publication_month)
    curves: dict[str, pd.Series] = {}
    for curve_set in INTEREST_CURVE_SETS:
        doc = store.read_item(
            EIOPA_RFR_SPOT_RATES_COLLECTION,
            f"{valuation_date}__{curve_set}__Base",
            valuation_date,
        )
        if doc is None:
            continue
        curves[curve_set] = pd.Series(
            {p["maturity"]: p["rate"] for p in doc["points"]}
        ).sort_index()
    return curves or None


def _eiopa_scr_shocks(publication_month: str) -> pd.DataFrame | None:
    valuation_date = _eiopa_month_end(publication_month)
    doc = store.read_item(EIOPA_SCR_SHOCKS_COLLECTION, valuation_date, valuation_date)
    return pd.DataFrame(doc["points"]) if doc else None


def _eiopa_equity_adjustment(publication_month: str) -> float | None:
    valuation_date = _eiopa_month_end(publication_month)
    doc = store.read_item(EIOPA_EQUITY_COLLECTION, valuation_date, valuation_date)
    return doc.get("symmetric_adjustment") if doc else None


def _interest_input(template: dict) -> InterestRateCurveInput:
    interest = template.get("interest", {})
    points = interest.get("liquidPoints") or []
    if not points:
        points = [
            {"tenor_years": t, "rate": 0.025, "liquid": t <= 20, "source": "manual"}
            for t in _FALLBACK_INTEREST_TENORS
        ]
    return InterestRateCurveInput(points=_liquid_points(points))


def _inflation_input(template: dict) -> InflationCurveInput | None:
    section = template.get("inflation", {})
    points = section.get("liquidPoints") or []
    if not section.get("included") or not points:
        return None
    return InflationCurveInput(points=_liquid_points(points))


def _hicp_observations(template: dict, valuation_date: date) -> list[HicpObservation]:

    section = template.get("hicp", {})
    observation_date = section.get("latestObservationDate")
    if (
        section.get("included")
        and observation_date
        and section.get("latestObservationValue") is not None
        and date.fromisoformat(observation_date) < valuation_date
    ):
        return [
            HicpObservation(
                month=observation_date, hicp=section["latestObservationValue"]
            )
        ]

    fallback_month = (valuation_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    return [HicpObservation(month=fallback_month, hicp=125.3)]


def _hicp_observation_warning(template: dict, valuation_date: date) -> str | None:

    section = template.get("hicp", {})
    observation_date = section.get("latestObservationDate")
    if (
        section.get("included")
        and observation_date
        and section.get("latestObservationValue") is not None
        and date.fromisoformat(observation_date) >= valuation_date
    ):
        return (
            f"HICP latest observation date ({observation_date}) must be strictly before the valuation date "
            f"({valuation_date.isoformat()}) -- used a placeholder HICP observation instead."
        )
    return None


@bp.route(route="economic-data/run-ede-template/{template_id}", methods=["POST"])
@handle
def run_ede_template(req: func.HttpRequest) -> func.HttpResponse:

    template_id = req.route_params["template_id"]
    doc = store.read_item(COLLECTION, template_id, template_id)
    if doc is None:
        raise ApiError(404, "not_found", f"No template {template_id}")

    valuation_date = date.fromisoformat(doc["valuationDate"])
    settings = get_model_settings()

    interest_section = doc.get("interest", {})
    eiopa_base_curves = None
    if interest_section.get("sourceMode") == "eiopa_published" and interest_section.get(
        "eiopaPublicationMonth"
    ):
        eiopa_base_curves = _eiopa_published_base_curves(
            interest_section["eiopaPublicationMonth"]
        )

    if eiopa_base_curves:

        interest_data = economic_service.run_eiopa_published_interest_curves(
            valuation_date=valuation_date,
            base_curves=eiopa_base_curves,
            scr_shock_bp=_eiopa_scr_shocks(interest_section["eiopaPublicationMonth"]),
            scenarios=doc.get("scenarios", []),
        )
    else:
        valuation_date_str = valuation_date.isoformat()
        active_parameters = store.get_active("parameters", valuation_date_str)
        parameters = (
            ParameterSet.model_validate(active_parameters)
            if active_parameters
            else ParameterSet(valuation_date=valuation_date)
        )
        interest_sw_parameters = interest_section.get("swParameters")
        if interest_sw_parameters:
            parameters = economic_service.apply_interest_sw_parameters(
                parameters, interest_sw_parameters
            )
        interest_scr_shocks = interest_section.get("scrShocks")
        if interest_scr_shocks:
            parameters = economic_service.apply_interest_scr_shocks(
                parameters, interest_scr_shocks
            )
        interest_data = economic_service.run_interest_curves(
            valuation_date=valuation_date,
            interest_input=_interest_input(doc),
            parameters=parameters,
            df_interest_scenarios=settings.parameters["interest_scenarios"],
        )

    inflation_input = _inflation_input(doc)
    inflation_data = None
    inflation_warning: str | None = None
    if inflation_input is None and doc.get("inflation", {}).get("included"):

        inflation_warning = "Inflation section is included but has no liquid points entered -- this run has no real inflation curve (hicp/spot_inflation are flat 0)."
    elif inflation_input is not None:
        df_inflation_scenarios = settings.parameters["inflation_scenarios"]
        inflation_sw_parameters = doc.get("inflation", {}).get("swParameters")
        if inflation_sw_parameters:
            df_inflation_scenarios = (
                economic_service.apply_cost_inflation_sw_parameters(
                    df_inflation_scenarios, inflation_sw_parameters
                )
            )
        inflation_warning = _hicp_observation_warning(doc, valuation_date)
        try:
            inflation_data = economic_service.run_inflation_curves(
                valuation_date=valuation_date,
                inflation_input=inflation_input,
                hicp_observations=_hicp_observations(doc, valuation_date),
                df_inflation_scenarios=df_inflation_scenarios,
            )
        except Exception as exc:

            logger.warning(
                "run-ede-template: inflation curves could not be built; continuing without them",
                exc_info=True,
            )
            inflation_warning = (
                f"Inflation curve could not be built, continuing without it: {exc}"
            )

    result = economic_service.to_template_curve_run_result(
        template_id=template_id,
        valuation_date=valuation_date,
        interest_data=interest_data,
        inflation_data=inflation_data,
        inflation_warning=inflation_warning,
    )

    equity = doc.get("equity", {})
    if equity.get("symmetricAdjustmentSourceMode") == "eiopa_published" and equity.get(
        "eiopaPublicationMonth"
    ):
        result.equity_symmetric_adjustment = _eiopa_equity_adjustment(
            equity["eiopaPublicationMonth"]
        )

    df_asset_rates = economic_service.build_asset_rates_table(
        interest_data, inflation_data
    )
    df_asset_rates = economic_service.filter_asset_rates_to_template_scenarios(
        df_asset_rates, doc.get("scenarios", [])
    )
    save_curve_run_document(
        template_id,
        {
            "result": result.model_dump(mode="json"),
            "asset_rates_table": df_asset_rates.to_dict(orient="records"),
        },
    )

    doc["lastRun"] = TemplateLastRun(
        ran_at=datetime.now(timezone.utc).isoformat(),
        status="success",
        curve_run_id=template_id,
        kpis=result.kpis,
        equity_symmetric_adjustment=result.equity_symmetric_adjustment,
        inflation_warning=result.inflation_warning,
    ).model_dump(mode="json", by_alias=True)
    store.upsert_item(COLLECTION, doc)

    return json_response(result, 201)


@bp.route(route="economic-data/run-ede-template/{template_id}", methods=["GET"])
@handle
def get_ede_template_run(req: func.HttpRequest) -> func.HttpResponse:
    template_id = req.route_params["template_id"]
    doc = load_curve_run_document(template_id)
    if doc is None:
        raise ApiError(404, "not_found", f"No run for template {template_id}")
    return json_response(doc["result"])
