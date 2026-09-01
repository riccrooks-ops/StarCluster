# Checkpoint 18c Validation - Headless Runner Policy and Initialization Hotfix

## Required acceptance

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-18c\apply_checkpoint_18c.ps1
```

The script performs the complete acceptance procedure. Expected result:

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- **506/506** tests pass;
- **7/7** deterministic headless scenarios pass; and
- scenario summaries and logs are written under `out\checkpoint-18c-scenarios`.

No separate mechanical Godot test is required.

## Failure handoff

If the apply script fails, preserve only:

- the full PowerShell output; and
- the matching failed scenario directory under `out\checkpoint-18c-scenarios`, when one exists.

The runner's compact summary and failure artifacts are sufficient for diagnosis. Screenshots are needed only for a genuine Godot presentation defect.
