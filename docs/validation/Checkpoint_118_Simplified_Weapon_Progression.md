# Checkpoint 118 - Simplified Weapon Progression

**Status:** candidate pending native acceptance  
**Accepted baseline:** Checkpoint 117 native weapon-family simplification / Swarmer architecture  
**Automatic promotion:** none; no automatic candidate promotion is permitted

## Purpose

CP118 resumes numerical weapon research after the CP117 KISS consolidation. It deliberately avoids broad ammunition/warhead menus and instead tests three compact progression questions:

1. how much GP Missile usefulness can be restored by energetic **yield alone**;
2. whether a simple Swarmer Missile can appear earlier than CP117's provisional TL5-TL7 window, how little it needs to mature, and whether natural obsolescence is acceptable; and
3. whether automatic Kinetic smart-projectile accuracy is a cleaner normal progression axis than repeated raw Damage or APEN increases.

TL1-TL6 are primary campaign evidence, TL7 is advanced validation, and TL8-TL9 are endpoint/stress checks. Family asymmetry is intentional. No all-target win-rate target is a release gate.

## Study definition

`docs/design/testing/simplified_weapon_progression_study_v0_1.json`

Study architecture:

`docs/design/testing/Simplified_Weapon_Progression_Study_Architecture_v0_1.md`

Checked-in bounded report/workbook:

- `docs/validation/evidence/checkpoint-118/Simplified_Weapon_Progression_Report_v1.md`
- `docs/validation/evidence/checkpoint-118/StarCluster_CP118_Simplified_Weapon_Progression_v0_1.xlsx`

## Population

- 135 exact-fill underlying builds.
- 1,824 mirrored variants.
  - 936 Missile.
  - 888 Kinetic.
- Priority bands:
  - 1,032 TL1-TL6 primary variants.
  - 264 TL7 advanced variants.
  - 528 TL8-TL9 endpoint/stress variants.
- 12 Missile profiles and 6 Kinetic profiles.
- Four legal target fixtures plus two controlled diagnostic fixtures.

### Missile boundaries

- GP explicit candidates vary Damage only and retain the study's SPEN 1 / APEN 2 diagnostic baseline.
- SP1/AP2 is held only to isolate yield; CP118 does not promote it as a permanent production GP baseline.
- Swarmer remains one Flight, one ammunition expenditure, one PDS interaction sequence, and one terminal attack package.
- Swarmer candidate axes are bounded terminal guidance/coverage, two-or-three internal packets, and at most a 15 pp PDS interception penalty.
- Swarmer gains no special SPEN/APEN, Shield bonus damage, recharge suppression, extra PDS windows, or Approximate-track targeting permission.

### Kinetic boundaries

- Kinetic profiles are automatic progression controls, not selectable ammunition.
- Candidate axes are +ACC, +DAM, or +APEN as independent controls.
- No CP118 Kinetic candidate changes SPEN or introduces packet/tandem/saturation ammo menus.

## Checked-in authoring evidence

The bounded authoring run uses 50 trials per variant:

**1,824 variants x 50 = 91,200 engagements.**

It is diagnostic evidence only and cannot promote a value. It reported zero failed gates.

Primary authoring signals to reproduce at native scale include:

- a simple early Swarmer is mechanically viable at TL1-TL2 but fixed small packets fall behind by TL3;
- a stronger two-packet mid Swarmer can recover a TL4 niche;
- a bounded 2 x D4 mature Swarmer is strongly relevant around TL6 and retains a narrower TL7 niche, while naturally fading at TL8-TL9;
- PDS-saturation telemetry shows the tested Swarmer penalty reducing successful PDS interception and increasing terminal hits without adding resolution windows;
- GP Missile yield-only candidates materially restore mid/advanced-ladder performance without SPEN/APEN creep;
- Kinetic +ACC produces a clean increase in actual hit rate, while +DAM often creates larger cross-defense swings and +APEN remains target-dependent.

These are hypotheses, not promotion gates.

## Native workload

Normal native acceptance runs:

**1,824 variants x 2,000 trials = 3,648,000 engagements.**

The normal invocation remains diagnostic even if one candidate leads its cohort.

## RepositoryOnly validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-118\apply_checkpoint_118.ps1 -RepositoryOnly
```

This must run:

- CPython 3.13 resolution and C#/Godot production-language boundary;
- automatic prepackage root hygiene apply/check;
- CP118 KISS/schema/gate preflight;
- all Python research self-tests;
- 25 C#/Python parity fixtures;
- CP114 `payload-study` one-trial regression smoke;
- CP115a `weapon-family-study` one-trial regression smoke;
- CP116 `warhead-generation-study` one-trial regression smoke;
- full CP118 1,824-variant one-trial smoke;
- deterministic repository/evidence/manifest contract.

## Full native validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-118\apply_checkpoint_118.ps1
```

This performs all RepositoryOnly checks and then the 3.648-million-engagement substantive study before final contract verification.

## Acceptance boundary

CP118 may be accepted when all mechanical/integration gates pass and the substantive result shape is complete. Candidate performance remains evidence for a later narrowing/promotion decision; CP118 itself changes no production C#/Godot rule, no CP109 candidate matrix value, no CP110 Reactor candidate, and no Concept authority.
