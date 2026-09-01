from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .ecology import LEGACY_COMBAT_DOCTRINE
from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from .study import load_json

RESULT_SCHEMA = "star-cluster-cp145-stage-a-diagnostic-attribution-result-v0.1"
EXPECTED_DIAGNOSTIC_SCENARIOS = 252
EXPECTED_PDS_SCENARIOS = 204
EXPECTED_TP_SCENARIOS = 48
DIAGNOSTIC_TRIALS_PER_SCENARIO = 25
EXPECTED_DIAGNOSTIC_TRIALS = EXPECTED_DIAGNOSTIC_SCENARIOS * DIAGNOSTIC_TRIALS_PER_SCENARIO
HARD_TURN_SENTINEL = 60
LONG_RESOLVED_TURN = 25
_WORKER_MATRICES: dict[str, Any] | None = None


def _sha(path: Path) -> str:
    h=hashlib.sha256();h.update(path.read_bytes());return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str,Any]]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8");return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields:fields.append(k)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)


def _q(values: list[float], frac: float) -> float:
    if not values:return 0.0
    vals=sorted(values);pos=(len(vals)-1)*frac;lo=int(pos);hi=min(len(vals)-1,lo+1);f=pos-lo
    return vals[lo]*(1-f)+vals[hi]*f


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs)!=len(ys) or len(xs)<2:return 0.0
    mx=statistics.fmean(xs);my=statistics.fmean(ys)
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys));dx=sum((x-mx)**2 for x in xs);dy=sum((y-my)**2 for y in ys)
    return num/math.sqrt(dx*dy) if dx>0 and dy>0 else 0.0


def validate_study(doc: dict[str,Any]) -> list[str]:
    e=[]
    if doc.get("schemaVersion")!="star-cluster-cp145-stage-a-diagnostic-attribution-study-v0.1":e.append("schemaVersion")
    if int(doc.get("checkpoint",0))!=145:e.append("checkpoint")
    if int(doc.get("baseCheckpoint",0))!=144:e.append("baseCheckpoint")
    if doc.get("scope")!="stage-a-zero-tuning-diagnostic-attribution":e.append("scope")
    if int(doc.get("expectedDiagnosticScenarios",0))!=EXPECTED_DIAGNOSTIC_SCENARIOS:e.append("expectedDiagnosticScenarios")
    if int(doc.get("expectedPdsOpportunityScenarios",0))!=EXPECTED_PDS_SCENARIOS:e.append("expectedPdsOpportunityScenarios")
    if int(doc.get("expectedTpStarvationScenarios",0))!=EXPECTED_TP_SCENARIOS:e.append("expectedTpStarvationScenarios")
    if int(doc.get("diagnosticTrialsPerScenario",0))!=DIAGNOSTIC_TRIALS_PER_SCENARIO:e.append("diagnosticTrialsPerScenario")
    if int(doc.get("diagnosticCombatTrials",0))!=EXPECTED_DIAGNOSTIC_TRIALS:e.append("diagnosticCombatTrials")
    if int(doc.get("hardTurnSentinel",0))!=HARD_TURN_SENTINEL:e.append("hardTurnSentinel")
    if int(doc.get("longResolvedTurn",0))!=LONG_RESOLVED_TURN:e.append("longResolvedTurn")
    if bool(doc.get("tuningAllowed",True)):e.append("tuningAllowed")
    if bool(doc.get("automaticPromotion",True)):e.append("automaticPromotion")
    if bool(doc.get("stageBAutomatic",True)):e.append("stageBAutomatic")
    return e


def _accepted_surfaces(repo: Path, doc: dict[str,Any]) -> tuple[list[dict[str,str]],list[dict[str,str]],dict[str,Any]]:
    # CP145 deliberately retains only the exact accepted CP144 tables it analyzes,
    # not the predecessor native-results ZIP. The original ZIP hash remains provenance.
    summary_path=repo/doc["acceptedCp144Summary"]
    scenario_path=repo/doc["acceptedCp144ScenarioSurface"]
    pareto_path=repo/doc["acceptedCp144ParetoSurface"]
    if _sha(summary_path)!=doc["acceptedCp144SummarySha256"]:raise ValueError("accepted CP144 summary hash drift")
    if _sha(scenario_path)!=doc["acceptedScenarioSurfaceSha256"]:raise ValueError("accepted CP144 scenario surface hash drift")
    if _sha(pareto_path)!=doc["acceptedParetoSurfaceSha256"]:raise ValueError("accepted CP144 Pareto surface hash drift")
    summary=json.loads(summary_path.read_text(encoding="utf-8-sig"))
    if int(summary.get("checkpoint",0))!=144 or not bool(summary.get("substantiveStageACompleted")) or int(summary.get("substantiveCombatTrials",0))!=3425000:
        raise ValueError("accepted CP144 summary is not the native-completed Stage-A result")
    rows=_read_csv(scenario_path);pareto=_read_csv(pareto_path)
    if len(rows)!=6850 or sum(int(r["trials"]) for r in rows)!=3425000:raise ValueError("accepted CP144 Stage-A surface coverage drift")
    return rows,pareto,summary


def validate_population(repo: Path, doc: dict[str,Any]) -> list[str]:
    e=[];m=_read_csv(repo/doc["diagnosticReplayManifest"]);stage=_read_csv(repo/doc["stageAExperimentManifest"]);stage_by_id={r["scenario_id"]:r for r in stage};stage_ids=set(stage_by_id)
    if len(m)!=EXPECTED_DIAGNOSTIC_SCENARIOS:e.append("diagnostic-count")
    if len({r["scenario_id"] for r in m})!=len(m):e.append("diagnostic-duplicate")
    if any(r["scenario_id"] not in stage_ids for r in m):e.append("diagnostic-not-cp144")
    identity_fields=("tl","side_a_weapon","side_b_weapon","resource_ensemble_id","scenario_stratum")
    if any(any(r.get(k)!=stage_by_id[r["scenario_id"]].get(k) for k in identity_fields) for r in m if r["scenario_id"] in stage_by_id):e.append("diagnostic-identity-drift")
    counts=defaultdict(int)
    for r in m:counts[r["diagnostic_family"]]+=1
    if counts["PDS_OPPORTUNITY"]!=EXPECTED_PDS_SCENARIOS:e.append("pds-count")
    if counts["TP_STARVATION"]!=EXPECTED_TP_SCENARIOS:e.append("tp-count")
    if any(int(r["planned_trials"])!=DIAGNOSTIC_TRIALS_PER_SCENARIO for r in m):e.append("planned-trials")
    return e


def _candidate_contexts(rows: list[dict[str,str]]) -> list[dict[str,Any]]:
    idx={(int(r["tl"]),r["resource_ensemble_id"],r["scenario_stratum"],r["side_a_weapon"],r["side_b_weapon"]):r for r in rows};out=[]
    for (tl,res,stratum,a,b),ca in sorted(idx.items()):
        if a==b:
            n=int(ca["trials"]);wins=(int(ca["a_wins"])+int(ca["b_wins"]))/2;fast=(int(ca["a_fast_wins_under25"])+int(ca["b_fast_wins_under25"]))/2
            def avg(fa:str,fb:str):return (float(ca[fa])+float(ca[fb]))/2
            metrics={
                "win_rate":wins/n,"fast_win_rate":fast/n,"damage_advantage":0.0,
                "tp_conflict_turn_rate":avg("a_tp_conflict_turn_rate","b_tp_conflict_turn_rate"),"tp_fulfillment_rate":avg("a_tp_fulfillment_rate","b_tp_fulfillment_rate"),
                "firm_track_turn_rate":avg("a_firm_track_turn_rate","b_firm_track_turn_rate"),"ammo_exhausted_rate":avg("a_primary_ammo_exhausted_rate","b_primary_ammo_exhausted_rate"),
                "duration_concern_rate":float(ca["gameplay_duration_concern_rate"]),"direct_shots_per_turn":avg("mean_a_direct_shots","mean_b_direct_shots")/max(1e-12,avg("mean_a_side_turns","mean_b_side_turns")),
                "direct_hit_rate":avg("a_direct_hit_rate","b_direct_hit_rate"),"direct_raw_damage_per_hit":avg("mean_a_direct_raw_damage","mean_b_direct_raw_damage")/max(1e-12,avg("mean_a_direct_hits","mean_b_direct_hits")),
                "direct_hull_conversion":avg("mean_a_direct_hull_damage","mean_b_direct_hull_damage")/max(1e-12,avg("mean_a_direct_raw_damage","mean_b_direct_raw_damage")),
                "damage_inflicted_per_turn":avg("mean_a_damage_inflicted","mean_b_damage_inflicted")/max(1e-12,avg("mean_a_side_turns","mean_b_side_turns")),
            }
        else:
            cb=idx.get((tl,res,stratum,b,a))
            if cb is None:continue
            n=int(ca["trials"])+int(cb["trials"]);wins=int(ca["a_wins"])+int(cb["b_wins"]);fast=int(ca["a_fast_wins_under25"])+int(cb["b_fast_wins_under25"])
            def avg(fa:str,fb:str):return (float(ca[fa])*int(ca["trials"])+float(cb[fb])*int(cb["trials"]))/n
            metrics={
                "win_rate":wins/n,"fast_win_rate":fast/n,"damage_advantage":(float(ca["a_damage_advantage_mean"])*int(ca["trials"])-float(cb["a_damage_advantage_mean"])*int(cb["trials"]))/n,
                "tp_conflict_turn_rate":avg("a_tp_conflict_turn_rate","b_tp_conflict_turn_rate"),"tp_fulfillment_rate":avg("a_tp_fulfillment_rate","b_tp_fulfillment_rate"),
                "firm_track_turn_rate":avg("a_firm_track_turn_rate","b_firm_track_turn_rate"),"ammo_exhausted_rate":avg("a_primary_ammo_exhausted_rate","b_primary_ammo_exhausted_rate"),
                "duration_concern_rate":(float(ca["gameplay_duration_concern_rate"])+float(cb["gameplay_duration_concern_rate"]))/2,
                "direct_shots_per_turn":avg("mean_a_direct_shots","mean_b_direct_shots")/max(1e-12,avg("mean_a_side_turns","mean_b_side_turns")),
                "direct_hit_rate":avg("a_direct_hit_rate","b_direct_hit_rate"),"direct_raw_damage_per_hit":avg("mean_a_direct_raw_damage","mean_b_direct_raw_damage")/max(1e-12,avg("mean_a_direct_hits","mean_b_direct_hits")),
                "direct_hull_conversion":avg("mean_a_direct_hull_damage","mean_b_direct_hull_damage")/max(1e-12,avg("mean_a_direct_raw_damage","mean_b_direct_raw_damage")),
                "damage_inflicted_per_turn":avg("mean_a_damage_inflicted","mean_b_damage_inflicted")/max(1e-12,avg("mean_a_side_turns","mean_b_side_turns")),
            }
        row={"tl":tl,"resource_ensemble_id":res,"scenario_stratum":stratum,"candidate_weapon":a,"opponent_weapon":b};row.update(metrics);out.append(row)
    return out


