# Architecture Boundaries

```text
SEDB
  semantic/content authority
      |
      v
AI World Assembly contracts/adapters
      |
      +--> CSC-OCM composition
      |
      +--> Dynamic Asset Graph assembly topology
      |
      v
CompilableWorld
  runtime world-state authority
      |
      v
Presentation adapter
  Three.js first
```

## Never conflate these

- Semantic canon != runtime state.
- Runtime state != presentation-local state.
- Fragment != artifact.
- Fragment != module.
- Capability != authority.
- Generation != canonicalization.
- Asset dependency != runtime causality.
- Scene graph != Dynamic Asset Graph.
- Conversation history != canonical project state.
