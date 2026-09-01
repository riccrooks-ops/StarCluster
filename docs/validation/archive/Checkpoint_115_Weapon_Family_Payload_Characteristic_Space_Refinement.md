# Checkpoint 115 - Weapon-Family Payload Characteristic-Space Refinement

## Purpose

Refine CP114's exploratory ammunition/warhead model around explicit weapon-family identity before any numerical promotion. CP115 adds energetic GP Missile maturation, contemporary-GP specialist pairing, accuracy/coverage-oriented Kinetic submunitions, ordered tandem Kinetic packets, controlled target archetypes, and native Energy reference lanes.

## Research scope

CP115 reconstructs **4,064 mirrored variants**:

- 2,272 Missile family-characteristic variants across TL4, TL5, TL7, and TL9;
- 1,664 Kinetic family-characteristic variants across TL4-TL9;
- 128 Energy reference variants across TL4, TL5, TL7, and TL9.

The study uses eight target fixtures. Five are legal exact-fill ship packages; three (`shield-overmatch-fixture`, `armor-heavy-fixture`, and `light-fixture`) are controlled diagnostic fixtures and are never promotion gates.

The checked-in authoring evidence is 20 trials/variant = **81,280 engagements**. The normal native run uses 2,000 trials/variant = **8,128,000 engagements**.

## Family-identity lens

The study does not demand equal performance against every defense. It asks whether each family retains intelligible niches and costs: Kinetic coverage/physical-penetration options, Energy's existing power-mode/reference behavior, and Missile GP flexibility plus mission-specific warheads. This is an interpretation guardrail rather than a newly imposed numeric balance rule.

## Missile scope

- legacy D5/SP1/AP2 GP remains a regression control;
- fission-, fusion-, and antimatter-era GP envelopes test energetic maturation;
- shaped/APEN and three Shield-specialist families remain exploratory;
- dual-launcher static specialist pairs use specialist + **contemporary GP**;
- observer-safe adaptive pairs begin on GP and switch only after permitted Firm-track combat assessment.

## Kinetic scope

- smart/maneuvering projectile +ACC envelopes;
- dense penetrator tradeoffs;
- +ACC saturation/submunition packages with one battery = one d100 attack package;
- ordered tandem packages that resolve multiple internal packets only after the single attack roll succeeds;
- reversed-order controls isolate sequencing effects.

## Damage and information boundary

The research consumer remains `layered_defense_hull_only`; internal critical/subsystem damage is not simulated. Adaptive Missile doctrine may use only observer-safe qualitative combat assessment and cannot inspect exact Shield capacity, recharge, Armor values, hidden components, or hidden EW arithmetic.

## Repository hygiene and authority

The standing prepackage hygiene step archives/removes recognized stale root checksum/manifests before manifest freeze and fails validation if root residue remains. CP109/CP110 numerical candidates, Concept v0.7k, C#/Godot production source, and accepted CP114 evidence remain unchanged.

## Native validation

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-115\apply_checkpoint_115.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-115\apply_checkpoint_115.ps1
```

`-RepositoryOnly` applies/checks root hygiene, runs all Python self-tests, 25 parity fixtures, and the full 4,064-variant one-trial smoke, then validates checked-in authoring evidence and the repository contract. The normal invocation additionally runs the 8.128-million-engagement substantive study.

No CP115 candidate promotes automatically.
