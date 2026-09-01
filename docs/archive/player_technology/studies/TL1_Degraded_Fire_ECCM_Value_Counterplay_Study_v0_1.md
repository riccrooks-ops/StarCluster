# TL1 Degraded-Fire / ECCM Value Counterplay Study v0.1

## Current architecture interpretation

This file is retained as historical calibration evidence. Current architecture separates degraded-fire **permission** from its numerical penalty: a specific weapon/variant/upgrade grants permission to fire from Approximate, while the ship Tactical Computer/fire-control profile supplies the degraded-fire penalty. Historical `-10/-20/-25/-30` study fields therefore represent candidate computer/fire-control penalties applied to explicitly enabled study weapons; they are not production weapon-profile-owned numbers. The current TL1 computer working value is -25 percentage points, and no production weapon is enabled merely by this clarification. Ordinary missiles remain Firm-terminal by default; any future Approximate-target missile rule is separate and missile-specific.

## Question

Checkpoint 75a established that the -20 and -25 percentage-point Approximate-track direct-fire candidates are both mechanically viable. Checkpoint 76 asks the next operational question: **when a specific weapon is capable of degraded fire, does restoring a Firm track with ECCM remain sufficiently valuable that degraded fire is a fallback rather than an easy substitute for counter-EW?**

This checkpoint does not promote either penalty and does not assign degraded fire to any production weapon.

## Design guardrail

Approximate-track direct fire is an explicit weapon-profile, variant, or upgrade capability. It is not an entitlement of the Kinetic, Energy, or any other weapon family. Two weapons in the same family may legitimately differ because one has the required fire-control/software/munition upgrade and the other does not.

A degraded-fire capability must also impose a **material combat penalty**. It may give a ship useful agency while jammed, but it must not make the appropriate counter-EW capability economically irrelevant. A candidate is therefore judged under the Tactical Power, offensive-fire, active-sensor, and PDS opportunity costs that matter in ordinary combat, not only by its isolated final hit chance.

The implementation remains data-driven. Checkpoint 76 keeps -20 and -25 as study-only candidates. It deliberately does not declare one to be the universal degraded-fire value.

## Accepted starting evidence

Checkpoint 74d validated the direct-fire foundation and showed that configured -10/-20/-30 percentage-point penalties propagate correctly into final hit chance while Firm-only weapons remain blocked on Approximate tracks. Checkpoint 75a then applied the -20/-25 candidates and showed that:

- both penalties remain combat-viable;
- -25 produces a clearly stronger pacing penalty than -20;
- equal Kinetic/Energy treatment avoids arbitrary family-specific asymmetry;
- one-family-only degraded-fire access is extremely powerful under jamming;
- missile/torpedo terminal eligibility remains independent and Firm-gated by the missile's own architecture.

Those studies intentionally isolated the degraded-fire mechanic. They did not answer whether ECCM still earns its Tactical Power cost once degraded fire is available.

## Operational study

Study ID: `tl1-itc18-degraded-fire-eccm-value-counterplay`.

The study uses the accepted 35-Space `balanced_generalist_ew_major` build, production 5 Tactical Power, Balanced-0 sensing, `FullVolleyFirst`, normal active acquisition, no overload, PDS enabled, 100 starting fuel, and the pre-combat EW sub-phase. Side A carries one Kinetic or Energy direct-fire battery. Side B carries one Missile battery. This makes combined direct-fire telemetry effectively Side A and missile/PDS telemetry effectively the opposing package while still exercising Tactical Power competition.

Checkpoint 76 also exercises the accepted AI Doctrine Registry v0.2 rather than treating EW as an isolated arithmetic switch. The hostile Missile side uses `tl1-ew-preserve-combat-package-v1` for jammed cases, so ECM is attempted only when its own ready combat package and possible reactive ECCM headroom remain affordable. Side A uses the accepted `tl1-ew-reactive-eccm-v1` where a reactive response is requested. The aggressive-ECCM cases intentionally bypass doctrine and request normal ECCM as a diagnostic control; they are not a proposed default doctrine.

