# Checkpoint 30 Validation

Expected acceptance totals:

- 627 engine-independent tests.
- 7 legacy deterministic moving-missile scenarios.
- 12 Phase A documents / 54 cases.
- 7 Phase B documents / 36 cases under revised EvM.
- 29 kinetic calibration variants / 10,000 trials each / zero failed gates.
- 31 energy calibration variants / 10,000 trials each / zero failed gates.
- 48 complete no-counter weapon-matrix variants / 10,000 trials each / zero failed gates.
- 59 PDS/interception variants / 10,000 trials each / zero failed gates.
- 46 ScenarioRunner self-tests.

Repository-contract-only validation must verify all static release contracts, including every literal file marker, Concept marker, workbook sheet and marker, manifest/count contract, normalized active-document state, JSON cardinality and pair reciprocity, Phase B static semantics, and PDS study invariants.

The full Windows validator must perform a clean warnings-as-errors build and execute every accepted prior lane before the new PDS study. It must be idempotent when repository-contract-only validation is followed by full validation. No mechanical Godot validation is required.

Before archive generation, `static_preflight_checkpoint_30.py` must pass against the authoring tree and again against a clean extraction. It covers the six environment-independent gates agreed for release: literal text assertions, Concept markers, workbook sheet/marker contracts, manifest/test/study cardinalities, normalized active-document state, and clean extraction/hash/no-extra-file verification. Windows compilation and runtime/idempotence remain the user's authoritative gates.
