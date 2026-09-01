# Spacedock Mining Note - Radiators

- **Source ID:** SD-Q15
- **Source:** Spacedock - Radiators
- **URL:** https://www.youtube.com/watch?v=w5fvy1ZcIZk
- **Status:** mined
- **Authority:** reference only; not a Star Cluster rule

## High-value design signals

Thermal management is foundational engineering but should normally remain inside Installation Space and component integration. Retractable/compact thermal systems, action-dependent thermal signature and enabling thermal capability tags are the most useful future candidates; no heat meter is implied.

## Observations

### SD-Q15-001 - Spacecraft must reject waste heat from power, electronics, crew and environment, making thermal management a foundational support requirement.
- **Timestamp:** 1:17-3:10
- **Source idea:** Spacecraft must reject waste heat from power, electronics, crew and environment, making thermal management a foundational support requirement.
- **Relationship:** new_candidate
- **Disposition:** retain_reference
- **Tags:** THERMAL, SHIP_ARCHITECTURE, POWER
- **Assessment:** Useful engineering basis for complete component footprint.

### SD-Q15-002 - Spacecraft thermal-control systems can circulate coolant through heat exchangers and dedicated radiators to move internal waste heat to surfaces optimized for radiation.
- **Timestamp:** 1:17-3:10
- **Source idea:** Spacecraft thermal-control systems can circulate coolant through heat exchangers and dedicated radiators to move internal waste heat to surfaces optimized for radiation.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** THERMAL, INSTALLATION_SPACE, AVOID_EXCESS_SIMULATION
- **Assessment:** Strong support for hiding normal thermal support inside Space and operating characteristics.
### SD-Q15-003 - Hotter/advanced radiators can reduce area and vulnerability but may demand more pumping power, materials capability or engineering complexity.
- **Timestamp:** 3:49-4:27
- **Source idea:** Hotter/advanced radiators can reduce area and vulnerability but may demand more pumping power, materials capability or engineering complexity.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** THERMAL, TACTICAL_POWER, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Useful compactness-power-vulnerability tradeoff.

### SD-Q15-004 - Thermal survivability can be improved through redundancy, protection, tougher construction or retractable radiators, each with costs.
- **Timestamp:** 4:27-4:55
- **Source idea:** Thermal survivability can be improved through redundancy, protection, tougher construction or retractable radiators, each with costs.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** THERMAL, REDUNDANCY, SHIP_ARCHITECTURE
- **Assessment:** Good technology/race differentiation without universal exposed radiator hit locations.

### SD-Q15-005 - Retracting radiators and relying on heat storage creates a temporary operating window before heat must be rejected again.
- **Timestamp:** 4:42-4:55
- **Source idea:** Retracting radiators and relying on heat storage creates a temporary operating window before heat must be rejected again.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** THERMAL, STEALTH, LIMITED_DURATION, SPECIALIZED_COUNTERPLAY
- **Assessment:** High-interest thermal-suppression/protected-operation concept; prefer finite activations/duration/Strain over a heat bar.

### SD-Q15-006 - Radiators deliberately emit thermal photons, and sufficiently high-temperature radiators can become visibly luminous as their emission spectrum shifts.
- **Timestamp:** recurring
- **Source idea:** Radiators deliberately emit thermal photons, and sufficiently high-temperature radiators can become visibly luminous as their emission spectrum shifts.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** THERMAL, STEALTH, EMISSIONS, SENSORS
- **Assessment:** Strong physical basis for qualitative action-dependent signature states.
### SD-Q15-007 - Large radiator structures can be vulnerable in combat, motivating redundancy, protection, harder-to-damage designs or temporary retraction backed by heat storage.
- **Timestamp:** 4:27-4:55
- **Source idea:** Large radiator structures can be vulnerable in combat, motivating redundancy, protection, harder-to-damage designs or temporary retraction backed by heat storage.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** THERMAL, DAMAGE, OVERLOAD, STRAIN
- **Assessment:** Potential effect through overload limits, Strain or reduced output rather than instant reactor explosion.
### SD-Q15-008 - Solid, moving, droplet, membrane, magnetic and plasma radiator concepts provide multiple technological/alien expressions of the same support function.
- **Timestamp:** 5:11-8:56
- **Source idea:** Solid, moving, droplet, membrane, magnetic and plasma radiator concepts provide multiple technological/alien expressions of the same support function.
- **Relationship:** new_candidate
- **Disposition:** retain_reference
- **Tags:** THERMAL, ALIEN_TECH, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Use as race/technology flavor and bounded traits, not separate universal cooling rules.

### SD-Q15-009 - Open-cycle cooling can handle exceptional thermal loads by consuming and discarding coolant rather than maintaining a closed loop.
- **Timestamp:** 8:57-9:20
- **Source idea:** Open-cycle cooling can handle exceptional thermal loads by consuming and discarding coolant rather than maintaining a closed loop.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** THERMAL, LIMITED_RESOURCE, OVERLOAD
- **Assessment:** Possible finite-charge emergency/high-output auxiliary; do not add ordinary Coolant inventory by default.

### SD-Q15-010 - Open-cycle cooling can be combined with closed-cycle radiators, using expendable coolant for unusually demanding thermal loads while radiators handle baseline continuous loads.
- **Timestamp:** recurring
- **Source idea:** Open-cycle cooling can be combined with closed-cycle radiators, using expendable coolant for unusually demanding thermal loads while radiators handle baseline continuous loads.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** THERMAL, COMPONENT_COMPATIBILITY, CROSS_CATEGORY_INTERACTION
- **Assessment:** Strong candidate for capability tags/support components rather than a sprawling research category.
## Candidate discussion queue

- Thermal-suppression/retracted-radiator operating modes.
- Thermal capability as an enabling tag/support system.
- Race-specific thermal architecture as visual/mechanical flavor.

No item in this note is authoritative until an explicit design decision updates the owning Star Cluster authority.
