# Checkpoint 111 Same-TL Build Ecology Instrumentation Report v1

## Executive assessment

Checkpoint 111 establishes a reusable, instrumented same-TL combat ecology consumer around the complete CP109 candidate numerical matrix and the CP110 retained Reactor candidates. The checkpoint is deliberately an **instrumentation and simulation-environment expansion**, not a technology-calibration or production-promotion pass.

The finalized local bounded pass executes 108 exact-fill frontier builds, 594 unordered same-TL pairings, both movement orders for every pairing, 1,188 variants, and 118,800 engagements at 100 trials/variant. The native acceptance workload is configured for 1,000 trials/variant, or 1,188,000 engagements.

All blocking instrumentation gates pass. No CP109/CP110 candidate number is changed or promoted by CP111.

The finalized 100-trial/variant authoring study was rerun after the last consumer fixes. All 11 deterministic CSV/JSONL evidence outputs reproduced byte-for-byte, and `analysis.json` reproduced semantically with only elapsed runtime excluded from comparison.

## Damage scope confirmed

The current Python research combat consumer is **not** using Star Cluster's internal critical/subsystem damage model. CP111 resolves:

1. Shield Armor prevention;
2. Shield Capacity absorption;
3. Armor Protection prevention;
4. Armor Integrity / Armor Protection degradation;
5. Hull damage and terminal Hull destruction.

Internal track markers, subsystem hit selection, component degradation/disable/destruction, magazine criticals, and related internal-damage effects are not simulated. CP111 explicitly labels every result `layered_defense_hull_only` and `internalDamageCriticalsSimulated=false`.

The internal-damage model remains in the C# repository and can be integrated later as a separately parity-validated consumer.

## Construction population

The primary population contains 12 builds per TL from TL1 through TL9: three Main Weapon families by four archetypes. Every build has `free_space=0`.

Residual capacity that cannot yet be represented by numerically executable support systems is recorded as zero-combat-effect mission AUX Space. Average mission AUX allocation grows from about 0.9 Space at TL1-TL2 to 20.2 Space at TL9. This is not a combat benefit. It is a direct warning that late-TL ecology cannot yet evaluate the opportunity cost/value of the many mission/logistics/AUX systems identified by the Technology Storyboard.

Mixed-TL construction is registered as a future population with zero inference weight and is not executed in CP111, so it cannot contaminate the fixed-TL baseline.

## Consumer defects found and corrected during instrumentation

The instrumentation-first workflow found two sequencing/doctrine defects before substantive interpretation:

### Fast missile terminal-defense readiness

High-TL one-turn missile flights could reach terminal resolution on the launch turn before the defending ship had reserved PDS power. The accepted C# doctrine already treats a known Missile-family opponent as sufficient reason to preserve planned PDS. The Python ecology consumer now matches that rule. Deterministic TL3/TL5 probes exercise PDS attempts and interceptions against fast missile arrivals.

### Track-ineligible range holding

Some ECM-heavy builds could reach contact, hold at a nominal preferred range with only an Approximate track, and then exchange no fire for the rest of the engagement. This was the same class of confounder found in earlier track-aware movement studies: physical/preferred range is not attack eligibility.

The ecology movement doctrine now continues closing after contact when the previous track is not Firm and no demonstrated standoff is being preserved. `track_driven_closure_hexes` makes that behavior directly observable.

CP111 also carries forward the accepted +1 same-hex Burn-through Resistance geometry contribution as a constant baseline. No speculative higher-TL burn-through progression is added.

## Instrumentation coverage

The final bounded pass exercises the principal current-mechanic paths. Aggregate mean-sum telemetry includes approximately:

- 12,890 direct shots and 8,849 direct hits;
- 7,348 missile launches, 7,256 terminal arrivals, 6,296 guidance attempts, and 3,951 missile hits;
- 2,604 PDS attempts and 961 interceptions;
- 13,592 ECM-active turns and 10,807 ECCM-active turns;
- 628 ECM downgrade events and 3,308 ECCM restoration events;
- 466 same-hex burn-through preservation events;
- 4,592 track-driven closure hexes;
- 293 weapon-power shortfall events;
- real Shield recharge and Shield Hardener Tactical Power expenditure;
- 28 useful Reactor-overload activations/unlocked TP events;
- damage separately attributed to direct and missile sources and through every simulated defense layer.

