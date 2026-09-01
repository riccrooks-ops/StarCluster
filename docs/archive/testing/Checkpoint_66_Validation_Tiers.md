# Checkpoint 66 Validation Tiers

Checkpoint 66 continues the scrubbed validation model: normal acceptance runs repository/build/unit/core-regression gates plus only the new stochastic study under review. Historical stochastic calibration remains opt-in Deep Calibration.

## Must always run

The normal suite has **8 stages**. It retains deterministic/core TL1 checks, the frozen 35-Space construction envelope, resource semantics, and runner self-tests, while replacing Checkpoint 65b's accepted finite-map study with the current **80-variant scripted bounded-overload study**.

At 10,000 trials per variant the normal stochastic workload is **800,000 trials**.

## Deep Calibration

Deep Calibration is optional. It retains the accepted 54-variant Checkpoint 65b bilateral finite-map study and all earlier historical stochastic stages, then adds the 80-variant Checkpoint 66 study.

Expected workload: **25 stages / 1,484 Monte Carlo variants / 14,840,000 default trials**.

Deep Calibration is not required for initial Checkpoint 66 acceptance because the new overload controls are opt-in fields and historical study documents retain their accepted defaults.

## Native acceptance dependency precheck

Checkpoint 66 makes the no-Python rule durable rather than checkpoint-local.

- The active checkpoint definitions require `nativeDependencyPrecheck` metadata.
- The shared checkpoint harness enforces that metadata for Checkpoint 66 and later before repository/output/native work proceeds.
- The PowerShell precheck parses the active apply script, checkpoint contract, shared harness, and guard script, and inspects both normal/deep checkpoint definitions.
- Direct or mediated dependencies on `python`, `python3`, or `py` are rejected.
- The approved native acceptance environment remains Windows PowerShell plus the pinned .NET SDK unless a future dependency is deliberately approved.

## Release-gate boundary

Release gates verify overload timing/eligibility, safe Strain bounds, finite-map/fuel consistency, paired study coverage, and preserved production controls.

No target win percentage, weapon-family ranking, overload frequency, Energy/APEN conclusion, or movement-order advantage is a release gate.
