# Checkpoint 132 - Canonical Combat Kernel and Defense Semantics

## Status

**Accepted - Corrected Replacement 5 native Windows acceptance completed successfully on 2026-08-19.**

Native acceptance passed 196/196 Python tests, the warning-as-error .NET SDK 8.0.423 build, 910/910 xUnit tests, 70/70 ScenarioRunner self-tests, the top-level and TL1 Phase-A deterministic corpora, 25/25 research parity cases, and 6/6 canonical-kernel tests with zero failed gates. The accepted native-results ZIP SHA-256 is `5b454578e4e24836a9defeabc6309719ab8d9844b679de9c2a94040d21f1a564`.

Checkpoint 131 remains accepted late-Missile research evidence under the pre-CP132 damage implementation. Its native acceptance summary and original results ZIP are preserved under `docs/validation/evidence/checkpoint-132/accepted-cp131/`. Checkpoint 128 remains the frozen numerical technology authority. CP132 changes mechanics/simulation architecture and documentation but changes no current TL1-TL9 technology value.

## Corrected Replacement 5

The Corrected Replacement 4 native Windows `-RepositoryOnly` run passed CP132 preflight, all **196/196 Python self-tests**, the warning-as-error C# build, **910/910 xUnit tests**, **70/70 ScenarioRunner self-tests**, and the top-level deterministic scenario corpus. The TL1 Phase-A deterministic corpus then isolated exactly two stale expected values in `tl1-a11-weapon-resource-packets`: `a11-c03` (standard Energy) and `a11-c04` (Missile). Both still expected pristine Hull 12 after a hit even though the new APEN-bypass model correctly sends one point through unhardened AP0 Armor, leaving Hull 11. Corrected Replacement 5 changes only those active scenario expectations to assert one point of Armor bypass/Hull damage, removes their legacy `effectiveProtection`/`damagePrevented` assertions, and makes preflight/contract enforce the canonical outcome. Scenario inputs, baseline numerical values, production gameplay, Concept v0.7t, Python research mechanics, shared fixture values, and technology values are unchanged from Corrected Replacement 4.

## Corrected Replacement 4

The Corrected Replacement 3 native Windows `-RepositoryOnly` run passed CP132 preflight, all **196/196 Python self-tests**, and the warning-as-error C# build. The improved xUnit wrapper then completed the full suite and isolated exactly one failure: `CanonicalCombatKernelFixtureTests.SharedFixtureMatchesCanonicalLayeredDamageContract` (909/910 passed). One shared fixture intentionally has `damageToArmor = 0`; the canonical resolver correctly emits no `ArmorLayerDamageResolution` when Shield Capacity absorbs the entire packet, but the C# fixture test unconditionally called `Assert.Single(result.ArmorLayers)`. Corrected Replacement 4 fixes only that fixture-representation assertion: zero Armor-reaching damage requires an empty diagnostic collection, while positive Armor-reaching damage still requires exactly one diagnostic for the fixture single armor layer. Preflight/contract now enforce the branch. No production gameplay code, Concept rule, Python research mechanic, scenario definition, shared fixture value, or technology value changes from Corrected Replacement 3.

The failing fixture was `hardening-does-not-delete-ordinary-damage`: DAM 4 / SPEN 0 / APEN 0 against SC 6 / SA 2 leaves SC 2 and sends **zero** damage to Armor. Because no damage reaches Armor, the C# resolver's `ArmorLayers` diagnostics collection is correctly empty. The shared fixture still records zero-valued Armor outcome fields so Python and C# can compare the semantic outcome; the C# test now treats those fields as expected zeros without requiring a fabricated resolution record.

## Corrected Replacement 3

