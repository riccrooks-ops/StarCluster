#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
EXPECTED_CP112_MANIFEST_SHA='7e6008eb63ff08f424b9591807b60a07d4d75b2519957054450f8d5ae3af2ae4'
EXPECTED_MATRIX_SHA='91cb29f7e1e0f792e5a2258b1ab0655fe9924c768f4d80b645269fae52384000'
EXPECTED_REACTOR_SHA='ebed51fa16d0ee1c9721b55ca135eb81e23c321a8373dfcb826a1a096371e9a6'


def req(x,msg):
    if not x: raise AssertionError(msg)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def text(p): req(p.is_file(),f'Missing {p}'); return p.read_text(encoding='utf-8-sig')
def js(p): return json.loads(text(p))
def owned(rel):
    p=Path(rel)
    if any(x in EXCLUDED_PARTS for x in p.parts) or p.name in EXCLUDED_FILES:return False
    return not any(p.name.lower().endswith(s) for s in EXCLUDED_SUFFIXES)

def validate_hash_list(repo,rel,expected):
    rows=[x for x in text(repo/rel).splitlines() if x.strip()]
    req(len(rows)==expected,f'{rel} count {len(rows)} != {expected}')
    for line in rows:
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad hash row {line}')
        h,r=m.groups(); p=repo/r; req(p.is_file(),f'missing frozen {r}'); req(sha(p)==h,f'frozen drift {r}')

def docx_text(p):
    req(p.is_file(),f'Missing {p}')
    with zipfile.ZipFile(p) as z:
        chunks=[]
        for n in z.namelist():
            if n=='word/document.xml' or n.startswith('word/header') or n.startswith('word/footer'):
                root=ET.fromstring(z.read(n))
                chunks.extend(e.text or '' for e in root.iter() if e.tag.endswith('}t'))
        return ' '.join(chunks)

