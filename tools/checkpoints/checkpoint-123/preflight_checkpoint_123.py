#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
CP122_NATIVE_SHA='32a2cf12384229b2285872c5c1c74d34207cc0406800cd53b0d99702a26b8aec'
FROZEN_PREFIXES=('src/','tests/','tools/simulation/','docs/design/testing/')
FROZEN_ALLOWED_CHANGES={'docs/design/testing/README.md'}
STABLE_FAMILIES=('reactor','stl','ftl','computer','sensor','ecm','eccm','kinetic_pds','energy_pds','amm_pds')
EXPECTED_SHEETS=['Overview','Lineage Map','Numerical Baseline','Optional Components','CP123 Decisions']
RESTORED_BEATS={('armor','armor-enhancements',7,'Adaptive reactive armor architecture'),('energy-weapons','energy-specials',7,'Nuclear-pumped sacrificial laser'),('missile-weapons','amm',2,'Improved local AMM guidance')}
def req(v,msg):
    if not v: raise AssertionError(msg)
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1); out[r]=h
    return out
def validate_cp122(repo):
    z=repo/'docs/validation/evidence/checkpoint-123/CP122_NATIVE_RESULTS_ACCEPTED.zip'; req(z.is_file() and sha(z)==CP122_NATIVE_SHA,'accepted CP122 archive hash')
    s=js(repo/'docs/validation/evidence/checkpoint-123/CP123_ACCEPTED_CP122_NATIVE_SUMMARY.json')
    req(s['acceptedCheckpoint']==122 and s['sourceArchiveSha256']==CP122_NATIVE_SHA,'CP122 provenance identity')
    req(s['xunitPassed']==905 and s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'CP122 accepted test counts')
    req(s['canonicalParityCases']==234138 and s['canonicalParityMismatches']==0 and s['exactParity'] is True,'CP122 canonical parity provenance')
    req(s['productionRepairHullPerKit']==1 and s['criticalCadenceMigrated'] is False and s['substantiveMonteCarloTrials']==0 and s['failedGates']==[],'CP122 semantic provenance')
def validate_frozen(repo):
    old=manifest(repo/'docs/validation/evidence/checkpoint-122/CP122_REPOSITORY_SHA256SUMS.txt')
    expected={r:h for r,h in old.items() if r.startswith(FROZEN_PREFIXES) and r not in FROZEN_ALLOWED_CHANGES}
    cur=[]
    for pref in FROZEN_PREFIXES:
        base=repo/pref.rstrip('/')
        if base.exists(): cur += [p.relative_to(repo).as_posix() for p in base.rglob('*') if p.is_file() and p.relative_to(repo).as_posix() not in FROZEN_ALLOWED_CHANGES and 'bin' not in p.parts and 'obj' not in p.parts and '__pycache__' not in p.parts]
    req(set(cur)==set(expected),f'frozen surface path drift missing={sorted(set(expected)-set(cur))[:5]} extra={sorted(set(cur)-set(expected))[:5]}')
    for rel,h in expected.items(): req(sha(repo/rel)==h,f'CP122 frozen surface drift: {rel}')
    oldconcept='docs/Star_Cluster_Game_Concept_v0.7m.docx'; arch=repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7m.docx'
    req(oldconcept in old and arch.is_file() and sha(arch)==old[oldconcept],'archived CP122 Concept not byte-preserved')
def storykeys(s): return [(d['disciplineId'],l['id'],int(b['tl']),b['title']) for d in s['disciplines'] for l in d['lineages'] for b in l['beats']]
def tablekeys(t): return [(e['disciplineId'],e['lineageId'],int(e['tl']),e['technology']) for e in t['lineageEntries']]
def validate_story_table(repo):
    s=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json'); t=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_5.json')
    sk=storykeys(s); tk=tablekeys(t)
    req(len(s['disciplines'])==10 and sum(len(d['lineages']) for d in s['disciplines'])==33,'Storyboard counts')
    req(len(sk)==218 and len(set(sk))==218 and len(tk)==218 and len(set(tk))==218 and set(sk)==set(tk),'Storyboard/Tech Table exact reconciliation')
    for k in RESTORED_BEATS: req(k in set(tk),f'formerly omitted technology missing: {k}')
    for e in t['lineageEntries']:
        if e.get('playerExpression') in ('deferred_concept','optional_component'):
            req('numericalProfileRef' not in e,f'non-baseline entry must not inherit numerical spine: {e["technology"]}')
    sw=next(l for d in s['disciplines'] if d['disciplineId']=='missile-weapons' for l in d['lineages'] if l['id']=='missile-swarmer')
    req([b['tl'] for b in sw['beats']]==[2,3,5,7] and sw['beats'][0]['playerExpression']=='payload_variant','Swarmer introduction/timing')
    req(all(b['playerExpression']=='automatic_capability' for b in sw['beats'][1:]),'Swarmer maturation expression')
    for d in s['disciplines']:
        for l in d['lineages']:
            for b in l['beats']: req(b.get('references') and b.get('playerExpression') in s['playerExpressionDefinitions'],f'untraceable Storyboard beat {b["title"]}')
def validate_matrix(repo):
    old=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_2.json'); m=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json'); p=m['profiles']
    req(m['checkpoint']==123 and m['damagePointScale']['canonicalScale']==2 and len(p)==20,'matrix identity/count')
    for fam,tiers in p.items(): req(set(tiers)==set(map(str,range(1,10))),f'{fam} TL1-TL9 rows')
    for fam in STABLE_FAMILIES: req(p[fam]==old['profiles'][fam],f'stable family drift: {fam}')
    req([p['hull'][str(t)]['hullPoints'] for t in range(1,10)]==[24,24,25,26,27,28,30,32,34],'Hull progression')
    req([(p['damage_control'][str(t)]['degradedToOperationalChancePp'],p['damage_control'][str(t)]['disabledToDegradedChancePp'],p['damage_control'][str(t)]['hullRepairChancePp'],p['damage_control'][str(t)]['hullRestoredPerSuccessfulKit']) for t in range(1,10)]==[(70,50,40,1),(70,50,40,1),(75,55,45,1),(75,55,45,1),(75,55,45,1),(75,55,45,1),(80,60,50,2),(80,60,50,2),(85,65,55,3)],'DamCon progression')
    req([(p['armor'][str(t)]['ap'],p['armor'][str(t)]['ai']) for t in range(1,10)]==[(0,8),(0,9),(2,10),(2,11),(3,12),(4,14),(4,14),(4,14),(6,16)],'Armor progression')
    req([(p['shield'][str(t)]['capacity'],p['shield'][str(t)]['baseRecharge'],p['shield'][str(t)]['shieldArmor']) for t in range(1,10)]==[(4,2,0),(5,2,0),(6,3,0),(7,3,0),(9,3,0),(10,4,0),(14,4,1),(18,5,2),(24,6,2)],'Shield progression')
    req([(p['kinetic_main'][str(t)]['accuracyPp'],p['kinetic_main'][str(t)]['damage'],p['kinetic_main'][str(t)]['spen'],p['kinetic_main'][str(t)]['apen']) for t in range(1,10)]==[(20,8,2,0),(20,8,2,2),(20,8,2,2),(25,10,2,2),(25,10,2,3),(30,11,2,4),(30,11,2,4),(30,12,3,5),(35,14,4,6)],'Kinetic progression')
    req([(p['energy_main'][str(t)]['lowDamage'],p['energy_main'][str(t)]['standardDamage'],p['energy_main'][str(t)]['highDamage'],p['energy_main'][str(t)]['spen'],p['energy_main'][str(t)]['apen']) for t in range(1,10)]==[(4,6,8,2,2),(4,6,8,2,2),(4,6,8,2,2),(5,8,10,3,2),(5,8,10,3,2),(6,9,11,4,2),(6,9,11,4,2),(8,11,13,5,3),(9,13,15,6,4)],'Energy progression')
    forbidden={'warheadDamage','spen','apen','guidanceBaseHit','commandDatalink','onboardNav','terminalSeeker','localApproxCanAcquire'}
    for tl,row in p['missile_delivery'].items(): req(not (forbidden & set(row)),f'missile delivery conflation TL{tl}')
    req([p['missile_guidance'][str(t)]['guidanceBaseHit'] for t in range(1,10)]==[55,55,55,60,60,65,65,70,75],'Missile guidance')
    req([p['missile_gp_warhead'][str(t)]['damage'] for t in range(1,10)]==[10,10,11,11,13,13,15,15,15],'GP yield')
    req(all(p['missile_gp_warhead'][str(t)]['spen']==2 and p['missile_gp_warhead'][str(t)]['apen']==4 for t in range(1,10)),'GP penetration hold')
    req(p['missile_swarmer']['1']['available'] is False,'Swarmer TL1 unavailable')
    req([(p['missile_swarmer'][str(t)]['packetDamage'],p['missile_swarmer'][str(t)]['terminalGuidanceBonusPp'],p['missile_swarmer'][str(t)]['pdsInterceptPenaltyPp']) for t in (2,3,5,7)]==[(4,10,10),(5,10,10),(7,10,10),(8,15,15)],'Swarmer maturation')
