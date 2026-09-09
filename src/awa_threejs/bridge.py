from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from uuid import uuid4
from awa_contracts.validator import validation_errors

class PresentationBridgeError(ValueError): pass
class StalePresentationBinding(PresentationBridgeError): pass

class PresentationBridge:
    def __init__(self,runtime:Any,actor_id:str,presentation_binding:dict[str,Any],*,root:str|Path|None=None):
        self.runtime=runtime; self.actor_id=actor_id; self.root=Path(root) if root else Path(__file__).resolve().parents[2]
        self.binding=self._validate_binding(presentation_binding)
        if not runtime.registry.contains(actor_id): raise PresentationBridgeError(f"presentation actor does not exist: {actor_id}")
        self.generation=0; self.presentation_instance_id=""; self.reload()
    def _schema(self,name:str)->dict[str,Any]: return json.loads((self.root/"schemas"/f"{name}.schema.json").read_text(encoding="utf-8"))
    def _validate_binding(self,binding):
        errors=validation_errors(self._schema("presentation-binding.v0.1"),binding)
        if errors: raise PresentationBridgeError("invalid Three.js presentation binding: "+"; ".join(errors))
        if binding["target"]!="threejs": raise PresentationBridgeError("presentation binding target must be threejs")
        if binding["semantic_role"] not in {"alien_lineage.runtime_projection","relay_station.runtime_projection"}: raise PresentationBridgeError("unsupported Three.js semantic_role")
        return binding
    def reload(self):
        self.generation+=1; self.presentation_instance_id=f"threejs:session:{uuid4().hex}"; return self.projection()
    @staticmethod
    def _int(value,default=0):
        if value is None: return default
        if isinstance(value,bool) or not isinstance(value,(int,float)) or int(value)!=value or value<0: raise PresentationBridgeError("projected numeric state is invalid")
        return int(value)
    def _binding_doc(self,entity_id:str,refs:list[str]):
        return {"contract":"runtime-binding.v0.1","world_entity_id":entity_id,"presentation_instance_id":f"{self.presentation_instance_id}:entity:{entity_id}","generation":self.generation,"binding_type":"entity","semantic_asset_refs":list(dict.fromkeys(refs))}
    def projection(self):
        return self._projection_relay() if self.binding["semantic_role"]=="relay_station.runtime_projection" else self._projection_alien()
    def _projection_alien(self):
        config=self.runtime.package.get("world",{}).get("alien_lineage_runtime")
        if not isinstance(config,dict): raise PresentationBridgeError("Alien Lineage runtime config is missing")
        manifest=self.runtime.package["manifest"]; actor=self.runtime.registry.get(self.actor_id); room=self.runtime.state.get(self.actor_id,"position","room")
        if not isinstance(room,str) or not room: raise PresentationBridgeError("actor position is not projectable")
        organs=self.runtime.state.get(self.actor_id,"lineage","organs",[])
        if not isinstance(organs,list) or any(not isinstance(x,str) for x in organs): raise PresentationBridgeError("lineage organs are not projectable")
        resources=[]; defaults=config.get("resource_defaults",{})
        for entity in sorted(self.runtime.registry.values(),key=lambda x:x.entity_id):
            eroom=self.runtime.state.get(entity.entity_id,"position","room")
            if entity.entity_type=="item" and eroom==room and entity.entity_id in defaults:
                resources.append({"entity_id":entity.entity_id,"name":entity.name,"room_id":eroom,"amount":self._int(self.runtime.state.get(entity.entity_id,"resource","amount",defaults[entity.entity_id]))})
        refs=list(dict.fromkeys([config["species_ref"],*organs])); stages=config.get("stages",[]); stage_default=stages[0] if stages else "unknown"
        doc={"contract":"runtime-projection.v0.1","world_id":manifest["world_id"],"world_version":manifest["world_version"],"projection_revision":len(self.runtime.event_log.events),"presentation_instance_id":self.presentation_instance_id,"generation":self.generation,"actor":{"world_entity_id":self.actor_id,"name":actor.name,"room_id":room,"worldline":self.runtime.state.get(self.actor_id,"world","worldline"),"biology":{"energy":self._int(self.runtime.state.get(self.actor_id,"biology","energy",0)),"growth_points":self._int(self.runtime.state.get(self.actor_id,"biology","growth_points",0))},"lineage":{"stage":self.runtime.state.get(self.actor_id,"lineage","stage",stage_default),"organs":list(organs),"egg_state":self.runtime.state.get(self.actor_id,"lineage","egg_state","none"),"child_stage":self.runtime.state.get(self.actor_id,"lineage","child_stage"),"child_species":self.runtime.state.get(self.actor_id,"lineage","child_species"),"last_rift":self.runtime.state.get(self.actor_id,"lineage","last_rift")}},"visible_resources":resources,"available_actions":sorted(self.binding["input_action_map"]),"bindings":[self._binding_doc(self.actor_id,refs)]}
        errors=validation_errors(self._schema("runtime-projection.v0.1"),doc)
        if errors: raise PresentationBridgeError("runtime projection violates contract: "+"; ".join(errors))
        return doc
    def _projection_relay(self):
        world=self.runtime.package.get("world",{}); config=world.get("relay_station_runtime")
        if not isinstance(config,dict): raise PresentationBridgeError("Relay Station runtime config is missing")
        manifest=self.runtime.package["manifest"]; actor=self.runtime.registry.get(self.actor_id); relay_id=config["relay_entity_id"]
        if not self.runtime.registry.contains(relay_id): raise PresentationBridgeError("Relay Station relay entity is missing")
        relay=self.runtime.registry.get(relay_id); room=self.runtime.state.get(self.actor_id,"position","room"); relay_room=self.runtime.state.get(relay_id,"position","room")
        if not isinstance(room,str) or not room or not isinstance(relay_room,str) or not relay_room: raise PresentationBridgeError("Relay Station positions are not projectable")
        visible=[]
        for entity in sorted(self.runtime.registry.values(),key=lambda x:x.entity_id):
            eroom=self.runtime.state.get(entity.entity_id,"position","room")
            carrier=self.runtime.state.get(entity.entity_id,"inventory","carrier")
            if entity.entity_type=="item" and eroom==room and carrier in {None,""}:
                visible.append({"entity_id":entity.entity_id,"name":entity.name,"room_id":eroom})
        condition=self.runtime.state.get(relay_id,"maintenance","condition",config.get("condition_default","damaged")); status=self.runtime.state.get(self.actor_id,"contract","status","assigned")
        refs_actor=[config["runner_semantic_ref"]]; refs_relay=[config["relay_semantic_ref"]]
        bindings=[self._binding_doc(self.actor_id,refs_actor),self._binding_doc(relay_id,refs_relay)]
        beacon=config["beacon"]; beacon_id=beacon["entity_id"]
        if self.runtime.registry.contains(beacon_id): bindings.append(self._binding_doc(beacon_id,[beacon["semantic_ref"]]))
        doc={"contract":"relay-runtime-projection.v0.1","world_id":manifest["world_id"],"world_version":manifest["world_version"],"projection_revision":len(self.runtime.event_log.events),"presentation_instance_id":self.presentation_instance_id,"generation":self.generation,"actor":{"world_entity_id":self.actor_id,"name":actor.name,"room_id":room,"cargo_id":self.runtime.state.get(self.actor_id,"cargo","current"),"contract_status":status},"relay":{"world_entity_id":relay_id,"name":relay.name,"room_id":relay_room,"condition":condition,"coupler_delivered":self.runtime.state.get(relay_id,"maintenance","coupler_delivered",False) is True,"active":self.runtime.state.get(relay_id,"signal","active",False) is True},"visible_items":visible,"available_actions":sorted(self.binding["input_action_map"]),"bindings":bindings}
        errors=validation_errors(self._schema("relay-runtime-projection.v0.1"),doc)
        if errors: raise PresentationBridgeError("relay runtime projection violates contract: "+"; ".join(errors))
        return doc
    def _action(self,intent):
        from compilableworld.models import ActionIR
        if not isinstance(intent,dict): raise PresentationBridgeError("presentation intent must be an object")
        kind=intent.get("type"); mapping=self.binding["input_action_map"]
        if not isinstance(kind,str) or kind not in mapping: raise PresentationBridgeError("unsupported presentation intent")
        verb=mapping[kind]; target=None; args={}; allowed={"presentation_instance_id","generation","type"}
        if kind=="move":
            allowed.add("direction"); direction=intent.get("direction")
            if direction not in {"north","south","east","west","up","down"}: raise PresentationBridgeError("move intent direction is invalid")
            args["direction"]=direction
        elif kind=="feed":
            allowed.add("target_id"); target=intent.get("target_id")
            if not isinstance(target,str) or not target: raise PresentationBridgeError("feed intent requires target_id")
        elif kind=="mutate":
            allowed.add("organ_id"); organ=intent.get("organ_id")
            if not isinstance(organ,str) or not organ: raise PresentationBridgeError("mutate intent requires organ_id")
            args["organ_id"]=organ
        elif kind=="enter_rift":
            allowed.add("rift_id"); rift=intent.get("rift_id")
            if not isinstance(rift,str) or not rift: raise PresentationBridgeError("enter_rift intent requires rift_id")
            args["rift_id"]=rift
        elif kind in {"inspect","pick_up","deliver","repair","activate"}:
            allowed.add("target_id"); target=intent.get("target_id")
            if not isinstance(target,str) or not target: raise PresentationBridgeError(f"{kind} intent requires target_id")
        extra=set(intent)-allowed
        if extra: raise PresentationBridgeError(f"presentation intent contains unknown fields: {sorted(extra)}")
        return ActionIR(self.actor_id,verb,target_id=target,args=args,authority="presentation")
    def submit_intent(self,intent):
        if intent.get("presentation_instance_id")!=self.presentation_instance_id or intent.get("generation")!=self.generation: raise StalePresentationBinding("stale presentation binding")
        action=self._action(intent); start=len(self.runtime.event_log.events); receipt=self.runtime.submit(action)
        return {"receipt":{"action_id":receipt.action_id,"status":receipt.status.value,"message":receipt.message,"event_ids":list(receipt.event_ids),"changed_paths":list(receipt.changed_paths),"changed_entities":list(getattr(receipt,"changed_entities",[]))},"events":[e.to_dict() for e in self.runtime.event_log.events[start:]],"projection":self.projection()}
