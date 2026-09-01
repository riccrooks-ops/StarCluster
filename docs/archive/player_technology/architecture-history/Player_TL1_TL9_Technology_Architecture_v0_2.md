# Player TL1-TL9 Technology Architecture v0.2

## Purpose

Checkpoint 50 reviews the Checkpoint 49 architecture through the player cruiser's installation limits before any new combat values are derived. The architecture remains provisional until human acceptance; retained simulation evidence is unchanged.

## Governing hierarchy

**Family -> Sub-family -> TL-specific implementation** remains the technology hierarchy. Names and flavor create no mechanics. Standard components are the best mature integrated systems normally available at their TL; AUX systems remain specialized additions with explicit capacity, power, ammunition, reliability, and compatibility costs.

## Cruiser installation-capacity candidate

| TL | Weapon Bays | AUX Capacity | Hull progression signal |
|---:|---:|---:|---|
| 1 | 1 | 1 | Starting cruiser; one primary battery and one meaningful AUX specialization. |
| 2 | 1 | 1 | Better structure and component choice without free installation growth. |
| 3 | 2 | 2 | First major modular-refit milestone; two primary batteries or one 2-bay weapon, plus two AUX capacity. |
| 4 | 2 | 2 | New future-SF options arrive, but capacity remains constrained. |
| 5 | 2 | 3 | Integrated pathways permit the first 2+1 AUX combination. |
| 6 | 3 | 3 | Third Weapon Bay milestone; support capacity holds steady. |
| 7 | 3 | 3 | Late-game structural sophistication without automatic capacity inflation. |
| 8 | 3 | 4 | Fourth AUX capacity supports two large specialist modules. |
| 9 | 4 | 4 | Final Weapon Bay milestone; cruiser remains cruiser-scale. |

The earlier TL2 AUX=2 value was a Checkpoint 48 screening allowance so capacity-2 concepts could be tested. It is retained as historical evidence but is not the normal TL2 production-hull candidate.

## Representative-ship review

`cruiser_installation_capacity_review_v0_1.json` and `representative_cruiser_capacity_profiles_v0_1.csv` provide eighteen legal capacity fixtures and three multi-bay occupancy stress cases. They are not production loadouts and do not promote weapon, AUX, damage, or power values.

The fixtures intentionally demonstrate the desired progression:

- TL1-TL2 force one-AUX specialization rather than early stacking.
- TL3 permits either two small AUX systems or one capacity-2 system.
- TL4 adds higher-impact options without increasing capacity.
- TL5 permits one capacity-2 plus one capacity-1 system.
- TL8 permits two capacity-2 systems.
- Weapon Bays grow only at TL3, TL6, and TL9 after the starting TL1 allowance.

## Hull-family refinement

The standard Hull mechanical promises now name the reviewed capacity candidates at TL1, TL2, TL3, TL5, TL6, TL8, and TL9. The exact second-shuttle-berth TL and the separate TL9 structural capstone remain unresolved.

## Scenario integration boundary

All Checkpoint 49 runtime scenario files remain unchanged. `scenario_architecture_bridge_v0_2.json` records both historical profile lineage and whether a retained Checkpoint 48 AUX estimate is architecture-legal at its original profile TL. Table-driven scenario generation remains deferred.

## Decision boundary

Checkpoint 50 is design-first. Successful execution validates repository consistency, representative capacity legality, and preservation of the retained quantitative baseline. It promotes no new combat statistic, higher-TL mechanic, or production loadout automatically.
