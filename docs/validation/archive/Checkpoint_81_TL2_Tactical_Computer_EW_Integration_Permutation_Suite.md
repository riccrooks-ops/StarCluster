# Checkpoint 81 - TL2 Tactical Computer EW Integration Permutation Suite

## Purpose

Checkpoint 81 follows accepted Checkpoint 80. CP80 supplied strong current-architecture evidence for Sensor DR1, ECM2, and ECCM2 at 1 TP/rating while demonstrating that old-Sensor + ECCM2 power pressure is a support/build tradeoff rather than broken EW mechanics. CP81 now revalidates the historical TL2 Tactical Computer **+12 percentage-point ordinary-targeting candidate** against the TL1 +10 control in that richer environment.

The second purpose is architectural: CP81 begins a standing, data-driven **Technology Integration Permutation Suite** so future technology checkpoints can reuse common scenario axes and paired candidate/control coverage rather than inventing a wholly bespoke Monte Carlo study for every subsystem group.

## Frozen architecture

- TL1 Tactical Computer ordinary targeting remains the production/working **+10 pp Operational** reference.
- The historical **+12 pp** value is a study candidate only; CP81 does not create a production TL2 Tactical Computer profile.
- Computer-owned degraded fire remains **-25 pp** for an explicitly capable direct-fire weapon; no production weapon receives that capability.
- Evasive Compensation remains **0**.
- CP80 Sensor/EW candidate mechanics are held: Sensor DR1; ECM/ECCM normal rating ceiling 2; 1 TP per rating.
- Production reactor output remains **5 TP**; CP81 does not use or promote the CP80 6-TP sensitivity.
- Sensor range and Sensor/ECM/ECCM overload behavior remain unchanged.
- TL1 weapons, defenses, PDS, movement/fuel, Damage Control, and ordinary missile Firm-terminal rules remain unchanged.

## Standing permutation suite

The machine-readable suite definition is `docs/design/testing/technology_integration_permutation_suite_v0_1.json`, with architecture guidance in `Technology_Integration_Permutation_Suite_Architecture_v0_1.md`.

The CP81 active submatrix is the actual-consumer study `tl2-itc08-tactical-computer-ew-integration-permutations` with **96 variants**:

- Side-A direct-fire family: Kinetic or Energy;
- opponent family: Missile or Kinetic;
- geometry: fixed range 3, dynamic Side-A-first, or dynamic Side-B-first;
- EW package: Firm reference, wide old-Sensor + ECCM2, tall DR1 + ECCM1, or explicit -25 degraded fire with no ECCM;
- Side-A Tactical Computer ordinary-targeting value: +10 or +12 pp.

This is 12 comparison groups x four EW packages x two computer candidates. All variants use the accepted 5-TP reactor output. The two computer candidates share the same comparison-group random salt within a context, providing common-random-number pairing for the subtle +2 pp change.

## What the +12 candidate owns

The Tactical Computer override changes the current ordinary direct-fire targeting assistance and the corresponding main-computer assistance to direct-fire PDS. It does **not** change the -25 degraded-fire penalty, create Evasive Compensation, improve Sensor reach/discrimination, alter ECM/ECCM rating, or grant missile terminal degraded fire. Existing missile guidance calculations retain their separate guidance architecture.

## Review evidence

Review +12 minus +10 paired deltas by weapon family, opponent type, geometry, and EW package. Important telemetry includes:

- conditional win share and unresolved outcomes;
- direct-fire attempts, hits, and realized final hit chance;
- PDS attempts/intercepts under missile pressure;
- track quality, ECM/ECCM use, and Tactical Power competition;
- engagement duration and damage pressure;
- whether +12 produces broadly consistent modest benefit rather than a new dominant interaction;
- whether the relative value of contemporary DR1+ECCM1 versus wide ECCM2 and -25 degraded fire remains intact.

No target win-rate or desired +2-pp outcome is a release gate. Promotion requires human review.

## Promotion policy

Successful execution does **not** automatically promote the +12 Tactical Computer candidate, Sensor DR1, ECM2, ECCM2, a reactor change, degraded fire, Evasive Compensation, or any production weapon capability. The Technology Architecture Matrix is updated only after review.

## Native acceptance

Run repository validation first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-81\apply_checkpoint_81.ps1 -RepositoryOnly
```

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-81\apply_checkpoint_81.ps1 -Jobs 24
```

Expected normal workload: 11 runner stages, approximately 863 unit tests unless unrelated counts change, 48 ScenarioRunner self-tests, 96 smoke trials, 96 substantive variants / 960,000 default substantive trials, zero failed gates, and zero trial errors.

Deep Calibration is not required unless normal acceptance exposes a broader regression.
