# TL2 Weapon Penetration and Layered-Defense Integration Study v0.1

## Question

Measure APEN and SPEN as **common sensitivity axes** across Kinetic, Energy, and Missile while preserving the rule that each weapon family may ultimately evolve differently. The study also checks whether a contemporary penetration response restores sensible counterplay to deferred AP1 armor without invalidating Shield 3 or AI5.

## Penetration profiles

| Family | Control | +APEN | +SPEN | Combined upper sensitivity |
|---|---|---|---|---|
| Kinetic | SPEN1 / APEN0 | SPEN1 / APEN1 | SPEN2 / APEN0 | SPEN2 / APEN1 |
| Energy | SPEN1 / APEN1 | SPEN1 / APEN2 | SPEN2 / APEN1 | SPEN2 / APEN2 |
| Missile | SPEN1 / APEN2 | SPEN1 / APEN3 | SPEN2 / APEN2 | SPEN2 / APEN3 |

Damage, range, accuracy/guidance, power cost, ammunition, terminal missile rules, and other weapon properties are held constant. The combined profile is an interaction/upper sensitivity, not an assumed TL2 bundle.

## Defensive target matrix

Side B fixes locally validated **AI5** and crosses:

- Shield 2 / AP0 / AI5
- Shield 2 / AP1 / AI5
- Shield 3 / AP0 / AI5
- Shield 3 / AP1 / AI5

Side A holds Shield 3 / AP0 / AI5. Both sides use 6 Operational TP for this contemporary penetration study so old-reactor power starvation is not the tested variable.

## Context matrix

- 3 attacker weapon families
- 4 penetration profiles
- 4 target defense packages
- 2 information-control environments: clean Firm reference; DR1 + reactive ECCM1 versus ECM2
- 3 geometry/order contexts: fixed Range 3; dynamic Side A first; dynamic Side B first

Total: **288 substantive variants**, using common random streams within each comparison group.

## Interpretation boundaries

The study does not require any weapon family to receive a penetration increase. A desirable conclusion can be asymmetric: Kinetic may value APEN, another family may value SPEN or neither, and later progression may use an entirely different family-specific property.

APEN should be judged particularly against AP0 versus AP1. SPEN should be judged particularly against Shield 2 versus Shield 3. Combined profiles reveal interaction terms. Outcomes are review evidence, not automatic production gates.

The accepted AI5 armor, Shield 3, Reactor 6, and information-control working candidates remain local working candidates subject to future mixed-TL/whole-ladder validation.
