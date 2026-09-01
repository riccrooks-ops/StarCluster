#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

POINT_IDS = {
    'hull_points','armor_protection','armor_integrity','shield_capacity','shield_base_recharge',
    'shield_tactical_recharge_rate','shield_degraded_base_recharge','shield_overcapacity_amount',
    'shield_recovery_overload_bonus','shield_hardener_max_sa','shield_hardener_overload_sa',
    'shield_battery_restore','kinetic_damage','kinetic_spen','kinetic_apen','energy_low_damage',
    'energy_standard_damage','energy_spen','energy_apen','energy_overload_damage',
    'missile_warhead_damage','missile_warhead_spen','missile_warhead_apen',
    'damage_control_calibration_hull_threshold',
}
PROFILE_POINTS = {
    'hull': {'hullPoints'}, 'armor': {'ap','ai'},
    'shield': {'capacity','baseRecharge','tacticalRechargePerTp','shieldArmor'},
    'kinetic_main': {'damage','spen','apen'},
    'energy_main': {'lowDamage','standardDamage','highDamage','spen','apen'},
    'missile_delivery': {'warheadDamage','spen','apen'},
}
RUNTIME_DEFENSE_POINTS = {'hull','armorIntegrity','armorProtection','shieldCapacity','shieldBaseRecharge','shieldArmor'}
RUNTIME_WEAPON_POINTS = {'damage','shieldPenetration','armorPenetration'}
AUX_POINTS = {'shieldBatteryRestore','shieldCapacityBonus','shieldRechargePerPower','ablativeProtection','ablativeIntegrity','shieldHardenerStrength','energizedArmorProtectionBonus'}
SOURCE_PATHS = (
    'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv',
    'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_4.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-auxiliary-runtime-profiles-v0_3.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl4-standard-runtime-profiles-v0_2.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-tl4-production-auxiliary-profiles-v0_2.json',
)
GENERATED_PATHS = (
    'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_4.csv',
    'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_2.json',
    'docs/archive/player_technology/pre-cp165-active/TL1_TL9_Canonical_Numerical_Technology_Matrix_v0_2.md',
    'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_1.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_5.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-auxiliary-runtime-profiles-v0_4.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl4-standard-runtime-profiles-v0_3.json',
    'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-tl4-production-auxiliary-profiles-v0_3.json',
)

CP122_CHANGED_CSHARP = (
    'src/StarCluster.Core/Combat/Damage/DamagePointScale.cs',
    'src/StarCluster.Core/Combat/InternalDamage/ComponentPerformance.cs',
    'src/StarCluster.ScenarioRunner/DamageScaling/CanonicalDamageScaleParityRunner.cs',
    'src/StarCluster.ScenarioRunner/Program.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1CombatPacingRunner.cs',
    'src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs',
    'tests/StarCluster.Tests/Combat/InternalDamage/CanonicalDamageScaleMigrationTests.cs',
)
CSHARP_DEPENDENCY_IMPORTS = {
    'ComponentCondition': 'using StarCluster.Core.Combat.Components;',
}



def req(ok: bool, msg: str) -> None:
    if not ok:
        raise AssertionError(msg)


