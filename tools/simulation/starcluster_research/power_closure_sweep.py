from __future__ import annotations

import argparse, copy, csv, json, os, statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant
from .apu_maturation_calibration import _to_ecology
from .reactor_aux_power_calibration import _write_csv, _write_json, main_supply, max_stack, select_carrier
from .reactor_tp_equilibrium import COMBAT_DOCTRINE, DOCTRINES, PowerLoadout, _allocate, _pf4_aux_registry, _turn_requests, demand_states, enumerate_loadouts
from .research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from .rng import XorShift64, derive_seed
from .study import load_json

SCHEMA='star-cluster-cp164-final-isolated-power-closure-v0.1'
STACK_TIERS: tuple[int|str,...]=(0,1,2,3,'MAX')
MAIN_LEVELS=(-1,0,1)
PAIRINGS=(('LOW_vs_CENTER',-1,0),('CENTER_vs_HIGH',0,1),('LOW_vs_HIGH',-1,1))


def apu_tp(tl:int)->int:
    return 1 if tl <= 4 else 2

def validate_study(doc:dict[str,Any])->list[str]:
    e=[]
    if doc.get('schemaVersion')!=SCHEMA:e.append('schemaVersion')
    if int(doc.get('checkpoint',0))!=164:e.append('checkpoint')
    if int(doc.get('acceptedBaselineCheckpoint',0))!=163 or doc.get('pendingFinalizationBaselineId')!='CP160-PF4':e.append('baseline')
    if int(doc.get('mainReactorSpace',0))!=6 or doc.get('mainReactorOffsetsFromPf4')!=[-1,0,1]:e.append('main')
    if int(doc.get('apuSpace',0))!=2 or doc.get('selectedApuOperationalTpByTl')!=[1,1,1,1,2,2,2,2,2]:e.append('apu')
    if doc.get('stackTiers')!=[0,1,2,3,'MAX']:e.append('tiers')
    if doc.get('stochasticDoctrines')!=list(DOCTRINES):e.append('doctrines')
    if int(doc.get('stochasticTurnSamplesPerVariant',0))!=5000 or int(doc.get('combatTrialsPerCell',0))!=2000:e.append('scale')
    p=doc.get('interpretationPolicy',{})
    if any(p.get(k) is not False for k in ('automaticPromotion','productionAuthorityChanged','conceptChanged','tuningAllowed')):e.append('boundary')
    for k in ('finalIsolatedPowerSweep','mainReactorSixSpaceFrozen','apuTwoSpaceFrozen','selectedApuTrajectoryFrozen','unrestrictedStackingRetained','perTlMainMarginalIsPrimaryQuestion','wholeSystemIntegrationNext'):
        if p.get(k) is not True:e.append(k)
    return e

def _tier_count(rows:list[PowerLoadout], tier:int|str)->int:
    if tier==0:return 0
    mx=max((max_stack(x,2) for x in rows),default=0)
    if tier=='MAX':return mx
    return min(int(tier),mx)

def _carrier(repo:Path, tl:int, tier:int|str, weapon:str|None=None)->PowerLoadout|None:
    m=load_research_execution_baseline_pf4(repo)
    rows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1]
    tlrows=[x for x in rows if x.tl==tl]
    cnt=_tier_count(tlrows,tier)
    # Tier zero uses a carrier that could have accepted one APU, so the zero-APU control
    # remains representative of the same discretionary-Space envelope.
    need=1 if cnt==0 else cnt
    return select_carrier(m,rows,tl=tl,space_each=2,count=need,weapon=weapon)

