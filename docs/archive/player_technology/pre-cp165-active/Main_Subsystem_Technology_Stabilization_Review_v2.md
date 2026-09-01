# Main-Subsystem Technology Stabilization Review v2

**Checkpoint:** 128 documentation/evidence consolidation candidate  
**Accepted production implementation baseline:** CP122 Corrected Replacement 1  
**Accepted pure-TL main-subsystem stabilization evidence:** CP127 Corrected Replacement 1  
**Purpose:** freeze the accepted TL1-TL9 main-subsystem numerical reference, correct stale explanatory metadata, and establish a sustainable evidence-retention boundary before broader TL-sensitivity work

## Status after CP127 native acceptance

CP127 completed native Windows acceptance with the pinned .NET SDK 8.0.423, warning-as-error build at 0 warnings/errors, 170/170 Python tests, 907/907 xUnit tests, 70/70 ScenarioRunner self-tests, 25/25 C#/Python research-parity fixtures, an 86,584-variant one-trial pipeline smoke with zero trial errors, 2,250/2,250 physical-symmetry comparisons with zero mismatches, and 8,658,400 substantive engagements with zero trial errors or failed gates.

CP128 does **not** rerun that balance study. It records the accepted decisions, fixes prose that still described superseded movement ladders, and preserves the accepted evidence in compact form without recursively embedding large raw native-results ZIPs.

## Stabilized main-subsystem decisions

### Tactical movement invariants

- **STL standard Move = installed STL Drive TL:** 1/2/3/4/5/6/7/8/9.
- **Operational Missile Move = installed Missile Drive TL + 1:** 2/3/4/5/6/7/8/9/10.
- **FTL remains a separate strategic progression:** 1/2/3/4/4/6/7/9/12.

The Storyboard may describe major propulsion science frontiers at TL5 or TL8, but those fiction/engineering transitions do not grant bonus tactical Move unless a later explicit rules decision says so. They may instead express through Space, overload behavior, fuel/endurance, reliability, or specialist branches.

Missile Range/Space and Missile Move are separate axes. A delivery generation may hold Range and Space while Operational Missile Move still advances automatically through the Drive-TL-plus-one invariant.

### TL5 -> TL6 maturation pulse

Accepted CP127 evidence retains TL5->TL6 as a deliberately strong maturation boundary. The higher-TL ship won about **88.97%** of the broad adjacent population and about **96.38%** of exact matched compositions.

The focused ablation does not identify a single erroneous scalar. Holding TL6 characteristics back to TL5 produced approximately these changes in the matched sampled lane:

| Held TL6 package | Approx. effect on higher-TL win rate |
|---|---:|
| Sensor | -9.91 percentage points |
| Kinetic Main | -5.59 pp |
| Armor | -1.78 pp |
| Shield | -1.52 pp |
| Missile package | -1.48 pp |
| Energy Main | -0.57 pp |
| Hull | -0.05 pp |
| STL | ~0.00 pp |
| Tactical Computer | ~0.00 pp in this consumer |

The TL6 Sensor step is a coherent range/discrimination/resistance maturation, and Kinetic enters a new weapon generation after the quieter TL5 step. Strong adjacent-TL performance is not itself a defect and is not normalized toward an arbitrary target.

### TL8 Energy

The accepted stabilized TL8 Energy Main values are **Low/Standard/High damage 7/10/12 canonical points with APEN 3**. Accuracy, SPEN, range, Space, and Tactical Power remain unchanged.

The CP127 factorial supports this exact disposition. Relative to the older 8/11/13/APEN3 state, 7/10/12/APEN3 reduces Energy's no-Shield advantage over Kinetic from about **+19.92 pp to +12.35 pp**, while retaining about a **+18.54 pp Shield-facing advantage**. Reducing APEN to 2 would weaken the intended Shield-facing distinction to about +12.12 pp without materially improving the no-Shield differential.

**Decision:** retain 7/10/12 and APEN3; make no additional Energy reduction from CP127 evidence.

### Late Missile behavior

The accepted full-map/corrected-movement evidence still shows unresolved rates of roughly **10.94% at TL8** and **17.32% at TL9**, with zero mover-order swing in the dedicated late-Missile lanes.

This is not attributed to the old axial geometry, mover-order asymmetry, or the corrected Missile Move rule. CP127 does not isolate a main-table value whose change is justified. The interaction remains a watch item for later broader/AUX/support studies rather than a reason to alter the stabilized main Missile table now.

## Main-subsystem freeze disposition

| Main subsystem | Stabilized disposition |
|---|---|
| Hull | Retain current TL1-TL9 values. |
| Damage Control | Retain current repair-yield progression; internal H/X critical cadence remains deferred. |
| Armor | Retain. |
| Reactor | Retain the CP110-derived progression. |
| STL | Retain **Move = TL** invariant. |
| FTL | Retain strategic **1/2/3/4/4/6/7/9/12** ladder. |
| Tactical Computer | Retain. |
| Sensors | Retain, including strong TL6 maturation. |
| ECM / ECCM | Retain. |
| Shields | Retain. |
| Kinetic Main | Retain. |
| Energy Main | Retain CP127 TL8 **7/10/12, APEN3** correction and all other current values. |
| Missile delivery | Retain **Move = TL+1** and current Range/Space progression. |
| Missile guidance | Retain. |
| GP Missile warhead | Retain. |
| Swarmer | Retain bounded TL7 mature/legacy lifecycle. |

PDS and most other Auxiliary/support families remain outside this numerical freeze. Their present values remain usable research inputs, but are not declared fully calibrated merely because they appear in pure-TL builds.

## Reopening standard

`technology_numerical_matrix_v0_5.json` is the CP128 current main-subsystem reference and is numerically identical to accepted CP127 v0.4. After CP128 native acceptance, a main-subsystem value should be reopened only for new evidence such as:

- a demonstrated rule or implementation defect;
- a newly implemented mechanic that materially changes its causal role;
- broader whole-ladder sensitivity evidence that exposes a real pathology;
- mixed-/legacy-TL interactions; or
- a later AUX/support interaction that changes the interpretation.

Preference for smoother adjacent-TL win rates is not sufficient. CP128 also does not claim final mixed-TL balance validation; broader pure-TL sensitivity remains the next research phase before mixed-/legacy-TL ecology.
