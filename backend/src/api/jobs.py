from datetime import datetime, timezone

import azure.functions as func

from api._common import ApiError, handle, json_response
from schemas.runs import Job
from storage import store

bp = func.Blueprint()
JOBS = "jobs"


def _get_job_or_404(job_id: str) -> dict:
    doc = store.read_item(JOBS, job_id, job_id)
    if doc is None:
        raise ApiError(404, "not_found", f"No job {job_id}")
    return doc


@bp.route(route="jobs/{job_id}", methods=["GET"])
@handle
def get_job(req: func.HttpRequest) -> func.HttpResponse:
    return json_response(Job(**_get_job_or_404(req.route_params["job_id"])))


@bp.route(route="jobs/{job_id}/cancel", methods=["POST"])
@handle
def cancel_job(req: func.HttpRequest) -> func.HttpResponse:
    job = _get_job_or_404(req.route_params["job_id"])
    if job["status"] in ("queued", "running"):
        job["status"] = "cancelled"
        job["updated_at"] = datetime.now(timezone.utc).isoformat()
        store.upsert_item(JOBS, job)

    return json_response(Job(**job))
