# Development Diagnostic Event Journal

## Purpose

The authoritative diagnostic journal exists to make tactical resolution reproducible and debuggable without leaking hidden state into player-facing information. It is a development instrument, not a player rulebook.

## Durable requirements

- Development builds create implementation-stamped authoritative encounter logs. These authoritative diagnostics remain separate from any current or future visibility-filtered player combat log.
- Journal entries use stable event names, deterministic ordering, and enough identifiers/coordinates/state to reconstruct authoritative resolution.
- Exact hidden movement, guidance, observation opportunities, and internal failure detail may be recorded for diagnosis.
- Player-visible logs and presentation are derived through observer-safe filtering and must never reconstruct hidden travel or hidden opponent values retroactively.
- Missile launch/advance/resolution reporting distinguishes newly launched salvos, existing salvos advanced, and total missile actions resolved so batch counts cannot silently omit work.
- Missile search, waiting, reacquisition, terminal-resolution, self-destruct, and expiration outcomes are journaled explicitly rather than inferred from disappearance.
- Observation events should capture detect, lose, and reacquire transitions when movement or Sensor/EW refresh changes what a player can legitimately observe.
- Development-only authoritative-debug views must be clearly separated from normal presentation and must disappear when debug mode is disabled.
- Finalization failures should be journaled explicitly with failed stage and exception information rather than leaving an apparently inert interface.

Checkpoint-specific event expectations and example logs belong in validation/evidence artifacts, not this durable document.
