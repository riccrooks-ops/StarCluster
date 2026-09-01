# Star Cluster AI Doctrine Registry Architecture v0.2

## Purpose

Star Cluster treats competent tactical behavior as versioned doctrine rather than one-off calibration code. Accepted doctrine records evidence provenance, declared dependencies, revalidation triggers, and player-information limits so unrelated checkpoints can rely on cheap deterministic regression instead of rerunning historical Monte Carlo.

## Lifecycle

- **control**: deliberate baseline or stress behavior retained for comparison.
- **experimental**: executable candidate still under evaluation.
- **accepted**: evidence-backed behavior available to current AI.
- **rejected**: tested behavior retained specifically so the project does not rediscover and retest a known poor default without a dependency change.
- **superseded**: formerly useful behavior retained for reproducibility after replacement.

The registry may name one current default doctrine per domain. Accepted supporting doctrines can remain separately recorded even when a newer composite doctrine is the operational default.

## Information parity

Doctrine may use own capabilities, current Available/uncommitted Tactical Power, observable track state, legitimately detected emissions, current intended actions, visible missile threats, and other information available to the player at that decision window. It must not query hidden enemy ECM/ECCM ratings, hidden components, the internal Jamming Margin, or future random outcomes.

## Evidence and revalidation

Every accepted or rejected conclusion points to a hash-pinned evidence record and declared dependencies. Expensive historical studies are rerun only when a declared dependency changes or when deliberately evaluating a competing doctrine. Normal unrelated checkpoints run deterministic behavior tests instead.

## Current accepted TL1 EW doctrine

`tl1-ew-reactive-eccm-v1` remains accepted supporting behavior: respond with ECCM only when hostile ECM observably degrades an otherwise Firm track and enough uncommitted TP remains.

`tl1-ew-preserve-combat-package-v1` is the current TL1 EW default. Normal ECM is activated only when the ship can still fund its ready offensive package, planned PDS against a present missile threat, and one possible reactive ECCM response. Its accepted evidence shows that this preserves PDS in Energy-vs-Missile while still allowing ECM when affordable.

`tl1-ew-always-ecm-reactive-eccm-v1` remains a control/stress policy, not a default. `tl1-ew-preserve-offense-v1` is explicitly rejected as a default because it fails to reserve PDS headroom against missile threats.

## Current degraded-fire interaction

Degraded direct fire is now architecturally split between **weapon permission** and **Tactical Computer fire-control quality**. A specific weapon/variant/upgrade must explicitly allow Approximate-track fire; the ship Tactical Computer supplies the numerical penalty. The current TL1 computer working value is -25 percentage points, but no production weapon is automatically granted the capability.

The accepted EW doctrine therefore remains valid without rerunning its historical Monte Carlo merely because the generic degraded-fire architecture exists. If a production weapon later receives the capability, or if Tactical Computer, Sensor, ECM, ECCM, Tactical Power, PDS, or relevant weapon behavior changes, that is a declared-dependency question: revalidate only when the changed dependency can plausibly alter the doctrine decision. Degraded fire must remain materially costly enough that restoring Firm with ECCM retains meaningful tactical value when ECCM can be afforded.
