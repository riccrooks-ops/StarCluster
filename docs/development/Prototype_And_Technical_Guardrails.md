# Prototype and Technical Guardrails

## Ownership boundary

The rules engine is engine-independent C#/.NET. `StarCluster.Core` owns authoritative game mechanics and state transitions. `StarCluster.ScenarioRunner` is a thin data-driven host for deterministic and stochastic studies. The Godot client owns presentation and interaction and must not silently duplicate or redefine Core rules.

The project currently targets the pinned .NET SDK declared by the active checkpoint and the Godot .NET presentation lane. Version changes are development decisions and require deliberate validation rather than Concept edits.

## Prototype-scope discipline

Prototype slices should expose the smallest coherent set of strategic and tactical mechanics needed to validate the next design question. They may deliberately limit content breadth, visuals, enemy variety, or map population while preserving authoritative mechanics and persistence required by the slice.

A prototype limitation is not automatically a game-design prohibition. Permanent gameplay rules belong in the Concept.

## Technical principles

- Keep deterministic game-state logic separate from presentation.
- Prefer data-driven component/scenario definitions over special-case study code.
- Preserve deterministic seeded replay and machine-readable outputs for reproducibility.
- New mechanics begin with small deterministic contract cases before broad stochastic balance work.
- Debug presentation may expose authoritative hidden state only in explicitly development-only views; normal player-facing presentation must obey game information rules.
- Full-repository checkpoints and manifests are development/release artifacts, not game concepts.
- System-entry and scenario-reset initialization must follow the same observer-safe Track Update path so reset/re-entry cannot expose hidden authoritative occupants before legitimate detection.

## Stable technical identity and platform boundaries

- Component records use stable machine identifiers even when player-facing display names change. Save data, scenarios, evidence, and tooling should bind to stable IDs rather than mutable labels.
- Campaign/system map dimensions may be configuration-driven; technical code must not hard-code one map radius when the game rule permits variable campaign scale.
- The current presentation target is Windows desktop with mouse/keyboard through the Godot .NET lane. Platform-target changes are technical/product decisions and do not belong in the Game Concept.
- Seeded authoritative resolution must remain stable across save/reload and independent of parallel worker scheduling where the design declares reproducibility. Worker order must not change game outcomes.

## First-slice and regression ownership

Detailed checkpoint procedures, scenario actions, screenshots, logs, and expected outputs belong in active validation runbooks and their archives. They should not accumulate here. This document records only reusable technical boundaries.
