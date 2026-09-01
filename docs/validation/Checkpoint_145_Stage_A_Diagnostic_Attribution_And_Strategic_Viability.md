# Checkpoint 145 — Stage-A Diagnostic Attribution and Strategic Viability

**Status:** candidate pending native Windows validation  
**Base checkpoint:** CP144 — EngageAdaptive Missile Parity Closure and Whole-Combat Stage-A Response Surface  
**Checkpoint type:** zero-tuning research attribution / evidence architecture  
**Gameplay numerical changes:** none  
**Production C#/Godot gameplay changes:** none  
**Automatic promotion:** disabled  
**Automatic Stage B:** disabled

## Purpose

CP145 preserves the native-accepted CP144 gameplay and numerical baseline and asks a narrower question before any further balance adjustment: **why did the CP144 whole-combat response surface behave as it did?**

CP144 established production/research EngageAdaptive parity and completed the first broad whole-combat Stage-A study: 6,850 scenario cells × 500 substantive trials = **3,425,000 accepted combat trials**. CP145 does not repeat that substantive study and does not introduce candidate values. Instead, it decomposes the frozen accepted CP144 response surface and adds observation-only telemetry to a deliberately bounded exact-seed replay population.

The diagnostic priorities are:

1. attribute the broad weakness of Kinetic main weapons without assuming APEN or damage is the cause;
2. distinguish PDS shot quality from Reaction Capacity / interception-opportunity limitations, especially for Energy PDS and Swarmer pressure;
3. identify the source of TL1–TL3 long-combat / turn-cap regions, especially TL2 Power Crisis and EW Contest;
4. quantify Energy's sensitivity to Tactical Power / resource environments;
5. replace the highly collinear CP144 three-objective Pareto view with a broader **diagnostic** strategic-viability view that includes resource robustness and endurance without mistaking efficiency for combat health.

## Accepted CP144 provenance

CP145 references the original supplied native-results archive by SHA-256 but does **not** nest that large predecessor ZIP inside the successor repository. Instead, it retains only the exact hash-matching CP144 response tables actually required by CP145 analysis, plus the native acceptance summary and compact provenance.

Retained evidence under `docs/validation/evidence/checkpoint-145/accepted-cp144/`:

- `CP144_ACCEPTED_SCENARIO_RESPONSE_SURFACE.csv` — exact accepted CP144 table, SHA-256 `ffa17024...`
- `CP144_ACCEPTED_PARETO_CHOICE_SURFACE.csv` — exact accepted CP144 table, SHA-256 `a60975cb...`
- `CP144_NATIVE_ACCEPTANCE_SUMMARY.json`
- `CP144_ACCEPTED_BASELINE_PROVENANCE.json`

Pinned SHA-256 values:

- submitted CP144 full-repository ZIP: `dfb5284184603e66faba19afcba4ed514774f777b25815c9492b9c2305bd79cc`
- submitted CP144 native-results ZIP: `71bd2b81980701292d6cd463b2a225752274a1045ea4e813c83e5728e9f961fd`
- normalized CP144 native acceptance summary: `ce3eef4f9a9b31d12c99bedb84715f27549d6e4ec79f2ec02163beedea21dd93`
- accepted CP144 scenario response surface: `ffa17024e0aed42be2def3f6b9e64a492da5c52d7d512cc31552aa19d6a132fd`
- accepted CP144 Pareto surface: `a60975cb58afdf735d27aac4692182eb7080dfcf10f15c419194177fc2df6e15`
- accepted CP144 symmetric pairwise response surface: `deb412591a006278c823b1cd24429e2412046390d123d41e7d3e812fa59078ad`
- Technology Numerical Matrix v0.9: `3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194`
- Concept authority: `f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f`

The retained CP144 acceptance records **6,850 Stage-A scenario cells and 3,425,000 substantive combat trials**. The two retained response tables are byte-identical to the corresponding members of the submitted native-results ZIP, and CP145 analyzes those frozen accepted tables directly. The unused CP144 pairwise table is not duplicated; its accepted SHA-256 remains provenance-only.

