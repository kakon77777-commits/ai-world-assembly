from __future__ import annotations
import json,sys,types,threading,urllib.error,urllib.request
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
class E:
    def __init__(self,i,t,n): self.entity_id=i; self.entity_type=t; self.name=n
class Registry:
    def __init__(self): self.d={'creature.crystal-filterer.001':E('creature.crystal-filterer.001','creature','Crystal Filterer'),'item.mineral-bloom':E('item.mineral-bloom','item','Mineral Bloom')}
    def contains(self,i): return i in self.d
    def get(self,i): return self.d[i]
    def values(self): return self.d.values()
class State:
    def __init__(self): self.d={('creature.crystal-filterer.001','position','room'):'room.abyss.feeding',('creature.crystal-filterer.001','biology','energy'):3,('creature.crystal-filterer.001','biology','growth_points'):2,('creature.crystal-filterer.001','lineage','stage'):'juvenile',('creature.crystal-filterer.001','lineage','organs'):[],('creature.crystal-filterer.001','lineage','egg_state'):'none',('item.mineral-bloom','position','room'):'room.abyss.feeding',('item.mineral-bloom','resource','amount'):2,('creature.crystal-filterer.001','secret','debug_token'):'no'}
    def get(self,o,n,k,d=None): return self.d.get((o,n,k),d)
class Event:
    def __init__(self): self.event_type='alien_lineage.creature_fed'
    def to_dict(self): return {'event_type':self.event_type,'source':'alien_lineage.runtime','payload':{'gain':2},'target':'creature.crystal-filterer.001','event_id':'e1','causation_id':None,'correlation_id':None,'timestamp_tick':0,'visibility':'public','authority':'runtime','version':1}
class Runtime:
    def __init__(self): self.package={'manifest':{'world_id':'alien-lineage.runtime-slice','world_version':'0.2.0'},'world':{'alien_lineage_runtime':{'species_ref':'species.crystal_filterer','stages':['juvenile','adult'],'resource_defaults':{'item.mineral-bloom':3}}}}; self.registry=Registry(); self.state=State(); self.event_log=types.SimpleNamespace(events=[]); self.last_action=None
    def submit(self,a): self.last_action=a; self.event_log.events.append(Event()); return types.SimpleNamespace(action_id=a.action_id,status=types.SimpleNamespace(value='completed'),message='ok',event_ids=[],changed_paths=[])
def fake(monkeypatch):
    class ActionIR:
        def __init__(self,actor_id,verb,target_id=None,args=None,authority='player'): self.actor_id=actor_id; self.verb=verb; self.target_id=target_id; self.args=args or {}; self.authority=authority; self.action_id='a1'
    m=types.ModuleType('compilableworld.models'); m.ActionIR=ActionIR; monkeypatch.setitem(sys.modules,'compilableworld',types.ModuleType('compilableworld')); monkeypatch.setitem(sys.modules,'compilableworld.models',m)
def binding(): return json.loads((ROOT/'fixtures/threejs/alien-lineage.presentation-binding.json').read_text())
def test_projection_and_reload_identity(monkeypatch):
    fake(monkeypatch); from awa_threejs.bridge import PresentationBridge
    b=PresentationBridge(Runtime(),'creature.crystal-filterer.001',binding()); p=b.projection(); assert 'secret' not in json.dumps(p); q=b.reload(); assert q['actor']['world_entity_id']==p['actor']['world_entity_id'] and q['generation']==p['generation']+1 and q['presentation_instance_id']!=p['presentation_instance_id']
def test_stale_and_actionir(monkeypatch):
    fake(monkeypatch); from awa_threejs.bridge import PresentationBridge,StalePresentationBinding
    r=Runtime(); b=PresentationBridge(r,'creature.crystal-filterer.001',binding()); p=b.projection(); result=b.submit_intent({'presentation_instance_id':p['presentation_instance_id'],'generation':p['generation'],'type':'feed','target_id':'item.mineral-bloom'}); assert r.last_action.verb=='feed' and r.last_action.authority=='presentation' and result['events'][0]['event_type']=='alien_lineage.creature_fed'; old=p; b.reload();
    with pytest.raises(StalePresentationBinding): b.submit_intent({'presentation_instance_id':old['presentation_instance_id'],'generation':old['generation'],'type':'feed','target_id':'item.mineral-bloom'})
def test_source_has_no_direct_world_mutation_api():
    s='\n'.join(p.read_text() for p in (ROOT/'presentation/threejs/src').glob('*.js')); assert not any(x in s for x in ['StateDelta','StateStore','registry.add(','growth_points +=','lineage.stage ='])
