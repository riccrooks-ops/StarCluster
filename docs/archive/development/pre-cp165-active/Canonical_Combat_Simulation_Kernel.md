# Canonical Combat Simulation Kernel

## Purpose and authority

This document defines the durable **research implementation contract** for the Star Cluster tactical-combat simulator beginning with Checkpoint 132. It is not a second gameplay authority. The active Game Concept defines the game rules; the canonical kernel is the single executable research expression of those rules.

When the Concept changes, update the canonical kernel, its deterministic fixtures, and the production C# mechanics together before generating new balance evidence. A study must not carry a private copy of ordinary combat mechanics merely because it needs a different population, candidate value, or experimental control.

## Architecture boundary

New combat research is organized into four layers:

1. **Technology/component data** - component characteristics and legal construction inputs.
2. **Canonical combat kernel** - map geometry, encounter start, phase order, power/recharge timing, sensing/EW, movement, attack commitment, missile flight/interception, layered damage, destruction, and explicit phase hooks.
3. **Doctrine/AI** - legal decisions made from player-observable information.
4. **Study/scenario harness** - build populations, pairings, candidate overrides, trial counts, seeds, metrics, and explicit experimental overrides.

A study may change layer 4 and may select a declared doctrine from layer 3. It must not fork layer 2. If a study needs fixed range, forced track, disabled movement, infinite ammunition, or another artificial control, that condition must be an explicit named override and must appear in the evidence.

## Canonical files

- `tools/simulation/starcluster_research/canonical_combat.py` - canonical finite-System-Map encounter orchestration.
- `tools/simulation/starcluster_research/canonical_mechanics.py` - pure deterministic mechanics that require parity with production C#; the current v0.4 contract includes layered damage, universal direct-fire track/range modifiers, Energy-main output relationships, finite-reserve tactical Armor regeneration, and Hull-only Damage Control execution for the same-TL research doctrine.
- `tools/simulation/starcluster_research/full_map_ecology.py` - compatibility facade for historical imports; it re-exports the canonical combat implementation and owns no independent combat rules.
- `docs/design/testing/canonical_combat_kernel_fixtures_v0_1.json` - shared deterministic C#/Python fixture contract.
- `src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs` - production layered-damage implementation paired to the Python resolver.
- `src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs` - production universal Firm/Approximate and Standard/Maximum Range contract.
- `src/StarCluster.Core/Combat/DirectFire/EnergyMainOutputRules.cs` - production Low/Standard/Overload Energy-main relationship.
- `src/StarCluster.Core/Combat/Damage/ArmorTacticalRegenerationService.cs` - production tactical Armor-regeneration relationship for profiles that explicitly support it.
- `src/StarCluster.Core/Combat/TacticalTurnState.cs` and `TacticalTurnPhase.cs` - production visible phase cursor paired to the canonical phase fixture.

Older checkpoint-specific axial or specialized consumers remain useful for reproducing historical evidence, but they are not a license to define new combat semantics. Where those consumers call common damage helpers, they inherit the canonical damage resolver. New balance/calibration studies must route normal combat through the canonical finite-map kernel unless a successor kernel is explicitly promoted.

Legacy telemetry field names such as `ShieldArmorPrevented`, `ArmorDamagePrevented`, and `ArmorProtectionDamage` remain in some historical C#/Python result structures for compatibility. Beginning with CP132 they are compatibility aliases, not mechanics definitions: the first two measure penetration rating resisted by hardening, and Armor Protection damage is zero under `penetration-hardening-v1`. New telemetry and new analysis should prefer explicit penetration/hardening names.

## Standard finite-System-Map encounter

The standing research encounter uses the ordinary radius-5 System Map:

- radius: 5 hexes;
- cells: 91;
- Side A standard start: `(-5, 0)`;
- Side B standard start: `(5, 0)`;
- initial separation: 10 hexes.

Before legitimate contact, each ship uses observer-safe search movement. On its Movement activation it moves **exactly one hex toward map center** if legal and if not already at center, regardless of a higher installed STL Move. Search does not inspect or route toward the hidden opponent coordinate. Once contact exists, normal capability/observation-driven tactical doctrine controls movement.

Starting geometry is a standard calibration condition, not a universal game rule. A geometry study may override it explicitly; the override must be reported.

## Turn and phase contract

The visible combat phase order is:

1. Movement
2. Electronic Warfare
3. Direct Fire
4. Missile / Interception
5. Damage
6. Damage Control

