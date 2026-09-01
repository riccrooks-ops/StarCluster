from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .canonical_mechanics import CANONICAL_DAMAGE_MODEL, DEF_RES_DAMAGE_MODEL, resolve_def_res_damage
from .combat_model_reconciliation import apply_combat_model_candidate, reconciliation_profile
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant, build_space


from .study import canonicalize_relocated_references

def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors=[]
    if doc.get('schemaVersion')!='star-cluster-cp139-def-res-reconciliation-study-v0.1': errors.append('schemaVersion')
    if int(doc.get('checkpoint',0))!=139: errors.append('checkpoint')
    if doc.get('productionDamageModel')!=CANONICAL_DAMAGE_MODEL: errors.append('productionDamageModel')
    if doc.get('researchDamageModel')!=DEF_RES_DAMAGE_MODEL: errors.append('researchDamageModel')
    if doc.get('substantiveCombatTrials')!=0: errors.append('substantiveCombatTrials')
    return errors


def _sha(path: Path) -> str:
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]) if rows else []
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)


def _fixture_rows() -> list[dict[str, Any]]:
    cases=[
        ('shield-deflection-at-boundary',dict(shield=8,armor_integrity=6,hull=12,damage=4,spen=0,apen=0,shield_def_pp=20,armor_res_pp=20,defense_roll=20)),
        ('shield-couples-above-deflection-boundary',dict(shield=8,armor_integrity=6,hull=12,damage=4,spen=0,apen=0,shield_def_pp=20,armor_res_pp=20,defense_roll=21)),
        ('spen-reduces-def-not-capacity',dict(shield=4,armor_integrity=6,hull=12,damage=6,spen=5,apen=0,shield_def_pp=20,armor_res_pp=20,defense_roll=16)),
        ('apen-reduces-res-fractionally',dict(shield=0,armor_integrity=6,hull=12,damage=4,spen=0,apen=5,shield_def_pp=20,armor_res_pp=20,defense_roll=1)),
        ('armor-collapse-carries-unused-raw-inward',dict(shield=0,armor_integrity=1,hull=12,damage=2,spen=0,apen=0,shield_def_pp=0,armor_res_pp=25,defense_roll=100)),
        ('caps-apply-after-penetration-reduction',dict(shield=1,armor_integrity=10,hull=12,damage=3,spen=0,apen=0,shield_def_pp=100,armor_res_pp=100,defense_roll=46)),
        ('no-live-shield-means-no-deflection',dict(shield=0,armor_integrity=3,hull=12,damage=2,spen=0,apen=0,shield_def_pp=45,armor_res_pp=20,defense_roll=1)),
        ('no-live-armor-means-unmitigated-hull',dict(shield=0,armor_integrity=0,hull=12,damage=12,spen=0,apen=0,shield_def_pp=0,armor_res_pp=95,defense_roll=100)),
    ]
    expected={
        'shield-deflection-at-boundary':(20,True,0,8,6,12),
        'shield-couples-above-deflection-boundary':(20,False,0,4,6,12),
        'spen-reduces-def-not-capacity':(15,False,20,0,4.4,12),
        'apen-reduces-res-fractionally':(0,False,15,0,2.6,12),
        'armor-collapse-carries-unused-raw-inward':(0,False,25,0,0,11.333333333333334),
        'caps-apply-after-penetration-reduction':(45,False,95,0,9.9,12),
        'no-live-shield-means-no-deflection':(0,False,20,0,1.4,12),
        'no-live-armor-means-unmitigated-hull':(0,False,0,0,0,0),
    }
    rows=[]
    for cid,kwargs in cases:
        r=resolve_def_res_damage(**kwargs)
        exp=expected[cid]
        actual=(r.effective_def_pp,r.deflected,r.effective_res_pp,r.final_shield,r.final_armor_integrity,r.final_hull)
        ok=all((a==b if isinstance(b,bool) else abs(float(a)-float(b))<1e-9) for a,b in zip(actual,exp))
        rows.append({'case_id':cid,'status':'PASS' if ok else 'FAIL','effective_def_pp':r.effective_def_pp,'deflected':r.deflected,'effective_res_pp':r.effective_res_pp,'final_shield':r.final_shield,'final_armor':r.final_armor_integrity,'final_hull':r.final_hull})
    return rows


def _build(matrix: CandidateMatrix, tl: int, label: str) -> EcologyBuild:
    if label in ('GP','Swarmer'): family='Missile'; payload=label
    else: family=label; payload='GP'
    pds={'Kinetic':'Kinetic','Energy':'Energy','Missile':'AMM'}[family]
    hardener=tl>=3
    combat=build_space(matrix,tl,family,1,1,True,False,True,pds,hardener)
    cap=matrix.capacity(tl)
    return EcologyBuild(f'cp139-tl{tl}-{label.lower()}',tl,'cp139-smoke',family,1,1,True,False,True,pds,hardener,cap,combat,max(0,cap-combat),payload)


