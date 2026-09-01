# Checkpoint 58a - Repository Validator Power-Cost Property Hotfix

## Purpose

Checkpoint 58a is a release-only hotfix for Checkpoint 58. The Checkpoint 58 repository-only acceptance gate failed before build because the strict-mode technology validator referenced the non-existent weapon property `power`; the canonical runtime-profile property is `powerCost`.

No simulation parameter, ScenarioRunner study, TL4 candidate, C# runtime behavior, test, Concept document, or technology workbook value changes in this hotfix.

## Repository-only gate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58a\apply_checkpoint_58a.ps1 -RepositoryOnly
```

Expected high-level results:

- the architecture validator completes without a strict-mode property failure;
- the three TL4 higher-output weapon checks read `powerCost` values 2 / 3 / 1 for Kinetic / Energy / Missile;
- repository manifest verifies with no unexpected repository-owned files;
- PowerShell parser succeeds;
- pinned SDK is 8.0.423;
- clean warnings-as-errors build succeeds;
- StarCluster.Tests succeeds;
- the frozen Checkpoint 57a ScenarioRunner boundary remains unchanged.

Do not start the Monte Carlo workload if repository-only validation fails.

## Full run

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58a\apply_checkpoint_58a.ps1 -Trials 10000 -Jobs 24
```

The workload is unchanged from Checkpoint 58: 56 runner stages, 14,746 Monte Carlo variants, and 147.46 million trials at 10,000 trials per variant. Results are written to `out/checkpoint-58a`.

## Hotfix scope

The Checkpoint 58 TL4 studies and design artifacts are retained unchanged. The only executable acceptance change is the PowerShell architecture validator's use of the canonical `powerCost` field, plus hotfix launcher/checkpoint bookkeeping and validation assertions protecting that contract.
