from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.identity import DefaultAzureCredential

from config import COSMOS_DATABASE, COSMOS_EIOPA_DATABASE, COSMOS_ENDPOINT, COSMOS_KEY

CONTAINER_PARTITION_KEYS: dict[str, str] = {
    "marketData": "/valuation_date",
    "parameters": "/valuation_date",
    "curveRuns": "/id",
    "scenarios": "/curve_set",
    "portfolios": "/id",
    "positions": "/portfolio_id",
    "runs": "/portfolio_id",
    "jobs": "/id",
    "ede-templates": "/id",
    "sampleAssets": "/modelling_class",
    "rfr_spot_rates": "/valuation_date",
    "scr_shocks": "/valuation_date",
    "equity_symmetric_adjustment": "/valuation_date",
    "sw_parameters": "/valuation_date",
    "implied_interest_swap_rates": "/valuation_date",
}

CONTAINER_DATABASES: dict[str, str] = {
    "rfr_spot_rates": COSMOS_EIOPA_DATABASE,
    "scr_shocks": COSMOS_EIOPA_DATABASE,
    "equity_symmetric_adjustment": COSMOS_EIOPA_DATABASE,
    "sw_parameters": COSMOS_EIOPA_DATABASE,
    "implied_interest_swap_rates": COSMOS_EIOPA_DATABASE,
}


def _is_local(endpoint: str) -> bool:
    return "localhost" in endpoint or "127.0.0.1" in endpoint


@lru_cache(maxsize=1)
def get_client() -> CosmosClient:
    if not COSMOS_ENDPOINT:
        raise RuntimeError("COSMOS_ENDPOINT is not set.")
    if COSMOS_KEY:
        return CosmosClient(
            url=COSMOS_ENDPOINT,
            credential=COSMOS_KEY,
            connection_verify=not _is_local(COSMOS_ENDPOINT),
        )
    if _is_local(COSMOS_ENDPOINT):
        raise RuntimeError(
            "COSMOS_KEY is not set. Start the Cosmos DB Emulator and copy its key (see README)."
        )
    return CosmosClient(url=COSMOS_ENDPOINT, credential=DefaultAzureCredential())


@lru_cache(maxsize=4)
def _get_database(database_id: str = COSMOS_DATABASE):
    return get_client().create_database_if_not_exists(id=database_id)


@lru_cache(maxsize=32)
def get_container(name: str):
    partition_key = CONTAINER_PARTITION_KEYS.get(name, "/id")
    database = _get_database(CONTAINER_DATABASES.get(name, COSMOS_DATABASE))
    return database.create_container_if_not_exists(
        id=name, partition_key=PartitionKey(path=partition_key)
    )


def upsert_item(container: str, item: dict) -> dict:
    stop = 1
    return get_container(container).upsert_item(item)


def read_item(container: str, item_id: str, partition_key: str) -> dict | None:
    try:
        return get_container(container).read_item(
            item=item_id, partition_key=partition_key
        )
    except exceptions.CosmosResourceNotFoundError:
        return None


def delete_item(container: str, item_id: str, partition_key: str) -> None:
    try:
        get_container(container).delete_item(item=item_id, partition_key=partition_key)
    except exceptions.CosmosResourceNotFoundError:
        pass


def query_items(
    container: str, query: str = "SELECT * FROM c", parameters: list[dict] | None = None
) -> list[dict]:

    return list(
        get_container(container).query_items(
            query=query, parameters=parameters or [], enable_cross_partition_query=True
        )
    )


def list_versions(collection: str, key: str) -> list[dict[str, Any]]:
    items = query_items(
        collection,
        "SELECT * FROM c WHERE c.valuation_date = @key",
        [{"name": "@key", "value": key}],
    )
    return sorted(items, key=lambda v: v["version"])


def get_active(collection: str, key: str) -> dict[str, Any] | None:
    versions = list_versions(collection, key)
    active = [v for v in versions if v.get("active")]
    if active:
        return max(active, key=lambda v: v["version"])
    return versions[-1] if versions else None


def append_version(
    collection: str, key: str, document: dict[str, Any]
) -> dict[str, Any]:
    versions = list_versions(collection, key)
    next_version = (max((v["version"] for v in versions), default=0)) + 1
    for v in versions:
        if v.get("active"):
            v["active"] = False
            upsert_item(collection, v)
    document = {
        **document,
        "id": f"{key}-v{next_version}",
        "version": next_version,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    upsert_item(collection, document)
    return document


def set_active(collection: str, key: str, version: int) -> dict[str, Any] | None:
    versions = list_versions(collection, key)
    found = None
    for v in versions:
        v["active"] = v["version"] == version
        upsert_item(collection, v)
        if v["active"]:
            found = v
    return found


def save_document(
    collection: str, doc_id: str, document: dict[str, Any]
) -> dict[str, Any]:
    document = {**document, "id": doc_id}
    upsert_item(collection, document)
    return document


def load_document(collection: str, doc_id: str) -> dict[str, Any] | None:
    return read_item(collection, doc_id, doc_id)
