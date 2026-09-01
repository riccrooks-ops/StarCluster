# Checkpoint 45 Validation - TL2 Defensive Micro-Refinement and Choice Viability

## Scope

This runbook validates only Checkpoint 45. Historical procedures remain in prior validation documents.

## Run

From a clean full-repository extraction in native Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-45\apply_checkpoint_45.ps1 -Trials 10000 -Jobs 24
```

Repository-only validation:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-45\apply_checkpoint_45.ps1 -RepositoryOnly
```

## Required automated results

- Repository manifest verification passes with no unexpected repository-owned files.
- Exact .NET SDK 8.0.423 is used.
- Warning-as-error calibration build passes.
- All tests pass with no skips or failures.
- All retained stages pass.
- The Checkpoint 45 primary stage runs exactly 1,188 variants.
- All primary gates pass and every trial reports zero errors.
- `combat-outcome-review.csv`, `movement-outcome-coverage.csv`, `same-family-progression.csv`, `family-choice-viability.csv`, `range-breakdown.csv`, `technology-profiles.csv`, `variants.csv`, `gates.csv`, `summary.json`, and `result.sha256.txt` are present.

## Assessment cautions

- Do not promote a profile solely because it is numerically closest to 60 percent.
- Do not combine escape-control results with ordinary combat win share.
- Treat low decisive coverage as insufficient evidence rather than as a high conditional win rate.
- Treat era-specific weapon advantages as acceptable unless they create broad dominance or make alternatives irrelevant.
- Preserve all output under `out/checkpoint-45` and attach the complete directory or ZIP for assessment.
