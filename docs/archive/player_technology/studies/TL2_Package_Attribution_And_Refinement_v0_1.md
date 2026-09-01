# TL2 Package Attribution and Identity-Preserving Refinement v0.1

## Purpose

Checkpoint 43 confirmed that the first integrated identity-preserving TL2 package is much stronger in the combat engine than its analytical proxy predicted: approximately 73.93 percent conditional win share against TL1 rather than the intended 57-64 percent review band. This study attributes that difference before changing any accepted mechanic or promoting any TL2 value.

## Locked interpretation

- The accepted TL1 baseline remains unchanged.
- The Checkpoint 42 identity-preserving package remains the source vector, not a promoted production package.
- The aggressive balanced and specialization-forward packages remain retained external controls in the original 324-variant study.
- No profile in this checkpoint is promoted automatically.
- A profile label or TL number must not create a hidden advantage; the null-vector control is numerically identical to TL1.
- Fixed Range 5 remains a reach-stress lane, not a standalone balance verdict.
- Final selection requires convergent fixed-range, movement-aware, pacing, unresolved-outcome, and same-TL identity evidence.

## Seven attribution groups

| Group | Identity-package changes isolated |
|---|---|
| Structure | Hull 12 to 13; Armor Integrity 4 to 5 |
| Shields | Shield Capacity 2 to 3 |
| Fire Control | Targeting bonus 10 to 15; effective PDS chance 45 to 48 |
| Propulsion | Ship Move 1 to 2; missile Move 2 to 3 |
| Direct-Fire Weapons | Kinetic SPEN 1 to 0 and accuracy 20 to 25; Energy accuracy 25 to 30 |
| Missile Guidance | Guidance 55 to 60; maximum travel/range 6 to 7 |
| Power and Logistics | Reactor output 5 to 6; standard combat commitment 2 to 3 |

Each group receives two complementary probes:

1. **Additive probe:** TL1 plus only that group.
2. **Leave-one-out probe:** the complete identity package with only that group reverted to TL1.

The additive and leave-one-out effects are both required because a component group can be modest alone but strong in combination. Their difference is reported as interaction asymmetry rather than hidden inside one aggregate score.

## Registered profiles

The catalog contains 19 diagnostic profiles:

- 1 exact TL1 null-vector control.
- 7 additive probes.
- 7 leave-one-out probes.
- 1 retained identity-source control.
- 3 preregistered moderated refinement probes.

The three refinement probes are:

- **Moderated Control Refinement:** complete identity package with targeting +2 rather than +5 and effective PDS +1 rather than +3.
- **Control and Shield-Tempered Refinement:** moderated control plus TL1 shield capacity.
- **Control and Structure-Tempered Refinement:** moderated control plus TL1 hull and Armor Integrity.

These are deliberately narrow. They test whether the integrated overmatch is primarily caused by broad fire-control improvement, by its interaction with defense, or by the full package. They do not redefine weapon identity.

## Monte Carlo coverage

The integrated study contains exactly 1,764 variants:

- **1,368 fixed-range cross-TL variants:** all 19 profiles, all nine ordered weapon-family pairings, Ranges 2-5, and both TL2-vs-TL1 and reciprocal TL1-vs-TL2 orientation.
- **252 movement-aware cross-TL variants:** seven selected profiles, all nine ordered family pairings, Scripted Pursuit and Preferred Range, and both orientations.
- **144 same-TL identity variants:** the identity source and three refinement probes, all nine ordered family pairings, and Ranges 2-5.

All lanes use the minimal-tactics contract: no Damage Control, no Evasive Maneuvers, no Protected Compartmentation, base shield recharge on, PDS on, and disengagement adaptation off. Dynamic movement still resolves normally under the existing movement policies.

## Output interpretation

`group-effects.csv` reports:

- additive fixed-range effect relative to the null control;
- leave-one-out fixed-range effect relative to the complete identity package;
- the mean of those two marginal estimates;
- interaction asymmetry;
- movement-aware propulsion effects where registered.

`refinement-review.csv` reports fixed and movement-aware win shares, review-band status, same-TL strongest edge, pacing, and unresolved outcomes. The profile nearest 60 percent may be highlighted in `summary.json`, but that is a convenience ranking only. It is not a promotion gate.

## Decision rule after results

Prefer the smallest attributable change that:

1. moves the integrated TL2/TL1 result toward 57-64 percent;
2. preserves kinetic, energy, and missile identity;
3. avoids a compulsory weapon family or universal same-TL dominance;
4. remains healthy under movement-aware policies;
5. preserves acceptable pacing and resolution rates; and
6. leaves enough progression space for TL3.

If no preregistered probe satisfies those conditions, use the attribution ranking to design one further surgical candidate rather than weakening every TL2 subsystem together.

## Integrated-study schema capacity

Schema v0.4 preserves the accepted integrated tactical-combat variant contract while raising the documented study-size ceiling from 400 to 2,500 variants. This is a packaging/schema-capacity change only; it does not alter simulation mechanics.
