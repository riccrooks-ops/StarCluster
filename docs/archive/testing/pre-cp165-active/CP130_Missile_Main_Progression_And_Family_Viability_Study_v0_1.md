# CP130 Missile Main Progression and Family Viability Study v0.1

## Purpose

CP129 established that Missile is normally the longest-duration Main-weapon family in same-TL mirror combat and is usually disadvantaged against contemporary Kinetic and Energy ships despite carrying extra delivery constraints: Firm-track launch eligibility, flight time, PDS exposure, finite ammunition, guidance/seeker dependence, and target-motion routing. CP130 therefore tests whether the **general-purpose Missile warhead progression itself** is underpowered across the ladder.

This is a research-only characteristic-space pass. The accepted CP128/CP129 numerical table remains unchanged unless a later human-reviewed checkpoint explicitly promotes a result.

## Frozen controls

- Production/game C# remains frozen at accepted CP122 Corrected Replacement 1.
- Current numerical authority remains `technology_numerical_matrix_v0_5.json` from accepted CP128/CP129.
- Kinetic and Energy Main weapons are unchanged.
- Missile Delivery, Guidance, Move, Range, launch TP, and 25-Flight per-Main magazine are unchanged.
- PDS, Shields, Armor, ECM/ECCM, Sensors, and Tactical Power behavior are unchanged.
- Swarmer remains unchanged and continues to share the generic Missile Flight magazine.
- No AUX Magazine is added in CP130; the future +25-Flight Magazine remains an AUX concept to test later as endurance, not as a prerequisite for basic Main-weapon viability.
- Matter-conversion warheads remain deferred. TL8/TL9 late candidates represent maturation/high-output antimatter only.

## Population and accepted comparison

CP130 deterministically regenerates the accepted CP129 legal-build population and pairing seed, then selects only same-TL pairings containing Missile:

- Missile vs Missile,
- Kinetic vs Missile,
- Energy vs Missile.

Both side assignments and both mover orders remain present through the inherited full-map consumer. The current-warhead `control` candidate is run at all TL1-TL9 with the accepted CP129 master seed and 100 trials per variant. At substantive depth its four prior-chart quantities must reproduce accepted CP129 exactly for every TL:

1. Missile-vs-Missile population-weighted mean turns;
2. Missile-vs-Missile unresolved rate;
3. Kinetic conditional win rate against the Missile family;
4. Energy conditional win rate against the Missile family.

Kinetic-vs-Kinetic and Energy-vs-Energy mirror durations are accepted fixed references from CP129 and are carried into `family_plot_inputs.csv` for direct replotting after assessment.

## TL1-TL7 clean damage sweep

At each TL1-TL7 the GP warhead is tested independently as:

- current control;
- current +1 DAM;
- current +2 DAM.

SPEN and APEN remain exactly at the accepted values. This isolates whether basic payload magnitude compensates adequately for Missile's delivery disadvantages without confusing the result with improved guidance or penetration.

## TL8 maturation space

Accepted control is D15 / SP2 / AP4. The bounded candidates are:

- D16 / SP2 / AP4;
- D17 / SP2 / AP4;
- D16 / SP3 / AP4;
- D17 / SP3 / AP4;
- D17 / SP3 / AP5.

The nested comparisons separate raw yield, Shield penetration, and Armor penetration.

## TL9 maturation space

Accepted control is D15 / SP2 / AP4. The bounded candidates are:

- D16 / SP2 / AP4;
- D17 / SP2 / AP4;
- D17 / SP3 / AP4;
- D18 / SP3 / AP4;
- D18 / SP3 / AP5;
- D18 / SP4 / AP5.

The upper candidate is a sensitivity anchor, not a proposed promotion.

## Outputs

`family_plot_inputs.csv` contains the exact values needed to remake the two comparison plots after results are reviewed: K/E/M mirror fight length and K/E win rate versus Missile. It also includes GP-only and single-Main-vs-single-Main GP diagnostics.

`missile_context_telemetry.csv` separates contemporary Kinetic/Energy opponents by PDS/no-PDS, Shield/no-Shield, GP-only, and single-Main GP contexts. It reports Missile win share, unresolved rate, fight length, launches, magazine-consumption fraction, terminal arrivals, hits, PDS attempts/intercepts, shield absorption, armor prevention, hull damage, and Firm-track turns.

The raw per-variant CSVs and derived matrices are deleted after successful aggregation so native-result handoff does not recreate the archive-bloat problem fixed in CP128.

## Interpretation

Fifty percent is not a balance target. Missile may remain somewhat slower because flight time is part of its identity, and PDS must remain a meaningful counter. The key viability question is whether a contemporary **single Main GP Missile** remains a credible primary weapon without requiring an AUX Magazine or specialist payload simply to overcome ordinary peer defenses.

No candidate is automatically promoted by CP130. Human review must consider family win rate, fight duration, unresolved behavior, PDS/Shield context, single-Main viability, and preservation of specialist-warhead niches together.
