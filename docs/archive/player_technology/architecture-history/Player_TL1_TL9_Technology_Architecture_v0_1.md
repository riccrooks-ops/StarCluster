# Player TL1-TL9 Technology Architecture v0.1

## Purpose

Checkpoint 49 establishes a provisional global technology architecture before additional local tuning. The architecture is a design map, not an automatic production catalog and not a replacement for accepted simulation evidence.

## Governing hierarchy

Technology is organized as:

**Family -> Sub-family -> TL-specific implementation**

Family rules apply to every sub-family unless a later explicit decision creates a named exception. Sub-families remain similar enough to compare but distinct enough to create meaningful choices.

Names and flavor never create mechanics. Unknown target classes, bonuses, weapons, concealment effects, information effects, or interactions remain unresolved until explicitly approved.

## Technology eras

| TL | Era | Character |
|---:|---|---|
| 1-3 | Realistic science fiction | Familiar engineering, human damage control, conventional EW, PDS, batteries, capacitors, ablative materials, and peak conventional integration. |
| 4-6 | Future science fiction | Robotics, nanoengineering, advanced fields, tractor systems, powered defenses, and mature exotic engineering. |
| 7-9 | Science fantasy | Bounded adaptive, gravitic, entangled, self-healing, extreme-material, and spacetime technologies below alien and Precursor capability. |

## Standard and Auxiliary systems

Standard components are the best mature integrated systems normally available at their TL. AUX components are specialized, experimental, theorycrafting, R&D, or constrained additions. A same-TL AUX should normally produce a modest marginal advantage, not complete an omitted standard capability.

Not every characteristic improves at every TL. Progression follows each sub-family purpose through selected characteristics such as accuracy, efficiency, capacity, Tactical Power, ammunition, reliability, counterplay, integration, or a bounded capability milestone.

## Common PDS rule

Kinetic PDS, Energy PDS, and AMM share the PDS target family: missile flights, boarding craft, and any other close-range terminal threat explicitly approved by the rules. Standard PDS cannot attack enemy ships. The sub-families differ through approved characteristics such as accuracy, reaction capacity, Tactical Power, ammunition, reliability, and evasive compensation.

## Initial entry-floor changes

| Component or lineage | Prior floor | Proposed floor | Rationale |
|---|---:|---:|---|
| Combat Battery | 1 | 1 | Retain a modest finite emergency-power identity; initial estimate is +1 Tactical Power for three uses. |
| Shield Battery | 1 | 3 | TL1 standard shields should not require a strong emergency-restoration AUX. |
| Evasive Maneuver System | 2 | 1 | Conventional maneuver-control support is realistic TL1 technology; effects remain tradeoff-bound. |
| ECM Suite | 2 | 1 | Modest conventional ECM belongs in the first technology era. |
| ECCM Suite | 2 | 1 | ECM counterplay must exist in the same early environment. |
| Energy PDS | 2 | 2 | Retain as an early refinement with Tactical Power dependence. |
| AMM PDS | 1 | 3 | Preserve strong interceptor identity without shutting down TL1 missiles. |
| Auxiliary Reactor | 2 | 3 | Renewable Tactical Power is too consequential for the earliest tiers. |
| Shield Booster | 2 | 3 | Capacity manipulation follows the accepted TL2 shield package. |
| Shield Power Stabilizer | 2 | 3 | Recharge-efficiency manipulation is grouped with later shield support. |
| Shield Hardener | 3 | 4 | Flat protection is a future-SF capability with high weak-attack suppression risk. |
| Tractor Projector | 3 | 4 | Direct movement denial begins in the future-SF era. |
| Repair Drone Bay | 2 | 4 | TL1-TL3 repair remains human-crewed; robotic repair begins at TL4. |
| Fabrication Module | 2 | 3 | Broad resource conversion begins at peak conventional engineering. |

Every prior AUX concept is listed in `auxiliary_component_availability_matrix_v0_2.csv`; unchanged entries remain provisional rather than promoted.

## Repair progression

- **TL1-TL3:** human damage-control crews, better tools, procedures, access, and materials.
- **TL4-TL6:** robotic repair support and autonomous diagnostics augment human allocation.
- **TL7-TL9:** bounded nanotechnological, adaptive-material, biological, or comparable self-healing systems may appear after their mechanics are explicitly defined.

## Machine-readable artifacts

- `player_technology_architecture_v0_1.json`
- `player_technology_architecture_schema_v0_1.json`
- `player_technology_subfamily_matrix_v0_1.csv`
- `auxiliary_component_availability_matrix_v0_2.csv`
- `scenario_architecture_bridge_v0_1.json`

## Scenario integration boundary

All Checkpoint 48 scenario files and runtime profiles remain byte-identical. The bridge maps current profile IDs to architecture lineages, but table-driven scenario generation is deferred. After review, a later checkpoint may derive explicit candidate TL1 and TL2 profiles from the approved chart and rerun TL1v1, TL2v2, and TL1v2 matrices.

## Decision boundary

Checkpoint 49 promotes no new standard value, AUX family, entry floor, capacity milestone, or higher-TL mechanic automatically.
