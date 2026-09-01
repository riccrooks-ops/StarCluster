# Checkpoint 100 — TL3 Core Technology Table Foundation

## Purpose

Checkpoint 100 advances Star Cluster's technology roadmap into the first explicit TL3 core package while keeping executable combat behavior pinned to the native-accepted CP99 TL1/TL2 consumer. It is deliberately a technology-architecture checkpoint rather than another narrow balance study.

## Native-accepted baseline

CP99 corrected replacement 2 is the baseline. Embedded evidence records:

- checkpoint-definition SHA-256 `e5bf5312ab520a425df0fbf63d796e98f35b51d5110260edab1856f54af7d508`;
- repository-manifest SHA-256 `f04186733fa1631bc0ee8384fe4e49f18e65dc07aba04e877773e402d4d56894`;
- 876/876 xUnit tests, 23/23 stages, 63 self-tests, zero failed gates;
- 11,776 legal builds and 37,184 exact TL1->TL2 progression edges;
- primary exact-edge summary SHA-256 `dd05e92896a273f55ea486e3ba8cbe340556fde75a018e19aea1e1877f9849a0`.

## Initial TL3 core candidates

| Stream | Candidate |
|---|---|
| Tactical Computer | Ordinary +12 and Approximate penalty -25 held; Evasive Compensation +5 pp |
| Sensor | DR1/passive reach held; Low Active 3/4 @1 TP; High Active 4/5 @2 TP, no Strain; overload beyond High deferred |
| ECM | Rating 2 held; full-strength normal operation 1 TP total |
| ECCM | Rating 2 held; full-strength normal operation 1 TP total |
| Reactor | Mature Compact Fusion: 6 Operational TP / 5 Space; current 3/1/0 damaged-state output held initially |
| Shields | Primary Capacity 3 held; optional 1-Space Shield Hardener sustains 1 TP for Shield Armor 1; normal hardening nonstacking; overload deferred |
| Armor | AP1 / AI5 |
| Weapon penetration | Kinetic SPEN1/APEN1, Energy SPEN1/APEN1, Missile SPEN1/APEN2 all held |

This is a partial core package. TL3 weapon-family, PDS, STL/FTL, and broader Auxiliary progression remain deliberately open.

## Progression architecture change

Standing suite v0.15 registers seven TL3 progression transitions/types without activating them in combat. CP99 foundation v0.8 remains byte-identical and executable.

The key architectural expansion is that future progression is not limited to same-Space replacement edges:

- Computer, Sensor, ECM, ECCM, and Armor are same-footprint capability/property transitions.
- Reactor TL2->TL3 is a miniaturization transition with Installation Space delta -1.
- Shield TL3 introduces an optional Shield-Hardener unlock; the +1 Space applies only when the component is installed.
- Weapon penetration has no TL3 edge because the core candidate deliberately holds those profiles.

`tl3CombatConsumerEnabled` remains false. A later checkpoint must implement mechanics/legal-build semantics, then run actual-consumer preflight and one-trial smoke before any substantive TL3 Monte Carlo.

## RepositoryOnly contract

The CP100 contract must fail before build/tests if any of the following drift:

1. accepted CP99 provenance or an undeclared frozen CP99 file;
2. the CP99 v0.8 executable foundation;
3. the agreed TL3 core values across machine profile, Matrix, workbook, Concept, or catalogs;
4. suite v0.15 transition type, Space delta, or runtime-activation boundary;
5. Shield Hardener gains an arbitrary Power/Hull TL prerequisite, additive stacking, or an undeclared overload;
6. a placeholder TL3 weapon/PDS/STL/FTL progression is invented;
7. checkpoint stage/trial accounting;
8. PowerShell 5.1 type/interface compatibility;
9. root manifest integrity.

The human-readable authority checks use stable semantic anchors rather than a single editorial phrase. Exact runtime state remains owned by the machine-readable assertions, including `tl3CombatConsumerEnabled=false`, the CP99 v0.8 executable foundation binding, the seven registered TL3 transition IDs/types, and the agreed numerical candidates. This prevents wording-only differences such as "not yet combat-consumer enabled" versus "not runtime activation" from becoming false acceptance failures.

## Native acceptance

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-100\apply_checkpoint_100.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-100\apply_checkpoint_100.ps1
```

Expected normal acceptance:

- SDK 8.0.423;
- warning-as-error clean build;
- 876 xUnit tests;
- 10 runner stages;
- 63 ScenarioRunner self-tests;
- zero stochastic trial executions;
- zero failed deterministic gates.

Deep Calibration is not applicable.
