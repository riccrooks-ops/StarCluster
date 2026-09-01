# TL1 EW AI Doctrine Study v0.1

## Purpose

Checkpoint 73 evaluates **decision doctrine**, not new EW numbers. It preserves the accepted TL1 5-TP reactor, Balanced-0 Sensor/EW envelope, Sensor Discrimination Resistance 0, same-hex Burn-through +1, ECM 1/1 TP, ECCM 1/1 TP, FullVolleyFirst Tactical Power doctrine, and Movement -> EW -> Combat timing.

The study exists to turn useful tactical heuristics into versioned evidence so later checkpoints do not repeatedly rediscover them.

## Accepted starting evidence

The AI Doctrine Registry records Checkpoint 72 reactive ECCM as accepted behavior:

- If hostile ECM actually degrades an otherwise Firm observation and uncommitted TP can fund normal ECCM, the doctrine may activate ECCM.
- If the observation remains Firm, ECCM stays off.
- The decision uses observable track state and own available power, not hidden enemy EW ratings or the internal Jamming Margin.

## Experimental ECM heuristics

Checkpoint 73 leaves ECM activation unpromoted and compares:

1. **AlwaysNormal** - activate normal ECM whenever installed and affordable; this is the stress/control behavior that exposed CP72 family-specific TP costs.
2. **PreserveOffenseAndEccm** - activate ECM only when enough TP remains for the currently ready offensive package plus one normal ECCM response if installed.
3. **PreserveCombatPackageAndEccm** - additionally preserve current planned PDS readiness against a missile threat.

The no-EW control uses neither ECM nor ECCM. All three experimental ECM doctrines use the accepted reactive-ECCM response rule.

## Matrix

The 24 substantive variants are:

- 3 ordered weapon pairings: Kinetic vs Missile, Energy vs Missile, Kinetic vs Energy;
- 2 movement orders: Side A first, Side B first;
- 4 symmetric doctrine packages.

All contexts use paired comparison groups and otherwise identical build, map, fuel, sensor, power, and overload controls.

## Evidence capture

The runner writes `ew-ai-doctrine-review.csv` plus a hash-linked `ai-doctrine-evidence-draft.json`. The evidence draft records:

- registry version and SHA-256;
- substantive `summary.json` SHA-256;
- accepted baseline doctrine;
- experimental candidate IDs;
- dependency IDs that determine when revalidation is required;
- per-doctrine aggregate TP/combat telemetry;
- all 24 context results.

The evidence draft is deliberately **review-required**. No release gate or win-rate threshold automatically changes a doctrine from experimental to accepted/rejected.
