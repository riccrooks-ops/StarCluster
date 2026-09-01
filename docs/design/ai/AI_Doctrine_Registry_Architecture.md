# Star Cluster AI Doctrine Registry Architecture v0.7

## Purpose

Star Cluster stores reusable tactical behavior as durable doctrine and lessons rather than hard-coding one preferred range or response sequence for a particular technology level. This document is an **AI architecture authority**, not a checkpoint diary. Raw trial counts and checkpoint conclusions belong in evidence artifacts.

The v0.7 architecture preserves the general **Adaptive Engage** encounter model from v0.6 and adds explicit own-capability availability memory. In particular, safe-Strain exhaustion is remembered as an unavailable escalation state rather than treated as another range-dependent overload failure.

## Lifecycle

- **control** - deliberate baseline or stress behavior retained for comparison.
- **experimental** - executable candidate still under evaluation.
- **accepted** - evidence-backed behavior available to current AI.
- **rejected** - behavior retained so a known poor default is not casually rediscovered without a dependency change.
- **superseded** - formerly useful behavior preserved for reproducibility after replacement.

A registry may name one current default doctrine per domain while retaining accepted supporting doctrines.

## Information parity is absolute

AI may use only information available to a player at the same decision window. It may use:

- its own installed and currently functional capabilities;
- its own current Available/uncommitted Tactical Power and Strain state;
- target contact state and track quality legitimately obtained during combat;
- legitimately observed enemy attacks, emissions, movement, and visible missile threats;
- results of its own previous legal actions, including ranges where tracking or overload attempts failed; and
- materially changed observable tactical state.

AI must **not** inspect hidden opponent technology levels, exact ECM/ECCM ratings, undisclosed components, internal Jamming Margin arithmetic, future random outcomes, or precomputed privileged combat results.

Information learned in a later phase cannot retroactively alter an earlier committed decision. A track failure learned after Movement on turn N may influence Movement on turn N+1, not rewrite turn N.

## Encounter state model

The general Engage consumer uses a small encounter state machine rather than beginning every duel with a pre-existing Firm solution:

1. **Initialize / Search.** Ships begin at opposite tactical-map edges. Before contact, each ship follows a neutral search rule that moves one hex toward map center per turn. The search decision receives no hidden target coordinate.
2. **Contact.** Legitimate passive detection, an observed emission, an observed attack, or another legal observation establishes target contact. Detection does not imply a Firm firing solution.
3. **Approach.** If the ship cannot legally attack, it uses its own capabilities plus remembered track outcomes to seek a better geometry.
4. **Engage / Standoff.** If observed combat demonstrates a one-sided engagement envelope, the ship may preserve or open that range rather than blindly close.
5. **Adapt.** Track failure, observed enemy fire, changed emissions, damage, or failed overload attempts update the target-specific combat blackboard and influence later legal decisions.

The state model is capability-driven rather than technology-level scripted. The same Engage policy can operate a low-TL or high-TL ship; installed equipment and observed combat determine the available choices.

## Target-specific combat blackboard

Each AI may retain a target-specific blackboard for the duration of the current combat. This is memory, not omniscience. Useful entries include:

- whether and when contact was established;
- latest observed track quality and range;
- closest range where an ordinary usable Firm solution still failed;
- farthest range from which the ship itself has actually attacked;
- farthest range from which the opponent has actually been observed attacking;
- whether hostile ECM or Active Sensor emissions were observed;
- whether an otherwise Firm observation was visibly degraded during an ECM response window; and
- failed ECCM or Active Sensor overload attempts keyed by target, range, and observable tactical state.

A blackboard may never cache hidden enemy ratings or technology data simply because the simulation engine internally knows them.

## Adaptive Engage movement doctrine

Adaptive Engage follows these durable priorities:

- **Preserve demonstrated asymmetric standoff.** If the ship has actually attacked successfully from a range beyond any range at which the opponent has demonstrated an attack, maintaining that envelope is legitimate tactics when geometry permits.
- **Do not infer enemy reach from weapon family or TL.** An opponent's nominal family range is not player-visible tactical knowledge unless the game later provides identification/intelligence that reveals it.
- **Close after failed Firm acquisition.** If the previous legal attack window produced less than Firm track at range X and the mission is Engage, the next legal Movement decision seeks a closer geometry, potentially all the way to range 0.
- **Use own physical reach, not TL1 presets.** Before enough combat evidence exists to establish a standoff, the AI may use its own installed weapon reach as a bounded approach target. It does not assume Kinetic/Energy/Missile opponent ranges from hard-coded family constants.
- **Respect map and movement limits.** A faster opponent may kite and prevent closure. Failure to close because the opponent successfully opens range is a real tactical outcome, not an AI permission to teleport or use hidden future information.

