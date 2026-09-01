from __future__ import annotations

import copy
import csv
import hashlib
import itertools
import json
import math
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .direct_fire_joint_refinement import _apply_cp151_center, _resource_rows, _write_csv
from .ecology import EcologyBuild, EcologyVariant, build_space
from .canonical_combat import run_trial_full_map
from .stage_a_integration_analysis import _features_for_stratum, WEAPON_MAP, PAYLOAD_MAP
from .study import load_json
from .four_main_ladder_synthesis import _copy_matrix, _apply_package

RESULT_SCHEMA = "star-cluster-cp154-pds-lifecycle-closure-result-v0.1"
FAMILIES = ("Kinetic", "Energy", "AMM")
CHANCE_GRID = tuple(range(5, 50, 5))
K_AMMO_GRID = (15, 25, 35, 50, 60, 75, 100)
AMM_AMMO_GRID = (6, 12, 18, 25, 35, 50)
SCREEN_TRIALS = 25
DEEP_TRIALS = 100
LADDERS_PER_FAMILY = 8
DEEP_LADDERS = len(FAMILIES) * LADDERS_PER_FAMILY

CP153_EVIDENCE_HASHES = {
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_NATIVE_ACCEPTANCE_SUMMARY.json": "78837b9dce7fbc38ab6b7a4c535a8042402f9e1f7ec155d8ae1ca8957af0bd2d",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_KINETIC_LADDER_CANDIDATES.csv": "afe2b700d03eabc3ef310d431c21a8706657c7503d1f7004127a5fb9f93411f4",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_ENERGY_LADDER_CANDIDATES.csv": "d7271113e9e7af6b09fa95a135a8750a7f2479314142be06d61621f49fa741a6",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_MISSILE_LADDER_CANDIDATES.csv": "03aec1b5a9edb400020edbdd8e2006c964e3b386b222bbab4b6de9474f15fc93",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_PACKAGE_SUMMARY.csv": "002d7abae79cd0a5b09a150d7828a3118824ea9d36e73c006888110fec8c85f8",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_FAMILY_RESPONSE.csv": "aef4ab990d88907adea1cf9557ab625d4f4334e27cb50ba5eea89e52ea1bbbd4",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_PAIR_RESPONSE.csv": "0aeb8dcfa6c635881bb9264802da758d78d48266f205f0dca1edb67cfedeab5e",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_DEEP_STRATUM_RESPONSE.csv": "97843ff0b864b7ab4eef73f63d8ae1ff08f0a4833ff92fe0321b14da68aad46c",
    "docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_SCREEN_PACKAGE_SUMMARY.csv": "6506a5bdccef736482902d88f0dac6c214b7478c206cdbc454d8b82ca98843c5",
}


def _sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))


def _accepted_cp153(repo: Path) -> None:
    for rel,expected in CP153_EVIDENCE_HASHES.items():
        p=repo/rel
        if not p.is_file() or _sha(p)!=expected: raise ValueError(f"CP154 accepted CP153 evidence hash mismatch: {rel}")
    s=json.loads((repo/"docs/validation/evidence/checkpoint-154/accepted-cp153/CP153_NATIVE_ACCEPTANCE_SUMMARY.json").read_text(encoding="utf-8-sig"))
    if int(s.get("checkpoint",0))!=153 or int(s.get("substantiveCombatTrials",0))!=102346800 or int(s.get("substantiveErrorTrials",-1))!=0:
        raise ValueError("CP154 accepted CP153 evidence does not prove native completion")


def _matrix_profile_audit(repo: Path) -> list[dict[str,Any]]:
    out=[]
    archive=repo/"docs/archive/player_technology/pre-cp165-active"
    paths=list(archive.glob("technology_numerical_matrix_v0_*.json"))
    retained=repo/"docs/design/player_technology/technology_numerical_matrix_v0_9.json"
    if retained.is_file(): paths.append(retained)
    for path in sorted(paths,key=lambda p:p.name):
        d=load_json(path)
        for key,family in (("kinetic_pds","Kinetic"),("energy_pds","Energy"),("amm_pds","AMM")):
            for tl in range(1,10):
                r=d["profiles"][key][str(tl)]
                out.append({"matrix":path.name,"family":family,"tl":tl,"base_chance_pp":r.get("baseChancePp",""),"reaction_capacity":r.get("reactionCapacity",""),"readiness_tp":r.get("readinessTp",""),"ammo":r.get("ammo",""),"intercept_range":r.get("interceptRange",r.get("interceptionRange","")),"notes":r.get("notes","")})
    return out


def _cp153_maps(repo: Path):
    base=repo/"docs/validation/evidence/checkpoint-154/accepted-cp153"
    ks={(r["ladder_id"],int(r["tl"])):r for r in _read_csv(base/"CP153_KINETIC_LADDER_CANDIDATES.csv")}
    es={(r["ladder_id"],int(r["tl"])):r for r in _read_csv(base/"CP153_ENERGY_LADDER_CANDIDATES.csv")}
    ms={(r["family"],r["ladder_id"],int(r["tl"])):r for r in _read_csv(base/"CP153_MISSILE_LADDER_CANDIDATES.csv")}
    return ks,es,ms


