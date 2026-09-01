# Checkpoint 94 - Adaptive Sampling and Mover-Neutral Cross-TL Screening

## Purpose

Checkpoint 94 continues directly from native-accepted Checkpoint 93. It does **not** return to component tuning. CP93 proved that the broad generalized legal-build analysis pipeline works, while also showing that one pair per population cell is too thin for high-population heterogeneous cells, that individual structurally-ready pairings can be hidden inside healthy activity cohorts, and that mover-order effects have a long tail.

CP94 therefore improves the **sampling instrument** before scaling the study further.

## Accepted baseline

Checkpoint 94 is built directly from native-accepted Checkpoint 93:

- CP93 checkpoint-definition SHA-256: `160adb4fee4fb419136916da0b99e7ebeb2f495c43513033fc93dd0852e970cb`
- CP93 repository-manifest SHA-256: `b1653b049655961474518872286c6bb044d83bcf3d349c5ecdce0224f118baec`
- expected / actual SDK: 8.0.423 / 8.0.423
- warning-as-error build: 0 warnings / 0 errors
- unit tests: 863 passed / 0 failed / 0 skipped
- configured runner stages: 13 / 13 passed
- ScenarioRunner self-tests: 57 passed
- deterministic cases: 7
- mechanics cases: 90
- failed gates: 0
- substantive cross-TL study: 720 variants x 2,000 trials = 1,440,000 trials
- one-trial full-pipeline smoke: 720 executions

The exact accepted CP93 repository manifest and compact native provenance are embedded under `docs/validation/evidence/checkpoint-93/`.

## What CP93 taught us

The accepted CP93 screen confirmed that structural readiness, matched orientation, Space strata, and population weighting are analytically necessary. It also exposed three reasons not to tune components yet:

1. one pair per 96 population cells leaves high-population cells represented by a single potentially idiosyncratic family/information-control matchup;
2. at least two mutually `closing_ready` sampled bundles produced zero main-weapon actions because TrackAware movement did not reach the exact range required for Firm attack eligibility; and
3. mover-order/orientation sensitivity was modest for many pairs but extreme for some, so a one-direction or single-mover-order estimate can be misleading.

CP94 addresses those analysis weaknesses without changing the accepted combat system.

## Authority boundary

Checkpoint 94 changes simulation-analysis infrastructure and its standing testing/development documentation only. It does **not** change:

- Game Concept v0.6z;
- component catalog or Technology Architecture Matrix values/statuses;
- weapon, reactor, shield, armor, Sensor/EW, PDS, missile, Damage Control, or movement gameplay values;
- the accepted AI doctrine or production initiative rules;
- CP92/CP93 external-reference mining content or Spacedock candidate status; or
- candidate promotion decisions.

CP90a gameplay/simulation authority carried through CP91-93 remains intact except for the explicitly accepted simulation-analysis infrastructure additions of later checkpoints.

## Standing architecture v0.11

CP94 promotes `Technology_Integration_Permutation_Suite_Architecture_v0_11` as the current simulation-planning authority and uses `cross-tl-build-permutation-foundation-v0_5.json`.

The underlying legal construction envelope remains unchanged:

- 82,944 raw combinations;
- 22,592 legal builds;
- 4,672 exact-fill / 11,328 near-fill / 6,592 underfilled;
- 255,187,936 unordered distinct legal pairs; and
- 510,375,872 oriented distinct legal pairs.

## Adaptive statistical sample

The same 96 population cells remain. CP94 allocates **192 unordered statistical base pairs** rather than exactly one per cell.

Allocation is deterministic and bounded:

- every cell receives at least 1 representative;
- extra representatives are apportioned using `population^0.5`;
- no cell receives more than 5 representatives; and
- the exact statistical base-pair budget is 192.

Every statistical base pair is mirrored, producing **384 statistical logical orientations**.

Each cell's unordered-distinct population is divided equally among that cell's statistical representatives. Only these statistical pairs enter population-weighted inference.

## Secondary-diversity overlay

The 12 highest-population cells each receive 2 additional unordered diagnostic pairs, producing **24 diversity base pairs / 48 mirrored orientations**. Selection prefers weapon-family-pair plus information-control-band combinations not already represented by the statistical sample.

The overlay is diagnostic only and carries **zero population-inference weight**. It improves within-cell visibility without distorting the population estimate.

Information-control bands are `equal` at distance 0, `near` at 1-2, and `far` at 3 or more.

