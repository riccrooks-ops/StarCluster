# Tactical Computer Degraded-Fire Architecture v0.1

## Purpose

This note separates **permission to conduct degraded fire** from **the quality of the fire-control solution**. It is current design authority together with the active Concept document.

## Ownership split

A direct-fire weapon profile, variant, or upgrade decides whether that specific weapon can operate from an Approximate target track. The weapon exposes only the capability permission; it does not own a numerical degraded-fire penalty.

The ship's Tactical Computer/fire-control profile decides how accurately a compatible weapon can execute degraded fire. A Firm-track attack never receives the degraded-fire penalty merely because the weapon is capable of the mode.

This produces two independent gates:

1. the selected weapon must explicitly support Approximate-track direct fire; and
2. the currently available Tactical Computer/fire-control state must support an Approximate-track solution.

If either gate fails, an Approximate contact does not satisfy ordinary direct-fire eligibility. Firm-track direct fire remains available through the weapon's local/manual controls even when the external Tactical Computer is unavailable, subject to the normal loss of whatever computer assistance the weapon would otherwise receive.

## TL1 working value

The current TL1 Tactical Computer degraded-fire rating is **-25 percentage points**. This value is applied only when a compatible direct-fire weapon actually fires from an Approximate track.

Checkpoint 76 operational evidence established that -25 remains a useful fallback while imposing a large enough combat penalty for reactive ECCM and restoration to Firm to retain substantial value. The evidence does **not** grant degraded fire to any production weapon by itself.

## Progression guardrails

Tactical Computer, Sensors, ECM, and ECCM progress independently. Later computer TLs may improve degraded-fire performance, but improvement is not assumed to occur at every TL and is not assumed to be a linear five-point ladder. A later value must be tested in the contemporary Sensor/EW/Tactical Power environment.

A future computer progression fails the design intent if degraded fire becomes an easy substitute for restoring Firm through ECCM. The evaluation must include hit throughput, pacing, Tactical Power opportunity cost, offensive-package preservation, PDS preservation, and the current ECM/ECCM environment rather than only comparing raw hit percentages.

The exact effect of Tactical Computer **Degraded, Disabled, or Destroyed** component condition on degraded-fire support remains intentionally deferred until Tactical Computer damage behavior is designed holistically. The Core profile can represent loss of Approximate-track fire-control support without changing the weapon's own capability flag.

## Whole-ladder progression roadmap

`Technology_Architecture_Matrix_v1.md` is the current roadmap for later Tactical Computer progression in the context of Sensor, ECM, and ECCM evolution. The matrix is design guidance rather than production data. It deliberately holds the TL1 **-25 percentage-point** degraded-fire rating into the first TL2 candidate while revalidating the older TL2 ordinary-targeting value, so the project does not improve conventional targeting and the degraded-fire fallback simultaneously without counterplay evidence.

Later degraded-fire improvements are deliberate breakpoints, not an automatic `-25 -> -20 -> -15` ladder. A later computer may instead gain another meaningful capability, integration benefit, resilience improvement, or Evasive Compensation at an appropriate level. Any change that can alter the value of restoring Firm through ECCM requires contemporary Sensor/EW/Tactical Power revalidation.

## Historical study-field interpretation

The retained TL1 integrated-combat study documents use fields such as `sideAApproximateDirectFireAccuracyPenalty`. Those fields are historical/calibration overrides. After this architecture decision, they are interpreted as the **Tactical Computer degraded-fire penalty being tested for a weapon that was explicitly enabled for degraded fire**, not as a penalty physically owned by the weapon profile. Historical study inputs remain frozen for reproducibility.

## Missile boundary

Ordinary missiles and torpedoes do not inherit this direct-fire rule. Their terminal solution remains governed by the missile's launcher-datalink, onboard navigation-sensor, seeker, and explicit profile capabilities.

A future missile type may implement a separate Approximate-target capability. A Swarmer concept, for example, may expend a deliberately large barrage into an estimated target volume so that some portion of the Missile Flight may find or intersect the target despite the absence of an ordinary Firm terminal solution. The eventual rule might express that cost through terminal accuracy, effective attack strength, required flight/ammunition size, seeker/search behavior, or a combination. Those mechanics and values remain deferred and do not alter ordinary missile Firm-terminal requirements.

## TL2 ordinary-targeting revalidation

Accepted Checkpoint 80 leaves the first TL2 Sensor/EW environment sufficiently understood to revalidate the older **+12 percentage-point ordinary targeting** candidate without simultaneously changing the degraded-fire rating, Evasive Compensation, reactor output, Sensor reach, or EW overload behavior.

Checkpoint 81/81a treated +10 versus +12 ordinary Tactical Computer assistance as a paired actual-consumer diagnostic across clean Firm fire, the contemporary DR1 + ECCM1 response to ECM2, the brute-force old-Sensor + ECCM2 response, and the explicit -25 degraded-fire fallback. The numerical degraded-fire penalty remained **-25** in both computer cases. Because current architecture permits the main Tactical Computer to assist self-contained PDS after a legal terminal opportunity exists, the ordinary-targeting override also changed that assistance by the same delta while leaving the PDS local fallback intact.

Accepted Checkpoint 81a validated the +12 ordinary-targeting value across that standing permutation suite. Checkpoint 82 therefore carries **+12 percentage points** forward as the TL2 Tactical Computer **validated working candidate**, while degraded fire remains **-25 percentage points** and Evasive Compensation remains **0**. This status is strong enough to guide further TL2 integration but is still not production component data or a complete TL2 combat profile.
