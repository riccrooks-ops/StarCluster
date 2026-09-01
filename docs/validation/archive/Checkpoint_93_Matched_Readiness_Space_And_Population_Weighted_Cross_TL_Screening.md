# Checkpoint 93 - Matched Readiness, Space, and Population-Weighted Cross-TL Screening

## Purpose

Checkpoint 93 resumes the generalized cross-TL permutation work that was deliberately paused for Checkpoints 91-92's controlled external-reference mining. It does **not** return to component tuning. Instead, it hardens the analysis of the existing 22,592-build legal envelope so later widening of the roughly 255-million unordered-distinct pairing population produces interpretable evidence.

The checkpoint implements five connected improvements:

1. separate structural engagement readiness from observed combat activity;
2. sample unordered legal pairs and execute both A-vs-B and B-vs-A orientations;
3. classify Space utilization and report pairwise Space advantage explicitly;
4. count the legal population represented by every sampling cell and report raw plus population-weighted screening estimates; and
5. gate expected combat activity by side/family/context so an inactive lane cannot be hidden by its opponent.

## Accepted baseline

Checkpoint 93 is built directly from native-accepted Checkpoint 92:

- CP92 checkpoint-definition SHA-256: `070b9e46446e68a4aaeb74773d9f9d9000618c119c8294f37567de9a6dae3ea1`
- CP92 repository-manifest SHA-256: `fda73ad40d9f122dff1036bdadc874c30de67454ec89232810707ec53075f31b`
- SDK: 8.0.423 expected / 8.0.423 actual
- Build: 0 warnings / 0 errors
- Tests: 863 passed / 0 failed / 0 skipped
- Runner: 8 of 8 stages passed
- ScenarioRunner self-tests: 56 passed
- Failed gates: 0
- Monte Carlo/primary study: none, as intended for CP92

CP92's exact manifest and compact native-acceptance provenance are embedded under `docs/validation/evidence/checkpoint-92/`.

## Authority boundary

Checkpoint 93 changes simulation-analysis infrastructure and its standing documentation only. It does **not** change:

- Game Concept v0.6z gameplay rules;
- Technology Architecture Matrix values/statuses;
- component catalog values;
- weapon/defense/reactor/sensor balance values;
- accepted AI doctrine behavior;
- CP92 reference-mining source, transcript, observation, note, or synthesis content; or
- any Spacedock candidate's authority status.

The CP92 reference corpus remains evidence for later design discussion. None of its concepts are promoted by this checkpoint.

## Standing architecture v0.10

`Technology_Integration_Permutation_Suite_Architecture_v0_10` supersedes v0.9 for current simulation planning while preserving the same generalized construction envelope.

The deterministic envelope remains:

- 82,944 raw Cartesian combinations;
- 22,592 legal builds at 35 Installation Space or less;
- 4,672 exact-fill builds at 35 Space;
- 11,328 near-fill builds at 32-34 Space;
- 6,592 underfilled builds at 31 Space or less;
- 510,398,464 oriented self-inclusive pairings;
- 255,210,528 unordered-with-self pairings;
- 510,375,872 oriented distinct pairings; and
- 255,187,936 unordered distinct pairings.

Construction legality is unchanged: at least one Main Weapon and one Reactor are required; explicit second homogeneous Main Weapons/Reactors remain legal when actual Space permits; redundant ECM/ECCM is non-additive; simultaneous Tactical Power insufficiency is an operational tradeoff rather than a construction illegality.

## Engagement-readiness classification

The generator classifies each oriented build-versus-opponent relationship independently of simulated firing results.

`reference_ready` means the observer can obtain the required Firm attack-quality track and is within its current physical weapon range at Range 3.

`closing_ready` means Range 3 is not attack-ready, but legal closing to Range 2, 1, or 0 can satisfy those structural requirements.

`engagement_denied` means the declared Sensor/EW/weapon capability cannot produce legal attack eligibility even after closing to Range 0.

The classifier uses the current Sensor/EW resolver and baseline weapon ranges. It intentionally does not infer readiness from later Tactical Power allocation, movement doctrine success, actual shots, or victory. Those are runtime outcomes and are reported separately.

## Side-specific combat-activity telemetry

The existing aggregate direct-action and missile-launch counters remain unchanged. CP93 adds Side-A and Side-B opportunity/action counters and validates that they sum back to the accepted aggregate telemetry.

Study-quality activity gates operate only on cohorts that are structurally expected to engage:

- fixed Range 3: `reference_ready`;
- TrackAware dynamic geometry: `reference_ready` and `closing_ready`.