The research kernel also exposes two internal timing windows so power and recharge cannot drift between studies:

- **Turn Refresh** - start-of-turn recharge/recovery and reset work that the Concept assigns before Movement.
- **Pre-Movement Tactical Power** - the bounded pre-Movement power-planning opportunity.

Electronic Warfare occurs after Movement and before either attack phase. Direct Fire commits attacks without immediately revealing damage. Missile launch, flight, terminal guidance, and interception occur in Missile / Interception. Successful attack packages are resolved in the Damage phase. Damage Control is an explicit central phase. Kernel v0.4 retains the CP135 diagnostic doctrine as Hull-only repair: at most one attempt per surviving damaged ship per turn, costing 1 TP and 1 prepared Repair Kit whether successful or not; success is queued and becomes active at the following Turn Refresh. Component repair remains outside this study doctrine. Tactical Armor regeneration then uses any remaining legal TP and remains a separate material capability. Kernel v0.4 adds a finite per-engagement Combat Regeneration Reserve: mainline TL6/TL7/TL8/TL9 can restore at most 3/4/5/6 total AI during combat, while retaining 1 AI/TP and per-turn TP caps 1/1/1/2. Reserve is consumed only by AI actually restored. TL6 A_b1 Crystalline has no regeneration or reserve. Out-of-combat self-healing remains a separate deferred recovery process.

### Commitment and damage reveal

Direct-fire attacks for both ships are committed before damage is applied. Complete committed direct-fire volleys resolve in movement/activation order. A ship destroyed during Damage still receives the benefit of any attack package it already committed. Later committed packages against a ship already reduced to zero Hull are recorded as overkill rather than canceling previously committed opposing fire.

Missile terminal attacks that successfully survive guidance/interception are likewise committed before Damage. Direct-fire packages resolve before missile terminal packages because Direct Fire precedes Missile / Interception in the visible phase order.

## Canonical layered-defense model: `penetration-hardening-v1`

CP132 establishes one simple rule family for Shield and Armor penetration.

### Terms

- **DAM** - fixed damage carried by one attack packet.
- **SC (Shield Capacity)** - Shield durability/hit points.
- **SA (Shield Armor)** - Shield penetration hardening; it reduces SPEN while SC is positive.
- **SPEN (Shield Penetration)** - maximum packet damage eligible to bypass the active Shield after SA hardening.
- **AI (Armor Integrity)** - Armor durability/hit points.
- **AP (Armor Protection)** - Armor penetration hardening; it reduces APEN while AI is positive.
- **APEN (Armor Penetration)** - maximum damage reaching an active Armor layer eligible to bypass that layer after AP hardening.

SA and AP are **not generic damage reduction** and are **not hit-point pools**. Penetration never creates damage.

### Shield stage

If `SC > 0`:

`Effective SPEN = max(0, SPEN - SA)`

`Shield bypass = min(DAM, Effective SPEN)`

The remainder of DAM attacks SC. SC absorbs up to its current capacity; any capacity overflow joins the bypassed damage and proceeds to Armor.

If `SC = 0`, the Shield layer is collapsed/absent, SA is inactive, and all packet damage proceeds to Armor. SA itself is not damaged or consumed. Restoring SC above zero makes the installed SA effective again if its source is otherwise functional/powered.

### Armor stage

For each active Armor layer reached by the packet, if `AI > 0`:

`Effective APEN = max(0, APEN - AP)`

`Armor bypass = min(damage reaching that layer, Effective APEN)`

The remainder attacks AI. AI absorbs up to its current integrity; any integrity overflow joins bypassed damage and proceeds to the next Armor layer or Hull.

If `AI = 0`, that Armor layer is defeated, AP is inactive, and damage passes onward unchanged. AP is never stripped into a secondary durability pool. Restoring AI above zero reactivates the installed AP if the Armor source remains otherwise valid.

For multiple Armor layers, APEN retains its original packet value at each active layer; each layer applies its own AP hardening. Penetration through an outer layer proceeds to the next layer rather than creating extra damage.

### Example

A `DAM 8 / SPEN 3 / APEN 2` packet hits `SC 4 / SA 1`, then `AI 5 / AP 1`:

- Effective SPEN = 2; 2 DAM bypasses Shield.
- 6 DAM faces SC; 4 removes SC and 2 overflows.
- 4 DAM reaches Armor (2 bypass + 2 overflow).
- Effective APEN = 1; 1 DAM bypasses Armor.
- 3 DAM removes AI, leaving AI 2.
- Hull takes 1 DAM.

