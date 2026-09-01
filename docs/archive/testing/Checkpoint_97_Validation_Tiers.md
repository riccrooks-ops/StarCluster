# Checkpoint 97 Validation Tiers

## Must always run

- native dependency guard, repository contract, pinned SDK, warning-as-error build, and unit tests;
- accepted deterministic/movement/missile, TL1 Phase A/B, construction, Sensor/EW, and resource-semantics regressions;
- accepted CP96 cross-TL foundation v0.6 preflight and generation;
- generated CP96 1,440-variant actual-consumer preflight plus one-trial full-pipeline regression smoke;
- CP97 36-variant Adaptive Engage actual-consumer preflight;
- CP97 36-variant one-trial full-pipeline smoke;
- CP97 3,000-trial x 36 substantive Encounter/Adaptive Engage study; and
- 62 ScenarioRunner self-tests.

The accepted CP96 2.16M-trial substantive causal replay is **not** repeated merely because CP97 changes a new movement mode. CP97 preserves the historical movement modes and uses the 1,440-variant full-pipeline smoke as the regression guard. Re-run an expensive CP96-style cross-TL substantive calibration only when a later change can plausibly alter that accepted evidence.

## CP97 Engage-AI gates

- every CP97 encounter begins on opposite radius-5 map edges at range 10 with the accepted 100-fuel tactical baseline;
- pre-contact search must exercise movement and must not require the hidden target coordinate to choose the search path;
- `EngageAdaptive` uses own capabilities plus player-observable combat memory rather than hidden opponent weapon-family/TL reach;
- ordinary failed Firm acquisition must be able to drive later closure, including range 0 where legal;
- observed one-sided attack reach may drive legitimate standoff/kiting;
- the ECM2/ECCM1 control must exercise ordinary closure and same-hex burn-through without requiring a synthetic promotion value;
- a harness-only ECM3 lane must exercise at least one ECCM-overload escalation after closure is exhausted;
- a harness-only standoff lane must exercise at least one last-ditch Active Sensor overload after ordinary closure is denied by kiting;
- ECCM overload remains preferred before Active Sensor overload when hostile ECM observably caused the track problem and both are plausible;
- failed overload at range X cannot be retried at X or farther without a materially changed observable state, while closer range remains eligible;
- harness-only overload fixtures are diagnostic and cannot become technology-tree promotion evidence; and
- win rates, unresolved rates, standoff persistence, closure success, and overload frequency remain human-review evidence rather than automatic balance gates.

## Information-parity gate

The AI may use its own installed capabilities, power/Strain state, current track quality, observed enemy attacks/emissions/movement, and current-combat blackboard memory. It may not inspect hidden opponent TLs, exact ECM/ECCM ratings, internal Jamming Margin, undisclosed component statistics, or future outcomes. Later-phase observations cannot retroactively alter already committed Movement or Tactical Power decisions.

## Broader-development boundary

CP97 is a substantive game-development pass, not a reopening of the dedicated instrumentation sequence. CP96 cohort/outlier reporting remains supporting infrastructure. Future passes should continue advancing overall mechanics, mixed-/cross-TL progression, and the technology tree unless a genuine measurement blocker appears.

## Deep Calibration

Not applicable. CP97 uses bounded representative encounter lanes to validate the new tactical behavior architecture and retains accepted cross-TL work as a one-trial regression smoke.
