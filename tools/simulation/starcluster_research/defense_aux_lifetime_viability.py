from __future__ import annotations
import argparse,csv,hashlib,itertools,json,math,statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any
from .canonical_combat import run_trial_full_map
from .ecology import CandidateMatrix,EcologyBuild,EcologyVariant
from .research_execution_baseline_pf2 import BASELINE_RELATIVE,load_research_execution_baseline_pf2
from .stage_a_integration_analysis import bind_scenario,_energy_mode_tp
from .study import load_json

SCHEMA='star-cluster-cp158-defense-aux-lifetime-v0.1'
SWEEP_FAMILIES=('SHIELD_HARDENER','SHIELD_BATTERY','SHIELD_BOOSTER','ABLATIVE_ARMOR','CRYSTALLINE_ARMOR','ENERGIZED_ARMOR','FIELD_STABILIZER','REPAIR_DRONE')
AUDIT_FAMILIES=('KINETIC_MAGAZINE','MISSILE_MAGAZINE')
BASELINE_TRIALS=50; SCREEN_TRIALS=25; DEEP_TRIALS=100; PAIR_TRIALS=25
LADDERS_PER_FAMILY=8

def _sha(p:Path)->str:
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def _read_csv(p:Path)->list[dict[str,str]]:
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def _write_csv(p:Path,rows:list[dict[str,Any]]):
 p.parent.mkdir(parents=True,exist_ok=True)
 if not rows: p.write_text('',encoding='utf-8'); return
 fields=[]
 for r in rows:
  for k in r:
   if k not in fields: fields.append(k)
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(rows)
def _resource_rows(repo:Path,doc:dict[str,Any]): return _read_csv(repo/doc['resourceEnsemble']),_read_csv(repo/doc['resourceEnsembleTl'])
def _manifest(repo:Path,doc:dict[str,Any])->list[dict[str,str]]: return _read_csv(repo/doc['stageAExperimentManifest'])

def _resource_matrix(repo:Path,doc:dict[str,Any],ensemble_id:str)->CandidateMatrix:
 m=load_research_execution_baseline_pf2(repo); ens_rows,tl_rows=_resource_rows(repo,doc); ens=next(r for r in ens_rows if r['ensemble_id']==ensemble_id); per={int(r['tl']):r for r in tl_rows if r['ensemble_id']==ensemble_id}
 m.resource_ensemble_id=ensemble_id; m.resource_ensemble_role=ens['ensemble_role']; m.resource_aux_proxy_profile=ens['aux_proxy_profile']; m.resource_aux_proxy_execution='metadata_only_no_fake_tp_demand'
 for tl in range(1,10):
  row=per[tl]; r=m.p('reactor',tl); r['operationalTp']=int(row['reactor_undamaged_operational_tp']);r['degradedTp']=int(row['reactor_degraded_tp']);r['emergencyTp']=int(row['reactor_damaged_emergency_tp'])
  m.p('kinetic_main',tl)['firingTp']=int(row['K_weapon_tp']); low,std,ov=_energy_mode_tp(int(row['E_weapon_tp'])); e=m.p('energy_main',tl);e['lowTp'],e['standardTp'],e['overloadTp']=low,std,ov; m.p('missile_delivery',tl)['launchTp']=int(row['M_weapon_tp'])
 if ens['weapon_space_pattern']=='Equal6':
  for tl in range(1,10):
   for key in ('kinetic_main','energy_main','missile_delivery'):m.p(key,tl)['space']=6
 mini=ens['miniaturization']; tl1={k:int(m.p(k,1)['space']) for k in ('reactor','stl','ftl','computer','sensor','shield')}
 freeze=('reactor','stl','ftl') if mini=='Selective_NoMajorMini' else ('reactor',) if mini=='Selective_PropulsionMini' else ('reactor','stl','ftl','computer','sensor','shield') if mini=='NoMini' else ()
 for key in freeze:
  for tl in range(1,10):m.p(key,tl)['space']=tl1[key]
 return m

def _candidate(fam:str,tl:int,idx:int,**kw)->dict[str,Any]:
 pref={'SHIELD_HARDENER':'HDN','SHIELD_BATTERY':'BAT','SHIELD_BOOSTER':'BST','ABLATIVE_ARMOR':'ABL','CRYSTALLINE_ARMOR':'CRY','ENERGIZED_ARMOR':'ENA','FIELD_STABILIZER':'FST','REPAIR_DRONE':'DRN','KINETIC_MAGAZINE':'KMG','MISSILE_MAGAZINE':'MMG'}[fam]
 return {'candidate_id':f'{pref}158-{tl:02d}-{idx:03d}','family':fam,'tl':tl,'candidate_index':idx,'promotion_allowed':0,**kw}
