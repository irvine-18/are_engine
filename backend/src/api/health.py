
import json
import logging
import os
import platform
import re
import uuid
from datetime import datetime, timezone
from itertools import islice

import azure.functions as func
from azure.storage.blob import ContentSettings

from config import COSMOS_DATABASE, COSMOS_EIOPA_DATABASE
from storage import blob, cosmos

bp = func.Blueprint()

logger = logging.getLogger(__name__)

APP_CONTAINER = "ede-templates"  # a container that lives in COSMOS_DATABASE
EIOPA_CONTAINER = "rfr_spot_rates"  # a container that lives in COSMOS_EIOPA_DATABASE
ITEMS_CONTAINER = "items"
UPLOADS_CONTAINER = "uploads"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(body, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(body, default=str), status_code=status,
                             mimetype="application/json")


def _check(fn) -> dict:
    try:
        return {"ok": True, **(fn() or {})}
    except Exception as exc:  # report, don't crash: this is a diagnostics endpoint
        logging.exception("Health check failed")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:500]}

@bp.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    def cosmos_check():
        props = cosmos.get_container(APP_CONTAINER).read()
        return {"database": COSMOS_DATABASE, "container": props["id"]}

    def cosmos_eiopa_check():
        props = cosmos.get_container(EIOPA_CONTAINER).read()
        return {"database": COSMOS_EIOPA_DATABASE, "container": props["id"]}

    def storage_check():
        container = blob.get_blob_service_client().get_container_client(UPLOADS_CONTAINER)
        list(islice(container.list_blobs(), 1))  # proves data-plane read access
        return {"container": container.container_name}

    checks = {
        "functions": {"ok": True, "python": platform.python_version()},
        "cosmos": _check(cosmos_check),
        "cosmos_eiopa": _check(cosmos_eiopa_check),
        "storage": _check(storage_check),
    }
    ok = all(c["ok"] for c in checks.values())
    return _json({"ok": ok, "checks": checks, "time": _now()}, 200 if ok else 503)


@bp.route(route="items", methods=["GET", "POST"])
def items(req: func.HttpRequest) -> func.HttpResponse:
    container = cosmos.get_container(ITEMS_CONTAINER)

    if req.method == "POST":
        try:
            data = req.get_json()
        except ValueError:
            return _json({"error": "Body must be JSON"}, 400)
        text = str((data or {}).get("text", "")).strip()
        if not text:
            return _json({"error": "'text' is required"}, 400)
        item = {"id": str(uuid.uuid4()), "text": text[:500], "createdAt": _now()}
        container.create_item(item)
        return _json(item, 201)

    rows = container.query_items(
        "SELECT TOP 20 c.id, c.text, c.createdAt FROM c ORDER BY c._ts DESC",
        enable_cross_partition_query=True,
    )
    return _json(list(rows))


@bp.route(route="files", methods=["GET", "POST"])
def files(req: func.HttpRequest) -> func.HttpResponse:
    container = blob.get_blob_service_client().get_container_client(UPLOADS_CONTAINER)

    if req.method == "POST":
        body = req.get_body()
        if not body:
            return _json({"error": "Empty body"}, 400)
        raw_name = os.path.basename(req.params.get("name") or "upload.bin")
        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", raw_name)[:100] or "upload.bin"
        blob_name = f"{uuid.uuid4().hex[:8]}-{safe_name}"
        content_type = req.headers.get("content-type") or "application/octet-stream"
        container.upload_blob(blob_name, body, overwrite=False,
                              content_settings=ContentSettings(content_type=content_type))
        return _json({"name": blob_name, "size": len(body)}, 201)

    blobs = [
        {"name": b.name, "size": b.size, "lastModified": b.last_modified}
        for b in islice(container.list_blobs(), 50)
    ]
    return _json(blobs)
