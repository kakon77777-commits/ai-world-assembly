# Phase 7 — Three.js Presentation Adapter

Phase 7 makes the bounded Alien Lineage world visible in Three.js without moving world authority into the browser.

## Authority path

```text
Browser input -> presentation intent + generation -> Python AWA sidecar -> CompilableWorld ActionIR -> Runtime Module / Kernel -> StateDelta + EventIR -> receipt + incremental EventIR + new projection -> Three.js geometry / VFX / UI
```

The browser never receives a StateStore or EntityRegistry write path. `runtime-projection.v0.1` is allowlisted: actor identity/location, bounded biology/lineage state, visible authored resources, available actions and generation-bound bindings only.

`world_entity_id` is stable Runtime identity. Reload creates a new `presentation_instance_id` and increments generation; stale intents fail with HTTP 409 before ActionIR creation.

EventIR maps to presentation-only effects: movement reprojects, feed pulses, mutation/growth rebuild procedural geometry, egg/hatch trigger local effects and rift triggers a transient scene transition. JavaScript always replaces state from the returned Runtime projection; it does not calculate growth, mutation, reproduction or worldline rules.

The target pins Three.js `0.180.0`. The build copies the local presentation sources and required Three.js module/core into `dist/`, emits `presentation-assets.json`, and `awa-threejs verify-assets` recomputes SHA-256 before the browser gate.

CI compiles the real Phase 6 package, builds the Three.js target, starts the localhost sidecar and launches headless Chromium. Smoke mode proves hydration, reload identity separation, browser input -> ActionIR, feed through the Kernel, mutation EventIR -> geometry rebuild, and DOM state from the new Runtime projection.

WebSocket, multiplayer, dynamic EntityRegistry spawn and a second presentation engine remain outside Phase 7.
