# Combat Scaling Framework and TL2 Candidate Derivation v0.2

## Purpose

This framework screens player-technology candidates before and alongside Monte Carlo balance testing. It does not assign a universal combat score and it does not replace hand design. It exposes the consequences of interacting weapon, defense, power, movement, and control vectors so candidate values are not chosen blindly.

> Equations establish consistency and reveal consequences; hand design establishes identity and fun; simulation decides whether the combination actually works.

## Technology-band rhythm

Player technology is piecewise rather than a smooth TL1-TL9 curve.

- **TL1-TL3: low technology.** Foundation, refinement, culmination.
- **TL4-TL6: medium technology.** Breakthrough, refinement, culmination.
- **TL7-TL9: high technology.** Transformation, refinement, apex.

Within a band, a comparable complete one-TL advancement uses approximately **60/40** higher-TL victory probability as a nominal review target. The working review band is **57-64 percent**. This is not a hard gate and does not apply to every subsystem or matchup.

The TL3-to-TL4 and TL6-to-TL7 band transitions use approximately **75/25** as the first qualitative-breakpoint review target, with **80/20** retained only as an upper stress case. These breakpoint values guide later design; Checkpoint 42 does not assign TL3-TL9 production data.

## Exact packet relationship

The analyzer calls the authoritative `LayeredDamageResolver`. The descriptive relationships are:

```
ShieldBypass = min(DAM, SPEN)
ShieldFacingDamage = DAM - ShieldBypass
ShieldArmorPrevented = min(ShieldFacingDamage, SA)
PostArmorShieldDamage = ShieldFacingDamage - ShieldArmorPrevented
ShieldAbsorption = min(CurrentShield, PostArmorShieldDamage)
DamageReachingArmor = ShieldBypass + (PostArmorShieldDamage - ShieldAbsorption)

EffectiveAP = max(0, CurrentAP - APEN)
ArmorDamagePrevented = min(DamageReachingArmor, EffectiveAP)
NetArmorLayerDamage = DamageReachingArmor - ArmorDamagePrevented
```

Net damage is applied to Armor Integrity, current Armor Protection, and Hull in the accepted order. Penetration adds no damage and is not consumed between layers.

## Accuracy, missiles, and renewable defense

Ordinary direct fire uses:

```
RawHitChance = 50 + WeaponAccuracy + TargetingBonus - 5 * Range
FinalHitChance = clamp(RawHitChance, MinimumChance, MaximumChance)
```

The compact missile screen uses guidance, flight delay, and one eligible PDS survival probability. The executable Monte Carlo lane remains authoritative for full Missile Flight behavior.

The analyzer solves the finite shield/armor/Hull state graph with turn-start recharge. A useful diagnostic is:

```
ExpectedShieldPressurePerTurn =
    HitProbability * ShieldDamagePerPacket * AttackCadence
    - BaseShieldRecharge
```

Near-zero pressure warns of long combat; negative pressure may still allow SPEN bypass progress.

## Evidence calibration

Checkpoint 42 expands calibration from twelve TL1 mirrors to the complete accepted **36-row ordered cross-family Range 2-5 AP0 grid** from Checkpoint 40.

- Mirror evidence: `docs/validation/evidence/checkpoint-40-minimal-tactics/tl1-mirror-calibration.csv`
- Ordered evidence: `docs/validation/evidence/checkpoint-40-minimal-tactics/tl1-cross-family-calibration.csv`

Family duration factors fit the legal mirrors. Ordered cross-family odds factors fit the accepted conditional win evidence wherever both sides can attack. Envelope cases in which one side cannot legally fire remain explicit rather than being forced into the odds calibration.

## Weapon-identity guardrails

Every pair of standard weapon families must retain at least two meaningful operational differences. The first automated review uses three core attributes:

- raw Damage;
- accuracy or terminal guidance;
- maximum range.

It also reports support differences in SPEN, APEN, Tactical Power, and ammunition model. The recommended candidate may share no more than two core attributes with another family and must retain at least two meaningful differences per family pair. Controls may violate the rule only when the violation is intentional and reported.

These checks prevent optimization toward a percentage target from flattening weapon identity. Same-TL families do not need universal 50/50 cross-family results; each must remain a valid player choice with distinct tactical conditions.

## TL2 candidate set

1. **Identity-Preserving Refinement** - recommended first Monte Carlo candidate, centered near the 60/40 within-band target while preserving TL1 family roles.
2. **Aggressive Balanced Control** - retains the former roughly 66.7-percent package as an upper control and deliberately exposes kinetic/energy convergence.
3. **Specialization-Forward Control** - tests earlier penetration, longer beam reach, and stronger missile guidance as a progression-boundary control.

All values remain candidate-only. TL2 Armor Protection remains 0. Ship Move is 2 and missile Move is 3 under the accepted movement laws. Names are provisional and may change if their tested vector conflicts with the low-tech progression rhythm or the TL3 culmination.

## Monte Carlo promotion lane

Checkpoint 42 adds 324 minimal-tactics variants:

- three candidate profiles;
- all nine ordered weapon-family pairings;
- Ranges 2-5;
- same-candidate TL2 versus TL2;
- candidate TL2 versus TL1;
- reciprocal TL1 versus candidate TL2.

The lane holds position and fires whenever legal. It excludes movement tactics, overload, withdrawal, EvM, Damage Control, and Protected Compartmentation while retaining base Shield recharge, PDS, ammunition, power, missile flight, internal damage, component conditions, destruction, and mission kills.

The 57-64 percent complete-package band is reported, not enforced as a mechanical pass/fail verdict. Weapon identity, pacing, cross-family usefulness, and the absence of universal dominance matter more than an exact aggregate percentage.

## Reference-use guardrail

The preserved reference library informs technology rhythms, qualitative milestones, subsystem relationships, efficiency tradeoffs, and naming patterns. It does not supply copied names, tables, numerical ladders, or proprietary resolution mechanics.
