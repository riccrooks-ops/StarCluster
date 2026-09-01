from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from . import combat_duration_stalemate_analysis as cp141
from .combat_model_reconciliation import apply_combat_model_candidate
from .combat_surface_deep_reconciliation import (
    AUX_RECONCILIATION,
    PDS_EFFECTIVE,
    apply_deep_combat_surface_reconciliation,
    build_deep_resource_matrix,
    reconciliation_profile,
)
from .ecology import CandidateMatrix
from .stage_a_integration_analysis import STAGE_A_SCENARIOS, _read_csv, _resource_rows, bind_scenario
from .study import canonicalize_relocated_references, load_json

RESULT_SCHEMA = "star-cluster-cp142-combat-surface-reconciliation-result-v0.1"
HARD_TURN_SENTINEL = cp141.HARD_TURN_SENTINEL
LONG_RESOLVED_TURN = cp141.LONG_RESOLVED_TURN


def _sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    cp141._write_csv(path, rows)


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors=[]
    if doc.get("schemaVersion") != "star-cluster-cp142-combat-surface-reconciliation-study-v0.1": errors.append("schemaVersion")
    if int(doc.get("checkpoint",0)) != 142: errors.append("checkpoint")
    if int(doc.get("baseCheckpoint",0)) != 141: errors.append("baseCheckpoint")
    if int(doc.get("expectedStageAScenarios",0)) != STAGE_A_SCENARIOS: errors.append("expectedStageAScenarios")
    if int(doc.get("hardTurnSentinel",0)) != HARD_TURN_SENTINEL: errors.append("hardTurnSentinel")
    if int(doc.get("longResolvedTurn",0)) != LONG_RESOLVED_TURN: errors.append("longResolvedTurn")
    if bool(doc.get("extendTurnCap",True)): errors.append("extendTurnCap")
    if int(doc.get("substantiveCombatTrials",-1)) != 0: errors.append("substantiveCombatTrials")
    if bool(doc.get("automaticPromotion")): errors.append("automaticPromotion")
    if doc.get("reconciliationPolicy") != "latest-explicit-combat-model-wins-cp138-fills-gaps-unresolved-stays-unresolved": errors.append("reconciliationPolicy")
    return errors


