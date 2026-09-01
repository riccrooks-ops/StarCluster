from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .ecology import CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE
from .stage_a_diagnostic_attribution import _diag_task, _worker_init
from .stage_a_integration_analysis import _read_csv, _resource_rows
from .study import load_json

RESULT_SCHEMA = "star-cluster-cp147-tactical-package-utility-result-v0.1"
EXPECTED_SCENARIOS = 252
TRIALS_PER_SCENARIO = 25
EXPECTED_PER_DOCTRINE = EXPECTED_SCENARIOS * TRIALS_PER_SCENARIO


def _sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str,Any]]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows: path.write_text("",encoding="utf-8"); return
    fields=[]
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def validate_study(doc: dict[str,Any]) -> list[str]:
    errors=[]
    exact={
        "schemaVersion":"star-cluster-cp147-tactical-package-utility-study-v0.1",
        "checkpoint":147,"baseCheckpoint":146,
        "baselineDoctrine":CONTEXTUAL_COMBAT_DOCTRINE,"candidateDoctrine":UTILITY_COMBAT_DOCTRINE,
        "expectedScenarios":EXPECTED_SCENARIOS,"trialsPerScenarioPerDoctrine":TRIALS_PER_SCENARIO,
        "expectedCombatTrialsPerDoctrine":EXPECTED_PER_DOCTRINE,"expectedTotalCombatTrials":2*EXPECTED_PER_DOCTRINE,
        "masterSeed":140001,"tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,
    }
    for k,v in exact.items():
        if doc.get(k)!=v: errors.append(f"{k}: expected {v!r}, found {doc.get(k)!r}")
    if len(doc.get("utilityDoctrineRequirements",[]))<10: errors.append("utilityDoctrineRequirements incomplete")
    return errors


def validate_population(repo:Path,doc:dict[str,Any])->list[str]:
    errors=validate_study(doc)
    for field,hash_field in (
        ("matrix","matrixSha256"),("acceptedCp146NativeSummary","acceptedCp146NativeSummarySha256"),
        ("acceptedCp146DoctrineSummary","acceptedCp146DoctrineSummarySha256"),
        ("acceptedCp146ContextualResults","acceptedCp146ContextualResultsSha256")):
        p=repo/str(doc[field])
        if not p.is_file(): errors.append(f"missing {field}: {p}"); continue
        if _sha(p)!=str(doc[hash_field]): errors.append(f"hash mismatch: {field}")
    manifest=_read_csv(repo/doc["diagnosticReplayManifest"])
    if len(manifest)!=EXPECTED_SCENARIOS: errors.append(f"diagnostic replay rows: {len(manifest)}")
    ids=[r["scenario_id"] for r in manifest]
    if len(set(ids))!=len(ids): errors.append("diagnostic replay scenario ids are not unique")
    stage=_read_csv(repo/doc["stageAExperimentManifest"]); stage_ids={r["scenario_id"] for r in stage}
    if set(ids)-stage_ids: errors.append("diagnostic identities missing from CP144 manifest")
    accepted=_read_csv(repo/doc["acceptedCp146ContextualResults"])
    if len(accepted)!=EXPECTED_SCENARIOS or {r["scenario_id"] for r in accepted}!=set(ids): errors.append("accepted CP146 contextual population mismatch")
    fixture=load_json(repo/doc["utilityParityFixtures"])
    if fixture.get("checkpoint")!=147 or len(fixture.get("cases",[]))<8: errors.append("CP147 utility parity fixture invalid")
    return errors


def _same_value(a:str,b:Any)->bool:
    if a=="" and (b=="" or b is None): return True
    try: return math.isclose(float(a),float(b),rel_tol=0.0,abs_tol=1e-12)
    except (TypeError,ValueError): return str(a)==str(b)


