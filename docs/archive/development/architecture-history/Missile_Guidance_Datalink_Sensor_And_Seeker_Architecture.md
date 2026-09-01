# Missile Guidance, Datalink, Sensor, and Seeker Architecture

## Status

This note records the current authoritative missile-guidance architecture. Earlier checkpoints established per-hex movement observation, launcher-to-missile datalink line of sight, copied and aged missile-owned reports, missile-local sensing/arbitration, terminal acquisition, Search/Wait, defensive-interception windows, and reproducible validation. Baseline command-guided missiles require the live launcher command solution; peer terminal authority is an explicit capability rather than an implicit report-source privilege; and a sensor-plus-seeker missile may refine Approximate information only after it owns at least an Approximate missile-local navigation track. Ordinary missile profiles remain Firm-terminal systems unless a future profile explicitly defines a separate Approximate-target attack capability. Later sections retain development history where useful; current-rule sections are authoritative when historical wording differs.

A tactical hex represents a very large volume of space. Entering the same hex as a target establishes proximity, not collision or automatic impact.

## Capability model

A missile may contain three independent optional capabilities:

1. **Launcher datalink receiver** — accepts copies of the launcher's target-track report while launcher-to-missile line of sight exists.
2. **Onboard navigation sensor** — creates and ages a missile-local target track using the same observer-relative sensor model as a ship, but normally with substantially inferior same-TL range, aperture, power, processing, and counter-jamming.
3. **Terminal seeker** — performs co-located terminal acquisition/refinement when the missile architecture relies on seeker acquisition; it does not provide a long-range cruise track.

The Core model must preserve the source and age of every report. It must never let a missile read the target's authoritative coordinate directly.

## Missile capability families

### Command-guided missile

A command-guided missile has a datalink receiver but no onboard sensor or terminal seeker.

- It may launch only while the launcher has a current Firm target track and a live launcher-to-missile datalink.
- It can resolve a hit only while sharing the target's hex, the launcher still has a current Firm target track, and the launcher-to-missile datalink remains live.
- If the datalink breaks or the launcher track degrades after launch, it retains the last delivered Firm command report and may continue to that coordinate, but it cannot independently reacquire or complete an attack.
- A restored live Firm command solution may redirect or authorize it later, subject to remaining range and endurance.

Unguided rockets are not part of the intended space-combat weapon set because their accuracy is inadequate over tactical space distances.

### Seeker-only missile

A seeker-only missile has a datalink receiver and terminal seeker but no general onboard navigation sensor.

- It may launch on a current Firm or Approximate launcher track. A purely Stale launcher report is not sufficient because the missile has no general onboard search sensor.
- The accepted launcher report guides it into the target's estimated hex.
- On arrival, the seeker performs local acquisition first and terminal refinement second.
- A failed local acquisition cannot be followed by a successful terminal lock.
- A failed lock leaves the missile searching or waiting in the hex while endurance remains.

### Sensor-only missile

A sensor-only missile has an onboard navigation sensor but no specialized terminal seeker.

- It can create a local track, continue autonomously after datalink loss, and replan from local observations.
- A local Approximate track is sufficient for navigation.
- A local Firm track is required to attempt the final attack.
- Its final accuracy will normally be worse than a seeker-equipped weapon; exact accuracy and damage rules are deferred to missile-family balance.

### Sensor-plus-seeker missile

A sensor-plus-seeker missile maintains launcher and onboard tracks separately.

- The best usable report controls navigation.
- A legitimate live Firm launcher report or Current/Firm missile-local navigation report can already supply the Firm terminal solution.
- If the missile must improve an Approximate solution, it may attempt seeker refinement only after it shares the target's hex and possesses at least a local Approximate navigation track.
- A local Firm track should provide a stronger terminal solution than a local Approximate track.
- A successful Firm terminal solution, whether already legitimate or obtained through seeker refinement, permits the final defensive-interception window and attack resolution.


## Launch eligibility by installed capability