Final state: SC 0, AI 2, AP unchanged, Hull -1.

## Canonical direct-fire track/range modifiers

Kernel v0.2 and later retain two KISS-friendly direct-fire modifiers to universal combat rules rather than component-owned traits.

- **Firm track:** no track-quality modifier.
- **Approximate track:** -25 percentage points. All otherwise-legal ship-target direct-fire weapons may attempt the attack; a Tactical Computer is not required to grant permission.
- **At or inside Standard Range:** no range modifier.
- **Beyond Standard Range but at or inside Maximum Range:** -10 percentage points.
- **Beyond Maximum Range:** the attack is illegal.
- Approximate plus extended-range fire stacks to **-35 percentage points**.

The Tactical Computer continues to provide its ordinary targeting assistance and other explicit capabilities, but historical Approximate-fire penalty fields are provenance/compatibility data and do not own the current universal -25 rule. Main-weapon Missile interception remains Firm-only. Missile terminal attacks remain governed by their own guidance/terminal architecture and do not inherit the direct-fire extended-range modifier.

## Universal Energy-main output relationship

Every ordinary Energy Main Weapon derives three bounded output modes from its listed Standard TP and Standard Damage:

- **Low:** `ceil(Standard TP / 2)` and `ceil(Standard DAM / 2)`, no Strain.
- **Standard:** listed Standard TP and DAM, no Strain.
- **Overload:** `ceil(1.5 x Standard TP)` and `ceil(1.5 x Standard DAM)`, plus 1 weapon Strain.

Overload remains subject to the normal Strain-limit/Forced-Overload system. The current same-TL diagnostic doctrine may use safe overloads first and fall back to Standard/Low as power and Strain dictate; that doctrine is a layer-3 choice, not a different mechanic.

## Shield and Armor recovery identity

The shared penetration model does not make Shields and Armor identical.

- Shield recovery is normally **fast, active, and power-driven**. Base recharge and optional Tactical Power recharge occur at the accepted refresh timing. A collapsed Shield has no active SA until SC returns.
- Armor recovery is **physical repair/regrowth**. Low-technology Armor normally does not regenerate in combat. A profile with tactical self-healing may spend Tactical Power during Damage Control to restore AI; the current candidate relationship is 1 AI per TP, capped by the Armor profile and pristine AI. AP remains a hardening characteristic, not repairable hit points. A passive branch such as TL6 Crystalline Armor can therefore trade stronger AP/AI for a zero regeneration cap without becoming a second Shield.

Future CREW damage, component criticals, broader Damage Control integration, and related mechanics must be added to the canonical phase/state machinery rather than implemented separately inside each research study.

## Missile and direct-fire boundaries

The canonical kernel keeps direct-fire and Missile mechanics distinct:

- direct-fire attacks are committed in Direct Fire and require a Firm or Approximate track plus ordinary legal Standard/Maximum-range, power, ammunition, line-of-sight, and target conditions;
- Missile launch belongs to Missile / Interception;
- Missile Flights occupy real finite-map coordinates, move against the target's post-Movement location, consume their travel envelope, and may reroute as the target moves;
- terminal Flights use the accepted guidance/acquisition and PDS windows before producing a committed damage package;
- a Missile's flight envelope is not converted into a direct-fire range accuracy penalty.

Any future Approximate-track Missile launch, seeker acquisition, radiation/CREW warhead, or other Missile branch must enter through this shared flight/terminal architecture. Swarmer remains a bounded multi-packet terminal branch inside that same architecture rather than a separate movement simulator.

## Standard calibration build convention

Shield and Armor are not universal legal-construction requirements. However, ordinary **same-TL reference/calibration ships include both a contemporary Shield and contemporary primary Armor** so every main weapon family exercises the complete layered-defense system. The CP134 baseline study keeps the build population intentionally narrow: one Main, one contemporary Reactor/Computer/Sensor, mandatory Shield+Armor, no primary-lane ECM/ECCM, and no tactical auxiliaries other than the paired PDS control. TL6 explicitly crosses the mainline regenerative Armor with the A_b1 Crystalline Armor seed in both side positions. Missile/Swarmer-bearing contexts run paired PDS-off and contemporary AMM-PDS-on lanes; direct-fire-only contexts do not duplicate the PDS lane. Shield-only, Armor-only, no-defense, EW-heavy, and broader legal-build populations remain later explicit diagnostics rather than primary baseline calibration.

## Deterministic verification before Monte Carlo

