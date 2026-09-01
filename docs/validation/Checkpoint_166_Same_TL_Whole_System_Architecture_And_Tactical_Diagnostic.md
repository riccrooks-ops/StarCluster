# Checkpoint 166 - Same-TL Whole-System Architecture and Tactical Diagnostic

## Purpose

Checkpoint 166 is the first whole-system balance checkpoint after CP165 CR3 reconciled the active design authorities. It begins the agreed progression:

1. pure same-TL ship combat;
2. pure different-TL ship combat after same-TL balance/tactics closure;
3. hybrid-TL ships after pure-TL progression is understood.

CP166 is a diagnostic checkpoint. It does not tune numerical values and does not promote research values into the production runtime.

## Accepted base and authority boundary

CP165 CR3 is the accepted native base. CP166 hash-locks the current Concept, current TL Tree, current working numerical baseline, current Space/AUX catalogs, and current Combat System Reference. The frozen production/PF4 compatibility sources remain compatibility evidence rather than the combat population authority for CP166.

The combat adapter constructs an in-memory `CandidateMatrix` from `current_working_technology_baseline.json`. It adds only neutral compatibility fields required by older kernel object shapes; those fields do not modify the current authority files and are not consulted by DEF/RES resolution.

## Same-TL population

Each combat pairs ships whose installed executable components use the same TL as the ship. Cross-TL opponents and mixed-TL component ships are excluded.

The legal executable census preserves both:

- the player/base-cruiser envelope (one Main, one Main Reactor, Shield present); and
- the broad legal envelope, including shieldless specialists and legal multiple-Main/multiple-Reactor designs.

The Stage-A census uses outcome-distinct intact-state architecture skeletons. APU and explicitly stackable magazine multiplicity are enumerated analytically rather than exploding each skeleton into duplicate rows. The exact population is:

- 101,207 architecture skeletons;
- 635,428 effect-distinct APU/magazine stack combinations;
- 252 representative builds, 28 at each TL.

Representatives are deterministic and deliberately cover weapon families, PDS families, EW, shield/no-shield, multiple Main/Reactors, APU extremes, magazine endurance, and every currently available selected binary AUX identity. To prevent family-level sampling bias, TL2-TL9 use exactly seven Kinetic, seven Energy, seven GP Missile, and seven Swarmer representatives; TL1 uses 10 Kinetic, 9 Energy, and 9 GP Missile representatives because Swarmer is unavailable.

## Combat response surface

For each TL, the 28 representatives form 406 unordered-with-replacement pair groups. Each group executes four side/order-controlled variants:

- build 1 vs build 2, Side A moves first;
- build 1 vs build 2, Side B moves first;
- build 2 vs build 1, Side A moves first;
- build 2 vs build 1, Side B moves first.

This produces 1,624 variants per TL and 14,616 variants across TL1-TL9. At 200 trials per variant, the substantive same-TL response surface contains 2,923,200 combats.

The side/order mirror pairs are a strict acceptance gate. Balance outcomes are not.

## Tactical-power monotonicity diagnostic

CP164 exposed a tactical-policy discontinuity in which additional available TP could cause the allocator to activate a harmful package. CP166 therefore carries four tactical sentinel roles per TL and gives the otherwise identical ship +1 or +2 free diagnostic TP. Side/order controls are retained.

This adds:

- 288 monotonicity variants;
- 250 trials per variant;
- 72,000 combats.

A boosted decisive share below 45 percent is reported as an allocator-regression watch, not interpreted as evidence that physical reactor capacity is harmful.

## Total diagnostic scale

- same-TL response: 2,923,200 combats;
- power-monotonicity diagnostic: 72,000 combats;
- total: **2,995,200 combat trials**.

The native run is TL-batched and resumable.

## Executable whole-system coverage

CP166 executes the currently integrated intact-system interactions together:

- current TL1-TL9 numerical profiles;
- DEF/RES Shield/Armor resolution;
- Kinetic, Energy, GP Missile, and Swarmer Main Weapons where available;
- direct-fire Firm/Approximate/extended-range modifiers;
- finite-map movement, range, fuel, Sensors, ECM/ECCM, and adaptive engagement;
- one executable Kinetic/Energy/AMM PDS installation/family per build;
- Operational Main Reactor TP, including legal multiple same-TL Reactors;
- Operational APU TP and legal stack counts constrained by Space;
- Shield Battery, Shield Booster, Shield Hardener, Ablative Armor, Energized Armor, Crystalline Armor, Field Stabilizer, and magazines;
- prepared Repair Kits and the Repair Drone Bay's additional kit complement;
- current hull Damage Control.

## Explicit coverage gaps

CP166 does not invent mechanics that are not yet represented by the validated full-map kernel. The following current-design areas are reported as deferred integration rather than approximated:

- live Main Reactor Operational/Degraded/Emergency component-state transitions;
- APU component damage and distributed resilience;
- Repair Drone distinct-target component repair action;
- mixed-family multiple Main Weapon packages on one ship;
- multiple simultaneous PDS installations/families and their shared reaction-capacity semantics;
- intact-state redundant ECM/ECCM/PDS copies where redundancy matters only after component damage;
- repeated AUX stacking when the current catalog does not explicitly define multiplicity.

These gaps are part of the same-TL integration program. CP166 first maps the current intact-system response surface so later component-state/multi-package integration has a clean reference point.

## Diagnostics and interpretation

The merged outputs include pair outcomes, build performance, weapon-family matchups, feature summaries, power monotonicity, symmetry audits, execution coverage, and tactical watch rows.

Watches include:

- representative decisive shares above 70 percent or below 30 percent;
- extra-power outcome regression;
- PDS TP consumption without a Missile threat;
- sole-Main defensive diversion without hull risk;
- repeated weapon-power shortfall;
- unresolved rates above 5 percent.

These are research signals. They do not fail native acceptance and do not authorize numerical changes. The next checkpoint is chosen only after the CP166 results are assessed and tactical-policy problems are separated from design-balance problems.

## Acceptance intent

RepositoryOnly validates the accepted base, current authority hashes, full regression stack, exact population/plan, static census, and live smoke path. The substantive run then executes/resumes TL1-TL9 batches, merges the response surface, enforces zero combat errors and exact side/order symmetry, and packages all telemetry.

No production promotion occurs in CP166.
