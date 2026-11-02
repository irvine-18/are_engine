import logging
import uuid

import azure.functions as func
import pandas as pd

from api._common import ApiError, handle, json_response, parse_body
from config import get_model_settings
from schemas.curves import CurveRunRequest
from storage import blob
import services.economic_service as economic_service

bp = func.Blueprint()

CONTAINER = "curves"

logger = logging.getLogger(__name__)


def _blob_path(curve_run_id: str) -> str:
    return f"{curve_run_id}/result.json"


def save_curve_run_document(curve_run_id: str, document: dict) -> None:
    """Public so `api/economic_data.py`'s template-level run can reuse the same Blob
    persistence (`curve_run_id` there is the template's own id, a deterministic path
    that each re-run simply overwrites)."""
    blob.save_json(CONTAINER, _blob_path(curve_run_id), document)


def load_curve_run_document(curve_run_id: str) -> dict | None:
    return blob.load_json(CONTAINER, _blob_path(curve_run_id))


@bp.route(route="curves/run", methods=["POST"])
@handle
def run_curves(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, CurveRunRequest)
    settings = get_model_settings()

    interest_data = economic_service.run_interest_curves(
        valuation_date=body.valuation_date,
        interest_input=body.interest,
        parameters=body.parameters,
        df_interest_scenarios=settings.parameters["interest_scenarios"],
    )
    inflation_warning: str | None = None
    try:
        inflation_data = economic_service.run_inflation_curves(
            valuation_date=body.valuation_date,
            inflation_input=body.inflation,
            hicp_observations=body.hicp_observations,
            df_inflation_scenarios=settings.parameters["inflation_scenarios"],
        )
    except Exception as exc:
        logger.warning(
            "curves/run: inflation curves could not be built; continuing without them",
            exc_info=True,
        )
        inflation_data = None
        inflation_warning = (
            f"Inflation curve could not be built, continuing without it: {exc}"
        )

    curve_run_id = str(uuid.uuid4())
    is_interest_set = body.curve_set in ("EIOPA_no_VA", "EIOPA_incl_VA")
    result = (
        economic_service.to_curve_run_result(
            curve_run_id=curve_run_id,
            valuation_date=body.valuation_date,
            curve_set=body.curve_set,
            interest_data=interest_data,
        )
        if is_interest_set
        else None
    )

    if result is None:
        raise ApiError(
            400,
            "unsupported_curve_set",
            f"{body.curve_set} inflation curve view not yet exposed via /curves/run; use /inflation (TODO)",
        )

    if inflation_data is not None:
        result.inflation = economic_service.to_inflation_scenario_curves(
            inflation_data, "Inflation"
        )
        result.cost_inflation = economic_service.to_inflation_scenario_curves(
            inflation_data, "Cost Inflation"
        )
    result.inflation_warning = inflation_warning

    # Persist the asset-ready wide rates table for later /assets/calculate lookups.
    df_asset_rates = economic_service.build_asset_rates_table(
        interest_data, inflation_data
    )
    save_curve_run_document(
        curve_run_id,
        {
            "result": result.model_dump(mode="json"),
            "asset_rates_table": df_asset_rates.to_dict(orient="records"),
        },
    )

    return json_response(result, 201)


def load_asset_rates_table(curve_run_id: str) -> pd.DataFrame:
    doc = load_curve_run_document(curve_run_id)
    if doc is None:
        raise ApiError(404, "not_found", f"No curve run {curve_run_id}")
    return pd.DataFrame(doc["asset_rates_table"])


def load_equity_symmetric_adjustment(curve_run_id: str) -> float | None:
    doc = load_curve_run_document(curve_run_id)
    if doc is None:
        raise ApiError(404, "not_found", f"No curve run {curve_run_id}")
    return doc["result"].get("equity_symmetric_adjustment")
