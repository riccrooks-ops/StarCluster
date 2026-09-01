# Checkpoint 121 Damage Resolution Scaling Report v1

## Evidence status

This report records **bounded authoring evidence**, not native acceptance. Checkpoint 119 remains the accepted baseline. CP121 supersedes the unaccepted CP120 candidate because CP120's combat execution was valid but one derived Missile telemetry path read terminal hits from the attacking side instead of the target side.

CP121 makes no production numerical change and does not modify the player-facing Concept authority.

## CP120 telemetry correction

The original CP120 native results archive is preserved as `CP120_NATIVE_RESULTS_ORIGINAL.zip` with SHA-256:

`ac76aeaa9792b1790d494fcf11817be86e3c5a922ea74138627ea481c25a3bd2`

Its native `variants.csv` SHA-256 is:

`2ec8ad0e34ef4460facb96205ec4bfb100761c23238ab546b1df48533fb1b1be`

CP121 reanalyzes those 4,284 aggregate variant rows / 8,568,000 already-completed engagements without rerunning combat. Missile launch telemetry remains attacker-side; terminal guidance attempts and terminal hits are target-side. The corrected output is under `cp120-corrected/`.

The corrected evidence confirms the combat mechanic was behaving correctly. Representative +10 Swarmer-guidance comparisons change terminal hit probability per guidance attempt by approximately:

| TL | Corrected terminal hit-rate delta | Conditional-win delta |
|---:|---:|---:|
| 2 | +9.999 pp | +18.00 pp |
| 3 | +10.000 pp | +9.36 pp |
| 4 | +9.868 pp | +12.19 pp |
| 5 | +9.906 pp | +11.25 pp |
| 6 | +9.904 pp | +4.93 pp |
| 7 | +10.032 pp | +12.81 pp |

This is consistent with the intended +10 guidance mechanic. The reporting defect did not invalidate CP120 win/loss combat outcomes.

## Exact x2 equivalence gate

Bounded authoring equivalence executed the complete CP120 4,284-variant population at 5 paired trials per variant:

- 21,420 legacy/x2 paired trials;
- 42,840 combat executions;
- zero mismatched paired trials;
- zero variants with a mismatch.

The comparison is strict. Winner, unresolved state, turns, errors, all non-damage telemetry, and normalized final states must match. Damage-domain telemetry and final Shield/Armor/Hull values must be exactly doubled.

This establishes that the CP121 research layer is a valid unit conversion for every combat consumer exercised by CP120. It does **not** yet prove that all production/internal-damage consumers can be converted safely; those are separately enumerated in `damage_domain_scaling_audit_v0_1.json`.

## Hull and critical-damage consequence

Hull is doubled in the x2 research scale. This is required for equivalence.

The current production internal-damage resolver advances one H/X position for each Hull point lost. If x2 became canonical while that literal loop remained unchanged, critical exposure would double. Therefore canonical adoption would require one legacy H/X advance for every **two** new-scale Hull damage points, with a deterministic remainder carried across packets. CP121 does not implement that production change because internal criticals are outside the current Python research consumer.

Likewise, today's successful 1-Hull Damage Control repair is equivalent to 2 new-scale Hull points. A future 1-point new-scale repair could exist, but it would be a deliberate half-strength repair rather than the old repair under new units.

## Half-step authoring study

The bounded authoring half-step population contains:

- 2,424 mirrored variants;
- 1,240 Missile;
- 832 Kinetic;
- 352 native-Energy references;
- 1,548 TL2–TL6 primary variants;
- 420 TL7 advanced variants;
- 456 TL8–TL9 endpoint/stress variants;
- 25 trials/variant = 60,600 engagements;
- zero trial errors and zero failed gates.

These trial counts are intentionally too small for final balance conclusions. They are sufficient to validate direction, output shape, and whether odd values occupy meaningful states.

### Deterministic resolution surface