| Missile capability | Minimum launcher information at launch |
|---|---|
| Command-guided; no onboard sensor or seeker | Current Firm launcher track and live launcher-to-missile datalink |
| Seeker-only | Current Firm or Approximate launcher track |
| Sensor-only | Firm, Approximate, or a data-defined usable Stale report |
| Sensor plus seeker | Firm, Approximate, or a data-defined usable Stale report |

A usable Stale report must satisfy an explicit maximum age or uncertainty rule. Sensor-equipped missiles may accept that risk because they can search and reacquire locally; missiles without a navigation sensor may not. A missile profile may impose a stricter minimum than the family default.

## Track arbitration and later fusion

The first implementation should use deterministic **track arbitration**, not mathematical fusion:

1. Higher quality wins: Firm, then Approximate, then Stale.
2. At equal quality, the fresher observation wins.
3. At equal quality and freshness, the smaller uncertainty region wins.
4. At an exact tie, prefer the missile-local report because it reflects local geometry.

The selected guidance solution retains its source provenance. A later computing or missile-technology pass may combine independent reports into a smaller uncertainty region, but must account for correlated reports rather than assuming every input is independent.

## Datalink rules

Launcher-to-target sensor line of sight and launcher-to-missile datalink line of sight are separate geometric relationships.

- A planet may block the datalink even while the launcher still sees the target.
- The launcher may retain a link to the missile while its own target track becomes Stale.
- A live link copies the launcher report into missile-owned state; the missile never reads a shared live track.
- When blocked, unavailable, or live without a usable launcher coordinate, no new report is delivered. The missile retains and ages its last copy.
- A retained Current or Approximate copy becomes Stale after the first missed guidance-phase delivery. The copied coordinate does not change merely because the launcher later acquires a different coordinate while the link is blocked.
- Retained age advances at most once per missile guidance phase. Additional same-phase line-of-sight checks cannot accelerate aging.
- The missile profile defines the maximum usable retained-report age. Once exceeded, the report remains available only for diagnostics and produces Lost guidance with no coordinate.
- When line of sight returns and the launcher has a usable report, a new copy replaces the retained report and resets age to zero.
- Report delivery occurs at the start of one missile action and link state is refreshed after movement. A link restored during movement is therefore visible immediately in diagnostics but delivers its next report at the following missile action; no movement or lifetime range is refunded.
- The current development profile retains reports for three missed guidance phases. Final TL-specific values remain balance data.
- Communications jamming, relays, cooperative guidance, latency, and bandwidth remain deferred.

## Missile sensor characteristics

Missile sensors use the common sensor-evaluation context but their data-driven profiles are normally inferior to ship sensors of the same TL because of size, aperture, power, cooling, processing, and field-of-regard constraints.

A terminal seeker may nevertheless be highly effective at short range because it is optimized for one target and one terminal task. Sensor and seeker performance must therefore be separate profile data rather than a fixed percentage of ship sensor range.

## Sensor-mode switching

The initial switching policy should be deterministic and replaceable.

- Launch and cruise in Passive mode when a current Firm datalink or local track is available.
- Continue passively toward an Approximate or Stale search coordinate while that area lies outside useful active-sensor range.
- Activate when the best track is Approximate, Stale, or lost and the expected search area enters active-sensor range.
- Activate when the datalink breaks and the expected target area is already within useful range.
- Activate for terminal acquisition when the missile reaches the target or search hex without a sufficient local track.
- Once active, remain active until terminal lock, search/endurance exhaustion, or loss of any plausible search area; this prevents mode oscillation.

Active missile sensing increases missile emissions and should eventually make the missile easier for the target's sensors and defenses to detect.

## Movement-event observation timing

Every authoritative movement path is resolved one entered hex at a time, even when the player selects a distant destination. The movement foundation performs a Track Update after every entered ship hex.

