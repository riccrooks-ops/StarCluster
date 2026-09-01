# Technology Component Table v0.8

**Checkpoint:** 133  
**Status:** revised combat-subsystem candidate baseline; Storyboard reconciliation and balance calibration pending.

The qualitative lineage map remains inherited from v0.7 so no reference-mined technology concept is lost. CP133 deliberately reopens only the selected numerical combat families using `technology_numerical_matrix_v0_6.json`: Hull, Armor, Shields, Kinetic main, Energy main, GP Missile delivery/warhead, and Swarmer. The old Storyboard is not treated as a numerical constraint in this pass; later reconciliation may update its prose to match the internally consistent family progression. Reactor/Space rebalance and most branch numerics are deferred.

The next calibration uses TLx-vs-TLx reference ships with mandatory contemporary Shield + Armor and mainline K/E/GP-Missile/Swarmer weapon sweeps through the accepted CP132 canonical kernel.


The table contains **218 unique entries for 218 unique Storyboard beats**. Native-accepted CP127 established the stabilized pure-TL main-subsystem characteristics; CP128 preserves that exact architecture and numerical content while synchronizing the documentation-only reference to `technology_numerical_matrix_v0_5.json`. Most AUX numerical tuning remains deferred, and the production runtime remains on the accepted CP122 implementation baseline.