The Corrected Replacement 2 native Windows `-RepositoryOnly` run passed CP132 preflight, all **196/196 Python self-tests**, and the warning-as-error C# build. It then reached xUnit and exposed three active calibration assertions that still encoded the superseded pre-CP132 defense semantics: two TL1 Kinetic duel tests treated AP as generic damage reduction / APEN as suppression of that reduction, and the Shield Hardener test treated SA as deletion of ordinary packet damage. Corrected Replacement 3 synchronizes all three tests with `penetration-hardening-v1`: AP/SA are penetration hardening only, AP remains persistent, and SA redirects SPEN-eligible damage into Shield Capacity rather than deleting it. The xUnit wrapper now lets `dotnet test` complete and write the full TRX before acceptance evaluates the exit code/counts, so any future regression exposes the complete failure set. No production gameplay code, Concept rule, Python simulation mechanic, scenario definition, or technology value changes from Corrected Replacement 2.

The stale xUnit assertions were active current-contract tests, not frozen historical evidence, so their expected behavior must follow the CP132 canonical resolver. The updated TL1 Kinetic probes now confirm that AP 2 does not slow an APEN-0 duel and that AP 2 fully hardens APEN 2 without being consumed; both retain the six-turn all-hit baseline. The Shield Hardener probe uses SC 4 so SA 1 versus SPEN 1 visibly moves one point from Armor exposure back into Shield Capacity while conserving total packet damage.

## Corrected Replacement 2

The Corrected Replacement 1 native Windows retry passed preflight and **196/196 Python tests**, then failed at the warning-as-error C# build because `CanonicalCombatKernelFixtureTests.cs` lacked imports for the production `StarCluster.Core.Combat` and `StarCluster.Core.Combat.Damage` namespaces. Corrected Replacement 2 added only those test imports plus preflight/contract guards that require them. No gameplay mechanic, Concept rule, simulation mechanic, scenario content, or technology value changed in that correction.

## Corrected Replacement 1

The original authored CP132 wrapper incorrectly captured Python `unittest` stderr under Windows PowerShell 5.1 with `ErrorActionPreference = Stop`, producing `NativeCommandError` from normal progress output. Corrected Replacement 1 restored the native-proven direct unittest invocation pattern while preflight separately enforces the 196-test and 6 canonical-test counts.

## Why this checkpoint exists

The project identified a mismatch between the intended layered-defense concept and the implemented resolver. The intended model uses Shield Capacity (SC) and Armor Integrity (AI) as durability, with Shield Armor (SA) and Armor Protection (AP) as hardening against SPEN/APEN. The pre-CP132 implementation instead used SA/AP as generic packet damage reduction and allowed post-AI damage to strip AP as if AP were another durability pool.

At the same time, research mechanics had accumulated across multiple consumers. The project now needs a single ordinary combat implementation so future CREW damage, Damage Control, self-repairing Armor, range rules, and similar mechanics can be added once and inherited by later studies.

## CP132 changes

### Production C#

- `LayeredDamageResolver` now implements `penetration-hardening-v1`.
- SC and AI are the ordinary defensive durability pools.
- SA reduces SPEN only while SC > 0.
- AP reduces APEN only while AI > 0.
- SA/AP do not delete ordinary damage and are not consumed.
- AP is no longer damaged after AI reaches zero.
- The visible `TacticalTurnPhase` sequence explicitly includes Electronic Warfare between Movement and Direct Fire.
- Production unit tests cover the revised damage semantics and phase cursor.
- The active TL1 Phase-A deterministic damage scenarios are synchronized to the same hardening model; obsolete destructible-AP expectations are removed.
- Three existing Missile deterministic scenarios plus the full-flight action builder gain only the additional Electronic Warfare phase advance needed by the six-phase turn.
- Shared fixture tests consume the same JSON contract as Python.

### Python research

