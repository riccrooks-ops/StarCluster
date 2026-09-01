# Simulation Development Guidelines

## Purpose and authority

This document is the durable authority for **how Star Cluster is simulated, calibrated, validated, and integrated across technology levels**. It does not define gameplay rules or promote component values. Those remain with the Game Concept, Technology Architecture Matrix, and current data authorities.

This file is deliberately not a checkpoint journal. Revise it only when reusable development doctrine changes.

## Canonical combat-kernel requirement (CP132+)

All new combat calibration and balance studies must use the standing canonical finite-System-Map combat kernel documented in `Canonical_Combat_Simulation_Kernel.md`. Ordinary combat mechanics belong in that shared kernel, not in a study-specific loop. Technology data, doctrine/AI, and study populations remain separate layers. Experimental controls such as fixed range, forced track, disabled movement, or infinite ammunition must be explicit named overrides and must be reported in evidence.

Checkpoint 132 promotes `canonical_combat.py` as the normal research encounter orchestrator and `canonical_mechanics.py` as the pure parity-critical mechanics layer. The former `full_map_ecology.py` path is a compatibility facade rather than an independent implementation. Historical axial/specialized consumers and their accepted result artifacts remain valid historical evidence under their recorded mechanics, but they do not define new combat behavior. Where historical consumers use common mechanics helpers, they inherit current canonical mechanics when rerun; do not compare such reruns to frozen historical outputs without recording the kernel change.

Mechanics changes must be validated deterministically before Monte Carlo: shared C#/Python fixtures, production unit tests, phase/start-geometry checks, physical symmetry where applicable, and the standing research parity corpus are blocking. Substantive simulation is calibration evidence, not a substitute for mechanics parity.

## Causal studies and integrated validation

Focused checkpoint studies isolate one or a few variables so their causal effects, breakpoints, opportunity costs, and interactions can be understood. Their output is evidence, not a final independent optimization of one TL.

Validated candidates must feed the standing integration architecture. The long-term simulator must support:

- arbitrary valid mixed-TL subsystem combinations;
- complete TL-vs-TL ship comparisons;
- tall, wide, and cross-category research combinations;
- older weapons against newer defenses and newer weapons against older defenses;
- ordinary reference builds and deliberately extreme but legal builds;
- pairing independent of subsystem TL except where a real prerequisite forbids the combination.

The goal is one coherent technology ecosystem, not nine separately balanced islands.

## General encounter and adaptive tactical-AI methodology

CP96 closed the dedicated narrow instrumentation sequence; from CP97 onward, instrumentation is supporting infrastructure for broader mechanics and technology development unless a genuine measurement blocker appears.

Broad tactical studies should begin from a neutral encounter state rather than granting both ships an artificial pre-existing targeting solution or a TL-specific preferred combat range. On the radius-5 tactical map, the standard adaptive-encounter harness starts ships on opposite edges (range 10). Before contact, each side searches one hex toward map center per turn without receiving the hidden target coordinate. Legitimate detection or observed emissions/attacks establish contact; contact alone does not grant Firm track.

After contact, **Engage AI is capability- and observation-driven**:

- use only own installed/functional capabilities plus information legitimately observed by the player at that decision window;
- never inspect hidden opponent TL, exact ECM/ECCM ratings, internal Jamming Margin, undisclosed component statistics, or future random outcomes;
- retain a target-specific combat blackboard for current-combat memory, including track quality/range, observed attacks/emissions/movement, and overload failures;
- preserve a demonstrated asymmetric standoff when the ship has actually shown an engagement reach the opponent has not demonstrated;
- when Firm acquisition fails and no demonstrated standoff is being preserved, close on a later legal Movement decision rather than repeating a failed static range assumption; and
- obey turn timing: information learned after a commitment can influence later decision windows, never retroactively rewrite an earlier one.

Risky sensor/EW escalation is deliberately late. Normal sensing, ordinary ECCM, movement/closure, and same-hex burn-through are considered before overload. When hostile ECM observably degraded an otherwise Firm observation and both options are plausible, **ECCM overload precedes Active Sensor overload**. Active Sensor overload is a later last-ditch range capability, not an intrinsic ECM counter. A failed overload at range X is remembered and is not repeated at range X or farther while the observable state is materially unchanged; closer geometry or a materially changed observable state may justify another attempt.

Harness-only profiles may be used to prove that an AI branch is executable, but they must be visibly isolated from technology evidence and cannot be promoted as production values.

## Candidate lifecycle

- **Conceptual candidate** - plausible design direction, not yet tested.
- **Locally validated working candidate** - survived focused causal/integration testing under current dependencies.
- **Cross-TL validated candidate** - survived broader mixed-tech and progression-lattice testing.
- **Production/baseline value** - current authoritative game value after sufficient integrated evidence and explicit human promotion.

A candidate can move backward when later integration evidence exposes skew or an interaction that the local study could not see.

## Preserve subsystem-family identity

Sensitivity studies may expose the same mathematical axis across multiple families so the comparison is controlled. That does **not** imply symmetric progression.

Higher TL should evolve each subsystem family only along directions appropriate to that family. Do not grant every weapon +DAM, +APEN, +SPEN, range, accuracy, or any other stat merely because technology rises. Prefer family-specific capability, integration, efficiency, resilience, mode, reliability, miniaturization, or frontier improvements when those fit the family better.

A useful result may therefore be asymmetric: for example, one weapon family may merit an APEN advance while another merits SPEN, efficiency, guidance, or no penetration change at that TL.

## Legal-build enumeration

Construction legality follows actual game constraints such as Installation Space, prerequisites, compatibility tags, uniqueness/primary rules, and hull architecture. Do **not** reject a build merely because all installed systems cannot be funded simultaneously from the current Tactical Power pool. Power pressure and tactical allocation are intended operational tradeoffs.

Enumeration must enforce the Concept's minimum combat core: every ordinary legal combat ship contains at least one Main Weapon, at least one Reactor, and at least one installed Sensor. Optional explicit second Main Weapons/Reactors remain legal when the actual Space, compatibility, and prerequisite rules permit them; the minimum-core guard must not become an accidental one-only maximum. ECM/ECCM remain optional. Sensorless configurations may remain as explicit diagnostic/special-scenario fixtures or post-damage states, but must not re-enter the normal legal-build population.

The enumeration layer should retain unusual legal builds, including overcommitted, highly specialized, mixed-generation, and apparent Pareto outliers. Screening may rank them, but should not silently prune them before the system has evidence.

## Progression review discipline

Every proposed technology/component progression change receives two complementary reviews before promotion:

- **Logical/family review:** does the change create or mature a capability that fits the subsystem family, expands a meaningful design choice, and preserves useful alternatives without making the frontier technology pointless?
- **Mathematical/integration review:** do legal contemporary and mixed-generation combinations reveal Pareto domination, accidental best-in-slot packages, integer breakpoints, or hidden interactions under the same Installation Space, Tactical Power, and prerequisite constraints?

A focused checkpoint may answer only part of the second question. Local evidence must therefore remain provisional until broader cross-TL coverage exists.

### Exact-edge marginal progression studies

When a deterministic legal progression lattice exists, use exact lower->higher edges to isolate marginal subsystem value before inventing a new technology tier. An exact edge must preserve the declared ship design and Installation Space except for one explicit construction axis. One-axis does not necessarily mean one physical component: a homogeneous double-installation axis may advance two installed components together, so the expected advanced-component delta must be declared and validated per transition.

Exact-edge sampling should be deterministic and stratified across the transition class plus dependency-relevant build dimensions such as weapon family, composition class, and Space utilization. Execute both movement-order mirrors so initiative sensitivity remains visible. Exact-edge studies are causal screening evidence, not automatic component-promotion or target-win-rate machinery. If the exact-edge study does not use broad legal-population inference weights, do not force legacy population-cell coverage/accounting helpers onto it merely because an older broad screen did.

