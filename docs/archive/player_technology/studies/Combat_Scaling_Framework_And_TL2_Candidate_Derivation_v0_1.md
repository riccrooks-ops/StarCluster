# Combat Scaling Framework and TL2 Candidate Derivation v0.1

## Purpose

This framework screens player-technology candidates before Monte Carlo balance testing. It does not assign a single universal combat value and it does not replace hand design. It exposes the consequences of interacting weapon, defense, power, movement, and control vectors so candidate values are not chosen blindly.

The governing principle is:

> Equations establish consistency and reveal consequences; hand design establishes identity and fun; simulation decides whether the combination actually works.

## Technology-band rhythm

Player technology is piecewise rather than one smooth TL1-TL9 curve.

- **TL1-TL3: low technology.** TL1 establishes the first practical baseline, TL2 refines it, and TL3 is the mature culmination of recognizable conventional engineering.
- **TL4-TL6: medium technology.** TL4 introduces a qualitative exotic-engineering breakpoint, TL5 integrates it, and TL6 matures it.
- **TL7-TL9: high technology.** TL7 begins transformative science-fantasy capability, TL8 makes it routine, and TL9 is the player pinnacle.

The numeric model therefore allows continuous growth, discrete protection/penetration milestones, efficiency gains, reliability gains, and capability unlocks to occur at different TLs. Names and mechanical promises constrain the candidate vector. Names may be revised if the tested mechanics no longer fit the progression rhythm.

## Exact packet relationship

Every attack packet has raw Damage (`DAM`), Shield Penetration (`SPEN`), and Armor Penetration (`APEN`). The analyzer calls the authoritative `LayeredDamageResolver`; the equations below describe the same transition.

### Shield layer

```
ShieldBypass = min(DAM, SPEN)
ShieldFacingDamage = DAM - ShieldBypass
ShieldArmorPrevented = min(ShieldFacingDamage, SA)
PostArmorShieldDamage = ShieldFacingDamage - ShieldArmorPrevented
ShieldAbsorption = min(CurrentShield, PostArmorShieldDamage)
DamageReachingArmor = ShieldBypass + (PostArmorShieldDamage - ShieldAbsorption)
```

`SA` is Shield Armor. The implementation schema uses `shieldArmor`. Standard TL1 and the first TL2 candidates keep SA at zero.

### Armor layer

```
EffectiveAP = max(0, CurrentAP - APEN)
ArmorDamagePrevented = min(DamageReachingArmor, EffectiveAP)
NetArmorLayerDamage = DamageReachingArmor - ArmorDamagePrevented
```

Net damage is applied in order to Armor Integrity, current Armor Protection, and then Hull. Penetration does not add damage and is not consumed between layers.

## Accuracy and terminal probability

Ordinary direct fire uses the current roll-high relationship:

```
RawHitChance = 50 + WeaponAccuracy + TargetingBonus - 5 * Range
FinalHitChance = clamp(RawHitChance, MinimumChance, MaximumChance)
```

The first analyzer assumes a current Firm solution and excludes EvM and other tactics. Missiles use terminal Guidance Chance multiplied by the probability of surviving one eligible PDS attempt:

```
TerminalPacketProbability = GuidanceChance * (1 - EffectivePDSChance)
```

This is a screening approximation, not a substitute for the full Missile Flight and PDS runtime.

## Renewable shield pressure

The useful screening relationship is:

```
ExpectedShieldPressurePerTurn =
    HitProbability * ShieldDamagePerPacket * AttackCadence
    - BaseShieldRecharge
```

A positive result means the attacker can normally collapse the shield over time. A near-zero result warns of long combat. A negative result may still allow progress through SPEN bypass, but the shield itself may remain intact.

The executable analyzer does not reduce the complete fight to this scalar. It solves the finite shield/armor/Hull state graph with turn-start recharge and hit/miss transitions, then reports the expected absorption time.

## Expected absorption time

For each reachable non-destroyed defense state `s`, the analyzer constructs a linear equation:

```
E(s) = 1 + (1 - pHit) * E(Recharge(s)) + pHit * E(Hit(Recharge(s)))
```

Destroyed states have `E = 0`. The finite linear system is solved directly. If the attack can never change the recharged state, expected time is infinite and the matchup is flagged as unable to make progress.

