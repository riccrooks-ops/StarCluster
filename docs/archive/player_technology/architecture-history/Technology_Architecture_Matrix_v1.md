# Technology Architecture Matrix v1

> **CP108 architecture note:** `Technology_Component_Table_v0_2` is the qualitatively reviewed whole-ladder placement/expression authority. This Matrix remains the numerical/current-candidate reference: CP108 changes none of its TL1-TL3 numerical values and assigns no TL4-TL9 balance values.

## Purpose and authority

This is the current whole-ladder technology roadmap. It records durable progression roles and the **current working/candidate state**, not checkpoint history. Detailed experiment provenance belongs in validation/evidence artifacts.

**CP106 architecture overlay:** the numerical TL chart and accepted TL1-TL3 values are unchanged. `Technology_Family_Storyboard_v1_1.md` is the conceptual authority for how individual families develop, branch, revive, or remain quiet across TL1-TL9; the Foundation Completeness Audit covers supporting campaign/ship domains. The generic whole-ladder rows below remain a working table scaffold, not a requirement that every family advance at every row.

Technology Level is discipline-specific. Mixed-TL ships are expected. A sensitivity tested across multiple subsystem families does not imply that every family receives the same progression.

## Status legend

- **Current working** - current authoritative/working reference.
- **Conceptual candidate** - plausible direction not yet executable/validated in the standing combat consumer.
- **Locally validated working candidate** - supported strongly enough for continued integration, but not final cross-TL/production authority.
- **Cross-TL validated candidate** - survived broader mixed-tech or exact-edge integration and remains a candidate pending explicit production promotion.
- **Deferred** - deliberately unspecified.

## Whole-ladder architecture

| TL | Hull | Tactical Computer | Sensors / EW | Power / Reactor | Propulsion | Shields | Armor | Weapons / PDS |
|---:|---|---|---|---|---|---|---|---|
| 1 | 35-Space cruiser baseline | Electronic fire-control baseline | Conventional passive/active sensing; ECM1/ECCM1 | Peak fission | Move1 STL / strategic Move1 FTL | Baseline field | Mature alloy/ceramic-composite armor | Baseline Kinetic/Energy/Missile weapons and separate Kinetic, Energy/Beam, and local AMM PDS families |
| 2 | 35-Space base held | Refined conventional fire control | Discrimination-focused maturation; scalable ECM/ECCM | Early practical fusion | Move2 propulsion law; no base miniaturization | Higher field capacity | Ceramic-composite durability maturation | Kinetic APEN1; other family baselines largely held |
| 3 | **36-Space mature cruiser integration** | **Mature integrated fire control; Evasive Compensation** | **Dual normal Active modes; efficient rating-2 ECM/ECCM** | **Mature compact fusion** | **Move3 STL/FTL; bounded STL overload; 5-Space drives held** | **Powered hardening** | **AP1 / AI5** | **Family-specific maturation: Kinetic power efficiency, Energy safe High output, Missile autonomy/Move4, differentiated PDS maturation** |
| 4 | Advanced structural integration | Advanced tactical integration | Improved discrimination/processing | High-output fusion | Advanced propulsion roles | Higher-performance field architecture | Advanced layered/material systems | Deferred future family-specific expansion |
| 5 | Specialized structural options | Specialized high-end fire control | Advanced sensor/EW techniques | Early antimatter plus peak-fusion option | Specialized propulsion | Advanced field control | High-energy/material countermeasures | Deferred |
| 6 | Mature advanced structure | Mature advanced computation | Mature advanced EW | Mature antimatter | Mature advanced propulsion | Mature advanced shields | Mature advanced armor | Deferred |
| 7 | Frontier structural integration | High-end specialized integration | Frontier conventional/advanced sensing | High-output antimatter | Frontier propulsion | Frontier shield specialization | Frontier armor specialization | Deferred |
| 8 | Exotic structural integration | Exotic integration support | Exotic sensing/EW roles | Direct/fractional matter conversion plus peak-antimatter option | Exotic propulsion | Exotic field architecture | Exotic material/field-assisted armor | Deferred |
| 9 | Peak player cruiser architecture | Peak player fire-control architecture | Peak player information control | Total matter conversion | Peak player propulsion architecture | Peak player shield architecture | Peak player armor architecture | Peak player weapon/PDS architectures |

