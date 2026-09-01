# Simplified Weapon Progression Study Architecture v0.1

**Checkpoint:** 118  
**Status:** Diagnostic candidate study; no automatic numerical promotion  
**Accepted baseline:** Checkpoint 117 weapon-family simplification / Swarmer architecture

## Purpose

CP118 resumes numerical research after the CP117 KISS consolidation. It does not reopen broad ammunition menus. It asks two bounded questions:

1. What GP Missile **yield** progression is plausible when SPEN/APEN are held at the existing GP baseline rather than increasing automatically?
2. How early can a simple **Swarmer Missile** branch appear, how can it mature with minimal mechanics, and when does it naturally lose relevance?
3. For Kinetics, how much of normal projectile maturation should come from automatic smart-projectile accuracy versus raw damage or APEN growth?

## Interpretation priority

| Band | TLs | Use |
|---|---|---|
| Primary campaign calibration | TL1-TL6 | Drives conclusions and future candidate narrowing. |
| Advanced validation | TL7 | Important late-campaign check. |
| Endpoint/stress | TL8-TL9 | Detects collapse/runaway interactions; does not drive whole-game complexity by itself. |

No single all-target average is a balance objective. Weapon-family asymmetry is intentional.

## Missile characteristic space

### GP Missile

GP candidates vary **Damage only**. They retain SPEN 1 / APEN 2 as an experimental constant so CP118 can isolate yield. This does not declare SP1/AP2 the final GP baseline.

- TL1-TL2: current D5 baseline only.
- TL3-TL4: D5 reference plus D6 mature-fission control.
- TL5-TL6: D5 reference plus Fusion D6 and D7 controls.
- TL7-TL9: D5 reference plus Antimatter D7 and D8 controls.

### Swarmer Missile

Swarmer remains one Missile Flight, one tactical counter, one ammunition expenditure, one PDS reaction sequence, and one terminal attack package. The attack package may resolve bounded internal submunition packets after a single terminal acquisition roll.

Candidate axes are intentionally small:

- **coverage:** positive terminal guidance modifier;
- **packetization:** two or three smaller internal damage packets;
- **PDS saturation:** at most a 15 pp reduction to the defender's normal interception chance in the tested profiles;
- **no specialist penetration mechanics:** no added SPEN/APEN, Shield bonus damage, recharge suppression, or extra PDS windows.

Introduction is deliberately tested at TL1-TL3 even though CP117's active architecture provisionally placed the branch later. CP118 is allowed to falsify that placement.

## Kinetic characteristic space

Kinetic ammunition remains generic and non-selectable. CP118 profiles are **automatic progression controls**, not player-facing rounds.

At TL4+ the study compares:

- +5 ACC;
- +10 ACC;
- +15 ACC at higher maturity;
- +1 Damage single-axis control;
- +1 APEN single-axis control.

SPEN is not increased by any CP118 Kinetic candidate. This protects the family's intended relative difficulty against strong Shields while measuring how much ordinary accuracy, packet strength, or physical penetration contributes.

## Target set

Four legal same-TL targets and two controlled diagnostic fixtures are used:

- balanced layered legal;
- Shield-heavy legal;
- Armor-exposed legal;
- PDS-heavy legal;
- Armor-heavy controlled fixture;
- lightly protected controlled fixture.

Controlled fixtures expose characteristic-space niches and are never promotion gates.

## Study shape

- 135 exact-fill underlying builds.
- 1,824 mirrored variants.
  - 936 Missile variants.
  - 888 Kinetic variants.
- 1,032 primary TL1-TL6 variants.
- 264 TL7 advanced variants.
- 528 TL8-TL9 endpoint/stress variants.
- 50 authoring trials per variant = 91,200 checked-in diagnostic engagements.
- 2,000 native trials per variant = 3,648,000 substantive engagements.

## Blocking gates

Only mechanical/integration failures block acceptance:

- study/schema invalid;
- trial errors;
- underlying build not exact-fill;
- missing Swarmer launch/PDS telemetry;
- missing Kinetic smart-projectile telemetry;
- missing TL-priority coverage;
- regression failure in CP114/CP115a/CP116 shared research consumers;
- parity or Python self-test failure.

No win-rate threshold promotes or rejects a candidate.
