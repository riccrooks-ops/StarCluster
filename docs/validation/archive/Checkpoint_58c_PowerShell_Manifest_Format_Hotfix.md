# Checkpoint 58c - PowerShell Repository Manifest Format Hotfix

## Purpose

Checkpoint 58c is a release-only hotfix for Checkpoint 58b. Checkpoint 58b correctly fixed the repository manifest so retained nested ZIP files are SHA-256 locked, but the new PowerShell architecture precheck used this dynamic regex expression:

```powershell
"^[0-9a-fA-F]{64}  {0}$" -f $escaped
```

In PowerShell, the `-f` operator processes every single-braced numeric token as a format placeholder. The regex quantifier `{64}` was therefore treated as placeholder index 64, causing `FormatError` before `-match` executed.

Checkpoint 58c removes format-string interpolation from this check. It parses each manifest line with the fixed regex `^([0-9a-fA-F]{64})  (.+)$`, normalizes the captured repository path, and compares it exactly with the retained ZIP path. This preserves the Checkpoint 58b manifest contract while eliminating the formatter/regex collision.

No ScenarioRunner study, Monte Carlo variant, simulation parameter, C# runtime behavior, Concept v0.5e content, or workbook v0.39 value changes in this hotfix. The Checkpoint 58a `powerCost` validator correction and Checkpoint 58b nested-ZIP manifest correction are both retained.

## Repository-only gate

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58c\apply_checkpoint_58c.ps1 -RepositoryOnly
```

Expected sequence:

1. `test_technology_architecture.ps1` validates the frozen Checkpoint 57a boundary and Checkpoint 58 architecture contracts.
2. The retained nested ZIP entries are parsed from `CHECKPOINT_58C_SHA256SUMS.txt`, found exactly once, and hash-verified.
3. The shared calibration harness verifies the complete Checkpoint 58c repository manifest, PowerShell parser contract, checkpoint definition, and repository-only gates.

Do not start the Monte Carlo workload if repository-only validation fails.

## Full run

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-58c\apply_checkpoint_58c.ps1 -Trials 10000 -Jobs 24
```

The workload remains 56 runner stages, 14,746 Monte Carlo variants, and 147.46 million trials at 10,000 trials per variant. Results are written to `out/checkpoint-58c`.
