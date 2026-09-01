#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys,unittest
from pathlib import Path

MATRIX_SHA='3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194'
CONCEPT_SHA='f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f'
CP147_NATIVE_SHA='a33b7fa137b2b17d8c4f5d45900cdc5073e0a4116147f521b40948a172730bd6'
CP147_MANIFEST='docs/validation/evidence/checkpoint-147/CP147_REPOSITORY_SHA256SUMS.txt'
CP147_MANIFEST_SHA='06a692ac3f9e2509569d29e37a9591474c4927ca73ce8fb960ff6dae8f7c981d'
CP148_MANIFEST='docs/validation/evidence/checkpoint-148/CP148_REPOSITORY_SHA256SUMS.txt'
ALLOWED={
'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/validation/README.md',
' tools/simulation/starcluster_research/whole_combat_stage_a_response_surface.py'.strip(),
}
ADDITIONS={
'docs/archive/testing/pre-cp165-active/cp148_whole_combat_stage_a_tactical_utility_response_surface_study_v0_1.json',
'docs/validation/Checkpoint_148_Whole_Combat_Stage_A_Response_Surface_Under_Tactical_Utility.md',
'docs/validation/evidence/checkpoint-148/accepted-cp147/CP147_NATIVE_ACCEPTANCE_SUMMARY.json',
'docs/validation/evidence/checkpoint-148/accepted-cp147/CP147_ACCEPTED_UTILITY_REPLAY_RESULTS.csv',
'docs/validation/evidence/checkpoint-148/accepted-cp147/CP147_ACCEPTED_UTILITY_ACTION_SUMMARY.csv',
'tools/simulation/tests/test_cp148_whole_combat_stage_a_tactical_utility.py',
'tools/checkpoints/checkpoint-148/apply_checkpoint_148.ps1',
'tools/checkpoints/checkpoint-148/checkpoint_148_definition.json',
'tools/checkpoints/checkpoint-148/preflight_checkpoint_148.py',
'tools/checkpoints/checkpoint-148/test_checkpoint_148_contract.py',
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
        if not p.is_file():continue
        rel=p.relative_to(repo).as_posix(); w='/'+rel
        if rel.startswith(('out/','.git/')) or '/__pycache__/' in w or rel.endswith('.pyc') or '/bin/' in w or '/obj/' in w or '/TestResults/' in w:continue
        if rel==CP148_MANIFEST:continue
        out.add(rel)
    return out
def count_suite(s): return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in s)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-148/checkpoint_148_definition.json')
        req(d['checkpoint']==148 and d['baseCheckpoint']==147,'checkpoint identity')
        req(d['expectedPythonTests']==358 and d['expectedPythonTestModules']==39,'Python test contract')
        req(d['expectedXunitTests']==934 and d['expectedFocusedCp148Tests']==12,'native/focused contract')
        req(d['stageAScenarios']==6850 and d['substantiveCombatTrials']==3425000 and d['combatDoctrine']=='cp147_tactical_utility','study scale/doctrine')
        req(d['baseMaxTpDemandPolicy']=='all-installed-normal-combat-demand-no-overload' and d['strategicParetoPolicy']=='combat-gated-before-resource-robustness','analysis policy')
        req(not d['tuningAllowed'] and not d['automaticPromotion'] and not d['stageBAutomatic'],'promotion boundary')
        req(sha(repo/'docs/design/player_technology/technology_numerical_matrix_v0_9.json')==MATRIX_SHA,'matrix drift')
        req(sha(repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx')==CONCEPT_SHA,'Concept drift')
        p=repo/CP147_MANIFEST;req(p.is_file() and sha(p)==CP147_MANIFEST_SHA,'CP147 manifest drift');base=manifest(p)
        for rel,h in base.items():
            req((repo/rel).is_file(),f'missing CP147 file {rel}')
            if rel not in ALLOWED:req(sha(repo/rel)==h,f'unexpected CP147 baseline drift: {rel}')
        cp147_cs={r for r in base if r.endswith('.cs')}; current_cs={p.relative_to(repo).as_posix() for p in repo.rglob('*.cs') if '/bin/' not in '/'+p.relative_to(repo).as_posix() and '/obj/' not in '/'+p.relative_to(repo).as_posix()}
        req(current_cs==cp147_cs,'CP148 must add/change no C# path')
        for rel in cp147_cs:req(sha(repo/rel)==base[rel],f'CP147 C# drift: {rel}')
        expected=set(base)|{CP147_MANIFEST}|ADDITIONS;cur=owned(repo);req(cur==expected,f'CP148 path drift added={sorted(cur-expected)[:8]} missing={sorted(expected-cur)[:8]}')
        study=js(repo/'docs/archive/testing/pre-cp165-active/cp148_whole_combat_stage_a_tactical_utility_response_surface_study_v0_1.json')
        req(study['submittedCp147NativeResultsArchiveSha256']==CP147_NATIVE_SHA,'CP147 native provenance')
        summary=js(repo/study.get('acceptedCp147NativeSummary','docs/validation/evidence/checkpoint-148/accepted-cp147/CP147_NATIVE_ACCEPTANCE_SUMMARY.json'))
        req(summary['checkpoint']==147 and summary['repositoryOnlyAccepted'] is True and summary['pythonTestsPassed']==346 and summary['xunitPassed']==934,'accepted CP147 identity')
        req(summary['acceptedCp146FieldMismatches']==0 and summary['cp147TurnCapSentinels']==0 and summary['cp147HeldMainAttempts']>0,'accepted CP147 behavior')
        sim=repo/'tools/simulation';sys.path.insert(0,str(sim))
        from starcluster_research.whole_combat_stage_a_response_surface import validate_study,validate_population,_base_max_installed_tp_demand
        from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
        req(validate_study(study)==[],'CP148 study validation');req(validate_population(repo,study)==[],'CP148 population validation');req(CANONICAL_COMBAT_KERNEL_VERSION=='0.7','kernel version')
        kernel=(repo/'tools/simulation/starcluster_research/whole_combat_stage_a_response_surface.py').read_text()
        for marker in ('_base_max_installed_tp_demand','_combat_gated_strategic_viability','tp_load_response_surface.csv','UTILITY_COMBAT_DOCTRINE'):
            req(marker in kernel,f'missing CP148 marker {marker}')
        tests=sorted((repo/'tools/simulation/tests').glob('test_*.py'));req(len(tests)==39,'Python module count')
        suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py');req(count_suite(suite)==358,'Python test count')
        print('CP148 preflight PASS: CP147 frozen, 358/39 Python tests discovered, 934 xUnit expected, 6,850x500 utility study bound, max-TP no-overload telemetry and combat-gated Pareto enabled.')
        return 0
    except Exception as e:
        print(f'CP148 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
