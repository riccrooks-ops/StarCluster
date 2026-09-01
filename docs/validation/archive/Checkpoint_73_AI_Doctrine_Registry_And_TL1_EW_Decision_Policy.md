# Checkpoint 73 - AI Doctrine Registry and TL1 EW Decision Policy

## Intent

Checkpoint 73 turns accepted AI/tactical heuristics into versioned, testable evidence instead of leaving them buried in one-off calibration scripts.

It preserves the accepted Checkpoint 72 pre-combat EW structure and all Checkpoint 71/72 TL1 Sensor/EW numerical values. The first accepted doctrine entry is CP72's **reactive ECCM** behavior: if hostile ECM actually degrades an otherwise Firm observation and uncommitted TP is available, ECCM may respond; if Firm survives, ECCM remains off.

ECM activation is deliberately still experimental. CP73 compares three ECM heuristics on top of reactive ECCM against a no-EW control:

1. always activate normal ECM when affordable;
2. activate ECM only if ready offense plus one possible ECCM response can still be funded;
3. activate ECM only if ready offense, planned PDS against a missile threat, and one possible ECCM response can still be funded.

The AI doctrine service may use own capabilities, current uncommitted TP, observable track degradation, and existing visible/accepted threat-planning inputs. It must not use hidden enemy ECM/ECCM ratings or the internal Jamming Margin.

## Evidence persistence

Authoritative registry inputs:

- `docs/design/ai/ai_doctrine_registry_v0_1.json`
- `docs/design/ai/ai_doctrine_registry_schema_v0_1.json`
- `docs/design/ai/AI_Doctrine_Registry_Architecture_v0_1.md`

The substantive study writes:

- `ew-ai-doctrine-review.csv`
- `ai-doctrine-evidence-draft.json`
- `ai-doctrine-evidence-draft.sha256.txt`

The evidence draft is review material, not an automatic registry mutation. After native results are reviewed, a future checkpoint may promote/reject a candidate and record the resulting evidence with its dependency/revalidation triggers.

## Normal native acceptance

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-73\apply_checkpoint_73.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-73\apply_checkpoint_73.ps1 -Jobs 24
```

Expected primary workload:

- 11 runner stages.
- 848 unit tests if no unrelated test count changes occur.
- 924 deterministic Sensor/EW foundation rows.
- 24-variant actual-consumer AI-doctrine preflight.
- 24 one-trial smoke executions.
- 24 substantive variants / 240,000 substantive trials.
- 46 ScenarioRunner self-tests.

## Acceptance interpretation

Release gates verify wiring, registry binding, control cleanliness, actual ECM exercise, one-TP Active Sensor accounting, absence of legacy per-variant EW toggles, and absence of overload/static-range-penalty drift. Combat outcomes and candidate ranking remain diagnostic.

After a successful native run, verify that the substantive output's AI evidence draft references the same `summary.json` hash written by `result.sha256.txt`, the same registry hash loaded by the runner, all declared candidate/dependency IDs, and all 24 context results.

## Deep Calibration

Do not run by default. Use `-DeepCalibration` only if normal results or a declared dependency change justify it.
