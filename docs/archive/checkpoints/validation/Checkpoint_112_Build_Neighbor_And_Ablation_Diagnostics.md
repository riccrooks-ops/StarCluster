# Checkpoint 112 - Build-Neighbor and Ablation Diagnostics

## Purpose

CP112 decomposes the strongest native CP111 same-TL ecology review signals before any numerical retuning. It adds targeted Energy-defense ablations, movement-order/start-range diagnostics, and late-Missile attrition defense ablations.

## Authority boundary

- Accepted simulation/instrumentation baseline: Checkpoint 111.
- Candidate numerical matrix: Checkpoint 109.
- Reactor candidates: Checkpoint 110 first-pass retained values.
- Concept authority: v0.7j, unchanged by CP112.
- Production runtime: C# / Godot, unchanged.
- Research/test consumer: Python.
- Damage model: `layered_defense_hull_only`; internal critical/subsystem damage remains excluded.

## Workload

The study contains 1,200 variants. The checked-in authoring evidence uses 100 trials/variant (120,000 engagements). Native substantive acceptance uses 2,000 trials/variant (2,400,000 engagements), preceded by Python self-tests, 25 deterministic C#/Python parity fixtures, and a one-trial all-variant smoke.

## Blocking gates

Only execution/instrumentation/repository correctness is blocking: no trial errors, exact-fill build construction, declared variant shape, expected telemetry, frozen production/numerical authority, accepted CP111 provenance, and manifest integrity. Balance/outcome thresholds are non-blocking.

## Candidate interpretation

The bounded authoring pass indicates three strong hypotheses for native confirmation:

1. Energy defense-specialist robustness is primarily driven by the Shield package, with the Energy main weapon a secondary contributor.
2. TL7/TL9 Kinetic-vs-Missile movement-order cliffs persist across shorter starting ranges and are not solely an edge-start artifact.
3. Late Missile-balanced vs Missile-defense stalemates are primarily a Shield sustain/damage-packet threshold interaction rather than a 60-turn timeout or a PDS-only effect.

No numerical change is promoted by CP112.