If the launcher observes one or more intermediate ship positions before the target crosses behind a planet, the first blocked step makes the launcher track Stale at the most recent intermediate coordinate actually observed. Same-epoch visibility loss changes quality immediately but does not consume a second tactical-time aging step. This allows later missiles to begin following the target around a body when track geometry remains favorable, or to head toward the true last-seen intermediate coordinate when contact is lost.

A missile with an onboard sensor receives one local observation opportunity:

- at the start of its missile action;
- after each hex the missile enters while the target lies within useful sensor range;
- after each hex the target ship enters while the missile is within useful observation geometry;
- when the target ship enters the missile's hex;
- when the target ship leaves the missile's hex; and
- once per later missile phase while the missile is waiting or searching.

Target entry and departure are distinct movement-edge events. Each permits at most one observation attempt per missile-target edge. A successful result may refresh or improve the missile-local track immediately. A miss does not repeatedly age the same track within one observation epoch.

Observation during the ship's Movement phase does not let the missile move or attack out of phase. The improved track is consumed when the Missile / Interception phase arrives.

## Guidance and replanning sequence

For one missile action:

1. Deliver any legal datalink report.
2. Evaluate the missile's local sensor from its current hex.
3. Arbitrate the best guidance report.
4. Plan toward the Firm coordinate, Approximate estimated center, or Stale last-known coordinate.
5. Enter one hex and spend movement and lifetime range.
6. Reevaluate the local sensor.
7. If the track improves, replan the remaining movement from the new coordinate.
8. Resolve eligible defensive interception.
9. Repeat until movement allowance is spent, the missile waits, or a terminal condition occurs.

Replanning never restores movement allowance, cumulative distance, maximum range, or endurance.

## Same-hex terminal rules

Same-hex occupancy creates a terminal opportunity but is not sufficient for impact. The authoritative order is terminal-entry PDS, terminal acquisition, pre-attack PDS, and then at most one terminal attack roll. Standard PDS is terminal defense and does not react during ordinary Transit or Stationary opportunities. Its two possible reactions are the `TerminalEntry` window and, only after Firm acquisition, the `PreTerminalAttack` window. Held main weapons are deliberate Transit/Stationary interceptors and do not participate in either terminal window.

- A command-guided missile requires a legitimate live Current/Firm remote report and link because it has no local navigation source.
- A sensor-equipped missile may use a live Current/Firm launcher datalink or its own Current/Firm local navigation report. A Current/Firm peer report may authorize terminal attack only when the missile profile explicitly enables cooperative peer terminal guidance; merely receiving a peer report does not grant that capability.
- A seeker-only missile may use a Current/Firm or Approximate remote cue to reach the target hex, but its co-located seeker must perform its own local acquisition before attack. This is a distinct architecture because it has no general onboard navigation sensor.
- A sensor-plus-seeker missile may attack from an already legitimate live Firm launcher report or Current/Firm local navigation report. If it needs the seeker to improve an Approximate solution, it must first possess at least an Approximate missile-local navigation track; a remote Approximate cue alone cannot be refined directly into terminal Firm.
- A seekerless autonomous missile may attack from a legitimate Current/Firm local report.
- Baseline command-guided missiles do not accept peer guidance as a substitute for the required live launcher command link. Cooperative terminal guidance remains an explicit profile capability for later technology.
- Retained Stale or Lost information may support cruise/search behavior but cannot authorize a terminal attack.
- The seeker supplies terminal acquisition ECCM and may supply a separate accuracy bonus. It does not maintain a second cruise track or replace the Guidance Computer.

### Future missile-specific Approximate-terminal capability

The direct-fire Approximate-Track Fire / Volume Fire trait does **not** apply to missiles. Ordinary missile profiles continue to require the legitimate Firm terminal solution defined above.

