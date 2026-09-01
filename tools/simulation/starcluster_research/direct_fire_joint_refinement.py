from __future__ import annotations

import copy
import csv
import hashlib
import itertools
import json
import math
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .ecology import UTILITY_COMBAT_DOCTRINE, build_space
from .point_scale_multivariate_response import _apply_exact_scale, _round_half_up, K_RESEARCH_DAMAGE_OLD_SCALE
from .stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario, _features_for_stratum
from .study import load_json
from . import whole_combat_stage_a_response_surface as wc

RESULT_SCHEMA = "star-cluster-cp152-direct-fire-joint-refinement-result-v0.1"
POINT_SCALE = 2
EXPECTED_STAGE_A = 6850
K_TRIALS = 25
E_TRIALS = 50
JOINT_TRIALS = 100
SMOKE_CONTEXTS = 50
K_CANDIDATES_PER_TL = 243
E_CANDIDATES_PER_TL = 243
JOINT_SHORTLIST_PER_FAMILY = 3
JOINT_CANDIDATES_PER_TL = JOINT_SHORTLIST_PER_FAMILY ** 2
K_CONTEXTS_BY_TL = {1: 200, **{tl: 300 for tl in range(2,10)}}
E_CONTEXTS_BY_TL = {1: 200, **{tl: 300 for tl in range(2,10)}}
JOINT_CONTEXTS_BY_TL = {tl: 100 for tl in range(1,10)}
K_CELLS = sum(K_CANDIDATES_PER_TL*K_CONTEXTS_BY_TL[tl] for tl in range(1,10))
E_CELLS = sum(E_CANDIDATES_PER_TL*E_CONTEXTS_BY_TL[tl] for tl in range(1,10))
K_COMBATS = K_CELLS*K_TRIALS
E_COMBATS = E_CELLS*E_TRIALS
JOINT_CELLS = sum(JOINT_CANDIDATES_PER_TL*JOINT_CONTEXTS_BY_TL[tl] for tl in range(1,10))
JOINT_COMBATS = JOINT_CELLS*JOINT_TRIALS
SUBSTANTIVE_COMBATS = K_COMBATS + E_COMBATS + JOINT_COMBATS
SMOKE_COMBATS = (K_CANDIDATES_PER_TL + E_CANDIDATES_PER_TL)*SMOKE_CONTEXTS*9

K_FACTORS = ("damage","accuracy","standard_range","max_range","apen")
E_FACTORS = (
    "low_damage","standard_damage","overload_damage","accuracy","standard_range","max_range",
    "low_tp_delta","standard_gap_delta","overload_gap_delta","spen","strain_limit",
)

EVIDENCE_HASHES = {
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_NATIVE_ACCEPTANCE_SUMMARY.json": "7714e9b4fc2543cb7d4ebfdd03b89d99ed68c1b3e35168bab048f06f840de9fc",
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_AXIAL_FAMILY_EFFECTS.CSV": "7c25aa5780c4e25f3c19d7988216628f1445a9f8276097103db1fbdcfb3ca491",
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_CANDIDATE_FAMILY_RESPONSE.CSV": "9ebdc4a07a46ae88fa12752c1b6996cca634375c877db1ab28259bf7f80fda83",
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_CANDIDATE_LEDGER.CSV": "d74e0248e6f36e275b0e92fe69a1924f1c0287854c437b04beed07f33dd31bce",
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_CANDIDATE_PAIR_RESPONSE.CSV": "d906c81ee596b03da3f156fc1af5d760258cf16fd48d3a949e7fcce5b35ce103",
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_FACTOR_FAMILY_MARGINALS.CSV": "b46786bec8e6158c57a07081a1d31520daca51e80ae75d3fd935cff7ebd5b367",
    "docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_POINT_SCALE_PAIRWISE_FACTOR_FAMILY_RESPONSE.CSV": "23f91d58abbd29cc0f7f738e5cbe72d9c4be4498074ddb57ba533384f581bd47",
}


def _sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str,Any]]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    cols=[]
    for r in rows:
        for k in r:
            if k not in cols: cols.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def _read_evidence(repo: Path) -> dict[str,Any]:
    for rel,expected in EVIDENCE_HASHES.items():
        p=repo/rel
        if not p.is_file() or _sha(p)!=expected: raise ValueError(f"CP152 accepted CP151 evidence hash mismatch: {rel}")
    s=json.loads((repo/"docs/validation/evidence/checkpoint-152/accepted-cp151/CP151_NATIVE_ACCEPTANCE_SUMMARY.json").read_text(encoding="utf-8-sig"))
    if int(s.get("checkpoint",0))!=151 or int(s.get("substantiveCombatTrials",0))!=45176250 or int(s.get("substantiveErrorTrials",-1))!=0 or int(s.get("equivalenceMismatches",-1))!=0:
        raise ValueError("CP152 accepted CP151 evidence does not prove native completion/equivalence")
    return s


def _base_matrix(repo: Path, doc: dict[str,Any], resource: str):
    er,tr=_resource_rows(repo,doc)
    return build_deep_resource_matrix(repo,doc["matrix"],resource,er,tr)


def _copy_matrix(m: Any):
    x=copy.deepcopy(m); x.doc=copy.deepcopy(m.doc); x.profiles=x.doc["profiles"]; x.branches={r["id"]:r for r in x.doc["branches"]}; return x


def _apply_cp151_center(base: Any) -> Any:
    # CP151 validated x2 point scale; keep defenses/missiles at its neutral research center.
    m=_apply_exact_scale(base)
    for tl in range(1,10):
        k=m.p("kinetic_main",tl); k["damage"]=int(K_RESEARCH_DAMAGE_OLD_SCALE[tl]*POINT_SCALE); k["spen"]=0
        e=m.p("energy_main",tl); e["apen"]=0
        gp=m.p("missile_gp_warhead",tl); gp["spen"]=0; gp["apen"]=0
        if tl>=2:
            sw=m.p("missile_swarmer",tl); sw["packetDamage"]=_round_half_up(float(base.p("missile_swarmer",tl)["packetDamage"])*POINT_SCALE); sw["spen"]=0; sw["apen"]=0
        sh=m.p("shield",tl)
        if float(sh.get("tacticalRechargePerTp",0))>0: sh["tacticalRechargePerTp"]=2
        ar=m.p("armor",tl)
        if float(ar.get("tacticalRegenerationPerTp",0))>0: ar["tacticalRegenerationPerTp"]=2
    return m


def _projective_columns() -> list[tuple[int,...]]:
    units=[tuple(1 if i==j else 0 for i in range(5)) for j in range(5)]; cols=list(units)
    for v in itertools.product(range(3),repeat=5):
        if not any(v): continue
        first=next(x for x in v if x); inv=1 if first==1 else 2; norm=tuple((x*inv)%3 for x in v)
        if norm not in cols: cols.append(norm)
    return cols

_OA_COLS=_projective_columns()


def _oa_codes(names: tuple[str,...]) -> list[dict[str,int]]:
    cols=_OA_COLS[:len(names)]; sym_to_code={0:0,1:-1,2:1}; out=[]
    for base in itertools.product(range(3),repeat=5):
        r={}
        for name,col in zip(names,cols):
            sym=sum(a*b for a,b in zip(base,col))%3; r[name]=sym_to_code[sym]
        out.append(r)
    return out


def _central_profiles(repo: Path, doc: dict[str,Any]) -> Any:
    return _apply_cp151_center(_base_matrix(repo,doc,"R1_CENTRAL_NO_MAJOR"))


def _levels(center: int, minus: int=1, plus: int=1, floor: int=0) -> dict[int,int]:
    return {-1:max(floor,int(center)-minus),0:int(center),1:int(center)+plus}


def k_factor_levels(repo: Path, doc: dict[str,Any], tl: int) -> dict[str,dict[int,int]]:
    m=_central_profiles(repo,doc); k=m.p("kinetic_main",tl)
    acc=int(k["accuracyPp"])
    # Broad delivery probes deliberately retain identity-stress corners; final ladder selection, not exploration, enforces monotonicity.
    acc_minus=5 if acc>=20 else 3
    acc_plus=10 if tl in (2,3,8,9) else 5
    return {
        "damage":_levels(int(k["damage"]),1,1,1),
        "accuracy":{-1:max(5,acc-acc_minus),0:acc,1:min(95,acc+acc_plus)},
        "standard_range":_levels(int(k["standardRange"]),1,1,1),
        "max_range":_levels(int(k["maxRange"]),1,1,2),
        "apen":_levels(int(k["apen"]),1,1,0),
    }


def e_factor_levels(repo: Path, doc: dict[str,Any], tl: int) -> dict[str,dict[int,int]]:
    m=_central_profiles(repo,doc); e=m.p("energy_main",tl)
    late=tl>=6; acc=int(e["accuracyPp"])
    return {
        "low_damage":_levels(int(e["lowDamage"]),2,2,1),
        "standard_damage":_levels(int(e["standardDamage"]),2,4 if late else 2,1),
        "overload_damage":_levels(int(e["overloadDamage"]),2,4 if late else 2,1),
        "accuracy":{-1:max(5,acc-5),0:acc,1:min(95,acc+(10 if tl>=7 else 5))},
        "standard_range":_levels(int(e["standardRange"]),1,1,1),
        "max_range":_levels(int(e["maxRange"]),1,1,2),
        "low_tp_delta":{-1:-1,0:0,1:1},
        "standard_gap_delta":{-1:-1,0:0,1:1},
        "overload_gap_delta":{-1:-1,0:0,1:1},
        "spen":_levels(int(e["spen"]),2,2,0),
        "strain_limit":{-1:1,0:2,1:3},
    }


def k_candidate_ledger(repo: Path, doc: dict[str,Any]) -> list[dict[str,Any]]:
    _read_evidence(repo); rows=[]
    center=_central_profiles(repo,doc)
    for tl in range(1,10):
        lev=k_factor_levels(repo,doc,tl); energy_acc=int(center.p("energy_main",tl)["accuracyPp"])
        for i,combo in enumerate(itertools.product((-1,0,1),repeat=len(K_FACTORS))):
            codes=dict(zip(K_FACTORS,combo)); actual={f:lev[f][codes[f]] for f in K_FACTORS}
            rows.append({"lane":"K","candidate_id":f"DK{tl:02d}-{i:03d}","tl":tl,"candidate_index":i,
                         **{f"code_{f}":codes[f] for f in K_FACTORS},**{f"candidate_{f}":actual[f] for f in K_FACTORS},
                         "intrinsic_progression_policy":"final ladder must be non-decreasing in ACC/standard/max range unless explicit tradeoff",
                         "identity_stress_current_energy_accuracy":int(actual["accuracy"]>=energy_acc),
                         "promotion_allowed":0})
    return rows


def e_candidate_ledger(repo: Path, doc: dict[str,Any]) -> list[dict[str,Any]]:
    _read_evidence(repo); rows=[]
    for tl in range(1,10):
        lev=e_factor_levels(repo,doc,tl)
        for i,codes in enumerate(_oa_codes(E_FACTORS)):
            actual={f:lev[f][int(codes[f])] for f in E_FACTORS}
            rows.append({"lane":"E","candidate_id":f"DE{tl:02d}-{i:03d}","tl":tl,"candidate_index":i,
                         **{f"code_{f}":int(codes[f]) for f in E_FACTORS},**{f"candidate_{f}":actual[f] for f in E_FACTORS},
                         "intrinsic_progression_policy":"final ladder must be non-decreasing in ACC/standard/max range unless explicit tradeoff",
                         "apen_policy":"fixed_zero","space_policy":"separate_legality_headroom_envelope","promotion_allowed":0})
    return rows


def energy_space_envelope(repo: Path, doc: dict[str,Any]) -> list[dict[str,Any]]:
    # Space is a construction/headroom axis only in fixed Stage-A templates.
    er,tr=_resource_rows(repo,doc); strata=sorted({r["scenario_stratum"] for r in _read_csv(repo/doc["stageAExperimentManifest"])})
    out=[]
    for eid in sorted({r["ensemble_id"] for r in er}):
        matrix=build_deep_resource_matrix(repo,doc["matrix"],eid,er,tr)
        for tl in range(1,10):
            base_space=int(matrix.p("energy_main",tl)["space"])
            for space in (4,5,6,7,8):
                for stratum in strata:
                    f=_features_for_stratum(stratum,tl); original=int(matrix.p("energy_main",tl)["space"]); matrix.p("energy_main",tl)["space"]=space
                    try:
                        combat=build_space(matrix,tl,"Energy",1,1,bool(f["shield"]),bool(f["ecm"]),bool(f["eccm"]),f["pds"],bool(f["hardener"]))
                    finally:
                        matrix.p("energy_main",tl)["space"]=original
                    cap=matrix.capacity(tl)
                    out.append({"resource_ensemble_id":eid,"tl":tl,"scenario_stratum":stratum,"base_energy_space":base_space,"candidate_energy_space":space,"combat_space":combat,"capacity":cap,"free_space":cap-combat,"legal":int(combat<=cap),"combat_effect_modeled":0,"interpretation":"legality/headroom only; freed Space is not converted into invented AUX"})
    return out


def _contexts(repo: Path, doc: dict[str,Any], lane: str, tl: int) -> list[dict[str,str]]:
    rs=[r for r in _read_csv(repo/doc["stageAExperimentManifest"]) if int(r["tl"])==tl]
    if lane=="K": rs=[r for r in rs if "K" in (r["side_a_weapon"],r["side_b_weapon"]) and r["side_a_weapon"]!=r["side_b_weapon"]]
    elif lane=="E": rs=[r for r in rs if "E" in (r["side_a_weapon"],r["side_b_weapon"]) and r["side_a_weapon"]!=r["side_b_weapon"]]
    elif lane=="J": rs=[r for r in rs if set((r["side_a_weapon"],r["side_b_weapon"]))=={"K","E"}]
    else: raise ValueError(lane)
    return sorted(rs,key=lambda r:r["scenario_id"])


def _smoke_contexts(repo: Path, doc: dict[str,Any], lane: str, tl: int) -> list[dict[str,str]]:
    rs=_contexts(repo,doc,lane,tl); groups=defaultdict(list)
    for r in rs: groups[(r["resource_ensemble_id"],r["scenario_stratum"])].append(r)
    out=[]
    for key in sorted(groups):
        g=sorted(groups[key],key=lambda r:r["scenario_id"]); pos=(tl+sum(ord(x) for x in (key[0]+key[1]+lane)))%len(g); out.append(g[pos])
    if len(out)!=SMOKE_CONTEXTS: raise ValueError(f"CP152 {lane} TL{tl} smoke {len(out)} != {SMOKE_CONTEXTS}")
    return out


def validate_study(doc: dict[str,Any]) -> list[str]:
    e=[]
    if doc.get("schemaVersion")!="star-cluster-cp152-direct-fire-joint-refinement-study-v0.1":e.append("schema")
    if int(doc.get("checkpoint",0))!=152 or int(doc.get("baseCheckpoint",0))!=151:e.append("checkpoint")
    if doc.get("combatDoctrine")!=UTILITY_COMBAT_DOCTRINE:e.append("doctrine")
    if int(doc.get("pointScale",0))!=2:e.append("scale")
    if int(doc.get("kTrialsPerCell",0))!=K_TRIALS or int(doc.get("eTrialsPerCell",0))!=E_TRIALS or int(doc.get("jointTrialsPerCell",0))!=JOINT_TRIALS:e.append("trials")
    if int(doc.get("expectedKCombatTrials",0))!=K_COMBATS or int(doc.get("expectedECombatTrials",0))!=E_COMBATS or int(doc.get("expectedJointCombatTrials",0))!=JOINT_COMBATS or int(doc.get("expectedTotalCombatTrials",0))!=SUBSTANTIVE_COMBATS:e.append("combat-count")
    if doc.get("heldFixed")!=["Hull capacity","Shield capacity","Armor capacity","Shield Regen=2","Armor Repair=2","GP Missile center","Swarmer integer center","PDS","AUX","ECM/ECCM/Sensor","Reactor ladder","DEF/RES"]:e.append("heldFixed")
    if bool(doc.get("automaticPromotion",True)) or bool(doc.get("stageBAutomatic",True)):e.append("promotion")
    return e


