from __future__ import annotations

import copy
import json
import shutil
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def canonical_bytes(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def relay_recipe(*, scale_peak: float, duration_ms: int, emissive_boost: float) -> bytes:
    return canonical_bytes({
        "contract": "presentation-effect-recipe.v0.2",
        "recipe_id": "effect.relay-activation-pulse",
        "event_type": "relay_station.relay_activated",
        "effect": {
            "target": "relay_visual",
            "scale_peak": scale_peak,
            "duration_ms": duration_ms,
            "emissive_boost": emissive_boost,
        },
        "version": "v0.2",
    })


@contextmanager
def fake_provider(payload: bytes, *, status: int = 200, content_type: str = "application/json") -> Iterator[tuple[str, list[dict]]]:
    requests: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            requests.append(json.loads(body.decode("utf-8")))
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):  # noqa: A003
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/generate", requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def run_provider_relay(tmp_path: Path, *, endpoint: str, provider_id: str, model_id: str):
    from awa_assembler import BoundedAssembler
    from awa_assembler.provider import HTTPProviderProducer

    task = load("fixtures/assembler/relay-station.activation-effect-recipe.task.json")
    producer = HTTPProviderProducer(
        root=ROOT,
        endpoint=endpoint,
        provider_id=provider_id,
        model_id=model_id,
        timeout_seconds=2.0,
    )
    return BoundedAssembler(root=ROOT, producer=producer).run(
        task=task,
        project_state=ROOT / "PROJECT_STATE.json",
        semantic_snapshot=ROOT / "fixtures/sedb/expected.game.relay_station.snapshot.json",
        composition_receipt=ROOT / "fixtures/csc_ocm/expected.relay_station.composition-receipt.json",
        presentation_binding=ROOT / "fixtures/threejs/relay-station.presentation-binding.json",
        capability_contract=ROOT / "fixtures/assembler/presentation_recipe_generation.capability.json",
        nodes=ROOT / "fixtures/relay_presentation_graph/nodes",
        edges=ROOT / "fixtures/relay_presentation_graph/edges",
        artifacts=ROOT / "fixtures/relay_presentation_graph/artifacts",
        validations=ROOT / "fixtures/relay_presentation_graph/validations",
        out=tmp_path,
    )


def test_http_provider_candidate_binds_exact_invocation_evidence(tmp_path: Path) -> None:
    payload = relay_recipe(scale_peak=1.12, duration_ms=210, emissive_boost=0.75)
    with fake_provider(payload) as (endpoint, requests):
        receipt = run_provider_relay(
            tmp_path / "run",
            endpoint=endpoint,
            provider_id="provider.test.alpha",
            model_id="model.alpha-1",
        )

    assert receipt["contract"] == "assembler-run-receipt.v0.2"
    assert receipt["status"] == "validated_candidate"
    assert receipt["promotion"]["canonical_write"] is False
    assert len(receipt["provider_invocations"]) == 1
    evidence = receipt["provider_invocations"][0]
    assert evidence["provider_id"] == "provider.test.alpha"
    assert evidence["model_id"] == "model.alpha-1"
    import hashlib
    from awa_asset_graph.graph import sha256_json
    assert evidence["request_sha256"] == hashlib.sha256(canonical_bytes(requests[0])).hexdigest()
    assert evidence["response_sha256"] == receipt["selected_candidate"]["sha256"]
    evidence_body = {key: value for key, value in evidence.items() if key != "evidence_hash"}
    assert evidence["evidence_hash"] == sha256_json(evidence_body)
    receipt_body = {key: value for key, value in receipt.items() if key != "evidence_hash"}
    assert receipt["evidence_hash"] == sha256_json(receipt_body)
    assert receipt["attempts"][0]["provider_evidence_hash"] == evidence["evidence_hash"]
    assert requests[0]["canonical_write"] is False
    assert requests[0]["authority"] == "proposal"
    assert (tmp_path / "run/attempts/1/provider-invocation-receipt.json").is_file()


def test_provider_transport_failure_fails_closed_before_candidate_validation(tmp_path: Path) -> None:
    from awa_assembler.common import AssemblerError

    with fake_provider(b"provider unavailable", status=503, content_type="text/plain") as (endpoint, _):
        with pytest.raises(AssemblerError, match="provider returned HTTP 503"):
            run_provider_relay(
                tmp_path / "run",
                endpoint=endpoint,
                provider_id="provider.test.failure",
                model_id="model.failure-1",
            )