Missile flight delay is added before applying the family calibration factor:

```
FlightDelay = max(0, ceil(Range / MissileMove) - 1)
```

## Evidence calibration

The exact state model intentionally omits internal component damage, committed simultaneous volleys, and other integrated-combat effects. A single family-specific factor is therefore fitted to the accepted Checkpoint 40 AP0 mirror results at Ranges 2-5. The factor corrects expected duration only; it does not change packet resolution or candidate inputs.

The calibration evidence is preserved at:

- `docs/validation/evidence/checkpoint-40-minimal-tactics/tl1-mirror-calibration.csv`

The checkpoint gate requires every legal TL1 mirror prediction to remain within 12 percent after calibration. Range 5 kinetic remains the deliberate no-legal-fire control.

## Pairwise odds screen

For simultaneous comparable ships, the first screening estimate treats each side's expected kill time as an inverse hazard rate:

```
P(Side A wins) = Side B Expected Kill Time /
                 (Side A Expected Kill Time + Side B Expected Kill Time)
```

This naturally returns 50/50 for identical profiles. It is not used as a final balance verdict. The provisional complete-package target for TL2 versus TL1 is 66.7 percent, with an exploratory review band of 60-72 percent.

The target applies to a complete comparable ship package, not to every isolated subsystem upgrade or every cross-family/range matchup.

## Power affordability

```
PowerMargin = ReactorOutput - StandardCombatPowerCommitment
```

The first candidates require at least one uncommitted Tactical Power point after their standard weapon/PDS posture. Higher reactor output is not considered successful if it simply removes all power choices.

## Protection and penetration breakpoints

AP, SA, APEN, and SPEN are discrete breakpoint values. The analyzer writes a complete protection table from zero through `DAM + 1` for every weapon profile. These values should normally advance at deliberate milestones rather than every TL.

Capacity values such as Hull, Armor Integrity, Shield capacity, ammunition, fuel, and Reactor output may progress more gradually, but do not have to change at every TL.

## TL2 named-component constraints

The current names and mechanical promises provide the starting design constraints:

- **Reinforced Spaceframe:** improved Hull and load tolerance.
- **Ceramic Composite Plating:** improved protection-to-mass and resistance; the first candidates improve Armor Integrity but retain AP0.
- **Magnetoplasma Screen:** improved capacity and broader field control; the first candidates add Shield capacity while retaining Recharge 1 and SA0.
- **Fusion Reactor:** higher Tactical Power and improved efficiency.
- **Fusion Torch Drive:** Ship Move 2 under `Move = Drive TL`.
- **Multispectral Sensor Suite:** better discrimination and passive track formation; not fully represented in the minimal-tactics screen.
- **Photonic Tactical Computer:** improved track fusion and targeting efficiency.
- **Coil Cannon:** improved electromagnetic acceleration, accuracy, velocity, or armor interaction.
- **Pulsed Laser Cannon:** higher peak output and better combat effect at a heat/power tradeoff.
- **Fusion Missile Flight:** improved warhead output and flight performance; Missile Move 3 under `Move = Missile Drive TL + 1`.

These names remain intentional drafts. A surviving mechanical vector may trigger a rename if it contradicts the stated promise or intrudes on the TL3 culmination.

## Candidate set

Three candidates are retained:

1. **Conservative Refinement** - capacity and precision growth with no standard weapon-packet increase.
2. **Balanced Derived Candidate** - the first recommended Monte Carlo candidate; analytically designed to approach the 66.7 percent complete-package target while preserving AP0 armor.
3. **Specialization-Forward Control** - tests earlier APEN, longer beam reach, and stronger missile guidance to reveal whether capability growth intrudes on TL3 identity.

Candidate inputs are authoritative only for this study:

- `src/StarCluster.ScenarioRunner/Scenarios/TL2Scaling/tl2-candidate-derivation-v0_1.json`
- `docs/design/player_technology/tl2_candidate_vector_matrix_v0_1.csv`

No candidate is promoted to the player baseline until the subsequent isolated and complete-package Monte Carlo studies pass review.

## Reference-use guardrail

The preserved reference library informs progression patterns, subsystem relationships, and tradeoffs. It does not supply copied names, tables, numerical ladders, or proprietary resolution mechanics. Existing reference-insight IDs associated with the TL2 components remain the traceable influence record.
