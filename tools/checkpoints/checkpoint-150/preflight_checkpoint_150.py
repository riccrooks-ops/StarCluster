#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys,unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
CP149_NATIVE_SHA='18b60851e5138b8cb44f76b5f0e2bad533dbf8935d88c70a64565bcd1c46f565'
CP149_MANIFEST='docs/validation/evidence/checkpoint-149/CP149_REPOSITORY_SHA256SUMS.txt'
CP149_MANIFEST_SHA='2f18d551d8d947d4dc1b89efca01576557b602ff98ab79c67811630cf9e41d51'
CP150_MANIFEST='docs/validation/evidence/checkpoint-150/CP150_REPOSITORY_SHA256SUMS.txt'
ALLOWED={
'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
'tools/simulation/starcluster_research/cli.py',
}
ADDITIONS={
'docs/archive/testing/pre-cp165-active/cp150_kinetic_viable_region_refinement_v0_1.json',
'docs/validation/Checkpoint_150_Kinetic_Viable_Region_High_Resolution_Refinement.md',
'tools/simulation/starcluster_research/kinetic_viable_region_refinement.py',
'tools/simulation/tests/test_cp150_kinetic_viable_region_refinement.py',
'tools/checkpoints/checkpoint-150/apply_checkpoint_150.ps1',
'tools/checkpoints/checkpoint-150/checkpoint_150_definition.json',
'tools/checkpoints/checkpoint-150/preflight_checkpoint_150.py',
'tools/checkpoints/checkpoint-150/test_checkpoint_150_contract.py',
'docs/validation/evidence/checkpoint-150/CP149_NATIVE_ACCEPTANCE_SUMMARY.json',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_AXIAL_EFFECTS.csv',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_PAIRWISE_INTERACTIONS.csv',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_TL_RESPONSE.csv',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_OPPONENT_RESPONSE.csv',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_ARMOR_ROLE_RESPONSE.csv',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_COMBAT_PARETO_CANDIDATES.csv',
'docs/validation/evidence/checkpoint-150/CP149_KINETIC_CANDIDATE_LEDGER.csv',
}

def req(x,m):
    if not x: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip():h,rel=line.split('  ',1);out[rel]=h
    return out
def owned(repo):
    out=set()
    for p in repo.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(repo).as_posix();w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
        if rel==CP150_MANIFEST:continue
        out.add(rel)
    return out
def count_suite(s):return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-150/checkpoint_150_definition.json')
        req(d['checkpoint']==150 and d['baseCheckpoint']==149,'checkpoint identity')
        req(d['expectedPythonTests']==390 and d['expectedPythonTestModules']==41,'Python test contract')
        req(d['expectedXunitTests']==934 and d['expectedFocusedCp150Tests']==16,'native/focused contract')
        req(d['kineticContexts']==2600 and d['tlCandidateCount']==349,'refinement design contract')
        req(d['candidateContextCells']==102900 and d['smokeCombatTrials']==10290 and d['substantiveCombatTrials']==20580000,'study scale')
        req(d['combatDoctrine']=='cp147_tactical_utility' and d['kineticSpenPolicy']=='fixed-zero-family-identity','doctrine/identity contract')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['stageBAutomatic'],'promotion boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        p=repo/CP149_MANIFEST;req(p.is_file() and sha(p)==CP149_MANIFEST_SHA,'CP149 manifest drift');base=manifest(p)
        for rel,h in base.items():
            req((repo/rel).is_file(),f'missing CP149 file {rel}')
            if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP149 baseline drift: {rel}')
        base_cs={r for r in base if r.endswith('.cs')}
        current_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
        req(current_cs==base_cs,'CP150 must add/change no C# path')
        for rel in base_cs:req(sha(repo/rel)==base[rel],f'CP149 C# drift: {rel}')
        expected=set(base)|{CP149_MANIFEST}|ADDITIONS;cur=owned(repo)
        req(cur==expected,f'CP150 path drift added={sorted(cur-expected)[:8]} missing={sorted(expected-cur)[:8]}')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp150_kinetic_viable_region_refinement_v0_1.json')
        req(study['acceptedCp149NativeResultsArchiveSha256']==CP149_NATIVE_SHA,'CP149 native provenance')
        sim=repo/'tools/simulation';sys.path.insert(0,str(sim))
        from starcluster_research.kinetic_viable_region_refinement import validate_study,validate_population,candidate_ledger,refinement_design_summary,EXPECTED_SUBSTANTIVE_COMBATS
        req(validate_study(study)==[],'CP150 study validation');req(validate_population(repo,study)==[],'CP150 population validation')
        ledger=candidate_ledger(repo,study);req(len(ledger)==349 and len({r['candidate_id'] for r in ledger})==349,'candidate ledger')
        req(all(int(r['candidate_spen'])==0 and int(r['firing_tp_delta'])==0 and int(r['ammo_level'])==100 for r in ledger),'frozen-factor boundary')
        req(all(int(r['identity_preserved'])==1 and int(r['promotion_allowed'])==0 for r in ledger),'identity/promotion boundary')
        req(sum(int(r['candidates']) for r in refinement_design_summary(repo,study))==349,'design summary')
        req(EXPECTED_SUBSTANTIVE_COMBATS==20580000,'substantive constant')
        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==41,'Python module count')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==390,'Python test count')
        print('CP150 preflight PASS: CP149 frozen and native evidence hash-locked; 390/41 Python tests discovered; 349 TL-specific identity-preserving K candidates x accepted K contexts = 102,900 cells x 200 matched trials = 20,580,000 substantive combats; TP/ammo/Space/SPEN frozen; no promotion.')
        return 0
    except Exception as e:
        print(f'CP150 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
