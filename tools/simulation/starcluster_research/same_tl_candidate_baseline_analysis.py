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

RESULT_SCHEMA = "star-cluster-same-tl-candidate-baseline-result-v0.2"
FAMILY_ORDER = ("Kinetic", "Energy", "GP", "Swarmer")


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors=[]
    cp=int(doc.get("checkpoint",0))
    expected_schema={134:"star-cluster-cp134-same-tl-candidate-baseline-v0.1",135:"star-cluster-cp135-recharge-damcon-rebaseline-v0.1",136:"star-cluster-cp136-armor-rebaseline-v0.1",137:"star-cluster-cp137-finite-armor-regeneration-v0.1"}.get(cp)
    expected_kernel={134:"0.2",135:"0.3",136:"0.3",137:"0.4"}.get(cp)
    if expected_schema is None or doc.get("schemaVersion") != expected_schema: errors.append("schemaVersion")
    if cp not in (134,135,136,137): errors.append("checkpoint")
    if expected_kernel is None or doc.get("canonicalKernelVersion") != expected_kernel: errors.append("canonicalKernelVersion")
    if doc.get("damageModel") != "penetration-hardening-v1": errors.append("damageModel")
    if doc.get("mandatoryDefenses") != ["Shield","Armor"]: errors.append("mandatoryDefenses")
    if doc.get("tl6ArmorProfiles") != ["mainline","A_b1"]: errors.append("tl6ArmorProfiles")
    if doc.get("pdsContexts",{}).get("missileBearing") != ["off","AMM"]: errors.append("pdsContexts.missileBearing")
    if doc.get("balanceTargets") is not None: errors.append("balanceTargets")
    if bool(doc.get("automaticPromotion")): errors.append("automaticPromotion")
    trials=doc.get("trialsPerVariant")
    if not isinstance(trials,int) or isinstance(trials,bool) or trials < 1: errors.append("trialsPerVariant")
    return errors


def _is_missile_family(fam: str) -> bool:
    return fam in ("GP","Swarmer")


def _weapon_family(fam: str) -> str:
    return "Missile" if _is_missile_family(fam) else fam


def _payload(fam: str) -> str:
    return "Swarmer" if fam == "Swarmer" else "GP"


def _family_tag(fam: str) -> str:
    return {"Kinetic":"k","Energy":"e","GP":"m","Swarmer":"s"}[fam]


def _build(matrix: CandidateMatrix, tl: int, fam: str, armor: str, pds: str) -> EcologyBuild:
    wf=_weapon_family(fam)
    pds_family=None if pds=="off" else pds
    cap=matrix.capacity(tl)
    combat=build_space(matrix,tl,wf,1,1,True,False,False,pds_family,False)
    if combat > cap:
        raise ValueError(f"reference build exceeds Space: TL{tl} {fam} {armor} {pds}: {combat}>{cap}")
    return EcologyBuild(
        id=f"tl{tl}-{_family_tag(fam)}-{armor}-{pds}", tl=tl, archetype="same-tl-reference",
        weapon_family=wf, main_count=1, reactor_count=1, shield=True, ecm=False, eccm=False,
        pds_family=pds_family, shield_hardener=False, capacity=cap, combat_space=combat,
        mission_aux_space=cap-combat, missile_payload=_payload(fam), armor_profile=armor,
    )


@dataclass(frozen=True, slots=True)
class LogicalContext:
    id: str
    tl: int
    family_a: str
    family_b: str
    armor_a: str
    armor_b: str
    pds: str
    build_a: EcologyBuild
    build_b: EcologyBuild


def build_contexts(matrix: CandidateMatrix) -> list[LogicalContext]:
    out=[]
    for tl in range(1,10):
        fams=("Kinetic","Energy","GP") if tl==1 else FAMILY_ORDER
        armor_pairs=[("mainline","mainline")]
        if tl==6:
            armor_pairs=[("mainline","mainline"),("mainline","A_b1"),("A_b1","mainline"),("A_b1","A_b1")]
        for fa,fb in combinations_with_replacement(fams,2):
            pds_contexts=("off","AMM") if (_is_missile_family(fa) or _is_missile_family(fb)) else ("off",)
            for aa,ab in armor_pairs:
                for pds in pds_contexts:
                    ident=f"tl{tl}-{_family_tag(fa)}v{_family_tag(fb)}-{aa}v{ab}-{pds}"
                    out.append(LogicalContext(ident,tl,fa,fb,aa,ab,pds,_build(matrix,tl,fa,aa,pds),_build(matrix,tl,fb,ab,pds)))
    return out


def build_variants(contexts: list[LogicalContext], max_turns: int) -> list[tuple[LogicalContext,EcologyVariant]]:
    out=[]
    for c in contexts:
        physical_a=c.id+":shipA"; physical_b=c.id+":shipB"
        for order in ("SideAFirst","SideBFirst"):
            vid=f"{c.id}-{order.lower()}"
            out.append((c,EcologyVariant(
                vid,c.tl,c.build_a,c.build_b,order,geometry=FULL_MAP_GEOMETRY,
                population="same_tl_reference",max_turns=max_turns,scenario_group=c.id,
                perturbation="candidate-baseline",physical_id_a=physical_a,physical_id_b=physical_b,
            )))
    return out


def _write_csv(path: Path, rows: list[dict[str,Any]], fieldnames: list[str] | None=None) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:
        path.write_text("",encoding="utf-8"); return
    fields=fieldnames or list(rows[0].keys())
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def build_plan(repo: Path, study_path: Path, outdir: Path | None=None) -> dict[str,Any]:
    doc=load_json(study_path); errs=validate_study(doc)
    if errs: raise ValueError(f"CP{int(doc.get('checkpoint',0))} study validation failed: "+", ".join(errs))
    matrix=CandidateMatrix(repo,doc["sourceMatrix"])
    contexts=build_contexts(matrix); variants=build_variants(contexts,int(doc.get("maxTurns",60)))
    expected=doc["expected"]; failed=[]
    checks={
        "logicalContexts":len(contexts),"generatedVariants":len(variants),
        "pipelineSmokeTrials":len(variants)*int(doc.get("smokeTrialsPerVariant",1)),
        "substantiveTrials":len(variants)*int(doc["trialsPerVariant"]),
        "tl6Variants":sum(1 for c,v in variants if c.tl==6),
    }
    for key,val in checks.items():
        if int(val)!=int(expected[key]): failed.append(f"{key}:{val}!={expected[key]}")
    if any(not c.build_a.shield or not c.build_b.shield for c in contexts): failed.append("mandatory-shield")
    if any(c.build_a.armor_profile not in ("mainline","A_b1") or c.build_b.armor_profile not in ("mainline","A_b1") for c in contexts): failed.append("mandatory-armor")
    if set((c.armor_a,c.armor_b) for c in contexts if c.tl==6) != {("mainline","mainline"),("mainline","A_b1"),("A_b1","mainline"),("A_b1","A_b1")}:
        failed.append("tl6-armor-coverage")
    for c in contexts:
        missile=_is_missile_family(c.family_a) or _is_missile_family(c.family_b)
        if missile and c.pds not in ("off","AMM"): failed.append("pds-context")
        if not missile and c.pds != "off": failed.append("direct-only-pds")
    summary={
        "schemaVersion":RESULT_SCHEMA,"checkpoint":int(doc["checkpoint"]),"mode":"plan","logicalContexts":len(contexts),
        "generatedVariants":len(variants),"pipelineSmokeTrials":checks["pipelineSmokeTrials"],
        "substantiveTrialsPerVariant":int(doc["trialsPerVariant"]),"plannedSubstantiveTrials":checks["substantiveTrials"],
        "tl6Variants":checks["tl6Variants"],"mandatoryDefenses":["Shield","Armor"],
        "pdsControl":"AMM paired off/on only when a Missile/Swarmer family is present",
        "balanceTargets":None,"automaticPromotion":False,"mixedTlShipsExecuted":False,"failedGates":failed,
    }
    if outdir is not None:
        outdir.mkdir(parents=True,exist_ok=True)
        _write_csv(outdir/"logical_contexts.csv",[{
            "context_id":c.id,"tl":c.tl,"family_a":c.family_a,"family_b":c.family_b,
            "armor_a":c.armor_a,"armor_b":c.armor_b,"pds":c.pds,
            "build_a":c.build_a.id,"build_b":c.build_b.id,"space_a":c.build_a.combat_space,"space_b":c.build_b.combat_space,
            "free_space_a":c.build_a.mission_aux_space,"free_space_b":c.build_b.mission_aux_space,
        } for c in contexts])
        (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return {"doc":doc,"matrix":matrix,"contexts":contexts,"variants":variants,"summary":summary}


_WORK_MATRIX: CandidateMatrix | None=None

def _init_worker(repo: str, matrix_relative: str) -> None:
    global _WORK_MATRIX
    _WORK_MATRIX=CandidateMatrix(Path(repo),matrix_relative)


def _run_chunk(args: tuple[int,list[tuple[LogicalContext,EcologyVariant]],int,int]) -> tuple[int,list[dict[str,Any]]]:
    idx,items,seed,trials=args
    assert _WORK_MATRIX is not None
    rows=[]
    for context,variant in items:
        results=[run_trial_full_map(_WORK_MATRIX,variant,seed,i) for i in range(trials)]
        row=aggregate_full_map_variant(variant,results)
        row.update({
            "context_id":context.id,"family_a":context.family_a,"family_b":context.family_b,
            "armor_profile_a":context.armor_a,"armor_profile_b":context.armor_b,"pds_context":context.pds,
            "contains_missile":_is_missile_family(context.family_a) or _is_missile_family(context.family_b),
            "space_a":context.build_a.combat_space,"space_b":context.build_b.combat_space,
            "free_space_a":context.build_a.mission_aux_space,"free_space_b":context.build_b.mission_aux_space,
        })
        rows.append(row)
    rows.sort(key=lambda r:str(r["variant_id"]))
    return idx,rows


def _chunks(items:list[Any], count:int)->list[list[Any]]:
    count=max(1,min(count,len(items))); size=math.ceil(len(items)/count)
    return [items[i:i+size] for i in range(0,len(items),size)]


def execute(repo:Path,doc:dict[str,Any],variants:list[tuple[LogicalContext,EcologyVariant]],out_csv:Path,trials:int,jobs:int)->float:
    jobs=max(1,min(int(jobs),len(variants))); started=time.perf_counter()
    chunks=_chunks(variants,min(len(variants),max(jobs,jobs*8)))
    temp=out_csv.parent/".variant_chunks"
    shutil.rmtree(temp,ignore_errors=True); temp.mkdir(parents=True)
    try:
        def write_chunk(idx,rows):
            if rows:_write_csv(temp/f"chunk-{idx:05d}.csv",rows)
        if jobs==1:
            _init_worker(str(repo),doc["sourceMatrix"])
            for idx,chunk in enumerate(chunks):
                _,rows=_run_chunk((idx,chunk,int(doc["masterSeed"]),trials)); write_chunk(idx,rows)
        else:
            ctx=get_context("spawn")
            with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_init_worker,initargs=(str(repo),doc["sourceMatrix"])) as ex:
                futs=[ex.submit(_run_chunk,(idx,chunk,int(doc["masterSeed"]),trials)) for idx,chunk in enumerate(chunks)]
                for fut in as_completed(futs): idx,rows=fut.result(); write_chunk(idx,rows)
        files=sorted(temp.glob("chunk-*.csv"))
        with out_csv.open("wb") as out:
            for i,fp in enumerate(files):
                data=fp.read_bytes()
                if i==0: out.write(data)
                else:
                    nl=data.find(b"\n"); out.write(data[nl+1:] if nl>=0 else data)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    return time.perf_counter()-started


