# Checkpoint 87 - Cross-TL Legal-Build Permutation Foundation

## Purpose

Checkpoint 87 moves Star Cluster from predominantly focused TL2 causal studies into the first reusable **cross-progression legal-build/permutation pipeline**. It does not attempt to exhaustively balance every TL1/TL2 combination in one pass. Instead, it proves that the repository can deterministically enumerate a declared legal technology envelope, preserve mixed-generation builds, generate a bounded representative integrated-combat study, pass that generated study through the real combat consumer, and reject dynamic lanes that lose otherwise available combat activity.

The active Game Concept remains `Star_Cluster_Game_Concept_v0.6x.docx` and is unchanged from accepted CP86a. CP87 changes simulation/integration architecture and current technology working data, not gameplay rules.

## Carried technology state

CP87 carries the current locally validated working candidates into integration rather than reopening their focused studies:

- TL2 information control: Tactical Computer +12 targeting, Sensor DR1, ECM2/ECCM2 ceilings;
- TL2 Reactor: 6 Operational Tactical Power / 6 Space;
- TL2 Shield: Capacity 3 / 3 Space;
- TL2 Armor: AP0 / AI5;
- TL2 Kinetic penetration: SPEN1 / APEN1;
- Energy penetration remains SPEN1 / APEN1;
- Missile penetration remains SPEN1 / APEN2.

Kinetic SPEN2, AP1 Armor, Energy SPEN2, and other non-promoted sensitivities remain available as historical/experimental evidence but are not silently inserted into the first working-envelope screen.

## Deterministic legal-build foundation

The machine definition is:

`src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/cross-tl-build-permutation-foundation-v0_1.json`

The first foundation uses one fixed 12-Space cruiser shell plus eight independently selected technology axes:

- Weapon: Kinetic TL1, Kinetic TL2 APEN1, Energy current, or Missile current;
- Reactor: TL1 5 TP or TL2 6 TP;
- Tactical Computer: +10 or +12 targeting;
- Sensor: Balanced DR0 or DR1;
- Shield: Capacity 2 or 3;
- Armor: AP0/AI4 or AP0/AI5;
- ECM: rating 1 or 2;
- ECCM: rating 1 or 2.

Every option combination exactly fills the current 35-Space shell, so the declared foundation contains **512 legal builds**. This is a first configurable envelope, not a claim that the future universal enumerator has only these axes/options.

The deterministic generator records the complete potential pairing envelope (**262,144 oriented pairings / 131,328 unordered-with-self pairings**) but does not run high-trial Monte Carlo over all of them.

## Bounded executable slice

Thirteen named recipes cover complete TL1 anchors, contemporary TL2 working packages, isolated Kinetic subsystem advances, grouped information-control and power/defense advances, and mixed-generation designs. Six pairing groups expand to **64 ordered logical pairings**.

Each logical pairing generates three contexts:

1. fixed Range 3 / simultaneous;
2. TrackAware dynamic movement / Side A moves first; and
3. TrackAware dynamic movement / Side B moves first.

The generated study therefore contains **192 variants**. At the default 10,000 trials per variant, the substantive workload is **1,920,000 trials**, preceded by a 192-trial one-per-variant smoke.

## Generated-study release chain

The normal checkpoint runs the native generator twice: first as a deterministic preflight, then as generation. The generated `generated-integrated-combat-study.json` must subsequently pass:

- the actual integrated-combat consumer's preflight;
- a one-trial-per-variant full-pipeline smoke; and
- the substantive screen.

This prevents generator-only/schema-only success from masquerading as consumer validation.

## Attack-eligibility / combat-activity guard

CP86a exposed a reusable doctrine-quality failure: a dynamic movement policy can choose a physically valid weapon range that is unusable under its current track/guidance requirements. CP87 therefore uses `TrackAwareOpponentRange` for dynamic contexts and adds a release gate comparing each dynamic lane to its fixed Range-3 reference.

If the fixed reference materially uses direct fire or missile launches, both dynamic movement-order lanes must preserve nonzero use of that attack type unless a future study explicitly declares a no-fire/search/withdrawal control. A self-induced zero-shot/zero-launch lane is a study-quality failure, not balance evidence.

The durable simulation rule is documented in `Simulation_Development_Guidelines.md`; the reusable opponent-AI lesson is documented in `AI_Doctrine_Registry_Architecture_v0_4.md`.

## Promotion boundary

CP87 is an integration/screening checkpoint. Outcome deltas, rankings, complete-TL comparisons, mixed-generation advantages, and progression-shape evidence require human review. Passing CP87 automatically promotes no candidate from local-working status to cross-TL-validated or production status.

## Acceptance commands

Repository/contracts only:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-87\apply_checkpoint_87.ps1 -RepositoryOnly
```

Normal native acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-87\apply_checkpoint_87.ps1 -Jobs 24
```

Optional Deep Calibration (not recommended initially):

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-87\apply_checkpoint_87.ps1 -Jobs 24 -DeepCalibration
```
