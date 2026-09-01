# TL1 Scripted Relative-Range and Missile-Budget Calibration Plan v0.1

## Calibration question

How do one-time changes in relative separation affect direct-fire eligibility, sensor/EW boundaries, Missile Flight range consumption, arrival timing, and layered interception without requiring full tactical movement?

## Controlled abstraction

- shared scalar relative separation only;
- legal values 0-10 hexes;
- strictly ordered turn/range schedule;
- normal change at start of Turn 2, followed by constant separation;
- one explicit later change to prove cumulative missile travel;
- no absolute coordinates or board-edge navigation.

## Scenario families

1. Static Kinetic, Energy, and Missile controls at ranges 2, 4, and 6.
2. Outward and inward direct-fire steps: 2->3, 2->4, 3->5, 4->6, 6->4, and 5->3.
3. Missile reach, delay, exact exhaustion, over-range exhaustion, late outward change, inward arrival, faster missile, and range-10 boundary cases.
4. Passive/Active Sensor, ECM, ECCM, denial, restoration, and inward reacquisition boundaries.
5. Kinetic PDS, AMM PDS, Held Kinetic, Held Energy, combined Held/PDS, and inward-arrival timing.
6. Scalar faster-target, equal-speed, and faster-missile pursuit proofs.

## Measurements

- terminal outcome and mean turns;
- initial/final range and changes applied;
- Firm and denied track rates;
- launches, hits, range exhaustion, and route adjustments;
- Held Main and PDS attempts/interceptions;
- remaining Hull;
- reciprocal side-swap differences.

## Interpretation guardrail

The study identifies mechanical thresholds and timing consequences. It does not establish final ship movement allowances, higher-TL missile speed, board geometry, or tactical AI.
