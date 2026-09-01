# Checkpoint 90 - Generalized Legal-Build and Cross-TL Stratified Screening

## Purpose

Checkpoint 90 resumes the cross-TL permutation architecture after the CP89 documentation consolidation. It generalizes the legal-build envelope beyond one-choice-per-axis exact-fill ships and exercises explicit Main Weapon/Reactor duplication plus redundant non-additive ECM/ECCM through the actual combat consumer.

This checkpoint is infrastructure and screening work. It does **not** retune or automatically promote technology values.

## Construction envelope

The v0.3 foundation enumerates nine axes inside the current 35-Space cruiser envelope:

- Main Weapon: one or two homogeneous Kinetic/Energy/Missile working profiles;
- Main Reactor: one or two homogeneous TL1/TL2 working profiles;
- Tactical Computer;
- Active Sensor, including not installed;
- Shield Generator, including not installed;
- Armor;
- ECM, including none and redundant same/mixed-rating installations;
- ECCM, including none and redundant same/mixed-rating installations;
- PDS, including not installed.

The fixed shell is STL5 + FTL5 = 10 Space. Every legal combat build requires at least one Main Weapon and one Reactor. Tactical Power sufficiency is not a legality filter. Same-type ECM/ECCM ratings never add; the actual combat runtime selects the highest applicable functional installation and can fall back to a surviving lower-rated redundant suite.

Expected deterministic accounting:

- raw combinations: **82,944**;
- legal builds at 35 Space or less: **22,592**;
- exact-fill 35-Space builds: **4,672**;
- oriented potential pairings: **510,398,464**;
- unordered-with-self potential pairings: **255,210,528**.

## Bounded actual-consumer screen

The generated screen contains 48 named diagnostic pairings plus 96 deterministic stratified pairings. The stratification crosses four composition classes with six progression-distance strata: lower-near/lower-far, equal-low/equal-high, and higher-near/higher-far. Near is a 1–2 Advanced Component Count difference; equal-low is at most 3 advanced components per side. Four ordered pairings are selected per composition/stratum cell. Each logical pairing runs at fixed Range 3 and both TrackAware movement orders.

Expected workload:

- logical pairings: **144**;
- geometries: **3**;
- generated variants: **432**;
- smoke: **432 trials**;
- normal substantive study: **4,320,000 trials** at 10,000 per variant.

## Acceptance requirements

1. Native dependency precheck reports no active Python runtime dependency.
2. Repository contract validates accepted CP89 provenance and freezes unrelated gameplay/test content.
3. Warning-as-error build succeeds on pinned .NET SDK 8.0.423.
4. All unit tests pass.
5. Deterministic enumeration independently validates legal counts, multiplicity, Space distribution, and EW redundancy rules.
6. Generated study passes actual-consumer preflight before smoke/substantive execution.
7. All 432 smoke variants execute one full trial before the substantive stage.
8. Fixed references may legitimately be unable to attack because of legal construction or enemy track denial, but a zero-attack lane may not be caused overwhelmingly by self-inflicted Tactical Power starvation; TrackAware dynamic contexts preserve attack types active in their fixed reference.
9. Redundant ECM/ECCM runtime resolution remains non-additive and highest-functional-rating based.
10. Normal outcomes are review evidence only. No build, subsystem, or technology candidate is automatically promoted or retuned.

## Expected review outputs

The generator should emit the complete legal-build inventory, named-build mapping, pairing plan, foundation gates, and generated integrated study. The substantive runner should emit detailed generalized-build and progression/composition-strata review CSVs in addition to ordinary integrated-combat telemetry.

Deep Calibration is not required initially; see `docs/design/testing/Checkpoint_90_Validation_Tiers.md`.