def _group_mean(rows: list[dict[str,Any]], keys: tuple[str,...], metrics: tuple[str,...]) -> list[dict[str,Any]]:
    g=defaultdict(list)
    for r in rows:g[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,rs in sorted(g.items()):
        row={k:v for k,v in zip(keys,key)};row["contexts"]=len(rs)
        for m in metrics:row[m]=statistics.fmean(float(x[m]) for x in rs)
        out.append(row)
    return out


def _accepted_analyses(rows: list[dict[str,str]], pareto: list[dict[str,str]]) -> dict[str,list[dict[str,Any]]]:
    contexts=_candidate_contexts(rows)
    # Redundancy diagnosis for the original CP144 Pareto objectives.
    w=[float(r["side_symmetric_win_rate"]) for r in pareto];f=[float(r["side_symmetric_fast_win_rate"]) for r in pareto];d=[float(r["side_symmetric_damage_advantage_mean"]) for r in pareto]
    pdiag=[
        {"objective_x":"win_rate","objective_y":"fast_win_rate","pearson_correlation":_pearson(w,f)},
        {"objective_x":"win_rate","objective_y":"damage_advantage","pearson_correlation":_pearson(w,d)},
        {"objective_x":"fast_win_rate","objective_y":"damage_advantage","pearson_correlation":_pearson(f,d)},
    ]
    # Strategic viability rolls up across resources, strata, and opponents, adding resource/endurance dimensions.
    g=defaultdict(list)
    for r in contexts:g[(r["tl"],r["candidate_weapon"])].append(r)
    strategic=[]
    for (tl,cand),rs in sorted(g.items()):
        wr=[float(x["win_rate"]) for x in rs]
        by_resource=defaultdict(list);by_stratum=defaultdict(list)
        for x in rs:
            by_resource[x["resource_ensemble_id"]].append(float(x["win_rate"]));by_stratum[x["scenario_stratum"]].append(float(x["win_rate"]))
        resource_means=[statistics.fmean(v) for v in by_resource.values()];stratum_means=[statistics.fmean(v) for v in by_stratum.values()]
        strategic.append({"tl":tl,"weapon":cand,"contexts":len(rs),"mean_win_rate":statistics.fmean(wr),"p25_win_rate":_q(wr,.25),"p90_win_rate":_q(wr,.90),
            "worst_resource_mean_win_rate":min(resource_means),"resource_win_rate_spread":max(resource_means)-min(resource_means),"worst_stratum_mean_win_rate":min(stratum_means),
            "mean_tp_fulfillment_rate":statistics.fmean(float(x["tp_fulfillment_rate"]) for x in rs),"mean_tp_conflict_turn_rate":statistics.fmean(float(x["tp_conflict_turn_rate"]) for x in rs),
            "mean_primary_ammo_exhausted_rate":statistics.fmean(float(x["ammo_exhausted_rate"]) for x in rs),"mean_duration_concern_rate":statistics.fmean(float(x["duration_concern_rate"]) for x in rs),
            "mean_damage_advantage":statistics.fmean(float(x["damage_advantage"]) for x in rs)})
    for tl in sorted({int(r["tl"]) for r in strategic}):
        rs=[r for r in strategic if int(r["tl"])==tl]
        for c in rs:
            combat=(c["mean_win_rate"],c["p25_win_rate"],c["p90_win_rate"],c["mean_damage_advantage"]);combat_dom=[]
            strategic_metrics=(c["mean_win_rate"],c["p25_win_rate"],c["p90_win_rate"],c["worst_resource_mean_win_rate"],c["worst_stratum_mean_win_rate"],c["mean_tp_fulfillment_rate"],1-c["mean_primary_ammo_exhausted_rate"],1-c["mean_duration_concern_rate"]);strategic_dom=[]
            for o in rs:
                if o is c:continue
                other_combat=(o["mean_win_rate"],o["p25_win_rate"],o["p90_win_rate"],o["mean_damage_advantage"])
                if all(x>=y-1e-12 for x,y in zip(other_combat,combat)) and any(x>y+1e-12 for x,y in zip(other_combat,combat)):combat_dom.append(o["weapon"])
                other_strategic=(o["mean_win_rate"],o["p25_win_rate"],o["p90_win_rate"],o["worst_resource_mean_win_rate"],o["worst_stratum_mean_win_rate"],o["mean_tp_fulfillment_rate"],1-o["mean_primary_ammo_exhausted_rate"],1-o["mean_duration_concern_rate"])
                if all(x>=y-1e-12 for x,y in zip(other_strategic,strategic_metrics)) and any(x>y+1e-12 for x,y in zip(other_strategic,strategic_metrics)):strategic_dom.append(o["weapon"])
            c["combat_pareto_viable"]=int(not combat_dom);c["combat_dominated_by"]=";".join(sorted(combat_dom))
            c["strategic_pareto_viable"]=int(not strategic_dom);c["strategic_dominated_by"]=";".join(sorted(strategic_dom))
            c["resource_or_robustness_only_frontier"]=int(not strategic_dom and bool(combat_dom))
    k=[r for r in contexts if r["candidate_weapon"]=="K"]
    kinetic=_group_mean(k,("tl","opponent_weapon","scenario_stratum"),("win_rate","tp_conflict_turn_rate","tp_fulfillment_rate","firm_track_turn_rate","ammo_exhausted_rate","duration_concern_rate","direct_shots_per_turn","direct_hit_rate","direct_raw_damage_per_hit","direct_hull_conversion","damage_inflicted_per_turn","damage_advantage"))
    kinetic_tl=_group_mean(k,("tl",),("win_rate","tp_conflict_turn_rate","tp_fulfillment_rate","firm_track_turn_rate","ammo_exhausted_rate","duration_concern_rate","direct_shots_per_turn","direct_hit_rate","direct_raw_damage_per_hit","direct_hull_conversion","damage_inflicted_per_turn","damage_advantage"))
    e=[r for r in contexts if r["candidate_weapon"]=="E"]
    # Matched K-vs-E decomposition: hold TL/resource/stratum/opponent constant and change only candidate main-weapon family.
    eidx={(r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],r["opponent_weapon"]):r for r in e};matched=[]
    delta_metrics=("win_rate","tp_conflict_turn_rate","tp_fulfillment_rate","firm_track_turn_rate","duration_concern_rate","direct_shots_per_turn","direct_hit_rate","direct_raw_damage_per_hit","direct_hull_conversion","damage_inflicted_per_turn","damage_advantage")
    for kr in k:
        erow=eidx.get((kr["tl"],kr["resource_ensemble_id"],kr["scenario_stratum"],kr["opponent_weapon"]))
        if erow is None:continue
        row={"tl":kr["tl"],"resource_ensemble_id":kr["resource_ensemble_id"],"scenario_stratum":kr["scenario_stratum"],"opponent_weapon":kr["opponent_weapon"]}
        for metric in delta_metrics:row[f"k_minus_e_{metric}"]=float(kr[metric])-float(erow[metric])
        matched.append(row)
    matched_metrics=tuple(f"k_minus_e_{m}" for m in delta_metrics)
    kinetic_vs_energy=_group_mean(matched,("tl","opponent_weapon","scenario_stratum"),matched_metrics)
    kinetic_vs_energy_tl=_group_mean(matched,("tl",),matched_metrics)
    energy=_group_mean(e,("tl","resource_ensemble_id"),("win_rate","tp_conflict_turn_rate","tp_fulfillment_rate","firm_track_turn_rate","duration_concern_rate","direct_shots_per_turn","direct_hit_rate","damage_inflicted_per_turn","damage_advantage"))
    base={(r["tl"]):r for r in energy if r["resource_ensemble_id"]=="R1_CENTRAL_NO_MAJOR"}
    for r in energy:
        b=base.get(r["tl"]);r["delta_win_rate_vs_r1"]=r["win_rate"]-b["win_rate"] if b else 0.0;r["delta_tp_conflict_vs_r1"]=r["tp_conflict_turn_rate"]-b["tp_conflict_turn_rate"] if b else 0.0
    # PDS aggregate from accepted surface, oriented Missile attacker -> K/E defender.
    pg=defaultdict(list);pmap={"KINETIC_PDS_PRESSURE":"KineticPDS","ENERGY_PDS_PRESSURE":"EnergyPDS","AMM_PDS_PRESSURE":"AMM"}
    for r in rows:
        if r["scenario_stratum"] not in pmap or r["side_a_weapon"] not in {"M_GP","M_SWARMER"} or r["side_b_weapon"] not in {"K","E"}:continue
        pg[(int(r["tl"]),r["side_a_weapon"],pmap[r["scenario_stratum"]],r["resource_ensemble_id"])].append(r)
    pds=[]
    for key,rs in sorted(pg.items()):
        launches=statistics.fmean(float(x["mean_a_missile_launches"]) for x in rs);term=statistics.fmean(float(x["mean_b_missile_terminal_arrivals"]) for x in rs);att=statistics.fmean(float(x["mean_b_pds_attempts"]) for x in rs);inter=statistics.fmean(float(x["mean_b_pds_intercepts"]) for x in rs);turns=statistics.fmean(float(x["mean_b_side_turns"]) for x in rs)
        pds.append({"tl":key[0],"missile_family":key[1],"pds_family":key[2],"resource_ensemble_id":key[3],"defender_weapon_contexts":len(rs),"mean_missile_launches":launches,"mean_terminal_arrivals":term,"mean_pds_attempts":att,"mean_pds_intercepts":inter,
            "attempts_per_launch":att/launches if launches else 0.0,"attempts_per_terminal":att/term if term else 0.0,"intercepts_per_attempt":inter/att if att else 0.0,"intercepts_per_launch":inter/launches if launches else 0.0,
            "terminal_arrivals_per_launch":term/launches if launches else 0.0,"pds_power_shortfalls_per_turn":statistics.fmean(float(x["mean_b_pds_power_shortfalls"]) for x in rs)/max(turns,1e-12)})
    hotspots=sorted(rows,key=lambda r:(-float(r["gameplay_duration_concern_rate"]),-float(r["turn_cap_rate"]),-(float(r["mean_a_weapon_power_shortfalls"])+float(r["mean_b_weapon_power_shortfalls"])),r["scenario_id"]))[:100]
    hotspot=[{k:r[k] for k in ("scenario_id","tl","side_a_weapon","side_b_weapon","resource_ensemble_id","scenario_stratum","gameplay_duration_concern_rate","turn_cap_rate","mean_turns_all","mean_a_weapon_power_shortfalls","mean_b_weapon_power_shortfalls","a_tp_conflict_turn_rate","b_tp_conflict_turn_rate")} for r in hotspots]
    return {"pareto_objective_diagnostics":pdiag,"strategic_viability_surface":strategic,"kinetic_attribution":kinetic,"kinetic_tl_summary":kinetic_tl,"kinetic_vs_energy_attribution":kinetic_vs_energy,"kinetic_vs_energy_tl_summary":kinetic_vs_energy_tl,"energy_resource_attribution":energy,"pds_baseline_attribution":pds,"duration_hotspots":hotspot}


