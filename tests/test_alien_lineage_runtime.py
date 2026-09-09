from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from awa_alien_lineage import AlienLineageBuildError, build_runtime_authoring_files, emit_runtime_authoring

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
RUNTIME = FIX / "alien_lineage_runtime"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inputs():
    return (
        load(FIX / "sedb" / "expected.game.alien_lineage.snapshot.json"),
        load(FIX / "csc_ocm" / "expected.alien_lineage.composition-receipt.json"),
        load(FIX / "compilableworld_intake" / "asset-graph.resolved.json"),
        load(RUNTIME / "alien_lineage.intake-plan.json"),
        load(RUNTIME / "runtime-slice.json"),
    )


def test_runtime_authoring_is_deterministic_and_adds_functionir_extension() -> None:
    values = inputs()
    files1, receipt1 = build_runtime_authoring_files(*values, root=ROOT)
    files2, receipt2 = build_runtime_authoring_files(*values, root=ROOT)
    assert files1 == files2
    assert receipt1 == receipt2
    assert "functions.json" in files1
    manifest = json.loads(files1["manifest.json"])
    world = json.loads(files1["world.json"])
    assert manifest["sources"]["functions"] == "functions.json"
    assert world["runtime_extensions"] == [{"entrypoint": "awa_alien_lineage.runtime:AlienLineageModule", "module_id": "alien_lineage.runtime", "version": "0.1.0"}]
    assert world["alien_lineage_runtime"]["species_ref"] == "species.crystal_filterer"
    assert receipt1["contract"] == "alien-lineage-runtime-receipt.v0.1"


def test_emit_matches_checked_in_phase6_golden(tmp_path: Path) -> None:
    receipt_path = emit_runtime_authoring(
        FIX / "sedb" / "expected.game.alien_lineage.snapshot.json",
        FIX / "csc_ocm" / "expected.alien_lineage.composition-receipt.json",
        FIX / "compilableworld_intake" / "asset-graph.resolved.json",
        RUNTIME / "alien_lineage.intake-plan.json",
        RUNTIME / "runtime-slice.json",
        tmp_path,
        root=ROOT,
    )
    expected = RUNTIME / "expected_authoring"
    for path in sorted(expected.rglob("*")):
        if path.is_file():
            relative = path.relative_to(expected)
            assert (tmp_path / relative).read_bytes() == path.read_bytes(), relative
    assert load(receipt_path) == load(expected / "awa-alien-lineage-runtime-receipt.json")


def test_rejects_species_not_in_semantic_snapshot() -> None:
    semantic, composition, graph, plan, slice_doc = inputs()
    slice_doc = deepcopy(slice_doc)
    slice_doc["runtime_config"]["species_ref"] = "species.unknown"
    with pytest.raises(AlienLineageBuildError, match="not present in semantic snapshot"):
        build_runtime_authoring_files(semantic, composition, graph, plan, slice_doc, root=ROOT)


def test_rejects_runtime_slice_without_exact_functionir_set() -> None:
    semantic, composition, graph, plan, slice_doc = inputs()
    slice_doc = deepcopy(slice_doc)
    slice_doc["functions"]["functions"][-1]["function_id"] = "alien_lineage.wrong"
    with pytest.raises(AlienLineageBuildError, match="exactly the bounded FunctionIR set"):
        build_runtime_authoring_files(semantic, composition, graph, plan, slice_doc, root=ROOT)


def test_phase6_plan_requires_evolution_and_rift_composition_modules() -> None:
    _, composition, _, plan, _ = inputs()
    assert set(plan["required_composition_modules"]) == {
        "alien_lineage.species_core", "alien_lineage.ecology", "alien_lineage.evolution", "alien_lineage.multiworld_rift"
    }
    assert set(plan["required_composition_modules"]) <= set(composition["resolved_modules"])


def test_runtime_module_import_is_compilableworld_lazy() -> None:
    import awa_alien_lineage.runtime as runtime_module
    assert runtime_module.MODULE_ID == "alien_lineage.runtime"
    assert runtime_module.MODULE_VERSION == "0.1.0"


def test_domain_assertion_sidecar_is_versioned_and_targets_full_cycle() -> None:
    sidecar = load(RUNTIME / "full-cycle.assertions.json")
    assert sidecar["contract"] == "alien-lineage-runtime-assertions.v0.1"
    assert sidecar["scenario_id"] == "alien-lineage.full-cycle"
    assert any(item["namespace"] == "lineage" and item["key"] == "organs" for item in sidecar["state"])


def test_native_full_cycle_assertions_stay_inside_compilableworld_whitelist() -> None:
    _, _, _, plan, _ = inputs()
    scenario = next(item for item in plan["scenarios"] if item["scenario_id"] == "alien-lineage.full-cycle")
    assert scenario["expect"]["state"] == [
        {"owner": "$actor", "namespace": "position", "key": "room", "equals": "room.abyss.rift"}
    ]
