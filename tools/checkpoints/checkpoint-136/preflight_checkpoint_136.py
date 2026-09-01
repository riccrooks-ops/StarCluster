#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re, sys, unittest, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP135_RESULTS_SHA='065d4de05265887f875d1bf1e3e36a267e6daded9d9426b34b9bcb7b57b7aefb'
CP135_MANIFEST='docs/validation/evidence/checkpoint-135/CP135_REPOSITORY_SHA256SUMS.txt'

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
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
def count_suite(suite): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in suite)


def validate_wrapper_contract(repo):
    wrapper=repo/'tools/checkpoints/checkpoint-136/apply_checkpoint_136.ps1'
    w=text(wrapper)
    expected={
        'preflight_checkpoint_136.py': repo/'tools/checkpoints/checkpoint-136/preflight_checkpoint_136.py',
        'test_checkpoint_136_contract.py': repo/'tools/checkpoints/checkpoint-136/test_checkpoint_136_contract.py',
    }
    for name,path in expected.items():
        req(path.is_file(),f'CP136 wrapper dependency missing {name}')
        req(name in w,f'CP136 wrapper must reference {name}')
    for stale in ('preflight_checkpoint_135.py','test_checkpoint_135_contract.py'):
        req(stale not in w,f'CP136 wrapper contains stale checkpoint dependency {stale}')
    req("$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_136.py'" in w,'CP136 wrapper preflight binding mismatch')
    req("$contract=Join-Path $PSScriptRoot 'test_checkpoint_136_contract.py'" in w,'CP136 wrapper contract binding mismatch')