These are progression roles, not a requirement that every statistic improve at every row. The TL3 **base** row is complete and native-accepted as a value table under CP101. CP102 binds that unchanged row into executable construction/progression/runtime consumers. CP102 native acceptance proves the implementation/executable binding; CP103 has now completed the first native-accepted substantive integration measurement; CP104 is now native-accepted diagnostic closure; CP105 adds family-story architecture only and changes none of these values. Additional Auxiliaries, specialist subcomponents, and pinnacle legacy-family items remain separate future catalog growth.

## Current TL1 references

- Tactical Computer ordinary targeting assistance: +10 pp Operational; degraded-fire penalty -25 pp when an explicit compatible weapon permits Approximate-track fire; Evasive Compensation 0.
- Sensor discrimination resistance 0; current Balanced-0 range fixture remains a calibration fixture rather than a universal production range claim.
- ECM1 and ECCM1 normal ceilings at 1 TP/rating; each current suite occupies 1 Installation Space. Multiple same-type suites may be installed for redundancy, but ratings are non-additive and the ship uses the highest applicable functional rating.
- Peak Fission Main Reactor: 5 Operational TP / 6 Installation Space, with the current 3/1/0 damaged-state mapping retained.
- Shield: Capacity 2 / 3 Space, Base Recharge 1, tactical recharge 1 Shield per TP capped at 2 TP/turn, Shield Armor 0.
- Armor: AP0 / AI4 baseline.
- Current penetration references used by the integrated combat model: Kinetic SPEN1/APEN0, Energy SPEN1/APEN1, Missile SPEN1/APEN2.

## Current TL2 candidate state after cross-TL screening

| Stream | Current candidate | Status after broad/exact-edge integration | Held/deferred properties |
|---|---|---|---|
| Tactical Computer | Ordinary targeting +12 pp | Locally validated working candidate | Degraded-fire penalty remains -25; Evasive Compensation 0; condition-specific degraded-fire behavior deferred |
| Sensor | Discrimination Resistance 1 | Locally validated working candidate | Physical range improvement and new overload behavior deferred |
| ECM | Normal ceiling 2 at 1 TP/rating; 1 Space | Locally validated working candidate | Same-type redundant suites are non-additive; later efficiency/overload behavior separate |
| ECCM | Normal ceiling 2 at 1 TP/rating; 1 Space | Locally validated working candidate / counter capability | Same-type redundant suites are non-additive; value is strongly context/power dependent |
| Power / Reactor | Early Practical Fusion: 6 Operational TP / 6 Space | Locally validated working candidate | Damaged output, overload, efficiency, storage, footprint, reliability and auxiliary generation unchanged/unpromoted |
| Shields | Capacity 3 / 3 Space | **Cross-TL validated candidate** | Base/tactical recharge, cap, Shield Armor, condition behavior, overload, efficiency and footprint unchanged/unpromoted |
| Armor | AP0 / AI5 | **Cross-TL validated candidate** | AP1 is not part of TL2; footprint/repair/ablative/special-material behavior unchanged |
| Kinetic penetration | SPEN1 / APEN1 | Locally validated working candidate; CP99 AP0 envelope was neutral/non-dispositive | SPEN2 remains experimental; combined SPEN2/APEN1 is not bundled |
| Energy penetration | SPEN1 / APEN1 | Current; no TL2 penetration promotion | Future Energy progression remains family-specific |
| Missile penetration | SPEN1 / APEN2 | Current; no TL2 penetration promotion | Future Missile progression remains family-specific |

Cross-TL validation is evidence of integration health, not automatic conversion into final production data.

## Complete TL3 base table and accepted CP102-CP104 evidence

The accepted TL3 row is a **family-specific working value row**, not a universal statement that TL3 is every family's maturation endpoint. CP101 completed the standard/base TL3 values; CP102 implements them; CP103 measured them; and CP104 closed the targeted TL3 diagnostics without changing them. CP105 now supplies the missing family stories. For Power, for example, TL1 is Peak Fission, TL2 introduces Early Practical Fusion, TL3 is Mature Compact Fusion, and TL4 remains the High-Output Fusion step. Other families may mature earlier, later, branch, remain quiet, or revive. The base row is not a complete future catalog.

