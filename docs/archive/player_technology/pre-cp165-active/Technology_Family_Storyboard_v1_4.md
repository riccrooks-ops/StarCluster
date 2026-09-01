# Technology Family Storyboard v1.4

**Checkpoint:** 117  
**Status:** Weapon-family simplification architecture; no balance calibration

CP117 preserves the 10-discipline / 32-lineage foundation while simplifying combat-facing weapon expression. Energy retains power/output modes; Kinetic projectile improvements auto-mature without a routine ammunition menu; the normal Missile line matures GP energetic yield while a bounded Swarmer Missile branch provides a distinct coverage/PDS-saturation niche. TL1-TL6 drive calibration, TL7 is advanced-game validation, and TL8-TL9 are endpoint stress checks rather than whole-game complexity drivers.

## Architecture rules

- TL1 is a highly mature slightly futuristic baseline; TL2-4 broadly feel like lower science fiction; TL5-7 higher science fiction; TL8-9 increasingly science fantasy. These are soft tone guides, not fixed family breakpoints.
- Every visible discipline owns a useful vertical spine. Cross-pollination expands branches and integration but cannot gate ordinary owning-discipline progression.
- Related research is descriptive and non-gating. Sparse hard external prerequisites may be established by explicit component/technology decisions when genuinely enabling; dependent technologies unlock automatically when their final prerequisite is completed. Tall progression must retain meaningful ungated vertical capability.
- Quiet TLs, one-off technologies, specialist Auxiliaries, and legacy revivals are valid; do not invent filler upgrades.
- Installation Space is the universal mass/volume/integration capacity. Auxiliary is a component role, not a separate slot pool.
- Heat rejection, radiation shielding, containment, service routing, and similar engineering normally live inside Space, power, signature, Strain, condition, or explicit traits rather than new universal meters.
- PDS has three separate sibling lineages from TL1: Kinetic, Energy/Beam, and local AMM. Main-weapon lineages do not automatically govern PDS progression.
- Normal player research remains TL1-TL9. TL10 is Precursor-grade shorthand, not a tenth research level.
- CP108 assigns a player-expression class to every Storyboard beat so research can resolve as installed hardware, automatic architecture/capability, operating mode, payload/variant, campaign infrastructure, supporting research, deferred concept, or Precursor exception without pretending every beat is a separate component.
- A specialist branch may unlock at a TL without replacing the contemporary standard family. Quiet primary-family TLs are preferable to silently turning branches into mandatory/default replacements.
- Causal/precognitive information access remains outside normal player TL1-TL9. Pinnacle sensing, ECM, ECCM, and computing remain probabilistic, provenance-aware, observer-safe, and counterable.
- Ammunition uses a strict-dominance guardrail: compatible improvements with no meaningful tactical downside become automatic family upgrades; only non-dominating tradeoffs remain selectable payload modes. Normal variants share broad magazine families; exceptional exotic munitions may be individually tracked.

## Player-expression classes

| Class | Meaning |
|---|---|
| `automatic_architecture` | Automatic hull/material/integration architecture; normally no separate installation. |
| `automatic_capability` | Capability added automatically to the owning family when it is a strict extension rather than a tactical choice. |
| `installed_component` | An installed player-facing component or alternate installed family. |
| `optional_component` | A non-mandatory installed support/specialist component competing for universal Installation Space. |
| `operating_mode` | A player-selectable mode/posture only when a meaningful cost/benefit tradeoff exists. |
| `payload_variant` | Ammunition, warhead, seeker/payload, or other selectable package/variant rather than a new shipwide system. |
| `campaign_capability` | A research capability whose principal expression is campaign/exploration/logistics behavior rather than a combat installation. |
| `infrastructure` | A route/site/infrastructure technology rather than an ordinary cruiser component. |
| `supporting_research` | Worldbuilding/enabling architecture recorded for completeness without a standalone player-facing item yet. |
| `deferred_concept` | Preserved idea not adopted into the current normal-player table. |
| `precursor_exception` | Precursor/TL10-shorthand exception outside normal player-developed TL1-TL9. |

## Hull

### Cruiser Structural Integration

**Identity:** A bounded cruiser platform whose main progression is better use of volume, load paths, service routing, survivability and integration rather than unlimited Hull Points or giant size.

**TL1-TL3 reconciliation:** TL1 narrative should be more advanced than the current shorthand “rolled-alloy era.” TL3 integration is consistent with accepted numbers; no numeric change is made here.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Mature aerospace/composite cruiser construction | base / core_family | `automatic_architecture` | Late-near-future alloys, ceramics, composites, embedded diagnostics, mature compartmentation and robust service trunks define the normal player cruiser. Baseline shielding/FTL are setting breakthroughs layered onto an otherwise comprehensible hull. | Armor; Computing / Fire Control | — | RI-004; RI-037; SD-DC-008; SD-Q15-001 | — |
| 2 | Distributed structural monitoring and modular service architecture | candidate / maturation | `automatic_architecture` | Improved embedded sensing, modular access and standardized high-energy service interfaces make repairs/refits cleaner without requiring more hull size. | Computing / Fire Control | — | SD-DC-003; SD-DC-008 | — |
| 3 | Integrated cruiser architecture | existing / maturation | `automatic_architecture` | The accepted TL3 +1 Installation-Space direction fits a structural-integration story: better routing, packaging and compartment use rather than a universal durability increase. | Power; Propulsion | — | Concept 8.7; CP104 | — |
| 4 | Nanostructured load-bearing frame | candidate / cross_pollinated_derivative | `automatic_architecture` | Advanced carbon structures/superalloys improve specific strength and high-temperature service integration, enabling better packaging and damage tolerance. | Armor | — | TI Carbon Nanotubes; TI Superalloys; SD-DC-009 | — |
| 5 | Atomically engineered structural composites | candidate / maturation | `automatic_architecture` | Designed material gradients, high-temperature joints and resilient laminates support high-energy systems without simply enlarging the cruiser. | Armor; Power | — | TI Superalloys; TI Molecular Assemblers | — |
| 6 | Self-monitoring smart lattice | candidate / cross_pollinated_derivative | `automatic_architecture` | Structural members participate in continuous load sensing and damage isolation; automated repair systems can stabilize rather than freely regenerate serious damage. | Computing / Fire Control; Armor | — | SD-DC-007; SD-DC-009 | — |
| 7 | Active load-distribution structure | candidate / maturation | `automatic_architecture` | High-SF structural control actively redistributes stress and isolates shocks, creating better tolerance for extreme propulsion/weapon loads. | Power; Propulsion | — | SD-SM-004; SD-Q15-003 | — |
| 8 | Field-assisted structural support | candidate / weird_science | `automatic_architecture` | Local field effects help support extreme accelerations, impacts or internal load paths. Treat as bounded support, not immunity to damage. | Shields; Propulsion | — | GURPS Space miracle taxonomy | — |
| 9 | Dynamic programmable cruiser architecture | candidate / cross_pollinated_derivative | `automatic_architecture` | A pinnacle player hull can re-route services and locally reconfigure material/field support, improving adaptation and repair while remaining the same cruiser lineage. | Armor; Computing / Fire Control | — | TI Molecular Assemblers; SD-DC-009 | — |
### Maintainability and Damage Control

**Identity:** A support lineage covering access, diagnostics, isolation, robotics, fabrication and bounded self-repair. Combat Damage Control remains distinct from post-combat reconstruction.

**TL1-TL3 reconciliation:** Current Damage Control rules already support this lineage. Higher-TL story should use existing conditions/Repair Kits rather than a second repair engine.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Expert crew, distributed spares and diagnostic access | base / core_family | `automatic_capability` | Human maintainers, standardized lockers, remote isolation and mature diagnostics underpin ordinary Damage Control. | Computing / Fire Control | — | SD-DC-001; SD-DC-002 | — |
| 3 | Predictive diagnostics and better service distribution | candidate / maturation | `automatic_capability` | Improved condition monitoring and maintainability reduce the engineering burden of complex systems without adding a new repair currency. | Computing / Fire Control | — | SD-DC-003; SD-DC-008 | — |
| 4 | Remote repair robotics | candidate / cross_pollinated_derivative | `optional_component` | Robotic manipulators and autonomous inspection can perform dangerous work while preserving existing Repair Kit/condition abstractions. | Computing / Fire Control | — | SD-DC-007 | — |
| 5 | Onboard fabrication-assisted repair | candidate / specialist_auxiliary | `optional_component` | Compact fabrication can replace selected damaged parts from broad resources; it is a support choice, not free restoration. | Armor | — | TI Molecular Assemblers; SD-DC-009 | — |
| 6 | Autonomous repair swarm | candidate / cross_pollinated_derivative | `optional_component` | Coordinated micro/robotic repair can stabilize multiple faults or improve repair efficiency, bounded by material/energy and condition limits. | Computing / Fire Control; Power | — | SD-DC-007; SD-DC-009 | — |
| 7 | Self-healing structural materials | candidate / cross_pollinated_derivative | `automatic_capability` | Engineered materials can close small cracks and restore limited integrity between severe events; destroyed components still require replacement. | Armor | — | SD-DC-009; TI Molecular Assemblers | — |
| 8 | Programmable matter repair patches | candidate / weird_science | `optional_component` | High-end matter control produces configurable structural patches and interfaces; use as bounded repair acceleration, not resurrection. | Armor; Power | — | TI Molecular Assemblers | — |
| 9 | Autonomous reconstruction architecture | candidate / maturation | `automatic_capability` | Pinnacle player maintainability can reconfigure stored matter and robotic systems to rebuild complex assemblies over appropriate campaign time, while still consuming resources. | Power; Computing / Fire Control | — | SD-Q06-005 | — |
### Habitation and Gravity Architecture

**Identity:** Mostly narrative/architectural support. Spin or acceleration gravity may remain a mature baseline; generated gravity is a later architectural breakthrough, not a mandatory combat stat.

**TL1-TL3 reconciliation:** No gravity technology is currently needed for the accepted combat model. Capture it now as architectural worldbuilding/cross-pollination.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Spin/acceleration gravity and mature long-duration habitation | base / branch | `supporting_research` | Conventional artificial-gravity architecture and medical countermeasures support extended missions. | Propulsion | — | SD-SG-001; SD-SG-003 | — |
| 4 | Compact/stowable gravity habitats | candidate / maturation | `supporting_research` | Improved structural and control systems reduce the burden of rotating habitats while preserving them as rugged legacy architecture. | Computing / Fire Control | — | SD-SG-003; SD-SG-004 | — |
| 6 | Generated local gravity | candidate / weird_science | `supporting_research` | A genuine higher-SF breakthrough may replace rotation in selected spaces, changing ship architecture more than combat arithmetic. | Power | — | SD-SG-002 | — |
| 8 | Inertial-comfort field | deferred / weird_science | `deferred_concept` | Field control may protect crew/equipment from extreme acceleration. Keep separate from tactical evasion until a clear gameplay role exists. | Propulsion; Shields | — | GURPS Space gravity discussion | — |

## Armor

### Passive Armor Materials

**Identity:** Layered protection whose identity comes from material architecture, Integrity and Protection rather than a single escalating resistance value.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Advanced alloy/ceramic composite armor | base / core_family | `automatic_architecture` | TL1 should read as slightly futuristic aerospace/warship armor, not literal industrial-era rolled plate. The accepted mechanics can remain unchanged while the narrative baseline is modernized. | Hull | — | TI Superalloys; TI Carbon Nanotubes; RI-003 | — |
| 2 | Toughened ceramic-composite laminate | existing / maturation | `automatic_architecture` | The accepted TL2 Integrity maturation fits improved fracture control and laminate design. | Hull | — | Concept TL2 Armor | — |
| 3 | Protected layered composite | existing / maturation | `automatic_architecture` | The accepted AP1/AI5 direction fits stronger layering/material interfaces without requiring a new armor family. | Hull | — | Concept 8.7; CP104 | — |
| 4 | Nanostructured armor matrix | candidate / cross_pollinated_derivative | `automatic_architecture` | Carbon nanostructures and atomically engineered alloys improve specific strength and thermal/radiation tolerance. | Hull | — | TI Carbon Nanotubes; TI Superalloys | — |
| 5 | Gradient/diamondoid composite armor | candidate / maturation | `automatic_architecture` | Designed material gradients and extremely strong covalent structures create more efficient passive protection. | Hull | — | TI Diamondoids/Molecular Assemblers | — |
| 6 | Self-healing smart laminate | candidate / cross_pollinated_derivative | `automatic_architecture` | Damage-tolerant material can restore limited integrity or improve repairability after combat rather than negate incoming damage. | Hull; Computing / Fire Control | — | TI Molecular Assemblers; SD-DC-009 | — |
| 9 | Programmable matter armor | candidate / maturation | `automatic_architecture` | Pinnacle armor dynamically optimizes local material structure and can regain limited Integrity through controlled reconfiguration. | Hull; Power | — | TI Molecular Assemblers | — |
### Armor Enhancement Branches

**Identity:** Optional external/auxiliary defensive layers that create distinct tradeoffs rather than replacing primary armor.

**TL1-TL3 reconciliation:** Do not turn every later armor improvement into another universal layer. Specialist counters should remain optional and causal.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Ablative outer layer | existing / specialist_auxiliary | `optional_component` | A TL1 optional outer armor layer is legal on the starting cruiser. It is an Auxiliary/support component that consumes the same universal Installation Space budget as every other installation; Space represents its added mass, volume, mounting, structure and service burden. It is not preinstalled and normally is replaced rather than repaired in combat. | Hull | — | Concept 9.4.1-9.4.3; Concept 10.9; C-068 | Starting legality and role are established. The provisional 1-Space footprint remains for the later component-table pass; no separate AUX capacity exists. |
| 4 | Thermal/radiation hardening package | candidate / specialist_auxiliary | `optional_component` | Specialist protection counters ionizing/particle or high-temperature effects without creating a universal resistance stat. | Hull | — | SD-SW-022; SD-Q15-003 | — |
| 5 | Powered reactive armor | candidate / cross_pollinated_derivative | `optional_component` | A powered armor auxiliary may alter one specific damage/penetration interaction at Tactical Power cost. | Power | — | RM-THEME-006 | — |
| 7 | Adaptive reactive armor architecture | candidate / maturation | `optional_component` | Matures the TL5 powered-reactive concept with faster sensing/control and more selective response. It remains an optional powered armor enhancement rather than automatic behavior of passive primary armor. | Power; Computing / Fire Control | — | RM-THEME-006 | Primary passive armor remains unpowered and usable when this enhancement is absent or unpowered. |
| 7 | Electromagnetic particle screen | deferred / specialist_auxiliary | `deferred_concept` | This concept overlaps the Shield-support particle-deflection family. Preserve the reference idea, but do not create a second near-duplicate charged-particle screen under Armor unless later mechanics prove a distinct armor-layer behavior is needed. | Power; Shields | — | SD-SW-045 | Consolidated with Shield Support for the provisional table; not an independent adopted Armor component. |
| 8 | Field-assisted armor reinforcement | candidate / weird_science | `optional_component` | A late optional field layer redistributes a bounded fraction of impact/deposition through the armor structure. It is powered, penetrable, and specialist rather than a new universal passive-armor stat. | Shields; Power | — | RM-THEME-005 | Do not make primary armor depend on Tactical Power or create immunity to ordinary penetration. |

## Power

### Main Reactor Generation

**Identity:** Sustained Tactical Power generation. Output, footprint, reliability, damaged output, overload, conversion efficiency, containment and enabling science are independent axes.

**TL1-TL3 reconciliation:** CP105 flags a story mismatch at TL2: the current mechanical candidate behaves mostly like improved TL1 output. Later table work should make Early Fusion read as a distinct family without invalidating accepted CP104 numbers by default.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Peak Fission | base / core_family | `installed_component` | Highly mature fission provides the dependable starting reactor. It is not obsolete merely because Fusion appears. | Hull | — | Concept 8.4; SD-Q10-002 | — |
| 2 | Early Practical Fusion | existing / core_family | `installed_component` | The first viable shipboard Fusion family appears. It should eventually have a recognizable operating/design promise beyond being “Reactor 2,” even if the accepted provisional numeric seed is retained until later table work. | Hull | — | Concept 8.4; LLNL NIF; TI Nuclear Fusion Methodologies | — |
| 3 | Mature Compact Fusion | existing / maturation | `installed_component` | Fusion integration/packaging improves; the accepted 6-TP/5-Space direction already fits this story. | Hull | — | Concept 8.4; CP104 | — |
| 4 | High-Output Fusion | existing / maturation | `installed_component` | Mature Fusion pushes the usable output frontier or delivers another genuinely output-related improvement. | Hull | — | Concept 8.4 | — |
| 5 | Early Antimatter Reactor | existing / core_family | `installed_component` | The first practical antimatter reactor becomes a new high-energy family with severe containment/production burdens. Peak Fusion remains a mature contemporary alternative rather than disappearing from the equipment catalog. | Hull; Armor | — | Concept 8.4; CERN Antimatter; SD-Q10-006 | — |
| 6 | Mature Antimatter | existing / maturation | `installed_component` | Containment, conditioning, integration and reliability make Antimatter practical enough for regular high-end warships. | Armor; Computing / Fire Control | — | Concept 8.4; CERN Antimatter | — |
| 7 | High-Output Antimatter | existing / maturation | `installed_component` | Antimatter reaches its strong player-developed performance form, with containment still a defining engineering identity. | Armor | — | Concept 8.4 | — |
| 8 | Fractional / Direct Matter-Conversion Reactor | existing / weird_science | `installed_component` | Limited direct conversion of ordinary feedstock appears as a new reactor principle. Peak Antimatter remains a mature alternative with known containment/logistics behavior. | Hull | — | Concept 8.4 | — |
| 9 | Total Matter Conversion | existing / core_family | `installed_component` | The normal player power ladder reaches its pinnacle: controlled conversion of ordinary matter to usable energy, bounded by component architecture and game balance rather than infinite power. | Hull | — | Concept 8.4 | — |
### Late Fission Specialist Revival

**Identity:** A deliberate example of the rule that old technology may become interesting again through new materials/conversion methods.

**TL1-TL3 reconciliation:** This lineage is intentionally sparse. It demonstrates legacy revival without forcing a fission entry at every TL.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 5 | Direct-conversion / advanced-containment fission specialist | base / legacy_revival | `installed_component` | Later materials, high-temperature conversion and reactor engineering may produce an exceptionally rugged, low-maintenance, damage-tolerant or low-signature fission reactor even after Fusion is dominant. It need not beat contemporary Antimatter on raw output. | Armor; Hull | — | Concept 8.3 Optimum Fission example; TI Advanced Fission Systems; NASA Space Nuclear Propulsion | — |
| 7 | Pinnacle fission expedition/auxiliary reactor | base / legacy_revival | `installed_component` | A mature fission derivative could remain attractive for long endurance, independent fuel logistics, benign failure modes or infrastructure duty. Keep as a niche, not a mandatory ladder step. | Hull | — | SD-Q10-001; SD-Q10-008 | — |
### Pulse Storage and Power Conditioning

**Identity:** Storage handles peak demand and temporal mismatch rather than replacing sustained reactor generation.

**TL1-TL3 reconciliation:** Keep storage as Aux/support choices unless a genuine whole-ship architecture requires otherwise.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | High-density battery / pulse capacitor | base / specialist_auxiliary | `optional_component` | A compact energy store can support emergency power or burst loads within existing Tactical Power rules. | Hull | — | SD-Q10-003 | — |
| 2 | Supercapacitor bank | candidate / cross_pollinated_derivative | `optional_component` | Nanostructured capacitors combine rapid charge/discharge with useful capacity, especially for burst weapons/shields. | Armor | — | TI Supercapacitors | — |
| 4 | Superconducting magnetic storage | candidate / cross_pollinated_derivative | `optional_component` | Advanced superconductors enable high-rate storage and low-loss power conditioning. | Armor | — | TI Advanced Superconductors; TI High-Temperature Superconductors | — |
| 6 | Molecular dielectric ultracapacitor | candidate / maturation | `optional_component` | Atomically engineered storage improves density/retention and pulse delivery without changing main-reactor output. | Armor | — | TI Molecular Assemblers | — |
| 8 | Field-energy reservoir | deferred / weird_science | `deferred_concept` | A high-end field system may store/release large energy pulses. Require explicit finite capacity and failure consequences if adopted. | Shields | — | RM-THEME-012 | — |
### Thermal Management and Energy Conversion

**Identity:** Thermal rejection and conversion are real engineering burdens expressed through component Space, power, signature, Strain, reliability and explicit modes. The lineage never creates a default shipwide heat/coolant/radiator damage subsystem.

**TL1-TL3 reconciliation:** Thermal remains support architecture, not a new visible research tree.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Heat pipes, coolant loops, radiators and phase-change reserves | base / core_family | `supporting_research` | Ordinary thermal engineering is part of component footprints rather than a universal heat meter. | Hull | — | SD-Q15-001; SD-Q15-002 | No universal heat meter, coolant inventory, radiator hit location, or independent radiator condition track. |
| 3 | High-temperature compact radiators | candidate / maturation | `supporting_research` | Improved materials permit smaller/hotter thermal systems with power/vulnerability tradeoffs. | Armor | — | SD-Q15-003; TI Advanced Heat Management Concepts | No universal heat meter, coolant inventory, radiator hit location, or independent radiator condition track. |
| 4 | Droplet/mist radiator architecture | candidate / branch | `supporting_research` | Advanced radiator forms can reduce mass/area for selected ships or installations. Treat as integration/Space support, not a new tactical bar. | Armor | — | TI Advanced Heat Management Concepts | No universal heat meter, coolant inventory, radiator hit location, or independent radiator condition track. |
| 5 | Retractable thermal suppression | candidate / operating_capability | `optional_component` | A ship may temporarily reduce exposed thermal signature by storing heat, with finite duration/Strain/activation limits rather than a continuous heat simulation. | Sensors / EW | — | SD-Q15-005; SD-Q12-004 | No universal heat meter, coolant inventory, radiator hit location, or independent radiator condition track. |
| 6 | Direct energy recovery / advanced heat pumping | candidate / cross_pollinated_derivative | `supporting_research` | More waste energy is recovered or shifted, supporting high-energy systems and lower signatures. | Armor | — | SD-Q10-005; SD-Q15-010 | No universal heat meter, coolant inventory, radiator hit location, or independent radiator condition track. |
| 8 | Entropy-routing field | deferred / weird_science | `deferred_concept` | Science-fantasy thermal control could temporarily move/store waste entropy in a bounded way. Keep far short of “no waste heat.” | Shields | — | RM-THEME-007 | No universal heat meter, coolant inventory, radiator hit location, or independent radiator condition track. |

## Propulsion

### Sublight Propulsion

**Identity:** Tactical/system maneuver. The story should preserve thrust/efficiency/endurance/overload distinctions while keeping movement rules KISS.

**TL1-TL3 reconciliation:** Current TL1-TL3 mechanics are generic movement values; CP105 flags the need for explicit operating-principle names/identity in later table work.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | High-power electric/plasma cruiser drive | base / core_family | `installed_component` | A slightly futuristic high-power electromagnetic/plasma system provides the normal STL baseline. Nuclear-electric and electric propulsion provide grounded inspiration for efficient in-space thrust, while Star Cluster abstracts actual acceleration into Move. | Power | — | NASA SEP; NASA Space Nuclear Propulsion; SD-Q10-007 | — |
| 2 | Pulsed high-energy plasma drive | candidate / maturation | `installed_component` | Better field control and power electronics increase useful tactical thrust without changing the research family into “Fusion Drive” automatically. | Power | — | TI High-Energy Electromagnetic Propulsion | — |
| 3 | Fusion-assisted torch / mature high-energy STL | candidate / cross_pollinated_derivative | `installed_component` | The accepted Move3 direction can be narrated as Propulsion exploiting mature Fusion-era power/containment, while Propulsion remains the owning tree. | Power | — | NASA Fusion Driven Rocket; SD-Q10-007 | — |
| 4 | Mature fusion torch architecture | candidate / maturation | `installed_component` | Lower-SF propulsion reaches a high-thrust/high-endurance form and better bounded overload behavior. | Power | — | LLNL NIF; NASA Fusion Driven Rocket | — |
| 5 | Antimatter-catalyzed fusion drive | candidate / cross_pollinated_derivative | `installed_component` | Tiny antimatter quantities catalyze a mature fusion/plasma system, bridging families without requiring a full antimatter main drive. | Power | — | SD-Q10-006 | — |
| 6 | Antimatter plasma drive | candidate / core_family | `installed_component` | Mature containment supports a direct high-energy antimatter/plasma propulsion family. | Power | — | CERN Antimatter | — |
| 7 | Beam-core / ultra-high-energy propulsion | candidate / maturation | `installed_component` | Higher-SF antimatter propulsion emphasizes extreme output and integration burden rather than free movement. | Power | — | TI Power Plant/drive inspiration | — |
| 8 | Inertial-coupled drive | candidate / weird_science | `installed_component` | Field manipulation begins reducing inertial/structural limits. Keep acceleration, fuel and tactical response costs explicit. | Hull; Shields | — | GURPS Space reactionless/gravity discussion | — |
| 9 | Gravitic/metric sublight drive | candidate / weird_science | `installed_component` | Pinnacle player STL manipulates local fields/spacetime for maneuver without becoming teleportation. Tactical hex movement and initiative still apply. | Power; Shields | — | GURPS Space gravity/drive taxonomy | — |
### Specialist Sublight Drives

**Identity:** Branches useful for probes, infrastructure or niche ships. They illustrate that “best” propulsion depends on mission.

**TL1-TL3 reconciliation:** Specialist drives need not occupy the base cruiser ladder.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Solar/nuclear electric endurance drive | base / branch | `installed_component` | Very efficient low-thrust drives remain excellent for probes/logistics even if inappropriate for tactical cruiser maneuver. | Power | — | NASA SEP; NASA NEP; SD-Q10-001 | — |
| 2 | Nuclear thermal sprint drive | base / branch | `installed_component` | A fission thermal branch can trade propellant efficiency and reactor integration for higher thrust. It may be infrastructure/mission tech rather than the player cruiser default. | Power | — | NASA Space Nuclear Propulsion | — |
| 4 | Fission pulse expedition drive | candidate / legacy_revival | `installed_component` | Advanced structures/materials could make pulsed fission propulsion a rugged specialist option. | Hull; Armor | — | TI Fission Pulse Drives | — |
### Strategic FTL Drive

**Identity:** Cluster-map transit. FTL is a deliberate setting miracle available at TL1; progression should preserve unknown-space exploration, route knowledge and strandedness rather than erase the map.

**TL1-TL3 reconciliation:** FTL remains separate from STL despite shared Propulsion research. Do not let high TL erase unknown-sector stops or exploration stakes without an explicit future decision.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | First-generation practical FTL | existing / core_family | `installed_component` | FTL is the setting-defining exception to the otherwise slightly futuristic TL1 tone. Its exact fictional physics can remain deliberately broad until lore requires a stronger commitment. | Computing / Fire Control | — | Concept 8.3; GURPS Space one-miracle framing; SD-Q23-001 | — |
| 2 | Stabilized FTL transit | existing / maturation | `installed_component` | Reliability/navigation and known-space speed improve while unknown-sector entry still interrupts movement. | Sensors / EW | — | SD-Q23-004 | — |
| 3 | Integrated FTL navigation | existing / maturation | `installed_component` | The accepted Move3 strategic direction represents faster known-space transit without defeating exploration geography. | Sensors / EW | — | Concept 8.7 | — |
| 4 | High-throughput FTL field | candidate / maturation | `installed_component` | Mature lower-SF FTL improves route efficiency, recovery and hazard tolerance rather than simply multiplying range. | Hull | — | SD-Q23-002; SD-Q23-009 | — |
| 5 | Adaptive transition geometry | candidate / operating_capability | `installed_component` | Higher-SF FTL can better handle difficult stars/regions or emergency rerouting, with explicit map-level costs. | Sensors / EW | — | SD-Q24-003 | — |
| 6 | Deep-route FTL navigation | candidate / cross_pollinated_derivative | `installed_component` | Advanced sensing/computation reduces uncertainty and supports more ambitious route planning without making unknown space fully known. | Sensors / EW; Computing / Fire Control | — | SD-Q23-009 | — |
| 7 | Resilient high-energy FTL | candidate / maturation | `installed_component` | A mature higher-SF drive tolerates disruptions and improves recovery/operating envelope; routine tactical micro-jumps remain deferred. | Power | — | SD-Q24-008 | — |
| 8 | Metric-transition FTL | candidate / weird_science | `installed_component` | Player science begins explicit spacetime engineering. This can alter strategic constraints but should not become arbitrary teleportation. | Power; Sensors / EW | — | Alcubierre paper; GURPS Space warp taxonomy | — |
| 9 | Pinnacle topology-control FTL | candidate / weird_science | `installed_component` | The strongest normal player FTL may shape routes/transition conditions in bounded ways while preserving sector geography and campaign decisions. | Power; Sensors / EW | — | SD-Q23-008; SD-Q24-003 | — |
### Transit Infrastructure and Natural/Artificial Routes

**Identity:** Strategic infrastructure that changes sector topology without replacing the onboard FTL ladder.

**TL1-TL3 reconciliation:** TL10 here is shorthand only; Precursor routes are not player research.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 4 | Mapped natural shortcuts / stable anomalies | candidate / campaign_technology | `infrastructure` | Sensors/Exploration can reveal persistent routes that low-TL ships may exploit. | Sensors / EW | — | SD-Q23-003; SD-Q24-005 | — |
| 7 | Player-built transit anchor | deferred / infrastructure | `deferred_concept` | A mature civilization might stabilize or service fixed route nodes. This is infrastructure, not a cruiser upgrade. | Power; Hull | — | SD-Q23-008 | — |
| 9 | Limited player-built gate network | deferred / infrastructure | `deferred_concept` | Pinnacle player science may construct rare fixed links under strict constraints; evaluate only when sector-economy/logistics systems warrant it. | Power | — | SD-Q23-003 | — |
| 10 | Precursor gate / one-way conduit / impossible shortcut | exotic / precursor_artifact | `precursor_exception` | A Precursor route artifact may explicitly break one normal FTL rule because the exception itself is discoverable content. | Sensors / EW | — | SD-Q24-007; RM-THEME-017 | — |

## Sensors / EW

### Sensor Suite

**Identity:** Multimodal passive/active sensing that creates observer-specific track quality and identification. Physical reach and attack eligibility remain separate.

**TL1-TL3 reconciliation:** Current TL1-TL3 sensor progression already fits the family-story approach well.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Integrated multimodal sensor suite | base / core_family | `installed_component` | Passive and active optical/radar/thermal/electronic sensing support navigation, search and weapons-quality tracking. | Computing / Fire Control | — | SD-Q09-001; SD-Q09-003 | — |
| 2 | Improved discrimination resistance | existing / maturation | `installed_component` | The accepted DR1 direction represents better classification/filtering under EW rather than simple range escalation. | Computing / Fire Control | — | Concept TL2 Sensor | — |
| 3 | Dual normal active modes | existing / operating_capability | `operating_mode` | The accepted Low/High Active modes are a qualitative integration step with real Tactical Power choice. | Power | — | Concept 8.7 | — |
| 4 | Multimodal fusion and cooperative apertures | candidate / cross_pollinated_derivative | `installed_component` | Advanced processing combines channels, rapid beam steering and shared observations while preserving provenance. | Computing / Fire Control | — | SD-Q09-004; SD-Q09-006; SD-Q09-007 | — |
| 5 | Low-probability active sensing / adaptive waveform suite | candidate / operating_capability | `installed_component` | Sensors trade emission conspicuousness, power and discrimination rather than simply becoming invisible. | Computing / Fire Control | — | SD-Q12-005; RM-THEME-013 | — |
| 6 | Quantum-limited / precision field sensors | candidate / cross_pollinated_derivative | `installed_component` | Higher-SF detectors improve weak-signal discrimination and navigation; avoid claims of magical omniscience. | Computing / Fire Control | — | TI Quantum Computing as enabling inspiration | — |
| 7 | Integrated penetrating multimodal sensing | candidate / maturation | `installed_component` | The standard high-TL suite integrates particle, gravity-gradient and other weak-signal channels with conventional observations. These channels improve difficult-contact inference without guaranteeing detection or identification. | Power | — | SD-Q09-008 | — |
| 8 | Spacetime/FTL-wake sensing | candidate / weird_science | `installed_component` | Science-fantasy sensors detect metric disturbances, transit wakes or field signatures; they do not automatically identify every ship. | Propulsion | — | SD-Q23-006 | — |
| 9 | Pinnacle multi-domain inference suite | candidate / maturation | `installed_component` | The player-developed pinnacle fuses independent passive, active, field and historical observations into unusually strong probabilistic tracks while preserving uncertainty, occlusion/provenance rules, and observer-safe information. | Computing / Fire Control | — | RM-THEME-009 | No precognition, hidden-state access, or automatic perfect identification. Causal/precognitive sensing remains Precursor-only. |
### Electronic Countermeasures

**Identity:** Active deception, noise, signature manipulation and track attack. Higher TL should diversify methods/costs instead of stacking unlimited rating.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Conventional noise/deception ECM | base / core_family | `installed_component` | Baseline ECM attacks discrimination at Tactical Power cost. | Computing / Fire Control | — | Concept ECM | — |
| 2 | High-strength conventional ECM | existing / maturation | `installed_component` | The accepted rating-2 ceiling increases pressure but remains non-additive across duplicate suites. | Power | — | Concept TL2 ECM | — |
| 3 | Efficient full-strength ECM | existing / maturation | `installed_component` | The accepted TL3 efficiency step reduces Tactical Power burden without raising rating. | Power | — | Concept 8.7 | — |
| 4 | Digital deception / false-track synthesis | candidate / operating_capability | `installed_component` | ECM can attack track provenance/identification with bounded ghost/deception behavior rather than only a larger number. | Computing / Fire Control | — | SD-SW-013; RM-THEME-013 | — |
| 5 | Adaptive cognitive EW | candidate / cross_pollinated_derivative | `installed_component` | Processing adapts jamming/deception to observed sensor behavior within information parity. | Computing / Fire Control | — | SD-Q09-006 | — |
| 6 | Distributed cooperative EW | candidate / branch | `installed_component` | Multiple allied emitters coordinate without simply adding local ratings; cooperative effects remain capped. | Computing / Fire Control | — | Concept cooperative EW; RM-THEME-013 | — |
| 7 | Emitter-targeted electronic attack | candidate / one_off | `installed_component` | Specialized systems attack active sensor/datalink behavior or force hard choices rather than universally suppressing everything. | Missile Weapons | — | SD-SW-012; SD-SW-035 | — |
| 8 | Field/signature spoofing | candidate / weird_science | `installed_component` | High-end emitters imitate exotic propulsion/shield signatures or distort apparent motion, with specialist counters. | Shields; Propulsion | — | RM-THEME-006 | — |
| 9 | Pinnacle adaptive cross-spectrum deception | candidate / maturation | `installed_component` | Pinnacle ECM coordinates deception across conventional and exotic observable channels, attacking consistency and identification while remaining detectable/counterable rather than erasing the ship from play. | Propulsion | — | RM-THEME-009 | No perfect invisibility and no falsification of information the defender independently observed. |
### Electronic Counter-Countermeasures

**Identity:** Counter-deception, fusion, validation and robust tracking. It should not become “ECM but positive.”

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Conventional filtering and emitter analysis | base / core_family | `installed_component` | Baseline ECCM restores discrimination against ordinary ECM. | Computing / Fire Control | — | Concept ECCM | — |
| 2 | High-strength conventional ECCM | existing / maturation | `installed_component` | The accepted rating-2 ceiling counters stronger conventional jamming at real power cost. | Power | — | Concept TL2 ECCM | — |
| 3 | Efficient full-strength ECCM | existing / maturation | `installed_component` | The accepted TL3 efficiency step reduces cost without automatically raising sensor range. | Power | — | Concept 8.7 | — |
| 4 | Sensor-fusion anti-deception | candidate / cross_pollinated_derivative | `installed_component` | Cross-checking multiple modalities makes false tracks harder while preserving uncertainty where all channels are weak. | Computing / Fire Control | — | SD-Q09-004 | — |
| 5 | Adaptive classifier / signature memory | candidate / maturation | `installed_component` | Advanced processing learns opponent deception patterns during observed combat without reading hidden ratings. | Computing / Fire Control | — | RM-THEME-013 | — |
| 6 | Cooperative track validation | candidate / operating_capability | `installed_component` | Allied observations can validate or reject deception with explicit provenance and bounded networking. | Computing / Fire Control | — | SD-Q09-007 | — |
| 7 | Counter-emitter localization | candidate / branch | `installed_component` | ECCM can turn hostile active emissions into localization/targeting opportunities for specialist weapons. | Missile Weapons | — | SD-SW-012 | — |
| 8 | Exotic-channel correlation | candidate / weird_science | `installed_component` | Metric/particle channels help reject advanced signature manipulation, at high cost and limited coverage. | Power | — | SD-Q09-008 | — |
| 9 | Pinnacle provenance-weighted track validation | candidate / maturation | `installed_component` | Pinnacle ECCM continuously compares independent observations, emitter history and model consistency to resist sophisticated deception while still producing bounded probabilistic confidence rather than absolute truth. | Computing / Fire Control | — | RM-THEME-009 | No omniscient truth oracle; uncertainty and failed discrimination remain possible. |
### Signature Management and Stealth

**Identity:** A potential branch covering passive design, quiet operation and bounded active concealment. It is not currently a standard TL table stream.

**TL1-TL3 reconciliation:** Keep ordinary passive signature management distinct from a future active cloak.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Passive low-observability design | base / branch | `operating_mode` | Geometry, emissions discipline and ordinary thermal management can reduce observability without creating invisibility. | Hull | — | SD-Q12-001; SD-Q12-002 | — |
| 3 | Emission-controlled operating posture | candidate / operating_capability | `operating_mode` | Ships may accept reduced active systems/performance for a quieter signature state. | Power | — | SD-Q12-005 | — |
| 5 | Thermal suppression window | candidate / cross_pollinated_derivative | `operating_mode` | Retractable/thermal-storage architecture creates a finite quiet window with explicit limits. | Power | — | SD-Q12-004; SD-Q15-005 | — |
| 6 | Active signature cancellation | deferred / branch | `deferred_concept` | Adaptive emissions can cancel or reshape specific signatures, but should be channel-limited and power-hungry. | Computing / Fire Control | — | SD-Q12-006 | — |
| 8 | Powered concealment field | deferred / weird_science | `deferred_concept` | An active cloak-like system could be a rare high-end Powered installation with incompatibilities and no guaranteed total invisibility. | Shields; Power | — | SD-Q12-008; Concept cloak deferred rule | — |
| 10 | Precursor phase cloak | exotic / precursor_artifact | `precursor_exception` | A Precursor device may break ordinary observability rules under explicit constraints. | Shields | — | RM-THEME-017 | — |

## Computing / Fire Control

### Tactical Computer and Fire Control

**Identity:** Shipwide fire-control, targeting, report fusion, initiative support and bounded automation. Player/AI information parity remains absolute.

**TL1-TL3 reconciliation:** Current TL1-TL3 story is coherent. Higher levels should emphasize architecture/automation rather than universal percentage bonuses.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Integrated electronic fire control | base / core_family | `installed_component` | Mature electronic/optical computing supports ordinary targeting, datalinks and ship control. | Sensors / EW | — | Concept computing | — |
| 2 | Refined conventional fire control | existing / maturation | `installed_component` | The accepted targeting improvement fits better estimation and processing rather than a new computer principle. | Sensors / EW | — | Concept TL2 Computer | — |
| 3 | Mature integrated fire control / Evasive Compensation | existing / operating_capability | `automatic_capability` | The accepted EvComp capability is a good example of qualitative integration rather than raw accuracy inflation. | Propulsion | — | Concept 8.7 | — |
| 4 | Photonic/optical combat computing | candidate / core_family | `installed_component` | Optical interconnect/processing offers a recognizable lower-SF architectural change in throughput and efficiency. | Power | — | TI Photonic Computing | — |
| 5 | Adaptive AI battle manager | candidate / maturation | `installed_component` | Machine reasoning supports multi-target prioritization, damage prediction and doctrine execution while obeying player-information parity. | Sensors / EW | — | RI-040; CP99 AI parity rule | — |
| 6 | Distributed resilient combat cloud | candidate / cross_pollinated_derivative | `installed_component` | Ship subsystems and allied assets share processing/track tasks with graceful degradation and provenance. | Sensors / EW | — | SD-Q09-006; SD-Q09-007 | — |
| 7 | Quantum-assisted optimization | candidate / core_family | `installed_component` | Quantum/advanced computation accelerates selected optimization/simulation tasks; it is not magical general intelligence. | Power | — | TI Quantum Computing | — |
| 8 | Predictive battle-state synthesis | candidate / maturation | `installed_component` | High-SF computing runs massive counterfactual models to improve timing/coordination. No peeking at hidden enemy state. | Sensors / EW | — | RM-THEME-009 | — |
| 9 | Pinnacle self-verifying battle synthesis | candidate / maturation | `installed_component` | The normal player pinnacle combines extreme parallel prediction, uncertainty modeling and self-checking battle-state synthesis. It can improve decisions and fire control without reading hidden state or predicting the future with certainty. | Sensors / EW | — | GURPS Space superscience caution | Probabilistic decision support only; literal precognition/causal information remains Precursor-grade. |
### Autonomy, Networking and Digital Crew

**Identity:** Cross-pollinated applications of computing rather than a separate visible research tree.

**TL1-TL3 reconciliation:** Keep sentience separate from raw computing power.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 3 | Advanced ship automation | candidate / operating_capability | `automatic_capability` | Automation reduces routine crew burden and supports damage control/sensors. | Hull | — | SD-DC-007 | — |
| 5 | Autonomous specialist agents | candidate / cross_pollinated_derivative | `automatic_capability` | Bounded AI agents support damage control, EW, logistics and tactical planning without replacing officers or subsystems. | Hull; Sensors / EW | — | RI-040 | — |
| 7 | Distributed autonomous mission control | candidate / campaign_technology | `campaign_capability` | Long-duration probes/expeditions can operate with greater independence while retaining meaningful failure/recovery risk. | Hull | — | SD-Q06-002; SD-Q06-005 | — |
| 9 | Synthetic crew core | deferred / weird_science | `deferred_concept` | A high-end digital crew/sentient ship computer may be possible, but narrative/crew consequences need deliberate design first. | Hull | — | SD-Q13-006 | — |

## Shields

### Defensive Field Generator

**Identity:** Renewable defensive field capacity. The exact fictional physics may remain broad; gameplay identity is renewable protection with explicit penetration/counterplay.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Baseline defensive field | existing / core_family | `installed_component` | A practical field generator is one of Star Cluster’s intentional TL1 “miracles.” It provides renewable capacity but no universal Shield Protection. | Power | — | Concept shields | — |
| 2 | Higher-capacity field | existing / maturation | `installed_component` | The accepted TL2 Capacity increase is straightforward field-strength maturation. | Power | — | Concept TL2 Shield | — |
| 3 | Mature stabilized field generator | existing / maturation | `installed_component` | The primary generator matures in stability/integration while the optional Shield Hardener remains a separate powered support component with its own Space and Tactical Power tradeoff. | Power | — | Concept 8.7 | — |
| 4 | Segmented/adaptive field geometry | candidate / operating_capability | `operating_mode` | Mature lower-SF fields can concentrate protection or isolate damaged sectors with meaningful power/coverage tradeoffs. | Computing / Fire Control | — | RM-THEME-001 | — |
| 5 | Frequency/phase-tuned shielding | candidate / maturation | `installed_component` | Advanced field control can specialize against selected beam/particle interactions rather than raising universal defense. | Sensors / EW | — | SD-SW-045 | — |
| 6 | Predictive localized reinforcement | candidate / cross_pollinated_derivative | `installed_component` | Fire-control prediction dynamically reinforces likely impact regions, trading Tactical Power/coverage. | Computing / Fire Control | — | RM-THEME-005 | — |
| 7 | Stand-off shear field | candidate / weird_science | `installed_component` | A higher-SF field begins deflecting or disrupting attacks before contact; keep damage/penetration relationships explicit. | Power | — | GURPS Space force-field taxonomy | — |
| 8 | Metric barrier field | candidate / weird_science | `installed_component` | Science-fantasy shielding manipulates local spacetime/fields to alter incoming trajectories/energy. It still has finite capacity and counters. | Propulsion | — | GURPS Space miracle taxonomy | — |
| 9 | Pinnacle adaptive barrier | candidate / maturation | `installed_component` | The strongest normal player shield combines dynamic geometry and material/field interaction while remaining destructible and power-limited. | Computing / Fire Control | — | RM-THEME-006 | — |
### Shield Support and Specialist Fields

**Identity:** Auxiliary technologies that modify field behavior without becoming another universal shield layer.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Shield Battery / Booster concepts | existing / specialist_auxiliary | `optional_component` | Finite emergency recharge and capacity support remain distinct roles. | Power | — | Concept shield auxiliaries | — |
| 3 | Shield Hardener | existing / specialist_auxiliary | `optional_component` | Powered Protection against shield-facing damage is an explicit optional component. | Power | — | Concept 8.7 | — |
| 5 | Particle/charged-beam screen | candidate / specialist_auxiliary | `optional_component` | A specialist electromagnetic/plasma-like field may counter charged particle beams more effectively than ordinary attacks. | Power | — | SD-SW-045 | — |
| 7 | Field stabilizer / anti-penetration tuner | candidate / specialist_auxiliary | `optional_component` | A dedicated support component trades power/Space for better resistance to a narrow penetration class. | Computing / Fire Control | — | RM-THEME-006 | — |
| 10 | Precursor stasis/phase barrier | exotic / precursor_artifact | `precursor_exception` | A Precursor field may ignore or redirect an otherwise normal rule for a bounded duration or condition. | Power | — | RM-THEME-017 | — |

## Projectile Weapons

### Kinetic Main Weapon

**Identity:** Ship-integrated accelerator weapon. Different accelerator principles can coexist; the gameplay family remains Kinetic when their tactical identity is similar.

**TL1-TL3 reconciliation:** Current TL1-TL3 identity is broadly coherent; CP105 encourages naming the launcher/material story instead of generic Kinetic I/II/III.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Mature electromagnetic mass driver | base / core_family | `installed_component` | A rail/coil-like accelerator with conventional smart fire control provides the baseline finite-ammunition main weapon. | Power; Computing / Fire Control | — | SD-SW-003; SD-SM-002 | — |
| 3 | Power-efficient mature accelerator | existing / maturation | `installed_component` | The accepted zero-TP ordinary fire direction fits mature power conditioning/accelerator efficiency while ammunition remains the defining resource. | Power | — | Concept 8.7 | — |
| 4 | Superconducting coil/induction accelerator | candidate / cross_pollinated_derivative | `installed_component` | Advanced magnets/materials reduce launcher losses and enable new projectile envelopes. | Power; Armor | — | TI Coilguns; TI High-Temperature Superconductors | — |
| 5 | Helical / continuous-induction cannon branch | candidate / branch | `installed_component` | An alternate accelerator architecture may trade Space, rate, velocity and wear without replacing mature rails/coils. | Power | — | SD-SW-031 | — |
| 6 | Smart hypervelocity mass driver | candidate / maturation | `installed_component` | Guided/terminal-corrected penetrators and advanced sabot/projectile architectures improve hit/penetration choices. | Computing / Fire Control | — | SD-SW-030; SD-SW-064 | — |
| 7 | Macron/dust accelerator branch | candidate / branch | `installed_component` | Extremely small high-velocity projectiles create a distinctive saturation/deposition tradeoff and demanding launcher architecture. | Power; Armor | — | SD-SW-041; SD-SW-042 | — |
| 8 | Field-assisted mass accelerator | candidate / weird_science | `installed_component` | Inertial/field control permits extreme projectile velocity or compact launch structures while preserving finite projectile packages. | Shields; Power | — | RM-THEME-005 | — |
| 9 | Relativistic kinetic lance | candidate / weird_science | `installed_component` | Pinnacle Kinetic attacks approach relativistic projectile regimes; use strict cost/range/accuracy/collateral constraints to preserve counterplay. | Power | — | SD-SW-008 | — |
### Kinetic Ammunition and Projectile Packages

**Identity:** Projectile engineering progresses independently of the launcher, but normal compatible improvements are automatic. Kinetic player choice should come mainly from installed weapon-family architecture rather than per-shot ammunition toggles.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Contemporary general-purpose projectile package | base / core_family | `automatic_capability` | The baseline compatible gun uses a contemporary balanced projectile/manufacturing package. Fragmentation, fuzing and penetrator construction remain abstract unless they create a meaningful choice. | Armor | — | SD-SW-061 | Normal projectile subtypes do not receive separate magazine counts. |
| 2 | Improved penetrator/projectile materials | existing / maturation | `automatic_capability` | Improved penetrator/projectile materials automatically mature compatible standard ammunition. Because the improvement has no intended tactical downside, the obsolete package does not remain a selectable loadout. | Armor | — | Concept TL2 Kinetic | Current TL2 APEN improvement is an automatic ammunition maturation, not a separate launcher or inventory type. |
| 4 | Maneuvering / programmable smart projectile | candidate / cross_pollinated_derivative | `automatic_capability` | Improved computing enables bounded terminal correction and programmable fuzing on compatible smart-munition accelerators without turning the shot into a Missile Flight. If the capability is a strict improvement, it is automatic rather than a selectable loadout. | Computing / Fire Control | Computing / Fire Control TL4 | SD-SW-030; SD-SW-064 | Requires a compatible smart-munition interface; legacy accelerators do not automatically gain it. Exact accuracy/degraded-fire benefit awaits calibration. |
| 5 | Graded penetrator/material maturation | candidate / maturation | `automatic_capability` | Improved projectile materials and graded penetrator construction automatically mature compatible standard rounds while preserving the Kinetic family emphasis on physical penetration. | Armor | — | SD-SW-061 | Automatic compatible maturation; no separate penetrator loadout unless a future branch proves a genuinely useful tradeoff. |
| 6 | Mature smart-projectile correction suite | candidate / maturation | `automatic_capability` | Later smart projectiles combine terminal correction, programmable fuzing and improved prediction to raise practical hit probability without becoming miniature Missile Flights. | Computing / Fire Control | — | SD-SW-030; SD-SW-064 | Automatic compatible maturation. Submunition/saturation ammunition is removed from the baseline Kinetic menu; the macron/dust launcher remains a distinct installed branch. |
| 8 | Exotic dense-matter projectile | deferred / weird_science | `deferred_concept` | Very high-density or engineered-matter projectiles are possible high-SF candidates, but material provenance and counterplay need definition. | Armor | — | GURPS Space exotic matter discussion | If adopted as a truly rare/exotic projectile, individual shot tracking is permitted because scarcity itself is gameplay. |
### Kinetic Point Defense

**Identity:** Local terminal defense using rapid kinetic/projectile interceptors and integrated fire control.

**TL1-TL3 reconciliation:** Beam PDS and AMM remain separate branches rather than upgrades that erase kinetic PDS.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Rapid-fire kinetic PDS | existing / core_family | `installed_component` | Finite Reaction Capacity and Ammo abstract many physical shots/intercepts. | Computing / Fire Control | — | SD-SW-011; SD-SW-038 | — |
| 3 | Mature local fire-control / effective-ammo PDS | existing / maturation | `installed_component` | The accepted differentiated PDS maturation can improve Reaction Capacity/efficiency without literal projectile bookkeeping. | Computing / Fire Control | — | SD-SW-037; RM-THEME-011 | — |
| 4 | Guided intercept projectile PDS | candidate / cross_pollinated_derivative | `installed_component` | Smart local rounds improve engagement efficiency and target discrimination. | Computing / Fire Control | — | SD-SW-037 | — |
| 6 | Distributed kinetic intercept grid | candidate / branch | `installed_component` | Multiple mounts/sensors coordinate as one bounded PDS installation rather than multiplying free reactions. | Sensors / EW | — | SD-SW-038 | — |

## Energy Weapons

### Coherent Beam Main Weapon

**Identity:** Laser/beam family whose natural resources are Tactical Power, focusing/track quality and sustained or pulsed energy deposition.

