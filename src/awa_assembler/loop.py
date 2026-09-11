from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .common import AssemblerError, candidate_artifact_id, sha_bytes, slug, write_json
from .context import load_context
from .evidence import artifact_reference, preview_graph, run_receipt, validation_documents
from .provider import CandidateProducer, provider_invocation_for


class BoundedAssembler:
    def __init__(self, *, root: str | Path, producer: CandidateProducer) -> None:
        self.root, self.producer = Path(root), producer

    def run(self, *, task: dict[str, Any], project_state: str | Path,
            semantic_snapshot: str | Path, composition_receipt: str | Path,
            presentation_binding: str | Path, capability_contract: str | Path,
            nodes: str | Path, edges: str | Path, artifacts: str | Path,
            validations: str | Path, out: str | Path) -> dict[str, Any]:
        context, source_hashes, graph, generation = load_context(
            root=self.root, task=task, project_state=Path(project_state),
            semantic_snapshot=Path(semantic_snapshot), composition_receipt=Path(composition_receipt),
            presentation_binding=Path(presentation_binding), capability_contract=Path(capability_contract),
            nodes=Path(nodes), edges=Path(edges), artifacts=Path(artifacts), validations=Path(validations))
        output = Path(out)
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        write_json(output / "observed.graph-snapshot.before.json", context["graph_before"])

        attempts, prior = [], []
        provider_invocations: list[dict[str, Any]] = []
        selected = payload_selected = validations_selected = None
        for attempt in range(1, task["repair_policy"]["max_attempts"] + 1):
            try:
                payload = self.producer.produce(attempt=attempt, task=task, diagnostics=prior)
            except Exception as exc:
                raise AssemblerError(f"candidate producer failed on attempt {attempt}: {exc}") from exc
            if not isinstance(payload, (bytes, bytearray)) or not payload:
                raise AssemblerError("candidate producer must return non-empty bytes")
            payload = bytes(payload)
            provider_evidence = provider_invocation_for(self.producer, attempt=attempt)
            if provider_evidence is not None:
                provider_invocations.append(provider_evidence)
            sha = sha_bytes(payload)
            aid = candidate_artifact_id(task, sha)
            vdocs, aggregate, diagnostics = validation_documents(self.root, task, payload, aid, sha, attempt)
            artifact = artifact_reference(
                self.root, self.producer.producer_id, task, payload, sha, aggregate,
                f"bundle://attempts/{attempt}/{task['target']['filename']}")
            adir = output / "attempts" / str(attempt)
            adir.mkdir(parents=True)
            (adir / task["target"]["filename"]).write_bytes(payload)
            write_json(adir / "artifact-reference.json", artifact)
            for validation in vdocs:
                write_json(adir / f"validation.{slug(validation['validator'])}.json", validation)
            attempt_receipt = {
                "attempt": attempt,
                "producer_id": self.producer.producer_id,
                "artifact_id": artifact["artifact_id"],
                "artifact_sha256": sha,
                "validation_ids": [validation["validation_id"] for validation in vdocs],
                "validation_status": aggregate,
                "diagnostics": diagnostics,
            }
            if provider_evidence is not None:
                attempt_receipt["provider_evidence_hash"] = provider_evidence["evidence_hash"]
                write_json(adir / "provider-invocation-receipt.json", provider_evidence)
            attempts.append(attempt_receipt)
            if aggregate == "passed":
                payload_selected, validations_selected = payload, vdocs
                selected = artifact_reference(
                    self.root, self.producer.producer_id, task, payload, sha, "passed",
                    f"bundle://candidate/{task['target']['filename']}")
                break
            prior = diagnostics

        preview = None
        if selected is not None:
            preview, target, vnodes, vedges = preview_graph(
                self.root, task, generation, graph, selected, validations_selected)
            cdir = output / "candidate"
            cdir.mkdir(parents=True)
            (cdir / task["target"]["filename"]).write_bytes(payload_selected)
            write_json(cdir / "artifact-reference.json", selected)
            write_json(cdir / "asset-graph-node.json", target)
            for validation, node, edge in zip(validations_selected, vnodes, vedges, strict=True):
                key = slug(validation["validator"])
                write_json(cdir / f"validation.{key}.json", validation)
                write_json(cdir / f"validation-node.{key}.json", node)
                write_json(cdir / f"validated-by-edge.{key}.json", edge)
            write_json(cdir / "graph-snapshot.preview.json", preview)

        receipt = run_receipt(
            self.root, task, source_hashes, attempts, selected, preview,
            provider_invocations=provider_invocations or None,
        )
        write_json(output / "assembler-run-receipt.json", receipt)
        return receipt