The deterministic packet-resolution surface examined 75 even/odd/even triplets across TL3–TL7 and three SPEN/APEN combinations. In **75/75** cases, the odd damage value produced a layer-resolution state distinct from both neighboring even values, and in **75/75** cases that state lay component-wise between its neighbors.

This is strong structural evidence that x2 creates genuine new integer resolution rather than redundant labels.

### GP Missile indication

The authoring sample split the former D5→D6 cliff as follows:

| TL | Legacy-equivalent step | Low win | Half win | Full win | First half | Second half |
|---:|---|---:|---:|---:|---:|---:|
| 3 | 5 → 5.5 → 6 | 58.6% | 68.4% | 79.4% | +9.85 pp | +11.00 pp |
| 4 | 5 → 5.5 → 6 | 39.2% | 47.4% | 57.2% | +8.21 pp | +9.80 pp |

The small sample reproduces the desired behavior: D5.5 occupies a useful intermediate region instead of merely collapsing onto D5 or D6.

The D6→D7 and D7→D8 probes also produce meaningful midpoints in authoring evidence, generally reducing one legacy one-point jump into two smaller steps. Endpoint D8→D9 remains more nonlinear at TL9, which is appropriate to retain as endpoint/stress evidence rather than a whole-ladder design driver.

### Swarmer indication

The extra resolution helps but does not erase intentional packet thresholds. Early 2×D2→2×D3 remains steep: the D2.5 midpoint absorbs a large part of the gain in the bounded sample. Mid and mature packet ladders are smoother in several TLs, but threshold behavior remains visible.

That is a desirable finding. The goal of x2 is **not** to make every technology step linear. It gives the designer an intermediate value when a smaller step is needed while preserving the possibility of a major threshold jump.

### Kinetic indication

The +0/+0.5/+1 legacy-equivalent DAM probe usually places the odd point between the current and +1 outcomes. APEN and SPEN half-steps can still be large because flat layered protection creates true penetration thresholds. This reinforces the family-design interpretation from CP120: higher resolution gives more control, but penetration technology should still be treated as a meaningful breakpoint rather than tuned solely to smooth win rates.

### Defense indication

CP121 includes +0/+0.5/+1 legacy-equivalent probes for Shield Capacity, Shield recharge, Armor Integrity, Armor Protection, and Hull. The 25-trial authoring sample is too noisy for promotion-level inference—some weak axes show non-monotonic sampled win rates—but it validates all fixture paths and confirms odd point values are executable on the defensive side as well.

Armor Protection is expected to remain threshold-heavy because it is flat prevention. Hull/Shield-capacity half-steps are expected to be gentler. Native 2,000-trial evidence is required before drawing magnitude conclusions.

## Adoption audit findings

A canonical x2 conversion cannot be implemented by multiplying the numerical matrix alone. At minimum it must address:

- H/X critical cadence per Hull lost;
- Hull-repair magnitude;
- degraded Energy weapon half-rounded-up damage semantics;
- Natural-100 point-domain bonuses when their full damage consumer is active;
- flat Shield-Hardener and other optional point-domain component bonuses;
- any still-active historical C# calibration consumer containing literal point values.

Non-point domains such as accuracy, range, Tactical Power, Space, ammunition counts, fuel, movement, Sensor/EW ratings, and PDS percentages/capacity remain unscaled.

## Authoring assessment

The x2 concept has passed the most important structural test available before native execution: **exact full-population conversion equivalence**, with zero mismatches, and the odd-point deterministic surface is universally non-redundant in the tested layer states.

The bounded outcome sample is directionally favorable for the original motivation. In particular, the GP D5→D6 cliff acquires a useful D5.5-equivalent midpoint. Some Swarmer and penetration changes remain sharp, showing that x2 improves numerical resolution without removing meaningful technology thresholds.

The recommended disposition is therefore to proceed with CP121 native acceptance. Do not promote x2 yet. If native evidence confirms that odd values repeatedly provide useful intermediate choices—and does not reveal pathological defense half-steps—the next checkpoint can decide whether to adopt x2 canonically and then perform the required production/internal-damage migration as a separate, parity-gated change.