| Stream | TL3 base executable candidate | Progression identity / boundary |
|---|---|---|
| Hull | **36 Installation Space; Hull 12, Crew/Marines, cargo and one-shuttle capacity held** | Minimum +1 integration-capacity step; no bundled durability/personnel/hangar increase. |
| Tactical Computer | **+12 ordinary held; -25 Approximate penalty held; Evasive Compensation +5 pp** | Capability addition; own Evasive penalty only, never a positive bonus. |
| Sensor | **DR1 held; Low Active 3/4 @1 TP; High Active 4/5 @2 TP, no Strain** | Rated operating-mode maturation; overload beyond High deferred. |
| ECM | **Rating2 held; full-strength normal 1 TP total** | Power-efficiency maturation; same-type ratings remain non-additive. |
| ECCM | **Rating2 held; full-strength normal 1 TP total** | Power-efficiency maturation; no range/discrimination increase. |
| Main Reactor | **Mature Compact Fusion: 6 TP / 5 Space** | Miniaturization; 3/1/0 damaged-state outputs held. |
| STL | **Move3 / 5 Space; 2 fuel/hex held; Overload I +1 Move, +1 TP, +2 fuel, +1 Strain; Strain Limit2 held** | Primary performance advances; no simultaneous drive miniaturization. |
| FTL | **Strategic Move3 / 5 Space** | Faster known-space transit while unknown-sector stop/interruption rules remain. |
| Shields | **Capacity3/3 Space held; optional 1-Space Hardener sustains 1 TP for SA1** | Optional support unlock; normal hardening nonstacking; overload deferred. |
| Armor | **AP1 / AI5** | Real Protection matures; Integrity held. |
| Kinetic Main | **6 Space; Acc+20, DAM4, SPEN1/APEN1, Range4, Ammo100 held; ordinary firing 0 TP** | Mature low-discretionary-power offense; finite ammunition remains the defining cost. |
| Energy Main | **6 Space; Range5; 1 TP→DAM2, 2 TP→DAM3, 3 TP→DAM4 safe rated modes; standard/high retain Acc+25 and SPEN1/APEN1** | Former overload-level output becomes safe High mode; no automatic DAM5 overload. |
| Missile Main | **6 Space; DAM5/SPEN1/APEN2, Range6, 25 Flights, 0 TP launch held; TL3 missile drive gives Move4; onboard navigation sensor standard; seeker optional** | Autonomy/propulsion maturation rather than larger warhead; ordinary Firm terminal requirement held. |
| Kinetic PDS | **TL2 base profile held: base13, RC1, readiness1 TP, Ammo60, 2 Space** | Deliberate hold; no placeholder stat increase. |
| Energy PDS | **base16/RC1 held; readiness improves 2 TP→1 TP; ammunition-free, 2 Space** | Matures its principal power weakness. |
| AMM PDS | **base20/Ammo25 held; 1 TP→RC1 or 2 TP→RC2, 2 Space** | Scalable anti-saturation readiness; normal two-attempt-per-flight cap and seeded automatic allocation remain. |

The accepted value authorities remain `tl3_base_technology_candidates_v0_2.json` and `tl3_base_build_sanity_v0_1.json`; CP102 does **not** change those values. `tl3_executable_implementation_profile_v0_1.json` binds them to the executable v7 consumer. Their lifecycle is **native-accepted implemented/executable and substantively measured through CP103, with CP104 diagnostic closure accepted**; no automatic numerical promotion follows. CP105 changes no values and instead establishes the family-story authority that will drive the next provisional TL1-TL9 table pass.

### TL3 base Space and Power sanity

The proposed 36-Space Hull and 5-Space reactor produce useful but bounded integer breakpoints:

| Architecture | TL1/TL2 used/free | TL3 used/free | TL3 interpretation |
|---|---:|---:|---|
| 1 Main / 1 Reactor | 28 / 7 | **27 / 9** | Generalist envelope broadens. |
| 2 Main / 1 Reactor | 34 / 1 | **33 / 3** | Legal outlier becomes practically supportable, but power remains family/mode constrained. |
| 1 Main / 2 Reactors | 34 / 1 | **32 / 4** | Legal outlier becomes practically supportable; 10 Space remains committed to reactors. |
| 2 Main / 2 Reactors | 40 / -5 | **38 / -2** | **Still illegal**; no special prohibition is required. |

A future dual-Main/dual-Reactor core first becomes spatially legal at an effective 38-Space envelope; adding even one meaningful 3-Space support package raises that milestone to 41. No future TL is preassigned to either breakpoint.

Power remains an operational constraint rather than a construction-legality filter. One TL3 6-TP reactor can fund two Standard Energy shots (4 TP) plus High Active Sensor (2 TP) exactly, leaving no power for PDS, ECM/ECCM, hardening, EvM, or tactical Shield recharge; with Low Active it retains only 1 TP. Two High-output Energy shots plus High Active would require 8 TP and therefore cannot run from one reactor. A support-heavy Kinetic/Missile generalist can itself consume all 6 TP on High Active + PDS + ECM + ECCM + Shield Hardener before EvM or tactical recharge. Dual-Main/single-Reactor therefore remains an outlier with meaningful opportunity cost rather than receiving an arbitrary one-reactor-per-weapon rule.

## TL3 progression semantics

The accepted CP99 TL1->TL2 lattice uses exact same-Space edges. That representation is not sufficient for every TL3 advance:

- Tactical Computer, Sensor, ECM, ECCM, and Armor are same-footprint property/capability transitions.
- Mature Compact Fusion is a **miniaturization transition** with Installation Space delta -1; its value includes newly legal fitting envelopes and cannot be reduced to a same-Space replacement edge.
- Shield Hardener is an **optional component unlock**, not a primary Shield Generator stat replacement. Its +1 Space cost applies only when installed.
- Held weapon-penetration streams create no TL2->TL3 penetration edge until a family-specific advancement is actually chosen.

Standing integration tooling must therefore represent transition type and Space effect explicitly rather than forcing new technology into the older exact-edge shape.

## Component Installation Space catalog

For the current compact footprint/multiplicity reference, use:

- workbook sheet **Component Catalog** in `StarCluster_Technology_Architecture_Matrix_v1.xlsx`; and
- machine-readable `component_installation_space_catalog_v1.json`.

Those references consolidate current working footprints plus the executable TL3 candidate footprints without turning this roadmap into a checkpoint inventory. Player-cruiser capacity is technology-dependent: 35 Space at TL1/TL2 and 36 Space for the accepted TL3 Hull implementation. Every ordinary combat build requires at least one Main Weapon, one Reactor, and one installed Sensor; additional Main Weapons/Reactors are optional full-Space design choices, while ECM/ECCM remain optional. ECM/ECCM duplicate installations are legal for redundancy, but same-type ratings never add: use the highest applicable functional rating.

The 36-Space TL3 Hull envelope, 5-Space Mature Compact Fusion reactor, completed base weapon/PDS/propulsion row, and 1-Space Shield Hardener are now bound to the CP102 executable v7 consumer. They remain unpromoted; CP102 executable acceptance and CP103 substantive integration evidence are complete. CP104 supplies accepted targeted closure evidence. CP105 adds the technology-family architecture used for the later full-tree table pass without changing these footprints or values.

## Weapon-family penetration architecture

Penetration progression is family-specific. The current references remain deliberately different:

| Family | TL1 | TL2 working/current | TL3 base |
|---|---|---|---|
| Kinetic | SPEN1 / APEN0 | SPEN1 / APEN1 | **Held at SPEN1 / APEN1** |
| Energy | SPEN1 / APEN1 | SPEN1 / APEN1 | **Held** |
| Missile | SPEN1 / APEN2 | SPEN1 / APEN2 | **Held** |

**No symmetric promotion is implied.** TL3 Armor AP1 creates a natural future cross-TL environment in which Kinetic APEN1 has a real breakpoint to exploit; it does not require a new Kinetic penetration increase at TL3.

## Durable progression guardrails

