export function assertEffectRecipe(recipe){
  if(!recipe||recipe.contract!=='presentation-effect-recipe.v0.1')throw new Error('invalid effect recipe contract');
  const allowed=new Set(['contract','recipe_id','event_type','effect','version']);for(const key of Object.keys(recipe))if(!allowed.has(key))throw new Error(`invalid effect recipe field: ${key}`);
  if(recipe.event_type!=='alien_lineage.creature_mutated')throw new Error('unsupported effect recipe event');
  const e=recipe.effect;
  const effectAllowed=new Set(['target','scale_peak','duration_ms','emissive_boost']);if(e)for(const key of Object.keys(e))if(!effectAllowed.has(key))throw new Error(`invalid effect field: ${key}`);
  if(!e||e.target!=='creature_visual')throw new Error('unsupported effect recipe target');
  if(!(e.scale_peak>=1&&e.scale_peak<=1.3))throw new Error('effect recipe scale_peak out of bounds');
  if(!Number.isInteger(e.duration_ms)||e.duration_ms<50||e.duration_ms>400)throw new Error('effect recipe duration_ms out of bounds');
  if(!(e.emissive_boost>=0&&e.emissive_boost<=2))throw new Error('effect recipe emissive_boost out of bounds');
  return recipe;
}

export function applyEffectRecipe(recipe,{creature,schedule=setTimeout}={}){
  assertEffectRecipe(recipe);
  if(!creature?.scale?.setScalar)return {applied:false,recipe_id:recipe.recipe_id};
  const effect=recipe.effect,materials=[];
  creature.traverse?.(child=>{
    const raw=child.material;
    if(!raw)return;
    for(const material of (Array.isArray(raw)?raw:[raw])){
      if(typeof material.emissiveIntensity==='number')materials.push([material,material.emissiveIntensity]);
    }
  });
  creature.scale.setScalar(effect.scale_peak);
  for(const [material,base] of materials)material.emissiveIntensity=base+effect.emissive_boost;
  schedule(()=>{
    creature?.scale?.setScalar?.(1);
    for(const [material,base] of materials)material.emissiveIntensity=base;
  },effect.duration_ms);
  return {applied:true,recipe_id:recipe.recipe_id,duration_ms:effect.duration_ms};
}
