# Checkpoint 29 Validation

Expected acceptance totals:

- 615 engine-independent tests.
- 7 legacy deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases.
- 7 Phase B documents / 36 cases under revised EvM.
- 29 kinetic calibration variants / 10,000 trials each / zero failed gates.
- 31 energy calibration variants / 10,000 trials each / zero failed gates.
- 48 complete weapon-matrix variants / 10,000 trials each / zero failed gates.
- 46 ScenarioRunner self-tests.

The validator must be idempotent when repository-contract-only validation is followed by full validation. No mechanical Godot validation is required.


## Checkpoint 29a release-process hotfix

Checkpoint 29a archives the Checkpoint 28 validation runbook before manifest locking and adds `tools/checkpoints/checkpoint-29/build_checkpoint_29_release.ps1`. The release builder must complete repository normalization, the complete warnings-as-errors acceptance suite, an idempotence preflight, isolated staging, ZIP creation, and post-archive release validation in that order. This prevents normalization from creating repository-owned files that are absent from the manifest.


## Checkpoint 29b hotfix

Checkpoint 29b corrects the repository README release identity by explicitly naming active Concept v0.4a. The pre-archive builder now validates required README metadata before normalization, build, manifest staging, or ZIP creation. No combat mechanics, scenario definitions, baseline values, workbook content, or Concept decisions changed.

## Checkpoint 29c hotfix

Checkpoint 29c corrects the workbook validation contract to require the retained `Checkpoint 28 Energy` sheet and the new `Checkpoint 29 Matrix` sheet. The prior validator incorrectly requested a nonexistent `Checkpoint 29 Energy` sheet. The pre-archive builder now validates these exact sheet names directly from the packaged workbook before release. No mechanics or calibration inputs changed.