A later missile profile may explicitly override that baseline with a purpose-built **Approximate-target capability**, but CP117 deliberately separates that idea from the baseline Swarmer Missile branch. The Swarmer is first a Firm-terminal Flight-family concept built around submunition coverage and PDS saturation. A future volume-barrage missile may expend a deliberately large barrage into an estimated target volume without ordinary Firm terminal quality, but that would require its own data-driven acquisition/search/ammunition/effectiveness costs. Approximate-target capability is not automatically granted by the Swarmer name, missile family, seeker installation, or the direct-fire degraded-fire trait.

This remains a future design path only. No current production missile receives an Approximate-target terminal attack, and the ordinary terminal guardrails above remain unchanged.

A failed acquisition enters Search/Wait. Arrival itself spends no additional stationary-search fuel; each later stationary search activation consumes one whole fuel unit. A better report may resume cruise, a new Firm solution may proceed immediately to the pre-attack PDS window and attack, and zero remaining fuel causes safe self-destruction.

## Overshoot and evasion

A fast ship may deliberately pass a missile, break the link or track, and move outside the missile's useful search range before the missile acts.

The missile then follows its best Approximate or Stale report to the old search coordinate. If passive and active attempts fail because the target is now out of range, the missile waits or searches there. This overshoot-and-reacquisition tactic is legitimate emergent counterplay, not a pathing defect.

The ship cannot pass through the missile's observation envelope without evaluation merely because the phase order resolves ship movement first. Intermediate ship hexes, including entry into and departure from the missile's hex, trigger the observation opportunities defined above.

## Hybrid ship-movement interface dependency

The final Movement interface supports both:

- one-hex manual steps; and
- selection of any legal destination within the remaining movement allowance.

After a manual step, the legal destination set is recomputed from the new coordinate and reduced allowance. A later distant selection may spend the remaining allowance automatically. The proposed route is previewed before commitment, and every intermediate hex still resolves authoritatively.

Automatic-route movement pauses when a previously Unknown hostile missile becomes visible before the selected destination is reached. Executed steps are not rewound after revealing information. More general interruption policies may later cover other materially changed threats.

## State dimensions

Avoid one combinatorial missile-state enum. Preserve separate dimensions:

- datalink: unavailable, live, or blocked;
- sensor mode: passive or active;
- launcher report: quality, coordinate, uncertainty, age, and source epoch;
- onboard track: quality, coordinate, uncertainty, age, and source epoch;
- selected guidance source;
- terminal state: none, opportunity, Search/Wait, Firm solution, or resolved;
- flight state: in flight, waiting for route/track, searching, expended, dud, intercepted, range exhausted, self-destructed, or destroyed.

## Diagnostics

The current journal records one `MissileDatalinkUpdated` event at action start and one state-only event after movement. The action-start event identifies delivery, retention, aging, expiration, launcher track quality, copied coordinate, source epoch, effective quality, and guidance provenance. The action-end event records the final launcher-to-missile geometry without delivering or aging another report.

The authoritative journal should record:

- datalink LOS and report delivery or interruption;
- launcher-report and onboard-track qualities separately;
- guidance-source arbitration and source changes;
- passive/active mode transitions and reasons;
- every permitted entry, departure, and per-hex observation attempt;
- route replans without range reset;
- same-hex local-track gate;
- terminal-seeker acquisition and lock outcome;
- waiting/searching reason and endurance consumption.

Player-visible summaries remain observer-safe and must not reveal hidden missile tracks, failed hidden attempts, or authoritative target coordinates. Friendly route projections use the missile's own last guidance report rather than silently substituting the player ship's newer target track. Enemy datalink state remains absent from normal player-facing summaries.

## Deferred balance and advanced behavior

- TL 0-9 component availability and performance;
- missile size, cost, payload, propulsion, and component tradeoffs;
- exact sensor-only accuracy penalty and seeker bonuses;
- probabilistic detection and terminal lock;
- search patterns, facing, seeker cones, and maneuverability;
- communication jamming, relays, bandwidth, and latency;
- false contacts, spoofing, decoys, target discrimination, and cooperative attacks;
- final fuel versus distance/endurance balance and richer search patterns.

## Historical implementation and validation notes

