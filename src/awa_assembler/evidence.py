from __future__ import annotations

from pathlib import Path
from typing import Any

from awa_asset_graph.graph import AssetGraph, sha256_json

from .common import AssemblerError, candidate_artifact_id, slug, validate, validation_id_prefix
from .validators import VALIDATORS


def validation_documents(root: Path, task: dict[str, Any], payload: bytes,
                         artifact_id: str, artifact_sha: str, attempt: int):
    docs, diagnostics, statuses = [], [], []
    for validator_id in task["validators"]:
        result = VALIDATORS[validator_id](payload, root, task)
        status = "passed" if result.passed else "failed"
        statuses.append(status)
        diagnostics.extend(result.diagnostics)
        vid = f"{validation_id_prefix(task)}.{slug(validator_id)}.{artifact_sha[:12]}"
        doc = {
            "contract": "artifact-validation.v0.1",
            "validation_id": vid,
            "artifact_id": artifact_id,
            "artifact_sha256": artifact_sha,
            "validator": validator_id,
            "validator_version": "v0.1",
            "status": status,
            "diagnostics": result.diagnostics,
            "evidence_ref": f"bundle://attempts/{attempt}/validation.{slug(validator_id)}.json",
        }
        docs.append(validate(root, "artifact-validation.v0.1", doc, f"validation {validator_id}"))
    return docs, ("failed" if "failed" in statuses else "passed"), diagnostics


def artifact_reference(root: Path, producer_id: str, task: dict[str, Any], payload: bytes,
                       artifact_sha: str, validation_status: str, uri: str):
    aid = candidate_artifact_id(task, artifact_sha)
    doc = {
        "contract": "artifact-reference.v0.1",
        "artifact_id": aid,
        "kind": task["target"]["kind"],
        "uri": uri,
        "sha256": artifact_sha,
        "mime_type": task["target"]["mime_type"],
        "size": len(payload),
        "generator": producer_id,
        "license_ref": "license:internal-original",
        "parent_artifacts": [],
        "validation_status": validation_status,
    }
    return validate(root, "artifact-reference.v0.1", doc, "candidate artifact")


def preview_graph(root: Path, task: dict[str, Any], generation: dict[str, Any],
                  base_graph: AssetGraph, artifact: dict[str, Any], validations: list[dict[str, Any]]):
    nodes, edges = dict(base_graph.nodes), dict(base_graph.edges)
    artifacts, validation_registry = dict(base_graph.artifacts), dict(base_graph.validations)
    source_node = base_graph.nodes[generation["target"]["node_ref"]]
    target = {
        "contract": "asset-graph-node.v0.1",
        "node_id": task["target"]["node_id"],
        "node_type": "artifact",
        "namespace": source_node["namespace"],
        "semantic_ref": source_node.get("semantic_ref"),
        "version": task["target"]["version"],
        "status": "candidate",
        "metadata": {
            "artifact_ref": artifact["artifact_id"],
            "assembler_task": task["task_id"],
            "role": task["target"]["kind"],
        },
        "provenance_ref": f"assembler://{task['task_id']}/{artifact['artifact_id']}",
    }
    validate(root, "asset-graph-node.v0.1", target, "candidate graph node")
    nodes[target["node_id"]] = target
    artifacts[artifact["artifact_id"]] = artifact
    vnodes, vedges = [], []
    for item in validations:
        validation_registry[item["validation_id"]] = item
        node = {
            "contract": "asset-graph-node.v0.1",
            "node_id": item["validation_id"],
            "node_type": "validation",
            "namespace": source_node["namespace"],
            "semantic_ref": source_node.get("semantic_ref"),
            "version": "v0.1",
            "status": "active",
            "metadata": {"validation_ref": item["validation_id"]},
            "provenance_ref": f"assembler-validation://{item['validation_id']}",
        }
        edge = {
            "contract": "asset-graph-edge.v0.1",
            "edge_id": f"edge:{target['node_id']}->{item['validation_id']}",
            "from": target["node_id"],
            "to": item["validation_id"],
            "type": "validated_by",
            "required": False,
            "version_constraint": None,
            "scope": "validation",
            "reason": "Bounded assembler exact-byte candidate validation evidence",
            "provenance_ref": f"assembler://{task['task_id']}/validation-edge",
        }
        validate(root, "asset-graph-node.v0.1", node, "validation graph node")
        validate(root, "asset-graph-edge.v0.1", edge, "validation graph edge")
        nodes[node["node_id"]] = node
        edges[edge["edge_id"]] = edge
        vnodes.append(node)
        vedges.append(edge)
    preview = AssetGraph(nodes, edges, artifacts, validation_registry, root=root).analyze([generation["target"]["node_ref"]])
    status = next(x for x in preview.snapshot["artifact_statuses"] if x["node_id"] == target["node_id"])
    if preview.snapshot["missing_required"] or preview.generation_tasks or status["effective_status"] != "passed":
        raise AssemblerError("candidate graph preview did not close the required target")
    return preview.snapshot, target, vnodes, vedges


def run_receipt(root: Path, task: dict[str, Any], source_hashes: dict[str, str],
                attempts: list[dict[str, Any]], selected: dict[str, Any] | None,
                preview: dict[str, Any] | None):
    if selected and preview:
        target_status = next(x for x in preview["artifact_statuses"] if x["node_id"] == task["target"]["node_id"])
        status = "validated_candidate"
        graph = {
            "snapshot_id": preview["snapshot_id"],
            "sha256": preview["sha256"],
            "missing_required": len(preview["missing_required"]),
            "generation_tasks": len(preview["generation_task_ids"]),
            "target_effective_status": target_status["effective_status"],
        }
        chosen = {k: selected[k] for k in ("artifact_id", "sha256", "uri", "mime_type")}
        promotion = {
            "status": "validated_candidate",
            "target_node_status": "candidate",
            "canonical_write": False,
            "reason": "all validators passed and the candidate graph preview is build-complete; canonical authority was not granted",
        }
    else:
        status, graph, chosen = "blocked", None, None
        promotion = {
            "status": "blocked",
            "target_node_status": "none",
            "canonical_write": False,
            "reason": "attempt budget exhausted before a build-complete validated candidate was produced",
        }
    basis = {
        "task_id": task["task_id"],
        "status": status,
        "source_hashes": source_hashes,
        "attempts": attempts,
        "selected_candidate": chosen,
        "graph_preview": graph,
        "promotion": promotion,
    }
    body = {"contract": "assembler-run-receipt.v0.1", "run_id": f"assembler-run:{sha256_json(basis)[:16]}", **basis}
    receipt = {**body, "evidence_hash": sha256_json(body)}
    return validate(root, "assembler-run-receipt.v0.1", receipt, "assembler run receipt")
