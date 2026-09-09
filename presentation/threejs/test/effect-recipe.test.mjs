import test from 'node:test';
import assert from 'node:assert/strict';
import {assertEffectRecipe,applyEffectRecipe} from '../src/effect-recipe.js';

const recipe={contract:'presentation-effect-recipe.v0.1',recipe_id:'effect.mutation-pulse',event_type:'alien_lineage.creature_mutated',effect:{target:'creature_visual',scale_peak:1.16,duration_ms:180,emissive_boost:.7},version:'v0.1'};

test('effect recipe is presentation-only and bounded',()=>{
  assert.equal(assertEffectRecipe(recipe),recipe);
  assert.throws(()=>assertEffectRecipe({...recipe,runtime_action:'mutate'}),/invalid|unsupported|bounds|contract/);
});

test('effect recipe changes only presentation object state',()=>{
  const calls=[];const material={emissiveIntensity:.4};
  const creature={scale:{setScalar:v=>calls.push(['scale',v])},traverse:fn=>fn({material})};
  const result=applyEffectRecipe(recipe,{creature,schedule:fn=>fn()});
  assert.equal(result.applied,true);
  assert.deepEqual(calls,[['scale',1.16],['scale',1]]);
  assert.equal(material.emissiveIntensity,.4);
});