def validate_population(repo: Path, doc: dict[str,Any]) -> list[str]:
    e=[]; _read_evidence(repo)
    man=_read_csv(repo/doc["stageAExperimentManifest"])
    if len(man)!=EXPECTED_STAGE_A:e.append("stage-a")
    k=k_candidate_ledger(repo,doc); en=e_candidate_ledger(repo,doc)
    if len(k)!=K_CANDIDATES_PER_TL*9 or len(en)!=E_CANDIDATES_PER_TL*9:e.append("candidate-count")
    for tl in range(1,10):
        if len(_contexts(repo,doc,"K",tl))!=K_CONTEXTS_BY_TL[tl]:e.append(f"K-contexts-{tl}")
        if len(_contexts(repo,doc,"E",tl))!=E_CONTEXTS_BY_TL[tl]:e.append(f"E-contexts-{tl}")
        if len(_contexts(repo,doc,"J",tl))!=JOINT_CONTEXTS_BY_TL[tl]:e.append(f"J-contexts-{tl}")
    return e


def run_plan(repo: Path, study_path: Path, outdir: Path) -> dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc); outdir.mkdir(parents=True,exist_ok=True)
    k=k_candidate_ledger(repo,doc); e=e_candidate_ledger(repo,doc)
    _write_csv(outdir/"direct_fire_k_candidate_ledger.csv",k); _write_csv(outdir/"direct_fire_e_candidate_ledger.csv",e); _write_csv(outdir/"energy_space_envelope.csv",energy_space_envelope(repo,doc))
    ds=[]
    for tl in range(1,10):
        ds.append({"tl":tl,"k_candidates":K_CANDIDATES_PER_TL,"k_contexts":K_CONTEXTS_BY_TL[tl],"k_trials_per_cell":K_TRIALS,"k_combats":K_CANDIDATES_PER_TL*K_CONTEXTS_BY_TL[tl]*K_TRIALS,
                   "e_candidates":E_CANDIDATES_PER_TL,"e_contexts":E_CONTEXTS_BY_TL[tl],"e_trials_per_cell":E_TRIALS,"e_combats":E_CANDIDATES_PER_TL*E_CONTEXTS_BY_TL[tl]*E_TRIALS,
                   "joint_shortlist_cross":JOINT_CANDIDATES_PER_TL,"joint_contexts":JOINT_CONTEXTS_BY_TL[tl],"joint_trials_per_cell":JOINT_TRIALS,"joint_combats":JOINT_CANDIDATES_PER_TL*JOINT_CONTEXTS_BY_TL[tl]*JOINT_TRIALS})
    _write_csv(outdir/"direct_fire_design_summary.csv",ds)
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":152,"mode":"plan","passed":not errs,"failedGates":errs,"kTlCandidates":len(k),"eTlCandidates":len(e),"kCandidateContextCells":K_CELLS,"eCandidateContextCells":E_CELLS,"kCombatTrials":K_COMBATS,"eCombatTrials":E_COMBATS,"jointCombatTrials":JOINT_COMBATS,"totalCombatTrials":SUBSTANTIVE_COMBATS,"smokeCombatTrials":SMOKE_COMBATS,"automaticPromotion":False,"stageBAutomatic":False}
    (outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8"); return s


_WORKER_BASE: dict[str,Any]|None=None
_WORKER_CANDS: dict[str,dict[str,Any]]|None=None
_WORKER_CACHE: dict[tuple[str,int,str],Any]|None=None
_WORKER_LANE: str|None=None


def _worker_init(repo_text: str, doc: dict[str,Any], candidates: list[dict[str,Any]], lane: str) -> None:
    global _WORKER_BASE,_WORKER_CANDS,_WORKER_CACHE,_WORKER_LANE
    repo=Path(repo_text); er,tr=_resource_rows(repo,doc); resources=sorted({r["ensemble_id"] for r in er})
    _WORKER_BASE={rid:_apply_cp151_center(build_deep_resource_matrix(repo,doc["matrix"],rid,er,tr)) for rid in resources}
    _WORKER_CANDS={r["candidate_id"]:r for r in candidates}; _WORKER_CACHE={}; _WORKER_LANE=lane


def _apply_candidate(base: Any, tl: int, c: dict[str,Any], lane: str) -> Any:
    m=_copy_matrix(base)
    if lane=="K":
        k=m.p("kinetic_main",tl); k["damage"]=int(c["candidate_damage"]); k["accuracyPp"]=int(c["candidate_accuracy"]); k["standardRange"]=int(c["candidate_standard_range"]); k["maxRange"]=max(int(c["candidate_max_range"]),int(k["standardRange"])); k["apen"]=int(c["candidate_apen"]); k["spen"]=0
    elif lane=="E":
        e=m.p("energy_main",tl); e["lowDamage"]=int(c["candidate_low_damage"]); e["standardDamage"]=int(c["candidate_standard_damage"]); e["overloadDamage"]=int(c["candidate_overload_damage"]); e["highDamage"]=int(c["candidate_overload_damage"]); e["accuracyPp"]=int(c["candidate_accuracy"]); e["standardRange"]=int(c["candidate_standard_range"]); e["maxRange"]=max(int(c["candidate_max_range"]),int(e["standardRange"])); base_low=int(e["lowTp"]); base_std=int(e["standardTp"]); base_over=int(e["overloadTp"]); new_low=max(1,base_low+int(c["candidate_low_tp_delta"])); std_gap=max(1,(base_std-base_low)+int(c["candidate_standard_gap_delta"])); over_gap=max(1,(base_over-base_std)+int(c["candidate_overload_gap_delta"])); e["lowTp"]=new_low; e["standardTp"]=new_low+std_gap; e["overloadTp"]=e["standardTp"]+over_gap; e["spen"]=int(c["candidate_spen"]); e["apen"]=0; e["strainLimit"]=int(c["candidate_strain_limit"])
    elif lane=="J":
        # joint rows carry prefixed actuals for one shortlisted K and E candidate.
        k=m.p("kinetic_main",tl); e=m.p("energy_main",tl)
        for key,profile_key in (("damage","damage"),("accuracy","accuracyPp"),("standard_range","standardRange"),("max_range","maxRange"),("apen","apen")): k[profile_key]=int(c[f"k_{key}"])
        k["spen"]=0
        e["lowDamage"]=int(c["e_low_damage"]); e["standardDamage"]=int(c["e_standard_damage"]); e["overloadDamage"]=int(c["e_overload_damage"]); e["highDamage"]=int(c["e_overload_damage"]); e["accuracyPp"]=int(c["e_accuracy"]); e["standardRange"]=int(c["e_standard_range"]); e["maxRange"]=int(c["e_max_range"]); base_low=int(e["lowTp"]); base_std=int(e["standardTp"]); base_over=int(e["overloadTp"]); new_low=max(1,base_low+int(c["e_low_tp_delta"])); std_gap=max(1,(base_std-base_low)+int(c["e_standard_gap_delta"])); over_gap=max(1,(base_over-base_std)+int(c["e_overload_gap_delta"])); e["lowTp"]=new_low; e["standardTp"]=new_low+std_gap; e["overloadTp"]=e["standardTp"]+over_gap; e["spen"]=int(c["e_spen"]); e["apen"]=0; e["strainLimit"]=int(c["e_strain_limit"])
    else: raise ValueError(lane)
    return m


def _matrix_for(resource: str, tl: int, cid: str):
    if _WORKER_BASE is None or _WORKER_CANDS is None or _WORKER_CACHE is None or _WORKER_LANE is None: raise RuntimeError("CP152 worker not initialized")
    key=(resource,tl,cid)
    if key not in _WORKER_CACHE: _WORKER_CACHE[key]=_apply_candidate(_WORKER_BASE[resource],tl,_WORKER_CANDS[cid],_WORKER_LANE)
    return _WORKER_CACHE[key]


def _task(args: tuple[int,dict[str,str],dict[str,Any],int,int]) -> dict[str,Any]:
    idx,src,c,seed,trials=args; tl=int(src["tl"]); m=_matrix_for(src["resource_ensemble_id"],tl,c["candidate_id"]); bound=bind_scenario(m,src)
    wc._WORKER_MATRICES={src["resource_ensemble_id"]:m}
    row=wc._substantive_task((idx,src,bound,seed,trials,UTILITY_COMBAT_DOCTRINE)); row.update({"lane":c["lane"],"candidate_id":c["candidate_id"],"candidate_index":c["candidate_index"]})
    for k,v in c.items():
        if k.startswith("candidate_") or k.startswith("code_") or k in ("k_candidate_id","e_candidate_id"): row[k]=v
    return row


def _lane_ledger(repo:Path,doc:dict[str,Any],lane:str)->list[dict[str,Any]]:
    if lane=="K":return k_candidate_ledger(repo,doc)
    if lane=="E":return e_candidate_ledger(repo,doc)
    raise ValueError(lane)


def run_lane_batch(repo:Path,study_path:Path,outdir:Path,lane:str,jobs:int=24,tl:int=1,candidate_start:int=0,candidate_end:int|None=None,trials:int|None=None,smoke_panel:bool=False)->dict[str,Any]:
    lane=lane.upper(); doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":errs}
    led=[r for r in _lane_ledger(repo,doc,lane) if int(r["tl"])==tl]; start=max(0,candidate_start); end=len(led) if candidate_end is None else min(len(led),candidate_end); selected=led[start:end]
    if not selected:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["empty-batch"]}
    contexts=_smoke_contexts(repo,doc,lane,tl) if smoke_panel else _contexts(repo,doc,lane,tl); ntrials=int(trials or (K_TRIALS if lane=="K" else E_TRIALS)); tasks=[]; idx=0
    for c in selected:
        for src in contexts: tasks.append((idx,src,c,int(doc["masterSeed"]),ntrials)); idx+=1
    outdir.mkdir(parents=True,exist_ok=True); jobs=max(1,min(jobs,len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc,selected,lane); rows=[_task(t) for t in tasks]
    else:
        ctx=get_context("spawn"); chunksize=min(16,max(1,len(tasks)//max(1,jobs*8)))
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc,selected,lane)) as ex: rows=list(ex.map(_task,tasks,chunksize=chunksize))
    rows.sort(key=lambda r:(int(r["candidate_index"]),int(r["scenario_index"]))); name=f"direct_fire_{lane.lower()}_candidate_context_results.csv"; _write_csv(outdir/name,rows)
    failures=[]
    if len(rows)!=len(selected)*len(contexts):failures.append("row-count")
    if any(int(r["error_trials"]) for r in rows):failures.append("errors")
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":152,"mode":"lane-batch","lane":lane,"passed":not failures,"failedGates":failures,"tl":tl,"smokePanel":smoke_panel,"candidateStart":start,"candidateEnd":end,"candidates":len(selected),"contextsPerCandidate":len(contexts),"candidateContextCells":len(rows),"trialsPerContext":ntrials,"combatTrials":len(rows)*ntrials,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errors":sum(int(r["error_trials"]) for r in rows)}
    (outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8"); return s


class _Agg:
    __slots__=("trials","wins","draws","turns","duration","caps","errors","damage","mode_low","mode_std","mode_over","tp_fulfill","tp_weight")
    def __init__(self): self.trials=self.wins=self.draws=self.caps=self.errors=0; self.turns=self.duration=self.damage=self.mode_low=self.mode_std=self.mode_over=self.tp_fulfill=self.tp_weight=0.0
    def add(self,r:dict[str,str],side:str):
        n=int(r["trials"]); self.trials+=n; self.wins+=int(r["a_wins"] if side=="A" else r["b_wins"]); self.draws+=int(r["draws"]); self.turns+=float(r["mean_turns_all"])*n; self.duration+=float(r["gameplay_duration_concern_rate"])*n; self.caps+=int(r["turn_cap_sentinels"]); self.errors+=int(r["error_trials"])
        dmg=float(r["a_damage_advantage_mean"]); self.damage+=(dmg if side=="A" else -dmg)*n; low=side.lower()
        self.mode_low+=float(r.get(f"mean_{low}_energy_low_shots",0) or 0)*n; self.mode_std+=float(r.get(f"mean_{low}_energy_standard_shots",0) or 0)*n; self.mode_over+=float(r.get(f"mean_{low}_energy_overload_shots",0) or 0)*n
        self.tp_fulfill+=float(r.get(f"{low}_tp_fulfillment_rate",1) or 0)*n; self.tp_weight+=n
    def row(self):
        n=self.trials or 1; modes=self.mode_low+self.mode_std+self.mode_over
        return {"trials":self.trials,"wins":self.wins,"win_rate":self.wins/n,"draw_rate":self.draws/n,"mean_turns":self.turns/n,"duration_concern_rate":self.duration/n,"mean_damage_advantage":self.damage/n,"turn_cap_sentinels":self.caps,"error_trials":self.errors,
                "mean_energy_low_shots":self.mode_low/n,"mean_energy_standard_shots":self.mode_std/n,"mean_energy_overload_shots":self.mode_over/n,"energy_low_shot_share":self.mode_low/modes if modes else 0.0,"energy_standard_shot_share":self.mode_std/modes if modes else 0.0,"energy_overload_shot_share":self.mode_over/modes if modes else 0.0,"mean_tp_fulfillment_rate":self.tp_fulfill/(self.tp_weight or 1)}


def _candidate_side(r:dict[str,str],weapon:str)->str:
    if r["side_a_weapon"]==weapon:return "A"
    if r["side_b_weapon"]==weapon:return "B"
    raise ValueError(f"{weapon} absent")


def _merge_lane(repo:Path,doc:dict[str,Any],lane:str,batch_root:Path,outdir:Path,expected_trials:int)->dict[str,Any]:
    weapon=lane; ledger=_lane_ledger(repo,doc,lane); led={(int(r["tl"]),r["candidate_id"]):r for r in ledger}; groups={}; opp={}; res={}; strata={}; factor={}; pair={}; audits=[]; seen=set(); total_rows=total_trials=total_caps=total_errors=0
    factors=K_FACTORS if lane=="K" else E_FACTORS
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json"; rp=d/f"direct_fire_{lane.lower()}_candidate_context_results.csv"
        if not sp.exists() or not rp.exists():continue
        s=json.loads(sp.read_text(encoding="utf-8-sig")); ok=bool(s.get("passed")) and s.get("lane")==lane and not bool(s.get("smokePanel")) and int(s.get("trialsPerContext",0))==expected_trials and int(s.get("errors",-1))==0; nr=nt=0
        if ok:
            with rp.open(encoding="utf-8-sig",newline="") as f:
                for r in csv.DictReader(f):
                    nr+=1; n=int(r["trials"]);nt+=n;total_rows+=1;total_trials+=n;total_caps+=int(r["turn_cap_sentinels"]);total_errors+=int(r["error_trials"]);key=(int(r["tl"]),r["candidate_id"],r["scenario_id"])
                    if key in seen:continue
                    seen.add(key); tl=int(r["tl"]); cid=r["candidate_id"]; c=led[(tl,cid)]; side=_candidate_side(r,weapon); opponent=r["side_b_weapon"] if side=="A" else r["side_a_weapon"]
                    for g,k in ((groups,(tl,cid)),(opp,(tl,cid,opponent)),(res,(tl,cid,r["resource_ensemble_id"])),(strata,(tl,cid,r["scenario_stratum"]))): g.setdefault(k,_Agg()).add(r,side)
                    for f1 in factors: factor.setdefault((tl,f1,int(c[f"code_{f1}"]),cid),_Agg()).add(r,side)
                    if (lane=="K") or c.get("candidate_id"):
                        for i,f1 in enumerate(factors):
                            for f2 in factors[i+1:]: pair.setdefault((tl,f1,int(c[f"code_{f1}"]),f2,int(c[f"code_{f2}"])),_Agg()).add(r,side)
        audits.append({"batch":d.name,"rows":nr,"combat_trials":nt,"passed":int(ok)})
    expected_cells=K_CELLS if lane=="K" else E_CELLS; expected_combats=K_COMBATS if lane=="K" else E_COMBATS
    errs=[]
    if total_rows!=expected_cells:errs.append("row-count")
    if total_trials!=expected_combats:errs.append("trial-count")
    if len(seen)!=expected_cells:errs.append("coverage")
    if total_errors:errs.append("errors")
    def conv(g,names):return [{**{n:v for n,v in zip(names,k)},**a.row()} for k,a in sorted(g.items(),key=lambda kv:tuple(str(x) for x in kv[0]))]
    overall=conv(groups,("tl","candidate_id")); opponent=conv(opp,("tl","candidate_id","opponent")); resource=conv(res,("tl","candidate_id","resource_ensemble_id")); stratum=conv(strata,("tl","candidate_id","scenario_stratum"))
    # Marginals aggregate across candidates sharing a code level (rather than candidate id).
    marg={}
    for r in overall: pass
    factor2={}
    # Re-read factor aggregation but collapse candidate id.
    for (tl,f,level,cid),a in factor.items():
        k=(tl,f,level); z=factor2.setdefault(k,_Agg());
        # combine _Agg without original rows
        z.trials+=a.trials;z.wins+=a.wins;z.draws+=a.draws;z.turns+=a.turns;z.duration+=a.duration;z.caps+=a.caps;z.errors+=a.errors;z.damage+=a.damage;z.mode_low+=a.mode_low;z.mode_std+=a.mode_std;z.mode_over+=a.mode_over;z.tp_fulfill+=a.tp_fulfill;z.tp_weight+=a.tp_weight
    marginals=conv(factor2,("tl","factor","level")); interactions=conv(pair,("tl","factor_1","level_1","factor_2","level_2"))
    # Add actual candidate parameters and useful robustness columns.
    opp_index=defaultdict(list)
    for r in opponent:opp_index[(int(r["tl"]),r["candidate_id"])].append(r)
    res_index=defaultdict(list)
    for r in resource:res_index[(int(r["tl"]),r["candidate_id"])].append(r)
    enriched=[]
    for r in overall:
        key=(int(r["tl"]),r["candidate_id"]); c=led[key]; ors=opp_index[key]; rrs=res_index[key]
        enriched.append({**r,**{k:v for k,v in c.items() if k.startswith("candidate_")},"min_opponent_win_rate":min(float(x["win_rate"]) for x in ors),"max_opponent_win_rate":max(float(x["win_rate"]) for x in ors),"resource_win_rate_range":max(float(x["win_rate"]) for x in rrs)-min(float(x["win_rate"]) for x in rrs),"promotion_allowed":0})
    _write_csv(outdir/"batch_merge_audit.csv",audits);_write_csv(outdir/f"direct_fire_{lane.lower()}_candidate_summary.csv",enriched);_write_csv(outdir/f"direct_fire_{lane.lower()}_candidate_opponent_response.csv",opponent);_write_csv(outdir/f"direct_fire_{lane.lower()}_candidate_resource_response.csv",resource);_write_csv(outdir/f"direct_fire_{lane.lower()}_candidate_stratum_response.csv",stratum);_write_csv(outdir/f"direct_fire_{lane.lower()}_factor_marginals.csv",marginals);_write_csv(outdir/f"direct_fire_{lane.lower()}_pairwise_response.csv",interactions)
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":152,"mode":"lane-merged","lane":lane,"passed":not errs,"failedGates":errs,"candidateContextCells":total_rows,"combatTrials":total_trials,"turnCapSentinels":total_caps,"errorTrials":total_errors,"automaticPromotion":False};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


def merge_lane(repo:Path,study_path:Path,lane:str,batch_root:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":errs}
    return _merge_lane(repo,doc,lane.upper(),batch_root,outdir,K_TRIALS if lane.upper()=="K" else E_TRIALS)


def _shortlist_score(r:dict[str,str],lane:str)->float:
    wr=float(r["win_rate"]); mn=float(r["min_opponent_win_rate"]); rr=float(r["resource_win_rate_range"]); target_penalty=abs(wr-0.50)
    # Favor competitive specialists over raw maxima. E gets extra penalty for mode collapse only when no low/overload use at all.
    mode_pen=0.0
    if lane=="E" and float(r.get("mean_energy_low_shots",0))==0 and float(r.get("mean_energy_overload_shots",0))==0: mode_pen=0.01
    return 0.45*mn + 0.35*(1-target_penalty) + 0.20*(1-rr) - mode_pen


def select_joint_shortlist(repo:Path,study_path:Path,k_merged:Path,e_merged:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc); outdir.mkdir(parents=True,exist_ok=True)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":errs}
    def read(path):return list(csv.DictReader(path.open(encoding="utf-8-sig",newline="")))
    kr=read(k_merged/"direct_fire_k_candidate_summary.csv"); er=read(e_merged/"direct_fire_e_candidate_summary.csv"); kled={(int(r["tl"]),r["candidate_id"]):r for r in k_candidate_ledger(repo,doc)}; eled={(int(r["tl"]),r["candidate_id"]):r for r in e_candidate_ledger(repo,doc)}
    kshort=[];eshort=[];joint=[]
    for tl in range(1,10):
        ks=sorted([r for r in kr if int(r["tl"])==tl],key=lambda r:(-_shortlist_score(r,"K"),abs(float(r["win_rate"])-0.5),r["candidate_id"]))[:JOINT_SHORTLIST_PER_FAMILY]
        es=sorted([r for r in er if int(r["tl"])==tl],key=lambda r:(-_shortlist_score(r,"E"),abs(float(r["win_rate"])-0.5),r["candidate_id"]))[:JOINT_SHORTLIST_PER_FAMILY]
        for rank,r in enumerate(ks,1):kshort.append({"tl":tl,"rank":rank,"score":_shortlist_score(r,"K"),**r})
        for rank,r in enumerate(es,1):eshort.append({"tl":tl,"rank":rank,"score":_shortlist_score(r,"E"),**r})
        idx=0
        for ka,ea in itertools.product(ks,es):
            kc=kled[(tl,ka["candidate_id"])]; ec=eled[(tl,ea["candidate_id"])]
            row={"lane":"J","candidate_id":f"DJ{tl:02d}-{idx:02d}","candidate_index":idx,"tl":tl,"k_candidate_id":ka["candidate_id"],"e_candidate_id":ea["candidate_id"]}
            for f in K_FACTORS:row[f"k_{f}"]=kc[f"candidate_{f}"]
            for f in E_FACTORS:row[f"e_{f}"]=ec[f"candidate_{f}"]
            joint.append(row);idx+=1
    _write_csv(outdir/"direct_fire_k_shortlist.csv",kshort);_write_csv(outdir/"direct_fire_e_shortlist.csv",eshort);_write_csv(outdir/"direct_fire_joint_candidate_ledger.csv",joint)
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":152,"mode":"joint-selection","passed":len(joint)==JOINT_CANDIDATES_PER_TL*9,"failedGates":[] if len(joint)==JOINT_CANDIDATES_PER_TL*9 else ["joint-count"],"kShortlistRows":len(kshort),"eShortlistRows":len(eshort),"jointTlCandidates":len(joint),"selectionPolicy":"competitive specialist score; no promotion; final ladder still requires cross-TL technology coherence"};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


def _read_joint_ledger(path:Path)->list[dict[str,Any]]:
    rows=[]
    with path.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            out=dict(r);out["candidate_index"]=int(out["candidate_index"]);out["tl"]=int(out["tl"])
            for k in list(out):
                if k.startswith("k_") and k!="k_candidate_id" or k.startswith("e_") and k!="e_candidate_id":
                    try:out[k]=int(float(out[k]))
                    except:pass
            rows.append(out)
    return rows


def run_joint_batch(repo:Path,study_path:Path,joint_ledger_path:Path,outdir:Path,jobs:int=24,tl:int=1,candidate_start:int=0,candidate_end:int|None=None,trials:int|None=None)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":errs}
    led=[r for r in _read_joint_ledger(joint_ledger_path) if int(r["tl"])==tl];start=max(0,candidate_start);end=len(led) if candidate_end is None else min(len(led),candidate_end);sel=led[start:end];contexts=_contexts(repo,doc,"J",tl);ntrials=int(trials or JOINT_TRIALS);tasks=[];idx=0
    for c in sel:
        for src in contexts:tasks.append((idx,src,c,int(doc["masterSeed"])+900000,ntrials));idx+=1
    outdir.mkdir(parents=True,exist_ok=True);jobs=max(1,min(jobs,len(tasks)))
    if jobs==1:_worker_init(str(repo),doc,sel,"J");rows=[_task(t) for t in tasks]
    else:
        ctx=get_context("spawn");chunksize=min(16,max(1,len(tasks)//max(1,jobs*8)))
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc,sel,"J")) as ex:rows=list(ex.map(_task,tasks,chunksize=chunksize))
    rows.sort(key=lambda r:(int(r["candidate_index"]),int(r["scenario_index"])));_write_csv(outdir/"direct_fire_joint_context_results.csv",rows);fails=[]
    if len(rows)!=len(sel)*len(contexts):fails.append("row-count")
    if any(int(r["error_trials"]) for r in rows):fails.append("errors")
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":152,"mode":"joint-batch","lane":"J","passed":not fails,"failedGates":fails,"tl":tl,"candidateStart":start,"candidateEnd":end,"candidates":len(sel),"contextsPerCandidate":len(contexts),"candidateContextCells":len(rows),"trialsPerContext":ntrials,"combatTrials":len(rows)*ntrials,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errors":sum(int(r["error_trials"]) for r in rows)};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


def merge_joint(repo:Path,study_path:Path,joint_ledger_path:Path,batch_root:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path);led={(int(r["tl"]),r["candidate_id"]):r for r in _read_joint_ledger(joint_ledger_path)};groups={};aud=[];seen=set();rowsn=trials=caps=errors=0
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json";rp=d/"direct_fire_joint_context_results.csv"
        if not sp.exists() or not rp.exists():continue
        s=json.loads(sp.read_text(encoding="utf-8-sig"));ok=bool(s.get("passed")) and int(s.get("trialsPerContext",0))==JOINT_TRIALS and int(s.get("errors",-1))==0;nr=nt=0
        if ok:
            with rp.open(encoding="utf-8-sig",newline="") as f:
                for r in csv.DictReader(f):
                    nr+=1;n=int(r["trials"]);nt+=n;rowsn+=1;trials+=n;caps+=int(r["turn_cap_sentinels"]);errors+=int(r["error_trials"]);key=(int(r["tl"]),r["candidate_id"],r["scenario_id"])
                    if key in seen:continue
                    seen.add(key);side=_candidate_side(r,"K");groups.setdefault((int(r["tl"]),r["candidate_id"]),_Agg()).add(r,side)
        aud.append({"batch":d.name,"rows":nr,"combat_trials":nt,"passed":int(ok)})
    errs=[]
    if rowsn!=JOINT_CELLS:errs.append("row-count")
    if trials!=JOINT_COMBATS:errs.append("trial-count")
    if errors:errs.append("errors")
    result=[]
    for key,a in sorted(groups.items()):result.append({"tl":key[0],"candidate_id":key[1],**{k:v for k,v in led[key].items() if k not in ("lane","tl","candidate_index","candidate_id")},**a.row()})
    _write_csv(outdir/"batch_merge_audit.csv",aud);_write_csv(outdir/"direct_fire_joint_response.csv",result)
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":152,"mode":"joint-merged","passed":not errs,"failedGates":errs,"jointCandidateContextCells":rowsn,"jointCombatTrials":trials,"turnCapSentinels":caps,"errorTrials":errors,"automaticPromotion":False};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s