def candidate_ledger()->list[dict[str,Any]]:
 out=[]
 # broad bounds deliberately extend beyond historical seeds; final promotion is forbidden here.
 for tl in range(1,10):
  i=0
  if tl>=3:
   for bonus,tp in itertools.product((5,10,15,20),(1,2)): out.append(_candidate('SHIELD_HARDENER',tl,i,kind='shield_hardener',space=1,def_bonus_pp=bonus,tp=tp));i+=1
  i=0
  for restore,charges,space in itertools.product((2,4,6,8),(1,2,3),(1,2)): out.append(_candidate('SHIELD_BATTERY',tl,i,kind='shield_battery',space=space,restore=restore,charges=charges,trigger_fraction=.5,tp=0));i+=1
  i=0
  if tl>=2:
   for bonus,space in itertools.product((2,4,6,8),(1,2)): out.append(_candidate('SHIELD_BOOSTER',tl,i,kind='shield_booster',space=space,capacity_bonus=bonus,tp=0));i+=1
  i=0
  for ai in (2,4,6,8,10):out.append(_candidate('ABLATIVE_ARMOR',tl,i,kind='ablative_armor',space=1,ablative_integrity=ai,tp=0));i+=1
  i=0
  if tl>=6:
   for cap,res in itertools.product((2,4,6,8),(0,5,10,15)):out.append(_candidate('CRYSTALLINE_ARMOR',tl,i,kind='crystalline_armor',space=0,capacity_bonus=cap,res_bonus_pp=res,tp=0));i+=1
  i=0
  if tl>=5:
   for res,tp,space in itertools.product((5,10,15,20),(1,2,3),(1,2)):out.append(_candidate('ENERGIZED_ARMOR',tl,i,kind='energized_armor',space=space,res_bonus_pp=res,tp=tp));i+=1
  i=0
  if tl>=7:
   for red,tp,space in itertools.product((1,2,3,4),(1,2),(1,2)):out.append(_candidate('FIELD_STABILIZER',tl,i,kind='field_stabilizer',space=space,spen_reduction=red,tp=tp));i+=1
  i=0
  if 4<=tl<=6:
   for chance,kits,space in itertools.product((5,10,15,20),(0,1,2),(1,2)):out.append(_candidate('REPAIR_DRONE',tl,i,kind='repair_drone',space=space,chance_bonus_pp=chance,extra_repair_kits=kits,tp=0));i+=1
  out.append(_candidate('KINETIC_MAGAZINE',tl,0,kind='kinetic_magazine',space=1,ammo_bonus=25,tp=0,audit_only=1))
  out.append(_candidate('MISSILE_MAGAZINE',tl,0,kind='missile_magazine',space=1,ammo_bonus=25,tp=0,audit_only=1))
 return out

def _relevant(c:dict[str,Any],b:EcologyBuild)->bool:
 fam=c['family']
 if fam.startswith('SHIELD_') or fam=='FIELD_STABILIZER': return b.shield
 if fam=='KINETIC_MAGAZINE': return b.weapon_family=='Kinetic'
 if fam=='MISSILE_MAGAZINE': return b.weapon_family=='Missile'
 return True

def _apply_candidate(m:CandidateMatrix,v:EcologyVariant,c:dict[str,Any])->EcologyVariant|None:
 b=v.side_b
 if not _relevant(c,b):return None
 extra=int(c.get('space',0)); hardener=b.shield_hardener
 if c['family']=='SHIELD_HARDENER' and hardener:extra=0
 if b.mission_aux_space<extra:return None
 if c['family']=='SHIELD_HARDENER': hardener=True
 aux=tuple(b.auxiliary_profiles)+(c['candidate_id'],); m.cp158_aux_profiles=dict(getattr(m,'cp158_aux_profiles',{}));m.cp158_aux_profiles[c['candidate_id']]=dict(c)
 nb=replace(b,shield_hardener=hardener,combat_space=b.combat_space+extra,mission_aux_space=b.mission_aux_space-extra,auxiliary_profiles=aux)
 return replace(v,side_b=nb,id=v.id+'__'+c['candidate_id'])

def _apply_package(m:CandidateMatrix,v:EcologyVariant,cands:list[dict[str,Any]])->EcologyVariant|None:
 cur=v
 for c in cands:
  nxt=_apply_candidate(m,cur,c)
  if nxt is None:return None
  cur=nxt
 return cur

def _bind(repo:Path,doc:dict[str,Any],src:dict[str,str],cands:list[dict[str,Any]]|None=None):
 m=_resource_matrix(repo,doc,src['resource_ensemble_id']); bound=bind_scenario(m,src); v=bound.variant
 if cands:v=_apply_package(m,v,cands)
 return m,v

def _trial_row(m:CandidateMatrix,v:EcologyVariant,src:dict[str,str],seed:int,trials:int,ident:str)->dict[str,Any]:
 aw=bw=dr=caps=err=turns=0;sums=defaultdict(float)
 fields=('power_spent_total','power_shield_hardener','power_aux_energized_armor','power_aux_field_stabilizer','aux_shield_battery_discharges','aux_shield_battery_restored','aux_ablative_absorbed','aux_energized_active_turns','aux_field_stabilizer_active_turns','aux_damage_control_bonus_attempts','damage_control_successes','shield_absorbed','armor_resisted_damage','hull_damage')
 for i in range(trials):
  r=run_trial_full_map(m,v,seed,i,combat_doctrine='cp147_tactical_utility');err+=bool(r.error);caps+=r.termination_cause=='TURN_CAP_SENTINEL';turns+=r.turns
  if r.winner=='A':aw+=1
  elif r.winner=='B':bw+=1
  else:dr+=1
  for f in fields:sums[f]+=float(getattr(r.side_b,f,0))
 out={'identity':ident,**src,'trials':trials,'a_wins':aw,'b_wins':bw,'draws':dr,'turn_cap_sentinels':caps,'error_trials':err,'mean_turns':turns/max(1,trials),'defender_decisive_share':bw/max(1,aw+bw)}
 for f,x in sums.items():out['mean_b_'+f]=x/max(1,trials)
 return out

# Worker state
_W_REPO=_W_DOC=_W_CANDS=_W_BASE=None
def _init(repo,doc,cands):
 global _W_REPO,_W_DOC,_W_CANDS,_W_BASE;_W_REPO=Path(repo);_W_DOC=doc;_W_CANDS={c['candidate_id']:c for c in cands};_W_BASE={}
def _worker_bind(src,cands):
 global _W_BASE
 rid=src['resource_ensemble_id']
 if rid not in _W_BASE:_W_BASE[rid]=_resource_matrix(_W_REPO,_W_DOC,rid)
 m=_W_BASE[rid];v=bind_scenario(m,src).variant
 if cands:v=_apply_package(m,v,cands)
 return m,v
def _screen_task(a):
 idx,src,cid,seed,trials=a;c=_W_CANDS[cid];m,v=_worker_bind(src,[c]);
 if v is None:return None
 r=_trial_row(m,v,src,seed+idx*1009,trials,cid);r.update({k:v for k,v in c.items() if k not in r});return r

