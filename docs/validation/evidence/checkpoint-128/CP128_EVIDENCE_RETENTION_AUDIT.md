# CP128 Evidence Retention and Packaging Audit

**Checkpoint:** 128  
**Purpose:** stop recursive growth of full-repository archives while preserving verifiable acceptance provenance and the decision-relevant evidence needed by later checkpoints

## Observed archive growth

| Full repository | Bytes | Approx. MiB | SHA-256 |
|---|---:|---:|---|
| CP125 | 128,712,912 | 122.75 | `6f37f9e042302bc08f59f42f0bc0c9c9dea5a939bb9071ffdbe44100a2b44ebf` |
| CP126 | 183,393,471 | 174.90 | `84cdf0d1ee1c81d11952199c307cb204f88ffe2a3796175474402d50160c86d6` |
| CP127 Corrected Replacement 1 | 209,650,996 | 199.94 | `f91bb10cd16269bf3765148d44bc7eb420c9aabfa6a901cce8a59f413b7439c9` |

The growth is not primarily source code, the reference library, or normal design documentation. Two large already-compressed predecessor native-results archives were recursively bundled:

- CP126 bundled `CP125_NATIVE_RESULTS_ORIGINAL.zip`: **54,357,183 bytes**; SHA-256 `e26f4a79075cd3bb395213d9a4da7d9e3708fecd3dbd3b5a29911c24ea63ecf0`.
- CP127 bundled `CP126_NATIVE_RESULTS_ORIGINAL.zip`: **24,612,025 bytes**; SHA-256 `a82e8e1f98f9af5589666d091f4773cd3f98b881c82c108a7da7ab2d1c74edb0`.

Because an inner ZIP is already compressed, an outer repository ZIP gains almost no additional compression. Repeating this pattern would make each new complete checkpoint carry every predecessor's large Monte Carlo rows indefinitely.

## CP128 retention decision

CP128 externalizes only those two large raw predecessor-result ZIPs. It does **not** delete their provenance.

For CP125, CP126, and accepted CP127, CP128 retains under `curated-predecessor-native-evidence/`:

1. the accepted native-acceptance summary;
2. the exact SHA-256 and byte size of the original native-results archive;
3. a complete per-entry SHA-256 manifest of the original results ZIP;
4. compact decision-relevant `analysis.json`, `summary.json`, and aggregate CSV outputs used by later reasoning; and
5. explicit notes at the former CP126/CP127 evidence locations explaining that the historical wrapper requires the separately retained original archive if someone deliberately reruns that old historical checkpoint contract.

The original raw `variants.csv` and other large trial-level tables are not recursively copied into CP128. They remain recoverable/verifiable against their recorded archive/content hashes when the original accepted results archive is available externally.

Historical smaller evidence ZIPs are retained. The project reference library under `docs/references/` is also retained in full and is outside this validation-evidence size policy.

## Packaging guard

The shared pre-package hygiene checker now enforces, for ZIP files under `docs/validation/evidence/`:

- maximum single validation-evidence ZIP: **5 MiB**;
- maximum total validation-evidence ZIP payload: **16 MiB**.

A future checkpoint that truly needs a larger embedded evidence archive must make that exception explicit rather than silently increasing every successor package. Source/reference archives under `docs/references/` are intentionally excluded.

## Historical reproducibility boundary

Frozen historical checkpoint files are not rewritten merely to accommodate externalization. If a historical CP126/CP127 wrapper explicitly expects a now-externalized native-results ZIP, that wrapper remains frozen and its evidence directory documents the external dependency. Current checkpoints must use the curated evidence ledger and current contract rather than pretending the old raw archive is still physically bundled.

The machine-readable authority for this policy and the curated-file hashes is `CP128_EVIDENCE_RETENTION_LEDGER.json`.
