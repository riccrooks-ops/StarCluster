# Star Cluster Checkpoint 167 Recovery Contract

**Status:** Recovered implementation contract; NOT a substitute for the CP167 full repository.
**Base:** Checkpoint 166 full repository, once the archive is readable in the execution sandbox.
**Promotion boundary:** Research/diagnostic checkpoint. No automatic production promotion.

## Purpose

Continue the CP166 same-TL whole-system architecture/tactical diagnostic and close the agreed tactical-allocation / Sensor-EW questions before moving on.

## Agreed scope to carry forward

### 1. Non-combat Mission/Support AUX reservation sweep

Reference/stress designs shall test **0, 1, 2, and 3 Installation Space** reserved for Mission/Support AUX whose campaign/non-combat effects are not yet implemented.

Rules for the sweep:

- Reserved Mission/Support Space has **zero direct tactical/combat effect** in CP167.
- It is a design-opportunity-cost sensitivity, not a hidden combat bonus.
- Do not score it as combat value.
- Do not invent MedBay/Crew/science/logistics mechanics merely to justify the reservation.
- The sweep exists to determine whether combat-focused ships remain viable when a realistic cruiser devotes some hull capacity to non-combat capability.
- Reference designs should not be rewarded for simply leaving Space unused.
- Combat-AUX portfolio identity remains intact; the reservation is explicit rather than silently filled with unrelated combat equipment.

### 2. Tactical allocation general rule

The normal tactical allocator should preserve coherent future options rather than greedily spending all Tactical Power on the first available action.

For normal ECM affordability, preserve enough uncommitted Tactical Power for:

1. the ship's ready/selected offensive package;
2. planned PDS demand when a real missile threat is present; and
3. one plausible reactive ECCM response.

Consequences:

- If no missile threat exists, no artificial PDS reserve is required.
- Reactive ECCM remains conditional: activate it only when hostile ECM actually degrades an otherwise-Firm observation and sufficient uncommitted TP remains.
- If burn-through / Sensor DR / another legitimate defense already preserves Firm, reactive ECCM remains off.
- Always-on ECM remains a deliberate aggressive/stress policy, not the default normal allocator.
- The allocator must obey information parity and must not inspect hidden enemy ECM/ECCM values, hidden Effective Jamming Margin, future random results, or other unavailable information.

### 3. Sensor Discrimination Resistance candidate

Test the candidate same-TL ladder:

> **Sensor DR(TL) = max(0, normal ECM rating(TL) - 1)**

Intent:

- With no ECCM and no burn-through, ordinary same-TL ECM retains a normal jamming margin of **1**.
- Where a legal ECM overload adds +1 rating, the corresponding no-response margin becomes **2**.
- Sensor progression therefore provides real resistance to obsolete/weaker ECM without making the optional ECCM system redundant.

This is a CP167 research candidate until the native diagnostic supports promotion.

### 4. ECM / ECCM mirror and counteraction contract

CP167 must explicitly prove that ECM and ECCM use the same rating domain and counteract one another through the canonical prospective Sensor/EW refresh:

`JammingMargin = max(0, ECM - ECCM - SensorDR - BurnThrough)`

Required invariants:

- The observer's full Powered ECCM applies to each target; it is not split or consumed per target.
- ECM and ECCM may operate simultaneously.
- Same-type duplicate ECM or ECCM suites do not add locally; use the highest functional rating.
- Matched Powered ECCM must reduce the hostile ECM term one-for-one in the same resolver.
- Swapping ship identities / observer roles must preserve the arithmetic and timing semantics.
- ECCM may preserve a Firm track from jamming; it cannot upgrade a track that is intrinsically Approximate because of sensor reach / underlying measurement quality.
- No completed observation or attack is retroactively rerolled.

### 5. EW timing / information boundary

Retain the existing sequence:

**Movement -> Electronic Warfare -> Direct Fire -> Missile / Interception -> Damage -> Damage Control**

For the EW sub-phase:

1. Movement geometry is final.
2. ECM declarations/commitments occur.
3. The observable post-ECM track state is resolved.
4. Each side gets one ECCM response opportunity from remaining Available TP.
5. Final track quality is resolved.
6. Combat begins.
7. There is no second ECM response after ECCM.

The player/AI may see legitimate track quality and qualitative jamming outcomes, but not hidden ECM/ECCM/DR/Burn-through arithmetic.

