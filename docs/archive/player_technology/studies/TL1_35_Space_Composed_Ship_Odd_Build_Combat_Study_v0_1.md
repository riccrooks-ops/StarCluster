# TL1 35-Space Composed-Ship / Odd-Build Combat Study v0.1

## Purpose

Checkpoint 61 is the first combat study that composes complete TL1 cruiser packages from the accepted Checkpoint 60 **35-Installation-Space** construction envelope. Its job is diagnostic: expose what the legal arithmetic actually does in combat before changing Space costs, component values, or stacking rules.

No win percentage is a promotion target or release gate. A strange legal build is evidence to inspect, not a reason to ban the build by fiat.

## Matrix

Side A rotates through the six legal Checkpoint 60 candidates:

1. `balanced_generalist_major` — 1 weapon, 1 reactor, Active Sensor, Shield, 1 PDS; 33 Space used / 2 free.
2. `dual_main_striker_major` — 2 weapons, 1 reactor, Active Sensor; 34 / 1.
3. `dual_reactor_power_core` — 1 weapon, 2 reactors, Active Sensor; 34 / 1.
4. `pds_saturator` — 1 weapon, 1 reactor, 5 PDS; 35 / 0.
5. `dual_main_dual_pds` — 2 weapons, 1 reactor, 2 PDS; 35 / 0.
6. `shielded_pds_fortress` — 1 weapon, 1 reactor, Shield, 3 PDS; 34 / 1.

Each Side-A package is tested with Kinetic, Energy, and Missile main weapons against a balanced-generalist Side B carrying Kinetic, Energy, or Missile. That produces **6 x 3 x 3 = 54 variants**. Dual-main packages install two copies of the same family in this first pass. Mixed-family two-main loadouts are deliberately deferred so weapon-density effects remain interpretable.

All variants use TL1 production technology, the zero-effect `aux-r53-none-tl1` control, opponent-aware movement from Range 4, normal Component-First Damage Control, base shield recharge where a Shield Generator is actually installed, no Evasive Maneuvering, and no escape/disengagement objective.

## Explicit composition semantics

The composed-ship path does not inherit the historical integrated calibration fixture's implicit Shield, PDS, Evasive Maneuvering, or +1 auxiliary-reactor assumptions. Hardware exists only when the build record says it exists.

A second Main Reactor is a second TL1 Main Reactor and contributes its own condition-dependent Tactical Power output. A second Main Weapon has independent support. Multiple Kinetic PDS installations create a pooled reaction budget. Each armed and functional PDS provides one reaction attempt for the terminal-defense window; reactions are distributed randomly across simultaneous threats before any surviving threat receives a second attempt, and ordinary PDS remains capped at two attempts against the same Missile Flight in that window.

The historical integrated studies keep their legacy one-PDS path so Checkpoint 61 does not silently rewrite old calibration baselines.

PDS ammunition remains a **provisional isolation fixture** in this pass: each installed Kinetic PDS receives the retained 50-round combat budget. This does not settle whether future ship construction represents that magazine inside the 2-Space PDS footprint or with separate support Space. If ammunition endurance materially drives an odd-build result, resolve that architecture before promoting or nerfing the build.

## Sensor isolation limitation

This is an **established-Firm-track combat isolation**, not a sensor/EW campaign study. Active Sensor installation therefore consumes the accepted Space and remains damageable hardware, but it does not receive an artificial direct-fire accuracy bonus and sensorless builds are not denied the study's assumed starting combat solution.

That means a sensorless odd build can reveal the combat value of the Space it spends elsewhere, but it cannot be promoted as a generally superior operational design from this study alone. A later sensor/EW-coupled composed-ship study must test acquisition, track maintenance, ECM, datalink, and loss-of-contact consequences.

## Review signals

The runner writes the normal detailed `variants.csv` plus three Checkpoint-61 review files:

- `composed-build-matrix.csv` — one row per matchup with build facts and combat telemetry;
- `composed-build-rollup.csv` — all-family rollup by Side-A build;
- `composed-build-family-rollup.csv` — rollup by Side-A build and weapon family.

Review power starvation/surplus, attack opportunities, PDS attempts/intercepts, shield absorption, hull damage, combat length, unresolved outcomes, and matchup sensitivity. Win share is reported as evidence but is non-blocking.

## Interpretation rules

If an extreme design is weak, do not automatically buff it. If it is strong, do not automatically ban stacking. First determine *why*: Space opportunity cost, Tactical Power contention, ammunition/endurance, missing Shield/Sensor, concentrated defense, duplicate attack packages, or a mechanical artifact.

Prefer correcting underlying component relationships when a pathology is real. Add a special anti-stacking rule only when the fiction independently requires one and the simpler component math cannot express the desired tradeoff.
