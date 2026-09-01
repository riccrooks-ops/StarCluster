## Checkpoint 53 status

Checkpoint 53 preserves every Checkpoint 52 stage and adds an 870-variant refined TL1/TL2 Auxiliary matrix, a 96-variant TL2 Ablative candidate study, a 78-variant Tactical Power stress study, and deterministic resource-semantics locks. Ablative Armor now enters at TL2; AMM is held at 25 rounds at TL1/TL2; Combat Battery remains three finite +1-TP charges with one discharge per turn and no per-encounter cap.

Run the deterministic resource-semantics stage directly with `auxiliary-resource-endurance`; use `auxiliary-resource-endurance-preflight` for input validation only. The checkpoint wrapper is `tools/checkpoints/checkpoint-53/apply_checkpoint_53.ps1`.

## Checkpoint 28 status

The TL1 Energy Cannon calibration is executable through `tl1-energy-calibration` and `tl1-energy-calibration-preflight`. The study contains 31 variants at 10,000 trials each; forced overload beyond the safe two-shot burst remains deferred.

# StarCluster.ScenarioRunner

`StarCluster.ScenarioRunner` is the engine-independent mechanical host for the
same `StarCluster.Core` services used by Godot. It does not render a board or
reimplement movement, sensing, datalink, guidance, interception, terminal, or
fuel rules.

## Shared initialization contract

Every deterministic or stochastic run:

1. creates the authoritative finite `SystemMap`;
2. places terrain and ships;
3. seeds declared fragmentary prior intelligence;
4. reconstructs pre-existing Missile Flights through normal
   `GuidedMissileSalvo` lifetime state, including adjacent travel history,
   retained datalink reports, local tracks, search state, and guidance phase;
5. runs the production sensor evaluator and system-entry track initializer for
   every observer against ships and existing Missile Flights; and
6. exposes the initialized runtime to the scenario's scripted actions.

A pre-positioned Missile Flight is therefore a normal authoritative game object,
not a special runner-only shortcut.

## Execution modes

### Deterministic single scenario

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  single .\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json `
  --output-dir .\out\single
```

`run <scenario>` remains an alias for `single`.

### Deterministic corpus

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  run-all `
  --scenario-dir .\src\StarCluster.ScenarioRunner\Scenarios `
  --output-dir .\out\deterministic
```

The whole selected corpus is deserialized and preflighted before any member is
executed. Malformed pre-existing travel history, references, profiles, actions,
or assertions stop the batch before partial results are produced.

### TL1 Phase A deterministic mechanics corpus

Checkpoint 25 adds a separate data-driven corpus for the first executable TL1
mechanics contracts. It reads the exact 117-value baseline CSV, verifies its
SHA-256 identity, preflights all scenario documents before execution, and
compares each actual result with a recursively matched expected subset.

Run all 12 scenario documents and 54 mechanics cases:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  tl1-phase-a `
  --scenario-dir .\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --output-dir .\out\checkpoint-25-tl1-phase-a
```

Preflight the corpus without executing mechanics cases:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  tl1-phase-a-preflight `
  --scenario-dir .\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv
```

Run one document:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  tl1-phase-a-single `
  .\src\StarCluster.ScenarioRunner\Scenarios\TL1PhaseA\tl1-a01-shield-bypass-capacity.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --output-dir .\out\checkpoint-25-tl1-phase-a-single
```

The corpus covers layered damage, Shield recharge, one-way Tactical Power, held
interception earmarks, the Turn Power Envelope, Reactor overload and Strain,
Turn/FTL resets, safe weapon resource packets, and charging/retention. No balance conclusions are authorized from these fixed deterministic cases; they
prove arithmetic, ordering, resource, and state fidelity only.

### Monte Carlo batch

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  batch .\src\StarCluster.ScenarioRunner\Scenarios\terminal-two-window-hit.json `
  --variant-id pds-40 `
  --trials 10000 `
  --master-seed 190100 `
  --jobs 24 `
  --checkpoint-every 256 `
  --output-dir .\out\batch
```

A batch ignores deterministic interception queues and fixed terminal rolls. It
uses independent, platform-stable random streams for interception and terminal
resolution. Every trial seed is derived solely from the master seed, variant ID,
trial index, and stream ID. Trial order and worker count therefore cannot change
a trial's random sequence.

