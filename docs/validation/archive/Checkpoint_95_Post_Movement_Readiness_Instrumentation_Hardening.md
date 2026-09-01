# Checkpoint 95 - Post-Movement Readiness Instrumentation Hardening

## Purpose

Checkpoint 95 continues directly from native-accepted Checkpoint 94. It is an **instrumentation-correction and outlier-triage checkpoint**, not a gameplay, component, technology, or AI-doctrine pass.

CP94 successfully validated the adaptive 1,440-variant cross-TL screen, but post-acceptance review found one important analysis defect: the observed-engagement diagnosis used `MeanMinimumRange`. In finite-map movement that metric includes movement-path closest approach, while ordinary Direct Fire / launch eligibility is governed by final post-Movement geometry. A ship can therefore pass through a nominal ready range during movement without ever ending Movement in a firing window at that range.

CP95 separates those signals and replays the exact CP94 workload so the instrumentation change is causally isolated.

## Accepted CP94 baseline

- checkpoint-definition SHA-256: `a121176b8525827ebbd7335b0f89a83d2bef9a6c194ef06a277b5a63335920f1`
- repository-manifest SHA-256: `10003c7bdc8ee167ec2ab02d547de87fe2dec7293e03872f96a61dbca64c763a`
- corrected repository ZIP SHA-256: `8259c82674bea280551f1f740497604ac3734541a746236ee1486c610fdebf0d`
- SDK 8.0.423; 0 build warnings/errors; 863/863 tests; 13/13 stages; 58 self-tests; zero failed gates/trial errors
- 1,440 smoke executions and 1,440 substantive variants x 1,500 trials = 2,160,000 substantive trials

The exact accepted CP94 manifest, compact native provenance, and compact instrumentation-review evidence are under `docs/validation/evidence/checkpoint-94/`.

## Authority boundary

CP95 does not change Game Concept v0.6z, component values/statuses, weapon or movement rules, Technology Matrix candidates, AI doctrine, Sensor/EW mechanics, reference mining, or production initiative. It changes runtime/reporting instrumentation and the development/testing authorities that own that instrumentation.

## Causal replay contract

Cross-TL foundation v0.6 preserves CP94's:

- 82,944 raw / 22,592 legal build envelope;
- 255,187,936 unordered-distinct legal pair population;
- 96 population cells;
- 192 statistical unordered base pairs / 384 orientations;
- 24 zero-weight diversity base pairs / 48 orientations;
- 48 named diagnostics;
- three geometries and 1,440 generated variants;
- pair-selection seed `940177`;
- combat master seed `940100`; and
- 1,500 substantive trials per variant.

The intended gameplay outcome stream is therefore unchanged. CP95 is specifically designed so any substantive outcome drift is suspicious rather than a new sampling choice.
The generated variant IDs advance from `c94-*` to `c95-*`, but the integrated combat RNG salt for paired studies is derived from the unchanged `ComparisonGroup`, not the display/variant ID. CP95 also adds no RNG calls before or inside combat resolution.

## New runtime telemetry

Generated matched-readiness variants now carry explicit side-specific:

- engagement-readiness class; and
- maximum ready range in hexes.

The combat consumer records, per trial and aggregates per variant:

- minimum final post-Movement range observed at an ordinary combat firing window;
- number of post-Movement firing windows;
- Side-A ready-window count;
- Side-B ready-window count;
- mutual ready-window count; and
- percentage of trials in which Side A, Side B, and both sides reached at least one ready firing window.

The legacy minimum-range metric remains intact as movement-path/closest-approach evidence. It is no longer used to prove that a post-Movement firing window was reached. The precomputed maximum-ready-range is likewise a structural screening estimate, not an absolute runtime attack-legality ceiling: legal reactive EW/power state can allow a runtime action outside that static estimate, which CP95 reports as review-only divergence rather than treating as a firing-window telemetry failure.

## Corrected observed-engagement diagnosis

For statistical/diversity results:

- `active`: both sides produced family-appropriate main-weapon actions;
- `not_mutually_expected`: one or both sides are not structurally expected to engage in that geometry;
- `movement_did_not_reach_mutual_ready_range`: a dynamic mutual-ready pairing never recorded a mutual post-Movement ready-window trial;
- `fixed_reference_ready_geometry_not_observed`: a structurally ready fixed reference failed to record its expected post-Movement ready window;
- `ready_geometry_reached_but_one_side_inactive`: mutual ready geometry was observed but one side remained inactive; and
- `ready_geometry_reached_but_no_actions`: mutual ready geometry was observed but both sides remained inactive.

Fixed-reference ready-window absence and substantive reached-geometry/no-action are blocking instrumentation/integration failures. Dynamic movement failure and one-side inactivity remain explicit review evidence, with side/family/context activity gates retained.

## Outlier review

CP95 emits `cross-tl-cp95-outlier-review.csv` with separate categories for:

1. observed-engagement anomalies;
2. movement-path vs post-Movement geometry divergence;
3. runtime action outside the precomputed structural ready-range estimate; and
4. high/extreme mover-order sensitivity.

The queue contains population/stratum context and a review-priority field. It is triage evidence, not an automatic balance gate.

## Required outputs

The substantive and smoke studies emit the ordinary summary/gate files plus:

- `cross-tl-cp95-paired-review.csv`;
- `cross-tl-cp95-population-weighted-review.csv`;
- `cross-tl-cp95-activity-review.csv`;
- `cross-tl-cp95-mover-neutral-review.csv`;
- `cross-tl-cp95-mover-neutral-summary.csv`; and
- `cross-tl-cp95-outlier-review.csv`.

## Native workload

- 1,440 one-trial smoke executions;
- 1,440 variants x 1,500 substantive trials = 2,160,000 substantive trials;
- 2,161,440 total trial executions including smoke;
- 59 ScenarioRunner self-tests expected.

Deep Calibration is not applicable.

## Native acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-95\apply_checkpoint_95.ps1 -RepositoryOnly
```

Full bounded acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-95\apply_checkpoint_95.ps1
```

## Review after native acceptance

First confirm exact repository/checkpoint hashes and green gates. Then compare CP95 outcome distributions to CP94 as a causal replay, inspect the corrected classification of the former `c94-1061-dynamic-a-first` pattern, quantify path/post-Movement divergence, and re-evaluate the range-0 activity gap and range-3-vs-1 mover-order tail using the hardened telemetry. Do not tune technology from CP95 until that review is complete.