def test_asset_manifest_is_hash_bound(tmp_path):
    from awa_threejs.assets import sha256_file,verify_presentation_assets,PresentationAssetError
    (tmp_path/'x.js').write_text('ok'); (tmp_path/'presentation-assets.json').write_text(json.dumps({'target':'threejs','three_version':'0.180.0','artifacts':[{'path':'x.js','sha256':sha256_file(tmp_path/'x.js')}]})); assert verify_presentation_assets(tmp_path); (tmp_path/'x.js').write_text('bad');
    with pytest.raises(PresentationAssetError): verify_presentation_assets(tmp_path)

class RelayRegistry:
    def __init__(self):
        self.d={
            'operator.relay-runner.001':E('operator.relay-runner.001','character','Relay Runner'),
            'facility.storm-relay-core.001':E('facility.storm-relay-core.001','facility','Storm Relay Core'),
            'item.phase-coupler':E('item.phase-coupler','item','Phase Coupler'),
        }
    def contains(self,i): return i in self.d
    def get(self,i): return self.d[i]
    def values(self): return self.d.values()
class RelayState:
    def __init__(self): self.d={
        ('operator.relay-runner.001','position','room'):'room.relay.hangar',
        ('operator.relay-runner.001','contract','status'):'assigned',
        ('facility.storm-relay-core.001','position','room'):'room.relay.core',
        ('facility.storm-relay-core.001','maintenance','condition'):'damaged',
        ('facility.storm-relay-core.001','maintenance','coupler_delivered'):False,
        ('facility.storm-relay-core.001','signal','active'):False,
        ('item.phase-coupler','position','room'):'room.relay.hangar',
        ('item.phase-coupler','inventory','carrier'):None,
        ('facility.storm-relay-core.001','secret','debug_token'):'no',
    }
    def get(self,o,n,k,d=None): return self.d.get((o,n,k),d)
class RelayEvent:
    def __init__(self): self.event_type='relay_station.inspected'
    def to_dict(self): return {'event_type':self.event_type,'source':'relay_station.runtime','payload':{'kind':'coupler'},'target':'operator.relay-runner.001','event_id':'r1','causation_id':None,'correlation_id':None,'timestamp_tick':0,'visibility':'public','authority':'runtime','version':1}
class RelayRuntime:
    def __init__(self):
        self.package={'manifest':{'world_id':'relay-station.runtime-slice','world_version':'0.1.0'},'world':{'relay_station_runtime':{'runner_semantic_ref':'role.relay_runner','relay_semantic_ref':'facility.storm_relay','relay_entity_id':'facility.storm-relay-core.001','coupler_item_id':'item.phase-coupler','condition_default':'damaged','beacon':{'entity_id':'signal.beacon.001','semantic_ref':'signal.restored_link'}}}}
        self.registry=RelayRegistry(); self.state=RelayState(); self.event_log=types.SimpleNamespace(events=[]); self.last_action=None
    def submit(self,a): self.last_action=a; self.event_log.events.append(RelayEvent()); return types.SimpleNamespace(action_id=a.action_id,status=types.SimpleNamespace(value='completed'),message='ok',event_ids=[],changed_paths=[],changed_entities=[])
def relay_binding(): return json.loads((ROOT/'fixtures/threejs/relay-station.presentation-binding.json').read_text())

def test_relay_projection_is_allowlisted_and_independent(monkeypatch):
    fake(monkeypatch); from awa_threejs.bridge import PresentationBridge
    b=PresentationBridge(RelayRuntime(),'operator.relay-runner.001',relay_binding()); p=b.projection(); dumped=json.dumps(p)
    assert p['contract']=='relay-runtime-projection.v0.1'
    assert p['relay']['world_entity_id']=='facility.storm-relay-core.001'
    assert p['actor']['contract_status']=='assigned'
    assert p['visible_items'][0]['entity_id']=='item.phase-coupler'
    assert 'debug_token' not in dumped and 'secret' not in dumped

def test_relay_presentation_intent_becomes_actionir(monkeypatch):
    fake(monkeypatch); from awa_threejs.bridge import PresentationBridge
    r=RelayRuntime(); b=PresentationBridge(r,'operator.relay-runner.001',relay_binding()); p=b.projection()
    result=b.submit_intent({'presentation_instance_id':p['presentation_instance_id'],'generation':p['generation'],'type':'inspect','target_id':'item.phase-coupler'})
    assert r.last_action.verb=='inspect' and r.last_action.target_id=='item.phase-coupler' and r.last_action.authority=='presentation'
    assert result['projection']['contract']=='relay-runtime-projection.v0.1'
