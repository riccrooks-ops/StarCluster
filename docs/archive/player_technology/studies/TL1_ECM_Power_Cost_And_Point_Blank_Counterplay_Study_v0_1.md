# TL1 ECM Power Cost and Point-Blank Counterplay Study v0.1

## Purpose

Checkpoint 69d established that the causal Sensor/EW resolver is mechanically coherent, but also exposed a more urgent balance question than the remaining passive-awareness comparison: **uncountered TL1 ECM can deny Firm discrimination strongly enough to suppress direct-fire eligibility even at same-hex tactical range**.

Checkpoint 70 therefore keeps the causal rule unchanged and tests whether ordinary Tactical Power opportunity cost is sufficient counterplay before introducing any same-hex exception or weakening ECM itself.

The study asks:

1. How does a normal ECM cost from **1 through 5 Tactical Power** change the jammer's operational combat performance under the accepted 5-TP TL1 reactor?
2. Does increasing normal ECM cost restore healthy practical counterplay at **fixed range zero**, especially against direct-fire weapons?
3. Does the answer depend on the jammer's own weapon family and power demand?
4. Does matched **1-TP normal ECCM** restore Firm discrimination coherently across the same cost sweep?

The existing 1-TP ECM value remains the production control. Costs 2-5 are calibration-only sensitivity values and are not production changes.

## Fixed Sensor/EW envelope

Checkpoint 70 uses **Balanced-0** as a fixed study fixture:

- Passive Firm/Approximate: **1/3**;
- normal Active Firm/Approximate: **3/4** at **1 TP**;
- overloaded Active Firm/Approximate: **4/5** at +1 TP, although Sensor overload is disabled in this study.

This does not promote Balanced-0 to the production sensor table. CP69d showed Balanced-0 and Balanced-1 to be operationally indistinguishable under AcquisitionFirstAutoActive, so the passive-awareness question is deferred while ECM/ECCM balance is isolated.

## Same-hex rule remains unchanged

Checkpoint 70 does **not** add a special point-blank ECM exception.

At range zero:

- line of sight is guaranteed and cannot be occluded;
- emission provenance still resolves;
- ECM/ECCM discrimination still resolves;
- positive net ECM may still degrade Firm to Approximate;
- matching or superior ECCM may preserve Firm.

The point-blank lanes are deliberately constructed to determine whether power opportunity cost alone makes that rule healthy at TL1. If even a jammer consuming the full 5-TP reactor budget still creates unacceptable practical immunity, that is evidence that a later mechanical constraint is required rather than evidence that ECM should simply cost still more power.

## Power-cost sweep

Side B is the jammer. Its **normal ECM Tactical Power cost** is overridden to 1, 2, 3, 4, or 5 TP. Rating remains 1; the sweep changes cost only.

Side A is the counter-EW side. In countered lanes its normal ECCM remains **rating 1 at 1 TP**.

The existing power allocator remains authoritative. EW is committed before Sensor/Direct-Fire allocations at the post-Movement boundary, so higher ECM cost naturally competes with Active Sensors, shield recharge, PDS, and weapon power. No artificial anti-stacking or special starvation rule is added.

Weapon-power context remains important:

- Kinetic main fire normally needs 1 TP;
- Energy standard output normally needs 2 TP, with its accepted lower-output behavior retained;
- Missile launch itself requires 0 TP.

The 5-TP ECM endpoint is therefore especially diagnostic for a missile-armed jammer: it can reveal whether full-reactor jamming remains disproportionately strong when its main offensive package does not need launch power.

## Matrix

Study ID: `tl1-itc12-ecm-power-cost-point-blank-counterplay`.

There are **nine matched contexts**. Each context contains:

- 1 clear no-EW control;
- 5 jammed/no-counter variants at ECM costs 1-5;
- 5 matched-ECCM variants at ECM costs 1-5.

That gives **11 variants per context / 99 variants total**.

### Operational contexts - 66 variants

Three pairings are tested under both Side-A-first and Side-B-first movement:

- Kinetic vs Missile;
- Energy vs Missile;
- Kinetic vs Energy.

Controls:

- TrackAwareOpponentRange;
- initial range 4;
- STL Move 1/1;
- radius-5 finite map.

These lanes measure the ordinary tactical opportunity cost of increasingly expensive ECM.

### Fixed point-blank contexts - 33 variants

The ships begin and remain at range zero with both STL movement values set to zero and simultaneous movement order:

- Kinetic vs Missile;
- Kinetic vs Energy;
- Energy vs Kinetic.

Side A is always a direct-fire family so Firm-track denial directly represents loss of direct-fire eligibility. Side B covers Missile, Energy, and Kinetic so the jammer's own offensive power demand is exposed rather than hidden.

## Fixed controls

Every variant retains:

- the accepted `balanced_generalist_ew_major` 35-Space EW-capable fixture on both sides;
- `tl1-production` technology;
- `aux-r53-none-tl1` zero-effect AUX control;
- 5-TP reactor output;
- FullVolleyFirst power doctrine;
- AcquisitionFirstAutoActive track policy;
- 100 starting fuel and 2 fuel per traversed hex;
- EvM disabled, PDS enabled, normal shield recharge enabled;
- STL overload disabled;
- Sensor overload disabled;
- ECM/ECCM overload disabled;
- historical static net-EW range penalty fixed at zero.

## Validation structure

The normal checkpoint must run, in order, before the substantive Monte Carlo stage:

1. repository/native dependency/build/unit/core regression gates;
2. the 924-row deterministic Sensor/EW foundation;
3. an **actual-consumer preflight** that deserializes and validates all 99 CP70 variants with the same C# path used by the simulation;
4. a **99-variant, one-trial-per-variant full-pipeline smoke** through simulation, gates, and reporting;
5. only then the 99-variant / 990,000-trial substantive study.

No target win rate is a blocking release gate.

## Required review evidence

The dedicated review reports, by variant:

- operational versus point-blank geometry;
- clear, jammed, or countered package;
- Side-B ECM normal power cost and Side-A ECCM cost;
- weapon families and movement order;
- conditional win share and combat duration;
- final/minimum/maximum range;
- Firm/Approximate/No-Track evaluations;
- ECM, ECCM, and Active Sensor power committed;
- track-unavailable and insufficient-power preventions;
- direct shots, missile launches, PDS attempts, and fuel use.

## Interpretation priorities

**First:** inspect fixed range-zero lanes. Determine at what ECM costs, if any, a direct-fire opponent regains meaningful attack eligibility and whether the jammer pays a commensurate offensive/defensive price.

**Second:** compare jammer weapon families. If Missile remains highly effective while Energy/Kinetic pay steep costs, the issue may be the interaction between ECM priority and weapon power rather than ECM discrimination alone.

**Third:** inspect matched ECCM. A 1-TP ECCM counter should restore Firm discrimination when funded, but its own opportunity cost should remain visible rather than being treated as free cancellation.

**Decision rule:** do not choose an ECM cost merely to force a desired win percentage. If cost alone yields a healthy tactical tradeoff, retain the causal rule and consider the most promising cost in a later production-candidate study. If even the full 5-TP endpoint leaves point-blank hard denial strategically dominant, stop increasing cost and test a principled mechanical point-blank/discrimination constraint next.
