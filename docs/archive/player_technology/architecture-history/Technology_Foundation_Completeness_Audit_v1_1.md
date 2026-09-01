# Technology Foundation Completeness Audit v1.1

**Checkpoint:** 107  
**Status:** foundation_current_with_provisional_tl1_tl9_table

Confirm that the broader player-ship and campaign foundation remains complete enough to support the first provisional TL1-TL9 technology/component table, while recording CP107’s resolved shuttle, Fuel, Ablative Armor, and support-component rules without numerical calibration.

## Global rules

- Foundation completeness is broader than technology-tree completeness: a domain may be established, partial, abstracted, deferred, or explicitly outside scope without becoming a visible research discipline.
- Use existing state first: Installation Space, Tactical Power, Strain, condition, ammunition, Fuel, cargo/resources, Crew/Marines, time, and tracks/reports.
- Create a new universal meter only after a repeated player decision cannot be expressed cleanly through those states.
- Every visible discipline owns a usable vertical spine; cross-pollination expands options and integration but does not gate ordinary owning-discipline progression.
- Architecture status does not promote numerical component values.

## Resolved in Checkpoint 107

- The starting player cruiser has exactly one shuttle.
- The current tactical Fuel working scale remains 100 Fuel, 2 Fuel per ship hex actually traversed, and +1 Fuel for a turn using Evasive Maneuvering.
- TL1 Ablative Armor costs 1 universal Installation Space.
- Auxiliary/support is a role, not a separate capacity pool; an optional support component belongs only when it materially changes capability, risk, or efficiency in an existing gameplay loop.
- The provisional TL1-TL9 technology/component placement table exists; CP107 assigns no new TL4-TL9 balance values and promotes no hard cross-category prerequisites.

## Foundation domains

### Installation Space, Mass, Volume, and Integration

**Foundation status:** `established`  
**Implementation status:** `implemented_tl1_tl3_construction`

One universal cruiser-wide Installation Space budget limits installed systems. Space abstracts mass, volume, structural and service integration burden rather than literal rooms; Auxiliary is a role, not a separate capacity pool. TL1 Ablative Armor is an explicit 1-Space optional installation.

**Player-facing state**
- total Installation Space
- component Space Cost
- legal/illegal construction result

**Technology hooks**
- bounded Hull integration growth
- component-family miniaturization
- adapters and specialist support

**Abstraction boundary:** No separate tonnage, volume, hardpoint, cabling, service-access, or maintenance-complexity ledgers.

**Open items**
- later-TL Hull capacity curve
- component-specific miniaturization floors
- bounded Critical Exposure relationship
- exact Space footprints for newly proposed support modules

**Authorities:** Concept 2.2; Concept 7.4; Concept 9.4.1-9.4.3; C-005; C-006; C-033

### Power Generation, Storage, and Distribution

**Foundation status:** `established`  
**Implementation status:** `implemented_with_later_families_provisional`

Main reactors, auxiliary sources, storage, power quality, overload, and installed consumer demand share the existing Tactical Power architecture.

**Player-facing state**
- Available/Powered/Spent Tactical Power
- component condition
- Strain where explicitly used

**Technology hooks**
- reactor-family frontier
- storage
- conditioning
- auxiliary generation
- power-form interfaces

**Abstraction boundary:** No voltage, current, resistance, bus routing, or per-circuit damage simulation.

**Open items**
- later reactor statistics
- storage scaling
- auxiliary source niches

**Authorities:** Concept 8.4; Concept 10.12-10.14; Power storyboard

### Thermal Rejection, Radiation Safety, and Containment

**Foundation status:** `abstracted`  
**Implementation status:** `represented_through_existing_burdens`

Heat rejection, radiation shielding, containment, cryogenic support, and related engineering are real design inputs expressed through Space, Tactical Power, signature, Strain, reliability, condition, or explicit traits only when they create a recurring decision.

**Player-facing state**
- Space Cost
- signature
- explicit powered mode
- Strain or condition when specified

**Technology hooks**
- compact radiators
- thermal suppression
- energy recovery
- specialist radiation hardening

**Abstraction boundary:** No universal heat meter, coolant inventory, radiator hit-location track, reactor dose model, or radiation-shielding subassembly by default.

**Open items**
- whether a bounded temporary thermal-suppression mode earns implementation
- special weapon hardening only if crew/internal effects mature

**Authorities:** Concept 2.2; Concept 9.4.2; Power/Thermal storyboard; SD-Q15-001

### Crew, Marines, Automation, and Officers

**Foundation status:** `established`  
**Implementation status:** `crew_thresholds_established_officers_deferred`

Crew and Marines are separate persistent resources. Crew consequences use a few thresholds and explicit events; automation may change capacity or minimum crew without creating per-station staffing.

**Player-facing state**
- Crew
- Marines
- Minimum Operating Crew
- four crew-effect bands

**Technology hooks**
- automation
- damage-control robotics
- crew-capacity modules
- bounded officer benefits

**Abstraction boundary:** No per-component crew assignment, shift schedule, skill roster, morale meter, or individual-casualty modifier stream in the core rules.

**Open items**
- officer implementation
- additional sparse crew-band consequences
- replacement and recovery pacing

**Authorities:** Concept 7.4; Concept 11.1-11.2; C-057; C-058

### Habitability, Life Support, Gravity, and Medical Care

**Foundation status:** `partial`  
**Implementation status:** `narrative_and_support_hooks_only`

Habitability and life support remain part of Hull/Space and campaign endurance. A Medical Bay is a legitimate optional support component because it can mitigate explicit crew casualty/recovery outcomes from exploration and combat; it does not create individual-health bookkeeping.

**Player-facing state**
- Crew Capacity
- mission/event modifiers
- medical support component when adopted

**Technology hooks**
- medical bay
- gravity maturation
- closed-loop life support
- emergency shelter
- suspended animation candidate

**Abstraction boundary:** No food, water, oxygen, waste, radiation-dose, or daily-health bookkeeping unless a scenario makes a finite supply the explicit problem.

**Open items**
- medical-bay effect
- long-duration endurance consequence
- whether suspended animation belongs in normal research

**Authorities:** Concept 9.4; Concept 11; Hull/Habitation storyboard; SD-SG-001

### Fuel, Propellant, and Expedition Endurance

**Foundation status:** `partial`  
**Implementation status:** `tactical_working_scale_established_campaign_link_open`

Fuel is one broad resource for FTL travel and selected propulsion actions. The current tactical working scale is 100 Fuel on the baseline cruiser, 2 Fuel per ship hex actually traversed, and +1 Fuel for a turn using Evasive Maneuvering. Propellant/feedstock distinctions become traits or specialist components rather than parallel universal currencies.

**Player-facing state**
- Fuel (current tactical baseline 100)
- 2 Fuel per traversed tactical hex
- +1 Fuel per EvM turn
- future campaign range/endurance warnings

**Technology hooks**
- fuel processor
- reserve/endurance module
- drive efficiency
- specialist fuel requirements

**Abstraction boundary:** No separate propellant chemistry, tank-by-tank transfer, boiloff, reactor-fuel isotope, or per-engine fuel ledger in the foundation.

**Open items**
- campaign/strategic Fuel costs and resupply scale
- tactical-to-strategic Fuel bridge
- Fuel Processor yields and eligible Resource inputs
- later-TL efficiency/storage/endurance progression
- refueling at home/allies

**Authorities:** Concept 6.3; Concept 10.19; Concept 12.1-12.2; SD-Q06-003; SD-Q24-006

### Cargo, Resources, and Stores

**Foundation status:** `partial`  
**Implementation status:** `resource_set_and_capacity_provisional`

Cargo is finite and competes with installed capability when expanded. The smallest resource set that sustains repair, research, refit, travel, trade, and mission decisions is preferred.

**Player-facing state**
- cargo capacity
- resource quantities
- storage at home

**Technology hooks**
- expanded cargo bay
- specialized containment
- handling automation
- resource compression only if bounded

