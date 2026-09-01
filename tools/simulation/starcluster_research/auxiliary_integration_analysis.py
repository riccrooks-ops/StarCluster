from __future__ import annotations

import csv
import json
import math
import shutil
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from itertools import combinations_with_replacement
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import FULL_MAP_GEOMETRY, aggregate_full_map_variant, mirror_equivalent, run_trial_full_map
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant, build_space
from .study import canonicalize_relocated_references, load_json

RESULT_SCHEMA = "star-cluster-cp138-auxiliary-integration-result-v0.1"
FAMILY_ORDER = ("Kinetic", "Energy", "GP", "Swarmer")
ROLE_ORDER = (
    "mission-control", "electronic-attack", "counter-ew", "information-control",
    "amm-escort", "energy-screen", "kinetic-screen", "shield-guard", "combat-generalist",
)

ROLE_SPECS = {
    "mission-control": dict(ecm=False, eccm=False, pds=None, hardener=False),
    "electronic-attack": dict(ecm=True, eccm=False, pds=None, hardener=False),
    "counter-ew": dict(ecm=False, eccm=True, pds=None, hardener=False),
    "information-control": dict(ecm=True, eccm=True, pds=None, hardener=False),
    "amm-escort": dict(ecm=False, eccm=True, pds="AMM", hardener=False),
    "energy-screen": dict(ecm=False, eccm=True, pds="Energy", hardener=False),
    "kinetic-screen": dict(ecm=False, eccm=True, pds="Kinetic", hardener=False),
    "shield-guard": dict(ecm=False, eccm=True, pds=None, hardener=True),
    "combat-generalist": dict(ecm=True, eccm=True, pds="AMM", hardener=True),
}


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors=[]
    if doc.get("schemaVersion") != "star-cluster-cp138-aux-reference-full-ship-integration-v0.1": errors.append("schemaVersion")
    if int(doc.get("checkpoint",0)) != 138: errors.append("checkpoint")
    if doc.get("canonicalKernelVersion") != "0.4": errors.append("canonicalKernelVersion")
    if doc.get("damageModel") != "penetration-hardening-v1": errors.append("damageModel")
    if doc.get("mandatoryDefenses") != ["Shield","Armor"]: errors.append("mandatoryDefenses")
    if doc.get("armorProfile") != "mainline": errors.append("armorProfile")
    if bool(doc.get("automaticPromotion")): errors.append("automaticPromotion")
    if doc.get("balanceTargets") is not None: errors.append("balanceTargets")
    if doc.get("reactorTuningEnabled") is not False: errors.append("reactorTuningEnabled")
    if doc.get("powerAuxExecutionEnabled") is not False: errors.append("powerAuxExecutionEnabled")
    if doc.get("masterSeed") != 138001: errors.append("masterSeed")
    expected=doc.get("expected",{})
    for k in ("logicalContexts","generatedVariants","pipelineSmokeTrials","substantiveTrials","catalogComponents","referencePhilosophies"):
        if not isinstance(expected.get(k),int): errors.append(f"expected.{k}")
    return errors


def _families_for_tl(tl:int)->tuple[str,...]:
    return FAMILY_ORDER[:3] if tl==1 else FAMILY_ORDER


def _weapon_family(label:str)->str:
    return "Missile" if label in ("GP","Swarmer") else label


def _roles_for_tl(tl:int)->tuple[str,...]:
    return tuple(r for r in ROLE_ORDER if not (r=="shield-guard" and tl<3))