## EW and overload escalation

Ordinary solutions are exhausted before risky overload:

1. use normal sensing and accepted non-overload EW doctrine;
2. use ordinary movement/closure when better geometry can improve the solution;
3. allow same-hex burn-through to resolve normally when range 0 is reached;
4. if hostile ECM observably degraded an otherwise Firm track and closure is exhausted for the current decision window, try **ECCM overload first** when the ship has a functional ECCM installation, power, and safe Strain headroom;
5. consider **Active Sensor overload later**, only after ordinary movement/closure and narrower ECCM escalation are unavailable, inappropriate, or have failed.

Active Sensor overload remains a sensing-range capability. It does not inherently reduce ECM strength or substitute for ECCM.

### Failed-overload memory

If an overload attempt fails to restore the required track at range X, the AI does not repeat that overload at range X or farther while the observable tactical state is materially unchanged. A closer range is new evidence and may justify another attempt. A materially changed observable state may also justify a retry at the same range, for example:

- hostile ECM emission ceases or begins;
- hostile Active Sensor emissions materially change;
- the ship's own ECCM condition changes; or
- the ship's own Active Sensor condition changes.

The memory rule prevents deterministic thrashing while still allowing rational adaptation.

### Capability-exhaustion memory

Range/state keyed overload failure and own-capability exhaustion are different facts. If a safe overload is unavailable because the subsystem has reached its current safe Strain limit, the blackboard marks that **escalation kind unavailable** for the remainder of the engagement under the current no-in-combat-Strain-recovery rules. Moving closer or observing a changed enemy emission does not restore safe Strain headroom.

A Tactical Power denial remains temporary: the AI may reconsider that overload after a real own-power-state change creates sufficient spendable Tactical Power. If future gameplay introduces in-combat Strain recovery, repair, or another explicit capability-restoration rule, that own-state transition may clear the exhaustion marker.

## Durable opponent-AI lessons

- **Respond to observable conditions rather than hidden causes.** Reactive counters such as ECCM trigger from visible track degradation/emissions and legal local state, not exact hidden enemy ratings.
- **Preserve the combat package, not merely offense.** Tactical Power budgeting must consider ready offense, immediate defensive reactions such as PDS, likely legal response windows, and optional EW/boost opportunity cost.
- **Price optional systems at their actual effective cost.** Affordability decisions use the currently installed/rated system cost, not a TL1/base-cost placeholder.
- **Do not assume every installed subsystem can be powered at once.** Power-constrained legal ships must make choices rather than being pruned as invalid.
- **Fallbacks remain fallbacks.** Degraded fire or overload should not cause the AI to ignore a safer dedicated counter when that counter is legal and strategically preferable.
- **Threat context matters.** Weapon family, visible missile pressure, track quality, geometry, range, current damage state, and resources may legitimately change choices.
- **Equal observable state should be reproducible.** With the same seed, observations, doctrine version, and own-ship state, decisions should remain deterministic enough for regression and explanation.
- **Family identity matters.** Do not reduce all weapons or defenses to a universal scalar when their range, penetration, guidance, power, ammunition, and counterplay differ.

## Current EW behavior

Reactive ECCM remains accepted supporting behavior: activate normal ECCM only when hostile ECM observably degrades an otherwise Firm observation and sufficient uncommitted Tactical Power remains.

The current ECM affordability/default heuristic activates normal ECM only when enough Available Tactical Power remains for the ship's ready offensive package, planned PDS against a present missile threat, and one possible reactive ECCM response. Always-on ECM remains a diagnostic stress/control behavior.

Adaptive Engage's overload order is an additional tactical escalation layer; it does not replace the accepted normal EW doctrine registry.

## Degraded-fire interaction

Degraded direct fire remains architecturally split between weapon permission and Tactical Computer fire-control quality. A compatible weapon/variant must explicitly allow Approximate-track fire; the Tactical Computer supplies the numerical penalty. AI should evaluate degraded fire as a costly fallback and preserve the strategic value of restoring Firm when a dedicated counter is affordable.

## Evidence boundary

The registry can reference evidence provenance and declared dependencies, but this document does not accumulate pass-by-pass trial counts or hashes. Harness-only sensor/EW fixtures used to prove an AI decision path are **not technology candidates** and cannot be promoted merely because they make a validation lane exercise the intended branch.

Revalidation is dependency-driven: rerun an expensive doctrine study when a changed mechanic can plausibly change the decision or when a competing doctrine is deliberately evaluated.
