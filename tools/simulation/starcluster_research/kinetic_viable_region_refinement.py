from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .kinetic_full_characteristic_sweep import (
    _aggregate,
    _trial_aggregate as _cp149_trial_aggregate,
    _worker_init as _cp149_worker_init,
    _write_csv,
    kinetic_contexts,
    smoke_contexts,
)
from .stage_a_integration_analysis import _read_csv, _resource_rows
from .study import load_json

RESULT_SCHEMA = "star-cluster-cp150-kinetic-viable-region-refinement-result-v0.1"
EXPECTED_CONTEXTS = 2600
DEFAULT_TRIALS = 200
EXPECTED_CANDIDATES_BY_TL = {1: 18, 2: 81, 3: 27, 4: 72, 5: 81, 6: 4, 7: 9, 8: 45, 9: 12}
EXPECTED_TL_CANDIDATES = sum(EXPECTED_CANDIDATES_BY_TL.values())
EXPECTED_CANDIDATE_CONTEXT_CELLS = 18 * 200 + sum(EXPECTED_CANDIDATES_BY_TL[tl] * 300 for tl in range(2, 10))
EXPECTED_SUBSTANTIVE_COMBATS = EXPECTED_CANDIDATE_CONTEXT_CELLS * DEFAULT_TRIALS
EXPECTED_SMOKE_COMBATS = 18 * 20 + sum(EXPECTED_CANDIDATES_BY_TL[tl] * 30 for tl in range(2, 10))

# CP150 deliberately removes factors that CP149 showed were non-binding for viable Kinetic candidates:
# firing TP delta=0, ammo=100, Space unchanged, SPEN=0. Active factors vary by TL based on
# the accepted CP149 response surface. Range profiles are (standard_range_delta, extended_band_delta).
TL_REFINEMENT: dict[int, dict[str, Any]] = {
    1: {"damage": [0, 1, 2], "accuracy": [0, 2, 5], "apen": [0], "range_profiles": [(0, 0), (0, 1)]},
    2: {"damage": [0, 1, 2], "accuracy": [0, 5, 10], "apen": [0, 1, 2], "range_profiles": [(0, 0), (1, 0), (0, 1)]},
    3: {"damage": [0, 1, 2], "accuracy": [0, 5, 10], "apen": [0], "range_profiles": [(0, 0), (1, 0), (0, 1)]},
    4: {"damage": [0, 1, 2, 3], "accuracy": [0, 2, 5], "apen": [0], "range_profiles": [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)]},
    5: {"damage": [0, 1, 2], "accuracy": [0, 2, 5], "apen": [0, 1, 2], "range_profiles": [(0, 0), (1, 0), (0, 1)]},
    6: {"damage": [0, 1, 2, 3], "accuracy": [0], "apen": [0], "range_profiles": [(0, 0)]},
    7: {"damage": [0, 1, 2], "accuracy": [0], "apen": [0, 1, 2], "range_profiles": [(0, 0)]},
    8: {"damage": [0, 1, 2, 3, 4], "accuracy": [0], "apen": [0, 1, 2], "range_profiles": [(0, 0), (1, 0), (0, 1)]},
    9: {"damage": [0, 1, 2, 3], "accuracy": [0], "apen": [0, 1, 2], "range_profiles": [(0, 0)]},
}