### Geometry contexts

Six contexts are used:

- Kinetic vs Missile, fixed range 3, simultaneous movement;
- Energy vs Missile, fixed range 3, simultaneous movement;
- Kinetic vs Missile, dynamic track-aware movement, Side A first;
- Kinetic vs Missile, dynamic track-aware movement, Side B first;
- Energy vs Missile, dynamic track-aware movement, Side A first;
- Energy vs Missile, dynamic track-aware movement, Side B first.

The fixed-range contexts provide a clean otherwise-Firm ECM degradation lane. The dynamic contexts test whether geometry, movement order, sensor power, missile pressure, and PDS create different incentives.

### Response packages

Every context contains nine packages:

1. Firm reference: no hostile ECM, no ECCM, Firm-only direct fire.
2. Jammed Firm-only / no ECCM: hostile accepted ECM doctrine, no degraded fire, no ECCM.
3. Jammed Firm-only / reactive ECCM: hostile accepted ECM doctrine, no degraded fire, accepted reactive ECCM.
4. -20 degraded fire / no ECCM.
5. -20 degraded fire / accepted reactive ECCM.
6. -20 degraded fire / aggressive normal-ECCM diagnostic.
7. -25 degraded fire / no ECCM.
8. -25 degraded fire / accepted reactive ECCM.
9. -25 degraded fire / aggressive normal-ECCM diagnostic.

Total: **54 variants x 10,000 trials = 540,000 substantive trials**, preceded by a 54-variant actual-consumer preflight and 54 one-trial full-pipeline smoke executions.

## Evidence to review

The release gates verify wiring and that the intended counterplay actually occurs. They do **not** decide whether -20 or -25 is acceptable from a win-rate threshold.

The native review should compare, within each geometry/family context:

- frequency and duration of Approximate versus Firm observations;
- actual Side-B ECM and Side-A ECCM power committed;
- direct shots, final hit chance, and direct hit rate;
- track-unavailable and insufficient-power preventions;
- Side-B missile launches;
- Side-A PDS attempts and interceptions;
- engagement length, unresolved rate, layer damage, and conditional outcome;
- reactive ECCM versus no-ECCM degraded fire;
- aggressive ECCM versus accepted reactive ECCM;
- -20 versus -25 when the ship deliberately accepts degraded fire.

The key design question is not whether degraded fire can win. It is whether **restoring Firm remains meaningfully better when the ship can afford it**, while accepting degraded fire remains a plausible choice when ECCM would compromise another important combat function.

## Promotion criteria

A future production promotion requires human review. Evidence should reject or revise a candidate if degraded fire makes ECCM routinely irrelevant, if the penalty is so severe that the capability rarely creates useful agency, or if a candidate creates pathological power/PDS incentives. The exact threshold remains data-driven rather than hard-coded into the release gate.

If both -20 and -25 preserve meaningful ECCM value, they may remain distinct upgrade-path candidates rather than forcing a universal value. For example, a less sophisticated Volume Fire upgrade could use a stronger penalty and a later fire-control improvement could reduce it. Such progression must still satisfy the project's logical and combinatorial technology checks.

## Missile boundary and future capability

Checkpoint 76 grants **no missile degraded-fire capability**. Ordinary command-guided, seeker-only, sensor-only, and sensor-plus-seeker missiles retain the Checkpoint 75 terminal rules and require the appropriate legitimate Firm terminal solution before an attack roll.

A future missile may nevertheless carry an explicit missile-specific Approximate-target capability. A possible **Swarmer Missile** concept is volume saturation: expend a deliberately larger barrage into the estimated target volume so some portion of the Missile Flight may find or intersect the target despite lacking an ordinary Firm solution. The eventual cost could be terminal accuracy, effective attack strength, larger flight/ammunition expenditure, seeker/search behavior, or a combination. That remains a separate missile-profile capability with its own acquisition, terminal, countermeasure, and balance rules; it is not inherited from the direct-fire Approximate-Track Fire trait.