### 6. Burn-through question

The current historical TL1 rule uses same-hex Burn-through Resistance +1 and 0 at greater ranges. Higher-TL burn-through scaling must be tested in CP167 rather than silently guessed.

Because the exact last agreed higher-TL numeric profile was not recoverable from the currently available conversation/index data, CP167 implementation should:

- preserve the current accepted CP166 value/profile as the control;
- explicitly sweep a small set of monotonic candidate burn-through profiles;
- include range/hex thresholds rather than treating burn-through as a permanent sensor bonus;
- test whether higher-TL sensors gain a sensible but bounded closer-range ability to defeat ECM;
- ensure same-TL ECM, ECCM, Sensor DR, and burn-through remain mutually interpretable;
- reject any profile that makes ECCM broadly pointless or makes normal ECM broadly ineffective;
- make no automatic promotion from the sweep.

If CP166 already contains the exact higher-TL burn-through candidate agreed in the interrupted CP167 work, use that value as the centerline and retain neighboring profiles as falsification controls.

## CP167 diagnostic matrix

At minimum cover TL1-TL9 same-TL cases with:

- ECM off / normal / legal overload where available;
- ECCM off / normal / legal enhanced/overload modes where available;
- Sensor DR control versus `ECM - 1` candidate;
- relevant burn-through ranges / geometries;
- both observer/target role directions;
- normal allocator and deliberate aggressive/stress allocator;
- missile-threat-present versus no-missile-threat cases for PDS reservation;
- Mission/Support reservation = 0, 1, 2, 3 Space.

## Required assertions / regression gates

1. **ECM/ECCM one-for-one counteraction:** increasing Powered ECCM by one lowers EJM by one until zero.
2. **Mirror symmetry:** equivalent role-swapped EW states produce equivalent EJM/track outcomes.
3. **No hidden-information allocator:** allocation decisions depend only on legitimately observable state and own ship state.
4. **Reactive ECCM trigger:** ECCM is not spent when post-ECM track remains Firm.
5. **Reactive ECCM response:** ECCM may be spent when hostile ECM degrades an otherwise-Firm track and TP exists.
6. **No second ECM response:** ECCM response closes the EW commitment sequence.
7. **Same-type non-additivity:** duplicate local ECM/ECCM suites do not stack ratings.
8. **Sensor DR candidate arithmetic:** same-TL normal ECM has pre-ECCM/pre-burn-through margin 1 under `DR = ECM - 1`; legal +1 ECM overload has margin 2.
9. **Mission/Support reservation neutrality:** changing only 0-3 reserved non-combat Space cannot directly modify combat mechanics or scores; any outcome differences arise only through changed legal equipment portfolios/opportunity cost.
10. **PDS reservation conditionality:** normal allocation reserves planned PDS only when a missile threat is legitimately present.
11. **Authority boundary:** CP166 authorities remain frozen unless CP167 explicitly records a candidate overlay; no automatic Tech Table / production-rule promotion.
12. **Archive hygiene:** active authority discovery must not bind archived/historical copies in place of canonical active paths.

## Packaging / native acceptance target

The finished checkpoint should be a **full CP167 repository archive**, not a hotfix delta, containing the normal checkpoint definition, research inputs/outputs, focused tests, and Windows acceptance entry point (expected `tools/checkpoints/checkpoint-167/apply_checkpoint_167.ps1`).

RepositoryOnly should verify, consistent with the repository's current checkpoint conventions:

- CP166 base/provenance freeze;
- authority/manifest integrity;
- Python research tests;
- warning-as-error .NET build;
- xUnit;
- deterministic / ScenarioRunner corpora required by the inherited baseline;
- C#/Python or shared-fixture parity required by the inherited baseline;
- CP167 focused diagnostic gates;
- deterministic study-plan identity / resumability for any substantive run;
- `promotionAllowed = false` unless a later explicit decision changes that boundary.

Native Windows execution remains the final acceptance authority.

## Blocker recorded on 2026-08-31

The CP166 attachment was supplied twice in the conversation, but the execution sandbox did not mount the second archive at its provided path. Direct checks from both available Python/container environments found the path absent. Therefore no CP166 source file has been modified and no CP167 repository has been fabricated from an older baseline.

The next implementation attempt should begin by verifying that the CP166 ZIP is physically readable before making any repository change.
