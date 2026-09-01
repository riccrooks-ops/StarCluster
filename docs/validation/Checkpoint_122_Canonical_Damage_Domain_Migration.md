# Checkpoint 122 - Canonical Damage-Domain Migration

> **Corrected Replacement 1 (2026-08-16):** Adds the missing `StarCluster.Core.Combat.Components` namespace imports to the two new CP122 C# consumers of `ComponentCondition`. CP122 preflight now audits the C# files added/changed relative to accepted CP121 for this dependency binding before the native build. No canonical values, parity populations, production mechanics, or acceptance counts changed.

**Status:** candidate pending native Windows acceptance  
**Accepted baseline:** Checkpoint 121  
**Deep Calibration:** not applicable  
**Substantive Monte Carlo:** none

## Purpose

CP121 native acceptance proved that an exact x2 damage-domain conversion preserves the exercised combat model and that newly available odd integers can provide meaningful intermediate resolution. CP122 is the final implementation checkpoint for that ruler. It migrates the current numerical authorities and production-facing damage arithmetic to canonical x2 units without performing a balance pass.

## Decisions implemented

1. One historical damage-domain point equals **2 canonical points**.
2. Current promoted DAM, SPEN/APEN, Shield Capacity/recharge/Shield Armor, Armor Protection/Integrity, Hull, and active direct point effects are doubled exactly.
3. Non-point domains are unchanged.
4. No odd CP121 half-step numerical candidate is promoted.
5. Degraded Energy damage is scale-aware: historical D3 -> degraded D2 becomes canonical D6 -> degraded D4. Non-damage half-rounding is unchanged.
6. Production TL1 Damage Control remains **1 canonical Hull restored per successful Repair Kit**. This is an intentional post-migration gameplay baseline, not exact parity.
7. Migration-equivalence tests may use an artificial **2 canonical Hull per Repair Kit** only inside the parity fixture.
8. H/X/internal-critical cadence migration is deferred until the critical system is fully implemented. CP122 changes no critical-frequency rule.
9. Historical numerical authorities and checkpoint consumers remain preserved for reproducibility; explicit successor authorities are canonical for new work.

## Canonical successor files

- `docs/Star_Cluster_Game_Concept_v0.7m.docx`
- `docs/design/player_technology/canonical_numerical_authority_v0_1.json`
- `docs/design/player_technology/tl1_core_combat_numerical_baseline_v0_4.csv`
- `docs/design/player_technology/technology_numerical_matrix_v0_2.json`
- `docs/design/player_technology/TL1_TL9_Canonical_Numerical_Technology_Matrix_v0_2.md`
- `src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_5.json`
- `src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-auxiliary-runtime-profiles-v0_4.json`
- `src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl4-standard-runtime-profiles-v0_3.json`
- `src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-tl4-production-auxiliary-profiles-v0_3.json`

## Native acceptance gates

RepositoryOnly and the normal run both execute the deterministic implementation gates because there is no long Monte Carlo study to skip:

1. resolve CPython 3.13 and pinned .NET SDK 8.0.423;
2. apply/check repository hygiene;
3. verify accepted CP121 native provenance;
4. regenerate all eight canonical numerical successors into an isolated directory and require byte identity;
5. prove declared point-domain fields are exactly x2 and declared non-point fields are unchanged;
6. run all Python research tests (expected 124);
7. warning-as-error build of `StarCluster.sln`;
8. run all xUnit tests (expected 905 after CP122 tests);
9. run ScenarioRunner self-tests;
10. run `damage-scale-parity` and require zero mismatches across 234,000 layered cases, 117 temporary-effect cases, and 21 degraded-Energy cases;
11. assert production Damage Control = 1 Hull/kit and parity-only fixture = 2 Hull/kit;
12. run all 25 C#/Python research parity fixtures;
13. verify all JSON, active documentation semantics, code boundaries, and the CP122 repository manifest.

No win-rate threshold, balance score, or odd-value candidate can fail or pass CP122 because no balance experiment is run.

## Commands

From repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-122\apply_checkpoint_122.ps1 -RepositoryOnly
```

If that succeeds:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-122\apply_checkpoint_122.ps1
```

The normal run writes its compact evidence under `out/checkpoint-122/`. Upload that output ZIP for review. Do not treat CP122 as accepted until the native run is reviewed.

## Intended post-acceptance state

After native acceptance, CP122 becomes the canonical numerical-implementation baseline. Subsequent technology calibration may use odd canonical point values when warranted. Hull-TL repair-yield progression is a separate future design axis; TL1 remains 1 Hull per Repair Kit. Internal critical/H-X cadence remains deferred to its dedicated implementation checkpoint.
