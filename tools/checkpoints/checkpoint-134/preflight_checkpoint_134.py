#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys, unittest, zipfile
from pathlib import Path

CP133_RESULTS_SHA='74c23a76553ede87e4f7352a5b0193f100a364335796125ed996fe29a9c9e522'
CP133_MANIFEST='docs/validation/evidence/checkpoint-133/CP133_REPOSITORY_SHA256SUMS.txt'

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

def count_suite(suite):
    return sum(count_suite(x) if isinstance(x,unittest.TestSuite) else 1 for x in suite)

def validate_cp133(repo):
    base=repo/'docs/validation/evidence/checkpoint-134/accepted-cp133'
    z=base/'checkpoint-133-native-results.zip'; req(sha(z)==CP133_RESULTS_SHA,'CP133 native-results ZIP hash')
    s=js(base/'CP133_NATIVE_ACCEPTANCE_SUMMARY.json')
    req(s['checkpoint']==133 and s['failedGates']==[],'CP133 accepted identity')
    req(s['pythonTestsPassed']==196 and s['xunitPassed']==910 and s['scenarioRunnerSelfTestsPassed']==70 and s['researchParityPassed']==25,'CP133 accepted gates')

def validate_frozen_candidate_authorities(repo):
    old=manifest(repo/CP133_MANIFEST)
    for rel in (
        'docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_8.json',
        'docs/archive/player_technology/pre-cp165-active/StarCluster_Revised_TL1_TL9_Technology_Component_Table_v0_8.xlsx',
        'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_5.json',
        'docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json',
        'src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs',
        'docs/archive/testing/pre-cp165-active/canonical_combat_kernel_fixtures_v0_1.json',
    ):
        req(rel in old,f'CP133 manifest missing {rel}')
        req(sha(repo/rel)==old[rel],f'CP133-frozen authority drift {rel}')
    archived='docs/archive/concepts/Star_Cluster_Game_Concept_v0.7t.docx'
    req(sha(repo/archived)==old['docs/Star_Cluster_Game_Concept_v0.7t.docx'],'archived v0.7t Concept must be exact CP133 copy')