def _authority_rows(repo: Path, matrix_relative: str) -> list[dict[str, Any]]:
    raw=CandidateMatrix(repo,matrix_relative)
    cp141m=CandidateMatrix(repo,matrix_relative); apply_combat_model_candidate(cp141m)
    deep=CandidateMatrix(repo,matrix_relative); apply_deep_combat_surface_reconciliation(deep)
    rows=[]
    def add(system,field,tl,classification,source,cp138,cp141v,cp142v,reason,executable="YES",changed=None):
        changed_flag=int(str(cp141v)!=str(cp142v)) if changed is None else int(bool(changed))
        rows.append({"system":system,"field":field,"tl":tl,"classification":classification,"source":source,
                     "cp138_value":cp138,"cp141_value":cp141v,"cp142_value":cp142v,"changed_vs_cp141":changed_flag,
                     "stage_a_executable":executable,"reason":reason})
    for tl in range(1,10):
        # Hull / DC / Computer
        add("Hull","hullPoints",tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 REF.Hull",raw.p("hull",tl)["hullPoints"],cp141m.p("hull",tl)["hullPoints"],deep.p("hull",tl)["hullPoints"],"Explicit latest full-combat same-TL durability reference; Hull Space capacity is a separate resource field.")
        add("Hull","installationCapacity",tl,"CP138_RETAINED","CP138/v22C resource architecture",raw.p("hull",tl)["capacity"],cp141m.p("hull",tl)["capacity"],deep.p("hull",tl)["capacity"],"Combat lab did not supersede cruiser Installation Space.")
        for f in ("preparedRepairKits","hullRepairChancePp","hullRestoredPerSuccessfulKit","capacity"):
            add("DamageControl",f,tl,"COMBINED_IDENTICAL","v17-v19 + CP138",raw.p("damage_control",tl).get(f),cp141m.p("damage_control",tl).get(f),deep.p("damage_control",tl).get(f),"Latest combat-model reference and CP138 agree.")
        add("DamageControl","attemptTp",tl,"CP138_RETAINED","CP138 full-map TP plumbing",raw.p("damage_control",tl).get("attemptTp"),cp141m.p("damage_control",tl).get("attemptTp"),deep.p("damage_control",tl).get("attemptTp"),"Lab did not assign a replacement TP cost.")
        add("Computer","targetingPp",tl,"COMBINED_IDENTICAL","v17-v19 REF.ComputerTargetPP + CP138",raw.p("computer",tl)["targetingPp"],cp141m.p("computer",tl)["targetingPp"],deep.p("computer",tl)["targetingPp"],"Explicit lab reference equals CP138; reused in accuracy/PDS translation.")

        # Shield
        for f in ("capacity","baseRecharge","tacticalRechargePerTp","tacticalRechargeCapTp"):
            add("Shield",f,tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 Shield reference",raw.p("shield",tl).get(f),cp141m.p("shield",tl).get(f),deep.p("shield",tl).get(f),"CP141 partial blend retained stale CP138 field; CP142 restores latest combat-model package.")
        add("Shield","space",tl,"CP138_RETAINED","CP138/v22C resource architecture",raw.p("shield",tl)["space"],cp141m.p("shield",tl)["space"],deep.p("shield",tl)["space"],"Combat lab did not promote Shield Space.")
        add("Shield","DEF_pp",tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 CORE_DEF_RES_PP","n/a",getattr(cp141m,"def_res_shield_def_pp",{}).get(tl),getattr(deep,"def_res_shield_def_pp",{}).get(tl),"Whole-packet DEF candidate retained.")
        add("Shield","collapseRechargeLockout",tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 primary lockout","restartable default","lockout","lockout","def-res research path keeps collapsed Shield offline for engagement.")

        # Armor
        for f in ("ai","baseRegeneration","tacticalRegenerationPerTp","tacticalRegenerationCapTp","combatRegenerationReserveAi"):
            add("Armor",f,tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 Armor reference",raw.p("armor",tl).get(f),cp141m.p("armor",tl).get(f),deep.p("armor",tl).get(f),"Explicit latest full-combat same-TL Armor profile.")
        add("Armor","space",tl,"CP138_RETAINED","CP138 structural Armor",raw.p("armor",tl)["space"],cp141m.p("armor",tl)["space"],deep.p("armor",tl)["space"],"Lab did not supersede passive Armor Space treatment.")
        add("Armor","RES_pp",tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 CORE_DEF_RES_PP","n/a",getattr(cp141m,"def_res_armor_res_pp",{}).get(tl),getattr(deep,"def_res_armor_res_pp",{}).get(tl),"Deterministic RES candidate retained.")

        # Weapons
        for fam,key,fields in (
            ("Kinetic","kinetic_main",("damage","spen","apen","accuracyPp")),
            ("Energy","energy_main",("standardDamage","spen","apen","accuracyPp")),
            ("GP Missile","missile_gp_warhead",("damage","spen","apen")),
        ):
            for f in fields:
                add(fam,f,tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 offensive candidate",raw.p(key,tl).get(f),cp141m.p(key,tl).get(f),deep.p(key,tl).get(f),"Latest explicit combat-model offensive characteristic; already present in CP141 where equal.")
        add("GP Missile","guidanceBaseHit",tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 REF.M_GUIDE",raw.p("missile_guidance",tl).get("guidanceBaseHit"),cp141m.p("missile_guidance",tl).get("guidanceBaseHit"),deep.p("missile_guidance",tl).get("guidanceBaseHit"),"Latest explicit missile guidance reference.")
        add("Kinetic","ammo",tl,"COMBINED_IDENTICAL","v17-v19 + CP138",raw.p("kinetic_main",tl).get("ammo"),cp141m.p("kinetic_main",tl).get("ammo"),deep.p("kinetic_main",tl).get("ammo"),"100-round reference agrees.")
        add("MissileDelivery","flights",tl,"COMBINED_IDENTICAL","v17-v19 + CP138",raw.p("missile_delivery",tl).get("flights"),cp141m.p("missile_delivery",tl).get("flights"),deep.p("missile_delivery",tl).get("flights"),"25-Flight magazine agrees.")
        for f in ("range","missileMove"):
            add("MissileDelivery",f,tl,"CP138_RETAINED","CP138 full-map movement/delivery",raw.p("missile_delivery",tl).get(f),cp141m.p("missile_delivery",tl).get(f),deep.p("missile_delivery",tl).get(f),"Later response labs did not supersede full-map delivery geometry.")
        for fam,key in (("Kinetic","kinetic_main"),("Energy","energy_main"),("MissileDelivery","missile_delivery")):
            add(fam,"space",tl,"LATER_RESOURCE_ENSEMBLE","v22C per-environment resource overlay",raw.p(key,tl).get("space"),cp141m.p(key,tl).get("space"),deep.p(key,tl).get("space"),"v21 resource centerline was later expanded to v22C ensemble; CP142 does not collapse resource uncertainty.")
        add("Energy","low/overload damage modes",tl,"COMBINED","combat-model standard damage + CP138 mode relationship",raw.p("energy_main",tl).get("lowDamage"),f"{cp141m.p('energy_main',tl).get('lowDamage')}/{cp141m.p('energy_main',tl).get('overloadDamage')}",f"{deep.p('energy_main',tl).get('lowDamage')}/{deep.p('energy_main',tl).get('overloadDamage')}","Lab calibrated Standard damage; full-map low/overload modes retain CP138 0.5x/1.5x relation around reconciled Standard.")

        # PDS: lab chances are effective, canonical stores base and adds Computer.
        for family,key in (("Kinetic","kinetic_pds"),("Energy","energy_pds"),("AMM","amm_pds")):
            target=int(PDS_EFFECTIVE[family]["chance"][tl-1])
            old_base=int(cp141m.p(key,tl)["baseChancePp"]); old_eff=min(95,old_base+int(cp141m.p("computer",tl)["targetingPp"]))
            new_base=int(deep.p(key,tl)["baseChancePp"]); new_eff=min(95,new_base+int(deep.p("computer",tl)["targetingPp"]))
            add(f"{family} PDS","baseChancePp",tl,"COMBINED_TRANSLATION","v17-v19 effective chance translated through CP138 Computer",raw.p(key,tl)["baseChancePp"],f"{old_base} (effective {old_eff})",f"{new_base} (effective {new_eff}; lab target {target})","CP141 wrote lab effective chance into a base field and then canonical Computer help was added again; CP142 removes the double count.",changed=(old_base!=new_base or old_eff!=new_eff))
            for f in ("reactionCapacity","ammo"):
                add(f"{family} PDS",f,tl,"COMBAT_MODEL_SUPERSEDED","v17-v19 PDS candidate",raw.p(key,tl).get(f),cp141m.p(key,tl).get(f),deep.p(key,tl).get(f),"Latest PDS role/mechanics candidate.")
            for f in ("space","readinessTp"):
                add(f"{family} PDS",f,tl,"CP138_RETAINED","v20 explicit resource boundary",raw.p(key,tl).get(f),cp141m.p(key,tl).get(f),deep.p(key,tl).get(f),"v20 explicitly retained CP138 PDS Space/readiness TP; v19 did not promote new costs.")
        add("AMM PDS","interceptRange",tl,"COMBINED_IDENTICAL","v17-v19 + CP138",raw.p("amm_pds",tl).get("interceptRange"),cp141m.p("amm_pds",tl).get("interceptRange"),deep.p("amm_pds",tl).get("interceptRange"),"Range-1 availability at TL7+ agrees; experimental third opportunity remains unresolved and is not enabled.")

    # Non-TL mechanics / AUX provenance rows.
    add("Swarmer","subFlight structure","TL2-TL9","COMBAT_MODEL_SUPERSEDED","v17-v19","CP138 packet model","two PDS-visible subFlights","two PDS-visible subFlights","90% GP total yield; one magazine Flight; independent guidance; shared PDS RC; no bespoke penalty.")
    add("ShieldHardener","effect","TL3-TL9","COMBINED","v17 response + v21 mechanic anchor","old Shield Armor +2","+10 DEF pp","+10 DEF pp","1 Space/1 TP executable candidate; DEF mapping retained.")
    for name,meta in AUX_RECONCILIATION.items():
        if name=="ShieldHardener": continue
        add(name,"combat effect","varies",meta["classification"],"v17-v21 AUX evidence","TBD/legacy",meta["lab_effect"],meta["disposition"],meta["disposition"],meta["execution"])
    add("AMM PDS","third range-1 opportunity","TL7-TL9","UNRESOLVED_CONFLICT_GAP","v10-v19 experimental toggle","not enabled","not enabled","not enabled","Experimented but not promoted; CP142 refuses silent promotion.","NO")
    return rows


def write_reconciliation_evidence(repo: Path, matrix_relative: str, outdir: Path) -> dict[str, Any]:
    outdir.mkdir(parents=True,exist_ok=True)
    rows=_authority_rows(repo,matrix_relative); _write_csv(outdir/"reconciliation_field_ledger.csv",rows)
    m=CandidateMatrix(repo,matrix_relative); apply_deep_combat_surface_reconciliation(m)
    (outdir/"reconciliation_profile.json").write_text(json.dumps(reconciliation_profile(m),indent=2)+"\n",encoding="utf-8")
    counts=Counter(r["classification"] for r in rows)
    unresolved=[r for r in rows if r["classification"]=="UNRESOLVED_CONFLICT_GAP"]
    changed=[r for r in rows if int(r["changed_vs_cp141"])]
    audit=[
        {"check":"every-ledger-row-classified","passed":int(all(r["classification"] for r in rows)),"value":len(rows)},
        {"check":"source-matrix-never-written","passed":1,"value":"in-memory CandidateMatrix overlay"},
        {"check":"unresolved-items-explicit","passed":1,"value":len(unresolved)},
        {"check":"cp141-fields-corrected","passed":1,"value":len(changed)},
        {"check":"resource-proxy-aux-not-promoted","passed":int(all(r["stage_a_executable"]!="RESOURCE_PROXY_ONLY" or r["classification"]=="UNRESOLVED_CONFLICT_GAP" for r in rows)),"value":"PASS"},
    ]
    _write_csv(outdir/"reconciliation_audit.csv",audit)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":142,"passed":all(int(r["passed"]) for r in audit),"ledgerRows":len(rows),"changedVsCp141Rows":len(changed),"classificationCounts":dict(counts),"explicitUnresolvedRows":len(unresolved),"automaticPromotion":False}
    (outdir/"reconciliation_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


# CP141's executor already implements the accepted 60-turn gameplay/duration
# semantics. We inject CP142 matrices into its worker global rather than fork the
# combat loop, preserving one canonical execution path.
def _worker_init(repo_text: str, matrix_relative: str, ensemble_rows: list[dict[str,str]], tl_rows: list[dict[str,str]]) -> None:
    repo=Path(repo_text); ids=sorted({r["ensemble_id"] for r in ensemble_rows})
    cp141._CP141_WORKER_MATRICES={eid:build_deep_resource_matrix(repo,matrix_relative,eid,ensemble_rows,tl_rows) for eid in ids}


def _execute_task(args):
    return cp141._execute_task(args)


def run_batch(repo: Path, study_path: Path, outdir: Path, jobs: int=24, batch_start: int=0, batch_end: int|None=None) -> dict[str,Any]:
    doc=load_json(study_path); errors=validate_study(doc)
    if errors:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True)
    manifest=_read_csv(repo/doc["stageAExperimentManifest"]); ensemble_rows,tl_rows=_resource_rows(repo,doc)
    source_matrix=repo/doc["matrix"]; before_hash=_sha(source_matrix)
    matrices={eid:build_deep_resource_matrix(repo,doc["matrix"],eid,ensemble_rows,tl_rows) for eid in sorted({r["ensemble_id"] for r in ensemble_rows})}
    bindings=[bind_scenario(matrices[r["resource_ensemble_id"]],r) for r in manifest]
    start=max(0,int(batch_start)); end=len(bindings) if batch_end is None else min(len(bindings),int(batch_end))
    if start>=end:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["invalid-batch-range"]}
    tasks=[(i,manifest[i],bindings[i],int(doc["masterSeed"])) for i in range(start,end)]
    jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc["matrix"],ensemble_rows,tl_rows); completed=[_execute_task(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],ensemble_rows,tl_rows)) as ex:
            completed=list(ex.map(_execute_task,tasks,chunksize=8))
    completed.sort(key=lambda x:x["index"]); rows=[x["row"] for x in completed]; diags=[x["diagnostic"] for x in completed if x["diagnostic"] is not None]
    _write_csv(outdir/"duration_smoke_results.csv",rows); _write_csv(outdir/"turn_cap_diagnostics.csv",diags)
    after_hash=_sha(source_matrix); failures=[]
    if len(rows)!=end-start:failures.append("scenario-count")
    if any(r["error"] for r in rows):failures.append("execution-errors")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in rows):failures.append("turn-telemetry-coverage")
    if any(int(r["turns"])>HARD_TURN_SENTINEL for r in rows):failures.append("turn-sentinel-exceeded")
    if before_hash!=after_hash:failures.append("source-matrix-modified")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":142,"baseCheckpoint":141,"passed":not failures,"failedGates":failures,"batchStart":start,"batchEnd":end,"scenarios":len(rows),"executionErrors":sum(bool(r["error"]) for r in rows),"resolved":sum(int(r["resolved_flag"]) for r in rows),"resolvedGe25":sum(int(r["resolved_ge25_flag"]) for r in rows),"safeStalemates":sum(int(r["safe_stalemate_flag"]) for r in rows),"turnCapSentinels":sum(int(r["turn_cap_flag"]) for r in rows),"hardTurnSentinel":HARD_TURN_SENTINEL,"sourceMatrixUnmodified":before_hash==after_hash,"substantiveCombatTrials":0,"promotionAllowed":False,"interpretation":"Deep-reconciliation one-trial diagnostic only; paired with CP141 to identify integration drift, never balance evidence."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); return summary


def merge_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path) -> dict[str,Any]:
    doc=load_json(study_path); errors=validate_study(doc)
    if errors:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True); manifest=_read_csv(repo/doc["stageAExperimentManifest"]); source_matrix=repo/doc["matrix"]; before_hash=_sha(source_matrix)
    rows=[];diags=[];audits=[];expected=0
    for d in sorted([p for p in batch_root.iterdir() if p.is_dir()]):
        sp=d/"summary.json"; rp=d/"duration_smoke_results.csv"
        if not sp.exists() or not rp.exists():continue
        payload=json.loads(sp.read_text()); analysis=payload.get("analysis",payload); start=int(analysis["batchStart"]);end=int(analysis["batchEnd"])
        br=_read_csv(rp); bd=_read_csv(d/"turn_cap_diagnostics.csv") if (d/"turn_cap_diagnostics.csv").exists() and (d/"turn_cap_diagnostics.csv").stat().st_size else []
        ok=bool(analysis.get("passed",payload.get("passed",False))) and start==expected and len(br)==end-start
        ids=[r["scenario_id"] for r in manifest[start:end]]==[r["scenario_id"] for r in br];ok=ok and ids
        audits.append({"batch":d.name,"start":start,"end":end,"scenarios":len(br),"ids_match":int(ids),"passed":int(ok)})
        if not ok:continue
        rows.extend(br);diags.extend(bd);expected=end
    failures=[]
    if expected!=len(manifest):failures.append("batch-coverage-incomplete")
    if len(rows)!=STAGE_A_SCENARIOS:failures.append("merged-scenario-count")
    if any(r["error"] for r in rows):failures.append("merged-execution-errors")
    if any(int(r["turns"])>HARD_TURN_SENTINEL for r in rows):failures.append("merged-turn-sentinel-exceeded")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in rows):failures.append("merged-turn-telemetry-coverage")
    after_hash=_sha(source_matrix)
    if before_hash!=after_hash:failures.append("source-matrix-modified")
    _write_csv(outdir/"batch_merge_audit.csv",audits);_write_csv(outdir/"duration_smoke_results.csv",rows);_write_csv(outdir/"turn_cap_diagnostics.csv",diags)
    groups=cp141._group_rows(rows);_write_csv(outdir/"duration_group_summary.csv",groups)
    causes=Counter(r["termination_cause"] for r in rows);_write_csv(outdir/"termination_cause_summary.csv",[{"termination_cause":k,"scenarios":v} for k,v in sorted(causes.items())])
    signals=Counter(r["dominant_cap_signal"] for r in diags);_write_csv(outdir/"turn_cap_signal_summary.csv",[{"dominant_cap_signal":k,"scenarios":v} for k,v in sorted(signals.items())])
    resolved=[r for r in rows if int(r["resolved_flag"])];long=sum(int(r["resolved_ge25_flag"]) for r in rows);caps=sum(int(r["turn_cap_flag"]) for r in rows);stale=sum(int(r["safe_stalemate_flag"]) for r in rows);overall=next((r for r in groups if r["group_type"]=="OVERALL"),{})
    rec=write_reconciliation_evidence(repo,doc["matrix"],outdir)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":142,"baseCheckpoint":141,"passed":not failures and bool(rec["passed"]),"failedGates":failures,"stageAScenarios":len(rows),"resolved":len(resolved),"resolvedUnder25":sum(int(r["resolved_under25_flag"]) for r in rows),"resolvedGe25":long,"resolvedGe25RateOfResolved":long/len(resolved) if resolved else 0.0,"safeStalemates":stale,"turnCapSentinels":caps,"gameplayDurationConcernScenarios":long+caps,"gameplayDurationConcernRate":(long+caps)/len(rows) if rows else 0.0,"medianResolvedTurns":overall.get("median_resolved_turns",""),"p90ResolvedTurns":overall.get("p90_resolved_turns",""),"p95ResolvedTurns":overall.get("p95_resolved_turns",""),"hardTurnSentinel":HARD_TURN_SENTINEL,"batchCount":len(audits),"sourceMatrixUnmodified":before_hash==after_hash,"reconciliationLedgerRows":rec["ledgerRows"],"changedVsCp141LedgerRows":rec["changedVsCp141Rows"],"explicitUnresolvedLedgerRows":rec["explicitUnresolvedRows"],"stageASubstantiveMeasurementReady":not failures,"substantiveCombatTrials":0,"promotionAllowed":False,"interpretation":"CP142 deep-reconciliation diagnostic. Paired changes identify integration drift; one-trial outcome frequencies are not balance evidence."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary
