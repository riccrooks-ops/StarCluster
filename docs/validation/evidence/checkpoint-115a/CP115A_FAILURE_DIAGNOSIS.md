# CP115a Failure Diagnosis

The first native CP115 `-RepositoryOnly` invocation passed repository hygiene, 64/64 Python self-tests, 25/25 C#/Python parity fixtures, the complete 4,064-variant one-trial smoke, and the repository/evidence contract. The normal invocation then exited nonzero during the 2,000-trial-per-variant substantive study.

The defect is in CP115's analysis gate, not in combat execution. `run_weapon_family_analysis()` contained a blocking gate named `adaptive-pair-switch-telemetry` that was evaluated only when `trials >= 50`. Both pre-handoff populations bypassed it: smoke used 1 trial/variant and checked-in authoring used 20 trials/variant.

The historical CP115 authoring CSV contains 384 adaptive-pair rows and zero rows with a natural payload switch. A targeted local TL7 Shield-overmatch probe likewise produced zero natural switches across 500 trials with no trial errors. This is consistent with the CP115 interpretation: contemporary GP warheads often penetrate sufficiently that observer-safe adaptive doctrine correctly remains on GP.

The doctrine's ability to switch is already deterministic and directly testable. The retained unit probe starts on GP with no hidden knowledge, then sets only the permitted observed Shield-absorption plus two-hit no-penetration evidence and verifies selection changes to the specialist while incrementing switch telemetry.

CP115a therefore removes natural switch occurrence from blocking gates and records it as information-only telemetry. It also adds a static pre-substantive guard that rejects any weapon-family blocking `failures.append(...)` gate conditioned on `trials`, and updates the PowerShell wrapper to surface actual failed gates/errors and the captured research-output tail.

No candidate profile, target fixture, variant, RNG behavior, damage mechanic, information rule, study workload, Concept rule, numerical matrix, Reactor candidate, or C#/Godot production source changes in CP115a.
