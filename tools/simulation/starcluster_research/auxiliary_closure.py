from __future__ import annotations
import argparse,csv,hashlib,itertools,json,math,random,statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any
from .canonical_combat import run_trial_full_map
from .ecology import CandidateMatrix
from .stage_a_integration_analysis import bind_scenario,_energy_mode_tp
from .study import load_json
from .research_execution_baseline_pf3 import load_research_execution_baseline_pf3,aux_profile
from .defense_aux_lifetime_viability import _apply_candidate,_apply_package,_trial_row

SCHEMA='star-cluster-cp159-aux-closure-v0.1'
BASELINE_TRIALS=50; FIELD_SCREEN_TRIALS=50; CRYSTAL_SCREEN_TRIALS=30; DEEP_TRIALS=100; INTERACTION_TRIALS=50; DRONE_MICRO_TRIALS=3000
FIELD_REDUCTIONS=(4,6,8,10,12,14,16,18,20,22,24); FIELD_TP=(0,1,2)
CRYSTAL_CAP=(8,10,12,14,16); CRYSTAL_RES=(15,20,25,30)


def _read_csv(p:Path)->list[dict[str,str]]:
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def _write_csv(p:Path,rows:list[dict[str,Any]]):
 p.parent.mkdir(parents=True,exist_ok=True)
 if not rows:p.write_text('',encoding='utf-8');return
 fields=[]
 for r in rows:
  for k in r:
   if k not in fields:fields.append(k)
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
def _json_write(p:Path,obj:Any):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
def _resource_rows(repo:Path,doc:dict[str,Any]):return _read_csv(repo/doc['resourceEnsemble']),_read_csv(repo/doc['resourceEnsembleTl'])
def _manifest(repo:Path,doc:dict[str,Any]):return _read_csv(repo/doc['stageAExperimentManifest'])

def _resource_matrix(repo:Path,doc:dict[str,Any],ensemble_id:str)->CandidateMatrix:
 m=load_research_execution_baseline_pf3(repo);ens_rows,tl_rows=_resource_rows(repo,doc);ens=next(r for r in ens_rows if r['ensemble_id']==ensemble_id);per={int(r['tl']):r for r in tl_rows if r['ensemble_id']==ensemble_id}
 m.resource_ensemble_id=ensemble_id;m.resource_ensemble_role=ens['ensemble_role'];m.resource_aux_proxy_profile=ens['aux_proxy_profile'];m.resource_aux_proxy_execution='metadata_only_no_fake_tp_demand'
 for tl in range(1,10):
  row=per[tl];r=m.p('reactor',tl);r['operationalTp']=int(row['reactor_undamaged_operational_tp']);r['degradedTp']=int(row['reactor_degraded_tp']);r['emergencyTp']=int(row['reactor_damaged_emergency_tp'])
  m.p('kinetic_main',tl)['firingTp']=int(row['K_weapon_tp']);low,std,ov=_energy_mode_tp(int(row['E_weapon_tp']));e=m.p('energy_main',tl);e['lowTp'],e['standardTp'],e['overloadTp']=low,std,ov;m.p('missile_delivery',tl)['launchTp']=int(row['M_weapon_tp'])
 if ens['weapon_space_pattern']=='Equal6':
  for tl in range(1,10):
   for key in ('kinetic_main','energy_main','missile_delivery'):m.p(key,tl)['space']=6
 mini=ens['miniaturization'];tl1={k:int(m.p(k,1)['space']) for k in ('reactor','stl','ftl','computer','sensor','shield')}
 freeze=('reactor','stl','ftl') if mini=='Selective_NoMajorMini' else ('reactor',) if mini=='Selective_PropulsionMini' else ('reactor','stl','ftl','computer','sensor','shield') if mini=='NoMini' else ()
 for key in freeze:
  for tl in range(1,10):m.p(key,tl)['space']=tl1[key]
 return m

def field_candidates()->list[dict[str,Any]]:
 out=[]
 for tl in (7,8,9):
  for i,(red,tp) in enumerate(itertools.product(FIELD_REDUCTIONS,FIELD_TP)):
   out.append({'candidate_id':f'FST159-{tl:02d}-{i:03d}','family':'FIELD_STABILIZER','kind':'field_stabilizer','tl':tl,'spen_reduction':red,'tp':tp,'space':1,'promotion_allowed':0})
 return out

def crystal_candidates()->list[dict[str,Any]]:
 out=[]
 for tl in (8,9):
  for i,(cap,res) in enumerate(itertools.product(CRYSTAL_CAP,CRYSTAL_RES)):
   out.append({'candidate_id':f'CRY159-{tl:02d}-{i:03d}','family':'CRYSTALLINE_ARMOR','kind':'crystalline_armor','tl':tl,'capacity_bonus':cap,'res_bonus_pp':res,'tp':0,'space':0,'promotion_allowed':0})
 return out

def _hardener_candidate(repo:Path,tl:int)->dict[str,Any]:
 p=aux_profile(repo,'shieldHardener',tl);return {'candidate_id':f'HDN159-COMP-TL{tl}','family':'SHIELD_HARDENER_COMPARATOR','kind':'shield_hardener','tl':tl,'def_bonus_pp':int(p['defBonusPp']),'tp':int(p['tp']),'space':int(p['space']),'promotion_allowed':0}

def _field_context(repo:Path,doc:dict[str,Any],src:dict[str,str])->bool:
 if int(src['tl']) not in (7,8,9) or src['side_a_weapon']!='E':return False
 m=_resource_matrix(repo,doc,src['resource_ensemble_id']);return bool(bind_scenario(m,src).variant.side_b.shield)
def _baseline_context(src:dict[str,str])->bool:return int(src['tl']) in (7,8,9)
def _crystal_context(src:dict[str,str])->bool:return int(src['tl']) in (8,9)

_W_REPO=None;_W_DOC=None;_W_CANDS=None;_W_BASE=None
def _init(repo,doc,cands):
 global _W_REPO,_W_DOC,_W_CANDS,_W_BASE;_W_REPO=Path(repo);_W_DOC=doc;_W_CANDS={c['candidate_id']:c for c in cands};_W_BASE={}
def _mat(src):
 rid=src['resource_ensemble_id']
 if rid not in _W_BASE:_W_BASE[rid]=_resource_matrix(_W_REPO,_W_DOC,rid)
 return _W_BASE[rid]
def _task(a):
 idx,src,cids,ident,seed,trials=a;m=_mat(src);v=bind_scenario(m,src).variant;cands=[_W_CANDS[x] for x in cids]
 if cands:
  v=_apply_package(m,v,cands)
  if v is None:return None
 r=_trial_row(m,v,src,seed+idx*1009,trials,ident)
 if len(cands)==1:r.update({k:v for k,v in cands[0].items() if k not in r})
 return r