The stale CP144 summary field that still described the 3.425M-trial Stage A as its `nextStage` is treated as historical metadata. CP145 does not modify the accepted CP144 result; its own lineage correctly states that the next decision follows review of CP145 causal attribution.

## Frozen production boundary

CP145 is not a mechanics checkpoint.

The checkpoint contract requires all native-accepted CP144 C#/Godot production source, C# tests, gameplay/scenario authority, Concept authority, and the Technology Numerical Matrix to remain byte-identical. No C# file may be added or modified.

Permitted executable changes are limited to Python observation telemetry and research analysis/CLI wiring. The telemetry must not alter decisions, random-number consumption, combat outcomes, or scenario binding.

Focused tests include exact-seed telemetry-off/telemetry-on outcome equivalence, and RepositoryOnly additionally replays the **entire 6,850-cell CP144 Stage-A smoke population** to verify that observation instrumentation preserves CP144's accepted one-trial signature.

Expected smoke signature:

- scenarios: 6,850 / 6,850
- errors: 0
- resolved: 6,785
- resolved at 25+ turns: 9
- 60-turn sentinels: 65
- safe stalemates: 0
- non-standoff Open orders: 0
- source matrix modified: no

## Diagnostic replay population

The study definition is `docs/design/testing/cp145_stage_a_diagnostic_attribution_study_v0_1.json` and the selected identities are in `docs/design/testing/cp145_diagnostic_replay_manifest.csv`.

CP145 replays **252 accepted CP144 scenario identities** at **25 exact CP144 trial indices each**, using the original CP144 master seed `140001`:

- PDS opportunity / Reaction Capacity attribution: **204 scenarios**
- TP-starvation attribution: **48 scenarios**
- total diagnostic combats: **6,300**

The compact CP145 replay manifest stores diagnostic-selection metadata. At execution, each selected identity is joined back to the authoritative CP144 Stage-A experiment manifest and identity fields are checked for consistency before binding the scenario. This prevents CP145 from becoming a second source of scenario geometry or build authority.

The 6,300 trials are therefore not fresh balance samples. They are **same-seed observational reproductions of already accepted CP144 trials**, used to expose causal telemetry.

## Observation telemetry

### Tactical Power telemetry

Per turn and per side, CP145 records requested and denied TP by category:

- main weapon
- PDS
- sensor
- ECM
- ECCM
- shield
- armor
- damage control

It also records missile-threat/PDS opportunity indicators. The purpose is to distinguish a weak numerical system from a system that is rarely afforded a legal powered opportunity.

### Terminal PDS telemetry

When an incoming missile threat exists, CP145 records a terminal-PDS phase event containing:

- PDS family;
- incoming threat flights;
- configured Reaction Capacity;
- planned Reaction Capacity after resource policy;
- PDS readiness TP;
- attempts actually used;
- zero-, one-, and two-attempt flight counts;
- first- and second-attempt interceptions;
- unserved attempt opportunities;
- Reaction-Capacity saturation;
- zero-RC-with-threat state;
- ammunition before/after and ammunition constraint state.

This is observation-only instrumentation. No PDS decision rule, chance, Reaction Capacity, ammunition value, TP cost, or resolution order changes in CP145.

## Accepted-surface decomposition

CP145 reads the hash-locked CP144 response surfaces directly and writes attribution tables for:

- original Pareto-objective correlation/redundancy;
- strategic viability by TL and weapon;
- Kinetic performance attribution;
- matched Kinetic-versus-Energy attribution holding TL/resource/stratum/opponent context constant;
- Energy resource sensitivity;
- PDS baseline response;
- duration hotspots.

### Pareto methodology caution

The CP144 Pareto view used win rate, fast-win rate, and damage advantage. CP145 confirms that win rate and fast-win rate have correlation **0.9987839612**, and **1,441** of the original 1,750 choice contexts have a single Pareto survivor. The original view remains valid as a combat-performance diagnostic, but its objective space is highly redundant.

