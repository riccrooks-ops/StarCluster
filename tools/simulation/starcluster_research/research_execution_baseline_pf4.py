from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
from .ecology import CandidateMatrix
from .canonical_mechanics import DEF_RES_DAMAGE_MODEL

BASELINE_RELATIVE = 'docs/design/player_technology/technology_research_execution_baseline_pending_finalization_v0_4.json'
MANIFEST_RELATIVE = 'docs/validation/evidence/checkpoint-160/research_execution_baseline_manifest_v0_4.json'
BASELINE_ID = 'CP160-PF4'


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def load_research_execution_baseline_pf4(repo: Path) -> CandidateMatrix:
    repo = Path(repo)
    manifest = _json(repo / MANIFEST_RELATIVE)
    path = repo / BASELINE_RELATIVE
    if not path.is_file():
        raise ValueError('CP160-PF4 matrix missing')
    if _sha(path) != manifest['materializedMatrixSha256']:
        raise ValueError('CP160-PF4 matrix hash drift')
    matrix = CandidateMatrix(repo, BASELINE_RELATIVE)
    meta = matrix.doc.get('pendingFinalizationResearchBaseline', {})
    if meta.get('baselineId') != BASELINE_ID:
        raise ValueError('CP160-PF4 identity mismatch')
    matrix.damage_model = DEF_RES_DAMAGE_MODEL
    matrix.def_res_shield_def_pp = {int(k): float(v) for k, v in meta['shieldDefByTl'].items()}
    matrix.def_res_armor_res_pp = {int(k): float(v) for k, v in meta['armorResByTl'].items()}
    matrix.def_res_hardener_bonus_pp = float(meta['shieldHardenerBonusDefPp'])
    matrix.reconciliation_profile = 'cp160-pf4'
    matrix.cp158_aux_profiles = {}
    matrix.cp159_aux_profiles = {}
    matrix.cp160_aux_profiles = {}
    matrix.pending_finalization_aux_profiles = matrix.doc.get('pendingFinalizationAuxProfiles', {})
    return matrix


def aux_profile(repo: Path, key: str, tl: int) -> dict[str, Any] | None:
    matrix = load_research_execution_baseline_pf4(repo)
    row = matrix.pending_finalization_aux_profiles.get(key)
    if not row or int(tl) < int(row.get('firstTl', 99)):
        return None
    spec = row.get('byTl', {}).get(str(int(tl)))
    if spec is None:
        return None
    return {**row, **spec, 'tl': int(tl), 'profileKey': key}


def baseline_identity(repo: Path) -> dict[str, Any]:
    repo = Path(repo)
    path = repo / BASELINE_RELATIVE
    manifest = _json(repo / MANIFEST_RELATIVE)
    return {
        'baselineId': BASELINE_ID,
        'path': BASELINE_RELATIVE,
        'sha256': _sha(path),
        'status': manifest['status'],
        'promotedAuxExecutionCenters': manifest['promotedAuxExecutionCenters'],
        'openDependencies': manifest['openDependencies'],
    }
