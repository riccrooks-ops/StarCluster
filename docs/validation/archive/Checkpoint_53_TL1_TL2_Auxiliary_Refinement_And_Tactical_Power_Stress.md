# Checkpoint 53 Validation - TL1/TL2 Auxiliary Refinement and Tactical Power Stress

## Purpose

Checkpoint 53 is the focused TL1/TL2 cleanup pass before table-backed TL3 runtime work. It preserves accepted Checkpoint 52 behavior and adds separate evidence for the revised Auxiliary entry floor, TL2 Ablative candidates, and Tactical Power support under actual constrained demand.

## Frozen baseline

- Checkpoint 52 is the accepted stateful-resource baseline.
- All **60** scenario JSON files present in Checkpoint 52 are SHA-256 locked before Checkpoint 53 additive files are considered.
- Every Checkpoint 52 runner stage remains in the checkpoint unchanged.
- The accepted cruiser capacity curve remains AUX `1/1/2/2/3/3/3/4/4` and Weapon Bays `1/1/2/2/2/3/3/3/4`.

## Checkpoint 53 design contracts

- Ablative Armor Layer enters at **TL2**, not TL1.
- TL2 Ablative candidates: leading **AP0 / AI2**; comparisons **AP0 / AI3** and **AP1 / AI1**; historical control **AP1 / AI2**.
- AMM: **25 rounds at TL1 and TL2**, **1 TP readiness**, current TL1/TL2 PDS accuracy progression retained.
- Combat Battery: **3 finite charges**, **+1 TP per charge**, maximum **one discharge per tactical turn**, **no per-encounter cap**; charges persist until replenishment.
- Power Capacitor: TL2, +1 discharge, later-turn 1 TP recharge, no same-turn recharge/discharge, no net TP generation.
- Tactical shield recharge remains a core ship capability.
- The power-stress background commitment is a **diagnostic common sustained load**, not a universal hotel-load rule. If damage reduces available TP below the requested diagnostic load, the runner consumes only the TP actually available.

## New evidence stages

1. `checkpoint-53-tl1-tl2-auxiliary-refinement`: **870** Monte Carlo variants = 768 legal + 102 No-AUX diagnostics; legal bands 147 TL1v1 / 243 TL2v2 / 378 cross-TL.
2. `checkpoint-53-tl2-ablative-candidate-review`: **96** Monte Carlo variants comparing the three candidate profiles plus No-AUX/evasion/historical controls across Kinetic, Energy, and Missile contexts.
3. `checkpoint-53-tactical-power-stress`: **78** Monte Carlo variants = 39 ordinary controls + 39 sustained-load diagnostics. The diagnostic background commitment is 3 TP at TL1 and 4 TP at TL2.
4. `checkpoint-53-resource-semantics-lock`: deterministic Battery/Capacitor/AMM/magazine state checks, including three Battery discharges over three turns of one prolonged encounter.

The complete checkpoint contains **31 stages** and **9,007 Monte Carlo variants**. At 10,000 trials per variant, the stochastic workload is **90.07 million trials**.

## Repository-only gate

Run from a clean extracted repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-53\apply_checkpoint_53.ps1 -RepositoryOnly
```

Expected results include:

- repository manifest valid with no unexpected repository-owned files;
- architecture/schema/bridge/resource-lifecycle contracts pass;
- active Concept/workbook/checkpoint references synchronized;
- all 60 frozen Checkpoint 52 scenario hashes match;
- 7 legal TL1 and 9 legal TL2 combat-AUX profiles;
- all Checkpoint 53 study inventories/counts and candidate values pass native PowerShell validation.

## Full native Windows validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-53\apply_checkpoint_53.ps1 -Trials 10000 -Jobs 24
```

Expected release gates include:

- pinned .NET SDK from `global.json`;
- warning-as-error build and full test suite;
- all 31 checkpoint stages;
- all retained Checkpoint 52 regression stages;
- 870 refined-AUX variants;
- 96 Ablative-candidate variants;
- 78 Tactical Power stress variants;
- deterministic resource-semantics gates;
- ScenarioRunner self-tests;
- zero failed acceptance gates.

## Assessment boundary

Do not promote a candidate solely because execution is clean. Assessment must compare:

- every frozen Checkpoint 52 retained result against its Checkpoint 53 counterpart;
- TL2 Ablative AP0/AI2, AP0/AI3, and AP1/AI1 across direct-fire and missile contexts, with AP1/AI2 treated only as historical control;
- Battery/Capacitor ordinary-duel behavior against the dedicated common-load stress lane;
- explicit Battery use over multiple turns of one encounter, not an invented one-use-per-encounter rule;
- AMM tactical effectiveness separately from its fixed 25-round campaign reserve;
- cross-TL progression after TL1 Ablative is removed from the legal catalog.

If these relationships are healthy, Checkpoint 53 may close TL1/TL2 and authorize the next pass to begin table-backed TL3 runtime derivation.
