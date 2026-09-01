# Checkpoint 144 — EngageAdaptive Missile Parity Closure and Whole-Combat Stage-A Response Surface

## Status

Candidate pending native Windows acceptance. CP143 — Missile-Mirror Pacing Attribution — is the native-accepted baseline.

CP144 deliberately combines one small, well-understood research-kernel parity correction with the first broad substantive whole-combat Stage-A study. It makes **no production gameplay-rule change and no numerical tuning**.

## 1. EngageAdaptive parity closure

CP143 showed that Missile-mirror pacing was dominated by a Python research-kernel open/close oscillation. The authoritative production C# `AdaptiveEngageTacticalPolicy` already holds the current range once contact is established and the target is inside the ship's own physical weapon envelope, except when a previous non-Firm track requires closure or actual combat evidence supports a one-sided standoff.

Python `canonical_combat.py` instead reopened toward its theoretical preferred Missile range. CP144 corrects that research-only divergence. Canonical kernel version is now `0.5`.

The parity branches are shared through `cp144_engage_adaptive_policy_parity_fixtures_v0_1.json` and are executed directly by both Python and a new C# xUnit test. The fixture covers:

- hold at current range inside own weapon reach;
- hold after a Firm observation;
- close when outside own weapon reach;
- close after a non-Firm track, using the production C# last-track formula;
- open/close/hold around a **demonstrated** one-sided standoff;
- no standoff exploitation when observed opponent reach is equal.

No production C# implementation is changed.

### Internal correction probe

Before the broad-matrix implementation was accepted for authoring, the patched Python kernel replayed all 1,980 CP143 Missile-mirror scenario identities. This is intentionally a correction probe, not a new balance study.

- 1,941 resolved;
- 39 hard 60-turn sentinels;
- only 3 resolved fights at 25+ turns;
- median resolved duration 8 turns;
- P90 12;
- P95 14;
- old effective-range/non-standoff Open orders: **0**.

This is a major reduction from CP143's 1,085 long-resolved Missile mirrors and 228 cap sentinels and is consistent with removal of the identified parity defect. It is not a tuning target and no Missile/PDS/Shield/Sensor value is changed.

## 2. Five-resource Stage-A population

The next broad response surface must not double-weight a mechanically duplicated resource condition. `R5_CENTRAL_HIGH_DEMAND` therefore leaves the Stage-A factorial because its extra AUX demand remains metadata-only and its executable mechanics are the same as R1.

The retained resource environments are:

1. `R0_CP138_HISTORICAL`
2. `R1_CENTRAL_NO_MAJOR`
3. `R2_CENTRAL_PROPULSION`
4. `R3_LOWER_DEMAND`
5. `R4_TIGHT_HIGH_DEMAND`

They remain research-only in-memory overlays. The source Technology Matrix is not rewritten.

The complete Stage-A population is:

- 137 ordered same-TL weapon pairings;
- 5 distinct executable resource environments;
- 10 combat/counter strata;
- **6,850 scenario cells**.

## 3. Complete one-trial whole-combat smoke

Authoring executes the entire 6,850-cell population at one trial per cell before enabling substantive execution. All scenarios use the hard 60-turn gameplay sentinel regardless of the older CP140 Recovery/Attrition source binding.

Authoring result:

- 6,850/6,850 scenarios executed;
- 0 execution errors;
- 6,785 resolved;
- 9 resolved at 25+ turns;
- 65 hard turn-cap sentinels;
- 0 safe offensive-exhaustion stalemates;
- **0 non-standoff Open orders**;
- source numerical matrix unchanged.

These one-trial frequencies are execution/pacing evidence only, never balance probabilities.

## 4. Substantive response-surface design

After native RepositoryOnly acceptance of the full smoke, the normal CP144 wrapper executes:

**6,850 scenario cells × 500 deterministic trials = 3,425,000 substantive combat trials.**

The run persists aggregated per-scenario statistics rather than millions of raw per-turn rows. Turn-level TP/track telemetry is accumulated in memory and reduced into response metrics.

Per-scenario evidence includes, among other fields:

- A/B wins, draws, unresolved and safe-stalemate incidence;
- Wilson 95% intervals for unconditional A/B win probability;
- resolved-by-10/15/20, resolved-under-25, long-resolved and cap rates;
- median/P90/P95 resolved duration;
- Shield/Armor/Hull damage, DEF/RES effects and defensive recovery;
- direct-fire and Missile delivery/guidance telemetry;
- PDS attempts/intercepts and ammunition exhaustion;
- movement/range, Firm-track exposure, EW and overload behavior;
- Tactical Power requested/allocated/denied, fulfillment and true conflict rates;
- final defense state, fuel and ammunition exhaustion;
- non-standoff versus demonstrated-standoff movement orders.

## 5. Broad multivariate outputs

The merged Stage-A result produces complementary views rather than a single balance score:

- per-scenario response surface;
- weapon-by-TL response curves;
- weapon-pair-by-TL response curves;
- stratum/counter response surfaces;
- resource response surfaces;
- overall weapon response summaries;
- counter effects relative to `BALANCED_CORE_NO_PDS`;
- resource effects relative to `R1_CENTRAL_NO_MAJOR`;
- side-order-neutral pairwise response tables;
- side-order-neutral multi-objective Pareto choice surfaces and participation summaries.

Side-order-neutral outputs combine X→Y and Y→X rather than assigning draws/unresolved trials to either family. Pareto comparisons use side-symmetric win rate, fast-win rate, and damage advantage inside each TL/resource/stratum/opponent context. They are diagnostic evidence, not an automatic promotion rule.

## 6. Acceptance and restart behavior

`-RepositoryOnly` performs the complete regression/build/parity chain plus the full 6,850 × 1 smoke. The subsequent normal invocation in the same extraction executes the 3.425M substantive run once.

The substantive run is divided into 27 deterministic scenario-cell batches (26 × 256 plus a final 194). A valid completed batch may be reused after interruption; invalid/incomplete batches are rerun. The merged result must contain exactly 6,850 cells and 3,425,000 combat trials with zero trial errors and zero recurrence of the non-standoff EngageAdaptive Open branch.

The checkpoint does **not** replay all 3.425M trials a second time. Deterministic aggregation is protected by fixed per-scenario/per-trial seeds, the full one-trial smoke, existing canonical parity gates, and focused repeated multi-trial aggregation tests.

## 7. Interpretation boundary

CP144 is the first broad substantive response-surface checkpoint. It must be reviewed before any tuning.

No value is promoted merely because it performs poorly or strongly in one slice. The intended next analysis is multivariate: identify broad dominance/non-viability, counter relationships, TL drift, pacing failures, TP/resource pressure, and interaction surfaces before deciding what to change. Stage B is not automatic.
