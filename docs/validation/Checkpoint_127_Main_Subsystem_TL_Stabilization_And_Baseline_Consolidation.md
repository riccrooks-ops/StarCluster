# Checkpoint 127 — Main-Subsystem TL Stabilization and Baseline Consolidation

**Corrected Replacement 1:** removes the accidental `openpyxl` dependency from the mandatory preflight, replaces workbook synchronization QA with stdlib OOXML parsing, and adds a stdlib-only import regression. Gameplay values, study scope, and production C# remain unchanged.
**Status:** Candidate pending native Windows acceptance

CP127 follows accepted CP126 full-map fidelity/era attribution. It is the bounded final main-subsystem stabilization pass before broader TL-sensitivity and mixed-/legacy-TL studies.

## Candidate decisions

- restore standard **STL Move = Drive TL**;
- restore **Operational Missile Move = Missile Drive TL + 1**;
- retain FTL as the deliberate strategic **1/2/3/4/4/6/7/9/12** ladder and reconcile the Concept accordingly;
- reduce only TL8 Energy Low/Standard/High damage from **8/11/13 to 7/10/12**;
- retain the TL5→TL6 maturation package unless native attribution identifies a concrete defect;
- preserve all other CP123/CP126 main numerical leaves;
- defer most AUX numerical stabilization.

The delta from `technology_numerical_matrix_v0_3.json` is exactly nine numerical leaves. Historical authorities remain immutable.

## Native acceptance

Run from a clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-127\apply_checkpoint_127.ps1 -RepositoryOnly
```

Then, in the **same extracted tree**, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-127\apply_checkpoint_127.ps1
```

RepositoryOnly performs repository hygiene, the independent CP127 preflight, **170/170 Python tests (including a stdlib-only dependency regression and four-variant actual-consumer micro-smoke)**, warning-as-error .NET build, **907/907 xUnit tests**, **70/70 ScenarioRunner self-tests**, **25/25 accepted C#/Python research-parity fixtures**, the 86,584-variant plan, the 2,250-comparison / 4,500-execution physical-symmetry gate, and the one-trial 86,584-variant full-pipeline smoke. It skips the substantive study.

The normal run repeats those gates and executes **86,584 variants x 100 trials = 8,658,400 engagements**.

Balance findings are review evidence rather than automatic gates. Acceptance requires mechanics/instrumentation integrity and explicit review of the resulting transition/ablation/factorial outputs.
