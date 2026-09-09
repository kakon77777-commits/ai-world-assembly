from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from awa_cw_intake import CompilableWorldIntakeError, build_authoring_files, emit_authoring

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
INTAKE = FIX / "compilableworld_intake"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inputs():
    return (
        load(FIX / "sedb" / "expected.game.alien_lineage.snapshot.json"),
        load(FIX / "csc_ocm" / "expected.alien_lineage.composition-receipt.json"),
        load(INTAKE / "asset-graph.resolved.json"),
        load(INTAKE / "alien_lineage.intake-plan.json"),
    )


def test_build_authoring_is_deterministic_and_grounded() -> None:
    semantic, composition, graph, plan = inputs()
    files1, receipt1 = build_authoring_files(semantic, composition, graph, plan, root=ROOT)
    files2, receipt2 = build_authoring_files(semantic, composition, graph, plan, root=ROOT)
    assert files1 == files2
    assert receipt1 == receipt2
    assert set(files1) == {
        "manifest.json", "world.json", "data/rooms.csv", "data/exits.csv",
        "data/entities.csv", "data/items.csv", "quests.json", "scenarios.json",
    }
    assert "Crystal Filterer" in files1["data/entities.csv"]
    assert "species.crystal_filterer" in files1["data/entities.csv"]
    assert receipt1["world_id"] == "alien-lineage.intake-demo"
    assert receipt1["target"] == "compilableworld.authoring/v0.1"


def test_emit_matches_checked_in_golden_authoring(tmp_path: Path) -> None:
    receipt_path = emit_authoring(
        FIX / "sedb" / "expected.game.alien_lineage.snapshot.json",
        FIX / "csc_ocm" / "expected.alien_lineage.composition-receipt.json",
        INTAKE / "asset-graph.resolved.json",
        INTAKE / "alien_lineage.intake-plan.json",
        tmp_path,
        root=ROOT,
    )
    expected = INTAKE / "expected_authoring"
    for path in sorted(expected.rglob("*")):
        if path.is_file():
            relative = path.relative_to(expected)
            assert (tmp_path / relative).read_bytes() == path.read_bytes(), relative
    assert load(receipt_path)["contract"] == "compilableworld-intake-receipt.v0.1"


def test_rejects_tampered_semantic_snapshot_hash() -> None:
    semantic, composition, graph, plan = inputs()
    semantic = deepcopy(semantic)
    semantic["entities"][0]["label"] = "Tampered"
    with pytest.raises(CompilableWorldIntakeError, match="semantic snapshot sha256 mismatch"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)


def test_rejects_incomplete_asset_graph() -> None:
    semantic, composition, _, plan = inputs()
    graph = load(FIX / "asset_graph" / "expected.crystal_filterer.graph-snapshot.json")
    with pytest.raises(CompilableWorldIntakeError, match="not build-complete"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)


def test_rejects_nonpassed_asset_evidence() -> None:
    semantic, composition, graph, plan = inputs()
    graph = deepcopy(graph)
    graph["artifact_statuses"][0]["effective_status"] = "stale"
    body = {key: value for key, value in graph.items() if key not in {"snapshot_id", "sha256"}}
    from awa_cw_intake.intake import sha256_json
    digest = sha256_json(body)
    graph["snapshot_id"] = f"graph:{digest[:16]}"
    graph["sha256"] = digest
    with pytest.raises(CompilableWorldIntakeError, match="non-passed required artifacts"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)


def test_rejects_missing_semantic_reference() -> None:
    semantic, composition, graph, plan = inputs()
    plan = deepcopy(plan)
    plan["entities"][0]["semantic_ref"] = "species.unknown"
    with pytest.raises(CompilableWorldIntakeError, match="semantic_ref not found"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)


def test_rejects_unresolved_required_composition_module() -> None:
    semantic, composition, graph, plan = inputs()
    plan = deepcopy(plan)
    plan["required_composition_modules"].append("alien_lineage.not_installed")
    with pytest.raises(CompilableWorldIntakeError, match="unresolved composition modules"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)


def test_rejects_graph_root_mismatch() -> None:
    semantic, composition, graph, plan = inputs()
    plan = deepcopy(plan)
    plan["graph_roots"] = ["species.shellback"]
    with pytest.raises(CompilableWorldIntakeError, match="graph_roots"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)


def test_rejects_duplicate_runtime_ids() -> None:
    semantic, composition, graph, plan = inputs()
    plan = deepcopy(plan)
    duplicate = deepcopy(plan["entities"][0])
    duplicate["semantic_ref"] = "species.shellback"
    plan["entities"].append(duplicate)
    with pytest.raises(CompilableWorldIntakeError, match="duplicate runtime entity ids"):
        build_authoring_files(semantic, composition, graph, plan, root=ROOT)