def _worker_init(repo_text: str, matrix_relative: str, er: list[dict[str,str]], tr: list[dict[str,str]]) -> None:
    global _WORKER_MATRICES
    repo=Path(repo_text);_WORKER_MATRICES={eid:build_deep_resource_matrix(repo,matrix_relative,eid,er,tr) for eid in sorted({r["ensemble_id"] for r in er})}


def _diag_task(args: tuple[Any, ...]) -> dict[str,Any]:
    source,trials,master_seed,*rest=args
    combat_doctrine = str(rest[0]) if rest else LEGACY_COMBAT_DOCTRINE
    if _WORKER_MATRICES is None:raise RuntimeError("CP145 worker matrices not initialized")
    matrix=_WORKER_MATRICES[source["resource_ensemble_id"]];bound=bind_scenario(matrix,source);variant=replace(bound.variant,max_turns=HARD_TURN_SENTINEL)
    counts=defaultdict(int);sums=defaultdict(float);pds=defaultdict(int);errors=[]
    categories=("weapon","pds","sensor","ecm","eccm","shield","armor","damage_control")
    for ti in range(trials):
        events=[];turns=[];ctx={"scenario_id":source["scenario_id"],"resource_ensemble_id":source["resource_ensemble_id"],"weapon_a":source["side_a_weapon"],"weapon_b":source["side_b_weapon"]}
        r=run_trial_full_map(matrix,variant,master_seed,ti,event_sink=events,turn_telemetry_sink=turns,telemetry_context=ctx,combat_doctrine=combat_doctrine)
        if r.error:counts["errors"]+=1;errors.append(r.error)
        if r.turns>=HARD_TURN_SENTINEL and r.unresolved:counts["caps"]+=1
        if not r.unresolved and r.turns>=LONG_RESOLVED_TURN:counts["long"]+=1
        if r.winner=="A":counts["a_wins"]+=1
        elif r.winner=="B":counts["b_wins"]+=1
        elif r.winner=="Draw":counts["draws"]+=1
        sums["turns"]+=r.turns
        sums["nonstandoff_open"]+=max(0,r.full_a.adaptive_open_orders-r.full_a.adaptive_standoff_orders)+max(0,r.full_b.adaptive_open_orders-r.full_b.adaptive_standoff_orders)
        for low, side_t in (("a", r.side_a), ("b", r.side_b)):
            for metric in ("direct_shots", "direct_hits", "missile_launches", "pds_attempts", "pds_intercepts"):
                sums[f"{low}_{metric}"] += int(getattr(side_t, metric, 0))
            for metric in (
                "cp146_weapon_core_funded_turns", "cp146_weapon_core_starved_turns",
                "cp146_active_sensor_default_turns", "cp146_passive_sensor_fallback_turns",
                "cp146_unknown_opponent_turns", "cp146_known_opponent_turns",
                "cp146_pds_unknown_readiness_turns", "cp146_pds_imminent_threat_turns",
                "cp146_pds_irrelevant_suppressed_turns", "cp146_hardener_unknown_readiness_turns",
                "cp146_hardener_relevant_turns", "cp146_hardener_irrelevant_suppressed_turns",
                "cp146_held_main_declarations", "cp146_held_main_attempts",
                "cp146_held_main_intercepts", "cp146_held_main_unused",
                "cp147_package_decisions", "cp147_direct_package_selections",
                "cp147_held_package_selections", "cp147_pds_package_selections",
                "cp147_passive_utility_fallbacks", "cp147_recovery_reserve_turns",
                "cp147_recovery_reserved_tp", "cp147_offense_utility_milli",
                "cp147_defense_utility_milli", "cp147_inbound_threat_turns",
                "cp147_observed_threat_turns", "cp147_terminal_hull_risk_turns",
                "cp147_sole_main_defensive_diversions",
                "cp147_sole_main_diversions_without_hull_risk",
            ):
                sums[f"{low}_{metric}"] += int(getattr(side_t, metric, 0))
        for label in ("A","B"):
            lr=[x for x in turns if x["side_id"]==label];low=label.lower();sums[f"{low}_side_turns"]+=len(lr)
            for x in lr:
                sums[f"{low}_tp_requested"]+=int(x["tp_requested_total"]);sums[f"{low}_tp_denied"]+=int(x["tp_denied_total"]);sums[f"{low}_tp_conflict_turns"]+=int(x["tp_conflict_flag"])
                for cat in categories:
                    sums[f"{low}_requested_{cat}"]+=int(x[f"tp_requested_{cat}"]);sums[f"{low}_denied_{cat}"]+=int(x[f"tp_denied_{cat}"])
                if int(x["tp_requested_weapon"])>0:counts[f"{low}_weapon_request_turns"]+=1
                if int(x["tp_denied_weapon"])>0:counts[f"{low}_weapon_denial_turns"]+=1
                if int(x["pds_threat_flag"]) and int(x["pds_reaction_capacity_planned"])==0:counts[f"{low}_zero_rc_threat_turns"]+=1
        for e in events:
            if e.get("event")!="pds_terminal_phase":continue
            low=str(e["target"]).lower();pds[f"{low}_phases"]+=1
            for field in ("threat_flights","pds_visible_subflights","terminal_magazine_flights",
                          "magazine_flights_with_any_pds_attempt","magazine_flights_fully_covered",
                          "magazine_flights_partially_covered","subflights_with_0_attempts",
                          "subflights_with_1_attempt","subflights_with_2_attempts",
                          "configured_reaction_capacity","planned_reaction_capacity","pds_readiness_tp",
                          "reaction_attempts_used","zero_attempt_flights","one_attempt_flights","two_attempt_flights",
                          "first_attempt_intercepts","second_attempt_intercepts","unserved_attempt_opportunities",
                          "rc_saturated","zero_rc_with_threat"):
                pds[f"{low}_{field}"]+=int(e.get(field,0))
            ammo_before=int(e.get("pds_ammo_before",-1));ammo_after=int(e.get("pds_ammo_after",-1));unserved=int(e.get("unserved_attempt_opportunities",0))
            if ammo_before==0:pds[f"{low}_ammo_empty_before_phases"]+=1
            if ammo_after==0 and unserved>0:pds[f"{low}_ammo_constrained_phases"]+=1
    out={"diagnostic_index":int(source["diagnostic_index"]),"scenario_id":source["scenario_id"],"diagnostic_family":source["diagnostic_family"],"combat_doctrine":combat_doctrine,"tl":int(source["tl"]),"side_a_weapon":source["side_a_weapon"],"side_b_weapon":source["side_b_weapon"],"resource_ensemble_id":source["resource_ensemble_id"],"scenario_stratum":source["scenario_stratum"],"trials":trials,
         "a_wins":counts["a_wins"],"b_wins":counts["b_wins"],"draws":counts["draws"],"turn_cap_sentinels":counts["caps"],"resolved_ge25":counts["long"],"error_trials":counts["errors"],"mean_turns":sums["turns"]/trials,"nonstandoff_open_orders":int(sums["nonstandoff_open"]),"unique_errors":";".join(sorted(set(errors)))[:1000]}
    for low in ("a","b"):
        st=max(1.0,sums[f"{low}_side_turns"]);out[f"{low}_side_turns"]=int(sums[f"{low}_side_turns"]);out[f"{low}_tp_conflict_turn_rate"]=sums[f"{low}_tp_conflict_turns"]/st;out[f"{low}_tp_denied_per_turn"]=sums[f"{low}_tp_denied"]/st
        for metric in ("direct_shots", "direct_hits", "missile_launches", "pds_attempts", "pds_intercepts"):
            out[f"{low}_{metric}"] = int(sums[f"{low}_{metric}"])
        for metric in (
            "cp146_weapon_core_funded_turns", "cp146_weapon_core_starved_turns",
            "cp146_active_sensor_default_turns", "cp146_passive_sensor_fallback_turns",
            "cp146_unknown_opponent_turns", "cp146_known_opponent_turns",
            "cp146_pds_unknown_readiness_turns", "cp146_pds_imminent_threat_turns",
            "cp146_pds_irrelevant_suppressed_turns", "cp146_hardener_unknown_readiness_turns",
            "cp146_hardener_relevant_turns", "cp146_hardener_irrelevant_suppressed_turns",
            "cp146_held_main_declarations", "cp146_held_main_attempts",
            "cp146_held_main_intercepts", "cp146_held_main_unused",
            "cp147_package_decisions", "cp147_direct_package_selections",
            "cp147_held_package_selections", "cp147_pds_package_selections",
            "cp147_passive_utility_fallbacks", "cp147_recovery_reserve_turns",
            "cp147_recovery_reserved_tp", "cp147_offense_utility_milli",
            "cp147_defense_utility_milli", "cp147_inbound_threat_turns",
            "cp147_observed_threat_turns", "cp147_terminal_hull_risk_turns",
            "cp147_sole_main_defensive_diversions",
            "cp147_sole_main_diversions_without_hull_risk",
        ):
            out[f"{low}_{metric}"] = sums[f"{low}_{metric}"]
        out[f"{low}_weapon_request_turn_rate"]=counts[f"{low}_weapon_request_turns"]/st;out[f"{low}_weapon_denial_turn_rate"]=counts[f"{low}_weapon_denial_turns"]/st;out[f"{low}_zero_rc_threat_turn_rate"]=counts[f"{low}_zero_rc_threat_turns"]/st
        for cat in categories:
            out[f"{low}_tp_requested_{cat}_per_turn"]=sums[f"{low}_requested_{cat}"]/st;out[f"{low}_tp_denied_{cat}_per_turn"]=sums[f"{low}_denied_{cat}"]/st
        phases=pds[f"{low}_phases"];threats=pds[f"{low}_threat_flights"]
        out[f"{low}_pds_threat_phases"]=phases;out[f"{low}_pds_threat_flights"]=threats;out[f"{low}_pds_configured_rc_sum"]=pds[f"{low}_configured_reaction_capacity"];out[f"{low}_pds_planned_rc_sum"]=pds[f"{low}_planned_reaction_capacity"];out[f"{low}_pds_readiness_tp_sum"]=pds[f"{low}_pds_readiness_tp"];out[f"{low}_pds_attempts_used"]=pds[f"{low}_reaction_attempts_used"]
        for explicit in ("pds_visible_subflights","terminal_magazine_flights","magazine_flights_with_any_pds_attempt","magazine_flights_fully_covered","magazine_flights_partially_covered","subflights_with_0_attempts","subflights_with_1_attempt","subflights_with_2_attempts"):
            out[f"{low}_{explicit}"] = pds[f"{low}_{explicit}"]
        out[f"{low}_pds_rc_saturated_phases"]=pds[f"{low}_rc_saturated"];out[f"{low}_pds_zero_rc_threat_phases"]=pds[f"{low}_zero_rc_with_threat"];out[f"{low}_pds_unserved_attempt_opportunities"]=pds[f"{low}_unserved_attempt_opportunities"];out[f"{low}_pds_ammo_empty_before_phases"]=pds[f"{low}_ammo_empty_before_phases"];out[f"{low}_pds_ammo_constrained_phases"]=pds[f"{low}_ammo_constrained_phases"]
        out[f"{low}_pds_zero_attempt_flights"]=pds[f"{low}_zero_attempt_flights"];out[f"{low}_pds_one_attempt_flights"]=pds[f"{low}_one_attempt_flights"];out[f"{low}_pds_two_attempt_flights"]=pds[f"{low}_two_attempt_flights"]
        out[f"{low}_pds_first_attempt_intercepts"]=pds[f"{low}_first_attempt_intercepts"];out[f"{low}_pds_second_attempt_intercepts"]=pds[f"{low}_second_attempt_intercepts"]
        out[f"{low}_pds_attempts_per_threat_flight"]=pds[f"{low}_reaction_attempts_used"]/threats if threats else 0.0;out[f"{low}_pds_configured_rc_per_phase"]=pds[f"{low}_configured_reaction_capacity"]/phases if phases else 0.0;out[f"{low}_pds_planned_rc_per_phase"]=pds[f"{low}_planned_reaction_capacity"]/phases if phases else 0.0;out[f"{low}_pds_rc_funding_ratio"]=pds[f"{low}_planned_reaction_capacity"]/pds[f"{low}_configured_reaction_capacity"] if pds[f"{low}_configured_reaction_capacity"] else 0.0;out[f"{low}_pds_rc_saturation_phase_rate"]=pds[f"{low}_rc_saturated"]/phases if phases else 0.0;out[f"{low}_pds_ammo_constrained_phase_rate"]=pds[f"{low}_ammo_constrained_phases"]/phases if phases else 0.0
    return out


