from __future__ import annotations

import hashlib
import json
from typing import Any
from urllib.parse import quote

from .source import ReadOnlySedbSource


class SedbProjectionError(RuntimeError):
    """Raised when SEDB rows cannot be projected safely."""


ACTIVE_FIELD_STATUSES = ("active", "converged")
PROJECTION_VERSION = "v0.1"


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise SedbProjectionError("projection contains non-canonical JSON data") from exc


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _load_cell_value(raw: str, *, entity_id: str, field_key: str) -> Any:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SedbProjectionError(
            f"invalid value_json for entity={entity_id} field={field_key}"
        ) from exc


def _entity_from_conn(conn, entity_id: str, namespace: str) -> dict[str, Any]:
    namespace = str(namespace).strip()
    if not namespace:
        raise ValueError("namespace is required")
    entity = conn.execute(
        "SELECT id,kind,label FROM entities WHERE id=?",
        (str(entity_id),),
    ).fetchone()
    if entity is None:
        raise KeyError(f"SEDB entity not found: {entity_id}")

    rows = conn.execute(
        """
        SELECT f.key, c.value_json
        FROM cells c
        JOIN fields f ON f.id=c.field_id
        WHERE c.entity_id=?
          AND f.namespace=?
          AND f.status IN (?,?)
        ORDER BY f.key, f.id
        """,
        (entity["id"], namespace, *ACTIVE_FIELD_STATUSES),
    ).fetchall()
    fields = {
        row["key"]: _load_cell_value(
            row["value_json"], entity_id=entity["id"], field_key=row["key"]
        )
        for row in rows
    }
    basis = {
        "contract": "semantic-game-entity.v0.1",
        "entity_id": entity["id"],
        "kind": entity["kind"],
        "namespace": namespace,
        "label": entity["label"],
        "semantic_fields": fields,
        "version": PROJECTION_VERSION,
    }
    digest = sha256_json(basis)
    encoded_entity = quote(entity["id"], safe="")
    encoded_namespace = quote(namespace, safe="")
    return {
        **basis,
        "provenance_ref": (
            f"sedb://entity/{encoded_entity}/namespace/{encoded_namespace}"
            f"?sha256={digest}"
        ),
    }


def export_entity(
    source: ReadOnlySedbSource,
    entity_id: str,
    *,
    namespace: str = "global",
) -> dict[str, Any]:
    with source.snapshot() as conn:
        return _entity_from_conn(conn, entity_id, namespace)


def export_namespace(
    source: ReadOnlySedbSource,
    namespace: str,
) -> dict[str, Any]:
    namespace = str(namespace).strip()
    if not namespace:
        raise ValueError("namespace is required")
    with source.snapshot() as conn:
        entity_rows = conn.execute(
            """
            SELECT DISTINCT e.id
            FROM entities e
            JOIN cells c ON c.entity_id=e.id
            JOIN fields f ON f.id=c.field_id
            WHERE f.namespace=?
              AND f.status IN (?,?)
            ORDER BY e.id
            """,
            (namespace, *ACTIVE_FIELD_STATUSES),
        ).fetchall()
        entities = [
            _entity_from_conn(conn, row["id"], namespace)
            for row in entity_rows
        ]

    basis = {
        "contract": "sedb-namespace-snapshot.v0.1",
        "source": "SEDB",
        "namespace": namespace,
        "projection_version": PROJECTION_VERSION,
        "entity_count": len(entities),
        "entities": entities,
    }
    return {**basis, "sha256": sha256_json(basis)}
