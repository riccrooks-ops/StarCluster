# Checkpoint 23a Validation - Hull, Layered Defense, and Unified Tactical Power Concept Backup

## Run

Checkpoint 23a is a complete repository archive. Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-23a\apply_checkpoint_23a.ps1
```

Repository-contract-only preflight:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-23a\apply_checkpoint_23a.ps1 -RepositoryContractOnly
```

Packaged archive validation from a trusted repository copy:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-23a\validate_checkpoint_23a_release.ps1 `
  -ArchivePath .\StarCluster_Checkpoint_23a_Hull_Layered_Defense_And_Unified_Tactical_Power_Concept_Backup_Full_Repository.zip
```

## Expected repository preflight

The preflight must report:

- the complete Checkpoint 23a manifest verified with no unexpected repository-owned files;
- native parsing of all packaged PowerShell scripts;
- one active Checkpoint 23a validation runbook;
- one active Concept v0.3u and archived v0.3t;
- 14 reference-library files hash-verified;
- 99 components, 11 families, 11 compatibility profiles, 13 reference records, and at least 40 reference insights;
- required workbook sheets with no structured-table parts; and
- all six stable Checkpoint 23a documentation markers.

## Expected full acceptance

- .NET SDK 8.0.423 selected;
- clean build with 0 warnings and 0 errors;
- 506/506 engine-independent tests passed;
- 7/7 deterministic scenarios passed; and
- 46/46 ScenarioRunner self-tests passed.

## Scope

This is a documentation and design backup only. No combat mechanic, numerical TL balance, Godot presentation behavior, or Monte Carlo calibration changed.
