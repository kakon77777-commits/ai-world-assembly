const EVENT_EFFECTS=Object.freeze({
  'movement.actor_moved':'move-entity',
  'alien_lineage.creature_fed':'pulse-feed',
  'alien_lineage.creature_mutated':'rebuild-creature',
  'alien_lineage.creature_grew':'rebuild-creature',
  'alien_lineage.egg_laid':'egg-effect',
  'alien_lineage.egg_hatched':'hatch-effect',
  'alien_lineage.rift_entered':'rift-transition',
  'relay_station.inspected':'inspect-pulse',
  'relay_station.coupler_picked':'cargo-picked',
  'relay_station.coupler_delivered':'cargo-delivered',
  'relay_station.relay_repaired':'relay-rebuild',
  'relay_station.relay_activated':'relay-activated'
});
export function makeIntent(projection,type,fields={}){return {presentation_instance_id:projection.presentation_instance_id,generation:projection.generation,type,...fields};}
export function effectForEvent(eventType){return EVENT_EFFECTS[eventType]??null;}
export function applyBridgeResponse(state,response){return {projection:response.projection,effects:(response.events??[]).map(e=>effectForEvent(e.event_type)).filter(Boolean)};}
export {EVENT_EFFECTS};
