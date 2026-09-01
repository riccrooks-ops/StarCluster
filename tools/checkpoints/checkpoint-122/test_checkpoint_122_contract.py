#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

EXCLUDED_PARTS={'.git','.vs','.vscode','.idea','out','bin','obj','TestResults','__pycache__'}
EXCLUDED_FILES={'.DS_Store','Thumbs.db'}
EXCLUDED_SUFFIXES={'.pyc','.user','.userosscache','.sln.docstates','.uid','.suo'}
ROOT_STALE=(re.compile(r'^CHECKPOINT_\d+[A-Za-z]*_SHA256SUMS\.txt$',re.I),re.compile(r'^SHA256SUMS(?:[-_].*)?\.txt$',re.I))
CP121_NATIVE_SHA='7292b23b559c1ebb0c551c0cd09c3588cc3127e72a131b6eabebbd50ed9aff1e'


def req(value,msg):
    if not value: raise AssertionError(msg)

def text(path:Path):
    req(path.is_file(),f'Missing {path}')
    return path.read_text(encoding='utf-8-sig')

def js(path:Path): return json.loads(text(path))

def sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def owned(rel:str):
    p=Path(rel)
    return not any(part in EXCLUDED_PARTS for part in p.parts) and p.name not in EXCLUDED_FILES and p.suffix.lower() not in EXCLUDED_SUFFIXES

def csv_rows(path:Path):
    with path.open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))


def validate_definition(repo:Path,d:dict,e:dict):
    req(d['checkpoint']==122 and d['acceptedBaseline']==121 and d['revision']=='corrected_replacement_1','definition identity/revision')
    req(d['status']=='candidate_pending_native_acceptance' and d['automaticPromotion'] is False,'candidate status/promotion')
    req(d['productionSourceChanged'] is True and d['simulationResearchChanged'] is True and d['numericalMatrixChanged'] is True and d['conceptChanged'] is True and d['playerAuthorityChanged'] is True,'scope flags')
    req(d['damagePointScale']==2 and d['balanceChangeIntended'] is False and d['oddHalfStepValuesPromoted'] is False,'scale/balance boundary')
    req(d['productionRepairHullPerKit']==1 and d['parityOnlyRepairHullPerKit']==2,'DamCon production/parity boundary')
    req(d['criticalCadenceMigrated'] is False and d['substantiveMonteCarloTrials']==0 and d['deepCalibrationRequired'] is False,'critical/Monte Carlo boundary')
    req(e['pythonTests']==124 and e['parityCases']==25 and e['xunitTests']==905 and e['scenarioRunnerSelfTests']==70,'deterministic suite counts')
    req(e['canonicalLayeredParityCases']==234000 and e['canonicalTemporaryEffectCases']==117 and e['canonicalEnergyDegradedCases']==21 and e['canonicalParityMismatches']==0,'canonical parity counts')


def validate_cp121(repo:Path):
    z=repo/'docs/validation/evidence/checkpoint-122/CP121_NATIVE_RESULTS_ACCEPTED.zip'
    req(sha(z)==CP121_NATIVE_SHA,'accepted CP121 native archive hash drift')
    s=js(repo/'docs/validation/evidence/checkpoint-122/CP122_ACCEPTED_CP121_NATIVE_SUMMARY.json')
    req(s['acceptedCheckpoint']==121 and s['status']=='accepted_native_baseline_for_cp122','CP121 accepted summary identity')
    req(s['archiveSha256']==CP121_NATIVE_SHA,'CP121 accepted summary hash')
    req(s['equivalencePairedTrials']==85680 and s['equivalenceMismatchedTrials']==0 and s['equivalenceExact'] is True,'CP121 equivalence evidence')
    req(s['halfStepTrials']==4848000 and s['trialErrors']==0 and s['failedGates']==[],'CP121 half-step evidence')
    with zipfile.ZipFile(z) as zz:
        names=set(zz.namelist())
        req(any(n.endswith('/analysis.json') for n in names),'CP121 native archive lacks analysis')


