# Star Cluster AI Doctrine Registry Architecture v0.1

## Purpose

Star Cluster records accepted tactical behavior as versioned doctrine instead of leaving useful AI heuristics embedded only in one calibration runner or one historical report. The registry is both a machine-readable runtime input for calibration and a durable design record.

## Doctrine lifecycle

- **control**: deliberate no-op/control behavior used for paired studies.
- **experimental**: executable candidate behavior under evaluation.
- **accepted**: current default AI behavior supported by accepted evidence.
- **superseded**: retained for reproducibility after a newer accepted doctrine replaces it.

Historical studies may pin a doctrine ID/version. New studies should use the current accepted doctrine unless the study deliberately compares alternatives.

## Information parity guardrail

AI doctrine must use information legitimately available to the player or own ship. It may use own component capabilities, current uncommitted Tactical Power, current/previous observed track quality, observable enemy emissions, visible missile threats, and the ship's intended combat package. It must not query hidden enemy ECM/ECCM ratings, hidden Jamming Margin arithmetic, unrevealed enemy components, or future random outcomes.

## Evidence and invalidation

Every accepted doctrine points to one or more evidence records. Evidence records name the checkpoint/study, accepted result SHA-256, concise conclusion, relevant metrics, dependency IDs, and human-readable conditions that require revalidation.

A future checkpoint should not rerun an expensive historical Monte Carlo study merely because unrelated mechanics changed. It should rerun/revalidate doctrine only when one of its declared dependencies changes or when a new competing doctrine is deliberately evaluated.

## Checkpoint 72 seed doctrine

`tl1-ew-reactive-eccm-v1` is the first accepted doctrine entry. It activates ECCM only when observable post-ECM resolution actually degrades a Firm track. CP72 showed that this retains ordinary-range counter-jamming while eliminating point-blank ECCM waste under burn-through.

## Checkpoint 73 candidate ECM doctrines

CP73 keeps reactive ECCM fixed and compares three ECM behaviors:

1. `tl1-ew-always-ecm-reactive-eccm-v1`: stress/control; ECM whenever affordable.
2. `tl1-ew-preserve-offense-v1`: ECM only if the ship retains enough uncommitted TP for its current ready offensive package and one possible normal ECCM response.
3. `tl1-ew-preserve-combat-package-v1`: additionally preserves planned PDS readiness when a missile threat is present.

These policies deliberately do not predict whether ECM will beat the opponent's hidden resistance. They decide only whether the ship can afford to attempt jamming without sacrificing its own declared tactical priorities.

## Evidence capture output

A doctrine study writes a compact `ai-doctrine-evidence-draft.json` next to its ordinary result files. The draft records the registry version/hash, candidate doctrine IDs, study/result identifiers, paired outcome and power metrics, and dependency IDs. It is evidence for review, not automatic promotion. A doctrine becomes accepted only after review and a later repository update changes its registry status/evidence linkage.
