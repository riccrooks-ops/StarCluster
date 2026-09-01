# Checkpoint 34 - Headless C# Calibration Lane and Stable Validation Harness

## Purpose

Checkpoint 34 removes routine technology calibration from the Godot application release path without creating a second rules implementation.

Godot/C# remains the production architecture. `StarCluster.Core` remains authoritative. The change is organizational: balance and technology studies now use a dedicated headless C# solution and a shared data-driven harness.

## Retained mechanical correction

Checkpoint 34 absorbs the unaccepted Checkpoint 33 mechanics and study without changing them:

- Kinetic Cannon fire spends 1 TP.
- Missile launch remains 0 TP.
- Held Kinetic fire earmarks and spends 1 TP when triggered.
- Held Main resolves before PDS.
- successful Held Main interception preserves PDS ammunition and Reaction Capacity;
- a held miss falls through to PDS;
- Shield overcapacity adds 1 temporary SP per activation;
- the TL1 Auxiliary Reactor comparison supplies +1 TP while Operational and +0 in lower conditions;
- the 294-variant correction study remains focused on reactor outputs 3-6.

## Two validation lanes

### Calibration lane

`StarCluster.Calibration.sln` contains:

- `StarCluster.Core`;
- `StarCluster.ScenarioRunner`;
- `StarCluster.Tests`.

The shared harness:

1. verifies the repository manifest;
2. parses PowerShell scripts;
3. reads a versioned checkpoint JSON definition;
4. confirms the pinned SDK;
5. builds the headless solution with warnings as errors;
6. runs engine-independent C# tests;
7. executes each configured ScenarioRunner stage;
8. accepts the run only when every native command returns exit code zero.

No stage inspects README prose, DOCX sentences, workbook cell text, or C# source strings to infer mechanical correctness.

### Integration lane

`StarCluster.sln` remains the full solution and includes `StarCluster.Game`. `tools/integration/run_full_solution_validation.ps1` is reserved for major integration milestones. Routine calibration neither builds nor launches Godot.

## Stable checkpoint definition

`tools/calibration/checkpoints/checkpoint-34.json` declares:

- the SDK and solution paths;
- default trials and worker count;
- output root;
- non-blocking documentation paths;
- the ordered ScenarioRunner commands and arguments.

The Checkpoint 34 wrapper contains no custom validation logic. Future calibration checkpoints should add or change a JSON definition rather than copy another large PowerShell validator.

## Acceptance

Checkpoint 34 is accepted when the Windows calibration command completes with successful exit codes for the build, tests, retained deterministic/calibration lanes, the 294-variant correction study, and ScenarioRunner self-tests.
