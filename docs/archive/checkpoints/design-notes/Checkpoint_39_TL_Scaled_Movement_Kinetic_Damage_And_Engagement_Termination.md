# Checkpoint 39 - TL-Scaled Movement, Kinetic Damage, and Engagement Termination

## Purpose

Checkpoint 39 corrects the movement-profile drift exposed by Checkpoint 38 and adds the diagnostics needed before changing broader combat balance. The production rules now derive movement directly from technology level rather than inheriting independent calibration constants.

## Movement law

- Operational ship STL Move equals the installed STL Drive TL.
- Missile Move equals the installed Missile Drive TL plus 1.
- A TL1 ship therefore moves 1 hex per turn and a TL1 missile moves 2 hexes per missile action.
- A Degraded STL Drive uses the shared half-rounded-up component rule; Disabled or Destroyed movement remains 0.
- A safe STL overload adds the drive's listed Move. A TL1 overload therefore reaches Move 2 and can temporarily deny a TL1 missile its normal closing advantage.
- Overload spends Tactical Power and extra fuel and accumulates STL Strain. Continued use beyond the Strain Limit requires a roll and can fail or worsen the drive.

The former 4/1 integrated profile and the Godot 3/2 test profile remain diagnostic controls only. TL9 ship movement is intentionally allowed to reach 9 hexes per turn; no artificial high-TL cap is introduced.

## Kinetic identity

The provisional production Kinetic Cannon changes from DAM 3/APEN 0 to **DAM 4/APEN 0**. Kinetic remains shorter-ranged and less accurate than standard energy fire, but now delivers the stronger immediate direct-fire packet.

The diagnostic study retains paired arms for:

- DAM 3/APEN 0;
- DAM 4/APEN 0;
- DAM 5/APEN 0;
- DAM 4/APEN 1.

Production TL1 armor remains AP 0. The four kinetic comparison arms use an explicit AP 1 diagnostic armor fixture so the APEN arm can produce an observable difference without silently changing the production defense baseline. No result is predeclared as final.

## Engagement termination

A ship with an explicit withdrawal objective that repeatedly orders Open, moves beyond all opponent weapon reach, has no viable inbound Missile Flight, and cannot presently be threatened may complete a disengagement after three consecutive qualifying turns. While that escape clock is active, the pursuer is not prematurely classified as mobility-mission-killed merely because the withdrawing target is outside its current weapon envelope. Disengagement is a distinct terminal outcome rather than a 40-turn unresolved result.

The resolver continues to distinguish:

- no movement required;
- desired-separation throttling;
- STL-unavailable coercion;
- other movement requests that resolve to no movement.

## Diagnostic telemetry

The integrated runner now reports:

- direct-fire opportunities, shots, hit chances, hits, and prevention reasons;
- missile launch opportunities, terminal chances, hits, and range exhaustion;
- base and tactical Shield restoration and Shieldless ship-turns;
- Shield absorption, Shield Armor prevention, Armor prevention, Armor damage, and Hull damage;
- separate order-resolution statuses;
- destruction, offensive mission kill, mobility mission kill, disengagement, and unresolved outcomes.

The Shield Generator is an exposed damageable component and the shared `ShieldRechargeService` owns integrated start-of-turn recharge. Integrated missile ships use the accepted zero-TP launch and 25-Flight magazine rather than the inherited one-TP/100-Flight diagnostic shortcut.

## Studies

The accepted 90-variant cross-family study is rerun under the new production defaults. A new 44-variant diagnostic study compares movement relationships, kinetic damage/APEN arms, Shield-recharge controls, EvM controls, and disengagement behavior using paired random streams.
