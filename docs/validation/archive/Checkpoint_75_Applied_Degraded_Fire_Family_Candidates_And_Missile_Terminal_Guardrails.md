# Checkpoint 75 - Applied Degraded-Fire Family Candidates and Missile Terminal-Guidance Guardrails

## Intent

Checkpoint 75 starts from the accepted Checkpoint 74d baseline. Native CP74d completed with warning-as-error build success, all 853 unit tests passing, all 11 runner stages passing, 47 ScenarioRunner self-tests passing, the 20-variant actual-consumer preflight and one-trial smoke passing, and the 20-variant / 200,000-trial Approximate-track degraded-fire foundation study completing with zero failed gates and zero trial errors.

CP74d established the generic direct-fire foundation and showed that -20 percentage points is a useful provisional middle candidate while -30 materially lengthens engagements. CP75 does not reopen that broad sweep. It applies the leading -20 candidate and the newly requested -25 candidate to controlled Kinetic/Energy family packages so that family asymmetry, pacing, and combat utility can be reviewed before any production assignment is considered.

CP75 also makes two previously agreed missile rules explicit in code, tests, and Concept v0.6n. These rules are independent of direct-fire degraded fire.

## Direct-fire applied study

The primary study is `tl1-itc17-applied-degraded-fire-family-candidates`.

It contains 40 variants: two weapon-family orientations (`Kinetic vs Energy` and `Energy vs Kinetic`) x two fixed ranges (2 and 3 hexes) x ten controlled profiles. Every context contains:

1. an unjammed Firm reference;
2. a bilateral-ECM Approximate-track Firm-only control;
3. Kinetic-only -20;
4. Kinetic-only -25;
5. Energy-only -20;
6. Energy-only -25;
7. both families at -20;
8. both families at -25;
9. Kinetic -20 / Energy -25; and
10. Kinetic -25 / Energy -20.

The Approximate-track lanes use bilateral normal ECM with no ECCM response so the direct-fire eligibility difference remains observable. Balanced-0, AcquisitionFirstAutoActive, no STL overload, and no Active Sensor overload remain controlled. Missiles and secondary weapon families are excluded.

The normal substantive workload is 40 variants x 10,000 trials = 400,000 trials, preceded by an actual-consumer preflight and 40 one-trial full-pipeline smoke executions. The study writes `degraded-fire-applied-review.csv` for human review.

No release gate promotes a family assignment or a -20/-25 penalty. Production direct-fire weapons remain unchanged until the results are reviewed and a later checkpoint explicitly records any accepted assignment.

## Missile terminal-guidance guardrails

### Baseline command-guided missiles

A baseline command-guided missile may make its terminal attack only from a live Current/Firm launcher datalink report. A retained report is not a live command solution. A peer Current/Firm report does not substitute for the launcher command link unless the missile's terminal profile explicitly enables peer terminal guidance.

`MissileTerminalProfile.AllowsPeerTerminalGuidance` is the explicit future capability seam. Existing prototype/baseline profiles default to `false`, so this checkpoint does not silently grant cooperative terminal guidance to low-technology command-guided missiles.

### Sensor plus seeker

A missile with an onboard navigation sensor and a terminal seeker may use a legitimate live Firm launcher report or its own Current/Firm local report directly. If the seeker is needed to improve an Approximate solution, the missile must first possess at least an Approximate missile-local navigation track. A merely remote Approximate datalink/peer cue cannot jump directly to terminal Firm through the seeker.

This preserves the previously agreed hierarchy: the local navigation sensor establishes a local track; the terminal seeker refines that local track into Firm terminal lock.

### Seeker-only architecture

A seeker-only missile remains distinct. It has no general onboard navigation sensor, so a Current or Approximate remote cue may bring it to the target hex and the co-located seeker may then attempt its own local acquisition. This does not grant direct-fire degraded-fire behavior and does not make co-location an automatic impact.

### Common terminal rule

The missile's actual terminal attack still requires the appropriate Firm terminal solution for its architecture. Approximate information may be sufficient to navigate/search where that architecture permits it, but it does not itself authorize a missile attack.

## Release-gate audit

CP75 adds six study-specific gates:

- `tl1-c75-variant-coverage`: exact four contexts x ten profiles;
- `tl1-c75-firm-reference-clean`: unjammed references establish Firm observations, spend no ECM/ECCM power, and execute ordinary direct fire;
- `tl1-c75-firm-only-approx-blocked`: bilateral-ECM controls establish Approximate observations but Firm-only weapons do not fire;
- `tl1-c75-family-package-wiring`: applied lanes exercise Approximate direct fire with only the configured -20/-25 family packages;
- `tl1-c75-no-missile-degraded-fire`: the study remains Kinetic/Energy direct-fire-only; and
- `tl1-c75-outcomes-review-only`: family preference, penalty preference, outcomes, and pacing remain human-review evidence rather than release targets.

The actual-consumer validator independently checks family orientation, fixed-range movement mode, control labels, Sensor/EW fixture, and exact side-by-side family/penalty mapping before Monte Carlo execution.

## Native acceptance

Extract this complete checkpoint repository over the repository root, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-75\apply_checkpoint_75.ps1 -RepositoryOnly
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-75\apply_checkpoint_75.ps1 -Jobs 24
```

Expected normal workload:

- 11 runner stages;
- 856 unit tests if no unrelated test-count changes occur (CP74d's 853 plus three new missile terminal regressions);
- 924 deterministic Sensor/EW foundation rows;
- 40-variant actual-consumer applied degraded-fire preflight;
- 40 one-trial full-pipeline smoke executions;
- 40 substantive variants / 400,000 substantive trials; and
- 47 ScenarioRunner self-tests.

Review `out/checkpoint-75/tl1-applied-degraded-fire/degraded-fire-applied-review.csv` together with the substantive summary before recommending any production family/penalty assignment.

## Deep Calibration

Do not run Deep Calibration by default. CP75 is a focused applied candidate study and missile-rule lock. Deep Calibration is reserved for a normal-acceptance regression, a newly exposed cross-system dependency, or an explicit later calibration decision.

## Local pre-handoff limitation

The packaging environment used to assemble CP75 does not provide native PowerShell or the pinned .NET SDK, so the authoritative warning-as-error build, unit-test execution, repository contract execution, and Monte Carlo runs must still be performed on native Windows. Pre-handoff QA therefore includes static cross-study integration auditing, JSON/schema/reference checks, manifest verification, clean-staged archive verification, and full Concept rendering/visual inspection; native acceptance remains the final gate.