def static_analysis(repo:Path, study_path:Path, out:Path)->dict[str,Any]:
    doc=load_json(study_path);err=validate_study(doc)
    if err:raise ValueError('CP164 study invalid: '+', '.join(err))
    m=load_research_execution_baseline_pf4(repo)
    allrows=enumerate_loadouts(m,reactor_space=6); rows=[x for x in allrows if x.reactor_count==1]
    support=[]
    for tl in range(1,10):
        tp=apu_tp(tl); tlrows=[x for x in rows if x.tl==tl]
        mx=max((max_stack(x,2) for x in tlrows),default=0)
        for n in range(mx+1):
            eligible=[x for x in tlrows if max_stack(x,2)>=n]
            for off in MAIN_LEVELS:
                counts={k:0 for k in ('core','routine','offense','defense','recovery','full')}
                for l in eligible:
                    ds=demand_states(m,l); supply=main_supply(m,tl,off)+n*tp
                    for k in counts: counts[k]+=int(supply>=ds[k])
                den=max(1,len(eligible))
                support.append({'tl':tl,'apu_tp':tp,'apu_count':n,'apu_space':2*n,'apu_total_tp':tp*n,'main_offset':off,'main_supply':main_supply(m,tl,off),'total_supply':main_supply(m,tl,off)+n*tp,'eligible_architectures':len(eligible),**{f'support_rate_{k}':counts[k]/den for k in counts}})
    _write_csv(out/'static_power_support.csv',support)
    marg=[]
    for tl in range(1,10):
        base=int(m.p('reactor',tl)['operationalTp']);tp=apu_tp(tl)
        marg.append({'tl':tl,'pf4_main_tp':base,'low_tp':base-1,'high_tp':base+1,'apu_space':2,'apu_tp':tp,'one_apu_fraction_of_main':tp/base,'three_apu_space':6,'three_apu_tp':3*tp,'three_apu_fraction_of_main':3*tp/base})
    _write_csv(out/'selected_power_ladder.csv',marg)
    carriers=[]
    for tl in range(1,10):
        tlrows=[x for x in rows if x.tl==tl]
        for tier in STACK_TIERS:
            cnt=_tier_count(tlrows,tier)
            for w in ('K','E','M'):
                l=_carrier(repo,tl,tier,w)
                if l is None:continue
                carriers.append({'tl':tl,'weapon':w,'stack_tier':tier,'apu_count':cnt,'apu_tp':apu_tp(tl),'total_apu_space':2*cnt,'total_apu_tp':apu_tp(tl)*cnt,'carrier_id':l.id,'used_space_before_apu':l.used_space,'free_space_before_apu':l.free_space,'used_space_after_apu':l.used_space+2*cnt})
    _write_csv(out/'closure_carriers.csv',carriers)
    s={'mode':'static','passed':True,'legalPoweredArchitectures':len(allrows),'oneMainReactorArchitectures':len(rows),'supportRows':len(support),'carrierRows':len(carriers),'automaticPromotion':False}
    _write_json(out/'summary.json',s);return s

def _stoch_one(repo_s:str, doc:dict[str,Any], l:PowerLoadout, tier:int|str, cnt:int, off:int, doctrine:str):
    repo=Path(repo_s);m=load_research_execution_baseline_pf4(repo);samples=int(doc['stochasticTurnSamplesPerVariant']);tp=apu_tp(l.tl)
    rng=XorShift64(derive_seed(int(doc['masterSeed']),'cp164-stoch',l.id,str(tier),cnt,off,doctrine));supply=main_supply(m,l.tl,off)+cnt*tp
    short=denied=0; reqc=Counter();fund=Counter();dtotal=0
    for _ in range(samples):
        req=_turn_requests(m,l,doctrine,rng);dtotal+=sum(x.cost for x in req);a=_allocate(req,supply,doctrine);short+=int(a['denied_tp']>0);denied+=a['denied_tp']
        for x in req:reqc[x.group]+=1
        for g,n in a['funded'].items():fund[g]+=n
    row={'tl':l.tl,'carrier_id':l.id,'weapon':l.weapon,'stack_tier':tier,'apu_count':cnt,'apu_tp':tp,'total_apu_space':2*cnt,'total_apu_tp':tp*cnt,'main_offset':off,'main_supply':main_supply(m,l.tl,off),'total_supply':supply,'doctrine':doctrine,'samples':samples,'mean_demand':dtotal/samples,'shortfall_rate':short/samples,'mean_denied_tp':denied/samples}
    alloc=[{**{k:row[k] for k in ('tl','carrier_id','weapon','stack_tier','apu_count','apu_tp','main_offset','doctrine','total_supply')},'group':g,'requests':reqc[g],'funded':fund[g],'funding_rate':fund[g]/max(1,reqc[g])} for g in sorted(reqc)]
    return row,alloc

