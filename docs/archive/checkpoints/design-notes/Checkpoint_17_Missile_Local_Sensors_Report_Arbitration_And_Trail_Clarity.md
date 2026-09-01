# Checkpoint 17 - Missile-Local Sensors, Report Arbitration, and Trail Clarity

## Purpose

Checkpoint 17 gives sensor-equipped missiles their first independent onboard target tracks. A missile now evaluates its own sensor at action start and after every entered hex, compares that local report with the fresh or retained launcher report available to it, and deterministically selects the best source without sharing mutable track state.

The pass also makes the tactical presentation more honest and easier to validate:

- friendly planned missile routes are dashed;
- hostile incoming-threat estimates are dotted and explicitly are not confirmed locks;
- every observer-confirmed trail remains visible, while selection only emphasizes it;
- hidden intervals remain disconnected; and
- an opt-in authoritative development panel exposes selected-missile internal state without weakening the normal observer-safe interface.

Terminal seeker lock and capability-specific terminal attack resolution remain deferred to the next pass.

## Missile-owned local sensor tracks

`MissileSensorProfile` is a data-driven onboard navigation-sensor profile. The Checkpoint 17 development missile uses TL2 Firm range 3, Approximate range 5, and a deterministic Active bonus of +2. It is intentionally inferior to the same-TL ship-sensor concept.

`MissileLocalSensorService` always tries Passive first. It escalates to Active only when:

1. Passive sensing produced no contact;
2. the installed profile allows Active mode; and
3. Active mode has a positive range benefit.

A successful local observation creates a missile-owned report containing target identity, Current/Approximate quality, coordinate, source observation epoch, uncertainty, sensor mode, and age. Local tracks follow the same epoch guardrails used by ship tracks:

- successful observation refreshes immediately;
- same-epoch visibility loss becomes Stale at the most recently observed coordinate without another age step;
- later misses age at most once per observation epoch; and
- the profile expires a local track after its configured maximum age.

Launcher reports and local reports remain separate values with separate provenance.

## Deterministic report arbitration

`MissileGuidanceArbitrator` considers all usable candidates available at a decision point:

- `FreshDatalink`;
- `RetainedDatalink`; and
- `LocalSensor`.

It selects by this stable order:

1. higher guidance quality: Current, then Approximate, then Stale;
2. newer source observation epoch;
3. smaller uncertainty radius; and
4. LocalSensor as the final tie-breaker only when the preceding values are equal.

Every decision preserves the complete candidate set, selected source, selected snapshot, and a human-readable reason. This is report selection, not mathematical uncertainty fusion.

## Per-entered-hex reacquisition and replanning

`MissileAutonomousGuidanceService` resolves one missile action in causal order:

1. consume the action-start datalink update;
2. perform a local sensor observation;
3. arbitrate the available reports;
4. plan from the missile's current coordinate;
5. enter one hex and spend one movement/range point;
6. observe locally again;
7. re-arbitrate and immediately replan if the selected source, quality, or coordinate changed; and
8. repeat while movement and lifetime range remain.

Movement spent before a new observation is never refunded. Lifetime range remains cumulative. Interception is resolved at most once for each entered hex, after the post-entry observation establishes whether that edge became a final approach.

Relevant target movement and Sensor/EW changes can update a missile's local track immediately, but cannot move or attack the missile outside the Missile / Interception phase.

## Observer-safe trail and route presentation

The normal tactical view distinguishes three different concepts:

- **Observed travel history:** solid, subdued segments containing only coordinates the player actually observed. All known segments remain visible; selecting a salvo increases emphasis.
- **Friendly planned route:** dashed, because the player legitimately knows the guidance state of a friendly missile.
- **Hostile incoming-threat estimate:** dotted, because it is an observer-side estimate of how a known hostile contact could threaten the player's ship. It does not prove the missile's actual target estimate, local sensor state, datalink state, or lock.

Losing a missile stops extension of the current trail but does not erase already observed history. Reacquisition starts a new disconnected segment and never draws through an unseen interval.

## Authoritative development diagnostics

The optional **AUTHORITATIVE DEBUG** panel is clearly marked as information unavailable to normal play. For the selected missile it reports:

- actual coordinate and terminal state;
- cumulative range used and maximum range;
- current datalink state;
- retained report quality, coordinate, and age;
- local sensor mode, quality, coordinate, uncertainty, and age;
- selected guidance source, quality, and coordinate;
- arbitration reason; and
- replan count from the most recent action.

The authoritative event journal adds:

- `MissileLocalSensorUpdated`;
- `MissileGuidanceArbitrated`; and
- `MissileGuidanceReplanned`.

These events identify the observation opportunity, candidate reports, selected source, movement already spent, replacement route, and the explicit no-refund result.

## Focused Godot scenario

The **Missile local-sensor occlusion** scenario provides repeatable geometry around the central star. Its focused run should demonstrate:

1. a launcher or retained report begins the action;
2. launcher-to-missile LOS becomes blocked or the launcher report remains stale;
3. the missile enters a hex that permits a local observation;
4. arbitration switches to the better local report;
5. the remaining route replans without restoring movement or lifetime range;
6. hostile threat presentation remains dotted rather than masquerading as a confirmed lock; and
7. observed trail segments remain visible even when the missile is not selected.

The authoritative debug panel may be enabled during this focused development scenario. It must remain off for observer-safe presentation checks.

## Tests

Checkpoint 17 adds twenty engine-independent tests:

- ten report-arbitration and provenance tests; and
- ten local-sensor, epoch-aging, blocked-link, target-movement, per-edge-replanning, and no-refund tests.

Expected complete suite: **490 tests**.

## Deferred work

Checkpoint 17 does not yet implement:

- terminal seeker acquisition or lock;
- seeker field of regard or search patterns;
- capability-specific terminal attack gates;
- communications jamming, relays, spoofing, decoys, or false contacts;
- probabilistic sensor resolution; or
- mathematical fusion of uncertainty regions.

The next substantive checkpoint should add terminal seeker acquisition, lock retention/loss, same-hex search, and capability-specific terminal attack authorization on top of the proven report architecture.
