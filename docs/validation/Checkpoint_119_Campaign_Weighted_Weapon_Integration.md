# Checkpoint 119 - Campaign-Weighted Weapon Integration

**Status:** candidate pending native Windows acceptance  
**Accepted baseline:** Checkpoint 118  
**Production promotion:** none

## Objective

Validate a small KISS working weapon set in a shared same-TL ecology before changing the working technology table:

- native Energy reference;
- Kinetic automatic smart-projectile +5 ACC from TL4+;
- GP Missile D5 -> D6 -> D7 -> D8 yield milestones with no penetration creep;
- TL2+ two-packet Swarmer maturation with bounded coverage/PDS saturation.

TL1-TL6 are primary evidence, TL7 advanced validation, and TL8-TL9 endpoint/stress evidence.

## Native workload

- 1,152 mirrored variants.
- 576 Missile / 360 Kinetic / 216 Energy-reference variants.
- 720 primary / 144 advanced / 288 endpoint variants.
- 2,000 trials per variant.
- **2,304,000 substantive engagements.**
- Damage consumer remains `layered_defense_hull_only`; internal critical/subsystem damage is not simulated.

## Acceptance commands

Repository contract first:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-119\apply_checkpoint_119.ps1 -RepositoryOnly
```

Then substantive acceptance:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\checkpoints\checkpoint-119\apply_checkpoint_119.ps1
```

## Acceptance stages

1. Resolve CPython 3.13 and reaffirm the C#/Godot production boundary.
2. Apply/check automatic prepackage root hygiene.
3. Run CP119 static/KISS preflight.
4. Run all Python research self-tests and 25 parity fixtures.
5. Run one-trial CP114/CP115a/CP116/CP118 regression smokes.
6. Run the 1,152-variant CP119 one-trial smoke.
7. For the non-RepositoryOnly path, run 2,304,000 CP119 substantive engagements.
8. Verify CP119 repository/evidence/native-result contracts.

## Acceptance interpretation

Only deterministic/mechanical/integration failures block CP119. Win rates, candidate rankings, Swarmer lifecycle, and movement-order swings are review evidence only. No result automatically promotes a weapon number or player-facing rule.

There is **no automatic** numerical, technology-table, or player-authority promotion in CP119.