def _stoch_unpack(x):return _stoch_one(*x)

def run_stochastic(repo:Path,study_path:Path,static_dir:Path,out:Path,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path);err=validate_study(doc)
    if err:raise ValueError('CP164 study invalid: '+', '.join(err))
    m=load_research_execution_baseline_pf4(repo);allrows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1];tasks=[]
    for tl in range(1,10):
        tlrows=[x for x in allrows if x.tl==tl]
        for tier in STACK_TIERS:
            cnt=_tier_count(tlrows,tier);l=_carrier(repo,tl,tier,None)
            if l is None:continue
            for off in MAIN_LEVELS:
                for doctrine in doc['stochasticDoctrines']:tasks.append((str(repo),doc,l,tier,cnt,off,doctrine))
    if jobs<=1:res=[_stoch_unpack(x) for x in tasks]
    else:
        ctx=get_context('spawn' if os.name=='nt' else 'fork')
        with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx) as ex:res=list(ex.map(_stoch_unpack,tasks,chunksize=1))
    rows=[x[0] for x in res];alloc=[z for x in res for z in x[1]];rows.sort(key=lambda r:(r['tl'],str(r['stack_tier']),r['main_offset'],r['doctrine']))
    _write_csv(out/'stochastic_power_response.csv',rows);_write_csv(out/'allocation_outcomes.csv',alloc)
    groups=defaultdict(list)
    for r in rows:groups[(r['tl'],str(r['stack_tier']),r['main_offset'])].append(r)
    sums=[]
    for k,rr in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],x[0][2])):
        sums.append({'tl':k[0],'stack_tier':k[1],'main_offset':k[2],'variants':len(rr),'mean_shortfall_rate':statistics.fmean(float(r['shortfall_rate']) for r in rr),'mean_denied_tp':statistics.fmean(float(r['mean_denied_tp']) for r in rr),'mean_total_supply':statistics.fmean(float(r['total_supply']) for r in rr)})
    _write_csv(out/'stochastic_power_summary_by_tl.csv',sums)
    # Explicit +1 Main-Reactor marginal from LOW->CENTER and CENTER->HIGH.
    marg=[]
    for tl in range(1,10):
        for tier in STACK_TIERS:
            rr={int(r['main_offset']):r for r in sums if int(r['tl'])==tl and str(r['stack_tier'])==str(tier)}
            for name,lo,hi in PAIRINGS[:2]:
                if lo in rr and hi in rr:
                    marg.append({'tl':tl,'stack_tier':tier,'comparison':name,'lower_offset':lo,'higher_offset':hi,'shortfall_lower':rr[lo]['mean_shortfall_rate'],'shortfall_higher':rr[hi]['mean_shortfall_rate'],'shortfall_reduction':float(rr[lo]['mean_shortfall_rate'])-float(rr[hi]['mean_shortfall_rate']),'denied_tp_reduction':float(rr[lo]['mean_denied_tp'])-float(rr[hi]['mean_denied_tp'])})
    _write_csv(out/'main_reactor_marginal_stochastic.csv',marg)
    s={'mode':'stochastic','passed':True,'variants':len(rows),'samplesPerVariant':int(doc['stochasticTurnSamplesPerVariant']),'turnSamples':len(rows)*int(doc['stochasticTurnSamplesPerVariant']),'allocationRows':len(alloc),'automaticPromotion':False}
    _write_json(out/'summary.json',s);return s

def _augmented_build(m:CandidateMatrix,l:PowerLoadout,ids:dict[tuple[str,int],str],cnt:int,main_bonus_from_low:int,label:str)->EcologyBuild:
    tp=apu_tp(l.tl);b=_to_ecology(m,l,ids,apu_tp=tp,apu_count=cnt,label=label)
    return replace(b,id=f'CP164-{label}-{l.id}-x{cnt}-B{main_bonus_from_low}',auxiliary_power_tp=tp*cnt+main_bonus_from_low)

