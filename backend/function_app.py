"""Azure Functions backend (Python v2 programming model).

Endpoints (all under /api, protected by a function key):
  GET  /api/health          checks Functions, Cosmos DB and Blob Storage
  GET  /api/items           last 20 items from Cosmos DB
  POST /api/items           {"text": "..."} -> creates an item
  GET  /api/files           lists blobs in the uploads container
  POST /api/files?name=x    raw request body -> uploaded as a blob

Auth to Cosmos and Storage uses DefaultAzureCredential: the Function App's managed
identity in Azure, and your `az login` identity when running locally.
"""

import json
import logging
import os
import platform
import re
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from itertools import islice

import azure.functions as func
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


# ---------- clients (created once per worker, reused across invocations) ----------

@lru_cache
def _credential() -> DefaultAzureCredential:
    return DefaultAzureCredential()


@lru_cache
def _cosmos_container():
    client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=_credential())
    db = client.get_database_client(os.environ.get("COSMOS_DATABASE", "appdb"))
    return db.get_container_client(os.environ.get("COSMOS_CONTAINER", "items"))


@lru_cache
def _blob_container():
    service = BlobServiceClient(os.environ["STORAGE_BLOB_URL"], credential=_credential())
    return service.get_container_client(os.environ.get("STORAGE_CONTAINER", "uploads"))


# ---------- helpers ----------

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


# ---------- endpoints ----------

@app.route(route="health", methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    def cosmos():
        props = _cosmos_container().read()
        return {"database": os.environ.get("COSMOS_DATABASE", "appdb"), "container": props["id"]}

    def storage():
        container = _blob_container()
        list(islice(container.list_blobs(), 1))  # proves data-plane read access
        return {"container": container.container_name}

    checks = {
        "functions": {"ok": True, "python": platform.python_version()},
        "cosmos": _check(cosmos),
        "storage": _check(storage),
    }
    ok = all(c["ok"] for c in checks.values())
    return _json({"ok": ok, "checks": checks, "time": _now()}, 200 if ok else 503)


@app.route(route="items", methods=["GET", "POST"])
def items(req: func.HttpRequest) -> func.HttpResponse:
    container = _cosmos_container()

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


@app.route(route="files", methods=["GET", "POST"])
def files(req: func.HttpRequest) -> func.HttpResponse:
    container = _blob_container()

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
