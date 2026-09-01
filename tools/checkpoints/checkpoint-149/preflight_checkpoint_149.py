#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys,unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
CP148_NATIVE_SHA='b00c97b620cc7824760a8af5b41e0e888bb1d7ace16e3d51d426473c6a86788e'
CP148_MANIFEST='docs/validation/evidence/checkpoint-148/CP148_REPOSITORY_SHA256SUMS.txt'
CP148_MANIFEST_SHA='1356bfb7ce786090883df8e3872706fc4b853231e5e09e65eae7baf9828a10d6'
CP149_MANIFEST='docs/validation/evidence/checkpoint-149/CP149_REPOSITORY_SHA256SUMS.txt'
EVIDENCE={
'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_NATIVE_ACCEPTANCE_SUMMARY.json':'b6b71c35c608ff3d48bea3b8a67aaa3582b428f2f2a52ad24fcb42fd468a6bb0',
'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_STAGE_A_SUBSTANTIVE_SUMMARY.json':'e2a9c05f9779608d23eed421b94ddf40f3fdd8ab6319ecfdae372dab7e4d84da',
'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_WEAPON_OVERALL_RESPONSE.csv':'218bbb2ab69bd874cd6bc6e6ca8a29a3c406ab99d2552561a7e0e6ca21dc88f0',
'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_COMBAT_GATED_STRATEGIC_VIABILITY.csv':'635f2d755fe7dd9ecb4c466429df266d8989f53fe123db0b4256f14c8e9ca33d',
'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_ROLE_RESPONSE_SUMMARY.csv':'f0c0702bbf1d128c8102b500090316575086cd9719f7015e70341d70a9ae2b11',
'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_TP_LOAD_WEAPON_TL_SUMMARY.csv':'47807b411e154a0500c482c3917dbd5c041838bc399928edbbc1ed39cd3e0ccd',
}
ALLOWED={
'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md','docs/design/testing/README.md',
'tools/simulation/starcluster_research/cli.py',
}
ADDITIONS=set(EVIDENCE)|{
'docs/archive/testing/pre-cp165-active/cp149_kinetic_full_characteristic_multivariate_sweep_v0_1.json',
'docs/validation/Checkpoint_149_Kinetic_Full_Characteristic_Multivariate_Response_Surface_Sweep.md',
'tools/simulation/starcluster_research/kinetic_full_characteristic_sweep.py',
'tools/simulation/tests/test_cp149_kinetic_full_characteristic_sweep.py',
'tools/checkpoints/checkpoint-149/apply_checkpoint_149.ps1',
'tools/checkpoints/checkpoint-149/checkpoint_149_definition.json',
'tools/checkpoints/checkpoint-149/preflight_checkpoint_149.py',
'tools/checkpoints/checkpoint-149/test_checkpoint_149_contract.py',
}

def req(x,m):
    if not x: raise AssertionError(m)
def sha(p):
    h=hashlib.sha256();h.update(p.read_bytes());return h.hexdigest()
