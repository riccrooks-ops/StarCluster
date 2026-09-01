# Weapon Family Simplification and Swarmer Architecture v0.1

**Checkpoint:** 117  
**Status:** Active KISS consolidation companion to `Weapon_Ammunition_And_Warhead_Architecture_v0_3.md`

## Compact family model

| Family | Normal progression | Deliberate player-facing flexibility |
|---|---|---|
| Energy | emitter/focusing/power architecture | bounded power/output modes |
| Kinetic | accelerator + automatic projectile/material/smart-correction maturation | normally none at the ammunition level |
| Missile | propulsion/guidance/seeker + automatic GP energetic-yield maturation | distinct Flight families only when the whole attack package changes |

## Swarmer branch

Swarmer is the retained Missile-family branch for the next focused study. It represents a Flight that disperses into many smaller terminal vehicles or submunitions. It remains one tactical Flight and one terminal attack package.

Candidate identity:
- improved terminal coverage / effective accuracy;
- reduced concentrated damage per internal packet;
- bounded resistance to PDS through saturation;
- natural weakness against heavy flat protection;
- generic Missile ammunition accounting;
- ordinary Firm-terminal requirement by default.

Do not add separate subtype inventories, multiple tactical counters, additional PDS windows, multiple attack rolls, or automatic Approximate-track attack permission merely because the Flight contains submunitions.

## Complexity guardrail

A research control does not become a production choice merely because it is measurable or occasionally useful. New selectable ammunition/warhead modes require a durable player decision with a clear cost, understandable information requirements, and enough campaign relevance to justify UI and AI burden.

## Calibration priority

TL1-TL6 are primary. TL7 is advanced validation. TL8-TL9 are endpoint/stress checks. This weighting applies to interpretation and scenario allocation; it is not a rule that late technology may be internally inconsistent.
