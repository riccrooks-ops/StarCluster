# Checkpoint 76 - Degraded-Fire / ECCM Value Counterplay and Upgrade-Path Guardrails

## Intent

Checkpoint 76 follows the accepted Checkpoint 75a implementation and evidence. It does **not** promote degraded fire to production. Instead it tests whether a weapon-specific Approximate-track fallback preserves the tactical/economic value of ECCM once ordinary movement, Tactical Power, PDS, active sensing, hostile ECM doctrine, and missile pressure are allowed to interact.

The checkpoint also synchronizes the Concept and missile architecture documentation with two explicit design boundaries:

- degraded fire belongs to a specific weapon profile, variant, or upgrade path rather than an entire broad weapon family;
- a future missile may gain a separate purpose-built Approximate-terminal capability, but ordinary missiles do not inherit the direct-fire degraded-fire trait and Checkpoint 76 implements no such missile attack.

## Implementation scope

Checkpoint 76 adds:

- Concept `Star_Cluster_Game_Concept_v0.6o.docx` with the weapon-specific upgrade-path and ECCM-value guardrail;
- the `tl1-itc18-degraded-fire-eccm-value-counterplay` operational study;
- 54 variants: six geometry/family contexts x nine response packages;
- -20 and -25 percentage-point study-only degraded-fire candidates;
- accepted AI Doctrine Registry v0.2 integration for CP76 EW execution;
- hostile `tl1-ew-preserve-combat-package-v1` ECM behavior;
- accepted `tl1-ew-reactive-eccm-v1` response cases plus aggressive normal-ECCM diagnostics;
- a deterministic direct-fire regression proving Approximate-track permission is specific to the evaluated weapon profile;
- `degraded-fire-eccm-value-review.csv` output with direct-fire, track, EW-power, missile, PDS, power-denial, pacing, and damage telemetry.

No production weapon component data is changed. Missile terminal Core code is frozen from Checkpoint 75a.

## Study structure

The fixed-range controls use range 3 and simultaneous movement. Dynamic controls begin at range 4 and use `TrackAwareOpponentRange`, mirrored Side-A-first and Side-B-first. Kinetic-vs-Missile and Energy-vs-Missile are both represented.

Each context contains:

1. Firm reference;
2. jammed Firm-only with no ECCM;
3. jammed Firm-only with accepted reactive ECCM;
4. -20 degraded fire with no ECCM;
5. -20 degraded fire with accepted reactive ECCM;
6. -20 degraded fire with aggressive ECCM;
7. -25 degraded fire with no ECCM;
8. -25 degraded fire with accepted reactive ECCM;
9. -25 degraded fire with aggressive ECCM.

The normal substantive workload is 54 x 10,000 = **540,000 trials**, preceded by a 54-variant actual-consumer preflight and 54 one-trial smoke executions.

## Release gates

The CP76 study-specific gate block must contain exactly these eight gates:

1. `tl1-c76-variant-coverage`;
2. `tl1-c76-firm-reference-clean`;
3. `tl1-c76-fixed-range-firm-only-blocked`;
4. `tl1-c76-fixed-range-reactive-eccm-restores-firm`;
5. `tl1-c76-fixed-range-degraded-fire-exercised`;
6. `tl1-c76-reactive-and-aggressive-eccm-exercised`;
7. `tl1-c76-no-missile-degraded-fire`;
8. `tl1-c76-outcomes-review-only`.

These gates validate execution and architecture. They do not make -20/-25, win share, pacing, or ECCM-value thresholds release-blocking balance targets.

## Evidence review

After native acceptance, review the CSV by matched context. The central questions are:

- how much direct-fire throughput is lost when the ship accepts -20 or -25 degraded fire instead of restoring Firm;
- how often accepted reactive ECCM spends power and restores Firm;
- whether aggressive ECCM materially improves combat enough to justify extra power pressure;
- whether ECCM spending sacrifices direct fire, PDS, or other actions through insufficient-power prevention;
- whether degraded fire is useful but still costly enough that ECCM remains a meaningful upgrade/countermeasure;
- whether -20 and -25 should remain distinct upgrade-path candidates rather than forcing one universal value.

Any production assignment remains a separate human-reviewed checkpoint.

## Native acceptance

Extract this complete repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-76\apply_checkpoint_76.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-76\apply_checkpoint_76.ps1 -Jobs 24
```

Expected normal workload after repository validation:

- pinned .NET SDK 8.0.423;
- warning-as-error build;
- approximately 857 unit tests if no unrelated test-count changes occurred;
- 11 runner stages;
- 47 ScenarioRunner self-tests;
- 54-variant actual-consumer preflight;
- 54 one-trial full-pipeline smoke executions;
- 54 substantive variants / 540,000 substantive trials;
- zero failed release gates and zero trial errors.

## Deep Calibration

Do not run by default. Checkpoint 76 deliberately consumes accepted CP72/73 EW behavior and the accepted CP75a degraded-fire/missile foundation while testing one new operational interaction. Run Deep Calibration only if normal acceptance exposes a regression or the reviewed evidence identifies a concrete dependency requiring broader revalidation.
