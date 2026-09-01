# Checkpoint 18d Validation - Scenario Corpus and Preflight Hotfix

## Required acceptance

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-18d\apply_checkpoint_18d.ps1
```

The script performs the complete acceptance procedure. Expected result:

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- **506/506** tests pass;
- scenario preflight reports **7 passed, 0 failed**;
- **7/7** deterministic headless scenarios pass; and
- scenario summaries and logs are written under `out\checkpoint-18d-scenarios`.

No separate mechanical Godot test is required.

## Failure handoff

If the apply script fails, preserve only:

- the full PowerShell output; and
- the matching failed scenario directory under `out\checkpoint-18d-scenarios`, when one exists.

A preflight failure writes `runner-error.txt` before any scenario is executed. An assertion-order failure now includes matched and available event indexes in the compact runner output.
