# Checkpoint 165 — Current Design Authority Reconciliation, Documentation Consolidation, and Repository Cleanup

CP165 is a **zero-substantive-combat** documentation/authority checkpoint based on native-accepted CP164. It updates the active Concept, current TL Tree (Markdown/XLSX), current machine baseline, Space/AUX catalogs, Combat System Reference, AI/testing/development guidance, and repository authority discovery. Superseded active-looking TL/candidate/testing documents are relocated into archive/reference locations while historical evidence remains reproducible through an archive-aware compatibility resolver.

Current working design now explicitly records DEF/RES, post-CP153 weapons, post-CP155 PDS, CP158-160 AUX, CP164 Main Reactor/APU closure, current direct-fire modifiers, Damage Control/Repair Drone, ammunition/endurance, and the whole-system integration boundary. Production Core/Game mechanics/config remain byte-frozen from CP164.

The external accepted CP164 native-results archive remains outside the repository and is hash-recorded in CP165 provenance (`ce633281099a4ef4e939e906b3905aa00bc1c58ad76a49ee4294c1ee691669a1`).

After native acceptance, the next substantive phase is whole-system integration/testing, not another isolated power sweep.

## Authoring validation

- 792/792 Python tests passed across 56 modules.
- 32/32 CP165-focused tests passed.
- 42/42 authority-consistency checks passed.
- Concept rendered successfully to 5 pages.
- Current TL workbook: 9 sheets, zero formulas/errors.
- Production Core/Game runtime freeze manifest remains clean.
- Native .NET/xUnit/ScenarioRunner acceptance remains required on Windows.
