from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from awa_alien_lineage import AlienLineageBuildError, build_spawn_runtime_authoring_files
from awa_alien_lineage.build import COMPILABLEWORLD_ENTITY_TRANSACTION_COMMIT

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
RUNTIME = FIX / "alien_lineage_runtime"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def values():
    return (
        load(FIX / "sedb" / "expected.game.alien_lineage.snapshot.json"),
        load(FIX / "csc_ocm" / "expected.alien_lineage.composition-receipt.json"),
        load(FIX / "compilableworld_intake" / "asset-graph.resolved.json"),
        load(RUNTIME / "alien_lineage.intake-plan.json"),
        load(RUNTIME / "runtime-slice.json"),
        load(RUNTIME / "spawn-profile.json"),
    )


def test_spawn_authoring_is_deterministic_and_declares_two_modules() -> None:
    files1, receipt1 = build_spawn_runtime_authoring_files(*values(), root=ROOT)
    files2, receipt2 = build_spawn_runtime_authoring_files(*values(), root=ROOT)
    assert files1 == files2
    assert receipt1 == receipt2
    world = json.loads(files1["world.json"])
    assert world["runtime_extensions"] == [
        {"entrypoint": "awa_alien_lineage.runtime:AlienLineageModule", "module_id": "alien_lineage.runtime", "version": "0.1.0"},
        {"entrypoint": "awa_alien_lineage.spawn:AlienLineageSpawnModule", "module_id": "alien_lineage.spawn", "version": "0.1.0"},
    ]
    assert world["alien_lineage_spawn"]["kernel_capability"] == "entity_transaction/v0.1"
    assert receipt1["contract"] == "alien-lineage-spawn-receipt.v0.1"
    assert receipt1["compatibility_commit"] == COMPILABLEWORLD_ENTITY_TRANSACTION_COMMIT


def test_spawn_profile_uses_reviewed_nonconflicting_runtime_ids() -> None:
    *base, profile = values()
    assert profile["parent_entity_id"] == "creature.crystal-filterer.001"
    assert profile["egg"]["entity_id"] == "egg.crystal-filterer.001"
    assert profile["child"]["entity_id"] == "creature.crystal-filterer.child.001"
    assert len({profile["parent_entity_id"], profile["egg"]["entity_id"], profile["child"]["entity_id"]}) == 3


def test_spawn_profile_rejects_authored_entity_id_conflict() -> None:
    semantic, composition, graph, plan, slice_doc, profile = values()
    profile = deepcopy(profile)
    profile["egg"]["entity_id"] = profile["parent_entity_id"]
    with pytest.raises(AlienLineageBuildError, match="must be distinct|conflicts"):
        build_spawn_runtime_authoring_files(semantic, composition, graph, plan, slice_doc, profile, root=ROOT)


def test_spawn_assertions_target_real_egg_and_child_entities() -> None:
    sidecar = load(RUNTIME / "full-cycle.spawn-assertions.json")
    assert sidecar["contract"] == "alien-lineage-spawn-assertions.v0.1"
    ids = {entry["entity_id"] for entry in sidecar["entities"]}
    assert ids == {"egg.crystal-filterer.001", "creature.crystal-filterer.child.001"}
    child = next(entry for entry in sidecar["entities"] if entry["entity_id"].startswith("creature."))
    assert {item["key"] for item in child["state"]} >= {"stage", "species_ref", "parent_id", "energy", "growth_points"}


def test_spawn_module_source_never_calls_registry_add_or_remove() -> None:
    source = (ROOT / "src" / "awa_alien_lineage" / "spawn.py").read_text(encoding="utf-8")
    assert "registry.add(" not in source
    assert "registry.remove(" not in source
    assert "EntityDelta(" in source
    assert "entity_transaction/v0.1" in source