| Discipline | Lineage | TL | Technology | Expression | Numerical profile |
|---|---|---:|---|---|---|
| Hull | Cruiser Structural Integration | 1 | Mature aerospace/composite cruiser construction | automatic_architecture | hull TL1 |
| Hull | Cruiser Structural Integration | 2 | Distributed structural monitoring and modular service architecture | automatic_architecture | hull TL2 |
| Hull | Cruiser Structural Integration | 3 | Integrated cruiser architecture | automatic_architecture | hull TL3 |
| Hull | Cruiser Structural Integration | 4 | Nanostructured load-bearing frame | automatic_architecture | hull TL4 |
| Hull | Cruiser Structural Integration | 5 | Atomically engineered structural composites | automatic_architecture | hull TL5 |
| Hull | Cruiser Structural Integration | 6 | Self-monitoring smart lattice | automatic_architecture | hull TL6 |
| Hull | Cruiser Structural Integration | 7 | Active load-distribution structure | automatic_architecture | hull TL7 |
| Hull | Cruiser Structural Integration | 8 | Field-assisted structural support | automatic_architecture | hull TL8 |
| Hull | Cruiser Structural Integration | 9 | Dynamic programmable cruiser architecture | automatic_architecture | hull TL9 |
| Hull | Maintainability and Damage Control | 1 | Expert crew, distributed spares and diagnostic access | automatic_capability | damage_control TL1 |
| Hull | Maintainability and Damage Control | 3 | Predictive diagnostics and better service distribution | automatic_capability | damage_control TL3 |
| Hull | Maintainability and Damage Control | 4 | Remote repair robotics | optional_component | — |
| Hull | Maintainability and Damage Control | 5 | Onboard fabrication-assisted repair | optional_component | — |
| Hull | Maintainability and Damage Control | 6 | Autonomous repair swarm | optional_component | — |
| Hull | Maintainability and Damage Control | 7 | Self-healing structural materials | automatic_capability | damage_control TL7 |
| Hull | Maintainability and Damage Control | 8 | Programmable matter repair patches | optional_component | — |
| Hull | Maintainability and Damage Control | 9 | Autonomous reconstruction architecture | automatic_capability | damage_control TL9 |
| Hull | Habitation and Gravity Architecture | 1 | Spin/acceleration gravity and mature long-duration habitation | supporting_research | — |
| Hull | Habitation and Gravity Architecture | 4 | Compact/stowable gravity habitats | supporting_research | — |
| Hull | Habitation and Gravity Architecture | 6 | Generated local gravity | supporting_research | — |
| Hull | Habitation and Gravity Architecture | 8 | Inertial-comfort field | deferred_concept | — |
| Armor | Passive Armor Materials | 1 | Advanced alloy/ceramic composite armor | automatic_architecture | armor TL1 |
| Armor | Passive Armor Materials | 2 | Toughened ceramic-composite laminate | automatic_architecture | armor TL2 |
| Armor | Passive Armor Materials | 3 | Protected layered composite | automatic_architecture | armor TL3 |
| Armor | Passive Armor Materials | 4 | Nanostructured armor matrix | automatic_architecture | armor TL4 |
| Armor | Passive Armor Materials | 5 | Gradient/diamondoid composite armor | automatic_architecture | armor TL5 |
| Armor | Passive Armor Materials | 6 | Self-healing smart laminate | automatic_architecture | armor TL6 |
| Armor | Passive Armor Materials | 9 | Programmable matter armor | automatic_architecture | armor TL9 |
| Armor | Armor Enhancement Branches | 1 | Ablative outer layer | optional_component | — |
| Armor | Armor Enhancement Branches | 4 | Thermal/radiation hardening package | optional_component | — |
| Armor | Armor Enhancement Branches | 5 | Powered reactive armor | optional_component | — |
| Armor | Armor Enhancement Branches | 7 | Adaptive reactive armor architecture | optional_component | — |
| Armor | Armor Enhancement Branches | 7 | Electromagnetic particle screen | deferred_concept | — |
| Armor | Armor Enhancement Branches | 8 | Field-assisted armor reinforcement | optional_component | — |
| Power | Main Reactor Generation | 1 | Peak Fission | installed_component | reactor TL1 |
| Power | Main Reactor Generation | 2 | Early Practical Fusion | installed_component | reactor TL2 |
| Power | Main Reactor Generation | 3 | Mature Compact Fusion | installed_component | reactor TL3 |
| Power | Main Reactor Generation | 4 | High-Output Fusion | installed_component | reactor TL4 |
| Power | Main Reactor Generation | 5 | Early Antimatter Reactor | installed_component | reactor TL5 |
| Power | Main Reactor Generation | 6 | Mature Antimatter | installed_component | reactor TL6 |
| Power | Main Reactor Generation | 7 | High-Output Antimatter | installed_component | reactor TL7 |
| Power | Main Reactor Generation | 8 | Fractional / Direct Matter-Conversion Reactor | installed_component | reactor TL8 |
| Power | Main Reactor Generation | 9 | Total Matter Conversion | installed_component | reactor TL9 |
| Power | Late Fission Specialist Revival | 5 | Direct-conversion / advanced-containment fission specialist | installed_component | — |
| Power | Late Fission Specialist Revival | 7 | Pinnacle fission expedition/auxiliary reactor | installed_component | — |
| Power | Pulse Storage and Power Conditioning | 1 | High-density battery / pulse capacitor | optional_component | — |
| Power | Pulse Storage and Power Conditioning | 2 | Supercapacitor bank | optional_component | — |
| Power | Pulse Storage and Power Conditioning | 4 | Superconducting magnetic storage | optional_component | — |
| Power | Pulse Storage and Power Conditioning | 6 | Molecular dielectric ultracapacitor | optional_component | — |
| Power | Pulse Storage and Power Conditioning | 8 | Field-energy reservoir | deferred_concept | — |
| Power | Thermal Management and Energy Conversion | 1 | Heat pipes, coolant loops, radiators and phase-change reserves | supporting_research | — |
| Power | Thermal Management and Energy Conversion | 3 | High-temperature compact radiators | supporting_research | — |
| Power | Thermal Management and Energy Conversion | 4 | Droplet/mist radiator architecture | supporting_research | — |
| Power | Thermal Management and Energy Conversion | 5 | Retractable thermal suppression | optional_component | — |
| Power | Thermal Management and Energy Conversion | 6 | Direct energy recovery / advanced heat pumping | supporting_research | — |
| Power | Thermal Management and Energy Conversion | 8 | Entropy-routing field | deferred_concept | — |
| Propulsion | Sublight Propulsion | 1 | High-power electric/plasma cruiser drive | installed_component | stl TL1 |
| Propulsion | Sublight Propulsion | 2 | Pulsed high-energy plasma drive | installed_component | stl TL2 |
| Propulsion | Sublight Propulsion | 3 | Fusion-assisted torch / mature high-energy STL | installed_component | stl TL3 |
| Propulsion | Sublight Propulsion | 4 | Mature fusion torch architecture | installed_component | stl TL4 |
| Propulsion | Sublight Propulsion | 5 | Antimatter-catalyzed fusion drive | installed_component | stl TL5 |
| Propulsion | Sublight Propulsion | 6 | Antimatter plasma drive | installed_component | stl TL6 |
| Propulsion | Sublight Propulsion | 7 | Beam-core / ultra-high-energy propulsion | installed_component | stl TL7 |
| Propulsion | Sublight Propulsion | 8 | Inertial-coupled drive | installed_component | stl TL8 |
| Propulsion | Sublight Propulsion | 9 | Gravitic/metric sublight drive | installed_component | stl TL9 |
| Propulsion | Specialist Sublight Drives | 1 | Solar/nuclear electric endurance drive | installed_component | — |
| Propulsion | Specialist Sublight Drives | 2 | Nuclear thermal sprint drive | installed_component | — |
| Propulsion | Specialist Sublight Drives | 4 | Fission pulse expedition drive | installed_component | — |
| Propulsion | Strategic FTL Drive | 1 | First-generation practical FTL | installed_component | ftl TL1 |
| Propulsion | Strategic FTL Drive | 2 | Stabilized FTL transit | installed_component | ftl TL2 |
| Propulsion | Strategic FTL Drive | 3 | Integrated FTL navigation | installed_component | ftl TL3 |
| Propulsion | Strategic FTL Drive | 4 | High-throughput FTL field | installed_component | ftl TL4 |
| Propulsion | Strategic FTL Drive | 5 | Adaptive transition geometry | installed_component | ftl TL5 |
| Propulsion | Strategic FTL Drive | 6 | Deep-route FTL navigation | installed_component | ftl TL6 |
| Propulsion | Strategic FTL Drive | 7 | Resilient high-energy FTL | installed_component | ftl TL7 |
| Propulsion | Strategic FTL Drive | 8 | Metric-transition FTL | installed_component | ftl TL8 |
| Propulsion | Strategic FTL Drive | 9 | Pinnacle topology-control FTL | installed_component | ftl TL9 |
| Propulsion | Transit Infrastructure and Natural/Artificial Routes | 4 | Mapped natural shortcuts / stable anomalies | infrastructure | — |
| Propulsion | Transit Infrastructure and Natural/Artificial Routes | 7 | Player-built transit anchor | deferred_concept | — |
| Propulsion | Transit Infrastructure and Natural/Artificial Routes | 9 | Limited player-built gate network | deferred_concept | — |
| Propulsion | Transit Infrastructure and Natural/Artificial Routes | 10 | Precursor gate / one-way conduit / impossible shortcut | precursor_exception | — |
| Sensors / EW | Sensor Suite | 1 | Integrated multimodal sensor suite | installed_component | sensor TL1 |
| Sensors / EW | Sensor Suite | 2 | Improved discrimination resistance | installed_component | sensor TL2 |
| Sensors / EW | Sensor Suite | 3 | Dual normal active modes | operating_mode | sensor TL3 |
| Sensors / EW | Sensor Suite | 4 | Multimodal fusion and cooperative apertures | installed_component | sensor TL4 |
| Sensors / EW | Sensor Suite | 5 | Low-probability active sensing / adaptive waveform suite | installed_component | sensor TL5 |
| Sensors / EW | Sensor Suite | 6 | Quantum-limited / precision field sensors | installed_component | sensor TL6 |
| Sensors / EW | Sensor Suite | 7 | Integrated penetrating multimodal sensing | installed_component | sensor TL7 |
| Sensors / EW | Sensor Suite | 8 | Spacetime/FTL-wake sensing | installed_component | sensor TL8 |
| Sensors / EW | Sensor Suite | 9 | Pinnacle multi-domain inference suite | installed_component | sensor TL9 |
| Sensors / EW | Electronic Countermeasures | 1 | Conventional noise/deception ECM | installed_component | ecm TL1 |
| Sensors / EW | Electronic Countermeasures | 2 | High-strength conventional ECM | installed_component | ecm TL2 |
| Sensors / EW | Electronic Countermeasures | 3 | Efficient full-strength ECM | installed_component | ecm TL3 |
| Sensors / EW | Electronic Countermeasures | 4 | Digital deception / false-track synthesis | installed_component | ecm TL4 |
| Sensors / EW | Electronic Countermeasures | 5 | Adaptive cognitive EW | installed_component | ecm TL5 |
| Sensors / EW | Electronic Countermeasures | 6 | Distributed cooperative EW | installed_component | ecm TL6 |
| Sensors / EW | Electronic Countermeasures | 7 | Emitter-targeted electronic attack | installed_component | ecm TL7 |
| Sensors / EW | Electronic Countermeasures | 8 | Field/signature spoofing | installed_component | ecm TL8 |
| Sensors / EW | Electronic Countermeasures | 9 | Pinnacle adaptive cross-spectrum deception | installed_component | ecm TL9 |
| Sensors / EW | Electronic Counter-Countermeasures | 1 | Conventional filtering and emitter analysis | installed_component | eccm TL1 |
| Sensors / EW | Electronic Counter-Countermeasures | 2 | High-strength conventional ECCM | installed_component | eccm TL2 |
| Sensors / EW | Electronic Counter-Countermeasures | 3 | Efficient full-strength ECCM | installed_component | eccm TL3 |
| Sensors / EW | Electronic Counter-Countermeasures | 4 | Sensor-fusion anti-deception | installed_component | eccm TL4 |
| Sensors / EW | Electronic Counter-Countermeasures | 5 | Adaptive classifier / signature memory | installed_component | eccm TL5 |
| Sensors / EW | Electronic Counter-Countermeasures | 6 | Cooperative track validation | installed_component | eccm TL6 |
| Sensors / EW | Electronic Counter-Countermeasures | 7 | Counter-emitter localization | installed_component | eccm TL7 |
| Sensors / EW | Electronic Counter-Countermeasures | 8 | Exotic-channel correlation | installed_component | eccm TL8 |
| Sensors / EW | Electronic Counter-Countermeasures | 9 | Pinnacle provenance-weighted track validation | installed_component | eccm TL9 |
| Sensors / EW | Signature Management and Stealth | 1 | Passive low-observability design | operating_mode | — |
| Sensors / EW | Signature Management and Stealth | 3 | Emission-controlled operating posture | operating_mode | — |
| Sensors / EW | Signature Management and Stealth | 5 | Thermal suppression window | operating_mode | — |
| Sensors / EW | Signature Management and Stealth | 6 | Active signature cancellation | deferred_concept | — |
| Sensors / EW | Signature Management and Stealth | 8 | Powered concealment field | deferred_concept | — |
| Sensors / EW | Signature Management and Stealth | 10 | Precursor phase cloak | precursor_exception | — |
| Computing / Fire Control | Tactical Computer and Fire Control | 1 | Integrated electronic fire control | installed_component | computer TL1 |
| Computing / Fire Control | Tactical Computer and Fire Control | 2 | Refined conventional fire control | installed_component | computer TL2 |
| Computing / Fire Control | Tactical Computer and Fire Control | 3 | Mature integrated fire control / Evasive Compensation | automatic_capability | computer TL3 |
| Computing / Fire Control | Tactical Computer and Fire Control | 4 | Photonic/optical combat computing | installed_component | computer TL4 |
| Computing / Fire Control | Tactical Computer and Fire Control | 5 | Adaptive AI battle manager | installed_component | computer TL5 |
| Computing / Fire Control | Tactical Computer and Fire Control | 6 | Distributed resilient combat cloud | installed_component | computer TL6 |
| Computing / Fire Control | Tactical Computer and Fire Control | 7 | Quantum-assisted optimization | installed_component | computer TL7 |
| Computing / Fire Control | Tactical Computer and Fire Control | 8 | Predictive battle-state synthesis | installed_component | computer TL8 |
| Computing / Fire Control | Tactical Computer and Fire Control | 9 | Pinnacle self-verifying battle synthesis | installed_component | computer TL9 |
| Computing / Fire Control | Autonomy, Networking and Digital Crew | 3 | Advanced ship automation | automatic_capability | — |
| Computing / Fire Control | Autonomy, Networking and Digital Crew | 5 | Autonomous specialist agents | automatic_capability | — |
| Computing / Fire Control | Autonomy, Networking and Digital Crew | 7 | Distributed autonomous mission control | campaign_capability | — |
| Computing / Fire Control | Autonomy, Networking and Digital Crew | 9 | Synthetic crew core | deferred_concept | — |
| Shields | Defensive Field Generator | 1 | Baseline defensive field | installed_component | shield TL1 |
| Shields | Defensive Field Generator | 2 | Higher-capacity field | installed_component | shield TL2 |
| Shields | Defensive Field Generator | 3 | Mature stabilized field generator | installed_component | shield TL3 |
| Shields | Defensive Field Generator | 4 | Segmented/adaptive field geometry | operating_mode | shield TL4 |
| Shields | Defensive Field Generator | 5 | Frequency/phase-tuned shielding | installed_component | shield TL5 |
| Shields | Defensive Field Generator | 6 | Predictive localized reinforcement | installed_component | shield TL6 |
| Shields | Defensive Field Generator | 7 | Stand-off shear field | installed_component | shield TL7 |
| Shields | Defensive Field Generator | 8 | Metric barrier field | installed_component | shield TL8 |
| Shields | Defensive Field Generator | 9 | Pinnacle adaptive barrier | installed_component | shield TL9 |
| Shields | Shield Support and Specialist Fields | 1 | Shield Battery / Booster concepts | optional_component | — |
| Shields | Shield Support and Specialist Fields | 3 | Shield Hardener | optional_component | — |
| Shields | Shield Support and Specialist Fields | 5 | Particle/charged-beam screen | optional_component | — |
| Shields | Shield Support and Specialist Fields | 7 | Field stabilizer / anti-penetration tuner | optional_component | — |
| Shields | Shield Support and Specialist Fields | 10 | Precursor stasis/phase barrier | precursor_exception | — |
| Projectile Weapons | Kinetic Main Weapon | 1 | Mature electromagnetic mass driver | installed_component | kinetic_main TL1 |
| Projectile Weapons | Kinetic Main Weapon | 3 | Power-efficient mature accelerator | installed_component | kinetic_main TL3 |
| Projectile Weapons | Kinetic Main Weapon | 4 | Superconducting coil/induction accelerator | installed_component | kinetic_main TL4 |
| Projectile Weapons | Kinetic Main Weapon | 5 | Helical / continuous-induction cannon branch | installed_component | kinetic_main TL5 |
| Projectile Weapons | Kinetic Main Weapon | 6 | Smart hypervelocity mass driver | installed_component | kinetic_main TL6 |
| Projectile Weapons | Kinetic Main Weapon | 7 | Macron/dust accelerator branch | installed_component | kinetic_main TL7 |
| Projectile Weapons | Kinetic Main Weapon | 8 | Field-assisted mass accelerator | installed_component | kinetic_main TL8 |
| Projectile Weapons | Kinetic Main Weapon | 9 | Relativistic kinetic lance | installed_component | kinetic_main TL9 |
| Projectile Weapons | Kinetic Ammunition and Projectile Packages | 1 | Contemporary general-purpose projectile package | automatic_capability | kinetic_main TL1 |
| Projectile Weapons | Kinetic Ammunition and Projectile Packages | 2 | Improved penetrator/projectile materials | automatic_capability | kinetic_main TL2 |
| Projectile Weapons | Kinetic Ammunition and Projectile Packages | 4 | Maneuvering / programmable smart projectile | automatic_capability | kinetic_main TL4 |
| Projectile Weapons | Kinetic Ammunition and Projectile Packages | 5 | Graded penetrator/material maturation | automatic_capability | kinetic_main TL5 |
| Projectile Weapons | Kinetic Ammunition and Projectile Packages | 6 | Mature smart-projectile correction suite | automatic_capability | kinetic_main TL6 |
| Projectile Weapons | Kinetic Ammunition and Projectile Packages | 8 | Exotic dense-matter projectile | deferred_concept | — |
| Projectile Weapons | Kinetic Point Defense | 1 | Rapid-fire kinetic PDS | installed_component | kinetic_pds TL1 |
| Projectile Weapons | Kinetic Point Defense | 3 | Mature local fire-control / effective-ammo PDS | installed_component | kinetic_pds TL3 |
| Projectile Weapons | Kinetic Point Defense | 4 | Guided intercept projectile PDS | installed_component | kinetic_pds TL4 |
| Projectile Weapons | Kinetic Point Defense | 6 | Distributed kinetic intercept grid | installed_component | kinetic_pds TL6 |
| Energy Weapons | Coherent Beam Main Weapon | 1 | High-energy coherent laser | installed_component | energy_main TL1 |
| Energy Weapons | Coherent Beam Main Weapon | 2 | Improved optics and pulse conditioning | installed_component | energy_main TL2 |
| Energy Weapons | Coherent Beam Main Weapon | 3 | Safe high-output beam mode | installed_component | energy_main TL3 |
| Energy Weapons | Coherent Beam Main Weapon | 4 | Short-wavelength / advanced focusing beam | installed_component | energy_main TL4 |
| Energy Weapons | Coherent Beam Main Weapon | 5 | Tunable-spectrum / free-electron beam branch | installed_component | energy_main TL5 |
| Energy Weapons | Coherent Beam Main Weapon | 6 | Distributed/phased beam director | installed_component | energy_main TL6 |
| Energy Weapons | Coherent Beam Main Weapon | 7 | Extreme-frequency beam branch | installed_component | energy_main TL7 |
| Energy Weapons | Coherent Beam Main Weapon | 8 | Field-guided coherent lance | installed_component | energy_main TL8 |
| Energy Weapons | Coherent Beam Main Weapon | 9 | Pinnacle coherent-energy lance | installed_component | energy_main TL9 |
| Energy Weapons | Energy / Beam Point Defense | 1 | Baseline beam point defense | installed_component | energy_pds TL1 |
| Energy Weapons | Energy / Beam Point Defense | 2 | Improved beam tracking and pulse control | installed_component | energy_pds TL2 |
| Energy Weapons | Energy / Beam Point Defense | 3 | Efficient beam-PDS readiness | installed_component | energy_pds TL3 |
| Energy Weapons | Energy / Beam Point Defense | 4 | Rapid-steering beam director | installed_component | energy_pds TL4 |
| Energy Weapons | Energy / Beam Point Defense | 5 | Multi-threat phased beam defense | installed_component | energy_pds TL5 |
| Energy Weapons | Energy / Beam Point Defense | 6 | Adaptive-spectrum interception | installed_component | energy_pds TL6 |
| Energy Weapons | Energy / Beam Point Defense | 8 | Field-guided defensive lattice | deferred_concept | — |
| Energy Weapons | Charged-Particle / Ion Beam Branch | 5 | Ion/charged-particle cannon | installed_component | — |
| Energy Weapons | Charged-Particle / Ion Beam Branch | 6 | Neutralized particle beam | installed_component | — |
| Energy Weapons | Charged-Particle / Ion Beam Branch | 7 | Adaptive particle species beam | installed_component | — |
| Energy Weapons | Charged-Particle / Ion Beam Branch | 8 | Relativistic particle lance | deferred_concept | — |
| Energy Weapons | Special Energy / Radiation Weapon Concepts | 4 | Microwave electronic-attack emitter | deferred_concept | — |
| Energy Weapons | Special Energy / Radiation Weapon Concepts | 6 | Plasma cannon | installed_component | — |
| Energy Weapons | Special Energy / Radiation Weapon Concepts | 7 | Nuclear-pumped sacrificial laser | deferred_concept | — |
| Energy Weapons | Special Energy / Radiation Weapon Concepts | 7 | Radiation-disruption weapon | deferred_concept | — |
| Energy Weapons | Special Energy / Radiation Weapon Concepts | 8 | Matter-bond disruptor | deferred_concept | — |
| Energy Weapons | Special Energy / Radiation Weapon Concepts | 10 | Singularity/black-hole gun | precursor_exception | — |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 1 | Command-guided missile flight | installed_component | missile_delivery TL1 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 2 | Improved propulsion/endurance package | installed_component | missile_delivery TL2 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 3 | Autonomous navigation-enabled missile | installed_component | missile_delivery TL3 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 4 | Terminal maneuver / multi-stage propulsion | installed_component | missile_delivery TL4 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 6 | High-energy fusion sprint missile | installed_component | missile_delivery TL6 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 7 | Antimatter-catalyzed missile drive | installed_component | missile_delivery TL7 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 8 | Field-assisted terminal maneuver package | installed_component | missile_delivery TL8 |
| Missile Weapons | Missile Launcher, Flight and Propulsion | 9 | Integrated field-coupled strike vehicle | installed_component | missile_delivery TL9 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 1 | Ship-command guidance / datalink | automatic_capability | missile_guidance TL1 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 3 | Onboard navigation and local reacquisition | automatic_capability | missile_guidance TL3 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 4 | Multi-mode terminal seeker | automatic_capability | missile_guidance TL4 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 5 | Cooperative seeker network | automatic_capability | missile_guidance TL5 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 6 | Adaptive anti-jam seeker | automatic_capability | missile_guidance TL6 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 7 | Anti-emitter seeker mode | operating_mode | missile_guidance TL7 |
| Missile Weapons | Missile Guidance, Seeker and Counter-Countermeasures | 8 | Exotic-field seeker | automatic_capability | missile_guidance TL8 |
| Missile Weapons | Missile Warhead Families | 1 | Conventional / fission-era general-purpose warhead | automatic_capability | missile_gp_warhead TL1 |
| Missile Weapons | Missile Warhead Families | 3 | Mature fission general-purpose payload integration | automatic_capability | missile_gp_warhead TL3 |
| Missile Weapons | Missile Warhead Families | 3 | Shaped/advanced penetrator warhead | deferred_concept | — |
| Missile Weapons | Missile Warhead Families | 4 | Nuclear directed-pulse / shield-disruption warhead | deferred_concept | — |
| Missile Weapons | Missile Warhead Families | 5 | Fusion microcharge general-purpose warhead | automatic_capability | missile_gp_warhead TL5 |
| Missile Weapons | Missile Warhead Families | 6 | Radiation/electronics-disruption warhead | deferred_concept | — |
| Missile Weapons | Missile Warhead Families | 7 | Antimatter general-purpose warhead | automatic_capability | missile_gp_warhead TL7 |
| Missile Weapons | Missile Warhead Families | 9 | Matter-conversion warhead | deferred_concept | — |
| Missile Weapons | Swarmer Missile Flight | 2 | Early cluster/submunition Flight | payload_variant | missile_swarmer TL2 |
| Missile Weapons | Swarmer Missile Flight | 3 | Coordinated submunition bus | automatic_capability | missile_swarmer TL3 |
| Missile Weapons | Swarmer Missile Flight | 5 | Cooperative Swarmer Flight | automatic_capability | missile_swarmer TL5 |
| Missile Weapons | Swarmer Missile Flight | 7 | Autonomous distributed Swarmer | automatic_capability | missile_swarmer TL7 |
| Missile Weapons | Local AMM PDS and Extended Interceptor Defense | 1 | Baseline local AMM point defense | installed_component | amm_pds TL1 |
| Missile Weapons | Local AMM PDS and Extended Interceptor Defense | 2 | Improved local AMM guidance | installed_component | amm_pds TL2 |
| Missile Weapons | Local AMM PDS and Extended Interceptor Defense | 2 | Extended-range AMM layer | installed_component | amm_pds TL2 |
| Missile Weapons | Local AMM PDS and Extended Interceptor Defense | 3 | Mature AMM readiness | installed_component | amm_pds TL3 |
| Missile Weapons | Local AMM PDS and Extended Interceptor Defense | 5 | Cooperative AMM screen | installed_component | amm_pds TL5 |
| Missile Weapons | Local AMM PDS and Extended Interceptor Defense | 7 | Hit-to-kill / extreme-sprint AMM | installed_component | amm_pds TL7 |


## CP127 main-subsystem stabilization

- **STL:** standard Move is again enforced as **Drive TL** at every TL.
- **Missile delivery:** Operational Missile Move is again enforced as **Drive TL + 1** at every TL.
- **FTL:** strategic movement remains the deliberate uneven ladder **1, 2, 3, 4, 4, 6, 7, 9, 12**; this is an explicit strategic exception, not a tactical movement rule.
- **TL8 Energy Main:** Low/Standard/High damage becomes **7/10/12** canonical points; accuracy, penetration, range, Space, and Tactical Power are unchanged.
- **TL5→TL6:** retain the broader maturation package. Bounded attribution identifies Sensors plus family-specific weapon improvements as meaningful contributors rather than one accidental scalar.
- **Other main subsystem spines:** retained pending CP127 native confirmation.
- **Auxiliary systems:** most numerical progression remains out of scope and will be tuned in a later phase.