def validate_cp112_native(repo):
    root=repo/'docs/validation/evidence/checkpoint-112/native'
    summary=js(root/'CP112_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(summary.get('nativeAccepted') is True and summary.get('pythonVersion')=='3.13.14','CP112 native summary')
    req(summary.get('selfTests')=={'run':36,'failures':0,'errors':0,'skipped':0},'CP112 native self tests')
    req(summary.get('parityPassed') is True and summary.get('parityCases')==25,'CP112 native parity')
    req(summary.get('substantiveVariants')==1200 and summary.get('trialsPerVariant')==2000 and summary.get('totalEngagements')==2400000,'CP112 native scale')
    req(summary.get('failedGates')==[] and summary.get('trialErrors')==0,'CP112 native gates')
    an=js(root/'neighbor-study/analysis.json')
    req(an.get('checkpoint')=='112' and an.get('totalTrials')==2400000 and an.get('failedGates')==[],'CP112 native analysis')

def flatten_beats(story):
    return [(d,l,b) for d in story['disciplines'] for l in d['lineages'] for b in l['beats']]

def validate_architecture(repo,d):
    pt=repo/'docs/design/player_technology'
    arch=js(pt/'weapon_ammunition_warhead_architecture_v0_1.json')
    req(arch['checkpoint']==113 and arch['authorityBoundary']['runsCalibration'] is False,'ammo architecture identity')
    req(arch['normalAmmoAccounting']['kinetic']['subtypeInventory'] is False,'kinetic subtype inventory')
    req(arch['normalAmmoAccounting']['missile']['subtypeInventory'] is False and 'launch' in arch['normalAmmoAccounting']['missile']['selectionTiming'],'missile subtype/commitment')
    req(len(arch['kineticProgression'])==d['expected']['kineticAmmoProgressionRows'],'kinetic progression count')
    req(len(arch['missileWarheadProgression'])==d['expected']['missileWarheadProgressionRows'],'missile progression count')
    req(len(arch['suspendedCp109PayloadCandidates'])==d['expected']['suspendedCp109PayloadCandidates'],'suspended candidate count')
    kin={x['tl']:x for x in arch['kineticProgression']}
    mis={x['tl']:x for x in arch['missileWarheadProgression']}
    req(kin[2]['mode']=='automatic_upgrade' and kin[4]['mode']=='automatic_compatible_upgrade','kinetic strict-dominance expression')
    req(kin[5]['mode']=='selectable_normal' and kin[6]['mode']=='selectable_normal','kinetic selectable tradeoffs')
    req(mis[1]['mode']=='automatic_baseline' and mis[3]['mode']=='selectable_normal' and mis[4]['mode']=='selectable_normal','missile GP/specialist expression')
    req(mis[5]['mode']=='automatic_compatible_upgrade' and mis[7]['mode']=='automatic_compatible_upgrade','missile GP maturation')
    req(mis[6]['mode']=='deferred_specialist' and mis[9]['mode']=='exotic_individually_tracked_if_adopted','missile deferred effects')
    req(arch['combatAssessment']['aiParity'].startswith('AI receives only the same derived assessment'),'AI information parity')
    req('hull penetration confirmed' in [x.lower() for x in arch['combatAssessment']['firmTrackFeedback']],'combat assessment Hull penetration')
    req(len(arch['compatibilityModel']['kineticTags'])>=4 and len(arch['compatibilityModel']['missileTags'])>=4,'compatibility tags')

    story=js(pt/'technology_family_storyboard_v1_3.json'); beats=flatten_beats(story)
    req(len(story['disciplines'])==d['expected']['disciplines'],'discipline count')
    req(sum(len(x['lineages']) for x in story['disciplines'])==d['expected']['lineages'],'lineage count')
    req(len(beats)==d['expected']['storyboardBeats'],'beat count')
    gates=[b for _,_,b in beats if b.get('hardExternalPrerequisites')]
    req(len(gates)==d['expected']['hardExternalPrerequisiteBeats'],'hard gate count')
    gate_sig={(b['tl'],b['title'],tuple((g['discipline'],g['tl']) for g in b['hardExternalPrerequisites'])) for b in gates}
    req((4,'Maneuvering / programmable smart projectile',(('Computing / Fire Control',4),)) in gate_sig,'smart projectile gate')
    req((5,'Fusion microcharge general-purpose warhead',(('Power',2),)) in gate_sig,'fusion gate')
    req((7,'Antimatter general-purpose warhead',(('Power',5),)) in gate_sig,'antimatter gate')
    req(not any('none are established by this storyboard' in x for x in story['principles']),'stale zero-hard-gate principle')
    req(any('automatically' in x.lower() and 'prerequisite' in x.lower() for x in story['principles']),'auto-unlock principle')

    ideas=js(pt/'technology_idea_register_v1_4.json')
    req(len(ideas['ideas'])==d['expected']['ideas'],'idea count')
    im={x['id']:x for x in ideas['ideas']}
    req(im['IDEA-059']['title']=='Antimatter-Catalyzed Warhead','antimatter-catalyzed idea preserved')
    req(im['IDEA-137']['title']=='Fusion Microcharge General-Purpose Warhead','fusion idea normalized')
    req(ideas['cp113Decisions']['newIdeasAdded']==1,'idea decision count')

    fa=js(pt/'Technology_Foundation_Completeness_Audit_v1_3.json')
    req(len(fa['domains'])==d['expected']['foundationDomains'],'foundation domains')
    ammo=next(x for x in fa['domains'] if x['id']=='ammunition-stores')
    req('no pre-battle subtype allocation' in ammo['foundationContract'].lower(),'foundation generic ammo')
    req('exotic' in ammo['foundationContract'].lower(),'foundation exotic ammo')

    ct=js(pt/'technology_component_table_v0_3.json')
    req(len(ct['lineageEntries'])==d['expected']['storyboardBeats'],'component table beat translation')
    req(len(ct['lineageExpressions'])==d['expected']['lineages'],'component table lineages')
    req(len(ct['optionalComponents'])==d['expected']['optionalSupportCandidates'],'optional candidates')
    req(ct['checkpoint']==113,'component table checkpoint')

    matrix=js(pt/'technology_numerical_matrix_v0_1.json')
    branch_ids={x['id'] for x in matrix.get('branches',[])}
    for x in arch['suspendedCp109PayloadCandidates']:
        req(x['id'] in branch_ids,f'suspended CP109 candidate missing {x["id"]}')

def validate_docs(repo):
    docs=repo/'docs'; pt=docs/'design/player_technology'; testing=docs/'design/testing'; validation=docs/'validation'
    concepts=sorted(x.name for x in docs.glob('Star_Cluster_Game_Concept_v*.docx'))
    req(concepts==['Star_Cluster_Game_Concept_v0.7k.docx'],f'active Concept set {concepts}')
    ctext=docx_text(docs/'Star_Cluster_Game_Concept_v0.7k.docx')
    for needle in ['Version 0.7k','10.4.1 Kinetic ammunition and Missile warhead expression','Normal compatible projectile/warhead modes','A Firm track may also support qualitative combat assessment','C-081']:
        req(needle in ctext,f'Concept missing {needle}')
    req('Draft v0.7j' not in ctext,'stale Concept header v0.7j')
    valfiles=sorted(x.name for x in validation.iterdir() if x.is_file())
    req(valfiles==['Checkpoint_113_Weapon_Ammunition_Warhead_Architecture_And_Docs_Hygiene.md','README.md'],f'validation active files {valfiles}')
    old_active=[
      'Technology_Component_Table_v0_2.md','Technology_Family_Storyboard_v1_2.md','Technology_Idea_Register_v1_3.md',
      'Technology_Foundation_Completeness_Audit_v1_2.md','StarCluster_Provisional_TL1_TL9_Technology_Component_Table_v0_2.xlsx'
    ]
    req(not any((pt/x).exists() for x in old_active),'superseded player-tech human docs still active')
    for x in ['Build_Neighbor_Ablation_Report_v1.md','StarCluster_CP112_Build_Neighbor_Ablation_v0_1.xlsx','Same_TL_Build_Ecology_Instrumentation_Report_v1.md','StarCluster_CP111_Same_TL_Build_Ecology_v0_1.xlsx','Checkpoint_107_Validation_Tiers.md']:
        req(not (testing/x).exists(),f'superseded testing result/policy still active {x}')
    cleanup=js(docs/'archive/docs_cleanup_checkpoint_113.json')
    for rel in cleanup['selectedArchiveChecks']: req((repo/rel).exists(),f'archive continuity missing {rel}')
    for rel in cleanup['compatibilitySnapshotsRetainedActive']: req((repo/rel).exists(),f'compat snapshot missing {rel}')
    req('Star_Cluster_Game_Concept_v0.7k.docx' in text(docs/'README.md'),'docs README authority')
    req('Weapon_Ammunition_And_Warhead_Architecture_v0_1.md' in text(pt/'README.md'),'player-tech README authority')

def validate_json(repo):
    count=0
    for p in repo.rglob('*.json'):
        rel=p.relative_to(repo).as_posix()
        if not owned(rel): continue
        try: json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as e: raise AssertionError(f'JSON parse {rel}: {e}')
        count+=1
    req(count>600,f'unexpected JSON coverage {count}')
    return count

def validate_manifest(repo,expected_count):
    mf=repo/'CHECKPOINT_113_SHA256SUMS.txt'; req(mf.is_file(),'missing CP113 manifest')
    exp={}
    for line in text(mf).splitlines():
        if not line.strip():continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad manifest row {line}')
        h,r=m.groups(); exp[r]=h
    req(len(exp)==expected_count,f'manifest count {len(exp)} != {expected_count}')
    actual=[]
    for p in repo.rglob('*'):
        if p.is_file():
            r=p.relative_to(repo).as_posix()
            if r!='CHECKPOINT_113_SHA256SUMS.txt' and owned(r): actual.append(r)
    actual=sorted(actual); req(actual==sorted(exp),f'manifest path-set mismatch missing={sorted(set(exp)-set(actual))[:10]} extra={sorted(set(actual)-set(exp))[:10]}')
    for r in actual:req(sha(repo/r)==exp[r],f'manifest hash mismatch {r}')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        print('       Validating accepted CP112 native provenance and frozen executable surfaces...')
        req(sha(repo/'CHECKPOINT_112_SHA256SUMS.txt')==EXPECTED_CP112_MANIFEST_SHA,'CP112 manifest hash drift')
        validate_cp112_native(repo)
        d=js(repo/'tools/checkpoints/checkpoint-113/checkpoint_113_architecture_definition.json')
        req(d['acceptedBaseline']=='112' and d['checkpointType']=='weapon_ammunition_warhead_architecture_and_docs_hygiene','CP113 definition identity')
        req(d['productionSourceChanged'] is False and d['simulationSourceChanged'] is False and d['numericalMatrixChanged'] is False and d['reactorCandidateChanged'] is False,'CP113 frozen flags')
        req(d['calibrationRun'] is False and d['monteCarloTrials']==0,'CP113 no-calibration boundary')
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-113/CP112_FROZEN_CSHARP_PRODUCTION_TEST_SHA256SUMS.txt',d['expected']['frozenCSharpAndTests'])
        validate_hash_list(repo,'docs/validation/evidence/checkpoint-113/CP112_FROZEN_SIMULATION_SHA256SUMS.txt',d['expected']['frozenSimulationFiles'])
        req(sha(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json')==EXPECTED_MATRIX_SHA,'CP109 numerical matrix drift')
        req(sha(repo/'docs/archive/player_technology/pre-cp165-active/power_reactor_calibration_profile_v0_1.json')==EXPECTED_REACTOR_SHA,'CP110 Reactor profile drift')

        print('       Validating ammunition/warhead architecture and technology reconciliation...')
        validate_architecture(repo,d)

        print('       Validating Concept, documentation hygiene, and runtime/testing boundary...')
        validate_docs(repo)
        for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
            py=list((repo/rel).rglob('*.py')); req(not py,f'Python leaked into production {py[:1]}')
        jcount=validate_json(repo)

        print('       Validating full repository manifest...')
        validate_manifest(repo,int(d['repositoryOwnedFiles']))
        print(f"       CP113 contract verified: {d['repositoryOwnedFiles']} repository-owned files; {jcount} JSON files parsed; {d['expected']['disciplines']} disciplines / {d['expected']['lineages']} lineages / {d['expected']['storyboardBeats']} beats / {d['expected']['ideas']} ideas / {d['expected']['foundationDomains']} foundation domains; 3 sparse hard gates; zero trials; zero numerical promotion.")
        return 0
    except Exception as e:
        print(f'CP113 contract failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
