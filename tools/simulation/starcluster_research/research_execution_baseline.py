from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
from .ecology import CandidateMatrix
from .canonical_mechanics import DEF_RES_DAMAGE_MODEL

BASELINE_RELATIVE='docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_1.json'
MANIFEST_RELATIVE='docs/validation/evidence/checkpoint-157/research_execution_baseline_manifest_v0_1.json'
BASELINE_ID='CP157-PF1'

def _sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def _json(path: Path) -> dict[str,Any]:
    return json.loads(path.read_text(encoding='utf-8-sig'))

def load_research_execution_baseline(repo: Path) -> CandidateMatrix:
    repo=Path(repo)
    manifest=_json(repo/MANIFEST_RELATIVE)
    path=repo/BASELINE_RELATIVE
    if not path.is_file(): raise ValueError('CP157 pending-finalization research execution matrix is missing')
    if _sha(path)!=manifest['materializedMatrixSha256']: raise ValueError('CP157 pending-finalization research execution matrix hash drift')
    m=CandidateMatrix(repo,BASELINE_RELATIVE)
    meta=m.doc.get('pendingFinalizationResearchBaseline',{})
    if meta.get('baselineId')!=BASELINE_ID: raise ValueError('CP157 research baseline identity mismatch')
    m.damage_model=DEF_RES_DAMAGE_MODEL
    m.def_res_shield_def_pp={int(k):float(v) for k,v in meta['shieldDefByTl'].items()}
    m.def_res_armor_res_pp={int(k):float(v) for k,v in meta['armorResByTl'].items()}
    m.def_res_hardener_bonus_pp=float(meta['shieldHardenerBonusDefPp'])
    m.reconciliation_profile='cp157-pending-finalization-research-execution-baseline-v0.1'
    return m

def baseline_identity(repo: Path) -> dict[str,Any]:
    repo=Path(repo); path=repo/BASELINE_RELATIVE; manifest=_json(repo/MANIFEST_RELATIVE)
    return {'baselineId':BASELINE_ID,'path':BASELINE_RELATIVE,'sha256':_sha(path),'status':manifest['status'],'selected':manifest['selected'],'requiredAlternatives':manifest['requiredAlternatives']}
