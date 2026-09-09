export function assertEffectRecipe(recipe){
  if(!recipe||!['presentation-effect-recipe.v0.1','presentation-effect-recipe.v0.2'].includes(recipe.contract))throw new Error('invalid effect recipe contract');
  const allowed=new Set(['contract','recipe_id','event_type','effect','version']);for(const key of Object.keys(recipe))if(!allowed.has(key))throw new Error(`invalid effect recipe field: ${key}`);
  const e=recipe.effect;const effectAllowed=new Set(['target','scale_peak','duration_ms','emissive_boost']);if(e)for(const key of Object.keys(e))if(!effectAllowed.has(key))throw new Error(`invalid effect field: ${key}`);
  if(!e||!['creature_visual','relay_visual'].includes(e.target))throw new Error('unsupported effect recipe target');
  if(recipe.contract==='presentation-effect-recipe.v0.1'&&(recipe.event_type!=='alien_lineage.creature_mutated'||e.target!=='creature_visual'||recipe.version!=='v0.1'))throw new Error('unsupported v0.1 effect recipe semantics');
  if(recipe.contract==='presentation-effect-recipe.v0.2'&&recipe.version!=='v0.2')throw new Error('unsupported v0.2 effect recipe version');
  if(!(e.scale_peak>=1&&e.scale_peak<=1.3))throw new Error('effect recipe scale_peak out of bounds');
  if(!Number.isInteger(e.duration_ms)||e.duration_ms<50||e.duration_ms>400)throw new Error('effect recipe duration_ms out of bounds');
  if(!(e.emissive_boost>=0&&e.emissive_boost<=2))throw new Error('effect recipe emissive_boost out of bounds');
  return recipe;
}

export function applyEffectRecipe(recipe,{creature,relay,schedule=setTimeout}={}){
  assertEffectRecipe(recipe);const visual=recipe.effect.target==='relay_visual'?relay:creature;
  if(!visual?.scale?.setScalar)return {applied:false,recipe_id:recipe.recipe_id};
  const effect=recipe.effect,materials=[];visual.traverse?.(child=>{const raw=child.material;if(!raw)return;for(const material of (Array.isArray(raw)?raw:[raw]))if(typeof material.emissiveIntensity==='number')materials.push([material,material.emissiveIntensity]);});
  visual.scale.setScalar(effect.scale_peak);for(const [material,base] of materials)material.emissiveIntensity=base+effect.emissive_boost;
  schedule(()=>{visual?.scale?.setScalar?.(1);for(const [material,base] of materials)material.emissiveIntensity=base;},effect.duration_ms);
  return {applied:true,recipe_id:recipe.recipe_id,duration_ms:effect.duration_ms,target:effect.target};
}
