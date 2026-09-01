# Same-TL Build Ecology Architecture v0.1

## Purpose

Checkpoint 111 adds a reusable build-level combat ecology consumer for Star Cluster. Its first job is instrumentation and consumer validation, not numerical promotion. The consumer evaluates same-Technology-Level ship designs in a bounded tactical environment while retaining enough telemetry to explain why a result occurred.

The architecture is intentionally layered:

1. **Primary same-TL frontier population.** This is the only population with inference weight in CP111.
2. **Zero-weight deterministic mechanic probes.** These prove telemetry paths that the primary doctrine does not intentionally exercise, especially risky overload modes.
3. **Future mixed-TL/legacy overlay.** Registered but not executed in CP111. It remains separate so it cannot contaminate same-TL inference.

## Damage-model scope

CP111 uses `layered_defense_hull_only` combat damage. The Python ecology consumer resolves Shield Armor/Shield Capacity, Armor Protection/Armor Integrity, and Hull damage. It does **not** invoke the repository's C# internal-damage track, subsystem critical selection, or component condition transitions.

This is deliberate. The C# repository retains the internal-damage architecture and historical calibration assets, but they require a separate parity/integration pass before they may influence Python ecology outcomes. Every CP111 result therefore carries `internalDamageCriticalsSimulated=false`.

## Exact-fill construction

A player would not normally leave Installation Space unused. Every CP111 primary build therefore fills the selected Hull capacity exactly.

When the current numerical matrix does not yet provide enough executable combat/support components to use all Space, the harness records the remainder as **mission AUX Space** in 1-Space accounting units. Mission AUX Space has zero tactical effect in CP111. It represents plausible laboratories, medical support, fabrication, logistics, cargo, hangar, mining, and other not-yet-numerical support installations; it is not a new game component.

This convention preserves realistic build behavior without inventing combat effects. The amount of mission AUX Space is itself an integration diagnostic and must be reported.

## Primary population

Each TL from 1 through 9 contains 12 exact-fill frontier builds:

- three Main Weapon families: Kinetic, Energy, Missile;
- four archetypes per family: balanced, dual-main, dual-reactor, and a family specialist.

Family specialists are deliberately distinct:

- Kinetic: EW specialist;
- Energy: defense specialist with Energy PDS and, from TL3, Shield Hardener where legal;
- Missile: missile-defense specialist with AMM PDS and, from TL3, Shield Hardener where legal.

All installed primary combat technologies in this population use the current population TL. Legacy/mixed-era installations belong in the later zero-weight overlay.

For 12 builds at a TL there are 66 unordered pairings. Both movement orders are mirrored, producing 132 variants/TL, 594 movement-neutral bundles, and 1,188 variants across TL1-TL9.

## Geometry and movement

The first pass uses the accepted radius-5 tactical hex map and the canonical opposite-edge axial lane: Side A at (-5,0), Side B at (5,0).

Before contact, ships move one hex toward map center using observer-safe information. After contact, physical/preferred weapon range is not treated as attack eligibility. If the prior combat track is not Firm and no demonstrated standoff is being preserved, the ship continues closing on later Movement decisions rather than holding forever at a nominal preferred range.

Movement-order mirrors are mandatory. Movement distance, fuel cost, map-boundary blocks, range changes, minimum range, and track-driven closure are instrumented separately.

CP111 carries forward the accepted +1 same-hex Burn-through Resistance geometry contribution at every TL as a baseline control. It does not introduce any higher-TL burn-through scaling.

## PDS timing

Known Missile-family opposition is sufficient to preserve planned PDS readiness even before an inbound missile exists, matching the accepted C# doctrine. This is required because fast one-turn missile flights can otherwise reach the terminal-defense window on the launch turn before PDS power is reserved.

Terminal PDS still resolves before missile terminal guidance/damage, using the accepted local terminal-defense model.

## Instrumentation contract

The ecology consumer records, at minimum:

- movement hexes, movement fuel, map-boundary blocks, range changes, track-driven closure, and minimum range;
- passive/active sensor use and Firm/Approximate/No-track time;
- ECM-active turns, ECCM-active turns, ECM downgrades, ECCM restorations, and same-hex burn-through preservation;
- Tactical Power available/spent by Sensor, ECM, ECCM, PDS, weapons, Shield recharge, and Shield Hardener;
- Tactical Power shortfalls by major package;
- Reactor overload requests/activations, unlocked TP, and maximum Strain;
- Shield recharge opportunities, denied recharge, and restored capacity;
- direct shots/hits and direct damage;
- missile launches, terminal arrivals, guidance attempts, hits, and damage;
- PDS attempts/intercepts;
- raw damage and prevention/absorption through Shield Armor, Shields, Armor Protection, Armor Integrity, and Hull.

The primary ecology doctrine intentionally does not use risky Sensor, ECM, ECCM, or STL overload. Five deterministic zero-weight Overload-I probes validate those paths, including Reactor overload. Probe results never contribute population weight.

## Interpretation discipline

CP111 has no target win rate and no automatic promotion. Same-TL win/loss results are diagnostic evidence.

Signals worth reviewing include dominant or weak builds, hard counters, family matchup structure, movement-order swing, unresolved rates, Tactical Power pressure, EW denial/restoration, PDS utilization, overload dependence, layer-by-layer damage, and residual mission-AUX Space.

A strong or weak build is not automatically a balance problem. Before numerical changes, distinguish:

- component math from doctrine quality;
- weapon effect from movement/track eligibility;
- real build advantage from movement-order sequencing;
- combat specialization from opportunity cost;
- a complete combat package from missing not-yet-numerical mission/AUX consumers.

## Expansion path

After CP111 instrumentation is native-validated, expand the design-space laboratory in separate layers:

1. larger same-TL samples and additional archetypes/build-neighbor perturbations;
2. off-axis/system-map geometry populations;
3. doctrine alternatives where hardware can support more than one sensible policy;
4. mixed-TL/legacy-component overlays with zero weight relative to the fixed-TL baseline unless explicitly promoted into a later inference design;
5. internal-damage/critical integration only after deterministic C#/Python parity for that consumer is established.
