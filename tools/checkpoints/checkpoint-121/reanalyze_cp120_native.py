from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

# Standalone checkpoint helpers must resolve the repository research package without
# relying on a caller-provided PYTHONPATH. The Windows checkpoint wrapper invokes
# this script directly.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_SIMULATION_ROOT = _REPO_ROOT / 'tools' / 'simulation'
if str(_SIMULATION_ROOT) not in sys.path:
    sys.path.insert(0, str(_SIMULATION_ROOT))

from starcluster_research.study import load_json
from starcluster_research.weapon_family_analysis import build_variants, _write_csv
from starcluster_research.weapon_sensitivity_analysis import (
    _gp_yield_summary,
    _kinetic_summary,
    _movement_rows,
    _path_rows,
    _path_tier_summary,
    _pds_isolation,
    _profile_meta,
    _sensitivity_deltas,
    _summary_rows,
    _swarmer_profile_summary,
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _member(zf: zipfile.ZipFile, suffix: str) -> str:
    hits = [n for n in zf.namelist() if n.replace('\\', '/').endswith(suffix)]
    if len(hits) != 1:
        raise ValueError(f'expected exactly one ZIP member ending {suffix!r}, found {len(hits)}')
    return hits[0]


def reanalyze(repo: Path, source_zip: Path, outdir: Path) -> dict:
    study = load_json(repo / 'docs/archive/testing/pre-cp165-active/weapon_progression_sensitivity_study_v0_1.json')
    builds, variants = build_variants(repo, study)
    meta = _profile_meta(repo, study, builds)

    with zipfile.ZipFile(source_zip) as zf:
        variants_member = _member(zf, 'checkpoint-120/native-weapon-sensitivity-study/variants.csv')
        analysis_member = _member(zf, 'checkpoint-120/native-weapon-sensitivity-study/analysis.json')
        raw_variants = zf.read(variants_member)
        raw_analysis = zf.read(analysis_member)
    rows = list(csv.DictReader(io.StringIO(raw_variants.decode('utf-8-sig'))))
    source_analysis = json.loads(raw_analysis.decode('utf-8-sig'))
    if len(rows) != 4284 or len(variants) != 4284:
        raise ValueError(f'CP120 native variant shape mismatch: rows={len(rows)} study={len(variants)}')
    total_trials = sum(int(r['trials']) for r in rows)
    if total_trials != 8_568_000 or int(source_analysis.get('totalTrials', 0)) != 8_568_000:
        raise ValueError(f'CP120 native trial shape mismatch: rows={total_trials} analysis={source_analysis.get("totalTrials")}')
    if source_analysis.get('failedGates'):
        raise ValueError(f'CP120 native source contains failed gates: {source_analysis.get("failedGates")}')

    summary = _summary_rows(rows, study, meta)
    outputs = {
        'integration_summary.csv': summary,
        'gp_yield_sensitivity.csv': _gp_yield_summary(summary),
        'swarmer_sensitivity.csv': _swarmer_profile_summary(summary),
        'sensitivity_delta_summary.csv': _sensitivity_deltas(summary, study),
        'pds_isolation_summary.csv': _pds_isolation(summary),
        'kinetic_sensitivity.csv': _kinetic_summary(summary),
    }
    paths = _path_rows(summary, study)
    outputs['progression_path_summary.csv'] = paths
    outputs['progression_path_tier_summary.csv'] = _path_tier_summary(paths)
    outputs['movement_order_summary.csv'] = _movement_rows(rows, study)

    outdir.mkdir(parents=True, exist_ok=True)
    for name, payload in outputs.items():
        _write_csv(outdir / name, payload)

    sw_rows = outputs['sensitivity_delta_summary.csv']
    guidance = [r for r in sw_rows if r['family'] == 'Missile' and r['axis'] == 'swarmer_accuracy']
    corrected_nonzero = [abs(float(r['delta_missile_hit_per_guidance_attempt'])) for r in guidance]
    report = {
        'schemaVersion': 'star-cluster-cp120-native-telemetry-correction-v0.1',
        'checkpoint': 121,
        'sourceCheckpoint': 120,
        'sourceArchive': source_zip.name,
        'sourceArchiveSha256': sha256_file(source_zip),
        'sourceVariantsMember': variants_member,
        'sourceVariantsSha256': sha256_bytes(raw_variants),
        'sourceAnalysisSha256': sha256_bytes(raw_analysis),
        'sourceVariants': len(rows),
        'sourceTrials': total_trials,
        'sourceFailedGates': source_analysis.get('failedGates', []),
        'combatRerun': False,
        'correction': 'Missile launches remain attacker-side telemetry; terminal guidance attempts and missile hits are target-side telemetry. CP120 derived summaries previously read attacking-side missile hits.',
        'correctedGuidanceComparisonRows': len(guidance),
        'maxAbsCorrectedGuidanceHitDelta': max(corrected_nonzero, default=0.0),
        'outputFiles': sorted(outputs),
    }
    # Reproducibility artifacts must be byte-identical across Windows/Linux.
    # write_text() performs platform newline translation on Windows; emit canonical UTF-8/LF bytes instead.
    (outdir / 'correction_summary.json').write_bytes((json.dumps(report, indent=2) + '\n').encode('utf-8'))
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--source-zip', required=True)
    ap.add_argument('--output-dir', required=True)
    args = ap.parse_args()
    report = reanalyze(Path(args.repo).resolve(), Path(args.source_zip).resolve(), Path(args.output_dir).resolve())
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