Each defense may declare `interceptionChancePercent` for stochastic runs.
Production TL-derived probability formulas remain deferred; this explicit field
is a validation seam for the Checkpoint 19 harness.

Use `--resume` to continue a compatible partial run. Completed trials are stored
in trial-index order and validated against the run identity and derived seed
before reuse. The requested trial count may increase during resume. Results are
checkpointed after each `--checkpoint-every` block.

Normal output is compact:

- `manifest.json` - scenario/configuration and assembly identity;
- `trials.jsonl` - one compact, resumable record per trial;
- `results.json` - canonical worker-independent aggregate;
- `result.sha256` - hash of the canonical result;
- `metrics.csv` - probability counts, proportions, and Wilson 95% intervals;
- `execution.json` - the latest worker count, timing, and resume accounting;
- `execution-history.jsonl` - append-only provenance across initial and resumed invocations; and
- `traces/` only when `--trace-samples N` is requested.

Use `--discard-trials` for a non-resumable compact batch after aggregation. The
Checkpoint 20 calibration mode instead discards per-trial journals by default
and preserves them only when `--keep-trials` is supplied.

`results.json` deliberately excludes worker count, elapsed time, output paths,
and timestamps. Runs with the same scenario, assemblies, master seed, variant,
and trial count must therefore produce the same result hash at `--jobs 1`,
`--jobs 12`, and `--jobs 24`.

### Parameter sweep

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  sweep .\src\StarCluster.ScenarioRunner\Studies\checkpoint-19-terminal-probability-validation.sweep.json `
  --jobs 24 `
  --output-dir .\out\sweep
```

A versioned sweep document references one base scenario and supplies named
variants through typed JSON-path overrides such as:

```json
{
  "path": "defenses[0].interceptionChancePercent",
  "value": 40
}
```

This avoids duplicating full scenario files for every TL, sensor, ECM, seeker,
PDS, range, or speed variation. Variants may supply expected aggregate
probabilities and a maximum absolute error. `sweep-summary.json` and its hash are
also independent of worker count.


### Representative-profile TL calibration

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-20-terminal-tl-calibration.calibration.json `
  --jobs 24 `
  --output-dir .\out\checkpoint-20b-terminal-tl-calibration
```

The calibration study combines a versioned profile catalog with one terminal
base scenario. The first matrix covers command-guided, seeker-only, sensor-only,
and sensor-plus-seeker Missile Flights at missile, PDS, and target-ECM TL 2, 4,
and 6. This yields 108 materialized variants.

The profile catalog contains explicit provisional component values rather than
a hidden universal ship-TL bonus. It supplies flight, datalink, sensor, Guidance
Computer, seeker, terminal-ECM, and PDS conversion values for TL 1 through TL 9.
The current PDS conversion starts at 35% per terminal window for equal TL and
changes by 10 percentage points per PDS-minus-missile TL, bounded from 5% to
95%. These are calibration inputs, not locked game rules.

Calibration output includes:

- `calibration-summary.json` and its SHA-256 hash;
- `calibration-summary.csv` with explicit input values, analytical expectations,
  observed frequencies, confidence intervals, and worst error;
- `calibration-marginals.csv` for paired adjacent missile, PDS, and target-ECM
  TL comparisons, including discordant counts, paired confidence bounds, raw
  and Holm-adjusted p-values, and common-random-numbers fingerprints; and
- compact per-variant result/manifest/execution files under `variants/`.

The runner analytically predicts both PDS windows, seeker-only acquisition,
and effective hit probability. A variant fails if any key observed metric is
farther from its expected value than the study tolerance. Calibration variants
share one random-seed namespace, so adjacent comparisons use common random
numbers. A marginal fails only when its paired effect opposes the expected TL
direction by more than the configured practical threshold and its
continuity-corrected McNemar p-value remains significant after Holm familywise
correction.

## Statistical contract

Checkpoint 20 reports unconditional per-launched-Missile-Flight frequencies,
including:

- effective hit per launched Missile Flight, combining ordinary and critical hits;
- terminal-entry and pre-attack interception;
- acquisition attempt and success;
- terminal attack resolution;
- Search/Wait activation;
- every final terminal outcome and flight status; and
- average distance and fuel expenditure.

Probability metrics include Wilson 95% confidence intervals. Marginal reports
use paired effective-hit differences and include their own paired 95% interval.
These reports are for simulator verification and later balance studies; they do
not themselves establish final game values.

## Reproducibility and integrity

