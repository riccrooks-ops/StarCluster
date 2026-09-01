# Checkpoint 87a - CP87 Study-ID Integration Contract Hotfix

## Purpose

Checkpoint 87a is a native-acceptance contract hotfix for Checkpoint 87. The CP87 cross-TL legal-build/permutation foundation, generated 192-variant integrated-combat screen, ScenarioRunner implementation, candidate values, Concept v0.6x, Technology Architecture Matrix, standing integration suite v0.7, AI doctrine v0.4, workloads, and release gates are unchanged.

The first native `-RepositoryOnly` run reached the IntegratedCombatRunner study-ID contract and exposed a validator/implementation-style mismatch. The CP87 runner centralizes the generated study ID in the named constant `CrossTlBuildPermutationScreeningStudyId` and uses that constant throughout dispatch, validation, study-family classification, release-gate routing, report routing, and stateful-combat handling. The CP87 contract incorrectly required the literal string `tl2-itc13-cross-tl-build-permutation-screening` to appear at least ten times. Because the literal correctly appears only once at the constant declaration, the contract rejected a fully registered named-constant implementation.

CP87a fixes the contract to validate the actual integration architecture: the literal study ID must be bound exactly once through the named constant, the named constant must appear throughout the required integration paths, and the existing explicit hook checks must all remain present. This preserves centralized IDs and strengthens the contract without weakening coverage.

## Scope

No gameplay, simulation, generator, scenario, candidate, stochastic topology, report, release-gate, Concept, Matrix, standing-suite, AI-doctrine, or development-guideline content is changed. The substantive study remains **192 variants / 1,920,000 default substantive trials**, preceded by a 192-trial one-per-variant full-pipeline smoke. The deterministic legal-build foundation remains **512 exact-fill builds**, representing **262,144 oriented** or **131,328 unordered-with-self** potential pairings. Deep Calibration remains optional and unchanged.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-87a\apply_checkpoint_87a.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-87a\apply_checkpoint_87a.ps1 -Jobs 24
```

Optional Deep Calibration:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-87a\apply_checkpoint_87a.ps1 -Jobs 24 -DeepCalibration
```

## Promotion boundary

Identical to CP87: generated cross-TL outcomes are screening evidence for human review. No technology candidate, doctrine, or balance value is automatically promoted by a successful release gate or ranking.
