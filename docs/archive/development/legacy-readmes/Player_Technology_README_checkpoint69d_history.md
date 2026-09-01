# Player Technology Design - Checkpoint 69d

## Current design authority

- `../../Star_Cluster_Game_Concept_v0.6h.docx`
- `TL1_Sensor_EW_Foundation_And_Range_Sweep_v0_1.md`
- `TL1_Sensor_EW_Candidate_Operational_Combat_Study_v0_1.md`
- `tl1_35_space_player_cruiser_baseline_v0_9.json` (accepted construction/combat control)
- `tl1_core_combat_numerical_baseline_v0_3.csv` (accepted numerical control)
- `TL1_35_Space_Construction_Envelope_v0_1.md`
- `TL1_Bilateral_Overload_EW_Counterplay_Study_v0_1.md`
- `tl1_integrated_tactical_combat_schema_v0_14.json`
- `../testing/checkpoint_69_validation_suite_policy_v0_1.json`

Checkpoint 69d is a release-gate telemetry-semantics hotfix; the substantive Checkpoint 69 design still does **not** promote new TL1 sensor ranges into the numerical baseline. It keeps Balanced-0 in the deterministic candidate set and compares Balanced-0, Balanced-1, and Balanced-2 in the matched integrated-combat matrix. The hotfix adds no gameplay rebalance and preserves CP69c's executable preflight/smoke hardening.

The primary candidate set is:

- Balanced-0: Passive 1/3, Active 3/4, Overload 4/5;
- Balanced-1: Passive 1/2, Active 3/4, Overload 4/5;
- Balanced-2: Passive 1/2, Active 3/4, Overload 5/6.

Balanced-0 versus Balanced-1 isolates passive Approximate awareness. Balanced-1 versus Balanced-2 isolates overload reach. All three retain one normal 1-TP Active mode plus one +1-TP overload commitment.

The Sensor/EW architecture continues to separate physical reach, emission-assisted detection, and EW discrimination. Active Sensor emissions may establish Approximate contact within the emitter's current detection envelope. Active ECM is conspicuous with LOS and can establish an Approximate emission contact across the tactical map while degrading Firm discrimination. ECCM counters that discrimination pressure but does not extend the sensor's physical reach.

At same hex, LOS cannot be occluded, but emissions and ECM/ECCM discrimination still resolve normally. Co-location is therefore not an automatic ECM immunity or automatic Firm solution.

Physical weapon range remains separate from target eligibility, preserving independent tall-versus-wide technology progression. Historical calibration artifacts remain evidence and are retained where active/deep checkpoint definitions consume them.
