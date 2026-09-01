# TL1 35-Space Track-Aware Movement and Acquisition Study v0.1

## Purpose

Checkpoint 64 follows the accepted Checkpoint 63b operational sensor/acquisition study without changing accepted combat numbers. Checkpoint 63b confirmed that the optional Active Sensor suite has real operational value, but it also showed that sensor effectiveness cannot be interpreted independently of movement doctrine.

The Checkpoint 64 question is narrower:

> When a ship needs Firm track to authorize its main attack, how much of the Checkpoint 63b track denial is caused by self-inflicted range choice, and how much is a legitimate consequence of an opponent preserving standoff?

No target win rate is a release gate.

## Frozen production controls

The study preserves the accepted production state:

- TL1 production reactor output: **5 Tactical Power per operational main reactor**.
- Tactical Power doctrine: **FullVolleyFirst**.
- Six legal Checkpoint 60 35-Space composed builds are unchanged.
- Side B is the balanced-generalist Missile control with an established Firm target solution.
- All main-weapon fire/launch authorization still requires Firm in this diagnostic.
- TL1 sensor envelopes remain unchanged: passive Firm 3 / Approximate 5; Active 1 TP Firm 5 / Approximate 7; Active 2 TP Firm 6 / Approximate 9 before EW pressure.
- EW1 remains an abstract one-hex net range penalty; it does not price or promote a specific ECM/ECCM component.
- Energy APEN and every other contextual/latent capability retain their existing value proposition and are not judged worthless merely because this opponent does not exercise them.

## New movement doctrine

`TrackAwareOpponentRange` does not replace the accepted `OpponentAwareRange` policy. It is a paired diagnostic alternative.

The doctrine begins from the same weapon/opponent range reasoning, but it caps the ship's effective useful range at the maximum **Firm** range that its current sensing/power state can support while preserving the ready full main-weapon volley when possible.

Examples at the accepted TL1 sensor envelope:

- A passive-only ship under clear conditions cannot plan around a Firm range greater than 3.
- A sensor-equipped ship that can spare only 1 TP after preserving its ready volley plans around Active Firm range 5 in clear space.
- Under EW1, that same 1-TP Firm envelope becomes 4.
- A Missile build able to preserve its volley while spending 2 TP may plan around Firm 6 in clear space or Firm 5 under EW1.

If the current damaged/power state cannot fund the entire ready volley at all, preserving that impossible volley is no longer treated as a planning constraint; the doctrine may instead plan around Active Sensor power that is actually available.

The doctrine does **not** guarantee that the ship reaches its desired range. If an equal-or-faster opponent opens range at the same time, the opponent may legitimately preserve standoff. That is a real cost of shorter sensor reach, not a doctrine failure.

## Acquisition-first active-sensor power

`AcquisitionFirstAutoActive` is also a paired diagnostic alternative, not a silent rewrite of Checkpoint 63b's `AutoActive` behavior.

After movement:

1. Passive sensing is used for free when it already supplies Firm.
2. If Firm requires Active sensing, the minimum useful 1-TP or 2-TP setting is requested.
3. That sensor setting is funded before defensive-system allocation, even when doing so leaves too little Tactical Power for every ready main weapon to fire.
4. FullVolleyFirst still governs subsequent PDS allocation and normal weapon spending from the remaining pool.

This avoids the pathological case where power is notionally protected for a full volley that cannot legally fire because the ship never funded the target solution.

## Study matrix

The study is:

**6 accepted builds x 3 Side-A weapon families x 5 paired operational regimes = 90 variants.**

Each build/family lane shares one comparison group and therefore one paired random stream.

The five regimes are:

1. `established-firm-control` — `OpponentAwareRange` + `EstablishedFirm`, clear.
2. `legacy-auto-active-clear` — Checkpoint 63b `OpponentAwareRange` + `AutoActive`, clear.
3. `track-aware-auto-active-clear` — `TrackAwareOpponentRange` + `AcquisitionFirstAutoActive`, clear.
4. `legacy-auto-active-ew1` — Checkpoint 63b `OpponentAwareRange` + `AutoActive`, EW1.
5. `track-aware-auto-active-ew1` — `TrackAwareOpponentRange` + `AcquisitionFirstAutoActive`, EW1.

For sensorless builds, the AutoActive policies cannot synthesize an Active Sensor suite; they continue to use the cruiser core passive envelope. The track-aware doctrine may therefore command closure, but a kiting opponent may still deny Firm.

## Interpretation rules

Checkpoint 64 is diagnostic. Review:

- final/minimum/maximum range and movement expenditure;
- Firm/Approximate/NoTrack evaluations;
- attacks prevented for lack of Firm;
- active-sensor power committed and unfunded requests;
- attack opportunities and actual direct shots/launches;
- Tactical Power preventions caused by acquisition-first sensing;
- conditional win share only as downstream evidence.

Do not rebalance sensor Space, EW strength, reactor output, Missile behavior, or weapon-family values solely from this study. A new release gate may require the new doctrine to produce a measurable operational response somewhere, but no gate requires a sensorless build to defeat a valid equal-speed standoff strategy.
