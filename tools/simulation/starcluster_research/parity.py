from pathlib import Path
from .study import load_json, build_study
from .combat import (
    CombatData,
    direct_hit_chance,
    apply_damage,
    create_side,
    sensor_track,
    _armor,
    _ew,
    _hardener,
    _move,
    _pds,
    _reactor_power,
    _targeting,
    _weapon,
)

# Deterministic bridge cases that keep the Python research kernel aligned with
# the current production combat contract while retaining the accepted component
# values used by the historical fixture.  CP132 updates the layered-defense
# expectations to penetration-hardening-v1; Python remains a research/screening
# simulator rather than the production game authority.
PARITY_CASE_COUNT = 25


def run_parity(repo: Path):
    errors = []
    cases = 0

    def check(condition: bool, message: str):
        nonlocal cases
        cases += 1
        if not condition:
            errors.append(message)

    base = repo / 'src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology'
    primary = build_study(load_json(base / 'cross-tl-build-permutation-foundation-v1_1.json'))
    data = CombatData(repo)

    def find(**sel):
        for build in primary['builds']:
            if all(build.selections[k] == v for k, v in sel.items()):
                return build
        raise LookupError(sel)

    common = dict(
        hull='h3', reactor='r3', computer='c2', sensor='s2', shield='sh2',
        shieldHardener='hard0', armor='a3', ecm='ecm0', eccm='eccm0',
        stl='stl2', ftl='ftl2', pds='p0'
    )
    try:
        k2 = find(weapon='k2', **common)
        check(direct_hit_chance(k2, data, 3) == 67,
              f'direct-fire chance expected 67 got {direct_hit_chance(k2, data, 3)}')
        check(direct_hit_chance(k2, data, 0) == 82,
              f'range-zero direct-fire chance expected 82 got {direct_hit_chance(k2, data, 0)}')
        check(direct_hit_chance(k2, data, 20) == 5,
              f'direct-fire minimum clamp expected 5 got {direct_hit_chance(k2, data, 20)}')

        hardened_state = create_side(k2, data)
        hard_result = apply_damage(hardened_state, 5, 1, 2, 1)
        check((hardened_state.shield, hardened_state.armor_integrity,
               hardened_state.armor_protection, hardened_state.hull) == (0, 4, 1, 11),
              f'layered hardener damage mismatch: {hard_result}')

        ordinary_state = create_side(k2, data)
        ordinary_result = apply_damage(ordinary_state, 5, 1, 2, 0)
        check((ordinary_state.shield, ordinary_state.armor_integrity,
               ordinary_state.armor_protection, ordinary_state.hull) == (0, 4, 1, 11),
              f'layered ordinary damage mismatch: {ordinary_result}')

        observer = find(
            hull='h2', weapon='k2', reactor='r2', computer='c2', sensor='s2',
            shield='sh0', shieldHardener='hard0', armor='a2', ecm='ecm0',
            eccm='eccm0', stl='stl2', ftl='ftl2', pds='p0')
        jammer = find(
            hull='h2', weapon='k2', reactor='r2', computer='c2', sensor='s2',
            shield='sh0', shieldHardener='hard0', armor='a2', ecm='ecm2',
            eccm='eccm0', stl='stl2', ftl='ftl2', pds='p0')
        passive = sensor_track(observer, jammer, data, 2, 0)
        check(passive[:3] == ('Approximate', 'passive', 0),
              f'TL2 passive range-2 expected Approximate/passive/0, got {passive[:3]}')
        check(sensor_track(observer, jammer, data, 3, 6)[0] == 'Approximate',
              'DR1 versus ECM2 without ECCM must degrade Firm to Approximate at range 3')

        eccm2 = find(
            hull='h2', weapon='k2', reactor='r2', computer='c2', sensor='s2',
            shield='sh0', shieldHardener='hard0', armor='a2', ecm='ecm0',
            eccm='eccm2', stl='stl2', ftl='ftl2', pds='p0')
        restored = sensor_track(eccm2, jammer, data, 3, 6)
        check(restored[0] == 'Firm' and restored[2] == 3,
              f'TL2 ECCM2 must restore Firm at 3 total TP (ECCM2 + Low Active), got {restored}')

        s3 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh0', shieldHardener='hard0', armor='a3', ecm='ecm0',
            eccm='eccm0', stl='stl3', ftl='ftl2', pds='p0')
        low = sensor_track(s3, observer, data, 3, 6)
        check(low[:3] == ('Firm', 'low', 1),
              f'TL3 range-3 sensor expected Firm/low/1, got {low[:3]}')
        high = sensor_track(s3, observer, data, 4, 6)
        check(high[:3] == ('Firm', 'high', 2),
              f'TL3 high sensor expected Firm/high/2 at range 4, got {high[:3]}')

        eccm3 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh0', shieldHardener='hard0', armor='a3', ecm='ecm0',
            eccm='eccm3', stl='stl3', ftl='ftl2', pds='p0')
        jammer3 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh0', shieldHardener='hard0', armor='a3', ecm='ecm3',
            eccm='eccm0', stl='stl3', ftl='ftl2', pds='p0')
        tl3_ew = sensor_track(eccm3, jammer3, data, 3, 6)
        check(tl3_ew[0] == 'Firm' and tl3_ew[2] == 2,
              f'TL3 ECCM2 full-strength 1 TP + Low Active 1 TP expected Firm/2 TP, got {tl3_ew}')

        ecm3x2 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh0', shieldHardener='hard0', armor='a3', ecm='ecm3x2',
            eccm='eccm0', stl='stl3', ftl='ftl2', pds='p0')
        check(_ew(ecm3x2, 'ecm') == (2, 1),
              f'duplicate TL3 ECM must remain Rating2/non-additive at 1 TP, got {_ew(ecm3x2, "ecm")}')

        k3 = s3
        check(_weapon(k3, data)['power'] == 0,
              'K3 parity fixture must retain 0-TP ordinary fire')
        check(_reactor_power(k3) == 6,
              f'TL3 single reactor expected 6 TP, got {_reactor_power(k3)}')
        check(_targeting(k3, data) == 12 and
              int(k3.option_payloads['computer'].get('evasiveCompensation', 0)) == 5,
              'TL3 Tactical Computer must retain +12 targeting and EvComp5')
        check(_move(k3, data) == 3,
              f'TL3 STL expected Move3, got {_move(k3, data)}')
        armor = _armor(k3, data)
        check(armor == (5, 1),
              f'TL3 armor expected AI5/AP1, got {armor}')
        check(k3.capacity == 36,
              f'TL3 hull expected 36 Installation Space, got {k3.capacity}')

        e3 = find(weapon='e3', **{**common, 'computer':'c3', 'sensor':'s3', 'stl':'stl3'})
        ew = _weapon(e3, data)
        check((ew['damage'], ew['power'], int(ew['high_damage']), int(ew['high_power'])) == (3, 2, 4, 3),
              f'TL3 Energy modes expected standard 3/2 and High 4/3, got {ew}')

        m3 = find(weapon='m3', **{**common, 'computer':'c3', 'sensor':'s3', 'stl':'stl3'})
        mw = _weapon(m3, data)
        check(mw['missile_move'] == 4 and bool(m3.option_payloads['weapon'].get('standardOnboardNavigationSensor')),
              'TL3 Missile must retain Move4 and the standard onboard navigation sensor')

        hard3 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh2', shieldHardener='hard3', armor='a3', ecm='ecm0',
            eccm='eccm0', stl='stl3', ftl='ftl2', pds='p0')
        check(_hardener(hard3) == (True, 1, 1),
              f'TL3 Shield Hardener expected installed/SA1/1TP, got {_hardener(hard3)}')

        ammpds3 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh0', shieldHardener='hard0', armor='a3', ecm='ecm0',
            eccm='eccm0', stl='stl3', ftl='ftl2', pds='ammpds3')
        ap = _pds(ammpds3)
        check(ap is not None and (ap['chance'], ap['power'], ap['rc'], int(ap['fallback_power']), int(ap['fallback_rc']), int(ap['ammo'])) == (20, 2, 2, 1, 1, 25),
              f'TL3 AMM PDS expected base20/2TP/RC2 with 1TP/RC1 fallback/Ammo25, got {ap}')

        epds2 = find(
            hull='h2', weapon='k2', reactor='r2', computer='c2', sensor='s2',
            shield='sh0', shieldHardener='hard0', armor='a2', ecm='ecm0',
            eccm='eccm0', stl='stl2', ftl='ftl2', pds='epds2')
        epds3 = find(
            hull='h3', weapon='k3', reactor='r3', computer='c3', sensor='s3',
            shield='sh0', shieldHardener='hard0', armor='a3', ecm='ecm0',
            eccm='eccm0', stl='stl3', ftl='ftl2', pds='epds3')
        check(_pds(epds2)['power'] == 2 and _pds(epds3)['power'] == 1,
              'Energy PDS readiness must improve from TL2 2 TP to TL3 1 TP')

        k3x2 = find(weapon='k3x2', **{**common, 'computer':'c3', 'sensor':'s3', 'stl':'stl3'})
        check(_weapon(k3x2, data)['count'] == 2,
              'TL3 dual-main Kinetic fixture must expose two main-weapon firings')

        r3x2 = find(
            hull='h3', weapon='k2', reactor='r3x2', computer='c2', sensor='s2',
            shield='sh0', shieldHardener='hard0', armor='a2', ecm='ecm0',
            eccm='eccm0', stl='stl2', ftl='ftl2', pds='p0')
        check(_reactor_power(r3x2) == 12,
              f'TL3 dual-reactor fixture expected 12 TP, got {_reactor_power(r3x2)}')
    except LookupError as exc:
        errors.append(f'parity fixture missing: {exc}')

    if cases != PARITY_CASE_COUNT:
        errors.append(f'parity corpus executed {cases} cases; expected {PARITY_CASE_COUNT}')
    return errors
