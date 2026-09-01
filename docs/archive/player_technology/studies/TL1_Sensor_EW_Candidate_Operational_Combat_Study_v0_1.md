# TL1 Sensor/EW Candidate Operational Combat Study v0.1

## Purpose

Checkpoint 69 moves the Checkpoint 68 causal Sensor/EW foundation into controlled integrated combat without changing the production numerical baseline.

The study answers two narrow design questions:

1. Does **Balanced-0** gain useful situational awareness from Passive 1/3 instead of Passive 1/2 when Passive Firm remains 1 and the Active/overload envelopes are unchanged?
2. Does **Balanced-2** gain healthy tactical value from a stronger 5/6 overload envelope, or does that +2/+2 extension create an undesirable breakpoint relative to the 4/5 overload used by Balanced-0/1?

It also verifies that the causal ECM/ECCM model remains meaningful in operational combat, including at same-hex range.

## Candidate set

| Candidate | Passive Firm/Approx | Active Firm/Approx | Overload Firm/Approx | Diagnostic purpose |
|---|---:|---:|---:|---|
| Balanced-0 | 1/3 | 3/4 | 4/5 | Wider passive Approximate awareness without better passive targeting |
| Balanced-1 | 1/2 | 3/4 | 4/5 | Conservative reference with tighter passive awareness |
| Balanced-2 | 1/2 | 3/4 | 5/6 | Isolate the value and breakpoint risk of a stronger overload |

All three use one normal **1-TP** Active Sensor mode and one **+1-TP** overload commitment. Sensor overload remains reach-only and does not provide ECCM.

The other CP69 deterministic candidates remain useful sensitivity evidence but are not part of this primary operational comparison.

## Same-hex causal guardrail

The CP68 range-zero shortcut is removed.

At range zero:

- line of sight is guaranteed and cannot be occluded;
- the observer still receives normal emission provenance;
- Active Sensor and ECM emissions remain attributable when their other rules permit;
- ECM/ECCM discrimination still resolves normally;
- positive net ECM may degrade an otherwise Firm observation to Approximate;
- matching or superior ECCM may preserve Firm;
- co-location by itself does not create an ECM-immune Firm target solution.

This preserves the fiction that a tactical hex is a very large volume and gives tall ECM investment the possibility of remaining relevant even at point-blank tactical range.

## Operational matrix

The study ID is `tl1-itc11-sensor-ew-candidate-operational-combat`.

Matrix size:

- 3 Sensor/EW candidates;
- 3 weapon-family pairings: Kinetic vs Missile, Energy vs Missile, Kinetic vs Energy;
- 2 movement orders: Side A first and Side B first;
- 4 Sensor/EW packages;
- **72 total variants**;
- **10,000 trials per variant** by default;
- **720,000 total default trials**.

### Sensor/EW packages

`clear-normal`
: Both ships may use normal Active Sensors under AcquisitionFirstAutoActive. Sensor overload, ECM, and ECCM are off.

`clear-overload`
: Both ships may use SafeWhenNeeded Sensor overload. ECM and ECCM are off.

`jammed-no-counter`
: Both ships may use SafeWhenNeeded Sensor overload. Side B powers normal ECM; Side A has no ECCM response.

`jammed-eccm`
: Same as jammed-no-counter, but Side A powers normal ECCM against Side B's normal ECM.

The ECM packages use normal rating rather than ECM overload so the study isolates the causal discrimination rule instead of adding another Strain/overload axis.

## Fixed controls

Every variant uses:

- the same `balanced_generalist_ew_major` 35-Space construction on both sides;
- `tl1-production` technology profile;
- `aux-r53-none-tl1` zero-effect AUX profile;
- 5 Tactical Power reactor output;
- FullVolleyFirst power doctrine;
- AcquisitionFirstAutoActive track policy;
- TrackAwareOpponentRange movement;
- radius-5 finite tactical map;
- initial range 4;
- 100 starting fuel;
- 2 fuel per traversed hex;
- EvM fuel cost 1, with EvM disabled in this isolation study;
- PDS enabled;
- normal shield recharge enabled;
- STL overload disabled;
- no static net-EW range penalty.

The single installed EW-capable build is intentional: leaving ECM/ECCM components installed in every package prevents construction Space from becoming a hidden comparison variable when those systems are simply powered off.

## Causal integrated resolution

Candidate variants use the Checkpoint 68/69 `SensorEwFoundationResolver` rather than the historical effective-Firm-range subtraction model.

For each observer/target evaluation:

1. determine the observer's Passive or powered Active envelope;
2. apply the candidate's bounded Active Sensor overload extension when active and successfully funded;
3. preserve legitimate target Active Sensor and ECM emission provenance;
4. establish any emission-assisted Approximate contact;
5. compute net ECM from target ECM minus observer ECCM;
6. degrade Firm to Approximate when net ECM is positive;
7. never let ECCM extend the underlying sensor envelope or promote baseline Approximate to Firm.

Historical CP67 and earlier integrated studies retain their frozen behavior and data bindings. CP69 is an additive successor study rather than a reinterpretation of old results.

## Required telemetry

The candidate review output reports, by variant:

- candidate profile and Sensor/EW package;
- conditional Side A win percentage and combat duration;
- final and minimum range;
- Active Sensor power committed by each side;
- Firm, Approximate, and No Track evaluations by side;
- Sensor overload requests and activations;
- defending ECM and attacking ECCM power;
- track-unavailable and insufficient-power preventions;
- fuel spent.

Standard integrated outputs retain the broader damage, attack, movement, power, and resolution telemetry.

## Release gates versus review evidence

Blocking gates verify:

- exact 72-variant matrix coverage;
- equal 24-variant coverage for Balanced-0/1/2;
- exact 18-variant coverage for each Sensor/EW package;
- no trial errors;
- 100-fuel accounting with STL overload held off;
- normal Active Sensor power bounded to the candidate 1-TP mode in clear-normal controls;
- safe Sensor overload bounded by the accepted Strain limit;
- actual exercise of ECM and ECCM packages;
- zero use of the historical static net-EW range penalty.

**No win percentage is a blocking gate.**

Candidate selection should consider information value, attack eligibility, power demand, overload dependence, EW counterplay, geometry, and family-specific outcomes together. A candidate is not preferred merely because it produces the highest aggregate win rate or the longest Firm envelope.

## Interpretation priorities

### Balanced-0 versus Balanced-1

This is the cleanest passive-awareness comparison. Active and overload behavior is identical. If operational behavior changes, the cause should be the extra passive Approximate hex or downstream decisions that use it.

A near-zero combat difference is also informative: it may indicate that current tactical decision-making does not yet consume Approximate information strongly enough to value the distinction. That result should not automatically invalidate Balanced-0; it may instead identify a future AI/UI/intelligence dependency.

### Balanced-1 versus Balanced-2

This isolates overload reach. Review whether the 5/6 overloaded envelope creates useful occasional opportunities or becomes a dominant solution that erases meaningful normal-sensor and movement tradeoffs.

### ECM versus ECCM packages

Confirm that normal ECM can meaningfully deny Firm discrimination without changing physical reach and that normal ECCM restores the expected counterplay when funded. The same-hex deterministic tests are the authoritative edge-case contract; the Monte Carlo study tests whether those rules matter coherently in an actual engagement.
