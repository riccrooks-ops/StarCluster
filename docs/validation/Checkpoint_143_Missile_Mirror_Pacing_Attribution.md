# Checkpoint 143 — Missile-Mirror Pacing Attribution

## Status

Candidate pending native Windows acceptance. CP142 — Combat Surface Deep Reconciliation — is the native-accepted research-integration baseline. CP143 changes no production C#/Godot mechanics, no source Technology Matrix value, no CP142 reconciled combat characteristic, and performs no balance tuning or promotion.

## Purpose and hard scope

CP143 is the deliberately bounded diagnostic requested after CP142 isolated Missile-vs-Missile as the remaining major gameplay-duration problem. It does **not** attempt to solve or optimize Missile mirrors. Its only job is to explain where the turns are being spent before the project zooms back out to the substantive whole-combat Stage-A matrix.

The paired population is exactly the 1,980 CP142 Missile-mirror scenarios: TL1 GP↔GP plus TL2-TL9 GP/Swarmer ordered pairings, all ten combat strata, and all six CP142 resource labels. The master seed, scenario IDs, reconciled mechanics, hard 60-turn sentinel, and 25-turn pacing boundary are unchanged.

`R1_CENTRAL_NO_MAJOR` and `R5_CENTRAL_HIGH_DEMAND` remain intentionally duplicated **only for exact CP142 paired attribution**. They are not considered independent executable resource levels. The next substantive whole-combat run will collapse the metadata-only R5 level unless a genuine executable AUX-demand mechanic exists by then.

## Observation-only instrumentation

The canonical full-map kernel now emits optional Missile attribution events when an event sink is supplied:

- per-turn launch decision and explicit block reason;
- launch turn, profile, magazine Flight, and GP/Swarmer subflight identity;
- terminal arrival timing and launch-to-terminal elapsed turns;
- PDS attempts/interception and guidance outcome for each terminal subflight;
- range exhaustion;
- per-turn in-flight inventory;
- end-of-turn Shield/Armor/Hull recovery totals and TP-conflict state;
- existing movement order/reason telemetry used to distinguish opening toward preferred weapon range from closing after track loss.

These events are observation-only. Twelve deterministic telemetry-off/on probes require exact result and existing turn-telemetry identity. In addition, CP143 carries a compact reference signature extracted from the native-accepted CP142 result set and requires **1,980/1,980 exact matches** for winner, unresolved state, turn count, and termination cause.

## Authoring attribution result

All 1,980 paired Missile-mirror scenarios executed with zero errors. Outcome/duration totals are intentionally identical to accepted CP142:

- 1,751 resolved;
- 1,085 resolved at 25+ turns;
- 228 hard 60-turn sentinels;
- 1 conservative mutual-offensive-exhaustion stalemate;
- median resolved duration 29 turns;
- P90 resolved duration 46 turns.

The new attribution identifies a clear baseline pacing mechanism.

### 1. Flight transit is not the principal delay

Across the whole population:

- mean first launch turn: 3.22;
- mean first terminal turn: 3.25;
- mean launch-to-terminal elapsed time: **0.03 turns**;
- range-exhausted missiles: **0**;
- out-of-range launch-block turns: **0**.

Once a Flight is actually launched, it almost always terminals in the same Missile phase. The current Missile-mirror pacing problem is therefore not primarily missile travel time/endurance.

### 2. Firm-track / preferred-weapon-range mismatch is the baseline cadence bottleneck

Missile launch requires Firm track, but EngageAdaptive currently treats Missile maximum range as its preferred weapon range. After a successful close/launch, the symmetric Missile ship tends to reopen toward that longer weapon envelope; the next turn it commonly lacks Firm track and closes again. This produces a repeated open/close acquisition cycle.

Across all Missile-mirror decision-turns:

- **71.2%** lack Firm track because the selected sensor/acquisition envelope does not provide Firm track at the current geometry;
- **0.0%** of those losses are classified as ECM downgrades in this paired population;
- effective-range Open orders occupy 18.8% of side-turns;
- track-close Close orders occupy 35.5% of side-turns;
- mean interval between Missile launch turns is 3.56 turns.

