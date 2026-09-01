# Player TL1-TL9 Technology Architecture v0.5

## Purpose

Checkpoint 53 preserves Checkpoint 52 as the frozen stateful-resource baseline and performs the focused TL1/TL2 Auxiliary refinement needed before TL3 runtime work. No TL3-TL9 runtime expansion occurs in this pass.

## Accepted architecture retained

- Weapon Bays TL1-TL9: `1 / 1 / 2 / 2 / 2 / 3 / 3 / 3 / 4`
- AUX Capacity TL1-TL9: `1 / 1 / 2 / 2 / 3 / 3 / 3 / 4 / 4`
- Kinetic PDS, Energy PDS, and AMM all enter at TL1.
- Normal TL1 and TL2 cruisers have one AUX Capacity.

## Combat Battery

The TL1/TL2 Combat Battery is **three finite charges, each providing +1 Tactical Power, with at most one discharge per tactical turn**. There is no per-encounter cap: one prolonged fight may consume all three charges over three turns. Spent charges persist until a valid replenishment opportunity; they do not auto-refill between ordinary encounters.

## Power Capacitor

The TL2 Power Capacitor begins charged with one stored Tactical Power. It may discharge that point to provide +1 TP. It then remains empty until a **later turn** spends 1 TP to recharge it. Charging and discharging on the same turn is prohibited. The capacitor therefore shifts power between turns instead of generating net energy. Existing between-encounter/FTL charging abstraction remains in place until strategic power logistics are implemented.

## Tactical shield recharge

Tactical shield recharge is a core ship capability, not a feature unlocked by a power-support Auxiliary. Any functional ship may allocate Tactical Power to legal shield recharge. Combat Battery and Power Capacitor may make that allocation affordable, but do not create the action. The Checkpoint 53 matrix uses a resource-aware policy that reserves expected attack/defense power before spending discretionary power on tactical shield recharge.

## PDS and AMM endurance

The accepted early PDS accuracy and Reaction Capacity candidates are retained for this pass. AMM costs 1 TP to ready at TL1 and TL2, the same readiness cost as Kinetic PDS; Energy PDS remains 2 TP. AMM is held at **25 rounds at both TL1 and TL2** for the current campaign-endurance baseline. It is not tuned to force depletion in one duel.

## Endurance components

Kinetic and Missile Magazine Expansions, AMM ammunition, and Combat Battery charges are evaluated on a repeated-engagement timescale. They are not required to equal armor, evasion, or PDS in one isolated fight. The resource-endurance stage is diagnostic evidence and does not automatically promote values.

## Runtime boundary

Checkpoint 52 and earlier studies remain frozen regression evidence. Checkpoint 53 adds `aux-itc04-tl1-tl2-auxiliary-refinement` as an **870-variant** refined matrix, `aux-abl01-tl2-ablative-candidate-study` as a 96-variant TL2 Ablative review, `aux-pwr01-tactical-power-stress` as a 78-variant power-stress diagnostic, and `aux-end02-resource-semantics-lock` as a deterministic resource-timescale stage. Higher-TL runtime generation remains deferred.


## Checkpoint 53 refinement notes

- Ablative Armor moves from TL1 to TL2. The leading TL2 entry candidate is AP0 / AI2; AP0 / AI3 and AP1 / AI1 are comparison candidates, while AP1 / AI2 remains a historical control only.
- AMM remains a TL1 PDS sub-family. TL1 and TL2 both carry 25 rounds and require 1 TP readiness; current accuracy progression is unchanged.
- Combat Battery is three finite +1 TP charges. At most one charge may discharge per tactical turn, but there is no encounter cap; one prolonged fight may consume all three charges over three turns.
- Power Capacitor remains TL2: +1 TP discharge, later-turn 1 TP recharge, no same-turn recharge/discharge.
- `aux-pwr01-tactical-power-stress` adds a common sustained-load diagnostic so Battery and Capacitor are evaluated where discretionary Tactical Power is actually constrained. The diagnostic does not imply a new universal hotel-load rule.
- TL3-TL9 runtime generation remains deferred until this TL1/TL2 refinement is accepted.
