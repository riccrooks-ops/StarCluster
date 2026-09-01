# Technology Calibration and Simulation Architecture

## Boundary

Technology calibration belongs in the engine-independent simulation host. The
Godot client presents and commands authoritative state but does not define TL
conversion formulas or statistical experiments.

The dependency direction remains:

```text
StarCluster.Core
    ^
    |-- StarCluster.Game            player-facing host
    `-- StarCluster.ScenarioRunner  deterministic and Monte Carlo host
```

## Data before promotion

A calibration catalog is intentionally provisional. It may assign explicit TL
1-9 component values and interaction conversions for experiments without
silently making them permanent game rules. Values are promoted into the Concept
and production component definitions only after representative studies are
reviewed.

Component TL, not a universal ship-TL modifier, supplies:

- ranges and movement ratings;
- Guidance Computer and seeker percentages;
- ECM/ECCM strengths;
- PDS conversion inputs;
- retention, capacity, power, cost, and durability in later systems.

## Study controls

A useful study changes the intended variables and holds unrelated gates open.
Checkpoint 20 therefore raises fixture sensor ranges so every variant retains a
legitimate terminal cue. It does not claim that every real ship receives those
ranges. Detection-range and terminal-resolution studies should remain separate
until a combined encounter study is explicitly requested.

## Reproducibility

Ordinary Monte Carlo batches derive independent interception and terminal
streams from the master seed, materialized variant ID, trial index, and stream
ID. Calibration studies may instead provide one shared random-seed namespace
for all variants. This common-random-numbers mode gives every variant the same
trial quantiles while preserving each materialized scenario and variant as a
separate hashed run.

Materialized scenario, random-seed namespace, runner assembly, and Core assembly
identity are stored with each batch. Worker count and resume boundaries cannot
change canonical results. Paired marginal reports verify a SHA-256 fingerprint
of the trial stream identities before comparing outcomes.

## Reporting

Calibration should report probabilities per launched Missile Flight rather than
only conditional percentages. Important outputs include:

- entry and pre-attack interception;
- terminal acquisition;
- attack resolution;
- effective hit per launch;
- search and fuel behavior;
- component/TL inputs used to produce the variant; and
- adjacent-TL marginal effects.

Per-variant point estimates retain Wilson 95% intervals. Adjacent-TL marginal
comparisons use paired effective-hit outcomes under common random numbers. The
runner reports discordant-pair counts, a paired-difference interval, and a
continuity-corrected McNemar p-value. Holm step-down correction controls the
familywise error rate across the complete marginal matrix. A comparison fails
only when the adjusted result opposes the analytical direction by more than the
configured practical-effect threshold.

## Future extension

The same architecture should later support:

- mixed component TL inside one Missile Flight;
- pursuit, overshoot, range, and speed matrices;
- multi-flight volleys and finite PDS Reaction Capacity;
- tactical power and damage studies;
- cost-effectiveness frontiers; and
- adaptive trial counts near balance thresholds.

## Full-flight pursuit studies

Checkpoint 21 materializes complete multi-turn pursuits rather than assuming a
terminal opportunity. The study begins from normal initialized state with one
pre-existing Missile Flight and then alternates target Movement with one normal
missile action per turn. The same Core services therefore determine target-track
updates, datalink delivery or loss, retained-report aging, local-sensor
observations, guidance arbitration, route recomputation, range expenditure,
Search/Wait, terminal PDS, and terminal resolution.

The controlled matrix separates four inputs:

- Missile Flight capability package;
- missile TL, which provisionally supplies speed, range, guidance, sensing, and
  seeker values;
- target propulsion TL, which supplies only the scripted movement allowance;
  and
- live versus deliberately occluded launcher datalink geometry.

The target ECM and standard-PDS TL remain fixed in this first pursuit study.
Target movement policies are deterministic and versioned. Common random numbers
remain appropriate because the stochastic interception and terminal streams are
unchanged across paired geometry/TL variants.

Full-flight reports distinguish reaching a terminal opportunity from producing
an effective hit. They also preserve range exhaustion, self-destruction, dud, miss, unresolved-horizon,
Search/Wait, blocked/expired datalink, fresh/retained/local guidance usage,
active sensor use, route replans, elapsed turns, distance, and fuel. This avoids
mistaking terminal conditional strength for effectiveness per launched Missile
Flight.

## Checkpoint 21a paired full-flight and scheduler contract

Full-flight calibration uses authoritative terminal-opportunity records rather
than treating a diagnostic event as the primary metric. A trial is invalid if
terminal interception, acquisition, or attack occurs without an opportunity,
or if authoritative and diagnostic opportunity counts differ.

Study horizons are operational safety caps derived from missile endurance and
track-retention inputs. Reaching that cap while still active is an explicit
operational timeout; a nonterminal trial before the cap is unexplained and
fails the variant. This distinction prevents a fixed short horizon from being
mistaken for a gameplay outcome.

Full-flight parallelism is variant-level and bounded to 24 workers. Each
variant runs its trial loop with one inner worker. Canonical output is assembled
in stable variant order after worker completion, while execution timing and
peak-worker telemetry are written to separate noncanonical files. The same
study must retain identical canonical hashes at one and 24 workers.


## Dedicated full-flight variant scheduler

Full-flight studies parallelize across independent variants, not within every
variant simultaneously. `--jobs 24` creates at most 24 dedicated variant
workers. Each variant executes its trials in one serial inner lane, writes only
to its own output directory, and contributes to canonically sorted aggregation
after all workers finish. This avoids nested oversubscription and preserves
worker-independent seeds and hashes.

A small scheduler-proof corpus tests one-worker and 24-worker execution with
gameplay statistical gates disabled. The full calibration runs once at the
selected 24-worker count. Timing, peak-worker, and throughput telemetry are
noncanonical.

## Mechanical and statistical failure separation

Every variant reports trial errors, datalink semantic-contract failures,
terminal-opportunity invariant failures, and unexplained unresolved outcomes
independently. Any mechanical failure rejects the variant. Directional
statistical acceptance is applied only where the modeled trajectory supports a
monotonic expectation. Crossing-weave and turnback datalink comparisons remain
descriptive because repeated current-position pursuit is not a predictive
intercept law.

## Global trial-block execution

Full-flight studies use one deterministic global work plan. Each work item owns
one variant index and a contiguous trial-index range. A bounded queue feeds up
to 24 dedicated workers; no worker starts another parallel loop. The result
matrix is pre-indexed, so completion order cannot affect placement, aggregation,
common-random-number pairing, or canonical hashes.

Compute workers do not create directories, serialize JSON, aggregate metrics,
or write journals. Those operations occur after compute completion in stable
variant order. This separates CPU scaling from output contention and keeps
filesystem activity out of the hot path.

The ScenarioRunner executable uses server GC and reports process CPU time,
effective core utilization, processor/affinity visibility, allocation volume,
and collection counts. A small one-worker versus 24-worker proof must show real
throughput improvement before a large calibration may begin. Worker presence is
not accepted as evidence of parallel speedup by itself.


## Compact Monte Carlo observation path

High-volume studies may suppress human-readable diagnostic event materialization
when they capture the same required observations directly at authoritative Core
service boundaries. This is an observation optimization, not an alternate
simulation. Every trial still constructs independent mutable tactical state.

A prepared execution plan may reuse only immutable parsed inputs and profiles.
Diagnostic and compact modes must produce identical canonical trial outcomes for
the same study, seed namespace, trial index, and random-stream IDs. Accepted
study summary and marginal files serve as behavioral references across
performance-only changes.

## Checkpoint 23 game-wide player-technology foundation

Checkpoint 23 established the shared player TL 1-9 vocabulary, named standard component catalog, reference-mining ledger, family-level support relationships, and adaptation schema so later combat studies operate inside one coherent technology framework.

- Research categories advance independently.
- One visible Propulsion TL governs distinct FTL and sublight component families.
- Standard components normally depend on no more than two related support categories plus explicit hard capability tags.
- Integrated, Adapted, and Incompatible are installation/operation states, not research locks.
- External references provide questions and patterns only; no proprietary names, exact ladders, tables, numbers, or core mechanics are copied.

## Checkpoint 24 TL1 core-combat calibration foundation

Checkpoint 24 deliberately begins below the previously planned matched TL1/3/5/7/9 cruiser matrix. The first study platform is one stripped TL1 cruiser chassis with one weapon bay and no optional Auxiliary systems. Kinetic, energy, and missile variants differ only by the installed weapon and use identical doctrine, geometry, starting state, and random-stream policy.

This sequence isolates the smallest complete combat loop before higher-TL efficiency, special modes, optional defenses, and differentiated doctrine create confounding interactions.

### Exact provisional data

The test program uses one exact versioned value for every implemented baseline parameter. Ranges remain useful for brainstorming but are not valid executable inputs. Every change must update the baseline version, rationale, scenario expectations, and checkpoint evidence.

Authoritative design inputs are:

- `player_technology/tl1_core_combat_numerical_baseline_v0_1.csv`;
- `player_technology/tl1_core_combat_loadouts_v0_1.csv`;
- `player_technology/tl1_core_combat_test_scenarios_v0_1.csv`;
- `player_technology/TL1_Core_Combat_Test_Plan_v0_1.md`; and
- `player_technology/StarCluster_Player_TL_Framework_Draft_v0_4.xlsx`.

### Controlled study ladder

1. deterministic packet, power, overload, repair, and reset contracts;
2. K/K, E/E, and M/M mirror duels under side-swapped common random numbers;
3. cross-family weapon duels with identical doctrine;
4. one optional defensive subsystem at a time;
5. ECM/ECCM and Active Sensor timing;
6. batteries, capacitors, Auxiliary Reactors, APUs, and overload;
7. component damage, Crew, Marines, Damage Control, Strain, and hazards;
8. movement, Evasive Maneuvering, STL overload, tractors, held interception, pursuit, and retreat;
9. differentiated weapon-family doctrine only after the common doctrine is understood;
10. TL2-TL9 and mixed-TL progression only after the TL1 foundation is stable.

### Relevance-space testing

A component is tested with its intended threat absent, present at ordinary intensity, and emphasized or saturated. The objective is situational viability rather than equal win rates.

Review labels are Dominant, Viable, Niche, Trap, Oppressive, and Redundant. Promotion should favor mostly Viable options and intentional Niche choices while eliminating dominant, oppressive, trap, and redundant designs.

### Metrics beyond win rate

The runner must capture the causal reason for each result, including layer timing, shieldless turns, power by state and phase, unused power, ammunition, fuel, battery and capacitor use, PDS coverage, track changes, overload and Strain, component conditions, Crew casualties, Damage Control, and retreat or mission-kill outcomes.

### Runtime boundary

Checkpoint 24 is documentation and data only. It does not retrofit incomplete Hull, armor, shield, power, Crew, or weapon mechanics into the existing missile-focused runtime. The next implementation pass begins with deterministic Phase A contracts and preserves the accepted Checkpoint 22d mechanical/performance baseline until each new mechanic has an explicit parity and validation lane.

## Revised study order

1. Checkpoint 24: unified post-23a concept, modular schema, exact TL1 baseline, and staged scenario specification.
2. TL1 implementation Phase A: deterministic defense, power, resource, overload, repair, and reset contracts.
3. TL1 implementation Phase B: mirror and cross-family core duels.
4. Incremental TL1 subsystem calibration through PDS, EW, power flexibility, damage/personnel, and movement.
5. Independent Missile Flight subsystem decomposition with a locked bundled-profile parity lane.
6. TL2-TL9 hybrid progression, matched anchors, and mixed-TL stress cases.
7. Promote only evidence-supported values into production component definitions.

## Checkpoint 25 deterministic TL1 Phase A execution

Checkpoint 25 converts the Checkpoint 24 Phase A specification into an engine-independent executable contract without beginning balance calibration.

### Rule ownership

Authoritative mechanics remain in `StarCluster.Core`:

- layered damage and persistent defense state;
- turn-start Shield recharge;
- Tactical Power ledger and held-power earmarks;
- Reactor output, overload, and Strain;
- weapon resource packets;
- charging and Ready-state lifecycle.

`StarCluster.ScenarioRunner/TL1` owns only baseline loading, synthetic fixture materialization, document preflight, expected-subset comparison, output, and corpus orchestration. Godot remains presentation-only.

### Baseline-driven scenario corpus

The runner reads `tl1_core_combat_numerical_baseline_v0_1.csv` at execution time and records its SHA-256 in every scenario summary. Twelve JSON documents link to matrix rows TL1-A01 through TL1-A12 and contain 54 named cases. Preflight validates every document before any case executes.

Expected JSON is a required subset of actual output. This permits additional diagnostics while ensuring every explicitly accepted arithmetic or state field remains locked.

### No balance claim

Phase A uses deterministic packets, fixed rolls, and scripted transitions. Passage proves rule ordering and resource accounting, not weapon-family viability. No Monte Carlo, direct-fire hit model, initiative assumption, endpoint rule, or differentiated doctrine is introduced in Checkpoint 25.

### Phase B gate

Before core duels are implemented, the project must define:

1. exact initiative and committed-fire ordering;
2. one direct-fire hit contract for Firm tracks;
3. destruction, mission-kill, unresolved, retreat, and surrender endpoints;
4. executable shared doctrine;
5. side-swapped common-random-number pairing;
6. causal output metrics; and
7. compatibility between abstract warhead packets and the existing moving Missile Flight runtime.


The authoritative TL1 baseline SHA-256 for this checkpoint is `50316e0528f5e80a16957017ecf407ce4655c40d57dc9e077d09d0d86e19bd7a`.

## Checkpoint 34 headless calibration lane

Routine technology calibration now uses `StarCluster.Calibration.sln`, which contains Core, ScenarioRunner, and Tests but excludes the Godot host. The production game remains Godot/C# and consumes the same authoritative Core library.

A stable shared PowerShell harness reads a versioned JSON checkpoint definition. It validates repository integrity and script syntax, builds the headless solution, runs compiled tests, and executes configured ScenarioRunner commands. It accepts semantic results from exit codes rather than searching source files, README prose, Concept text, workbook cells, or console wording.

Godot integration is a separate milestone lane built from `StarCluster.sln`. This avoids presentation-layer friction during frequent balance iteration while preserving periodic end-to-end integration proof.
