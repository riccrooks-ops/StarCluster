# Checkpoint 101 — TL3 Base Technology Table Completion

## Purpose

Checkpoint 101 completes the **base/standard TL3 conceptual technology table** while retaining native-accepted CP100 as the repository baseline and CP99 foundation v0.8 as the executable TL1/TL2 combat consumer. It deliberately does **not** implement, calibrate, promote, or Monte-Carlo screen TL3 combat mechanics.

## Accepted baseline

CP100 corrected replacement is native-accepted: definition SHA-256 `4d9420008706b2970151159d4041a2b3ad81bad145b8985a1583416f82d54c13`, manifest SHA-256 `e8104cc761e0807414ccf278a7bd9813cdd3ea99cfd5f58dab9ae7cce16faaf6`, SDK 8.0.423, 0 build warnings/errors, 876/876 xUnit tests, 10/10 runner stages, 63 self-tests, zero failed gates, and zero stochastic executions. Embedded evidence is under `docs/validation/evidence/checkpoint-100/`.

## Complete TL3 base candidates

The current machine authority is `docs/design/player_technology/tl3_base_technology_candidates_v0_2.json`. It carries forward the accepted CP100 core and adds the remaining base streams:

- Hull: 36 Installation Space; Hull12/personnel/cargo/one-shuttle values held.
- STL: Move3 / 5 Space; bounded +1 Move overload with current +1 TP/+2 fuel/+1 Strain costs.
- FTL: strategic Move3 / 5 Space; frontier-entry rules held.
- Kinetic Main: +20/DAM4/SPEN1/APEN1/Range4/Ammo100 and 6 Space held; ordinary firing becomes 0 discretionary TP.
- Energy Main: 1TP/DAM2, 2TP/DAM3 and 3TP/DAM4 become safe rated modes; Range5 and standard/high +25/SPEN1/APEN1 held; overload beyond High deferred.
- Missile Main: DAM5/SPEN1/APEN2/Range6/25 Flights/0 TP launch and 6 Space held; TL3 missile drive gives Move4; onboard navigation sensor becomes standard; seeker remains optional and detailed sensor stats remain a later subcomponent profile.
- Kinetic PDS: TL2 base profile held.
- Energy PDS: readiness improves from 2 TP to 1 TP with accuracy/RC held.
- AMM PDS: 1 TP -> RC1 or 2 TP -> RC2; accuracy/ammunition held; two-attempt-per-flight cap and seeded automatic allocation held.

All prior CP100 core candidates remain unchanged: TC +12/-25 + EvComp5; Sensor DR1 Low3/4@1 + High4/5@2 no Strain; efficient ECM2/ECCM2 at 1 TP full strength; 6TP/5Space compact fusion; Shield3 plus optional Hardener; Armor AP1/AI5.

## Base table versus future catalog

A complete **base** row is not a complete equipment catalog. Later checkpoints may add additional Auxiliaries, specialist weapons, detailed missile sensors/seekers, alternate armor packages, magazines, batteries/capacitors, hangars, or pinnacle legacy-family items. A future **Optimum Fission Reactor**, for example, can remain a mature fission-family item improved by later Power research while Mature Compact Fusion remains the standard TL3 reactor.

## Build and power sanity

`tl3_base_build_sanity_v0_1.json` locks deterministic arithmetic only:

| Architecture | TL1/TL2 | TL3 | Result |
|---|---:|---:|---|
| 1 Main / 1 Reactor | 28/35 | 27/36 | 9 discretionary Space |
| 2 Main / 1 Reactor | 34/35 | 33/36 | legal outlier; 3 discretionary Space |
| 1 Main / 2 Reactors | 34/35 | 32/36 | legal outlier; 4 discretionary Space |
| 2 Main / 2 Reactors | 40/35 | 38/36 | **illegal by 2 Space** |

The corrected 40-Space TL1/TL2 arithmetic includes the mandatory Sensor and supersedes stale pre-mandatory-Sensor prose that said 37. The first future effective-space threshold for the bare dual-main/dual-reactor core is 38; a meaningful 3-Space support package raises the threshold to 41. No future TL is assigned to either milestone.

Power remains an operational tradeoff, not a legality filter. A single 6-TP TL3 reactor can fund two Standard Energy shots plus High Active Sensor exactly (4+2=6) but has zero TP left for PDS, ECM/ECCM, Hardening, EvM, or tactical Shield recharge. Two High Energy shots plus High Active require 8 TP and do not fit. Do not add an artificial one-reactor-per-weapon restriction: dual-main single-reactor builds remain family/mode-dependent outliers whose support opportunity cost is the balancing mechanism.

## Standing integration architecture

Suite v0.16 registers 16 TL3 base transition records, including Hull capacity growth, reactor miniaturization, optional Shield-Hardener unlock, safe/readiness mode additions, propulsion performance, missile autonomy, and explicit holds. `tl3CombatConsumerEnabled` remains false. CP99 foundation v0.8 remains byte-identical executable behavior.

A later implementation checkpoint must generalize the legal-build/progression consumer for TL-specific Hull capacity and Space-changing/unlock/mode transitions, implement the owning mechanics, then run actual-consumer preflight plus a tiny full-pipeline smoke before substantive Monte Carlo.


## RepositoryOnly-to-full-run sequence preflight

CP101 validates the actual two-step user flow in one repository tree. The contract creates or recognizes the same `out/checkpoint-101/acceptance-summary.json` and `.txt` artifacts left by RepositoryOnly, verifies they remain generated/local rather than repository-owned, and immediately rechecks the exact manifest-owned path set. The wrapper also removes stale `out/checkpoint-101` before the contract on normal non-`-NoClean` invocations. This prevents a successful RepositoryOnly run from causing the immediately following full run to fail before harness cleanup.

## Native acceptance

CP101 reuses CP100's bounded deterministic native workload: warning-as-error build, 876 xUnit tests, 10 runner stages, 63 self-tests, CP99 exact-edge preflight/generation, and zero stochastic executions. Deep Calibration is not applicable.