The sections below preserve implementation chronology and accepted evidence. They are retained for reproducibility and context; when wording differs, the current-rule sections above and the active Concept control.

## Checkpoint 17 implemented local-sensor and arbitration layer

Checkpoint 17 implements the onboard navigation-sensor foundation described above.

- Every sensor-equipped missile owns a separate `MissileLocalTrackReport`.
- Passive observation is always attempted first; deterministic Active escalation occurs only after a Passive miss and only when the profile permits a useful Active bonus.
- Action-start and every entered missile hex are local observation opportunities.
- Relevant target movement and Sensor/EW changes refresh local tracks without moving or attacking the missile out of phase.
- Fresh launcher, retained launcher, and local reports are immutable candidates with preserved provenance.
- Arbitration is quality, then recency, then lower uncertainty, then LocalSensor as an exact-tie winner.
- A better post-entry report causes immediate route replanning with no movement or lifetime-range refund.
- Interception remains limited to one resolution per entered edge after post-entry sensing determines whether that edge became a final approach.

Presentation now distinguishes known history from prediction. Observer-confirmed travel is drawn as solid disconnected segments; friendly planned routes are dashed; hostile incoming-threat estimates are dotted and do not assert a confirmed enemy guidance lock. All known trail segments remain visible, while selection only emphasizes one salvo.

An opt-in authoritative development panel and dedicated journal events expose candidate reports and decisions for regression work. These diagnostics are not normal player knowledge and do not alter the observer-safe snapshot.

Checkpoint 18 implements the first terminal seeker, acquisition, Search/Wait, and capability-specific terminal attack layer described below.


## Checkpoint 17a diagnostic ordering contract

The authoritative simulation may resolve an action before the Godot journal formats it, but the emitted evidence must reconstruct the same causal order: action-start link, action-start local observation, initial arbitration, guidance start, one entered-edge event, post-entry local observation, arbitration, optional no-refund replan, edge interception, aggregate movement, and completion. Every local-observation event carries the missile coordinate for that exact opportunity. Observer movement can begin or close a visible trail segment without moving the missile, and those transitions receive explicit segment lifecycle events. This is a diagnostic and presentation contract; it does not change missile guidance authority.


## Checkpoint 17b terminology and validation hotfix

Concept v0.3s uses **Missile Flight** for one tactical counter representing one missile or a small coordinated cluster resolved as one guidance, fuel/range, terminal-attack, and warhead package. The existing `GuidedMissileSalvo` implementation name remains a code-level term until a later refactor is justified.

Checkpoint 17b does not implement terminal seeker rules. It adds a dedicated **Friendly missile route validation** fixture and improves the development-only AUTHORITATIVE DEBUG region with a usable minimum height and automatic scrolling to selected-missile details. The next substantive layer should require a Current/Firm terminal solution for every missile attack and treat a terminal seeker as an optional co-located ECCM and accuracy aid rather than a separate long-range track or mandatory lock state.


## Checkpoint 17c player-owned Missile Flight presentation

Checkpoint 17c changes presentation only; it does not alter authoritative guidance or observer-safe state. A friendly Missile Flight is treated as a player-owned unit. Its exact own-unit status may be shown in the selected panel and hover summary, but its dashed current plan and solid observed history are drawn only while that Flight is selected. The normal view no longer draws `VisibleLastExecutedRoute` as a faint solid future line. Hostile dotted projections remain observer-side threat estimates rather than enemy guidance truth.

The development-only **AUTHORITATIVE DEBUG** toggle is moved above the detail pane, the default viewport increases to 1440x900, and the detail region receives a 280-pixel minimum. These changes support validation without weakening the information boundary.


## Checkpoint 18 implemented terminal contract

Checkpoint 18 makes terminal processing authoritative in the engine-independent Core.