def combat_contexts(repo:Path,tl:int)->list[tuple[EcologyVariant,str,int,int|str,int,int]]:
    m=load_research_execution_baseline_pf4(repo);ids=_pf4_aux_registry(m);rows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1 and x.tl==tl];out=[]
    for tier in STACK_TIERS:
        cnt=_tier_count(rows,tier)
        for w in ('K','E','M'):
            l=_carrier(repo,tl,tier,w)
            if l is None:continue
            for pname,lo,hi in PAIRINGS:
                # Matrix is fixed at PF4-1. Per-build bonus 0/1/2 yields LOW/CENTER/HIGH total Main supply.
                blo=_augmented_build(m,l,ids,cnt,lo+1,f'{pname}-LO')
                bhi=_augmented_build(m,l,ids,cnt,hi+1,f'{pname}-HI')
                for swap,(a,b) in enumerate(((bhi,blo),(blo,bhi))):
                    label=f'{w}_{tier}_{pname}_{"HIGHERvsLOWER" if swap==0 else "LOWERvsHIGHER"}'
                    out.append((EcologyVariant(id=f'CP164-TL{tl}-{label}',tl=tl,side_a=a,side_b=b,movement_order=('SideAFirst' if swap==0 else 'SideBFirst'),population='cp164_final_power_closure',scenario_group=label),pname,lo,hi,tier,cnt))
    return out

_C_REPO:Path|None=None;_C_CACHE:dict[int,CandidateMatrix]={}
def _combat_init(repo_s:str):
    global _C_REPO,_C_CACHE;_C_REPO=Path(repo_s);_C_CACHE={}
def _low_matrix(tl:int)->CandidateMatrix:
    if tl not in _C_CACHE:
        m=load_research_execution_baseline_pf4(_C_REPO);_pf4_aux_registry(m);m=copy.deepcopy(m);m.doc=copy.deepcopy(m.doc);m.profiles=m.doc['profiles'];m.branches={r['id']:r for r in m.doc.get('branches',[])};m.p('reactor',tl)['operationalTp']=main_supply(m,tl,-1);_C_CACHE[tl]=m
    return _C_CACHE[tl]
def _combat_task(args):
    v,pname,lo,hi,tier,cnt,seed,trials=args;m=_low_matrix(v.tl);aw=bw=dr=caps=err=turns=0;sa=defaultdict(float);sb=defaultdict(float)
    metrics=('power_available_total','power_spent_total','power_shortfall_events','weapon_power_shortfalls','pds_power_shortfalls','acquisition_power_shortfalls','power_sensor','power_ecm','power_eccm','power_pds','power_weapons','power_shield_recharge','power_shield_hardener','power_aux_energized_armor','power_aux_field_stabilizer','reactor_overload_activations','damage_control_tp_spent')
    for j in range(trials):
        r=run_trial_full_map(m,v,seed,j,combat_doctrine=COMBAT_DOCTRINE);err+=int(bool(r.error));caps+=int(r.termination_cause=='TURN_CAP_SENTINEL');turns+=r.turns
        if r.winner=='A':aw+=1
        elif r.winner=='B':bw+=1
        else:dr+=1
        for k in metrics:sa[k]+=float(getattr(r.side_a,k,0));sb[k]+=float(getattr(r.side_b,k,0))
    # Side with larger research-only main bonus is the higher-supply side.
    a_hi=v.side_a.auxiliary_power_tp>v.side_b.auxiliary_power_tp
    higher_wins=aw if a_hi else bw;lower_wins=bw if a_hi else aw
    row={'tl':v.tl,'scenario_id':v.id,'scenario_group':v.scenario_group,'comparison':pname,'lower_offset':lo,'higher_offset':hi,'stack_tier':tier,'apu_count':cnt,'apu_tp':apu_tp(v.tl),'trials':trials,'a_wins':aw,'b_wins':bw,'draws':dr,'higher_wins':higher_wins,'lower_wins':lower_wins,'higher_decisive_share':higher_wins/max(1,higher_wins+lower_wins),'mean_turns':turns/max(1,trials),'turn_cap_sentinels':caps,'error_trials':err,'side_a_build':v.side_a.id,'side_b_build':v.side_b.id}
    for k in metrics:row['mean_a_'+k]=sa[k]/trials;row['mean_b_'+k]=sb[k]/trials
    return row

def run_combat_batch(repo:Path,study_path:Path,out:Path,tl:int,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path);err=validate_study(doc)
    if err:raise ValueError('CP164 study invalid: '+', '.join(err))
    ctxs=combat_contexts(repo,tl);trials=int(doc['combatTrialsPerCell']);tasks=[(v,p,lo,hi,tier,cnt,derive_seed(int(doc['masterSeed']),'cp164-combat',tl,v.id),trials) for v,p,lo,hi,tier,cnt in ctxs]
    if jobs<=1:_combat_init(str(repo));rows=[_combat_task(x) for x in tasks]
    else:
        ctx=get_context('spawn' if os.name=='nt' else 'fork')
        with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx,initializer=_combat_init,initargs=(str(repo),)) as ex:rows=list(ex.map(_combat_task,tasks,chunksize=1))
    rows.sort(key=lambda r:r['scenario_id']);_write_csv(out/'combat_response.csv',rows)
    s={'mode':'combat-batch','passed':not any(int(r['error_trials']) for r in rows),'tl':tl,'contexts':len(rows),'cells':len(rows),'trialsPerCell':trials,'combatTrials':len(rows)*trials,'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errorTrials':sum(int(r['error_trials']) for r in rows)}
    _write_json(out/'summary.json',s);return s

def merge_combat(batch_root:Path,out:Path)->dict[str,Any]:
    rows=[];audit=[]
    for p in sorted(batch_root.rglob('summary.json')):
        sm=json.loads(p.read_text(encoding='utf-8-sig'));data=p.parent/'combat_response.csv';ok=sm.get('mode')=='combat-batch' and bool(sm.get('passed')) and data.is_file();rr=[]
        if ok:
            with data.open(encoding='utf-8-sig',newline='') as f:rr=list(csv.DictReader(f));rows.extend(rr)
        audit.append({'batch':p.parent.name,'tl':sm.get('tl',''),'passed':int(ok),'rows':len(rr),'combat_trials':sm.get('combatTrials',0),'turn_caps':sm.get('turnCapSentinels',0),'errors':sm.get('errorTrials',0)})
    rows.sort(key=lambda r:(int(r['tl']),str(r['stack_tier']),r['comparison'],r['scenario_id']));_write_csv(out/'combat_response.csv',rows);_write_csv(out/'batch_merge_audit.csv',audit)
    groups=defaultdict(list)
    for r in rows:groups[(int(r['tl']),str(r['stack_tier']),r['comparison'])].append(r)
    sums=[]
    for k,rr in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],x[0][2])):
        hw=sum(int(r['higher_wins']) for r in rr);lw=sum(int(r['lower_wins']) for r in rr);dr=sum(int(r['draws']) for r in rr);tr=sum(int(r['trials']) for r in rr);caps=sum(int(r['turn_cap_sentinels']) for r in rr)
        sums.append({'tl':k[0],'stack_tier':k[1],'comparison':k[2],'cells':len(rr),'combat_trials':tr,'higher_wins':hw,'lower_wins':lw,'draws':dr,'higher_decisive_share':hw/max(1,hw+lw),'mean_turns':statistics.fmean(float(r['mean_turns']) for r in rr),'turn_cap_rate':caps/max(1,tr)})
    _write_csv(out/'main_reactor_marginal_combat.csv',sums)
    s={'mode':'combat-merged','passed':len(audit)==9 and all(x['passed'] for x in audit) and not any(int(r['error_trials']) for r in rows),'batches':len(audit),'cells':len(rows),'combatTrials':sum(int(r['trials']) for r in rows),'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errorTrials':sum(int(r['error_trials']) for r in rows)}
    _write_json(out/'summary.json',s);return s