### Progression transition types and activation boundaries

Exact same-Space replacement edges are one useful progression type, not the universal representation of technology advancement. Standing progression definitions should carry an explicit transition type plus any Installation Space effect needed to preserve the actual design meaning. At minimum, architecture should distinguish same-footprint property/capability changes, miniaturization/density changes with a declared Space delta, and optional component unlocks whose Space cost applies only when the new component is installed. Do not distort a technology candidate merely to make it fit an older exact-edge consumer.

Registration in a technology matrix or standing coverage definition is not runtime activation. A conceptual candidate may be registered so the next consumer expansion has an explicit target, while executable combat coverage remains pinned to the last native-accepted mechanics. Before a registered transition becomes combat-consumer enabled, implement the mechanic and legal-build semantics, update the progression generator for its transition type, run the actual-consumer preflight, and run a tiny full-pipeline smoke before any substantive Monte Carlo.

Repository contracts that inspect human-readable Markdown should validate stable semantic anchors rather than require arbitrary editorial phrasing. When machine-readable JSON already owns exact booleans, version identifiers, counts, or transition IDs, keep those checks strict in the machine authority and use prose checks to confirm the complementary human-facing meaning. Do not make native acceptance depend on adverb, punctuation, capitalization, or synonymous wording when those differences do not change the documented rule.

## Cross-TL progression checks

Broad validation should look for more than local win rate. Aggregate by TL, family investment, subsystem composition, power pressure, matchup class, and other meaningful dimensions. Flag:

- discontinuities or unexpectedly large TL jumps;
- dead zones where a research step has little practical value;
- dominant or nearly mandatory combinations;
- subsystem-family convergence or loss of identity;
- hidden mixed-TL synergies or anti-synergies;
- old technology that becomes unintentionally superior to broad later technology;
- contemporary tall paths that become systematic traps;
- integer packet/breakpoint interactions that create regional skew.

## Workload strategy

The architecture may enumerate more legal pairings than should receive expensive Monte Carlo immediately. Use a tiered funnel:

1. schema, arithmetic, prerequisite, Installation Space, and deterministic combinatorial checks;
2. actual-consumer preflight and one-trial smoke for executable coverage;
3. low-cost screening and symmetry reduction where appropriate;
4. stratified sampling of normal, extreme, and boundary builds;
5. higher-trial paired Monte Carlo for interesting, uncertain, or promotion-relevant regions;
6. Deep Calibration only when the dependency surface justifies it.

Use common random streams for clean candidate/control comparisons when practical. Never manufacture a fixed TL-vs-TL win-rate target simply to make progression look regular.

## Study integration contract

Before handing off any new or materially changed integrated study, audit it across:

- study ID and required variant dispatch;
- schema/document fields and actual runtime consumers;
- pre-run validation;
- finite-map / operational-sensor / stateful-resource study classifications;
- shared/global release-gate classifications;
- study-specific gates;
- report writers and output routing;
- checkpoint stage definitions, expected counts, and baseline/schema bindings;
- self-tests and reusable study-family helper/whitelist logic.

A one-trial smoke must prove routing and mechanics, not statistical outcomes.
A checkpoint definition must also be checked against its own declared stage count, primary variant count, smoke/regression arithmetic, substantive-trial arithmetic, and total execution accounting before packaging. When a new generator or gate method is mutated, run compiler-class source preflights for known failure patterns (including nullable out bindings, cross-enum comparisons, and nested local shadowing) across the whole changed method surface, not only the first reported line.
When a new study or tactical policy relies on shared/global telemetry gates, the actual-consumer preflight must validate the same study classification or source-binding assumptions used by those gates. Prefer a shared helper consumed by both preflight and the full gate over duplicated study-ID lists. The repository contract should verify that binding so omissions are caught before build/tests or a trial smoke.

## Native acceptance and provenance

The authoritative game/mechanics release path remains native Windows PowerShell plus the pinned .NET SDK. Historical checkpoints continue to reject Python. Starting with CP103, the research/calibration path may additionally use a checkpoint-declared Python runtime after explicit approval. CP103 pins stdlib-only CPython 3.13.x and records the exact patch/interpreter at execution. Run repository/dependency contracts before build/tests, then executable schema/enumeration/parity/smoke before expensive substantive studies.

When an active checkpoint declares Python as **stdlib-only**, its mandatory preflight must not import optional authoring packages such as spreadsheet/document libraries. Validate packaged XLSX/DOCX content through standard ZIP/XML interfaces or another explicitly approved in-repository mechanism. The preflight must scan the active checkpoint/research Python surface for undeclared non-stdlib imports before build/tests or expensive simulations, so a missing third-party package fails as a contract violation rather than as an import traceback.

Contracts must be compatible with Windows PowerShell 5.1 and `Set-StrictMode`. Check object properties before accessing them and parse manifests line-by-line or with deliberately tested regex semantics. Static JSON/schema inspection is not a substitute for native contract execution.

For PowerShell-to-native interpreter bootstrap on Windows PowerShell 5.1, avoid `python -c`/`py -c` probes whose source argument contains embedded quoting. Native argument marshalling can alter those quotes before Python receives them. Prefer quote-free executable metadata probes such as `--version`, parse their output explicitly, and statically preflight the wrapper so the unsafe bootstrap form cannot recur. Keep full research execution in a script file rather than inline `-c` source.

PowerShell preflight code must also be parser-safe in its own right. Do not detect forbidden PowerShell/native-command syntax by embedding quote-heavy source fragments inside `.Contains(...)` string literals when the fragment itself contains nested quotes or array syntax. Prefer simple anchored regexes over the relevant assignment/call line, and keep an independent non-PowerShell source-shape test where practical. This prevents a defensive guard from becoming the first native parser failure.


Checkpoint definitions own part of the native-acceptance execution contract. When a checkpoint is cloned from an earlier definition, `nativeDependencyPrecheck.powerShellPaths` and `nativeDependencyPrecheck.checkpointDefinitionPaths` must be rewritten to the new active checkpoint before handoff. The active normal definition must inspect itself, the deep alias must be included where declared, and the inspected PowerShell surface must include the active wrapper and contract rather than only the prior checkpoint. New checkpoint wrappers should validate these metadata bindings before invoking the contract/harness, and RepositoryOnly contracts should assert the exact same lists. Copied-forward description text should be treated as lifecycle/contract drift and corrected in the same pass.

Checkpoint-authored PowerShell must also preflight bracketed type tokens before invoking a new contract. Modern C#/PowerShell spellings are not automatically valid Windows PowerShell 5.1 type accelerators (for example, use the reviewed CLR/PowerShell-compatible type name rather than assuming a C# alias exists). For new checkpoint scripts, keep an explicit reviewed allow-list or equivalent resolver check over the changed PowerShell surface so unresolved type tokens fail before contract execution, build/tests, or long runner stages.

When a checkpoint changes a C# record, class, interface, or other consumer-facing member surface, RepositoryOnly must include a compile-surface contract for the changed consumer path whenever the authoritative native compiler is not available during packaging. At minimum, validate that member names referenced by the newly changed path exist on the declared type and reject stale object-style/member aliases left behind by refactoring. This is not a substitute for the native build; it is an early guard against deterministic CS1061-style interface mismatches that static JSON/count checks cannot detect.

Nullable reference flow across collection/LINQ boundaries is also part of the compile surface when warnings are errors. A validator may prove a nullable document property non-null earlier in control flow without the compiler carrying that fact into a later lambda or array expression. When a later expression intentionally materializes those validated values into a non-null collection, make the boundary explicit with a reviewed null-forgiving operation or a filtering/projection step that produces a non-null type. RepositoryOnly should reject known nullable-to-non-null collection shapes introduced by the checkpoint so CS8619-style failures occur before native compilation. Do not weaken nullable warnings or change a shared document property from nullable merely to silence such a warning.