**Abstraction boundary:** No mass-by-item manifest, container geometry, loading-order puzzle, or commodity-market simulation.

**Open items**
- final cargo scale
- resource consolidation
- special storage for Exotic items

**Authorities:** Concept 7.4; Concept 9.4; Concept 12.1-12.3; C-061

### Ammunition, Ready Packages, and Magazines

**Foundation status:** `established`  
**Implementation status:** `implemented_with_campaign_resupply_open`

Ammunition-fed weapons use a Ready Package plus bounded shared or internal magazines. Magazine components compete for Installation Space; Energy PDS has no conventional ammunition.

**Player-facing state**
- Ready Package
- magazine ammunition
- reload/resupply state

**Technology hooks**
- magazine expansion
- compact ammunition
- smart munitions
- fabrication/resupply

**Abstraction boundary:** No round-by-round handling crew, feed-path routing, individual turret magazine geometry, or propellant inventory separate from the ammunition package.

**Open items**
- magazine review
- campaign resupply costs
- special ammunition families

**Authorities:** Concept 10.17; C-028; PDS TL1/TL2 contract

### Damage Control, Repair, Salvage, and Fabrication

**Foundation status:** `established`  
**Implementation status:** `combat_repair_established_strategic_repair_partial`

Combat stabilization, field repair, post-combat restoration, salvage, and fabrication are distinct uses of the existing condition, Repair Supplies, resource, time, and support-component model.

**Player-facing state**
- component condition
- Repair Kits/Supplies
- Damage Control allocation
- Salvage
- repair time

**Technology hooks**
- repair drones
- fabrication module
- self-sealing structure
- bounded self-repair

**Abstraction boundary:** No deck-by-deck repair parties, spare-part SKU inventory, weld/material process simulation, or free regeneration.

**Open items**
- strategic repair costs
- fabricator conversion rates
- high-TL self-repair ceilings

**Authorities:** Concept 10.15-10.16; Hull/Damage Control storyboard; SD-DC-001; SD-Q06-003

### Shuttles, Hangars, Boarding, and Planetary Mission Systems

**Foundation status:** `partial`  
**Implementation status:** `one_starting_shuttle_established_later_capacity_open`

The baseline player cruiser carries exactly one shuttle. Later Hull TL may increase ordinary small-craft capacity. A Space-consuming Hangar/Mission Bay may provide additional capacity or support heavier craft, but CP107 does not commit its exact unlock TL or number of extra shuttles.

**Player-facing state**
- one starting shuttle
- shuttle availability/condition
- mission assignment/result
- future Hull/hangar capacity when defined

**Technology hooks**
- advanced shuttle bay
- mission module
- boarding pod
- small-craft protection
- recovery aids

**Abstraction boundary:** No shuttle fuel ledger, individual small-craft loadout builder, deck plan, or fighter-squadron management in the current foundation.

**Open items**
- Hull-TL shuttle-capacity milestones
- Hangar/Mission Bay Space cost and capacity effect
- small-craft damage/replacement detail
- boarding/planetary mission package effects

**Authorities:** Concept 7.4; Concept 10.20; Concept 11.3; C-059

### Science, Laboratories, Research Data, and Analysis

**Foundation status:** `partial`  
**Implementation status:** `research_architecture_exists_campaign_inputs_partial`

Research combines time, selected projects, data, discoveries, and facilities. Laboratories are optional installed support, not a separate research tree.

**Player-facing state**
- research discipline/TL
- selected project
- Research Data
- discovery analysis state

**Technology hooks**
- scientific laboratory
- specialist analysis suite
- probe/survey data
- alien adaptation

**Abstraction boundary:** No scientist roster, paper/publication system, laboratory minigame, or research-point source proliferation.

**Open items**
- research pacing
- laboratory benefit
- data conversion and diminishing returns

**Authorities:** Concept 8; Concept 9.2; Concept 12.3; C-003; C-062

### Mining, Extraction, Processing, and Field Industry

**Foundation status:** `partial`  
**Implementation status:** `campaign_hooks_only`

Mining/extraction and field processing are legitimate mission systems when they change eligible sites, Resource yield, time, risk, or conversion options. Fuel Processor and Fabricator concepts explicitly connect Resources to Fuel, repair, ammunition, and mission support without creating an industrial simulator.

**Player-facing state**
- eligible site
- yield
- time/risk
- cargo/resource result

**Technology hooks**
- mining module
- fuel processor
- fabrication module
- automated extractor

**Abstraction boundary:** No ore-body simulation, refinery flow sheet, factory production chain, or colony industry layer.

**Open items**
- module footprints
- site/yield rules
- field versus home efficiency

**Authorities:** Concept 9.4; Concept 12.2; C-061

### Exploration, Probes, Beacons, Communications, and Navigation

**Foundation status:** `partial`  
**Implementation status:** `map_knowledge_and_sensor_foundation_established_campaign_tools_partial`

Exploration tools extend observation, navigation, communication, and persistent map knowledge. Probes/beacons are small campaign assets, not a player fleet.

**Player-facing state**
- Unknown/Charted/Surveyed
- sensor reports
- probe/beacon state
- communication reach/latency when relevant

**Technology hooks**
- survey probe
- autonomous probe
- communications relay
- FTL communication
- navigation beacon

**Abstraction boundary:** No communications packet routing, orbital mechanics, probe-fleet command layer, or universal real-time FTL communications assumption.

**Open items**
- FTL communications rule
- probe recovery/autonomy
- beacon persistence and enemy discovery

**Authorities:** Concept 6; Concept 9.4; Sensors/Computing storyboard; SD-Q09-001; SD-Q24-011

### Home System, Shipyard, Storage, and Limited Infrastructure

**Foundation status:** `established`  
**Implementation status:** `campaign_role_established_details_partial`

Home is the safest repair/research/refit/storage anchor. Limited beacons, extractors, stations, or defenses may exist as bounded campaign assets without becoming empire management.

**Player-facing state**
- home services
- stored items/resources
- limited infrastructure state
- home threat/defense state

**Technology hooks**
- shipyard capabilities
- research facilities
- automated extractor
- sensor beacon
- defense installation

**Abstraction boundary:** No colonies, populations, trade routes, tax economy, industrial build queue, or controllable combat fleet.

**Open items**
- service time/cost
- limited defense investment
- deployable infrastructure limits

**Authorities:** Concept 2.1; Concept 12.3; Concept 14.4; C-001; C-060

### Information, Diplomacy, Enemy Awareness, and Strategic Signatures

**Foundation status:** `established`  
**Implementation status:** `conceptual_campaign_foundation`

Information quality, communication actions, diplomacy, emissions, and enemy awareness shape encounters and campaign pressure without a generic influence currency.

**Player-facing state**
- knowledge/reports
- relationship state
- enemy awareness cues
- emission/signature consequences

**Technology hooks**
- communications suite
- signature control
- encryption
- counterintelligence
- translation/analysis

**Abstraction boundary:** No social-combat spreadsheet, universal reputation points, or invisible awareness growth without telegraphing.

**Open items**
- simple diplomacy actions
- awareness thresholds
- communication delay and interception

**Authorities:** Concept 13; Concept 14.3; Concept 16.3; SD-Q09-001

### Alien, Adapted, Incompatible, and Precursor Technology

**Foundation status:** `established`  
**Implementation status:** `architecture_established_mechanics_partial`

Recovered equipment uses explicit owning TL, capability requirements, and Integrated/Adapted/Incompatible states. Precursor/TL10 shorthand remains outside normal player research.

**Player-facing state**
- Item TL versus researched TL
- compatibility state
- adaptation cost/Strain
- research/trade/install choice

**Technology hooks**
- adapters
- analysis lab
- matched components
- bounded reverse engineering

**Abstraction boundary:** No universal relative-TL prohibition, automatic reverse engineering, or assumption that Precursor gear is simply TL9+1.

**Open items**
- repair/adaptation rates
- alien interface families
- campaign-specific Precursor constraints

