# Checkpoint 86 — Development Continuity and TL2 Weapon Penetration Integration

## Purpose

Checkpoint 86 has two deliberately separated workstreams:

1. **Deterministic documentation/authority consolidation with no gameplay effect.** It establishes a mandatory session bootstrap, separates game concepts from simulation/repository methodology, preserves durable opponent-AI lessons in the AI architecture, and prevents long-lived authorities from becoming checkpoint journals.
2. **Focused stochastic weapon-penetration study.** It measures family-specific APEN and SPEN sensitivities against the current layered-defense candidates without assuming symmetric progression across Kinetic, Energy, and Missile weapons.

The documentation work must not change combat mechanics. The stochastic study changes only per-variant weapon SPEN/APEN overrides in ScenarioRunner.

## Accepted continuation baseline

The continuation baseline is the native-accepted Checkpoint 85b repository. Its embedded evidence manifest and provenance are under `docs/validation/evidence/checkpoint-85b/` and are used to freeze unrelated production/test code.

Carried working candidates:

- Tactical Computer ordinary targeting +12 pp; degraded-fire penalty -25 pp; Evasive Compensation 0.
- Sensor Discrimination Resistance 1.
- ECM2 and ECCM2 normal ceilings at 1 TP/rating.
- Early Practical Fusion: 6 Operational TP / 6 Installation Space.
- Shield Capacity 3 / 3 Installation Space.
- Armor AP0 / AI5.

Armor AP1 remains deferred/experimental; AP1+AI5 remains an upper integration sensitivity.

## Documentation authority consolidation

CP86 must establish and preserve the following authority boundaries:

- `docs/Star_Cluster_Game_Concept_v0.6x.docx`: game concepts, player-facing mechanics, and durable game-design rules only.
- `CHAT_README.md`: mandatory new-session bootstrap and short authority/guardrail index.
- `docs/development/Simulation_Development_Guidelines.md`: simulation, calibration, permutation, validation, candidate lifecycle, and cross-TL methodology.
- `docs/development/Prototype_And_Technical_Guardrails.md`: prototype/technical ownership and implementation guardrails formerly misplaced in the Concept.
- `docs/development/Diagnostic_Event_Journal.md`: durable diagnostic/event-journal architecture formerly misplaced in the Concept.
- `docs/design/ai/AI_Doctrine_Registry_Architecture_v0_3.md`: reusable opponent-AI principles and lessons; never a raw checkpoint notebook.
- Technology Matrix/current machine profiles: current technology roles and candidate state without trial-count/hash chronology.
- Checkpoint/study/evidence artifacts: reproducible pass-specific definitions, hashes, trial counts, and results.

Long-lived authorities must be revised only when durable knowledge changes. They must not accumulate pass-by-pass result summaries.

## CP86 study design

Study ID: `tl2-itc12-weapon-penetration-layered-defense-permutations`

The active matrix is:

- **Weapon families:** Kinetic, Energy, Missile.
- **Penetration profiles per family:** control, +APEN, +SPEN, combined +APEN/+SPEN upper sensitivity.
- **Target defenses:** Shield 2 or 3 × AP0 or AP1, with AI5 fixed.
- **Information control:** Firm reference; DR1 + reactive ECCM1 against ECM2.
- **Geometry/order:** fixed Range 3; dynamic Side A first; dynamic Side B first.
- **Power:** both sides Reactor 6.

This is 3 × 4 × 4 × 2 × 3 = **288 variants**.

Current/sensitivity penetration profiles:

| Family | Control | +APEN | +SPEN | Combined upper sensitivity |
|---|---|---|---|---|
| Kinetic | SPEN1 / APEN0 | SPEN1 / APEN1 | SPEN2 / APEN0 | SPEN2 / APEN1 |
| Energy | SPEN1 / APEN1 | SPEN1 / APEN2 | SPEN2 / APEN1 | SPEN2 / APEN2 |
| Missile | SPEN1 / APEN2 | SPEN1 / APEN3 | SPEN2 / APEN2 | SPEN2 / APEN3 |

Damage, range, accuracy/guidance, power cost, ammunition, attack package/rate, missile terminal rules, and Installation Space remain held.

The common sensitivity matrix is an experimental instrument. It must **not** imply that every weapon family receives the same TL2 penetration improvement.

## Required outputs

The substantive stage must emit the normal integrated-combat outputs plus:

- `tl2-weapon-penetration-layered-defense-review.csv`
- `tl2-weapon-penetration-layered-defense-paired-deltas.csv`

The paired report must support control→APEN, control→SPEN, and control→combined comparisons plus an APEN×SPEN interaction view. Human review should compare family-specific benefit against Shield/AP defense, hull exposure, armor prevention, shield behavior, pacing, power pressure, PDS, and direct-fire/missile outcomes as appropriate.

## Blocking gates

Release gates are structural/mechanical, not desired win-rate targets. They must establish at minimum:

- all 288 variants reached the actual production consumer;
- penetration overrides affect only the selected weapon family/profile and do not alter held weapon properties;
- control values preserve Kinetic 1/0, Energy 1/1, Missile 1/2 SPEN/APEN references;
- Shield2/3 × AP0/1 with AI5 is fully covered;
- both sides hold Reactor6 and the declared information-control/geometry matrix;
- missile terminal guidance/track architecture is unchanged;
- no production weapon penetration or Armor AP1 value is automatically promoted;
- family-specific review remains required.

## Native acceptance

First run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-86\apply_checkpoint_86.ps1 -RepositoryOnly
```

Then normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-86\apply_checkpoint_86.ps1 -Jobs 24
```

Normal workload: 11 stages, 288 one-trial smoke executions, and 288 × 10,000 = **2,880,000 substantive trials**.

Deep Calibration remains opt-in and should run only if the normal result exposes a dependency-driven reason.

## Promotion boundary

Passing CP86 proves the experiment and documentation contracts executed correctly. It does not itself promote a weapon penetration value. Human review may identify different family-specific outcomes—for example one family advancing APEN, another SPEN, and another neither—and should preserve each family’s mechanical identity.
