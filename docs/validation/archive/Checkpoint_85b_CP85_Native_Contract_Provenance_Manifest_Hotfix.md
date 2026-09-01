# Checkpoint 85b - CP85 Native Contract and CP84 Provenance-Manifest Hotfix

## Purpose

Checkpoint 85b is a validation-tooling/document-hygiene hotfix for Checkpoint 85. The CP85 Armor AP/AI x Shield integration study, ScenarioRunner simulation code, Concept v0.6w, Technology Matrix candidate values, 288-cell substantive workload, and gameplay behavior are unchanged.

CP85a corrected the original `profileLabel` schema mismatch. Native `-RepositoryOnly` then exposed a second validation defect in the accepted-CP84 provenance check: the contract's custom manifest parser was not robust on the native acceptance path and reported the complete 1,622-entry CP84 evidence manifest as incomplete.

CP85b replaces that parser with line-oriented `Get-Content` validation. Every nonblank manifest line must match the SHA-256/path schema, duplicate paths are rejected, and the embedded CP84 evidence is now checked against the **accepted native CP84 manifest SHA-256** from provenance plus the exact expected **1,622 physical lines / 1,622 unique entries**. The contract prints these counts before applying the production-code freeze.

The current acceptance path was also audited for text/manifest parsing. `run_calibration_checkpoint.ps1` already uses line-oriented `Get-Content` for manifest verification, and the native-dependency guard already uses `Get-Content -Raw` for checkpoint JSON. No simulation or release-gate consumer changes were required.

## Scope

No gameplay, simulation, scenario, candidate profile, Monte Carlo topology, release-gate logic, or production component changes are made. The CP85 study remains **18 comparison groups x 16 variants = 288 variants**, with **2,880,000 substantive trials** at the normal 10,000-trial setting plus 288 smoke trials. Deep Calibration remains optional and unchanged.

The accepted CP84 provenance and production-code freeze remain the comparison authority.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85b\apply_checkpoint_85b.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85b\apply_checkpoint_85b.ps1 -Jobs 24
```

Optional Deep Calibration:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85b\apply_checkpoint_85b.ps1 -Jobs 24 -DeepCalibration
```

## Promotion boundary

Identical to CP85: a successful run does not automatically promote Armor. AP0/AI5 and AP1/AI4 remain independent candidates; AP1/AI5 remains an upper/integration sensitivity. Shield 3 and Reactor 6 remain validated working candidates.
