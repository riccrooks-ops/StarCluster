#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
CP150_NATIVE_SHA='79dd7051103ad4796c1664d21fe03c740a4c3369404a57fe0dc7754bf3ca5c07'
CP150_MANIFEST='docs/validation/evidence/checkpoint-150/CP150_REPOSITORY_SHA256SUMS.txt'
CP150_MANIFEST_SHA='936576d216871302007f771261cef1a10023abd02fd6c70dc49e65cdc02a87f0'
CP151_MANIFEST='docs/validation/evidence/checkpoint-151/CP151_REPOSITORY_SHA256SUMS.txt'
ALLOWED={
    'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
    'tools/simulation/starcluster_research/cli.py',
}
ADDITIONS={
    'docs/archive/testing/pre-cp165-active/cp151_point_scale_multivariate_response_v0_1.json',
    'docs/validation/Checkpoint_151_Point_Scale_Multivariate_Response.md',
    'tools/simulation/starcluster_research/point_scale_multivariate_response.py',
    'tools/simulation/tests/test_cp151_point_scale_multivariate_response.py',
    'tools/checkpoints/checkpoint-151/apply_checkpoint_151.ps1',
    'tools/checkpoints/checkpoint-151/checkpoint_151_definition.json',
    'tools/checkpoints/checkpoint-151/preflight_checkpoint_151.py',
    'tools/checkpoints/checkpoint-151/test_checkpoint_151_contract.py',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_NATIVE_ACCEPTANCE_SUMMARY.json',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_TL_RESPONSE.CSV',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_OPPONENT_RESPONSE.CSV',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_ARMOR_ROLE_RESPONSE.CSV',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_PARAMETER_MARGINALS.CSV',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_PAIRWISE_RESPONSE.CSV',
    'docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_LEDGER.CSV',
}

def req(x,m):
    if not x: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip(): h,rel=line.split('  ',1); out[rel]=h
    return out
def owned(repo):
    out=set()
    for p in repo.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(repo).as_posix(); w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
        if rel==CP151_MANIFEST: continue
        out.add(rel)
    return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-151/checkpoint_151_definition.json')
        req(d['checkpoint']==151 and d['baseCheckpoint']==150,'checkpoint identity')
        req(d['expectedPythonTests']==408 and d['expectedPythonTestModules']==42,'Python test contract')
        req(d['expectedXunitTests']==934 and d['expectedFocusedCp151Tests']==18,'native/focused contract')
        req(d['pointScale']==2 and d['stageAContexts']==6850 and d['tlCandidateCount']==2373,'point-scale design')
        req(d['candidateContextCells']==1807050 and d['smokeCombatTrials']==118650 and d['substantiveCombatTrials']==45176250,'study scale')
        req(d['combatDoctrine']=='cp147_tactical_utility','doctrine contract')
        req(d['unchangedFields']==['ACC','DEF','RES','TP','range','Space'],'unchanged-domain contract')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['stageBAutomatic'],'promotion boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        p=repo/CP150_MANIFEST; req(p.is_file() and sha(p)==CP150_MANIFEST_SHA,'CP150 manifest drift'); base=manifest(p)
        for rel,h in base.items():
            req((repo/rel).is_file(),f'missing CP150 file {rel}')
            if rel not in ALLOWED: req(sha(repo/rel)==h,f'unexpected CP150 baseline drift: {rel}')
        base_cs={r for r in base if r.endswith('.cs')}
        current_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
        req(current_cs==base_cs,'CP151 must add/change no C# path')
        for rel in base_cs: req(sha(repo/rel)==base[rel],f'CP150 C# drift: {rel}')
        expected=set(base)|{CP150_MANIFEST}|ADDITIONS; cur=owned(repo)
        req(cur==expected,f'CP151 path drift added={sorted(cur-expected)[:8]} missing={sorted(expected-cur)[:8]}')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp151_point_scale_multivariate_response_v0_1.json')
        req(study['acceptedCp150NativeResultsArchiveSha256']==CP150_NATIVE_SHA,'CP150 native provenance')
        sim=repo/'tools/simulation'; sys.path.insert(0,str(sim))
        from starcluster_research.point_scale_multivariate_response import validate_study,validate_population,candidate_ledger,design_summary,EXPECTED_SUBSTANTIVE_COMBATS,EXPECTED_SMOKE_COMBATS
        req(validate_study(study)==[],'CP151 study validation'); req(validate_population(repo,study)==[],'CP151 population validation')
        ledger=candidate_ledger(repo,study); req(len(ledger)==2373 and len({(r['tl'],r['candidate_id']) for r in ledger})==2373,'candidate ledger')
        req(all(int(r['promotion_allowed'])==0 for r in ledger),'promotion boundary')
        req(sum(int(r['candidates']) for r in design_summary(repo,study))==2373,'design summary')
        req(EXPECTED_SUBSTANTIVE_COMBATS==45176250 and EXPECTED_SMOKE_COMBATS==118650,'study constants')
        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py')); req(len(tests)==42,f'Python module count {len(tests)}')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py'); req(count_suite(suite)==408,f'Python test count {count_suite(suite)}')
        print('CP151 preflight PASS: CP150 frozen/native evidence hash-locked; 408/42 Python tests discovered; x2 equivalence + 2,373 TL-candidates / 1,807,050 cells / 45,176,250 substantive combats; ACC/DEF/RES/TP/range/Space unchanged; no promotion.')
        return 0
    except Exception as e:
        print(f'CP151 preflight failure: {e}',file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
