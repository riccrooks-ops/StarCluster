# Star Cluster Combat System Reference

**Status:** current working combat design after CP164.

## Phase order
Movement → Electronic Warfare / Track Update → Direct Fire → Missile / Interception → Damage → Damage Control. Turn refresh/pre-Movement power planning are explicit timing windows.

## Tracks/direct fire
Firm 0 pp. Approximate -25 pp when permitted. Extended range -10 pp. Approximate+Extended stack. Beyond Maximum Range illegal. Missiles do not use the direct-fire Extended-range penalty.

## Weapons
Kinetic is ammunition-limited medium-TP APEN direct fire. Energy is higher-TP SPEN direct fire with explicit Low/Standard/Overload modes. Missile Flight is an abstract salvo. Swarmer (TL2+) creates two PDS-visible sub-flights sharing Reaction Capacity.

## PDS
Kinetic, Energy and AMM are distinct families with TL-specific chance/Reaction Capacity/TP. Kinetic/AMM consume ammunition; Energy is power-intensive and ammunition-free.

## DEF/RES
Current working mode is `def-res-v1`: Shield DEF whole-packet deflection after SPEN, 45 pp cap; Armor RES fractional mitigation after APEN, 95 pp cap; base 20-36 pp across TL1-9. Armor RES ends after Armor collapse.

## Tactical Power
Main Reactor: 6 Space, Operational TP 5/6/7/8/9/10/11/12/13. APU: 2 Space, +1 TP TL1-4, +2 TL5-9, additive, no arbitrary cap. Extra TP is optional capacity and must not force harmful activations.

## Damage Control
Normal attempts use 1 TP + one Repair Kit and current TL chances. Repair Drone adds one distinct-target action, not a reroll, and carries one additional default kit load.

## Whole-system next
Integrate Reactor/APU damage states, Repair Drone component repair, powered AUX, legal multi-Main/multi-Reactor, allocator monotonicity, and cross-system interactions before production promotion.
