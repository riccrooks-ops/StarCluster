# Checkpoint 25 Validation Runbook

## Scope

This runbook validates the complete Checkpoint 25 repository, its documentation/data contracts, the new Core TL1 mechanics, the 54-case Phase A corpus, and all accepted legacy headless regression lanes.

No Monte Carlo calibration or mechanical Godot interaction is required. Godot must be closed during validation.

## Prerequisites

- Windows 11
- PowerShell 5.1 or later
- .NET SDK 8.0.423 selected by the repository `global.json`
- repository extracted into a writable directory

## Repository-only preflight

From the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-25\apply_checkpoint_25.ps1 `
  -RepositoryContractOnly
```

Expected completion:

```text
Checkpoint 25 repository-contract preflight completed successfully.
Manifest, parser, normalization, reference, documentation, CSV, JSON corpus, schema, and workbook contracts passed.
```

## Full acceptance

Close Godot, then run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-25\apply_checkpoint_25.ps1
```

Expected stages:

1. complete manifest, parser, runbook/Concept normalization, and local-artifact policy;
2. Concept, references, numerical baseline, loadouts, matrix v0.2, schema, JSON corpus, and workbook v0.5;
3. Godot closed and .NET SDK 8.0.423 selected;
4. clean warnings-as-errors solution build;
5. 562 engine-independent tests;
6. seven accepted deterministic moving-missile scenarios;
7. 12 TL1 Phase A scenario documents and 54 mechanics cases;
8. 46 ScenarioRunner self-tests.

Expected final summary:

```text
Checkpoint 25 completed successfully.
Engine-independent tests passed: 562.
Legacy deterministic scenarios passed: 7.
TL1 Phase A scenarios passed: 12 documents / 54 cases.
Runner self-tests passed: 46.
No Monte Carlo calibration or mechanical Godot validation is required.
```

## Phase A output review

The validator writes under:

```text
out\checkpoint-25-tl1-phase-a
```

Every scenario directory contains:

- `summary.json` - scenario identity, baseline path/hash, pass counts, and failures;
- `cases.json` - actual output, events, and failures for every case;
- `results.log` - readable case-by-case record.

Confirm:

- all scenario summaries report `passed: true`;
- all 54 cases pass;
- every summary uses the same baseline SHA-256 `50316e0528f5e80a16957017ecf407ce4655c40d57dc9e077d09d0d86e19bd7a`;
- no `runner-error.txt` exists;
- the existing seven missile scenarios also pass unchanged.

## Interpretation

A clean result accepts the deterministic implementation foundation only. Do not infer weapon-family balance from these fixed packets. Phase B remains blocked until its initiative, hit, endpoint, doctrine, pairing, metric, and missile-compatibility contracts are documented and implemented.

## Release validation

To validate the packaged archive itself:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-25\validate_checkpoint_25_release.ps1 `
  -ArchivePath .\StarCluster_Checkpoint_25_TL1_Deterministic_Layered_Damage_Power_And_Phase_A_Scenario_Foundation_Full_Repository.zip
```
