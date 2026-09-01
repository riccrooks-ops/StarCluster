# Checkpoint 120 - Weapon Progression Sensitivity Mapping Report v1

> **Superseded by Checkpoint 121.** CP120 combat outcomes remain valid, but its derived Missile terminal hit-rate summaries read terminal hits from the attacking side even though guidance attempts/hits are recorded on the target side. CP121 preserves the original native archive and regenerates the affected summaries without rerunning combat. CP119 remains the accepted baseline until CP121 native acceptance.


## Status

**Candidate pending native acceptance.** This report summarizes the 5-trial-per-variant authoring pass only. The authoring sample is intentionally too small for numerical promotion; it proves the sensitivity machinery and provides rough directional hypotheses for the native 2,000-trial run.

## Why CP120 exists

CP119 showed that the simplified weapon architecture is viable, but it did not tell us enough about the *shape* of the nearby numerical space. The CP119 working Missile GP ladder was powerful, and the mature Swarmer sometimes stacked larger total raw payload with coverage/PDS advantages. CP120 therefore freezes mechanics and maps the nearby numerical slopes before narrowing candidates.

## Authoring population

- 4,284 mirrored variants.
- 3,060 variants at TL1-TL6 primary calibration.
- 576 TL7 advanced variants.
- 648 TL8-TL9 endpoint/stress variants.
- 21,420 authoring engagements at 5 trials/variant.
- Zero failed mechanical gates.

## Rough GP yield signal

The authoring surface is noisy but confirms that single integer Damage steps can cross large layered-defense breakpoints. Examples from the legal-target aggregate:

- TL3: D5 -> D6 approximately +23 pp; D6 -> D7 approximately +9 pp.
- TL4: D5 -> D6 approximately +15 pp; D6 -> D7 approximately +12 pp.
- TL5: D5 -> D6 approximately +10 pp; D6 -> D7 approximately +17 pp; D7 -> D8 only a few points in this small sample.
- TL6: D5 -> D6 approximately +14 pp; D6 -> D7 approximately +14 pp; D7 -> D8 approximately +11 pp.

The exact magnitudes are not authoritative at five trials. The important result is that the runner now exposes where the marginal slopes change. The native run can therefore distinguish a robust progression step from an integer-threshold accident.

## Rough Swarmer signal

The selected-comparison output successfully separates packet, coverage, and PDS axes.

- Increasing packet size produces much larger changes than PDS saturation in many layered-defense lanes.
- The TL3 D2 -> D3 packet control is especially large in the bounded sample, confirming the known small-packet threshold problem.
- Mid/mature PDS-saturation changes measurably reduce PDS interception probability, but their combat value is target-dependent.
- The no-PDS control makes it possible to distinguish `PDS got less effective` from `the packet itself became strong`.
- The TL6 D5-per-packet upper control is intentionally over-budget and exists only to show how much apparent Swarmer strength can be raw-payload contamination.

The native run should be used to identify the smallest packet/coverage/PDS package that preserves a real Swarmer niche.

## Rough Kinetic signal

The authoring data reproduces the expected mechanical separation:

- +5 ACC raises measured direct-hit rate by roughly five percentage points.
- +10/+15 ACC extend that slope without adding another mechanic.
- +1 DAM produces a much broader combat swing because it crosses layered-defense packet thresholds.
- +1 APEN is more target- and TL-sensitive.

This reinforces the working hypothesis that smart/maneuvering projectile progression should primarily use restrained automatic ACC steps, while DAM/APEN changes belong to separate accelerator/material/penetrator milestones when technologically justified.

## Candidate path synthesis

The report intentionally includes several progression paths rather than selecting the highest authoring win rate. The CP119 frontier GP path, maturity-delayed path, hybrid path, Kinetic +5/+10 paths, restrained Swarmer path, payload-conservative Swarmer path, and native Energy path are all reconstructed from executed Layer-1 cells.

The native decision should focus on **robust regions**, not a single highest-scoring path.

## Native questions

CP120 native evidence should answer:

1. Which GP Damage steps are smooth improvements and which are major integer breakpoints?
2. At what TL should D6 and D7 enter without making Missile GP broadly dominant in the campaign core?
3. How much of Swarmer value comes from packet size versus ACC versus PDS saturation?
4. Can a Swarmer remain useful while keeping nominal payload at or below the contemporary GP budget?
5. Is +5 Kinetic ACC the restrained automatic step, or does the native slope support a different cadence?
6. Do Shield-heavy, Armor-heavy, PDS-heavy, and light targets preserve recognizable family niches?

No result from this checkpoint automatically promotes a number.