CP145 therefore writes two TL-level frontiers:

- **combat frontier:** mean, P25, and P90 win performance plus damage advantage;
- **strategic diagnostic frontier:** combat distribution plus worst-resource performance, resource spread, worst-stratum performance, TP fulfillment/conflict, endurance/ammunition, and pacing.

A separate `resource_or_robustness_only_frontier` flag identifies systems that survive the broader strategic frontier despite being combat-dominated. This is important: **resource efficiency is not allowed to be misreported as proof of combat health.** These frontiers are diagnostic only and are not numerical promotion gates.

## Authoring validation

The current CP145 authoring build has completed the following checks outside the native Windows acceptance environment:

- focused CP145 tests: **12 / 12 passed**;
- complete Python regression set: **310 / 310 passed** across three isolated stable chunks of 120, 84, and 106 tests;
- complete 6,850-cell CP144 smoke regression under the telemetry-enabled kernel: exact expected CP144 signature, zero errors and zero non-standoff Open orders;
- CP145 diagnostic execution: **252 / 252 scenarios, 6,300 / 6,300 combats, zero failed gates**;
- source Technology Numerical Matrix unchanged;
- tuning disabled;
- automatic promotion disabled;
- Stage B disabled.

These are **authoring/pre-handoff results only**. Native Windows `-RepositoryOnly` followed by the normal wrapper in the same unchanged extraction remains the acceptance authority.

## Preliminary authoring attribution — not numerical authority

The following findings justify the checkpoint design but **must not be treated as accepted tuning conclusions until native validation reproduces the diagnostic evidence**.

### 1. Energy PDS: opportunity capacity, not shot quality or TP funding

Across the selected R1/R4 PDS-opportunity population, every threatened Energy-PDS phase was funded to its configured Reaction Capacity:

| PDS family | Configured RC / threat phase | Planned RC / threat phase | RC funding | Attempts / threat flight | Intercepts / attempt | Unserved opportunities / threat | RC-saturated phases |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kinetic PDS | 1.507 | 1.507 | 100% | 0.976 | 28.34% | 0.822 | 64.72% |
| Energy PDS | **1.000** | **1.000** | **100%** | **0.691** | **32.12%** | **1.087** | **82.45%** |
| AMM | 1.835 | 1.835 | 100% | 1.170 | 28.01% | 0.618 | 50.36% |

Energy PDS has the highest observed success rate per actual attempt, zero zero-RC threat phases, and no meaningful ammunition constraint in this sample, yet receives exactly one configured/planned RC opportunity per threatened phase and leaves the most interception opportunities unserved.

**Preliminary attribution:** its weakness in CP144 is primarily structural opportunity volume / configured Reaction Capacity, not inadequate individual-shot probability and not TP starvation. CP145 does not change RC.

### 2. TL2 duration hotspots: offensive TP starvation

The 48 TP-starvation identities are the eight worst CP144 cells in each TL1–TL3 × {EW Contest, Power Crisis} region, replayed for 25 exact seeds each.

| TL | Stratum | Trials | Mean turns | 60-turn caps | Side A weapon-denial turns | Side B weapon-denial turns |
|---|---|---:|---:|---:|---:|---:|
| 1 | EW Contest | 200 | 24.095 | 25 | 57.8% | 63.7% |
| 1 | Power Crisis | 200 | 31.575 | 50 | 81.2% | 81.0% |
| 2 | EW Contest | 200 | **60.000** | **200** | **91.9%** | **92.0%** |
| 2 | Power Crisis | 200 | **60.000** | **200** | **99.2%** | **99.3%** |
| 3 | EW Contest | 200 | 24.335 | 3 | 71.6% | 78.5% |
| 3 | Power Crisis | 200 | 37.700 | 97 | 82.2% | 82.4% |

The TL2 hotspot is therefore not a stochastic long-tail problem. In the selected worst cells it is a deterministic region where main-weapon TP requests are denied for nearly the entire combat.

