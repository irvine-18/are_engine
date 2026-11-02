from __future__ import annotations

from typing import Any

from . import cosmos


def list_versions(collection: str, key: str) -> list[dict[str, Any]]:
    return cosmos.list_versions(collection, key)


def get_active(collection: str, key: str) -> dict[str, Any] | None:
    return cosmos.get_active(collection, key)


def append_version(
    collection: str, key: str, document: dict[str, Any]
) -> dict[str, Any]:
    return cosmos.append_version(collection, key, document)


def set_active(collection: str, key: str, version: int) -> dict[str, Any] | None:
    return cosmos.set_active(collection, key, version)


def save_document(
    collection: str, doc_id: str, document: dict[str, Any]
) -> dict[str, Any]:
    return cosmos.save_document(collection, doc_id, document)


def load_document(collection: str, doc_id: str) -> dict[str, Any] | None:
    return cosmos.load_document(collection, doc_id)


def upsert_item(container: str, item: dict[str, Any]) -> dict[str, Any]:
    return cosmos.upsert_item(container, item)


def read_item(
    container: str, item_id: str, partition_key: str | None = None
) -> dict[str, Any] | None:
    return cosmos.read_item(container, item_id, partition_key)


def delete_item(container: str, item_id: str, partition_key: str | None = None) -> None:
    cosmos.delete_item(container, item_id, partition_key)


def query_items(
    container: str, query: str = "SELECT * FROM c", parameters: list[dict] | None = None
) -> list[dict[str, Any]]:
    return cosmos.query_items(container, query, parameters)