When the user-facing acceptance flow is explicitly two-step (`-RepositoryOnly` followed by the full run in the same extracted tree), release preflight must exercise that state transition rather than validating each invocation only from a pristine checkout. RepositoryOnly may legitimately create acceptance summaries or other generated artifacts under `out/`; the next repository contract must either normalize those artifacts before exact file-set validation or classify them with the same generated/local ownership policy as the shared harness. Exact repository-owned file-set checks must filter generated/local paths before comparing counts or paths to the manifest. A checkpoint that uses this two-step flow should include a sequence self-test that materializes the expected RepositoryOnly outputs and immediately reruns the repository-owned file-set logic, so `RepositoryOnly -> full run` regressions are caught before handoff.

When a new runner version strengthens validation for an existing frozen JSON document type, retained regression documents that predate a newly introduced field must be exercised explicitly. Do not mutate accepted historical documents merely to add the field. Instead, define a deterministic backward-compatible resolution rule for omitted legacy values, require current documents to declare the new value explicitly when appropriate, and make RepositoryOnly independently validate both the frozen legacy semantics and the current explicit semantics before native execution.

When a study disables a sampler or feature but shared classifiers still read fields from that configuration object, treat those fields as live consumer inputs rather than dead configuration. Keep required classification thresholds explicit in the current document, and make RepositoryOnly derive its reconstruction from the same declared fields the runtime deserializes. Do not hard-code the intended threshold only in the contract; otherwise a missing JSON field can deserialize to a default and collapse runtime strata while static reconstruction still passes.

Evidence must be tied to the exact repository manifest and checkpoint-definition hashes that produced it. Green execution proves the declared gates passed; candidate promotion remains a human design decision.

## Documentation and evidence hygiene

Long-lived documents are reference authorities, not execution logs. Do not append checkpoint-by-checkpoint trial counts, hashes, or narrative result summaries here. Update this document only when reusable simulation-development doctrine changes.

- Game mechanics and durable game design -> Concept.
- Current/candidate progression architecture -> Technology Matrix/data.
- Reusable opponent-AI lessons -> AI doctrine architecture/registry.
- Checkpoint-specific experiment and findings -> study/runbook/evidence artifacts.

Historical evidence may be archived indefinitely without becoming current design authority.

## Generated-study pipeline for broad permutations

When the legal combination envelope is much larger than the first Monte Carlo slice, separate **enumeration** from **execution**. A deterministic generator should validate component/package data, enumerate every currently legal build in the declared envelope, retain mixed-generation/extreme builds, calculate the potential pairing envelope, and emit a bounded named/stratified executable study for the existing combat consumer.

The generated study is not trusted merely because the generator produced JSON. The checkpoint must run the generator through its native executable, then pass the generated file through the actual combat consumer's preflight and a one-trial full-pipeline smoke before substantive screening. Later checkpoints may broaden recipe selection, stratification, or pairing policy without discarding the underlying legal-build catalog.

For every generated-study pipeline, treat the producer's emitted `generatedStudyId` as an executable interface contract. RepositoryOnly must derive that ID from the same authoritative producer configuration consumed at runtime and verify that the downstream consumer explicitly recognizes it across every relevant registration surface: required-count dispatch, pre-run coverage validation, movement/sensor/resource classifiers, generalized-build permissions, shared gate classifications, and output/report routing. Do not validate only that the producer can serialize the study; a generated JSON document that the next consumer rejects as an unknown study is a release-blocking interface mismatch. Where an older report writer has narrower semantic assumptions, route the new smoke to neutral/common outputs rather than broadening the old study-family classifier merely to make the ID accepted.

When a new stage consumes an existing shared JSON document type, reuse the established serializer/binding contract for that type. Do not replace a proven case-insensitive or otherwise specialized binding path with a stricter local serializer merely because the new caller's own document classes bind successfully under different options. Add a regression check that exercises the same binding helper with authoritative-format data so a producer/consumer casing or schema mismatch fails before the expensive study.

For an explicitly approved **separate research simulator** (CP103+), the executable-consumer rule applies to the declared research consumer rather than requiring every statistical study to be added to the game-facing C# ScenarioRunner. The research study must be parsed and executed by its real Python consumer before handoff, including strict field-type validation, exhaustive enumeration, deterministic sampling, parity fixtures against accepted C# mechanics/value relationships, and a full-variant smoke. Keep the native C#/Godot build/tests and accepted deterministic/regression mechanics stages as a separate authority boundary. Do not maintain two checkpoint-specific Monte Carlo implementations merely for symmetry.

The authoring environment is not required to complete every long Monte Carlo workload when tool/runtime ceilings make that impractical. It **is** required to execute the exact schemas, full legal-build population, sampling, parity, every-variant smoke, and a bounded substantive stress workload locally. Record any local full-workload timeout transparently. The user/native host then performs the declared long statistical run as cross-environment acceptance rather than as the first executable test of the simulator.

## Matched screening, readiness, and population accounting

Broad cross-TL screens must distinguish **structural engagement readiness** from **observed runtime activity**. A build can be legal yet unable to attack at the reference geometry, capable only after legal closing, or denied by its current sensing/weapon capability. That classification must not be inferred from final shot counts: doctrine, Tactical Power allocation, and movement can still fail a nominally ready build. Preserve both signals.

Where practical, stratified legal-pair sampling should treat an unordered A/B pair as the sampling unit and execute both A-vs-B and B-vs-A orientations. Keep bundle identity, orientation, seed, and movement-order geometry explicit so side assignment and geometric information advantage can be measured rather than silently folded into progression.

Construction-envelope utilization is a comparability dimension. Report used Space, signed/absolute Space difference, and understandable Space-utilization strata alongside technology progression. A fuller legal build beating an underfilled legal build is valid ecosystem evidence, but it is not automatically evidence that one technology step is intrinsically better.

Stratification changes sample frequencies. When a bounded screen is intended to say anything about the broader legal-pair envelope, analytically count the relevant legal population per sampling cell, report inclusion/coverage, and provide population-weighted screening estimates alongside raw sample summaries. Weighting restores cell prevalence; it does not make a single sampled pair representative of every build inside that cell. Keep this limitation explicit, especially when readiness or other within-cell properties vary.

Do not invent a universal scalar technology score merely to simplify mixed-TL comparisons. Prefer explicit descriptors such as progression magnitude/direction, used-Space difference, weapon-family pairing, information-control gap, and other dependency-relevant dimensions.

When population weights are concentrated or a primary cell is internally heterogeneous, improve the **number of statistical representatives inside important cells** before merely increasing Monte Carlo trials on a single representative. Allocation should remain deterministic, bounded, auditable, and population-aware. A square-root population allocation is an acceptable bounded screening policy when it is declared explicitly; later evidence may justify variance-aware refinement.

Keep inference samples separate from **diagnostic diversity overlays**. Population-representative weight belongs only to the declared statistical sample. If a cell has multiple statistical representatives, divide that cell's inference weight among them according to the declared sampling design so the representative weights recover the complete analytical population exactly. Family/information-control diversity overlays, named anchors, or other diagnostic additions must carry zero population-inference weight unless the sampling design is deliberately redefined and revalidated.

