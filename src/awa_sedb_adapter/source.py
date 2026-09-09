from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class SedbCompatibilityError(RuntimeError):
    """Raised when the source database does not expose the required SEDB read schema."""


_REQUIRED_COLUMNS: dict[str, set[str]] = {
    "entities": {"id", "kind", "label", "created_at", "updated_at"},
    "fields": {
        "id", "key", "label", "value_type", "description", "status",
        "created_at", "updated_at", "namespace", "normalized_key",
    },
    "cells": {
        "entity_id", "field_id", "value_json", "source",
        "confidence", "updated_at",
    },
}


class ReadOnlySedbSource:
    """Read-only SQLite boundary for a SEDB v0.4B-compatible database.

    AWA intentionally does not import SEDB write services. SQLite is opened with
    ``mode=ro`` and ``PRAGMA query_only=ON`` so an adapter defect cannot mutate
    canonical SEDB state through this connection.
    """

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path).expanduser().resolve()

    def _uri(self) -> str:
        if not self.database_path.exists():
            raise FileNotFoundError(self.database_path)
        return f"{self.database_path.as_uri()}?mode=ro"

    @contextmanager
    def snapshot(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._uri(), uri=True)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA query_only=ON")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN")
            self.assert_compatible_schema(conn)
            yield conn
        finally:
            try:
                conn.rollback()
            finally:
                conn.close()

    @staticmethod
    def assert_compatible_schema(conn: sqlite3.Connection) -> None:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing_tables = sorted(set(_REQUIRED_COLUMNS) - tables)
        if missing_tables:
            raise SedbCompatibilityError(
                f"SEDB source is missing required tables: {missing_tables}"
            )
        for table, required in _REQUIRED_COLUMNS.items():
            columns = {
                row["name"]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            missing = sorted(required - columns)
            if missing:
                raise SedbCompatibilityError(
                    f"SEDB table {table} is missing required columns: {missing}"
                )