A new or changed mechanic is not ready for substantive calibration until deterministic tests pass. At minimum CP132 requires:

- shared C#/Python damage fixtures;
- `DAM 8 / SPEN 1 / APEN 1` chain behavior in an unhardened layered defense;
- SA/AP cancel penetration rather than ordinary DAM;
- hardening becomes inactive at SC/AI zero;
- AP is not destructible hit points;
- penetration is bounded by actual damage;
- standard radius-5 starts and one-hex pre-contact search;
- Firm/Approximate direct-fire modifier behavior (0 / -25 pp);
- Standard/extended-range modifier behavior (0 / -10 pp) and -35 stacked behavior;
- Energy Low/Standard/Overload rounding and Overload Strain;
- Shield full-recharge arithmetic for candidate profiles;
- tactical Armor regeneration and passive zero-cap branch behavior;
- visible phase-order parity;
- simultaneous direct-fire commitment behavior;
- finite-map movement/Missile physical symmetry; and
- the standing research parity corpus.

Substantive Monte Carlo is evidence about the current mechanics and current data, not a mechanics validator. When the kernel changes materially, old balance results remain historical evidence under their recorded kernel and must not be numerically mixed with post-change results as if the rules were identical.

## Versioning and change discipline

The kernel version begins at `0.1` for CP132. **Kernel v0.2 in CP134** adds universal Approximate-track ship fire, Standard/Maximum direct-fire range behavior, universal Energy-main output relationships, and tactical Armor-regeneration integration. **Kernel v0.3 in CP135** adds executable Hull-only Damage Control to the same-TL research path and updates Shield candidate data so a fully collapsed contemporary Shield cannot normally reset to full in one recharge window. **Kernel v0.4 in CP137** caps tactical Armor self-healing with a finite AI-denominated combat reserve, separating in-combat endurance from deferred out-of-combat recovery. **Kernel v0.5 in CP144** closes the EngageAdaptive Missile movement-policy divergence so the Python research path preserves an established legal firing solution rather than reopening toward a theoretical preferred range. **Kernel v0.6 in CP146** adds an explicitly versioned information-limited contextual combat-resource doctrine, contextual system activation, and the K/E Held Main anti-missile layer to the whole-combat research path while retaining `cp145_legacy` for exact historical reproduction. These changes can alter legal state transitions and combat outcomes and therefore require a version increment. Pure reporting additions may extend telemetry without changing the version when semantics remain identical, but renamed/reinterpreted metrics must be documented.

CP133 supplies the first accepted post-redesign candidate numerical/component baseline. CP134 applies it through kernel v0.2 and establishes the first same-TL diagnostic evidence. CP135 changes Shield recharge and prepared Damage Control kit counts, activates Hull-only Damage Control in kernel v0.3, and becomes the accepted reduced-recharge research baseline. CP136 changes only candidate Armor data while retaining kernel v0.3. CP137 holds every CP136 numerical value and advances to kernel v0.4 solely for finite in-combat Armor regeneration reserves. CP144 advances to v0.5 for production/research EngageAdaptive parity before the accepted whole-combat Stage-A surface. CP145 adds observation-only attribution telemetry without changing the v0.5 combat doctrine. CP146 advances to v0.6 because Tactical Power decisions and K/E missile-interception actions can change combat outcomes; all numerical component authority remains frozen. Historical CP144/CP145 balance evidence therefore remains evidence under `cp145_legacy` and must not be mixed with v0.6 contextual outcomes as if doctrine were unchanged. No output automatically promotes balance changes.


## CP147 kernel v0.7 — tactical package utility

CP147 retains the explicitly selectable `cp146_contextual` path for exact accepted-result reproduction and adds `cp147_tactical_utility`. The v0.7 doctrine couples Tactical Power allocation to powered-resource action choice using a bounded, deterministic, information-limited utility selector. Candidate utility may use own mechanics, current geometry/track and defensive state, observed hostile actions, and projected terminal missiles; hidden opponent build fields are forbidden.

For K/E main weapons, direct ship fire and Held Main are distinct actions. A sole legal ship attack is not diverted for ordinary Shield/Armor exposure; projected Hull risk is required before defensive diversion can compete. When ship fire is illegal, terminal Firm-track Held Main remains available; dual-main packages may split banks. Terminal PDS demand is based on projected terminal subflights, not all distant inbound missiles. Turn-Refresh tactical Shield recharge preserves core and currently relevant terminal/hardener TP before spending optional recharge. All component statistics remain unchanged.
