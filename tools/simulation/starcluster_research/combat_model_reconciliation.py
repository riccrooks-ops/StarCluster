from __future__ import annotations

import copy
import math
from pathlib import Path
from typing import Any

from .canonical_mechanics import DEF_RES_DAMAGE_MODEL
from .ecology import CandidateMatrix

DEF_RES_BY_TL = {1:20.0,2:22.0,3:24.0,4:26.0,5:28.0,6:30.0,7:32.0,8:34.0,9:36.0}

KINETIC = {
    1:(4,8,80), 2:(5,9,82), 3:(5,10,82), 4:(5,10,90), 5:(6,11,90),
    6:(6,12,95), 7:(7,13,95), 8:(7,14,95), 9:(8,14,95),
}
ENERGY = {
    1:(4,12,85), 2:(4,13,92), 3:(4,14,92), 4:(5,16,95), 5:(5,17,95),
    6:(6,18,95), 7:(6,19,95), 8:(7,20,95), 9:(7,22,95),
}
GP = {
    1:(6,70), 2:(7,70), 3:(8,75), 4:(9,75), 5:(10,80),
    6:(11,85), 7:(12,85), 8:(13,90), 9:(14,95),
}
PDS = {
    'Kinetic': {
        2:(22,1,50),3:(23,1,60),4:(26,1,60),5:(27,1,60),
        6:(27,2,30),7:(31,2,30),8:(33,2,30),9:(34,2,30),
    },
    'Energy': {
        2:(25,1,None),3:(26,1,None),4:(30,1,None),5:(31,1,None),
        6:(33,1,None),7:(37,1,None),8:(39,1,None),9:(40,1,None),
    },
    'AMM': {
        2:(28,1,25),3:(22,2,25),4:(26,2,25),5:(27,2,25),
        6:(28,2,25),7:(28,2,30),8:(31,2,30),9:(32,2,30),
    },
}


def _accuracy_pp_for_absolute_hit(matrix: CandidateMatrix, tl: int, absolute_hit_pp: int) -> int:
    targeting = int(matrix.p('computer', tl).get('targetingPp', 0))
    return int(absolute_hit_pp) - 50 - targeting


def apply_combat_model_candidate(matrix: CandidateMatrix) -> CandidateMatrix:
    """Apply the CP139 reconciliation candidate in memory only.

    The underlying technology_numerical_matrix_v0_9.json is never written.
    """
    matrix.doc = copy.deepcopy(matrix.doc)
    matrix.profiles = matrix.doc['profiles']
    matrix.branches = {row['id']: row for row in matrix.doc['branches']}
    matrix.damage_model = DEF_RES_DAMAGE_MODEL
    matrix.def_res_shield_def_pp = dict(DEF_RES_BY_TL)
    matrix.def_res_armor_res_pp = dict(DEF_RES_BY_TL)
    matrix.def_res_hardener_bonus_pp = 10.0
    matrix.reconciliation_profile = 'cp139-combat-model-reconciliation-v0.1'

    for tl in range(1, 10):
        k_damage, k_apen, k_hit = KINETIC[tl]
        k = matrix.p('kinetic_main', tl)
        k['damage'] = k_damage
        k['spen'] = 0
        k['apen'] = k_apen
        k['accuracyPp'] = _accuracy_pp_for_absolute_hit(matrix, tl, k_hit)

        e_damage, e_spen, e_hit = ENERGY[tl]
        e = matrix.p('energy_main', tl)
        e['standardDamage'] = e_damage
        e['spen'] = e_spen
        e['apen'] = 0
        e['accuracyPp'] = _accuracy_pp_for_absolute_hit(matrix, tl, e_hit)
        e['lowDamage'] = math.ceil(e_damage / 2)
        e['overloadDamage'] = math.ceil(e_damage * 1.5)
        e['highDamage'] = e['overloadDamage']

        gp_damage, gp_guidance = GP[tl]
        gp = matrix.p('missile_gp_warhead', tl)
        gp['damage'] = gp_damage
        gp['spen'] = 0
        gp['apen'] = 0
        guidance = matrix.p('missile_guidance', tl)
        guidance['guidanceBaseHit'] = gp_guidance

        if tl >= 2:
            sw = matrix.p('missile_swarmer', tl)
            sw['available'] = True
            sw['packetCount'] = 1
            sw['subFlightCount'] = 2
            sw['packetDamage'] = gp_damage * 0.45
            sw['spen'] = 0
            sw['apen'] = 0
            sw['terminalGuidanceBonusPp'] = 0
            sw['pdsInterceptPenaltyPp'] = 0
            sw['oneFlightCounter'] = True
            sw['oneTerminalAttackRoll'] = False
            sw['independentSubFlightGuidance'] = True
            sw['pdsVisibleSubFlights'] = 2
            sw['sharedPdsReactionCapacity'] = True

    fam_key = {'Kinetic':'kinetic_pds','Energy':'energy_pds','AMM':'amm_pds'}
    for family, by_tl in PDS.items():
        for tl, (chance, rc, ammo) in by_tl.items():
            row = matrix.p(fam_key[family], tl)
            row['baseChancePp'] = chance
            row['reactionCapacity'] = rc
            row['ammo'] = ammo
    return matrix


def candidate_matrix(repo: Path, matrix_relative_path: str) -> CandidateMatrix:
    matrix = CandidateMatrix(repo, matrix_relative_path)
    return apply_combat_model_candidate(matrix)


def reconciliation_profile() -> dict[str, Any]:
    return {
        'damageModel': DEF_RES_DAMAGE_MODEL,
        'shieldDefByTl': DEF_RES_BY_TL,
        'armorResByTl': DEF_RES_BY_TL,
        'hardenerBonusDefPp': 10,
        'kinetic': KINETIC,
        'energy': ENERGY,
        'gp': GP,
        'pds': PDS,
        'swarmer': {
            'magazineFlightsConsumed': 1,
            'subFlights': 2,
            'totalYieldFractionVsGp': 0.90,
            'independentGuidance': True,
            'pdsVisibleSubFlights': 2,
            'sharedPdsReactionCapacity': True,
            'bespokePdsPenaltyPp': 0,
        },
    }