def _cp153_package_row(repo: Path, tl: int, gp_ladder: str="M2") -> dict[str,Any]:
    ks,es,ms=_cp153_maps(repo); k=ks[("K1",tl)]; e=es[("E7",tl)]; gp=ms[("M_GP",gp_ladder,tl)]; sw=ms.get(("M_SWARMER","SW2",tl))
    return {
        "k_damage":int(float(k["damage"])),"k_accuracy":int(float(k["accuracy"])),"k_standard_range":int(float(k["standard_range"])),"k_max_range":int(float(k["max_range"])),"k_apen":int(float(k["apen"])),
        "e_low_damage":int(float(e["low_damage"])),"e_standard_damage":int(float(e["standard_damage"])),"e_overload_damage":int(float(e["overload_damage"])),"e_accuracy":int(float(e["accuracy"])),"e_standard_range":int(float(e["standard_range"])),"e_max_range":int(float(e["max_range"])),"e_low_tp":int(float(e["low_tp"])),"e_standard_gap":int(float(e["standard_gap"])),"e_overload_gap":int(float(e["overload_gap"])),"e_spen":int(float(e["spen"])),"e_strain_limit":int(float(e["strain_limit"])),
        "m_damage":int(float(gp["damage"])),"sw_packet_damage":"" if sw is None else int(float(sw["damage"])),
    }


def _base_matrix(repo: Path, doc: dict[str,Any], resource: str, gp_ladder: str="M2"):
    er,tr=_resource_rows(repo,doc)
    m=_apply_cp151_center(build_deep_resource_matrix(repo,doc["matrix"],resource,er,tr))
    return _apply_package(m,1,_cp153_package_row(repo,1,gp_ladder)) if False else m


def _main_matrix(repo: Path, doc: dict[str,Any], resource: str, tl: int, gp_ladder: str) -> Any:
    er,tr=_resource_rows(repo,doc); base=_apply_cp151_center(build_deep_resource_matrix(repo,doc["matrix"],resource,er,tr))
    return _apply_package(base,tl,_cp153_package_row(repo,tl,gp_ladder))


def _chance_levels(current: int) -> list[int]:
    return sorted(set(CHANCE_GRID+(int(current),)))


def _energy_profiles() -> list[dict[str,Any]]:
    out=[]
    for rc1 in (1,2,3):
        out.append({"reaction_capacity":1,"rc1_tp":rc1,"rc2_tp":"","safe_rc":1,"extra_strain":0,"strain_limit":0,"mode":"RC1"})
        for delta in (0,1,2):
            rc2=rc1+delta
            out.append({"reaction_capacity":2,"rc1_tp":rc1,"rc2_tp":rc2,"safe_rc":2,"extra_strain":0,"strain_limit":0,"mode":"RC2_SAFE"})
            for limit in (1,2,3,4):
                out.append({"reaction_capacity":2,"rc1_tp":rc1,"rc2_tp":rc2,"safe_rc":1,"extra_strain":1,"strain_limit":limit,"mode":"RC2_OVERCHARGED"})
    # dedup exact profiles (delta 0 remains meaningful but duplicates across semantic mode only where safe differs)
    seen=set(); rows=[]
    for r in out:
        k=tuple((x,r[x]) for x in sorted(r))
        if k not in seen: seen.add(k); rows.append(r)
    return rows


def _amm_profiles(tl: int) -> list[dict[str,Any]]:
    out=[]
    for rc1 in (1,2): out.append({"reaction_capacity":1,"rc1_tp":rc1,"rc2_tp":"","rc3_tp":"","range_one":0,"mode":"RC1"})
    for rc1 in (1,2):
        for delta in (0,1,2):
            rc2=rc1+delta
            out.append({"reaction_capacity":2,"rc1_tp":rc1,"rc2_tp":rc2,"rc3_tp":"","range_one":0,"mode":"RC2"})
    if tl>=5:
        for rc1,rc2,rc3 in ((1,2,2),(1,2,3),(1,2,4),(1,3,3),(1,3,4),(1,3,5),(2,3,3),(2,3,4),(2,3,5)):
            out.append({"reaction_capacity":3,"rc1_tp":rc1,"rc2_tp":rc2,"rc3_tp":rc3,"range_one":1,"mode":"RC3_RANGE1"})
    return out


def pds_candidate_ledger(repo: Path, doc: dict[str,Any]) -> list[dict[str,Any]]:
    _accepted_cp153(repo); raw=load_json(repo/doc["matrix"]); out=[]
    for tl in range(1,10):
        current={fam:raw["profiles"][key][str(tl)] for fam,key in (("Kinetic","kinetic_pds"),("Energy","energy_pds"),("AMM","amm_pds"))}
        idx=0
        for chance,rc,tp,ammo in itertools.product(_chance_levels(int(current["Kinetic"]["baseChancePp"])),(1,2),(1,2,3),K_AMMO_GRID):
            out.append({"family":"Kinetic","candidate_id":f"PK{tl:02d}-{idx:04d}","tl":tl,"candidate_index":idx,"base_chance_pp":chance,"reaction_capacity":rc,"rc1_tp":tp if rc==1 else 1,"rc2_tp":"" if rc==1 else tp,"rc3_tp":"","readiness_tp":tp,"ammo":ammo,"range_one":0,"safe_rc":rc,"extra_strain":0,"strain_limit":0,"mode":f"RC{rc}","promotion_allowed":0}); idx+=1
        idx=0
        for chance,p in itertools.product(_chance_levels(int(current["Energy"]["baseChancePp"])),_energy_profiles()):
            full_tp=int(p["rc1_tp"] if p["reaction_capacity"]==1 else p["rc2_tp"])
            out.append({"family":"Energy","candidate_id":f"PE{tl:02d}-{idx:04d}","tl":tl,"candidate_index":idx,"base_chance_pp":chance,"reaction_capacity":p["reaction_capacity"],"rc1_tp":p["rc1_tp"],"rc2_tp":p["rc2_tp"],"rc3_tp":"","readiness_tp":full_tp,"ammo":"","range_one":0,"safe_rc":p["safe_rc"],"extra_strain":p["extra_strain"],"strain_limit":p["strain_limit"],"mode":p["mode"],"promotion_allowed":0}); idx+=1
        idx=0
        for chance,p,ammo in itertools.product(_chance_levels(int(current["AMM"]["baseChancePp"])),_amm_profiles(tl),AMM_AMMO_GRID):
            rc=p["reaction_capacity"]; full_tp=int(p["rc1_tp"] if rc==1 else p["rc2_tp"] if rc==2 else p["rc3_tp"])
            out.append({"family":"AMM","candidate_id":f"PA{tl:02d}-{idx:04d}","tl":tl,"candidate_index":idx,"base_chance_pp":chance,"reaction_capacity":rc,"rc1_tp":p["rc1_tp"],"rc2_tp":p["rc2_tp"],"rc3_tp":p["rc3_tp"],"readiness_tp":full_tp,"ammo":ammo,"range_one":p["range_one"],"safe_rc":rc,"extra_strain":0,"strain_limit":0,"mode":p["mode"],"promotion_allowed":0}); idx+=1
    return out


