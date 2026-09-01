# Technology Foundation Completeness Audit v1

**Checkpoint:** 106  
**Status:** Architecture foundation / current-direction and bounded open items  
**Numerical TL-table change:** None

## Why this ledger exists

The technology storyboard cannot by itself prove that the game foundation is complete. Crew, Fuel, cargo, repair, shuttles, laboratories, mining, home facilities, hazards, and similar concepts may support technology without deserving their own visible research discipline. This ledger keeps those domains visible before the provisional TL1-TL9 tables are written.

Completeness does not mean simulation density. A domain can be deliberately abstracted or deferred and still be correctly represented in the foundation. A new universal meter is justified only when a recurring player decision cannot be expressed through Installation Space, Tactical Power, Strain, condition, ammunition, Fuel, cargo/resources, Crew/Marines, time, or track/report state.

## Domain ledger

| Domain | Foundation status | Player-facing state | Abstraction boundary | Open work |
|---|---|---|---|---|
| Installation Space, Mass, Volume, and Integration | established | total Installation Space; component Space Cost; legal/illegal construction result | No separate tonnage, volume, hardpoint, cabling, service-access, or maintenance-complexity ledgers. | later-TL Hull capacity curve; component-specific miniaturization floors; bounded Critical Exposure relationship |
| Power Generation, Storage, and Distribution | established | Available/Powered/Spent Tactical Power; component condition; Strain where explicitly used | No voltage, current, resistance, bus routing, or per-circuit damage simulation. | later reactor statistics; storage scaling; auxiliary source niches |
| Thermal Rejection, Radiation Safety, and Containment | abstracted | Space Cost; signature; explicit powered mode; Strain or condition when specified | No universal heat meter, coolant inventory, radiator hit-location track, reactor dose model, or radiation-shielding subassembly by default. | whether a bounded temporary thermal-suppression mode earns implementation; special weapon hardening only if crew/internal effects mature |
| Crew, Marines, Automation, and Officers | established | Crew; Marines; Minimum Operating Crew; four crew-effect bands | No per-component crew assignment, shift schedule, skill roster, morale meter, or individual-casualty modifier stream in the core rules. | officer implementation; additional sparse crew-band consequences; replacement and recovery pacing |
| Habitability, Life Support, Gravity, and Medical Care | partial | Crew Capacity; mission/event modifiers; medical support component when adopted | No food, water, oxygen, waste, radiation-dose, or daily-health bookkeeping unless a scenario makes a finite supply the explicit problem. | medical-bay effect; long-duration endurance consequence; whether suspended animation belongs in normal research |
| Fuel, Propellant, and Expedition Endurance | partial | Fuel; tactical fuel where already defined; range/endurance warnings | No separate propellant chemistry, tank-by-tank transfer, boiloff, reactor-fuel isotope, or per-engine fuel ledger in the foundation. | campaign Fuel scale; tactical-to-strategic Fuel bridge; processor yields and eligible sites; refueling at home/allies |
| Cargo, Resources, and Stores | partial | cargo capacity; resource quantities; storage at home | No mass-by-item manifest, container geometry, loading-order puzzle, or commodity-market simulation. | final cargo scale; resource consolidation; special storage for Exotic items |
| Ammunition, Ready Packages, and Magazines | established | Ready Package; magazine ammunition; reload/resupply state | No round-by-round handling crew, feed-path routing, individual turret magazine geometry, or propellant inventory separate from the ammunition package. | magazine review; campaign resupply costs; special ammunition families |
| Damage Control, Repair, Salvage, and Fabrication | established | component condition; Repair Kits/Supplies; Damage Control allocation; Salvage; repair time | No deck-by-deck repair parties, spare-part SKU inventory, weld/material process simulation, or free regeneration. | strategic repair costs; fabricator conversion rates; high-TL self-repair ceilings |
| Shuttles, Hangars, Boarding, and Planetary Mission Systems | partial | shuttle count/condition; mission package; Crew/Marine commitment; mission time and risk | No shuttle fuel ledger, individual small-craft loadout builder, deck plan, or fighter-squadron management in the current foundation. | active authority says one starting shuttle; an older two-shuttle discussion requires explicit human resolution; second-shuttle/hangar progression; small-craft damage model |
| Science, Laboratories, Research Data, and Analysis | partial | research discipline/TL; selected project; Research Data; discovery analysis state | No scientist roster, paper/publication system, laboratory minigame, or research-point source proliferation. | research pacing; laboratory benefit; data conversion and diminishing returns |
| Mining, Extraction, Processing, and Field Industry | partial | eligible site; yield; time/risk; cargo/resource result | No ore-body simulation, refinery flow sheet, factory production chain, or colony industry layer. | module footprints; site/yield rules; field versus home efficiency |
| Exploration, Probes, Beacons, Communications, and Navigation | partial | Unknown/Charted/Surveyed; sensor reports; probe/beacon state; communication reach/latency when relevant | No communications packet routing, orbital mechanics, probe-fleet command layer, or universal real-time FTL communications assumption. | FTL communications rule; probe recovery/autonomy; beacon persistence and enemy discovery |
| Home System, Shipyard, Storage, and Limited Infrastructure | established | home services; stored items/resources; limited infrastructure state; home threat/defense state | No colonies, populations, trade routes, tax economy, industrial build queue, or controllable combat fleet. | service time/cost; limited defense investment; deployable infrastructure limits |
| Information, Diplomacy, Enemy Awareness, and Strategic Signatures | established | knowledge/reports; relationship state; enemy awareness cues; emission/signature consequences | No social-combat spreadsheet, universal reputation points, or invisible awareness growth without telegraphing. | simple diplomacy actions; awareness thresholds; communication delay and interception |
| Alien, Adapted, Incompatible, and Precursor Technology | established | Item TL versus researched TL; compatibility state; adaptation cost/Strain; research/trade/install choice | No universal relative-TL prohibition, automatic reverse engineering, or assumption that Precursor gear is simply TL9+1. | repair/adaptation rates; alien interface families; campaign-specific Precursor constraints |
| Hazards, Atmosphere, Fire, Contamination, and Extreme Environments | partial | hazard warning; mission/ship consequence; condition or resource cost | No deck-by-deck atmosphere, fire propagation, contamination map, individual exposure dose, or coolant/pressure plumbing simulation. | small event vocabulary; boarding/planetary hazard resolution; specialist hardening scope |
| Time, Travel, Repair, Research, and Logistics Pressure | established | strategic turns; travel cost; repair/research/extraction time; enemy response cues | No freight network, route-optimization economy, procurement bureaucracy, or maintenance-calendar micromanagement. | campaign clocks; action durations; enemy awareness/response schedule |
| Cybersecurity, Control Integrity, and Autonomy | deferred | explicit compromised/control condition only if adopted; automation capability; countermeasure/counterplay | No universal hacking action, per-subsystem software versions, exploit inventory, or remote takeover without physical/information prerequisites. | whether cyber combat earns a core mechanic; access conditions; crew/AI relationship |
| Matter Transport, Portals, and Rule-Bending Mobility | deferred | none until a bounded artifact or campaign rule is adopted | No default teleportation of ships, people, cargo, attacks, or boarding parties. | artifact-only versus researchable; range/targeting/counterplay; interaction with PDS and mission systems |

