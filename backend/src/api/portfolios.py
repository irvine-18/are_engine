import uuid
from datetime import date, datetime, timezone

import azure.functions as func
import pandas as pd

from api._common import ApiError, handle, json_response, parse_body
from api.curves import load_curve_run_document
from config import get_model_settings
from schemas.parameters import ParameterSet
from schemas.portfolios import (
    Portfolio,
    PortfolioCreate,
    PortfolioRename,
    Position,
    PositionCreate,
    TptImportResult,
)
from schemas.runs import Job, Run, RunCreate, RunCreated
import services.asset_service as asset_service
import services.portfolio_service as portfolio_service
import services.run_service as run_service
from storage import blob, store

bp = func.Blueprint()
PORTFOLIOS = "portfolios"
POSITIONS = "positions"
RUNS = "runs"
JOBS = "jobs"


def _get_portfolio_or_404(portfolio_id: str) -> dict:
    doc = store.read_item(PORTFOLIOS, portfolio_id, portfolio_id)
    if doc is None:
        raise ApiError(404, "not_found", f"No portfolio {portfolio_id}")
    return doc


def _positions_for(portfolio_id: str) -> list[dict]:
    return [
        p for p in store.query_items(POSITIONS) if p.get("portfolio_id") == portfolio_id
    ]


def _recompute_totals(portfolio_id: str) -> dict:
    positions = _positions_for(portfolio_id)
    count, total_mv = portfolio_service.totals(positions)
    portfolio = _get_portfolio_or_404(portfolio_id)
    portfolio["position_count"] = count
    portfolio["total_market_value"] = total_mv
    store.upsert_item(PORTFOLIOS, portfolio)
    return portfolio


@bp.route(route="portfolios", methods=["GET"])
@handle
def list_portfolios(req: func.HttpRequest) -> func.HttpResponse:
    items = sorted(store.query_items(PORTFOLIOS), key=lambda p: p.get("created_at", ""))
    return json_response(items)


@bp.route(route="portfolios", methods=["POST"])
@handle
def create_portfolio(req: func.HttpRequest) -> func.HttpResponse:
    body = parse_body(req, PortfolioCreate)
    portfolio = Portfolio(
        id=str(uuid.uuid4()),
        name=body.name,
        currency=body.currency,
        created_at=datetime.now(timezone.utc),
    )
    store.upsert_item(PORTFOLIOS, portfolio.model_dump(mode="json"))
    return json_response(portfolio, 201)


