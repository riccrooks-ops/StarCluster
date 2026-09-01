# Checkpoint 33 Validation

## Checkpoint 33b harness correction

The Phase A resource preflight retains its exact semantic registry for `a06-c02`, `a07-c02`, and `a11-c01`. The C# runner source gate now uses a named semantic regex registry for variant count, Reactor range, Auxiliary output, and required Held boundaries. It no longer searches human-readable diagnostic prose, which may be split across C# string literals. Generic case-ID matching and narrative runner-message matching are prohibited. This correction changes no mechanics, scenarios, tests, calibration variants, Concept content, or workbook content.

## Authoritative Windows command

Close Godot and run from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-33\apply_checkpoint_33.ps1
```

Repository-contract-only validation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-33\apply_checkpoint_33.ps1 `
  -RepositoryContractOnly
```

Both paths must be idempotent and must not modify manifest-controlled repository content.

## Expected acceptance totals

- 674 engine-independent tests.
- 7 deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases / 127-value baseline.
- 7 Phase B documents / 36 cases.
- 29 kinetic variants / 10,000 trials each / zero failed gates.
- 31 energy variants / 10,000 trials each / zero failed gates.
- 48 no-counter weapon-matrix variants / 10,000 trials each / zero failed gates.
- 59 corrected PDS variants / 10,000 trials each / zero failed gates.
- 171 layered defensive-system variants / 10,000 trials each / zero failed gates.
- 294 main-power/interception correction variants / 10,000 trials each / zero failed gates.
- 46 ScenarioRunner self-tests.

## Repository-contract gates

The native PowerShell preflight verifies:

1. the complete repository SHA-256 manifest and rejection of unexpected repository-owned files;
2. parser success for every packaged PowerShell script and semantic operation-registry dispatch;
3. exactly one active validation runbook and one active Concept document;
4. the 127-row TL1 baseline and its current SHA-256;
5. every active Phase A/B and calibration document carrying the same baseline hash;
6. exact TL1 values: Kinetic fire 1 TP, Missile launch 0 TP, overcapacity 1 SP per activation, Auxiliary +1/+0;
7. Held Main source ordering before PDS, Kinetic earmark/spend behavior, successful ammo preservation, and PDS fallback after a miss;
8. the 294-variant study, exact category counts, focused outputs 3-6, +1 Auxiliary overlays, representative variants, and reciprocal pairs;
9. 32 focused Tactical Power facts and 674 total discovered test cases;
10. Concept v0.4e, Decisions D-279 through D-285, and `END OF DRAFT v0.4e`;
11. workbook v0.13 with retained Checkpoint 29-32 sheets and new `Checkpoint 33 Correction` sheet;
12. clean extraction, archive checksum, and unauthorized-file rejection.

## Full execution gates

The full validator additionally performs clean restore/build with warnings as errors under .NET SDK 8.0.423, all retained test/calibration lanes, the 294-variant correction study with a 24-worker ceiling, and all ScenarioRunner self-tests.

No mechanical Godot validation is required because Checkpoint 33 changes engine-independent mechanics, data, tests, documentation, and calibration tools.
