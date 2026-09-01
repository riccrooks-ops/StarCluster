# Checkpoint 147 — Tactical Package Utility and Powered Resource Allocation

## Status

Candidate pending native Windows acceptance. Checkpoint 146 is the native-accepted baseline. CP147 is logic-only: it changes no Technology Numerical Matrix value, player-facing Concept rule, weapon/PDS/Reactor statistic, movement value, ammunition value, DEF/RES value, or Stage-B authority.

## Purpose

CP146 removed the fixed subsystem-priority starvation pathology, but one tactical choice remained rule-based: a powered Kinetic/Energy main weapon could either attack the opposing ship or be held for missile interception, yet the doctrine did not compare those actions in the immediate tactical state. CP147 introduces a bounded tactical-package utility selector so Tactical Power allocation and the use of the powered resources are reasoned about together.

The doctrine is information-limited. It may use own-system mechanics, current geometry/track, current Shield/Armor/Hull state, observed hostile actions, and missiles already visible/in flight. It may not inspect hidden opponent build fields. Unknown capability can justify residual readiness, but it contributes no invented numerical threat value.

## Utility contract

Candidate packages are compared by expected one-turn raw combat swing: expected damage inflicted plus expected structural damage prevented. Exact ties deliberately favor continued offense, then defensive value, funded main banks, Active Sensor, Firm track, fewer held banks, and lower TP. The pure selector is shared between Python and C# through `cp147_tactical_package_utility_parity_fixtures_v0_1.json`; the fixture contains policy examples only, not promoted component values.

Important safeguards:

- Active Sensor remains the normal established-combat posture; Passive is a deliberate package fallback.
- ECCM is considered only when observed ECM changes the usable track.
- PDS utility is attached to projected terminal threats, not merely to a distant missile somewhere in flight.
- A sole legal K/E ship attack is not sacrificed for ordinary Shield/Armor exposure. Defensive diversion of that sole legal attack requires projected terminal Hull risk and superior defensive utility.
- If no legal ship shot exists, K/E Held Main may protect against a Firm-tracked terminal missile. Dual-main designs may split banks between offensive and defensive use.
- Tactical Shield recharge is phase-aware: it cannot pre-consume core TP, currently projected terminal PDS demand, or a known-Energy Shield-Hardener reservation. Distant missiles alone do not suppress recharge.
- Finite-ammo main weapons and PDS stop consuming TP after exhaustion.
- Damage Control/Armor recovery and Energy overload compete for residual TP using current-state utility rather than static ordering.

## Versioning and causal study

The kernel advances to v0.7. `cp146_contextual` remains explicitly callable and must reproduce the accepted native CP146 contextual replay field-for-field. CP147 uses `cp147_tactical_utility`.

The matched study is intentionally bounded:

- 252 accepted CP145/CP146 diagnostic identities;
- 25 exact CP144-seed trials per identity;
- 6,300 CP146-contextual baseline combats;
- 6,300 CP147-utility candidate combats;
- 12,600 total matched combats;
- no tuning, automatic promotion, or Stage B.

The accepted CP146 native summary, doctrine summary, and exact contextual replay table are retained under `docs/validation/evidence/checkpoint-147/accepted-cp146/` and hash-locked. The submitted native CP146 results archive remains external provenance by SHA-256 rather than being recursively embedded.

## Authoring evidence

The final authoring candidate replay completed all 252 identities / 6,300 CP147 combats with 0 trial errors, 0 turn-cap sentinels, and 0 resolved fights at 25+ turns. The accepted CP146 baseline over these identities has the same 0/0 duration counts; mean scenario duration changes only from approximately 10.756 to 10.640 turns.

The utility branch was exercised rather than remaining synthetic: 134,064 package decisions in the matched authoring run, 116,343 direct-main package selections, 47,187 PDS-package selections, and 396 natural Held-Main selections/attempts. The held layer recorded 359 interceptions. No observed sole-main legal ship attack was diverted without the required Hull-risk condition. Focused fixtures separately exercise the legal sole-main Hull-risk diversion branch because the matched population's natural Held-Main events occur when no legal ship attack is available.

The CP145 TL2 starvation pathology remains closed: CP147 produces 0 TL2 EW/Power-Crisis turn caps and no new saturated cells. The exact CP146 baseline path is still reproduced by focused field-for-field checks, and the full Python regression is 346/346 across 38 modules in authoring.

These are pre-handoff findings only. Native Windows execution remains acceptance authority.

## Interpretation boundary

CP147 validates tactical reasoning, not numerical balance. Outcome deltas between CP146 and CP147 must not be promoted directly into weapon/PDS/Reactor/AUX numbers. If native acceptance confirms the behavior and exact CP146 reproduction, the next research step is a new broad whole-combat response surface under the accepted utility doctrine before numerical tuning or Stage B.
