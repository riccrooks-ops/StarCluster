from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
from .ecology import CandidateMatrix
from .canonical_mechanics import DEF_RES_DAMAGE_MODEL
BASELINE_RELATIVE='docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_2.json'
MANIFEST_RELATIVE='docs/validation/evidence/checkpoint-158/research_execution_baseline_manifest_v0_2.json'
BASELINE_ID='CP158-PF2'
def _sha(p:Path)->str:
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def _json(p:Path)->dict[str,Any]: return json.loads(p.read_text(encoding='utf-8-sig'))
def load_research_execution_baseline_pf2(repo:Path)->CandidateMatrix:
 repo=Path(repo); man=_json(repo/MANIFEST_RELATIVE); path=repo/BASELINE_RELATIVE
 if not path.is_file(): raise ValueError('CP158-PF2 matrix missing')
 if _sha(path)!=man['materializedMatrixSha256']: raise ValueError('CP158-PF2 matrix hash drift')
 m=CandidateMatrix(repo,BASELINE_RELATIVE); meta=m.doc.get('pendingFinalizationResearchBaseline',{})
 if meta.get('baselineId')!=BASELINE_ID: raise ValueError('CP158-PF2 identity mismatch')
 m.damage_model=DEF_RES_DAMAGE_MODEL
 m.def_res_shield_def_pp={int(k):float(v) for k,v in meta['shieldDefByTl'].items()}; m.def_res_armor_res_pp={int(k):float(v) for k,v in meta['armorResByTl'].items()}
 m.def_res_hardener_bonus_pp=float(meta['shieldHardenerBonusDefPp']); m.reconciliation_profile='cp158-pf2'; m.cp158_aux_profiles={}
 return m
def baseline_identity(repo:Path)->dict[str,Any]:
 repo=Path(repo); p=repo/BASELINE_RELATIVE; man=_json(repo/MANIFEST_RELATIVE); return {'baselineId':BASELINE_ID,'path':BASELINE_RELATIVE,'sha256':_sha(p),'status':man['status'],'selected':man['selected'],'requiredAlternatives':man['requiredAlternatives']}
