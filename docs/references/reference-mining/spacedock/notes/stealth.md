# Spacedock Mining Note - Stealth

- **Source ID:** SD-Q12
- **Source:** Spacedock - Stealth
- **URL:** https://www.youtube.com/watch?v=s5xGp5_OMls
- **Status:** mined
- **Authority:** reference only; not a Star Cluster rule

## High-value design signals

Stealth is an information problem rather than binary invisibility. Detection, identification and precise tracking can fail separately, and ship actions can change observability. Thermal suppression and LPI-style integration are high-interest candidates, not adopted rules.

## Observations

### SD-Q12-001 - Stealth is reduced observability and uncertainty, not binary invisibility.
- **Timestamp:** recurring
- **Source idea:** Stealth is reduced observability and uncertainty, not binary invisibility.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** STEALTH, INFORMATION, SENSORS
- **Assessment:** Strong fit for graded observer information.

### SD-Q12-002 - Low observability is sensor-specific; suppressing one signature channel does not automatically defeat every detection method.
- **Timestamp:** recurring
- **Source idea:** Low observability is sensor-specific; suppressing one signature channel does not automatically defeat every detection method.
- **Relationship:** new_candidate
- **Disposition:** retain_reference
- **Tags:** STEALTH, SENSORS, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Avoid one universal stealth number if future mechanics need channel distinctions, but keep player controls simple.

### SD-Q12-003 - Detection, identification and precise tracking are distinct mission-relevant information layers, and stealth can defeat any one of them without making the ship nonexistent.
- **Timestamp:** recurring
- **Source idea:** Detection, identification and precise tracking are distinct mission-relevant information layers, and stealth can defeat any one of them without making the ship nonexistent.
- **Relationship:** corroborates_existing
- **Disposition:** discuss
- **Tags:** STEALTH, TRACK_QUALITY, INFORMATION
- **Assessment:** High-interest support for existing graded track architecture.

### SD-Q12-004 - Thermal and propulsion emissions are difficult to hide; suppressing them tends to be temporary, costly or operationally constraining.
- **Timestamp:** thermal section
- **Source idea:** Thermal and propulsion emissions are difficult to hide; suppressing them tends to be temporary, costly or operationally constraining.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** STEALTH, THERMAL, PROPULSION, SPECIALIZED_COUNTERPLAY
- **Assessment:** Strong candidate for bounded quiet/thermal-suppression behavior, not a heat meter.

### SD-Q12-005 - Ship actions such as hard burns, active sensing and other emissions can change observability over time.
- **Timestamp:** recurring
- **Source idea:** Ship actions such as hard burns, active sensing and other emissions can change observability over time.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** STEALTH, EMISSIONS, ACTIVE_SENSOR, MOVEMENT
- **Assessment:** High-interest action-dependent signature direction.

### SD-Q12-006 - Low-observable design can conflict with the ship's own sensing/emission needs; low-probability-of-intercept and advanced integration can mitigate that trade.
- **Timestamp:** sensor-tradeoff section
- **Source idea:** Low-observable design can conflict with the ship's own sensing/emission needs; low-probability-of-intercept and advanced integration can mitigate that trade.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** STEALTH, SENSORS, CROSS_CATEGORY_INTERACTION
- **Assessment:** Useful high-TL integration idea without guaranteeing perfect stealth.

### SD-Q12-007 - Stealth and electronic warfare can reinforce each other but remain different tools: one reduces observability while the other interferes with information/discrimination.
- **Timestamp:** recurring
- **Source idea:** Stealth and electronic warfare can reinforce each other but remain different tools: one reduces observability while the other interferes with information/discrimination.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** STEALTH, ELECTRONIC_WARFARE, SENSORS
- **Assessment:** Preserve separate subsystem identities.

### SD-Q12-008 - Passive low-observability design and active cloaking are distinct concepts with different costs and failure modes.
- **Timestamp:** cloak discussion
- **Source idea:** Passive low-observability design and active cloaking are distinct concepts with different costs and failure modes.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** STEALTH, CLOAK, EXOTIC_TECH
- **Assessment:** If active cloak ever appears, treat it as a costly special system rather than Stealth +N.

### SD-Q12-009 - All-angle observation in space makes perfect passive concealment difficult, especially for powered craft.
- **Timestamp:** recurring
- **Source idea:** All-angle observation in space makes perfect passive concealment difficult, especially for powered craft.
- **Relationship:** conflicts_or_warns
- **Disposition:** retain_reference
- **Tags:** STEALTH, SENSORS, DESIGN_GUARDRAIL
- **Assessment:** Good guardrail against routine total invisibility.

### SD-Q12-010 - Even suspected presence without exact position/identity can create tactical value, uncertainty and route pressure.
- **Timestamp:** recurring
- **Source idea:** Even suspected presence without exact position/identity can create tactical value, uncertainty and route pressure.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** STEALTH, INFORMATION, TACTICS
- **Assessment:** Supports observer-safe suspected-contact states.

## Candidate discussion queue

- Action-dependent signature states.
- Thermal suppression/quiet operation as a bounded mode.
- Keep stealth, EW and active cloaking distinct.

No item in this note is authoritative until an explicit design decision updates the owning Star Cluster authority.