- Reaching the actual target hex creates `MissileTerminalState.Opportunity`; it does not create an impact.
- Standard PDS receives one `TerminalEntry` opportunity per defending ship and Flight. If Firm is later obtained, it receives one separate `PreTerminalAttack` opportunity.
- `MissileTerminalResolutionService` accepts legitimate Current/Firm information from FreshDatalink or LocalSensor according to installed capability and live-link state. `PeerGuidance` may supply terminal Firm authority only when the missile profile explicitly enables that cooperative capability; baseline command-guided missiles cannot substitute a peer report for their required live launcher command link.
- A seeker-only architecture may perform its co-located local acquisition from the eligible Current/Firm or Approximate remote cue that brought it into the target hex. A sensor-plus-seeker architecture is stricter: its seeker may refine an Approximate cue only after the missile already has at least an Approximate missile-local navigation track. Remote Approximate guidance by itself cannot jump directly to terminal Firm for that architecture.
- The Guidance Computer supplies bounded hit probability. An installed seeker may add accuracy only after Firm exists.
- Natural 01 produces a dud; natural 100 records a critical hit; ordinary failure is an ineffective detonation; ordinary success is a hit.
- Failed acquisition enters Search/Wait without an arrival surcharge. Later stationary search activations spend one whole fuel unit and may attack immediately after reacquisition.
- Entry interception, pre-attack interception, acquisition failure, dud, miss, hit, critical hit, and self-destruction remain distinct diagnostic outcomes.
- `PeerGuidance` is an explicit source seam only. Production peer-link delivery, relays, and cooperative arbitration remain deferred.

The Godot prototype uses seeded terminal randomness, observer-safe resolution cues, and a development-only detailed panel. Final component TL values and balance are intentionally provisional.

## Checkpoint 18b deterministic validation host

Checkpoint 18b validates this architecture through `StarCluster.ScenarioRunner` rather than requiring the Godot client to expose every internal state. `ScenarioInitializationService` constructs the authoritative map, ships, prior intelligence, tracks, and optional pre-existing Missile Flights before scripted actions begin. The runner then calls the same Core movement, sensing, datalink, guidance, interception, terminal, and fuel services used by a game host.

The versioned scenario schema and deterministic random-source queues are intentionally reusable by future Monte Carlo parameter sweeps. They are validation and balance infrastructure, not alternate gameplay rules.


## Checkpoint 18c initialization and interception correction

Checkpoint 18c makes the defense-window separation explicit in Core: held direct-fire weapons are eligible only during `Transit` and `Stationary`, while standard PDS is eligible only during `TerminalEntry` and `PreTerminalAttack`. Scenario initialization also restores each pre-existing Missile Flight's guidance-phase counter to at least the received phase recorded by any retained datalink report before scripted execution begins.

## Checkpoint 18d scenario preflight and corpus correction

Checkpoint 18d changes no missile mechanics. The headless host now preflights every selected scenario through the shared document mapper before any scenario executes, with explicit adjacency diagnostics for pre-existing Missile Flight travel history. Ordered-event assertion failures report matched and available event indexes. The corrected deterministic corpus uses only physically adjacent seeded histories and authoritative per-entered-hex movement/event ordering.


## Checkpoint 19 reproducible stochastic validation boundary

Checkpoint 19 extends `StarCluster.ScenarioRunner` without adding a parallel
combat implementation. Deterministic scenarios, Monte Carlo trials, and
parameter sweeps all construct authoritative state through
`ScenarioInitializationService` and execute the same movement, sensing,
datalink, guidance, interception, terminal, and fuel services used by a game
host.

The stochastic host derives one stable seed per trial and separate stream seeds
for interception and terminal resolution. Trial identity is independent of
worker scheduling, so canonical aggregates must be identical at one or many
workers and after resume. Output identity includes the materialized scenario,
runner assembly, Core assembly, master seed, and variant.

Parameter sweeps apply explicit typed overrides to one base scenario rather than
copying complete fixtures. The initial `interceptionChancePercent` field is a
simulation-harness seam used to validate probability and aggregation behavior;
it is not the final PDS/TL formula.