Every canonical result records hashes for:

- the fully materialized scenario after overrides;
- `StarCluster.ScenarioRunner.dll`; and
- `StarCluster.Core.dll`.

A resume is rejected when any of those identities, the variant ID, or master
seed differs. Separate interception and terminal streams prevent a change in
one subsystem's random-consumption count from silently shifting the other
subsystem's rolls.

## Validation hierarchy

1. Core unit and integration tests validate isolated rules.
2. The seven deterministic scenarios validate complete causal sequences.
3. Monte Carlo batches validate seeded stochastic behavior and aggregation.
4. Sweeps validate parameter effects and mathematical assumptions.
5. Godot testing is reserved for player-facing input, rendering, visibility,
   and presentation smoke checks.

## Current interception roles

Held direct-fire weapons may react during `Transit` and `Stationary`. Standard
PDS reacts only during `TerminalEntry` and `PreTerminalAttack`. The runner calls
the shared Core eligibility policy and does not override these roles.

### Full-flight pursuit calibration

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  pursuit-calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --jobs 24 `
  --output-dir .\out\checkpoint-21-full-flight-pursuit-calibration
```

The Checkpoint 21 study crosses four missile capability packages, missile TL
2/4/6, target propulsion TL 2/4/6, four deterministic target-movement policies,
and live/occluded launcher datalinks. Its 288 variants execute the normal
multi-turn Core sequence from pre-existing flight state through terminal
outcome, range exhaustion, or the configured horizon.

Routine output is compact and includes terminal-opportunity and effective-hit
probability per launch, range/search/self-destruction/dud/miss/datalink/guidance-source rates, relative
speed class, average turns/actions/replans/distance/fuel, and paired marginal
reports. Trial journals are retained only with `--keep-trials`.

### Checkpoint 21a full-flight repair and 24-worker execution

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  pursuit-calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --jobs 24 `
  --output-dir .\out\checkpoint-21a-full-flight-pursuit-calibration
```

The full-flight study now uses authoritative terminal-opportunity records with
four source classes: missile entered the target hex, target entered the missile
hex, action began co-located, and stationary Search/Wait retry. A trial fails
its invariant if terminal mechanics occur without the corresponding record or
if diagnostic and authoritative counts diverge.

`lateral` is replaced by the distinct `crossing-weave` fixture, while the exact
backtracking case is named `turnback`. Every scenario receives an
endurance-derived `operationalTurnLimit`; active state at the cap is reported as
an operational timeout, while any earlier unexplained nonterminal state fails
the variant.

`--jobs 24` now means at most 24 concurrently executing variants. Each variant
uses one inner trial worker, preventing nested parallelism. Non-resume runs that
discard trials no longer write a temporary trial journal. Canonical summaries
remain worker-independent and timing data is isolated in
`full-flight-execution.json` and `full-flight-variant-execution.csv`.


### Checkpoint 21c dedicated scheduler and semantic diagnostics

Scheduler proof:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  pursuit-calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --scheduler-proof `
  --trials 8 `
  --jobs 24 `
  --output-dir .\out\checkpoint-21c-scheduler-proof-j24
```

Full calibration:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  pursuit-calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --jobs 24 `
  --output-dir .\out\checkpoint-21c-full-flight-pursuit-calibration
```

`--scheduler-proof` selects exactly 24 representative variants, disables
gameplay statistical gates, and verifies mechanical contracts and canonical
common-random-number output. Full calibration uses the complete 288-variant
matrix. The scheduler starts dedicated long-running variant workers, caps them
at 24, and assigns one serial trial lane to each variant.

A stale candidate-coordinate arrival is reported as Search/Wait rather than
terminal acquisition when the target is not co-located. Occluded-datalink
validation forbids fresh guidance and validates any attempted update as Blocked;
trials that resolve before an update remain valid. `errors.jsonl` is retained
for failed trials even when `trials.jsonl` is discarded.

### Checkpoint 21e global trial-block scheduler

The rejected dedicated-variant design is superseded. Full-flight execution now
builds one deterministic queue of small `(variant, trial range)` blocks and
feeds it to at most 24 dedicated workers. Workers write only to preassigned
in-memory result slots. Per-variant aggregation, manifests, metrics, error
journals, and optional trial journals are emitted after compute completes.

The executable enables server GC. `full-flight-execution.json` schema 3 records
compute-only throughput, block completion, process CPU time, effective core use,
processor and affinity visibility, allocation volume, GC counts, and output
finalization time. Progress is printed every five percent.

Use a 32-trial scheduler proof before a large study:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  pursuit-calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --scheduler-proof `
  --trials 32 `
  --jobs 24 `
  --output-dir .\out\checkpoint-21e-scheduler-proof-j24
```

The checkpoint apply script compares this with the one-worker proof and refuses
to launch the full 288,000-trial calibration unless compute throughput improves
by at least 2.0x and the projected runtime is no more than 30 minutes.


### Checkpoint 22 compact Monte Carlo execution

Full-flight calibration defaults to compact metrics:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  pursuit-calibrate .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --trial-execution compact `
  --jobs 24 `
  --output-dir .\out\checkpoint-22-full-flight-pursuit-calibration
```

Use `--trial-execution diagnostic` for the full-journal reference path. Both
modes invoke the same Core mechanics and random streams. Compact mode reuses one
immutable execution plan per variant, records direct Monte Carlo observations,
and omits unused diagnostic-event and track-update result objects. Fresh mutable
scenario state is still created for every trial.

Checkpoint 22a is a build-only source-symbol hotfix: metrics resolve
`SensorMode` from `StarCluster.Core.Combat.Tracking`, and canonical parity tests
use `ScenarioDocumentSerialization.CompactWriteOptions`. Runtime semantics are
unchanged.

### Checkpoint 22b allocation attribution

Checkpoint 22b does not run the failed full allocation gate. It profiles the
unchanged 24-variant scheduler-proof corpus serially in diagnostic and compact
modes:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  allocation-profile .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --trials 4 `
  --warmup-trials 1 `
  --output-dir .\out\checkpoint-22b-allocation-profile
```

The command writes a JSON summary, aggregate CSV stage table, per-trial CSV,
and text report. Every matching diagnostic and compact trial must serialize to
the same canonical
`MonteCarloTrialResult`. Stage measurements use per-thread allocation counters
and include top-level initialization, movement, missile, phase, finalization,
and projection attribution plus nested movement and guidance detail.

### Checkpoint 22c calibration-map optimization proof

Checkpoint 22b showed that map-heavy runtime initialization, not journal
materialization, dominated trial allocation. Generated full-flight scenarios
now use a variant-sized map based on every explicit coordinate plus a two-hex
safety margin. Radius 192 remains available only for reference parity.

Run the direct proof with:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  map-optimization-proof .\src\StarCluster.ScenarioRunner\Studies\checkpoint-21-full-flight-pursuit.calibration.json `
  --parity-trials 4 `
  --map-measurements 3 `
  --output-dir .\out\checkpoint-22c-map-optimization-proof
```

The command measures `SystemMap.Create` at radii 5, 28, 64, 100, and 192,
validates explicit-coordinate containment for all 288 variants, and compares
canonical compact results against radius-192 reference variants using identical
random streams. It writes `map-optimization-summary.json`,
`map-allocation-sweep.csv`, `map-radius-variants.csv`, and a text report.

The allocation profiler now includes nested initialization stages, especially
`InitializationMapCreation`. Checkpoint 22c freezes the successful Checkpoint
22b compact baseline at 20,863,918 bytes/trial and requires optimized compact
allocation no greater than 4,172,784 bytes/trial before the full calibration is
allowed to start.


### Checkpoint 22d accepted baseline

Checkpoint 22c map sizing and compact Monte Carlo execution are accepted through
Checkpoint 22d. Checkpoint 21e remains the frozen behavioral reference. The
accepted full-flight result hash is
`226677d3b9d2fded9e529ab5b897f6ec0e5251eb27937208f571cbb9b184ee28`.

Future runner changes must preserve the locked summary/marginal CSV references,
worker-independent hashes, diagnostic/compact semantic parity, and the frozen
4,172,784-byte compact allocation ceiling unless a reviewed successor checkpoint
explicitly replaces a gate.

### TL1 Phase B direct-fire foundation

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-phase-b-preflight
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-phase-b --output-dir .\out\checkpoint-26-tl1-phase-b
```

The corpus currently contains 7 documents and 36 deterministic cases. It verifies accuracy arithmetic, roll-high boundaries, EvM, computer degradation, simultaneous return fire, mutual destruction, and the fixed-geometry kinetic mirror duel. It does not establish weapon balance.

## TL1 kinetic interaction calibration

Preflight the 29-variant study without trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-kinetic-calibration-preflight
```