def _comparison(accepted:list[dict[str,str]], replayed:list[dict[str,Any]])->tuple[list[dict[str,Any]],int]:
    by={r["scenario_id"]:r for r in accepted}; rows=[]; mismatches=0
    for row in replayed:
        old=by[row["scenario_id"]]; bad=[field for field,value in old.items() if field not in row or not _same_value(value,row[field])]
        mismatches+=len(bad); rows.append({"scenario_id":row["scenario_id"],"matching_fields":len(old)-len(bad),"field_mismatches":len(bad),"mismatched_fields":";".join(bad)})
    return rows,mismatches


def _deltas(base:list[dict[str,Any]],cand:list[dict[str,Any]])->list[dict[str,Any]]:
    old={r["scenario_id"]:r for r in base}; out=[]
    metrics=("a_wins","b_wins","draws","turn_cap_sentinels","resolved_ge25","mean_turns","a_weapon_denial_turn_rate","b_weapon_denial_turn_rate","a_pds_attempts","b_pds_attempts","a_direct_shots","b_direct_shots")
    for r in cand:
        b=old[r["scenario_id"]]; row={k:r[k] for k in ("diagnostic_index","scenario_id","diagnostic_family","tl","side_a_weapon","side_b_weapon","resource_ensemble_id","scenario_stratum")}
        for m in metrics: row[f"cp146_{m}"]=b[m]; row[f"cp147_{m}"]=r[m]; row[f"delta_{m}"]=float(r[m])-float(b[m])
        out.append(row)
    return out


def _tp_before_after(base:list[dict[str,Any]],cand:list[dict[str,Any]])->list[dict[str,Any]]:
    groups=defaultdict(lambda:{"cp146":[],"cp147":[]})
    for label,rows in (("cp146",base),("cp147",cand)):
        for r in rows:
            if r["diagnostic_family"]=="TP_STARVATION": groups[(int(r["tl"]),str(r["scenario_stratum"]))][label].append(r)
    out=[]
    for key,g in sorted(groups.items()):
        row={"tl":key[0],"scenario_stratum":key[1],"scenarios":len(g["cp146"])}
        for label in ("cp146","cp147"):
            rs=g[label]; combats=sum(int(x["trials"]) for x in rs); caps=sum(int(x["turn_cap_sentinels"]) for x in rs)
            row[f"{label}_combats"]=combats; row[f"{label}_turn_caps"]=caps; row[f"{label}_turn_cap_rate"]=caps/combats if combats else 0.0
            row[f"{label}_mean_weapon_denial_turn_rate"]=statistics.fmean((float(x["a_weapon_denial_turn_rate"])+float(x["b_weapon_denial_turn_rate"]))/2 for x in rs)
        out.append(row)
    return out


