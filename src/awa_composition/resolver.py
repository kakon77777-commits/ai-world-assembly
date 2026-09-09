from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from awa_contracts.validator import ContractValidationError, load_json, validation_errors


class CompositionError(ValueError):
    pass


_CLASS_RANK = {"C0": 0, "C1": 1, "C2": 2, "C3": 3, "C4": 4}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _schema(root: Path, contract: str) -> dict[str, Any]:
    path = root / "schemas" / f"{contract}.schema.json"
    try:
        return load_json(path)
    except ContractValidationError as exc:
        raise CompositionError(str(exc)) from exc


def _validate(root: Path, contract: str, document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise CompositionError(f"{label} must be a JSON object")
    errors = validation_errors(_schema(root, contract), document)
    if errors:
        raise CompositionError(f"{label} violates {contract}: " + "; ".join(errors))
    return document


def load_world_profile(path: str | Path, *, root: str | Path) -> dict[str, Any]:
    try:
        document = load_json(path)
    except ContractValidationError as exc:
        raise CompositionError(str(exc)) from exc
    return _validate(Path(root), "world-profile.v0.1", document, f"profile {path}")


def _json_files(directory: str | Path) -> Iterable[Path]:
    target = Path(directory)
    if not target.is_dir():
        raise CompositionError(f"registry directory not found: {target}")
    return sorted(target.glob("*.json"), key=lambda item: item.name)


def load_module_registry(directory: str | Path, *, root: str | Path) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in _json_files(directory):
        try:
            document = load_json(path)
        except ContractValidationError as exc:
            raise CompositionError(str(exc)) from exc
        manifest = _validate(Path(root), "module-manifest.v0.1", document, f"module {path}")
        module_id = manifest["module"]["id"]
        if module_id in registry:
            raise CompositionError(f"duplicate module id in v0.1 registry: {module_id}")
        if module_id in manifest["compatibility"]["conflicts"]:
            raise CompositionError(f"module cannot conflict with itself: {module_id}")
        registry[module_id] = manifest
    return registry


def load_capability_registry(directory: str | Path, *, root: str | Path) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for path in _json_files(directory):
        try:
            document = load_json(path)
        except ContractValidationError as exc:
            raise CompositionError(str(exc)) from exc
        contract = _validate(Path(root), "capability-contract.v0.1", document, f"capability {path}")
        capability_id = contract["capability"]["id"]
        if capability_id in registry:
            raise CompositionError(f"duplicate capability id: {capability_id}")
        registry[capability_id] = contract
    return registry


def _validate_profile_sets(profile: dict[str, Any]) -> None:
    modules = profile["modules"]
    required = set(modules["required"])
    optional = set(modules["optional"])
    disabled = set(modules["disabled"])
    overlap = (required & optional) | (required & disabled) | (optional & disabled)
    if overlap:
        raise CompositionError(f"module profile sets overlap: {sorted(overlap)}")
    capabilities = profile["capability_profile"]
    cap_overlap = set(capabilities["available"]) & set(capabilities["disabled"])
    if cap_overlap:
        raise CompositionError(f"capability profile sets overlap: {sorted(cap_overlap)}")


def resolve_composition(
    profile: dict[str, Any],
    modules: dict[str, dict[str, Any]],
    capabilities: dict[str, dict[str, Any]],
    *,
    root: str | Path,
) -> dict[str, Any]:
    root_path = Path(root)
    _validate(root_path, "world-profile.v0.1", profile, "world profile")
    _validate_profile_sets(profile)

    disabled_modules = set(profile["modules"]["disabled"])
    available_capabilities = set(profile["capability_profile"]["available"])
    disabled_capabilities = set(profile["capability_profile"]["disabled"])
    max_class = profile["compatibility_policy"]["max_class"]
    core_version = profile["core_version"]

    visiting: list[str] = []
    visited: set[str] = set()
    ordered: list[str] = []

    def visit(module_id: str) -> None:
        if module_id in visited:
            return
        if module_id in visiting:
            start = visiting.index(module_id)
            cycle = visiting[start:] + [module_id]
            raise CompositionError("required module dependency cycle: " + " -> ".join(cycle))
        if module_id in disabled_modules:
            raise CompositionError(f"disabled module is required by active composition: {module_id}")
        manifest = modules.get(module_id)
        if manifest is None:
            raise CompositionError(f"module manifest not found: {module_id}")
        allowed_cores = manifest["requires"]["core"]
        if allowed_cores and core_version not in allowed_cores:
            raise CompositionError(
                f"module {module_id} does not support core {core_version}; allowed={sorted(allowed_cores)}"
            )
        module_class = manifest["compatibility"]["class"]
        if _CLASS_RANK[module_class] > _CLASS_RANK[max_class]:
            raise CompositionError(
                f"module {module_id} compatibility class {module_class} exceeds profile max {max_class}"
            )
        visiting.append(module_id)
        for dependency in sorted(manifest["requires"]["modules"]):
            visit(dependency)
        visiting.pop()
        visited.add(module_id)
        ordered.append(module_id)

    roots = sorted(profile["modules"]["required"] + profile["modules"]["optional"])
    for module_id in roots:
        visit(module_id)

    active = set(ordered)
    conflicts: list[tuple[str, str]] = []
    for module_id in sorted(active):
        for conflict in sorted(modules[module_id]["compatibility"]["conflicts"]):
            if conflict in active:
                conflicts.append(tuple(sorted((module_id, conflict))))
    conflicts = sorted(set(conflicts))
    if conflicts:
        rendered = ", ".join(f"{left}<->{right}" for left, right in conflicts)
        raise CompositionError(f"active module conflict: {rendered}")

    required_capabilities = sorted({
        capability
        for module_id in active
        for capability in modules[module_id]["requires"]["capabilities"]
    })
    for capability_id in required_capabilities:
        if capability_id in disabled_capabilities:
            raise CompositionError(f"required capability is disabled: {capability_id}")
        if capability_id not in available_capabilities:
            raise CompositionError(f"required capability is not available in profile: {capability_id}")
        if capability_id not in capabilities:
            raise CompositionError(f"capability contract not found: {capability_id}")

    selected_manifests = [modules[module_id] for module_id in ordered]
    selected_capabilities = [capabilities[capability_id] for capability_id in required_capabilities]
    source_hashes = {
        "profile": sha256_json(profile),
        "modules": sha256_json(selected_manifests),
        "capabilities": sha256_json(selected_capabilities),
    }
    identity_hash = sha256_json({"profile": profile["profile_id"], "source_hashes": source_hashes})
    receipt = {
        "contract": "composition-receipt.v0.1",
        "receipt_id": f"composition:{profile['profile_id']}:{identity_hash[:16]}",
        "profile": profile["profile_id"],
        "core": core_version,
        "resolved_modules": ordered,
        "module_versions": {
            module_id: modules[module_id]["module"]["version"]
            for module_id in sorted(active)
        },
        "capability_policy": {
            "available": sorted(available_capabilities),
            "disabled": sorted(disabled_capabilities),
            "required": required_capabilities,
        },
        "compatibility_result": "pass",
        "source_hashes": source_hashes,
    }
    errors = validation_errors(_schema(root_path, "composition-receipt.v0.1"), receipt)
    if errors:
        raise CompositionError("internal composition receipt violates contract: " + "; ".join(errors))
    return receipt
