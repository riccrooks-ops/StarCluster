# Checkpoint 85a - CP85 Native Contract `profileLabel` Hotfix

## Purpose

Checkpoint 85a is a validation-tooling-only hotfix for Checkpoint 85. The CP85 Armor AP/AI x Shield integration study, ScenarioRunner code, Concept v0.6w, Technology Matrix, candidate values, and 288-cell substantive workload are unchanged.

The original CP85 repository contract incorrectly queried each scenario variant through a non-existent `label` property while the established scenario schema uses `profileLabel`. Because the contract runs under `Set-StrictMode -Version 2.0`, native `-RepositoryOnly` acceptance stopped with `PropertyNotFoundStrict` before the intended pairing assertions could run.

CP85a corrects the pairing lookup to `profileLabel` and adds an explicit required-property schema guard before any pairing query. This converts a future schema mismatch into a checkpoint-owned assertion with the affected variant/property named, rather than an unhandled StrictMode property exception.

## Scope

No gameplay, simulation, scenario, production component, candidate profile, or study-matrix value changes are made. The CP85 study remains 18 comparison groups x 16 variants = **288 variants**, with **2,880,000 substantive trials** at the normal 10,000-trial setting plus 288 smoke trials. Deep Calibration remains optional and unchanged.

The accepted CP84 provenance and production-code freeze remain the comparison authority.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85a\apply_checkpoint_85a.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85a\apply_checkpoint_85a.ps1 -Jobs 24
```

Optional Deep Calibration:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-85a\apply_checkpoint_85a.ps1 -Jobs 24 -DeepCalibration
```

## Promotion boundary

Identical to CP85: a successful run does not automatically promote Armor. AP0/AI5 and AP1/AI4 remain independent candidates; AP1/AI5 remains an upper/integration sensitivity. Shield 3 and Reactor 6 remain validated working candidates.
