# Checkpoint 58b - Repository Manifest Nested-ZIP Hotfix

## Purpose

Checkpoint 58b is a release-only hotfix for Checkpoint 58a. Repository-only validation correctly rejected three retained repository-owned ZIP files because the Checkpoint 58a top-level manifest omitted them. The release process had incorrectly treated nested ZIPs like top-level deliverable packaging artifacts.

Checkpoint 58b changes the packaging rule: only the external deliverable ZIP is excluded from the repository manifest. Nested reference/evidence ZIPs inside the repository are normal repository-owned files and must be SHA-256 locked.

The three files that triggered the Checkpoint 58a failure are:

- `docs/references/StarfireUltra(2).zip`
- `docs/references/Ultra_4_2009(complete).zip`
- `docs/validation/evidence/checkpoint-22c-accepted/checkpoint-22c-results.zip`

No ScenarioRunner study, Monte Carlo variant, simulation parameter, C# runtime behavior, test, Concept v0.5e content, or workbook v0.39 value changes in this hotfix. The earlier Checkpoint 58a `powerCost` validator correction is retained.

## Repository-only gate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58b\apply_checkpoint_58b.ps1 -RepositoryOnly
```

The architecture precheck explicitly verifies that each retained nested ZIP appears exactly once in `CHECKPOINT_58B_SHA256SUMS.txt` and that the manifest hash matches the packaged file before the generic repository-manifest gate runs.

Do not start the Monte Carlo workload if repository-only validation fails.

## Full run

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58b\apply_checkpoint_58b.ps1 -Trials 10000 -Jobs 24
```

The workload remains 56 runner stages, 14,746 Monte Carlo variants, and 147.46 million trials at 10,000 trials per variant. Results are written to `out/checkpoint-58b`.