Run the default 10,000-trial study with common random numbers and up to 24 workers:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- tl1-kinetic-calibration --trials 10000 --jobs 24 --output-dir .\out\checkpoint-27-tl1-kinetic-calibration
```

Outputs are `summary.json`, `variants.csv`, and `gates.csv`. They include Wilson 95% intervals for terminal outcomes, per-layer final-state means, Hull-damage and Armor-depletion rates, duel pace, hits, and ammunition use. Mirror and side-swapped gates establish deterministic fairness; they do not establish final weapon balance.

## Checkpoint 29 complete TL1 weapon matrix

Use `tl1-weapon-matrix-preflight` to validate the 48-variant study and its baseline hash without running trials. Use `tl1-weapon-matrix` to execute kinetic, energy, and missile mirror/cross-family comparisons. The matrix intentionally excludes ECM, ECCM, PDS, and richer Tactical Power doctrine so it can expose mechanically impossible penetration, range exhaustion, pursuit failure, ammunition exhaustion, and hard stalls first.

## Checkpoint 30 TL1 PDS and interception calibration

Checkpoint 31 supersedes this section's finite-ammunition, Targeting Computer, and AMM-EvM assumptions; the command remains as a corrected retained control.

Preflight the 59-variant PDS study and its exact baseline without running trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-pds-calibration-preflight
```

Run the default 10,000-trial matrix with up to 24 workers:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-pds-calibration `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-30-tl1-pds-calibration
```

Outputs are `summary.json`, `variants.csv`, and `gates.csv`. They report PDS attempts and interceptions, terminal-entry and pre-attack attempts, finite ammunition consumption, Powered Tactical Power committed to readiness, Missile Flights reaching terminal Guidance, missile hits, duel outcomes, duration, and remaining Hull. Direct/terminal and interception random streams are separate. Mirror and side-swapped gates establish execution fairness; they do not establish final PDS or missile balance.

## Checkpoint 31 TL1 layered defensive systems calibration

Checkpoint 31 supersedes the Checkpoint 30 finite-magazine and PDS fire-control assumptions while retaining its 59 variants as a corrected control. Main Missile Flights total 25, Kinetic PDS packages total 50, and AMMs total 25; each finite system begins with one Ready Package included in total capacity and automatically reloads from reserve. PDS remains locally self-contained but may receive +10/+5/+0 main Targeting Computer assistance. Own EvM penalizes Kinetic and Energy PDS by five percentage points but not AMM after launch.

Preflight the exact 171-variant defensive study and baseline without running trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-defensive-calibration-preflight
```

Run the default 10,000-trial study with up to 24 workers:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-defensive-calibration `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-ds01-layered-defensive-systems-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-31-tl1-defensive-calibration
```

Outputs are `summary.json`, `variants.csv`, and `gates.csv`. They report outcomes, duration, direct hits, Missile Flights launched, terminal attacks, missile hits, PDS attempts/interceptions, remaining finite ammunition, Firm and denied turns, sensor/ECM/ECCM/PDS/Shield-Hardener power commitments, tactical shield-recharge power, Shield Battery charges, remaining Hull, and unresolved combat. The 171 variants comprise 6 accepted controls, 36 PDS correction cases, 57 sensor/EW boundary cases, 36 shield-defense cases, and 36 layered-defense cases. Reciprocal and mirror gates establish execution fairness; they do not establish final balance.

## Checkpoint 34 headless C# calibration lane

Checkpoint 34 preserves the Checkpoint 33 mechanics and 294-variant correction study, but runs them through the stable shared calibration harness and the Godot-independent `StarCluster.Calibration.sln`. Routine acceptance depends on the repository manifest, PowerShell syntax, the pinned .NET SDK, compiled C# tests, typed ScenarioRunner validation, and runner exit codes. Documentation presence is reported but non-blocking; README, Concept, workbook, and source-code phrases are never interpreted as mechanical contracts.

Run the checkpoint wrapper:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\tools\checkpoints\checkpoint-34\apply_checkpoint_34.ps1
```

Use `tools/integration/run_full_solution_validation.ps1` separately at major Godot/C# integration milestones.

## Checkpoint 33 TL1 main-power and interception correction

