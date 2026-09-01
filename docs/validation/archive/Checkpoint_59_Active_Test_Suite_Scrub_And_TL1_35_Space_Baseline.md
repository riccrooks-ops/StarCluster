# Checkpoint 59 - Active Test-Suite Scrub and TL1 35-Space Baseline

## Purpose

Checkpoint 59 resets the active validation lineup after the technology-architecture rethink and records the current TL1 player-cruiser construction baseline. It does **not** replace the established TL1 combat formulas. Instead it carries those validated mechanics forward as a seed, removes superseded calibration studies from the active release path, and prepares a smaller validation foundation for new 35-Installation-Space simulations.

The active Concept is `docs/Star_Cluster_Game_Concept_v0.6b.docx`. The machine-readable design seed is `docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_1.json`.

## What changed

- TL1 player cruiser working budget: **35 Installation Spaces**.
- Working footprints: main weapon 6, main reactor 6, STL 5, FTL 5, tactical computer 3, active sensor 3, shield generator 3, kinetic PDS 2, provisional PDS ammunition support 1, and small AUX 1.
- Mandatory player core is 25 Space: one main weapon, at least one main reactor, one primary STL, one primary FTL, and one primary tactical computer/fire-control architecture.
- Main weapons and reactors may duplicate when their effects naturally add. Full duplicate STL, FTL, and tactical-computer primary architectures are not legal normal stacking. Later AUX may provide limited computer/STL backup, never backup FTL.
- Base primary armor is hull-integrated/external and uses 0 Installation Space; optional armor enhancements may consume support/AUX Space.
- Every technology progression now requires both a logical frontier check and a mathematical/combinatorial check, including legacy stacking and integer-breakpoint review.
- The previously validated TL1 power/damage/PDS/sensor/Damage Control/AUX mechanics remain the numerical seed and must be revalidated under the new Space architecture rather than replaced without evidence.

## Active validation tiers

### Default: must always run

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-59\apply_checkpoint_59.ps1 -RepositoryOnly
```

Then run the default active checkpoint:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-59\apply_checkpoint_59.ps1
```

The launcher first verifies the Checkpoint 59 design/test-suite contract. The shared harness then performs repository-manifest validation, pinned SDK confirmation, a clean warnings-as-errors build, the xUnit suite, and these six deterministic ScenarioRunner stages:

1. accepted deterministic moving-missile scenarios;
2. TL1 Phase A mechanics corpus;
3. TL1 Phase B direct-fire corpus;
4. Auxiliary resource-endurance contracts;
5. deterministic resource-semantics lock;
6. ScenarioRunner self-tests.

There are **0 Monte Carlo variants** in the default runner lineup. This is intentional for this architecture/documentation checkpoint.

### Optional: Deep Calibration

When a change can plausibly affect accepted TL1 combat balance/mechanics, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-59\apply_checkpoint_59.ps1 -DeepCalibration
```

This retains the must-always-run stages and adds twelve accepted TL1 stochastic studies covering kinetic, energy, weapon matrix, PDS, layered defense, power, range control, Damage Control, pacing, integrated tactical combat, movement/kinetic pacing, and minimal tactics. At the normal 10,000-trial default it is **1,026 variants / 10.26 million trials**.

Deep Calibration is evidence, not a promotion mechanism. Future checkpoints should select deep studies according to the mechanics/dependencies they changed rather than automatically inheriting every historical study.

## Archived historical stages

Checkpoint 58e had 56 ScenarioRunner stages (61 total harness steps) and 14,746 Monte Carlo variants / 147.46 million default trials. Checkpoint 59 classifies 38 of those runner stages as historical-only. They remain in the repository through their old checkpoint definitions/scenario corpora, but they are removed from the active Checkpoint 59 lineups because their purpose depends on superseded TL2-TL4 progression, Weapon Bay/AUX-capacity, single-main, generational-foundation, or fixed screening-target assumptions.

All previous active validation runbooks have been moved under `docs/validation/archive`; this file is the only active validation runbook.

## Acceptance

A Checkpoint 59 release candidate is acceptable only after:

1. repository-only validation succeeds on native Windows PowerShell;
2. the default must-always-run checkpoint completes cleanly with the pinned .NET SDK, zero build warnings/errors, and all tests/stages passing;
3. Deep Calibration is run only when the implementation change requires it, or explicitly when requested for broader regression evidence;
4. the active Concept and machine-readable TL1 baseline agree on the 35-Space architecture and primary-system rules;
5. no superseded design study has been silently reintroduced as an active release gate.
