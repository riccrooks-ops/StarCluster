# Star Cluster - Checkpoint 110 Power / Reactor Calibration Report v1

**Status:** First-pass calibration evidence. CP109 Reactor candidates retained unchanged; no production promotion.  
**Source matrix:** `technology_numerical_matrix_v0_1.json` (Checkpoint 109).  
**Study definition:** `docs/design/testing/power_reactor_calibration_study_v0_1.json`.  
**Production boundary:** C# / Godot remains authoritative for shipped gameplay. Python is used for research, simulation, testing, and checkpoint validation.

## 1. Purpose

Checkpoint 110 is the first calibration checkpoint built on the complete CP109 TL1-TL9 candidate matrix. It tests the **Primary Main Reactor Generation** ladder in context rather than smoothing the Reactor values in isolation. The study asks whether the Storyboard-driven frontier/maturation rhythm creates useful ship-design and Tactical Power consequences across the complete candidate technology environment.

This checkpoint does **not** calibrate Energy Storage, auxiliary generation, or every future AUX/mission consumer. It also does not use a target win rate or require one Reactor to power every installed system simultaneously. Full simultaneous demand is a stress diagnostic. The stronger warning signs are routine activity becoming broadly impossible, a new frontier family being numerically pointless, all legacy niches disappearing immediately, or high-TL power becoming so abundant that allocation choices disappear.

## 2. Study scale and method

The study combines exhaustive deterministic enumeration with large deterministic Monte Carlo sampling:

- **18,006 legal standard one-Reactor cruiser builds** exhaustively enumerated across TL1-TL9.
- **72 representative legal loadouts** selected across lean, median, maximum-demand, PDS-heavy, dual-Energy, EW/shield, mixed-weapon, missile-fortress, and population-cell coverage roles.
- **288 stochastic variants**: 9 TLs x 8 representative loadouts x 4 doctrines.
- **7,025,000 adaptive turn-demand Monte Carlo samples** using the repository-owned deterministic RNG.
- Sampling stops only after the configured minimum and when the candidate shortfall-rate Wilson 95% half-width reaches **0.004**, or at the 60,000-sample cap.
- Four doctrines: offense, EW-contested, defense, and mixed.
- Safe Reactor overload is evaluated over a **20-turn encounter model**. The bounded two-use Strain process is solved in closed form from each adaptive turn-demand estimate rather than wasting millions of additional RNG calls; the reporting population is equivalent to **14,400,000 encounter turns**.
- Legacy Reactor alternatives, same-family multi-Reactor installations, branch-heavy maximum legal demand, damaged-state output, Space efficiency, and +/-2 TP operational sensitivity are evaluated separately.

All values remain research candidates. The study has no automatic promotion path.

## 3. Primary result

**Recommendation: retain all CP109 primary Reactor values unchanged as first-pass calibrated working candidates.**

The full ladder exhibits the intended Storyboard rhythm without requiring a smooth per-TL scalar increase:

| TL | Candidate | Space | Operational | Degraded | Emergency | Mean stochastic shortfall | Full-envelope support | Branch-heavy max demand |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Peak Fission | 6 | 5 | 3 | 1 | 15.58% | 20.75% | 11 |
| 2 | Early Practical Fusion | 6 | 7 | 3 | 0 | 4.64% | 43.20% | 13 |
| 3 | Mature Compact Fusion | 5 | 7 | 4 | 1 | 7.49% | 32.02% | 14 |
| 4 | High-Output Fusion | 5 | 9 | 5 | 1 | 3.87% | 52.31% | 15 |
| 5 | Early Antimatter | 5 | 12 | 4 | 0 | 3.23% | 55.53% | 19 |
| 6 | Mature Antimatter | 4 | 12 | 7 | 1 | 9.61% | 36.48% | 23 |
| 7 | High-Output Antimatter | 4 | 15 | 8 | 1 | 2.72% | 66.12% | 26 |
| 8 | Fractional / Direct Matter Conversion | 4 | 17 | 6 | 0 | 4.23% | 59.03% | 32 |
| 9 | Total Matter Conversion | 3 | 20 | 12 | 2 | 0.69% | 78.97% | 34 |

The rise in stochastic shortfall at TL3 and TL6 despite unchanged headline Reactor output is not a contradiction. Those maturation TLs improve Reactor footprint and damaged-state behavior while other ship systems continue to advance, so Tactical Power allocation becomes tighter again until the mature family receives its next output-frontier step.

## 4. Frontier and maturation behavior

Every primary Reactor candidate is on the numerical Pareto frontier at the TL where it is introduced when comparing Space, Operational TP, Degraded TP, and Emergency TP.

The most important frontier coexistence results are:

- **TL2:** Peak Fission and Early Practical Fusion both remain Pareto-relevant. Fusion raises peak output; Fission retains emergency resilience.
- **TL5:** High-Output Fusion, Early Antimatter, and the TL5 Fission revival all survive on the frontier. The new Antimatter family does not numerically erase its predecessors.
- **TL8:** High-Output Antimatter, Pinnacle Fission, and early Matter Conversion all remain frontier options.
- **TL9:** Total Matter Conversion dominates the single-Reactor numerical frontier. That is acceptable for the normal player-ladder pinnacle; older technologies can still compete through multi-Reactor configurations, campaign traits, reliability, mission economics, or other future systems rather than requiring artificial single-unit superiority.

This supports the Storyboard principle that a new physical principle may expand the frontier while mature older families remain useful for resilience, footprint, integration, or specialist roles.

## 5. Damaged-state identity

The candidate ladder produces a deliberate repeating rhythm:

- **TL2 Early Fusion:** 7 / 3 / 0 - frontier output with immature damaged-state behavior.
- **TL3 Mature Fusion:** 7 / 4 / 1 at one less Space - maturation rather than another peak-output jump.
- **TL5 Early Antimatter:** 12 / 4 / 0 - another frontier leap with severe containment fragility.
- **TL6 Mature Antimatter:** 12 / 7 / 1 at one less Space - major resilience and integration improvement.
- **TL8 Early Matter Conversion:** 17 / 6 / 0 - new frontier principle with poor damaged-state resilience.
- **TL9 Total Matter Conversion:** 20 / 12 / 2 at one less Space - mature pinnacle capability.

Conditional on already being Degraded, mean representative shortfall is roughly 55.6% at TL2, 63.4% at TL5, and 61.2% at TL8. The corresponding maturation steps reduce this to about 38.1% at TL3, 35.5% at TL6, and 12.5% at TL9. This is strong evidence that damaged-state values are creating family identity rather than merely scaling with Operational TP.

This study does **not** determine how frequently Reactors become Degraded in combat. That remains a damage/integration question.

## 6. Operational sensitivity

The candidate outputs are not sitting on a universal target band, but the +/-1 TP sensitivity confirms that one point remains meaningful through most of the ladder:

| TL | Candidate TP | Shortfall at -1 | Candidate | Shortfall at +1 |
|---:|---:|---:|---:|---:|
| 1 | 5 | 30.70% | 15.58% | 6.43% |
| 2 | 7 | 12.36% | 4.64% | 2.55% |
| 3 | 7 | 13.64% | 7.49% | 4.33% |
| 4 | 9 | 6.36% | 3.87% | 2.29% |
| 5 | 12 | 5.60% | 3.23% | 1.74% |
| 6 | 12 | 12.64% | 9.61% | 6.98% |
| 7 | 15 | 4.27% | 2.72% | 1.52% |
| 8 | 17 | 5.75% | 4.23% | 2.95% |
| 9 | 20 | 1.24% | 0.69% | 0.37% |

TL9 is intentionally generous for normal representative loads, but it does not eliminate peak design pressure: the maximum legal branch-heavy stress configuration reaches **34 TP**, 14 TP above one TL9 Reactor.