def _read_rows(path:Path)->list[dict[str,str]]:
    with path.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))


def _f(row:dict[str,str],key:str)->float:return float(row.get(key,0) or 0)


def _aggregate_contexts(rows:list[dict[str,str]])->list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:groups[r["context_id"]].append(r)
    out=[]
    telem=[
        "direct_shots","direct_hits","direct_firm_shots","direct_approximate_shots","direct_standard_range_shots","direct_extended_range_shots","direct_stacked_penalty_shots",
        "energy_low_shots","energy_standard_shots","energy_overload_shots","energy_overload_strain_added","power_weapons","power_shield_recharge","power_pds","armor_regen_tp_spent","armor_regen_restored","armor_regen_reserve_initial","armor_regen_reserve_spent","armor_regen_reserve_exhaustions","armor_regen_denied_exhausted",
        "shield_base_restored","shield_tactical_restored","shield_reconstitutions","shield_collapse_events","armor_collapse_events","shield_penetration_bypassed","armor_penetration_bypassed",
        "armor_integrity_damage","hull_damage","missile_launches","missile_terminal_arrivals","missile_guidance_attempts","missile_hits","pds_attempts","pds_intercepts",
        "first_shield_damage_turn","first_shield_collapse_turn","first_armor_damage_turn","first_armor_collapse_turn","first_hull_damage_turn",
        "damage_control_attempts","damage_control_successes","damage_control_kits_consumed","damage_control_tp_spent","damage_control_hull_queued","damage_control_hull_restored",
    ]
    for cid,g in sorted(groups.items()):
        first=g[0]
        row={k:first[k] for k in ("context_id","tl","family_a","family_b","armor_profile_a","armor_profile_b","pds_context","contains_missile")}
        row.update({
            "variants":len(g),"trials":sum(int(x["trials"]) for x in g),
            "side_a_win_rate":statistics.fmean(_f(x,"win_rate_a") for x in g),
            "side_b_win_rate":statistics.fmean(_f(x,"win_rate_b") for x in g),
            "draw_rate":statistics.fmean(_f(x,"draw_rate") for x in g),
            "unresolved_rate":statistics.fmean(_f(x,"unresolved_rate") for x in g),
            "mean_turns":statistics.fmean(_f(x,"mean_turns") for x in g),
            "mean_min_range":statistics.fmean(_f(x,"mean_min_range") for x in g),
            "mean_final_hull_a":statistics.fmean(_f(x,"mean_final_hull_a") for x in g),
            "mean_final_hull_b":statistics.fmean(_f(x,"mean_final_hull_b") for x in g),
            "mean_final_armor_a":statistics.fmean(_f(x,"mean_final_armor_a") for x in g),
            "mean_final_armor_b":statistics.fmean(_f(x,"mean_final_armor_b") for x in g),
            "mean_final_shield_a":statistics.fmean(_f(x,"mean_final_shield_a") for x in g),
            "mean_final_shield_b":statistics.fmean(_f(x,"mean_final_shield_b") for x in g),
        })
        for side in ("a","b"):
            for metric in telem:
                row[f"mean_{side}_{metric}"]=statistics.fmean(_f(x,f"mean_{side}_{metric}") for x in g)
        out.append(row)
    return out


