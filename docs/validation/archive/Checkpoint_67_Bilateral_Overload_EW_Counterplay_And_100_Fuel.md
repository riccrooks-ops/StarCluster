# Checkpoint 67 - Bilateral Overload/EW Counterplay and 100-Fuel Baseline

## Scope

Checkpoint 67 advances the accepted Checkpoint 66d overload foundation without implementing the full tactical AI.

It makes **100 fuel** the authoritative player-cruiser tactical baseline while preserving 2 fuel per traversed hex, EvM +1, and existing overload fuel costs. It then adds improved overload request/activation telemetry and two controlled counterplay experiments:

- mirrored pre-Movement STL-overload commitments on both sides;
- post-Movement Active Sensor / ECM / ECCM responses using the existing Tactical Power adjustment window.

The existing Tactical Power commitment windows, finite radius-5 map, final-position combat geometry, overload/Strain rules, 5-TP production reactor, and FullVolleyFirst isolation doctrine remain authoritative.

## Native dependency precheck

The **first validation action** must invoke `tools/checkpoints/Test-NativeAcceptanceDependencies.ps1` and reject active acceptance paths that require `python`, `python3`, or `py`. The shared checkpoint harness independently enforces this requirement for Checkpoint 66 and later.

## Required clean-extraction acceptance

From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-67\apply_checkpoint_67.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-67\apply_checkpoint_67.ps1
```

Do not run Deep Calibration unless the normal run or a cross-study concern justifies it.

## Normal suite

The normal suite contains 8 stages. Its only Monte Carlo stage is the 60-variant Checkpoint 67 bilateral overload/EW counterplay study, for **600,000 trials** at the default 10,000 trials per variant.

The study consists of:

- 48 bilateral STL-precommit variants: 3 ordered matchups x 2 symmetric EW controls x 2 movement orders x 4 STL commitment pairings;
- 12 post-Movement EW-response variants: Missile-vs-Missile x 2 movement orders x 6 scripted response packages.

## Required release-gate properties

- all 60 variants complete without trial errors;
- every Checkpoint 67 variant uses starting fuel 100, movement fuel 2/hex, EvM cost 1;
- fuel accounting includes the existing +2 TL1 STL-overload fuel cost on whichever side overloads;
- safe-only STL, Active Sensor, ECM, and ECCM overloads never exceed two mean activations per engagement;
- activation telemetry never exceeds request telemetry;
- power-denied and safe-Strain-limit-denied overload requests are journaled separately and remain a bounded subset of explicit requests;
- both sides exercise pre-Movement STL requests somewhere in the mirrored matrix;
- the post-Movement matrix exercises Side-B ECM overload, Side-A ECCM overload, and reactive Side-A sensor-overload requests;
- the 33-Space non-EW fixture never synthesizes ECM/ECCM power;
- no target win rate is a release gate.

## Interpretation

The purpose is to learn when a legal tactical option is contemplated, requested, actually activated, or denied by Tactical Power / the safe Strain limit, and what it costs. A doctrine may influence Movement as a contingency and then not be needed after the opponent reacts. That distinction is part of the evidence.

Checkpoint 67 does not promote any scripted package to a full AI rule and does not retune sensors, EW, overload values, reactor output, weapon families, map geometry, or fuel costs from the study alone.