def _action_summary(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:
        for low,weapon in (("a",r["side_a_weapon"]),("b",r["side_b_weapon"])): groups[(r["diagnostic_family"],weapon)].append((r,low))
    out=[]
    metrics=("cp147_package_decisions","cp147_direct_package_selections","cp147_held_package_selections","cp147_pds_package_selections","cp147_passive_utility_fallbacks","cp147_recovery_reserve_turns","cp147_recovery_reserved_tp","cp147_inbound_threat_turns","cp147_observed_threat_turns","cp147_terminal_hull_risk_turns","cp147_sole_main_defensive_diversions","cp147_sole_main_diversions_without_hull_risk","cp146_held_main_attempts","cp146_held_main_intercepts","cp146_held_main_unused")
    for key,rs in sorted(groups.items()):
        row={"diagnostic_family":key[0],"weapon":key[1],"scenario_sides":len(rs)}
        for m in metrics: row[m]=sum(int(float(r.get(f"{low}_{m}",0))) for r,low in rs)
        row["offense_utility_milli"]=sum(int(float(r.get(f"{low}_cp147_offense_utility_milli",0))) for r,low in rs)
        row["defense_utility_milli"]=sum(int(float(r.get(f"{low}_cp147_defense_utility_milli",0))) for r,low in rs)
        out.append(row)
    return out


def _missile_action_summary(rows:list[dict[str,Any]])->list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:
        if r["diagnostic_family"]!="PDS_OPPORTUNITY": continue
        # CP145/146 selection fixes Missile attacker as A, K/E+PDS defender as B.
        groups[(r["side_a_weapon"],r["side_b_weapon"],r["resource_ensemble_id"],r["scenario_stratum"])].append(r)
    out=[]
    for key,rs in sorted(groups.items()):
        sm=lambda m:sum(int(float(r.get(f"b_{m}",0))) for r in rs)
        out.append({"missile_family":key[0],"defender_main":key[1],"resource_ensemble_id":key[2],"scenario_stratum":key[3],"scenario_rows":len(rs),
                    "package_decisions":sm("cp147_package_decisions"),"direct_package_selections":sm("cp147_direct_package_selections"),"held_package_selections":sm("cp147_held_package_selections"),"pds_package_selections":sm("cp147_pds_package_selections"),
                    "terminal_threat_turns":sm("cp147_inbound_threat_turns"),"terminal_hull_risk_turns":sm("cp147_terminal_hull_risk_turns"),"sole_main_defensive_diversions":sm("cp147_sole_main_defensive_diversions"),"sole_main_diversions_without_hull_risk":sm("cp147_sole_main_diversions_without_hull_risk"),
                    "held_main_attempts":sm("cp146_held_main_attempts"),"held_main_intercepts":sm("cp146_held_main_intercepts"),"pds_attempts":sum(int(r["b_pds_attempts"]) for r in rs),"direct_shots":sum(int(r["b_direct_shots"]) for r in rs)})
    return out


def run_analysis(repo:Path,study_path:Path,outdir:Path,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path); failures=validate_population(repo,doc)
    if failures: return {"schemaVersion":RESULT_SCHEMA,"checkpoint":147,"passed":False,"failedGates":failures}
    outdir.mkdir(parents=True,exist_ok=True)
    replay=_read_csv(repo/doc["diagnosticReplayManifest"]); stage=_read_csv(repo/doc["stageAExperimentManifest"]); stage_by={r["scenario_id"]:r for r in stage}
    stage_doc=load_json(repo/doc["stageAStudy"]); er,tr=_resource_rows(repo,stage_doc); sources=[]
    for selection in replay:
        source=dict(stage_by[selection["scenario_id"]]);source.update(selection);sources.append(source)
    before=_sha(repo/doc["matrix"]); trials=int(doc["trialsPerScenarioPerDoctrine"]); seed=int(doc["masterSeed"]); jobs=max(1,min(int(jobs),len(sources)))
    def execute(doctrine:str)->list[dict[str,Any]]:
        tasks=[(r,trials,seed,doctrine) for r in sources]
        if jobs==1:
            _worker_init(str(repo),doc["matrix"],er,tr); done=[_diag_task(t) for t in tasks]
        else:
            ctx=get_context("spawn" if os.name=="nt" else "fork")
            with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],er,tr)) as ex: done=list(ex.map(_diag_task,tasks,chunksize=1))
        done.sort(key=lambda r:int(r["diagnostic_index"])); return done
    baseline=execute(CONTEXTUAL_COMBAT_DOCTRINE); candidate=execute(UTILITY_COMBAT_DOCTRINE)
    _write_csv(outdir/"cp146_replay_results.csv",baseline);_write_csv(outdir/"cp147_replay_results.csv",candidate)
    audit,mismatches=_comparison(_read_csv(repo/doc["acceptedCp146ContextualResults"]),baseline);_write_csv(outdir/"cp146_reproduction_audit.csv",audit)
    _write_csv(outdir/"utility_delta_results.csv",_deltas(baseline,candidate));tp=_tp_before_after(baseline,candidate);_write_csv(outdir/"tp_starvation_before_after.csv",tp)
    actions=_action_summary(candidate);_write_csv(outdir/"utility_action_summary.csv",actions);missiles=_missile_action_summary(candidate);_write_csv(outdir/"missile_action_selection_summary.csv",missiles)
    after=_sha(repo/doc["matrix"])
    if mismatches: failures.append(f"accepted-cp146-reproduction:{mismatches}-field-mismatches")
    for label,rows in (("cp146",baseline),("cp147",candidate)):
        if len(rows)!=EXPECTED_SCENARIOS: failures.append(f"{label}-scenario-count")
        if sum(int(r["trials"]) for r in rows)!=EXPECTED_PER_DOCTRINE: failures.append(f"{label}-trial-count")
        if any(int(r["error_trials"]) for r in rows): failures.append(f"{label}-trial-errors")
        if any(int(r["nonstandoff_open_orders"]) for r in rows): failures.append(f"{label}-nonstandoff-open")
    if before!=after: failures.append("source-matrix-modified")
    base_by={r["scenario_id"]:r for r in baseline}
    new_saturated=[r["scenario_id"] for r in candidate if int(r["turn_cap_sentinels"])==int(r["trials"]) and int(base_by[r["scenario_id"]]["turn_cap_sentinels"])<int(base_by[r["scenario_id"]]["trials"])]
    if new_saturated: failures.append(f"cp147-created-saturated-turn-cap-cells:{len(new_saturated)}")
    tl2=[r for r in candidate if r["diagnostic_family"]=="TP_STARVATION" and int(r["tl"])==2 and r["scenario_stratum"] in {"EW_CONTEST","POWER_CRISIS"}]
    tl2_caps=sum(int(r["turn_cap_sentinels"]) for r in tl2)
    if tl2_caps>0: failures.append(f"cp147-tl2-pathology-regressed:{tl2_caps}-turn-caps")
    total_caps=sum(int(r["turn_cap_sentinels"]) for r in candidate)
    if total_caps>0: failures.append(f"cp147-turn-cap-sentinels:{total_caps}")
    held=sum(int(r["cp147_held_package_selections"]) for r in actions); direct=sum(int(r["cp147_direct_package_selections"]) for r in actions)
    held_attempts=sum(int(r["cp146_held_main_attempts"]) for r in actions)
    invalid_diversions=sum(int(r["cp147_sole_main_diversions_without_hull_risk"]) for r in actions)
    if direct<=0: failures.append("cp147-direct-package-selection-not-observed")
    if held<=0 or held_attempts<=0: failures.append("cp147-held-main-not-naturally-exercised")
    if invalid_diversions>0: failures.append(f"cp147-sole-main-diversion-without-hull-risk:{invalid_diversions}")
    package_decisions=sum(int(r["cp147_package_decisions"]) for r in actions)
    if package_decisions<=0: failures.append("cp147-utility-selector-not-observed")
    if sum(int(r["cp147_pds_package_selections"]) for r in actions)<=0: failures.append("cp147-pds-utility-selection-not-observed")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":147,"baseCheckpoint":146,"passed":not failures,"failedGates":failures,
             "scenariosPerDoctrine":len(candidate),"trialsPerScenarioPerDoctrine":trials,"combatTrialsPerDoctrine":sum(int(r["trials"]) for r in candidate),"totalCombatTrials":sum(int(r["trials"]) for r in baseline+candidate),
             "acceptedCp146FieldMismatches":mismatches,"sourceMatrixUnmodified":before==after,"tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,
             "cp147TurnCapSentinels":total_caps,"cp147Tl2TurnCapSentinels":tl2_caps,"cp147NewSaturatedTurnCapCells":len(new_saturated),
             "cp147PackageDecisions":package_decisions,"cp147DirectPackageSelections":direct,"cp147HeldPackageSelections":held,"cp147HeldMainAttempts":held_attempts,
             "cp147PdsPackageSelections":sum(int(r["cp147_pds_package_selections"]) for r in actions),"cp147SoleMainDiversionsWithoutHullRisk":invalid_diversions,
             "interpretation":"Logic-only matched CP146/CP147 tactical-package study. Utility chooses powered actions from legitimate current knowledge; no component statistic is tuned or promoted."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
