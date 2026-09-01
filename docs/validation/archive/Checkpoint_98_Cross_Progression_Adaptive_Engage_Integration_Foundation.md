# Checkpoint 98 - Cross-Progression Adaptive Engage Integration Foundation

## Accepted baseline

CP98 continues from native-accepted CP97:

- checkpoint-definition SHA-256: `d261eb01efde0919bb55f36e9fa58a5cf8885845af89310c12a92ebba0689055`;
- repository-manifest SHA-256: `888e8c85f1fa3db5b95abc435d1bc51103ef7f7b99d5f79be5c8492bd6269ad4`;
- CP97 Adaptive Engage substantive summary SHA-256: `24b2d6745dc71995b12a5cc449da3a8dd4239d08ec9bfbcac04a2e38af7a6bbc`;
- SDK 8.0.423; 875/875 tests; 15/15 stages; 62 self-tests; zero failed gates.

CP97 is embedded as accepted evidence under `docs/validation/evidence/checkpoint-97/`.

## CP98 purpose

CP98 is not a TL3 tuning pass and does not change initiative. It has two bounded goals:

1. make the Adaptive Engage combat blackboard distinguish safe-Strain exhaustion from range/state keyed overload failure, suppressing futile overload requests while preserving retry after a real Tactical Power state change; and
2. make the accepted mixed-TL 35-Space legal-build envelope run through the range-10 Encounter/Adaptive Engage consumer while adding a deterministic same-design single-axis TL1->TL2 progression lattice.

## Deterministic cross-progression foundation

Foundation v0.7 preserves 82,944 raw combinations, 22,592 legal builds, 4,672 exact-fill builds, the accepted deterministic pair-selection seed 940177, and 480 logical pairings. It adds 12 explicit same-Space transitions totaling **65,648 legal progression edges**. No Energy, Missile, PDS, Propulsion, or TL3 transition is invented merely for symmetry.

Every pairing is generated in two Adaptive Engage contexts: Side A first and Side B first, both from range 10 on the radius-5 map. This yields **960 variants**.

## Workload

Normal CP98 acceptance contains 19 runner stages and default `--jobs 24` / `--trials 250`. Stochastic workload:

- accepted CP96 generated regression: 1,440 x 1;
- accepted CP97 Adaptive Engage regression: 36 x 1;
- CP98 generated smoke: 960 x 1;
- CP98 substantive screen: 960 x 250 = 240,000;
- total: **242,436 trial executions**.

Expected native counts: **876 xUnit tests** and **62 ScenarioRunner self-tests**. Deep Calibration is not applicable.

## Pre-package / RepositoryOnly guardrails

The CP98 wrapper performs a Windows PowerShell 5.1 type-token compatibility precheck over both newly authored CP98 PowerShell scripts before invoking the repository contract. Any unreviewed or unsupported bracketed type token fails immediately, preventing unresolved type accelerators from surfacing later in native acceptance. The repository contract also performs a method-level nested-local shadowing scan over the CP98-mutated progression-lattice/gate methods, including the aggregate-versus-transition exact-fill counters, so C# CS0136 redeclaration mistakes fail in RepositoryOnly before the warning-as-error native build.

The CP98 repository contract must independently verify:

- accepted CP97 definition/manifest provenance and frozen repository surface;
- JSON parsing and active-authority hygiene;
- exact 82,944 / 22,592 construction counts and all 12 transition/65,648 progression-edge counts;
- v0.7 generated study ID, seed, trial count, geometry, and 960-variant binding;
- actual consumer dispatch, finite-map/Adaptive Encounter routing, policy telemetry classification, result gates, and report routing;
- all referenced technology/AUX/Sensor-EW/AI doctrine IDs;
- safe-Strain blackboard API and the request-suppression call order for both adaptive ECCM and Active Sensor overload;
- changed-C# scans for known nullable `TryGetValue`, cross-enum comparison, and unresolved dispatch/method patterns; and
- exact manifest/path-set integrity.

The actual native warning-as-error build remains authoritative for C# compilation.

## Acceptance commands

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-98\apply_checkpoint_98.ps1 -RepositoryOnly
```

then:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-98\apply_checkpoint_98.ps1
```

## Review focus after native success

Do not ask whether every TL2 endpoint wins. Review:

- whether single-axis progression expands useful design options under equal Space;
- whether compact/duplicated legacy combinations dominate contemporary alternatives;
- where Tactical Power pressure changes the value of Reactor/Computer/Sensor/EW advancement;
- whether Sensor/EW and weapon-family identity remain distinct under Adaptive Engage;
- where legal builds still fail to force engagement and whether that is rational standoff/EW denial versus AI pathology;
- mover-order sensitivity as a diagnostic dimension only; and
- which missing progression families deserve the next reference-informed design pass.
