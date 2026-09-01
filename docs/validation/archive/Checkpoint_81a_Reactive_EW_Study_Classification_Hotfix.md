# Checkpoint 81a - Reactive EW Study Classification Hotfix

## Purpose

Checkpoint 81a is a validation/runtime-integration hotfix for Checkpoint 81. The CP81 repository contract, native build, 863 unit tests, deterministic suites, and 96-variant actual-consumer preflight all passed. The one-trial full-pipeline smoke then executed all 96 variants but failed three CP81 study gates because the CP81 study ID had not been registered in the ScenarioRunner's current reactive-EW sub-phase whitelist.

The omission caused CP81 variants to fall through to the frozen historical EW path. In that path CP81 did not allocate explicit ECM/ECCM, so the contemporary DR1 + ECCM1 and wide old-Sensor + ECCM2 packages could not exercise their intended Firm-restoration behavior, while the -25 degraded-fire package never received the intended Approximate track. The gates therefore rejected the smoke run correctly.

## Hotfix

CP81a adds `Tl2TacticalComputerEwPermutationStudyId` to the same current reactive-EW execution branch already used by the accepted CP79/CP80 TL2 Sensor/EW studies.

A new static contract assertion now isolates that branch and requires:

- the CP81 study ID to appear exactly once in the current reactive-EW study classification;
- the prior CP79 Sensor/EW discrimination and CP80 power-pressure study classifications to remain present;
- the existing CP81 dispatch, coverage validation, shared policy-telemetry classification, eleven study-specific gates, report routing, schema bindings, and production exclusions to remain intact.

## Frozen semantics

This hotfix changes no calibration candidate or gameplay value. The following remain exactly as in CP81:

- TL1 Tactical Computer +10 pp control;
- legacy TL2 Tactical Computer +12 pp candidate;
- computer-owned degraded-fire penalty -25 pp;
- Evasive Compensation 0;
- Sensor DR1 / ECM2 / ECCM2 candidate mechanics at 1 TP per rating;
- production reactor output 5 TP;
- fixed Sensor range and overload behavior;
- 96-variant paired Technology Integration Permutation Suite study;
- ordinary missile Firm-terminal/degraded-fire boundaries;
- no production TL2 profile and no production degraded-fire weapon assignment.

The failed CP81 runbook is retained under `docs/validation/archive/` for continuity.

## Native acceptance

Run repository validation first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-81a\apply_checkpoint_81a.ps1 -RepositoryOnly
```

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-81a\apply_checkpoint_81a.ps1 -Jobs 24
```

Expected normal workload is unchanged from CP81: 11 runner stages, approximately 863 unit tests, 48 ScenarioRunner self-tests, 96 one-trial smoke executions, and 96 substantive variants / 960,000 default substantive trials. Deep Calibration is not required unless normal acceptance exposes a broader regression.
