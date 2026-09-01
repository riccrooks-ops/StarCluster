# Checkpoint 103 — TL1/TL2/TL3 Integration and Permutation Analysis

## Candidate status

**Corrected Replacement 4 candidate** built on native-accepted **Checkpoint 102 Corrected Replacement 3**.

CP103 changes research/validation architecture and performs substantive TL1/TL2/TL3 screening. It does not change accepted gameplay rules, technology values, Concept v0.7d, or the technology workbook. Automatic technology promotion remains prohibited.

## Why Corrected Replacement 4 changes the simulation architecture

The first CP103 candidates exposed repeated failures in checkpoint-specific PowerShell/C# research plumbing rather than Star Cluster mechanics:

1. Windows PowerShell singleton pipeline output collapsed before a `.Count` assertion;
2. copied CP102 `nativeDependencyPrecheck` paths remained in the new CP103 definitions;
3. a CP103-only C# LINQ aggregation triggered CS8619 under warnings-as-errors;
4. after that compile fix, the actual v8 C# consumer rejected numeric `"checkpoint": 103` because its DTO required a string.

The fourth failure is decisive evidence that static repository contracts were validating derived properties without executing the actual study document through its consumer. Continuing to add CP103-specific C# study routing would increase a simulation-only surface that is not part of the shipped game.

Corrected Replacement 4 therefore adopts the explicitly approved architecture:

- **C#/Godot remains authoritative for game mechanics and production behavior.**
- The three CP103-modified ScenarioRunner files are restored byte-for-byte to the native-accepted CP102 CR3 versions.
- **Python becomes the CP103 research simulator** for v8 document validation, exhaustive construction enumeration, population accounting, deterministic sampling, Monte Carlo screening, aggregation, and analysis.
- PowerShell remains a thin Windows checkpoint/orchestration layer.
- Deterministic parity fixtures connect the Python research model to accepted C# mechanics.

This is not a port of the game engine to Python. It is separation of a research/calibration tool from the game implementation.

## Python runtime contract

CP103 explicitly approves **CPython 3.13.x** as a research/acceptance dependency. The research package is standard-library-only; no pip package or virtual environment is required for acceptance.

`tools/simulation/PYTHON_RUNTIME.json` is the runtime policy authority. `tools/simulation/Invoke-StarClusterResearch.ps1` resolves, in order, a compatible `py -3.13`, `python`, or `python3` interpreter and emits a direct setup error if none is available. The exact interpreter, implementation, patch version, and platform are recorded during execution.

**Corrected Replacement 5 Windows bootstrap rule:** interpreter discovery uses `--version` only. The earlier `python -c` version probe embedded Python string quotes inside a native-command argument; Windows PowerShell 5.1 could strip/mangle those quotes before `py.exe` received them, producing a Python `SyntaxError` even with a valid CPython 3.13 installation. The wrapper, pre-preflight, RepositoryOnly contract, and Python unit corpus now reject that bootstrap shape.

**Corrected Replacement 6 parser rule:** checkpoint-authored PowerShell must not inspect source code by embedding quote-heavy PowerShell syntax inside `.Contains(...)` string literals. CR5 proved that a guard intended to reject an unsafe Python bootstrap can itself make the wrapper unparsable under Windows PowerShell 5.1. CP103 now uses an anchored regex over the `$probe` assignment, and the Python unit corpus independently rejects quote-sensitive `.Contains('@(...')`/`.Contains("@(...")` guard shapes in the active wrapper and contract.

Historical checkpoint definitions remain unchanged and continue to reject Python by default. The shared native-dependency precheck accepts additional interpreters only through an explicit checkpoint-scoped `allowedInterpreters` declaration.

## Executable schema and local validation

The v8 JSON study contract now has both a human/tooling JSON Schema and an executable stdlib Python validator. Field **types** are part of the contract. In particular, CP103 requires:

```json
"checkpoint": "103"
```

and explicitly rejects numeric `103`. The Python unit corpus contains a negative regression test for the exact native failure that ended Corrected Replacement 3.

Before handoff the research engine must execute, not merely inspect:

- both v8 study documents;
- exhaustive legal-build enumeration;
- primary population reconstruction;
- deterministic sampling;
- named legacy-overlay materialization;
- 25 deterministic parity cases spanning accuracy, layered defense, Sensor/EW, power/propulsion, weapon-mode, missile-navigation, Shield-Hardener, and PDS contracts;
- one-trial full-variant smoke.

When local runtime permits, the complete substantive workload is also executed before handoff. The authoring environment is not allowed to substitute static inspection for the executable tiers merely because the full Monte Carlo is long.

### Authoring-environment executable evidence

Corrected Replacement 4 has been exercised under **CPython 3.13.5** with no third-party packages. Current-code local evidence includes:

- six Python unit tests passed;
- all 25 deterministic parity/value cases passed;
- exact primary validation reproduced 921,600 raw / 164,160 legal / 96 cells / 576 logical pairings / 1,152 variants and 97,848 statistical-sampler attempts;
- exact overlay validation reproduced 1,417,176 declared raw / 28 materialized legal builds / 50 logical pairings / 100 variants;
- all 1,152 primary variants completed a one-trial smoke with zero trial errors;
- all 100 overlay variants completed a one-trial smoke with zero trial errors;
- a 28,800-trial primary stress run (25 trials across every primary variant) completed with zero trial errors;
- a 115,200-trial primary stress run (100 trials across every primary variant) completed with zero trial errors;
- the complete 25,000-trial overlay substantive workload completed with zero trial errors;
- one-trial primary output was byte-identical with one worker and eight workers, proving worker-count-independent deterministic seeding/output for the smoke corpus.