The primary doctrine intentionally does not activate risky STL, Sensor, ECM, or ECCM overload. Five zero-weight deterministic probes validate all supported Overload-I paths:

- STL: Move 1 -> 2, +1 TP, +2 overload fuel, +1 Strain;
- Active Sensor: Firm/Approx 3/4 -> 4/5, accepted TL1 overload total 3 TP, +1 Strain;
- ECM: rating 1 -> 2, 1 -> 2 TP, +1 Strain;
- ECCM: rating 1 -> 2, 1 -> 2 TP, +1 Strain, with Firm restoration demonstrated against ECM2/DR0;
- Reactor: available Tactical Power 5 -> 6, +1 Strain.

All five probes pass.

## Local same-TL review signals

These are **review signals only** from the 100-trial/variant authoring pass. The native 1,000-trial/variant run should be used to determine whether they persist.

### Energy defense specialists

Energy defense-specialist builds are unusually robust through much of the middle/late ladder. Their mean conditional win rates in this bounded population are approximately 87.0% at TL3, 91.5% at TL4, 93.3% at TL5, 93.9% at TL6, 86.0% at TL7, and 92.2% at TL8.

At the family level, Energy also shows strong cross-family performance against Kinetic from TL4 through TL8 (roughly 71.6%-81.7% in the local pass). This may reflect weapon/defense interaction, Shield/Hardener value, Energy PDS opportunity cost, doctrine, or the incompleteness of late support/AUX consumers. CP111 does not diagnose it as a numerical defect yet.

### Dual-Reactor combat archetypes

Dual-Reactor archetypes are consistently weak in the current combat-only population. That is unsurprising: the second Reactor consumes Space while the first-pass ecology has relatively few numerically executable high-demand support systems that can exploit the extra power. At high TL the same builds simultaneously carry large zero-effect mission-AUX allocations.

This reinforces CP110's existing integration watch rather than contradicting it. Do not nerf or buff Reactors from CP111 dual-Reactor win rates.

### Kinetic EW specialist

The Kinetic EW specialist is another weak mid/high-TL archetype in this first population, particularly TL6-TL8. Because EW/track state, Tactical Power, and weapon activity are now directly instrumented, the native results can distinguish whether the problem is excessive EW opportunity cost, doctrine, or weapon-family matchup structure before any retuning.

### Movement-order sensitivity

The local pass flags 31/594 movement-neutral bundles with at least a 15 percentage-point mirrored-order swing. The strongest examples cluster around Kinetic/Missile interactions at TL7, with one TL7 dual-main pairing near a 69-point swing. TL7's average order swing is also visibly higher than most tiers.

This remains a sequencing/geometry review target. CP111 uses one canonical axial geometry, so movement-order results must not be generalized to the whole tactical map until off-axis/system-map geometry populations are added.

### Unresolved combat

The finalized movement/EW fixes eliminate the earlier permanent zero-offense deadlocks. Mean unresolved rate is zero through TL3 and remains low thereafter in the bounded pass, rising only to roughly 1%-1.5% at TL7-TL9. There are no variants that are both 100% unresolved and produce zero offense in the final smoke/authoring evidence.

## What CP111 does not prove

CP111 does not calibrate weapon families, defenses, EW, movement, or Reactors. It does not establish a target same-TL win rate. It does not model internal damage. It does not test mixed-TL populations. It does not test the full system-map geometry envelope. It does not numerically represent the growing late-TL mission/AUX catalog.

Accordingly, dominance/weakness signals are hypotheses for later controlled work, not release gates.

## Recommendation

Native-validate the instrumentation checkpoint with the full 1,188,000-engagement same-TL run. If the telemetry and consumer gates reproduce cleanly, accept CP111 as a simulation-environment baseline.

After acceptance, use the native output to choose the next evidence-driven expansion. The strongest candidates are:

1. build-neighbor/one-decision perturbation tests around the Energy defense and Kinetic EW signals;
2. wider same-TL stratified build populations that numerically consume more of the available late-TL Space;
3. off-axis/system-map geometry populations focused on movement-order-sensitive Kinetic/Missile matchups;
4. a separately weighted mixed-TL/legacy overlay;
5. later internal-damage integration after deterministic parity exists.

No candidate numerical value should be promoted from CP111 alone.
