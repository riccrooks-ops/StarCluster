from __future__ import annotations

import copy
import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from itertools import combinations, product
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .ecology import UTILITY_COMBAT_DOCTRINE, build_space
from .stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario, _features_for_stratum
from .study import load_json
from .whole_combat_stage_a_response_surface import _base_max_installed_tp_demand

RESULT_SCHEMA = "star-cluster-cp149-kinetic-full-characteristic-sweep-result-v0.1"
EXPECTED_CONTEXTS = 2600
EXPECTED_FACTORS = 7
EXPECTED_CANDIDATES_PER_TL = 163
EXPECTED_TL_CANDIDATES = 9 * EXPECTED_CANDIDATES_PER_TL
DEFAULT_TRIALS = 100
HARD_TURN_SENTINEL = 60

FACTORS = (
    "accuracy_delta_pp",
    "damage_delta",
    "apen_delta",
    "firing_tp_delta",
    "standard_range_delta",
    "extended_band_delta",
    "ammo_level",
)

# Coded -1 / 0 / +1 values.  Ammo is absolute; the rest are deltas from each
# executable CP148 resource-environment baseline.  SPEN is intentionally fixed at 0.
FACTOR_LEVELS: dict[str, dict[int, int]] = {
    "accuracy_delta_pp": {-1: -10, 0: 0, 1: 10},
    "damage_delta": {-1: -2, 0: 0, 1: 2},
    "apen_delta": {-1: -2, 0: 0, 1: 2},
    "firing_tp_delta": {-1: -1, 0: 0, 1: 1},
    "standard_range_delta": {-1: -1, 0: 0, 1: 1},
    "extended_band_delta": {-1: -1, 0: 0, 1: 1},
    "ammo_level": {-1: 25, 0: 100, 1: 200},
}

_WORKER_BASE: dict[str, Any] | None = None
_WORKER_CANDIDATES: dict[str, dict[str, Any]] | None = None
_WORKER_CACHE: dict[tuple[str, int, str], Any] | None = None


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def _design_vectors() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    zero = {f: 0 for f in FACTORS}
    rows.append({"design_class":"baseline", **zero})
    for f in FACTORS:
        for sign in (-1, 1):
            v = dict(zero); v[f] = sign
            rows.append({"design_class":"axial", **v})
    for f1, f2 in combinations(FACTORS, 2):
        for s1, s2 in product((-1, 1), repeat=2):
            v = dict(zero); v[f1] = s1; v[f2] = s2
            rows.append({"design_class":"pairwise", **v})
    # 64-run resolution-VII half fraction for seven 2-level factors:
    # A-F are independent; G = A*B*C*D*E*F, giving I=ABCDEFG.
    first6 = FACTORS[:6]; g = FACTORS[6]
    for signs in product((-1, 1), repeat=6):
        v = dict(zero)
        for f, s in zip(first6, signs): v[f] = s
        prod_sign = 1
        for s in signs: prod_sign *= s
        v[g] = prod_sign
        rows.append({"design_class":"fractional_factorial", **v})
    assert len(rows) == EXPECTED_CANDIDATES_PER_TL
    return rows