def _run_tasks(tasks,initargs,jobs,fn):
 if not tasks:return []
 if jobs<=1:
  _init(*initargs);return [x for x in (fn(t) for t in tasks) if x is not None]
 ctx=get_context('spawn');ch=max(1,min(16,len(tasks)//max(1,jobs*8)))
 with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx,initializer=_init,initargs=initargs) as ex:return [x for x in ex.map(fn,tasks,chunksize=ch) if x is not None]

def _baseline_task(a):
 idx,src,seed,trials=a;m,v=_worker_bind(src,[]);return _trial_row(m,v,src,seed+idx*1009,trials,'BASELINE')

def run_baseline(repo:Path,study:Path,out:Path,jobs=24,trials=BASELINE_TRIALS):
 doc=load_json(study);rows=_manifest(repo,doc);tasks=[(i,src,int(doc['masterSeed']),trials) for i,src in enumerate(rows)]
 if jobs<=1:
  _init(str(repo),doc,[]);res=[_baseline_task(t) for t in tasks]
 else:
  ctx=get_context('spawn');ch=max(1,min(16,len(tasks)//max(1,jobs*8)))
  with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctx,initializer=_init,initargs=(str(repo),doc,[])) as ex:res=list(ex.map(_baseline_task,tasks,chunksize=ch))
 _write_csv(out/'aux_baseline_context_results.csv',res);s={'mode':'baseline','passed':not any(int(r['error_trials']) for r in res),'cells':len(res),'trialsPerCell':trials,'combatTrials':len(res)*trials,'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in res),'errors':sum(int(r['error_trials']) for r in res)};out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def run_screen_batch(repo:Path,study:Path,out:Path,family:str,tl:int,start=0,end=None,jobs=24,trials=SCREEN_TRIALS):
 doc=load_json(study);allc=[c for c in candidate_ledger() if c['family']==family and int(c['tl'])==tl];end=len(allc) if end is None else min(end,len(allc));cands=allc[start:end];ctx=[r for r in _manifest(repo,doc) if int(r['tl'])==tl];tasks=[];i=0
 for c in cands:
  for src in ctx:tasks.append((i,src,c['candidate_id'],int(doc['masterSeed']),trials));i+=1
 res=_run_tasks(tasks,(str(repo),doc,cands),jobs,_screen_task);res.sort(key=lambda r:(r['candidate_id'],r['scenario_id']));_write_csv(out/'aux_candidate_context_results.csv',res)
 s={'mode':'screen-batch','family':family,'tl':tl,'candidateStart':start,'candidateEnd':end,'passed':not any(int(r['error_trials']) for r in res),'candidates':len(cands),'cells':len(res),'trialsPerCell':trials,'combatTrials':len(res)*trials,'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in res),'errors':sum(int(r['error_trials']) for r in res)};out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def merge_screen(repo:Path,study:Path,baseline:Path,batches:Path,out:Path):
 base={r['scenario_id']:r for r in _read_csv(baseline)};rows=[];seen=set();audit=[]
 for d in sorted(x for x in batches.rglob('*') if x.is_dir()):
  sp=d/'summary.json';rp=d/'aux_candidate_context_results.csv'
  if not sp.exists() or not rp.exists():continue
  sm=json.loads(sp.read_text());ok=sm.get('passed') and sm.get('mode')=='screen-batch';n=0
  if ok:
   for r in _read_csv(rp):
    k=(r['candidate_id'],r['scenario_id'])
    if k in seen:continue
    seen.add(k);rows.append(r);n+=1
  audit.append({'batch':str(d.relative_to(batches)),'rows':n,'passed':int(bool(ok))})
 groups=defaultdict(list)
 for r in rows:groups[r['candidate_id']].append(r)
 summary=[];resp=[]
 for cid,rs in groups.items():
  c=next(x for x in candidate_ledger() if x['candidate_id']==cid);ups=[];by=defaultdict(list);n=aw=bw=dr=0
  for r in rs:
   b=base[r['scenario_id']];u=float(r['defender_decisive_share'])-float(b['defender_decisive_share']);ups.append(u);n+=int(r['trials']);aw+=int(r['a_wins']);bw+=int(r['b_wins']);dr+=int(r['draws'])
   for dim in ('side_a_weapon','side_b_weapon','resource_ensemble_id','scenario_stratum'):by[(dim,r[dim])].append(u)
  for (dim,lev),vals in sorted(by.items()):resp.append({'candidate_id':cid,'family':c['family'],'tl':c['tl'],'dimension':dim,'level':lev,'mean_uplift':statistics.mean(vals),'min_uplift':min(vals),'max_uplift':max(vals),'cells':len(vals)})
  cost=int(c.get('space',0))*10+int(c.get('tp',0))*3;mean=statistics.mean(ups);summary.append({**c,'cells':len(rs),'trials':n,'mean_uplift':mean,'median_uplift':statistics.median(ups),'p10_uplift':sorted(ups)[max(0,int(.1*(len(ups)-1)))],'p90_uplift':sorted(ups)[min(len(ups)-1,int(.9*(len(ups)-1)))],'min_uplift':min(ups),'max_uplift':max(ups),'resource_cost_index':cost,'uplift_per_cost':mean/max(1,cost),'defender_decisive_share':bw/max(1,aw+bw),'promotion_allowed':0})
 summary.sort(key=lambda r:(r['family'],int(r['tl']),-float(r['mean_uplift']),int(r['resource_cost_index']),r['candidate_id']));_write_csv(out/'batch_merge_audit.csv',audit);_write_csv(out/'aux_candidate_summary.csv',summary);_write_csv(out/'aux_candidate_response.csv',resp)
 s={'mode':'screen-merged','passed':True,'candidates':len(summary),'cells':len(rows),'combatTrials':sum(int(r['trials']) for r in rows),'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errorTrials':sum(int(r['error_trials']) for r in rows)};out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def _trajectory(tls:list[int], levels:list[dict[str,Any]], seq:list[int])->dict[int,dict[str,Any]]:
 out={};n=len(tls);k=len(seq)
 for i,tl in enumerate(tls):out[tl]=levels[seq[min(k-1,(i*k)//max(1,n))]]
 return out

def _flat(tls:list[int], spec:dict[str,Any])->dict[int,dict[str,Any]]:return {tl:spec for tl in tls}

def representative_designs()->dict[str,list[tuple[str,dict[int,dict[str,Any]]]]]:
 # Eight architecture-stratified trajectories per family.  Four flat levels map
 # the response envelope; resource-stress and rising trajectories exercise
 # lifecycle maturation without selecting on a global win-rate objective.
 defs={}
 def add(fam,tls,levels,stress=None):
  ds=[('ECONOMY_FLAT',_flat(tls,levels[0])),('CENTER_FLAT',_flat(tls,levels[1])),('HIGH_FLAT',_flat(tls,levels[2])),('MAX_FLAT',_flat(tls,levels[3]))]
  if stress is not None:ds.append(('RESOURCE_STRESS',_flat(tls,stress)))
  else:ds.append(('RISING_LOW_HIGH',_trajectory(tls,levels,[0,1,2])))
  ds += [('RISING_LOW_CENTER',_trajectory(tls,levels,[0,1])),('RISING_CENTER_HIGH',_trajectory(tls,levels,[1,2])),('RISING_FULL',_trajectory(tls,levels,[0,1,2,3]))]
  defs[fam]=ds
 add('SHIELD_HARDENER',list(range(3,10)),[{'def_bonus_pp':5,'tp':1,'space':1},{'def_bonus_pp':10,'tp':1,'space':1},{'def_bonus_pp':15,'tp':1,'space':1},{'def_bonus_pp':20,'tp':1,'space':1}],{'def_bonus_pp':20,'tp':2,'space':1})
 add('SHIELD_BATTERY',list(range(1,10)),[{'restore':2,'charges':1,'space':1},{'restore':4,'charges':2,'space':1},{'restore':6,'charges':3,'space':1},{'restore':8,'charges':3,'space':1}],{'restore':8,'charges':3,'space':2})
 add('SHIELD_BOOSTER',list(range(2,10)),[{'capacity_bonus':2,'space':1},{'capacity_bonus':4,'space':1},{'capacity_bonus':6,'space':1},{'capacity_bonus':8,'space':1}],{'capacity_bonus':8,'space':2})
 add('ABLATIVE_ARMOR',list(range(1,10)),[{'ablative_integrity':2,'space':1},{'ablative_integrity':4,'space':1},{'ablative_integrity':8,'space':1},{'ablative_integrity':10,'space':1}])
 add('CRYSTALLINE_ARMOR',list(range(6,10)),[{'capacity_bonus':2,'res_bonus_pp':0,'space':0},{'capacity_bonus':4,'res_bonus_pp':5,'space':0},{'capacity_bonus':6,'res_bonus_pp':10,'space':0},{'capacity_bonus':8,'res_bonus_pp':15,'space':0}])
 add('ENERGIZED_ARMOR',list(range(5,10)),[{'res_bonus_pp':5,'tp':1,'space':1},{'res_bonus_pp':10,'tp':1,'space':1},{'res_bonus_pp':15,'tp':1,'space':1},{'res_bonus_pp':20,'tp':1,'space':1}],{'res_bonus_pp':20,'tp':3,'space':2})
 add('FIELD_STABILIZER',list(range(7,10)),[{'spen_reduction':1,'tp':1,'space':1},{'spen_reduction':2,'tp':1,'space':1},{'spen_reduction':3,'tp':1,'space':1},{'spen_reduction':4,'tp':1,'space':1}],{'spen_reduction':4,'tp':2,'space':2})
 add('REPAIR_DRONE',list(range(4,7)),[{'chance_bonus_pp':5,'extra_repair_kits':0,'space':1},{'chance_bonus_pp':10,'extra_repair_kits':1,'space':1},{'chance_bonus_pp':15,'extra_repair_kits':1,'space':1},{'chance_bonus_pp':20,'extra_repair_kits':2,'space':1}],{'chance_bonus_pp':20,'extra_repair_kits':2,'space':2})
 return defs

def _design_matches(c:dict[str,Any],spec_by_tl:dict[int,dict[str,Any]])->bool:
 spec=spec_by_tl.get(int(c['tl']));return spec is not None and all(str(c.get(k))==str(v) for k,v in spec.items())

def _matches(c:dict[str,Any],spec:dict[str,Any])->bool:
 return all(str(c.get(k))==str(v) for k,v in spec.items())
def synthesize(screen:Path,out:Path):
 # Architecture-stratified deep confirmation is intentionally not selected by a
 # global win-rate objective. It samples four technology-valid trajectories from
 # the broad measured surface; final promotion remains an offline Pareto decision.
 rows=_read_csv(screen); byid={r['candidate_id']:r for r in rows}; allc=candidate_ledger(); ladders=[]
 for fam,designs in representative_designs().items():
  for j,(cls,spec) in enumerate(designs,1):
   lid=f'{fam}-L{j}'
   for c in allc:
    if c['family']!=fam or not _design_matches(c,spec): continue
    r=dict(c); measured=byid.get(c['candidate_id'],{})
    for k in ('mean_uplift','median_uplift','p10_uplift','p90_uplift','min_uplift','max_uplift','uplift_per_cost'):
     if k in measured:r[k]=measured[k]
    ladders.append({'ladder_id':lid,'architecture_class':cls,**r})
 _write_csv(out,ladders);return {'ladders':len(set(r['ladder_id'] for r in ladders)),'rows':len(ladders)}

def _deep_init(repo,doc,rows):
 global _W_REPO,_W_DOC,_W_CANDS,_W_BASE;_W_REPO=Path(repo);_W_DOC=doc;_W_CANDS={(r['ladder_id'],int(r['tl'])):r for r in rows};_W_BASE={}
def _deep_task(a):
 idx,src,lid,seed,trials=a;c=_W_CANDS.get((lid,int(src['tl'])));
 if c is None:return None
 m,v=_worker_bind(src,[c]);
 if v is None:return None
 r=_trial_row(m,v,src,seed+idx*1013,trials,lid);r['ladder_id']=lid;r['family']=c['family'];r['candidate_id']=c['candidate_id'];return r

def run_deep_batch(repo:Path,study:Path,ladders_path:Path,out:Path,start=0,end=None,jobs=24,trials=DEEP_TRIALS):
 doc=load_json(study);rows=_read_csv(ladders_path);ids=[]
 for r in rows:
  if r['ladder_id'] not in ids:ids.append(r['ladder_id'])
 end=len(ids) if end is None else min(end,len(ids));sel=ids[start:end];ctx=_manifest(repo,doc);tasks=[];i=0
 for lid in sel:
  tls={int(r['tl']) for r in rows if r['ladder_id']==lid}
  for src in ctx:
   if int(src['tl']) in tls:tasks.append((i,src,lid,int(doc['masterSeed'])+500000,trials));i+=1
 if jobs<=1:
  _deep_init(str(repo),doc,rows);res=[x for x in (_deep_task(t) for t in tasks) if x]
 else:
  ctxm=get_context('spawn');ch=max(1,min(12,len(tasks)//max(1,jobs*8)))
  with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctxm,initializer=_deep_init,initargs=(str(repo),doc,rows)) as ex:res=[x for x in ex.map(_deep_task,tasks,chunksize=ch) if x]
 res.sort(key=lambda r:(r['ladder_id'],r['scenario_id']));_write_csv(out/'aux_deep_context_results.csv',res);s={'mode':'deep-batch','ladderIds':sel,'passed':not any(int(r['error_trials']) for r in res),'ladders':len(sel),'cells':len(res),'combatTrials':len(res)*trials,'trialsPerCell':trials,'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in res),'errors':sum(int(r['error_trials']) for r in res)};out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def merge_deep(baseline:Path,batches:Path,out:Path):
 base={r['scenario_id']:r for r in _read_csv(baseline)};rows=[];seen=set();audit=[]
 for d in sorted(x for x in batches.rglob('*') if x.is_dir()):
  sp=d/'summary.json';rp=d/'aux_deep_context_results.csv'
  if not sp.exists() or not rp.exists():continue
  sm=json.loads(sp.read_text());ok=sm.get('passed') and sm.get('mode')=='deep-batch';n=0
  if ok:
   for r in _read_csv(rp):
    k=(r['ladder_id'],r['scenario_id']);
    if k not in seen:seen.add(k);rows.append(r);n+=1
  audit.append({'batch':str(d.relative_to(batches)),'rows':n,'passed':int(bool(ok))})
 by=defaultdict(list);resp=[];summary=[]
 for r in rows:by[r['ladder_id']].append(r)
 for lid,rs in by.items():
  ups=[float(r['defender_decisive_share'])-float(base[r['scenario_id']]['defender_decisive_share']) for r in rs];fam=rs[0]['family'];dims=defaultdict(list)
  for r,u in zip(rs,ups):
   for dim in ('tl','side_a_weapon','resource_ensemble_id','scenario_stratum'):dims[(dim,r[dim])].append(u)
  for (dim,lev),v in sorted(dims.items()):resp.append({'ladder_id':lid,'family':fam,'dimension':dim,'level':lev,'mean_uplift':statistics.mean(v),'min_uplift':min(v),'max_uplift':max(v),'cells':len(v)})
  summary.append({'ladder_id':lid,'family':fam,'cells':len(rs),'trials':sum(int(r['trials']) for r in rs),'mean_uplift':statistics.mean(ups),'median_uplift':statistics.median(ups),'min_uplift':min(ups),'max_uplift':max(ups),'resource_swing':max(statistics.mean(v) for (d,l),v in dims.items() if d=='resource_ensemble_id')-min(statistics.mean(v) for (d,l),v in dims.items() if d=='resource_ensemble_id'),'promotion_allowed':0})
 summary.sort(key=lambda r:(r['family'],-float(r['mean_uplift']),r['ladder_id']));_write_csv(out/'batch_merge_audit.csv',audit);_write_csv(out/'aux_deep_ladder_summary.csv',summary);_write_csv(out/'aux_deep_response.csv',resp)
 s={'mode':'deep-merged','passed':True,'ladders':len(summary),'cells':len(rows),'combatTrials':sum(int(r['trials']) for r in rows),'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errorTrials':sum(int(r['error_trials']) for r in rows),'automaticPromotion':False};out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def anchor_candidates()->dict[str,dict[str,dict[int,dict[str,Any]]]]:
 rows=candidate_ledger()
 prefs={
 'CENTER':{'SHIELD_HARDENER':lambda c:c.get('def_bonus_pp')==10 and c.get('tp')==1,'SHIELD_BATTERY':lambda c:c.get('restore')==4 and c.get('charges')==2 and c.get('space')==1,'SHIELD_BOOSTER':lambda c:c.get('capacity_bonus')==4 and c.get('space')==1,'ABLATIVE_ARMOR':lambda c:c.get('ablative_integrity')==4,'CRYSTALLINE_ARMOR':lambda c:c.get('capacity_bonus')==4 and c.get('res_bonus_pp')==5,'ENERGIZED_ARMOR':lambda c:c.get('res_bonus_pp')==10 and c.get('tp')==1 and c.get('space')==1,'FIELD_STABILIZER':lambda c:c.get('spen_reduction')==2 and c.get('tp')==1 and c.get('space')==1,'REPAIR_DRONE':lambda c:c.get('chance_bonus_pp')==10 and c.get('extra_repair_kits')==1 and c.get('space')==1},
 'HIGH':{'SHIELD_HARDENER':lambda c:c.get('def_bonus_pp')==15 and c.get('tp')==1,'SHIELD_BATTERY':lambda c:c.get('restore')==6 and c.get('charges')==3 and c.get('space')==1,'SHIELD_BOOSTER':lambda c:c.get('capacity_bonus')==6 and c.get('space')==1,'ABLATIVE_ARMOR':lambda c:c.get('ablative_integrity')==8,'CRYSTALLINE_ARMOR':lambda c:c.get('capacity_bonus')==6 and c.get('res_bonus_pp')==10,'ENERGIZED_ARMOR':lambda c:c.get('res_bonus_pp')==15 and c.get('tp')==1 and c.get('space')==1,'FIELD_STABILIZER':lambda c:c.get('spen_reduction')==3 and c.get('tp')==1 and c.get('space')==1,'REPAIR_DRONE':lambda c:c.get('chance_bonus_pp')==15 and c.get('extra_repair_kits')==1 and c.get('space')==1}}
 out={}
 for anchor,fams in prefs.items():
  out[anchor]={fam:{int(c['tl']):c for c in rows if c['family']==fam and fn(c)} for fam,fn in fams.items()}
 return out

def center_candidates()->dict[str,dict[int,dict[str,Any]]]:return anchor_candidates()['CENTER']

def _pair_init(repo,doc,pairs):
 global _W_REPO,_W_DOC,_W_CANDS,_W_BASE;_W_REPO=Path(repo);_W_DOC=doc;_W_CANDS=pairs;_W_BASE={}
def _pair_task(a):
 idx,src,pid,seed,trials=a;c1,c2=_W_CANDS[pid];m,v=_worker_bind(src,[c1,c2]);
 if v is None:return None
 r=_trial_row(m,v,src,seed+idx*1019,trials,pid);r['pair_id']=pid;r['family_a']=c1['family'];r['family_b']=c2['family'];return r

def run_pairwise(repo:Path,study:Path,out:Path,jobs=24,trials=PAIR_TRIALS,tl_filter:int|None=None):
 doc=load_json(study);anchors=anchor_candidates();pairs={};ctx=_manifest(repo,doc)
 for anchor,aset in anchors.items():
  for a,b in itertools.combinations(SWEEP_FAMILIES,2):
   for tl in range(1,10):
    if tl_filter is not None and tl!=tl_filter: continue
    if tl in aset[a] and tl in aset[b]:pairs[f'{anchor}__{a}__{b}__TL{tl}']=(aset[a][tl],aset[b][tl])
 tasks=[];i=0
 for pid,(a,b) in pairs.items():
  tl=int(a['tl'])
  for src in ctx:
   if int(src['tl'])==tl:tasks.append((i,src,pid,int(doc['masterSeed'])+900000,trials));i+=1
 if jobs<=1:
  _pair_init(str(repo),doc,pairs);res=[x for x in (_pair_task(t) for t in tasks) if x]
 else:
  ctxm=get_context('spawn');ch=max(1,min(12,len(tasks)//max(1,jobs*8)))
  with ProcessPoolExecutor(max_workers=min(jobs,len(tasks)),mp_context=ctxm,initializer=_pair_init,initargs=(str(repo),doc,pairs)) as ex:res=[x for x in ex.map(_pair_task,tasks,chunksize=ch) if x]
 for r in res:r['anchor_class']=r['pair_id'].split('__',1)[0]
 _write_csv(out/'aux_pairwise_context_results.csv',res);s={'mode':'pairwise','tlFilter':tl_filter,'passed':not any(int(r['error_trials']) for r in res),'pairs':len(pairs),'cells':len(res),'combatTrials':len(res)*trials,'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in res),'errors':sum(int(r['error_trials']) for r in res)};out.mkdir(parents=True,exist_ok=True);(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def merge_pairwise(pair_rows:Path,baseline:Path,screen:Path,out:Path):
 rows=_read_csv(pair_rows);base={r['scenario_id']:r for r in _read_csv(baseline)};single=_read_csv(screen);single_map=defaultdict(lambda:defaultdict(dict))
 anchors=anchor_candidates();sm={r['candidate_id']:float(r['mean_uplift']) for r in single}
 for anchor,aset in anchors.items():
  for fam,bytl in aset.items():
   for tl,c in bytl.items():single_map[anchor][fam][tl]=sm.get(c['candidate_id'],0.0)
 by=defaultdict(list)
 for r in rows:by[r['pair_id']].append(r)
 outrows=[]
 for pid,rs in by.items():
  tl=int(rs[0]['tl']);fa,fb=rs[0]['family_a'],rs[0]['family_b'];anchor=rs[0].get('anchor_class') or pid.split('__',1)[0];up=statistics.mean(float(r['defender_decisive_share'])-float(base[r['scenario_id']]['defender_decisive_share']) for r in rs);sa=single_map[anchor][fa].get(tl,0);sb=single_map[anchor][fb].get(tl,0);interaction=up-sa-sb
  outrows.append({'pair_id':pid,'anchor_class':anchor,'tl':tl,'family_a':fa,'family_b':fb,'combined_mean_uplift':up,'single_a_mean_uplift':sa,'single_b_mean_uplift':sb,'interaction_uplift':interaction,'cells':len(rs)})
 outrows.sort(key=lambda r:(-abs(float(r['interaction_uplift'])),r['pair_id']));_write_csv(out/'aux_pairwise_interaction_summary.csv',outrows);return {'pairs':len(outrows)}

def merge_pairwise_batches(pair_root:Path,baseline:Path,screen:Path,out:Path):
 rows=[];audit=[]
 for d in sorted(x for x in pair_root.rglob('*') if x.is_dir()):
  sp=d/'summary.json';rp=d/'aux_pairwise_context_results.csv'
  if not sp.exists() or not rp.exists():continue
  sm=json.loads(sp.read_text());ok=bool(sm.get('passed')) and sm.get('mode')=='pairwise';rr=_read_csv(rp) if ok else [];rows.extend(rr);audit.append({'batch':str(d.relative_to(pair_root)),'rows':len(rr),'passed':int(ok)})
 tmp=out/'_combined_pairwise.csv';out.mkdir(parents=True,exist_ok=True);_write_csv(tmp,rows);r=merge_pairwise(tmp,baseline,screen,out);_write_csv(out/'batch_merge_audit.csv',audit);tmp.unlink(missing_ok=True);summaries=[json.loads((d/'summary.json').read_text()) for d in pair_root.rglob('*') if d.is_dir() and (d/'summary.json').exists()];r['combatTrials']=sum(int(x.get('combatTrials',0)) for x in summaries);r['turnCapSentinels']=sum(int(x.get('turnCapSentinels',0)) for x in summaries);r['errorTrials']=sum(int(x.get('errors',0)) for x in summaries);(out/'summary.json').write_text(json.dumps({'mode':'pairwise-merged','passed':r['errorTrials']==0,**r},indent=2)+'\n');return r

def disposition(repo:Path,out:Path):
 cat=load_json(repo/'docs/archive/player_technology/pre-cp165-active/auxiliary_component_catalog_v0_4.json');sweep={'ablative-armor','shield-battery','shield-booster','shield-hardener','repair-drone-bay','powered-reactive-armor','field-stabilizer'};fixed={'missile-magazine','kinetic-magazine'};power={'auxiliary-power-plant','auxiliary-reactor','battery-bank','supercapacitor','smes','power-stabilizer','thermal-suppression'}
 rows=[]
 for c in cat.get('components',[]):
  cid=c['id'];disp='BROAD_COMBAT_SWEEP' if cid in sweep else 'FIXED_ENDURANCE_AUDIT' if cid in fixed else 'DEFER_FINAL_TP_SUPPLY' if cid in power or 'power' in str(c.get('gameplayLoop','')).lower() and c.get('owner')=='Power' else 'DEFER_THREAT_TAGS' if cid in ('particle-deflection-screen','radiation-hardening','field-containment') else 'ARCHITECTURE_ONLY_OR_REUSE'
  rows.append({'id':cid,'name':c['name'],'owner':c['owner'],'window':c.get('window',''),'disposition':disp,'reason':c.get('mechanicalIdentity','')})
 rows += [{'id':'crystalline-armor','name':'Crystalline Armor branch','owner':'Armor','window':'TL6+','disposition':'BROAD_COMBAT_SWEEP','reason':'validated alternate armor seed; response magnitude/lifecycle remains open'},{'id':'ECM','name':'ECM','owner':'Sensors / EW','window':'TL1+','disposition':'REUSE_CLOSED_INTEGRATED','reason':'integrated standard system; current AUX pass does not reopen accepted EW ladder'},{'id':'ECCM','name':'ECCM','owner':'Sensors / EW','window':'TL1+','disposition':'REUSE_CLOSED_INTEGRATED','reason':'integrated standard system; current AUX pass does not reopen accepted EW ladder'},{'id':'PDS','name':'K/E/AMM PDS','owner':'PDS','window':'TL1+','disposition':'REUSE_CLOSED_CP155','reason':'dedicated PDS surfaces closed by CP155; consume PF2 only'}]
 _write_csv(out,rows);return rows

def plan(repo:Path,study:Path,out:Path):
 doc=load_json(study);cands=candidate_ledger();manifest=_manifest(repo,doc);out.mkdir(parents=True,exist_ok=True);_write_csv(out/'aux_candidate_ledger.csv',cands);_write_csv(out/'aux_stage_a_contexts.csv',manifest);disposition(repo,out/'aux_lifecycle_disposition.csv')
 # Bind each Stage-A identity once; legal AUX placement thereafter is a cheap build-headroom test.
 bound={}
 for src in manifest:
  key=src['scenario_id'];m=_resource_matrix(repo,doc,src['resource_ensemble_id']);bound[key]=bind_scenario(m,src).variant.side_b
 bytl=defaultdict(list)
 for src in manifest:bytl[int(src['tl'])].append(src)
 def legal_one(c,src):
  b=bound[src['scenario_id']]
  if not _relevant(c,b):return False
  extra=int(c.get('space',0));
  if c['family']=='SHIELD_HARDENER' and b.shield_hardener:extra=0
  return b.mission_aux_space>=extra
 def legal_pair(a,b,src):
  build=bound[src['scenario_id']]
  if not _relevant(a,build) or not _relevant(b,build):return False
  ea=int(a.get('space',0));eb=int(b.get('space',0))
  if a['family']=='SHIELD_HARDENER' and build.shield_hardener:ea=0
  if b['family']=='SHIELD_HARDENER' and build.shield_hardener:eb=0
  return build.mission_aux_space>=ea+eb
 legal=0;by=defaultdict(int)
 for c in cands:
  n=sum(legal_one(c,src) for src in bytl[int(c['tl'])]);legal+=n;by[(c['family'],int(c['tl']))]+=n
 base_trials=len(manifest)*BASELINE_TRIALS;screen_trials=legal*SCREEN_TRIALS
 anchors=anchor_candidates();deep_cells=0
 allc=cands
 for fam,designs in representative_designs().items():
  for _cls,spec in designs:
   for c in allc:
    if c['family']==fam and _design_matches(c,spec): deep_cells += sum(legal_one(c,src) for src in bytl[int(c['tl'])])
 deep_trials=deep_cells*DEEP_TRIALS
 pair_cells=0
 for anchor,aset in anchors.items():
  for a,b in itertools.combinations(SWEEP_FAMILIES,2):
   for tl in range(1,10):
    if tl in aset[a] and tl in aset[b]:pair_cells += sum(legal_pair(aset[a][tl],aset[b][tl],src) for src in bytl[tl])
 pair_trials=pair_cells*PAIR_TRIALS
 counts=[{'family':f,'tl':tl,'legal_cells':n,'candidate_count':sum(1 for c in cands if c['family']==f and int(c['tl'])==tl)} for (f,tl),n in sorted(by.items())];_write_csv(out/'aux_candidate_counts.csv',counts)
 s={'schemaVersion':SCHEMA,'checkpoint':158,'candidateTlPoints':len(cands),'baselineCells':len(manifest),'screenLegalCells':legal,'plannedDeepCells':deep_cells,'pairwiseLegalCells':pair_cells,'baselineCombatTrials':base_trials,'screenCombatTrials':screen_trials,'deepCombatTrials':deep_trials,'pairwiseCombatTrials':pair_trials,'substantiveCombatTrials':base_trials+screen_trials+deep_trials+pair_trials,'automaticPromotion':False};(out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def smoke(repo:Path,study:Path,out:Path):
 doc=load_json(study);manifest=_manifest(repo,doc);reps=representative_designs();rows=[]
 for fam in SWEEP_FAMILIES:
  spec=reps[fam][1][1]  # CENTER_FLAT architecture
  cand=next((c for c in candidate_ledger() if c['family']==fam and _design_matches(c,spec)),None)
  if cand is None: raise RuntimeError(f'No CENTER smoke candidate for {fam}')
  src=next((r for r in manifest if int(r['tl'])==int(cand['tl']) and _relevant(cand,bind_scenario(_resource_matrix(repo,doc,r['resource_ensemble_id']),r).variant.side_b)),None)
  if src is None: raise RuntimeError(f'No legal smoke context for {fam}')
  m,v=_bind(repo,doc,src,[cand])
  if v is None: raise RuntimeError(f'CENTER smoke candidate illegal for {fam}')
  rr=_trial_row(m,v,src,int(doc['masterSeed'])+970000+len(rows)*101,1,cand['candidate_id']);rr['family']=fam;rows.append(rr)
 out.mkdir(parents=True,exist_ok=True);_write_csv(out/'aux_smoke.csv',rows)
 s={'mode':'architecture-smoke','passed':len(rows)==len(SWEEP_FAMILIES) and not any(int(r['error_trials']) for r in rows),'families':len(rows),'combatTrials':len(rows),'turnCapSentinels':sum(int(r['turn_cap_sentinels']) for r in rows),'errors':sum(int(r['error_trials']) for r in rows)}
 (out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');return s

def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);ap.add_argument('--study',required=True);sub=ap.add_subparsers(dest='cmd',required=True)
 p=sub.add_parser('plan');p.add_argument('--out',required=True)
 p=sub.add_parser('smoke');p.add_argument('--out',required=True)
 p=sub.add_parser('baseline');p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=24)
 p=sub.add_parser('screen');p.add_argument('--out',required=True);p.add_argument('--family',required=True);p.add_argument('--tl',type=int,required=True);p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int);p.add_argument('--jobs',type=int,default=24)
 p=sub.add_parser('merge-screen');p.add_argument('--baseline',required=True);p.add_argument('--batches',required=True);p.add_argument('--out',required=True)
 p=sub.add_parser('synthesize');p.add_argument('--screen',required=True);p.add_argument('--out',required=True)
 p=sub.add_parser('deep');p.add_argument('--ladders',required=True);p.add_argument('--out',required=True);p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int);p.add_argument('--jobs',type=int,default=24)
 p=sub.add_parser('merge-deep');p.add_argument('--baseline',required=True);p.add_argument('--batches',required=True);p.add_argument('--out',required=True)
 p=sub.add_parser('pairwise');p.add_argument('--out',required=True);p.add_argument('--jobs',type=int,default=24);p.add_argument('--tl',type=int)
 p=sub.add_parser('merge-pairwise');p.add_argument('--pairs',required=True);p.add_argument('--baseline',required=True);p.add_argument('--screen',required=True);p.add_argument('--out',required=True)
 p=sub.add_parser('merge-pairwise-batches');p.add_argument('--batches',required=True);p.add_argument('--baseline',required=True);p.add_argument('--screen',required=True);p.add_argument('--out',required=True)
 a=ap.parse_args(argv);repo=Path(a.repo);study=Path(a.study)
 if a.cmd=='plan':r=plan(repo,study,Path(a.out))
 elif a.cmd=='smoke':r=smoke(repo,study,Path(a.out))
 elif a.cmd=='baseline':r=run_baseline(repo,study,Path(a.out),a.jobs)
 elif a.cmd=='screen':r=run_screen_batch(repo,study,Path(a.out),a.family,a.tl,a.start,a.end,a.jobs)
 elif a.cmd=='merge-screen':r=merge_screen(repo,study,Path(a.baseline),Path(a.batches),Path(a.out))
 elif a.cmd=='synthesize':r=synthesize(Path(a.screen),Path(a.out))
 elif a.cmd=='deep':r=run_deep_batch(repo,study,Path(a.ladders),Path(a.out),a.start,a.end,a.jobs)
 elif a.cmd=='merge-deep':r=merge_deep(Path(a.baseline),Path(a.batches),Path(a.out))
 elif a.cmd=='pairwise':r=run_pairwise(repo,study,Path(a.out),a.jobs,tl_filter=a.tl)
 elif a.cmd=='merge-pairwise':r=merge_pairwise(Path(a.pairs),Path(a.baseline),Path(a.screen),Path(a.out))
 else:r=merge_pairwise_batches(Path(a.batches),Path(a.baseline),Path(a.screen),Path(a.out))
 print(json.dumps(r,indent=2));return 0 if r.get('passed',True) else 1
if __name__=='__main__':raise SystemExit(main())
