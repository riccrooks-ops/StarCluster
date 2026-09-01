# Checkpoint 80 - TL2 EW Power Pressure and Tall Viability

## Purpose

Checkpoint 80 follows accepted Checkpoint 79a without promoting its TL2 Sensor/EW candidates. CP79a showed that Sensor DR1, ECM2, and ECCM2 produce the intended mechanical tall-versus-wide EW relationships, but also showed that brute-force ECCM2 at 2 Tactical Power can sharply compete with offense and PDS on a power-hungry ship.

CP80 asks whether that pressure is a healthy technology/build tradeoff or whether it systematically punishes tall/skewed progression. Higher-TL equipment is allowed to require more Tactical Power; power efficiency is a separate progression axis. The guardrail is that higher technology must still broaden or improve viable solutions rather than make advanced equipment a routine self-trap.

## Frozen architecture

- Accepted CP79a Sensor/EW candidate mechanics remain unchanged: Sensor DR1; ECM/ECCM normal rating ceiling 2; 1 TP per normal EW rating.
- TL1 production reactor output remains 5 TP.
- 6 TP is used only as a diagnostic sensitivity and is not promoted by this checkpoint.
- Sensor range and Sensor/ECM/ECCM overload behavior remain unchanged.
- The legacy TL2 Tactical Computer +12 ordinary-targeting candidate remains excluded.
- The TL1 Tactical Computer degraded-fire value remains -25 percentage points when an explicit study-only direct-fire weapon capability permits Approximate-track fire.
- No production weapon gains degraded fire.
- Ordinary missiles and missile interception retain their accepted Firm-terminal architecture.

## Study design

The actual-consumer study is `tl2-itc07-ew-power-pressure-tall-viability` with 72 variants: 12 combat contexts x 6 response packages.

The 12 contexts cover Kinetic and Energy Side-A direct-fire ships against both Missile and Kinetic opponents, with fixed range-3 controls plus Side-A-first and Side-B-first dynamic movement-order contexts. This yields 36 missile-pressure variants and 36 direct-fire-pressure variants.

Each context compares:

1. Firm reference at 5 TP.
2. Wide TL1 Sensor DR0 + ECCM2 at 5 TP.
3. Tall TL2 Sensor DR1 + ECCM1 at 5 TP.
4. Explicit -25 degraded-fire fallback with no ECCM at 5 TP.
5. Wide TL1 Sensor + ECCM2 at 6 TP, sensitivity only.
6. Tall DR1 + ECCM1 at 6 TP, sensitivity only.

At default settings the substantive study executes 72 x 10,000 = 720,000 trials. It is preceded by a 72-variant one-trial full-pipeline smoke.

## Review evidence

The review should compare, by weapon family, opponent type, geometry, and reactor sensitivity:

- conditional win share and unresolved outcomes;
- track quality and ECCM/ECM activation;
- Tactical Power spent and insufficient-power prevention;
- direct-fire attempts and realized hit chance;
- missile launches;
- PDS attempts/intercepts;
- shield/hull pressure and engagement duration.

The most important comparison is not a predetermined win-rate target. It is whether the tall DR1 + ECCM1 path remains a viable contemporary solution, whether the wide old-Sensor + ECCM2 path is meaningfully more power-expensive without becoming universally bad, and whether -25 degraded fire remains a useful fallback rather than an easy replacement for proper counter-EW.

## Promotion policy

Successful execution does **not** promote Sensor DR1, ECM2, ECCM2, 6-TP reactor output, a new power-efficiency value, or degraded fire into production. Results require human review before the Technology Architecture Matrix or runtime data is changed.

## Native acceptance

Run repository validation first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-80\apply_checkpoint_80.ps1 -RepositoryOnly
```

Then run normal acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-80\apply_checkpoint_80.ps1 -Jobs 24
```

Expected normal workload: 11 runner stages, approximately 863 unit tests unless unrelated counts change, 47 ScenarioRunner self-tests, 72 smoke trials, 72 substantive variants / 720,000 default substantive trials, zero failed gates, and zero trial errors.

Deep Calibration is not required unless normal acceptance exposes a broader regression.
