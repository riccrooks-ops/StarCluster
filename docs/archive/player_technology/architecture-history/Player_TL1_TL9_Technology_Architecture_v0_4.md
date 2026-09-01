# Player TL1-TL9 Technology Architecture v0.4

## Purpose

Checkpoint 52 accepts Checkpoint 51 as the frozen architecture/runtime-bridge baseline and evaluates the intended stateful behavior of early power-support and ammunition-endurance systems. No TL3-TL9 runtime expansion occurs in this pass.

## Accepted architecture retained

- Weapon Bays TL1-TL9: `1 / 1 / 2 / 2 / 2 / 3 / 3 / 3 / 4`
- AUX Capacity TL1-TL9: `1 / 1 / 2 / 2 / 3 / 3 / 3 / 4 / 4`
- Kinetic PDS, Energy PDS, and AMM all enter at TL1.
- Normal TL1 and TL2 cruisers have one AUX Capacity.

## Combat Battery

The primary TL1/TL2 candidate is the architecture value that predated the Checkpoint 51 screening inheritance: **three finite charges, each providing +1 Tactical Power, with at most one discharge per turn**. Charges persist across encounters until strategic replenishment. A two-charge version is retained as a diagnostic fallback; moving the family to TL2 is a later fallback only if the intended +1/3 implementation remains a compulsory TL1 choice.

## Power Capacitor

The TL2 Power Capacitor begins charged with one stored Tactical Power. It may discharge that point to provide +1 TP. It then remains empty until a **later turn** spends 1 TP to recharge it. Charging and discharging on the same turn is prohibited. The capacitor therefore shifts power between turns instead of generating net energy. Existing between-encounter/FTL charging abstraction remains in place until strategic power logistics are implemented.

## Tactical shield recharge

Tactical shield recharge is a core ship capability, not a feature unlocked by a power-support Auxiliary. Any functional ship may allocate Tactical Power to legal shield recharge. Combat Battery and Power Capacitor may make that allocation affordable, but do not create the action. The Checkpoint 52 matrix uses a resource-aware policy that reserves expected attack/defense power before spending discretionary power on tactical shield recharge.

## PDS and AMM endurance

Checkpoint 51 PDS accuracy and Reaction Capacity candidates are retained for this pass. AMM already costs 1 TP to ready at TL1 and TL2, the same readiness cost as Kinetic PDS; Energy PDS remains 2 TP. Primary combat profiles retain 25 TL1 and 30 TL2 AMM rounds. A separate endurance stress study examines 15, 20, 25, and 30 rounds over repeated demand so ammunition is not tuned merely to force depletion in one duel.

## Endurance components

Kinetic and Missile Magazine Expansions, AMM ammunition, and Combat Battery charges are evaluated on a repeated-engagement timescale. They are not required to equal armor, evasion, or PDS in one isolated fight. The resource-endurance stage is diagnostic evidence and does not automatically promote values.

## Runtime boundary

The Checkpoint 51 architecture-derived study remains frozen regression evidence. Checkpoint 52 adds `aux-itc03-stateful-power-and-pds-tuning` as a separate 975-variant matrix using the same legal loadout counts, plus `aux-end01-resource-endurance-stress` as a deterministic resource-timescale stage. Higher-TL runtime generation remains deferred.