Checkpoint 19 aggregates exactly one primary Missile Flight per trial. Before
fleet or volley studies are authorized, multi-flight aggregation must define
whether statistics are per launched package, per target, per defending ship,
per engagement, or some combination, and must avoid silently selecting one
Flight from a mixed result.

Godot is no longer the primary host for hidden mechanical validation. It remains
responsible for player input, rendering, observer-safe visibility, and
presentation smoke tests. Mechanical and balance evidence belongs in unit
tests, deterministic scenarios, and reproducible statistical studies.


## Checkpoint 20 provisional technology calibration

Checkpoint 20 uses the shared Core terminal contract to compare four representative capability packages: command-guided, seeker-only, sensor-only, and sensor plus seeker. A versioned runner catalog supplies explicit provisional TL 1-9 component values; it does not introduce a universal ship-TL bonus or promote those numbers to final game rules.

The first controlled matrix holds launcher cue availability open and varies matched Missile Flight TL, standard PDS TL, and target terminal-ECM TL at 2, 4, and 6. Analytical and observed per-launch probabilities are compared for TerminalEntry interception, acquisition, PreTerminalAttack interception, attack resolution, and effective hit. Detection-range, pursuit, mixed-component-TL, capacity saturation, tactical power, ammunition, and damage studies remain separate later layers.

## Checkpoint 21 full-flight calibration boundary

Checkpoint 21 exercises the existing guidance architecture across multi-turn
moving-target pursuits in `StarCluster.ScenarioRunner`. Each turn updates the
target first, then executes one authoritative missile action. The runner does
not calculate a shortcut intercept point or replace the Core route planner; it
records the resulting guidance source, route replans, entered-hex movement,
range/fuel use, search state, and terminal result.

Live-link controls are placed away from the star. Occluded variants use a small
planet screen between launcher and Missile Flight while leaving the missile and
target on the autonomous-sensor side of the screen. This isolates launcher-link
loss from missile-local line of sight and allows retained-report aging and local
reacquisition to appear naturally.

The resulting probabilities are per launched Missile Flight. They are not
conditional on reaching the target hex. The provisional speed/range values and
target movement allowances remain calibration data until the pursuit results
are reviewed.

## Checkpoint 21a full-flight opportunity and pursuit evidence

A terminal opportunity can arise because the Missile Flight enters the target
hex, the target enters the Flight's hex before its action, the action begins
co-located, or a co-located Flight performs a later Search/Wait retry. The
headless host records the source explicitly and emits the corresponding
`MissileTerminalOpportunity` diagnostic before terminal-entry PDS. This is an
instrumentation contract around the existing Core terminal sequence, not a new
attack path.

The full-flight movement corpus uses stationary, straight-retreat,
crossing-weave, and explicit turnback fixtures. Crossing-weave replaces a prior
nominal lateral path that was geometrically equivalent to retreat from the
selected starting bearing. Target movement still resolves before missile
movement, and the Core route planner recomputes the path after each target
movement.


## Candidate-coordinate Search/Wait diagnostics

Reaching a guidance report coordinate does not itself create a terminal
opportunity. If the actual target is not co-located, Core may return an
`AcquisitionFailed` result and place the Missile Flight in Search/Wait. The
runner records this as `MissileSearchActivated` with a
`CandidateCoordinateReached` trigger. `MissileTerminalAcquisitionResolved` is
reserved for actual co-location.

Occluded-datalink evidence is behavioral. An occluded Flight cannot use fresh
datalink guidance; any attempted update must report Blocked rather than Live.
No Blocked event is required when a target enters the missile hex or another
terminal outcome resolves before the first guidance update.

Stationary and straight-retreat trajectories support directional datalink
comparisons. Crossing-weave and turnback are descriptive relative-motion cases:
a stale course can accidentally intersect a later target path while direct
current-position pursuit consumes finite range. This is geometry of motion, not
facing, firing arcs, or directional defense.