def make_build(matrix:CandidateMatrix, tl:int, family_label:str, role:str)->EcologyBuild:
    if role not in ROLE_SPECS: raise ValueError(role)
    if role=="shield-guard" and tl<3: raise ValueError("Shield Guard requires TL3")
    spec=dict(ROLE_SPECS[role])
    if role=="combat-generalist" and tl<3: spec["hardener"]=False
    wf=_weapon_family(family_label)
    combat=build_space(matrix,tl,wf,1,1,True,spec["ecm"],spec["eccm"],spec["pds"],spec["hardener"])
    capacity=matrix.capacity(tl)
    if combat>capacity: raise ValueError(f"illegal build TL{tl} {family_label} {role}: {combat}>{capacity}")
    return EcologyBuild(
        id=f"tl{tl}-{family_label.lower()}-{role}", tl=tl, archetype=role, weapon_family=wf,
        main_count=1, reactor_count=1, shield=True, ecm=spec["ecm"], eccm=spec["eccm"],
        pds_family=spec["pds"], shield_hardener=spec["hardener"], capacity=capacity,
        combat_space=combat, mission_aux_space=capacity-combat,
        missile_payload=("Swarmer" if family_label=="Swarmer" else "GP"), armor_profile="mainline",
    )


@dataclass(frozen=True,slots=True)
class AuxContext:
    id:str
    layer:str
    tl:int
    family_a:str
    family_b:str
    role_a:str
    role_b:str
    build_a:EcologyBuild
    build_b:EcologyBuild


def _ctx(layer:str, tl:int, fa:str, fb:str, ra:str, rb:str, matrix:CandidateMatrix)->AuxContext:
    return AuxContext(
        id=f"{layer}-tl{tl}-{fa.lower()}-{ra}__vs__{fb.lower()}-{rb}", layer=layer, tl=tl,
        family_a=fa, family_b=fb, role_a=ra, role_b=rb,
        build_a=make_build(matrix,tl,fa,ra), build_b=make_build(matrix,tl,fb,rb),
    )


def build_contexts(matrix:CandidateMatrix)->list[AuxContext]:
    out=[]
    # Layer 1: baseline mirrors and every tactical role against the same-family mission-control reference.
    for tl in range(1,10):
        for fam in _families_for_tl(tl):
            out.append(_ctx("role-baseline",tl,fam,fam,"mission-control","mission-control",matrix))
            for role in _roles_for_tl(tl):
                if role!="mission-control": out.append(_ctx("role-marginal",tl,fam,fam,role,"mission-control",matrix))
    # Layer 2: EW counterplay, same family so weapon identity is controlled.
    ew_pairs=(("electronic-attack","counter-ew"),("electronic-attack","information-control"),("information-control","counter-ew"))
    for tl in range(1,10):
        for fam in _families_for_tl(tl):
            for ra,rb in ew_pairs: out.append(_ctx("ew-counterplay",tl,fam,fam,ra,rb,matrix))
    # Layer 3: terminal-defense threat lanes. Defender Main is K/E; attacker is GP/S, control or information-control.
    for tl in range(1,10):
        threats=("GP",) if tl==1 else ("GP","Swarmer")
        for dfam in ("Kinetic","Energy"):
            for drole in ("amm-escort","energy-screen","kinetic-screen"):
                for threat in threats:
                    for arole in ("mission-control","information-control"):
                        out.append(_ctx("pds-threat",tl,dfam,threat,drole,arole,matrix))
    # Layer 4: full combat-generalist family matrix.
    for tl in range(1,10):
        for fa,fb in combinations_with_replacement(_families_for_tl(tl),2):
            out.append(_ctx("generalist-cross-family",tl,fa,fb,"combat-generalist","combat-generalist",matrix))
    # Layer 5: Shield Hardener focus. Hold defender Main to K/E; attack with E/GP/S and attacker control or ECM.
    for tl in range(3,10):
        for dfam in ("Kinetic","Energy"):
            for threat in ("Energy","GP","Swarmer"):
                for arole in ("mission-control","electronic-attack"):
                    out.append(_ctx("hardener-focus",tl,dfam,threat,"shield-guard",arole,matrix))
    ids=[x.id for x in out]
    if len(ids)!=len(set(ids)): raise ValueError("duplicate AUX context IDs")
    return out


