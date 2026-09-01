# Checkpoint 140 — v22C Stage-A Resource, TP-Telemetry, and Combat-Strata Integration

## Status

Candidate pending native Windows acceptance. CP139 is the native-accepted research-integration baseline. CP140 makes no production C#/Godot combat-mechanics change and does not promote numerical values.

## Purpose

CP140 closes the three integration blockers intentionally left by CP139 before substantive multivariate combat research:

1. bind the six native-validated v22C resource environments as simulation-only in-memory overlays;
2. measure genuine Tactical Power decision pressure using observational counterfactual-demand telemetry without changing EngageAdaptive policy or RNG streams; and
3. bind the ten v22C Stage-A combat/counter strata to executable current mechanics and legal exact-fill 1W/1R reference cruisers.

The accepted CP139 `def-res-v1` research damage model remains opt-in for this study. CP138 `penetration-hardening-v1`, the production numerical matrix, Concept v0.7x, and production C# resolver remain frozen controls.

## Exact Stage-A smoke matrix

The carried v22C experiment manifest contains 8,220 unique scenarios:

- 137 ordered same-TL weapon-pair/TL cells;
- 6 resource environments; and
- 10 combat/counter strata.

The weapon set is Kinetic, Energy, GP Missile, and Swarmer from TL2 onward (TL1 has Kinetic, Energy, and GP Missile). Each pairing therefore has the complete 6 x 10 crossing.

CP140 executes exactly **one trial per scenario**. These 8,220 engagements are execution/telemetry evidence only. The later 500-trial-per-scenario Stage A (4,110,000 substantive trials) remains deferred until CP140 is native accepted.

## Resource overlay boundary

All candidate resource values are applied to `CandidateMatrix` copies in memory. `technology_numerical_matrix_v0_9.json` is never written.

The six carried environments include the CP138 historical control, central/no-major and propulsion-miniaturization candidates, a lower-demand neighbor, and two stress environments. Reactor Operational/Degraded/Emergency values and K/E/M weapon TP bind from the native-validated v22C resource tables. Equal6 and miniaturization Space patterns are applied only to the research matrix copy.

The v22C `ModerateHighDemand` AUX proxy is **not** converted into fictitious Tactical Power demand. Until the corresponding AUX consumers have executable TP mechanics, that label remains provenance-only. CP140 reports executable resource-equivalence classes explicitly; under this boundary R1 and R5 are mechanically identical even though their v22C provenance labels differ.

## Tactical Power conflict telemetry

CP140 instruments the existing canonical policy rather than replacing it. Each turn a shadow policy call with effectively unlimited TP identifies policy-qualified desirable legal actions without RNG or state mutation. Actual allocation remains the existing combat allocation.

A TP conflict requires:

- at least two desirable legal actions;
- at least one desired action not fully funded; and
- total desirable TP demand greater than usable Reactor plus activated-overload TP supply.

Zero TP headroom alone is not a conflict.

The accepted v22C contract requires 47 turn-level fields and 15 battle-level fields. CP140 validates every observed turn, aggregates every battle, and persists a deterministic turn sample (first, final, and first conflict row per side) rather than an unbounded all-turn CSV. This is the storage pattern intended to remain scalable for the later multi-million-trial study.

Instrumentation neutrality is a hard gate: twelve representative encounters are replayed with telemetry disabled/enabled under identical seeds, and the complete pre-existing combat result/telemetry object must be exactly identical.

## Ten executable strata

- `BALANCED_CORE_NO_PDS`: standard Shield + mainline Armor; no PDS/EW extras.
- `KINETIC_PDS_PRESSURE`: Kinetic PDS installed.
- `ENERGY_PDS_PRESSURE`: Energy PDS installed.
- `AMM_PDS_PRESSURE`: AMM PDS installed.
- `SHIELD_PRESSURE`: Shield Hardener installed where technologically available.
- `ARMOR_PRESSURE`: legal armor-centered/no-Shield reference build; no hidden stat bonus.
- `EW_CONTEST`: ECM + ECCM installed.
- `MOBILITY_STANDOFF`: legal six-hex initial separation instead of the normal ten-hex edge start.
- `RECOVERY_ATTRITION`: Shield Hardener where available and a 90-turn ceiling.
- `POWER_CRISIS`: ECM + ECCM + AMM PDS + Shield Hardener where available, starting at range three so multiple real systems can become desirable together. No artificial TP load is injected.

## Runtime hygiene

The telemetry-rich smoke is executed as nine isolated deterministic process batches (eight x 1,024 scenarios plus a final 28-scenario tail), then merged against the exact source-manifest order. This avoids long-lived multiprocessing allocator degradation while preserving scenario IDs, master seed, trial index, and combat RNG identity.

The merge must verify:

- exact contiguous coverage of all 8,220 scenario IDs;
- zero smoke errors;
- exactly two side telemetry observations per executed turn;
- 8,220/8,220 schema-consistent scenarios;
- 16,440 battle telemetry rows;
- 12/12 instrumentation-equivalence replays;
- nonzero TP-conflict telemetry, including `POWER_CRISIS`;
- unchanged source numerical-matrix SHA-256; and
- zero substantive combat trials / no automatic promotion.

The full native invocation reruns all nine batches and requires byte-identical hashes for the merged smoke, battle telemetry, turn sample, instrumentation-equivalence audit, TP-conflict coverage, and resource-equivalence table produced by RepositoryOnly.

## Authoring validation

The authoring environment completed the exact 8,220-case batch/merge contract with:

- 8,220 smoke trials;
- 0 execution errors;
- 352,260 turn telemetry observations;
- 8,220/8,220 turn-schema-consistent scenarios;
- 34,819 persisted deterministic turn-sample rows;
- 16,440 battle rows;
- 12/12 telemetry-off/on outcome-equivalence cases;
- 40,047 observed TP-conflict turns, including 18,965 in `POWER_CRISIS`; and
- unchanged numerical-matrix SHA-256 `3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194`.

These counts prove execution and telemetry coverage only. One-trial winners, damage totals, and TP-conflict frequencies are **not balance evidence**.

## Native acceptance sequence

From a fresh extracted CP140 full repository, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-140\apply_checkpoint_140.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-140\apply_checkpoint_140.ps1
```

The second command must run in the same unchanged extraction. Native acceptance requires Python 3.13.x and .NET SDK 8.0.423 exactly.
