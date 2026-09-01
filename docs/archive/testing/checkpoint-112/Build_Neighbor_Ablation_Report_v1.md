# Checkpoint 112 Build-Neighbor / Ablation Diagnostic Report v1

## Executive assessment

Checkpoint 112 is a causal diagnostic expansion of the native-accepted Checkpoint 111 same-TL ecology. It does not change or promote any CP109 technology number, CP110 Reactor candidate, C#/Godot runtime value, or gameplay rule. Its purpose is to decompose the strongest CP111 review signals before any balance decision.

The study contains 1,200 targeted same-TL variants: 1,056 Energy-defense ablations across TL3-TL8, 24 movement-order/start-range diagnostics around the strongest TL7/TL9 Kinetic-vs-Missile cliffs, and 120 late-Missile attrition ablations across TL7-TL9. All target and control builds exactly fill Hull Installation Space after explicit zero-tactical-effect mission/AUX accounting. Mixed-TL populations remain registered but are not executed.

The checked-in authoring evidence uses 100 trials/variant (120,000 engagements). The native workload uses 2,000 trials/variant (2,400,000 engagements). Outcome thresholds are review signals only.

## Energy defense-specialist decomposition

The authoring evidence indicates that the Energy defense-specialist signal is primarily a **defensive-package effect**, with the Energy main weapon providing an additional but smaller contribution.

Across TL3-TL8, the full Energy-defense package averages about 90.6% conditional wins against the eleven standard same-TL opponents. Replacing only the Energy main weapon while retaining the same Shield/ECCM/Energy-PDS/Hardener package yields about 86.2% with a Kinetic main and 79.3% with a Missile main. Thus the Energy weapon matters, especially at TL4/TL6/TL8, but it does not explain the package's overall robustness by itself.

The strongest ablation by far is removing the Shield. That reduces mean conditional win share by roughly 39-61 percentage points depending on TL, about 53.8 points on average across TL3-TL8. Removing PDS is a much smaller effect overall (about -4.1 points), while removing both PDS and the Hardener averages about -17.4 points because the interaction is material at the earlier tiers.

The Shield Hardener is strongly useful in its early/mid life but becomes numerically redundant once the standard Shield acquires Shield Armor 1. In the current candidate matrix the Hardener is defined as `1 TP sustained -> Shield Armor 1; nonstacking`; the standard Shield reaches native Shield Armor 1 at TL7. Accordingly, removing the Hardener changes almost nothing at TL7-TL8. This is not automatically a defect: the legacy Hardener may simply become obsolete at that point, or a later Hardener family may eventually replace it. CP112 does not alter the branch.

Removing ECCM has almost no aggregate effect in this specific Energy-ablation population. That does **not** establish that ECCM is worthless. Many opponents do not create an ECM condition in which ECCM is the marginal factor, and earlier dedicated EW studies already establish ECCM value under matched jamming. The correct interpretation is only that ECCM is not the primary source of this Energy package's CP111 robustness.

### Working interpretation

The CP111 Energy-defense signal should not be treated as evidence for a simple Energy-main nerf. The first-order factor is the Shield/recharge/protection package; Energy-main quality becomes more important at selected later TLs. A later calibration pass should therefore separate Shield capacity/recharge/protection from weapon tuning rather than adjusting Energy damage or accuracy in isolation.

## Movement-order/start-range decomposition

The strongest CP111 movement-order cliffs are **not merely an edge-to-edge map artifact**.

For TL7 Kinetic dual-main versus Missile dual-main, the authoring movement-order swing remains roughly 44-53 percentage points at starting ranges 4, 6, 8, and 10. TL7 dual-Reactor Kinetic-versus-Missile remains strongly order-sensitive as well, although the range-8 lane is somewhat less extreme. The TL9 Kinetic dual-main versus Missile dual-main comparison remains even more sensitive, with roughly 40-78 point swings across the four starting ranges in the authoring pass.

This points toward the sequential movement/response geometry itself, interacting with very high STL movement and divergent weapon envelopes, rather than a single radius-5 edge-start condition. The existing Concept intentionally leaves final production initiative unresolved and allows the second mover to gain geometric information while pre-Movement Tactical Power commitments remain fixed. CP112 therefore records this as an initiative/geometry diagnostic, not a weapon-balance failure.

A later movement study should expand from the axial lane into full 2D radius-5 geometry and compare alternative initiative/commitment policies before any Kinetic/Missile number is changed because of these cliffs.

## Late Missile attrition decomposition

The TL7-TL9 Missile-balanced versus Missile-defense stalemates are primarily a **Shield sustain / damage-packet threshold interaction**.

Removing the Shield almost eliminates the unresolved equilibrium at every tested late TL: unresolved rates fall to only a few percent in the 100-trial authoring pass, and the attacking Missile-balanced ship usually wins. By contrast, removing the Hardener or ECCM changes little. That is expected at TL7-TL9 because native Shield Armor is already 1, making the TL3 Hardener's nonstacking Shield Armor 1 effect redundant.

Removing PDS materially increases terminal hits, but it is not sufficient by itself to break the sustained Shield equilibrium for the balanced single-main attacker. At TL7/TL8, no-PDS lanes begin producing substantial Hull damage yet still remain highly unresolved. At TL9, even removing PDS leaves the balanced lane 100% unresolved in the authoring evidence: roughly 19 terminal hits can be absorbed/recovered without Hull damage because the TL9 Shield/Armor package and between-hit recharge repeatedly reset the damage threshold.

Doubling the engagement horizon from 60 to 120 turns does not cure the full-defense stalemate. The issue is therefore not simply that the 60-turn timeout is too short.

Dual-main Missile attackers do not generally time out because they omit the Shield in the CP111 archetype and can themselves be killed by the defender. However, their conditional win share against the intact Missile-defense package remains near zero. That reinforces the conclusion that the defensive package is the limiting factor rather than a lack of simulation time.

### Working interpretation

Do not apply a blanket Missile buff from this evidence alone. The current standard Missile warhead remains a flat Damage 5 / SPEN 1 / APEN 2 from TL1-TL9 while late Shields and Armor continue to progress. CP112 establishes that this produces a real late damage-packet threshold interaction, but the next numerical experiment should distinguish warhead progression, salvo/package size, Shield recharge, Shield Armor, and Armor protection before choosing which parameter should move.

## Damage-model scope

As in CP111, the Python research consumer is `layered_defense_hull_only`. Shields, Armor, Hull, ammunition, power, sensing/EW, PDS, fuel, movement, and terminal Hull destruction are modeled. Internal criticals and subsystem hits are not. CP112 does not change that boundary.

## Recommendation

Native-validate the 2.4-million-engagement CP112 workload. If the large native sample reproduces these causal patterns, accept CP112 as diagnostic evidence and then choose the next calibration slice from the results rather than changing values automatically.

The likely follow-ups are:

1. Shield/late-defense numerical calibration with controlled capacity/recharge/Shield-Armor perturbations;
2. Missile warhead/salvo progression sensitivity against that defense envelope;
3. full 2D movement/initiative geometry around the TL7/TL9 Kinetic-vs-Missile cliffs;
4. only then, if still indicated, direct Energy-main adjustments.

No CP112 result automatically promotes a numerical change.