- Do not improve every stream or statistic at every TL.
- Preserve subsystem-family identity; avoid converging different weapon families into differently named versions of the same mechanics.
- Cross-category prerequisites are sparse and causal. Broad low-TL research does not synthesize a de facto high-TL capability.
- Power output, density, efficiency, damaged-state behavior, overload, storage, auxiliary generation, and footprint are separate reactor axes.
- Shield capacity, recharge, hardening, condition behavior, maintenance/boost power, overload, and footprint are separate shield axes.
- Armor Protection and Armor Integrity are separate axes and must retain meaningful APEN counterplay.
- Integer damage/penetration/defense breakpoints are real design effects; do not treat a one-point increase as a uniform percentage gain.
- Ordinary missiles retain their distinct terminal-guidance architecture; direct-fire degraded-fire rules do not automatically transfer to missiles.
- A locally or cross-TL validated candidate can still be revised when later technology exposes skew.
- Multiple ECM/ECCM suites may be installed for redundancy, but same-type ratings are never additive; use the highest applicable functional rating. Allied cooperative EW remains a separate capped mechanic.
- Registration in the technology table is not runtime activation. A conceptual candidate becomes an executable progression option only after its mechanics, legal-build semantics, and actual-consumer bindings are implemented and preflighted.

For simulation methodology and candidate lifecycle, see `docs/development/Simulation_Development_Guidelines.md`.

## Current generalized cross-TL construction envelope

The **native-accepted TL1/TL2 regression envelope remains CP99 foundation v0.8**: 82,944 raw combinations, **11,776 legal builds**, **37,184 exact same-Space TL1->TL2 progression edges**, 181 exact-edge strata, 362 selected logical edge pairs, and 724 mirrored Adaptive Engage variants. Neither CP102 nor CP103 alters or reinterprets that frozen regression surface.

CP102 now binds the complete TL3 base candidates to an **executable v7 consumer** without changing their CP101 values. The native-accepted CP99 v0.8 TL1/TL2 foundation remains a frozen regression reference, while CP102 uses separate v7 construction-envelope and transition-smoke definitions so variable Hull capacity, reactor miniaturization, optional unlocks, rated modes, and held transitions do not have to masquerade as same-Space scalar replacements.

## Integration guardrails update

- **Mandatory combat core:** every ordinary legal combat ship includes at least one Main Weapon, one Reactor, and one installed Sensor. Additional Main Weapons/Reactors are optional explicit design choices; ECM/ECCM remain optional. Sensorless states are reserved for explicit diagnostics/special objects or combat damage, not normal construction.
- **Accepted regression baseline:** CP99 foundation v0.8 remains the native-accepted TL1/TL2 exact-edge regression consumer and is not rewritten by CP102.
- **TL3 executable candidate:** CP102 was native-accepted under standing suite v0.17; current standing suite v0.18 retains that v7 TL2/TL3 consumer after implementing variable Hull capacity, Space-changing transitions, optional Shield Hardener compatibility, dual normal Sensor modes, fixed full-strength EW costs, EvComp, propulsion/weapon/PDS runtime bindings, and the current 16-transition registry. `tl3CombatConsumerEnabled=true` means executable ownership only; TL3 remains uncalibrated and unpromoted.
- **Base-table boundary:** TL3 base weapons, PDS, and STL/FTL are now explicitly defined by family-appropriate progression; broader Auxiliaries, specialist subcomponents, and pinnacle legacy-family items remain open. Do not add them merely to fill catalog space.


## Native-accepted CP102 executable TL3 integration

CP102 introduces cross-TL schema v7 while preserving CP99 v6 byte-for-byte as the accepted TL1/TL2 regression consumer. The v7 design separates two jobs:

- `cross-tl-build-permutation-foundation-v0_9.json` is a **construction-envelope preflight**. It enumerates 221,184 raw spatial combinations and 51,264 legal 35/36-Space builds, with 10,752 exact-fill builds. It deliberately collapses technology or operating-mode states that are Installation-Space-isomorphic and therefore cannot affect construction legality. It generates no combat trials.
- `cross-tl-build-permutation-foundation-v1_0.json` is the **semantic transition smoke**. It enumerates 43,008 raw / 38,400 legal transition-bearing states, validates 220,416 legal edges across all 16 registered TL2->TL3 transitions, and generates 16 named lower->higher pairs across both mover orders for exactly 32 one-trial integrated variants. These outcomes are pipeline evidence only.