def validate_matrix(repo):
    d=js(repo/'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_6.json')
    req(d['checkpoint']==134 and d['schemaVersion'].endswith('v0.6'),'matrix CP134 identity')
    cm=d['combatModifiers']; req(cm['directFireApproximateTrackPenaltyPp']==-25 and cm['directFireExtendedRangePenaltyPp']==-10 and cm['modifiersStack'] is True,'universal direct-fire modifiers')
    p=d['profiles']
    # CP133 candidate values remain fixed; CP134 only changes rule ownership/metadata needed to execute them.
    H=[(35,24),(35,25),(36,26),(36,27),(37,28),(37,29),(38,30),(38,31),(39,32)]
    A=[(0,6,0),(0,8,0),(1,9,0),(1,10,0),(2,10,0),(1,10,1),(1,12,2),(2,12,2),(3,14,3)]
    Sh=[(4,2,1,2,0),(5,2,1,3,0),(6,2,2,2,0),(7,3,2,2,0),(8,2,2,3,0),(8,4,2,2,0),(9,3,2,3,0),(10,4,3,2,1),(12,6,3,2,1)]
    K=[(20,6,0,0,2,3,1),(20,7,0,1,2,3,1),(20,7,0,1,2,4,1),(25,7,0,2,2,4,1),(25,8,0,2,3,5,1),(30,8,0,2,3,6,1),(30,9,0,2,3,6,1),(30,10,0,3,4,7,2),(35,11,0,3,4,8,2)]
    E=[(4,25,2,5,0,0,2),(4,30,2,5,0,0,3),(5,30,2,5,0,0,4),(6,30,2,6,0,0,4),(6,30,2,6,1,0,4),(7,35,2,6,1,0,5),(7,35,2,7,1,0,5),(8,35,4,8,2,0,5),(9,40,4,9,2,0,5)]
    M=[(6,2,8,0,0),(7,3,8,0,0),(7,4,8,0,0),(8,5,9,0,0),(9,6,10,0,0),(10,7,10,0,0),(10,8,11,0,0),(11,9,12,1,0),(12,10,14,1,0)]
    S={2:(7,3,3,0,0,10,10),3:(7,4,3,0,0,10,10),4:(8,5,4,0,0,10,10),5:(9,6,4,0,0,10,10),6:(10,7,4,0,0,10,10),7:(10,8,5,0,0,15,15),8:(11,9,5,1,0,15,15),9:(12,10,6,1,0,15,15)}
    for i,tl in enumerate(range(1,10)):
        h=p['hull'][str(tl)]; req((h['capacity'],h['hullPoints'])==H[i],f'hull TL{tl}')
        a=p['armor'][str(tl)]; req((a['ap'],a['ai'],a['tacticalRegenerationCapTp'])==A[i],f'armor TL{tl}')
        sh=p['shield'][str(tl)]; req((sh['capacity'],sh['baseRecharge'],sh['tacticalRechargePerTp'],sh['tacticalRechargeCapTp'],sh['shieldArmor'])==Sh[i],f'shield TL{tl}'); req(sh['baseRecharge']+sh['tacticalRechargePerTp']*sh['tacticalRechargeCapTp']>=sh['capacity'],f'shield refill TL{tl}')
        k=p['kinetic_main'][str(tl)]; req((k['accuracyPp'],k['damage'],k['spen'],k['apen'],k['standardRange'],k['maxRange'],k['firingTp'])==K[i] and k['ammo']==100,f'kinetic TL{tl}')
        e=p['energy_main'][str(tl)]; req((e['maxRange'],e['accuracyPp'],e['standardTp'],e['standardDamage'],e['spen'],e['apen'],e['standardRange'])==E[i] and e['strainLimit']==2,f'energy TL{tl}')
        md=p['missile_delivery'][str(tl)]; mw=p['missile_gp_warhead'][str(tl)]; req((md['range'],md['missileMove'],mw['damage'],mw['spen'],mw['apen'])==M[i] and md['launchTp']==0 and md['flights']==25,f'missile TL{tl}')
        sw=p['missile_swarmer'][str(tl)]
        if tl==1:req(sw['available'] is False,'Swarmer TL1')
        else:req((md['range'],md['missileMove'],sw['packetDamage'],sw['spen'],sw['apen'],sw['terminalGuidanceBonusPp'],sw['pdsInterceptPenaltyPp'])==S[tl] and sw['packetCount']==2,f'Swarmer TL{tl}')
    for tl in range(1,10):
        c=p['computer'][str(tl)]; req('approxPenaltyPp' not in c and 'legacyApproxPenaltyPp' in c,f'computer Approx ownership TL{tl}')
    seeds={x['id']:x for x in d['candidateBranchSeeds']}; req(seeds['A_b1']['tl6']=={'ap':2,'ai':12,'tacticalRegenerationCapTp':0},'A_b1 seed')
    st=d['sameTlCalibrationContract']; req(st['implementedCheckpoint']==134 and st['mandatoryDefenses']==['shield','armor'] and st['tl6ArmorProfiles']==['mainline','A_b1'],'same-TL contract')

def docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml=z.read('word/document.xml').decode('utf-8')
    import re
    return re.sub(r'<[^>]+>',' ',xml).replace('&gt;','>').replace('&lt;','<').replace('&amp;','&')

def validate_concept(repo):
    active=repo/'docs/Star_Cluster_Game_Concept_v0.7u.docx'; req(active.is_file(),'active Concept v0.7u')
    t=docx_text(active)
    for phrase in ('Approximate-track direct fire is a universal combat rule','-25 percentage-point accuracy modifier','universal provisional -10 percentage-point extended-range','Every normal Energy Main Weapon supports three bounded output levels','restores 1 AI per Tactical Power spent'):
        req(phrase in t,f'Concept missing {phrase}')
    req('Weapon-specific degraded fire is an explicit direct-fire capability' not in t,'stale weapon-specific degraded-fire prose remains')
    req('-5 × n percentage points' not in t,'stale per-hex direct-fire range table remains')

