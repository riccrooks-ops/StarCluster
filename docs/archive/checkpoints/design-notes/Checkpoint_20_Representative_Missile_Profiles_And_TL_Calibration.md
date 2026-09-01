# Checkpoint 20 - Representative Missile Profiles and TL Calibration

## Purpose

Checkpoint 20 is the first substantive use of the accepted Checkpoint 19 Monte
Carlo harness. It defines a provisional, data-driven set of representative
Missile Flight, PDS, and terminal-ECM values and measures their interactions
without adding Godot UI or declaring the values final game rules.

The checkpoint answers two questions:

1. Can the simulation materialize a broad TL matrix from explicit component
   data while preserving the same authoritative Core mechanics?
2. Do observed Monte Carlo frequencies match the analytical two-window PDS,
   seeker-acquisition, and terminal-hit model across that matrix?

## Representative Missile Flight profiles

The catalog defines four capability configurations:

- **Command-guided** - live launcher datalink and Guidance Computer; no onboard
  navigation sensor or terminal seeker.
- **Seeker-only** - launcher guidance reaches the candidate hex; the terminal
  seeker must create the Firm local solution.
- **Sensor-only** - onboard navigation sensor supplies a Current/Firm local
  report; no seeker accuracy bonus.
- **Sensor plus seeker** - onboard navigation sensor supplies the terminal
  report and the seeker contributes its separate accuracy bonus.

All four are matched-component representative profiles. Later studies may vary
flight, datalink, sensor, Guidance Computer, and seeker TL independently.

## Provisional TL catalog

`Studies/checkpoint-20-representative-profiles.json` contains explicit TL 1
through TL 9 values for:

- Missile Flight speed and maximum lifetime range;
- retained datalink-report age;
- onboard sensor Firm and Approximate ranges, Active bonus, and local-track
  retention;
- Guidance Computer base hit chance;
- seeker base acquisition chance, terminal ECCM, and accuracy bonus; and
- target terminal-ECM strength.

The catalog intentionally supplies component values rather than a universal
ship-TL combat bonus. These values are runner calibration inputs only. They are
not promoted into Concept v0.3s as locked rules.

The initial standard-PDS conversion is:

- 35% interception per terminal window at equal PDS and Missile Flight TL;
- plus or minus 10 percentage points per PDS-minus-missile TL;
- bounded from 5% through 95%; and
- one attempt at TerminalEntry and one at PreTerminalAttack.

This produces an equal-TL total two-window interception probability of 57.75%
when acquisition succeeds, while preserving meaningful superior- and
inferior-TL cases for calibration.

## Calibration matrix

`checkpoint-20-terminal-tl-calibration.calibration.json` combines:

- 4 representative missile profiles;
- Missile Flight TL 2, 4, and 6;
- standard PDS TL 2, 4, and 6; and
- target terminal-ECM TL 2, 4, and 6.

The result is **108 variants**. The acceptance run uses 2,000 trials per variant
for 216,000 total trials. `--trials` may override this for later deeper runs.

Ship sensor ranges are raised only as a study control so the terminal matrix is
not accidentally converted into a launcher-detection study. Target jamming
remains enabled, and the target EW range-penalty value supplies the already
implemented terminal-ECM strength during seeker acquisition.

## Analytical contract

For per-window PDS probability `p`, conditional terminal-acquisition
probability `q`, and effective terminal attack probability `h`:

- TerminalEntry interception = `p`;
- acquisition success per launch = `(1 - p) q`;
- PreTerminalAttack interception = `(1 - p) q p`;
- attack resolution = `(1 - p) q (1 - p)`; and
- effective hit per launch = `(1 - p)^2 q h`.

For command-guided, sensor-only, and sensor-plus-seeker profiles, `q = 1` when
the fixture supplies a legitimate live Firm source. Seeker-only uses the
bounded seeker acquisition chance after net terminal ECM.

The effective-hit metric combines ordinary hits and natural-100 critical hits.
Natural 01 remains a dud, so the Guidance Computer's bounded d100 hit chance is
also the effective-hit probability conditional on attack resolution.

## Runner additions

Checkpoint 20 adds:

- a `calibrate` execution mode;
- a versioned profile-catalog and calibration-study schema;
- typed materialization of every profile/TL combination;
- analytical expectation checks for five key probabilities;
- `effect.effectiveHit` and `effect.intercepted` aggregate metrics;
- compact calibration JSON and CSV reports;
- adjacent-TL marginal reports for missile, PDS, and target ECM;
- confidence-interval checks that flag only statistically clear directional
  contradictions;
- optional `--keep-trials`; calibration discards trial journals by default; and
- append-only `execution-history.jsonl` provenance for initial and resumed
  batch invocations.

Detailed variant results remain available under `variants/`, but the user-facing
handoff is the compact calibration summary and marginal reports.

## Validation boundary

Checkpoint 20 does not require Godot. Acceptance consists of:

- the unchanged 506 engine-independent tests;
- the seven deterministic scenarios;
- twelve runner self-tests, including four calibration-specific contracts;
- the Checkpoint 19 worker-count reproducibility gate; and
- all 108 calibration variants within the configured absolute-error tolerance,
  with no statistically contradictory adjacent-TL marginal.

## Deferred calibration work

Checkpoint 20 is terminal-focused. It does not yet calibrate:

- target pursuit and missile-versus-ship speed;
- range exhaustion over multi-turn evasive movement;
- multiple simultaneous Missile Flights or PDS capacity saturation;
- power allocation, ammunition economics, or magazine limits;
- damage per effective hit; or
- independent mixed-TL components within one Missile Flight.

Those studies should build on the accepted profile and reporting contract rather
than expanding manual Godot testing.