def candidate_ledger(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    er, tr = _resource_rows(repo, doc)
    central = build_deep_resource_matrix(repo, doc["matrix"], "R1_CENTRAL_NO_MAJOR", er, tr)
    energy = central
    rows: list[dict[str, Any]] = []
    for tl in range(1, 10):
        base = central.p("kinetic_main", tl); e = energy.p("energy_main", tl)
        band = int(base["maxRange"]) - int(base["standardRange"])
        for i, coded in enumerate(_design_vectors()):
            vals = {f: FACTOR_LEVELS[f][int(coded[f])] for f in FACTORS}
            std = max(1, int(base["standardRange"]) + vals["standard_range_delta"])
            ext = max(0, band + vals["extended_band_delta"])
            actual = {
                "accuracyPp": int(base["accuracyPp"]) + vals["accuracy_delta_pp"],
                "damage": max(1, int(base["damage"]) + vals["damage_delta"]),
                "apen": max(0, int(base["apen"]) + vals["apen_delta"]),
                "standardRange": std,
                "maxRange": std + ext,
                "ammo": vals["ammo_level"],
            }
            cid = f"K{tl:02d}-{i:03d}"
            identity_flags = []
            if actual["accuracyPp"] > int(e["accuracyPp"]): identity_flags.append("ACC_GT_E")
            if actual["standardRange"] > int(e["standardRange"]): identity_flags.append("STD_RANGE_GT_E")
            if actual["maxRange"] > int(e["maxRange"]): identity_flags.append("MAX_RANGE_GT_E")
            rows.append({
                "candidate_id": cid, "tl": tl, "design_index": i, "design_class": coded["design_class"],
                **{f"code_{f}": int(coded[f]) for f in FACTORS},
                **vals,
                "central_base_accuracyPp": int(base["accuracyPp"]), "candidate_accuracyPp": actual["accuracyPp"],
                "central_base_damage": int(base["damage"]), "candidate_damage": actual["damage"],
                "central_base_apen": int(base["apen"]), "candidate_apen": actual["apen"],
                "candidate_spen": 0,
                "central_base_firingTp": int(base["firingTp"]), "central_candidate_firingTp": max(0, int(base["firingTp"])+vals["firing_tp_delta"]),
                "central_base_standardRange": int(base["standardRange"]), "candidate_standardRange": actual["standardRange"],
                "central_base_maxRange": int(base["maxRange"]), "candidate_maxRange": actual["maxRange"],
                "central_base_ammo": int(base["ammo"]), "candidate_ammo": actual["ammo"],
                "identity_stress": int(bool(identity_flags)), "identity_stress_flags": ";".join(identity_flags),
                "promotion_allowed": 0,
            })
    return rows


def _space_envelope(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    er, tr = _resource_rows(repo, doc)
    out: list[dict[str, Any]] = []
    for eid in sorted({r["ensemble_id"] for r in er}):
        matrix = build_deep_resource_matrix(repo, doc["matrix"], eid, er, tr)
        for tl in range(1, 10):
            base_space = int(matrix.p("kinetic_main", tl)["space"])
            for delta in (-2, -1, 0, 1, 2):
                candidate_space = max(1, base_space + delta)
                for stratum in sorted({r["scenario_stratum"] for r in _read_csv(repo/doc["stageAExperimentManifest"])}):
                    f = _features_for_stratum(stratum, tl)
                    original = int(matrix.p("kinetic_main", tl)["space"])
                    matrix.p("kinetic_main", tl)["space"] = candidate_space
                    try:
                        combat = build_space(matrix, tl, "Kinetic", 1, 1, bool(f["shield"]), bool(f["ecm"]), bool(f["eccm"]), f["pds"], bool(f["hardener"]))
                    finally:
                        matrix.p("kinetic_main", tl)["space"] = original
                    cap = matrix.capacity(tl)
                    out.append({"resource_ensemble_id":eid,"tl":tl,"scenario_stratum":stratum,"space_delta":delta,"base_k_space":base_space,"candidate_k_space":candidate_space,"combat_space":combat,"capacity":cap,"free_space":cap-combat,"legal":int(combat<=cap)})
    return out


def validate_study(doc: dict[str, Any]) -> list[str]:
    e=[]
    if doc.get("schemaVersion") != "star-cluster-cp149-kinetic-full-characteristic-sweep-study-v0.1": e.append("schemaVersion")
    if int(doc.get("checkpoint",0)) != 149: e.append("checkpoint")
    if int(doc.get("baseCheckpoint",0)) != 148: e.append("baseCheckpoint")
    if doc.get("combatDoctrine") != UTILITY_COMBAT_DOCTRINE: e.append("combatDoctrine")
    if doc.get("kineticSpenPolicy") != "fixed-zero-family-identity": e.append("kineticSpenPolicy")
    if int(doc.get("expectedKineticContexts",0)) != EXPECTED_CONTEXTS: e.append("expectedKineticContexts")
    if int(doc.get("factors",0)) != EXPECTED_FACTORS: e.append("factors")
    if int(doc.get("candidatesPerTl",0)) != EXPECTED_CANDIDATES_PER_TL: e.append("candidatesPerTl")
    if int(doc.get("tlCandidateCount",0)) != EXPECTED_TL_CANDIDATES: e.append("tlCandidateCount")
    if int(doc.get("trialsPerCandidateContext",0)) != DEFAULT_TRIALS: e.append("trialsPerCandidateContext")
    if int(doc.get("candidateContextCells",0)) != EXPECTED_CONTEXTS*EXPECTED_CANDIDATES_PER_TL: e.append("candidateContextCells")
    if int(doc.get("substantiveCombatTrials",0)) != EXPECTED_CONTEXTS*EXPECTED_CANDIDATES_PER_TL*DEFAULT_TRIALS: e.append("substantiveCombatTrials")
    if int(doc.get("smokeContextCount",0)) != 260: e.append("smokeContextCount")
    if int(doc.get("smokeCombatTrials",0)) != 42380: e.append("smokeCombatTrials")
    if int(doc.get("batchCandidates",0)) != 16: e.append("batchCandidates")
    if bool(doc.get("tuningAllowed",True)): e.append("tuningAllowed")
    if bool(doc.get("automaticPromotion",True)): e.append("automaticPromotion")
    if bool(doc.get("stageBAutomatic",True)): e.append("stageBAutomatic")
    return e


def kinetic_contexts(repo: Path, doc: dict[str, Any]) -> list[dict[str,str]]:
    rows=_read_csv(repo/doc["stageAExperimentManifest"])
    out=[r for r in rows if (r["side_a_weapon"]=="K") ^ (r["side_b_weapon"]=="K")]
    return out


def smoke_contexts(repo: Path, doc: dict[str, Any], tl: int) -> list[dict[str,str]]:
    rows=[r for r in kinetic_contexts(repo,doc) if int(r["tl"])==int(tl)]
    out=[]
    # Central E spans every stratum; tight GP spans every stratum; tight Swarmer
    # spans every stratum where Swarmer exists. Use either side assignment but only
    # one physical scenario per opponent/stratum/resource smoke cell.
    seen=set()
    for r in rows:
        opp=r["side_b_weapon"] if r["side_a_weapon"]=="K" else r["side_a_weapon"]
        wanted=(r["resource_ensemble_id"]=="R1_CENTRAL_NO_MAJOR" and opp=="E") or (r["resource_ensemble_id"]=="R4_TIGHT_HIGH_DEMAND" and opp in ({"M_GP","M_SWARMER"} if int(tl)>=2 else {"M_GP"}))
        key=(r["resource_ensemble_id"],r["scenario_stratum"],opp)
        if wanted and key not in seen:
            out.append(r); seen.add(key)
    expected=20 if int(tl)==1 else 30
    if len(out)!=expected: raise ValueError(f"CP149 smoke panel TL{tl}: expected {expected}, found {len(out)}")
    return out


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    e=[]; rows=kinetic_contexts(repo,doc)
    if len(rows)!=EXPECTED_CONTEXTS: e.append("kinetic-context-count")
    if any(r["side_a_weapon"]=="K" and r["side_b_weapon"]=="K" for r in rows): e.append("self-pair-present")
    c=Counter(int(r["tl"]) for r in rows)
    if c[1]!=200 or any(c[tl]!=300 for tl in range(2,10)): e.append("tl-context-count")
    # TL1 has no Swarmer. Each K-vs-other ordered pair is crossed with 5 resources x 10 strata.
    if len({r["scenario_id"] for r in rows})!=EXPECTED_CONTEXTS: e.append("duplicate-context-id")
    return e


def _apply_candidate(base: Any, tl: int, c: dict[str,Any]) -> Any:
    m=copy.deepcopy(base); k=m.p("kinetic_main",tl)
    base_std=int(k["standardRange"]); base_band=int(k["maxRange"])-base_std
    k["accuracyPp"] = int(k["accuracyPp"]) + int(c["accuracy_delta_pp"])
    k["damage"] = max(1, int(k["damage"]) + int(c["damage_delta"]))
    k["apen"] = max(0, int(k["apen"]) + int(c["apen_delta"]))
    k["spen"] = 0
    k["firingTp"] = max(0, int(k["firingTp"]) + int(c["firing_tp_delta"]))
    k["standardRange"] = max(1, base_std + int(c["standard_range_delta"]))
    k["maxRange"] = int(k["standardRange"]) + max(0, base_band + int(c["extended_band_delta"]))
    k["ammo"] = int(c["ammo_level"])
    return m


def _worker_init(repo_text: str, doc: dict[str,Any], candidates: list[dict[str,Any]]) -> None:
    global _WORKER_BASE, _WORKER_CANDIDATES, _WORKER_CACHE
    repo=Path(repo_text); er,tr=_resource_rows(repo,doc)
    _WORKER_BASE={eid:build_deep_resource_matrix(repo,doc["matrix"],eid,er,tr) for eid in sorted({r["ensemble_id"] for r in er})}
    _WORKER_CANDIDATES={r["candidate_id"]:r for r in candidates}; _WORKER_CACHE={}


def _matrix_for(resource: str, tl: int, cid: str):
    if _WORKER_BASE is None or _WORKER_CANDIDATES is None or _WORKER_CACHE is None: raise RuntimeError("CP149 worker not initialized")
    key=(resource,tl,cid)
    if key not in _WORKER_CACHE: _WORKER_CACHE[key]=_apply_candidate(_WORKER_BASE[resource],tl,_WORKER_CANDIDATES[cid])
    return _WORKER_CACHE[key]


def _trial_aggregate(args: tuple[int,dict[str,str],dict[str,Any],int,int]) -> dict[str,Any]:
    idx,src,c,master_seed,trials=args; tl=int(src["tl"]); matrix=_matrix_for(src["resource_ensemble_id"],tl,c["candidate_id"]); bound=bind_scenario(matrix,src); variant=bound.variant
    k_side="A" if src["side_a_weapon"]=="K" else "B"; opp=src["side_b_weapon"] if k_side=="A" else src["side_a_weapon"]
    cnt=Counter(); sums=defaultdict(float); peak_tp=0; errors=[]
    base_max,parts=_base_max_installed_tp_demand(matrix,variant.side_a if k_side=="A" else variant.side_b); reactor=int(matrix.p("reactor",tl)["operationalTp"])
    kprof=matrix.p("kinetic_main",tl)
    for trial in range(trials):
        turn_rows=[]; ctx={"scenario_id":src["scenario_id"],"resource_ensemble_id":src["resource_ensemble_id"],"weapon_a":src["side_a_weapon"],"weapon_b":src["side_b_weapon"]}
        res=run_trial_full_map(matrix,variant,master_seed,trial,turn_telemetry_sink=turn_rows,telemetry_context=ctx,combat_doctrine=UTILITY_COMBAT_DOCTRINE)
        if res.error: cnt["errors"]+=1; errors.append(res.error); continue
        if res.termination_cause=="TURN_CAP_SENTINEL": cnt["turn_cap"]+=1
        if res.termination_cause=="STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION": cnt["stalemate"]+=1
        if res.unresolved: cnt["unresolved"]+=1
        elif res.winner==k_side: cnt["k_wins"]+=1
        elif res.winner in ("A","B"): cnt["opp_wins"]+=1
        else: cnt["draws"]+=1
        sums["turns"]+=res.turns
        kt=res.side_a if k_side=="A" else res.side_b; ot=res.side_b if k_side=="A" else res.side_a
        for name in ("direct_shots","direct_hits","direct_raw_damage","direct_hull_damage","raw_damage_on_hit","hull_damage","armor_integrity_damage","shield_absorbed","weapon_power_shortfalls","cp146_held_main_attempts","cp146_held_main_intercepts","cp147_package_decisions","cp147_direct_package_selections","cp147_held_package_selections","cp147_pds_package_selections","pds_attempts","pds_intercepts"):
            sums[name]+=float(getattr(kt,name))
        sums["damage_inflicted"]+=float(ot.hull_damage+ot.armor_integrity_damage+ot.shield_absorbed)
        sums["damage_received"]+=float(kt.hull_damage+kt.armor_integrity_damage+kt.shield_absorbed)
        relevant=[r for r in turn_rows if r["side_id"]==k_side]
        sums["side_turns"]+=len(relevant); sums["tp_requested"]+=sum(float(r.get("tp_requested_total",0)) for r in relevant); sums["tp_allocated"]+=sum(float(r.get("tp_allocated_total",0)) for r in relevant); sums["tp_denied"]+=sum(float(r.get("tp_denied_total",0)) for r in relevant)
        if relevant:
            peak_tp=max(peak_tp,max(int(r.get("tp_allocated_total",0)) for r in relevant)); last=relevant[-1]
            if last.get("kinetic_ammo_remaining","")!="" and int(last["kinetic_ammo_remaining"])<=0: cnt["ammo_exhausted"]+=1
    valid=trials-cnt["errors"]; side_turns=sums["side_turns"]; shots=sums["direct_shots"]; hits=sums["direct_hits"]
    return {
        "row_index":idx,"candidate_id":c["candidate_id"],"design_class":c["design_class"],"tl":tl,"scenario_id":src["scenario_id"],"opponent_weapon":opp,"resource_ensemble_id":src["resource_ensemble_id"],"scenario_stratum":src["scenario_stratum"],"k_side":k_side,"trials":trials,
        "k_wins":cnt["k_wins"],"opponent_wins":cnt["opp_wins"],"draws":cnt["draws"],"unresolved":cnt["unresolved"],"turn_cap_sentinels":cnt["turn_cap"],"safe_stalemates":cnt["stalemate"],"error_trials":cnt["errors"],"unique_errors":" | ".join(sorted(set(errors))),
        "k_win_rate":cnt["k_wins"]/trials,"opponent_win_rate":cnt["opp_wins"]/trials,"mean_turns":sums["turns"]/valid if valid else 0,"damage_advantage":(sums["damage_inflicted"]-sums["damage_received"])/valid if valid else 0,
        "mean_direct_shots":shots/valid if valid else 0,"direct_hit_rate":hits/shots if shots else 0,"mean_direct_raw_damage":sums["direct_raw_damage"]/valid if valid else 0,"raw_damage_per_direct_hit":sums["direct_raw_damage"]/hits if hits else 0,"mean_direct_hull_damage":sums["direct_hull_damage"]/valid if valid else 0,
        "mean_held_main_attempts":sums["cp146_held_main_attempts"]/valid if valid else 0,"held_main_intercept_rate":sums["cp146_held_main_intercepts"]/sums["cp146_held_main_attempts"] if sums["cp146_held_main_attempts"] else 0,"mean_pds_attempts":sums["pds_attempts"]/valid if valid else 0,"pds_intercept_rate":sums["pds_intercepts"]/sums["pds_attempts"] if sums["pds_attempts"] else 0,
        "mean_tp_requested_per_turn":sums["tp_requested"]/side_turns if side_turns else 0,"mean_tp_allocated_per_turn":sums["tp_allocated"]/side_turns if side_turns else 0,"tp_fulfillment_rate":sums["tp_allocated"]/sums["tp_requested"] if sums["tp_requested"] else 1.0,"mean_tp_denied_per_turn":sums["tp_denied"]/side_turns if side_turns else 0,"peak_tp_allocated":peak_tp,
        "base_reactor_tp":reactor,"base_max_installed_tp_demand":base_max,"base_max_demand_vs_reactor":base_max/reactor if reactor else 0,"ammo_exhausted_rate":cnt["ammo_exhausted"]/trials,
        "k_accuracyPp":int(kprof["accuracyPp"]),"k_damage":int(kprof["damage"]),"k_apen":int(kprof["apen"]),"k_spen":int(kprof["spen"]),"k_firingTp":int(kprof["firingTp"]),"k_standardRange":int(kprof["standardRange"]),"k_maxRange":int(kprof["maxRange"]),"k_ammo":int(kprof["ammo"]),
        **{f"code_{f}":int(c[f"code_{f}"]) for f in FACTORS},
    }


def _aggregate(rows: list[dict[str,Any]], keys: tuple[str,...]) -> list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows: groups[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,rs in sorted(groups.items(),key=lambda x:tuple(str(v) for v in x[0])):
        trials=sum(int(r["trials"]) for r in rs); kw=sum(int(r["k_wins"]) for r in rs); ow=sum(int(r["opponent_wins"]) for r in rs); dr=sum(int(r["draws"]) for r in rs)
        row={k:v for k,v in zip(keys,key)}; row.update({"contexts":len(rs),"trials":trials,"k_win_rate":kw/trials if trials else 0,"opponent_win_rate":ow/trials if trials else 0,"draw_rate":dr/trials if trials else 0,
            "mean_turns":statistics.fmean(float(r["mean_turns"]) for r in rs),"mean_damage_advantage":statistics.fmean(float(r["damage_advantage"]) for r in rs),"mean_direct_shots":statistics.fmean(float(r["mean_direct_shots"]) for r in rs),"mean_direct_hit_rate":statistics.fmean(float(r["direct_hit_rate"]) for r in rs),"mean_raw_damage_per_direct_hit":statistics.fmean(float(r["raw_damage_per_direct_hit"]) for r in rs),"mean_tp_fulfillment_rate":statistics.fmean(float(r["tp_fulfillment_rate"]) for r in rs),"mean_tp_allocated_per_turn":statistics.fmean(float(r["mean_tp_allocated_per_turn"]) for r in rs),"mean_base_max_demand_vs_reactor":statistics.fmean(float(r["base_max_demand_vs_reactor"]) for r in rs),"mean_ammo_exhausted_rate":statistics.fmean(float(r["ammo_exhausted_rate"]) for r in rs),"turn_cap_sentinels":sum(int(r["turn_cap_sentinels"]) for r in rs),"error_trials":sum(int(r["error_trials"]) for r in rs)})
        out.append(row)
    return out


def _axial_effects(candidate_tl: list[dict[str,Any]], ledger_by: dict[tuple[int,str],dict[str,Any]]) -> list[dict[str,Any]]:
    by={(int(r["tl"]),r["candidate_id"]):r for r in candidate_tl}; out=[]
    for tl in range(1,10):
        base_ledger=next(x for (t,_),x in ledger_by.items() if t==tl and x["design_class"]=="baseline"); base=by[(tl,base_ledger["candidate_id"])]
        for f in FACTORS:
            for sign in (-1,1):
                lr=next(x for (t,_),x in ledger_by.items() if t==tl and x["design_class"]=="axial" and int(x[f"code_{f}"])==sign and all(int(x[f"code_{o}"])==0 for o in FACTORS if o!=f))
                r=by[(tl,lr["candidate_id"])]
                out.append({"tl":tl,"factor":f,"direction":sign,"candidate_id":lr["candidate_id"],"k_win_rate":r["k_win_rate"],"delta_win_rate_vs_baseline":float(r["k_win_rate"])-float(base["k_win_rate"]),"delta_damage_advantage_vs_baseline":float(r["mean_damage_advantage"])-float(base["mean_damage_advantage"]),"delta_hit_rate_vs_baseline":float(r["mean_direct_hit_rate"])-float(base["mean_direct_hit_rate"]),"delta_tp_fulfillment_vs_baseline":float(r["mean_tp_fulfillment_rate"])-float(base["mean_tp_fulfillment_rate"]),"delta_turns_vs_baseline":float(r["mean_turns"])-float(base["mean_turns"])})
    return out


def _pairwise_interactions(candidate_tl: list[dict[str,Any]], ledger: list[dict[str,Any]]) -> list[dict[str,Any]]:
    by={(int(r["tl"]),r["candidate_id"]):r for r in candidate_tl}; out=[]
    for tl in range(1,10):
        ltl=[x for x in ledger if int(x["tl"])==tl]
        for f1,f2 in combinations(FACTORS,2):
            vals={}
            for s1,s2 in product((-1,1),repeat=2):
                lr=next(x for x in ltl if x["design_class"]=="pairwise" and int(x[f"code_{f1}"])==s1 and int(x[f"code_{f2}"])==s2 and all(int(x[f"code_{o}"])==0 for o in FACTORS if o not in (f1,f2)))
                vals[(s1,s2)]=by[(tl,lr["candidate_id"])]
            def contrast(metric:str)->float:
                return (float(vals[(1,1)][metric])-float(vals[(1,-1)][metric])-float(vals[(-1,1)][metric])+float(vals[(-1,-1)][metric]))/4.0
            out.append({"tl":tl,"factor_1":f1,"factor_2":f2,"win_rate_interaction":contrast("k_win_rate"),"damage_advantage_interaction":contrast("mean_damage_advantage"),"hit_rate_interaction":contrast("mean_direct_hit_rate"),"tp_fulfillment_interaction":contrast("mean_tp_fulfillment_rate"),"turns_interaction":contrast("mean_turns")})
    return out


def _pareto(candidate_tl:list[dict[str,Any]], opponent:list[dict[str,Any]], role:list[dict[str,Any]], ledger:list[dict[str,Any]])->list[dict[str,Any]]:
    opp={(int(r["tl"]),r["candidate_id"],r["opponent_weapon"]):r for r in opponent}; rolemap={(int(r["tl"]),r["candidate_id"]):r for r in role}; led={(int(r["tl"]),r["candidate_id"]):r for r in ledger}; out=[]
    for tl in range(1,10):
        rs=[r for r in candidate_tl if int(r["tl"])==tl]; metrics={}
        for r in rs:
            cid=r["candidate_id"]; ovals=[float(opp[(tl,cid,o)]["k_win_rate"]) for o in ("E","M_GP") if (tl,cid,o) in opp]
            if (tl,cid,"M_SWARMER") in opp: ovals.append(float(opp[(tl,cid,"M_SWARMER")]["k_win_rate"]))
            armor=float(rolemap.get((tl,cid),{}).get("k_win_rate",0))
            metrics[cid]=(float(r["k_win_rate"]), min(ovals) if ovals else 0, armor, float(r["mean_damage_advantage"]))
        for r in rs:
            cid=r["candidate_id"]; dom=[]
            for o in rs:
                oid=o["candidate_id"]
                if oid==cid: continue
                a=metrics[oid]; b=metrics[cid]
                if all(x>=y-1e-12 for x,y in zip(a,b)) and any(x>y+1e-12 for x,y in zip(a,b)): dom.append(oid)
            l=led[(tl,cid)]
            out.append({**r,"worst_opponent_win_rate":metrics[cid][1],"armor_role_win_rate":metrics[cid][2],"combat_pareto_viable":int(not dom),"combat_dominated_by":";".join(dom[:25]),"identity_stress":l["identity_stress"],"identity_stress_flags":l["identity_stress_flags"],"promotion_allowed":0})
    return out


def run_plan(repo:Path,study_path:Path,outdir:Path)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc); outdir.mkdir(parents=True,exist_ok=True)
    ledger=candidate_ledger(repo,doc); space=_space_envelope(repo,doc); contexts=kinetic_contexts(repo,doc)
    _write_csv(outdir/"kinetic_candidate_ledger.csv",ledger);_write_csv(outdir/"kinetic_space_envelope.csv",space);_write_csv(outdir/"kinetic_context_manifest.csv",contexts)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":149,"mode":"plan","passed":not errs,"failedGates":errs,"kineticContexts":len(contexts),"factors":EXPECTED_FACTORS,"candidatesPerTl":EXPECTED_CANDIDATES_PER_TL,"tlCandidateCount":len(ledger),"candidateContextCells":len(contexts)*EXPECTED_CANDIDATES_PER_TL,"trialsPerCandidateContext":int(doc["trialsPerCandidateContext"]),"substantiveCombatTrials":len(contexts)*EXPECTED_CANDIDATES_PER_TL*int(doc["trialsPerCandidateContext"]),"spaceEnvelopeRows":len(space),"tuningAllowed":False,"automaticPromotion":False}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary


def run_batch(repo:Path,study_path:Path,outdir:Path,jobs:int=24,tl:int=1,candidate_start:int=0,candidate_end:int|None=None,trials:int|None=None,smoke_panel:bool=False)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)+validate_population(repo,doc)
    if errs:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":errs}
    ledger=[r for r in candidate_ledger(repo,doc) if int(r["tl"])==int(tl)]; start=max(0,int(candidate_start));end=len(ledger) if candidate_end is None else min(len(ledger),int(candidate_end)); selected=ledger[start:end]
    if not selected:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["empty-candidate-batch"]}
    contexts=smoke_contexts(repo,doc,tl) if smoke_panel else [r for r in kinetic_contexts(repo,doc) if int(r["tl"])==int(tl)]; ntrials=int(trials or doc["trialsPerCandidateContext"]); tasks=[];idx=0
    for c in selected:
        for src in contexts: tasks.append((idx,src,c,int(doc["masterSeed"]),ntrials));idx+=1
    outdir.mkdir(parents=True,exist_ok=True); jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc,selected); rows=[_trial_aggregate(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        chunksize = min(32, max(1, len(tasks) // max(1, jobs * 8))) if smoke_panel else 1
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc,selected)) as ex: rows=list(ex.map(_trial_aggregate,tasks,chunksize=chunksize))
    rows.sort(key=lambda r:r["row_index"]); [r.pop("row_index",None) for r in rows]; _write_csv(outdir/"kinetic_candidate_context_results.csv",rows)
    failures=[]
    if len(rows)!=len(selected)*len(contexts): failures.append("row-count")
    if any(int(r["error_trials"]) for r in rows): failures.append("execution-errors")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":149,"mode":"batch","passed":not failures,"failedGates":failures,"tl":int(tl),"smokePanel":bool(smoke_panel),"candidateStart":start,"candidateEnd":end,"candidates":len(selected),"contextsPerCandidate":len(contexts),"candidateContextCells":len(rows),"trialsPerContext":ntrials,"combatTrials":len(rows)*ntrials,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errors":sum(int(r["error_trials"]) for r in rows)}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary


def merge_batches(repo:Path,study_path:Path,batch_root:Path,outdir:Path,expected_trials:int|None=None)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)+validate_population(repo,doc);ntrials=int(expected_trials or doc["trialsPerCandidateContext"]);outdir.mkdir(parents=True,exist_ok=True)
    rows=[];aud=[]
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json";rp=d/"kinetic_candidate_context_results.csv"
        if not sp.exists() or not rp.exists():continue
        s=json.loads(sp.read_text(encoding="utf-8-sig")); a=s.get("analysis",s); br=_read_csv(rp); ok=bool(a.get("passed",False)) and all(int(r["trials"])==ntrials for r in br)
        aud.append({"batch":d.name,"tl":a.get("tl"),"candidate_start":a.get("candidateStart"),"candidate_end":a.get("candidateEnd"),"rows":len(br),"combat_trials":sum(int(r["trials"]) for r in br),"passed":int(ok)})
        if ok: rows.extend(br)
    failures=list(errs);expected=EXPECTED_CONTEXTS*EXPECTED_CANDIDATES_PER_TL
    if len(rows)!=expected:failures.append("merged-row-count")
    if any(int(r["error_trials"]) for r in rows):failures.append("execution-errors")
    _write_csv(outdir/"batch_merge_audit.csv",aud);_write_csv(outdir/"kinetic_candidate_context_results.csv",rows)
    candtl=_aggregate(rows,("tl","candidate_id"));opp=_aggregate(rows,("tl","candidate_id","opponent_weapon"));strat=_aggregate(rows,("tl","candidate_id","scenario_stratum"));res=_aggregate(rows,("tl","candidate_id","resource_ensemble_id"));role=_aggregate([r for r in rows if r["opponent_weapon"]=="E" and r["scenario_stratum"]=="ARMOR_PRESSURE"],("tl","candidate_id"))
    ledger=candidate_ledger(repo,doc);ledby={(int(r["tl"]),r["candidate_id"]):r for r in ledger}
    axial=_axial_effects(candtl,ledby);inter=_pairwise_interactions(candtl,ledger);pareto=_pareto(candtl,opp,role,ledger);space=_space_envelope(repo,doc)
    for fn,data in (("kinetic_candidate_tl_response.csv",candtl),("kinetic_candidate_opponent_response.csv",opp),("kinetic_candidate_stratum_response.csv",strat),("kinetic_candidate_resource_response.csv",res),("kinetic_candidate_armor_role_response.csv",role),("kinetic_axial_effects.csv",axial),("kinetic_pairwise_interactions.csv",inter),("kinetic_combat_pareto_candidates.csv",pareto),("kinetic_candidate_ledger.csv",ledger),("kinetic_space_envelope.csv",space)):_write_csv(outdir/fn,data)
    total=sum(int(r["trials"]) for r in rows);summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":149,"mode":"merged-substantive","passed":not failures,"failedGates":failures,"candidateContextCells":len(rows),"kineticContexts":EXPECTED_CONTEXTS,"candidatesPerTl":EXPECTED_CANDIDATES_PER_TL,"tlCandidateCount":EXPECTED_TL_CANDIDATES,"trialsPerCandidateContext":ntrials,"substantiveCombatTrials":total,"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errorTrials":sum(int(r["error_trials"]) for r in rows),"tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,"interpretation":"Broad seven-dimensional Kinetic operational response surface plus independent Space construction envelope. SPEN stays zero. Review main effects, interactions, identity-stress regions, role response and combat Pareto regions before any numerical promotion."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary
