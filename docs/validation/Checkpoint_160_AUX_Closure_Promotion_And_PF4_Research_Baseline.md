# Checkpoint 160 — AUX Closure Promotion and PF4 Research Baseline

Status: native-accepted 2026-08-30.

## Purpose

CP160 is the zero-combat authority-promotion checkpoint following native-accepted CP159. It converts the reviewed CP159 specialist-closure evidence into **CP160-PF4**, the next mandatory Pending-Finalization Research Execution Baseline. No new AUX response surface is run, no combat number is tuned, and production numerical/runtime authority remains unchanged.

CP160 closes the isolated AUX magnitude/architecture phase and leaves **Reactor/TP Scarcity and Whole-Ship Equilibrium** as the sole remaining major balance dependency.

## Accepted CP159 evidence

The CP159 native archive is hash-locked at:

`e7c17f3aeb6d6833620e8f8ca72694fdc4be589ef9791fb73e7cc0cfbe771a65`

Native acceptance completed:

- 604/604 Python tests;
- 934/934 xUnit tests;
- 70/70 ScenarioRunner self-tests;
- 25/25 C#/Python research-parity cases;
- 30/30 CP159 focused tests;
- 3,390,000 substantive combats;
- 1,728,000 Damage-Control Drone microtrials;
- zero substantive combat errors; and
- zero turn-cap sentinels.

Compact CP159 response surfaces and the native-results archive SHA-256 are preserved under `docs/validation/evidence/checkpoint-160/accepted-cp159/`. The raw CP159 results ZIP remains externalized to respect the repository packaging budget.

## PF4 AUX selections

### Field Stabilizer — `FST_HIGH`

The CP159 specialist response surface bracketed the useful region through complete incoming-SPEN nullification. PF4 selects the high trajectory rather than the maximum trajectory:

| TL | Incoming SPEN reduction | TP | Space |
|---:|---:|---:|---:|
| 7 | 16 | 1 | 1 |
| 8 | 18 | 1 | 1 |
| 9 | 20 | 1 | 1 |

The deep `FST_HIGH` package produced mean defender decisive-share uplift of **0.0844019090** in the deliberately high-SPEN specialist environment, versus **0.0951366623** for `FST_MAX` and **0.0601952647** for `FST_CENTER`. The selected point therefore preserves strong specialist value while retaining clear diminishing-return headroom. The 1-TP operating cost remains provisional until the final Reactor/TP equilibrium pass; CP160 does not make the system passive merely because the passive CP159 control was somewhat stronger.

### Crystalline Armor — `CRY_RISE_A`

PF4 retains the CP158 lower-TL branch and adopts the CP159 late-TL `CRY_RISE_A` extension:

| TL | Capacity bonus | RES bonus | TP | Space |
|---:|---:|---:|---:|---:|
| 6 | +2 | +0 pp | 0 | 0 |
| 7 | +4 | +5 pp | 0 | 0 |
| 8 | +8 | +15 pp | 0 | 0 |
| 9 | +10 | +20 pp | 0 | 0 |

`CRY_RISE_A` produced **0.0909303081** mean uplift across the TL8-TL9 deep surface, with TL8 **0.0592130783** and TL9 **0.1226475380**. Stronger `RISE_B` and `RISE_C` candidates produced much larger effects, demonstrating ample headroom but not a requirement to consume it. PF4 therefore corrects the prior TL9 potency decay without converting Crystalline Armor into an overwhelming generic defensive branch.

### Repair Drone Bay — parallel Damage Control + complete additional kit load

PF4 adopts the CP159 semantic without modification:

> A Repair Drone Bay grants one additional Damage Control action in each Damage Control phase. The crew and Drone must target different eligible repair targets during that phase. The Drone uses the normal target-specific Damage Control success chance, the normal per-attempt TP cost, and one Repair Kit per attempt. It never provides a same-target reroll.

The Bay also carries **one additional prepared Repair Kit load equal to the ship's normal default reserve at that TL**. A ship with 5 normal kits therefore carries 10 total when fitted with one Repair Drone Bay.

This endpoint is deliberately resource-coupled. CP159 showed that the extra action supplies parallelism rather than free recovery: insufficient TP prevents the second action, while insufficient kits limits how long the parallel action can be sustained. The selected additional full kit load is therefore the simplest scalable KISS rule and preserves the intended dependency on whole-ship TP supply.

## AUX status after PF4

The following AUX execution centers are now closed for isolated balance research and carried as Pending Finalization:

- Shield Battery — CP158 selected rising trajectory;
- Shield Booster — CP158 selected rising trajectory;
- Shield Hardener — CP158 selected rising trajectory;
- Ablative Armor — CP158 selected rising trajectory;
- Energized Armor — CP158 selected rising trajectory;
- Crystalline Armor — CP159 `CRY_RISE_A`;
- Field Stabilizer — CP159 `FST_HIGH`;
- Repair Drone Bay — CP159 distinct-target parallel action + full additional default kit load;
- Kinetic Magazine +25 — endurance/logistics classification; and
- Missile Magazine +25 — endurance/logistics classification.

"Closed" here means **closed as an isolated AUX magnitude/architecture research question**, not immutable final production authority. Powered AUX operating costs remain provisional because their opportunity cost depends on the final Reactor/TP economy.

## Authority boundary

`technology_research_execution_baseline_pending_finalization_v0_4.json` is the CP160-PF4 research execution authority. It supersedes CP159-PF3 for future substantive research while preserving the PF3 executable main/PDS/core-defense/resource profiles exactly.

CP160 does **not** change:

- `technology_numerical_matrix_v0_9.json` production authority;
- production C#/Godot mechanics;
- Concept authority;
- main-weapon/PDS/core-defense numerical values;
- Reactor TP supply;
- Space supply; or
- any campaign/resource values.

PF4's only remaining major open dependency is `FINAL_REACTOR_TP_SCARCITY`.

## Zero-combat contract

CP160 runs **zero substantive combats and zero Damage-Control microtrials**. RepositoryOnly acceptance performs regression, build, deterministic-scenario, research-parity, PF4 provenance, and focused promotion tests only. The normal invocation revalidates the same repository state and packages the native acceptance evidence.

## Native workflow

Use one fresh extraction and run both commands in the same unchanged tree:

```powershell
.\tools\checkpoints\checkpoint-160\apply_checkpoint_160.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-160\apply_checkpoint_160.ps1
```

Native acceptance completed cleanly. CP161 now begins the **Reactor/TP Scarcity and Whole-Ship Equilibrium** diagnostic from CP160-PF4 rather than reopening AUX in isolation.
