from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from awa_contracts.validator import ContractValidationError, load_json, validation_errors


class AssetGraphError(ValueError):
    pass


_ALLOWED_TASK_LAYERS = {"semantic", "composition", "asset", "runtime", "presentation"}
_EXACT_VERSION_RE = re.compile(r"^v\d+\.\d+$")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _schema(root: Path, contract: str) -> dict[str, Any]:
    path = root / "schemas" / f"{contract}.schema.json"
    try:
        return load_json(path)
    except ContractValidationError as exc:
        raise AssetGraphError(str(exc)) from exc


def _validate(root: Path, contract: str, document: Any, label: str) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise AssetGraphError(f"{label} must be a JSON object")
    errors = validation_errors(_schema(root, contract), document)
    if errors:
        raise AssetGraphError(f"{label} violates {contract}: " + "; ".join(errors))
    return document


def _json_files(directory: str | Path) -> Iterable[Path]:
    target = Path(directory)
    if not target.is_dir():
        raise AssetGraphError(f"registry directory not found: {target}")
    return sorted(target.glob("*.json"), key=lambda item: item.name)


def _load_registry(
    directory: str | Path,
    *,
    root: str | Path,
    contract: str,
    id_path: tuple[str, ...],
    label: str,
) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    root_path = Path(root)
    for path in _json_files(directory):
        try:
            document = load_json(path)
        except ContractValidationError as exc:
            raise AssetGraphError(str(exc)) from exc
        document = _validate(root_path, contract, document, f"{label} {path}")
        current: Any = document
        for part in id_path:
            current = current[part]
        identifier = current
        if identifier in registry:
            raise AssetGraphError(f"duplicate {label} id: {identifier}")
        registry[identifier] = document
    return registry


def load_nodes(directory: str | Path, *, root: str | Path) -> dict[str, dict[str, Any]]:
    return _load_registry(directory, root=root, contract="asset-graph-node.v0.1", id_path=("node_id",), label="node")


def load_edges(directory: str | Path, *, root: str | Path) -> dict[str, dict[str, Any]]:
    return _load_registry(directory, root=root, contract="asset-graph-edge.v0.1", id_path=("edge_id",), label="edge")


def load_artifacts(directory: str | Path, *, root: str | Path) -> dict[str, dict[str, Any]]:
    return _load_registry(directory, root=root, contract="artifact-reference.v0.1", id_path=("artifact_id",), label="artifact")


def load_validations(directory: str | Path, *, root: str | Path) -> dict[str, dict[str, Any]]:
    return _load_registry(directory, root=root, contract="artifact-validation.v0.1", id_path=("validation_id",), label="validation")


@dataclass(frozen=True)
class GraphAnalysis:
    snapshot: dict[str, Any]
    generation_tasks: list[dict[str, Any]]


class AssetGraph:
    def __init__(self, nodes: dict[str, dict[str, Any]], edges: dict[str, dict[str, Any]], artifacts: dict[str, dict[str, Any]], validations: dict[str, dict[str, Any]], *, root: str | Path) -> None:
        self.root = Path(root)
        self.nodes = dict(nodes)
        self.edges = dict(edges)
        self.artifacts = dict(artifacts)
        self.validations = dict(validations)
        for node in self.nodes.values():
            _validate(self.root, "asset-graph-node.v0.1", node, f"node {node.get('node_id')}")
        for edge in self.edges.values():
            _validate(self.root, "asset-graph-edge.v0.1", edge, f"edge {edge.get('edge_id')}")
        for artifact in self.artifacts.values():
            _validate(self.root, "artifact-reference.v0.1", artifact, f"artifact {artifact.get('artifact_id')}")
        for validation in self.validations.values():
            _validate(self.root, "artifact-validation.v0.1", validation, f"validation {validation.get('validation_id')}")
        self._validate_structure()

    @classmethod
    def from_directories(cls, *, nodes: str | Path, edges: str | Path, artifacts: str | Path, validations: str | Path, root: str | Path) -> "AssetGraph":
        return cls(load_nodes(nodes, root=root), load_edges(edges, root=root), load_artifacts(artifacts, root=root), load_validations(validations, root=root), root=root)

    def _validate_structure(self) -> None:
        for edge_id, edge in sorted(self.edges.items()):
            edge_type = edge["type"]
            required = edge["required"]
            if edge_type == "requires" and not required:
                raise AssetGraphError(f"requires edge must set required=true: {edge_id}")
            if edge_type == "optional" and required:
                raise AssetGraphError(f"optional edge must set required=false: {edge_id}")
            if edge_type not in {"requires", "optional"} and required:
                raise AssetGraphError(f"non-dependency edge cannot set required=true: {edge_id}")
            if edge["from"] not in self.nodes:
                raise AssetGraphError(f"edge source node not found: {edge_id} -> {edge['from']}")
            if edge["to"] not in self.nodes and edge_type not in {"requires", "optional"}:
                raise AssetGraphError(f"edge target node not found: {edge_id} -> {edge['to']}")
            constraint = edge["version_constraint"]
            if constraint is not None and not _EXACT_VERSION_RE.fullmatch(constraint):
                raise AssetGraphError(f"v0.1 only supports null or exact vN.N version_constraint: {edge_id}")
            if constraint is not None and edge["to"] in self.nodes:
                actual = self.nodes[edge["to"]]["version"]
                if actual != constraint:
                    raise AssetGraphError(f"edge version constraint mismatch: {edge_id} requires {constraint}, actual={actual}")

        for node_id, node in sorted(self.nodes.items()):
            if node["node_type"] == "artifact":
                artifact_ref = node["metadata"].get("artifact_ref")
                if not isinstance(artifact_ref, str) or not artifact_ref:
                    raise AssetGraphError(f"artifact node requires metadata.artifact_ref: {node_id}")
                if artifact_ref not in self.artifacts:
                    raise AssetGraphError(f"artifact reference not found for node {node_id}: {artifact_ref}")
            if node["node_type"] == "validation":
                validation_ref = node["metadata"].get("validation_ref")
                if not isinstance(validation_ref, str) or not validation_ref:
                    raise AssetGraphError(f"validation node requires metadata.validation_ref: {node_id}")
                if validation_ref not in self.validations:
                    raise AssetGraphError(f"validation reference not found for node {node_id}: {validation_ref}")

        for edge_id, edge in sorted(self.edges.items()):
            if edge["type"] != "validated_by" or edge["to"] not in self.nodes:
                continue
            source = self.nodes[edge["from"]]
            target = self.nodes[edge["to"]]
            if source["node_type"] != "artifact" or target["node_type"] != "validation":
                raise AssetGraphError(f"validated_by must connect artifact -> validation nodes: {edge_id}")
            artifact_ref = source["metadata"]["artifact_ref"]
            validation_ref = target["metadata"]["validation_ref"]
            validation = self.validations[validation_ref]
            if validation["artifact_id"] != artifact_ref:
                raise AssetGraphError(f"validation artifact mismatch: {validation_ref} targets {validation['artifact_id']}, expected {artifact_ref}")

    def _required_edges_from(self, node_id: str) -> list[dict[str, Any]]:
        return sorted((edge for edge in self.edges.values() if edge["from"] == node_id and edge["type"] == "requires" and edge["required"]), key=lambda edge: (edge["to"], edge["edge_id"]))

    def _validated_by_edges_from(self, node_id: str) -> list[dict[str, Any]]:
        return sorted((edge for edge in self.edges.values() if edge["from"] == node_id and edge["type"] == "validated_by"), key=lambda edge: (edge["to"], edge["edge_id"]))

    def required_closure(self, roots: Iterable[str]) -> tuple[list[str], list[dict[str, Any]]]:
        root_ids = sorted(set(roots))
        if not root_ids:
            raise AssetGraphError("at least one graph root is required")
        for root_id in root_ids:
            if root_id not in self.nodes:
                raise AssetGraphError(f"graph root node not found: {root_id}")
        visiting: list[str] = []
        visited: set[str] = set()
        ordered: list[str] = []
        missing: dict[str, dict[str, Any]] = {}

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                start = visiting.index(node_id)
                cycle = visiting[start:] + [node_id]
                raise AssetGraphError("required asset dependency cycle: " + " -> ".join(cycle))
            visiting.append(node_id)
            for edge in self._required_edges_from(node_id):
                target = edge["to"]
                if target not in self.nodes:
                    missing[edge["edge_id"]] = {"edge_id": edge["edge_id"], "from": edge["from"], "to": target, "scope": edge["scope"], "version_constraint": edge["version_constraint"]}
                    continue
                visit(target)
            visiting.pop()
            visited.add(node_id)
            ordered.append(node_id)

        for root_id in root_ids:
            visit(root_id)
        return ordered, [missing[key] for key in sorted(missing)]

    def _generation_task(self, missing: dict[str, Any]) -> dict[str, Any]:
        basis = {"edge_id": missing["edge_id"], "from": missing["from"], "to": missing["to"], "version_constraint": missing["version_constraint"]}
        task_id = f"task:generate:{sha256_json(basis)[:16]}"
        layer = missing["scope"] if missing["scope"] in _ALLOWED_TASK_LAYERS else "asset"
        constraints = [f"required_by={missing['edge_id']}"]
        if missing["version_constraint"] is not None:
            constraints.append(f"version={missing['version_constraint']}")
        task = {"contract": "generation-task.v0.1", "task_id": task_id, "target": {"node_ref": missing["from"], "missing_role": missing["to"]}, "inputs": [missing["from"]], "constraints": constraints, "allowed_layers": [layer], "validators": [], "budget": {"max_attempts": 2, "max_cost_units": 0}, "authority": "proposal", "status": "pending"}
        errors = validation_errors(_schema(self.root, "generation-task.v0.1"), task)
        if errors:
            raise AssetGraphError("internal generation task violates contract: " + "; ".join(errors))
        return task

    def _artifact_status(self, node_id: str) -> dict[str, Any]:
        node = self.nodes[node_id]
        artifact_id = node["metadata"]["artifact_ref"]
        artifact = self.artifacts[artifact_id]
        fresh: list[str] = []
        stale: list[str] = []
        fresh_statuses: list[str] = []
        for edge in self._validated_by_edges_from(node_id):
            validation_node = self.nodes[edge["to"]]
            validation_id = validation_node["metadata"]["validation_ref"]
            validation = self.validations[validation_id]
            if validation["artifact_sha256"] == artifact["sha256"]:
                fresh.append(validation_id)
                fresh_statuses.append(validation["status"])
            else:
                stale.append(validation_id)
        if "failed" in fresh_statuses:
            effective = "failed"
        elif "passed" in fresh_statuses:
            effective = "passed"
        elif stale:
            effective = "stale"
        else:
            effective = "unvalidated"
        return {"node_id": node_id, "artifact_id": artifact_id, "sha256": artifact["sha256"], "effective_status": effective, "fresh_validation_ids": sorted(fresh), "stale_validation_ids": sorted(stale)}

    def analyze(self, roots: Iterable[str]) -> GraphAnalysis:
        root_ids = sorted(set(roots))
        closure, missing = self.required_closure(root_ids)
        tasks = [self._generation_task(item) for item in missing]
        closure_set = set(closure)
        selected_edges = sorted((edge for edge in self.edges.values() if edge["from"] in closure_set and (((edge["type"] == "requires" and edge["required"] and (edge["to"] in closure_set or edge["to"] not in self.nodes))) or edge["type"] == "validated_by")), key=lambda edge: edge["edge_id"])
        selected_node_ids = set(closure)
        for edge in selected_edges:
            if edge["to"] in self.nodes and self.nodes[edge["to"]]["node_type"] == "validation":
                selected_node_ids.add(edge["to"])
        selected_nodes = [self.nodes[node_id] for node_id in sorted(selected_node_ids)]
        artifact_node_ids = sorted(node_id for node_id in closure if self.nodes[node_id]["node_type"] == "artifact")
        artifact_statuses = [self._artifact_status(node_id) for node_id in artifact_node_ids]
        selected_artifact_ids = sorted(status["artifact_id"] for status in artifact_statuses)
        selected_validation_ids = sorted({validation_id for status in artifact_statuses for validation_id in status["fresh_validation_ids"] + status["stale_validation_ids"]})
        selected_artifacts = [self.artifacts[item] for item in selected_artifact_ids]
        selected_validations = [self.validations[item] for item in selected_validation_ids]
        source_hashes = {"nodes": sha256_json(selected_nodes), "edges": sha256_json(selected_edges), "artifacts": sha256_json(selected_artifacts), "validations": sha256_json(selected_validations)}
        body = {"contract": "asset-graph-snapshot.v0.1", "roots": root_ids, "required_closure": closure, "missing_required": missing, "generation_task_ids": [task["task_id"] for task in tasks], "artifact_statuses": artifact_statuses, "source_hashes": source_hashes}
        digest = sha256_json(body)
        snapshot = {**body, "snapshot_id": f"graph:{digest[:16]}", "sha256": digest}
        errors = validation_errors(_schema(self.root, "asset-graph-snapshot.v0.1"), snapshot)
        if errors:
            raise AssetGraphError("internal graph snapshot violates contract: " + "; ".join(errors))
        return GraphAnalysis(snapshot=snapshot, generation_tasks=tasks)
