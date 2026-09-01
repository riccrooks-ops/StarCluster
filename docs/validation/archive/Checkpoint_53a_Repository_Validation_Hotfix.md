# Checkpoint 53a Validation - Repository Validation Harness Hotfix

Checkpoint 53a changes only release-validation plumbing for the Checkpoint 53 candidate. The Concept remains v0.4z, the technology workbook remains v0.34, all scenario and runtime files are unchanged, and the Checkpoint 53 workload remains 31 stages / 9,007 Monte Carlo variants / 90.07 million trials at the default 10,000 trials per variant.

## Corrected defect

The original `tools/checkpoints/checkpoint-53/test_technology_architecture.ps1` attempted to read `$ablative.auxiliaryProfiles`. The study file `aux-abl01-tl2-ablative-candidate-study.json` does not embed candidate profiles. It exposes `auxiliaryProfileCatalog`, a repository-relative path to `tl2-ablative-candidate-profiles-v0_1.json`; the six candidate/control rows are in that catalog's `profiles` array.

Checkpoint 53a loads that referenced catalog explicitly and validates the six expected profile IDs under strict PowerShell mode.

## Repository-only validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-53a\apply_checkpoint_53a.ps1 -RepositoryOnly
```

Expected result: the architecture gate completes before the shared repository contract/build harness is invoked. No simulation is run in this mode.

## Full validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-53a\apply_checkpoint_53a.ps1 -Trials 10000 -Jobs 24
```

Preserve the complete `out/checkpoint-53a` directory for assessment. Successful execution does not by itself promote a TL2 Ablative candidate or authorize TL3 runtime generation.
