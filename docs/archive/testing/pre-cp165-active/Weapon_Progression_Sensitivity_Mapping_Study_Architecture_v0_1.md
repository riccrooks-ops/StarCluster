# Weapon Progression Sensitivity Mapping Study Architecture v0.1

## Purpose

Checkpoint 120 maps the numerical sensitivity around the simplified CP117-CP119 weapon architecture before any working value is promoted. It deliberately widens the **numeric** envelope while keeping the **mechanical** envelope frozen.

The study answers two questions:

1. Where are the important GP Missile yield breakpoints, and how sensitive are candidate progression schedules to when each +1 Damage step appears?
2. How much of Swarmer value comes from packet strength, terminal coverage, and PDS saturation separately, while Kinetic smart-projectile progression is checked against ACC/DAM/APEN single-axis controls?

The study is diagnostic only. Outcome rates are review evidence and never automatic promotion gates.

## Frozen mechanical boundary

### Energy

Energy is a native same-TL reference only. CP120 does not retune Energy or add Energy mechanics.

### Kinetic

Normal Kinetic ammunition remains generic and automatic. CP120 does not create selectable normal ammunition.

The only candidate axes are single-axis controls:

- +5, +10, or +15 ACC for smart/maneuvering projectile sensitivity;
- +1 DAM as an accelerator/packet-strength control;
- +1 APEN as a physical-penetration control.

No Kinetic profile changes SPEN, packet count, ordered packets, or ammunition selection.

### Missile GP

GP Missile profiles vary **Damage/yield only**. The study holds the inherited diagnostic GP baseline at SPEN 1 / APEN 2 so yield sensitivity is not confounded with penetration specialization.

This does not promote SPEN 1 / APEN 2 as the final GP baseline.

### Swarmer

Swarmer remains:

- one Missile Flight counter;
- one ammunition expenditure;
- one terminal attack roll;
- exactly two internal damage packets;
- one normal PDS reaction sequence.

Candidate axes are limited to:

- packet Damage;
- terminal guidance/coverage bonus: 0 / +5 / +10 / +15;
- defender PDS interception penalty: 0 / 5 / 10 / 15 percentage points.

No extra tactical counters, extra terminal attacks, extra PDS windows, independent submunition inventories, SPEN/APEN creep, or specialist-warhead menu is introduced.

## Evidence weighting

- **TL1-TL6:** primary campaign calibration evidence.
- **TL7:** advanced-game validation.
- **TL8-TL9:** endpoint/stress evidence.

The executable population is intentionally denser in TL1-TL6. Endpoint behavior may expose an architectural defect, but it cannot by itself justify whole-ladder complexity.

## Target ecology

Six legal exact-fill same-TL targets are shared by Energy, Kinetic, and Missile attackers:

- Energy balanced;
- Energy defense-specialist;
- Kinetic balanced;
- Kinetic EW-specialist;
- Missile balanced;
- Missile defense-specialist.

Three controlled fixtures are diagnostic only:

- **Missile-defense no-PDS control:** identical base package with PDS removed to isolate PDS cost and Swarmer saturation value.
- **Armor-heavy control:** Shield/PDS/Hardener removed and Armor exaggerated to expose physical packet/APEN sensitivity.
- **Light control:** Shield/PDS/Hardener removed with very low Armor to expose coverage/accuracy value.

Controlled fixtures never carry promotion weight.

## Layer 1 - Controlled sensitivity mapping

### GP Missile yield

Adjacent yield controls are sampled around the likely campaign-era milestones. All explicit GP candidates retain SPEN 1 / APEN 2 and one damage packet.

The study reports, by TL and target:

- conditional win rate;
- unresolved rate;
- mean turns;
- target Hull damage;
- Shield absorption;
- marginal change versus the next lower sampled Damage value.

The purpose is to locate integer breakpoints, not to reward the highest Damage candidate.

### Swarmer main effects

The Swarmer grid uses selected main effects and interactions rather than a full Cartesian product. It compares:

- packet-size steps at fixed coverage/PDS settings;
- ACC changes at fixed packet/PDS settings;
- PDS-saturation changes at fixed packet/ACC settings;
- a few intentional upper/lower packet controls to reveal when apparent Swarmer strength is actually raw-payload contamination.

The no-PDS fixture provides an explicit isolation lens for how much value is attributable to PDS resistance rather than packet/coverage behavior.

### Kinetic automatic progression

Kinetic controls isolate:

- ACC slope: +5 / +10 / +15;
- +1 DAM;
- +1 APEN.

Direct hit rate is reported alongside combat outcomes so the study can distinguish a clean smart-guidance effect from broader defensive-threshold changes caused by DAM/APEN.

## Layer 2 - Candidate progression-path synthesis

CP120 does not run a second combat simulation for each progression path. Instead, it synthesizes several candidate ladders from Layer-1 rows that were already executed against the same ecology.

The path summary includes:

- CP119 frontier-timing GP ladder;
- a maturity-delayed GP ladder;
- a hybrid early-fission/late-fusion ladder;
- current Kinetic;
- +5 and +10 Kinetic smart-accuracy paths;
- restrained and payload-conservative Swarmer paths;
- native Energy reference.

Path results are reported separately for primary, advanced, and endpoint tiers.

## Population shape

The study reconstructs:

- 135 exact-fill underlying builds;
- 4,284 mirrored variants;
- 2,952 Missile variants;
- 1,008 Kinetic variants;
- 324 Energy reference variants;
- 3,060 primary TL1-TL6 variants;
- 576 TL7 advanced variants;
- 648 TL8-TL9 endpoint/stress variants.

Native substantive workload: **2,000 trials per variant = 8,568,000 engagements**.

Checked-in authoring evidence uses only **5 trials per variant = 21,420 engagements** and is plumbing/directional evidence, not calibration authority.

## Required outputs

The runner emits:

- `variants.csv`
- `builds.csv`
- `target_fixtures.csv`
- `profile_catalog.csv`
- `integration_summary.csv`
- `gp_yield_sensitivity.csv`
- `swarmer_sensitivity.csv`
- `sensitivity_delta_summary.csv`
- `pds_isolation_summary.csv`
- `kinetic_sensitivity.csv`
- `progression_path_summary.csv`
- `progression_path_tier_summary.csv`
- `movement_order_summary.csv`
- `analysis.json`
- `summary.json`

## Interpretation guardrails

1. Do not optimize one pooled all-target score. Weapon families are intentionally asymmetric.
2. A strong specialist/branch result against its intended defense is not automatically imbalance.
3. A candidate that gains value mainly because it increases raw payload beyond the intended budget must be identified as payload contamination.
4. PDS saturation is evaluated separately from packet penetration.
5. TL8-TL9 do not receive equal design weight with the campaign core.
6. Internal critical/subsystem damage remains outside this consumer.
7. No CP120 outcome automatically changes the Concept, production runtime, CP109 numerical matrix, or CP110 Reactor profile.