def _run(tasks,cands,jobs):
 if jobs<=1:
  _init(str(_RUN_REPO),_RUN_DOC,cands);return [x for x in (_task(t) for t in tasks) if x]
 ctx=get_context('spawn');ch=max(1,min(12,len(tasks)//max(1,jobs*8)))
 with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx,initializer=_init,initargs=(str(_RUN_REPO),_RUN_DOC,cands)) as ex:return [x for x in ex.map(_task,tasks,chunksize=ch) if x]
_RUN_REPO=None;_RUN_DOC=None

def _run_rows(repo:Path,doc:dict[str,Any],contexts:list[dict[str,str]],packages:list[tuple[str,list[dict[str,Any]]]],out:Path,trials:int,jobs:int,seed_offset:int,mode:str):
 global _RUN_REPO,_RUN_DOC;_RUN_REPO=repo;_RUN_DOC=doc;cands=[];seen=set()
 for _,cs in packages:
  for c in cs:
   if c['candidate_id'] not in seen:seen.add(c['candidate_id']);cands.append(c)
 tasks=[];i=0;seed=int(doc['masterSeed'])+seed_offset
 for ident,cs in packages:
  tls={int(c['tl']) for c in cs} if cs else set()
  for src in contexts:
   tl=int(src['tl'])
   if tls and tl not in tls:continue
   cids=[c['candidate_id'] for c in cs if int(c['tl'])==tl] if cs else []
   if cs and not cids:continue
   tasks.append((i,src,cids,ident,seed,trials));i+=1
 rows=_run(tasks,cands,jobs);rows.sort(key=lambda r:(r['identity'],r['scenario_id']));_write_csv(out/'context_results.csv',rows)
 s={'mode':mode,'passed':not any(int(r['error_trials']) for r in rows),'packages':len(packages),'cells':len(rows),'trialsPerCell':trials,'combatTrials':len(rows)*trials,'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errors':sum(int(r['error_trials']) for r in rows)};_json_write(out/'summary.json',s);return s

def run_baseline(repo:Path,study:Path,out:Path,jobs=24):
 doc=load_json(study);ctx=[r for r in _manifest(repo,doc) if _baseline_context(r)];return _run_rows(repo,doc,ctx,[('BASELINE',[])],out,BASELINE_TRIALS,jobs,0,'baseline')

def run_field_screen(repo:Path,study:Path,out:Path,tl:int,jobs=24):
 doc=load_json(study);ctx=[r for r in _manifest(repo,doc) if int(r['tl'])==tl and r['side_a_weapon']=='E' and _field_context(repo,doc,r)];cs=[c for c in field_candidates() if c['tl']==tl];packages=[(c['candidate_id'],[c]) for c in cs];return _run_rows(repo,doc,ctx,packages,out,FIELD_SCREEN_TRIALS,jobs,100000+tl*1000,'field-screen')

def run_crystal_screen(repo:Path,study:Path,out:Path,tl:int,jobs=24):
 doc=load_json(study);ctx=[r for r in _manifest(repo,doc) if int(r['tl'])==tl];cs=[c for c in crystal_candidates() if c['tl']==tl];return _run_rows(repo,doc,ctx,[(c['candidate_id'],[c]) for c in cs],out,CRYSTAL_SCREEN_TRIALS,jobs,200000+tl*1000,'crystal-screen')

def _baseline_map(p:Path):return {r['scenario_id']:r for r in _read_csv(p)}
def _merge_screen(baseline:Path,batch_root:Path,out:Path,family:str):
 base=_baseline_map(baseline);rows=[];seen=set();audit=[]
 for p in sorted(batch_root.rglob('context_results.csv')):
  sm=json.loads((p.parent/'summary.json').read_text());n=0
  if sm.get('passed'):
   for r in _read_csv(p):
    k=(r['identity'],r['scenario_id'])
    if k not in seen:seen.add(k);rows.append(r);n+=1
  audit.append({'batch':str(p.parent.relative_to(batch_root)),'rows':n,'passed':int(bool(sm.get('passed')))})
 by=defaultdict(list);resp=[];summary=[]
 for r in rows:by[r['identity']].append(r)
 for cid,rs in by.items():
  ups=[];dims=defaultdict(list)
  for r in rs:
   u=float(r['defender_decisive_share'])-float(base[r['scenario_id']]['defender_decisive_share']);ups.append(u)
   for dim in ('tl','side_b_weapon','resource_ensemble_id','scenario_stratum'):dims[(dim,r[dim])].append(u)
  for (dim,lev),vals in sorted(dims.items()):resp.append({'candidate_id':cid,'family':family,'dimension':dim,'level':lev,'mean_uplift':statistics.mean(vals),'min_uplift':min(vals),'max_uplift':max(vals),'cells':len(vals)})
  c=next(c for c in (field_candidates() if family=='FIELD_STABILIZER' else crystal_candidates()) if c['candidate_id']==cid)
  summary.append({**c,'cells':len(rs),'trials':sum(int(r['trials']) for r in rs),'mean_uplift':statistics.mean(ups),'median_uplift':statistics.median(ups),'min_uplift':min(ups),'max_uplift':max(ups),'promotion_allowed':0})
 summary.sort(key=lambda r:(int(r['tl']),-float(r['mean_uplift']),r['candidate_id']));_write_csv(out/'batch_merge_audit.csv',audit);_write_csv(out/'candidate_summary.csv',summary);_write_csv(out/'candidate_response.csv',resp)
 s={'mode':family.lower()+'-screen-merged','passed':True,'candidates':len(summary),'cells':len(rows),'combatTrials':sum(int(r['trials']) for r in rows),'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errorTrials':sum(int(r['error_trials']) for r in rows)};_json_write(out/'summary.json',s);return s

def merge_field(baseline,batches,out):return _merge_screen(baseline,batches,out,'FIELD_STABILIZER')
def merge_crystal(baseline,batches,out):return _merge_screen(baseline,batches,out,'CRYSTALLINE_ARMOR')

def _pick_field(tl,red,tp=1):return next(c for c in field_candidates() if c['tl']==tl and c['spen_reduction']==red and c['tp']==tp)
def _pick_crystal(tl,cap,res):return next(c for c in crystal_candidates() if c['tl']==tl and c['capacity_bonus']==cap and c['res_bonus_pp']==res)
def field_deep_packages(repo:Path):
 seqs=[('FST_LOW',(8,10,12),1),('FST_CENTER',(12,14,16),1),('FST_HIGH',(16,18,20),1),('FST_MAX',(20,22,24),1),('FST_HIGH_PASSIVE',(16,18,20),0),('FST_HIGH_EXPENSIVE',(16,18,20),2)]
 out=[]
 for name,reds,tp in seqs:out.append((name,[_pick_field(t,r,tp) for t,r in zip((7,8,9),reds)]))
 out.append(('SHIELD_HARDENER_PROMOTED',[_hardener_candidate(repo,t) for t in (7,8,9)]));return out

def crystal_deep_packages():
 specs=[('CRY_CURRENT_BOUNDARY',[(8,8,15),(9,8,15)]),('CRY_RISE_A',[(8,8,15),(9,10,20)]),('CRY_RISE_B',[(8,10,20),(9,12,25)]),('CRY_RISE_C',[(8,12,25),(9,14,30)]),('CRY_HIGH_FLAT',[(8,14,30),(9,14,30)]),('CRY_MAX_FLAT',[(8,16,30),(9,16,30)])]
 return [(name,[_pick_crystal(*x) for x in sp]) for name,sp in specs]

def run_field_deep(repo,study,out,jobs=24):
 doc=load_json(study);ctx=[r for r in _manifest(repo,doc) if _field_context(repo,doc,r)];return _run_rows(repo,doc,ctx,field_deep_packages(repo),out,DEEP_TRIALS,jobs,300000,'field-deep')
def run_crystal_deep(repo,study,out,jobs=24):
 doc=load_json(study);ctx=[r for r in _manifest(repo,doc) if _crystal_context(r)];return _run_rows(repo,doc,ctx,crystal_deep_packages(),out,DEEP_TRIALS,jobs,400000,'crystal-deep')

def _merge_deep(baseline:Path,rows_path:Path,out:Path,mode:str):
 base=_baseline_map(baseline);rows=_read_csv(rows_path);by=defaultdict(list);resp=[];summary=[]
 for r in rows:by[r['identity']].append(r)
 for lid,rs in by.items():
  ups=[];dims=defaultdict(list)
  for r in rs:
   u=float(r['defender_decisive_share'])-float(base[r['scenario_id']]['defender_decisive_share']);ups.append(u)
   for dim in ('tl','side_b_weapon','resource_ensemble_id','scenario_stratum'):dims[(dim,r[dim])].append(u)
  for (dim,lev),vals in sorted(dims.items()):resp.append({'package_id':lid,'dimension':dim,'level':lev,'mean_uplift':statistics.mean(vals),'min_uplift':min(vals),'max_uplift':max(vals),'cells':len(vals)})
  summary.append({'package_id':lid,'cells':len(rs),'trials':sum(int(r['trials']) for r in rs),'mean_uplift':statistics.mean(ups),'median_uplift':statistics.median(ups),'min_uplift':min(ups),'max_uplift':max(ups)})
 _write_csv(out/'deep_summary.csv',summary);_write_csv(out/'deep_response.csv',resp);s={'mode':mode,'passed':True,'packages':len(summary),'cells':len(rows),'combatTrials':sum(int(r['trials']) for r in rows),'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errorTrials':sum(int(r['error_trials']) for r in rows)};_json_write(out/'summary.json',s);return s

def merge_field_deep(baseline,rows,out):return _merge_deep(baseline,rows,out,'field-deep-merged')
def merge_crystal_deep(baseline,rows,out):return _merge_deep(baseline,rows,out,'crystal-deep-merged')

def run_field_hardener_interactions(repo,study,out,jobs=24):
 doc=load_json(study);ctx=[r for r in _manifest(repo,doc) if _field_context(repo,doc,r)];packages=[]
 for red in (16,20,24):
  for tl in (7,8,9):
   pass
  packages.append((f'FST{red}_PLUS_HARDENER',[_pick_field(t,red,1) for t in (7,8,9)]+[_hardener_candidate(repo,t) for t in (7,8,9)]))
 # _run_rows assumes package candidate list may contain multiple TL-specific definitions; application must choose TL only.
 # Expand to per-TL package IDs to avoid applying off-TL rows simultaneously.
 expanded=[]
 for red in (16,20,24):
  for tl in (7,8,9):expanded.append((f'FST{red}_PLUS_HARDENER_TL{tl}',[_pick_field(tl,red,1),_hardener_candidate(repo,tl)]))
 return _run_rows(repo,doc,ctx,expanded,out,INTERACTION_TRIALS,jobs,500000,'field-hardener-interaction')

def _target(kind:str,amount:int=1):return {'kind':kind,'remaining':amount}
def _workload(name:str):
 if name=='SINGLE_HULL':return [_target('hull',4)],{}
 if name=='TWO_DEGRADED':return [_target('degraded'),_target('degraded')],{}
 if name=='DISABLED_PLUS_HULL':return [_target('disabled'),_target('hull',4)],{}
 if name=='THREE_MIXED':return [_target('disabled'),_target('degraded'),_target('hull',4)],{}
 if name=='HEAVY_FOUR':return [_target('disabled'),_target('disabled'),_target('degraded'),_target('hull',6)],{}
 if name=='SUSTAINED_ATTRITION':return [_target('disabled'),_target('degraded'),_target('hull',4)],{2:'degraded',4:'degraded',6:'disabled'}
 raise ValueError(name)
def _priority(t):return {'disabled':0,'degraded':1,'hull':2}[t['kind']]
def _chance(dc,t):return int(dc['disabledToDegradedChancePp'] if t['kind']=='disabled' else dc['degradedToOperationalChancePp'] if t['kind']=='degraded' else dc['hullRepairChancePp'])
def _success_apply(dc,t):
 if t['kind']=='disabled':t['kind']='degraded';return 1,0
 if t['kind']=='degraded':t['remaining']=0;return 1,0
 amt=min(int(t['remaining']),int(dc['hullRestoredPerSuccessfulKit']));t['remaining']-=amt;return 0,amt
def _active(targets):return [t for t in targets if int(t.get('remaining',1))>0]
def _micro_one(dc,extra_kits,workload,tp_cap,seed):
 rng=random.Random(seed);targets,arrivals=_workload(workload);targets=[dict(x) for x in targets];kits=int(dc['preparedRepairKits'])+extra_kits;attempts=succ=drone_attempts=component_steps=hull_restored=0;exhausted=False;fully_clear=0
 for turn in range(1,9):
  if turn in arrivals:targets.append(_target(arrivals[turn]))
  act=sorted(_active(targets),key=_priority)
  actions=min(2,int(tp_cap),kits,len(act))
  # distinct-target rule: first two entries only; never retry the same target in this phase.
  chosen=act[:actions]
  for j,t in enumerate(chosen):
   kits-=1;attempts+=1
   if j==1:drone_attempts+=1
   if rng.randint(1,100)<=_chance(dc,t):
    succ+=1;cs,hr=_success_apply(dc,t);component_steps+=cs;hull_restored+=hr
  if kits==0 and _active(targets):exhausted=True
  if not _active(targets) and all(k<=turn for k in arrivals):fully_clear=turn;break
 return {'attempts':attempts,'successes':succ,'drone_attempts':drone_attempts,'component_steps_repaired':component_steps,'hull_restored':hull_restored,'kits_remaining':kits,'kit_exhausted':int(exhausted),'unresolved_targets':len(_active(targets)),'fully_clear_turn':fully_clear}

def run_repair_drone_micro(repo:Path,out:Path,trials=DRONE_MICRO_TRIALS):
 m=load_research_execution_baseline_pf3(repo);workloads=('SINGLE_HULL','TWO_DEGRADED','DISABLED_PLUS_HULL','THREE_MIXED','HEAVY_FOUR','SUSTAINED_ATTRITION');rows=[];summary=[];seed0=159771
 for tl in range(2,10):
  dc=m.p('damage_control',tl);base=int(dc['preparedRepairKits'])
  for extra in range(0,base+1):
   for tp_cap in (1,2):
    for workload in workloads:
     vals=[_micro_one(dc,extra,workload,tp_cap,seed0+tl*100000+extra*10000+tp_cap*1000+i) for i in range(trials)]
     r={'tl':tl,'default_kits':base,'extra_kits':extra,'total_kits':base+extra,'total_kit_multiplier':(base+extra)/base,'available_damage_control_tp':tp_cap,'workload':workload,'trials':trials,
        'mean_attempts':statistics.mean(v['attempts'] for v in vals),'mean_drone_attempts':statistics.mean(v['drone_attempts'] for v in vals),'mean_successes':statistics.mean(v['successes'] for v in vals),'mean_component_steps_repaired':statistics.mean(v['component_steps_repaired'] for v in vals),'mean_hull_restored':statistics.mean(v['hull_restored'] for v in vals),'kit_exhaustion_rate':statistics.mean(v['kit_exhausted'] for v in vals),'mean_unresolved_targets':statistics.mean(v['unresolved_targets'] for v in vals),'clear_rate':statistics.mean(v['fully_clear_turn']>0 for v in vals),'mean_clear_turn':statistics.mean([v['fully_clear_turn'] for v in vals if v['fully_clear_turn']>0]) if any(v['fully_clear_turn']>0 for v in vals) else 0.0}
     rows.append(r)
 # aggregate each TL/extra across workloads at TP2; TP1 is explicit constrained control
 for tl in range(2,10):
  for extra in range(0,int(m.p('damage_control',tl)['preparedRepairKits'])+1):
   rr=[r for r in rows if r['tl']==tl and r['extra_kits']==extra and r['available_damage_control_tp']==2]
   summary.append({'tl':tl,'default_kits':int(m.p('damage_control',tl)['preparedRepairKits']),'extra_kits':extra,'total_kits':int(m.p('damage_control',tl)['preparedRepairKits'])+extra,'mean_drone_attempts':statistics.mean(r['mean_drone_attempts'] for r in rr),'mean_successes':statistics.mean(r['mean_successes'] for r in rr),'mean_kit_exhaustion_rate':statistics.mean(r['kit_exhaustion_rate'] for r in rr),'mean_unresolved_targets':statistics.mean(r['mean_unresolved_targets'] for r in rr),'mean_clear_rate':statistics.mean(r['clear_rate'] for r in rr)})
 _write_csv(out/'repair_drone_micro_response.csv',rows);_write_csv(out/'repair_drone_kit_summary.csv',summary);s={'mode':'repair-drone-micro','passed':True,'candidateTlPoints':sum(int(m.p('damage_control',tl)['preparedRepairKits'])+1 for tl in range(2,10)),'workloads':len(workloads),'tpControls':2,'trialsPerCell':trials,'microTrials':len(rows)*trials,'sameTargetRerollAllowed':False,'extraKitMaximumEqualsDefault':True};_json_write(out/'summary.json',s);return s

def plan(repo:Path,study:Path,out:Path):
 doc=load_json(study);manifest=_manifest(repo,doc);base=[r for r in manifest if _baseline_context(r)];fctx=[r for r in manifest if _field_context(repo,doc,r)];cctx=[r for r in manifest if _crystal_context(r)]
 field=field_candidates();crys=crystal_candidates();field_cells=sum(sum(1 for r in fctx if int(r['tl'])==c['tl']) for c in field);crys_cells=sum(sum(1 for r in cctx if int(r['tl'])==c['tl']) for c in crys)
 fd_cells=sum(len([r for r in fctx if int(r['tl']) in {int(c['tl']) for c in cs}]) for _,cs in field_deep_packages(repo));cd_cells=sum(len([r for r in cctx if int(r['tl']) in {int(c['tl']) for c in cs}]) for _,cs in crystal_deep_packages());inter_cells=3*len(fctx)
 combat=len(base)*BASELINE_TRIALS+field_cells*FIELD_SCREEN_TRIALS+crys_cells*CRYSTAL_SCREEN_TRIALS+fd_cells*DEEP_TRIALS+cd_cells*DEEP_TRIALS+inter_cells*INTERACTION_TRIALS
 m=load_research_execution_baseline_pf3(repo);micro_points=sum(int(m.p('damage_control',tl)['preparedRepairKits'])+1 for tl in range(2,10));micro_cells=micro_points*6*2;micro_trials=micro_cells*DRONE_MICRO_TRIALS
 s={'mode':'plan','passed':True,'baselineContexts':len(base),'fieldCandidateTlPoints':len(field),'fieldContexts':len(fctx),'fieldScreenCells':field_cells,'crystallineCandidateTlPoints':len(crys),'crystallineContexts':len(cctx),'crystallineScreenCells':crys_cells,'fieldDeepPackages':len(field_deep_packages(repo)),'fieldDeepCells':fd_cells,'crystallineDeepPackages':len(crystal_deep_packages()),'crystallineDeepCells':cd_cells,'fieldHardenerInteractionPackages':9,'fieldHardenerInteractionCells':inter_cells,'substantiveCombatTrials':combat,'repairDroneCandidateTlPoints':micro_points,'repairDroneMicroCells':micro_cells,'repairDroneMicroTrials':micro_trials,'automaticPostStudyPromotion':False,'finalReactorTpTuning':False};_json_write(out/'summary.json',s);_write_csv(out/'field_stabilizer_candidate_ledger.csv',field);_write_csv(out/'crystalline_headroom_candidate_ledger.csv',crys);return s

def smoke(repo:Path,study:Path,out:Path):
 doc=load_json(study);m=load_research_execution_baseline_pf3(repo);rows=[]
 # Field Stabilizer one real trial
 src=next(r for r in _manifest(repo,doc) if int(r['tl'])==9 and r['side_a_weapon']=='E' and _field_context(repo,doc,r));c=_pick_field(9,20,1);v=bind_scenario(_resource_matrix(repo,doc,src['resource_ensemble_id']),src).variant;mm=_resource_matrix(repo,doc,src['resource_ensemble_id']);v=_apply_candidate(mm,v,c);rr=_trial_row(mm,v,src,int(doc['masterSeed']),1,'FST_SMOKE');rows.append({'probe':'field_stabilizer','passed':int(rr['error_trials']==0 and rr['turn_cap_sentinels']==0)})
 # Crystalline one real trial
 src=next(r for r in _manifest(repo,doc) if int(r['tl'])==9);c=_pick_crystal(9,12,25);mm=_resource_matrix(repo,doc,src['resource_ensemble_id']);v=_apply_candidate(mm,bind_scenario(mm,src).variant,c);rr=_trial_row(mm,v,src,int(doc['masterSeed'])+1,1,'CRY_SMOKE');rows.append({'probe':'crystalline_headroom','passed':int(rr['error_trials']==0 and rr['turn_cap_sentinels']==0)})
 # Drone semantics microprobe: one target => no second action; two targets => second action possible with TP2.
 dc=m.p('damage_control',4);a=_micro_one(dc,4,'SINGLE_HULL',2,123);b=_micro_one(dc,4,'TWO_DEGRADED',2,123);rows.append({'probe':'repair_drone_distinct_target','passed':int(a['drone_attempts']==0 and b['drone_attempts']>0)})
 _write_csv(out/'aux_closure_smoke.csv',rows);s={'mode':'smoke','passed':all(int(r['passed']) for r in rows),'probes':len(rows),'combatTrials':2,'microProbes':1};_json_write(out/'summary.json',s);return s

def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--study',required=True);sp=ap.add_subparsers(dest='cmd',required=True)
 for n in ('plan','smoke','baseline','field-deep','crystal-deep','repair-drone-micro'):
  p=sp.add_parser(n);p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=24)
 for n in ('field-screen','crystal-screen'):
  p=sp.add_parser(n);p.add_argument('--out',required=True);p.add_argument('--tl',type=int,required=True);p.add_argument('--jobs',type=int,default=24)
 p=sp.add_parser('merge-field');p.add_argument('--baseline',required=True);p.add_argument('--batches',required=True);p.add_argument('--out',required=True)
 p=sp.add_parser('merge-crystal');p.add_argument('--baseline',required=True);p.add_argument('--batches',required=True);p.add_argument('--out',required=True)
 p=sp.add_parser('merge-field-deep');p.add_argument('--baseline',required=True);p.add_argument('--rows',required=True);p.add_argument('--out',required=True)
 p=sp.add_parser('merge-crystal-deep');p.add_argument('--baseline',required=True);p.add_argument('--rows',required=True);p.add_argument('--out',required=True)
 p=sp.add_parser('field-hardener-interactions');p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=24)
 a=ap.parse_args(argv);repo=Path(a.repo);study=Path(a.study);out=Path(getattr(a,'out','.') or '.')
 if a.cmd=='plan':r=plan(repo,study,out)
 elif a.cmd=='smoke':r=smoke(repo,study,out)
 elif a.cmd=='baseline':r=run_baseline(repo,study,out,a.jobs)
 elif a.cmd=='field-screen':r=run_field_screen(repo,study,out,a.tl,a.jobs)
 elif a.cmd=='crystal-screen':r=run_crystal_screen(repo,study,out,a.tl,a.jobs)
 elif a.cmd=='merge-field':r=merge_field(Path(a.baseline),Path(a.batches),out)
 elif a.cmd=='merge-crystal':r=merge_crystal(Path(a.baseline),Path(a.batches),out)
 elif a.cmd=='field-deep':
  r=run_field_deep(repo,study,out,a.jobs);merge_field_deep(out.parent/'baseline'/'context_results.csv',out/'context_results.csv',out/'merged')
 elif a.cmd=='crystal-deep':
  r=run_crystal_deep(repo,study,out,a.jobs);merge_crystal_deep(out.parent/'baseline'/'context_results.csv',out/'context_results.csv',out/'merged')
 elif a.cmd=='field-hardener-interactions':r=run_field_hardener_interactions(repo,study,out,a.jobs)
 elif a.cmd=='repair-drone-micro':r=run_repair_drone_micro(repo,out)
 else:raise SystemExit(2)
 print(json.dumps(r,indent=2));return 0 if r.get('passed',False) else 1
if __name__=='__main__':raise SystemExit(main())
