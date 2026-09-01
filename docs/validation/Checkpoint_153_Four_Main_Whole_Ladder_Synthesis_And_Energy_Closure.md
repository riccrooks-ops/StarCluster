# Checkpoint 153 — Four-Main Whole-Ladder Synthesis and Energy Closure

Status: **candidate pending native Windows acceptance**.

CP153 is the whole-ladder synthesis checkpoint following native-accepted CP152 CR1. It intentionally makes **no production numerical changes**. The current Technology Numerical Matrix, Concept authority, C# mechanics, Shield/Armor centers, Shield Regen=2, Armor Repair=2, PDS, AUX, ECM/ECCM/Sensor, Reactor ladder, DEF/RES, movement, and missile cadence remain fixed while the four main-weapon families are studied as complete TL1–TL9 progressions.

## Research doctrine

Balance remains diversity and strategic viability rather than numerical equality. Kinetic, Energy, GP Missile, and Swarmer should each preserve a rational research/install role across their intended lifetimes without one family becoming a universal answer.

Energy is evaluated according to its intended three-mode doctrine:

- **Low:** offense while conserving TP for defense/support, or while preserving TP/main-weapon opportunity for PDS duty. Low usage is not expected to be high in unconstrained duels.
- **Standard:** normal Energy firing mode and expected dominant operating state.
- **Overload:** reserved burst performance. Each normal use adds one persistent weapon Strain and should not become routine sustained fire.
- **Forced Overload:** emergency/desperation behavior. The normal research optimizer remains safe-only and does not count beyond-limit forced attempts as routine DPS.

Strain Limit is therefore retained as an Energy identity characteristic rather than frozen by assumption.

## Energy closure design

CP152 established the broad main effects but also showed materially larger Energy interactions than Kinetic. CP153 closes those interactions with a deliberately unaliased local design instead of another broad OA alone.

At every TL it evaluates 11 factors: Low/Standard/Overload DAM, ACC, Standard/Maximum Range, Low TP, Standard-minus-Low TP gap, Overload-minus-Standard TP gap, SPEN, and Strain Limit.

Each TL contains:

- **264 pairwise-isolation candidates:** center, every single-factor alternative, and every pairwise alternative while all unrelated factors remain at the center. Strain Limit is 1/2/3/4 and is fully crossed against every other factor.
- **Two OA(81) compound blocks**, deduplicated against the isolation set, to verify multi-factor behavior away from the center. The second block explicitly reaches Strain Limit 4.
- **422 unique E candidates/TL**, **3,798 across TL1–TL9**.

Each candidate runs against the same broad E-vs-other Stage-A context population used by CP152, at 75 matched trials/cell: **82,290,000 Energy closure combats**. RepositoryOnly executes an all-candidate 50-context/TL smoke panel: **189,900 combats**.

This is intended to be the closing focused Energy-characteristic pass. CP153 selection uses only actually tested CP152/CP153 Energy candidates; it does not promote untested response-surface extrapolations.

## Whole-ladder synthesis

CP153 treats a candidate as a **complete technology ladder**, not nine independent TL winners.

- **Kinetic:** six coherent ladders synthesized directly from the accepted CP152 full 3^5 K response surface. K is not broadly re-swept.
- **Energy:** eight coherent ladders selected from the union of accepted CP152 and CP153 tested candidates, preserving distinct Strain-limit trajectories where useful.
- **GP Missile:** three coherent ladders, including the current center and two evidence-informed alternatives from accepted CP151 dedicated axial probes.
- **Swarmer:** three coherent TL2–TL9 ladders using the same evidence rule.

Intrinsic progression may remain quiet, but unexplained regression is rejected. The synthesis uses non-regression/jump constraints and penalizes Energy solutions that turn Overload into ordinary sustained fire.

The Cartesian set is **6 × 8 × 3 × 3 = 432 four-family packages**.

## Joint package testing

A deterministic screening panel selects one resource ensemble for every Stage-A TL × weapon-pair × scenario-stratum group: **1,370 contexts/package**. All 432 packages run at 20 trials/cell for **11,836,800 combats**.

The best diverse 12 packages then receive the full **6,850-context Stage-A** confirmation at 100 trials/cell: **8,220,000 combats**. Deep selection first preserves representation of all eight Energy-ladder identities, then fills the remaining slots by package balance score.

Total substantive CP153 scale is **102,346,800 combats**.

## Deferred deliberately

CP153 does not attempt to solve every remaining balance layer simultaneously. The intended sequence after four-main closure remains:

1. defense/AUX lifetime-value viability, including Shield/Armor auxiliaries and other installed AUX choices;
2. final Reactor/TP supply tuning across complete legal builds so TP remains meaningfully scarce and creates tactical opportunity cost;
3. only then numerical promotion when the evidence supports it.

No CP153 result automatically edits the source numerical matrix, Concept authority, or production C#.
