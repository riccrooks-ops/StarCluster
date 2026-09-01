# CP131 Late Missile Warhead Maturation Study v0.1

## Purpose

Native-accepted CP130 found that a uniform +2 GP Missile DAM sensitivity across TL1-TL7 restores broad Main Missile viability while preserving meaningful PDS and Shield counters. CP130 did **not** find a satisfactory late-TL solution: TL8 D17/SP3/AP4 improved aggregate family performance but left single-Main GP Missile too defense-dependent, while TL9 D18/SP4/AP5 remained substantially disadvantaged against contemporary Kinetic/Energy ships.

CP131 therefore performs one bounded late-warhead characteristic-space pass before any numerical promotion. The current CP128 Tech Table remains frozen. CP130's TL1-TL7 `damage_plus_2` result is carried as provisional research evidence and is **not rerun**. Only TL8 and TL9 candidate warheads execute in CP131.

## Frozen controls

- Accepted production implementation baseline remains CP122 Corrected Replacement 1.
- Accepted current numerical authority remains `technology_numerical_matrix_v0_5.json` from CP128.
- CP129 remains the accepted broad pure-TL sensitivity baseline; CP130 is the accepted Missile progression evidence baseline.
- Kinetic and Energy Main weapons remain unchanged.
- Missile Delivery, Guidance, Move, Range, launch TP, and the 25-Flight per-Main magazine remain unchanged.
- Swarmer remains unchanged.
- PDS, Shields, Armor, Sensors/EW, Tactical Power, movement, and the radius-5 System Map remain unchanged.
- No AUX Magazine is executed. The future +25-Flight Magazine remains an endurance option, not a prerequisite for baseline Main Missile viability.
- Matter-conversion warheads remain deferred. CP131 late candidates represent mature/high-output antimatter payloads.
- No candidate is automatically promoted.

## Accepted CP130 reference

CP131 retains the compact native-accepted CP130 result archive plus extracted chart/context evidence. The accepted TL1-TL7 +2 DAM rows are carried forward unchanged for later whole-ladder chart replots.

Two CP130 late anchors are blocking substantive replication controls:

- TL8: D17 / SPEN3 / APEN4 (`d17_sp3` in CP130)
- TL9: D18 / SPEN4 / APEN5 (`d18_sp4_ap5` in CP130)

At 100 trials per variant, CP131 must reproduce the accepted CP130 anchor metrics exactly before new candidates are trusted.

## TL8 primary sweep

Center: accepted CP130 D17/SP3/AP4.

- DAM: **15, 16, 17, 18, 19**
- SPEN: **3, 4, 5, 6**
- APEN: **4** throughout

This is a complete 5 x 4 factorial: **20 candidates**. APEN remains 4 because CP130 proved APEN5 was redundant against TL8 Armor Protection 4.

## TL9 primary sweep

Center: accepted CP130 D18/SP4/AP5.

- DAM: **16, 17, 18, 19, 20**
- SPEN: **4, 5, 6, 7**
- APEN: **5** throughout

This is another complete 5 x 4 factorial: **20 candidates**.

## TL9 APEN6 threshold probes

TL9 Armor Protection reaches 6, so CP131 adds six deliberately sparse APEN6 probes. Each has an exact APEN5 counterpart in the primary grid, allowing the Armor threshold to be measured without doubling the full TL9 space:

- D16 / SP4 / AP6
- D17 / SP5 / AP6
- D18 / SP4 / AP6
- D18 / SP6 / AP6
- D19 / SP6 / AP6
- D20 / SP7 / AP6

These are threshold diagnostics, not preselected promotions.

## Population and workload

CP131 regenerates the accepted CP129/CP130 legal pure-TL population and pairing seed, but executes only same-TL TL8/TL9 pairings involving Missile:

- Missile vs Missile;
- Kinetic vs Missile;
- Energy vs Missile.

The inherited pairing population contains 10,384 variants per TL8 candidate and 10,356 variants per TL9 candidate. CP131 therefore executes:

- 20 TL8 candidates;
- 26 TL9 candidates;
- **476,936 total variants**;
- one trial per variant in RepositoryOnly smoke;
- **47,693,600 substantive engagements** at 100 trials per variant.

The inherited full-map physical-symmetry gate remains 2,250 comparisons / 4,500 executions / zero mismatches.

## Outputs and interpretation

`family_plot_inputs.csv` carries K/E mirror references plus every candidate's Missile mirror duration/unresolved rate and K/E-vs-M results. It also adds combined Missile-family, GP-only, and single-Main GP Missile win shares versus K/E.

`missile_context_telemetry.csv` retains the CP130 PDS/no-PDS, Shield/no-Shield, GP-only, and single-Main context telemetry.

`tl9_apen6_threshold_effects.csv` directly compares each APEN6 probe to the same DAM/SPEN APEN5 primary candidate.

Successful raw per-variant CSVs and derived matrices are removed after aggregation to preserve checkpoint packaging hygiene.

The desired outcome is **not** the highest possible Missile win rate. Human review should prefer the lowest reasonable maturation package that restores single-Main credibility while preserving family identity and meaningful PDS/Shield counters. High DAM remains part of Missile identity; SPEN/APEN are evaluated as ways for that large payload to keep making progress through contemporary layered defenses, not as replacements for payload yield.
