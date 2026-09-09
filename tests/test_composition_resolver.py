from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from awa_composition import (
    CompositionError,
    load_capability_registry,
    load_module_registry,
    load_world_profile,
    resolve_composition,
)
from awa_contracts.validator import validation_errors

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "csc_ocm"
MODULES = FIX / "modules"
CAPABILITIES = FIX / "capabilities"
PROFILE = FIX / "alien_lineage.profile.json"
EXPECTED = FIX / "expected.alien_lineage.composition-receipt.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _registry():
    return (
        load_world_profile(PROFILE, root=ROOT),
        load_module_registry(MODULES, root=ROOT),
        load_capability_registry(CAPABILITIES, root=ROOT),
    )


def test_golden_resolution_is_deterministic_and_contract_valid() -> None:
    profile, modules, capabilities = _registry()
    one = resolve_composition(profile, modules, capabilities, root=ROOT)
    two = resolve_composition(copy.deepcopy(profile), copy.deepcopy(modules), copy.deepcopy(capabilities), root=ROOT)
    assert one == two == _load(EXPECTED)
    schema = _load(ROOT / "schemas" / "composition-receipt.v0.1.schema.json")
    assert validation_errors(schema, one) == []
    assert one["resolved_modules"] == [
        "alien_lineage.species_core",
        "alien_lineage.ecology",
        "alien_lineage.evolution",
        "alien_lineage.multiworld_rift",
    ]
    assert one["capability_policy"]["required"] == ["semantic_analysis"]


def test_optional_profile_modules_are_selected_not_best_effort() -> None:
    profile, modules, capabilities = _registry()
    modules.pop("alien_lineage.multiworld_rift")
    with pytest.raises(CompositionError, match="module manifest not found: alien_lineage.multiworld_rift"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_missing_or_disabled_required_dependency_fails_closed() -> None:
    profile, modules, capabilities = _registry()
    modules.pop("alien_lineage.species_core")
    with pytest.raises(CompositionError, match="module manifest not found: alien_lineage.species_core"):
        resolve_composition(profile, modules, capabilities, root=ROOT)

    profile, modules, capabilities = _registry()
    profile["modules"]["disabled"] = ["alien_lineage.species_core"]
    with pytest.raises(CompositionError, match="disabled module is required"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_dependency_cycle_is_rejected() -> None:
    profile, modules, capabilities = _registry()
    modules["alien_lineage.species_core"]["requires"]["modules"] = ["alien_lineage.ecology"]
    with pytest.raises(CompositionError, match="dependency cycle"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_explicit_module_conflict_is_rejected() -> None:
    profile, modules, capabilities = _registry()
    modules["alien_lineage.ecology"]["compatibility"]["conflicts"] = ["alien_lineage.evolution"]
    with pytest.raises(CompositionError, match="active module conflict"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_core_and_compatibility_class_are_enforced() -> None:
    profile, modules, capabilities = _registry()
    profile["core_version"] = "world.core.v9.9"
    with pytest.raises(CompositionError, match="does not support core"):
        resolve_composition(profile, modules, capabilities, root=ROOT)

    profile, modules, capabilities = _registry()
    modules["alien_lineage.evolution"]["compatibility"]["class"] = "C3"
    with pytest.raises(CompositionError, match="exceeds profile max C2"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_required_capability_must_be_available_enabled_and_registered() -> None:
    profile, modules, capabilities = _registry()
    profile["capability_profile"]["available"] = []
    with pytest.raises(CompositionError, match="not available in profile"):
        resolve_composition(profile, modules, capabilities, root=ROOT)

    profile, modules, capabilities = _registry()
    profile["capability_profile"]["available"] = []
    profile["capability_profile"]["disabled"] = ["semantic_analysis"]
    with pytest.raises(CompositionError, match="required capability is disabled"):
        resolve_composition(profile, modules, capabilities, root=ROOT)

    profile, modules, capabilities = _registry()
    capabilities.pop("semantic_analysis")
    with pytest.raises(CompositionError, match="capability contract not found"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_profile_set_overlap_is_rejected() -> None:
    profile, modules, capabilities = _registry()
    profile["modules"]["disabled"] = ["alien_lineage.ecology"]
    with pytest.raises(CompositionError, match="module profile sets overlap"):
        resolve_composition(profile, modules, capabilities, root=ROOT)

    profile, modules, capabilities = _registry()
    profile["capability_profile"]["disabled"] = ["semantic_analysis"]
    with pytest.raises(CompositionError, match="capability profile sets overlap"):
        resolve_composition(profile, modules, capabilities, root=ROOT)


def test_registry_rejects_duplicate_ids_and_provider_specific_extensions(tmp_path: Path) -> None:
    manifest = _load(MODULES / "alien_lineage.species_core.json")
    (tmp_path / "a.json").write_text(json.dumps(manifest), encoding="utf-8")
    duplicate = copy.deepcopy(manifest)
    duplicate["module"]["version"] = "v0.2"
    (tmp_path / "b.json").write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(CompositionError, match="duplicate module id"):
        load_module_registry(tmp_path, root=ROOT)

    provider_dir = tmp_path / "provider"
    provider_dir.mkdir()
    provider_specific = copy.deepcopy(manifest)
    provider_specific["provider"] = "some-model-vendor"
    (provider_dir / "bad.json").write_text(json.dumps(provider_specific), encoding="utf-8")
    with pytest.raises(CompositionError, match="violates module-manifest.v0.1"):
        load_module_registry(provider_dir, root=ROOT)


def test_receipt_hash_changes_when_selected_module_semantics_change() -> None:
    profile, modules, capabilities = _registry()
    original = resolve_composition(profile, modules, capabilities, root=ROOT)
    modules["alien_lineage.evolution"]["module"]["version"] = "v0.2"
    changed = resolve_composition(profile, modules, capabilities, root=ROOT)
    assert changed["source_hashes"]["modules"] != original["source_hashes"]["modules"]
    assert changed["receipt_id"] != original["receipt_id"]
    assert changed["module_versions"]["alien_lineage.evolution"] == "v0.2"