## Explicit complexity exclusions

- universal heat meter and coolant loop management
- radiator hit locations or independent radiator damage track
- reactor radiation-dose and shielding thickness simulation
- separate per-component mass and volume ledgers
- food/water/oxygen/waste daily consumable bookkeeping
- per-component staffing and shift scheduling
- deck-by-deck atmosphere, fire, or contamination simulation
- tank-by-tank propellant chemistry and transfer
- spare-part SKU and industrial production-chain management
- colony, population, trade-route, or controllable-fleet management

These exclusions are architecture decisions, not claims that the underlying engineering is unreal. Installation Space and component traits already include the mass, volume, thermal, shielding, containment, structural, routing, and service burdens that matter to ship design.

## Decisions required before numerical table work

- Confirm the active one-starting-shuttle rule versus an older provisional two-shuttle discussion before fixing hangar progression.
- Set the campaign Fuel scale and its bridge to existing tactical Fuel.
- Decide whether the TL1 ablative layer's provisional 1-Space footprint is promoted when the equipment table is authored; starting legality and Auxiliary role are already established.
- Choose initial mechanics for Medical Bay, Fuel Processor, Laboratory, Mining Module, Fabrication Module, Cargo Expansion, Hangar/Mission Bay, and Magazine Expansion only after their campaign loops are specified.
- Keep cyber intrusion and matter transport deferred unless bounded access, counterplay, and cross-system consequences are designed.

## Gate to the next pass

The provisional TL1-TL9 table may begin only when every proposed component can point to an owning discipline, a foundation domain, a player-facing decision, an abstraction boundary, and a lifecycle status. Nothing in this audit promotes a component statistic.