def validate_preflight(repo:Path):
    result=subprocess.run([sys.executable,'-B',str(repo/'tools/checkpoints/checkpoint-122/preflight_checkpoint_122.py'),'--repo',str(repo)],capture_output=True,text=True)
    req(result.returncode==0,f'CP122 preflight failed inside contract:\n{result.stdout}\n{result.stderr}')


def validate_authorities(repo:Path,d:dict):
    for rel in d['canonicalAuthorities']: req((repo/rel).is_file(),f'canonical authority missing: {rel}')
    a=js(repo/'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_1.json')
    req(a['damagePointScale']==2 and a['legacyPointEqualsCanonicalPoints']==2,'canonical authority scale')
    req(a['productionDamageControlHullPerRepairKit']==1 and a['parityOnlyHullPerRepairKit']==2,'canonical authority repair semantics')
    req(a['criticalCadenceMigrationDeferred'] is True and a['oddHalfStepValuesPromoted'] is False and a['balanceChangeIntended'] is False,'canonical authority scope')
    audit=js(repo/'docs/archive/testing/pre-cp165-active/canonical_damage_domain_implementation_audit_v0_1.json')
    req(audit['canonicalScale']==2 and audit['productionRepairHullPerKit']==1 and audit['parityOnlyRepairHullPerKit']==2,'implementation audit repair/scale')
    req(audit['criticalCadenceMigrated'] is False and audit['oddHalfStepValuesPromoted'] is False,'implementation audit deferred boundaries')
    classes={x['classification'] for x in audit['activePointConsumers']}
    req({'unit_agnostic','scale_sensitive_rounding','intentional_production_exception','ratio_invariant','data_point_domain','deferred','historical_test_fixture'}<=classes,'implementation audit consumer coverage')

    rows={r['parameter_id']:r for r in csv_rows(repo/'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_4.csv')}
    for pid,val in {'hull_points':'24','armor_integrity':'8','shield_capacity':'4','shield_base_recharge':'2','kinetic_damage':'8','kinetic_spen':'2','energy_low_damage':'4','energy_standard_damage':'6','energy_overload_damage':'8','missile_warhead_damage':'10','missile_warhead_spen':'2','missile_warhead_apen':'4'}.items():
        req(rows[pid]['value']==val,f'canonical TL1 value mismatch {pid}')
    req(rows['repair_hull_chance']['display_name']=='Repair 1 Hull','TL1 Repair Kit semantics')


def validate_code(repo:Path):
    dps=text(repo/'src/StarCluster.Core/Combat/Damage/DamagePointScale.cs')
    req('public const int Current = 2;' in dps and 'Math.Min(damage, scaled)' in dps,'scale helper / odd clamp')
    cp=text(repo/'src/StarCluster.Core/Combat/InternalDamage/ComponentPerformance.cs')
    req('DamagePointScale.HalfDamageRoundedUp(normalDamage, damagePointScale)' in cp,'Energy scale-aware damage rounding missing')
    ship=text(repo/'src/StarCluster.Core/Combat/InternalDamage/ShipDamageState.cs')
    req('Defense.RestoreHull(1);' in ship,'production Damage Control must restore 1 Hull')
    core='\n'.join(p.read_text() for p in (repo/'src/StarCluster.Core').rglob('*.cs'))
    req('RestoreHull(2)' not in core,'parity-only 2-Hull repair leaked into production Core')
    test=text(repo/'tests/StarCluster.Tests/Combat/InternalDamage/CanonicalDamageScaleMigrationTests.cs')
    req('Production_damage_control_still_restores_exactly_one_canonical_hull' in test and 'Parity_fixture_may_artificially_restore_two_canonical_hull' in test,'DamCon production/parity xUnit separation missing')
    test_import = 'using StarCluster.Core.Combat.Components;'
    req(test_import in test,'CP122 migration xUnit file missing ComponentCondition namespace import')
    runner=text(repo/'src/StarCluster.ScenarioRunner/DamageScaling/CanonicalDamageScaleParityRunner.cs')
    req(test_import in runner,'CP122 parity runner missing ComponentCondition namespace import')
    for token in ('layeredCases','temporaryEffectCases','energyDegradedCases','productionRepairHullPerKit = 1','parityOnlyRepairHullPerKit = 2','criticalCadenceMigrated = false'):
        req(token in runner,f'canonical parity runner missing {token}')
    for rel in ('src/StarCluster.Game','src/StarCluster.Core'):
        req(not list((repo/rel).rglob('*.py')),f'Python leaked into production runtime {rel}')