The complete 288,000-trial primary default workload was also attempted locally but exceeded the current container/tool execution ceiling during the long multiprocessing stage. Individual trials are bounded and the lower-volume all-variant stress runs above complete normally. This limitation is therefore recorded as an **authoring-environment throughput constraint**, not treated as evidence that the study passed. Native Windows acceptance still requires the complete 288,000 primary + 25,000 overlay substantive workload.

## Frozen native C# mechanics surface

CP103 preserves these native-accepted CP102 CR3 files byte-for-byte:

- `CrossTlBuildPermutationRunner.cs` SHA-256 `6cebb3efa11e1fea63cab88377b9de0960b3d5e2a9029385a72556c87afe2984`;
- `Tl1IntegratedTacticalCombatRunner.cs` SHA-256 `8c46eb15814737a1dae80c3320be385361b054c6f8c3cce96afd4dd3a4cc525e`;
- `ScenarioRunnerSelfTests.cs` SHA-256 `af3bb02e64f371f20a4ed6051c7f90fbec960ed6fc614960893d17e28ee858ce`.

Consequently the expected ScenarioRunner self-test count returns to the accepted **70**, while the native xUnit count remains **876**.

## CP103 primary population — v1.1

Executable Python reconstruction must reproduce:

- 921,600 raw combinations;
- 164,160 legal builds;
- 43,584 exact-fill;
- 82,848 near-fill;
- 37,728 underfilled;
- 96 non-empty population cells;
- 240 weighted statistical base pairs;
- deterministic statistical sampler completion in exactly **97,848 attempts**;
- 32 zero-weight diversity base pairs;
- 32 zero-weight named logical diagnostics;
- 576 logical pairings;
- 1,152 movement-order variants;
- 250 substantive trials/variant = 288,000 trials.

The conceptual 13,474,170,720 unordered pairing universe remains bucket/combinatorial; it is never materialized O(N^2).

## CP103 all-tier legacy overlay — v1.2

Executable Python reconstruction must reproduce:

- declared raw axis product 1,417,176;
- 33 named recipes;
- 28 unique legal physical builds;
- 50 logical comparisons;
- 100 variants;
- 250 substantive trials/variant = 25,000 trials;
- population-inference weight zero.

## Research mechanics/parity boundary

The Python tactical model is intentionally a research-screening model. It uses actual build/runtime data and mirrors selected accepted deterministic relationships needed by CP103, including:

- direct-fire accuracy;
- layered Shield/Armor/Hull damage;
- Sensor/EW discrimination and ECCM restoration;
- TL3 High Active Sensor behavior;
- legitimate K3 0-TP ordinary Kinetic fire.

The parity corpus must pass before smoke/substantive research. Python stochastic results are not a bit-for-bit replacement for the production game engine and cannot override C#/Godot mechanics authority.

## Trial workload

The default CP103 research workload is:

- 1,152 primary smoke trials;
- 100 overlay smoke trials;
- 288,000 primary substantive trials;
- 25,000 overlay substantive trials;
- plus the retained accepted CP102 32-trial regression smoke.

Total substantive CP103 research: **313,000 trials**. Total checkpoint trial accounting at defaults: **314,284**.

No separate Deep Calibration is required; the deep definition is the exact same workload alias.

## Native acceptance sequence

After Python is installed/configured on the Windows host, run from one clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-103\apply_checkpoint_103.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-103\apply_checkpoint_103.ps1
```

The first path validates repository/dependency contracts without requiring Python to be installed. The full path requires CPython 3.13.x and records it before research execution.

Acceptance requires:

1. repository/manifest/dependency contracts pass;
2. pinned .NET SDK 8.0.423 build succeeds with warnings as errors;
3. 876/876 xUnit tests pass;
4. accepted deterministic, CP99, and CP102 regression stages pass;
5. CP102 32-trial integrated smoke remains clean;
6. CPython 3.13 environment, six Python unit tests, and deterministic parity pass;
7. primary/overlay executable validation reproduces all declared counts;
8. both one-trial full-variant Python smokes complete with zero trial exceptions;
9. all 313,000 substantive Python trials complete;
10. research analysis completes without failed gates;
11. resource locks and 70 ScenarioRunner self-tests pass;
12. zero failed release gates.

Passing CP103 means the research architecture and declared study executed reproducibly. It does **not** mean any TL3 value is balanced or promoted.

## Post-acceptance review

After native acceptance, analyze design diversity, Pareto/frontier domination, legacy stacking, integer Space breakpoints, Tactical Power pressure, readiness/activity cliffs, mover-order sensitivity, and Kinetic/Energy/Missile interactions before proposing any technology change.

### Python analysis outputs and repository hygiene
The CP103 research analysis stage writes explicit composition, progression-distance, Space-breakpoint, weapon-family, matched-pair dominance-screen, and legacy-overlay CSVs in addition to `analysis.json`. It gates the expected 1,152-row primary shape, 960/128/64 statistical/diversity/named split, 240 four-variant statistical bundles, 96 population cells, exact 13,474,170,720 represented unordered-pair weight, 100-row / 25-diagnostic legacy overlay shape, and zero trial errors. These outputs are screening evidence only and cannot automatically promote a technology value.

The acceptance wrapper invokes CPython with `-B`. Repository ownership checks additionally ignore `__pycache__/` and `.pyc` as generated/local artifacts so direct developer invocation cannot poison the required RepositoryOnly-to-full-run sequence.