The transparent pacing classifier therefore labels 1,284/1,980 scenarios `SENSOR_WEAPON_ENVELOPE_OSCILLATION`: all 1,085 long-resolved cases plus 199 of the 228 turn-cap cases. Another 29 cap cases are dominated by `TP_LAUNCH_DENIAL`, overwhelmingly in POWER_CRISIS. The remaining 666 cases resolve under 25 turns; the single safe stalemate remains offensive exhaustion.

This is a diagnostic classification, not a tuning prescription.

### 3. PDS, recovery, guidance, and TP amplify the baseline bottleneck

The baseline oscillation is not sufficient by itself to make every fight long. The defensive context determines whether the sparse launch cadence still produces a timely kill.

Whole-population aggregates:

- PDS intercepts: 13.7% of terminal subflights;
- guidance success: 81.1% of un-intercepted terminal attempts;
- total defensive recovery: 29.4% of connected Missile raw damage;
- TP-denied weapon-plan turns: 2.2% of all side-turns, concentrated in POWER_CRISIS.

The contrast among strata is particularly useful:

- **ARMOR_PRESSURE:** median 16 turns, 0 caps, only 3 long resolutions; no PDS and recovery ≈14% of Missile raw damage. The same acquisition oscillation exists, but each successful delivery makes enough lasting progress.
- **BALANCED_CORE_NO_PDS:** median 26, 3 caps, 112 long resolutions. This proves the baseline pacing issue exists even with PDS removed.
- **KINETIC_PDS_PRESSURE:** median 35 with ~27% terminal interception.
- **ENERGY_PDS_PRESSURE:** median 34 with ~22% terminal interception.
- **AMM_PDS_PRESSURE:** median 39 with ~32% terminal interception and ~36% recovery.
- **POWER_CRISIS:** median 40 and 116/198 caps; ~33% terminal interception, ~35% recovery, plus ~12.8% of side-turns with TP-denied Missile weapon plans.

Thus PDS/defensive recovery/resource pressure are real amplifiers, but they act on top of a launch-opportunity cadence already constrained by the Sensor/weapon-range relationship.

### 4. Technology-level response reinforces the interpretation

The problem is strongest in the middle ladder and largely disappears at TL9:

- TL2 median 31;
- TL3 33;
- TL4 32;
- TL5 34;
- TL6 33;
- TL7 30;
- TL8 22;
- TL9 15 with zero caps.

Mean launch gap peaks around 4.5 turns at TL5-TL6 and falls to ~2.0 at TL9 as the broader Sensor/guidance/offense package catches up. This is evidence for an interaction surface, not a universal requirement to increase Missile damage.

## Interpretation boundary

CP143 makes **no Missile, PDS, Shield, Sensor, movement, TP, guidance, or AI tuning change**. The attribution does not justify promoting any numerical change in isolation.

The key diagnostic conclusion is:

> Current Missile-mirror pacing is primarily a launch-opportunity / Sensor-to-weapon-envelope interaction, with PDS, recovery, guidance loss, and TP pressure acting as secondary amplifiers. Missile flight transit itself is negligible in almost all paired cases.

That conclusion is sufficient for this bounded pass. CP143 intentionally stops here rather than beginning a Missile-focused optimization loop.

## Next stage

After native acceptance, return immediately to the broad multivariate program:

- collapse metadata-only `R5_CENTRAL_HIGH_DEMAND` into its executable-equivalent R1 condition;
- retain the five distinct executable resource environments;
- run the whole-combat Stage-A matrix across 137 same-TL ordered weapon pairings × 5 resources × 10 strata = **6,850 distinct scenarios**;
- at 500 trials per scenario, execute **3,425,000 substantive trials**;
- analyze response surfaces for viability, dominance, counter sensitivity, TL drift, duration, TP pressure, PDS/EW/defense interactions, and Pareto participation before tuning any subsystem.

The Missile attribution metrics should travel into that broad analysis so the known pacing mechanism can be measured in context rather than locally optimized first.