A structural readiness class should expose the actual geometry it assumes when that distinction matters. For cross-TL screening, record the maximum range at which the declared reference Firm-track and physical-weapon conditions become jointly legal. **Movement-path closest approach and final post-Movement combat geometry are different telemetry and must never be substituted for one another.** Ordinary post-Movement readiness diagnosis must use per-trial firing-window geometry (or equivalent authoritative engagement-window telemetry), while path closest approach remains a separate movement/event diagnostic. The structural maximum-ready-range is a screening estimate, not an absolute runtime attack-legality ceiling: reactive ECM/ECCM doctrine, power choices, seeker behavior, or other legal runtime state may permit an action outside that static estimate. Such a runtime-action/structural-readiness divergence is review evidence and must not be folded into the hard counter-integrity gate. If a nominally `closing_ready` pairing produces no combat activity, determine whether its actual post-Movement firing window reached the required side/mutual structural ready range before labeling the result. `movement_did_not_reach_mutual_ready_range` is a doctrine/movement diagnostic; reaching ready geometry yet still producing zero family-appropriate actions is a stronger consumer/integration failure. Preserve side/family/context activity cohorts as a second guard and restrict their blocking population to side-variants that actually reached their structural ready geometry, so a movement shortfall is not mislabeled as a dead weapon lane and one side's activity cannot mask the other. Runtime variants should carry readiness class/range explicitly when those values drive gating; human-readable profile labels are provenance, not the authoritative runtime data path.

For interpretation, keep **three observables separate** rather than allowing one label to stand in for all of them: (1) reference-context mutual readiness, which is the static screening estimate; (2) observed reference-ready firing-window reach, which records whether the simulation actually reached the geometry required by that static estimate; and (3) true runtime bilateral activity, which depends only on both sides actually producing family-appropriate legal combat actions. Runtime bilateral activity must not be conditioned on the reference-context estimate. A reference-not-expected/runtime-active result is a false negative of the screening estimate, not an illegal action by definition. If a historical report used a reference-conditioned `observed_active` cohort, preserve it only under an explicit compatibility name when needed for causal comparison, and report the pure runtime-active cohort beside it.

Aggregate family/context activity is not sufficient when an individual dead pairing can be hidden inside a healthy cohort. Preserve individual matched-bundle observed-engagement diagnostics and route blocking gates to the failure mode that actually indicates broken execution rather than to a broad zero-action count.

For broad screens, produce an explicit outlier review queue when practical. Keep materially different outlier classes separate (for example engagement/activity anomalies, path-versus-post-Movement geometry divergence, and mover-order sensitivity), include population/stratum context, and distinguish blocking execution invariants from review-only tails. An outlier queue is a triage aid, not an automatic balance or promotion rule.

When movement order is intentionally being bounded rather than finalized as a production initiative rule, keep both orderings and derive a **mover-order-neutral matched estimate** from the same unordered build pair. Report the first-versus-second gap explicitly and classify high-sensitivity pairings for review. The sensitivity label is analysis metadata, not a gameplay rule or automatic balance gate.

## Combat-activity and attack-eligibility guards

Movement/range doctrine must reason about **current attack eligibility**, not physical weapon range alone. Track quality, sensor/EW state, guidance or terminal-lock requirements, power availability, and other current prerequisites may make a physically reachable target ineligible to attack.

For broad integration screens, pair dynamic contexts with a healthy fixed/reference geometry when practical. If an attack type is materially active in the reference, dynamic doctrine must preserve nonzero activity for that attack type unless the study explicitly declares a withdrawal/search/no-fire control. A zero-shot or zero-launch dynamic lane that exists only because doctrine moved itself outside its usable targeting/guidance envelope is a study-quality failure, not a balance result.

The fixed/reference lane must itself be viable. When an intended-active reference records nonzero legal attack opportunities but converts none into attacks because of self-inflicted doctrine, power allocation, or other integration behavior, fail the study-quality gate before interpreting its win rate. This is an activity invariant, not a balance target.

For mixed-family or bilateral screens, activity telemetry should be side-specific when a family-specific failure could otherwise be hidden by the opponent's actions. Contextual activity gates should test the action type the side is actually expected to perform—for example direct shots for direct-fire families and launches for Missile—while allowing explicitly classified engagement-denied controls to remain in all-legal ecosystem reporting.


## Cross-progression Adaptive Engage methodology

- **Own capability exhaustion is durable combat knowledge.** Safe-Strain exhaustion is different from a failed overload at range X. Once an Adaptive Engage ship reaches the current safe Strain limit for an escalation kind, the combat blackboard suppresses further requests until an explicit own-state capability-restoration rule makes the overload legal again. Closer range or changed enemy emissions do not restore Strain. Tactical Power denial remains temporary and may be reconsidered after a real power-state change.
- **Broad mixed-TL screens start as encounters, not preselected firing geometries.** Generated integration studies should use the general search/contact/Adaptive Engage consumer when that is the gameplay question, beginning at opposite map edges and preserving player-information parity. Historical fixed/TrackAware studies remain regression/evidence assets.
- **Progression edges are explicit, not scalar TL scores.** When practical, enumerate same-design single-axis legal upgrade edges under identical Installation Space and other-axis choices. Higher TL should expand useful design space, but no gate requires the higher endpoint to win every matchup. Use the lattice to expose Pareto domination, opportunity cost, legacy stacking, and integer breakpoints.
- **Do not synthesize missing progression for symmetry.** A historical monolithic runtime profile is not permission to invent an independent subsystem candidate. Add a progression axis only when the current technology authority owns the working value/capability.
- **Actual-consumer preflight must mirror shared gate assumptions.** New studies or AI/movement modes that depend on global telemetry classification, runtime catalogs, schema bindings, or study-family helpers must validate those same bindings before the one-trial smoke, preferably through shared helper logic used by both preflight and full gates.
- **Package precheck targets compiler-class mistakes too.** Where native compilation is unavailable during authoring, release preparation statically audits changed C# for known nullable-reference, enum/type-binding, unresolved method/dispatch, and actual-consumer referential-integrity patterns. Native warnings-as-errors build remains authoritative acceptance. For newly mutated generator/gate methods, also scan local declarations for nested-scope name reuse that would trigger C# CS0136; method-level aggregate locals and per-transition/per-case locals must use distinct names even when their meanings are related.

- **Zero-cost executable actions are first-class values, not invalid spend requests.** When a technology maturation legitimately reduces an action's Tactical Power cost to 0, the consumer must treat the resource operation as a no-op and must not call a ledger API whose contract requires a positive quantity. The same helper should serve zero- and positive-cost forms where possible. Before native smoke, RepositoryOnly and/or an actual-consumer preflight must prove the declared zero-cost data reaches a zero-safe execution path, and a deterministic self-test should cover both 0 and a positive control value.
- **Counted trial errors must still preserve full diagnostics.** Monte Carlo/smoke runners may convert an exception into a `TrialErrors` count so the batch can complete and release gates can fail deterministically, but they must also emit enough immediate diagnostics to reproduce the fault: study/variant identity, trial index, full exception message, and stack trace. Do not swallow native-only exceptions into summary counters that erase the original failure site.


### Base technology table completion versus catalog expansion

A completed base TL row defines the standard representative capability for each existing stream; it does not require every optional Auxiliary, specialist subcomponent, alternate profile, or pinnacle legacy-family item to be defined at the same time. Keep candidate lifecycle explicit: **registered candidate != implemented != calibrated != promoted**. When later research improves an older family (for example a pinnacle fission reactor after fusion exists), preserve the owning family identity and treat the item as catalog expansion rather than silently replacing the base row.

Whole-ship Space/Power sanity should accompany a base-row lock. Preserve odd-but-legal outlier builds rather than adding anti-stacking rules; construction legality and simultaneous Tactical Power feasibility remain separate. Record important integer build breakpoints so later miniaturization/Hull growth can reveal when previously impossible architectures become legal naturally.


## Typed progression and executable-tier integration

When a new Technology Level changes the **design envelope** rather than merely increasing a same-footprint scalar, do not force it through an older advanced-component-count abstraction. Represent the transition type explicitly and validate the quantities it actually changes. Supported progression semantics should include, where owned by current technology authority: Hull-capacity integration, component miniaturization, power efficiency, capability additions, normal operating-mode additions, optional-component unlocks, primary performance changes, protection maturation, safe-output/readiness modes, autonomy/propulsion changes, and explicit holds.

Preserve accepted legacy consumers as regression assets when practical. A generalized new schema should be additive rather than silently reinterpreting a frozen older schema. The older consumer must remain executable under its accepted inputs and counts, while the new schema owns only the newly required semantics.

Separate **construction-envelope coverage** from **semantic transition coverage** when full Cartesian enumeration would multiply irrelevant family/mode variants. The construction consumer may collapse states that are provably Space-isomorphic for legality, but the transition consumer must independently exercise every declared technology transition. Document what each consumer is allowed to prove.

Fields on optional or compatibility runtime records must retain their existing meaning. If a new Technology Level needs a different semantic (for example, a full-strength EW cost rather than legacy TP-per-rating), add an explicit field and preserve legacy null/default behavior instead of overloading an old field with a new meaning. Likewise, normal rated modes and overload modes are different mechanics and should have separate data paths.

For a checkpoint that first activates a new tier in the combat consumer, require this sequence before substantive stochastic work: repository/static contracts -> warning-as-error native build and unit tests -> deterministic consumer/self-tests -> actual construction/progression consumer preflight -> generated-study deserialization preflight -> tiny one-trial-per-variant full-pipeline smoke. The smoke proves plumbing and legal execution only; it is never balance evidence.

If the release workflow instructs users to run `-RepositoryOnly` and then a full checkpoint in the same extraction, test that exact sequence. Generated output directories, acceptance summaries, build products, TestResults, and similar artifacts must be classified as generated/local so the first run cannot poison repository ownership checks in the second.

Cross-platform byte-reproducibility checks must control serialization bytes explicitly. Do not hash a text artifact generated with default platform newline translation and compare it against a checked-in copy produced on another operating system. For JSON/text evidence whose SHA-256 is part of an acceptance gate, emit a declared canonical encoding/newline convention (normally UTF-8 with LF) via byte-oriented or explicitly newline-controlled I/O, and make RepositoryOnly regenerate and byte-compare the artifact on the user's native platform before expensive regression or Monte Carlo stages. Semantic JSON equality is insufficient when the gate is intentionally byte-level.

Under native Windows PowerShell 5.1 with `Set-StrictMode`, do not assume a function that syntactically returns `@(...)` will remain an array after assignment: PowerShell pipeline output is enumerated, so a one-item result may collapse to a scalar. Whenever a caller relies on `.Count`, indexing, or array membership semantics from helper output whose cardinality can be one, explicitly materialize the call with `@(...)` at the assignment boundary (or otherwise return a deliberately non-enumerated collection). RepositoryOnly compatibility checks should statically reject known helper-call patterns that omit this materialization so scalar-collapse failures occur before the contract body executes.

## CP103+ population inference and legacy-diagnostic separation

- **Classify Space utilization relative to the selected Hull capacity.** When legal populations include multiple Hull capacities, exact/near/underfilled strata must use free-Space headroom against each build's actual capacity. A single global used-Space cutoff can silently classify a 35-Space and 36-Space ship differently for reasons unrelated to utilization and is not valid for mixed-capacity inference.
- **Do not overweight tactically isomorphic labels.** If two technology labels are operationally identical in the study domain (for example a held strategic-only FTL transition in a tactical combat population, or an explicit held PDS transition), do not count both as separate weighted population states merely to preserve the labels. Collapse the isomorphic state in the inference population and retain the transition as a zero-weight named negative control.
- **Separate population inference from legacy/all-tier diagnostic overlays.** When a full all-tier Cartesian universe would be computationally wasteful or semantically misleading, keep a complete bounded weighted population for the inference question and a second named-only diagnostic overlay for complete-tier anchors, legacy stacking, mixed-era packages, negative controls, and integer breakpoints. The overlay must declare zero population-inference weight.
- **Frontier counts are stratifiers, not scores.** A frontier-component count may be redefined by a new schema/version to count the currently studied frontier TL, but that meaning must be explicit and versioned. It is an attribution dimension only; do not convert it into a universal technology, utility, or balance score. Historical schema meanings remain frozen.
- **Match frontier attribution to the study domain.** For a tactical frontier study, count installed frontier-TL capabilities that can materially distinguish tactical construction or execution, including capacity/enabling systems where appropriate. Explicitly exclude held or strategic-only labels that the weighted tactical population intentionally collapses, and document that exclusion so the frontier count cannot be mistaken for a complete whole-ship TL score.
- **Adaptive cell budgets must be independently feasible before release.** Do not respond to impossible or extremely sparse strata by merely raising sampler attempts. Independently reproduce the legal population, verify every configured population cell is non-empty, reproduce deterministic quota allocation, and confirm the declared random sampler fills all quotas within the bounded attempt budget.
- **Conceptual population size is not an execution license.** Large all-pairs envelopes used for weighting or attribution must be accounted through buckets/combinatorics or another bounded exact method. Materialize only the legal build set and the explicitly selected samples unless a later checkpoint justifies a different bounded representation; never introduce O(N²) iteration merely because an oriented/unordered pairing count is reported.
- **Only declared statistical representatives carry legal-population weight.** Diversity overlays and named diagnostics remain zero-weight unless a future sampling design explicitly promotes them into the inference sample and validates the resulting inclusion probabilities.
- **Substantive measurement still does not auto-promote technology.** Population-weighted outcomes, Pareto/frontier diagnostics, legacy-component stacking, integer Space breakpoints, Tactical Power pressure, engagement/activity cliffs, and mover-order sensitivity remain human-review evidence. Any retuning requires a later explicit design decision and dependency-relevant validation.
- **Absent catalog placeholders do not raise a build's executable Technology Level.** In mixed-era/all-tier studies, a selected `installed=false` placeholder may carry later catalog metadata only because the schema needs a canonical absence option. Runtime-tier routing and tier-based diagnostics must derive from installed/effective selections, not from the highest metadata TL among absent placeholders. Preserve historical schema behavior; apply installed-aware tier semantics only in schema versions that explicitly declare them.

### Python research bytecode hygiene (CP103+)
- The user-facing research wrapper invokes CPython with `-B` so repository-local `__pycache__`/`.pyc` files are not created during checkpoint acceptance.
- Repository ownership checks must also classify `__pycache__/` and `.pyc` as generated/local artifacts. This is defense in depth for users or developers who invoke the Python package directly without `-B`; generated bytecode must never change the repository-owned manifest or break the required RepositoryOnly-to-full-run sequence.


## Bounded local-tier closure and higher-TL expansion

Do not turn a locally interesting Technology Level into an indefinite optimization loop before the broader progression chart exists. After a tier has an executable baseline plus substantive integration evidence, allow at most the bounded diagnostic follow-ups needed to resolve architecture questions that could invalidate later work. Ordinary matchup imbalance, specialization, or opportunity-cost-bearing legacy viability is not an architecture blocker.

When the project explicitly declares a post-checkpoint expansion gate, treat that gate as a planning constraint: the default next work is to fill additional basic subsystem TL rows and then revisit the enlarged design space. Additional local-tier tuning requires a concrete mechanics, construction, power-accounting, parity, sampling, or sequencing defect that would make the higher-TL study misleading.

As more TL rows become executable, stop treating adjacent-tier comparisons as sufficient evidence. Standing cross-TL validation should include mixed-era component packages, nonadjacent complete-tier comparisons, tall/wide alternatives, legacy stacking, integer Space/Power breakpoints, and latent/contextual upgrades. This guards against a locally tidy TL1→TL2→TL3 sequence hiding global domination or regressions at TL4+ and beyond.