def _smoke_rows(repo: Path, matrix_path: str) -> list[dict[str, Any]]:
    rows=[]
    for model in ('cp138-legacy-control','cp139-reconciled-candidate'):
        matrix=CandidateMatrix(repo,matrix_path)
        if model.startswith('cp139'): apply_combat_model_candidate(matrix)
        for tl in (1,5,9):
            labels=['Kinetic','Energy','GP'] if tl==1 else ['Kinetic','Energy','GP','Swarmer']
            builds={x:_build(matrix,tl,x) for x in labels}
            for a_name in labels:
                for b_name in labels:
                    v=EcologyVariant(f'cp139-{model}-tl{tl}-{a_name.lower()}-vs-{b_name.lower()}',tl,builds[a_name],builds[b_name],'SideAFirst',scenario_group='cp139-reconciliation-smoke',physical_id_a='physical-a',physical_id_b='physical-b')
                    r=run_trial_full_map(matrix,v,139001,0)
                    rows.append({
                        'model':model,'damage_model':getattr(matrix,'damage_model',CANONICAL_DAMAGE_MODEL),'variant_id':v.id,'tl':tl,'family_a':a_name,'family_b':b_name,
                        'winner':r.winner,'turns':r.turns,'unresolved':r.unresolved,'error':r.error,
                        'final_hull_a':r.hull_a,'final_hull_b':r.hull_b,'final_armor_a':r.armor_a,'final_armor_b':r.armor_b,'final_shield_a':r.shield_a,'final_shield_b':r.shield_b,
                        'def_res_packets_a':r.side_a.def_res_packets,'def_res_packets_b':r.side_b.def_res_packets,'shield_deflections_a':r.side_a.shield_deflections,'shield_deflections_b':r.side_b.shield_deflections,
                        'armor_resisted_a':r.side_a.armor_resisted_damage,'armor_resisted_b':r.side_b.armor_resisted_damage,
                        'pds_attempts_a':r.side_a.pds_attempts,'pds_attempts_b':r.side_b.pds_attempts,'pds_intercepts_a':r.side_a.pds_intercepts,'pds_intercepts_b':r.side_b.pds_intercepts,
                        'missile_arrivals_a':r.side_a.missile_terminal_arrivals,'missile_arrivals_b':r.side_b.missile_terminal_arrivals,'missile_guidance_attempts_a':r.side_a.missile_guidance_attempts,'missile_guidance_attempts_b':r.side_b.missile_guidance_attempts,
                    })
    return rows


def _swarmer_rows() -> list[dict[str, Any]]:
    profile=reconciliation_profile(); rows=[]
    for tl in (2,5,9):
        gp_damage,guidance=profile['gp'][tl]
        packet=gp_damage*0.45
        rows.append({'tl':tl,'gp_damage':gp_damage,'swarmer_packet_damage':packet,'swarmer_total_yield':packet*2,'yield_fraction_vs_gp':0.9,'gp_guidance':guidance,'swarmer_guidance':guidance,'pds_visible_subflights':2,'pds_penalty_pp':0})
    return rows


