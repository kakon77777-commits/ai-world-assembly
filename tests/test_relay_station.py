from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_relay_station_package_and_contracts_exist():
    from awa_relay_station.runtime import RelayStationModule
    from awa_relay_station.activation import RelayActivationModule
    assert RelayStationModule is not None
    assert RelayActivationModule is not None
    assert (ROOT / 'schemas/relay-station-runtime-slice.v0.1.schema.json').is_file()
    assert (ROOT / 'schemas/relay-runtime-projection.v0.1.schema.json').is_file()


def test_relay_station_fixtures_are_second_world_not_alien_lineage():
    semantic = json.loads((ROOT / 'fixtures/sedb/expected.game.relay_station.snapshot.json').read_text())
    profile = json.loads((ROOT / 'fixtures/csc_ocm/relay_station.profile.json').read_text())
    binding = json.loads((ROOT / 'fixtures/threejs/relay-station.presentation-binding.json').read_text())
    assert semantic['namespace'] == 'game.relay_station'
    assert all('alien_lineage' not in module for module in profile['modules']['required'])
    assert binding['semantic_role'] == 'relay_station.runtime_projection'
    assert set(binding['input_action_map']) >= {'inspect','pick_up','deliver','repair','activate'}


def test_relay_activation_source_does_not_mutate_registry_directly():
    source = (ROOT / 'src/awa_relay_station/activation.py').read_text()
    assert 'EntityDelta' in source
    assert 'entity_transaction/v0.1' in source
    assert 'registry.add(' not in source
    assert 'registry.remove(' not in source

def _load(path): return json.loads(path.read_text())

def test_relay_station_build_is_deterministic_and_matches_golden():
    from awa_relay_station.build import build_runtime_authoring_files
    files,receipt=build_runtime_authoring_files(
        _load(ROOT/'fixtures/sedb/expected.game.relay_station.snapshot.json'),
        _load(ROOT/'fixtures/csc_ocm/expected.relay_station.composition-receipt.json'),
        _load(ROOT/'fixtures/relay_asset_graph/expected.graph-snapshot.json'),
        _load(ROOT/'fixtures/relay_station_runtime/relay_station.intake-plan.json'),
        _load(ROOT/'fixtures/relay_station_runtime/runtime-slice.json'),root=ROOT)
    assert receipt['authoring_sha256']=='7d6ec14e8ec496e1dc55aa15e60b3bb44d87ab0a936d37faef4e939d23c65c96'
    golden=ROOT/'fixtures/relay_station_runtime/expected_authoring'
    for rel,text in files.items(): assert (golden/rel).read_text()==text
    assert _load(golden/'awa-relay-station-runtime-receipt.json')==receipt

def test_relay_beacon_cannot_collide_with_authored_entity():
    from awa_relay_station.build import build_runtime_authoring_files,RelayStationBuildError
    semantic=_load(ROOT/'fixtures/sedb/expected.game.relay_station.snapshot.json'); comp=_load(ROOT/'fixtures/csc_ocm/expected.relay_station.composition-receipt.json'); graph=_load(ROOT/'fixtures/relay_asset_graph/expected.graph-snapshot.json'); plan=_load(ROOT/'fixtures/relay_station_runtime/relay_station.intake-plan.json'); slice_doc=_load(ROOT/'fixtures/relay_station_runtime/runtime-slice.json')
    slice_doc['runtime_config']['beacon']['entity_id']='operator.relay-runner.001'
    with pytest.raises(RelayStationBuildError,match='beacon ID'): build_runtime_authoring_files(semantic,comp,graph,plan,slice_doc,root=ROOT)
