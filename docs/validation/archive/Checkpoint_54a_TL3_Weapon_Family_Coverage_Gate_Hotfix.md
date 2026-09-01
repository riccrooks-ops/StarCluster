# Checkpoint 54a - TL3 Weapon-Family Coverage Gate Hotfix

## Purpose

Checkpoint 54a repairs a validation-only defect discovered during the full Checkpoint 54 native run. The TL3 two-bay Tactical Power envelope completed its Monte Carlo work but returned exit code 1 because the generic `weapon-family-coverage` gate inspected only the primary Weapon Bay.

## Failure mechanism

The power-envelope matrix intentionally uses KK, KE, EE, and EM two-bay loadouts. Missile is therefore represented by the **secondary bay** in the EM lane. The old gate examined only `SideAFamily` and `SideBFamily`, incorrectly concluded that Missile was absent, and failed the stage.

## Hotfix

The gate now evaluates family coverage from the study variant definitions and counts:

- Side A primary bay;
- Side B primary bay;
- Side A secondary bay, when present; and
- Side B secondary bay, when present.

This is the correct definition for a multi-bay technology study. TL1/TL2 studies are behaviorally unaffected because their secondary-bay fields are null.

## Frozen boundary

Checkpoint 54a changes no scenario JSON, technology profile, AUX profile, TL3 candidate value, Concept document, workbook, or Monte Carlo workload. The Checkpoint 54 release-facing manifest/readme/preflight report are archived under `docs/archive/checkpoint-54-release/` for provenance.

The workload remains **35 stages / 9,877 Monte Carlo variants / 98.77 million trials** at 10,000 trials per variant.

## Acceptance

Run repository-only validation first, then the full checkpoint. Successful execution is necessary but does not promote a TL3 candidate. The resulting TL3 balance evidence should be assessed under the original Checkpoint 54 acceptance questions.
