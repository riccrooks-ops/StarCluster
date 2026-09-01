# Checkpoint 52 Validation - Stateful Auxiliary Power and Endurance Tuning

## Purpose

Checkpoint 52 tests the intended stateful resource mechanics without rewriting accepted Checkpoint 51 evidence. It is an evidence pass, not automatic balance promotion.

## Frozen baselines

- Checkpoint 50 cruiser installation-capacity curve remains accepted.
- Checkpoint 51 is the frozen architecture/runtime-bridge baseline.
- All 56 Checkpoint 51 scenario JSON files are SHA-256 locked before Checkpoint 52 additive scenario/data files are considered.
- Historical Checkpoint 51 runtime stages remain executable and unchanged.

## Mechanics under test

- Combat Battery: primary 3 finite charges, +1 TP per discharge, maximum one discharge per turn; 2-charge fallback is diagnostic only.
- TL2 Power Capacitor: starts with 1 stored TP, discharges +1 TP, then costs 1 TP on a later turn to recharge; same-turn recharge/discharge is prohibited.
- Tactical shield recharge: core ship action whenever the shield is functional and TP is available; power-support AUX changes affordability, not eligibility.
- AMM: 1 TP readiness at TL1/TL2; Checkpoint 51 tactical accuracy candidates retained; 25/30-round primary combat values with 15/20/25/30 endurance stress candidates.
- Kinetic/Missile Magazine Expansions: assessed on repeated-engagement reserve endurance as well as duel behavior.

## New evidence

Checkpoint 52 adds two stages after the retained Checkpoint 51 corpus:

1. `stateful-tl1-tl2-auxiliary-pds`: 975 Monte Carlo variants, retaining the legal one-slot early AUX inventory and 867 legal + 108 no-AUX diagnostic partition.
2. `auxiliary-resource-endurance`: deterministic Battery/Capacitor/AMM/magazine resource accounting across repeated-demand patterns.

The complete checkpoint contains 27 stages and 7,963 Monte Carlo variants. At 10,000 trials per variant the stochastic workload is 79.63 million trials; the new stateful combat matrix contributes 9.75 million of those trials.

## Repository-only gate

Run from a clean extracted repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-52\apply_checkpoint_52.ps1 -RepositoryOnly
```

Expected results:

- repository manifest is valid and no unexpected repository-owned files are present;
- architecture/schema/resource-lifecycle contracts pass;
- active Concept/workbook/checkpoint references are synchronized;
- all 56 Checkpoint 51 scenario hashes match;
- Checkpoint 52 study inventory/counts and resource candidates pass native PowerShell validation.

## Full native Windows validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-52\apply_checkpoint_52.ps1 -Trials 10000 -Jobs 24
```

Expected release gates include:

- pinned .NET SDK from `global.json`;
- warning-as-error build and full test suite;
- all 27 checkpoint stages;
- all retained Checkpoint 51 regression stages;
- 975 new stateful combat variants;
- deterministic resource-endurance gates;
- ScenarioRunner self-tests;
- zero failed acceptance gates.

## Assessment boundary

Do not promote a candidate solely because execution is clean. Assessment must compare:

- frozen Checkpoint 51 outputs versus their Checkpoint 52 retained-stage outputs;
- Checkpoint 51 power-AUX behavior versus the corrected Checkpoint 52 stateful matrix;
- 3-charge versus 2-charge Combat Battery endurance pressure;
- Power Capacitor alternating-demand and back-to-back-demand behavior;
- AMM tactical PDS results separately from 15/20/25/30-round multi-encounter endurance;
- Kinetic/Missile Magazine Expansion endurance gains separately from isolated-duel parity.

Only after this evidence is reviewed should Battery charges, Capacitor rules, AMM ammunition/accuracy, magazine values, production loadouts, or TL3-TL9 runtime population be changed.