def run_analysis(repo: Path, study_path: Path, outdir: Path, jobs: int=24) -> dict[str,Any]:
    doc=load_json(study_path);fail=validate_study(doc)+validate_population(repo,doc)
    if fail:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["study-validation:"+",".join(fail)]}
    rows,pareto,accepted_summary=_accepted_surfaces(repo,doc);analyses=_accepted_analyses(rows,pareto);outdir.mkdir(parents=True,exist_ok=True)
    for name,data in analyses.items():_write_csv(outdir/f"{name}.csv",data)
    manifest=_read_csv(repo/doc["diagnosticReplayManifest"]);stage_manifest=_read_csv(repo/doc["stageAExperimentManifest"]);stage_by_id={r["scenario_id"]:r for r in stage_manifest};stage_doc=load_json(repo/doc["stageAStudy"]);er,tr=_resource_rows(repo,stage_doc)
    replay_sources=[]
    for selection in manifest:
        source=dict(stage_by_id[selection["scenario_id"]]);source.update(selection);replay_sources.append(source)
    source_matrix=repo/doc["matrix"];before=_sha(source_matrix);master_seed=int(stage_doc["masterSeed"]);trials=int(doc["diagnosticTrialsPerScenario"]);tasks=[(r,trials,master_seed) for r in replay_sources];jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc["matrix"],er,tr);done=[_diag_task(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],er,tr)) as ex:done=list(ex.map(_diag_task,tasks,chunksize=1))
    done.sort(key=lambda r:r["diagnostic_index"]);_write_csv(outdir/"diagnostic_replay_results.csv",done)
    pds=[r for r in done if r["diagnostic_family"]=="PDS_OPPORTUNITY"];tp=[r for r in done if r["diagnostic_family"]=="TP_STARVATION"]
    _write_csv(outdir/"pds_opportunity_replay.csv",pds);_write_csv(outdir/"tp_starvation_replay.csv",tp)
    # Compact TP category attribution by TL/stratum/side weapon.
    tg=defaultdict(list)
    for r in tp:
        for low,weapon in (("a",r["side_a_weapon"]),("b",r["side_b_weapon"])):tg[(r["tl"],r["scenario_stratum"],weapon)].append((r,low))
    tsum=[];cats=("weapon","pds","sensor","ecm","eccm","shield","armor","damage_control")
    for key,rs in sorted(tg.items()):
        o={"tl":key[0],"scenario_stratum":key[1],"weapon":key[2],"scenario_sides":len(rs),"mean_tp_conflict_turn_rate":statistics.fmean(float(r[f"{low}_tp_conflict_turn_rate"]) for r,low in rs),"mean_weapon_denial_turn_rate":statistics.fmean(float(r[f"{low}_weapon_denial_turn_rate"]) for r,low in rs)}
        for cat in cats:o[f"mean_tp_requested_{cat}_per_turn"]=statistics.fmean(float(r[f"{low}_tp_requested_{cat}_per_turn"]) for r,low in rs);o[f"mean_tp_denied_{cat}_per_turn"]=statistics.fmean(float(r[f"{low}_tp_denied_{cat}_per_turn"]) for r,low in rs)
        tsum.append(o)
    _write_csv(outdir/"tp_starvation_category_summary.csv",tsum)
    after=_sha(source_matrix);failures=[]
    if len(done)!=EXPECTED_DIAGNOSTIC_SCENARIOS:failures.append("diagnostic-scenario-count")
    if sum(int(r["trials"]) for r in done)!=EXPECTED_DIAGNOSTIC_TRIALS:failures.append("diagnostic-trial-count")
    if any(int(r["error_trials"]) for r in done):failures.append("diagnostic-errors")
    if any(int(r["nonstandoff_open_orders"]) for r in done):failures.append("engage-adaptive-nonstandoff-open-regression")
    if len(pds)!=EXPECTED_PDS_SCENARIOS or len(tp)!=EXPECTED_TP_SCENARIOS:failures.append("diagnostic-family-count")
    if before!=after:failures.append("source-matrix-modified")
    unique_original_survivors=defaultdict(int)
    for r in pareto:
        if int(r["pareto_viable"]):unique_original_survivors[(r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],r["opponent_weapon"])]+=1
    original_single=sum(v==1 for v in unique_original_survivors.values())
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":145,"baseCheckpoint":144,"passed":not failures,"failedGates":failures,
        "acceptedCp144SubstantiveTrials":int(accepted_summary["substantiveCombatTrials"]),"acceptedCp144Scenarios":int(accepted_summary["stageAScenarios"]),
        "diagnosticScenarios":len(done),"diagnosticTrialsPerScenario":trials,"diagnosticCombatTrials":sum(int(r["trials"]) for r in done),"pdsOpportunityScenarios":len(pds),"tpStarvationScenarios":len(tp),
        "sourceMatrixUnmodified":before==after,"tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,
        "originalParetoWinFastCorrelation":_pearson([float(r["side_symmetric_win_rate"]) for r in pareto],[float(r["side_symmetric_fast_win_rate"]) for r in pareto]),"originalParetoSingleSurvivorContexts":original_single,
        "strategicParetoRows":len(analyses["strategic_viability_surface"]),"kineticAttributionRows":len(analyses["kinetic_attribution"]),"kineticVsEnergyAttributionRows":len(analyses["kinetic_vs_energy_attribution"]),"energyResourceRows":len(analyses["energy_resource_attribution"]),"pdsBaselineRows":len(analyses["pds_baseline_attribution"]),
        "interpretation":"Accepted CP144 evidence decomposition plus exact-seed observation-only replays; no numerical tuning or promotion."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary
