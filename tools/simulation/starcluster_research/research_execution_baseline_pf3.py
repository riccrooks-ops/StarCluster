from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
from .ecology import CandidateMatrix
from .canonical_mechanics import DEF_RES_DAMAGE_MODEL
BASELINE_RELATIVE='docs/archive/player_technology/pre-cp165-active/technology_research_execution_baseline_pending_finalization_v0_3.json'
MANIFEST_RELATIVE='docs/validation/evidence/checkpoint-159/research_execution_baseline_manifest_v0_3.json'
BASELINE_ID='CP159-PF3'
def _sha(p:Path)->str:
 h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def _json(p:Path)->dict[str,Any]:return json.loads(p.read_text(encoding='utf-8-sig'))
def load_research_execution_baseline_pf3(repo:Path)->CandidateMatrix:
 repo=Path(repo);man=_json(repo/MANIFEST_RELATIVE);path=repo/BASELINE_RELATIVE
 if not path.is_file():raise ValueError('CP159-PF3 matrix missing')
 if _sha(path)!=man['materializedMatrixSha256']:raise ValueError('CP159-PF3 matrix hash drift')
 m=CandidateMatrix(repo,BASELINE_RELATIVE);meta=m.doc.get('pendingFinalizationResearchBaseline',{})
 if meta.get('baselineId')!=BASELINE_ID:raise ValueError('CP159-PF3 identity mismatch')
 m.damage_model=DEF_RES_DAMAGE_MODEL
 m.def_res_shield_def_pp={int(k):float(v) for k,v in meta['shieldDefByTl'].items()};m.def_res_armor_res_pp={int(k):float(v) for k,v in meta['armorResByTl'].items()}
 m.def_res_hardener_bonus_pp=float(meta['shieldHardenerBonusDefPp']);m.reconciliation_profile='cp159-pf3';m.cp158_aux_profiles={};m.cp159_aux_profiles={}
 m.pending_finalization_aux_profiles=m.doc.get('pendingFinalizationAuxProfiles',{})
 return m
def aux_profile(repo:Path,key:str,tl:int)->dict[str,Any]|None:
 m=load_research_execution_baseline_pf3(repo);row=m.pending_finalization_aux_profiles.get(key)
 if not row or int(tl)<int(row.get('firstTl',99)):return None
 spec=row.get('byTl',{}).get(str(int(tl)))
 if spec is None:return None
 return {**row,**spec,'tl':int(tl),'profileKey':key}
def baseline_identity(repo:Path)->dict[str,Any]:
 repo=Path(repo);p=repo/BASELINE_RELATIVE;man=_json(repo/MANIFEST_RELATIVE)
 return {'baselineId':BASELINE_ID,'path':BASELINE_RELATIVE,'sha256':_sha(p),'status':man['status'],'promotedAuxExecutionCenters':man['promotedAuxExecutionCenters'],'openClosureAux':man['openClosureAux']}
