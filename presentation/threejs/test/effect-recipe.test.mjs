import test from 'node:test';
import assert from 'node:assert/strict';
import {assertEffectRecipe,applyEffectRecipe} from '../src/effect-recipe.js';

const recipe={contract:'presentation-effect-recipe.v0.1',recipe_id:'effect.mutation-pulse',event_type:'alien_lineage.creature_mutated',effect:{target:'creature_visual',scale_peak:1.16,duration_ms:180,emissive_boost:.7},version:'v0.1'};
const relayRecipe={contract:'presentation-effect-recipe.v0.2',recipe_id:'effect.relay-activation-pulse',event_type:'relay_station.relay_activated',effect:{target:'relay_visual',scale_peak:1.12,duration_ms:220,emissive_boost:.8},version:'v0.2'};

test('effect recipe is presentation-only and bounded',()=>{assert.equal(assertEffectRecipe(recipe),recipe);assert.throws(()=>assertEffectRecipe({...recipe,runtime_action:'mutate'}),/invalid|unsupported|bounds|contract/);});
test('v0.2 relay effect recipe is accepted without runtime authority',()=>{assert.equal(assertEffectRecipe(relayRecipe),relayRecipe);assert.throws(()=>assertEffectRecipe({...relayRecipe,state_delta:{}}),/invalid/);});
test('effect recipe changes only presentation object state',()=>{const calls=[];const material={emissiveIntensity:.4};const creature={scale:{setScalar:v=>calls.push(['scale',v])},traverse:fn=>fn({material})};const result=applyEffectRecipe(recipe,{creature,schedule:fn=>fn()});assert.equal(result.applied,true);assert.deepEqual(calls,[['scale',1.16],['scale',1]]);assert.equal(material.emissiveIntensity,.4);});
test('relay effect targets relay visual only',()=>{const creatureCalls=[],relayCalls=[];const relay={scale:{setScalar:v=>relayCalls.push(v)},traverse:()=>{}};const creature={scale:{setScalar:v=>creatureCalls.push(v)},traverse:()=>{}};const result=applyEffectRecipe(relayRecipe,{creature,relay,schedule:fn=>fn()});assert.equal(result.target,'relay_visual');assert.deepEqual(relayCalls,[1.12,1]);assert.deepEqual(creatureCalls,[]);});
