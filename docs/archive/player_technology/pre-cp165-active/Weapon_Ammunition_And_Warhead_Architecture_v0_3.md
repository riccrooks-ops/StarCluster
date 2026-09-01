# Weapon Ammunition and Missile-Family Architecture v0.3

**Checkpoint:** 117  
**Status:** KISS consolidation architecture; CP116 native evidence incorporated; no numerical promotion

CP117 intentionally compresses the ammunition/warhead characteristic-space work back into a simpler player-facing weapon model. CP114-CP116 remain valuable diagnostic evidence, but experimental dimensions are not automatically promoted into UI choices.

## Family identity

| Family | Primary tactical flexibility | Baseline player-facing rule |
|---|---|---|
| Energy | power/output modes | retain a small number of defined safe/output/overload choices where the power tradeoff is meaningful |
| Kinetic | automatic projectile and fire-control maturation | one normal Kinetic ammunition pool; compatible smart/projectile advances auto-mature rather than creating a per-shot ammunition menu |
| Missile | delivery/guidance + GP energetic yield; a few genuinely different flight families | one normal GP Missile line plus distinct branches such as Swarmer Missile when the whole Flight behaves differently |

Family asymmetry is intentional. Kinetic may be naturally stronger into physical Armor and weaker into Shields; Energy may naturally prefer Shields and pay more against Armor; Missile is the broader delivery family with finite ammunition, guidance, interception risk, and a small number of distinct flight architectures. Calibration must not force every family toward equal performance against every defense.

## Kinetic simplification

1. Normal Kinetic ammunition has no routine player selector.
2. Improved penetrator materials, projectile manufacturing, programmable fuzing, maneuvering correction, and later smart guidance are automatic compatible maturation when they are strict improvements.
3. The intended visible progression is therefore mainly better practical accuracy and family-appropriate physical penetration/launcher performance, not a growing list of ammunition buttons.
4. A concept that is truly different enough to justify player choice should normally become a separate installed Kinetic weapon family (for example a macron/dust accelerator) rather than another ammunition toggle.
5. The CP114-CP116 dense, saturation, tandem, and reversed-packet profiles remain archived research probes. They are not baseline gameplay commitments.

## Missile GP progression

The normal Missile Flight carries a general-purpose payload. GP maturation follows major energetic generations and is automatic on compatible flight bodies:

- **TL1 baseline:** mature conventional / fission-era GP payload appropriate to the starting setting.
- **TL5 candidate milestone:** Fusion microcharge GP maturation, gated by the existing Power relationship.
- **TL7 candidate milestone:** Antimatter GP maturation, gated by the existing Power relationship.
- **TL8-TL9:** endpoint/pinnacle behavior is validated for sanity but does not need another ordinary payload family solely to fill the ladder. Matter-conversion remains Exotic/deferred.

Higher energetic generation primarily changes usable **yield/DAM**. It does not automatically increase SPEN or APEN. The existing CP109 D5/SP1/AP2 profile remains historical numerical evidence, not a locked forever-baseline and not proof that GP should gain additional penetration as yield rises.

## Swarmer Missile branch

The **Swarmer Missile** is a distinct Missile Flight family, provisionally centered on TL5-TL7 rather than a Kinetic ammunition mode or ordinary warhead selector.

Working KISS behavior for later calibration:

- one Missile Flight counter;
- one launch from the normal generic Missile magazine;
- ordinary guidance, fuel/range, and Firm-terminal requirements unless a later profile explicitly says otherwise;
- one terminal attack roll for the Flight;
- on a successful terminal attack, a small bounded number of lower-strength submunition packets may resolve internally;
- a bounded **PDS Saturation** trait may reduce the chance that a normal PDS engagement defeats the Flight;
- a successful standard PDS engagement still defeats the attack package;
- no extra PDS windows, no literal cloud of tactical counters, and no extra natural-critical rolls;
- lower concentrated packet strength should make Swarmer performance worse against heavy flat protection unless some other explicit technology changes that relationship.

Possible later calibration axes are deliberately few: effective terminal accuracy/coverage, internal packet count/strength, and PDS Saturation. Do not simultaneously add specialist SPEN/APEN, recharge suppression, seeker exceptions, and Approximate-target fire to the same branch.

## Specialist warheads

Shaped-charge/APEN, directed-pulse/shield-disruption, radiation/electronics, antimatter-catalyzed bridge, and other specialist payload ideas remain preserved in the Idea Register. CP117 does **not** assume a standing normal warhead-selection menu.

A specialist warhead may return later only if play produces a clear unmet mission and the additional choice survives a KISS test. Exotic/rare payloads may still be individually tracked when scarcity itself is gameplay.

## Calibration priority

| Tier | TLs | Use |
|---|---:|---|
| Primary campaign calibration | TL1-TL6 | Main tuning evidence; early and middle campaign behavior must be healthy and understandable |
| Advanced-game validation | TL7 | Important high technology; confirm maturation and branch identity remain viable |
| Endpoint stress validation | TL8-TL9 | Sanity/stress checks; catch runaway thresholds or dead systems, but do not redesign the whole weapon model around rare pinnacle interactions |

TL9 may expose mathematical breakpoints and implementation defects, but it is not the default balance anchor for the nine-level game.

## What CP117 retires from the active baseline

- routine selectable Kinetic dense/penetrator ammunition;
- routine Kinetic submunition/saturation ammunition;
- tandem/reversed Kinetic packet menus;
- an assumed normal shaped/anti-Shield Missile warhead menu;
- the expectation that every experimental CP114-CP116 payload characteristic becomes a production technology;
- TL9-first whole-ladder tuning.

The historical studies stay preserved as evidence and may support future optional branches.

## Next numerical pass

The next calibration pass should be intentionally small. Calibrate the GP Missile yield milestones and the Swarmer family primarily at TL1-TL7, with TL8-TL9 as endpoint checks. Kinetic should use its ordinary contemporary projectile profile with automatic smart-projectile accuracy maturation rather than a matrix of ammunition modes. No value promotes automatically.
