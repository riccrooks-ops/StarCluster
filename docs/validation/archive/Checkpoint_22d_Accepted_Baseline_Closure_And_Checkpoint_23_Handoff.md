# Checkpoint 22d Validation - Accepted Baseline Closure and Checkpoint 23 Handoff

## Run

Checkpoint 22d is a complete repository archive. A clean extraction is
preferred and it does not depend on an earlier checkpoint or overlay chain. If
it is extracted over an existing working tree, the script archives stale
top-level checkpoint runbooks before enforcing the sole-active-runbook rule.
Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22d\apply_checkpoint_22d.ps1
```

## Expected scope

The script:

1. verifies the complete-repository inventory and SHA-256 manifest;
2. parses every packaged PowerShell script with the native PowerShell parser;
3. executes a runtime self-test of stale-runbook normalization and normalizes
   stale top-level checkpoint runbooks in the working tree;
4. confirms that Godot is closed and .NET SDK 8.0.423 is selected;
5. verifies accepted map-sizing, compact-execution, symbol, documentation, and
   baseline-handoff contracts;
6. performs a clean warning-as-error build of all four projects;
7. runs 506 engine-independent tests;
8. runs seven deterministic scenarios and 46 runner self-tests;
9. repeats the 288-variant radius-192 map parity proof;
10. repeats the optimized allocation profile against the frozen absolute gate;
11. proves ordinary worker independence and compact/diagnostic scheduler parity;
12. runs the complete 288,000-trial compact calibration;
13. reproduces the accepted Checkpoint 21e summary and marginal CSV hashes; and
14. locks the accepted Checkpoint 22d result hash.

## Preserve for assessment

Preserve the complete console output and:

```text
out\checkpoint-22d-map-optimization-proof\
out\checkpoint-22d-allocation-profile\
out\checkpoint-22d-diagnostic-proof-j24\
out\checkpoint-22d-compact-proof-j1\
out\checkpoint-22d-compact-proof-j24\
out\checkpoint-22d-full-flight-pursuit-calibration\
```

The accepted result hash is:

```text
226677d3b9d2fded9e529ab5b897f6ec0e5251eb27937208f571cbb9b184ee28
```

Neither `map-parity-failures.txt` nor `parity-failures.txt` may exist on a
passing run.

## Interpretation boundary

Checkpoint 22d changes no mechanics. A successful run confirms that the full
archive independently reproduces the accepted Checkpoint 22c implementation,
performance, and Checkpoint 21e behavioral reference. Checkpoint 23 may begin
only after this closure archive passes locally.

No mechanical Godot validation is required.

## Repository-contract preflight

A lightweight native-PowerShell execution path is available before the full
compiler and simulation workload:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22d\apply_checkpoint_22d.ps1 -RepositoryContractOnly
```

It must complete the manifest check, native parsing, runbook-normalization
self-test, working-tree normalization, and source/documentation contracts.

## Release-candidate ZIP validation

The packaged ZIP should also be tested with native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-22d\validate_checkpoint_22d_release.ps1 `
  -ArchivePath <checkpoint-22d-full-repository.zip>
```

This verifies both clean extraction and extraction over an existing active
runbook state.