def build_variants(contexts:list[AuxContext], max_turns:int)->list[tuple[AuxContext,EcologyVariant]]:
    out=[]
    for c in contexts:
        group=f"cp138-{c.id}"
        for order,suffix in (("SideAFirst","afirst"),("SideBFirst","bfirst")):
            v=EcologyVariant(
                id=f"{c.id}-{suffix}",tl=c.tl,side_a=c.build_a,side_b=c.build_b,movement_order=order,
                geometry=FULL_MAP_GEOMETRY,population="cp138_full_ship_aux",max_turns=max_turns,
                scenario_group=group,physical_id_a=group+":ship-a",physical_id_b=group+":ship-b",
            )
            out.append((c,v))
    return out


def _write_csv(path:Path,rows:list[dict[str,Any]])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def _catalog_checks(repo:Path,doc:dict[str,Any])->dict[str,Any]:
    catalog=load_json(repo/doc["auxiliaryCatalog"]); philosophies=load_json(repo/doc["referencePhilosophies"])
    comps=catalog["components"]
    covered={c for p in philosophies["philosophies"] for c in p["catalogComponents"]}
    shield={k:v for k,v in catalog["cp138ShieldAuxVetting"].items()}
    return {
        "catalogComponents":len(comps),"catalogUnique":len({c["id"] for c in comps})==len(comps),
        "catalogCovered":len(covered),"referencePhilosophies":len(philosophies["philosophies"]),
        "allComponentsHaveReferences":all(bool(c.get("referenceBasis")) for c in comps),
        "allComponentsHaveDisposition":all(bool(c.get("sweepDisposition")) for c in comps),
        "combatExecutedCatalogComponents":sorted(c["id"] for c in comps if c.get("cp138CombatExecution")),
        "integratedStandardAuxSystems":sorted(x["id"] for x in catalog.get("integratedStandardAuxSystems",[])),
        "shieldAuxVetting":shield,
    }


def build_plan(repo:Path,study_path:Path,outdir:Path|None=None)->dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)
    if errs: raise ValueError("CP138 study validation failed: "+", ".join(errs))
    matrix=CandidateMatrix(repo,doc["sourceMatrix"])
    contexts=build_contexts(matrix); variants=build_variants(contexts,int(doc.get("maxTurns",60)))
    cat=_catalog_checks(repo,doc); failed=[]
    expected=doc["expected"]
    checks={"logicalContexts":len(contexts),"generatedVariants":len(variants),"pipelineSmokeTrials":len(variants)*int(doc.get("smokeTrialsPerVariant",1)),"substantiveTrials":len(variants)*int(doc["trialsPerVariant"]),"catalogComponents":cat["catalogComponents"],"referencePhilosophies":cat["referencePhilosophies"]}
    for k,v in checks.items():
        if int(v)!=int(expected[k]): failed.append(f"{k}:{v}!={expected[k]}")
    if not cat["catalogUnique"] or cat["catalogCovered"]!=cat["catalogComponents"]: failed.append("catalog-coverage")
    if not cat["allComponentsHaveReferences"] or not cat["allComponentsHaveDisposition"]: failed.append("catalog-reference-disposition")
    for c in contexts:
        for b in (c.build_a,c.build_b):
            if not b.shield or b.armor_profile!="mainline": failed.append("mandatory-defense")
            if b.used_space!=b.capacity: failed.append("not-exact-fill")
    if any(c.role_a=="shield-guard" and c.tl<3 for c in contexts): failed.append("illegal-hardener-tl")
    layers=defaultdict(int)
    for c in contexts: layers[c.layer]+=1
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":138,"mode":"plan","logicalContexts":len(contexts),"generatedVariants":len(variants),"pipelineSmokeTrials":checks["pipelineSmokeTrials"],"substantiveTrialsPerVariant":int(doc["trialsPerVariant"]),"plannedSubstantiveTrials":checks["substantiveTrials"],"layerContexts":dict(sorted(layers.items())),"exactFill":True,"mandatoryDefenses":["Shield","Armor"],"catalogCoverage":cat,"reactorTuningEnabled":False,"powerAuxExecutionEnabled":False,"balanceTargets":None,"automaticPromotion":False,"failedGates":failed}
    if outdir:
        outdir.mkdir(parents=True,exist_ok=True)
        _write_csv(outdir/"logical_contexts.csv",[{"context_id":c.id,"layer":c.layer,"tl":c.tl,"family_a":c.family_a,"family_b":c.family_b,"role_a":c.role_a,"role_b":c.role_b,"build_a":c.build_a.id,"build_b":c.build_b.id,"combat_space_a":c.build_a.combat_space,"mission_aux_space_a":c.build_a.mission_aux_space,"capacity_a":c.build_a.capacity,"combat_space_b":c.build_b.combat_space,"mission_aux_space_b":c.build_b.mission_aux_space,"capacity_b":c.build_b.capacity} for c in contexts])
        (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return {"doc":doc,"matrix":matrix,"contexts":contexts,"variants":variants,"summary":summary}


_WORK_MATRIX:CandidateMatrix|None=None

def _init_worker(repo:str,matrix_relative:str)->None:
    global _WORK_MATRIX; _WORK_MATRIX=CandidateMatrix(Path(repo),matrix_relative)

def _run_chunk(args:tuple[int,list[tuple[AuxContext,EcologyVariant]],int,int])->tuple[int,list[dict[str,Any]]]:
    idx,items,seed,trials=args; assert _WORK_MATRIX is not None
    rows=[]
    for c,v in items:
        rs=[run_trial_full_map(_WORK_MATRIX,v,seed,i) for i in range(trials)]
        row=aggregate_full_map_variant(v,rs)
        row.update({"context_id":c.id,"layer":c.layer,"family_a":c.family_a,"family_b":c.family_b,"role_a":c.role_a,"role_b":c.role_b,"combat_space_a":c.build_a.combat_space,"mission_aux_space_a":c.build_a.mission_aux_space,"combat_space_b":c.build_b.combat_space,"mission_aux_space_b":c.build_b.mission_aux_space})
        rows.append(row)
    rows.sort(key=lambda r:str(r["variant_id"])); return idx,rows

def _chunks(items:list[Any],count:int)->list[list[Any]]:
    count=max(1,min(count,len(items))); size=math.ceil(len(items)/count); return [items[i:i+size] for i in range(0,len(items),size)]

def execute(repo:Path,doc:dict[str,Any],variants:list[tuple[AuxContext,EcologyVariant]],out_csv:Path,trials:int,jobs:int)->float:
    jobs=max(1,min(jobs,len(variants))); started=time.perf_counter(); chunks=_chunks(variants,min(len(variants),max(jobs,jobs*8))); temp=out_csv.parent/".variant_chunks"; shutil.rmtree(temp,ignore_errors=True); temp.mkdir(parents=True)
    try:
        if jobs==1:
            _init_worker(str(repo),doc["sourceMatrix"])
            for idx,chunk in enumerate(chunks):
                _,rows=_run_chunk((idx,chunk,int(doc["masterSeed"]),trials)); _write_csv(temp/f"chunk-{idx:05d}.csv",rows)
        else:
            ctx=get_context("spawn")
            with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_init_worker,initargs=(str(repo),doc["sourceMatrix"])) as ex:
                futs=[ex.submit(_run_chunk,(idx,chunk,int(doc["masterSeed"]),trials)) for idx,chunk in enumerate(chunks)]
                for fut in as_completed(futs):
                    idx,rows=fut.result(); _write_csv(temp/f"chunk-{idx:05d}.csv",rows)
        files=sorted(temp.glob("chunk-*.csv"))
        with out_csv.open("wb") as out:
            for i,fp in enumerate(files):
                data=fp.read_bytes()
                if i==0: out.write(data)
                else:
                    nl=data.find(b"\n"); out.write(data[nl+1:] if nl>=0 else data)
    finally: shutil.rmtree(temp,ignore_errors=True)
    return time.perf_counter()-started

