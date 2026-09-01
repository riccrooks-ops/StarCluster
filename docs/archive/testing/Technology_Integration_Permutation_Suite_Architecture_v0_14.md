# Star Cluster Technology Integration Permutation Suite Architecture v0.14

## Purpose

Version 0.14 is the standing mixed-TL integration/testing architecture for marginal subsystem progression. It promotes **Sensor** into the ordinary legal combat-ship core, preserves the accepted TL1/TL2 working component values, and consumes the deterministic same-Space progression lattice directly so a single declared construction axis can be evaluated without inventing TL3 values or changing initiative.

This document owns testing architecture only. It does not promote component values, choose production initiative, or define a target TL-versus-TL win rate.

## Revised legal envelope

The 35-Space player-cruiser envelope still enumerates 82,944 raw combinations over the same nine construction axes. Normal combat construction now requires at least one Main Weapon, one Main Reactor, **and one installed Sensor**. ECM/ECCM remain optional; explicit sensorless configurations remain available only as diagnostic/special-scenario or post-damage states outside the normal legal population.

The resulting legal envelope is:

- 11,776 legal combat builds;
- 2,944 exact-fill builds;
- 6,656 near-fill builds;
- 2,176 underfilled builds;
- 138,674,176 oriented pairings with self; and
- 69,331,200 unordered distinct pairings.

No installed component statistic changes merely because Sensor becomes mandatory.

## Exact same-Space progression lattice

A progression edge connects two legal builds that are identical except for one declared TL1 -> TL2 construction axis and consume the same Installation Space. The v0.14/v0.8 lattice contains **37,184 legal edges** across 12 transitions:

| Transition | Legal edges | Exact-fill edges | Expected advanced-component delta |
|---|---:|---:|---:|
| Kinetic single k1 -> k2 | 2,864 | 672 | 1 |
| Kinetic double k1x2 -> k2x2 | 80 | 64 | 2 |
| Reactor single r1 -> r2 | 5,728 | 1,344 | 1 |
| Reactor double r1x2 -> r2x2 | 160 | 128 | 2 |
| Tactical Computer c1 -> c2 | 5,888 | 1,472 | 1 |
| Sensor s1 -> s2 | 5,888 | 1,472 | 1 |
| Shield sh1 -> sh2 | 3,264 | 1,216 | 1 |
| Armor a1 -> a2 | 5,888 | 1,472 | 1 |
| ECM single ecm1 -> ecm2 | 2,048 | 384 | 1 |
| ECM double ecm1x2 -> ecm2x2 | 1,664 | 512 | 2 |
| ECCM single eccm1 -> eccm2 | 2,048 | 384 | 1 |
| ECCM double eccm1x2 -> eccm2x2 | 1,664 | 512 | 2 |

"Single-axis" means one construction axis changes. A homogeneous double-installation axis can therefore advance two physical components together; the expected advanced-component delta is declared and validated per transition rather than assumed to be +1.

## Stratified exact-edge sample

The complete lattice is stratified by:

1. transition class;
2. weapon family;
3. composition class; and
4. Space-utilization class.

There are **181 populated strata**. Every stratum contains at least eight legal edges, so the bounded CP99 screen deterministically selects the first two sorted edges from each stratum without fragile singleton behavior. That yields **362 logical lower->higher exact-edge pairs**.

The broad CP98 sampler is disabled in CP99, but its shared classification thresholds remain explicit because build and pair metadata still consume them: near-fill starts at **32 Space**, progression distance **1-2** is `near`, equal-low remains capped at **3** advanced components, and information-control distance **1-2** is `near`. These are classification inputs only; they do not re-enable broad population weighting.

This is a causal/marginal screen, not a population-prevalence estimate. CP98's 96-cell broad-population weighting is therefore not imposed on CP99; after making Sensor mandatory only 88 of those historical broad cells remain populated anyway. The accepted CP98 broad screen remains a one-trial regression.

## Adaptive Encounter consumer

Each logical exact-edge pair is exercised with the same range-10 player-information-parity Adaptive Engage consumer validated in CP97/CP98:

1. `EngageAdaptive` / `SideAFirst` / initial range 10;
2. `EngageAdaptive` / `SideBFirst` / initial range 10.

This produces **724 generated variants**. Mover order remains an explicit diagnostic dimension and is not averaged away or promoted into a production initiative rule.

## Bounded CP99 study

The CP99 primary screen uses:

- 362 exact-edge logical pairs;
- 2 mirrored mover orders;
- 724 variants;
- combat seed 990100; and
- 250 trials per variant = **181,000 substantive trials**.

Regression/smoke execution remains bounded:

- accepted CP96 generated consumer: 1,440 one-trial variants;
- accepted CP97 Adaptive Engage: 36 one-trial variants;
- accepted CP98 broad Adaptive Engage: 960 one-trial variants;
- CP99 exact-edge full-pipeline smoke: 724 one-trial variants.

Default total stochastic executions are therefore **184,160**.

## Release/preflight rules

1. Generator and actual consumer must agree on study ID, 724 variants, 362 comparison groups, range-10 Engage geometry, mover-order mirrors, catalogs, AI doctrine, and runtime IDs.
2. The legal envelope, 37,184-edge lattice, 12 transition counts, expected advanced-component deltas, 181 strata, and deterministic 362-pair sample must be independently reproducible from v0.8.
3. Every normal CP99 generated build must contain a Sensor; sensorless states remain explicit diagnostics only.
4. Exact-edge pairs must preserve physical Space and differ only on their declared construction axis. The expected advanced-component delta is 1 or 2 as declared by the transition.
5. CP99 exact-edge generation must not invoke CP98's broad 96-cell population-weight accounting path.
6. Actual-consumer preflight and a one-trial 724-variant smoke must run before substantive Monte Carlo.
7. Shared/global telemetry, report routing, schemas, checkpoint accounting, and study-family helpers must bind the same CP99 study ID.
8. New C# mutation surfaces receive compiler-class static checks for known nullable/type-binding/local-shadowing failures before packaging; authoritative native warnings-as-errors build remains mandatory.
9. Outcome statistics are review evidence. No automatic technology promotion, TL3 invention, or initiative change is permitted.

## Interpretation

The exact-edge study is intended to distinguish subsystem upgrades that are broadly useful, matchup-dependent, enabling/supportive, weak under current opportunity costs, or unusually dominant. Mover-order sensitivity must be reported alongside marginal outcomes because CP98 showed that initiative geometry can exceed modest technology advantages. The result is evidence for the next design discussion, not an automated balance decision.
