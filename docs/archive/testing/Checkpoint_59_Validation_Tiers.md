# Checkpoint 59 Validation Tiers

Checkpoint 59 separates release validation by purpose so obsolete calibration history no longer dominates every run.

## Must always run

The default Checkpoint 59 launcher runs repository/manifest validation, the pinned warnings-as-errors build and xUnit suite, then six deterministic ScenarioRunner stages: accepted missile scenarios, TL1 Phase A, TL1 Phase B, Auxiliary resource endurance, the resource-semantics lock, and ScenarioRunner self-tests. It also runs the Checkpoint 59 design/validation contract before the shared harness.

No Monte Carlo stage is part of the default active runner lineup. This is intentional: the current checkpoint changes design architecture and validation policy, not the accepted combat formulas.

## Deep Calibration

`-DeepCalibration` selects a separate Checkpoint 59 definition containing the must-always-run stages plus twelve accepted TL1 stochastic studies for kinetic, energy, weapon-matrix, PDS, layered defense, power, range control, Damage Control, pacing, integrated combat, movement/kinetic pacing, and minimal-tactics behavior. At the 10,000-trial default this is 1,026 variants / 10.26 million trials rather than Checkpoint 58e's 14,746 variants / 147.46 million trials.

Deep Calibration is opt-in unless the current change plausibly affects one of those mechanics or its dependencies. A future checkpoint should include only the deep studies relevant to the changed subsystem rather than automatically inheriting the entire historical corpus.

## Archived historical calibration

The remaining Checkpoint 58e stages stay in the repository as historical evidence but are not in either Checkpoint 59 active lineup. This includes prior TL2-TL4 progression, Weapon Bay/AUX-capacity, single-main, generation-foundation, and fixed generational-screening studies whose architectural assumptions have been superseded.

Retirement from the active lineup does not invalidate the historical result. It means that result no longer functions as a current release gate unless a later investigation deliberately reactivates it for a relevant regression question.
