from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant
from .reactor_tp_equilibrium import (
    COMBAT_DOCTRINE, DOCTRINES, PowerLoadout, Request, _allocate, _aux, _core_space,
    _costs, _pf4_aux_registry, _pds_row, _turn_requests, _weapon_row, demand_states,
    enumerate_loadouts,
)
from .research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from .rng import XorShift64, derive_seed
from .study import load_json

SCHEMA = "star-cluster-cp162-main-aux-reactor-joint-calibration-v0.1"
STACK_TIERS = (1, 2, 3, "MAX")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_study(doc: dict[str, Any]) -> list[str]:
    e: list[str] = []
    if doc.get("schemaVersion") != SCHEMA: e.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 162: e.append("checkpoint")
    if int(doc.get("acceptedBaselineCheckpoint", 0)) != 161 or doc.get("pendingFinalizationBaselineId") != "CP160-PF4": e.append("baseline")
    if int(doc.get("mainReactorSpace", 0)) != 6: e.append("mainReactorSpace")
    if doc.get("mainReactorOffsetsFromPf4") != [-1, 0, 1]: e.append("mainOffsets")
    if doc.get("auxiliaryReactorSpaceSweep") != [1,2,3,4] or doc.get("auxiliaryReactorTpSweep") != [1,2,3,4]: e.append("auxSweep")
    sp = doc.get("stackingPolicy", {})
    if sp.get("installationCountCapImposed") is not False or sp.get("screenEveryLegalCountStatic") is not True or sp.get("stochasticAndCombatTiers") != [1,2,3,"MAX"]: e.append("stackingPolicy")
    if doc.get("stochasticDoctrines") != list(DOCTRINES): e.append("doctrines")
    if int(doc.get("stochasticTurnSamplesPerVariant",0)) != 2000 or int(doc.get("combatTrialsPerCell",0)) != 500: e.append("scale")
    p=doc.get("interpretationPolicy",{})
    if any(p.get(k) is not False for k in ("automaticPromotion","productionAuthorityChanged","conceptChanged","tuningAllowed")): e.append("promotionBoundary")
    req=("noTargetWinRate","noUniversalUtilizationTarget","balanceMeansDistinctViableChoices","mainReactorSixSpaceFrozenForThisPass","unrestrictedAuxStackingMustBeExplicitlyScreened","countCapMayBeRecommendedOnlyIfEconomicsFailToBoundStacking","auxiliaryReactorMustNotEconomicallyReplaceFullMainReactor","playerBaseCruiserAndBroadLegalEnvelopeBothRetained")
    if not all(p.get(k) is True for k in req): e.append("interpretationPolicy")
    return e


def main_supply(m: CandidateMatrix, tl: int, offset: int) -> int:
    return max(1, int(m.p("reactor",tl)["operationalTp"]) + int(offset))


def aux_specs(doc: dict[str, Any]) -> list[tuple[int,int]]:
    return [(s,t) for s in doc["auxiliaryReactorSpaceSweep"] for t in doc["auxiliaryReactorTpSweep"]]


