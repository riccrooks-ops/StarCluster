# Checkpoint 79a - Policy-Telemetry Study Classification Hotfix

## Purpose

Checkpoint 79a is a validation/integration hotfix for the Checkpoint 79 TL2 Sensor/EW Discrimination and Rating Isolation study. Native Checkpoint 79 repository validation, warning-as-error build, 863 unit tests, deterministic suites, and the actual-consumer preflight all passed. The one-trial full-pipeline smoke then failed only at the shared `policy-telemetry` release gate because the new CP79 study ID had not been registered in that gate's single-policy diagnostic classification.

The failure does not indicate a TL2 Sensor/EW mechanics failure, a degraded-fire failure, or a balance result. It is a cross-study ScenarioRunner integration omission in a global release-gate whitelist.

## Hotfix

- Add `Tl2SensorEwDiscriminationIsolationStudyId` to both semantic branches of the shared `policy-telemetry` gate: the pass predicate and its diagnostic-message classification.
- Keep the existing requirement that every result records requested orders.
- Preserve the existing CP79 movement/order policy behavior; no policy algorithm or telemetry counter changes.
- Extend the checkpoint contract so the CP79 study ID must appear exactly twice inside the isolated shared `policy-telemetry` gate. This converts the native failure class into a pre-run static contract failure if it regresses.
- Freeze the CP79 54-variant study, Sensor/EW catalog, Concept v0.6q, Technology Architecture Matrix v1, validation-tier policy, integrated schema, and document model.

## Substantive study remains unchanged

Checkpoint 79a still evaluates the exact CP79 hypothesis:

- Sensor Discrimination Resistance 0 versus candidate 1;
- ECM/ECCM normal rating 1 versus candidate 2;
- 1 Tactical Power per normal EW rating;
- unchanged Sensor reach and overload behavior;
- unchanged TL1 Tactical Computer, including the -25 degraded-fire penalty when an explicit study-only weapon capability permits Approximate-track fire;
- no production degraded-fire assignment;
- ordinary missiles remain on their accepted Firm-terminal architecture;
- 54 variants / 540,000 substantive trials at the default trial count, preceded by 54 one-trial full-pipeline smoke executions.

No TL2 value is promoted by this hotfix.

## Native validation

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-79a\apply_checkpoint_79a.ps1 -RepositoryOnly
```

Then:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-79a\apply_checkpoint_79a.ps1 -Jobs 24
```

Expected normal acceptance remains 11 runner stages, 863 unit tests unless unrelated counts change, 47 ScenarioRunner self-tests, 54 smoke trials, 54 substantive variants / 540,000 default substantive trials, zero failed gates, and zero trial errors.

Deep Calibration is not required unless normal acceptance exposes a broader regression.