**Preliminary attribution:** do not tune weapon damage against these cells. First examine resource-policy priorities and the intended severity of the early-TL power-crisis/EW environments.

### 3. Kinetic: delivery/cadence/accuracy before penetration

Matched Kinetic-versus-Energy contexts show Kinetic generally enjoys **better TP fulfillment and lower TP conflict**, and at many weak TLs it also produces **higher raw direct damage per hit** and equal or slightly better hull conversion. Nevertheless, Kinetic frequently loses damage-per-turn because its shot opportunity and/or hit rate is lower.

Examples of K-minus-E matched deltas:

| TL | Win rate | Shots/turn | Hit rate | Raw damage/hit | Hull conversion | Damage/turn |
|---|---:|---:|---:|---:|---:|---:|
| 4 | -0.342 | -0.075 | -0.113 | +0.629 | +0.035 | -1.145 |
| 5 | -0.194 | -0.104 | -0.114 | +0.667 | +0.016 | -0.731 |
| 8 | -0.197 | -0.125 | ~0.000 | +0.324 | +0.020 | -1.370 |

Kinetic's Armor-pressure specialization also reappears positively at TL7 and TL9 in the matched surface rather than disappearing completely.

**Preliminary attribution:** the CP144 Kinetic problem does not look like a simple APEN/hull-conversion failure. Delivery, cadence, accuracy, and engagement opportunity should be decomposed before any DAM/APEN adjustment.

### 4. Energy: real resource sensitivity, concentrated early

Relative to the R1 central resource environment, the R4 tight/high-demand environment changes Energy mean win rate by approximately:

- TL1: -13.3 pp
- TL2: -10.4 pp
- TL3: -10.7 pp
- TL4: -5.7 pp
- TL5: -0.5 pp
- TL6: -3.5 pp
- TL7: -3.0 pp
- TL8: -3.6 pp
- TL9: -2.8 pp

The corresponding TP-conflict increase is especially large at TL2 (+52.5 pp), TL3 (+37.8 pp), TL4 (+26.8 pp), TL7 (+25.1 pp), and TL9 (+25.5 pp).

**Preliminary attribution:** Energy's high-demand identity is present in the intended direction, but the early-TL magnitude should be examined together with the TP-starvation result before changing Energy weapon values.

### 5. Strategic frontier: useful warning, not absolution

The broader strategic frontier often retains Kinetic because of its TP efficiency and robustness even when the combat-only frontier dominates it. CP145 intentionally flags those cases as `resource_or_robustness_only_frontier` rather than declaring Kinetic healthy.

This supports the program's multivariate balance philosophy while preserving a hard distinction between **having a strategic tradeoff** and **being sufficiently combat-competitive**.

## Native Windows acceptance sequence

Use a fresh CP145 extraction and run the required two-step sequence in the **same unchanged tree**:

```powershell
.\tools\checkpoints\checkpoint-145\apply_checkpoint_145.ps1 -RepositoryOnly
.\tools\checkpoints\checkpoint-145\apply_checkpoint_145.ps1
```

RepositoryOnly performs, among other gates:

- CP145 preflight / ownership contract;
- the full 310-test Python regression set in three isolated chunks;
- warning-as-error .NET build;
- 916/916 expected xUnit tests;
- 70/70 expected ScenarioRunner self-tests and standing deterministic corpora;
- 25/25 expected research parity;
- CP139 reconciliation and CP140–CP145 focused regression gates;
- the full 6,850-cell CP144 Stage-A smoke regression and exact signature check.

The normal invocation requires the RepositoryOnly acceptance artifact in the same tree, revalidates the repository contract, executes only the 252 × 25 = 6,300 CP145 diagnostic replays, checks attribution outputs, writes the native acceptance summary, and packages the results ZIP.

## Promotion rule

CP145 itself promotes **no gameplay value**.

After native acceptance, review the causal attribution first. Only if the evidence isolates a bounded mechanism should the next checkpoint define a correspondingly bounded candidate sweep. Stage B remains explicitly non-automatic.
