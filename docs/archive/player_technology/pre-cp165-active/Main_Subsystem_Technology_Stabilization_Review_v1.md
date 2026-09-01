# Main-Subsystem Technology Stabilization Review v1

**Checkpoint:** 127 candidate  
**Accepted implementation baseline:** CP122 Corrected Replacement 1  
**Accepted full-map evidence baseline:** CP126  
**Purpose:** establish a stable TL1-TL9 main-subsystem numerical baseline before broader TL sensitivity and mixed-/legacy-TL ecology

## Decision standard

CP127 is deliberately bounded. It does **not** seek equal adjacent-TL win rates and it does not smooth every uneven progression. A main-subsystem value changes only when one of two conditions is met:

1. the active game-facing rule/reference authority is inconsistent with the numerical table; or
2. accepted CP126 evidence plus focused one-axis attribution identifies a narrow characteristic that is undermining the intended family identity.

Most Auxiliary/support-component numerical progression remains outside this pass. AUX systems may appear in legal builds because the existing research envelope already contains PDS and Shield Hardener options, but CP127 does not use their behavior as a reason to redesign the AUX ladder.

## Authority reconciliation

### STL — restore the explicit tactical invariant

The Concept and historical CP39 rule both state that an Operational STL drive's standard Move equals its installed Drive TL. The post-CP109 provisional whole-ladder table unintentionally displaced that rule with 1/2/3/4/6/6/7/9/10.

CP127 restores the intended sequence:

**STL Move TL1-TL9: 1, 2, 3, 4, 5, 6, 7, 8, 9.**

Uneven propulsion technology may still express through Installation Space, overload behavior, fuel/reliability, specialist drives, or later capabilities. It does not silently replace the standard-Move rule.

### Missile propulsion — restore the explicit tactical invariant

The Concept and CP39 also state that Operational Missile Move equals Missile Drive TL plus 1. The provisional table had drifted to 2/3/4/5/5/7/8/8/9.

CP127 restores:

**Missile Move TL1-TL9: 2, 3, 4, 5, 6, 7, 8, 9, 10.**

Missile range/endurance, guidance/seeker quality, payload, packet behavior, and PDS interaction remain independent axes.

### FTL — retain the deliberate strategic exception

FTL is different. The Concept originally described a direct TL-to-hex progression **and explicitly said it could change as the wider ladder matured**. CP109 deliberately changed the strategic ladder. CP127 therefore reconciles the stale Concept table to the already intended strategic values rather than treating FTL as a tactical-rule defect:

**FTL strategic movement TL1-TL9: 1, 2, 3, 4, 4, 6, 7, 9, 12.**

This remains a strategic/campaign hypothesis; CP127's combat study does not calibrate FTL.

## CP126 evidence and focused numerical decision

### TL5→TL6 maturation pulse

On the accepted CP126 full map, the higher-TL ship won about **89.0%** of the population-weighted adjacent TL5→TL6 encounters and about **96.4%** of exact matched-composition encounters. The matched-composition result is especially important: the strong transition is not created by the 680 newly legal TL6 compositions.

Bounded CP127 development attribution, repeated in the native study design, shows a multi-source maturation pulse rather than a single accidental scalar. Sensor range/discrimination growth is a major cross-family contributor; Kinetic, Energy and Missile each also gain meaningful family-specific combat performance. Armor/Shield/Hull contributions are smaller, and several non-combat/latent changes cannot explain the result in the present consumer.

**Decision:** retain the TL6 package. A strong maturation/integration step is allowed. CP127 will report the one-axis ablations but will not force TL5→TL6 toward a preferred win percentage.

### TL8 Energy family identity

CP126 isolated the late Energy issue more narrowly. At TL8:

- Energy vs Shield: **49.1%** attacker conditional win rate;
- Kinetic vs Shield: **31.1%**;
- Energy without Shield: **86.4%**;
- Kinetic without Shield: **70.9%**.

Energy therefore retained roughly a **15.5 percentage-point advantage even without Shield interaction**. That is broader than the desired late Energy identity.

A bounded 2x2 development sensitivity over TL8 Energy raw damage and APEN showed that reducing only Low/Standard/High damage by one canonical point materially reduces the no-Shield advantage while preserving a stronger Shield-facing advantage. Reducing APEN as well was not necessary to establish the intended direction.

**CP127 candidate:** TL8 Energy Low/Standard/High damage **7/10/12** instead of 8/11/13. Keep TL8 Energy Accuracy 35, APEN 3, SPEN 5, Range 9, Space 5 and Tactical Power unchanged.

The native CP127 factorial reproduces this attribution using common task selection and corrected movement invariants.

## Main-subsystem disposition

| Main subsystem | CP127 disposition | Reason |
|---|---|---|
| Hull | Retain | CP126 progression coherent; no isolated defect. |
| Damage Control | Retain | New canonical repair-yield ladder is intentional; internal critical cadence remains deferred. |
| Armor | Retain | Family identity and x2-era progression remain coherent. |
| Reactor | Retain | First-pass CP110 ladder already calibrated; TL5→6 operational output does not jump. Revisit when late AUX/mission Space competition is numeric. |
| STL | **Correct** | Restore Move = Drive TL. |
| FTL | Retain / reconcile docs | Deliberate strategic 1/2/3/4/4/6/7/9/12 exception. |
| Tactical Computer | Retain | No concrete CP126 defect; some characteristics remain latent until relevant mechanics/states occur. |
| Sensors | Retain | TL6 Sensor maturation is a real contributor, not an accidental mismatch. |
| ECM / ECCM | Retain | No new CP126 evidence warrants changing the accepted information-control ladder. |
| Shields | Retain | Progression remains part of intended defensive identity; TL8 Energy correction addresses the narrower family issue. |
| Kinetic Main | Retain | Family-specific Armor-facing progression remains coherent. |
| Energy Main | **Adjust TL8 damage only** | Restore Shield-facing specialization without changing penetration/range/power identity. |
| Missile delivery | **Correct Move rule** | Restore Missile Move = Drive TL + 1. |
| Missile guidance | Retain | No isolated defect. |
| GP Missile warhead | Retain | Current D10→D11→D13→D15 yield ladder remains coherent. |
| Swarmer | Retain | CP126 supports a bounded TL7 mature legacy lifecycle; no forced TL8/TL9 upgrade. |

PDS and most other support/AUX families remain outside the numerical-stabilization obligation for CP127. Existing values are preserved for research continuity but do not become broadly calibrated AUX progression by implication.

## Freeze boundary after acceptance

If CP127 passes its native mechanics/instrumentation gates and the substantive review reveals no new concrete pathology, `technology_numerical_matrix_v0_4.json` becomes the provisional stabilized main-subsystem baseline for the next broad TL-sensitivity work.

After that, a stabilized main value should be reopened only because of new evidence: a demonstrated defect, a newly implemented mechanic, a mixed-/legacy-TL interaction, or a later AUX interaction that materially changes the causal interpretation. Routine preference for smoother progression is not enough.