def _read_rows(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
def _f(r:dict[str,Any],k:str)->float: return float(r.get(k,0) or 0)

def _aggregate_contexts(rows:list[dict[str,str]])->list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows: groups[r["context_id"]].append(r)
    telemetry=("power_available_total","power_spent_total","power_sensor","power_ecm","power_eccm","power_pds","power_weapons","power_shield_recharge","power_shield_hardener","power_shortfall_events","weapon_power_shortfalls","pds_power_shortfalls","acquisition_power_shortfalls","ecm_active_turns","eccm_active_turns","ecm_downgrade_events","eccm_restore_events","firm_track_turns","approximate_track_turns","no_track_turns","direct_shots","direct_hits","missile_launches","missile_hits","pds_attempts","pds_intercepts","shield_armor_prevented","shield_absorbed","shield_collapse_events","shield_reconstitutions","armor_integrity_damage","armor_regen_restored","armor_regen_reserve_spent","armor_regen_denied_exhausted","hull_damage","damage_control_hull_restored")
    out=[]
    for cid,g in sorted(groups.items()):
        first=g[0]; row={k:first[k] for k in ("context_id","layer","tl","family_a","family_b","role_a","role_b")}
        row.update({"variants":len(g),"trials":sum(int(x["trials"]) for x in g),"side_a_win_rate":statistics.fmean(_f(x,"win_rate_a") for x in g),"side_b_win_rate":statistics.fmean(_f(x,"win_rate_b") for x in g),"draw_rate":statistics.fmean(_f(x,"draw_rate") for x in g),"unresolved_rate":statistics.fmean(_f(x,"unresolved_rate") for x in g),"mean_turns":statistics.fmean(_f(x,"mean_turns") for x in g),"mean_final_hull_a":statistics.fmean(_f(x,"mean_final_hull_a") for x in g),"mean_final_hull_b":statistics.fmean(_f(x,"mean_final_hull_b") for x in g),"combat_space_a":int(float(first["combat_space_a"])),"mission_aux_space_a":int(float(first["mission_aux_space_a"])),"combat_space_b":int(float(first["combat_space_b"])),"mission_aux_space_b":int(float(first["mission_aux_space_b"]))})
        for side in ("a","b"):
            for m in telemetry: row[f"mean_{side}_{m}"]=statistics.fmean(_f(x,f"mean_{side}_{m}") for x in g)
        out.append(row)
    return out

def _summary_by(contexts:list[dict[str,Any]],keys:tuple[str,...])->list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in contexts: groups[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,g in sorted(groups.items(),key=lambda x:tuple(str(v) for v in x[0])):
        row={k:v for k,v in zip(keys,key)}
        row.update({"contexts":len(g),"mean_unresolved_rate":statistics.fmean(float(x["unresolved_rate"]) for x in g),"mean_turns":statistics.fmean(float(x["mean_turns"]) for x in g),"mean_tp_utilization_a":statistics.fmean((_f(x,"mean_a_power_spent_total")/_f(x,"mean_a_power_available_total") if _f(x,"mean_a_power_available_total") else 0) for x in g),"mean_tp_utilization_b":statistics.fmean((_f(x,"mean_b_power_spent_total")/_f(x,"mean_b_power_available_total") if _f(x,"mean_b_power_available_total") else 0) for x in g),"mean_ecm_downgrades":statistics.fmean((_f(x,"mean_a_ecm_downgrade_events")+_f(x,"mean_b_ecm_downgrade_events"))/2 for x in g),"mean_eccm_restores":statistics.fmean((_f(x,"mean_a_eccm_restore_events")+_f(x,"mean_b_eccm_restore_events"))/2 for x in g),"mean_pds_intercepts":statistics.fmean((_f(x,"mean_a_pds_intercepts")+_f(x,"mean_b_pds_intercepts"))/2 for x in g),"mean_shield_armor_prevented":statistics.fmean((_f(x,"mean_a_shield_armor_prevented")+_f(x,"mean_b_shield_armor_prevented"))/2 for x in g)})
        out.append(row)
    return out

def _diagnostic_flags(contexts:list[dict[str,Any]])->list[dict[str,Any]]:
    flags=[]
    for r in contexts:
        if float(r["unresolved_rate"])>=0.95: flags.append({"severity":"review","context_id":r["context_id"],"flag":"very_high_unresolved","value":r["unresolved_rate"]})
        if float(r["mean_turns"])>=50: flags.append({"severity":"review","context_id":r["context_id"],"flag":"very_long_combat","value":r["mean_turns"]})
        # Mechanics gates only require systems intended by the role to actually activate in at least a relevant opportunity-rich layer.
        for side in ("a","b"):
            role=r[f"role_{side}"]
            if role in ("electronic-attack","information-control","combat-generalist") and r["layer"]=="ew-counterplay" and _f(r,f"mean_{side}_ecm_active_turns")<=0: flags.append({"severity":"mechanics","context_id":r["context_id"],"flag":f"{side}_ecm_never_active","value":0})
            if role in ("counter-ew","information-control") and r["layer"]=="ew-counterplay":
                other="b" if side=="a" else "a"
                if r[f"role_{other}"] in ("electronic-attack","information-control") and _f(r,f"mean_{side}_eccm_active_turns")<=0: flags.append({"severity":"mechanics","context_id":r["context_id"],"flag":f"{side}_eccm_never_active","value":0})
            if role in ("amm-escort","energy-screen","kinetic-screen") and r["layer"]=="pds-threat" and _f(r,f"mean_{side}_pds_attempts")<=0: flags.append({"severity":"mechanics","context_id":r["context_id"],"flag":f"{side}_pds_never_attempted","value":0})
            if role=="shield-guard" and r["layer"]=="hardener-focus" and _f(r,f"mean_{side}_power_shield_hardener")<=0: flags.append({"severity":"mechanics","context_id":r["context_id"],"flag":f"{side}_hardener_never_powered","value":0})
    return flags

def run_symmetry(repo:Path,study_path:Path,outdir:Path)->dict[str,Any]:
    plan=build_plan(repo,study_path,None); doc=plan["doc"]; matrix=plan["matrix"]; contexts=plan["contexts"]
    selected=[]
    # 10 contexts x 5 trials = 50 comparisons, spanning role layers and TLs.
    for tl,layer in ((1,"role-marginal"),(2,"pds-threat"),(3,"hardener-focus"),(4,"ew-counterplay"),(5,"generalist-cross-family"),(6,"role-marginal"),(7,"pds-threat"),(8,"hardener-focus"),(9,"ew-counterplay"),(9,"generalist-cross-family")):
        selected.append(next(c for c in contexts if c.tl==tl and c.layer==layer))
    mismatches=[]; comparisons=0
    for ci,c in enumerate(selected):
        for trial in range(5):
            scenario=f"cp138-sym-{ci}-{c.id}"
            v1=EcologyVariant(scenario+"-a",c.tl,c.build_a,c.build_b,"SideAFirst",geometry=FULL_MAP_GEOMETRY,population="cp138_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship1",physical_id_b=scenario+":ship2")
            v2=EcologyVariant(scenario+"-b",c.tl,c.build_b,c.build_a,"SideBFirst",geometry=FULL_MAP_GEOMETRY,population="cp138_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship2",physical_id_b=scenario+":ship1")
            r1=run_trial_full_map(matrix,v1,int(doc["masterSeed"]),trial); r2=run_trial_full_map(matrix,v2,int(doc["masterSeed"]),trial); comparisons+=1
            if not mirror_equivalent(r1,r2): mismatches.append({"context":c.id,"trial":trial})
    failed=[]
    if comparisons!=50: failed.append(f"comparisons:{comparisons}!=50")
    if mismatches: failed.append(f"mismatches:{len(mismatches)}")
    outdir.mkdir(parents=True,exist_ok=True); _write_csv(outdir/"symmetry_mismatches.csv",mismatches)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":138,"mode":"symmetry","comparisons":comparisons,"combatExecutions":comparisons*2,"mismatches":len(mismatches),"failedGates":failed}; (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); return summary

def run_auxiliary_integration(repo:Path,study_path:Path,outdir:Path,mode:str,trials:int|None=None,jobs:int=24)->dict[str,Any]:
    if mode=="plan": return build_plan(repo,study_path,outdir)["summary"]
    if mode=="symmetry": return run_symmetry(repo,study_path,outdir)
    plan=build_plan(repo,study_path,outdir/"plan"); doc=plan["doc"]; variants=plan["variants"]
    n=1 if mode=="smoke" else int(trials or doc["trialsPerVariant"]); outdir.mkdir(parents=True,exist_ok=True)
    elapsed=execute(repo,doc,variants,outdir/"variants.csv",n,jobs); rows=_read_rows(outdir/"variants.csv"); errors=sum(int(r["errors"]) for r in rows)
    contexts=_aggregate_contexts(rows); _write_csv(outdir/"contexts.csv",contexts)
    role=_summary_by(contexts,("tl","role_a")); _write_csv(outdir/"role_summary.csv",role)
    ew=_summary_by([r for r in contexts if r["layer"]=="ew-counterplay"],("tl","role_a","role_b")); _write_csv(outdir/"ew_counterplay_summary.csv",ew)
    pds=_summary_by([r for r in contexts if r["layer"]=="pds-threat"],("tl","role_a","family_b","role_b")); _write_csv(outdir/"pds_threat_summary.csv",pds)
    hard=_summary_by([r for r in contexts if r["layer"]=="hardener-focus"],("tl","family_a","family_b","role_b")); _write_csv(outdir/"hardener_summary.csv",hard)
    gen=_summary_by([r for r in contexts if r["layer"]=="generalist-cross-family"],("tl","family_a","family_b")); _write_csv(outdir/"generalist_cross_family_summary.csv",gen)
    flags=_diagnostic_flags(contexts); _write_csv(outdir/"diagnostic_flags.csv",flags)
    failed=[]; expected=int(doc["expected"]["generatedVariants"])
    if len(rows)!=expected: failed.append(f"variants:{len(rows)}!={expected}")
    if errors: failed.append(f"trial-errors:{errors}")
    mechanics=[f for f in flags if f["severity"]=="mechanics"]
    if mechanics: failed.append(f"aux-activation:{len(mechanics)}")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":138,"mode":mode,"variants":len(rows),"logicalContexts":len(contexts),"trialsPerVariant":n,"totalTrials":len(rows)*n,"trialErrors":errors,"elapsedSeconds":elapsed,"diagnosticReviewFlags":sum(1 for f in flags if f["severity"]=="review"),"mechanicsFlags":len(mechanics),"roleSummaryRows":len(role),"ewCounterplayRows":len(ew),"pdsThreatRows":len(pds),"hardenerRows":len(hard),"generalistRows":len(gen),"catalogComponents":plan["summary"]["catalogCoverage"]["catalogComponents"],"catalogCovered":plan["summary"]["catalogCoverage"]["catalogCovered"],"exactFill":True,"reactorTuningEnabled":False,"powerAuxExecutionEnabled":False,"automaticPromotion":False,"balanceTargets":None,"failedGates":failed}
    (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); return summary
