# Checkpoint 99 - Mandatory Sensor and Exact-Edge Progression Screening

## Purpose

Checkpoint 99 continues from **native-accepted Checkpoint 98 corrected replacement 2**. It makes one gameplay/construction-rule correction before the next causal technology study: every ordinary legal player/AI combat ship must include at least one installed Sensor, alongside the existing Main Weapon and Reactor requirements. It then consumes the legal same-Space progression lattice directly to measure marginal TL1->TL2 subsystem changes under the accepted range-10 Adaptive Engage encounter.

CP99 does **not** introduce TL3 values, redesign initiative, alter accepted component statistics, or automatically promote technology candidates.

## Accepted baseline provenance

Accepted CP98 authority:

- checkpoint definition SHA-256: `c57f4912ccf2fa79b3085f64ec1887c599946c02712fcb48173ba9580f8ab2c5`;
- repository manifest SHA-256: `f6a1b8c04bc5b237d3e80d02ee2874bb5290c5369ff367459b43c2e21b2bc126`;
- native-results ZIP SHA-256: `1ee459063d8bd24a0228c8410c6912aeaabe3daa21b888b1dd7b68c348de4014`;
- CP98 substantive summary SHA-256: `37be9c45ba62f020a2ccdcdc9d0988288a76ff90b6deace3763b3ffec899eea5`;
- native acceptance: SDK 8.0.423, 0 warnings/errors, 876 xUnit tests, 19 runner stages, 62 ScenarioRunner self-tests, zero failed gates.

The CP98 evidence is embedded under `docs/validation/evidence/checkpoint-98/`. CP99 freezes every unchanged CP98 repository path and byte-preserves superseded authorities in their archive locations.

## Construction-rule change

Normal combat construction now requires:

1. at least one Main Weapon;
2. at least one Main Reactor; and
3. at least one installed Sensor.

A ship may become sensor-disabled through combat damage. Explicit diagnostic fixtures, derelicts, mines, or special scenario objects may intentionally be sensorless when their own scenario contract says so. ECM and ECCM remain optional.

At the current working 35-Space cruiser footprint, the mandatory primary architecture becomes 28 Space and leaves 7 Space discretionary. This is a construction-rule correction only; no installed component cost or performance statistic changes in CP99.

## Revised legal envelope

The v0.8 cross-TL foundation preserves all CP98 construction axes and component values but excludes sensorless combinations from the ordinary legal build population:

- raw combinations: **82,944**;
- legal builds: **11,776**;
- exact-fill: **2,944**;
- near-fill: **6,656**;
- underfilled: **2,176**;
- oriented pairing envelope: **138,674,176**;
- unordered-with-self pairing envelope: **69,342,976**;
- oriented-distinct pairing envelope: **138,662,400**;
- unordered-distinct pairing envelope: **69,331,200**.

## Exact-edge progression lattice

The same-Space TL1->TL2 lattice contains **37,184 legal edges** across 12 transitions. Each edge changes one declared construction axis. Homogeneous double-installation transitions advance two physical components together and therefore declare an expected advanced-component delta of 2; single-installation transitions declare delta 1.

| Transition | Legal | Exact fill | Delta |
|---|---:|---:|---:|
| weapon-single | 2,864 | 672 | 1 |
| weapon-double | 80 | 64 | 2 |
| reactor-single | 5,728 | 1,344 | 1 |
| reactor-double | 160 | 128 | 2 |
| computer | 5,888 | 1,472 | 1 |
| sensor | 5,888 | 1,472 | 1 |
| shield | 3,264 | 1,216 | 1 |
| armor | 5,888 | 1,472 | 1 |
| ecm-single | 2,048 | 384 | 1 |
| ecm-double | 1,664 | 512 | 2 |
| eccm-single | 2,048 | 384 | 1 |
| eccm-double | 1,664 | 512 | 2 |

The lattice is stratified by transition, weapon family, composition class, and Space-utilization class. It contains **181 populated strata**, each with at least eight legal edges. The bounded study deterministically selects two edges per stratum, producing **362 logical lower->higher pairs**.

Although CP99 disables CP98's broad population sampler, the shared build/pair classifiers still consume its classification thresholds. CP99 therefore keeps those thresholds explicit: near-fill begins at **32/35 Space**, progression distance **1-2** is `near`, the equal-low cutoff remains **3** advanced components, and information-control distance **1-2** is `near`. RepositoryOnly reconstructs strata from these declared values rather than hard-coding intended constants.

## Adaptive Engage study

Each exact edge is executed twice:

- `EngageAdaptive`, Side A moves first, initial range 10;
- `EngageAdaptive`, Side B moves first, initial range 10.

That produces **724 variants**. The higher endpoint remains Side B within an exact-edge logical pair; mirrored mover order exposes the first/second-mover interaction without changing production initiative.

Primary study ID: `tl2-itc19-exact-edge-progression-screening`

- combat master seed: **990100**;
- trials per variant: **250**;
- substantive trials: **181,000**.

Exact-edge outcomes are review evidence. No win-rate target is blocking and no candidate is promoted automatically.

## Acceptance workload

Normal and Deep-alias definitions intentionally use the same bounded workload:

- **23 runner stages**;
- expected **876 xUnit tests**;
- expected **63 ScenarioRunner self-tests**;
- CP96 one-trial regression: 1,440 executions;
- CP97 one-trial regression: 36 executions;
- CP98 broad one-trial regression: 960 executions;
- CP99 exact-edge one-trial smoke: 724 executions;
- smoke/regression subtotal: **3,160**;
- CP99 substantive: **181,000**;
- total stochastic executions: **184,160**.

Deep Calibration is not applicable.

## Required preflight protections

`-RepositoryOnly` must fail before native build when possible if any of these contracts drift:

- CP98 accepted hashes/evidence or frozen repository surface;
- Windows PowerShell 5.1 dependency/type-token compatibility;
- checkpoint stage count, variant count, self-test count, or stochastic execution arithmetic;
- v0.8 construction axes/value drift relative to accepted v0.7 beyond the mandatory-Sensor/sampling metadata change;
- independently reconstructed 11,776-build / 37,184-edge / 181-stratum / 362-pair counts;
- mandatory-Sensor legality or accidental re-entry of sensorless builds into the normal population;
- expected advanced-component delta 1/2 semantics;
- frozen CP98 v0.7 progression documents that predate `expectedAdvancedComponentDelta`: RepositoryOnly must infer their legacy delta from from/to option multiplicity (1 for single-installation axes, 2 for homogeneous double-installation axes) without modifying accepted CP98 bytes, while v0.8 must continue to declare and validate the delta explicitly;
- exact-edge study accidentally routed through CP98 broad 96-cell population-weight accounting;
- study ID/dispatch/preflight/shared telemetry/report routing mismatches;
- known C# compiler-risk classes from recent checkpoints: nullable `TryGetValue` out bindings, cross-enum `FinalTrack` comparisons, and nested local-name shadowing in newly mutated methods;
- active-authority/archive/documentation drift; or
- root manifest path/hash mismatch.

The native harness still performs the authoritative SDK/build/test/actual-consumer checks. Static preflight does not substitute for the warning-as-error native build.

## Run commands

Repository contract only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-99\apply_checkpoint_99.ps1 -RepositoryOnly
```

Normal bounded acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-99\apply_checkpoint_99.ps1
```

Do not run a separate Deep Calibration pass; it is intentionally not applicable to CP99.