Combinatorial legal-population weighting is not automatically a player-build prior. When one redundant or optional subsystem family contributes disproportionate state multiplicity, preserve the exact combinatorial result but report reasonable review-only sensitivity lenses (for example equal bundle, equal cell, equal composition, equal progression, or equal Space stratum) before drawing balance conclusions. Do not silently replace the declared population with a preferred prior.


## Build-ecology instrumentation and population separation

Build-level ecology studies must prove that the combat consumer is observable before interpreting balance. At minimum, expose weapon-family activity/damage, missile/PDS flow, track quality, ECM/ECCM downgrade/restoration, Tactical Power allocation and shortfalls, overload usage, movement/range/fuel/map interactions, Shield/Armor/Hull damage flow, unresolved outcomes, and movement-order sensitivity. A headline win rate without mechanism telemetry is not sufficient evidence for retuning.

Label the active damage consumer explicitly. If internal critical/subsystem damage is not simulated, results must say so and must not be interpreted as evidence about subsystem survivability, mission-kill frequency, magazine criticals, or internal damage balance. Integrate internal damage into a new research consumer only after deterministic parity with the authoritative C# mechanics is established.

Same-TL and mixed-TL populations answer different questions. Keep a fixed-TL primary population separate from mixed-era/legacy overlays unless a later study explicitly defines a combined weighting model. Zero-weight diagnostic overlays may coexist with the primary population but must not silently affect inference.

Legal player builds should normally spend their available Installation Space. When the numerical matrix does not yet contain enough executable support/mission components to represent plausible use of residual Space, a research harness may record residual capacity as zero-effect mission/AUX accounting. Such accounting must be explicit, must confer no tactical benefit, and must be reported as a missing-consumer/integration diagnostic rather than treated as a complete ship design.

Movement doctrine must distinguish physical/preferred range from attack eligibility. After legitimate contact, a ship that still lacks the track quality required for its planned attack and has no demonstrated standoff to preserve should normally continue closing on later Movement decisions. Instrument track-driven closure separately so doctrine corrections are visible in the evidence.

When fast missiles can reach terminal defense on the launch turn, PDS readiness must still receive the accepted terminal-defense window. If the accepted doctrine knows the opponent is a Missile-family threat, that observed family is sufficient reason to preserve planned PDS readiness; do not require an inbound-flight object to exist before reserving defensive power.

Use canonical geometry for a bounded instrumentation pass when appropriate, but do not generalize movement-order or positional balance conclusions to the complete tactical map until off-axis/system-map geometry populations are tested. Mirrored movement order remains mandatory wherever sequencing can affect outcomes.

Prefer expanding scenario dimensions, legal-build coverage, doctrines, geometry, and pairings over multiplying repeated trials once sampling uncertainty is already small. The user's native workstation can support large Python workloads; select the substantive sample size for statistical and diagnostic usefulness rather than for authoring-environment convenience.

## Causal build-neighbor and ablation diagnostics

When a broad build-ecology screen identifies a strong or weak package, do not immediately retune the most visible component. Build-neighbor studies should hold the surrounding package and opponent population as constant as practical while removing, substituting, or otherwise perturbing one decision at a time. Where a component removal leaves Installation Space unused by executable combat systems, preserve exact-fill accounting with explicitly zero-tactical-effect mission/AUX capacity rather than pretending the ship would be physically underfilled.

Use family-control substitutions when they help distinguish a weapon-family effect from a defense/support-package effect. Interpret a control only within the mechanics it actually exercises; for example, a no-ECCM ablation against opponents that rarely jam does not supersede dedicated ECCM evidence.

For sequencing or geometry signals, vary starting geometry/range before changing weapon values. If a movement-order cliff persists across multiple legal starts, treat initiative/sequential-response semantics as a first-class causal hypothesis. Do not infer that a map-edge start is the sole cause merely because the original screen began at opposite edges.

For unresolved/attrition signals, vary engagement horizon and remove defensive layers separately. If doubling the horizon does not resolve a matchup while removing one defense layer does, classify the issue as a sustainable defensive/damage-packet interaction rather than a timeout artifact. Only after causal attribution should a later checkpoint sweep numerical parameters such as damage, penetration, recharge, capacity, or salvo size.


## Ammunition and warhead characteristic studies

Treat weapon-family flexibility asymmetrically. Energy primarily varies power/output modes; Kinetic ammunition should auto-mature when a compatible new projectile strictly dominates the previous normal package, while selectable Kinetic modes require a real tradeoff. Missile warheads may remain mission-specific selectable payloads when shield, armor, structural, or other effects trade against one another. Do not create pre-battle subtype inventories for normal ammunition; use the existing broad Kinetic/Missile stores. Rare or Exotic munitions may be individually tracked only when scarcity is itself part of the design question.

Payload studies must validate compatibility explicitly. A researched munition may be exercised only by weapon/flight profiles that declare the required interface/body capability. Missile warhead choice is fixed when launch is committed. General-purpose payloads should remain sensible defaults when target defenses are unknown; specialist payloads must not become universal best-in-slot.

For anti-shield studies, measure cumulative shield pressure rather than paper SPEN alone. Preserve Shield Armor prevented, Shield Capacity removed, recharge/restoration, Armor/Hull penetration, ammunition exhaustion, unresolved rate, and PDS activity. Compare shield-specialist payloads against GP and armor-specialist controls with shielded, armor-heavy, and no-shield targets, and include PDS-present/PDS-removed lenses. A shield-specialist payload should gain meaningful cumulative shield performance while giving up enough Armor/Hull effect that its role remains contextual.

Combat-assessment logic used by research AI must obey player-information parity. If Firm observation can legitimately report shield absorption/collapse, armor contact, Hull penetration, or lack of observed penetration, the AI may remember and act on those same derived flags. It may never branch on exact hidden Shield Capacity, recharge, Armor values, or internal arithmetic merely because the simulator owns those values.

Keep internal-effect/radiation payloads deferred until the Python research consumer parity-validates the authoritative internal critical/subsystem and crew consequences. Keep known extreme movement-order-cliff lanes separate from primary payload balance inference unless sequencing/initiative is the explicit study dimension.


## Weapon-family KISS consolidation and TL weighting

CP117 establishes a simplification guardrail for weapon-family studies. Do not convert every useful characteristic-space control into a player-facing mode. Energy may expose a small number of power/output choices because the power tradeoff is intrinsic; normal Kinetic projectile improvements should auto-mature when compatible; the normal Missile line should mature GP energetic yield while distinct Flight families such as Swarmer carry their own compact rules. Preserved specialist-warhead concepts may return only when play demonstrates a clear unmet mission worth the additional choice.

Calibration priority is intentionally uneven. TL1-TL6 are primary campaign evidence, TL7 is advanced-game validation, and TL8-TL9 are endpoint/stress validation. Pinnacle-TL breakpoints may reveal bugs or runaway interactions, but they should not by themselves justify adding complexity across the whole ladder. Report primary and endpoint conclusions separately rather than averaging all TLs into one design signal.

For a future Swarmer study, preserve one Missile Flight counter and one terminal attack roll. Candidate axes should remain small: bounded terminal coverage/accuracy, bounded internal packet count/strength, and a bounded PDS-saturation modifier. Do not multiply tactical counters, PDS windows, natural-critical rolls, or hidden submunition inventories.

### CP118 simplified weapon-progression studies

After CP117 KISS consolidation, progression studies should test the smallest active family model before reopening characteristic-space complexity. For Missiles, isolate GP energetic yield from penetration specialization; if a study holds a GP SPEN/APEN baseline constant, label it diagnostic rather than promoted. Swarmer studies preserve one Flight counter, one terminal attack package, one ammunition expenditure, and one existing PDS interaction sequence; terminal coverage, bounded internal packetization, and modest PDS-saturation resistance are sufficient candidate axes unless evidence demonstrates a missing mechanic.