def validate_docs(repo:Path):
    required=(
      'README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md','docs/development/Simulation_Development_Guidelines.md',
      'docs/validation/Checkpoint_122_Canonical_Damage_Domain_Migration.md','docs/archive/testing/pre-cp165-active/Canonical_Damage_Domain_Migration_Architecture_v0_1.md','docs/archive/testing/pre-cp165-active/canonical_damage_domain_migration_v0_1.json','docs/archive/testing/pre-cp165-active/canonical_damage_domain_implementation_audit_v0_1.json','docs/Star_Cluster_Game_Concept_v0.7m.docx')
    for rel in required:req((repo/rel).is_file(),f'missing CP122 doc {rel}')
    for rel in ('README.md','CHAT_README.md','docs/README.md','docs/Prototype_TODO.md','docs/design/player_technology/README.md','docs/design/testing/README.md','docs/validation/README.md'):
        req('122' in text(repo/rel),f'{rel} missing CP122 pointer')
    rb=text(repo/'README.md').lower()
    for phrase in ('canonical x2','repair kit','1 hull','parity','2 hull','critical','defer','checkpoint-122'):
        req(phrase in rb,f'root README missing {phrase}')
    cp121=text(repo/'docs/validation/Checkpoint_121_Damage_Resolution_Scaling.md').lower()
    req('native accepted on 2026-08-16' in cp121 and 'accepted baseline for checkpoint 122' in cp121,'CP121 accepted/supersession status missing')
    req(not (repo/'docs/Star_Cluster_Game_Concept_v0.7l.docx').exists(),'old active Concept v0.7l must be archived')
    req((repo/'docs/archive/concepts/Star_Cluster_Game_Concept_v0.7l.docx').is_file(),'archived Concept v0.7l missing')


def validate_wrapper(repo:Path):
    t=text(repo/'tools/checkpoints/checkpoint-122/apply_checkpoint_122.ps1')
    for token in ('[switch]$RepositoryOnly','[switch]$NoClean','8.0.423','preflight_checkpoint_122.py','test_checkpoint_122_contract.py','124/124','905/905','70/70','damage-scale-parity','234000','117','21','productionRepairHullPerKit','parityOnlyRepairHullPerKit','substantiveMonteCarloTrials=0','prepackage_repository_hygiene.py'):
        req(token in t,f'CP122 wrapper missing {token}')
    req('checkpoint-121' not in re.sub(r'acceptedBaseline=121','',t),'CP122 wrapper unexpectedly invokes CP121 checkpoint workflow')


def validate_hygiene(repo:Path):
    stale=[]
    for p in repo.iterdir():
        if p.is_file() and (p.name.lower() in {'repository_manifest.txt','manifest.sha256','sha256sums.txt'} or any(rx.match(p.name) for rx in ROOT_STALE)): stale.append(p.name)
    req(not stale,f'stale root checksum/manifest artifacts: {stale}')
    req((repo/'tools/checkpoints/prepackage_repository_hygiene.py').is_file(),'prepackage hygiene tool missing')


def validate_json(repo:Path):
    count=0
    for p in repo.rglob('*.json'):
        rel=p.relative_to(repo).as_posix()
        if not owned(rel): continue
        try: json.loads(p.read_text(encoding='utf-8-sig'))
        except Exception as exc: raise AssertionError(f'JSON parse {rel}: {exc}')
        count+=1
    return count