def _apply_pds_candidate(base: Any, candidate: dict[str,Any]) -> Any:
    m=_copy_matrix(base); tl=int(candidate["tl"]); fam=str(candidate["family"]); key={"Kinetic":"kinetic_pds","Energy":"energy_pds","AMM":"amm_pds"}[fam]; p=m.p(key,tl)
    p["baseChancePp"]=int(candidate["base_chance_pp"]); p["reactionCapacity"]=int(candidate["reaction_capacity"]); p["readinessTp"]=int(candidate["readiness_tp"])
    p["rc1Tp"]=int(candidate["rc1_tp"])
    if candidate.get("rc2_tp","")!="": p["rc2Tp"]=int(candidate["rc2_tp"])
    else: p.pop("rc2Tp",None)
    if candidate.get("rc3_tp","")!="": p["rc3Tp"]=int(candidate["rc3_tp"])
    else: p.pop("rc3Tp",None)
    p["safeReactionCapacity"]=int(candidate.get("safe_rc",candidate["reaction_capacity"])); p["extraReactionStrain"]=int(candidate.get("extra_strain",0)); p["strainLimit"]=int(candidate.get("strain_limit",0)); p["rangeOneAttempt"]=bool(int(candidate.get("range_one",0)))
    if fam=="Energy": p["ammo"]=None
    else: p["ammo"]=int(candidate["ammo"])
    # Preserve current Space; the later AUX/whole-ship pass owns Space-value retuning.
    return m


def _resources(repo: Path, doc: dict[str,Any]) -> list[str]:
    er,_=_resource_rows(repo,doc); return sorted({r["ensemble_id"] for r in er})


def _attackers(tl:int) -> tuple[str,...]: return ("GP_M2","GP_M3") if tl==1 else ("GP_M2","GP_M3","SW2")
def _defenders(tl:int) -> tuple[str,...]: return ("K1","E7","M2") if tl==1 else ("K1","E7","M2","SW2")

def _weapon_code(x:str)->str:
    return {"GP_M2":"M_GP","GP_M3":"M_GP","SW2":"M_SWARMER","K1":"K","E7":"E","M2":"M_GP"}[x]

def _gp_ladder(attacker:str)->str: return "M3" if attacker=="GP_M3" else "M2"


def pds_contexts(repo: Path, doc: dict[str,Any], broad: bool) -> list[dict[str,Any]]:
    resources=_resources(repo,doc); strata=list(doc["pdsClosureDesign"]["strata"]); out=[]; idx=0
    for tl in range(1,10):
        combos=list(itertools.product(_attackers(tl),_defenders(tl),strata))
        for ci,(att,defn,stratum) in enumerate(combos):
            use_resources=[resources[(ci + 2*tl) % len(resources)]] if broad else resources
            for rid in use_resources:
                out.append({"scenario_index":idx,"scenario_id":f"cp154-{'b' if broad else 'd'}-{tl}-{att}-{defn}-{stratum}-{rid}","tl":tl,"attacker":att,"defender":defn,"side_a_weapon":_weapon_code(att),"side_b_weapon":_weapon_code(defn),"gp_ladder":_gp_ladder(att),"resource_ensemble_id":rid,"scenario_stratum":stratum,"geometry":"radius5_full_hex_adaptive"}); idx+=1
    return out


def _bind_candidate(matrix: Any, src: dict[str,Any], pds_family: str) -> EcologyVariant:
    tl=int(src["tl"]); stratum=src["scenario_stratum"]; f=_features_for_stratum(stratum,tl); qa,qb=f["start"]
    def make(side:str, weapon_variant:str, pds:str|None):
        fam=WEAPON_MAP[weapon_variant]; payload=PAYLOAD_MAP[weapon_variant]
        combat=build_space(matrix,tl,fam,1,1,bool(f["shield"]),bool(f["ecm"]),bool(f["eccm"]),pds,bool(f["hardener"]))
        cap=matrix.capacity(tl)
        if combat>cap: raise ValueError(f"illegal CP154 build {tl} {weapon_variant} {pds}: {combat}>{cap}")
        return EcologyBuild(id=f"cp154-{src['scenario_id']}-{side}",tl=tl,archetype=f"cp154-{stratum.lower()}",weapon_family=fam,main_count=1,reactor_count=1,shield=bool(f["shield"]),ecm=bool(f["ecm"]),eccm=bool(f["eccm"]),pds_family=pds,shield_hardener=bool(f["hardener"]),capacity=cap,combat_space=combat,mission_aux_space=cap-combat,missile_payload=payload,armor_profile=str(f["armor"]))
    a=make("A",src["side_a_weapon"],None); b=make("B",src["side_b_weapon"],pds_family)
    group=f"cp154-{src['scenario_id']}"
    return EcologyVariant(id=src["scenario_id"],tl=tl,side_a=a,side_b=b,movement_order="SideAFirst",geometry=src["geometry"],population="cp154-pds-lifecycle-closure",start_q_a=int(qa),start_q_b=int(qb),max_turns=int(f["max_turns"]),scenario_group=group,physical_id_a=group+":ship-a",physical_id_b=group+":ship-b")