**Authorities:** Concept 9.1-9.5; C-019; C-042; C-064

### Hazards, Atmosphere, Fire, Contamination, and Extreme Environments

**Foundation status:** `partial`  
**Implementation status:** `event_and_trait_hooks_only`

Hazards matter through explicit events, component traits, mission risk, conditions, Crew effects, and repair consequences when they create gameplay.

**Player-facing state**
- hazard warning
- mission/ship consequence
- condition or resource cost

**Technology hooks**
- hazard hardening
- sealed compartments
- decontamination
- specialist sensors

**Abstraction boundary:** No deck-by-deck atmosphere, fire propagation, contamination map, individual exposure dose, or coolant/pressure plumbing simulation.

**Open items**
- small event vocabulary
- boarding/planetary hazard resolution
- specialist hardening scope

**Authorities:** Concept 2.2; Concept 10.18; Concept 11; SD-DC-005; SD-SW-016

### Time, Travel, Repair, Research, and Logistics Pressure

**Foundation status:** `established`  
**Implementation status:** `campaign_principle_established_values_open`

Strategic turns make travel, repair, research, extraction, missions, and refits compete under enemy pressure. Logistics are expressed through time, Fuel, cargo/resources, damage, and access to facilities.

**Player-facing state**
- strategic turns
- travel cost
- repair/research/extraction time
- enemy response cues

**Technology hooks**
- FTL efficiency
- repair automation
- processing speed
- communications
- endurance

**Abstraction boundary:** No freight network, route-optimization economy, procurement bureaucracy, or maintenance-calendar micromanagement.

**Open items**
- campaign clocks
- action durations
- enemy awareness/response schedule

**Authorities:** Concept 4; Concept 6.3; Concept 12; Concept 14.2

### Cybersecurity, Control Integrity, and Autonomy

**Foundation status:** `deferred`  
**Implementation status:** `guardrails_only`

Automation and software failures may matter, but hostile intrusion requires an explicit access path, bounded effect, counterplay, and observer-safe information. It must not become arbitrary remote ship control.

**Player-facing state**
- explicit compromised/control condition only if adopted
- automation capability
- countermeasure/counterplay

**Technology hooks**
- hardened control architecture
- intrusion specialist module
- autonomous repair/probes
- AI assistance

**Abstraction boundary:** No universal hacking action, per-subsystem software versions, exploit inventory, or remote takeover without physical/information prerequisites.

**Open items**
- whether cyber combat earns a core mechanic
- access conditions
- crew/AI relationship

**Authorities:** Concept 8; Computing/Autonomy storyboard; SD-DC-003; SD-SW-035

### Matter Transport, Portals, and Rule-Bending Mobility

**Foundation status:** `deferred`  
**Implementation status:** `boundary_only`

Teleportation, portals, micro-transitions, and equivalent effects are separate from ordinary FTL and require explicit limits because they can bypass boarding, cargo, PDS, map, and rescue gameplay.

**Player-facing state**
- none until a bounded artifact or campaign rule is adopted

**Technology hooks**
- Precursor artifact
- late weird-science branch
- campaign installation

**Abstraction boundary:** No default teleportation of ships, people, cargo, attacks, or boarding parties.

**Open items**
- artifact-only versus researchable
- range/targeting/counterplay
- interaction with PDS and mission systems

**Authorities:** Concept 9.3; Concept 17; SD-Q23-010

## Explicitly excluded complexity

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

## Remaining decisions before numerical TL4+ packages

- Define campaign/strategic Fuel costs, refueling and the bridge to the retained 100/2/+1 tactical working scale.
- Define exact Space/effects for new support components only when their gameplay loops are implemented; do not invent filler values in the architecture table.
- Choose later Hull-TL shuttle-capacity milestones and decide whether/how a Hangar/Mission Bay adds craft capacity.
- Retain cyber/control integrity and matter transport as deferred until their access, counters, and rule-bypass consequences are bounded.
- Promote hard external research prerequisites only in a later component-level decision when enabling science is truly mandatory; CP107 promotes none.