def _pds_effects(context_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    lookup={
        (int(r["tl"]),r["family_a"],r["family_b"],r["armor_profile_a"],r["armor_profile_b"],r["pds_context"]):r
        for r in context_rows
    }
    out=[]
    for key,off in sorted(lookup.items()):
        tl,fa,fb,aa,ab,pds=key
        if pds!="off" or not (_is_missile_family(fa) or _is_missile_family(fb)):continue
        on=lookup.get((tl,fa,fb,aa,ab,"AMM"))
        if not on:continue
        out.append({
            "tl":tl,"family_a":fa,"family_b":fb,"armor_a":aa,"armor_b":ab,
            "off_mean_turns":off["mean_turns"],"on_mean_turns":on["mean_turns"],"delta_turns":on["mean_turns"]-off["mean_turns"],
            "off_unresolved_rate":off["unresolved_rate"],"on_unresolved_rate":on["unresolved_rate"],"delta_unresolved_rate":on["unresolved_rate"]-off["unresolved_rate"],
            "off_a_missile_hits":off["mean_a_missile_hits"],"on_a_missile_hits":on["mean_a_missile_hits"],
            "off_b_missile_hits":off["mean_b_missile_hits"],"on_b_missile_hits":on["mean_b_missile_hits"],
            "on_a_pds_intercepts":on["mean_a_pds_intercepts"],"on_b_pds_intercepts":on["mean_b_pds_intercepts"],
            "on_a_pds_power":on["mean_a_power_pds"],"on_b_pds_power":on["mean_b_power_pds"],
        })
    return out


def _tl6_armor_effects(context_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    return [r for r in context_rows if int(r["tl"])==6]


def _diagnostic_flags(context_rows:list[dict[str,Any]])->list[dict[str,Any]]:
    flags=[]
    for r in context_rows:
        fams=(r["family_a"],r["family_b"])
        if r["unresolved_rate"] >= 0.95:
            flags.append({"severity":"review","context_id":r["context_id"],"flag":"very_high_unresolved","value":r["unresolved_rate"]})
        if r["mean_turns"] >= 50:
            flags.append({"severity":"review","context_id":r["context_id"],"flag":"very_long_combat","value":r["mean_turns"]})
        for side,fam in zip(("a","b"),fams):
            activity=r[f"mean_{side}_missile_launches"] if _is_missile_family(fam) else r[f"mean_{side}_direct_shots"]
            if activity <= 0:
                flags.append({"severity":"mechanics","context_id":r["context_id"],"flag":f"{side}_no_offensive_activity","value":activity})
    return flags


def run_symmetry(repo:Path,study_path:Path,outdir:Path)->dict[str,Any]:
    plan=build_plan(repo,study_path,None); doc=plan["doc"]; matrix=plan["matrix"]
    contexts=plan["contexts"]
    # One representative context per TL plus a TL6 cross-armor/missile-PDS case.
    selected=[]
    for tl in range(1,10):
        cand=[c for c in contexts if c.tl==tl and c.family_a=="Kinetic" and c.family_b==("GP" if tl==1 else "Swarmer") and c.pds==("AMM" if tl>=2 else "off")]
        selected.append(cand[0] if cand else next(c for c in contexts if c.tl==tl))
    selected.append(next(c for c in contexts if c.tl==6 and c.armor_a=="mainline" and c.armor_b=="A_b1" and c.family_a=="Energy" and c.family_b=="GP" and c.pds=="AMM"))
    mismatches=[]; comparisons=0; trials=5
    for ci,c in enumerate(selected):
        for trial in range(trials):
            scenario=f"cp{int(doc["checkpoint"])}-sym-{ci}-{c.id}"
            v1=EcologyVariant(scenario+"-a",c.tl,c.build_a,c.build_b,"SideAFirst",geometry=FULL_MAP_GEOMETRY,population="same_tl_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship1",physical_id_b=scenario+":ship2")
            v2=EcologyVariant(scenario+"-b",c.tl,c.build_b,c.build_a,"SideBFirst",geometry=FULL_MAP_GEOMETRY,population="same_tl_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship2",physical_id_b=scenario+":ship1")
            r1=run_trial_full_map(matrix,v1,int(doc["masterSeed"]),trial); r2=run_trial_full_map(matrix,v2,int(doc["masterSeed"]),trial)
            comparisons+=1
            if not mirror_equivalent(r1,r2):mismatches.append({"context":c.id,"trial":trial})
    failed=[]
    if comparisons!=50:failed.append(f"comparisons:{comparisons}!=50")
    if mismatches:failed.append(f"mismatches:{len(mismatches)}")
    outdir.mkdir(parents=True,exist_ok=True); _write_csv(outdir/"symmetry_mismatches.csv",mismatches)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":int(doc["checkpoint"]),"mode":"symmetry","comparisons":comparisons,"combatExecutions":comparisons*2,"mismatches":len(mismatches),"failedGates":failed}
    (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def run_same_tl_candidate_baseline(repo:Path,study_path:Path,outdir:Path,mode:str,trials:int|None=None,jobs:int=24)->dict[str,Any]:
    if mode=="plan":return build_plan(repo,study_path,outdir)["summary"]
    if mode=="symmetry":return run_symmetry(repo,study_path,outdir)
    plan=build_plan(repo,study_path,outdir/"plan"); doc=plan["doc"]; variants=plan["variants"]
    n=1 if mode=="smoke" else int(trials or doc["trialsPerVariant"])
    outdir.mkdir(parents=True,exist_ok=True)
    elapsed=execute(repo,doc,variants,outdir/"variants.csv",n,jobs)
    rows=_read_rows(outdir/"variants.csv")
    errors=sum(int(r["errors"]) for r in rows)
    contexts=_aggregate_contexts(rows)
    _write_csv(outdir/"contexts.csv",contexts)
    pds=_pds_effects(contexts); _write_csv(outdir/"pds_effects.csv",pds)
    tl6=_tl6_armor_effects(contexts); _write_csv(outdir/"tl6_armor_contexts.csv",tl6)
    flags=_diagnostic_flags(contexts); _write_csv(outdir/"diagnostic_flags.csv",flags)
    failed=[]
    expected=int(doc["expected"]["generatedVariants"])
    if len(rows)!=expected:failed.append(f"variants:{len(rows)}!={expected}")
    if errors:failed.append(f"trial-errors:{errors}")
    mechanics_flags=[f for f in flags if f["severity"]=="mechanics"]
    if mechanics_flags:failed.append(f"offensive-activity:{len(mechanics_flags)}")
    summary={
        "schemaVersion":RESULT_SCHEMA,"checkpoint":int(doc["checkpoint"]),"mode":mode,"variants":len(rows),"logicalContexts":len(contexts),
        "trialsPerVariant":n,"totalTrials":len(rows)*n,"trialErrors":errors,"elapsedSeconds":elapsed,
        "diagnosticReviewFlags":sum(1 for f in flags if f["severity"]=="review"),"mechanicsFlags":len(mechanics_flags),
        "pdsComparisons":len(pds),"tl6ArmorContexts":len(tl6),"armorRegenerationReserveTelemetryPresent":bool(contexts and "mean_a_armor_regen_reserve_spent" in contexts[0]),"automaticPromotion":False,"balanceTargets":None,
        "failedGates":failed,
    }
    (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
