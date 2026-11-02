import csv
import io
import azure.functions as func

from api._common import ApiError, handle, json_response
from schemas.runs import PositionResult, RunExport, RunSummary
from storage import blob, store

bp = func.Blueprint()
RUNS = "runs"
RUN_RESULTS = "runsResults"


def _get_run_or_404(run_id: str) -> dict:
    run = next((r for r in store.query_items(RUNS) if r.get("id") == run_id), None)
    if run is None:
        raise ApiError(404, "not_found", f"No run {run_id}")
    return run


def _get_results_or_404(run_id: str) -> dict:
    results = store.load_document(RUN_RESULTS, run_id)
    if results is None:
        raise ApiError(404, "not_found", f"No results for run {run_id}")
    return results


@bp.route(route="runs", methods=["GET"])
@handle
def list_runs(req: func.HttpRequest) -> func.HttpResponse:
    portfolio_id = req.params.get("portfolio_id")
    items = store.query_items(RUNS)
    if portfolio_id:
        items = [r for r in items if r.get("portfolio_id") == portfolio_id]
    return json_response(
        sorted(items, key=lambda r: r.get("created_at", ""), reverse=True)
    )


@bp.route(route="runs/{run_id}", methods=["GET"])
@handle
def get_run(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(_get_run_or_404(req.route_params["run_id"]))


@bp.route(route="runs/{run_id}/summary", methods=["GET"])
@handle
def get_run_summary(req: func.HttpRequest) -> func.HttpResponse:
    run = _get_run_or_404(req.route_params["run_id"])
    results = _get_results_or_404(run["id"])
    summary = RunSummary(
        run_id=run["id"],
        portfolio_id=run["portfolio_id"],
        status=run["status"],
        scenarios=results["scenarios"],
        created_at=run["created_at"],
        **results["summary"],
    )
    return json_response(summary)


@bp.route(route="runs/{run_id}/positions", methods=["GET"])
@handle
def get_run_positions(req: func.HttpRequest) -> func.HttpResponse:
    run = _get_run_or_404(req.route_params["run_id"])
    results = _get_results_or_404(run["id"])
    return json_response(
        [PositionResult(**p).model_dump(mode="json") for p in results["positions"]]
    )


@bp.route(route="runs/{run_id}/export", methods=["GET"])
@handle
def export_run(req: func.HttpRequest) -> func.HttpResponse:
    run = _get_run_or_404(req.route_params["run_id"])
    results = _get_results_or_404(run["id"])

    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(results["positions"][0].keys()) if results["positions"] else [],
    )
    writer.writeheader()
    writer.writerows(results["positions"])

    blob_path = f"{run['id']}/export.csv"
    blob.upload_bytes("exports", blob_path, buffer.getvalue().encode("utf-8"))
    download_url = blob.generate_download_url("exports", blob_path)
    return json_response(RunExport(download_url=download_url))
