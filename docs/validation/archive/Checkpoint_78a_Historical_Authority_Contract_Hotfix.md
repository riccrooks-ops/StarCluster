# Checkpoint 78a - Historical Authority Contract Hotfix

## Purpose

Checkpoint 78a is a validation/documentation hotfix built on Checkpoint 78. Checkpoint 78's repository-only acceptance reached the final documentation synchronization block and then failed because the PowerShell contract looked for the literal substring `not current authority` while the README rendered the same semantic statement as Markdown emphasis: `**not** current authority`.

The failure is therefore in the **contract's formatting sensitivity**, not in Technology Architecture Matrix v1, Concept v0.6q, TL2 candidate arithmetic, runtime behavior, or production data.

Checkpoint 78a makes the historical-authority wording explicit in plain prose and makes the PowerShell audit compare markup-normalized documentation text where Markdown emphasis is not semantically meaningful. The same normalization is applied to the Tactical Computer architecture check so another emphasis-only edit cannot produce the same class of false failure.

This hotfix deliberately changes **no production combat values, runtime mechanics, AI doctrine, Matrix v1 values, Concept content, spreadsheet content, or Monte Carlo study inputs**.

## What must be true

- Concept v0.6q remains the only active Concept under `docs/` and is byte-identical to Checkpoint 78.
- Technology Architecture Matrix v1 Markdown, JSON, and XLSX artifacts remain byte-identical to Checkpoint 78.
- Historical `Player_TL1_TL9_Technology_Architecture_*` material is explicitly identified as historical and not current authority.
- The documentation contract ignores Markdown emphasis markers when testing semantic authority phrases.
- The TL2 Matrix row remains candidate-only and non-production.
- TL1 runtime authority remains unchanged: Tactical Computer degraded-fire rating -25 pp, weapon-specific permission, Sensor Discrimination Resistance 0, same-hex Burn-through +1, normal ECM/ECCM rating 1 at 1 TP, and ordinary missile Firm-terminal rules.
- Normal acceptance remains the accepted deterministic 8-stage suite with zero Monte Carlo variants.

## Native validation

First run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-78a\apply_checkpoint_78a.ps1 -RepositoryOnly
```

Expected repository-only behavior:

- native dependency precheck succeeds without a Python runtime dependency;
- Checkpoint 78a definition/manifest bindings are correct;
- the markup-normalized historical-authority check passes;
- Concept, Matrix v1, focused architecture documents, and machine-readable data remain synchronized;
- TL2 candidates remain proven non-production;
- repository manifest validation succeeds.

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-78a\apply_checkpoint_78a.ps1 -Jobs 24
```

Expected normal acceptance:

- pinned .NET SDK 8.0.423;
- warning-as-error build with zero warnings/errors;
- approximately 863 unit tests if no unrelated test-count changes occurred;
- 8/8 runner stages;
- 47 ScenarioRunner self-tests;
- zero Monte Carlo variants/trials;
- zero failed gates and zero trial errors.

## Deep Calibration

Do **not** run Deep Calibration for this hotfix unless normal native acceptance exposes an unrelated substantive regression. No simulation dependency changed.

## Next substantive pass

After Checkpoint 78a acceptance, return to Matrix v1 review and the focused TL2 technology-progression calibration: revalidate the legacy +12 Tactical Computer targeting candidate and test the provisional Sensor Discrimination Resistance 1 / ECM 2 / ECCM 2 relationships under the current architecture before promoting TL2 values.
