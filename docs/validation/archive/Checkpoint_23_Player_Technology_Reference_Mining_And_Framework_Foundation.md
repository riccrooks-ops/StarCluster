# Checkpoint 23 Validation - Player Technology Reference Mining and Framework Foundation

## Run

Checkpoint 23 Revision 3 is a complete repository archive. A clean extraction is preferred. Extraction over the established working repository is also supported: known local/generated artifacts are tolerated, while unknown repository-owned files remain contract failures. Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-23\apply_checkpoint_23.ps1
```

A lightweight repository-contract preflight is also available:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-23\apply_checkpoint_23.ps1 -RepositoryContractOnly
```

To validate the packaged ZIP itself from a trusted repository copy, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-23\validate_checkpoint_23_release.ps1 `
  -ArchivePath .\StarCluster_Checkpoint_23_Player_Technology_Reference_Mining_And_Framework_Foundation_Full_Repository_Rev3.zip
```

## Revision 1 compatibility repair

Revision 1 must run under Windows PowerShell 5.1 without calling `System.IO.Path.GetRelativePath`. The repository-contract preflight now executes a dedicated relative-path compatibility self-test before verifying the complete manifest.


## Revision 2 repository repair

Revision 2 restores the 41 foundational repository-owned files captured from the accepted working tree and locks exactly 466 files in `CHECKPOINT_23_SHA256SUMS.txt`. The repository scanner ignores only explicit local/generated classes: `.vs`, `.vscode`, `.idea`, Godot `.godot`, `.uid`, `bin`, `obj`, `TestResults`, `out`, OS metadata, stale root checkpoint identity files, the temporary capture helper, and root ZIP package copies. Unknown files under source, test, tool, or documentation paths are still rejected.

Duplicate stale active validation runbooks and Concept documents are normalized against their archived copies. Identical duplicates are removed; divergent copies are preserved with imported archive names so user data is not silently discarded.

## Revision 3 documentation-contract repair

Revision 3 replaces a brittle prose search for `one Propulsion TL` with three explicit stable decision markers in the Checkpoint 23 documentation. The accepted design remains one player-visible Propulsion TL with separate FTL and STL component families. The repair changes no data or mechanics.

## Expected scope

The scripts:

1. verify the exact 467-entry ZIP set: 466 manifested repository files plus the manifest itself;
2. reject unsafe, duplicate, missing, hash-mismatched, or unmanifested packaged files;
3. parse every packaged PowerShell script with the native parser;
4. self-test and normalize stale active validation runbooks and Concept documents;
5. verify Concept v0.3t and archived v0.3s;
6. verify all thirteen external reference files, including the MOO2 manual, against `docs/references/SHA256SUMS.txt`;
7. validate 99 components across 11 families and TL 1-9;
8. validate 11 compatibility profiles and their support/engineer/strain schema;
9. validate the reference library, insight, and reconciliation CSVs;
10. validate the XLSX package, required sheets, and absence of structured tables;
11. perform a clean warning-as-error build;
12. run 506 engine-independent tests;
13. run seven deterministic scenarios and 46 ScenarioRunner self-tests;
14. test extraction-over-existing runbook/Concept normalization and local-artifact tolerance; and
15. inject an unknown source file and prove that the repository contract rejects it.

## Acceptance

- [ ] Packaged-archive entry and hash validation passes.
- [ ] Repository-contract-only preflight passes on a clean extraction.
- [ ] Extraction-over-existing runbook and Concept normalization passes.
- [ ] Local/generated artifacts are tolerated and an unknown source file is rejected.
- [ ] Full script passes under .NET SDK 8.0.423.
- [ ] The workbook opens in Excel without repair warnings.
- [ ] All CSV and reference hashes pass.
- [ ] Build reports zero warnings and zero errors.
- [ ] 506 tests, seven deterministic scenarios, and 46 runner self-tests pass.
- [ ] No mechanical Godot validation is required.

## Evidence to preserve

Preserve the complete console output and the exact archive checksum. No heavy Monte Carlo output is required for this design/data checkpoint.
