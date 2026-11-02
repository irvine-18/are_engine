from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, BlobServiceClient, generate_blob_sas

from config import STORAGE_ACCOUNT_URL, STORAGE_CONNECTION_STRING

CONTAINERS = ["uploads", "market-data", "curves", "runs", "exports", "reference"]


@lru_cache(maxsize=1)
def get_blob_service_client() -> BlobServiceClient:
    if STORAGE_CONNECTION_STRING:
        return BlobServiceClient.from_connection_string(STORAGE_CONNECTION_STRING)
    if not STORAGE_ACCOUNT_URL:
        raise RuntimeError(
            "Set STORAGE_CONNECTION_STRING (local/Azurite) or STORAGE_ACCOUNT_URL (Azure)."
        )
    return BlobServiceClient(
        account_url=STORAGE_ACCOUNT_URL, credential=DefaultAzureCredential()
    )


_ensured_containers: set[str] = set()


def _ensure_container(container: str) -> None:
    if container in _ensured_containers:
        return
    client = get_blob_service_client()
    try:
        client.create_container(container)
    except (
        Exception
    ):  # noqa: BLE001 -- already exists (ResourceExistsError) or no perms to create
        pass
    _ensured_containers.add(container)


def upload_bytes(
    container: str, blob_path: str, data: bytes, overwrite: bool = True
) -> str:

    _ensure_container(container)
    client = get_blob_service_client().get_blob_client(
        container=container, blob=blob_path
    )
    client.upload_blob(data, overwrite=overwrite)
    return client.url


def download_bytes(container: str, blob_path: str) -> bytes:
    client = get_blob_service_client().get_blob_client(
        container=container, blob=blob_path
    )
    return client.download_blob().readall()


def save_json(
    container: str, blob_path: str, document: dict[str, Any]
) -> dict[str, Any]:

    upload_bytes(
        container, blob_path, json.dumps(document, default=str).encode("utf-8")
    )
    return document


def load_json(container: str, blob_path: str) -> dict[str, Any] | None:
    try:
        return json.loads(download_bytes(container, blob_path).decode("utf-8"))
    except ResourceNotFoundError:
        return None


def generate_download_url(
    container: str, blob_path: str, expiry_minutes: int = 15
) -> str:

    service = get_blob_service_client()
    account_key = getattr(service.credential, "account_key", None)
    if not account_key:
        raise NotImplementedError(
            "generate_download_url only supports account-key auth (local/Azurite) today; "
            "wire up a user-delegation SAS for the Azure (Managed Identity) case."
        )
    client = service.get_blob_client(container=container, blob=blob_path)
    sas = generate_blob_sas(
        account_name=service.account_name,
        container_name=container,
        blob_name=blob_path,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
    )
    return f"{client.url}?{sas}"
