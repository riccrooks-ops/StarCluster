# Spacedock Mining Note - Sensors

- **Source ID:** SD-Q09
- **Source:** Spacedock - Sensors
- **URL:** https://www.youtube.com/watch?v=sgbtiGUmZiU
- **Status:** mined
- **Authority:** reference only; not a Star Cluster rule

## High-value design signals

The strongest signals are search-versus-fire-control separation, multimodal/redundant sensing, observable active illumination and cooperative sensing. These fit the existing graded-track and information-parity architecture without adding modality-by-modality controls.

## Observations

### SD-Q09-001 - Passive sensing and active sensing provide different information and emission tradeoffs; even encrypted communications can reveal direction or activity.
- **Timestamp:** 0:45-2:03
- **Source idea:** Passive sensing and active sensing provide different information and emission tradeoffs; even encrypted communications can reveal direction or activity.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** SENSORS, PASSIVE_SENSOR, ACTIVE_SENSOR, EMISSIONS
- **Assessment:** Strong support for separate active/passive behavior and observable emissions.

### SD-Q09-002 - Different sensing modalities specialize in search, range, motion or identification rather than one sensor being best at everything.
- **Timestamp:** 0:45-4:30
- **Source idea:** Different sensing modalities specialize in search, range, motion or identification rather than one sensor being best at everything.
- **Relationship:** new_candidate
- **Disposition:** retain_reference
- **Tags:** SENSORS, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Useful rationale for abstract multimodal suites; do not expose six separate sensor-control panels.

### SD-Q09-003 - Broad search/detection and precision fire-control tracking are distinct sensing tasks with different accuracy requirements.
- **Timestamp:** 2:05-5:20
- **Source idea:** Broad search/detection and precision fire-control tracking are distinct sensing tasks with different accuracy requirements.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** SENSORS, TACTICAL_COMPUTER, TRACK_QUALITY
- **Assessment:** Strong support for search versus Firm weapons-quality track and Sensors versus Computing/Fire Control separation.

### SD-Q09-004 - Redundant or multimodal sensing can preserve useful information when one channel is jammed, obscured or damaged.
- **Timestamp:** recurring
- **Source idea:** Redundant or multimodal sensing can preserve useful information when one channel is jammed, obscured or damaged.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** SENSORS, REDUNDANCY, ELECTRONIC_WARFARE, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** High-interest progression direction without simply raising sensor range.

### SD-Q09-005 - Active fire-control illumination or other active sensing can warn the target that it is being observed or precisely tracked.
- **Timestamp:** 2:05-5:20
- **Source idea:** Active fire-control illumination or other active sensing can warn the target that it is being observed or precisely tracked.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** SENSORS, EMISSIONS, INFORMATION
- **Assessment:** Potential observer-safe warning information without exposing hidden enemy ratings.

### SD-Q09-006 - Phased arrays and advanced processing can combine rapid steering, multiple tracks, communication/datalink and resistance to interference.
- **Timestamp:** recurring
- **Source idea:** Phased arrays and advanced processing can combine rapid steering, multiple tracks, communication/datalink and resistance to interference.
- **Relationship:** extends_candidate
- **Disposition:** discuss
- **Tags:** SENSORS, ELECTRONIC_WARFARE, COMMUNICATIONS, QUALITATIVE_TECH_PROGRESSION
- **Assessment:** Strong integrated-sensor maturation concept; keep player controls simple.

### SD-Q09-007 - Friendly assets can share observations or hand off targeting information, making cooperative sensing a distinct capability from one sensor being stronger.
- **Timestamp:** combat section
- **Source idea:** Friendly assets can share observations or hand off targeting information, making cooperative sensing a distinct capability from one sensor being stronger.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** SENSORS, COOPERATIVE_TRACKING, COMMUNICATIONS
- **Assessment:** High-interest networked-sensing candidate; preserve track provenance and information parity.

### SD-Q09-008 - Exotic high-energy sensing channels can counter some low-observability techniques but require specialized emitters/detectors.
- **Timestamp:** combat section
- **Source idea:** Exotic high-energy sensing channels can counter some low-observability techniques but require specialized emitters/detectors.
- **Relationship:** new_candidate
- **Disposition:** defer
- **Tags:** SENSORS, STEALTH, EXOTIC_TECH
- **Assessment:** Good alien/high-TL candidate, not an ordinary toggle.

### SD-Q09-009 - Advanced sensing can require substantial computation for beam steering, noise filtering, detection tracking, track processing and signature recognition.
- **Timestamp:** recurring
- **Source idea:** Advanced sensing can require substantial computation for beam steering, noise filtering, detection tracking, track processing and signature recognition.
- **Relationship:** corroborates_existing
- **Disposition:** retain_reference
- **Tags:** SENSORS, COMPUTING, CROSS_CATEGORY_INTERACTION
- **Assessment:** Supports sparse causal cross-category requirements.
### SD-Q09-010 - A precise positional/fire-control track need not imply complete identification of target class, equipment or intent.
- **Timestamp:** recurring
- **Source idea:** A precise positional/fire-control track need not imply complete identification of target class, equipment or intent.
- **Relationship:** new_candidate
- **Disposition:** discuss
- **Tags:** SENSORS, INFORMATION, TRACK_QUALITY
- **Assessment:** Useful information-control guardrail: Firm position can remain distinct from intelligence/identification.

## Candidate discussion queue

- Multimodal/redundant sensor progression.
- Cooperative sensing/target handoff with provenance.
- Observer-safe active-illumination warnings and information layers.

No item in this note is authoritative until an explicit design decision updates the owning Star Cluster authority.