def test_provider_identity_is_evidence_not_candidate_semantic_identity(tmp_path: Path) -> None:
    payload = relay_recipe(scale_peak=1.11, duration_ms=205, emissive_boost=0.71)
    with fake_provider(payload) as (endpoint_a, _):
        a = run_provider_relay(tmp_path / "a", endpoint=endpoint_a, provider_id="provider.a", model_id="m-a")
    with fake_provider(payload) as (endpoint_b, _):
        b = run_provider_relay(tmp_path / "b", endpoint=endpoint_b, provider_id="provider.b", model_id="m-b")

    assert a["selected_candidate"]["sha256"] == b["selected_candidate"]["sha256"]
    a_ref = load_json_path(tmp_path / "a/candidate/artifact-reference.json")
    b_ref = load_json_path(tmp_path / "b/candidate/artifact-reference.json")
    assert a_ref["artifact_id"] == b_ref["artifact_id"]
    assert a_ref["generator"] == b_ref["generator"] == "provider-backed.http.v0.1"
    assert "provider.a" not in json.dumps(a_ref)
    assert "provider.b" not in json.dumps(b_ref)
    assert a["evidence_hash"] != b["evidence_hash"]


def load_json_path(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_multi_world_orchestrator_accepts_provider_resolver_without_authority_merge(tmp_path: Path) -> None:
    from awa_assembler.provider import HTTPProviderProducer, reference_producer_for
    from awa_orchestrator import MultiWorldOrchestrator

    payload = relay_recipe(scale_peak=1.13, duration_ms=215, emissive_boost=0.77)
    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    with fake_provider(payload) as (endpoint, _):
        def resolver(job):
            if job["orchestration_task_id"] == "relay-activation-recipe":
                return HTTPProviderProducer(
                    root=ROOT, endpoint=endpoint,
                    provider_id="provider.test.multiworld", model_id="model.multiworld-1",
                    timeout_seconds=2.0,
                )
            return reference_producer_for(job["task"])

        receipt = MultiWorldOrchestrator(root=ROOT, producer_resolver=resolver).run(
            plan=plan, out=tmp_path / "orchestration"
        )

    assert receipt["status"] == "completed"
    assert receipt["promotion"]["canonical_write"] is False
    assert {item["world_scope"] for item in receipt["task_results"]} == {"game.alien_lineage", "game.relay_station"}
    child = load_json_path(tmp_path / "orchestration/tasks/relay-activation-recipe/assembler-run-receipt.json")
    assert child["contract"] == "assembler-run-receipt.v0.2"
    assert child["provider_invocations"][0]["provider_id"] == "provider.test.multiworld"


def test_provider_bindings_are_execution_policy_not_world_semantics(tmp_path: Path) -> None:
    from awa_orchestrator.providers import producer_resolver_for_plan

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    bindings = {
        "contract": "provider-bindings.v0.1",
        "authority": "execution_binding",
        "canonical_write": False,
        "bindings": [{
            "orchestration_task_id": "relay-activation-recipe",
            "adapter": "http",
            "provider_id": "provider.example",
            "model_id": "model.example-1",
            "endpoint": "https://provider.invalid/generate",
            "timeout_seconds": 10,
        }],
    }
    resolver = producer_resolver_for_plan(root=ROOT, plan=plan, bindings=bindings)
    relay_job = {"orchestration_task_id": "relay-activation-recipe", "task": load("fixtures/assembler/relay-station.activation-effect-recipe.task.json")}
    provider = resolver(relay_job)
    assert provider.producer_id == "provider-backed.http.v0.1"
    assert provider.provider_id == "provider.example"
    assert "provider.example" not in json.dumps(plan)

    bad = copy.deepcopy(bindings)
    bad["bindings"][0]["orchestration_task_id"] = "unknown-task"
    with pytest.raises(ValueError, match="unknown orchestration task"):
        producer_resolver_for_plan(root=ROOT, plan=plan, bindings=bad)


def _run_provider_orchestration(out: Path, *, payload: bytes, provider_id: str):
    from awa_assembler.provider import HTTPProviderProducer, reference_producer_for
    from awa_orchestrator import MultiWorldOrchestrator

    plan = load("fixtures/orchestration/phase12.multi-world.plan.json")
    with fake_provider(payload) as (endpoint, _):
        def resolver(job):
            if job["orchestration_task_id"] == "relay-activation-recipe":
                return HTTPProviderProducer(
                    root=ROOT, endpoint=endpoint, provider_id=provider_id,
                    model_id=f"{provider_id}.model", timeout_seconds=2.0,
                )
            return reference_producer_for(job["task"])
        receipt = MultiWorldOrchestrator(root=ROOT, producer_resolver=resolver).run(plan=plan, out=out)
    return plan, receipt


def test_independent_provider_orchestrations_feed_phase13_selection_without_provider_tiebreak(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    from awa_promotion.bridge import candidate_from_orchestration

    # PromotionEvaluator deliberately only accepts repository-local artifact refs.
    root_build = ROOT / "build" / "phase14-test-provider-selection"
    if root_build.exists():
        shutil.rmtree(root_build)
    try:
        plan_a, receipt_a = _run_provider_orchestration(
            root_build / "run-a",
            payload=relay_recipe(scale_peak=1.10, duration_ms=200, emissive_boost=0.70),
            provider_id="provider.alpha",
        )
        plan_b, receipt_b = _run_provider_orchestration(
            root_build / "run-b",
            payload=relay_recipe(scale_peak=1.16, duration_ms=230, emissive_boost=0.82),
            provider_id="provider.beta",
        )
        job_a = next(x for x in plan_a["tasks"] if x["orchestration_task_id"] == "relay-activation-recipe")
        job_b = next(x for x in plan_b["tasks"] if x["orchestration_task_id"] == "relay-activation-recipe")
        a = candidate_from_orchestration(
            root=ROOT, orchestration_out=root_build / "run-a", orchestration_receipt=receipt_a,
            orchestration_task=job_a, policy_facts={"reviewed_priority": 20},
            policy_source="review:phase14-board",
        )
        b = candidate_from_orchestration(
            root=ROOT, orchestration_out=root_build / "run-b", orchestration_receipt=receipt_b,
            orchestration_task=job_b, policy_facts={"reviewed_priority": 10},
            policy_source="review:phase14-board",
        )
        conflict_set = {
            "contract": "candidate-conflict-set.v0.1",
            "conflict_set_id": "phase14:provider-selection",
            "authority": "comparison_input",
            "candidates": [a, b],
        }
        policy = load("fixtures/promotion/phase13.explicit-rank.policy.json")
        readiness = PromotionEvaluator(root=ROOT).evaluate(conflict_set=conflict_set, policy=policy)

        assert readiness["status"] == "ready"
        selected = readiness["decisions"][0]["selected_candidate"]
        assert selected["candidate_id"] == a["candidate_id"]
        assert "provider.alpha" not in json.dumps(conflict_set)
        assert "provider.beta" not in json.dumps(conflict_set)
    finally:
        shutil.rmtree(root_build, ignore_errors=True)


def test_provider_candidates_tied_by_reviewed_policy_still_block(tmp_path: Path) -> None:
    from awa_promotion import PromotionEvaluator
    from awa_promotion.bridge import candidate_from_orchestration

    root_build = ROOT / "build" / "phase14-test-provider-tie"
    shutil.rmtree(root_build, ignore_errors=True)
    try:
        plan_a, receipt_a = _run_provider_orchestration(
            root_build / "run-a",
            payload=relay_recipe(scale_peak=1.09, duration_ms=195, emissive_boost=0.68),
            provider_id="provider.tie-a",
        )
        plan_b, receipt_b = _run_provider_orchestration(
            root_build / "run-b",
            payload=relay_recipe(scale_peak=1.15, duration_ms=225, emissive_boost=0.80),
            provider_id="provider.tie-b",
        )
        job_a = next(x for x in plan_a["tasks"] if x["orchestration_task_id"] == "relay-activation-recipe")
        job_b = next(x for x in plan_b["tasks"] if x["orchestration_task_id"] == "relay-activation-recipe")
        a = candidate_from_orchestration(
            root=ROOT, orchestration_out=root_build / "run-a", orchestration_receipt=receipt_a,
            orchestration_task=job_a, policy_facts={"reviewed_priority": 10}, policy_source="review:phase14-board")
        b = candidate_from_orchestration(
            root=ROOT, orchestration_out=root_build / "run-b", orchestration_receipt=receipt_b,
            orchestration_task=job_b, policy_facts={"reviewed_priority": 10}, policy_source="review:phase14-board")
        readiness = PromotionEvaluator(root=ROOT).evaluate(
            conflict_set={"contract": "candidate-conflict-set.v0.1", "conflict_set_id": "phase14:provider-tie", "authority": "comparison_input", "candidates": [a, b]},
            policy=load("fixtures/promotion/phase13.explicit-rank.policy.json"),
        )
        assert readiness["status"] == "blocked"
        assert readiness["decisions"][0]["decision"] == "blocked_tie"
    finally:
        shutil.rmtree(root_build, ignore_errors=True)


def test_phase14_provider_path_has_no_canonical_or_runtime_write_authority() -> None:
    paths = [ROOT / "src/awa_assembler/provider.py", ROOT / "src/awa_orchestrator/providers.py", ROOT / "src/awa_promotion/bridge.py"]
    source = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.exists())
    for token in ["StateDelta(", "EntityDelta(", "registry.add(", "canonical_write=True"]:
        assert token not in source