For Kinetics, treat smart-projectile ACC, raw DAM, and APEN as automatic-progression diagnostic axes rather than selectable normal ammunition. Preserve intended family asymmetry: a change that greatly improves Kinetics against Shields may be mechanically effective but should be reported separately from a clean smart-guidance improvement. Do not use a single all-target average as a balance objective.

Weight TL evidence explicitly: TL1-TL6 primary, TL7 advanced, TL8-TL9 endpoint/stress. Endpoint collapse can expose an architectural problem, but endpoint performance alone does not justify adding whole-ladder gameplay complexity. Outcome thresholds remain information unless a checkpoint explicitly establishes a predeclared mechanical safety gate.


### CP119 integration-ecology narrowing

After a characteristic-space checkpoint has isolated useful axes, prefer a smaller shared-ecology confirmation before promoting values. The integration population should compare only a few working candidates against the same legal exact-fill target packages and retain native/reference families where needed for context. Do not reopen discarded ammunition modes merely because a working candidate is strong or weak in a bounded authoring run.

Campaign weighting must remain explicit: TL1-TL6 primary, TL7 advanced, TL8-TL9 endpoint/stress unless a later checkpoint deliberately changes the campaign model. Working Missile yield milestones, Swarmer maturation, or Kinetic smart-accuracy steps remain review candidates until native integration evidence confirms them; outcome rates are not automatic promotion gates.

### CP120 sensitivity mapping before narrowing

When an integration checkpoint identifies a plausible simple progression but the candidate jumps are large or integer thresholds are suspected, run a bounded sensitivity-mapping checkpoint before promotion. Freeze the mechanical model and widen only the numerical envelope around the active design. Prefer adjacent-value slopes, explicit single-axis controls, and selected interactions over reopening a full combinatorial characteristic space.

For Missile GP yield studies, hold penetration traits fixed while mapping Damage so yield and specialization cannot be conflated. For Swarmer studies, isolate packet size, terminal coverage, and PDS saturation with a same-base no-PDS control; flag candidates whose apparent strength is primarily greater total nominal payload. For Kinetic smart-projectile studies, compare ACC against separate DAM/APEN controls but keep those axes automatic and non-selectable.

Synthesize a small number of candidate progression paths from already executed cells instead of rerunning identical combat merely to label a ladder. Report primary TL1-TL6, advanced TL7, and endpoint TL8-TL9 results separately. Controlled fixtures diagnose mechanics but do not carry promotion weight. Sensitivity outcomes remain review evidence and cannot automatically promote the highest-scoring path.

### CP121 numerical-domain rescaling and equivalence

When changing the integer resolution of an established numerical domain, treat the change as a unit conversion first and a balance experiment second. Define a machine-readable list of values that share the domain, explicitly list quantities that do not scale, and audit every consumer whose behavior is tied to a point magnitude, per-point cadence, rounding rule, threshold, repair amount, or special-case bonus.

Before interpreting any newly available intermediate value, execute same-seed paired legacy-versus-rescaled trials over the complete relevant regression population. Normalize only the declared point-domain outputs; winner, turn order, RNG-visible events, non-point telemetry, and all other behavior must remain exact. A mismatch is a mechanics/integration failure, not a balance result.

Do not assume a per-point cadence should scale as a magnitude. For example, if Hull and damage are doubled, an H/X track that advances once per Hull point would double critical frequency unless its cadence is converted separately. Likewise, rounded degradation formulas can break mathematical equivalence even when their inputs are doubled. Record such consumers explicitly before canonical promotion.

Use odd values in the rescaled domain only after equivalence passes. A higher-resolution scale is justified when the newly representable values repeatedly occupy useful intermediate mechanical/outcome regions; it is not justified merely because more integers exist. Preserve deliberate technology breakpoints where the design calls for them. No resolution change or intermediate value should auto-promote from a sensitivity study.

### Canonical unit-domain migrations and explicit parity exceptions

When a numerical ruler is promoted after a resolution study, migrate by **physical/gameplay dimension**, not by filename or superficial field name. Maintain a machine-readable list of point-domain fields and a separate list of non-point fields. Regeneration/RepositoryOnly must prove exact multiplication for every declared point-domain value and equality for every declared non-point value before native acceptance can proceed.

Do not rewrite frozen historical authorities merely to make them look current. Introduce explicit canonical successors and keep historical research/default paths stable when old checkpoints depend on them. New research consumers should accept an explicit canonical authority path rather than silently changing the meaning of an old default.

Rounding rules belong to their domain. A generic arithmetic helper can become incorrect after a unit migration even when the inputs are doubled. For damage degradation, verify normalized legacy/canonical equivalence across the full relevant value range. Do not alter rounding for Tactical Power, movement, ratings, or other non-damage quantities merely because damage units changed.

If an intentional gameplay exception breaks exact unit parity, declare it twice: once as the **production semantic** and once as the **parity-only fixture**. The parity fixture may temporarily use an artificial equivalent value to prove the migration, but native tests must separately assert that the production rule retains the intended exception. CP122's Damage Control rule is the reference example: production remains 1 canonical Hull per successful Repair Kit, while an artificial 2-Hull restore is legal only inside migration-equivalence tests.

Do not force not-yet-complete systems into a unit migration. If a per-point cadence such as internal critical progression is not ready for authoritative implementation, mark its conversion explicitly deferred and prevent current parity claims from being interpreted as covering that subsystem.

### Native C# dependency preflight when authoring without the native compiler

When a checkpoint adds or changes C# files but the authoring environment cannot run the pinned .NET compiler, preflight must inspect the checkpoint-owned C# delta for explicit namespace/type dependencies that are not covered by project/global usings. At minimum, newly referenced production enums/classes used by the checkpoint must either be fully qualified or have the same explicit `using` directive used by established consumers. This static audit is a handoff guard only; it never replaces the authoritative pinned-SDK warning-as-error native build.

## Raw-telemetry ownership and large-study readiness

Before a new large statistical study is allowed to rely on a research consumer, instrumentation correctness is a blocking acceptance concern rather than a nonblocking convenience. Maintain a machine-readable telemetry contract that states each raw counter/quantity, its gameplay dimension, and the side/entity that owns it. Derived rates must be reconstructible from those raw values. In particular, do not infer Missile hit-per-launch from two counters merely because they share a prefix: launch telemetry belongs to the attacker while terminal arrival, guidance-attempt, Missile-hit, PDS, and received-damage telemetry may belong to the target/defender.

When adding a new raw point-domain telemetry quantity, update any damage-scale equivalence field registry so historical scale/parity studies continue to normalize it correctly. When adding a non-point event count, keep it outside point-domain normalization. Deterministic probes should compare layered-damage accounting to an independently implemented oracle whenever practical rather than merely checking that counters are nonzero.

A foundation checkpoint may exhaustively enumerate a broad legal-build envelope while executing only a small zero-weight smoke. Enumeration proves representation/legality; a one-trial smoke proves pipeline/instrumentation reachability; neither is balance evidence. Once those gates are accepted, prefer moving to a statistically useful larger study instead of creating repeated narrow instrumentation-only checkpoints, unless a genuine measurement blocker is discovered.

## Whole-population coverage without Cartesian execution

When a legal-build universe is too large for a literal Cartesian combat sweep, distinguish **population enumeration** from **pair execution**. Preserve the complete legal-build population, define a deterministic pairing design whose coverage properties are machine-checkable, and attach explicit design weights that reconstruct the intended population cells. Prefer guarantees such as “every build appears against every opponent TL” over vague random-sample coverage when the workload permits it.

