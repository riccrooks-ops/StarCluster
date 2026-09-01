# Checkpoint 142 — Combat Surface Deep Reconciliation

## Status

Candidate pending native Windows acceptance. CP141 is the native-accepted combat-duration/stalemate baseline. CP142 changes no production C#/Godot mechanics, no source Technology Matrix values, and promotes no numerical candidate.

## Purpose

CP142 closes the reconciliation gap exposed by CP141's duration diagnostics. CP139 had correctly introduced DEF/RES and later weapon candidates, but it had not imported every companion combat-model field. The result was a partial blend: newer DEF/RES operated against several older CP138 defensive/resource values.

CP142 therefore applies one rule field-by-field rather than subsystem-by-subsystem:

> **Latest explicit combat-model evidence wins where that exact field/mechanic was revisited; CP138/full-map behavior fills genuine gaps; later resource evidence remains separate; unresolved conflicts remain unresolved.**

The reconciliation ledger contains 531 explicit rows. Relative to CP141, 72 rows change their value or disposition: 66 are executable Stage-A value/semantic corrections and six are unresolved AUX disposition corrections. Seven ledger rows remain explicitly unresolved overall.

## Full-combat characteristic authority

The latest complete combat-characteristic reference is the v17-v19 combat-model line. v20-v21 intentionally pivoted to Space/TP/AUX resource architecture and preserved earlier combat-mechanics evidence rather than redefining the full combat profile.

The reconciled in-memory research candidate therefore uses:

- Hull combat durability: `12/12/13/13/14/14/15/15/16`;
- Shield Capacity: `8/9/10/11/12/13/14/15/16`;
- Shield base recharge: `0` at every TL;
- Shield tactical recharge: `+1 per TP`, cap `1` at TL1-TL7 and `2` at TL8-TL9;
- Shield DEF: `20/22/24/26/28/30/32/34/36`, effective cap 45 pp after SPEN;
- Armor AI: `6/7/8/9/10/9/10/11/12`;
- Armor tactical regeneration per TP: `0/0/0/0/0/1/1/1/1`;
- Armor regeneration TP cap: `0/0/0/0/0/1/1/2/2`;
- finite Armor regeneration reserve: `0/0/0/0/0/3/4/6/8`;
- Armor RES: `20/22/24/26/28/30/32/34/36`;
- the already-reconciled K/E/GP/Swarmer damage, accuracy/penetration, guidance, and two-subflight Swarmer semantics;
- Kinetic ammunition 100 and missile magazine 25 Flights, which already agree between CP138 and the later combat model;
- Damage Control and Tactical Computer targeting values where CP138 and the later combat-model reference already agree.

Hull Installation Space/capacity is **not** replaced by the combat-durability Hull ladder. It remains a separate CP138/v22C ship-resource axis.

## PDS semantic correction

The v17-v19 PDS probability tables are effective per-attempt chances that already include contemporary Tactical Computer assistance. The canonical full-map kernel stores `baseChancePp` and adds the Computer targeting bonus at resolution.

CP139-CP141 wrote the effective lab chance directly into the canonical base field, so Computer help was counted twice from TL2 onward. CP142 translates the effective chance back to base chance before canonical recomposition. The resulting full-map effective PDS chances exactly equal the later combat-model targets.

PDS Reaction Capacity/ammunition follow the later combat-model candidate. PDS Space/readiness TP remain CP138 resource inputs because v20 explicitly retained those resource fields rather than inferring new costs from the combat candidate. The AMM range-1 third opportunity remains an unresolved experimental toggle and is not silently enabled.

## AUX reconciliation

AUX is classified by evidence, not filled with guessed effects:

- **Shield Hardener** — executable combined candidate: +10 Shield DEF pp while powered, 1 Space / 1 TP, nonstacking.
- **Ablative Armor Layer** — latest lab profile recorded as a separate sacrificial layer with no RES/repair and TL ladder `0/1/2/3/4/5/6/7/8`; full-map installation/state integration remains unresolved, so CP142 does not invent it.
- **Powered Reactive Armor** — +10 RES existed as a response-curve mapping diagnostic, while v21 categorized PRA as a resource proxy; no combat bonus is promoted.
- **Shield Booster / Field Stabilizer** — earlier response studies were illustrative/sensitivity cases; v21 leaves their footprint/effect TBD, so no combat effect is invented.
- **Auxiliary power/batteries, repair/EW AUX** — remain bounded resource hypotheses/proxies. They do not become free sustained TP or hidden combat value.

This preserves the latest evidence while keeping unresolved design work visible.

## Resource boundary

CP142 does not replace the six v22C resource environments with a single v21 centerline. Reactor supply, weapon TP, and weapon Space remain simulation-only v22C research overlays. `R1_CENTRAL_NO_MAJOR` and `R5_CENTRAL_HIGH_DEMAND` remain mechanically equivalent while the high-AUX-demand axis is metadata-only; CP142 does not fabricate demand to differentiate them.

## Authoring paired replay

The exact same 8,220 Stage-A scenario IDs and master seed used by CP141 were replayed once under the fully reconciled candidate, with the same hard 60-turn sentinel and 25-turn gameplay-duration boundary. There were zero execution errors.

One-trial results are integration diagnostics, never final balance rates:

| Metric | CP141 accepted smoke | CP142 reconciled smoke |
|---|---:|---:|
| Resolved | 7,382 | 7,950 |
| Turn-cap sentinels | 838 | 269 |
| Resolved at 25+ turns | 1,403 | 1,089 |
| Median resolved turns | 12 | 10 |
| P90 resolved turns | 34 | 31 |
| P95 resolved turns | 41.95 | 38 |
| Defensive-recovery-loop caps | 599 | 43 |

The most important structural changes are:

- Direct-vs-Direct cap hits fall from 569/2,160 to 36/2,160.
- Kinetic mirror cap hits fall from 336/540 to 12/540.
- Energy mirror cap hits fall from 99/540 to 8/540.
- Direct-vs-Missile cap hits fall from 75/4,080 to 5/4,080.
- Missile-vs-Missile remains the principal pacing concern: caps rise from 194/1,980 to 228/1,980 while long-resolved cases fall from 1,330 to 1,085 and median resolved duration moves from 32 to 29 turns.
- One legitimate `STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION` appears naturally (TL9 Swarmer vs GP under lower-demand POWER_CRISIS), confirming the conservative stalemate path is reachable without using the 60-turn sentinel.

These shifts show that most of CP141's direct-fire recovery deadlock was integration drift, not evidence that DEF or Kinetic damage necessarily needed retuning. Missile mirrors remain a genuine post-reconciliation diagnostic region and should be investigated after native CP142 acceptance.

## Scope boundary

CP142 executes only the 8,220 one-trial reconciliation diagnostic. It performs **zero substantive balance trials**, changes no source Technology Matrix value, and cannot promote the reconciled research candidate into production authority.