Kinetic/Energy sides are checked through direct-fire activity; Missile sides through launch activity. `engagement_denied` builds remain valid members of the all-legal ecosystem and are not failed merely because they have zero attack opportunities.

This separation is specifically intended to distinguish a bad/denied build from a bad initial geometry or a doctrine/integration failure.

## Matched population sampling

The CP90 named diagnostic set remains at 48 ordered logical pairings. The new statistical slice is based on **unordered distinct legal pairs** rather than independently sampled orientations.

Population cells cross:

- 4 composition classes;
- 4 orientation-neutral progression-magnitude strata (`equal_low`, `equal_high`, `near`, `far`); and
- 6 canonical Space-pair strata.

This creates 96 cells. Each cell receives exactly one deterministic unordered distinct base pair. Every sampled base pair is emitted as both forward and reverse orientation, producing 192 stratified logical pairings. With the named diagnostics, CP93 generates 240 logical pairings across 3 geometries = **720 actual-consumer variants**.

Pair bundle ID, orientation, build IDs, seed, composition, progression magnitude/direction, Advanced Component Count distance, used-Space signed/absolute delta, Space stratum, weapon-family pair, information-control direction/distance, readiness, population-cell key, and cell population are all explicit/reproducible metadata.

## Population coverage and weighting

The generator analytically counts unordered distinct legal pairs in every one of the 96 population cells without materializing all 255,187,936 pairs. It emits machine-readable population coverage with per-cell population, sample count, and inclusion fraction.

The combat review emits both raw sample summaries and population-weighted screening estimates. The weight of a sampled base pair is its cell's unordered-distinct legal-pair population.

This weighting corrects the deliberate over/under-sampling of cells, but it does **not** imply that one selected pair exhaustively represents every build inside that cell. In particular, readiness can vary within a cell. The mutually-active weighted cohort is therefore explicitly a screening estimate based on the sampled pair's readiness, not an exact census of the cell's active fraction.

No universal scalar technology score is introduced. Technology comparisons remain decomposed into explicit progression, Space, weapon-family, information-control, and readiness dimensions.

## Bounded CP93 proving study

Checkpoint 93 intentionally does not widen the pair sample yet. It first proves that the new analysis pipeline works end-to-end:

- deterministic enumeration/preflight;
- generated 720-variant study;
- actual-consumer preflight;
- 1 trial per variant full-pipeline smoke = 720 executions;
- 2,000 substantive trials per variant by default = 1,440,000 primary trials.

This workload is large enough to exercise all reporting/gating paths but deliberately smaller than CP90a's 10,000-trial-per-variant screen. If CP93 is native-clean and its reports are useful, a later checkpoint can widen the sampled fraction and selectively increase trials in interesting regions.

## New review outputs

The generator adds or extends:

- `legal-builds.csv` with Space-utilization and information-control metadata;
- `pairing-plan.csv` with matched bundle/orientation, progression, Space, family, information-control, readiness, and population metadata;
- `population-coverage.csv`; and
- `population-coverage-summary.json`.

The combat consumer adds:

- `cross-tl-cp93-paired-review.csv` for forward/reverse matched results and orientation gap;
- `cross-tl-cp93-population-weighted-review.csv` for raw versus population-weighted all-legal and mutually-active screening estimates; and
- `cross-tl-cp93-activity-review.csv` for auditable side-specific expected/observed activity.

These reports are diagnostic evidence only.

## Native acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-93\apply_checkpoint_93.ps1 -RepositoryOnly
```

Full bounded acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-93\apply_checkpoint_93.ps1
```

`-DeepCalibration` intentionally aliases the same bounded workload for CP93; wider/higher-trial escalation is deferred until this architecture is accepted.

## Expected full native result

At the default CP93 setting:

- pinned SDK 8.0.423;
- warning-as-error build with 0 warnings/errors;
- all unit tests;
- 13 configured runner stages;
- 57 ScenarioRunner self-tests;
- 720 generated cross-TL variants;
- 720 one-trial smoke executions;
- 1,440,000 substantive primary trials; and
- zero failed release gates or trial errors.

The exact final unit-test count is inherited from the source tree and should remain 863 unless compilation of the additional self-test is represented only in the existing ScenarioRunner self-test harness, as intended.

## Acceptance decision boundary

A green Checkpoint 93 run validates the v0.10 analysis architecture and its bounded evidence pipeline. It does not promote any technology candidate. The intended next decision is whether the matched/readiness/Space/population reports are sufficiently rigorous to justify a later broader legal-pair sample, not whether any one sampled component should be retuned immediately.
