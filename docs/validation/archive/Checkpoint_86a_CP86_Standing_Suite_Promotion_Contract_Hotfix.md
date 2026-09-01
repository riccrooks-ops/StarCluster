# Checkpoint 86a - CP86 Standing-Suite Promotion-Contract Hotfix

## Purpose

Checkpoint 86a is a native-acceptance contract hotfix for Checkpoint 86. The CP86 gameplay state, 288-cell weapon-penetration study, ScenarioRunner implementation, Concept v0.6x, Technology Architecture Matrix, standing integration suite v0.6, candidate profiles, workload, and release gates are unchanged.

The first native `-RepositoryOnly` run reached the standing-suite documentation contract and exposed a validator/schema mismatch. The standing suite already records `weaponPenetrationPackages.automaticPromotion = false`, `promotionPolicy = family_specific_human_review`, and an activation-policy rule that a shared sensitivity axis does not imply symmetric promotion. The CP86 contract incorrectly searched for a nonexistent literal field named `automaticSymmetricWeaponPromotion`.

CP86a fixes the contract to validate the **actual structured standing-suite fields and policy statement** instead of requiring a duplicate field name. This preserves one source of truth and avoids adding redundant schema solely to satisfy a text-search assertion.

## Scope

No gameplay, simulation, scenario, candidate value, stochastic topology, report logic, release gate, Concept rule, Technology Matrix value, or standing-suite content changes are made. The substantive study remains **288 variants / 2,880,000 default substantive trials**, preceded by a 288-trial full-pipeline smoke. Deep Calibration remains optional and unchanged.

The CP86 documentation-authority boundaries remain in force: long-lived documents are reference authorities rather than checkpoint journals, subsystem-family identity is preserved, and shared APEN/SPEN sensitivity axes do not imply symmetric weapon-family progression.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-86a\apply_checkpoint_86a.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-86a\apply_checkpoint_86a.ps1 -Jobs 24
```

Optional Deep Calibration:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-86a\apply_checkpoint_86a.ps1 -Jobs 24 -DeepCalibration
```

## Promotion boundary

Identical to CP86: successful execution validates the experiment and documentation contracts but does not automatically promote any weapon penetration value or deferred Armor AP1 candidate. Family-specific human review remains mandatory.