Checkpoint 33 retains every accepted lane and adds a 294-variant focused correction study. It repeats Reactor outputs 3 through 6 after making Kinetic main fire cost 1 TP, retaining zero-TP Missile launch, resolving Held Main before PDS, reducing TL1 Shield overcapacity to 1 temporary SP per activation, and reducing the early Auxiliary Reactor comparison to +1 Operational / +0 Degraded. Fixed doctrines remain envelope probes rather than tactical AI.

Preflight the exact study, baseline, reciprocal pairs, and category counts without trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-power-envelope-calibration-preflight `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-pe02-main-power-interception-correction-study.json
```

Run the full study:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-power-envelope-calibration `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-pe02-main-power-interception-correction-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-33-tl1-power-correction-calibration
```

## Checkpoint 32 TL1 Tactical Power completion and Reactor-envelope calibration (retained historical study)

Checkpoint 32 retains every accepted lane and adds a 504-variant static envelope study. It sweeps renewable Reactor output from 0 through 8 TP while keeping Auxiliary Reactor output, full-after-FTL Capacitor storage, Combat Battery injection, and safe Reactor overload separately attributable. The study uses fixed package priorities rather than adaptive tactics. Shield Batteries remain finite emergency reserves and are excluded from routine reactor valuation. Tractor Beams, Tractor overload, STL Drive overload, and movement-dependent valuation remain deferred.

