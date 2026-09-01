# Technology Integration Permutation Suite Architecture v0.10

## Authority

This is the current standing integration-suite architecture. It defines reusable legal-build enumeration, matched screening, population accounting, engagement-readiness classification, activity guards, and escalation rules. It is **not** a checkpoint evidence log and does not itself promote gameplay values.

Version 0.10 extends v0.9. It does not replace the accepted 35-Space construction model, component values, gameplay rules, AI doctrine, or candidate lifecycle.

## Generalized legal-build envelope

The current TL1/TL2 working envelope uses a 35-Space cruiser and independently enumerates weapon, reactor, tactical computer, sensor, shield, armor, ECM, ECCM, and PDS choices. The fixed shell holds only the mandatory STL and FTL drives constant at 10 Space.

The multiplicity envelope supports one or two homogeneous Main Weapons and one or two homogeneous Main Reactors as explicit construction choices. It permits the optional absence of active sensors, shields, PDS, ECM, and ECCM. Multiple ECM/ECCM suites may be installed for redundancy; their ratings never add and runtime resolves the highest applicable functional rating. Tactical Power sufficiency is an operational tradeoff, not a construction-legality filter.

The deterministic envelope remains **82,944 raw combinations**, of which **22,592 are legal at 35 Space or less**. Space utilization is now classified explicitly:

- **4,672 exact-fill** builds use all 35 Space;
- **11,328 near-fill** builds use 32-34 Space; and
- **6,592 underfilled** builds use 31 Space or less.

The legal envelope represents **510,398,464 oriented self-inclusive** or **255,210,528 unordered-with-self** potential pairings. Excluding self-pairs, the current population contains **510,375,872 oriented distinct** or **255,187,936 unordered distinct** legal pairings. The current footprint still does not permit a legal build containing both two full Main Weapons and two full Main Reactors.

## Engagement readiness and observed activity

Version 0.10 separates **structural engagement readiness** from **what the simulation actually did**.

A build is classified against its opponent under the declared reference Sensor/EW state as:

- `reference_ready` - the build can obtain the required Firm attack-quality track and is within physical attack range at reference Range 3;
- `closing_ready` - the reference is not immediately attack-ready, but legal closing to Range 2, 1, or 0 can produce a Firm attack-quality track within physical weapon range; or
- `engagement_denied` - the declared reference capability cannot produce legal attack eligibility even after closing to Range 0.

This classification is intentionally a capability diagnostic. It does not predict doctrine success, Tactical Power affordability, firing cadence, PDS results, or victory. Those remain observed runtime telemetry.

The combat consumer therefore records Side-A and Side-B direct-action opportunities/shots and missile-launch opportunities/launches separately. The pre-existing aggregate counters remain authoritative and the side-specific counters must sum back to them. This permits study-quality gates to distinguish a structurally denied build from a nominally ready build whose doctrine, power allocation, or movement failed to produce combat activity.

## Matched bounded screening strategy

Expensive combat simulation does not exhaustively Monte Carlo the 255-million-plus unordered legal-pair population. Version 0.10 retains the **48 durable named/diagnostic ordered pairings** and replaces the older one-direction stratified slice with a deterministic matched sample over unordered distinct legal pairs.

The matched sample crosses:

- four composition classes: single/no-EW-redundancy, EW redundancy, Main-Weapon/Reactor duplication, and combined duplication;
- four orientation-neutral progression-magnitude strata: `equal_low`, `equal_high`, `near`, and `far`; and
- six canonical Space-utilization pair strata: exact/exact, exact/near, exact/underfilled, near/near, near/underfilled, and underfilled/underfilled.

This creates **96 base population cells**. One unordered distinct legal pair is deterministically sampled from every cell. Each sampled base pair is then emitted in **both orientations**, producing **192 stratified logical pairings**. Together with the 48 named diagnostics, the screen contains **240 logical pairings**.

Every logical pairing is executed at fixed Range 3 and under both TrackAware movement orders, producing **720 actual-consumer variants**. Matched bundle IDs, forward/reverse orientation, random seed, build IDs, Space delta, weapon-family pairing, information-control gap, readiness classes, and population-cell membership are deterministic and journaled.

The named diagnostics remain diagnostic anchors and are excluded from population-weighted inference.

## Population accounting and weighting

Stratified sampling intentionally changes the frequency with which different legal-pair cells appear in the executable sample. Raw means over the 96 sampled cells therefore answer a different question from means over the complete legal-pair population.

Version 0.10 analytically counts the **unordered distinct legal-pair population in every composition x progression-magnitude x Space-utilization cell** without materializing all 255,187,936 pairs. The generator reports for each cell:

- legal unordered-distinct population count;
- sampled base-pair count;
- inclusion fraction; and
- deterministic coverage status.

Substantive reports provide both raw sample summaries and population-weighted screening estimates where an aggregate is meaningful. Population weighting restores cell prevalence; it does **not** make one sampled pair exhaustive of the internal diversity of its cell. Readiness-filtered population-weighted outputs are therefore explicitly labeled as screening estimates and must not be read as exact population frequencies.

No scalar universal "technology score" is introduced. Pair comparability is reported through explicit dimensions: Advanced Component Count magnitude/direction, used-Space difference, Space-utilization stratum, weapon-family pairing, and information-control direction/distance.

## Execution guards

1. Deterministically enumerate the complete legal-build envelope and validate construction/multiplicity rules.
2. Validate exact/near/underfilled Space counts and distinct-pair envelope arithmetic.
3. Analytically populate all 96 matched population cells and reject empty/miscounted cells.
4. Generate physical build documents for every build referenced by the bounded screen.
5. Actual-consumer preflight the generated combat study.
6. Run one trial per generated variant through the full combat pipeline before substantive Monte Carlo.
7. Preserve the accepted rated-cost, preserve-combat-package EW doctrine.
8. Preserve structural readiness independently from runtime combat activity; do not reclassify a bad doctrine outcome as an illegal build.
9. Side-specific contextual activity gates require every family/geometry/readiness cohort that is expected to engage to produce the appropriate direct-fire or missile-launch activity.
10. Broad all-legal screening may legitimately contain `engagement_denied` variants. Those variants are reported rather than rejected merely for having zero attack opportunities.
11. Redundant same-type ECM/ECCM suites use the highest applicable functional rating and never add ratings.
12. Win rates, rankings, matched orientation effects, Space strata, population-weighted estimates, readiness cohorts, and information-control gaps remain human-review evidence. No automatic candidate promotion or retuning is permitted.

## CP93 bounded proving workload

The first v0.10 implementation deliberately uses **2,000 substantive trials per generated variant** rather than immediately scaling the sample or trial count. The purpose is to prove the matched/readiness/Space/population analysis pipeline itself:

- 720 generated variants;
- 720 one-trial smoke executions; and
- 1,440,000 substantive trial executions at the default CP93 setting.

If native CP93 evidence confirms that the new classification, matching, activity gating, and weighting outputs are sound, a later checkpoint may widen the sampled fraction of the legal envelope and/or selectively raise trials in diagnostically important regions.

## Expansion direction

The generalized builder remains deliberately extensible. Later envelopes may add heterogeneous dual-main/dual-reactor combinations, more component families, compatibility/prerequisite rules, broader TL ranges, adaptive or larger samples, and promotion-relevant high-trial submatrices.

Expansion should preserve causal interpretability through deterministic enumeration, explicit population accounting, matched comparison, activity validation, bounded screening, and targeted escalation rather than indiscriminate exhaustive Monte Carlo.

Shared sensitivity/integration axes never imply symmetric technology progression across subsystem families.
