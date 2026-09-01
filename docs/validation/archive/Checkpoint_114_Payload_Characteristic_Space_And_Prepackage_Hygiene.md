# Checkpoint 114 - Payload Characteristic Space and Pre-package Hygiene

## Purpose

Turn CP113's ammunition/warhead architecture into a simulation-only research consumer before any numerical promotion, and make repository-root packaging cleanup automatic and enforceable.

## Research scope

CP114 tests 3,184 exact-fill mirrored variants:

- 2,720 Missile payload/warhead variants across TL4, TL5, TL7, and TL9;
- 464 Kinetic ammunition variants across TL4-TL9.

The study compares GP controls, shaped/APEN warheads, three anti-Shield characteristic families, observer-safe adaptive doctrine, coordinated dual-launcher specialist+GP salvos, Fusion/Antimatter GP maturation envelopes, smart Kinetic projectiles, dense penetrators, and saturation/submunition packets.

The normal native run uses 2,000 trials per variant = 6,368,000 engagements. The checked-in authoring evidence is a bounded 20-trial-per-variant mechanism pass and is not calibration authority.

## Information and damage boundary

Adaptive doctrine may use only observer-side Firm-track combat assessment. It cannot read exact hidden defense values or hidden EW arithmetic. The consumer remains `layered_defense_hull_only`; internal critical/subsystem damage is not simulated.

## Repository hygiene

Before validation/packaging, `tools/checkpoints/prepackage_repository_hygiene.py --apply` archives recognized historical root checkpoint manifests into their checkpoint evidence directories and removes disposable root checksum residue. `--check` fails if stale root checksum/manifest artifacts remain.

CP114's own repository manifest is stored under `docs/validation/evidence/checkpoint-114/`, not at repository root.

## Non-promotion boundary

CP114 changes no CP109 numerical matrix value, CP110 Reactor candidate, Concept rule, or C#/Godot production value. Payload profiles are exploratory characteristic-space candidates only.

## Native validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-114\apply_checkpoint_114.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-114\apply_checkpoint_114.ps1
```

`-RepositoryOnly` runs deterministic tests/parity/smoke and validates checked-in bounded evidence. The normal invocation additionally runs the 6.368-million-engagement payload study and validates its native result.