## 7. Safe Reactor overload

The existing candidate safe overload rule (+1 TP, limited by Reactor Strain) provides bounded relief rather than replacing Reactor sizing. Mean representative raw shortfall versus safe-overload-assisted shortfall is:

- TL1: 15.58% -> 10.36%
- TL2: 4.64% -> 3.09%
- TL3: 7.49% -> 5.03%
- TL4: 3.87% -> 2.48%
- TL5: 3.23% -> 1.90%
- TL6: 9.61% -> 7.38%
- TL7: 2.72% -> 1.62%
- TL8: 4.23% -> 3.06%
- TL9: 0.69% -> 0.37%

Mean expected safe overload use remains below about 1.05 activations per 20-turn encounter in every TL aggregate. This supports keeping overload as a tactical relief valve rather than increasing sustained generation.

## 8. Multiple-Reactor design implications

The proportion of the same legal non-Reactor package that can accept a **second current-TL Reactor** rises sharply with technological miniaturization and Hull capacity:

| TL | Same package can fit second current Reactor |
|---:|---:|
| 1 | 3.1% |
| 2 | 3.1% |
| 3 | 12.3% |
| 4 | 14.6% |
| 5 | 17.1% |
| 6 | 46.6% |
| 7 | 71.4% |
| 8 | 96.9% |
| 9 | 100.0% |

Whenever the second current Reactor fits in this standard-component enumeration, its doubled output is enough to satisfy the enumerated full simultaneous demand. That is **not** a reason to nerf Reactor output in CP110. It is a cross-system integration flag.

The current high-TL candidate matrix deliberately creates more discretionary Space through Hull growth and component miniaturization, while many intended AUX/mission systems still lack numerical Space/Power values. Retuning Reactors now to compensate for absent mission equipment would bake an incomplete ship-design environment into the power ladder. The correct response is to rerun this integration test after those systems receive numerical candidates.

Older Reactors also remain usable through stacking. Examples include two TL4 Fusion reactors at TL5, two mature Antimatter reactors at TL7/8, or two TL8 matter-conversion reactors at TL9. They buy high sustained output at a substantial Space opportunity cost. This is consistent with the intended rule that players may compensate for older generation technology by installing more of it when the hull budget permits.

## 9. What is deliberately not calibrated here

- Energy Storage branches (supercapacitors, SMES, ultracapacitors).
- Auxiliary generation.
- Campaign fuel-production or reactor-resource economics.
- Damage frequency and Reactor critical-hit exposure.
- Heat/coolant/radiator bookkeeping, which remains deliberately abstracted under the KISS architecture.
- Final high-TL AUX/mission component competition for Space and Tactical Power.
- Ship-vs-ship balance or target win rates.

Energy Storage should follow sustained-generation calibration rather than be mixed into it. Storage changes **when** power can be spent, not how much sustained power a Reactor produces, and deserves its own temporal-allocation study.

## 10. CP110 recommendation

1. Retain all nine CP109 primary Reactor numerical candidates unchanged.
2. Retain the TL5 and TL7 Fission revival Reactor candidates as specialist/legacy alternatives; they demonstrate viable resilience niches in the current numerical frontier.
3. Do not promote any CP110 value into the C#/Godot runtime yet.
4. Record the primary Reactor ladder as **first-pass calibrated working candidates**, still subject to later cross-system revalidation.
5. Treat high-TL multi-Reactor availability as an integration watch item until AUX/mission systems and other high-TL Space consumers are numerically represented.
6. Re-run CP110 when a declared Power-demand dependency materially changes rather than after unrelated checkpoints.
7. Calibrate Energy Storage separately after the sustained-generation baseline is stable enough to serve as its reference.

The first-pass evidence therefore supports the **shape** of the CP109 Reactor ladder and does not justify numerical smoothing. The Storyboard-driven uneven jumps are functioning as intended in the current whole-ladder candidate environment.
