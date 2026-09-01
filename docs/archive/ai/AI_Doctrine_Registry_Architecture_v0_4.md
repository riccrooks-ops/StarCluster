# Star Cluster AI Doctrine Registry Architecture v0.4

## Purpose

Star Cluster stores reusable opponent-AI behavior as durable doctrine and lessons rather than rediscovering tactics in each study. This document is an **AI architecture authority**, not a checkpoint diary. Update it only when a reusable information rule, decision principle, doctrine lifecycle rule, or durable tactical lesson changes.

The machine registry may retain evidence/dependency metadata needed for reproducibility, while raw study outcomes remain in study/evidence artifacts.

## Lifecycle

- **control** - deliberate baseline or stress behavior retained for comparison.
- **experimental** - executable candidate still under evaluation.
- **accepted** - evidence-backed behavior available to current AI.
- **rejected** - behavior retained so a known poor default is not casually rediscovered without a dependency change.
- **superseded** - formerly useful behavior preserved for reproducibility after replacement.

A registry may name one current default doctrine per domain while retaining accepted supporting doctrines.

## Information parity

AI may use its own capabilities, current Available/uncommitted Tactical Power, observable track state, legitimately detected emissions, current intended actions, visible missile threats, and other information available to the player at the same decision window. It must not query hidden enemy ECM/ECCM ratings, hidden components, internal Jamming Margin arithmetic, future random outcomes, or other unrevealed authoritative state.

## Durable opponent-AI lessons

- **Respond to observable conditions rather than hidden causes.** Reactive counters such as ECCM should trigger from visible track degradation/emissions and legal local state, not exact hidden enemy ratings.
- **Preserve the combat package, not merely offense.** Tactical Power budgeting must consider ready offense, immediate defensive reactions such as PDS, likely legal response windows, and the opportunity cost of optional EW/boost actions.
- **Do not assume every installed subsystem can be powered at once.** A legal ship may be deliberately power-constrained; AI must allocate the current pool rather than treating overcommitment as an invalid build.
- **Range goals must remain attack-eligible.** Movement doctrine must not choose a preferred physical weapon range that invalidates the ship's current track, guidance, terminal-lock, power, or other attack prerequisites. Leaving a usable attack envelope should require an explicit tactical reason such as withdrawal, search/reacquisition, or a deliberate positional trade.
- **Fallbacks remain fallbacks.** Capabilities such as degraded direct fire may be valuable when Firm restoration is unavailable or too expensive, but should not cause the AI to ignore a dedicated counter such as ECCM when restoration is affordable and strategically preferable.
- **Threat context matters.** Weapon family, visible missile pressure, track quality, geometry, range, current damage state, and available resources may legitimately change doctrine choices.
- **Reserve finite reactions when visible threats justify them.** Spending every reaction/power point on the first available action can be strategically inferior when additional terminal threats are already observable.
- **Equal observable state should be reproducible.** With the same seed, legal observations, doctrine version, and ship state, decisions should remain deterministic enough for regression and explanation.
- **Family identity matters to AI evaluation too.** Do not reduce all weapons or defenses to one scalar score when their penetration, range, guidance, packet, power, and counterplay identities imply different tactical choices.

## Current EW behavior

Reactive ECCM remains accepted supporting behavior: activate only when hostile ECM observably degrades an otherwise Firm observation and sufficient uncommitted Tactical Power remains.

The current TL1 ECM affordability/default heuristic activates normal ECM only when enough Available Tactical Power remains for the ship's ready offensive package, planned PDS against a present missile threat, and one possible reactive ECCM response. Always-on ECM remains a diagnostic stress/control behavior; offense-only headroom is not an appropriate default because it can sacrifice required missile defense.

## Degraded-fire interaction

Degraded direct fire is architecturally split between weapon permission and Tactical Computer fire-control quality. A compatible weapon/variant must explicitly allow Approximate-track fire; the Tactical Computer supplies the numerical penalty. AI should evaluate degraded fire as a costly fallback and preserve the strategic value of restoring Firm when ECCM is affordable.

## Evidence boundary

The registry can reference evidence provenance and declared dependencies so accepted/rejected doctrine is reproducible, but this document does not accumulate trial counts, hashes, or pass-by-pass narratives. Revalidation is dependency-driven: rerun an expensive doctrine study when a changed mechanic can plausibly change the decision or when a competing doctrine is deliberately evaluated.
