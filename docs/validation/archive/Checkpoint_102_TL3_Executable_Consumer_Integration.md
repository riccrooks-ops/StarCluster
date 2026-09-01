# Checkpoint 102 — TL3 Executable Consumer Generalization and Integration

## Purpose

Checkpoint 102 converts the **native-accepted CP101 TL3 base table** from registered architecture into an executable, data-driven TL1/TL2/TL3 construction/progression/runtime consumer. It changes no accepted CP101 TL3 values and performs no balance calibration or technology promotion.

## Accepted baseline

Checkpoint 101 is native-accepted: definition SHA-256 `31c6fe641a562005af325034c925d76f7339f97827d21cad5989052a4872cba3`, repository-manifest SHA-256 `674912367de56d5dd3775f2535bc768b636dbd625c0583362c3df024ee5d1fab`, native-results ZIP SHA-256 `6320c62576097aed1f7f3060011f174d880cda5ead28576cf19d5fa14408f5d7`, pinned SDK 8.0.423, warning-as-error build with 0 warnings/errors, 876/876 xUnit tests, 10/10 runner stages, 63 self-tests, zero failed gates, and zero stochastic executions. Retained evidence is under `docs/validation/evidence/checkpoint-101/`.

## CP102 executable boundary

The accepted CP101 registry `docs/design/player_technology/tl3_base_technology_candidates_v0_2.json` remains the value authority and is not rewritten. CP102 adds `tl3_executable_implementation_profile_v0_1.json`, v7 construction/progression studies, runtime profile bindings, and executable mechanics. Lifecycle is explicit: **accepted value -> implemented/executable candidate -> calibrated -> promoted**. CP102 stops at implemented/executable.

### Construction

The v7 consumer makes Hull capacity data-driven and enforces the existing mandatory combat core: at least one Main Weapon, one Reactor, and one Sensor. Additional Main Weapons and Reactors are optional; Tactical Power sufficiency remains an operational constraint rather than a construction filter. Shield Hardener is an optional separate component and is legal only with an installed Shield. Same-type ECM/ECCM duplicates remain legal redundancy but never add ratings.

CP102 construction-envelope preflight uses `cross-tl-build-permutation-foundation-v0_9.json` and independently locks: **221,184 raw combinations; 51,264 legal builds; 10,752 exact-fill; 25,536 near-fill; 14,976 underfilled; 0 legal dual-main+dual-reactor builds**. Near-fill is capacity-relative rather than hard-coded to a 35-Space hull.

The accepted TL3 whole-ship sanity remains unchanged: 1W/1R=27/36; 2W/1R=33/36; 1W/2R=32/36; 2W/2R=38/36 and illegal by 2 Space.

### Typed TL2->TL3 progression

The v7 transition consumer no longer assumes that every upgrade is a same-Space increase in a scalar advanced-component count. It represents 16 explicit transitions across these semantic types: capacity integration, capability addition, operating-mode addition, power efficiency, miniaturization, primary performance, optional-component unlock, protection maturation, safe-output maturation, autonomy/propulsion, explicit hold, and readiness-mode addition. Each edge validates its declared installed-Space and Hull-capacity deltas.

`cross-tl-build-permutation-foundation-v1_0.json` independently locks **43,008 raw combinations; 38,400 legal builds; 220,416 legal one-axis TL2->TL3 progression edges; 16 named logical transition pairings; 2 movement-order geometries; 32 generated smoke variants**.

### Runtime bindings

CP102 wires the accepted TL3 mechanics into the existing integrated combat shell without inventing deferred values:

- Tactical Computer: +5 Evasive Compensation offsets only the firing ship's own Evasive penalty, never below zero and never as a positive bonus.
- Sensor: normal Low Active 3/4 @ 1 TP and normal High Active 4/5 @ 2 TP/no Strain are separate data-driven modes; no higher overload is invented.
- ECM/ECCM: Rating 2 full-strength normal operation costs **1 TP total**, not 1 TP per rating. Legacy per-rating behavior remains unchanged when the new full-strength override is absent.
- Reactor/Hull: 6 TP at 5 Space and 36-Space Hull capacity are consumed by construction/runtime data.
- STL/FTL: Move 3 tactical/strategic values are represented; the existing bounded STL overload remains unchanged.
- Shield: Capacity 3 remains; optional 1-Space Shield Hardener consumes 1 TP for SA1 while functional/powered.
- Armor: AP1/AI5 is represented.
- Kinetic Main: ordinary discretionary firing cost 0 TP.
- Energy Main: safe Low/Standard/High rated modes are represented. CP102 smoke selects declared modes; a future tactical UI/AI mode-selection policy remains separate.
- Missile Main: Move 4 and standard onboard navigation-sensor presence are represented. CP102 does **not** invent the deferred detailed navigation-sensor profile or make the optional seeker standard. Existing launcher/terminal Firm rules remain intact.
- Kinetic PDS: explicit TL3 hold. Energy PDS: 1-TP readiness. AMM PDS: preferred 2 TP/RC2 readiness with legal 1 TP/RC1 fallback; seeded automatic threat allocation and the two-attempt-per-flight cap remain unchanged.

## Regression boundary

CP99 foundation v0.8 remains the frozen native-accepted TL1/TL2 regression consumer and must continue to reproduce 11,776 legal builds, 37,184 progression edges, 181 exact-edge strata, 362 logical pairings, and 724 generated variants. CP102 v7 is additive; it must not reinterpret the v6 schema or its legacy transition semantics.

## Corrected replacement 1 — compile-surface repair

The original CP102 candidate passed `-RepositoryOnly` on native Windows, including repository integrity and PowerShell syntax, but the warning-as-error build then failed with four CS1061 errors in `CrossTlBuildPermutationRunner.cs`. The new named-pairing transition validation referenced `edge.LowerBuild.Id` and `edge.HigherBuild.Id`, while `CrossTlProgressionEdge` deliberately exposes endpoint identifiers as `LowerBuildId` and `HigherBuildId`.

Corrected replacement 1 changes those four accesses to the declared ID members. It does not change CP101 TL3 values, v7 construction counts, transition semantics, edge counts, checkpoint workload, seeds, runtime profiles, combat rules, or promotion/calibration status. RepositoryOnly is strengthened with a compile-surface preflight that extracts the declared `CrossTlProgressionEdge` member set, validates every `edge.<member>` use against it, requires the ID-based endpoint bindings, and rejects the stale embedded-object spellings that caused the native failure. The durable Simulation Development Guidelines now require the same class of member-surface preflight when a checkpoint refactors C# consumer interfaces but packaging cannot run the pinned native compiler.

## Corrected replacement 2 — generated-study consumer registration repair

Corrected replacement 1 passed `-RepositoryOnly`, then passed the pinned .NET SDK 8.0.423 warning-as-error build with **0 warnings / 0 errors**, all **876/876 xUnit tests**, the retained deterministic and mechanics corpora, the accepted CP99 v0.8 11,776-build / 37,184-edge / 724-variant regression, the CP102 v7 51,264-build construction-envelope preflight, and the CP102 v7 38,400-build / 220,416-edge / 32-variant transition preflight and generation. The next stage—the generated 32-variant integrated-combat actual-consumer preflight—then failed before any smoke trial ran because `Tl1IntegratedTacticalCombatRunner` rejected the producer-emitted study ID `tl3-cp102-16-transition-integrated-smoke` as unsupported.

The defect was not in the v7 generator or TL3 values. The producer correctly emitted its declared `generatedStudyId`, but the shared integrated-combat consumer retained explicit study-ID registration surfaces that had not been extended for CP102. Corrected replacement 2 therefore registers the CP102 smoke study coherently rather than adding only a one-line whitelist: it adds the 32-variant required-count dispatch, Adaptive Engage/finite-map/operational Sensor-EW classification, generalized build legality, dedicated CP102 coverage validation, stateful build-level power/auxiliary handling so Shield Hardener/PDS behavior is actually exercised, and isolated output routing that writes resolved profiles without invoking an unrelated legacy TL3 review writer.

The dedicated CP102 consumer validation requires the accepted seed/workload/catalog bindings, exactly 22 unique named physical builds, all 16 transition comparison groups mirrored over the two mover-order geometries, TL2-reference -> TL3-candidate profile orientation, accepted AI/track/overload settings, and evidence that every CP102 runtime field family survives producer -> generated JSON -> actual-consumer deserialization. It remains structural/pipeline validation only; it adds no stochastic balance gate.

RepositoryOnly is also strengthened so it reads the authoritative v1.0 producer's `generatedStudyId` and requires the actual consumer to own that exact ID across the relevant dispatch/classification/validation/output surfaces. The durable development guidelines now require this producer/consumer registration check for future generated-study pipelines. No CP101 TL3 value, v7 enumeration count, transition definition, checkpoint definition, seed, workload, runtime profile, Concept document, workbook, or xUnit test changes as part of this correction.

## Corrected replacement 3 — zero-TP direct-fire execution and trial-error diagnostics

Corrected replacement 2 passed `-RepositoryOnly`, the pinned .NET SDK 8.0.423 warning-as-error build with **0 warnings / 0 errors**, all **876/876 xUnit tests**, all retained deterministic/mechanics stages, the accepted CP99 exact-edge regression, both CP102 v7 construction/transition consumers, and the CP102 generated-study actual-consumer preflight. The 32-variant one-trial full-pipeline smoke then executed all variants but failed three shared gates: `no-trial-errors`, `policy-telemetry`, and `attack-layer-telemetry`. The only zero-summary variants were `c102s-021-*` and `c102s-022-*`, which deterministically correspond to the eleventh named transition pairing, `weapon-k2-to-k3`.

The root cause is a real runtime defect in the new TL3 Kinetic maturation path, not three independent gate defects. CP101/CP102 intentionally define TL3 Kinetic ordinary firing as **0 discretionary Tactical Power**. `CommitDirectFire` nevertheless called `TacticalPowerLedger.Spend(0)` unconditionally, while the ledger correctly rejects non-positive spend requests. Missile launch already treated its valid 0-TP cost as a no-op, so the defect was limited to direct fire. The two Kinetic transition trials therefore threw on their first firing opportunity; their zeroed error summaries then caused the policy-telemetry and attack-layer gates to fail secondarily.

Corrected replacement 3 centralizes attack-power spending behind a helper that rejects negative costs, treats 0 TP as a valid no-op, and delegates positive costs to the existing ledger. Direct fire and missile launch both use that helper. The CP102 generated-study preflight now executes a deterministic micro-proof that 0 TP leaves a 6-TP ledger untouched while 1 TP consumes exactly one point. The existing CP102 ScenarioRunner self-test also exercises the same helper and the Kinetic 0-TP override without increasing the expected 70-self-test count. RepositoryOnly additionally requires the v1.0 producer's `k3` option to remain a 0-TP Kinetic weapon and verifies that both attack paths call the zero-safe helper rather than spending the raw cost directly.

Trial-error handling is also hardened. `RunVariant` still counts a failed trial so release gates remain strict, but it now prints the variant ID, trial index, full exception, and stack trace. A future native-only trial failure should therefore expose its cause directly instead of surfacing only as a downstream `no-trial-errors` gate failure. No CP101 TL3 value, v7 enumeration/transition count, checkpoint workload, seed, profile, Concept document, workbook, or balance/promotion status changes in this correction.

## Native acceptance sequence

From a clean full-repository extraction, run exactly:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-102\apply_checkpoint_102.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-102\apply_checkpoint_102.ps1
```

The first run must validate repository contracts, accepted-CP101 provenance, v7 counts/semantics, native dependencies, and checkpoint-definition arithmetic without leaving repository-owned artifacts. The immediately following full run in the same tree must repeat those checks, build warning-as-error, run xUnit, execute all 15 runner stages, complete 70 ScenarioRunner self-tests, generate exactly 32 smoke variants, run their actual-consumer preflight, and execute exactly 32 one-trial smoke trials with zero failed gates/trial errors.

## Interpretation

Passing CP102 proves that the CP101 TL3 architecture is executable through the current construction/progression/combat integration path. It does **not** prove that TL3 is balanced, that any TL3 item is production-promoted, or that TL3 should beat TL2 by a target percentage. Broad cross-TL measurement is intentionally deferred.
