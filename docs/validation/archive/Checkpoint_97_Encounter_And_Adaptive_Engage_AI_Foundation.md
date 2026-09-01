# Checkpoint 97 - Encounter and Adaptive Engage AI Foundation

## Status before native acceptance

**Candidate.** Checkpoint 96 remains the accepted baseline until both the repository-only and normal native Checkpoint 97 acceptance paths succeed.

Accepted CP96 provenance is embedded under `docs/validation/evidence/checkpoint-96/`:

- checkpoint definition SHA-256 `6c5ffdd09669137f892e88c678c9b3536ac61a456174eea24e85fd1108377d89`;
- repository manifest SHA-256 `f4906ecdc98a782e16ce0be3e5230261d9a867653abc8489505b4edc00d0f512`;
- accepted repository archive SHA-256 `945e1da63b714a36ee9aabe29575cc85e827f4d7537ab38e609a3760eef05fa0`;
- native-results archive SHA-256 `a04e25825151dfaa69d4fb24d532cb64c4019a884cdcb36030739fc99f74972d`; and
- substantive CP96 summary SHA-256 `7e8829d458d12220f2d6afe1d96fb276fea12a1db1f255fd537b3468dc505897`.

CP96 accepted 863 tests, 13 runner stages, 59 ScenarioRunner self-tests, and zero failed gates. CP96 closed the dedicated instrumentation sequence.

## Purpose

Checkpoint 97 resumes broader game-mechanics development by replacing TL1-era static range assumptions with a general encounter and Adaptive Engage AI foundation. It does **not** tune component values or promote technology candidates.

The new consumer must demonstrate that the same tactical architecture can operate TL1, TL2, peer, split-TL, and EW-asymmetric representative encounters from neutral pre-contact initialization while respecting player information and turn timing.

## Durable behavior introduced

### Neutral pre-contact encounter

- Radius-5 tactical map.
- Opposite-edge starting geometry, range 10.
- Before contact, each ship searches one hex toward map center per turn.
- The search decision does not receive the hidden target coordinate.
- Contact may be established by legitimate sensing or observable emissions/attacks; contact does not automatically grant Firm track.

### Adaptive Engage

- Movement uses own installed weapon reach and target-specific combat memory rather than hidden opponent family/TL reach.
- A failed Firm acquisition at range X drives a later legal attempt to close below X when the mission remains Engage.
- An actually demonstrated one-sided attack envelope may be preserved through standoff/kiting.
- Target-specific memory stores observable track outcomes, own/observed opponent attack ranges, emissions, and overload failures.
- Decisions cannot use hidden exact opponent ECM/ECCM ratings, TLs, internal Jamming Margin, unrevealed component statistics, or future RNG.
- Later-phase information may affect later decision windows only; no retroactive Movement or power allocation is permitted.

### Escalation

- Normal sensing/ECCM and ordinary movement/closure precede overload.
- Same-hex burn-through resolves normally when closure reaches range 0.
- When hostile ECM observably degrades Firm and both overload paths are plausible, ECCM overload is attempted before Active Sensor overload.
- Active Sensor overload is a later last-ditch option and remains a range capability, not an intrinsic ECM counter.
- A failed overload at range X is not repeated at X or farther while observable tactical state is unchanged. Closer range or materially changed observable state may make a retry legal.

## Study design

`tl2-itc17-adaptive-engage-encounter-foundation`

- Master seed: `970100`
- 18 comparison groups
- mirrored `SideAFirst` / `SideBFirst` movement order
- 36 variants
- 3,000 trials per variant
- 108,000 substantive trials
- no Simultaneous movement-order assumption while production initiative remains unresolved

Representative lanes cover:

- TL1 Kinetic/Energy/Missile peer controls;
- TL2 Kinetic/Energy/Missile peer controls;
- family range asymmetry;
- split-TL TL1/TL2 range asymmetry in both orientations;
- ordinary ECM2/ECCM1 closure + same-hex burn-through;
- harness-only ECM3/ECCM-overload exercise; and
- harness-only Active Sensor overload under demonstrated kiting.

The ECM3 and sensor-range probe fixtures are **test harness controls only**. They are not technology-tree values and cannot be promoted from this study.

## Acceptance workload

Normal native acceptance runs 15 runner stages. The stochastic load is bounded:

- accepted CP96 generated cross-TL regression smoke: 1,440 x 1 trial = 1,440;
- CP97 Adaptive Engage smoke: 36 x 1 trial = 36;
- CP97 substantive Engage study: 36 x 3,000 = 108,000;
- total default trial executions: **109,476**.

The accepted CP96 2.16M-trial substantive replay is not rerun because CP97 adds a new movement mode and retains the historical modes. The full 1,440-variant generated consumer still runs one trial per variant as a regression guard.

Expected native test/self-test counts after the CP97 additions:

- xUnit: **875** total;
- ScenarioRunner self-tests: **62**.

Before the harness starts, the repository contract also mirrors the primary runtime-catalog compatibility checks: the study baseline must hash to the authoritative TL1 baseline, its technology catalog must carry the same baseline hash and reproduce the current TL1 runtime vector, the TL2 production vector must remain unchanged from the frozen v0.3 catalog, and every technology/AUX/Sensor-EW/AI-doctrine ID referenced by the 36 variants must resolve. This is intended to catch catalog-loader failures in `-RepositoryOnly` rather than after build/tests/regression stages.

The CP97 actual-consumer preflight also shares the same single-source policy-telemetry classifier used by the full Monte Carlo gate. Adaptive Engage is explicitly registered there. This prevents a new policy mode from passing structural preflight only to fail the one-trial smoke because its order-request telemetry source was omitted from a separate historical gate list. The repository contract checks that the shared classifier and preflight binding remain present before packaging/native execution.

## Required commands

Repository/contracts first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-97\apply_checkpoint_97.ps1 -RepositoryOnly
```

Normal bounded acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-97\apply_checkpoint_97.ps1
```

Deep Calibration is not applicable.

## Review questions after native success

- Did pre-contact search establish contacts without target-coordinate cheating?
- Do failed Firm tracks actually cause later closure rather than permanent nominal-range deadlock?
- Does observed attack evidence preserve legitimate asymmetric standoff/kiting?
- Does ordinary ECM2/ECCM1 counterplay reach same-hex burn-through as expected?
- Is ECCM overload exercised before Active Sensor overload in the controlled ECM escalation lane?
- Is Active Sensor overload genuinely last-ditch in the controlled kiting lane?
- Do any unresolved encounters now represent real tactical denial/kiting rather than stale TL1 movement assumptions?
- Are the behaviors credible enough to become the general consumer for the next mixed-TL/technology-tree passes?

No win-rate target is automatically promoted by this checkpoint.