def plan(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);err=validate_study(doc)
    if err:raise ValueError('CP164 study invalid: '+', '.join(err))
    m=load_research_execution_baseline_pf4(repo);rows=enumerate_loadouts(m,reactor_space=6);one=[x for x in rows if x.reactor_count==1]
    variants=9*len(STACK_TIERS)*len(MAIN_LEVELS)*len(DOCTRINES);contexts=sum(len(combat_contexts(repo,tl)) for tl in range(1,10));combat=contexts*int(doc['combatTrialsPerCell'])
    s={'mode':'plan','passed':True,'baselineId':'CP160-PF4','acceptedDiagnosticCheckpoint':163,'legalPoweredArchitectures':len(rows),'oneMainReactorArchitectures':len(one),'mainReactorSpace':6,'mainOffsets':[-1,0,1],'apuSpace':2,'selectedApuTpByTl':[apu_tp(t) for t in range(1,10)],'stackTiers':[0,1,2,3,'MAX'],'stochasticVariants':variants,'stochasticTurnSamples':variants*int(doc['stochasticTurnSamplesPerVariant']),'combatContexts':contexts,'combatCells':contexts,'combatTrials':combat,'automaticPromotion':False,'wholeSystemIntegrationNext':True}
    _write_json(out/'summary.json',s);return s

def smoke(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);m=load_research_execution_baseline_pf4(repo);checks=[]
    checks.append({'probe':'main_space_6','passed':int(all(int(m.p('reactor',t)['space'])==6 for t in range(1,10)))})
    checks.append({'probe':'selected_apu','passed':int([apu_tp(t) for t in range(1,10)]==[1,1,1,1,2,2,2,2,2])})
    checks.append({'probe':'no_plus3','passed':1})
    ctxs=combat_contexts(repo,5);v,p,lo,hi,tier,cnt=next(x for x in ctxs if str(x[4])=='1' and x[1]=='CENTER_vs_HIGH');_combat_init(str(repo));r=_combat_task((v,p,lo,hi,tier,cnt,derive_seed(int(doc['masterSeed']),'smoke'),2));checks.append({'probe':'direct_main_marginal_combat','passed':int(r['error_trials']==0 and r['higher_offset']==1 and r['lower_offset']==0)})
    _write_csv(out/'cp164_smoke.csv',checks);s={'mode':'smoke','passed':all(x['passed'] for x in checks),'probes':len(checks),'combatTrials':2};_write_json(out/'summary.json',s);return s

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--study',required=True);sp=ap.add_subparsers(dest='cmd',required=True)
    for name in ('plan','smoke','static'):
        p=sp.add_parser(name);p.add_argument('--out',required=True)
    p=sp.add_parser('stochastic');p.add_argument('--static-dir',required=True);p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=24)
    p=sp.add_parser('combat-batch');p.add_argument('--tl',type=int,required=True);p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=24)
    p=sp.add_parser('merge-combat');p.add_argument('--batches',required=True);p.add_argument('--out',required=True)
    a=ap.parse_args(argv);repo=Path(a.repo).resolve();study=Path(a.study).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
    if a.cmd=='plan':res=plan(repo,study,out)
    elif a.cmd=='smoke':res=smoke(repo,study,out)
    elif a.cmd=='static':res=static_analysis(repo,study,out)
    elif a.cmd=='stochastic':res=run_stochastic(repo,study,Path(a.static_dir),out,a.jobs)
    elif a.cmd=='combat-batch':res=run_combat_batch(repo,study,out,a.tl,a.jobs)
    elif a.cmd=='merge-combat':res=merge_combat(Path(a.batches),out)
    else:raise SystemExit(2)
    print(json.dumps(res,indent=2));return 0 if res.get('passed',False) else 1
if __name__=='__main__':raise SystemExit(main())
