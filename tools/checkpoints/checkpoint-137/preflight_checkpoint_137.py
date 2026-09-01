#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re, sys, unittest, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
CP136_SHA='043a20f32996af09c414bbc293f597b73be8b11bcd837119c4e90c900c973e8d'

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def validate_wrapper(repo):
    w=text(repo/'tools/checkpoints/checkpoint-137/apply_checkpoint_137.ps1')
    req("$preflight=Join-Path $PSScriptRoot 'preflight_checkpoint_137.py'" in w,'wrapper preflight binding')
    req("$contract=Join-Path $PSScriptRoot 'test_checkpoint_137_contract.py'" in w,'wrapper contract binding')
    req("$study='docs/archive/testing/pre-cp165-active/cp137_finite_armor_regeneration_study_v0_1.json'" in w,'wrapper study binding')
    req('preflight_checkpoint_136.py' not in w and 'test_checkpoint_136_contract.py' not in w,'stale CP136 wrapper dependency')
    req('checkpoint=137;' in w,'repository-only summary checkpoint')

def validate_cp136(repo):
    base=repo/'docs/validation/evidence/checkpoint-137/accepted-cp136'
    z=base/'checkpoint-136-native-results.zip'; req(sha(z)==CP136_SHA,'CP136 native results hash')
    s=js(base/'CP136_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==136 and s['failedGates']==[],'CP136 accepted identity')
    req((s['pythonTestsPassed'],s['xunitPassed'],s['scenarioRunnerSelfTestsPassed'],s['researchParityPassed'],s['cp136KernelTestsPassed'])==(218,913,70,25,7),'CP136 deterministic gates')
    req(s['substantiveTrials']==1960000 and s['substantiveTrialErrors']==0 and s['substantiveMechanicsFlags']==0,'CP136 substantive acceptance')

def validate_matrix(repo):
    old=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_8.json')
    new=js(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')
    req(new['checkpoint']==137 and new['schemaVersion'].endswith('v0.9'),'matrix identity')
    # All non-Armor profiles are frozen byte-for-data.
    for fam,val in old['profiles'].items():
        if fam!='armor': req(new['profiles'][fam]==val,f'unintended profile drift {fam}')
    # Armor numeric values held; only reserve field/notes are new.
    reserves={6:3,7:4,8:5,9:6}
    for tl in range(1,10):
        a=old['profiles']['armor'][str(tl)]; b=new['profiles']['armor'][str(tl)]
        for k in ('ap','ai','baseRegeneration','tacticalRegenerationPerTp','tacticalRegenerationCapTp','space'):
            req(a.get(k)==b.get(k),f'Armor TL{tl} numeric drift {k}')
        req(int(b.get('combatRegenerationReserveAi',-99))==reserves.get(tl,0),f'Armor TL{tl} reserve')
    old_seeds={x['id']:x for x in old['candidateBranchSeeds']}; new_seeds={x['id']:x for x in new['candidateBranchSeeds']}
    req(set(old_seeds)==set(new_seeds),'branch IDs')
    for sid in set(old_seeds)-{'A_b1'}: req(new_seeds[sid]==old_seeds[sid],f'branch drift {sid}')
    oa=old_seeds['A_b1']['tl6']; na=new_seeds['A_b1']['tl6']
    for k in ('ap','ai','baseRegeneration','tacticalRegenerationPerTp','tacticalRegenerationCapTp'): req(oa[k]==na[k],f'A_b1 drift {k}')
    req(na['combatRegenerationReserveAi']==0,'A_b1 reserve')
    rule=new['armorRegenerationCandidateRule']; req(rule['combatRegenerationReserveAiByTl']=={'6':3,'7':4,'8':5,'9':6},'reserve rule')
    req('deferred' in rule['outOfCombatRecovery'].lower(),'out-of-combat deferred')
    req(new['profiles']['reactor']==old['profiles']['reactor'],'Reactor must be frozen')

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
        req(target is not None,f'missing sheet {sheet_name}'); target=('xl/'+target.lstrip('/')) if not target.startswith('/') else target.lstrip('/')
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
    path=repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8d.xlsx'
    rows=xlsx_rows(path,'Numerical Baseline'); found={}
    for r in rows:
        if r.get('A') in ('armor','armor_A_b1') and r.get('B'):
            key=(r['A'],int(float(r['B']))); req(key not in found,f'duplicate workbook key {key}'); found[key]=json.loads(r['D'])
    req(len(found)==10,'workbook Armor row count')
    reserves={6:3,7:4,8:5,9:6}
    for tl in range(1,10): req(found[('armor',tl)]['combatRegenerationReserveAi']==reserves.get(tl,0),f'workbook reserve TL{tl}')
    req(found[('armor_A_b1',6)]['combatRegenerationReserveAi']==0,'workbook A_b1 reserve')
    ov=' '.join(v for r in xlsx_rows(path,'Overview') for v in r.values())
    req('3/4/5/6 AI' in ov and 'Out-of-combat' in ov and 'Reactor' in ov,'Overview reserve/recovery/frozen Reactor wording')
    req(any(r.get('A')=='Decision' and 'finite in-combat Armor regeneration reserve' in r.get('B','') for r in xlsx_rows(path,'CP137 Revision')),'CP137 Revision sheet')

def docx_text(path):
    with zipfile.ZipFile(path) as z: chunks=[z.read(n).decode('utf-8','ignore') for n in z.namelist() if n.startswith('word/') and n.endswith('.xml')]
    return re.sub(r'<[^>]+>',' ',' '.join(chunks)).replace('&gt;','>').replace('&lt;','<').replace('&amp;','&')
def validate_concept(repo):
    p=repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx'; req(p.is_file(),'Concept v0.7x')
    t=docx_text(p)
    for phrase in ('Version 0.7x','3, 4, and 5 AI respectively','6-AI reserve','Once the reserve is exhausted','Out of combat','AP2/AI11'):
        req(phrase in t,f'Concept missing {phrase}')
    req('Version 0.7w' not in t,'stale Concept version')

def validate_study(repo):
    s=js(repo/'docs/archive/testing/pre-cp165-active/cp137_finite_armor_regeneration_study_v0_1.json')
    req(s['checkpoint']==137 and s['schemaVersion']=='star-cluster-cp137-finite-armor-regeneration-v0.1' and s['canonicalKernelVersion']=='0.4','study identity')
    req(s['sourceMatrix'].endswith('technology_numerical_matrix_v0_9.json'),'study matrix')
    req(s['masterSeed']==134001,'master seed')
    req(s['expected']['logicalContexts']==196 and s['expected']['generatedVariants']==392 and s['expected']['tl6Variants']==136 and s['expected']['substantiveTrials']==1960000,'study shape')
    req(s['armorRegenerationDoctrine']['inCombatReserveAiByTl']=={'6':3,'7':4,'8':5,'9':6},'study reserve')
    req(s['armorRegenerationDoctrine']['outOfCombatRecoverySimulated'] is False,'OOC not simulated')

def validate_code(repo):
    c=text(repo/'src/StarCluster.Core/Combat/Damage/ArmorTacticalRegenerationService.cs')
    for x in ('combatRegenerationReserveAi','CombatRegenerationReserveRemaining','maximumRestorable'):
        req(x in c,f'C# reserve service missing {x}')
    e=text(repo/'tools/simulation/starcluster_research/ecology.py'); req('armor_regen_reserve_remaining' in e and 'armor_regen_denied_exhausted' in e,'Python reserve state/telemetry')
    cc=text(repo/'tools/simulation/starcluster_research/canonical_combat.py'); req('CANONICAL_COMBAT_KERNEL_VERSION = "0.4"' in cc,'kernel v0.4')
    a=text(repo/'tools/simulation/starcluster_research/same_tl_candidate_baseline_analysis.py'); req('137:"star-cluster-cp137-finite-armor-regeneration-v0.1"' in a and 'armorRegenerationReserveTelemetryPresent' in a,'study validator/telemetry')

def validate_python_dependencies(repo):
    roots=[repo/'tools/checkpoints/checkpoint-137',repo/'tools/simulation/tests/test_cp137_finite_armor_regeneration.py']
    bad=[]; count=0
    for root in roots:
        paths=[root] if root.is_file() else list(root.rglob('*.py'))
        for p in paths:
            count+=1; tree=ast.parse(p.read_text(encoding='utf-8-sig'))
            for n in ast.walk(tree):
                if isinstance(n,ast.Import): names=[x.name.split('.')[0] for x in n.names]
                elif isinstance(n,ast.ImportFrom): names=[(n.module or '').split('.')[0]]
                else: continue
                for name in names:
                    if name and name not in sys.stdlib_module_names and name!='starcluster_research': bad.append(f'{p.relative_to(repo)}:{n.lineno}:{name}')
    req(not bad,'non-stdlib CP137 dependency '+', '.join(bad[:6])); return count

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        validate_wrapper(repo); validate_cp136(repo); validate_matrix(repo); validate_workbook(repo); validate_concept(repo); validate_study(repo); validate_code(repo)
        count=validate_python_dependencies(repo)
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); req(count_suite(suite)==226,f'Python discovery expected 226 got {count_suite(suite)}')
        print(f'       CP137 preflight passed: wrapper dependencies verified; accepted CP136 evidence pinned; finite 3/4/5/6 AI reserve only; Reactor/numerics frozen; workbook/Concept/study/code synchronized; 226 Python tests discovered; {count} CP137 stdlib-only Python surfaces inspected.')
        return 0
    except Exception as e:
        print(f'CP137 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
