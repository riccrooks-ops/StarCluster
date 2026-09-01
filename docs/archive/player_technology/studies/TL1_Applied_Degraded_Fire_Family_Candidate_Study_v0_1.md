# TL1 Applied Degraded-Fire Family Candidate Study v0.1

## Current architecture interpretation

This file is retained as historical calibration evidence. Current architecture separates degraded-fire **permission** from its numerical penalty: a specific weapon/variant/upgrade grants permission to fire from Approximate, while the ship Tactical Computer/fire-control profile supplies the degraded-fire penalty. Historical `-10/-20/-25/-30` study fields therefore represent candidate computer/fire-control penalties applied to explicitly enabled study weapons; they are not production weapon-profile-owned numbers. The current TL1 computer working value is -25 percentage points, and no production weapon is enabled merely by this clarification. Ordinary missiles remain Firm-terminal by default; any future Approximate-target missile rule is separate and missile-specific.

## Question

After Checkpoint 74d established that weapon-specific Approximate-track direct fire works as a data-driven trait, should TL1 Kinetic weapons, TL1 Energy weapons, both families, or neither receive that capability, and is a -20 or -25 percentage-point accuracy penalty the stronger provisional candidate?

## Accepted starting evidence

Checkpoint 74d remains the foundation baseline. It demonstrated that:

- Firm-only direct-fire weapons remain blocked when bilateral ECM leaves only Approximate tracks;
- an explicitly trait-enabled direct-fire weapon can fire from an Approximate track;
- the configured accuracy penalties are reflected closely in final hit chance;
- -20 percentage points was the leading provisional middle candidate from the -10/-20/-30 foundation sweep;
- -30 remained viable but substantially lengthened combat;
- no production TL1 weapon was promoted and missiles/torpedoes received no degraded-fire permission.

Checkpoint 75 adds the requested -25 candidate and applies the two leading middle penalties to weapon-family assignments rather than rerunning the broad foundation sweep.

## Controlled study

Study ID: `tl1-itc17-applied-degraded-fire-family-candidates`.

The study uses the accepted 35-Space balanced EW-major build, Balanced-0 sensing, 5 Tactical Power, FullVolleyFirst, no overload, no ECCM, no PDS, no missiles, and fixed ranges 2 and 3. Bilateral normal ECM creates the same controlled Approximate-track condition used by the foundation study. Both Kinetic-vs-Energy orientations are retained to expose any Side-A/Side-B asymmetry.

Each of the four pairing/range contexts contains ten paired variants:

1. unjammed Firm reference;
2. bilateral ECM with both weapon families Firm-only;
3. Kinetic only at -20;
4. Kinetic only at -25;
5. Energy only at -20;
6. Energy only at -25;
7. both families at -20;
8. both families at -25;
9. Kinetic -20 / Energy -25;
10. Kinetic -25 / Energy -20.

Total: 40 variants x 10,000 trials = 400,000 substantive trials, preceded by a 40-variant actual-consumer preflight and 40 one-trial full-pipeline smoke executions.

## Interpretation

This is an **applied candidate study**, not an automatic production promotion. Release gates validate family/penalty wiring, track conditions, Firm-only controls, and missile exclusion. Family assignment, -20 versus -25 preference, win share, pacing, and any asymmetry are review evidence.

Questions for the native result review:

- Does one direct-fire family gain clearly more useful tactical agency from Approximate-track fire than the other?
- Does granting degraded fire to both sides meaningfully erode the value of ECM, or does the accuracy loss preserve a real jamming advantage?
- Is -25 meaningfully different from -20 in pacing and family balance, or are they operationally too close to justify separate production values?
- Do mixed Kinetic/Energy penalty packages reveal a natural family-specific assignment?
- Does any candidate produce excessive unresolved combat or pacing inflation?

## Missile boundary

Checkpoint 75 does not treat missile navigation, datalink guidance, onboard navigation sensing, peer guidance, seeker acquisition, or terminal lock as degraded direct fire.

- baseline command-guided missiles still require a live Current/Firm launcher command solution and live communication link at terminal opportunity;
- peer guidance can authorize a terminal Firm solution only when an explicit missile-profile capability enables it;
- sensor-plus-seeker missiles may use a seeker to refine an Approximate solution only after the missile has at least an Approximate **missile-local navigation track**;
- a remote Approximate cue may support navigation but does not substitute for that local track in the sensor-plus-seeker architecture;
- seeker-only missiles remain a distinct architecture whose co-located seeker performs its own local acquisition from the remote cue because no general onboard navigation sensor exists;
- every terminal missile attack still requires a legitimate Firm terminal solution before the attack roll.