EVIDENCE_HASHES = {
    "docs/validation/evidence/checkpoint-150/CP149_NATIVE_ACCEPTANCE_SUMMARY.json": "a91a3fbc5b625b4dfd4713abe747f62c71a8e0a2030871df7a01ada27145bb59",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_AXIAL_EFFECTS.csv": "c9aaa8dbecfbe40a9070498f6c19a9b272b3c6b92665da3026b49ddd772cece4",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_PAIRWISE_INTERACTIONS.csv": "a6fd68299591ac5f0d6bb11175e363c905189462b6b172620d01fd0e78355eb9",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_TL_RESPONSE.csv": "3b33437d953dd2096f8c9568044b1d1c0a1f6573bab00b5b34574d49bc8b716c",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_OPPONENT_RESPONSE.csv": "0d2b89f0ad9a781b03dc83d7c4ad09fa772ed97162705728c3e42562c9b8a1db",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_ARMOR_ROLE_RESPONSE.csv": "4969fbac45c5c2a4c843ae373348d32e81de913364423b641878b4bff67e8736",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_COMBAT_PARETO_CANDIDATES.csv": "55e5337795e73a1a1ad9cfb8a22054e57e1e96e2cdd49d5f3e257473935f4dc3",
    "docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_LEDGER.csv": "8a83db2ea00ce178c26d7bcc87596ce89714bdab75b1360b244c98332f4349b1",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _read_evidence(repo: Path) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for rel, expected in EVIDENCE_HASHES.items():
        p = repo / rel
        if not p.is_file() or _sha(p) != expected:
            raise ValueError(f"CP150 accepted CP149 evidence hash mismatch: {rel}")
        if p.suffix.lower() == ".csv":
            out[p.name] = _read_csv(p)
    summary = json.loads((repo / "docs/validation/evidence/checkpoint-150/CP149_NATIVE_ACCEPTANCE_SUMMARY.json").read_text(encoding="utf-8-sig"))
    if int(summary.get("checkpoint", 0)) != 149 or int(summary.get("substantiveCombatTrials", 0)) != 42380000 or int(summary.get("substantiveErrorTrials", -1)) != 0:
        raise ValueError("CP150 accepted CP149 native summary does not prove the 42.38M sweep")
    return out


def _grid_rows_for_tl(tl: int) -> list[dict[str, int]]:
    spec = TL_REFINEMENT[int(tl)]
    out: list[dict[str, int]] = []
    for damage, accuracy, apen, rp in product(spec["damage"], spec["accuracy"], spec["apen"], spec["range_profiles"]):
        std, ext = rp
        out.append({
            "damage_delta": int(damage),
            "accuracy_delta_pp": int(accuracy),
            "apen_delta": int(apen),
            "standard_range_delta": int(std),
            "extended_band_delta": int(ext),
            "firing_tp_delta": 0,
            "ammo_level": 100,
        })
    return out


def candidate_ledger(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    _read_evidence(repo)
    er, tr = _resource_rows(repo, doc)
    central = build_deep_resource_matrix(repo, doc["matrix"], "R1_CENTRAL_NO_MAJOR", er, tr)
    rows: list[dict[str, Any]] = []
    for tl in range(1, 10):
        k = central.p("kinetic_main", tl); e = central.p("energy_main", tl)
        base_std = int(k["standardRange"]); base_band = int(k["maxRange"]) - base_std
        for i, g in enumerate(_grid_rows_for_tl(tl)):
            std = max(1, base_std + g["standard_range_delta"])
            band = max(0, base_band + g["extended_band_delta"])
            actual = {
                "accuracyPp": int(k["accuracyPp"]) + g["accuracy_delta_pp"],
                "damage": max(1, int(k["damage"]) + g["damage_delta"]),
                "apen": max(0, int(k["apen"]) + g["apen_delta"]),
                "standardRange": std,
                "maxRange": std + band,
            }
            if actual["accuracyPp"] > int(e["accuracyPp"]) or actual["standardRange"] > int(e["standardRange"]) or actual["maxRange"] > int(e["maxRange"]):
                raise ValueError(f"CP150 grid crossed Energy identity ceiling at TL{tl}: {g}")
            boundary = []
            if actual["accuracyPp"] == int(e["accuracyPp"]): boundary.append("ACC_EQ_E")
            if actual["standardRange"] == int(e["standardRange"]): boundary.append("STD_RANGE_EQ_E")
            if actual["maxRange"] == int(e["maxRange"]): boundary.append("MAX_RANGE_EQ_E")
            rows.append({
                "candidate_id": f"KR{tl:02d}-{i:03d}",
                "tl": tl,
                "design_index": i,
                "design_class": "tl_specific_full_factorial_refinement",
                "code_accuracy_delta_pp": g["accuracy_delta_pp"],
                "code_damage_delta": g["damage_delta"],
                "code_apen_delta": g["apen_delta"],
                "code_firing_tp_delta": 0,
                "code_standard_range_delta": g["standard_range_delta"],
                "code_extended_band_delta": g["extended_band_delta"],
                "code_ammo_level": 0,
                **g,
                "range_profile": f"STD{g['standard_range_delta']:+d}_EXT{g['extended_band_delta']:+d}",
                "central_base_accuracyPp": int(k["accuracyPp"]), "candidate_accuracyPp": actual["accuracyPp"],
                "central_energy_accuracyPp": int(e["accuracyPp"]),
                "central_base_damage": int(k["damage"]), "candidate_damage": actual["damage"],
                "central_base_apen": int(k["apen"]), "candidate_apen": actual["apen"], "candidate_spen": 0,
                "central_base_firingTp": int(k["firingTp"]), "central_candidate_firingTp": int(k["firingTp"]),
                "central_base_standardRange": base_std, "candidate_standardRange": actual["standardRange"], "central_energy_standardRange": int(e["standardRange"]),
                "central_base_maxRange": int(k["maxRange"]), "candidate_maxRange": actual["maxRange"], "central_energy_maxRange": int(e["maxRange"]),
                "central_base_ammo": int(k["ammo"]), "candidate_ammo": 100,
                "identity_preserved": 1, "identity_boundary_touch": int(bool(boundary)), "identity_boundary_flags": ";".join(boundary),
                "promotion_allowed": 0,
            })
    return rows


def refinement_design_summary(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = candidate_ledger(repo, doc)
    out=[]
    for tl in range(1,10):
        rows=[r for r in ledger if int(r["tl"])==tl]
        spec=TL_REFINEMENT[tl]
        out.append({
            "tl":tl,"candidates":len(rows),
            "damage_levels":";".join(map(str,spec["damage"])),
            "accuracy_delta_pp_levels":";".join(map(str,spec["accuracy"])),
            "apen_delta_levels":";".join(map(str,spec["apen"])),
            "range_profiles":";".join(f"{a},{b}" for a,b in spec["range_profiles"]),
            "firing_tp_delta":0,"ammo_level":100,"spen":0,
            "identity_preserved":int(all(int(r["identity_preserved"])==1 for r in rows)),
        })
    return out


def validate_study(doc: dict[str, Any]) -> list[str]:
    e=[]
    if doc.get("schemaVersion") != "star-cluster-cp150-kinetic-viable-region-refinement-study-v0.1": e.append("schemaVersion")
    if int(doc.get("checkpoint",0)) != 150: e.append("checkpoint")
    if int(doc.get("baseCheckpoint",0)) != 149: e.append("baseCheckpoint")
    if doc.get("combatDoctrine") != "cp147_tactical_utility": e.append("combatDoctrine")
    if int(doc.get("expectedKineticContexts",0)) != EXPECTED_CONTEXTS: e.append("expectedKineticContexts")
    if int(doc.get("tlCandidateCount",0)) != EXPECTED_TL_CANDIDATES: e.append("tlCandidateCount")
    if int(doc.get("candidateContextCells",0)) != EXPECTED_CANDIDATE_CONTEXT_CELLS: e.append("candidateContextCells")
    if int(doc.get("trialsPerCandidateContext",0)) != DEFAULT_TRIALS: e.append("trialsPerCandidateContext")
    if int(doc.get("substantiveCombatTrials",0)) != EXPECTED_SUBSTANTIVE_COMBATS: e.append("substantiveCombatTrials")
    if int(doc.get("smokeCombatTrials",0)) != EXPECTED_SMOKE_COMBATS: e.append("smokeCombatTrials")
    if int(doc.get("batchCandidates",0)) != 12: e.append("batchCandidates")
    if doc.get("kineticSpenPolicy") != "fixed-zero-family-identity": e.append("kineticSpenPolicy")
    if doc.get("firingTpPolicy") != "freeze-cp148-executable-by-resource-environment": e.append("firingTpPolicy")
    if doc.get("ammoPolicy") != "freeze-100": e.append("ammoPolicy")
    if doc.get("spacePolicy") != "freeze-cp148-kinetic-space": e.append("spacePolicy")
    if bool(doc.get("tuningAllowed",True)): e.append("tuningAllowed")
    if bool(doc.get("automaticPromotion",True)): e.append("automaticPromotion")
    if bool(doc.get("stageBAutomatic",True)): e.append("stageBAutomatic")
    return e


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    e=[]
    try:
        _read_evidence(repo)
        contexts=kinetic_contexts(repo,doc)
        if len(contexts)!=EXPECTED_CONTEXTS:e.append("kinetic-context-count")
        ledger=candidate_ledger(repo,doc)
        if len(ledger)!=EXPECTED_TL_CANDIDATES:e.append("candidate-count")
        for tl,n in EXPECTED_CANDIDATES_BY_TL.items():
            if sum(int(r["tl"])==tl for r in ledger)!=n:e.append(f"candidate-count-tl{tl}")
        if len({r["candidate_id"] for r in ledger})!=len(ledger):e.append("candidate-id-uniqueness")
        if any(int(r["candidate_spen"])!=0 or int(r["firing_tp_delta"])!=0 or int(r["ammo_level"])!=100 for r in ledger):e.append("frozen-factor-boundary")
        if any(int(r["identity_preserved"])!=1 or int(r["promotion_allowed"])!=0 for r in ledger):e.append("identity-promotion-boundary")
    except Exception as ex:
        e.append(f"population-exception:{ex}")
    return e


def _pareto(candidate_tl:list[dict[str,Any]], opponent:list[dict[str,Any]], role:list[dict[str,Any]], ledger:list[dict[str,Any]])->list[dict[str,Any]]:
    opp={(int(r["tl"]),r["candidate_id"],r["opponent_weapon"]):r for r in opponent}
    rolemap={(int(r["tl"]),r["candidate_id"]):r for r in role}
    led={(int(r["tl"]),r["candidate_id"]):r for r in ledger}
    out=[]
    for tl in range(1,10):
        rs=[r for r in candidate_tl if int(r["tl"])==tl]; metrics={}
        for r in rs:
            cid=r["candidate_id"]
            ovals=[float(x["k_win_rate"]) for x in opponent if int(x["tl"])==tl and x["candidate_id"]==cid]
            armor=float(rolemap.get((tl,cid),{}).get("k_win_rate",0))
            metrics[cid]=(float(r["k_win_rate"]),min(ovals) if ovals else 0,armor,float(r["mean_damage_advantage"]))
        for r in rs:
            cid=r["candidate_id"];dom=[]
            for o in rs:
                oid=o["candidate_id"]
                if oid==cid:continue
                a=metrics[oid];b=metrics[cid]
                if all(x>=y-1e-12 for x,y in zip(a,b)) and any(x>y+1e-12 for x,y in zip(a,b)):dom.append(oid)
            l=led[(tl,cid)]
            out.append({**r,"worst_opponent_win_rate":metrics[cid][1],"armor_role_win_rate":metrics[cid][2],
                        "armor_role_margin_vs_overall":metrics[cid][2]-metrics[cid][0],
                        "combat_pareto_viable":int(not dom),"combat_dominated_by":";".join(dom[:25]),
                        "identity_preserved":l["identity_preserved"],"identity_boundary_touch":l["identity_boundary_touch"],
                        "identity_boundary_flags":l["identity_boundary_flags"],"promotion_allowed":0})
    return out


def _parameter_marginals(candidate_tl:list[dict[str,Any]], ledger:list[dict[str,Any]]) -> list[dict[str,Any]]:
    metric={(int(r["tl"]),r["candidate_id"]):r for r in candidate_tl}; out=[]
    fields=("damage_delta","accuracy_delta_pp","apen_delta","range_profile")
    for tl in range(1,10):
        ltl=[r for r in ledger if int(r["tl"])==tl]
        for f in fields:
            values=sorted({str(r[f]) for r in ltl})
            if len(values)<=1:continue
            for v in values:
                rs=[metric[(tl,r["candidate_id"])] for r in ltl if str(r[f])==v]
                out.append({"tl":tl,"factor":f,"level":v,"candidates":len(rs),
                            "mean_k_win_rate":statistics.fmean(float(x["k_win_rate"]) for x in rs),
                            "mean_damage_advantage":statistics.fmean(float(x["mean_damage_advantage"]) for x in rs),
                            "mean_turns":statistics.fmean(float(x["mean_turns"]) for x in rs)})
    return out


def _pairwise_grid(candidate_tl:list[dict[str,Any]], ledger:list[dict[str,Any]]) -> list[dict[str,Any]]:
    metric={(int(r["tl"]),r["candidate_id"]):r for r in candidate_tl};out=[]
    fields=("damage_delta","accuracy_delta_pp","apen_delta","range_profile")
    for tl in range(1,10):
        ltl=[r for r in ledger if int(r["tl"])==tl]
        active=[f for f in fields if len({str(r[f]) for r in ltl})>1]
        for i,f1 in enumerate(active):
            for f2 in active[i+1:]:
                groups=defaultdict(list)
                for r in ltl:groups[(str(r[f1]),str(r[f2]))].append(metric[(tl,r["candidate_id"])])
                for (v1,v2),rs in sorted(groups.items()):
                    out.append({"tl":tl,"factor_1":f1,"level_1":v1,"factor_2":f2,"level_2":v2,"candidates":len(rs),
                                "mean_k_win_rate":statistics.fmean(float(x["k_win_rate"]) for x in rs),
                                "mean_damage_advantage":statistics.fmean(float(x["mean_damage_advantage"]) for x in rs)})
    return out


def run_plan(repo:Path,study_path:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)+validate_population(repo,doc);outdir.mkdir(parents=True,exist_ok=True)
    ledger=candidate_ledger(repo,doc);contexts=kinetic_contexts(repo,doc);design=refinement_design_summary(repo,doc)
    _write_csv(outdir/"kinetic_refinement_candidate_ledger.csv",ledger)
    _write_csv(outdir/"kinetic_refinement_context_manifest.csv",contexts)
    _write_csv(outdir/"kinetic_refinement_design_summary.csv",design)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":150,"mode":"plan","passed":not errs,"failedGates":errs,
             "kineticContexts":len(contexts),"tlCandidateCount":len(ledger),"candidateContextCells":EXPECTED_CANDIDATE_CONTEXT_CELLS,
             "trialsPerCandidateContext":DEFAULT_TRIALS,"substantiveCombatTrials":EXPECTED_SUBSTANTIVE_COMBATS,
             "smokeCombatTrials":EXPECTED_SMOKE_COMBATS,"candidatesByTl":EXPECTED_CANDIDATES_BY_TL,
             "tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary


def run_batch(repo:Path,study_path:Path,outdir:Path,jobs:int=24,tl:int=1,candidate_start:int=0,candidate_end:int|None=None,trials:int|None=None,smoke_panel:bool=False)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)+validate_population(repo,doc)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"checkpoint":150,"passed":False,"failedGates":errs}
    ledger=[r for r in candidate_ledger(repo,doc) if int(r["tl"])==int(tl)];start=max(0,int(candidate_start));end=len(ledger) if candidate_end is None else min(len(ledger),int(candidate_end));selected=ledger[start:end]
    if not selected:return {"schemaVersion":RESULT_SCHEMA,"checkpoint":150,"passed":False,"failedGates":["empty-candidate-batch"]}
    contexts=smoke_contexts(repo,doc,tl) if smoke_panel else [r for r in kinetic_contexts(repo,doc) if int(r["tl"])==int(tl)]
    ntrials=int(trials or doc["trialsPerCandidateContext"]);tasks=[];idx=0
    for c in selected:
        for src in contexts:tasks.append((idx,src,c,int(doc["masterSeed"]),ntrials));idx+=1
    outdir.mkdir(parents=True,exist_ok=True);jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _cp149_worker_init(str(repo),doc,selected);rows=[_cp149_trial_aggregate(t) for t in tasks]
    else:
        ctx=get_context("spawn");chunksize=min(32,max(1,len(tasks)//max(1,jobs*8))) if smoke_panel else 1
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_cp149_worker_init,initargs=(str(repo),doc,selected)) as ex:
            rows=list(ex.map(_cp149_trial_aggregate,tasks,chunksize=chunksize))
    rows.sort(key=lambda r:r["row_index"]);[r.pop("row_index",None) for r in rows];_write_csv(outdir/"kinetic_refinement_candidate_context_results.csv",rows)
    failures=[]
    if len(rows)!=len(selected)*len(contexts):failures.append("row-count")
    if any(int(r["error_trials"]) for r in rows):failures.append("execution-errors")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":150,"mode":"batch","passed":not failures,"failedGates":failures,"tl":int(tl),"smokePanel":bool(smoke_panel),
             "candidateStart":start,"candidateEnd":end,"candidates":len(selected),"contextsPerCandidate":len(contexts),"candidateContextCells":len(rows),
             "trialsPerContext":ntrials,"combatTrials":len(rows)*ntrials,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errors":sum(int(r["error_trials"]) for r in rows)}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary


def merge_batches(repo:Path,study_path:Path,batch_root:Path,outdir:Path,expected_trials:int|None=None)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)+validate_population(repo,doc);ntrials=int(expected_trials or doc["trialsPerCandidateContext"]);outdir.mkdir(parents=True,exist_ok=True)
    rows=[];aud=[]
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json";rp=d/"kinetic_refinement_candidate_context_results.csv"
        if not sp.exists() or not rp.exists():continue
        s=json.loads(sp.read_text(encoding="utf-8-sig"));a=s.get("analysis",s);br=_read_csv(rp);ok=bool(a.get("passed",False)) and all(int(r["trials"])==ntrials for r in br)
        aud.append({"batch":d.name,"tl":a.get("tl"),"candidate_start":a.get("candidateStart"),"candidate_end":a.get("candidateEnd"),"rows":len(br),"combat_trials":sum(int(r["trials"]) for r in br),"passed":int(ok)})
        if ok:rows.extend(br)
    failures=list(errs)
    if len(rows)!=EXPECTED_CANDIDATE_CONTEXT_CELLS:failures.append("merged-row-count")
    if any(int(r["error_trials"]) for r in rows):failures.append("execution-errors")
    _write_csv(outdir/"batch_merge_audit.csv",aud);_write_csv(outdir/"kinetic_refinement_candidate_context_results.csv",rows)
    candtl=_aggregate(rows,("tl","candidate_id"));opp=_aggregate(rows,("tl","candidate_id","opponent_weapon"));strat=_aggregate(rows,("tl","candidate_id","scenario_stratum"));res=_aggregate(rows,("tl","candidate_id","resource_ensemble_id"));role=_aggregate([r for r in rows if r["opponent_weapon"]=="E" and r["scenario_stratum"]=="ARMOR_PRESSURE"],("tl","candidate_id"))
    ledger=candidate_ledger(repo,doc);pareto=_pareto(candtl,opp,role,ledger);marg=_parameter_marginals(candtl,ledger);pairs=_pairwise_grid(candtl,ledger);design=refinement_design_summary(repo,doc)
    for fn,data in (("kinetic_refinement_candidate_tl_response.csv",candtl),("kinetic_refinement_candidate_opponent_response.csv",opp),("kinetic_refinement_candidate_stratum_response.csv",strat),("kinetic_refinement_candidate_resource_response.csv",res),("kinetic_refinement_candidate_armor_role_response.csv",role),("kinetic_refinement_combat_pareto.csv",pareto),("kinetic_refinement_parameter_marginals.csv",marg),("kinetic_refinement_pairwise_response.csv",pairs),("kinetic_refinement_candidate_ledger.csv",ledger),("kinetic_refinement_design_summary.csv",design)):_write_csv(outdir/fn,data)
    total=sum(int(r["trials"]) for r in rows)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":150,"mode":"merged-substantive","passed":not failures,"failedGates":failures,
             "candidateContextCells":len(rows),"kineticContexts":EXPECTED_CONTEXTS,"tlCandidateCount":EXPECTED_TL_CANDIDATES,"candidatesByTl":EXPECTED_CANDIDATES_BY_TL,
             "trialsPerCandidateContext":ntrials,"substantiveCombatTrials":total,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errorTrials":sum(int(r["error_trials"]) for r in rows),
             "combatParetoCandidates":sum(int(r["combat_pareto_viable"]) for r in pareto),"identityPreservingCandidates":sum(int(r["identity_preserved"]) for r in pareto),
             "tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,
             "interpretation":"High-resolution TL-specific Kinetic viable-region refinement using accepted CP149 evidence. Damage/accuracy/range/APEN are resolved only where CP149 showed leverage; firing TP, ammo, Space and SPEN are frozen. No candidate is automatically promoted."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary
