# Checkpoint 24 Validation - Unified Tactical Power, Component State, and TL1 Test Foundation

## Scope

Checkpoint 24 changes documentation, design data, schema records, and test specifications only. It does not change the accepted runtime mechanics. Validation therefore proves repository integrity, documentation reconciliation, exact data contracts, and preservation of the Checkpoint 22d mechanical baseline.

## Required repository state

- Active Concept: `docs/Star_Cluster_Game_Concept_v0.3v.docx`
- Archived predecessor: `docs/archive/Star_Cluster_Game_Concept_v0.3u.docx`
- Active runbook: this file only
- Archived predecessor runbook: `docs/validation/archive/Checkpoint_23a_Hull_Layered_Defense_And_Unified_Tactical_Power_Concept_Backup.md`
- Active checkpoint note: `docs/checkpoints/Checkpoint_24_Unified_Tactical_Power_Component_State_And_TL1_Core_Combat_Test_Foundation.md`
- Manifest: `CHECKPOINT_24_SHA256SUMS.txt`

## Documentation contract checks

Confirm that the Concept, foundation documents, schema, workbook, TODO, and checkpoint note agree on:

- Available / Powered / Spent terminology;
- one-way within-turn power flow;
- four optional power-adjustment opportunities;
- the Turn Power Envelope and immediate component-effect loss;
- Main/Auxiliary Reactor, APU, Emergency Output, battery, and capacitor identities;
- scalable ECM/ECCM, range-scaled Active Sensors, self-contained PDS, and rare non-overloadable cloaks;
- Shield Armor, generator overcapacity/recovery, hardeners, and fixed Shield Batteries;
- weapon-family, charging, retention, held-interception, and hazard contracts;
- safe overload, Forced Overload, Strain, and repair;
- STL/EvM/tractor boundaries;
- Turn Refresh and FTL transition as the only universal resets;
- pristine/persistent/derived/turn-local state and effect precedence;
- modular subsystem schemas and pristine/field ceilings;
- Crew 100, Marines 10, Minimum Operating Crew 10, and broad Crew stages;
- exact versioned TL1 values and situational-viability testing.

Reject legacy active wording that treats Tactical Power as Available/Committed/Consumed, permits ordinary within-turn power refunds, uses Shield Protection as the current term, or defines a universal combat-end reset.

## Exact data contracts

Verify UTF-8 CSV parsing and exact headers for:

- `tl1_core_combat_numerical_baseline_v0_1.csv` - 117 rows;
- `tl1_core_combat_loadouts_v0_1.csv` - 13 rows;
- `tl1_core_combat_test_scenarios_v0_1.csv` - 60 rows;
- `player_tl_design_reconciliation_v0_2.csv` - 24 rows.

Verify workbook `StarCluster_Player_TL_Framework_Draft_v0_4.xlsx` contains at least:

- Overview
- TL1 Baseline
- TL1 Loadouts
- TL1 Test Matrix
- Component Schema
- Checkpoint 24 Plan
- Design Reconciliation
- Design Decisions

The decision sheet must contain D-197 through D-232.

## Automated validation

From the repository root on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-24\apply_checkpoint_24.ps1
```

Repository-contract-only preflight:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-24\apply_checkpoint_24.ps1 -RepositoryContractOnly
```

The full pass must:

1. verify every manifest entry and reject unknown source files;
2. parse every packaged PowerShell script with the native parser;
3. normalize stale duplicate active Concept/runbook files when extracting over an existing tree;
4. validate the Checkpoint 24 documentation, CSV, and workbook contracts;
5. build the full solution cleanly with warnings treated as errors;
6. pass all 506 engine-independent tests;
7. pass the seven deterministic ScenarioRunner scenarios; and
8. pass all 46 ScenarioRunner self-tests.

## Expected result

Checkpoint 24 is accepted when all repository and documentation contracts pass and the unchanged runtime baseline remains green. The next checkpoint may then implement Phase A TL1 deterministic mechanics without reopening or silently changing the accepted conceptual contracts.
