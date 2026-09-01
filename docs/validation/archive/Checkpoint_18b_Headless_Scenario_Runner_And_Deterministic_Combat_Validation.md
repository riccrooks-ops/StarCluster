# Checkpoint 18b Validation - Headless Scenario Runner and Deterministic Combat Validation

## Required acceptance

Close Godot and run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-18b\apply_checkpoint_18b.ps1
```

The script performs the complete acceptance procedure. Expected result:

- .NET SDK 8.0.423 selected;
- solution builds with zero warnings and zero errors;
- **506/506** tests pass;
- **7/7** deterministic headless scenarios pass; and
- scenario summaries and logs are written under `out\checkpoint-18b-scenarios`.

No separate mechanical Godot test is required.

## Optional Godot smoke check

After automated acceptance, reopen `src\StarCluster.Game\project.godot` and confirm only that:

1. the tactical prototype starts;
2. a scenario is displayed; and
3. one normal phase advance or missile launch does not produce a runtime error.

Do not attempt to force Search/Wait, terminal interception, dud, critical, datalink-loss, or other mechanical outcomes through manual play. Those conditions are now deterministic runner scenarios.

## Failure handoff

If the apply script fails, preserve only:

- the full PowerShell output; and
- the matching failed scenario directory under `out\checkpoint-18b-scenarios`, when one exists.

The per-scenario `failures.txt`, `summary.json`, `events.jsonl`, and `events.log` files are sufficient for diagnosis. Screenshots are needed only for a genuine Godot presentation defect.