- `canonical_mechanics.py` owns pure deterministic parity-critical layered damage.
- `canonical_combat.py` is the normal finite-System-Map encounter orchestrator for new research.
- `full_map_ecology.py` is a compatibility facade and no longer owns a separate full-map implementation.
- CP126+ active full-map consumers route through the canonical combat module.
- Common legacy damage helpers delegate to the canonical pure resolver so reruns do not silently retain the obsolete SA/AP model.
- Direct Fire now commits only direct-fire attacks; Missile launch is executed in Missile / Interception; successful packages resolve centrally in Damage.
- Damage Control is an explicit central no-op hook until repair/CREW/component mechanics are added.

### Documentation

- Active Concept advances to v0.7t and defines the penetration-hardening model.
- `docs/development/Canonical_Combat_Simulation_Kernel.md` becomes the durable executable research contract.
- Simulation Development Guidelines require new studies to use the canonical kernel and explicit experimental overrides.
- Root/bootstrap documentation identifies the CP132 boundary and preserves CP131 as historical evidence under its recorded mechanics.

## Standard canonical encounter contract

- radius-5 finite System Map / 91 cells;
- starts at `(-5,0)` and `(5,0)`, range 10;
- before legitimate contact, exactly one observer-safe hex toward map center per activation;
- visible phases: Movement -> Electronic Warfare -> Direct Fire -> Missile / Interception -> Damage -> Damage Control;
- internal Turn Refresh and pre-Movement Tactical Power windows remain explicit;
- direct-fire volleys are committed before Damage and resolve in movement/activation order without canceling already committed opposing fire;
- Missile Flights occupy finite-map coordinates and pass through the standing flight/guidance/PDS path.

## Shared deterministic fixture

`docs/design/testing/canonical_combat_kernel_fixtures_v0_1.json` is consumed by Python and C# tests. It blocks drift in:

- canonical damage-model version;
- standard map radius/cell count/start coordinates/range;
- one-hex pre-contact search;
- visible phase order;
- unhardened SPEN->APEN Hull penetration;
- SA/AP penetration cancellation;
- absence of generic hardening damage deletion;
- hardening inactivity after SC/AI collapse; and
- AP persistence after AI exhaustion.

## Numerical freeze boundary

CP132 must byte-preserve the current numerical authorities:

- `docs/design/player_technology/technology_numerical_matrix_v0_5.json`
- `docs/design/player_technology/technology_component_table_v0_7.json`
- `docs/design/player_technology/StarCluster_Stabilized_TL1_TL9_Technology_Component_Table_v0_7.xlsx`

The user's revised TL chart is intentionally not part of this checkpoint.

## Native acceptance

From a clean extraction on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-132\apply_checkpoint_132.ps1 -RepositoryOnly
```

If RepositoryOnly succeeds, finalize the checkpoint in the same unchanged extraction:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-132\apply_checkpoint_132.ps1
```

RepositoryOnly must verify:

- CPython 3.13.x;
- pinned .NET SDK 8.0.423;
- repository packaging hygiene;
- CP132 deterministic preflight/contract;
- all Python research self-tests;
- warning-as-error C# build;
- all xUnit tests with zero failed/skipped;
- ScenarioRunner self-tests with zero failures;
- the top-level deterministic scenario corpus and TL1 Phase-A deterministic mechanics corpus;
- 25/25 research parity fixtures;
- shared CP132 C#/Python canonical-kernel fixtures; and
- a tiny deterministic canonical finite-map Python smoke with zero trial errors.

The normal invocation performs no substantive Monte Carlo. It revalidates the successful RepositoryOnly marker and writes the final native acceptance summary.

## Evidence interpretation

A successful CP132 run validates mechanics architecture, not balance. CP131's 47.69M late-Missile engagements remain historical evidence for the old damage semantics and should not be combined numerically with later CP132+ calibration as if the mechanics were identical.

After the user's revised TL tree is reviewed and synchronized, the recommended next numerical step is same-TL Kinetic/Energy/GP-Missile reference calibration with contemporary Shield + Armor baseline defenses through the CP132 canonical kernel. Broader mixed/nonadjacent-TL screens should follow after same-TL trends are mechanically reasonable.
