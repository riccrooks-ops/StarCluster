#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys, zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}

def require(c,m):
    if not c: raise AssertionError(m)
def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def read_json(p): require(p.is_file(),f'Missing JSON: {p}'); return json.loads(p.read_text(encoding='utf-8-sig'))
def read_text(p): require(p.is_file(),f'Missing text: {p}'); return p.read_text(encoding='utf-8-sig')
def is_repo_owned(rel):
    p=Path(rel)
    if any(x in EXCLUDED_PARTS for x in p.parts) or p.name in EXCLUDED_FILES: return False
    return not any(p.name.lower().endswith(s) for s in EXCLUDED_SUFFIXES)
def docx_text(p):
    require(p.is_file(),f'Missing Concept: {p}')
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(p) as z: root=ET.fromstring(z.read('word/document.xml'))
    return '\n'.join(''.join(t.text or '' for t in q.findall('.//w:t',ns)) for q in root.findall('.//w:p',ns))
def validate_production_boundary(repo):
    for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
        root=repo/rel; require(root.is_dir(),f'Missing production tree: {rel}')
        py=list(root.rglob('*.py')); require(not py,f'Python leaked into production runtime: {py[0].relative_to(repo) if py else ""}')
        for p in root.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in {'.cs','.csproj','.props','.targets'}: continue
            text=p.read_text(encoding='utf-8-sig',errors='ignore').lower()
            for marker in ('python.runtime','pythonnet','ironpython','python.exe','python3.exe'):
                require(marker not in text,f'Production runtime references Python marker {marker}: {p.relative_to(repo)}')
def validate_frozen(repo):
    evidence=repo/'docs/validation/evidence/checkpoint-109/CP108_FROZEN_RUNTIME_TEST_SIMULATION_SHA256SUMS.txt'
    n=0
    for line in read_text(evidence).splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); require(m is not None,f'Malformed frozen row: {line}')
        h,rel=m.groups(); p=repo/rel
        require(p.is_file(),f'Frozen CP108 file missing: {rel}')
        require(sha256(p)==h,f'Frozen CP108 runtime/test/simulation file drifted: {rel}')
        n+=1
    require(n==1150,f'Expected 1150 frozen CP108 runtime/test/simulation files, found {n}')
    return n
def validate_manifest(repo):
    p=repo/'CHECKPOINT_109_SHA256SUMS.txt'; require(p.is_file(),'CHECKPOINT_109_SHA256SUMS.txt missing')
    listed={}
    for line in read_text(p).splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); require(m is not None,f'Malformed manifest row: {line}')
        h,rel=m.groups(); require(rel not in listed,f'Duplicate manifest path: {rel}'); listed[rel]=h
    actual={}
    for q in repo.rglob('*'):
        if not q.is_file(): continue
        rel=q.relative_to(repo).as_posix()
        if rel=='CHECKPOINT_109_SHA256SUMS.txt' or not is_repo_owned(rel): continue
        actual[rel]=sha256(q)
    require(set(actual)==set(listed),f'Manifest path set mismatch: actual {len(actual)}, manifest {len(listed)}')
    for rel,h in actual.items(): require(listed[rel]==h,f'Manifest hash mismatch: {rel}')
    return len(actual)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); args=ap.parse_args(); repo=Path(args.repo).resolve()
    print('       Validating accepted CP108 provenance and frozen runtime/test/simulation surfaces...')
    require(sha256(repo/'CHECKPOINT_108_SHA256SUMS.txt')=='0c91e50991e72cdc3c98051d1545829fe40f4123b8da2b5e5e1cfab7b741f847','Accepted CP108 manifest hash drifted.')
    frozen=validate_frozen(repo)
    require(sha256(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_2.json')=='68fcefc8c7a42fea643de28e984812adfc63e35dc3685ba21e85e9c37a65e450','CP108 qualitative table drifted.')
    require(sha256(repo/'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_2.json')=='450c6dce341dd40cf60276659d886ea2f6bbb76ff724f29753b90718466391c4','CP108 Storyboard drifted.')

    print('       Validating complete TL1-TL9 numerical candidate matrix...')
    definition=read_json(repo/'tools/checkpoints/checkpoint-109/checkpoint_109_architecture_definition.json')
    require(definition['checkpointId']=='109' and definition['acceptedBaseline']=='108','CP109 definition identity drifted.')
    require(definition['productionRuntime']=='C# / Godot' and definition['pythonAllowedForTestingSimulationAndCheckpointValidation'] is True and definition['pythonRequiredByProductionRuntime'] is False,'Runtime/testing boundary drifted.')
    require(definition['wholeLadderNumericalCandidateBuilt'] is True and definition['existingProductionRuntimeValuesChanged'] is False,'CP109 candidate/runtime boundary drifted.')
    require(definition['simulationOrCalibrationRun'] is False and int(definition['declaredTrials'])==0,'CP109 may not run calibration.')
    runtime=read_json(repo/'tools/checkpoints/checkpoint-109/PYTHON_RUNTIME.json')
    require(runtime=={'schemaVersion':1,'implementation':'CPython','majorMinor':'3.13','stdlibOnly':True,'purpose':'Deterministic Star Cluster checkpoint validation and testing infrastructure','productionBoundary':'The shipped C# / Godot game runtime must not require Python.'},'CP109 Python runtime contract drifted.')

    m=read_json(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')
    require(m['schemaVersion']=='star-cluster-whole-ladder-numerical-matrix-v0.1','Matrix schema/version drifted.')
    require(m['status']=='provisional_whole_ladder_candidate_no_calibration','Matrix lifecycle status drifted.')
    v=m['validation']; require(v=={'profileFamilies':16,'profileRows':144,'qualitativeStoryboardBeats':214,'disciplines':10,'hardGateCount':16,'standardSparseGateCount':4,'branchGateCount':12,'calibrationTrials':0},f'Matrix validation summary drifted: {v}')
    require(set(m['profiles'])=={'hull','armor','reactor','stl','ftl','computer','sensor','ecm','eccm','shield','kinetic_main','kinetic_pds','energy_main','energy_pds','missile_delivery','amm_pds'},'Profile-family set drifted.')
    for fam,rows in m['profiles'].items():
        require(set(rows)=={str(x) for x in range(1,10)},f'{fam} must contain TL1-TL9')
        for tl,row in rows.items(): require(int(row['tl'])==int(tl),f'{fam} TL key/value mismatch')
    require(len(m['overview'])==90 and len(m['branches'])==31 and len(m['hardPrerequisites'])==16 and len(m['lowerTlReconciliation'])==7 and len(m['wholeShipSanity'])==9,'Whole-ladder collection counts drifted.')
    require(m['authorityBoundary']['calibrationRun'] is False and m['authorityBoundary']['monteCarloRun'] is False,'Matrix may not claim calibration/Monte Carlo.')
    require(m['authorityBoundary']['productionRuntime']=='C# / Godot','Matrix production runtime boundary drifted.')

    # Storyboard/qualitative alignment and tall-play gate density.
    qual=read_json(repo/'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_2.json')
    entries=qual['lineageEntries']; require(len(entries)==214 and len(qual['standardLineages'])==10,'CP108 qualitative counts drifted.')
    std=Counter()
    for e in entries:
        if e.get('adoptedInProvisionalTable') and e.get('normalPlayerTlRange') and e.get('standardSpine'): std[e['discipline']]+=1
    gated=Counter()
    ids=set()
    for g in m['hardPrerequisites']:
        require(g['id'] not in ids,f'Duplicate gate id: {g["id"]}'); ids.add(g['id'])
        require(1<=int(g['ownerTl'])<=9 and 1<=len(g['requires'])<=2,f'Invalid prerequisite cardinality/TL: {g["id"]}')
        for r in g['requires']: require(1<=int(r['tl'])<=9,f'Invalid external prereq TL: {g["id"]}')
        if g['kind']=='standard_sparse_gate': gated[g['owner']]+=1
    require(sum(gated.values())==4,'Exactly four standard-spine gates expected in v0.1.')
    for disc,count in std.items(): require(gated[disc] < max(2,count/2),f'Hard gating is too dense for tall play in {disc}')

    # Key Storyboard-driven lower-TL corrections and family-introduction cadence.
    p=m['profiles']
    require((p['reactor']['1']['operationalTp'],p['reactor']['2']['operationalTp'],p['reactor']['3']['operationalTp'])==(5,7,7),'Fusion lower-ladder frontier/maturation cadence drifted.')
    require((p['reactor']['2']['degradedTp'],p['reactor']['2']['emergencyTp'])==(3,0) and p['reactor']['3']['space']==5,'Early/Mature Fusion resilience/Space identity drifted.')
    require(p['kinetic_pds']['2']['newTech'] is False and p['kinetic_pds']['2']['baseChancePp']==10 and p['kinetic_pds']['3']['baseChancePp']==13,'TL2/TL3 Kinetic PDS reconciliation drifted.')
    require(p['energy_main']['2']['range']==6 and p['energy_main']['2']['accuracyPp']==30 and p['energy_main']['2']['standardDamage']==3,'TL2 Energy optics/pulse candidate drifted.')
    require(p['missile_delivery']['2']['missileMove']==3 and p['missile_delivery']['2']['range']==8 and p['missile_delivery']['2']['warheadDamage']==5,'TL2 Missile delivery-only improvement drifted.')
    require((p['sensor']['1']['passiveFirm'],p['sensor']['1']['passiveApprox'],p['sensor']['1']['activeLowFirm'],p['sensor']['1']['activeLowApprox'],p['sensor']['1']['overloadFirm'],p['sensor']['1']['overloadApprox'])==(1,3,3,4,4,5),'TL1 Balanced-0 Sensor authority drifted.')
    require(p['stl']['5']['move']==6 and p['stl']['6']['move']==6 and p['stl']['8']['move']==9,'Uneven STL frontier/maturation cadence drifted.')
    require(p['ftl']['5']['strategicMove']==4,'TL5 FTL qualitative/geometry hold drifted.')
    require(p['armor']['7']['newTech'] is False and p['armor']['8']['newTech'] is False,'Passive Armor TL7/TL8 quiet steps drifted.')
    require(p['missile_delivery']['5']['newTech'] is True and p['missile_delivery']['8']['newTech'] is True,'Native seeker advances at Missile TL5/TL8 must be represented even when delivery hardware holds.')

    # Foundation constraints and bounded ranges.
    abl=next((x for x in m['branches'] if x['id']=='ablative-armor'),None); require(abl and abl['space']==1,'TL1 Ablative Armor must cost 1 Space.')
    for fam in ('sensor','kinetic_main','energy_main','missile_delivery'):
        for tl,row in p[fam].items():
            for key in ('range','passiveFirm','passiveApprox','activeLowFirm','activeLowApprox','activeHighFirm','activeHighApprox','overloadFirm','overloadApprox'):
                val=row.get(key)
                if isinstance(val,(int,float)): require(0<=val<=10,f'Current-map range bound exceeded: {fam} TL{tl} {key}={val}')
    # Recompute whole-ship Space sanity exactly.
    main={str(t):max(p['kinetic_main'][str(t)]['space'],p['energy_main'][str(t)]['space'],p['missile_delivery'][str(t)]['space']) for t in range(1,10)}
    recomputed=[]
    for t in range(1,10):
        k=str(t); mandatory=main[k]+p['reactor'][k]['space']+p['stl'][k]['space']+p['ftl'][k]['space']+p['computer'][k]['space']+p['sensor'][k]['space']; dual=2*main[k]+2*p['reactor'][k]['space']+p['stl'][k]['space']+p['ftl'][k]['space']+p['computer'][k]['space']+p['sensor'][k]['space']
        recomputed.append({'tl':t,'hullCapacity':p['hull'][k]['capacity'],'mandatoryCore':mandatory,'mandatorySpare':p['hull'][k]['capacity']-mandatory,'dualMainDualReactorCore':dual,'dualMainDualReactorLegalBeforeOptionalSystems':dual<=p['hull'][k]['capacity']})
    require(recomputed==m['wholeShipSanity'],'Whole-ship Space sanity is not derived from current profile values.')

    # Companion artifacts are exact reviewed v0.1 outputs.
    require(sha256(repo/'docs/archive/player_technology/pre-cp165-active/StarCluster_TL1_TL9_Candidate_Numerical_Technology_Matrix_v0_1.xlsx')=='722ed63856e96a8f171ad18c1d004d469def7cc8e8487c2a722eadf844862c3c','Candidate workbook drifted from reviewed artifact.')
    require(sha256(repo/'docs/archive/player_technology/pre-cp165-active/TL1_TL9_Candidate_Numerical_Technology_Matrix_v0_1.md')=='faef80026e6abfb1aad076542d15178c917f3cbbd39e96a141a993316c9931ee','Candidate Markdown table drifted from reviewed artifact.')
    require(sha256(repo/'docs/design/player_technology/Technology_Numerical_Matrix_Review_v1.md')=='ead66bfa66265528893547157e3cc7d3737f99048b3de24fc4c56c4d50645b78','Numerical review report drifted.')

    print('       Validating Concept/document consistency and production/testing boundary...')
    active=[q.name for q in (repo/'docs').glob('Star_Cluster_Game_Concept*.docx')]
    require(active==['Star_Cluster_Game_Concept_v0.7i.docx'],f'Exactly Concept v0.7i must be active; found {active}')
    concept=docx_text(repo/'docs/Star_Cluster_Game_Concept_v0.7i.docx')
    for phrase in ('Version 0.7i','Checkpoint 109 creates the first complete whole-ladder numerical candidate surface','7 Operational / 3 Degraded / 0 Emergency','Candidate != implemented != calibrated != promoted','automatically when the final missing prerequisite TL is researched','C-079'):
        require(phrase in concept,f'Concept v0.7i missing required text: {phrase}')
    validation_files=sorted(q.name for q in (repo/'docs/validation').glob('Checkpoint_*.md'))
    require(validation_files==['Checkpoint_109_Whole_Ladder_Candidate_Numerical_Technology_Matrix.md'],f'Only CP109 active checkpoint runbook expected; found {validation_files}')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/Prototype_TODO.md'):
        text=read_text(repo/rel); require('109' in text and '108' in text,f'Active doc must recognize CP108 baseline and CP109 candidate: {rel}')
    validate_production_boundary(repo)

    print('       Validating full repository manifest...')
    count=validate_manifest(repo)
    print(f'       CP109 contract verified: {count} repository-owned files; {frozen} frozen CP108 runtime/test/simulation files; 10 disciplines / 32 lineages / 214 beats; 16 profile families / 144 TL profiles / 31 branch candidates / 16 sparse hard gates; zero trials; no production promotion.')
    return 0

if __name__=='__main__':
    try: raise SystemExit(main())
    except AssertionError as e:
        print(f'CP109 CONTRACT FAILURE: {e}',file=sys.stderr); raise SystemExit(1)