def validate_cp135(repo):
    base=repo/'docs/validation/evidence/checkpoint-136/accepted-cp135'
    z=base/'checkpoint-135-native-results.zip'; req(sha(z)==CP135_RESULTS_SHA,'CP135 native-results ZIP hash')
    s=js(base/'CP135_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==135 and s['failedGates']==[],'CP135 accepted identity')
    req(s['pythonTestsPassed']==211 and s['xunitPassed']==913 and s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25 and s['cp135KernelTestsPassed']==7,'CP135 accepted deterministic gates')
    req(s['substantiveTrials']==1960000 and s['substantiveTrialErrors']==0 and s['substantiveMechanicsFlags']==0,'CP135 accepted substantive evidence')

def validate_frozen_surfaces(repo):
    old=manifest(repo/CP135_MANIFEST)
    for rel,h in old.items():
        if rel.startswith(('src/','tests/')):
            req((repo/rel).is_file(),f'CP135 frozen file missing {rel}'); req(sha(repo/rel)==h,f'CP135 production/test drift {rel}')
    for rel in ('tools/simulation/starcluster_research/canonical_combat.py','tools/simulation/starcluster_research/ecology.py','tools/simulation/starcluster_research/canonical_mechanics.py','docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json'):
        req(rel in old,f'CP135 manifest missing {rel}'); req(sha(repo/rel)==old[rel],f'CP135 frozen mechanics/storyboard drift {rel}')
    archived='docs/archive/concepts/Star_Cluster_Game_Concept_v0.7v.docx'
    req(old.get('docs/Star_Cluster_Game_Concept_v0.7v.docx') is not None,'CP135 active Concept hash missing')
    req(sha(repo/archived)==old['docs/Star_Cluster_Game_Concept_v0.7v.docx'],'archived v0.7v Concept must be exact CP135 copy')

def validate_matrix(repo):
    old=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_7.json')
    new=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_8.json')
    req(new['checkpoint']==136 and new['schemaVersion'].endswith('v0.8'),'matrix CP136 identity')
    for family,val in old['profiles'].items():
        if family!='armor': req(new['profiles'][family]==val,f'unintended profile drift {family}')
    req(new['combatModifiers']==old['combatModifiers'],'direct-fire modifier drift')
    expected={1:(0,6,0,0),2:(0,8,0,0),3:(1,9,0,0),4:(1,10,0,0),5:(2,10,0,0),6:(1,9,1,1),7:(1,10,1,1),8:(2,11,1,1),9:(3,12,1,2)}
    for tl,want in expected.items():
        p=new['profiles']['armor'][str(tl)]; got=(p['ap'],p['ai'],p['tacticalRegenerationPerTp'],p['tacticalRegenerationCapTp']); req(got==want,f'Armor TL{tl} {got}!={want}'); req(p['baseRegeneration']==0,f'Armor TL{tl} free regen')
    old_seeds={x['id']:x for x in old['candidateBranchSeeds']}; new_seeds={x['id']:x for x in new['candidateBranchSeeds']}
    req(set(old_seeds)==set(new_seeds),'candidate branch ID drift')
    for sid in set(old_seeds)-{'A_b1'}: req(new_seeds[sid]==old_seeds[sid],f'unintended branch drift {sid}')
    a=new_seeds['A_b1']; req(a['placementTl']==6 and a['laterProgression']=='TBD','A_b1 placement/progression'); req(a['tl6']=={'ap':2,'ai':11,'baseRegeneration':0,'tacticalRegenerationPerTp':0,'tacticalRegenerationCapTp':0},'A_b1 TL6 profile')
    rule=new['armorRegenerationCandidateRule']; req(rule['tacticalRegenerationCapTpByTl']=={'6':1,'7':1,'8':1,'9':2},'Armor regen cap rule')
    req(new['profiles']['shield']==old['profiles']['shield'] and new['profiles']['damage_control']==old['profiles']['damage_control'],'CP135 Shield/DamCon must be frozen')
    st=new['sameTlCalibrationContract']; req(st['implementedCheckpoint']==136 and st['mandatoryDefenses']==['shield','armor'] and st['tl6ArmorProfiles']==['mainline','A_b1'],'same-TL contract')

def xlsx_rows(path,sheet_name):
    NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'; RNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'; PKG='{http://schemas.openxmlformats.org/package/2006/relationships}'
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall(NS+'si'): shared.append(''.join(t.text or '' for t in si.iter(NS+'t')))
        wb=ET.fromstring(z.read('xl/workbook.xml')); rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels')); relmap={x.attrib['Id']:x.attrib['Target'] for x in rels.findall(PKG+'Relationship')}; target=None
        for s in wb.find(NS+'sheets'):
            if s.attrib['name']==sheet_name: target=relmap[s.attrib[RNS+'id']]; break
        req(target is not None,f'workbook sheet missing {sheet_name}'); target=('xl/'+target.lstrip('/')) if not target.startswith('/') else target.lstrip('/')
        root=ET.fromstring(z.read(target)); rows=[]
        for row in root.iter(NS+'row'):
            vals={}
            for c in row.findall(NS+'c'):
                ref=c.attrib['r']; col=re.match(r'[A-Z]+',ref).group(0); typ=c.attrib.get('t'); v=c.find(NS+'v'); isel=c.find(NS+'is'); raw=''
                if typ=='s' and v is not None: raw=shared[int(v.text)]
                elif typ=='inlineStr' and isel is not None: raw=''.join(t.text or '' for t in isel.iter(NS+'t'))
                elif v is not None: raw=v.text or ''
                vals[col]=raw
            rows.append(vals)
        return rows

def validate_workbook(repo):
    path=repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8c.xlsx'
    rows=xlsx_rows(path,'Numerical Baseline'); found={}
    for r in rows:
        if r.get('A') in ('armor','armor_A_b1') and r.get('B'):
            key=(r['A'],int(float(r['B']))); req(key not in found,f'duplicate workbook key {key}'); found[key]=(json.loads(r['D']),r.get('C',''),r.get('E',''))
    req(len(found)==10,'workbook Armor row count')
    matrix=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_8.json')
    for tl in range(1,10):
        char,name,note=found[('armor',tl)]; src=matrix['profiles']['armor'][str(tl)]
        for k,v in char.items(): req(src.get(k)==v,f'workbook/matrix mismatch Armor TL{tl} {k}')
    b=found[('armor_A_b1',6)][0]; req((b['ap'],b['ai'],b['tacticalRegenerationCapTp'])==(2,11,0),'workbook A_b1')
    overview=' '.join(v for r in xlsx_rows(path,'Overview') for v in r.values())
    req('A_b1 Crystalline AP2/AI11' in overview,'Overview stale A_b1 value'); req('TL6-TL8' in overview and '1 AI per TP' in overview and 'TL9' in overview and '2-TP cap' in overview,'Overview regen rule')
    lineage=xlsx_rows(path,'Lineage Map'); req(any(r.get('B')=='Crystalline Armor Branch' and r.get('D')=='Crystalline Composite Armor' and r.get('G')=='armor_A_b1 TL6' for r in lineage),'Lineage Map missing Crystalline branch')

def docx_all_text(path):
    with zipfile.ZipFile(path) as z:
        chunks=[z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/') and n.endswith('.xml')]
    return re.sub(r'<[^>]+>',' ',' '.join(chunks)).replace('&gt;','>').replace('&lt;','<').replace('&amp;','&')
def validate_concept(repo):
    active=repo/'docs/Star_Cluster_Game_Concept_v0.7w.docx'; req(active.is_file(),'active Concept v0.7w')
    t=docx_all_text(active)
    for phrase in ('Version 0.7w','August 19, 2026','TL6-TL8','at most 1 TP per turn','TL9','at most 2 TP per turn','AP2/AI11'):
        req(phrase in t,f'Concept missing {phrase}')
    req('Version 0.7v' not in t,'stale Concept version metadata')

def validate_study(repo):
    s=js(repo/'docs/archive/testing/pre-cp165-active/cp136_armor_rebaseline_study_v0_1.json')
    req(s['checkpoint']==136 and s['schemaVersion']=='star-cluster-cp136-armor-rebaseline-v0.1' and s['canonicalKernelVersion']=='0.3','study identity')
    req(s['sourceMatrix'].endswith('technology_numerical_matrix_v0_8.json'),'study matrix'); req(s['masterSeed']==134001,'master seed'); req(s['expected']['logicalContexts']==196 and s['expected']['generatedVariants']==392 and s['expected']['tl6Variants']==136 and s['expected']['substantiveTrials']==1960000,'study shape')

def validate_python_dependencies(repo):
    roots=[repo/'tools/checkpoints/checkpoint-136',repo/'tools/simulation/tests/test_cp136_armor_rebaseline.py']
    bad=[]; count=0
    for root in roots:
        paths=[root] if root.is_file() else list(root.rglob('*.py'))
        for p in paths:
            count+=1
            tree=ast.parse(p.read_text(encoding='utf-8-sig'))
            for n in ast.walk(tree):
                if isinstance(n,ast.Import): names=[x.name.split('.')[0] for x in n.names]
                elif isinstance(n,ast.ImportFrom): names=[(n.module or '').split('.')[0]]
                else: continue
                for name in names:
                    if name and name not in sys.stdlib_module_names and name!='starcluster_research': bad.append(f'{p.relative_to(repo)}:{n.lineno}:{name}')
    req(not bad,'non-stdlib CP136 checkpoint/test dependency: '+', '.join(bad[:8])); return count

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        validate_wrapper_contract(repo); validate_cp135(repo); validate_frozen_surfaces(repo); validate_matrix(repo); validate_workbook(repo); validate_concept(repo); validate_study(repo)
        count=validate_python_dependencies(repo)
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); req(count_suite(suite)==218,f'Python test discovery expected 218 got {count_suite(suite)}')
        print(f'       CP136 preflight passed: wrapper dependencies verified; accepted CP135 evidence; Armor/A_b1-only delta; workbook/Concept/study synchronized; 218 Python tests discovered; {count} CP136 stdlib-only Python surfaces inspected.')
        return 0
    except Exception as e:
        print(f'CP136 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
