# Checkpoint 32 - TL1 Tactical Power Completion and Reactor Envelope Calibration

## Goal

Complete the static TL1 Tactical Power ledger and produce an initial reactor-output assessment without adding adaptive tactics or movement-dependent systems.

## Implemented mechanics

- Full-after-FTL Capacity-3 Capacitor Bank with Charge Rate 1, Discharge Rate 2, and one operation per turn.
- Three-charge Combat Battery with +2 TP and one discharge per turn.
- Auxiliary Reactor comparison output of +2 Operational / +1 Degraded / +0 unavailable.
- Kinetic and Energy Held Interception using normal ammunition, accuracy, power earmarks, and lost offensive cycles.
- Safe Reactor, Energy Cannon, Active Sensor, ECM, ECCM, Shield Hardener, shield-overcapacity, and shield-recovery overload boundaries.
- Shield Battery retained as a finite emergency reserve but removed from ordinary reactor-package doctrine.
- PDS Reaction Capacity 1 and one Flight per installed main Missile Launcher per turn retained.

## Evaluation space

The executable `tl1-pe01-tactical-power-and-reactor-envelope-study.json` contains 504 variants at 10,000 trials each:

- 6 accepted controls;
- 90 reactor-sweep variants;
- 144 single-consumer variants;
- 144 layered-sweep variants;
- 60 power-source overlays;
- 30 overload-boundary variants;
- 30 Held Interception variants.

Renewable outputs 0-8 are all represented. Every asymmetric case has an exact reciprocal side swap. Static stalls and extreme outcomes are accepted mechanics proofs.

## Deferred

- Tractor Beams and Tractor overload.
- STL Drive overload and movement-dependent value.
- Adaptive/optimized power allocation.
- Multiple-weapon higher-TL hull balance.
- Forced-overload failure consequences.
- Campaign resupply and multi-engagement doctrine.

## Acceptance

Run `tools/checkpoints/checkpoint-32/apply_checkpoint_32.ps1`. Acceptance requires 668 engine-independent tests, every retained deterministic/calibration lane, 504 power-envelope variants with zero failed gates, and 46 ScenarioRunner self-tests.
