# CP114 Payload Characteristic-Space Report v1

## Status

Checkpoint 114 is an exploratory research-consumer checkpoint. The checked-in authoring pass executed 3,184 variants at 20 trials each (63,680 engagements). These results validate characteristic-space behavior and guide the native 2,000-trial-per-variant run; they are not calibration promotions.

## Missile findings from the bounded authoring pass

### Specialist anti-Shield warheads create pressure but do not independently solve the TL9 threshold

Against the TL9 Missile-defense package, the current Damage-5 GP control remains unable to produce Hull damage in the intact-defense lane. The anti-Shield families materially alter the Shield layer:

- Shield-only bonus profiles can absorb substantially more Shield Capacity than GP;
- recharge-suppression profiles can remove tens of points of Shield recharge over an engagement;
- Shield-Armor reduction changes the protection encountered by its own hit;
- adaptive profiles correctly switch after repeated Firm-track observations of Shield absorption with no observed Armor/Hull penetration.

However, the specialist profiles pay structural-performance costs by design. Static specialist-only attacks therefore often strip or suppress Shields without delivering enough follow-on structural packet strength to exploit the opening.

### Coordinated dual-launcher salvos are not a magic fix

CP114 tests specialist-first + GP same-cycle salvos for Shield-only bonus, Shield-Armor reduction, and recharge suppression, plus reversed-order controls. In the bounded TL9 full-defense lane none reliably produces Hull progress. Removing PDS creates a small opening for the strongest Shield-only bonus + GP mix, but it remains far weaker than a mature GP packet.

This is useful negative evidence: an anti-Shield role cannot be justified solely by "more Shield damage" if Shield recovery and later Armor layers still prevent structural progress. Specialist warheads may remain valuable support tools, but they do not remove the need for normal GP warhead maturation.

### GP maturation is the strongest late-TL signal

Fusion- and Antimatter-era GP candidates were included as characteristic envelopes, not selected values. The bounded results show a clear packet-threshold effect:

- Fusion-era profiles begin helping around TL5/TL7, but the less penetrative variants still fail against TL9 intact defense.
- Antimatter-era profiles cross the late layered-defense threshold much more naturally.
- In the TL9 Missile-defense/no-PDS dual-main lane, the three tested Antimatter GP envelopes produced roughly 63%, 81%, and 97% conditional attacker wins in the 20-trial authoring sample, versus 0% for current GP.
- Against full TL9 defense the same profiles still face strong PDS/defense pressure; the strongest candidate makes meaningful structural progress but is not an automatic universal win.

The conclusion is architectural, not numerical: the standard GP warhead likely needs real technological maturation as defenses advance. An anti-Shield specialist should complement that maturation rather than substitute for it.

### Shaped/APEN specialists remain contextual

The shaped candidates trade raw damage and/or SPEN for APEN. They are intentionally worse against active Shields and become more attractive when physical Armor is the dominant remaining layer. That is the correct qualitative direction for a selectable missile warhead, but larger native samples are required before choosing a profile.

## Kinetic findings from the bounded authoring pass

### Smart projectile looks like an automatic upgrade, not a firing mode

The TL4/5 +5-accuracy smart-projectile candidate modestly improves hit quality without changing the damage packet. Nothing in the current characteristic definition creates a reason to choose the older unguided round once compatibility is available. This supports the CP113 architecture: treat smart/maneuvering projectile improvements as automatic compatible ammunition maturation unless later implementation adds a real cost.

### Dense penetrators show two different design patterns

Dense candidates that retain SPEN while gaining APEN frequently outperform GP against shielded/armored targets, especially TL6/TL7. Some are close enough to strict improvements that they may belong in automatic progression rather than a selectable menu.

The profile that sacrifices SPEN more aggressively performs much worse into Shields while retaining an armor-oriented role. That is a healthier selectable tradeoff because the target-layer context matters.

The native study should therefore be read less as "which dense profile wins" and more as "which profile creates a defensible specialist niche instead of a universal upgrade."

### Saturation/submunition packets expose the per-packet protection rule

Saturation ammunition is genuinely distinct. Multiple smaller packets can be catastrophically ineffective against flat per-packet protection: the three-by-Damage-2 candidate can be completely nullified by Armor Protection 2 even with no Shield. Two-by-Damage-3 profiles can succeed against lighter/unshielded protection but remain poor against strong Shields/Armor.

That is potentially a real specialist identity for future small-target, lightly protected, or volume-fire contexts. It is not a general anti-armor replacement for GP.

## Doctrine and information result

The observer-safe adaptive doctrine works without hidden knowledge. It reacts to derived Firm-track evidence that repeated impacts are being absorbed by Shields without observed Armor/Hull penetration. Armor contact without damage is not falsely treated as successful penetration, and later observation of an impact reaching Armor/Hull without Shield effect can return doctrine to GP.

The bounded pass also shows that correct information does not guarantee a specialist is mechanically sufficient: the adaptive anti-Shield doctrines can recognize the problem and switch, yet still fail if the chosen specialist cannot create an exploitable structural opening. This cleanly separates information quality from payload quality.

## Recommendation pending native CP114

Do not promote any payload number from the authoring pass. The native 6.368-million-engagement run should determine whether the same signals hold with small Monte Carlo error.

If they do, the likely next design direction is:

1. preserve automatic Kinetic progression where the newer projectile is a strict/near-strict improvement;
2. retain only Kinetic selectable modes that have a visible layer/packet tradeoff;
3. give Missile GP warheads meaningful family maturation at major warhead-technology milestones;
4. keep anti-Shield warheads as specialist/support tools only if native results show a useful niche after accounting for GP maturation, PDS, and target defense;
5. avoid using specialist anti-Shield warheads as a disguised universal damage upgrade;
6. continue to defer internal-effect payloads until the internal critical/subsystem research consumer exists.

No CP109 numerical candidate, CP110 Reactor candidate, C#/Godot runtime value, or Concept rule is changed by CP114.