For technology-progression studies, keep ship-generation purity separate from opponent-generation distance. A pure-TL ship may fight another pure-TL ship at a different TL without becoming a mixed-TL build. Emit both side assignments and both movement orders when side/mover effects can contaminate the technology estimate. Treat balance curves and dominance signals as review evidence unless the checkpoint explicitly declares a validated numerical acceptance target.

## CP126 research-consumer fidelity, physical symmetry, and geometry parity

A deliberately simplified research consumer must remain **explicitly versioned as an abstraction**. Do not allow an early screening simplification (for example, a one-dimensional axial lane or ETA-only Missile travel) to become the silent default for later studies whose conclusions depend on the omitted geometry. Preserve historical consumers when reproducibility matters, and introduce a new fidelity consumer when the research question has outgrown the abstraction. Use the historical consumer as a causal control rather than rewriting old evidence in place.

For symmetric tactical geometry, equal-choice tie-breakers must be physical/relative unless an absolute-map asymmetry is intentional gameplay. Global axial coordinate ordering such as raw `Q` then `R` can create a hidden handedness between geometrically mirrored encounters. Prefer target-relative vector ordering; when a relative vector is undefined (for example co-located ships), use an explicit physical encounter-bearing reference. Validate both ship movement and autonomous-object movement such as Missile pursuit under physical mirror transformations.

Mirrored and paired-sensitivity studies should assign random streams to **physical entities and event types**, not to processing labels such as Side A/Side B. A side swap must not silently hand a different sequence of random values to the same physical ship. When comparing closely related conditions, prefer common random numbers so the observed delta is dominated by the condition rather than independent Monte Carlo noise. Preserve event-stream identity in study metadata when it is part of a blocking symmetry or sensitivity claim.

When a research consumer claims parity with accepted finite-map mechanics, maintain a **shared machine-readable C#/Python geometry fixture** that is executed by both implementations. Include map shape/cell count, pre-contact search, off-axis movement, shortest-path choices, boundary behavior, moving-target Missile pursuit, terminal arrival, range exhaustion, and physical mirror cases. Python-only agreement with itself is not production parity; native C# compilation/tests remain authoritative.

If a prior broad study exposes a side-label asymmetry, do not merely average the two orientations and proceed. First determine whether the cause is tactical sequencing, coordinate tie-breaking, RNG ownership, telemetry ownership, or another consumer effect. Make corrected side/mover mirror equivalence a blocking gate before extending that consumer to a more combinatorial population such as mixed-TL ships.

## CP127 rule-invariant versus provisional-table authority

When a provisional whole-ladder table conflicts with an explicit game-facing invariant, do not silently assume the later table superseded the rule merely because its checkpoint number is newer. Distinguish **rule authority** from **candidate numerical authority**. A later candidate may intentionally replace a rule only when that replacement is explicit in the design record; otherwise reconcile the numerical table back to the rule and preserve the historical candidate as evidence.

Conversely, do not over-apply a tactical invariant to a different rules layer. Strategic FTL movement is a separate campaign quantity from tactical STL or Missile Move and may use an intentionally uneven progression when the Concept explicitly permits later maturation. Document such exceptions in both human-readable and machine-readable authorities so future passes do not have to infer whether the difference was deliberate.

Before a major mixed-TL or combinatorial study, run a **main-subsystem stability audit**: compare active Concept rules, the current numerical matrix, Storyboard/Tech Table references, and accepted simulation evidence. Resolve hard authority mismatches first; then use focused one-axis attribution only for concrete numerical anomalies. Do not require equal adjacent-TL win rates. Strong era-entry or maturation steps are acceptable when they arise from coherent, intended subsystem improvements rather than one accidental scalar.

Once a main-subsystem table has passed such a stabilization gate, raise the burden for reopening it. Later retuning should require a demonstrated defect, newly implemented mechanic, mixed-/legacy-TL interaction, or AUX/support interaction that materially changes the causal interpretation. Preference for a smoother curve is not by itself sufficient evidence.


## Evidence-retention and full-repository packaging hygiene

Complete checkpoints must preserve enough evidence to prove accepted lineage without recursively carrying every predecessor's raw Monte Carlo output forever. For an accepted predecessor, retain the exact native-results archive SHA-256 and byte size, the native-acceptance summary, a complete per-entry hash manifest when the raw archive is externalized, and the compact decision-relevant analyses/summaries used by later checkpoints. Raw trial-level `variants.csv` data and other large result files need not be embedded in every successor full-repository ZIP when those provenance records are preserved.

Do not rewrite frozen historical checkpoint scripts merely because a later packaging pass externalizes an archive they once consumed. Keep the historical checkpoint byte-stable, document the external rerun dependency beside its evidence, and make the current checkpoint consume the curated evidence authority instead.

The shared pre-package hygiene gate must reject accidental validation-evidence archive growth before packaging. Unless an explicit future checkpoint changes the policy, a ZIP under `docs/validation/evidence/` may not exceed 5 MiB and all such ZIPs together may not exceed 16 MiB. Source/reference archives under `docs/references/` are outside this budget and remain part of complete checkpoints. A deliberate exemption must be documented rather than silently bypassed.


## Whole-ladder sensitivity before mixed-TL ecology

After a pure-TL main-subsystem table has passed a stabilization gate, characterize the frozen ladder broadly before moving immediately into legal mixed-/legacy-TL builds. Preserve one whole-population control across all TL distances, then use adjacent matched-composition counterfactuals to estimate which subsystem families materially contribute to each one-step technology transition. A counterfactual that temporarily substitutes lower-TL performance values into the higher-TL side is a causal research probe only; it must not be registered as a legal mixed-TL build or interpreted as a promoted component combination.

Separate **combat-performance sensitivity** from **construction-envelope sensitivity**. Performance holdbacks should preserve the higher-TL ship's construction footprint, composition, and branch availability so the measured delta is not silently caused by fitting a different ship. Space miniaturization and Hull-capacity changes should instead be tested by deterministic legal-build re-enumeration. This avoids attributing a larger legal design envelope to an individual combat stat.

When AUX/support progression remains intentionally deferred, compare an all-options population with a clearly declared control that removes only the deferred optional choices whose values could contaminate the main-table interpretation. Do not remove stabilized main systems merely to simplify the sample. Report the difference as an AUX-boundary diagnostic, not as proof that optional systems are good or bad in isolation.

One-step subsystem holdback effects are **marginal and non-additive**. Interactions among Sensors, EW, weapons, power, defense, geometry, and construction mean their deltas do not sum to the total TL advantage. Rank or summarize them descriptively, preserve weapon-family stratification where useful, and treat a large effect as a review signal rather than an automatic request to smooth the numerical ladder. Strong coherent maturation or era-entry steps remain acceptable.

A broad sensitivity checkpoint should reuse accepted pairing identities, seeds, physical RNG ownership, and finite-map geometry where possible. Exact reproduction of an accepted overlapping control is a high-value blocking regression gate before new sensitivity conclusions are trusted.


## CSV evidence schemas must be explicit at heterogeneous aggregation boundaries

When a validation/research CSV combines multiple row categories (for example baseline lanes plus holdback lanes), do not infer the file schema from the first row unless all row producers are contractually identical. Define the output field list explicitly and require every row category to populate every field, using neutral values such as zero where appropriate. Permanent preflight/unit coverage should serialize at least one row from each category through the actual writer boundary. This prevents late native failures where expensive simulation completes successfully but evidence serialization rejects a field introduced only by later row types.

Checkpoint wrappers may expose deterministic worker parallelism as a validated performance-only parameter when the underlying scheduler preserves task/seed identity and deterministic merge ordering. Record the worker count in acceptance evidence; do not require a repository edit to tune concurrency.