def validate_native(path:Path,e:dict):
    s=js(path/'CP122_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==122 and s['acceptedBaseline']==121,'native summary identity')
    req(s['dotnetSdk']=='8.0.423' and s['buildPassed'] is True and s['buildWarningsAsErrors'] is True,'native build gate')
    req(s['xunitTotal']==e['xunitTests'] and s['xunitPassed']==e['xunitTests'],'native xUnit count')
    req(s['scenarioRunnerSelfTests']==e['scenarioRunnerSelfTests'] and s['scenarioRunnerSelfTestsPassed']==e['scenarioRunnerSelfTests'],'native ScenarioRunner self-test count')
    req(s['researchParityCases']==e['parityCases'] and s['researchParityPassed']==e['parityCases'],'native research parity count')
    req(s['damagePointScale']==2 and s['exactParity'] is True and s['parityMismatches']==0,'native damage-scale parity')
    req(s['layeredParityCases']==e['canonicalLayeredParityCases'] and s['temporaryEffectParityCases']==e['canonicalTemporaryEffectCases'] and s['degradedEnergyParityCases']==e['canonicalEnergyDegradedCases'],'native parity case shape')
    req(s['productionRepairHullPerKit']==1 and s['parityOnlyRepairHullPerKit']==2,'native DamCon boundary')
    req(s['criticalCadenceMigrated'] is False and s['oddHalfStepValuesPromoted'] is False and s['substantiveMonteCarloTrials']==0 and s['failedGates']==[],'native scope/gates')
    d=js(path/'canonical-damage-scale-parity/summary.json')
    req(d['exactParity'] is True and d['mismatches']==0 and d['repairParityExact'] is True,'native parity summary')
    req(d['productionRepairHullPerKit']==1 and d['parityOnlyRepairHullPerKit']==2 and d['criticalCadenceMigrated'] is False,'native parity repair/critical')
    p=js(path/'research-parity/summary.json'); req(p['passed'] is True and p['cases']==25 and p['errors']==[],'native research parity')
    req((path/'xunit/cp122-tests.trx').is_file(),'native xUnit TRX missing')


def validate_manifest(repo:Path,count:int):
    rel='docs/validation/evidence/checkpoint-122/CP122_REPOSITORY_SHA256SUMS.txt'; mf=repo/rel
    expected={}
    for line in text(mf).splitlines():
        if not line.strip(): continue
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line); req(m is not None,f'bad manifest row: {line}')
        h,r=m.groups(); expected[r]=h
    req(len(expected)==count,f'manifest count {len(expected)} != definition {count}')
    actual=sorted(p.relative_to(repo).as_posix() for p in repo.rglob('*') if p.is_file() and p.relative_to(repo).as_posix()!=rel and owned(p.relative_to(repo).as_posix()))
    req(actual==sorted(expected),f'manifest path mismatch missing={sorted(set(expected)-set(actual))[:8]} extra={sorted(set(actual)-set(expected))[:8]}')
    for r in actual:req(sha(repo/r)==expected[r],f'manifest hash mismatch {r}')


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); ap.add_argument('--native-results'); ap.add_argument('--skip-manifest',action='store_true'); a=ap.parse_args(); repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-122/checkpoint_122_definition.json'); e=d['expected']
        validate_definition(repo,d,e)
        print('       Validating accepted CP121 provenance and canonical migration regeneration...'); validate_cp121(repo); validate_preflight(repo)
        print('       Validating canonical authorities, production code boundaries, and DamCon exception...'); validate_authorities(repo,d); validate_code(repo)
        print('       Validating active documentation, wrapper, hygiene, and JSON corpus...'); validate_docs(repo); validate_wrapper(repo); validate_hygiene(repo); n=validate_json(repo); req(n>=e['jsonFilesMinimum'],f'JSON count {n} below {e["jsonFilesMinimum"]}')
        if a.native_results:
            print('       Validating CP122 native deterministic evidence...'); validate_native(Path(a.native_results).resolve(),e)
        if not a.skip_manifest:
            print('       Validating full repository manifest...'); validate_manifest(repo,int(e['repositoryOwnedFiles']))
        print(f"       CP122 contract verified: {e['repositoryOwnedFiles'] if not a.skip_manifest else 'pre-manifest'} repository-owned files; {n} JSON files; canonical x2 point domain; Repair Kit=1 production/2 parity; critical cadence deferred; no Monte Carlo.")
        return 0
    except Exception as exc:
        print(f'CP122 contract failure: {exc}',file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
