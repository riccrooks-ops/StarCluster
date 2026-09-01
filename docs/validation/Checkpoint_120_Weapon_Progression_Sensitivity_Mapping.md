# Checkpoint 120 - Weapon Progression Sensitivity Mapping

> **Superseded by Checkpoint 121.** CP120 combat outcomes remain valid, but its derived Missile terminal hit-rate summaries read terminal hits from the attacking side even though guidance attempts/hits are recorded on the target side. CP121 preserves the original native archive and regenerates the affected summaries without rerunning combat. CP119 remains the accepted baseline until CP121 native acceptance.


## Objective

Map the numerical sensitivities around the simplified CP117-CP119 weapon architecture before narrowing or promoting values. Mechanics remain frozen: GP Missile yield only, TL2+ two-packet Swarmer with bounded coverage/PDS saturation, automatic Kinetic single-axis progression controls, and native Energy reference.

## Accepted baseline

Checkpoint 119 native acceptance is embedded under `docs/validation/evidence/checkpoint-120/checkpoint-119-native-results.zip` and is the accepted baseline for CP120.

## Scope

- 4,284 mirrored variants.
- 2,952 Missile / 1,008 Kinetic / 324 Energy reference variants.
- 3,060 TL1-TL6 primary variants; 576 TL7 advanced; 648 TL8-TL9 endpoint/stress.
- 135 exact-fill underlying builds.
- Six legal same-TL targets plus three controlled sensitivity fixtures.
- 32 Missile profiles, six Kinetic profiles, one Energy reference profile.
- 22 declared sensitivity comparisons and nine synthesized progression paths.
- Checked-in authoring: 5 trials/variant = 21,420 engagements.
- Native substantive: 2,000 trials/variant = **8,568,000 engagements**.
- No production/runtime, Concept, CP109 matrix, CP110 Reactor, or player-authority promotion. No automatic promotion is permitted.

## Required native sequence

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-120\apply_checkpoint_120.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-120\apply_checkpoint_120.ps1
```

The normal invocation reruns deterministic preflight, all Python self-tests, C#/Python parity, CP114/115a/116/118/119 one-trial regression smokes, the full CP120 one-trial smoke, and then the 8.568-million-engagement substantive study.

## Interpretation boundary

Outcome rates are review information only. CP120 is designed to map slopes, breakpoints, and interactions so a later human-reviewed narrowing/promotion checkpoint can select a robust candidate region. It must not automatically select the highest win-rate profile.
