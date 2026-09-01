# Player TL1-TL9 Technology Architecture v0.6

## Purpose

Checkpoint 54 preserves accepted Checkpoint 53a TL1/TL2 behavior as frozen regression territory and opens **TL3 candidate runtime screening**. TL3 is the first major cruiser refit milestone: 2 Weapon Bays and 2 Auxiliary Capacity. No TL3 values are promoted by this checkpoint, and TL4-TL9 runtime generation remains deferred.

## Frozen early architecture

- Weapon Bays TL1-TL9: `1 / 1 / 2 / 2 / 2 / 3 / 3 / 3 / 4`.
- AUX Capacity TL1-TL9: `1 / 1 / 2 / 2 / 3 / 3 / 3 / 4 / 4`.
- TL1/TL2 standard combat profiles, legal AUX inventories, PDS progression, TL2 Ablative AP0/AI2, Combat Battery 3 x +1 TP semantics, Power Capacitor semantics, AMM 25-round reserve, and endurance rules remain frozen from accepted Checkpoint 53a.

## TL3 standard-profile screening

Three numerical vectors are executable and intentionally provisional:

1. **Capacity-only structural control** - the accepted TL2 numerical combat vector at TL3 installation capacity. It isolates the effect of a second Weapon Bay and expanded AUX Capacity.
2. **Balanced first-refit candidate** - a moderate TL3 technology step across structure, shields, reactor, targeting, movement, and weapon characteristics.
3. **Output-forward sensitivity control** - deliberately stronger than the balanced candidate so the study can reveal where progression becomes excessive.

The screening study does not automatically promote any vector.

## Two Weapon Bays

A TL3 cruiser may install two weapon batteries. Each bay remains one attack package and one roll per use. Checkpoint 54 permits all ordered Kinetic/Energy/Missile two-bay combinations. The first/primary bay drives the current opponent-aware range doctrine; the second bay fires opportunistically when legal. This is a bounded screening policy, **not** the final mixed-battery tactical doctrine.

Two same-family Kinetic or Missile bays draw from the same ship-wide family ammunition reserve. A mixed-family secondary bay receives the appropriate separate support representation. All attacks are committed before damage resolution, preserving simultaneous-volley semantics.

## Two Auxiliary Capacity

TL3 may install either two capacity-1 effects or one capacity-2 component. Same-source stacking remains prohibited unless an explicit component rule allows it. Checkpoint 54 uses thirteen curated capacity-2 combat loadouts plus a no-AUX diagnostic. Composite runtime profiles are a screening abstraction for combined effects; they do not yet claim perfect separate-component damage exposure for every pair.

New TL3 combat-support candidates include:

- Auxiliary Reactor: capacity 2, +1 renewable Tactical Power candidate.
- Shield Battery: finite restoration candidate.
- Shield Booster: +1 shield-capacity candidate.
- Shield Power Stabilizer: 2 shield restored per 1 TP, capped at 1 TP per recharge decision.
- Kinetic PDS: TL2 accuracy held while ammunition efficiency improves.
- Energy PDS: TL2 accuracy held while readiness power improves from 2 TP to 1 TP.
- AMM: 1 TP, 25 rounds, TL2 accuracy held while higher-TL salvo/efficiency mechanics remain deferred.
- Combat Battery: unchanged 3 x +1 TP, maximum one discharge per tactical turn, no encounter cap.
- Power Capacitor: stored-power capacity candidate increases to 2 while discharge remains +1 per use and later-turn recharge remains required.
- Ablative Armor: AP0/AI2 held for the initial TL3 screen so the new capacity and weapon environment can be isolated before another armor step.

## Tactical Power envelope

The balanced TL3 candidate is tested under normal conditions and a common 3-TP sustained diagnostic load. Combat Battery, Power Capacitor, and Auxiliary Reactor are compared in identical two-bay contexts. The diagnostic is not a new universal hotel-load rule; it exists to reveal whether power-support choices become useful without becoming compulsory.

## Runtime boundary

Checkpoint 54 adds four studies totaling 870 Monte Carlo variants:

- `tl3-itc01-standard-profile-screening`: 72 variants.
- `tl3-itc02-two-bay-loadout-screening`: 141 variants.
- `tl3-aux01-two-capacity-loadout-screening`: 585 variants.
- `tl3-pwr01-two-bay-power-envelope`: 72 variants.

All Checkpoint 53a scenario JSON files are frozen by SHA-256 before these additive studies. TL4-TL9 runtime generation remains deferred pending review of TL3 progression, loadout diversity, opportunity cost, and power pressure.
