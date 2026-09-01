# Checkpoint 64 - TL1 Track-Aware Movement and Acquisition

## Goal

Validate the opt-in track-aware movement/acquisition doctrine identified by accepted Checkpoint 63b without changing accepted component statistics, reactor output, sensor ranges, EW strength, or weapon-family values.

Checkpoint 64 compares the accepted Checkpoint 63b operational behavior against a doctrine that makes engagement range aware of the Firm-track envelope and lets active sensing obtain the target solution before subsequent PDS/weapon power allocation.

## Locked controls

- Full repository baseline: accepted Checkpoint 63b.
- TL1 player-cruiser Installation Space: 35.
- Production reactor output: 5 Tactical Power per operational main reactor.
- Tactical Power doctrine: FullVolleyFirst.
- Six Checkpoint 60 legal composed builds unchanged.
- Side B: balanced-generalist Missile control with established Firm track.
- Initial range: 4.
- Firm remains required for all main-weapon fire/launch authorization in this diagnostic.
- Passive/active sensor envelopes and EW1 range pressure are unchanged from Checkpoint 63b.
- No target win rate is a release gate.
- Contextual/latent capabilities such as Energy APEN remain protected from premature rebalance conclusions.

## New opt-in controls

`TrackAwareOpponentRange` caps the ship's opponent-aware useful range at the maximum Firm range it can support while preserving its ready full volley when possible. It does not guarantee closure; equal-or-faster opposition may preserve standoff.

`AcquisitionFirstAutoActive` uses passive sensing for free when possible. When Firm requires Active sensing after movement, it funds the minimum useful active setting before defensive allocation. This can reduce the number of weapons that ultimately fire if the power budget is tight.

Historical studies retain `OpponentAwareRange` and their previous track policies.

## Normal acceptance workload

The current Monte Carlo study is:

**6 builds x 3 Side-A weapon families x 5 paired regimes = 90 variants / 900,000 default trials.**

The paired regimes are:

1. Established Firm + legacy opponent-aware movement, clear.
2. Checkpoint 63b AutoActive + legacy opponent-aware movement, clear.
3. Track-aware movement + AcquisitionFirstAutoActive, clear.
4. Checkpoint 63b AutoActive + legacy opponent-aware movement, EW1.
5. Track-aware movement + AcquisitionFirstAutoActive, EW1.

The normal suite has **8 stages**.

## Acceptance commands

From a clean extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-64\apply_checkpoint_64.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-64\apply_checkpoint_64.ps1
```

The default Monte Carlo workload uses `--jobs 24`.

## Deep Calibration

Do **not** run Deep Calibration for routine Checkpoint 64 acceptance unless the normal suite exposes a broader regression. The new movement mode and track policy are opt-in, so historical stochastic studies retain their accepted execution path.

If deliberately requested:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-64\apply_checkpoint_64.ps1 -DeepCalibration
```

Deep Calibration is **23 stages / 1,350 Monte Carlo variants / 13,500,000 default trials**.

## Interpretation

The new doctrine is expected to fix self-inflicted unusable range choices, particularly active-sensor/EW breakpoints. It is **not** expected to make sensorless ships magically close on equal-speed opponents that deliberately preserve standoff. Such standoff is an authentic advantage of longer sensor reach.

Review movement, range, Firm/Approximate/NoTrack evaluations, track-denied attacks, active-sensor Tactical Power, insufficient-power preventions, attack execution, and downstream combat outcomes. Do not automatically change sensor Space cost, EW, reactor output, Missile rules, or weapon-family values from these results alone.