Preflight the exact study, baseline, reciprocal pairs, and category counts without trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-power-envelope-calibration-preflight
```

Run the default 10,000-trial study with up to 24 workers:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-power-envelope-calibration `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-pe01-tactical-power-and-reactor-envelope-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-32-tl1-power-envelope-calibration
```

The 504 variants comprise 6 accepted controls, 90 Reactor-output sweeps, 144 single-consumer cases, 144 layered-package cases, 60 power-source overlays, 30 overload boundaries, and 30 Held Interception cases. Results distinguish renewable output from Auxiliary contribution, Capacitor discharge, Combat Battery injection, and overload gain; report Powered, Spent, earmarked, unused, and unfunded power; and record weapon firing, Energy mode, defensive uptime, interception, shield restoration, Strain, and terminal outcomes. The study identifies affordability thresholds and component strengths or weaknesses; it does not model realistic tactics or lock final Reactor output.


## Checkpoint 35 scripted relative-range calibration

Checkpoint 35 adds a typed relative-range schedule to the shared TL1 simulation profiles. A change is applied at the start of the named turn before sensor/EW, power, firing, and missile resolution. Live Missile Flights adjust remaining route by the separation delta while cumulative traveled distance remains spent against Maximum Range.

Preflight the exact 75-variant study without running trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-range-control-calibration-preflight `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-rc01-scripted-relative-range-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv
```

Run the default 10,000-trial study with up to 24 workers:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-range-control-calibration `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-rc01-scripted-relative-range-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-35\tl1-range-control-calibration
```

Outputs are `summary.json`, `variants.csv`, and `gates.csv`. The study reports outcomes, range changes, Firm/denied track rates, missile launches/hits/exhaustion/reroutes, Held/PDS activity, and remaining Hull. It does not implement absolute board movement.


## Checkpoint 36 internal damage and Damage Control calibration

Checkpoint 36 adds a persistent deterministic H/X stream, weighted direct and Electronics-group Critical Exposure, component condition progression, TL1 combat Damage Control, ship-state evaluation, Jump Perimeter and FTL power-up rules, and Missile Flight exit cleanup. Checkpoint 36b preserves paired ordinary/protected finite X counts with a terminal H/X swap and adds the initial +10-point Immobile Target ship-target accuracy modifier for Disabled/Destroyed STL.

Preflight the exact 80-variant study without trials:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-internal-damage-calibration-preflight `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-id01-internal-damage-and-damage-control-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv
```

Run the default 10,000-trial study with up to 24 workers:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-internal-damage-calibration `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-id01-internal-damage-and-damage-control-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-36\tl1-internal-damage-calibration
```

Outputs are `summary.json`, `variants.csv`, `gates.csv`, `component-frequency.csv`, `hull-band.csv`, and `result.sha256.txt`. The study reports calibration evidence; it does not select the final ordinary H/X density.

## Checkpoint 37 Damage Control doctrine and combat pacing

Checkpoint 37 supersedes the Checkpoint 36 eager repair-policy calibration with two focused commands.

Preflight the exact 64-variant Damage Control study:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-damage-control-calibration-preflight `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-dc01-damage-control-doctrine-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv
```

Run it:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-damage-control-calibration `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-dc01-damage-control-doctrine-study.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-37\tl1-damage-control-calibration
```

The study compares 25% and 33 1/3% internal critical density, ordinary and Protected placement, four doctrines, two loadouts, and steady/burst Hull packets. It uses a calibration-only five-kit profile while retaining the player-facing TL1 three-kit rule. Outputs separately report component/Hull attempts, condition-specific success rates, next-turn activations, resource use, target frequency, doctrine deferrals, and kits available at the first X.

Preflight and run the 8-variant pacing probe with `tl1-combat-pacing-preflight` and `tl1-combat-pacing`. The pacing output adds mean/median/P75/P90 turns, the share over 18 turns, destruction/mission-kill/unresolved rates, first consequential impairment, and following-turn Immobile Target use. The simulator captures target STL at the start of each turn so later damage cannot retroactively alter committed accuracy.
## Checkpoint 38 integrated tactical combat

Checkpoint 38 adds `tl1-integrated-tactical-combat-preflight` and `tl1-integrated-tactical-combat`. The 90-variant study covers all ordered kinetic, energy, and missile pairings under Hold Range 2, Hold Range 4, Scripted Pursuit, and Preferred Range policies. It retains 33 1/3% internal criticals, ordinary/Protected placement, the normal three-kit TL1 Damage Control profile, PDS, Evasive Maneuvers, component-conditioned performance, and start-of-turn Immobile Target snapshots.

Range intent comes through `ITacticalOrderPolicy`; `RangeOrderResolver` applies actual STL condition, simultaneous movement, desired-separation throttling, and no-crossing rules. Missile position and cumulative travel remain independent after launch, so target movement changes the remaining geometry without refunding range. Output is `summary.json`, `variants.csv`, `gates.csv`, and `result.sha256.txt`.

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-integrated-tactical-combat `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc01-cross-family-dynamic-range.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-38\tl1-integrated-tactical-combat
```


## Checkpoint 39 movement, kinetic, and pacing diagnostics

Checkpoint 39 keeps the `tl1-integrated-tactical-combat` command and upgrades its typed document to schema v2. The production 90-variant study now uses ship STL Move = Drive TL, missile Move = Missile Drive TL + 1, and the provisional DAM 4/APEN 0 Kinetic Cannon.

The same command also runs `tl1-itc02-movement-kinetic-pacing-diagnostics.json`, a 44-variant paired study that compares production 1/2, Godot 3/2, legacy 4/1, and overload-equivalent 2/2 movement; DAM 3, DAM 4, DAM 5, and DAM 4/APEN 1 kinetic arms against an AP 1 diagnostic armor fixture; and Shield-recharge/EvM controls. Production armor remains AP 0. Integrated missile ships use the accepted 0-TP launch and 25-Flight magazine. Output now includes explicit-withdrawal disengagement, attack-prevention reasons, hit chances, Shield restoration, Shieldless turns, and layer-by-layer damage.

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj --no-build -- `
  tl1-integrated-tactical-combat `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\TL1Calibration\tl1-itc02-movement-kinetic-pacing-diagnostics.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-39\tl1-movement-kinetic-pacing-diagnostics
```

## Checkpoint 48 AUX screening

The `tl1-integrated-tactical-combat` command now accepts an optional Auxiliary combat profile catalog. Retained studies default to the frozen `legacy-integrated-aux-suite`, preserving their historical PDS, Evasive Maneuvers, and Auxiliary Reactor behavior. The Checkpoint 48 study supplies explicit one-component AUX profiles and records both side profile IDs in results.

Run the primary study directly with:

```powershell
dotnet run --project .\src\StarCluster.ScenarioRunner\StarCluster.ScenarioRunner.csproj -- `
  tl1-integrated-tactical-combat `
  --study-file .\src\StarCluster.ScenarioRunner\Scenarios\AuxiliaryTechnology\aux-itc01-single-slot-performance-screening.json `
  --baseline-file .\docs\design\player_technology\tl1_core_combat_numerical_baseline_v0_1.csv `
  --trials 10000 `
  --jobs 24 `
  --output-dir .\out\checkpoint-48\auxiliary-single-slot-performance-screening
```

The legal matrix always installs one non-counterfactual AUX per ship. Empty-slot profiles appear only in the separately labeled diagnostic partition.
