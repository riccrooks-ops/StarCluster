# Checkpoint 116 — Warhead Role Orthogonality and Generational Scaling

## Status
Candidate pending native Windows acceptance. Checkpoint 115a is the accepted baseline.

## Purpose
Checkpoint 116 tests whether Missile general-purpose energetic maturation can remain distinct from mission specialization. It directly addresses the CP115a confound where later GP candidates increased DAM, SPEN, and APEN together.

The checkpoint also verifies that specialist Missile payloads and specialist Kinetic packets scale with their contemporary technology generation instead of being judged with frozen early-TL packet sizes.

## Design boundary
- GP energetic maturation and specialist penetration are separate axes.
- CP116 **pure GP** candidates raise DAM while holding the study baseline at SPEN 1 / APEN 2.
- SPEN-only, APEN-only, and bundled-penetration GP profiles are matched-DAM diagnostic controls, not promotion candidates.
- The SPEN 1 / APEN 2 baseline is itself a study control, not a final production rule.
- Generation-relative Missile specialists retain contemporary energetic scale while paying explicit role tradeoffs.
- Static CP115-style specialists remain controls for artificial obsolescence.
- Kinetic saturation/tandem candidates derive from contemporary projectile scale and still use one battery/one attack roll.
- Family asymmetry is intentional; controlled fixtures expose niches and are not balance-promotion gates.
- Damage scope remains `layered_defense_hull_only`; internal critical/subsystem damage is not simulated.
- No candidate promotes automatically.

## Population
- 2,976 mirrored variants.
- 2,176 Missile variants.
- 672 Kinetic variants.
- 128 native Energy-reference variants.
- 138 underlying exact-fill builds.
- Eight target fixtures: five legal exact-fill targets plus three controlled characteristic-space fixtures.
- 616 deterministic packet-layer probe rows.

## Checked-in authoring evidence
- 25 trials per variant.
- 74,400 engagements.
- Zero failed gates.
- 128 adaptive-pair summary rows; 20 show at least one natural observer-safe switch.

The authoring evidence is diagnostic only. Its most important signal is that matched-DAM late-TL SPEN controls can produce very large performance changes, demonstrating that hidden penetration growth materially changes the GP role.

## Native workload
The normal validation invocation runs:

- 2,976 variants × 2,000 trials = **5,952,000 engagements**.

`-RepositoryOnly` skips that substantive run while executing all deterministic/reconstruction checks and one-trial regression populations.

## Acceptance sequence
```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-116\apply_checkpoint_116.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-116\apply_checkpoint_116.ps1
```

## Acceptance gates
Before the substantive study, the wrapper must pass:
1. CPython 3.13 runtime resolution and production-language boundary notice.
2. Automatic pre-package root hygiene apply/check.
3. CP116 static preflight:
   - no trial-count-dependent blocking gates in the CP116 analysis path;
   - pure GP profiles exactly preserve the declared baseline SPEN/APEN;
   - single-axis and bundled controls are explicitly declared;
   - no accidental cross-generation specialist pairing.
4. All 77 Python self-tests.
5. All 25 C#/Python parity fixtures.
6. CP114 one-trial regression smoke: 3,184 variants.
7. CP115a/CP115 one-trial regression smoke: 4,064 variants.
8. CP116 one-trial smoke: 2,976 variants.
9. Deterministic repository/evidence contract and full repository manifest.

The normal invocation additionally requires the 5,952,000-engagement CP116 substantive study to complete with zero failed gates.

## Frozen authorities
CP116 does not change or promote:
- the CP109 whole-ladder numerical candidate matrix;
- the CP110 Reactor candidate profile;
- the active Concept v0.7k;
- production C#/Godot gameplay code;
- the CP115 study definition/population;
- the accepted CP115a native evidence.

## Interpretation guardrails
A high win rate is not itself a promotion criterion. Specifically:
- pure-GP yield must be interpreted separately from SPEN/APEN controls;
- specialist success should be judged primarily in its intended defensive niche and against its opportunity cost;
- poor off-niche performance can be healthy family identity;
- controlled fixtures reveal mechanical thresholds but cannot alone justify production balance changes;
- internal damage remains absent from the research consumer and must not be inferred from Hull-only results.
