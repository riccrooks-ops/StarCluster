# Checkpoint 19a - Validation Runbook Guard Hotfix

## Purpose

Checkpoint 19a corrects a packaging-only validation defect in Checkpoint 19.
The Checkpoint 19 active validation runbook correctly stated that the
reproducibility study runs at worker counts 1, 12, and 24, but the apply script
required the exact literal substring `--jobs 24`. Because the runbook used
compressed prose (`--jobs 1`, `12`, and `24`), the documentation guard stopped
before compilation or simulation.

No authoritative combat, scenario-initialization, random-stream, Monte Carlo,
resume, aggregation, or statistical behavior changes in this hotfix.

## Hotfix contents

- Adds an explicit worker-count command matrix to the active validation
  runbook, including literal `--jobs 1`, `--jobs 12`, and `--jobs 24` entries.
- Replaces the brittle Checkpoint 19 documentation guard with the synchronized
  Checkpoint 19a runbook check.
- Re-runs the complete Checkpoint 19 acceptance sequence:
  - 506 engine-independent tests;
  - seven deterministic scenarios;
  - eight runner self-tests;
  - the 2,000-trial reproducibility study at 1, 12, and 24 workers;
  - the 24-worker resume proof; and
  - the three-variant, 15,000-trial terminal-probability validation sweep.
- Archives the superseded Checkpoint 19 active validation runbook and leaves
  exactly the Checkpoint 19a runbook active.

## Acceptance target

- solution builds with zero warnings and zero errors;
- 506/506 engine-independent tests pass;
- 7/7 deterministic scenarios pass;
- 8/8 runner self-tests pass;
- reproducibility sweep hashes match at 1, 12, and 24 workers;
- resume reuses all 2,000 trials and preserves the canonical hash;
- 3/3 terminal-probability variants pass; and
- no mechanical Godot validation is required.