def max_stack(l: PowerLoadout, space_each: int) -> int:
    return max(0, l.free_space // int(space_each))


def resolved_tier_count(rows: list[PowerLoadout], space_each: int, tier: int|str) -> int:
    if tier == "MAX":
        return max((max_stack(x,space_each) for x in rows), default=0)
    return int(tier)


def select_carrier(m: CandidateMatrix, rows: list[PowerLoadout], *, tl:int, space_each:int, count:int, weapon:str|None=None) -> PowerLoadout|None:
    candidates=[x for x in rows if x.tl==tl and x.reactor_count==1 and max_stack(x,space_each)>=count and (weapon is None or x.weapon==weapon)]
    if not candidates: return None
    # Worst-case power-demand carrier among ships that can physically take the requested stack.
    return max(candidates,key=lambda x:(demand_states(m,x)["full"],demand_states(m,x)["offense"],demand_states(m,x)["defense"],x.used_space,x.id))


def _base_cruiser_space(m: CandidateMatrix, tl:int, weapon:str="K", reactors:int=1, mains:int=1) -> int:
    return _core_space(m,tl,weapon,mains,reactors,6) + int(m.p("shield",tl)["space"])


def static_analysis(repo:Path, study_path:Path, out:Path) -> dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs: raise ValueError("CP162 study invalid: "+", ".join(errs))
    m=load_research_execution_baseline_pf4(repo); all_rows=enumerate_loadouts(m,reactor_space=6); rows=[x for x in all_rows if x.reactor_count==1]
    specs=aux_specs(doc); states=("core","routine","offense","defense","recovery","full")

    density=[]
    for tl in range(1,10):
        base=int(m.p("reactor",tl)["operationalTp"])
        for s,tp in specs:
            copies=math.ceil(base/tp); space_match=copies*s
            density.append({"tl":tl,"aux_space":s,"aux_tp":tp,"tp_per_space":tp/s,"pf4_main_tp":base,"copies_to_meet_or_exceed_one_main":copies,"space_to_meet_or_exceed_one_main":space_match,"matches_main_with_less_than_6_space":int(space_match<6),"matches_main_with_at_most_6_space":int(space_match<=6),"copies_for_plus2_tp":math.ceil(2/tp),"space_for_plus2_tp":math.ceil(2/tp)*s})
    _write_csv(out/"aux_power_density.csv",density)

    base_rows=[]
    for tl in range(1,10):
        cap=int(m.p("hull",tl)["capacity"])
        one=_base_cruiser_space(m,tl,reactors=1,mains=1); two_r=_base_cruiser_space(m,tl,reactors=2,mains=1); two_m=_base_cruiser_space(m,tl,reactors=1,mains=2)
        for s in doc["auxiliaryReactorSpaceSweep"]:
            base_rows.append({"tl":tl,"capacity":cap,"base_cruiser_space":one,"base_cruiser_free_space":cap-one,"second_main_reactor_space":two_r,"second_main_reactor_fits":int(two_r<=cap),"second_main_weapon_space":two_m,"second_main_weapon_fits":int(two_m<=cap),"aux_space_each":s,"max_aux_copies_on_intact_base_cruiser":max(0,(cap-one)//s)})
    _write_csv(out/"player_base_cruiser_fit.csv",base_rows)

    # Every legal count is screened for every Space/TP point and all three Main Reactor offsets.
    agg: dict[tuple[int,int,int,int,int,int], dict[str,Any]]={}
    for l in rows:
        ds=demand_states(m,l)
        for s,tp in specs:
            mx=max_stack(l,s)
            for n in range(mx+1):
                for off in doc["mainReactorOffsetsFromPf4"]:
                    supply=main_supply(m,l.tl,off)+n*tp
                    key=(l.tl,s,tp,n,off)
                    a=agg.setdefault(key,{"tl":l.tl,"aux_space":s,"aux_tp":tp,"aux_count":n,"main_offset":off,"eligible_architectures":0,"max_carrier_stack_observed":0,**{f"supports_{st}":0 for st in states}})
                    a["eligible_architectures"]+=1;a["max_carrier_stack_observed"]=max(int(a["max_carrier_stack_observed"]),mx)
                    for st in states: a[f"supports_{st}"]+=int(supply>=ds[st])
    stack=[]
    for key,a in sorted(agg.items()):
        n=max(1,int(a["eligible_architectures"])); r=dict(a)
        for st in states:r[f"support_rate_{st}"]=a[f"supports_{st}"]/n
        r["total_aux_space"]=int(a["aux_space"])*int(a["aux_count"]);r["total_aux_tp"]=int(a["aux_tp"])*int(a["aux_count"]);r["effective_supply"]=main_supply(m,int(a["tl"]),int(a["main_offset"]))+r["total_aux_tp"]
        stack.append(r)
    _write_csv(out/"legal_stack_support.csv",stack)

    carriers=[]
    for tl in range(1,10):
        tlrows=[x for x in rows if x.tl==tl]
        for s,tp in specs:
            for tier in STACK_TIERS:
                cnt=resolved_tier_count(tlrows,s,tier)
                if cnt<=0: continue
                l=select_carrier(m,rows,tl=tl,space_each=s,count=cnt)
                if not l: continue
                ds=demand_states(m,l)
                carriers.append({"tl":tl,"aux_space":s,"aux_tp":tp,"tier":tier,"aux_count":cnt,"carrier_id":l.id,"weapon":l.weapon,"used_space_before_aux":l.used_space,"free_space_before_aux":l.free_space,"used_space_after_aux":l.used_space+cnt*s,"demand_full":ds["full"],"demand_offense":ds["offense"],"demand_defense":ds["defense"]})
    _write_csv(out/"stack_carriers.csv",carriers)

    summary={"mode":"static","passed":True,"legalPoweredArchitectures":len(all_rows),"oneMainReactorArchitectures":len(rows),"auxCandidates":len(specs),"densityRows":len(density),"baseCruiserRows":len(base_rows),"legalStackSupportRows":len(stack),"carrierRows":len(carriers),"installationCountCapImposed":False,"automaticPromotion":False,"tuningAllowed":False}
    _write_json(out/"summary.json",summary);return summary


def _stoch_one(repo_s:str, doc:dict[str,Any], l:PowerLoadout, aux_space:int, aux_tp:int, count:int, main_offset:int, doctrine:str):
    repo=Path(repo_s);m=load_research_execution_baseline_pf4(repo);samples=int(doc["stochasticTurnSamplesPerVariant"]);seed=derive_seed(int(doc["masterSeed"]),"cp162-stochastic",l.id,aux_space,aux_tp,count,main_offset,doctrine)
    rng=XorShift64(seed);supply=main_supply(m,l.tl,main_offset)+count*aux_tp
    hist=Counter();short=denied=0;group_req=Counter();group_fund=Counter()
    for _ in range(samples):
        req=_turn_requests(m,l,doctrine,rng);d=sum(x.cost for x in req);hist[d]+=1;a=_allocate(req,supply,doctrine);short+=int(a["denied_tp"]>0);denied+=a["denied_tp"]
        for x in req:group_req[x.group]+=1
        for g,n in a["funded"].items():group_fund[g]+=n
    total=sum(k*v for k,v in hist.items())/samples
    row={"tl":l.tl,"carrier_id":l.id,"weapon":l.weapon,"aux_space":aux_space,"aux_tp":aux_tp,"aux_count":count,"total_aux_space":aux_space*count,"total_aux_tp":aux_tp*count,"main_offset":main_offset,"main_supply":main_supply(m,l.tl,main_offset),"total_supply":supply,"doctrine":doctrine,"samples":samples,"mean_demand":total,"shortfall_rate":short/samples,"mean_denied_tp":denied/samples}
    alloc=[]
    for g in sorted(group_req):alloc.append({**{k:row[k] for k in ("tl","carrier_id","weapon","aux_space","aux_tp","aux_count","main_offset","doctrine","total_supply")},"group":g,"requests":group_req[g],"funded":group_fund[g],"funding_rate":group_fund[g]/max(1,group_req[g])})
    return row,alloc


def _stoch_unpack(x): return _stoch_one(*x)


def run_stochastic(repo:Path,study_path:Path,static_dir:Path,out:Path,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs: raise ValueError("CP162 study invalid: "+", ".join(errs))
    m=load_research_execution_baseline_pf4(repo); rows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1]; tasks=[];seen=set()
    for tl in range(1,10):
        tlrows=[x for x in rows if x.tl==tl]
        for s,tp in aux_specs(doc):
            for tier in STACK_TIERS:
                cnt=resolved_tier_count(tlrows,s,tier)
                if cnt<=0: continue
                l=select_carrier(m,rows,tl=tl,space_each=s,count=cnt)
                if not l: continue
                key=(tl,s,tp,cnt,l.id)
                if key in seen:continue
                seen.add(key)
                for off in doc["mainReactorOffsetsFromPf4"]:
                    for d in doc["stochasticDoctrines"]:tasks.append((str(repo),doc,l,s,tp,cnt,int(off),d))
    if jobs<=1:res=[_stoch_unpack(x) for x in tasks]
    else:
        ctx=get_context("spawn" if os.name=="nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx) as ex:res=list(ex.map(_stoch_unpack,tasks,chunksize=1))
    rows_out=[x[0] for x in res];alloc=[z for x in res for z in x[1]]
    rows_out.sort(key=lambda r:(r["tl"],r["aux_space"],r["aux_tp"],r["aux_count"],r["main_offset"],r["doctrine"]));_write_csv(out/"stochastic_stack_response.csv",rows_out);_write_csv(out/"allocation_outcomes.csv",alloc)
    agg=[];groups=defaultdict(list)
    for r in rows_out:groups[(r["aux_space"],r["aux_tp"],r["aux_count"],r["main_offset"])].append(r)
    for k,rr in sorted(groups.items()):agg.append({"aux_space":k[0],"aux_tp":k[1],"aux_count":k[2],"main_offset":k[3],"variants":len(rr),"mean_shortfall_rate":statistics.fmean(r["shortfall_rate"] for r in rr),"mean_denied_tp":statistics.fmean(r["mean_denied_tp"] for r in rr),"mean_total_supply":statistics.fmean(r["total_supply"] for r in rr)})
    _write_csv(out/"stochastic_stack_summary.csv",agg)
    summary={"mode":"stochastic","passed":True,"variants":len(rows_out),"samplesPerVariant":int(doc["stochasticTurnSamplesPerVariant"]),"turnSamples":len(rows_out)*int(doc["stochasticTurnSamplesPerVariant"]),"allocationRows":len(alloc),"automaticPromotion":False,"tuningAllowed":False}
    _write_json(out/"summary.json",summary);return summary


def _to_ecology(m:CandidateMatrix,l:PowerLoadout,ids:dict[tuple[str,int],str],*,aux_space:int,aux_tp:int,aux_count:int,label:str)->EcologyBuild:
    aux=[]
    if l.hardener and ("shieldHardener",l.tl) in ids:aux.append(ids[("shieldHardener",l.tl)])
    if l.energized and ("energizedArmor",l.tl) in ids:aux.append(ids[("energizedArmor",l.tl)])
    if l.stabilizer and ("fieldStabilizer",l.tl) in ids:aux.append(ids[("fieldStabilizer",l.tl)])
    if l.drone and ("repairDroneBay",l.tl) in ids:aux.append(ids[("repairDroneBay",l.tl)])
    if l.crystalline and ("crystallineArmor",l.tl) in ids:aux.append(ids[("crystallineArmor",l.tl)])
    fam={"K":"Kinetic","E":"Energy","M":"Missile","SW":"Missile"}[l.weapon];pds={"NONE":None,"K":"Kinetic","E":"Energy","AMM":"AMM"}[l.pds]
    used=l.used_space+aux_space*aux_count
    if used>l.capacity:raise ValueError("illegal CP162 combat carrier")
    return EcologyBuild(id=f"CP162-{label}-{l.id}-AR{aux_space}S{aux_tp}T-x{aux_count}",tl=l.tl,archetype="cp162-aux-reactor-carrier",weapon_family=fam,main_count=l.main_count,reactor_count=l.reactor_count,shield=l.shield,ecm=l.ecm,eccm=l.eccm,pds_family=pds,shield_hardener=l.hardener,capacity=l.capacity,combat_space=used,mission_aux_space=l.capacity-used,missile_payload=("Swarmer" if l.weapon=="SW" else "GP"),armor_profile="mainline",auxiliary_profiles=tuple(aux),auxiliary_power_tp=aux_tp*aux_count,auxiliary_reactor_count=aux_count)


def combat_contexts(repo:Path,study_path:Path,tl:int)->list[tuple[EcologyVariant,int,int,int,int]]:
    doc=load_json(study_path);m=load_research_execution_baseline_pf4(repo);ids=_pf4_aux_registry(m);rows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1 and x.tl==tl];out=[];seen=set()
    for s,tp in aux_specs(doc):
        for tier in STACK_TIERS:
            cnt=resolved_tier_count(rows,s,tier)
            if cnt<=0:continue
            for w in doc["combatWeaponFamilies"]:
                l=select_carrier(m,rows,tl=tl,space_each=s,count=cnt,weapon=w)
                if not l:continue
                key=(s,tp,cnt,w,l.id)
                if key in seen:continue
                seen.add(key)
                base=_to_ecology(m,l,ids,aux_space=s,aux_tp=tp,aux_count=0,label="BASE")
                aug=_to_ecology(m,l,ids,aux_space=s,aux_tp=tp,aux_count=cnt,label="STACK")
                for swap,(a,b) in enumerate(((aug,base),(base,aug))):
                    label=f"{w}_AR{s}S_{tp}TP_x{cnt}_{'STACKvsBASE' if swap==0 else 'BASEvsSTACK'}"
                    v=EcologyVariant(id=f"CP162-TL{tl}-{label}",tl=tl,side_a=a,side_b=b,movement_order=("SideAFirst" if swap==0 else "SideBFirst"),population="cp162_aux_reactor_stack_safety",scenario_group=label)
                    out.append((v,s,tp,cnt,swap))
    return out


_C_REPO:Path|None=None;_C_STUDY:Path|None=None;_C_DOC:dict[str,Any]|None=None;_C_CACHE:dict[tuple[int,int],CandidateMatrix]={}
def _combat_init(repo_s:str,study_s:str,doc:dict[str,Any]):
    global _C_REPO,_C_STUDY,_C_DOC,_C_CACHE;_C_REPO=Path(repo_s);_C_STUDY=Path(study_s);_C_DOC=doc;_C_CACHE={}
def _combat_matrix(tl:int,off:int)->CandidateMatrix:
    key=(tl,off)
    if key not in _C_CACHE:
        m=load_research_execution_baseline_pf4(_C_REPO);_pf4_aux_registry(m);m=copy.deepcopy(m);m.doc=copy.deepcopy(m.doc);m.profiles=m.doc["profiles"];m.branches={r["id"]:r for r in m.doc.get("branches",[])};m.p("reactor",tl)["operationalTp"]=main_supply(m,tl,off);_C_CACHE[key]=m
    return _C_CACHE[key]
def _combat_task(args):
    v,s,tp,cnt,swap,off,seed,trials=args;m=_combat_matrix(v.tl,off);aw=bw=dr=caps=err=turns=0;sa=defaultdict(float);sb=defaultdict(float);metrics=("power_available_total","power_spent_total","power_shortfall_events","weapon_power_shortfalls","pds_power_shortfalls","acquisition_power_shortfalls","power_sensor","power_ecm","power_eccm","power_pds","power_weapons","power_shield_recharge","power_shield_hardener","power_aux_energized_armor","power_aux_field_stabilizer","reactor_overload_activations","damage_control_tp_spent")
    for j in range(trials):
        r=run_trial_full_map(m,v,seed,j,combat_doctrine=COMBAT_DOCTRINE);err+=int(bool(r.error));caps+=int(r.termination_cause=="TURN_CAP_SENTINEL");turns+=r.turns
        if r.winner=="A":aw+=1
        elif r.winner=="B":bw+=1
        else:dr+=1
        for k in metrics:sa[k]+=float(getattr(r.side_a,k,0));sb[k]+=float(getattr(r.side_b,k,0))
    row={"tl":v.tl,"scenario_id":v.id,"scenario_group":v.scenario_group,"aux_space":s,"aux_tp":tp,"aux_count":cnt,"total_aux_space":s*cnt,"total_aux_tp":tp*cnt,"main_offset":off,"main_supply":main_supply(load_research_execution_baseline_pf4(_C_REPO),v.tl,off),"trials":trials,"a_wins":aw,"b_wins":bw,"draws":dr,"a_decisive_share":aw/max(1,aw+bw),"mean_turns":turns/max(1,trials),"turn_cap_sentinels":caps,"error_trials":err,"side_a_build":v.side_a.id,"side_b_build":v.side_b.id,"side_a_aux_count":v.side_a.auxiliary_reactor_count,"side_b_aux_count":v.side_b.auxiliary_reactor_count}
    for k in metrics:row["mean_a_"+k]=sa[k]/trials;row["mean_b_"+k]=sb[k]/trials
    return row


def run_combat_batch(repo:Path,study_path:Path,out:Path,tl:int,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP162 study invalid: "+", ".join(errs))
    ctxs=combat_contexts(repo,study_path,tl);trials=int(doc["combatTrialsPerCell"]);tasks=[]
    for i,(v,s,tp,cnt,swap) in enumerate(ctxs):
        for off in doc["mainReactorOffsetsFromPf4"]:tasks.append((v,s,tp,cnt,swap,int(off),derive_seed(int(doc["masterSeed"]),"cp162-combat",tl,v.id,off),trials))
    if jobs<=1:_combat_init(str(repo),str(study_path),doc);rows=[_combat_task(x) for x in tasks]
    else:
        ctx=get_context("spawn" if os.name=="nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx,initializer=_combat_init,initargs=(str(repo),str(study_path),doc)) as ex:rows=list(ex.map(_combat_task,tasks,chunksize=1))
    rows.sort(key=lambda r:(r["scenario_id"],r["main_offset"]));_write_csv(out/"combat_response.csv",rows)
    summary={"mode":"combat-batch","passed":not any(r["error_trials"] for r in rows),"tl":tl,"contexts":len(ctxs),"mainOffsetCandidates":3,"cells":len(rows),"trialsPerCell":trials,"combatTrials":len(rows)*trials,"turnCapSentinels":sum(r["turn_cap_sentinels"] for r in rows),"errorTrials":sum(r["error_trials"] for r in rows),"automaticPromotion":False}
    _write_json(out/"summary.json",summary);return summary


def merge_combat(batch_root:Path,out:Path)->dict[str,Any]:
    rows=[];audit=[]
    for p in sorted(batch_root.rglob("summary.json")):
        sm=json.loads(p.read_text(encoding="utf-8-sig"));data=p.parent/"combat_response.csv";ok=sm.get("mode")=="combat-batch" and bool(sm.get("passed")) and data.is_file();n=0
        if ok:
            with data.open(encoding="utf-8-sig",newline="") as f:r=list(csv.DictReader(f));rows.extend(r);n=len(r)
        audit.append({"batch":p.parent.name,"tl":sm.get("tl",""),"passed":int(ok),"rows":n,"combat_trials":sm.get("combatTrials",0),"turn_caps":sm.get("turnCapSentinels",0),"errors":sm.get("errorTrials",0)})
    rows.sort(key=lambda r:(int(r["tl"]),int(r["aux_space"]),int(r["aux_tp"]),int(r["aux_count"]),int(r["main_offset"]),r["scenario_id"]));_write_csv(out/"combat_response.csv",rows);_write_csv(out/"batch_merge_audit.csv",audit)
    groups=defaultdict(list)
    for r in rows:groups[(int(r["aux_space"]),int(r["aux_tp"]),int(r["aux_count"]),int(r["main_offset"]))].append(r)
    sums=[]
    for k,rr in sorted(groups.items()):
        # Stack is Side A in exactly half the mirrored rows; normalize decisive share to stack side.
        wins=losses=draws=trials=turncaps=0
        for r in rr:
            a_stack=int(r["side_a_aux_count"])>0;wins+=int(r["a_wins"] if a_stack else r["b_wins"]);losses+=int(r["b_wins"] if a_stack else r["a_wins"]);draws+=int(r["draws"]);trials+=int(r["trials"]);turncaps+=int(r["turn_cap_sentinels"])
        sums.append({"aux_space":k[0],"aux_tp":k[1],"aux_count":k[2],"total_aux_space":k[0]*k[2],"total_aux_tp":k[1]*k[2],"main_offset":k[3],"cells":len(rr),"combat_trials":trials,"stack_wins":wins,"base_wins":losses,"draws":draws,"stack_decisive_share":wins/max(1,wins+losses),"turn_cap_rate":turncaps/max(1,trials)})
    _write_csv(out/"combat_stack_summary.csv",sums)
    summary={"mode":"combat-merged","passed":len(audit)==9 and all(x["passed"] for x in audit) and not any(int(r["error_trials"]) for r in rows),"batches":len(audit),"cells":len(rows),"combatTrials":sum(int(r["trials"]) for r in rows),"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errorTrials":sum(int(r["error_trials"]) for r in rows),"automaticPromotion":False}
    _write_json(out/"summary.json",summary);return summary


def plan(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP162 study invalid: "+", ".join(errs))
    m=load_research_execution_baseline_pf4(repo);all_rows=enumerate_loadouts(m,reactor_space=6);rows=[x for x in all_rows if x.reactor_count==1]
    # Count stochastic tasks exactly with the same de-duplication rule as execution.
    stoch=0
    for tl in range(1,10):
        tlrows=[x for x in rows if x.tl==tl];seen=set()
        for s,tp in aux_specs(doc):
            for tier in STACK_TIERS:
                cnt=resolved_tier_count(tlrows,s,tier)
                if cnt<=0:continue
                l=select_carrier(m,rows,tl=tl,space_each=s,count=cnt)
                if not l:continue
                key=(tl,s,tp,cnt,l.id)
                if key in seen:continue
                seen.add(key);stoch+=len(doc["mainReactorOffsetsFromPf4"])*len(doc["stochasticDoctrines"])
    ctx={tl:len(combat_contexts(repo,study_path,tl)) for tl in range(1,10)};cells=sum(ctx.values())*3;combat=cells*int(doc["combatTrialsPerCell"])
    summary={"mode":"plan","passed":True,"baselineId":"CP160-PF4","acceptedDiagnosticCheckpoint":161,"legalPoweredArchitectures":len(all_rows),"oneMainReactorArchitectures":len(rows),"mainReactorSpace":6,"mainOffsets":doc["mainReactorOffsetsFromPf4"],"auxCandidates":len(aux_specs(doc)),"installationCountCapImposed":False,"stochasticVariants":stoch,"stochasticTurnSamples":stoch*int(doc["stochasticTurnSamplesPerVariant"]),"combatContextsByTl":ctx,"combatContexts":sum(ctx.values()),"combatCells":cells,"combatTrials":combat,"automaticPromotion":False,"tuningAllowed":False}
    _write_json(out/"summary.json",summary);return summary


def smoke(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);m=load_research_execution_baseline_pf4(repo);rows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1];checks=[]
    checks.append({"probe":"pf4_main_reactor_space_6","passed":int(all(int(m.p("reactor",t)["space"])==6 for t in range(1,10)))})
    # TL1 intact base cruiser cannot fit a second full Reactor, but can fit up to 4 one-Space Aux Reactors.
    cap=int(m.p("hull",1)["capacity"]);base=_base_cruiser_space(m,1);checks.append({"probe":"tl1_base_cruiser_second_main_reactor_blocked","passed":int(base+6>cap)})
    checks.append({"probe":"tl1_base_cruiser_one_space_aux_stacks","passed":int((cap-base)//1==4)})
    c=select_carrier(m,rows,tl=9,space_each=1,count=3,weapon="E");checks.append({"probe":"stack_carrier_exists","passed":int(c is not None)})
    ctxs=combat_contexts(repo,study_path,9);v,s,tp,cnt,swap=next(x for x in ctxs if x[1]==1 and x[2]==2 and x[3]>=2);_combat_init(str(repo),str(study_path),doc);r=_combat_task((v,s,tp,cnt,swap,0,derive_seed(int(doc["masterSeed"]),"smoke"),2));checks.append({"probe":"live_aux_power_combat","passed":int(r["error_trials"]==0 and max(v.side_a.auxiliary_power_tp,v.side_b.auxiliary_power_tp)>=4)})
    _write_csv(out/"cp162_smoke.csv",checks);summary={"mode":"smoke","passed":all(x["passed"] for x in checks),"probes":len(checks),"combatTrials":2};_write_json(out/"summary.json",summary);return summary


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--study",required=True);sp=ap.add_subparsers(dest="cmd",required=True)
    for n in ("plan","smoke","static"):p=sp.add_parser(n);p.add_argument("--out",required=True)
    p=sp.add_parser("stochastic");p.add_argument("--static-dir",required=True);p.add_argument("--out",required=True);p.add_argument("--jobs",type=int,default=24)
    p=sp.add_parser("combat-batch");p.add_argument("--tl",type=int,required=True);p.add_argument("--out",required=True);p.add_argument("--jobs",type=int,default=24)
    p=sp.add_parser("merge-combat");p.add_argument("--batches",required=True);p.add_argument("--out",required=True)
    a=ap.parse_args(argv);repo=Path(a.repo).resolve();study=Path(a.study).resolve();out=Path(a.out).resolve()
    if a.cmd=="plan":r=plan(repo,study,out)
    elif a.cmd=="smoke":r=smoke(repo,study,out)
    elif a.cmd=="static":r=static_analysis(repo,study,out)
    elif a.cmd=="stochastic":r=run_stochastic(repo,study,Path(a.static_dir),out,a.jobs)
    elif a.cmd=="combat-batch":r=run_combat_batch(repo,study,out,a.tl,a.jobs)
    elif a.cmd=="merge-combat":r=merge_combat(Path(a.batches),out)
    else:raise SystemExit(2)
    print(json.dumps(r,indent=2));return 0 if r.get("passed",False) else 1

if __name__=="__main__":raise SystemExit(main())
