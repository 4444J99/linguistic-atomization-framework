from __future__ import annotations

from pathlib import Path
from typing import Any


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}
DOCS_ONLY_KEYS = {
    "description",
    "summary",
    "title",
    "example",
    "examples",
    "externalDocs",
}


def _normalize_schemaish(value: Any) -> Any:
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key in sorted(value):
            if key in DOCS_ONLY_KEYS:
                continue
            normalized[key] = _normalize_schemaish(value[key])
        return normalized
    if isinstance(value, list):
        items = [_normalize_schemaish(item) for item in value]
        if all(isinstance(item, str) for item in items):
            return sorted(items)
        return items
    return value


def _normalize_operation(operation: dict[str, Any]) -> dict[str, Any]:
    return _normalize_schemaish(
        {
            "operationId": operation.get("operationId"),
            "tags": operation.get("tags", []),
            "security": operation.get("security", []),
            "parameters": operation.get("parameters", []),
            "requestBody": operation.get("requestBody"),
            "responses": operation.get("responses", {}),
        }
    )


def normalized_openapi_contract(openapi: dict[str, Any], *, api_prefix: str = "/api/v1/") -> dict[str, Any]:
    paths_out: dict[str, Any] = {}
    for path, path_spec in sorted(openapi.get("paths", {}).items()):
        if not path.startswith(api_prefix):
            continue
        operations: dict[str, Any] = {}
        for method, operation in sorted(path_spec.items()):
            if method not in HTTP_METHODS:
                continue
            operations[method] = _normalize_operation(operation)
        if operations:
            paths_out[path] = operations

    components = openapi.get("components", {})
    return {
        "paths": paths_out,
        "components": _normalize_schemaish(
            {
                "schemas": components.get("schemas", {}),
                "securitySchemes": components.get("securitySchemes", {}),
            }
        ),
    }


def default_snapshot_path(repo_root: Path) -> Path:
    return repo_root / "tests" / "snapshots" / "openapi_contract_normalized.json"
