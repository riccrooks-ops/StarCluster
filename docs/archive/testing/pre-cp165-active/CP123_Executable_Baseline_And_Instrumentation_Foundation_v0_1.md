# CP123 Executable Baseline and Instrumentation Foundation v0.1

**Checkpoint:** 124  
**Accepted reference baseline:** CP123  
**Accepted implementation baseline:** CP122 Corrected Replacement 1  
**Balance claim:** none

## Purpose

CP124 turns the accepted CP123 technology reference into a reusable research input without changing production C#/Godot mechanics or C# ScenarioRunner scenario definitions. It is the bridge between “the table we intend to test” and the larger statistical studies that will follow.

## Executable reference catalog

The foundation consumes `technology_numerical_matrix_v0_3.json` directly and exposes all **20 TL1-TL9 profile families / 180 rows**. Historical research studies keep their old matrices for reproducibility; CP124 does not rewrite them.

The Missile consumer now understands CP123's separation of:

- delivery/propulsion;
- guidance/seeker;
- contemporary GP warhead;
- Swarmer Flight.

GP and Swarmer are composed at execution time. A Swarmer remains one Missile Flight counter and one terminal guidance roll, with two internal damage packets and the CP123 bounded PDS-intercept penalty.

## Broad same-TL legal-build sanity envelope

CP124 exhaustively enumerates the baseline component envelope rather than sampling a few hand-built ships. The axes are:

- Kinetic / Energy / Missile Main Weapon;
- one or two Main Weapons;
- one or two Reactors;
- Shield absent/present;
- zero, one, or two ECM installations;
- zero, one, or two ECCM installations;
- no PDS, Kinetic PDS, Energy PDS, or AMM PDS;
- Shield Hardener when available and a Shield is installed;
- GP or Swarmer Missile Flight when available.

STL, FTL, Computer, Sensor, Hull and Armor are mandatory same-TL baseline components. Duplicate ECM/ECCM consumes Space but never adds ratings. Any residual Hull Installation Space is filled explicitly as zero-tactical-effect mission/AUX capacity.

The resulting foundation contains **14,112 raw combinations and 9,427 legal builds**:

| TL | Legal builds | Exact combat fill | Near fill | Mission/AUX fill |
|---:|---:|---:|---:|---:|
| 1 | 207 | 42 | 75 | 90 |
| 2 | 276 | 56 | 100 | 120 |
| 3 | 616 | 124 | 228 | 264 |
| 4 | 736 | 120 | 248 | 368 |
| 5 | 864 | 128 | 244 | 492 |
| 6 | 1,544 | 80 | 256 | 1,208 |
| 7 | 1,728 | 0 | 48 | 1,680 |
| 8 | 1,728 | 0 | 0 | 1,728 |
| 9 | 1,728 | 0 | 0 | 1,728 |

The large late-TL mission/AUX residual is a **diagnostic**, not a failure. It reflects growing Hull Space combined with an intentionally incomplete numerical catalog for mission/logistics/AUX competition. Future ecology work should either populate those consumers or continue carrying the residual explicitly rather than silently treating it as empty Space.

## Power sanity

The build catalog reports operational Reactor TP, a reproducible nominal simultaneous combat demand, optional Shield-recharge demand, and resulting margins. Negative nominal margins are not illegal builds; they are resource-pressure diagnostics.

The envelope contains some nominal shortfall builds at TL1-TL3, none from TL4 onward, and increasingly large late-TL margins. This is not a Reactor rebalance conclusion. It is a useful feed for the next studies, especially because CP110 already warned that late-TL dual-Reactor feasibility rises sharply as currently unmodeled consumers remain absent.

## Pipeline smoke

A **70-variant / 70-trial zero-weight smoke** exercises both movement-order mirrors for:

- Kinetic vs Energy at TL1-TL9;
- Energy vs Kinetic at TL1-TL9;
- GP Missile vs AMM-equipped defense at TL1-TL9;
- Swarmer vs AMM-equipped defense at TL2-TL9.

The smoke is an execution/instrumentation gate only. Win rates from one trial have no design weight.

## Instrumentation acceptance gate

`Telemetry_Instrumentation_Contract_v0_1.md/json` makes raw telemetry correctness blocking. CP124 adds explicit raw fields for:

- direct-fire and Missile-launch eligibility opportunities;
- damage packet count;
- Shield penetration bypass contribution;
- Armor penetration bypass contribution;
- Damage Control attempts, successes, and Hull restored.

Existing telemetry continues to cover movement/fuel, Sensor/EW, Tactical Power, overload, direct fire, Missile terminal flow, PDS, Shield/Armor/Hull damage, and related current mechanics.

Nine deterministic probes must pass. They validate damage-layer arithmetic against an independent oracle, split Missile composition, Swarmer packet shape, Damage Control yields, EW redundancy, Missile telemetry ownership, and telemetry-schema completeness.

## Explicit limits

CP124 does not add internal critical/subsystem damage to the Python research consumer. It also does not claim the Python ETA Missile travel model reproduces the C# moving-target range-exhaustion mechanic. Damage Control is represented and instrumented as a reference consumer but is not scheduled into the 70-trial combat smoke. Larger studies must keep those boundaries explicit unless a later parity-validated consumer expands them.

## Next-step intent

If CP124 passes native acceptance, the project should stop creating instrumentation-only checkpoints. The next work should use this foundation for larger same-TL and then mixed-/cross-TL studies, with sample sizes chosen for statistical usefulness and with the CP124 build/telemetry schema preserved as the analytical spine.