The v7 transition vocabulary includes capacity integration, capability addition, operating-mode addition, power efficiency, miniaturization, primary performance, optional-component unlock, protection maturation, safe-output maturation, autonomy/propulsion, explicit hold, and readiness-mode addition. Each transition declares expected installed-Space and Hull-capacity deltas independently.

Runtime integration is explicit rather than inferred: TL3 Sensor Low/High normal power costs flow through the active-sensor allocator; ECM/ECCM have a distinct full-strength total-cost override so legacy per-rating semantics do not change; Shield Hardener is a separate powered damageable component; EvComp is condition-aware and can only reduce own-Evasive penalty to zero; AMM PDS can fall back from 2 TP/RC2 to 1 TP/RC1; and Energy High output is exercised as a safe rated mode rather than overload. Missile onboard-navigation presence is represented without inventing the deferred detailed navigation-sensor profile or weakening ordinary Firm-terminal rules.

No CP102 value or one-trial outcome is a balance promotion. CP103 uses the native-accepted CP102 consumer for the first substantive TL1/TL2/TL3 permutation study, evaluating design diversity, Pareto/frontier domination, integer breakpoints, mixed-era stacking, Tactical-Power opportunity costs, readiness/activity cliffs, and mover-order sensitivity without automatic value promotion.

## CP103 substantive TL1/TL2/TL3 integration measurement

CP103 adds schema v8 as an **analysis layer** over the accepted CP102 runtime. It changes no technology value. The weighted primary study (`cross-tl-build-permutation-foundation-v1_1.json`) enumerates 921,600 raw combinations and 164,160 legal TL2/TL3 tactical builds, with 43,584 exact-fill, 82,848 near-fill, and 37,728 underfilled builds. Space utilization is capacity-relative: exact means zero free Space, near means one through three free Space, and underfilled means more than three free Space against the selected 35- or 36-Space Hull.

The primary population has 96 non-empty composition/frontier-progression/Space cells. A deterministic square-root allocation selects 240 unordered statistical base pairs and mirrors them to 480 weighted logical pairings. A 32-base-pair diversity overlay adds 64 mirrored zero-weight diagnostics, and 32 named logical diagnostics remain zero-weight. Across two Adaptive Engage mover-order geometries this yields 1,152 variants and 288,000 substantive trials at the declared 250 trials per variant. Only the statistical sample carries population-representative weight.

A separate named-only legacy overlay (`cross-tl-build-permutation-foundation-v1_2.json`) keeps TL1/TL2/TL3 complete-tier anchors, old-component stacking, mixed-era packages, Hull breakpoints, and held-transition negative controls visible without treating that curated subset as population inference. Its 1,417,176-state raw axis product is a contract bound only; v8 materializes 33 named recipes resolving to 28 unique legal builds, 50 mirrored logical pairings, 100 variants, and 25,000 substantive trials. Every overlay comparison has zero population-inference weight.

For v8 only, `AdvancedComponentCount` and its information-control counterpart are **TL3 frontier stratifiers**, not scalar technology scores. The tactical frontier count includes TL3 Main Weapon/Reactor installations, Computer, Sensor, Shield, Armor, Hull, Shield Hardener, STL, PDS, and each installed ECM/ECCM suite. Strategic FTL is excluded because its held TL2/TL3 transition is tactically isomorphic and intentionally collapsed from the weighted primary population. The held Kinetic-PDS2/PDS3 label is likewise collapsed from population weighting but PDS still contributes when the installed weighted option is a genuinely improved TL3 PDS. Both held transitions remain explicit zero-weight diagnostic controls. V1–V7 historical semantics remain unchanged. V8 runtime-tier routing likewise derives from installed/effective selections, so a later-TL `installed=false` catalog placeholder cannot promote a legacy anchor to a newer whole-ship runtime profile.

CP103 outcome data remains human-review evidence. Any technology retuning, production promotion, initiative change, or construction-rule change requires an explicit later decision/checkpoint.