def docx_text(path):
    with zipfile.ZipFile(path) as z: root=ET.fromstring(z.read('word/document.xml'))
    return ''.join((e.text or '') for e in root.iter() if e.tag.endswith('}t'))
def xlsx_info(path):
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('xl/workbook.xml')); names=[e.attrib.get('name') for e in root.iter() if e.tag.endswith('}sheet')]; formulas=0; rows={}
        for i,name in enumerate(names,1):
            sr=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')); formulas+=sum(1 for e in sr.iter() if e.tag.endswith('}f')); rows[name]=sum(1 for e in sr.iter() if e.tag.endswith('}row'))
    return names,formulas,rows
def validate_docs(repo):
    active=list((repo/'docs').glob('Star_Cluster_Game_Concept_v0.7*.docx')); req([p.name for p in active]==['Star_Cluster_Game_Concept_v0.7n.docx'],f'active Concept {active}')
    dt=docx_text(active[0])
    for phrase in ('Checkpoint 123','10 disciplines, 33 lineages, and 218 unique Storyboard beats','GP D10','distinct TL2+','1 canonical Hull per successful kit','Version 0.7n','August 16, 2026','Whole-system technology baseline consolidation'): req(phrase.lower() in dt.lower(),f'Concept missing {phrase}')
    with zipfile.ZipFile(active[0]) as z:
        header=''.join(z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/header') and n.endswith('.xml')); core=z.read('docProps/core.xml').decode('utf-8','ignore')
    req('v0.7n' in header and 'Star Cluster Game Concept v0.7n' in core and '<cp:version>0.7n</cp:version>' in core,'Concept metadata')
    x=repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_5.xlsx'; names,formulas,rows=xlsx_info(x)
    req(names==EXPECTED_SHEETS and formulas==0 and rows['Lineage Map']==219 and rows['Numerical Baseline']==181,'workbook structure')
    cov=js(repo/'docs/references/reference-mining/technology-architecture/cp106_reference_observation_coverage_v1.json'); req(cov['observationCount']==195 and cov['coverageCount']==195 and cov['complete'] is True,'reference coverage ledger')
    ideas=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_idea_register_v1_6.json'); req(len(ideas['ideas'])==138 and ideas['cp123Decisions']['swarmerWindowReconciledToTl2Plus'],'Idea Register')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-123/checkpoint_123_definition.json'); req(d['checkpoint']==123 and d['acceptedBaseline']==122 and d['referenceOnly'] is True,'definition')
        print('       Validating accepted CP122 provenance and frozen executable/scenario surfaces...'); validate_cp122(repo); validate_frozen(repo)
        print('       Validating exact Storyboard/Tech-Table reconciliation and revised numerical baseline...'); validate_story_table(repo); validate_matrix(repo)
        print('       Validating active documentation, Concept, workbook, and reference coverage...'); validate_docs(repo)
        print('       CP123 preflight: accepted CP122 evidence verified; production/scenario/simulation surfaces frozen; 10 disciplines / 33 lineages / 218 exact Storyboard-Tech-Table beats; 20 x 9 numerical reference profiles; 195-observation reference ledger retained; no scenario or balance study.')
        return 0
    except Exception as e:
        print(f'CP123 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
