# Checkpoint 33 - TL1 Main-Weapon Power and Interception-Order Correction

## Goal

Correct the TL1 main-weapon power asymmetry, Held Interception order, early Auxiliary Reactor output, and Shield overcapacity magnitude identified by Checkpoint 32 while retaining fixed envelope doctrines.

## Implemented mechanics

- TL1 Kinetic Cannon fire spends 1 TP; TL1 Missile launch remains 0 TP.
- Kinetic Held Interception earmarks and, when triggered, spends 1 TP.
- Held Main resolves before PDS. Successful held fire prevents a PDS attempt and preserves finite PDS ammunition; a miss permits normal PDS fallback.
- TL1 Shield overcapacity adds 1 temporary SP per safe activation rather than 2.
- Early Auxiliary Reactor comparison output is +1 Operational / +0 Degraded / +0 unavailable.
- Existing Capacitor, Combat Battery, PDS Reaction Capacity 1, and one-Flight-per-launcher rules are retained.

## Evaluation space

The executable `tl1-pe02-main-power-interception-correction-study.json` contains 294 variants at 10,000 trials each:

- 6 accepted controls;
- 40 reactor-sweep variants;
- 64 single-consumer variants;
- 64 layered-sweep variants;
- 60 power-source overlays;
- 30 overload-boundary variants;
- 30 Held Interception variants.

Repeated reactor sweeps focus on outputs 3-6. Every asymmetric case has an exact reciprocal side swap. Retained Checkpoint 32 lanes remain regression controls.

## Acceptance

Run `tools/checkpoints/checkpoint-33/apply_checkpoint_33.ps1`. Acceptance requires 674 engine-independent tests, every retained deterministic/calibration lane, 294 correction variants with zero failed gates, and 46 ScenarioRunner self-tests.