The retained 48 named diagnostic logical pairings also carry zero population-inference weight.

Total CP94 pairings:

- 384 statistical orientations;
- 48 diversity orientations;
- 48 named diagnostics;
- **480 logical pairings** total;
- 3 geometries each; and
- **1,440 generated actual-consumer variants**.

## Ready-range and individual activity diagnosis

The readiness classes remain `reference_ready`, `closing_ready`, and `engagement_denied`, but CP94 also records exact maximum ready range:

- reference-ready = 3;
- closing-ready = 2, 1, or 0; and
- denied = -1.

For statistical/diversity matched results, runtime output now distinguishes:

- `active` when both sides produce family-appropriate main-weapon actions;
- `not_mutually_expected`;
- `movement_did_not_reach_mutual_ready_range`;
- `ready_geometry_reached_but_one_side_inactive`; and
- `ready_geometry_reached_but_no_actions`.

This prevents a movement/doctrine failure from being mistaken for a structurally invalid build and keeps one side's activity from masking the other. The movement-did-not-reach diagnosis is review evidence. The retained side/family/context cohort gate only judges side-variants that actually reached their declared ready geometry. In the substantive multi-trial run, reaching mutual ready geometry yet still producing zero relevant action on both sides is a blocking individual integration/activity failure. The one-trial smoke is not allowed to turn a single stochastic no-action result into a balance failure.

## Mover-order-neutral reporting

CP94 retains both TrackAware movement-order bounds. It does not define the final production initiative system.

For each matched statistical/diversity bundle, the reports combine both orientations and both dynamic mover orders to calculate:

- build X conditional win when moving first;
- build X conditional win when moving second;
- mover-order-neutral conditional win;
- corresponding Y neutral estimate;
- higher-advanced-side neutral estimate when progression is unequal;
- absolute initiative gap in percentage points; and
- diagnostic `low`, `moderate`, `high`, or `extreme` initiative-sensitivity class.

Population-weighted mover-neutral summaries use statistical representative weights only.

## Required output layers

CP94 must preserve separate reporting for:

1. all legal sampled pairs;
2. structurally mutual-ready sampled pairs; and
3. sampled pairs that actually produced family-appropriate combat activity.

New/expanded generated-study outputs include:

- `pairing-plan.csv` with source role, exact ready ranges, statistical sample count/representative weight, information-control band, and secondary key;
- `population-coverage.csv` and `population-coverage-summary.json` with statistical versus diversity counts and representative weights;
- `secondary-coverage.csv`;
- `cross-tl-cp94-paired-review.csv`;
- `cross-tl-cp94-population-weighted-review.csv`;
- `cross-tl-cp94-activity-review.csv`;
- `cross-tl-cp94-mover-neutral-review.csv`; and
- `cross-tl-cp94-mover-neutral-summary.csv`.

All are screening evidence, not automatic promotion mechanisms.

## Bounded native workload

CP94 deliberately widens pair representation while lowering per-variant trials from 2,000 to **1,500** so the pass buys sampling quality rather than only reducing Monte Carlo noise on a thin sample.

Default workload:

- 1,440 generated variants;
- 1,440 one-trial smoke executions;
- 1,500 substantive trials per variant;
- **2,160,000 substantive trials**; and
- **2,161,440 total trial executions including smoke**.

Deep Calibration is not applicable. The compatibility alias uses the same bounded definition.

## Native acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-94\apply_checkpoint_94.ps1 -RepositoryOnly
```

Full bounded acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-94\apply_checkpoint_94.ps1
```

## Expected acceptance

A successful default native run should show:

- SDK 8.0.423;
- warning-as-error build with 0 warnings/errors;
- all 863 inherited unit tests passing unless unrelated source-tree changes deliberately alter that count;
- all 13 configured runner stages passing;
- **58 ScenarioRunner self-tests**;
- 7 deterministic and 90 mechanics cases;
- 1,440 generated variants;
- 1,440 successful one-trial smoke executions;
- 2,160,000 substantive primary trials;
- zero trial errors; and
- zero failed blocking gates.

## Acceptance decision boundary

A green CP94 validates the improved sampling-quality and mover-neutral analysis instrument. It does **not** promote Kinetic APEN, reactor values, Sensor/EW candidates, any Spacedock concept, or any other component/technology change. The subsequent decision should be whether the resulting within-cell coverage and initiative/readiness diagnostics are strong enough to justify broader or promotion-focused studies.
