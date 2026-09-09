from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_relay_presentation_recipe_repairs_authority_and_duration(tmp_path):
    from awa_assembler.loop import BoundedAssembler
    from awa_assembler.provider import reference_producer_for
    task=json.loads((ROOT/'fixtures/assembler/relay-station.activation-effect-recipe.task.json').read_text())
    receipt=BoundedAssembler(root=ROOT,producer=reference_producer_for(task)).run(
        task=task,
        project_state=ROOT/'PROJECT_STATE.json',
        semantic_snapshot=ROOT/'fixtures/sedb/expected.game.relay_station.snapshot.json',
        composition_receipt=ROOT/'fixtures/csc_ocm/expected.relay_station.composition-receipt.json',
        presentation_binding=ROOT/'fixtures/threejs/relay-station.presentation-binding.json',
        capability_contract=ROOT/'fixtures/assembler/presentation_recipe_generation.capability.json',
        nodes=ROOT/'fixtures/relay_presentation_graph/nodes',
        edges=ROOT/'fixtures/relay_presentation_graph/edges',
        artifacts=ROOT/'fixtures/relay_presentation_graph/artifacts',
        validations=ROOT/'fixtures/relay_presentation_graph/validations',
        out=tmp_path/'out')
    assert receipt['status']=='validated_candidate'
    assert [x['validation_status'] for x in receipt['attempts']]==['failed','passed']
    assert receipt['attempts'][0]['artifact_sha256']=='ca1997484da2fdcd0ae3f7fd00f21837016883e4d84ddcf30f96909cf24a577b'
    assert receipt['attempts'][1]['artifact_sha256']=='ea8e25f916df287242fa2096933f7576c3f8efa560245d05e067dbb6f9f11817'
    first='\n'.join(receipt['attempts'][0]['diagnostics'])
    assert 'state_delta' in first and 'duration_ms' in first
    assert receipt['graph_preview']['missing_required']==0
    assert receipt['graph_preview']['generation_tasks']==0
    assert receipt['graph_preview']['target_effective_status']=='passed'
    assert receipt['promotion']['canonical_write'] is False
    candidate=json.loads((tmp_path/'out/candidate/relay_activation_effect_recipe.json').read_text())
    assert candidate['contract']=='presentation-effect-recipe.v0.2'
    assert candidate['event_type']=='relay_station.relay_activated'
    assert candidate['effect']['target']=='relay_visual'
    assert 'state_delta' not in candidate
