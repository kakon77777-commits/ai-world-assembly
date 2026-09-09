from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from awa_contracts.validator import validation_errors
from awa_sedb_adapter import (
    ReadOnlySedbSource,
    SedbCompatibilityError,
    SedbProjectionError,
    canonical_json,
    export_entity,
    export_namespace,
)


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "fixtures" / "sedb"


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript((FIXTURES / "v0.4b-minimal.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _semantic_schema() -> dict:
    return json.loads(
        (ROOT / "schemas" / "semantic-game-entity.v0.1.schema.json")
        .read_text(encoding="utf-8")
    )


def test_export_entity_matches_golden_contract_projection(tmp_path: Path) -> None:
    db = tmp_path / "sedb.db"
    _make_db(db)
    payload = export_entity(
        ReadOnlySedbSource(db),
        "species.crystal_filterer",
        namespace="game.alien_lineage",
    )
    assert validation_errors(_semantic_schema(), payload) == []
    assert payload == _load("expected.species.crystal_filterer.json")
    assert payload["semantic_fields"] == {"feeding": "filter", "habitat": "abyss"}


def test_namespace_snapshot_matches_golden_and_is_deterministic(tmp_path: Path) -> None:
    db = tmp_path / "sedb.db"
    _make_db(db)
    source = ReadOnlySedbSource(db)
    one = export_namespace(source, "game.alien_lineage")
    two = export_namespace(source, "game.alien_lineage")
    assert one == two == _load("expected.game.alien_lineage.snapshot.json")
    assert one["entity_count"] == 2
    assert [item["entity_id"] for item in one["entities"]] == [
        "species.crystal_filterer",
        "species.shellback",
    ]
    basis = {key: value for key, value in one.items() if key != "sha256"}
    assert one["sha256"] == hashlib.sha256(
        canonical_json(basis).encode("utf-8")
    ).hexdigest()


def test_namespace_hash_changes_when_projected_semantics_change(tmp_path: Path) -> None:
    db = tmp_path / "sedb.db"
    _make_db(db)
    before = export_namespace(ReadOnlySedbSource(db), "game.alien_lineage")["sha256"]
    conn = sqlite3.connect(db)
    conn.execute(
        "UPDATE cells SET value_json=? WHERE entity_id=? AND field_id=?",
        (json.dumps("reef"), "species.crystal_filterer", "f_habitat"),
    )
    conn.commit()
    conn.close()
    after = export_namespace(ReadOnlySedbSource(db), "game.alien_lineage")["sha256"]
    assert before != after


def test_source_connection_is_actually_read_only(tmp_path: Path) -> None:
    db = tmp_path / "sedb.db"
    _make_db(db)
    with ReadOnlySedbSource(db).snapshot() as conn:
        with pytest.raises(sqlite3.OperationalError):
            conn.execute(
                "INSERT INTO entities VALUES(?,?,?,?,?)",
                ("x", "record", "X", "n", "n"),
            )


def test_incompatible_schema_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "bad.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE entities(id TEXT)")
    conn.commit()
    conn.close()
    with pytest.raises(SedbCompatibilityError):
        with ReadOnlySedbSource(db).snapshot():
            pass


def test_invalid_cell_json_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "sedb.db"
    _make_db(db)
    conn = sqlite3.connect(db)
    conn.execute(
        "UPDATE cells SET value_json='not-json' WHERE entity_id=? AND field_id=?",
        ("species.crystal_filterer", "f_habitat"),
    )
    conn.commit()
    conn.close()
    with pytest.raises(SedbProjectionError):
        export_entity(
            ReadOnlySedbSource(db),
            "species.crystal_filterer",
            namespace="game.alien_lineage",
        )