def _ledger_rows() -> list[dict[str,str]]:
    raw=[
('production damage model','CP138 retained','PASS','ready','penetration-hardening-v1 remains default; production LayeredDamageResolver unchanged'),
('Shield DEF','combat model supersedes for research','PASS','ready','whole-packet stochastic DEF; SPEN reduces DEF; 45 pp cap'),
('Armor RES','combat model supersedes for research','PASS','ready','fractional mitigation; APEN reduces RES; 95 pp cap; fractional collapse overflow'),
('defense RNG','new integration requirement','PASS','ready','independent defense stream leaves direct/guidance/PDS/DamCon streams unchanged'),
('continuous S/A/H state','combat model supersedes for research','PASS','ready','candidate path supports fractional Armor/Hull while legacy state remains integer'),
('Shield recovery after collapse','combat model supersedes for research','PASS','ready','candidate uses collapse lockout; CP138 default remains restartable'),
('Kinetic offense','combat model candidate','PASS','ready','v17 DAM/ACC/APEN candidate ladder applied in memory'),
('Energy offense','combat model candidate + CP138 mode semantics','PASS','ready','combat-model damage mapped to Standard; Low/Overload re-derived; CP138 operating modes retained'),
('GP Missile offense','combat model candidate','PASS','ready','v17 GP DAM/guidance, 0 SPEN/APEN applied in memory'),
('PDS numerical centers','combat model candidate','PASS','ready','v19 K/E/AMM chance, RC, ammo centers applied in memory; current terminal attempt cap retained'),
('Swarmer terminal/PDS structure','combat model supersedes for research','PASS','ready','90% GP yield split into two independently guided PDS-visible sub-Flights sharing PDS RC; zero bespoke PDS penalty'),
('Shield Hardener','blend','PASS','ready','CP138 install/TP gating retained; candidate active effect maps to +10 DEF pp'),
('Powered Reactive Armor','combat-model stress concept','DEFERRED','nonblocking','+10 RES concept recorded but current canonical consumer does not execute branch; v22C forbids invented TBD mechanics'),
('Ablative Armor','combat-model concept','DEFERRED','nonblocking','sacrificial AI-only/no-RES semantics recorded; not required by Stage A baseline strata'),
('range/movement/Sensor/EW/EngageAdaptive','CP138 retained','PASS','ready','standalone combat lab did not supersede these full-map mechanics'),
('subsystem damage states','CP138 retained/deferred','DEFERRED','nonblocking','v22C Stage A uses Undamaged subsystem condition; later condition-coupled studies remain separate'),
('reactor/TP resource environments','v22C ensemble','OPEN','BLOCKING','six v22C resource environments must be applied as simulation-only overlays; no single reactor/TP curve promoted'),
('dynamic TP conflict telemetry','v22C contract','OPEN','BLOCKING','requested/desirable/funded/denied actions and true TP-conflict flag still need instrumentation'),
('ten Stage A combat strata','v22C contract','OPEN','BLOCKING','legal-build/geometry/tactical bindings still need implementation before 8,220-scenario smoke'),
]
    return [dict(zip(('area','precedence','status','stage_a','detail'),x)) for x in raw]


def run_analysis(repo: Path, study_path: Path, output_dir: Path) -> dict[str, Any]:
    doc=json.loads(study_path.read_text(encoding='utf-8'))
    errs=validate_study(doc)
    if errs: raise ValueError('invalid CP139 study: '+','.join(errs))
    output_dir.mkdir(parents=True,exist_ok=True)
    matrix_path=doc['matrix']
    matrix_abs=repo/matrix_path
    before=_sha(matrix_abs)
    fixture=_fixture_rows(); smoke=_smoke_rows(repo,matrix_path); sw=_swarmer_rows(); ledger=_ledger_rows()
    _write_csv(output_dir/'def_res_fixture_audit.csv',fixture)
    _write_csv(output_dir/'full_map_smoke.csv',smoke)
    _write_csv(output_dir/'swarmer_structure_audit.csv',sw)
    _write_csv(output_dir/'reconciliation_ledger.csv',ledger)
    after=_sha(matrix_abs)
    candidate=[r for r in smoke if r['model']=='cp139-reconciled-candidate']
    result={
        'schemaVersion':'star-cluster-cp139-def-res-reconciliation-results-v0.1','checkpoint':139,
        'passed':all(r['status']=='PASS' for r in fixture) and not any(r['error'] for r in smoke) and before==after,
        'failedGates':[], 'baseCheckpoint':138,'productionDamageModel':CANONICAL_DAMAGE_MODEL,'researchDamageModel':DEF_RES_DAMAGE_MODEL,
        'sourceMatrixSha256Before':before,'sourceMatrixSha256After':after,'sourceMatrixUnmodified':before==after,
        'fixtureCases':len(fixture),'fixturePass':sum(r['status']=='PASS' for r in fixture),
        'smokeVariants':len(smoke),'legacySmokeVariants':sum(r['model']=='cp138-legacy-control' for r in smoke),'candidateSmokeVariants':len(candidate),
        'smokeErrors':sum(bool(r['error']) for r in smoke),'candidateDefResPackets':sum(r['def_res_packets_a']+r['def_res_packets_b'] for r in candidate),
        'candidateShieldDeflections':sum(r['shield_deflections_a']+r['shield_deflections_b'] for r in candidate),
        'candidateArmorResistedDamage':sum(float(r['armor_resisted_a'])+float(r['armor_resisted_b']) for r in candidate),
        'stageAReady':False,'stageABlockers':['reactor/TP resource environments','dynamic TP conflict telemetry','ten Stage A combat strata'],
        'stageABlockerCount':3,'substantiveCombatTrials':0,'promotionAllowed':False,
        'interpretation':'Mechanics/reconciliation foundation only. One-trial smoke outcomes are execution evidence, never balance evidence.'
    }
    if not result['passed']:
        if before!=after: result['failedGates'].append('source-matrix-modified')
        if any(r['status']!='PASS' for r in fixture): result['failedGates'].append('def-res-fixtures')
        if any(r['error'] for r in smoke): result['failedGates'].append('full-map-smoke')
    (output_dir/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result
