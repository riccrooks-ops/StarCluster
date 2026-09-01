#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re, sys, unittest, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP134_RESULTS_SHA='00dbbad6513905848995f37674c66cc3f43bcbf9cfe302152ea6b738d8c227b4'
CP134_MANIFEST='docs/validation/evidence/checkpoint-134/CP134_REPOSITORY_SHA256SUMS.txt'

def req(v,m):
    if not v: raise AssertionError(m)
def text(p): req(p.is_file(),f'missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def manifest(p):
    out={}
    for line in text(p).splitlines():
        if line.strip(): h,r=line.split('  ',1);out[r]=h
    return out
def count_suite(suite): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in suite)

def validate_cp134(repo):
    base=repo/'docs/validation/evidence/checkpoint-135/accepted-cp134'
    z=base/'checkpoint-134-native-results.zip'; req(sha(z)==CP134_RESULTS_SHA,'CP134 native-results ZIP hash')
    s=js(base/'CP134_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==134 and s['failedGates']==[],'CP134 accepted identity')
    req(s['pythonTestsPassed']==204 and s['xunitPassed']==913 and s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25 and s['cp134KernelTestsPassed']==8,'CP134 accepted deterministic gates')
    req(s['substantiveTrials']==1960000 and s['substantiveTrialErrors']==0 and s['substantiveMechanicsFlags']==0,'CP134 accepted substantive evidence')

def validate_frozen_surfaces(repo):
    old=manifest(repo/CP134_MANIFEST)
    # Production C# and xUnit remain byte-frozen from authored CP134.
    for rel,h in old.items():
        if rel.startswith(('src/','tests/')):
            req((repo/rel).is_file(),f'CP134 frozen file missing {rel}')
            req(sha(repo/rel)==h,f'CP134 production/test drift {rel}')
    for rel in ('docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json','docs/archive/testing/pre-cp165-active/canonical_combat_kernel_fixtures_v0_1.json'):
        req(sha(repo/rel)==old[rel],f'CP134 frozen authority drift {rel}')
    archived='docs/archive/concepts/Star_Cluster_Game_Concept_v0.7u.docx'
    req(sha(repo/archived)==old['docs/Star_Cluster_Game_Concept_v0.7u.docx'],'archived v0.7u Concept must be exact CP134 copy')

def validate_matrix(repo):
    old=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_6.json')
    new=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_7.json')
    req(new['checkpoint']==135 and new['schemaVersion'].endswith('v0.7'),'matrix CP135 identity')
    for family,val in old['profiles'].items():
        if family not in ('shield','damage_control'):
            req(new['profiles'][family]==val,f'unintended profile drift {family}')
    req(new['combatModifiers']==old['combatModifiers'],'direct-fire modifier drift')
    req(new['candidateBranchSeeds']==old['candidateBranchSeeds'],'candidate branch drift')
    shields=[(4,1,1,2,0),(5,2,1,2,0),(6,2,1,2,0),(7,2,1,3,0),(8,3,1,3,0),(8,3,1,3,0),(9,3,1,4,0),(10,4,2,2,1),(12,6,2,2,1)]
    kits=[3,3,4,4,5,5,6,6,7]
    for i,tl in enumerate(range(1,10)):
        sh=new['profiles']['shield'][str(tl)]
        got=(sh['capacity'],sh['baseRecharge'],sh['tacticalRechargePerTp'],sh['tacticalRechargeCapTp'],sh['shieldArmor'])
        req(got==shields[i],f'shield TL{tl} {got}')
        req(sh['baseRecharge']+sh['tacticalRechargePerTp']*sh['tacticalRechargeCapTp'] < sh['capacity'],f'shield TL{tl} still fully resets from collapse')
        dc=new['profiles']['damage_control'][str(tl)]
        req(dc['preparedRepairKits']==kits[i],f'Damage Control kits TL{tl}')
        # Repair odds/yield are held from CP134 matrix.
        odc=old['profiles']['damage_control'][str(tl)]
        for k in ('capacity','attemptTp','degradedToOperationalChancePp','disabledToDegradedChancePp','hullRepairChancePp','hullRestoredPerSuccessfulKit','destroyedFieldRepairable'):
            req(dc[k]==odc[k],f'Damage Control non-kit drift TL{tl} {k}')
    rule=new['damageControlCandidateRule']; req(rule['preparedRepairKitsByTl']=={str(i+1):v for i,v in enumerate(kits)},'Damage Control candidate rule kits'); req(rule['studyDoctrine']=='HullOnlyWhenDamaged' and rule['componentRepairInCp135Study'] is False and rule['armorRegenerationSeparate'] is True,'Damage Control doctrine')
    st=new['sameTlCalibrationContract']; req(st['implementedCheckpoint']==135 and st['mandatoryDefenses']==['shield','armor'] and st['tl6ArmorProfiles']==['mainline','A_b1'],'same-TL contract')

def xlsx_rows(path,sheet_name):
    NS='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    RNS='{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    PKG='{http://schemas.openxmlformats.org/package/2006/relationships}'
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall(NS+'si'):
                shared.append(''.join(t.text or '' for t in si.iter(NS+'t')))
        wb=ET.fromstring(z.read('xl/workbook.xml'))
        rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        relmap={x.attrib['Id']:x.attrib['Target'] for x in rels.findall(PKG+'Relationship')}
        target=None
        for s in wb.find(NS+'sheets'):
            if s.attrib['name']==sheet_name: target=relmap[s.attrib[RNS+'id']]; break
        req(target is not None,f'workbook sheet missing {sheet_name}')
        if not target.startswith('/'): target='xl/'+target.lstrip('/')
        else: target=target.lstrip('/')
        root=ET.fromstring(z.read(target))
        rows=[]
        for row in root.iter(NS+'row'):
            vals={}
            for c in row.findall(NS+'c'):
                ref=c.attrib['r']; col=re.match(r'[A-Z]+',ref).group(0); typ=c.attrib.get('t')
                v=c.find(NS+'v'); isel=c.find(NS+'is')
                raw=''
                if typ=='s' and v is not None: raw=shared[int(v.text)]
                elif typ=='inlineStr' and isel is not None: raw=''.join(t.text or '' for t in isel.iter(NS+'t'))
                elif v is not None: raw=v.text or ''
                vals[col]=raw
            rows.append(vals)
        return rows

def validate_workbook(repo):
    rows=xlsx_rows(repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8b.xlsx','Numerical Baseline')
    found={}
    for r in rows:
        if r.get('A') in ('shield','damage_control') and r.get('B'):
            found[(r['A'],int(float(r['B'])))]=(json.loads(r['D']),r.get('C',''),r.get('E',''))
    matrix=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_7.json')
    for fam in ('shield','damage_control'):
        for tl in range(1,10):
            req((fam,tl) in found,f'workbook missing {fam} TL{tl}')
            char,name,note=found[(fam,tl)]; src=matrix['profiles'][fam][str(tl)]
            for k,v in char.items(): req(src.get(k)==v,f'workbook/matrix mismatch {fam} TL{tl} {k}')
    _,name,note=found[('damage_control',5)]; req(name=='Expanded prepared repair stores' and 'Prepared Repair Kits increase to 5' in note,'TL5 DamCon note/name not corrected')
    overview=xlsx_rows(repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8b.xlsx','Overview')
    txt=' '.join(v for r in overview for v in r.values())
    req('Collapsed Shields do not fully reset in one recharge window' in txt,'Overview Shield note not corrected')
    req('base recharge + maximum tactical recharge is sufficient to refill full SC' not in txt,'stale Shield full-reset invariant remains in Overview')

def docx_all_text(path):
    with zipfile.ZipFile(path) as z:
        chunks=[]
        for n in z.namelist():
            if n.startswith('word/') and n.endswith('.xml'):
                chunks.append(z.read(n).decode('utf-8','ignore'))
    return re.sub(r'<[^>]+>',' ',' '.join(chunks)).replace('&gt;','>').replace('&lt;','<').replace('&amp;','&')
def validate_concept(repo):
    active=repo/'docs/Star_Cluster_Game_Concept_v0.7v.docx'; req(active.is_file(),'active Concept v0.7v')
    t=docx_all_text(active)
    for phrase in ('Version 0.7v','August 19, 2026','fully collapsed contemporary Shield cannot normally return to full SC','Prepared Repair Kits progress 3/3/4/4/5/5/6/6/7','one Repair Kit whether it succeeds or fails'):
        req(phrase in t,f'Concept missing {phrase}')
    req('Game Concept & Design Draft v0.7u' not in t and 'Version 0.7q' not in t,'stale Concept version metadata')

def validate_sources(repo):
    cc=text(repo/'tools/simulation/starcluster_research/canonical_combat.py')
    req('CANONICAL_COMBAT_KERNEL_VERSION = "0.3"' in cc and '_attempt_hull_damage_control' in cc and '"damcon"' in cc,'kernel v0.3 Hull DamCon integration')
    ec=text(repo/'tools/simulation/starcluster_research/ecology.py')
    for token in ('repair_kits_remaining','pending_hull_repair','damage_control_attempts','damage_control_kits_consumed','damage_control_tp_spent','damage_control_hull_queued','damage_control_hull_restored','def _attempt_hull_damage_control'):
        req(token in ec,f'DamCon implementation/telemetry missing {token}')
    an=text(repo/'tools/simulation/starcluster_research/same_tl_candidate_baseline_analysis.py')
    req('star-cluster-same-tl-candidate-baseline-result-v0.2' in an and 'damage_control_attempts' in an,'same-TL DamCon reporting')
    # No production C# changes in CP135; CP134 C# already carries the gameplay rules.

def validate_python_dependencies(repo):
    roots=[repo/'tools/simulation/starcluster_research',repo/'tools/simulation/tests',repo/'tools/checkpoints/checkpoint-135']
    local={p.stem for r in roots for p in r.rglob('*.py')}|{'starcluster_research'}
    bad=[]; count=0
    for r in roots:
        for p in r.rglob('*.py'):
            count+=1
            tree=ast.parse(p.read_text(encoding='utf-8-sig'))
            for n in ast.walk(tree):
                names=[]
                if isinstance(n,ast.Import): names=[a.name.split('.')[0] for a in n.names]
                elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module.split('.')[0]]
                for name in names:
                    if name not in sys.stdlib_module_names and name not in local: bad.append((p.relative_to(repo).as_posix(),name))
    req(not bad,f'undeclared third-party Python imports {bad[:8]}')
    return count

def validate_tests_and_plan(repo):
    all_suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py')
    req(count_suite(all_suite)==211,f'Python test discovery {count_suite(all_suite)} != 211')
    cp_suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_cp135_recharge_damcon_rebaseline.py')
    req(count_suite(cp_suite)==7,f'CP135 test discovery {count_suite(cp_suite)} != 7')
    cp_test_text=text(repo/'tools/simulation/tests/test_cp135_recharge_damcon_rebaseline.py')
    req('sys.path.insert(0,str(REPO/"tools/simulation"))' in cp_test_text,'CP135 isolated-test import path guard')
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.same_tl_candidate_baseline_analysis import build_plan
    r=build_plan(repo,repo/'docs/archive/testing/pre-cp165-active/cp135_recharge_damcon_rebaseline_study_v0_1.json',None)['summary']
    req(r['failedGates']==[],'CP135 study plan failed')
    req((r['logicalContexts'],r['generatedVariants'],r['tl6Variants'],r['plannedSubstantiveTrials'])==(196,392,136,1960000),'CP135 study shape')
    study=js(repo/'docs/archive/testing/pre-cp165-active/cp135_recharge_damcon_rebaseline_study_v0_1.json')
    req(study['masterSeed']==134001 and study['comparisonBaseline'].startswith('CP134 substantive'),'common-random-number baseline')
    req(study['damageControlDoctrine'].startswith('HullOnlyWhenDamaged'),'DamCon study doctrine')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-135/checkpoint_135_definition.json');req(d['checkpoint']==135 and d['declaredSubstantiveTrials']==1960000 and d['balanceTargets'] is None,'definition')
        print('       Validating accepted CP134 native baseline and provenance...');validate_cp134(repo)
        print('       Verifying CP134 production/tests, Storyboard, and shared fixture remain frozen...');validate_frozen_surfaces(repo)
        print('       Validating narrow Shield/Damage Control numerical delta...');validate_matrix(repo)
        print('       Validating v0.8b workbook synchronization and corrected notes...');validate_workbook(repo)
        print('       Validating active Concept v0.7v recharge/Damage Control semantics...');validate_concept(repo)
        print('       Validating canonical research kernel v0.3 and Damage Control telemetry...');validate_sources(repo)
        count=validate_python_dependencies(repo);print(f'       Active CP135/research Python files inspected: {count}; stdlib-only policy intact.')
        print('       Validating Python discovery counts and full common-random-number study plan...');validate_tests_and_plan(repo)
        print('       CP135 preflight passed: CP134 accepted evidence pinned; only Shield recharge/Repair Kit numerics changed; Hull-only DamCon executes in kernel v0.3; 196 contexts / 392 variants / 136 TL6 variants.')
        return 0
    except Exception as e:
        print(f'CP135 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
