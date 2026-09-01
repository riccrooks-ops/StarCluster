# CP129 Whole-Ladder Pure-TL Sensitivity and Subsystem Attribution Study v0.1

**Checkpoint:** 129  
**Accepted baseline:** CP128  
**Accepted main-subsystem stabilization evidence:** CP127 Corrected Replacement 1  
**Accepted production implementation baseline:** CP122 Corrected Replacement 1

## Purpose

CP129 resumes the broader pure-TL research phase after CP128 froze the current TL1-TL9 main-subsystem numerical reference. It does **not** reopen values in advance, introduce legal mixed-/legacy-TL ships, or calibrate deferred AUX families.

The study answers four questions:

1. What does the complete current pure-TL ladder look like on the accepted radius-5 System Map after the CP127 stabilization changes?
2. Which **main combat subsystem packages** materially drive each adjacent-TL advantage when composition and construction footprint are held fixed?
3. How much of adjacent progression is associated with optional PDS/Shield-Hardener choices whose detailed AUX progression is still deferred?
4. Which Hull-capacity and main-subsystem Space changes expand the legal build envelope independently of combat-stat improvements?

Balance signals remain review evidence. The checkpoint blocks only on repository/runtime/test integrity, physical symmetry, exact plan/population contracts, accepted CP127 control replication, variant/trial counts, and zero trial errors.

## Lane A — full-map whole-ladder control

CP129 reuses the accepted CP125 deterministic all-build/every-opponent-TL pairing design over the **current CP128 matrix** and executes it through the accepted CP126/CP127 finite radius-5 research consumer.

- 9,427 legal pure-TL builds;
- 45 canonical unordered TL cells / 81 ordered orientations;
- 70,034 base pairings;
- every legal build represented against every opponent TL;
- both side assignments and both movement orders;
- 280,136 variants;
- 100 trials/variant = **28,013,600 engagements**.

The pairing seed is the accepted CP125 seed. The combat master seed is the accepted CP127 seed. Because CP128 is numerically identical to accepted CP127 and the adjacent pairing/task identities are preserved, the eight adjacent-TL aggregate cells must reproduce the accepted CP127 adjacent summary exactly. This is a blocking regression/control gate before new sensitivity interpretation.

Primary outputs include the 9x9 ordered TL matrix, Delta-TL curve, family matchup matrix, canonical pairing outcomes, movement-order summary, and full-map telemetry summaries.

## Lane B — main-only adjacent control

The current legal-build universe includes PDS and Shield Hardener choices even though most AUX/support progression remains deferred. CP129 therefore repeats the adjacent-TL population design on a restricted **main-only control envelope** that excludes only:

- PDS; and
- Shield Hardener.

It retains Kinetic/Energy/Missile main families, GP/Swarmer payload branches, Shields, ECM/ECCM, duplicate Main Weapons, duplicate Reactors, and every stabilized main subsystem.

This lane contains 1,856 legal builds, 1,784 adjacent base pairings, 7,136 variants, and 713,600 engagements at 100 trials/variant. Its purpose is diagnostic: compare progression with and without the two deferred optional defensive/support choices. It does not declare those AUX families balanced or unbalanced.

## Lane C — ladder-wide main-subsystem performance holdbacks

Every adjacent TL boundary has an exact matched-composition population. CP129 runs all **7,699** matched adjacent pairs through eleven conditions: current baseline plus ten one-step holdbacks.

For each adjacent boundary, only that boundary's **higher-TL row** in the selected package uses the immediately lower-TL combat-performance fields while preserving the higher-TL ship's:

- component/branch selection;
- Hull Installation Space capacity;
- component Space footprint;
- branch availability; and
- overall composition.

These are counterfactual causal probes, **not legal mixed-TL ship designs**. Full-map physical IDs, scenario IDs, master seed, and trial indices are held constant across conditions, so the accepted physical-entity RNG system provides common random numbers.

The ten packages are:

1. Hull durability;
2. Armor;
3. Reactor performance/power;
4. STL tactical performance;
5. Tactical Computer;
6. Sensors;
7. ECM;
8. ECCM;
9. Shields; and
10. the installed Main Offense package (Kinetic Main, Energy Main, or Missile delivery/guidance/payload as applicable).

Damage Control is not scheduled in these tactical encounters and FTL is strategic, so neither receives a combat holdback. Their lack of a CP129 combat sensitivity result must not be interpreted as zero design value.

Each condition executes 30,796 variants at 50 trials/variant. Eleven conditions produce **338,756 variants / 16,937,800 engagements**. Because holdbacks are marginal counterfactuals around the same complete higher-TL package, their effects are not assumed to add linearly to 100% of the technology advantage.

Analysis reports each package by TL boundary and by weapon-family stratum, including change in higher-TL conditional win rate, unresolved rate, and mean duration. Conditions with no actual field change at a boundary are expected to reproduce baseline exactly under common random numbers.

## Lane D — deterministic construction-envelope sensitivity

Combat-stat holdbacks deliberately exclude `space` and Hull `capacity`, because changing those fields can make the fixed higher-TL composition illegal and would mix construction effects into combat performance.

CP129 therefore separately re-enumerates the pure-TL legal-build universe after one-step counterfactual holdbacks for:

- Hull capacity;
- Reactor Space;
- STL Space;
- FTL Space;
- Tactical Computer Space;
- Sensor Space;
- Shield Space; and
- Main Weapon / Missile-delivery Space.

This lane is deterministic and has no Monte Carlo workload. It reports the change in legal-build count and composition availability at each TL. AUX/PDS/Shield-Hardener Space progression is explicitly outside this attribution pass.

## Workload

The native pipeline smoke executes one trial for every planned combat variant:

- whole-ladder control: 280,136;
- main-only adjacent control: 7,136;
- matched sensitivity: 338,756;
- **total smoke: 626,028 trials**.

The substantive workload is:

- 28,013,600 whole-ladder engagements;
- 713,600 main-only adjacent engagements;
- 16,937,800 matched sensitivity engagements;
- **45,665,000 total engagements**.

Default native parallelism is `Jobs=24`. Corrected Replacement 1 exposes this as wrapper parameter `-Jobs <1-61>`; changing it changes only ProcessPool concurrency and is recorded in acceptance evidence, not study semantics, seeds, variant identities, or trial counts.

## Interpretation boundary

CP129 is intended to tell us where the frozen ladder is sensitive, not to force every TL transition to the same win rate. A main-subsystem value should be reopened only if the broader evidence shows a concrete pathology: an unexpectedly dominant marginal package, a reversed or dead progression region, a systemic information/power/defense lock, or another causal result that cannot reasonably be explained by intended family/era identity.

If the frozen main table remains coherent, the next research phase may proceed to legal mixed-/legacy-TL ship ecology. Most AUX/support-component numerical calibration remains a later dedicated phase.

## Result-retention policy

Raw per-variant CSVs are transient consumer output. After the substantive analyses and pairing/summary tables are written and all gates are evaluated, CP129 removes those raw CSVs and transition-specific derived matrices from the native-results handoff. The study definition, seeds, repository state, pair/task plans, aggregate pairing outcomes, summaries, and native acceptance record remain sufficient to reproduce the run while avoiding a new evidence-archive size problem.