def js(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def manifest(p):
    out={}
    for line in p.read_text(encoding='utf-8-sig').splitlines():
        if line.strip(): h,rel=line.split('  ',1);out[rel]=h
    return out
def owned(repo):
    out=set()
    for p in repo.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(repo).as_posix();w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w: continue
        if rel==CP149_MANIFEST: continue
        out.add(rel)
    return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-149/checkpoint_149_definition.json')
        req(d['checkpoint']==149 and d['baseCheckpoint']==148,'checkpoint identity')
        req(d['expectedPythonTests']==374 and d['expectedPythonTestModules']==40,'Python test contract')
        req(d['expectedXunitTests']==934 and d['expectedFocusedCp149Tests']==16,'native/focused contract')
        req(d['kineticContexts']==2600 and d['factors']==7 and d['candidatesPerTl']==163 and d['tlCandidateCount']==1467,'sweep design contract')
        req(d['candidateContextCells']==423800 and d['smokeCombatTrials']==42380 and d['substantiveCombatTrials']==42380000,'study scale')
        req(d['combatDoctrine']=='cp147_tactical_utility' and d['kineticSpenPolicy']=='fixed-zero-family-identity','doctrine/identity contract')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['stageBAutomatic'],'promotion boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        p=repo/CP148_MANIFEST;req(p.is_file() and sha(p)==CP148_MANIFEST_SHA,'CP148 manifest drift');base=manifest(p)
        for rel,h in base.items():
            req((repo/rel).is_file(),f'missing CP148 file {rel}')
            if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP148 baseline drift: {rel}')
        cp148_cs={r for r in base if r.endswith('.cs')}
        current_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
        req(current_cs==cp148_cs,'CP149 must add/change no C# path')
        for rel in cp148_cs:req(sha(repo/rel)==base[rel],f'CP148 C# drift: {rel}')
        expected=set(base)|{CP148_MANIFEST}|ADDITIONS;cur=owned(repo)
        req(cur==expected,f'CP149 path drift added={sorted(cur-expected)[:8]} missing={sorted(expected-cur)[:8]}')
        for rel,h in EVIDENCE.items(): req((repo/rel).is_file() and sha(repo/rel)==h,f'accepted CP148 evidence drift: {rel}')
        summary=js(repo/'docs/validation/evidence/checkpoint-149/accepted-cp148/CP148_NATIVE_ACCEPTANCE_SUMMARY.json')
        req(summary['checkpoint']==148 and summary['repositoryOnlyAccepted'] is True and summary['substantiveStageACompleted'] is True,'accepted CP148 identity')
        req(summary['pythonTestsPassed']==358 and summary['xunitPassed']==934 and summary['substantiveCombatTrials']==3425000,'accepted CP148 coverage')
        req(summary['substantiveTurnCapSentinels']==0 and summary['sourceMatrixUnmodified'] is True,'accepted CP148 behavior/boundary')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp149_kinetic_full_characteristic_multivariate_sweep_v0_1.json')
        req(study['acceptedCp148NativeResultsArchiveSha256']==CP148_NATIVE_SHA,'CP148 native provenance')
        sim=repo/'tools/simulation';sys.path.insert(0,str(sim))
        from starcluster_research.kinetic_full_characteristic_sweep import validate_study,validate_population,candidate_ledger,kinetic_contexts,smoke_contexts,_space_envelope
        req(validate_study(study)==[],'CP149 study validation');req(validate_population(repo,study)==[],'CP149 population validation')
        ledger=candidate_ledger(repo,study);req(len(ledger)==1467 and len({r['candidate_id'] for r in ledger})==1467,'candidate ledger')
        req(all(int(r['candidate_spen'])==0 and int(r['promotion_allowed'])==0 for r in ledger),'SPEN/promotion boundary')
        req(len(kinetic_contexts(repo,study))==2600,'Kinetic context count')
        req(sum(len(smoke_contexts(repo,study,tl)) for tl in range(1,10))==260,'smoke panel count')
        req(len(_space_envelope(repo,study))==2250,'Space envelope count')
        kernel=(repo/'tools/simulation/starcluster_research/kinetic_full_characteristic_sweep.py').read_text()
        for marker in ('EXPECTED_CANDIDATES_PER_TL = 163','resolution-VII','fixed at 0','kinetic_combat_pareto_candidates.csv'):
            req(marker in kernel,f'missing CP149 marker {marker}')
        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==40,'Python module count')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==374,'Python test count')
        print('CP149 preflight PASS: CP148 frozen, 374/40 Python tests discovered, 934 xUnit expected, 1,467 TL-candidates x 2,600 K contexts x 100 trials = 42,380,000 substantive combats; SPEN fixed zero; no promotion.')
        return 0
    except Exception as e:
        print(f'CP149 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
