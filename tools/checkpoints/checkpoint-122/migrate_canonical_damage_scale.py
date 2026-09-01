#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
from pathlib import Path

SCALE = 2

TL1_POINT_IDS = {
    'hull_points',
    'armor_protection', 'armor_integrity',
    'shield_capacity', 'shield_base_recharge', 'shield_tactical_recharge_rate',
    'shield_degraded_base_recharge', 'shield_overcapacity_amount',
    'shield_recovery_overload_bonus', 'shield_hardener_max_sa',
    'shield_hardener_overload_sa', 'shield_battery_restore',
    'kinetic_damage', 'kinetic_spen', 'kinetic_apen',
    'energy_low_damage', 'energy_standard_damage', 'energy_spen', 'energy_apen',
    'energy_overload_damage',
    'missile_warhead_damage', 'missile_warhead_spen', 'missile_warhead_apen',
    'damage_control_calibration_hull_threshold',
}

PROFILE_POINT_FIELDS = {
    'hull': ('hullPoints',),
    'armor': ('ap', 'ai'),
    'shield': ('capacity', 'baseRecharge', 'tacticalRechargePerTp', 'shieldArmor'),
    'kinetic_main': ('damage', 'spen', 'apen'),
    'energy_main': ('lowDamage', 'standardDamage', 'highDamage', 'spen', 'apen'),
    'missile_delivery': ('warheadDamage', 'spen', 'apen'),
}

RUNTIME_POINT_FIELDS = {
    'defense': ('hull', 'armorIntegrity', 'armorProtection', 'shieldCapacity', 'shieldBaseRecharge', 'shieldArmor'),
}
WEAPON_POINT_FIELDS = ('damage', 'shieldPenetration', 'armorPenetration')
AUX_POINT_FIELDS = ('shieldBatteryRestore', 'shieldCapacityBonus', 'shieldRechargePerPower', 'ablativeProtection', 'ablativeIntegrity', 'shieldHardenerStrength', 'energizedArmorProtectionBonus')

BRANCH_NUMERIC = {
    'ablative-armor': 'AP0 / AI4 expendable outer layer',
    'kinetic-smart-projectile': '+10 pp weapon accuracy; grants Approximate-Track Fire permission; attack still uses Tactical Computer penalty',
    'kinetic-dense-penetrator': 'DAM -2; APEN +2 relative to current standard Kinetic package',
    'kinetic-submunition': 'candidate 2 x DAM6 packets; standard SPEN/APEN per packet',
    'kinetic-helical': 'DAM8 / R4 / Acc25 / SPEN2 / APEN2 / 0 TP; candidate high-rate/efficiency identity',
    'kinetic-macron': 'candidate saturation weapon; 2 x DAM6 packets / R5 / Acc20 / SPEN2 / APEN2 / 2 TP',
    'armor-powered-reactive': '1 TP sustained; candidate +2 Protection against first eligible physical packet each turn',
    'armor-adaptive-reactive': '1 TP sustained; candidate +2 Protection against up to 2 eligible physical packets each turn',
    'armor-field-assisted': '2 TP sustained; candidate reduce post-penetration DAM by 2 (minimum 2) for eligible packets',
    'shield-hardener': '1 TP sustained -> Shield Armor 2; nonstacking',
    'shield-particle-screen': '1 TP sustained; candidate Shield Armor +2 only vs particle/charged-beam-tagged attacks',
    'shield-field-stabilizer': '1 TP sustained; candidate reduce incoming SPEN by 2 (minimum 0) before Shield Armor check',
    'energy-fel': 'R7 / Acc30 / Standard 3 TP DAM8; choose SPEN4/APEN2 or SPEN2/APEN4 before firing',
    'energy-ion': 'R5 / Acc25 / 3 TP / DAM8 / SPEN4 / APEN2',
    'energy-neutral-particle': 'R6 / Acc25 / 3 TP / DAM10 / SPEN2 / APEN4',
    'energy-plasma': 'R3 / Acc20 / 3 TP / DAM12 / SPEN2 / APEN4',
    'energy-extreme-frequency': 'R9 / Acc30 / 4 TP / DAM12 / SPEN4 / APEN4',
    'missile-extended-amm': 'intercept range 1; Base Chance 15; RC1; 2 TP; 20 interceptors',
    'missile-shaped-warhead': 'DAM10 / SPEN2 / APEN6',
    'missile-nuclear-shaped': 'DAM14 / SPEN4 / APEN6',
    'missile-swarm-bus': 'candidate launch up to 2 Missile Flights in one launch action; each consumes 1 flight and resolves/intercepts independently',
    'missile-fusion-warhead': 'DAM16 / SPEN4 / APEN6',
    'missile-antimatter-warhead': 'DAM20 / SPEN6 / APEN8',
    'missile-field-terminal': 'candidate +2 terminal Move only in final approach; no range extension; remains PDS-interceptable',
    'power-fission-revival-tl5': '6 Operational / 5 Degraded / 2 Emergency TP',
    'power-fission-revival-tl7': '7 Operational / 6 Degraded / 2 Emergency TP',
    'power-supercapacitor': 'candidate 3 stored TP; discharge up to 2 TP/turn; recharge from Available TP',
    'power-smes': 'candidate 5 stored TP; discharge up to 3 TP/turn',
    'power-ultracap': 'candidate 7 stored TP; discharge up to 4 TP/turn',
    'hull-repair-robotics': 'candidate +10 pp to one Damage Control attempt/turn; no extra repair step',
    'hull-repair-swarm': 'candidate +10 pp and may assist up to 2 allocated Damage Control attempts/turn; no free repair',
}