@bp.route(route="portfolios/{portfolio_id}", methods=["GET"])
@handle
def get_portfolio(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(_get_portfolio_or_404(req.route_params["portfolio_id"]))


@bp.route(route="portfolios/{portfolio_id}", methods=["PUT"])
@handle
def rename_portfolio(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.route_params["portfolio_id"]
    body = parse_body(req, PortfolioRename)
    portfolio = _get_portfolio_or_404(portfolio_id)
    portfolio["name"] = body.name
    store.upsert_item(PORTFOLIOS, portfolio)
    return json_response(portfolio)


@bp.route(route="portfolios/{portfolio_id}", methods=["DELETE"])
@handle
def delete_portfolio(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.route_params["portfolio_id"]
    _get_portfolio_or_404(portfolio_id)
    for position in _positions_for(portfolio_id):
        store.delete_item(POSITIONS, position["id"], portfolio_id)
    store.delete_item(PORTFOLIOS, portfolio_id, portfolio_id)
    return func.HttpResponse(status_code=204)


@bp.route(route="portfolios/{portfolio_id}/duplicate", methods=["POST"])
@handle
def duplicate_portfolio(req: func.HttpRequest) -> func.HttpResponse:
    source = _get_portfolio_or_404(req.route_params["portfolio_id"])
    new_id = str(uuid.uuid4())
    copy = Portfolio(
        id=new_id,
        name=f"{source['name']} (copy)",
        currency=source.get("currency", "EUR"),
        created_at=datetime.now(timezone.utc),
    )
    store.upsert_item(PORTFOLIOS, copy.model_dump(mode="json"))
    for position in _positions_for(source["id"]):
        new_position = {
            **position,
            "id": portfolio_service.new_position_id(),
            "portfolio_id": new_id,
        }
        store.upsert_item(POSITIONS, new_position)
    return json_response(_recompute_totals(new_id), 201)


@bp.route(route="portfolios/{portfolio_id}/positions", methods=["GET"])
@handle
def list_positions(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.route_params["portfolio_id"]
    _get_portfolio_or_404(portfolio_id)
    return json_response(_positions_for(portfolio_id))


@bp.route(route="portfolios/{portfolio_id}/positions", methods=["POST"])
@handle
def add_position(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.route_params["portfolio_id"]
    _get_portfolio_or_404(portfolio_id)
    body = parse_body(req, PositionCreate)
    position = portfolio_service.position_from_create(portfolio_id, body)
    store.upsert_item(POSITIONS, position.model_dump(mode="json"))
    _recompute_totals(portfolio_id)
    return json_response(position, 201)


@bp.route(route="portfolios/{portfolio_id}/positions/{position_id}", methods=["DELETE"])
@handle
def remove_position(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.route_params["portfolio_id"]
    position_id = req.route_params["position_id"]
    _get_portfolio_or_404(portfolio_id)
    store.delete_item(POSITIONS, position_id, portfolio_id)
    _recompute_totals(portfolio_id)
    return func.HttpResponse(status_code=204)


@bp.route(route="portfolios/{portfolio_id}/tpt", methods=["POST"])
@handle
def upload_tpt(req: func.HttpRequest) -> func.HttpResponse:

    portfolio_id = req.route_params["portfolio_id"]
    _get_portfolio_or_404(portfolio_id)

    file_storage = req.files.get("file") if req.files else None
    if file_storage is None:
        raise ApiError(
            400, "missing_file", "No file was sent (expected multipart field 'file')."
        )
    filename = file_storage.filename or "upload.xlsx"
    data = file_storage.read()

    upload_id = str(uuid.uuid4())
    valuation_date = (
        req.form.get("valuation_date", "unknown") if req.form else "unknown"
    )
    blob_path = f"tpt/{valuation_date}/{upload_id}/{filename}"
    blob.upload_bytes("uploads", blob_path, data)

    positions, validation_issues = portfolio_service.parse_positions_file(
        data, filename, portfolio_id
    )
    if positions:
        for existing in _positions_for(portfolio_id):
            store.delete_item(POSITIONS, existing["id"], portfolio_id)
        for position in positions:
            store.upsert_item(POSITIONS, position.model_dump(mode="json"))
        _recompute_totals(portfolio_id)

    result = TptImportResult(
        portfolio_id=portfolio_id,
        upload_id=upload_id,
        blob_path=blob_path,
        filename=filename,
        positions_imported=len(positions),
        positions=positions,
        validation_issues=validation_issues,
    )
    return json_response(result, 201)


@bp.route(route="portfolios/{portfolio_id}/runs", methods=["POST"])
@handle
def start_run(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.route_params["portfolio_id"]
    _get_portfolio_or_404(portfolio_id)
    body = parse_body(req, RunCreate)
    positions = _positions_for(portfolio_id)
    if not positions:
        raise ApiError(400, "no_positions", "This portfolio has no positions to run.")
    if not body.curve_run_id:
        raise ApiError(
            422,
            "no_curve_run",
            "No economic data template run to price against -- select an active template with a run, or run it, first.",
        )

    curve_run_doc = load_curve_run_document(body.curve_run_id)
    if curve_run_doc is None:
        raise ApiError(404, "not_found", f"No curve run {body.curve_run_id}")
    df_rates = pd.DataFrame(curve_run_doc["asset_rates_table"])
    valuation_date = date.fromisoformat(curve_run_doc["result"]["valuation_date"])
    equity_symmetric_adjustment = curve_run_doc["result"].get(
        "equity_symmetric_adjustment"
    )
    active_parameters = store.get_active("parameters", valuation_date.isoformat())
    parameters = (
        ParameterSet.model_validate(active_parameters)
        if active_parameters
        else ParameterSet(valuation_date=valuation_date)
    )

    run_id = str(uuid.uuid4())
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    scenarios = ["Base"]

    run = Run(
        id=run_id,
        portfolio_id=portfolio_id,
        job_id=job_id,
        scenarios=scenarios,
        status="succeeded",
        created_at=now,
    )
    store.upsert_item(RUNS, run.model_dump(mode="json"))

    settings = get_model_settings()
    position_results, errors = run_service.price_portfolio(
        positions=positions,
        valuation_date=valuation_date,
        df_rates=df_rates,
        df_modelling_properties=settings.parameters["modelling_properties"],
        df_cqs_rating_mapping=asset_service.build_cqs_mapping_df(
            parameters, settings.parameters["cqs_rating_mapping"]
        ),
        df_spread_risk_coefficients=asset_service.build_spread_coefficients_df(
            parameters, settings.parameters["spread_risk_coefficients"]
        ),
        df_eiopa_equity_adjustment=asset_service.build_equity_adjustment_df(
            parameters, equity_symmetric_adjustment
        ),
        scenarios=scenarios,
    )
    summary = run_service.summarise(
        position_results, positions_total=len(positions), positions_errored=len(errors)
    )
    store.save_document(
        f"{RUNS}Results",
        run_id,
        {
            "positions": position_results,
            "summary": summary,
            "scenarios": scenarios,
            "errors": errors,
        },
    )

    job = Job(
        id=job_id,
        run_id=run_id,
        portfolio_id=portfolio_id,
        status="succeeded",
        positions_total=len(positions),
        positions_done=len(positions),
        error_count=len(errors),
        errors=errors,
        created_at=now,
        updated_at=now,
    )
    store.upsert_item(JOBS, job.model_dump(mode="json"))

    portfolio = _get_portfolio_or_404(portfolio_id)
    portfolio["last_run_at"] = now.isoformat()
    store.upsert_item(PORTFOLIOS, portfolio)

    return json_response(RunCreated(job_id=job_id, run_id=run_id), 202)
