# CP115 Cross-Study Integration Audit

## Purpose

CP115 adds a new Monte Carlo research-study family and therefore receives a cross-study integration audit before handoff. The goal is to ensure the new study is isolated correctly, does not break accepted study families, and does not silently enter unrelated global release-gate logic.

## Dispatch and validation routing

- `weapon-family-study` is registered as its own CLI parser command.
- The command has its own dispatch branch, study validation call, execution function, output routing, failed-gate handling, and summary writer.
- `payload-study` remains registered independently and retains its own CP114 validation/execution path.
- The CP115 study schema/version is validated by `weapon_family_analysis.validate_study`; it does not masquerade as a CP114 payload study or cross-TL v8 ScenarioRunner study.

## Backward compatibility smoke

After the CP115 CLI change, the frozen CP114 executable study was rerun at one trial per variant:

- CP114 `payload-study`: 3,184 variants / 3,184 engagements / zero failed gates.
- CP115 `weapon-family-study`: 4,064 variants / 4,064 engagements / zero failed gates.

The accepted CP114 study and consumer remain hash-frozen:

- `payload_characteristic_space_study_v0_1.json`: `f88f8079d0fb2429837f7e880ce09194d622f49e00b2dede1fd923187bf080a9`
- `payload_analysis.py`: `8ff46ff94b4e51a48d0be13c0301b466aca8cb1eb207e8df0c9f12322b7d1438`

Twenty-one prior simulation files are frozen by the CP115 evidence hash list; the CLI and simulation README are the intended previously existing files changed for CP115 integration.

## Global-gate classification

CP115 is a dedicated Python research command and is not a new ScenarioRunner stage or production release-gate classification. Therefore:

- no C# ScenarioRunner required-variant dispatch is changed;
- no shared/global production policy-telemetry gate is extended;
- no cross-TL v8 schema/baseline binding is changed;
- no existing checkpoint study-family whitelist is repurposed;
- CP115 gates remain study-specific and `automaticPromotion=false`.

If a later checkpoint promotes this consumer into a shared standing suite, the integration audit must be repeated against those global classifications at that time.

## Regression layers

Pre-handoff validation completed:

- 64/64 Python self-tests;
- 25/25 deterministic C#/Python parity fixtures;
- CP114 all-variant one-trial backward-compatibility smoke: 3,184/3,184, zero failed gates;
- CP115 all-variant one-trial smoke: 4,064/4,064, zero failed gates;
- 561 C#/test files frozen;
- CP109 numerical matrix and CP110 Reactor profile frozen;
- accepted CP114 native evidence preserved;
- root prepackage hygiene passes.

## Result

Cross-study integration audit: **PASS**. CP115 is isolated as a new research-study family, preserves the accepted CP114 study path, and introduces no unintended production/global-gate integration.