def canonical_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace('\r\n', '\n').replace('\r', '\n').encode('utf-8'))


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_json(path: Path, value) -> None:
    canonical_write_text(path, json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def migrate_tl1_csv(repo: Path) -> None:
    src = repo / 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv'
    dst = repo / 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_4.csv'
    with src.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    for row in rows:
        pid = row['parameter_id']
        if pid in TL1_POINT_IDS:
            value = int(row['value'])
            row['value'] = str(value * SCALE)
            row['status'] = row.get('status') or 'provisional_exact'
            suffix = ' Canonical CP122 x2 point-domain migration; no balance change intended.'
            if suffix.strip() not in row['rationale']:
                row['rationale'] = row['rationale'].rstrip() + suffix
        if pid == 'shield_hardener_power_per_sa':
            row['display_name'] = 'Shield Hardener normal power'
            row['unit'] = 'TP per installed hardener'
            row['rationale'] = ('Compatibility ID retained; 1 TP powers the installed TL1 Hardener, whose canonical x2 output is SA2. '
                                'Power is not charged once per new-scale SA point.')
            row['rationale'] += ' Do not multiply Tactical Power cost by the x2 damage-point scale.'
        if pid == 'repair_hull_chance':
            row['display_name'] = 'Repair 1 Hull'
            row['rationale'] = ('CP122 intentionally keeps a successful Repair Kit at 1 canonical Hull point. '
                                'Exact migration parity uses an artificial 2-Hull/kit test mode only; future Hull TL may improve repair yield.')
            row['rationale'] += ' Production rule is intentionally not x2-equivalent; chance remains unchanged.'
        if pid == 'damage_control_calibration_hull_threshold':
            row['rationale'] = ('Historical half-Hull calibration threshold migrated from 6/12 to 12/24 canonical Hull points. '
                                'This does not change the production Repair Kit yield.')
    out = []
    from io import StringIO
    s = StringIO(newline='')
    w = csv.DictWriter(s, fieldnames=fields, lineterminator='\n')
    w.writeheader(); w.writerows(rows)
    canonical_write_text(dst, s.getvalue())


def migrate_matrix(repo: Path) -> None:
    src = repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json'
    dst = repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_2.json'
    old = load_json(src)
    new = copy.deepcopy(old)
    new['schemaVersion'] = 'star-cluster-whole-ladder-numerical-matrix-v0.2'
    new['status'] = 'canonical_x2_point_domain_migration_no_balance_change'
    new['purpose'] = ('Canonical x2 damage-domain migration of the CP109 v0.1 whole-ladder candidate. '
                      'All point-domain quantities are doubled solely to increase integer resolution; non-point quantities are unchanged. '
                      'Repair Kit Hull yield intentionally remains 1 canonical Hull in production and is not encoded in this technology matrix.')
    new['damagePointScale'] = {
        'canonicalScale': 2,
        'legacyScale': 1,
        'legacyPointEqualsCanonicalPoints': 2,
        'migrationCheckpoint': 122,
        'balanceChangeIntended': False,
        'criticalsMigrated': False,
        'damageControlHullPerRepairKit': 1,
        'parityOnlyHullPerRepairKit': 2,
    }
    ab = new.get('authorityBoundary', {})
    ab['damagePointScale'] = 2
    ab['canonicalPointDomainMigration'] = True
    ab['balanceChangeIntended'] = False
    ab['criticalCadenceMigrationDeferred'] = True
    ab['productionDamageControlHullPerRepairKit'] = 1
    for family, fields in PROFILE_POINT_FIELDS.items():
        for row in new['profiles'][family].values():
            for field in fields:
                row[field] = int(row[field]) * SCALE
    for branch in new['branches']:
        branch['numeric'] = BRANCH_NUMERIC[branch['id']]
        if branch['id'] in {
            'ablative-armor','kinetic-dense-penetrator','kinetic-submunition','kinetic-helical','kinetic-macron',
            'armor-powered-reactive','armor-adaptive-reactive','armor-field-assisted','shield-hardener','shield-particle-screen',
            'shield-field-stabilizer','energy-fel','energy-ion','energy-neutral-particle','energy-plasma','energy-extreme-frequency',
            'missile-shaped-warhead','missile-nuclear-shaped','missile-fusion-warhead','missile-antimatter-warhead'}:
            branch['notes'] = branch['notes'].rstrip() + ' Point-domain magnitudes shown here use the canonical CP122 x2 scale.'

    # Rebuild only the point-domain portions of the human overview; other numbers remain unchanged.
    for item in new['overview']:
        tl = str(item['tl'])
        disc = item['discipline']
        if disc == 'Hull':
            r = new['profiles']['hull'][tl]
            item['numericSummary'] = f"Cruiser Structural Integration: Hull capacity {r['capacity']} Space; Hull {r['hullPoints']}"
        elif disc == 'Armor':
            r = new['profiles']['armor'][tl]
            hold = ' (hold)' if not r.get('newTech', True) else ''
            item['numericSummary'] = f"Passive Armor Materials: AP{r['ap']} / AI{r['ai']}{hold}"
        elif disc == 'Shields':
            r = new['profiles']['shield'][tl]
            item['numericSummary'] = (f"Shield Generator: {r['space']}S; Cap {r['capacity']}; BaseR {r['baseRecharge']}; "
                                      f"Tac {r['tacticalRechargePerTp']}/TP cap {r['tacticalRechargeCapTp']}; SA {r['shieldArmor']}")
        elif disc == 'Projectile Weapons':
            r = new['profiles']['kinetic_main'][tl]; p = new['profiles']['kinetic_pds'][tl]
            item['numericSummary'] = (f"Kinetic Main Weapon: {r['space']}S; DAM{r['damage']} SP{r['spen']} AP{r['apen']} "
                                      f"R{r['range']} Acc+{r['accuracyPp']} TP{r['firingTp']}\n"
                                      f"Kinetic PDS: {p['space']}S; Base {p['baseChancePp']}pp RC{p['reactionCapacity']} TP{p['readinessTp']} Ammo{p['ammo']}")
        elif disc == 'Energy Weapons':
            r = new['profiles']['energy_main'][tl]; p = new['profiles']['energy_pds'][tl]
            item['numericSummary'] = (f"Coherent Beam Main Weapon: {r['space']}S; R{r['range']} Acc+{r['accuracyPp']}; "
                                      f"L {r['lowTp']}TP/D{r['lowDamage']} S {r['standardTp']}TP/D{r['standardDamage']} "
                                      f"H {r['highTp']}TP/D{r['highDamage']}; SP{r['spen']} AP{r['apen']}\n"
                                      f"Energy / Beam PDS: {p['space']}S; Base {p['baseChancePp']}pp RC{p['reactionCapacity']} TP{p['readinessTp']}")
        elif disc == 'Missile Weapons':
            r = new['profiles']['missile_delivery'][tl]; p = new['profiles']['amm_pds'][tl]
            item['numericSummary'] = (f"Missile Delivery + Guidance: {r['space']}S; R{r['range']} Move{r['missileMove']} Hit{r['guidanceBaseHit']}%; "
                                      f"warhead D{r['warheadDamage']}/SP{r['spen']}/AP{r['apen']}\n"
                                      f"AMM PDS: {p['space']}S; Base {p['baseChancePp']}pp RC{p['reactionCapacity']} TP{p['readinessTp']} "
                                      f"Range{p['interceptRange']} Ammo{p['ammo']}")
    # Non-point whole-ship Space sanity is intentionally unchanged.
    write_json(dst, new)


def migrate_standard_runtime_catalog(
    repo: Path,
    source_name: str,
    target_name: str,
    target_id: str,
) -> None:
    root = repo / 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology'
    src = root / source_name
    dst = root / target_name
    old = load_json(src); new = copy.deepcopy(old)
    new['id'] = target_id
    new['checkpoint'] = 122
    new['status'] = 'checkpoint122_canonical_x2_damage_domain_migration'
    new['baselineSha256'] = 'generated canonical x2 successor; verified by CP122 contract'
    new['damagePointScale'] = 2
    new['policy'] = copy.deepcopy(new.get('policy', {}))
    new['policy'].update({
        'historicalSourceProfilesPreserved': True,
        'pointDomainExactlyDoubled': True,
        'nonPointDomainUnchanged': True,
        'balanceChangeIntended': False,
        'productionDamageControlHullPerRepairKit': 1,
        'criticalCadenceMigrationDeferred': True,
    })
    for profile in new['profiles']:
        for field in RUNTIME_POINT_FIELDS['defense']:
            profile['defense'][field] = int(profile['defense'][field]) * SCALE
        for weapon in profile['weapons'].values():
            for field in WEAPON_POINT_FIELDS:
                weapon[field] = int(weapon[field]) * SCALE
        if profile['id'] == 'tl1-production':
            profile['source'] = 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_4.csv'
        else:
            profile['source'] = 'Canonical CP122 x2 migration of: ' + profile['source']
    write_json(dst, new)


def migrate_aux_runtime_catalog(
    repo: Path,
    source_name: str,
    target_name: str,
    target_id: str,
) -> None:
    root = repo / 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology'
    src = root / source_name
    dst = root / target_name
    old = load_json(src); new = copy.deepcopy(old)
    new['id'] = target_id
    new['checkpoint'] = 122
    new['status'] = 'checkpoint122_canonical_x2_damage_domain_migration'
    new['damagePointScale'] = 2
    new['migrationNotes'] = ('Point-domain auxiliary effects are doubled. Tactical Power, counts, percentages, Space, ammunition, and repair-kit counts are unchanged.')
    for profile in new['profiles']:
        for field in AUX_POINT_FIELDS:
            if field in profile:
                profile[field] = int(profile[field]) * SCALE
    write_json(dst, new)


def migrate_runtime_catalogs(repo: Path) -> None:
    migrate_standard_runtime_catalog(
        repo,
        'tl1-tl3-standard-runtime-profiles-v0_4.json',
        'tl1-tl3-standard-runtime-profiles-v0_5.json',
        'tl1-tl3-standard-runtime-profiles-v0_5')
    migrate_aux_runtime_catalog(
        repo,
        'tl1-tl2-auxiliary-runtime-profiles-v0_3.json',
        'tl1-tl2-auxiliary-runtime-profiles-v0_4.json',
        'tl1-tl2-auxiliary-runtime-profiles-v0_4')
    migrate_standard_runtime_catalog(
        repo,
        'tl1-tl4-standard-runtime-profiles-v0_2.json',
        'tl1-tl4-standard-runtime-profiles-v0_3.json',
        'tl1-tl4-standard-runtime-profiles-v0_3')
    migrate_aux_runtime_catalog(
        repo,
        'tl3-tl4-production-auxiliary-profiles-v0_2.json',
        'tl3-tl4-production-auxiliary-profiles-v0_3.json',
        'tl3-tl4-production-auxiliary-profiles-v0_3')


def write_matrix_markdown(repo: Path) -> None:
    m = load_json(repo / 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_2.json')
    lines = [
        '# Star Cluster Canonical TL1-TL9 Numerical Technology Matrix v0.2',
        '',
        '**Status:** canonical x2 point-domain migration of the CP109 v0.1 candidate; no balance change is intended.',
        '',
        'CP122 changes the integer ruler only. One legacy damage/defense point equals two canonical points. Non-point quantities such as Space, Tactical Power, range, movement, accuracy/guidance percentages, ammunition, fuel, PDS Reaction Capacity, Sensor/EW ratings, and TL are unchanged.',
        '',
        'A successful production Damage Control Hull repair intentionally remains **1 canonical Hull point per Repair Kit**. Exact migration parity uses an artificial 2-Hull repair only inside the CP122 parity suite. Critical/H-X cadence migration is deferred until the critical system is fully implemented.',
        '',
        '## Point-domain progression',
        '',
        '| TL | Hull | Armor | Shield | Kinetic main | Energy main L/S/H | Missile GP |',
        '|---:|---:|---|---|---|---|---|',
    ]
    for tl in range(1,10):
        k=str(tl); h=m['profiles']['hull'][k]; a=m['profiles']['armor'][k]; s=m['profiles']['shield'][k]; kin=m['profiles']['kinetic_main'][k]; e=m['profiles']['energy_main'][k]; ms=m['profiles']['missile_delivery'][k]
        lines.append(
            f"| {tl} | {h['hullPoints']} | AP{a['ap']} / AI{a['ai']} | Cap{s['capacity']} / R{s['baseRecharge']} / {s['tacticalRechargePerTp']}/TP / SA{s['shieldArmor']} | "
            f"D{kin['damage']} SP{kin['spen']} AP{kin['apen']} | D{e['lowDamage']}/{e['standardDamage']}/{e['highDamage']} SP{e['spen']} AP{e['apen']} | "
            f"D{ms['warheadDamage']} SP{ms['spen']} AP{ms['apen']} |")
    lines += ['', '## Scaled optional/specialist point effects', '', '| Branch | Canonical numerical expression |', '|---|---|']
    for b in m['branches']:
        if b['id'] in {'ablative-armor','kinetic-dense-penetrator','kinetic-submunition','kinetic-helical','kinetic-macron','armor-powered-reactive','armor-adaptive-reactive','armor-field-assisted','shield-hardener','shield-particle-screen','shield-field-stabilizer','energy-fel','energy-ion','energy-neutral-particle','energy-plasma','energy-extreme-frequency','missile-shaped-warhead','missile-nuclear-shaped','missile-fusion-warhead','missile-antimatter-warhead'}:
            lines.append(f"| `{b['id']}` | {b['numeric']} |")
    lines += [
        '',
        '## Historical compatibility',
        '',
        '- `technology_numerical_matrix_v0_1.json` and its companion CP109 artifacts remain unchanged for historical checkpoint reproducibility.',
        '- CP122 introduces `technology_numerical_matrix_v0_2.json` as the canonical numerical ruler for new work.',
        '- No odd half-step value from CP121 is promoted by this migration. Existing values are doubled exactly.',
        '- Future progression checkpoints may use odd canonical integers where a validated half-step is desirable.',
        '',
    ]
    canonical_write_text(repo / 'docs/archive/player_technology/pre-cp165-active/TL1_TL9_Canonical_Numerical_Technology_Matrix_v0_2.md', '\n'.join(lines))


def write_authority(repo: Path) -> None:
    obj = {
        'schemaVersion': 'star-cluster-canonical-numerical-authority-v0.1',
        'checkpoint': 122,
        'damagePointScale': 2,
        'legacyPointEqualsCanonicalPoints': 2,
        'canonicalTl1Baseline': 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_4.csv',
        'canonicalWholeLadderMatrix': 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_2.json',
        'canonicalWholeLadderHumanReference': 'docs/archive/player_technology/pre-cp165-active/TL1_TL9_Canonical_Numerical_Technology_Matrix_v0_2.md',
        'canonicalTl1Tl3RuntimeProfiles': 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl3-standard-runtime-profiles-v0_5.json',
        'canonicalTl1Tl2AuxiliaryRuntimeProfiles': 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl2-auxiliary-runtime-profiles-v0_4.json',
        'canonicalTl1Tl4RuntimeProfiles': 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl1-tl4-standard-runtime-profiles-v0_3.json',
        'canonicalTl3Tl4AuxiliaryRuntimeProfiles': 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/tl3-tl4-production-auxiliary-profiles-v0_3.json',
        'historicalMatrixPreserved': 'docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json',
        'historicalTl1BaselinePreserved': 'docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_3.csv',
        'productionDamageControlHullPerRepairKit': 1,
        'parityOnlyHullPerRepairKit': 2,
        'criticalCadenceMigrationDeferred': True,
        'oddHalfStepValuesPromoted': False,
        'balanceChangeIntended': False,
    }
    write_json(repo / 'docs/archive/player_technology/pre-cp165-active/canonical_numerical_authority_v0_1.json', obj)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    migrate_tl1_csv(repo)
    migrate_matrix(repo)
    migrate_runtime_catalogs(repo)
    write_matrix_markdown(repo)
    write_authority(repo)
    print('CP122 canonical x2 numerical artifacts regenerated deterministically (eight successor authorities).')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