**TL1-TL3 reconciliation:** CP104 shows E3 is a strong robust step. Higher-TL Energy design should be defined in story context before revisiting its numbers.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | High-energy coherent laser | base / core_family | `installed_component` | A practical space-combat laser/beam is an intentional slightly-futuristic-to-lower-SF baseline. | Power; Computing / Fire Control | — | SD-EW-001 | — |
| 2 | Improved optics and pulse conditioning | existing / maturation | `installed_component` | Current TL2 may hold combat stats while materials/power integration mature behind the scenes; no forced improvement is needed at every TL. | Armor; Power | — | SD-EW-002 | — |
| 3 | Safe high-output beam mode | existing / operating_capability | `installed_component` | The accepted Energy High mode is a qualitative power-handling maturation rather than automatic damage on every shot. | Power | — | Concept 8.7 | — |
| 4 | Short-wavelength / advanced focusing beam | candidate / maturation | `installed_component` | Improved wavelength control and optics can extend useful concentration/range independent of raw damage. | Armor; Computing / Fire Control | — | SD-EW-002; SD-EW-003 | — |
| 5 | Tunable-spectrum / free-electron beam branch | candidate / branch | `installed_component` | A tunable beam trades specialization for adaptability against range, material and defensive conditions. | Power; Computing / Fire Control | — | SD-EW-007; SD-EW-008 | — |
| 6 | Distributed/phased beam director | candidate / cross_pollinated_derivative | `installed_component` | Multiple apertures coordinate rapid steering/resilience while sharing a bounded output pool. | Computing / Fire Control | — | SD-SW-029; SD-SW-032 | — |
| 7 | Extreme-frequency beam branch | candidate / branch | `installed_component` | UV/X-ray-class or equivalent high-energy optics become plausible, with demanding generation/focusing/thermal support and possible radiation side effects. | Power; Armor | — | SD-EW-003; SD-EW-006 | — |
| 8 | Field-guided coherent lance | candidate / weird_science | `installed_component` | Science-fantasy field control helps focus/guide extreme beams, but does not grant perfect tracking or infinite range. | Shields | — | SD-SW-033 | — |
| 9 | Pinnacle coherent-energy lance | candidate / weird_science | `installed_component` | Matter-conversion-era power and mature field control support an extreme coherent-energy weapon with explicit power, Strain/charge, range and counterplay. The weapon remains a beam-family system; it does not automatically convert target matter. | Power | — | RM-THEME-008 | Do not infer a matter-conversion damage mechanic from the reactor era alone. |
### Energy / Beam Point Defense

**Identity:** A self-contained local directed-energy interception lineage with its own emitter, tracking and fire control. It is scientifically related to coherent-beam weapons but does not inherit Main-Weapon progression automatically.

**TL1-TL3 reconciliation:** Restores the accepted three-family PDS baseline: TL1 and TL2 use 2 TP readiness and no conventional ammunition; TL3 matures readiness to 1 TP. Existing PDS contracts remain numerical authority.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Baseline beam point defense | base / core_family | `installed_component` | Starting-available local beam interception provides RC1, 2-TP readiness and no conventional ammunition, trading power demand for ammunition independence. | Computing / Fire Control | — | PDS TL1/TL2 contract; Concept 10.8; C-071 | Separate installed PDS component; never attacks ships. |
| 2 | Improved beam tracking and pulse control | existing / maturation | `installed_component` | Accuracy improves while RC1 and 2-TP readiness preserve the high-power identity. | Computing / Fire Control | — | PDS TL1/TL2 contract | No Main-Weapon stat is inherited automatically. |
| 3 | Efficient beam-PDS readiness | existing / maturation | `installed_component` | The accepted TL3 direction lowers readiness to 1 TP while retaining local interception and no conventional ammunition. | Power | — | Concept 8.7; CP101/CP102 | A power-efficiency maturation, not a new PDS introduction. |
| 4 | Rapid-steering beam director | candidate / maturation | `installed_component` | Faster steering or pulse scheduling can improve interception quality without turning PDS into a Main Weapon. | Computing / Fire Control | — | SD-SW-010; IDEA-052 | Finite Reaction Capacity and terminal windows remain. |
| 5 | Multi-threat phased beam defense | candidate / cross_pollinated_derivative | `installed_component` | Distributed apertures and coordination may improve saturation handling within explicit reaction budgets. | Computing / Fire Control; Power | — | SD-SW-010; SD-Q09-006 | Related research is not a gate on the Energy Weapons vertical spine. |
| 6 | Adaptive-spectrum interception | candidate / operating_capability | `installed_component` | A mature beam-defense branch may tune pulse or wavelength behavior against selected small-craft/missile defenses. | Sensors / EW | — | IDEA-052 | Requires explicit target/counter relationship before promotion. |
| 8 | Field-guided defensive lattice | deferred / weird_science | `deferred_concept` | Late field control might extend or reshape a beam-defense envelope while preserving finite attempts and counterplay. | Shields | — | CP106 foundation audit | No perfect shield, infinite interception, or automatic immunity. |
### Charged-Particle / Ion Beam Branch

**Identity:** A strong candidate higher-TL branch that can emphasize armor deposition, electronics/radiation effects and specialist defenses rather than behaving as a renamed laser.

**TL1-TL3 reconciliation:** Current synthesis leans toward Energy/Beam ownership rather than a new visible research category unless gameplay later proves a separate tree worthwhile.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 5 | Ion/charged-particle cannon | candidate / branch | `installed_component` | A ship-scale charged-particle accelerator becomes practical once power, magnetic control and thermal support are sufficiently mature. This is the user-cited “Ion Cannon” class of candidate, but the final Star Cluster name/mechanics remain open. | Power; Armor | — | SD-SW-007; SD-SW-043; TI Particle Beams | — |
| 6 | Neutralized particle beam | candidate / maturation | `installed_component` | Beam conditioning/neutralization improves range/focus and reduces self-dispersion, creating a natural maturation step. | Power; Computing / Fire Control | — | SD-SW-044 | — |
| 7 | Adaptive particle species beam | candidate / operating_capability | `installed_component` | Different particle species/energies could trade material damage, electronics disruption or radiation effects without a universal dose simulator. | Computing / Fire Control | — | SD-SW-043 | — |
| 8 | Relativistic particle lance | deferred / weird_science | `deferred_concept` | Ultra-relativistic beams risk erasing ordinary counterplay; keep as a carefully constrained late candidate rather than automatic progression. | Power | — | SD-SW-046 | — |
### Special Energy / Radiation Weapon Concepts

**Identity:** One-off or rare branches that should be preserved without forcing them into a nine-level sequence.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 4 | Microwave electronic-attack emitter | deferred / one_off | `deferred_concept` | A long-wavelength emitter may be more useful as electronic attack/sensor interference than hull-damage beam. | Sensors / EW | — | SD-EW-005 | — |
| 6 | Plasma cannon | candidate / branch | `installed_component` | Magnetically contained/plasma projectiles are a recognizable higher-SF branch, potentially with strong shield/armor interaction and short effective range. | Power | — | TI Plasma Weapons | — |
| 7 | Nuclear-pumped sacrificial laser | deferred / one_off | `deferred_concept` | A reactor/nuclear-coupled one-shot beam is memorable when it requires preparation and consequences; likely Special Weapon rather than normal Main upgrade. | Power | — | SD-NL-001; RM-THEME-008 | — |
| 7 | Radiation-disruption weapon | deferred / one_off | `deferred_concept` | A specialist attack might threaten crew/electronics or leave contamination, but only after internal/crew mechanics can support it cleanly. | Armor | — | SD-SW-022; SD-SW-024 | — |
| 8 | Matter-bond disruptor | deferred / weird_science | `deferred_concept` | A science-fantasy field/particle weapon that destabilizes material structure. Preserve the concept without committing mechanics or normal-TL placement. | Power | — | RM-THEME-018 | — |
| 10 | Singularity/black-hole gun | exotic / precursor_artifact | `precursor_exception` | A Precursor-scale weapon based on artificial singularities or extreme spacetime manipulation is event technology, not a normal player weapon family. | Power | — | Crane & Westmoreland black-hole starship paper; RM-THEME-008 | — |

## Missile Weapons

### Missile Launcher, Flight and Propulsion

**Identity:** The delivery system creates finite range/endurance, movement and attack-package behavior.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Command-guided missile flight | base / core_family | `installed_component` | Lower-tech missiles depend on ship track/datalink support and use finite onboard fuel/endurance. | Sensors / EW; Computing / Fire Control | — | Concept missile architecture; SD-SW-056 | — |
| 2 | Improved propulsion/endurance package | candidate / maturation | `installed_component` | A delivery improvement can raise tactical reach or sprint behavior without changing guidance/warhead. | Propulsion | — | SD-SW-060 | — |
| 3 | Autonomous navigation-enabled missile | existing / operating_capability | `installed_component` | The accepted TL3 onboard navigation/sensor presence fits qualitative autonomy without weakening Firm terminal requirements. | Sensors / EW | — | Concept missile TL3 | — |
| 4 | Terminal maneuver / multi-stage propulsion | candidate / maturation | `installed_component` | Mature lower-SF missiles trade cruise endurance against terminal sprint/evasion. | Propulsion | — | SD-SW-065 | — |
| 5 | Swarmer Missile / cooperative submunition Flight | candidate / branch | `installed_component` | A distinct Missile Flight family distributes payload across multiple small terminal vehicles/submunitions, trading concentrated packet strength for coverage and a bounded PDS-saturation advantage while remaining one Flight counter and one terminal attack package. | Computing / Fire Control | — | SD-SW-005; SD-SW-059 | Working window TL5-TL7. Ordinary Firm-terminal requirements and generic Missile Flight inventory remain. |
| 6 | High-energy fusion sprint missile | candidate / cross_pollinated_derivative | `installed_component` | Power/Propulsion science creates faster terminal delivery without automatically changing seeker/warhead. | Power; Propulsion | — | RM-THEME-010 | — |
| 7 | Antimatter-catalyzed missile drive | candidate / cross_pollinated_derivative | `installed_component` | Small antimatter quantities produce extreme sprint/endurance at high cost and containment risk. | Power | — | SD-Q10-006 | — |
| 8 | Field-assisted terminal maneuver package | candidate / branch | `installed_component` | A late missile branch uses bounded local field manipulation to improve terminal maneuver/endurance. It remains on-map and must still obey ordinary detection, guidance/track, PDS windows and terminal attack rules. | Shields; Propulsion | — | RM-THEME-006 | No teleporting past geometry, PDS, Firm-terminal requirements, or the missile phase. |
| 9 | Integrated field-coupled strike vehicle | candidate / maturation | `installed_component` | The normal player pinnacle integrates high-energy propulsion, bounded field maneuver and mature guidance into an extreme strike vehicle. It can push delivery performance without becoming an unanswerable micro-jump weapon. | Propulsion | — | SD-Q23-010 | Must remain track-dependent, on-map, interceptable, and subject to ordinary terminal-defense windows. Tactical micro-jump delivery remains deferred. |
### Missile Guidance, Seeker and Counter-Countermeasures

**Identity:** Target acquisition/discrimination can mature independently of propulsion or warhead.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Ship-command guidance / datalink | base / core_family | `automatic_capability` | The launching ship provides Firm-track guidance for basic missiles. | Sensors / EW | — | Concept missile guidance | — |
| 3 | Onboard navigation and local reacquisition | existing / maturation | `automatic_capability` | Missile sensors can perform bounded local track improvement while preserving separate command-guided low-tech behavior. | Sensors / EW | — | Concept missile sensor rules | — |
| 4 | Multi-mode terminal seeker | candidate / maturation | `automatic_capability` | A seeker combines modalities and better countermeasure rejection rather than gaining automatic damage. | Sensors / EW | — | SD-SW-058 | — |
| 5 | Cooperative seeker network | candidate / cross_pollinated_derivative | `automatic_capability` | Missile Flight elements share observations or assign targets while maintaining provenance/finite communications. | Computing / Fire Control | — | RM-THEME-010 | — |
| 6 | Adaptive anti-jam seeker | candidate / maturation | `automatic_capability` | Higher guidance robustness counters EW through better discrimination and onboard autonomy. | Sensors / EW | — | SD-SW-034; SD-SW-058 | — |
| 7 | Anti-emitter seeker mode | candidate / operating_capability | `operating_mode` | A specialist seeker can home on active emissions, creating counterplay to aggressive sensors/ECM. | Sensors / EW | — | SD-SW-012 | — |
| 8 | Exotic-field seeker | candidate / weird_science | `automatic_capability` | Late missiles may track metric/shield/propulsion signatures when ordinary sensors fail. | Sensors / EW | — | SD-Q09-008 | — |
### Missile Warhead Families

**Identity:** The normal Missile payload is a GP warhead that auto-matures with energetic generation. Specialist warhead ideas remain preserved, but the baseline game does not require a standing warhead-selection menu unless later play proves the extra choice worthwhile.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Conventional / fission-era general-purpose warhead | base / core_family | `automatic_capability` | The mature starting missile carries a balanced contemporary GP payload appropriate to the setting’s peak-fission baseline; detailed conventional-versus-fission subtype bookkeeping is abstracted. | Projectile Weapons | — | SD-SW-051 | Automatic baseline using the generic Missile Flight store; exact yield remains a calibration question. |
| 3 | Shaped/advanced penetrator warhead | deferred / branch | `deferred_concept` | Armor-focused shaped/penetrator payloads remain preserved specialist concepts, but CP117 removes them from the assumed normal player-facing menu until a later play need justifies the added choice. | Armor | — | SD-SW-052 | Preserve concept; no standing launch-time warhead selector in the simplified baseline. |
| 4 | Nuclear directed-pulse / shield-disruption warhead | deferred / branch | `deferred_concept` | Directed-pulse/shield-disruption payloads remain preserved specialist concepts. CP116 proved the mechanic can have a niche, but CP117 does not require it in the normal baseline because GP yield plus distinct Missile families are simpler. | Power | — | SD-SW-052; TI shaped-nuclear inspiration | Preserve for later optional branch or scenario technology; not an assumed normal warhead menu. |
| 5 | Fusion microcharge general-purpose warhead | candidate / cross_pollinated_derivative | `automatic_capability` | Practical Fusion knowledge enables a higher-energy contemporary GP payload on compatible high-energy missile bodies. If it is otherwise superior to the older GP warhead, the upgrade is automatic rather than a separate loadout. | Power | Power TL2 | SD-SW-053 | Normal generic Missile Flight inventory; exact numerical improvement awaits calibration. |
| 6 | Radiation/electronics-disruption warhead | deferred / one_off | `deferred_concept` | A specialist radiation/electronics payload may attack crew or internal electronics once those consequences exist in the research consumer. | Sensors / EW | — | SD-SW-054 | Do not use this as the current anti-shield solution; defer until internal critical/subsystem and crew effects are simulated. |
| 7 | Antimatter general-purpose warhead | candidate / cross_pollinated_derivative | `automatic_capability` | Antimatter production/containment enables a higher-energy contemporary GP payload on compatible hardened missile bodies. Tactical subtype bookkeeping remains abstract; strategic resource/hazard identity may matter later. | Power | Power TL5 | CERN Antimatter; SD-Q10-006 | Normal generic Missile Flight inventory once industrially supported; exact numerical improvement awaits calibration. |
| 9 | Matter-conversion warhead | deferred / weird_science | `deferred_concept` | A pinnacle player payload may convert a bounded amount of target/feedstock matter. Require strong defenses/scarcity to avoid universal best-in-slot behavior. | Power | — | Concept TL9 Power | If adopted, treat as individually tracked Exotic ammunition rather than normal generic Missile Flight progression; scarcity and counterplay are mandatory. |
### Local AMM PDS and Extended Interceptor Defense

**Identity:** A TL1 local ammunition-fed PDS lineage plus later optional extended-range defensive interceptors. The local system uses the standard two terminal windows; a long-range AMM layer is a separate future operating envelope.

**TL1-TL3 reconciliation:** TL1 local AMM PDS already exists with RC1, 1-TP readiness and 25-round ammunition. TL2 improves accuracy; TL3 matures readiness/capability per the accepted PDS/TL3 contracts. Long-range interception is not retroactively present at TL1.

| TL | Beat | Status / role | Player expression | Story | Related research | Hard prerequisites | References | Boundary |
|---:|---|---|---|---|---|---|---|---|
| 1 | Baseline local AMM point defense | base / core_family | `installed_component` | Starting-available guided interceptors provide local terminal defense with RC1, 1-TP readiness and a finite 25-round ammunition reserve. | Computing / Fire Control | — | PDS TL1/TL2 contract; Concept 10.8; C-071 | Local terminal PDS only; this is not the later long-range AMM layer. |
| 2 | Improved local AMM guidance | existing / maturation | `installed_component` | Local interceptor accuracy improves while RC1, 1-TP readiness and the 25-round endurance baseline hold. | Computing / Fire Control | — | PDS TL1/TL2 contract | Still uses standard terminal PDS windows. |
| 2 | Extended-range AMM layer | candidate / branch | `installed_component` | A separate guided defensive-missile layer may engage outside the local terminal envelope at an explicit ammunition, tracking, launch-capacity and timing cost. | Sensors / EW | — | SD-SW-039; IDEA-054 | Does not replace or redefine the TL1 local AMM PDS. |
| 3 | Mature AMM readiness | existing / maturation | `installed_component` | The accepted TL3 AMM PDS/readiness concept fits this branch. | Computing / Fire Control | — | Concept TL3 PDS | — |
| 5 | Cooperative AMM screen | candidate / cross_pollinated_derivative | `installed_component` | Networked sensors/launchers coordinate defensive salvos with bounded attempt budgets. | Sensors / EW; Computing / Fire Control | — | SD-SW-039 | — |
| 7 | Hit-to-kill / extreme-sprint AMM | candidate / maturation | `installed_component` | Higher propulsion/guidance improves intercept envelope while maintaining finite reactions and ammunition. | Propulsion | — | SD-SW-065 | — |

## CP113 ammunition / warhead reconciliation

- Normal ammunition subtype inventory bookkeeping: **No**.
- Missile warhead is committed at launch: **Yes**.
- Exotic ammunition may use explicit per-shot counts when scarcity itself is gameplay: **Yes**.
- CP109 payload branch numbers suspended by CP113: kinetic-smart-projectile, missile-shaped-warhead, missile-nuclear-shaped, missile-fusion-warhead, missile-antimatter-warhead.