def validate_sources(repo):
    df=text(repo/'src/StarCluster.Core/Combat/DirectFire/DirectFireTargetEligibility.cs')
    req('ApproximateTrackAccuracyPenaltyPp = -25' in df and 'ExtendedRangeAccuracyPenaltyPp = -10' in df,'C# direct-fire constants')
    req('weapon.StandardRangeHexes' in df and 'tacticalComputer' in df,'C# standard-range/compatibility surface')
    ep=text(repo/'src/StarCluster.Core/Combat/DirectFire/EnergyMainOutputRules.cs'); req('EnergyMainOutputMode.Low' in ep and 'EnergyMainOutputMode.Overload' in ep and 'StrainGained' in ep,'C# Energy output rules')
    ar=text(repo/'src/StarCluster.Core/Combat/Damage/ArmorTacticalRegenerationService.cs'); req('armor.RestoreIntegrity' in ar and 'tacticalPowerCap' in ar,'C# Armor regeneration')
    cm=text(repo/'tools/simulation/starcluster_research/canonical_mechanics.py'); req('DIRECT_FIRE_APPROXIMATE_TRACK_PENALTY_PP = -25' in cm and 'DIRECT_FIRE_EXTENDED_RANGE_PENALTY_PP = -10' in cm and 'energy_output_modes' in cm,'Python canonical mechanics')
    cc=text(repo/'tools/simulation/starcluster_research/canonical_combat.py'); req('CANONICAL_COMBAT_KERNEL_VERSION = "0.2"' in cc and '_apply_armor_regeneration' in cc,'Python canonical kernel 0.2')
    cli=text(repo/'tools/simulation/starcluster_research/cli.py'); req("same-tl-candidate-baseline-study" in cli,'CP134 CLI routing')

def validate_tests_and_plan(repo):
    all_suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_*.py')
    req(count_suite(all_suite)==204,f'Python test discovery {count_suite(all_suite)} != 204')
    cp_suite=unittest.defaultTestLoader.discover(str(repo/'tools/simulation/tests'),pattern='test_cp134_candidate_baseline_kernel.py')
    req(count_suite(cp_suite)==8,f'CP134 test discovery {count_suite(cp_suite)} != 8')
    sys.path.insert(0,str(repo/'tools/simulation'))
    from starcluster_research.same_tl_candidate_baseline_analysis import build_plan
    result=build_plan(repo,repo/'docs/archive/testing/pre-cp165-active/cp134_same_tl_candidate_baseline_study_v0_1.json',None)['summary']
    req(result['failedGates']==[],'study plan failed')
    req((result['logicalContexts'],result['generatedVariants'],result['tl6Variants'],result['plannedSubstantiveTrials'])==(196,392,136,1960000),'study shape')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',required=True);a=ap.parse_args();repo=Path(a.repo).resolve()
    try:
        d=js(repo/'tools/checkpoints/checkpoint-134/checkpoint_134_definition.json');req(d['checkpoint']==134 and d['declaredSubstantiveTrials']==1960000 and d['balanceTargets'] is None,'definition')
        print('       Validating accepted CP133 native evidence...');validate_cp133(repo)
        print('       Verifying CP133 candidate table/workbook, Storyboard, layered damage, and shared fixture stay frozen...');validate_frozen_candidate_authorities(repo)
        print('       Validating CP133 numerical candidate and CP134 mechanics ownership/schema...');validate_matrix(repo)
        print('       Validating active Concept v0.7u...');validate_concept(repo)
        print('       Validating C#/Python canonical kernel v0.2 surfaces...');validate_sources(repo)
        print('       Validating Python discovery counts and full same-TL study plan...');validate_tests_and_plan(repo)
        print('       CP134 preflight passed: accepted CP133 candidate preserved; kernel v0.2 mechanics synchronized; 196 contexts / 392 variants / 136 TL6 variants; no 50/50 target or automatic promotion.')
        return 0
    except Exception as e:
        print(f'CP134 preflight failure: {e}',file=sys.stderr);return 1
if __name__=='__main__':raise SystemExit(main())