def validate_study(doc: dict[str,Any]) -> list[str]:
    e=[]
    if doc.get("schemaVersion")!="star-cluster-cp154-pds-lifecycle-closure-study-v0.1":e.append("schema")
    if int(doc.get("checkpoint",0))!=154 or int(doc.get("baseCheckpoint",0))!=153:e.append("checkpoint")
    if doc.get("combatDoctrine")!="cp147_tactical_utility":e.append("doctrine")
    if doc.get("automaticPromotion") or doc.get("tuningAllowed"):e.append("promotion")
    return e


def validate_population(repo: Path, doc: dict[str,Any]) -> list[str]:
    try: _accepted_cp153(repo)
    except Exception as ex: return [str(ex)]
    rows=pds_candidate_ledger(repo,doc); e=[]
    for fam in FAMILIES:
        for tl in range(1,10):
            n=sum(r["family"]==fam and int(r["tl"])==tl for r in rows)
            if n<=0:e.append(f"empty-{fam}-{tl}")
    # Architecture constraints.
    if any(r["family"] in ("Kinetic","Energy") and int(r["reaction_capacity"])>2 for r in rows):e.append("local-rc3")
    if any(r["family"]!="AMM" and int(r["range_one"]) for r in rows):e.append("non-amm-range1")
    if any(r["family"]=="AMM" and int(r["reaction_capacity"])==3 and not int(r["range_one"]) for r in rows):e.append("amm-rc3-no-range1")
    if any(r["family"]=="AMM" and int(r["tl"])<5 and int(r["reaction_capacity"])==3 for r in rows):e.append("early-amm-rc3")
    return e


def run_plan(repo: Path, study_path: Path, outdir: Path) -> dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc); outdir.mkdir(parents=True,exist_ok=True)
    rows=pds_candidate_ledger(repo,doc) if not errs else []; broad=pds_contexts(repo,doc,True) if not errs else []; deep=pds_contexts(repo,doc,False) if not errs else []
    _write_csv(outdir/"pds_candidate_ledger.csv",rows); _write_csv(outdir/"pds_broad_contexts.csv",broad); _write_csv(outdir/"pds_deep_contexts.csv",deep); _write_csv(outdir/"pds_matrix_history_audit.csv",_matrix_profile_audit(repo))
    counts=[]
    for fam in FAMILIES:
        for tl in range(1,10): counts.append({"family":fam,"tl":tl,"candidates":sum(r["family"]==fam and int(r["tl"])==tl for r in rows),"broad_contexts":sum(int(x["tl"])==tl for x in broad)})
    _write_csv(outdir/"pds_candidate_counts.csv",counts)
    screen_cells=sum(r["candidates"]*r["broad_contexts"] for r in counts); screen_combats=screen_cells*int(doc["screenTrialsPerCell"]); deep_cells=DEEP_LADDERS*len(deep); deep_combats=deep_cells*int(doc["deepTrialsPerCell"])
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":154,"mode":"plan","passed":not errs,"failedGates":errs,"candidateTlRows":len(rows),"broadContexts":len(broad),"deepContextsPerLadder":len(deep),"screenCandidateContextCells":screen_cells,"screenCombatTrials":screen_combats,"deepLadders":DEEP_LADDERS,"deepCombatTrials":deep_combats,"substantiveCombatTrials":screen_combats+deep_combats,"automaticPromotion":False}
    (outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8"); return s


_C_REPO: Path|None=None; _C_DOC:dict[str,Any]|None=None; _C_CANDS:dict[str,dict[str,Any]]|None=None; _C_BASE:dict[tuple[str,int,str],Any]|None=None; _C_CACHE:dict[tuple[str,int,str,str],Any]|None=None

def _candidate_worker_init(repo_text:str,doc:dict[str,Any],candidates:list[dict[str,Any]]):
    global _C_REPO,_C_DOC,_C_CANDS,_C_BASE,_C_CACHE
    _C_REPO=Path(repo_text); _C_DOC=doc; _C_CANDS={r["candidate_id"]:r for r in candidates}; _C_BASE={}; _C_CACHE={}

def _matrix_for_candidate(src:dict[str,Any],cid:str):
    assert _C_REPO is not None and _C_DOC is not None and _C_CANDS is not None and _C_BASE is not None and _C_CACHE is not None
    tl=int(src["tl"]); rid=src["resource_ensemble_id"]; gp=src["gp_ladder"]; key=(rid,tl,gp)
    if key not in _C_BASE:_C_BASE[key]=_main_matrix(_C_REPO,_C_DOC,rid,tl,gp)
    ckey=(rid,tl,gp,cid)
    if ckey not in _C_CACHE:_C_CACHE[ckey]=_apply_pds_candidate(_C_BASE[key],_C_CANDS[cid])
    return _C_CACHE[ckey]

def _trial_row(matrix:Any,variant:EcologyVariant,src:dict[str,Any],cid:str,family:str,seed:int,trials:int)->dict[str,Any]:
    aw=bw=dr=caps=errors=turns=0; sums=defaultdict(float); maxstrain=0
    fields=("pds_attempts","pds_intercepts","pds_range_one_attempts","pds_range_one_intercepts","pds_overcharge_attempts","pds_overcharge_strain_added","power_pds","pds_power_shortfalls","power_weapons","power_spent_total","missile_terminal_arrivals","missile_hits")
    for i in range(trials):
        r=run_trial_full_map(matrix,variant,seed,i,combat_doctrine="cp147_tactical_utility")
        if r.error: errors+=1
        if r.winner=="A":aw+=1
        elif r.winner=="B":bw+=1
        else:dr+=1
        if r.termination_cause=="TURN_CAP_SENTINEL":caps+=1
        turns+=int(r.turns); t=r.side_b
        for f in fields:sums[f]+=float(getattr(t,f,0))
        maxstrain=max(maxstrain,int(getattr(t,"pds_max_strain",0)))
    out={"candidate_id":cid,"family":family,**src,"trials":trials,"a_wins":aw,"b_wins":bw,"draws":dr,"turn_cap_sentinels":caps,"error_trials":errors,"mean_turns":turns/max(1,trials),"defender_win_rate":bw/max(1,trials),"defender_decisive_share":bw/max(1,aw+bw),"max_pds_strain":maxstrain}
    for f,v in sums.items():out[f"mean_b_{f}"]=v/max(1,trials)
    return out

def _candidate_task(args):
    idx,src,cid,family,seed,trials=args; m=_matrix_for_candidate(src,cid); v=_bind_candidate(m,src,family); return _trial_row(m,v,src,cid,family,seed+idx*1009,trials)


def run_candidate_batch(repo:Path,study_path:Path,outdir:Path,family:str,tl:int,candidate_start:int=0,candidate_end:int|None=None,jobs:int=24,trials:int|None=None,smoke:bool=False)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":errs}
    allc=[r for r in pds_candidate_ledger(repo,doc) if r["family"]==family and int(r["tl"])==int(tl)]; start=max(0,candidate_start); end=len(allc) if candidate_end is None else min(len(allc),candidate_end); cands=allc[start:end]
    if not cands:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["empty-candidate-batch"]}
    contexts=[x for x in pds_contexts(repo,doc,True) if int(x["tl"])==int(tl)]
    if smoke: contexts=contexts[:min(6,len(contexts))]
    ntrials=int(trials or (1 if smoke else doc["screenTrialsPerCell"])); tasks=[]; idx=0
    for c in cands:
        for src in contexts:tasks.append((idx,src,c["candidate_id"],family,int(doc["masterSeed"]),ntrials));idx+=1
    outdir.mkdir(parents=True,exist_ok=True); jobs=max(1,min(jobs,len(tasks)))
    if jobs==1:
        _candidate_worker_init(str(repo),doc,cands); result=[_candidate_task(t) for t in tasks]
    else:
        ctx=get_context("spawn"); chunksize=min(12,max(1,len(tasks)//max(1,jobs*8)))
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_candidate_worker_init,initargs=(str(repo),doc,cands)) as ex: result=list(ex.map(_candidate_task,tasks,chunksize=chunksize))
    result.sort(key=lambda r:(r["candidate_id"],int(r["scenario_index"]))); _write_csv(outdir/"pds_candidate_context_results.csv",result)
    e=[]
    if len(result)!=len(cands)*len(contexts):e.append("row-count")
    if any(int(r["error_trials"]) for r in result):e.append("errors")
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":154,"mode":"candidate-smoke" if smoke else "candidate-screen-batch","passed":not e,"failedGates":e,"family":family,"tl":tl,"candidateStart":start,"candidateEnd":end,"candidates":len(cands),"contextsPerCandidate":len(contexts),"candidateContextCells":len(result),"trialsPerCell":ntrials,"combatTrials":len(result)*ntrials,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in result),"errors":sum(int(r["error_trials"]) for r in result)}
    (outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


def _agg_rows(rows:list[dict[str,str]],candidate_meta:dict[str,dict[str,Any]])->tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    groups=defaultdict(list)
    for r in rows:groups[r["candidate_id"]].append(r)
    summary=[]; responses=[]
    for cid,rs in groups.items():
        meta=candidate_meta[cid]; n=sum(int(r["trials"]) for r in rs); bw=sum(int(r["b_wins"]) for r in rs); aw=sum(int(r["a_wins"]) for r in rs); dr=sum(int(r["draws"]) for r in rs); att=defaultdict(lambda:[0,0])
        pds_attempts=sum(float(r["mean_b_pds_attempts"])*int(r["trials"]) for r in rs); pds_intercepts=sum(float(r["mean_b_pds_intercepts"])*int(r["trials"]) for r in rs); pds_power=sum(float(r["mean_b_power_pds"])*int(r["trials"]) for r in rs); over=sum(float(r["mean_b_pds_overcharge_attempts"])*int(r["trials"]) for r in rs); ro=sum(float(r["mean_b_pds_range_one_attempts"])*int(r["trials"]) for r in rs)
        for r in rs:
            k=r["attacker"]; att[k][0]+=int(r["b_wins"]);att[k][1]+=int(r["a_wins"])
        decisive=bw/max(1,bw+aw); attacker_devs=[]
        for k,(w,l) in sorted(att.items()):
            sh=w/max(1,w+l); attacker_devs.append(abs(sh-.5)); responses.append({"candidate_id":cid,"family":meta["family"],"tl":meta["tl"],"dimension":"attacker","level":k,"defender_decisive_share":sh,"decisive_trials":w+l})
        intercept_rate=pds_intercepts/max(1e-9,pds_attempts); over_share=over/max(1e-9,pds_attempts); range_share=ro/max(1e-9,pds_attempts); tp_per_attempt=pds_power/max(1e-9,pds_attempts)
        # Balance first; small regularizers preserve resource efficiency and keep
        # overcharged Energy from winning solely by routine strain use.
        score=abs(decisive-.5)+0.45*(max(attacker_devs) if attacker_devs else 0)+0.015*tp_per_attempt
        if meta["family"]=="Energy":score+=0.35*max(0.0,over_share-.35)
        summary.append({**meta,"trials":n,"defender_wins":bw,"attacker_wins":aw,"draws":dr,"defender_decisive_share":decisive,"max_attacker_decisive_deviation":max(attacker_devs) if attacker_devs else 0,"pds_attempts":pds_attempts,"pds_intercepts":pds_intercepts,"intercept_rate_per_attempt":intercept_rate,"pds_tp_per_attempt":tp_per_attempt,"overcharge_attempt_share":over_share,"range_one_attempt_share":range_share,"selection_score":score,"promotion_allowed":0})
    summary.sort(key=lambda r:(r["family"],int(r["tl"]),float(r["selection_score"]),r["candidate_id"]));return summary,responses


def merge_candidate_batches(repo:Path,study_path:Path,batch_root:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path); meta={r["candidate_id"]:r for r in pds_candidate_ledger(repo,doc)}; rows=[]; audit=[]; seen=set(); errors=0
    for d in sorted(p for p in batch_root.rglob("*") if p.is_dir()):
        sp=d/"summary.json"; rp=d/"pds_candidate_context_results.csv"
        if not sp.exists() or not rp.exists():continue
        s=json.loads(sp.read_text(encoding="utf-8-sig")); ok=bool(s.get("passed")) and s.get("mode")=="candidate-screen-batch" and int(s.get("errors",-1))==0
        nr=0
        if ok:
            for r in _read_csv(rp):
                key=(r["candidate_id"],r["scenario_id"])
                if key in seen:continue
                seen.add(key);rows.append(r);nr+=1;errors+=int(r["error_trials"])
        audit.append({"batch":str(d.relative_to(batch_root)),"rows":nr,"passed":int(ok)})
    expected=sum(1 for c in meta.values() for x in pds_contexts(repo,doc,True) if int(x["tl"])==int(c["tl"]))
    errs=[]
    if len(rows)!=expected:errs.append("coverage")
    if errors:errs.append("errors")
    summary,responses=_agg_rows(rows,meta); outdir.mkdir(parents=True,exist_ok=True);_write_csv(outdir/"batch_merge_audit.csv",audit);_write_csv(outdir/"pds_candidate_summary.csv",summary);_write_csv(outdir/"pds_candidate_attacker_response.csv",responses)
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":154,"mode":"candidate-merged","passed":not errs,"failedGates":errs,"candidateContextCells":len(rows),"candidates":len(summary),"combatTrials":sum(int(r["trials"]) for r in rows),"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errorTrials":errors,"automaticPromotion":False};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


def _compatible(prev:dict[str,Any],cur:dict[str,Any],family:str)->bool:
    if int(cur["reaction_capacity"])<int(prev["reaction_capacity"]):return False
    if int(cur["base_chance_pp"])<int(prev["base_chance_pp"]):return False
    if int(cur["base_chance_pp"])-int(prev["base_chance_pp"])>15:return False
    if family=="AMM" and int(prev["range_one"]) and not int(cur["range_one"]):return False
    # A strained Energy RC2 may mature into safe RC2, but not regress from safe
    # RC2 into a strain-requiring implementation at the same/higher RC.
    if family=="Energy" and prev["mode"]=="RC2_SAFE" and cur["mode"]=="RC2_OVERCHARGED":return False
    return True


def _jump_penalty(a:dict[str,Any],b:dict[str,Any],family:str)->float:
    p=0.002*abs(int(b["base_chance_pp"])-int(a["base_chance_pp"]))
    if int(a["reaction_capacity"])!=int(b["reaction_capacity"]):p+=0.012
    if int(a["readiness_tp"])!=int(b["readiness_tp"]):p+=0.004*abs(int(a["readiness_tp"])-int(b["readiness_tp"]))
    if family!="Energy" and str(a["ammo"])!=str(b["ammo"]):p+=0.002
    if family=="Energy" and a["mode"]!=b["mode"]:p+=0.004
    return p


def synthesize_ladders(repo:Path,study_path:Path,merged:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path); rows=_read_csv(merged/"pds_candidate_summary.csv"); outdir.mkdir(parents=True,exist_ok=True); allout=[]; errs=[]
    for family in FAMILIES:
        by={tl:[] for tl in range(1,10)}
        for r in rows:
            if r["family"]!=family:continue
            x=dict(r)
            for k in ("tl","base_chance_pp","reaction_capacity","readiness_tp","rc1_tp","safe_rc","extra_strain","strain_limit","range_one"):
                if x.get(k,"")!="":x[k]=int(float(x[k]))
            for k in ("rc2_tp","rc3_tp","ammo"):
                if x.get(k,"")!="":x[k]=int(float(x[k]))
            x["selection_score"]=float(x["selection_score"]);by[int(x["tl"])].append(x)
        for tl in by:by[tl].sort(key=lambda r:(r["selection_score"],r["candidate_id"]));by[tl]=by[tl][:120]
        beam=[(r["selection_score"],[r]) for r in by[1]]
        beam=sorted(beam,key=lambda x:x[0])[:600]
        for tl in range(2,10):
            nxt=[]
            for cost,path in beam:
                for r in by[tl]:
                    if _compatible(path[-1],r,family):nxt.append((cost+r["selection_score"]+_jump_penalty(path[-1],r,family),path+[r]))
            nxt.sort(key=lambda x:(x[0],tuple(r["candidate_id"] for r in x[1])));beam=nxt[:600]
            if not beam:errs.append(f"no-{family}-beam-tl{tl}");break
        chosen=[];signatures=set()
        for cost,path in beam:
            if family=="Energy": sig=(tuple(r["reaction_capacity"] for r in path),tuple(r["mode"] for r in path),tuple(r["strain_limit"] for r in path))
            elif family=="AMM": sig=(tuple(r["reaction_capacity"] for r in path),next((r["tl"] for r in path if r["range_one"]),0))
            else:sig=(tuple(r["reaction_capacity"] for r in path),)
            if sig in signatures:continue
            signatures.add(sig);chosen.append((cost,path))
            if len(chosen)>=LADDERS_PER_FAMILY:break
        for item in beam:
            if len(chosen)>=LADDERS_PER_FAMILY:break
            if item not in chosen:chosen.append(item)
        if len(chosen)<LADDERS_PER_FAMILY:errs.append(f"ladder-count-{family}")
        prefix={"Kinetic":"KP","Energy":"EP","AMM":"AP"}[family]
        for rank,(cost,path) in enumerate(chosen[:LADDERS_PER_FAMILY],1):
            lid=f"{prefix}{rank}"
            for r in path:allout.append({"family":family,"ladder_id":lid,"rank":rank,"ladder_selection_cost":cost,**{k:r[k] for k in ("candidate_id","tl","base_chance_pp","reaction_capacity","rc1_tp","rc2_tp","rc3_tp","readiness_tp","ammo","range_one","safe_rc","extra_strain","strain_limit","mode","defender_decisive_share","intercept_rate_per_attempt","pds_tp_per_attempt","overcharge_attempt_share","range_one_attempt_share","selection_score")},"promotion_allowed":0})
    _write_csv(outdir/"pds_ladder_candidates.csv",allout);s={"schemaVersion":RESULT_SCHEMA,"checkpoint":154,"mode":"ladder-synthesis","passed":not errs and len(allout)==DEEP_LADDERS*9,"failedGates":errs,"laddersPerFamily":LADDERS_PER_FAMILY,"deepLadders":DEEP_LADDERS,"ladderTlRows":len(allout),"automaticPromotion":False};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


_D_REPO:Path|None=None;_D_DOC:dict[str,Any]|None=None;_D_ROWS:dict[tuple[str,int],dict[str,Any]]|None=None;_D_BASE:dict[tuple[str,int,str],Any]|None=None;_D_CACHE:dict[tuple[str,int,str,str],Any]|None=None

def _deep_worker_init(repo_text:str,doc:dict[str,Any],rows:list[dict[str,Any]]):
    global _D_REPO,_D_DOC,_D_ROWS,_D_BASE,_D_CACHE
    _D_REPO=Path(repo_text);_D_DOC=doc;_D_ROWS={(r["ladder_id"],int(r["tl"])):r for r in rows};_D_BASE={};_D_CACHE={}

def _deep_task(args):
    idx,src,lid,family,seed,trials=args;assert _D_REPO is not None and _D_DOC is not None and _D_ROWS is not None and _D_BASE is not None and _D_CACHE is not None
    tl=int(src["tl"]);key=(src["resource_ensemble_id"],tl,src["gp_ladder"])
    if key not in _D_BASE:_D_BASE[key]=_main_matrix(_D_REPO,_D_DOC,key[0],tl,key[2])
    ckey=(key[0],tl,key[2],lid); cand=_D_ROWS[(lid,tl)]
    if ckey not in _D_CACHE:_D_CACHE[ckey]=_apply_pds_candidate(_D_BASE[key],cand)
    m=_D_CACHE[ckey];v=_bind_candidate(m,src,family);row=_trial_row(m,v,src,cand["candidate_id"],family,seed+idx*1013,trials);row["ladder_id"]=lid;return row


def run_deep_batch(repo:Path,study_path:Path,ladder_path:Path,outdir:Path,ladder_start:int=0,ladder_end:int|None=None,jobs:int=24,trials:int|None=None)->dict[str,Any]:
    doc=load_json(study_path);rows=_read_csv(ladder_path); ids=[];meta={}
    for r in rows:
        if r["ladder_id"] not in ids:ids.append(r["ladder_id"]);meta[r["ladder_id"]]=r["family"]
    start=max(0,ladder_start);end=len(ids) if ladder_end is None else min(len(ids),ladder_end);sel=ids[start:end]
    if not sel:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["empty-deep-batch"]}
    selected=[r for r in rows if r["ladder_id"] in sel];contexts=pds_contexts(repo,doc,False);ntrials=int(trials or doc["deepTrialsPerCell"]);tasks=[];idx=0
    for lid in sel:
        fam=meta[lid]
        for src in contexts:tasks.append((idx,src,lid,fam,int(doc["masterSeed"])+500000,ntrials));idx+=1
    outdir.mkdir(parents=True,exist_ok=True);jobs=max(1,min(jobs,len(tasks)))
    if jobs==1:_deep_worker_init(str(repo),doc,selected);result=[_deep_task(t) for t in tasks]
    else:
        ctx=get_context("spawn");chunksize=min(12,max(1,len(tasks)//max(1,jobs*8)))
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_deep_worker_init,initargs=(str(repo),doc,selected)) as ex:result=list(ex.map(_deep_task,tasks,chunksize=chunksize))
    result.sort(key=lambda r:(r["ladder_id"],int(r["scenario_index"])));_write_csv(outdir/"pds_deep_context_results.csv",result);errs=[]
    if len(result)!=len(sel)*len(contexts):errs.append("row-count")
    if any(int(r["error_trials"]) for r in result):errs.append("errors")
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":154,"mode":"deep-batch","passed":not errs,"failedGates":errs,"ladderStart":start,"ladderEnd":end,"ladders":len(sel),"contextsPerLadder":len(contexts),"ladderContextCells":len(result),"trialsPerCell":ntrials,"combatTrials":len(result)*ntrials,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in result),"errors":sum(int(r["error_trials"]) for r in result)};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s


def merge_deep(repo:Path,study_path:Path,ladder_path:Path,batch_root:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path);ladder_rows=_read_csv(ladder_path);meta={}
    for r in ladder_rows:meta.setdefault(r["ladder_id"],r["family"])
    rows=[];seen=set();audit=[];errors=0
    for d in sorted(p for p in batch_root.rglob("*") if p.is_dir()):
        sp=d/"summary.json";rp=d/"pds_deep_context_results.csv"
        if not sp.exists() or not rp.exists():continue
        s=json.loads(sp.read_text(encoding="utf-8-sig"));ok=bool(s.get("passed")) and s.get("mode")=="deep-batch" and int(s.get("errors",-1))==0;nr=0
        if ok:
            for r in _read_csv(rp):
                key=(r["ladder_id"],r["scenario_id"])
                if key in seen:continue
                seen.add(key);rows.append(r);nr+=1;errors+=int(r["error_trials"])
        audit.append({"batch":str(d.relative_to(batch_root)),"rows":nr,"passed":int(ok)})
    expected=DEEP_LADDERS*len(pds_contexts(repo,doc,False));errs=[]
    if len(rows)!=expected:errs.append("coverage")
    if errors:errs.append("errors")
    by=defaultdict(list)
    for r in rows:by[r["ladder_id"]].append(r)
    summary=[];responses=[]
    for lid,rs in by.items():
        n=sum(int(r["trials"]) for r in rs);bw=sum(int(r["b_wins"]) for r in rs);aw=sum(int(r["a_wins"]) for r in rs);dr=sum(int(r["draws"]) for r in rs);fam=meta[lid]
        pa=sum(float(r["mean_b_pds_attempts"])*int(r["trials"]) for r in rs);pi=sum(float(r["mean_b_pds_intercepts"])*int(r["trials"]) for r in rs);pp=sum(float(r["mean_b_power_pds"])*int(r["trials"]) for r in rs);ov=sum(float(r["mean_b_pds_overcharge_attempts"])*int(r["trials"]) for r in rs);ro=sum(float(r["mean_b_pds_range_one_attempts"])*int(r["trials"]) for r in rs)
        dims={}
        for dim in ("attacker","defender","resource_ensemble_id","scenario_stratum","tl"):
            gd=defaultdict(lambda:[0,0,0])
            for r in rs:
                k=str(r[dim]);gd[k][0]+=int(r["b_wins"]);gd[k][1]+=int(r["a_wins"]);gd[k][2]+=int(r["draws"])
            vals=[]
            for level,(w,l,d) in sorted(gd.items()):
                sh=w/max(1,w+l);vals.append(sh);responses.append({"ladder_id":lid,"family":fam,"dimension":dim,"level":level,"defender_decisive_share":sh,"wins":w,"losses":l,"draws":d})
            dims[dim]=max(abs(x-.5) for x in vals) if vals else 0
        decisive=bw/max(1,bw+aw);summary.append({"ladder_id":lid,"family":fam,"trials":n,"defender_wins":bw,"attacker_wins":aw,"draws":dr,"defender_decisive_share":decisive,"max_attacker_deviation":dims["attacker"],"max_defender_main_deviation":dims["defender"],"max_resource_deviation":dims["resource_ensemble_id"],"max_stratum_deviation":dims["scenario_stratum"],"max_tl_deviation":dims["tl"],"pds_attempts":pa,"pds_intercepts":pi,"intercept_rate_per_attempt":pi/max(1e-9,pa),"pds_tp_per_attempt":pp/max(1e-9,pa),"overcharge_attempt_share":ov/max(1e-9,pa),"range_one_attempt_share":ro/max(1e-9,pa),"selection_score":abs(decisive-.5)+0.35*dims["attacker"]+0.15*dims["resource_ensemble_id"]+0.10*dims["scenario_stratum"],"promotion_allowed":0})
    summary.sort(key=lambda r:(r["family"],float(r["selection_score"]),r["ladder_id"]));_write_csv(outdir/"batch_merge_audit.csv",audit);_write_csv(outdir/"pds_deep_ladder_summary.csv",summary);_write_csv(outdir/"pds_deep_response.csv",responses)
    # Offline triad combinations: no interaction term is invented; this is a
    # shortlist index over three independently confirmed PDS response surfaces.
    famrows={f:[r for r in summary if r["family"]==f] for f in FAMILIES};tri=[]
    for k,e,a in itertools.product(famrows["Kinetic"],famrows["Energy"],famrows["AMM"]):
        shares=[float(k["defender_decisive_share"]),float(e["defender_decisive_share"]),float(a["defender_decisive_share"])];score=max(shares)-min(shares)+sum(abs(x-.5) for x in shares)+0.15*float(e["overcharge_attempt_share"])
        tri.append({"kinetic_ladder":k["ladder_id"],"energy_ladder":e["ladder_id"],"amm_ladder":a["ladder_id"],"kinetic_decisive_share":shares[0],"energy_decisive_share":shares[1],"amm_decisive_share":shares[2],"triad_selection_score":score,"promotion_allowed":0})
    tri.sort(key=lambda r:(float(r["triad_selection_score"]),r["kinetic_ladder"],r["energy_ladder"],r["amm_ladder"]));_write_csv(outdir/"pds_triad_shortlist.csv",tri)
    s={"schemaVersion":RESULT_SCHEMA,"checkpoint":154,"mode":"deep-merged","passed":not errs,"failedGates":errs,"ladders":len(summary),"ladderContextCells":len(rows),"combatTrials":sum(int(r["trials"]) for r in rows),"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errorTrials":errors,"triadCombinations":len(tri),"automaticPromotion":False};(outdir/"summary.json").write_text(json.dumps(s,indent=2)+"\n",encoding="utf-8");return s
