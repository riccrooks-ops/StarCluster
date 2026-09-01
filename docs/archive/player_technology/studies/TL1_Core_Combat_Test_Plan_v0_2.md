# TL1 Core Combat Test Plan v0.2

**Checkpoint 25 status:** Phase A deterministic mechanics are executable. Values remain exact provisional test inputs, not promoted balance.

## Goal

The TL1 program measures the smallest complete combat loop before optional systems, higher technology, and specialized doctrine obscure cause and effect. It seeks situational viability, not equal outcomes.

A healthy option:

- has a clear purpose;
- is valuable when its intended problem exists;
- carries a visible opportunity cost when irrelevant;
- is helped, but not erased, by counters;
- remains understandable in the event record;
- is not routinely dominant, oppressive, redundant, or a trap.

## Controlled TL1 chassis

Core duel variants will share one stripped TL1 cruiser:

- Hull, one primary armor layer, shields, one Main Reactor, FTL and STL drives, passive sensors, one Targeting Computer, one Weapon Bay, Crew, Marines, and Damage Control;
- no optional PDS, ECM, ECCM, Shield Hardener, batteries, capacitor, Auxiliary Reactor, APU, tractor, cloak, powered armor, or other Auxiliary component;
- one weapon family: kinetic, energy, or missile;
- identical starting state, geometry, initiative policy, and doctrine;
- fixed Firm tracks for the first weapon tests.

This fixture is a controlled laboratory, not a complete campaign loadout.

## Phase A executable boundary

Checkpoint 25 executes 12 baseline-driven scenario documents containing 54 deterministic cases:

| Matrix ID | Runtime contract | Cases |
|---|---|---:|
| TL1-A01 | SPEN, Shield Armor, Shield Capacity, and overflow | 5 |
| TL1-A02 | AP, AI, multiple layers, Hull overflow, and overkill | 5 |
| TL1-A03 | Turn-start Shield recharge and Spent power | 6 |
| TL1-A04 | Available, Powered, Spent, and earmarked power | 4 |
| TL1-A05 | shutdown / disable lock and same-turn restart prohibition | 2 |
| TL1-A06 | unused held-interception earmarks | 2 |
| TL1-A07 | triggered held-interception spending | 2 |
| TL1-A08 | current Turn Power Envelope versus next-turn reactor output | 3 |
| TL1-A09 | safe, forced, failed, and critical Reactor overload | 7 |
| TL1-A10 | Turn Refresh and FTL transition | 2 |
| TL1-A11 | safe kinetic, energy, and missile resource packets | 5 |
| TL1-A12 | charging, Ready state, retention, consecutive-payment enforcement, non-retaining auto-discharge, disablement, and FTL | 11 |

The charging cases additionally enforce one charging or retention payment per weapon per turn, reset incomplete progress after a missed required turn, and require paid retention upkeep before a carried Ready weapon may fire on a later turn. The final charging payment itself covers firing during that same turn.

The runtime corpus lives under `src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/`. Every document:

- declares `star-cluster-tl1-phase-a-v1`;
- identifies its scenario-matrix row;
- references baseline version `tl1-core-combat-v0.1`;
- contains named cases with typed operation input;
- contains an expected JSON subset;
- is preflighted before any case executes.

The runner writes the source baseline path and SHA-256 into each result summary. Expected subsets permit output to gain additional diagnostics without weakening the explicitly asserted contract.

## Phase A execution commands

From the repository root:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-phase-a-preflight

dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-phase-a --output-dir .\out\checkpoint-25-tl1-phase-a
```

One document may be run with:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-phase-a-single .\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA\tl1-a01-shield-bypass-capacity.json
```

## Phase A interpretation

Passing Phase A means:

- exact arithmetic and state transitions match the accepted rules and baseline;
- resource use is deterministic and traceable;
- invalid one-way-power and retention actions are rejected;
- reset boundaries retain and clear the intended state;
- existing missile runtime remains regression-safe.

Passing Phase A does **not** mean:

- the provisional numbers are balanced;
- a weapon family is viable under stochastic play;
- direct-fire accuracy, initiative, Damage Control, Crew casualty, or endpoint rules are finished;
- energy overload, optional systems, or movement are implemented.

Energy-weapon overload is deliberately excluded from the packet corpus until its additional power, Strain, once-per-turn use, and forced-overload failure path are implemented together.

## Phase B entry gate

Phase B begins only after the Checkpoint 25 Windows validator passes. Before Monte Carlo, the next pass must settle and implement:

- deterministic initiative / simultaneous-fire ordering;
- one exact direct-fire hit rule using the existing Firm-track premise;
- exact destruction and mission-kill endpoints;
- common core doctrine sequencing;
- side-swapped common-random-number pairing;
- complete event and metric records;
- compatibility between abstract missile warhead packets and the existing moving Missile Flight runtime.

## Later test ladder

1. **Phase B:** K/K, E/E, M/M mirrors; then cross-family pairings.
2. **Phase C:** PDS and defensive modules, one at a time.
3. **Phase D:** ECM, ECCM, and Active Sensors.
4. **Phase E:** power flexibility and remaining overload modes.
5. **Phase F:** component damage, Crew, Marines, Damage Control, and hazards.
6. **Phase G:** movement, EvM, STL overload, tractors, held interception, and retreat.
7. Only then progress through TL2-TL9 and mixed-TL stress cases.

## Symmetric, asymmetric, and relevance tests

Every optional system begins with neither side, both sides, Side A only, and side-swapped Side B only. Power-using systems are tested both with the same reactor and with compensating reactor output.

Each countermeasure is tested in:

- irrelevant context;
- ordinary relevant context;
- heavy or saturation context.

For example, PDS should be irrelevant against a kinetic-only opponent, materially helpful against ordinary missiles, and still permit a missile-heavy doctrine to function under saturation or other counterplay.

## Metrics for later duel phases

Record at minimum:

- endpoint and turns to endpoint;
- shield collapse, shieldless turns, and layer timing;
- damage prevented, bypassed, absorbed, and applied;
- AP, AI, Hull, component, Crew, and Marine outcomes;
- Available, Powered, earmarked, Spent, and unused Tactical Power by phase;
- ammunition, battery, capacitor, repair-supply, and fuel use;
- overload, forced-overload, failure, critical, and Strain outcomes;
- PDS attempts and interception;
- track transitions and missed firing opportunities;
- tractor and movement outcomes.

## Interpretation labels

- **Dominant** - routinely best outside its intended context.
- **Viable** - worthwhile in intended contexts with meaningful costs.
- **Niche** - narrow but real purpose.
- **Trap** - appears useful but is almost never worth its cost.
- **Oppressive** - invalidates the system it counters.
- **Redundant** - another option provides the same purpose more efficiently.

The desired space contains mostly Viable options and some intentional Niche options.

## Traceability

- exact values: `tl1_core_combat_numerical_baseline_v0_1.csv`;
- reusable fixtures: `tl1_core_combat_loadouts_v0_1.csv`;
- staged matrix and runtime links: `tl1_core_combat_test_scenarios_v0_2.csv`;
- executable Phase A corpus: `src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/`;
- modular schema: `Component_State_And_Profile_Schema_v0_2.md`;
- human-readable workbook: `StarCluster_Player_TL_Framework_Draft_v0_5.xlsx`.


The authoritative TL1 baseline SHA-256 for this checkpoint is `50316e0528f5e80a16957017ecf407ce4655c40d57dc9e077d09d0d86e19bd7a`.