def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def csv_rows(path: Path):
    with path.open(newline='',encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def cp121_manifest(repo: Path) -> dict[str,str]:
    path=repo/'docs/validation/evidence/checkpoint-121/CP121_REPOSITORY_SHA256SUMS.txt'
    out={}
    for line in path.read_text(encoding='utf-8').splitlines():
        m=re.fullmatch(r'([0-9a-f]{64})  (.+)',line)
        if m: out[m.group(2)]=m.group(1)
    return out


def validate_historical_sources(repo: Path) -> None:
    manifest=cp121_manifest(repo)
    for rel in SOURCE_PATHS:
        req(rel in manifest,f'CP121 manifest missing historical source {rel}')
        req(sha(repo/rel)==manifest[rel],f'historical source changed from accepted CP121: {rel}')


def validate_tl1(repo: Path) -> None:
    old=csv_rows(repo/SOURCE_PATHS[0]); new=csv_rows(repo/GENERATED_PATHS[0])
    req([r['parameter_id'] for r in old]==[r['parameter_id'] for r in new],'TL1 row identity/order changed')
    for a,b in zip(old,new):
        pid=a['parameter_id']
        if pid in POINT_IDS:
            av=int(a['value']); bv=int(b['value'])
            req(bv==av*2,f'TL1 point field not exactly x2: {pid}')
        else:
            req(b['value']==a['value'],f'TL1 non-point value changed: {pid}')
    by={r['parameter_id']:r for r in new}
    req(by['hull_points']['value']=='24','TL1 Hull must be 24')
    req(by['energy_standard_damage']['value']=='6','TL1 Energy standard damage must be 6')
    req(by['repair_hull_chance']['display_name']=='Repair 1 Hull','production Repair Kit must remain 1 Hull')
    req('1 canonical Hull point' in by['repair_hull_chance']['rationale'],'repair exception rationale missing')
    req(by['shield_hardener_power_per_sa']['value']=='1' and by['shield_hardener_power_per_sa']['unit']=='TP per installed hardener','Hardener power semantics must remain 1 TP per installed hardener')


def validate_matrix(repo: Path) -> None:
    old=js(repo/SOURCE_PATHS[1]); new=js(repo/GENERATED_PATHS[1])
    scale=new['damagePointScale']
    req(scale['canonicalScale']==2 and scale['legacyScale']==1,'matrix scale metadata')
    req(scale['damageControlHullPerRepairKit']==1 and scale['parityOnlyHullPerRepairKit']==2,'matrix repair exception metadata')
    req(scale['criticalsMigrated'] is False and scale['balanceChangeIntended'] is False,'matrix critical/balance boundary')
    for fam,oldtiers in old['profiles'].items():
        newtiers=new['profiles'][fam]
        req(set(oldtiers)==set(newtiers),f'matrix tier keys changed for {fam}')
        points=PROFILE_POINTS.get(fam,set())
        for tl,a in oldtiers.items():
            b=newtiers[tl]
            for key,value in a.items():
                if key in points:
                    req(int(b[key])==int(value)*2,f'matrix {fam} TL{tl} {key} not x2')
                else:
                    req(b.get(key)==value,f'matrix non-point changed {fam} TL{tl} {key}')
    req(new['profiles']['hull']['1']['hullPoints']==24,'matrix TL1 Hull')
    req(new['profiles']['armor']['3']['ap']==2 and new['profiles']['armor']['3']['ai']==10,'matrix TL3 Armor')
    req(new['profiles']['shield']['3']['capacity']==6,'matrix TL3 Shield')
    req(new['profiles']['missile_delivery']['1']['warheadDamage']==10,'matrix TL1 Missile')


def validate_standard_runtime_pair(repo: Path, old_rel: str, new_rel: str) -> None:
    old=js(repo/old_rel); new=js(repo/new_rel)
    req(new['damagePointScale']==2 and new['policy']['productionDamageControlHullPerRepairKit']==1,'standard runtime policy')
    old_by={p['id']:p for p in old['profiles']}; new_by={p['id']:p for p in new['profiles']}
    req(set(old_by)==set(new_by),f'standard runtime profile IDs changed: {old_rel}')
    for pid,a in old_by.items():
        b=new_by[pid]
        for key,val in a['defense'].items():
            req(b['defense'][key]==val*(2 if key in RUNTIME_DEFENSE_POINTS else 1),f'standard {pid} defense {key}')
        for weapon,wa in a['weapons'].items():
            wb=b['weapons'][weapon]
            for key,val in wa.items():
                if val is None: req(wb[key] is None,f'standard {pid} {weapon} {key}')
                elif key in RUNTIME_WEAPON_POINTS: req(wb[key]==val*2,f'standard {pid} {weapon} {key} not x2')
                else: req(wb[key]==val,f'standard non-point changed {pid} {weapon} {key}')
        for section in ('powerAndControl','movement'):
            req(b[section]==a[section],f'standard non-point section changed {pid} {section}')


def validate_aux_runtime_pair(repo: Path, old_rel: str, new_rel: str) -> None:
    old=js(repo/old_rel); new=js(repo/new_rel)
    req(new['damagePointScale']==2,'aux runtime scale metadata')
    old_by={p['id']:p for p in old['profiles']}; new_by={p['id']:p for p in new['profiles']}
    req(set(old_by)==set(new_by),f'aux profile IDs changed: {old_rel}')
    for pid,a in old_by.items():
        b=new_by[pid]
        for key,val in a.items():
            if key in AUX_POINTS: req(b[key]==val*2,f'aux {pid} {key} not x2')
            else: req(b.get(key)==val,f'aux non-point changed {pid} {key}')


def validate_runtime_catalogs(repo: Path) -> None:
    validate_standard_runtime_pair(repo,SOURCE_PATHS[2],GENERATED_PATHS[4])
    validate_aux_runtime_pair(repo,SOURCE_PATHS[3],GENERATED_PATHS[5])
    validate_standard_runtime_pair(repo,SOURCE_PATHS[4],GENERATED_PATHS[6])
    validate_aux_runtime_pair(repo,SOURCE_PATHS[5],GENERATED_PATHS[7])
    aux=js(repo/GENERATED_PATHS[7])
    by={p['id']:p for p in aux['profiles']}
    hardeners=[p for p in by.values() if p.get('shieldHardenerStrength',0)>0]
    req(hardeners and all(p['shieldHardenerStrength']%2==0 for p in hardeners),'canonical TL3/TL4 hardener strength must be x2')
    req(all(p.get('shieldHardenerPower',0) in (0,1,2) for p in hardeners),'Hardener Tactical Power must not be x2-scaled')
    energized=[p for p in by.values() if p.get('energizedArmorProtectionBonus',0)>0]
    req(energized and all(p['energizedArmorProtectionBonus']%2==0 for p in energized),'canonical energized Armor flat bonus must be x2')


def validate_regeneration(repo: Path) -> None:
    script=repo/'tools/checkpoints/checkpoint-122/migrate_canonical_damage_scale.py'
    with tempfile.TemporaryDirectory(prefix='starcluster-cp122-regen-') as td:
        temp=Path(td)
        for rel in SOURCE_PATHS:
            dst=temp/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(repo/rel,dst)
        result=subprocess.run([sys.executable,'-B',str(script),'--repo',str(temp)],capture_output=True,text=True)
        req(result.returncode==0,f'canonical regeneration failed: {result.stdout}\n{result.stderr}')
        for rel in GENERATED_PATHS:
            req((temp/rel).is_file(),f'regeneration missing {rel}')
            req((temp/rel).read_bytes()==(repo/rel).read_bytes(),f'canonical output not byte reproducible: {rel}')


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root=ET.fromstring(z.read('word/document.xml'))
    ns='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    return '\n'.join((n.text or '') for n in root.iter(ns+'t'))



def validate_csharp_dependency_bindings(repo: Path) -> None:
    req(
        (repo / 'src/StarCluster.Core/Combat/Components/ComponentCondition.cs').is_file(),
        'ComponentCondition authority is missing',
    )
    for rel in CP122_CHANGED_CSHARP:
        path = repo / rel
        req(path.is_file(), f'CP122 changed C# file missing: {rel}')
        source = path.read_text(encoding='utf-8-sig')
        for symbol, import_line in CSHARP_DEPENDENCY_IMPORTS.items():
            if symbol not in source:
                continue
            declares_symbol = re.search(
                rf'\b(?:class|record|struct|enum|interface)\s+{re.escape(symbol)}\b',
                source,
            ) is not None
            fully_qualified = f'StarCluster.Core.Combat.Components.{symbol}' in source
            req(
                declares_symbol or fully_qualified or import_line in source,
                f'CP122 C# dependency binding missing for {symbol}: {rel}',
            )


def validate_code_and_docs(repo: Path) -> None:
    dps=(repo/'src/StarCluster.Core/Combat/Damage/DamagePointScale.cs').read_text()
    cp=(repo/'src/StarCluster.Core/Combat/InternalDamage/ComponentPerformance.cs').read_text()
    req('public const int Current = 2;' in dps and 'HalfDamageRoundedUp' in dps and 'Math.Min(damage, scaled)' in dps,'canonical damage scale helper / odd-value safety clamp')
    req('damagePointScale = DamagePointScale.Current' in cp and 'DamagePointScale.HalfDamageRoundedUp(normalDamage, damagePointScale)' in cp,'Energy scale-aware damage rounding')
    for rel in ('src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs','src/StarCluster.ScenarioRunner/TL1Calibration/Tl1CombatPacingRunner.cs'):
        text=(repo/rel).read_text(); calls=text.count('ComponentPerformance.Weapon('); legacy=text.count('damagePointScale: DamagePointScale.Legacy')
        req(calls==legacy,f'historical runner must bind every weapon conditioning call to legacy scale: {rel}')
    ship=(repo/'src/StarCluster.Core/Combat/InternalDamage/ShipDamageState.cs').read_text()
    req('Defense.RestoreHull(1);' in ship,'production Damage Control must restore 1 Hull')
    req('RestoreHull(2)' not in '\n'.join(p.read_text() for p in (repo/'src/StarCluster.Core').rglob('*.cs')),'2-Hull parity repair leaked into production core')
    manifest=cp121_manifest(repo)
    for rel in ('src/StarCluster.Core/Combat/InternalDamage/InternalDamageTrack.cs','src/StarCluster.Core/Combat/InternalDamage/ShipDamageResolver.cs','src/StarCluster.Core/Combat/InternalDamage/DamageControl.cs','src/StarCluster.Core/Combat/InternalDamage/ShipDamageState.cs'):
        req(sha(repo/rel)==manifest[rel],f'critical/DamCon core drift outside CP122 scope: {rel}')
    concept=docx_text(repo/'docs/Star_Cluster_Game_Concept_v0.7m.docx')
    for phrase in ('canonical x2 integer ruler','restore exactly 1 canonical Hull','critical cadence under the canonical x2 Hull ruler is deferred','canonical Shield Armor 2','AP2/AI10'):
        req(phrase.lower() in concept.lower(),f'Concept missing CP122 semantic: {phrase}')
    audit=js(repo/'docs/archive/testing/pre-cp165-active/canonical_damage_domain_implementation_audit_v0_1.json')
    req(audit['canonicalScale']==2 and audit['productionRepairHullPerKit']==1 and audit['parityOnlyRepairHullPerKit']==2,'implementation audit scale/repair boundary')
    req(audit['criticalCadenceMigrated'] is False and audit['oddHalfStepValuesPromoted'] is False,'implementation audit critical/odd boundary')
    authority=js(repo/'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_1.json')
    req(authority['damagePointScale']==2 and authority['productionDamageControlHullPerRepairKit']==1 and authority['parityOnlyHullPerRepairKit']==2,'canonical authority repair/scale')
    req(authority['criticalCadenceMigrationDeferred'] is True and authority['oddHalfStepValuesPromoted'] is False,'canonical authority deferred critical/odd value')


def validate_cp121(repo: Path) -> None:
    path=repo/'docs/validation/evidence/checkpoint-122/CP121_NATIVE_RESULTS_ACCEPTED.zip'
    req(sha(path)=='7292b23b559c1ebb0c551c0cd09c3588cc3127e72a131b6eabebbd50ed9aff1e','accepted CP121 archive hash')
    s=js(repo/'docs/validation/evidence/checkpoint-122/CP122_ACCEPTED_CP121_NATIVE_SUMMARY.json')
    req(s['equivalencePairedTrials']==85680 and s['equivalenceMismatchedTrials']==0 and s['equivalenceExact'] is True,'CP121 equivalence evidence')
    req(s['halfStepTrials']==4848000 and s['trialErrors']==0 and s['failedGates']==[],'CP121 half-step evidence')


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); args=ap.parse_args(); repo=Path(args.repo).resolve()
    try:
        validate_cp121(repo)
        validate_historical_sources(repo)
        validate_regeneration(repo)
        validate_tl1(repo); validate_matrix(repo); validate_runtime_catalogs(repo)
        validate_csharp_dependency_bindings(repo)
        validate_code_and_docs(repo)
        print('       CP122 preflight: accepted CP121 evidence verified; historical sources frozen; eight canonical successors byte-reproducible; point domains exactly x2; non-point domains held; Repair Kit=1 production/2 parity; critical cadence deferred; changed C# dependency bindings verified.')
        return 0
    except Exception as exc:
        print(f'CP122 preflight failure: {exc}',file=sys.stderr); return 1

if __name__=='__main__': raise SystemExit(main())
