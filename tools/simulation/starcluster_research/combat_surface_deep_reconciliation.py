from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

from .combat_model_reconciliation import apply_combat_model_candidate
from .ecology import CandidateMatrix

# Latest full-combat reference carried through v17-v19. v20-v21 intentionally
# pivoted to resource architecture and retained earlier mechanics evidence.
TL = tuple(range(1, 10))
LAB_SOURCE = "Combat Model Lab v17-v19"
RESOURCE_SOURCE = "Combat Model Lab v20-v21 / v22C resource ensemble"
CP138_SOURCE = "CP138 technology_numerical_matrix_v0_9 / full-map mechanics"

HULL_POINTS = (12, 12, 13, 13, 14, 14, 15, 15, 16)
SHIELD_CAPACITY = (8, 9, 10, 11, 12, 13, 14, 15, 16)
SHIELD_BASE_RECHARGE = (0, 0, 0, 0, 0, 0, 0, 0, 0)
SHIELD_TACTICAL_PER_TP = (1, 1, 1, 1, 1, 1, 1, 1, 1)
SHIELD_TACTICAL_CAP_TP = (1, 1, 1, 1, 1, 1, 1, 2, 2)
ARMOR_AI = (6, 7, 8, 9, 10, 9, 10, 11, 12)
ARMOR_REGEN_PER_TP = (0, 0, 0, 0, 0, 1, 1, 1, 1)
ARMOR_REGEN_CAP_TP = (0, 0, 0, 0, 0, 1, 1, 2, 2)
ARMOR_REGEN_RESERVE = (0, 0, 0, 0, 0, 3, 4, 6, 8)
ABLATIVE_AI = (0, 1, 2, 3, 4, 5, 6, 7, 8)
COMPUTER_TARGET_PP = (10, 12, 12, 15, 15, 15, 18, 20, 20)
DAMAGE_CONTROL_KITS = (3, 3, 4, 4, 5, 5, 6, 6, 7)
DAMAGE_CONTROL_HULL_REPAIR_PP = (40, 40, 45, 45, 45, 45, 50, 50, 55)
DAMAGE_CONTROL_HULL_PER_SUCCESS = (1, 1, 1, 1, 1, 1, 2, 2, 3)
DAMAGE_CONTROL_CAPACITY = (1, 1, 1, 1, 1, 1, 1, 1, 1)
KINETIC_AMMO = (100,) * 9
MISSILE_FLIGHTS = (25,) * 9

# Lab PDS probabilities are EFFECTIVE per-attempt chances and already include
# contemporary Tactical Computer help. The canonical full-map kernel adds
# targetingPp at resolution, so these must be translated back to baseChancePp.
PDS_EFFECTIVE = {
    "Kinetic": {
        "chance": (20, 22, 23, 26, 27, 27, 31, 33, 34),
        "rc": (1, 1, 1, 1, 1, 2, 2, 2, 2),
        "ammo": (50, 50, 60, 60, 60, 30, 30, 30, 30),
    },
    "Energy": {
        "chance": (22, 25, 26, 30, 31, 33, 37, 39, 40),
        "rc": (1, 1, 1, 1, 1, 1, 1, 1, 1),
        "ammo": (None,) * 9,
    },
    "AMM": {
        "chance": (25, 28, 22, 26, 27, 28, 28, 31, 32),
        "rc": (1, 1, 2, 2, 2, 2, 2, 2, 2),
        "ammo": (25, 25, 25, 25, 25, 25, 30, 30, 30),
        "range": (0, 0, 0, 0, 0, 0, 1, 1, 1),
    },
}

AUX_RECONCILIATION = {
    "ShieldHardener": {
        "classification": "COMBINED",
        "execution": "EXECUTABLE",
        "lab_effect": "+10 Shield DEF pp while powered",
        "resource": "1 Space / 1 TP sustained mechanic anchor",
        "disposition": "retain executable candidate; nonstacking",
    },
    "AblativeArmorLayer": {
        "classification": "UNRESOLVED_CONFLICT_GAP",
        "execution": "NOT_STAGE_A_EXECUTABLE",
        "lab_effect": "separate sacrificial layer; Ablative AI ladder 0/1/2/3/4/5/6/7/8; no RES or repair",
        "resource": "v21 mechanic anchor, fixed 1 Space",
        "disposition": "record exact lab profile; do not invent full-map installation/state integration in CP142",
    },
    "PoweredReactiveArmorSystem": {
        "classification": "UNRESOLVED_CONFLICT_GAP",
        "execution": "NOT_PROMOTED",
        "lab_effect": "+10 RES pp was a response-curve mapping diagnostic",
        "resource": "v21 labels this a resource proxy, not an executable mechanic anchor",
        "disposition": "do not convert diagnostic bonus into production/research combat value",
    },
    "ShieldBooster": {
        "classification": "UNRESOLVED_CONFLICT_GAP",
        "execution": "RESOURCE_PROXY_ONLY",
        "lab_effect": "earlier illustrative +SC response studies",
        "resource": "v21 footprint/effect TBD resource proxy",
        "disposition": "no invented combat effect",
    },
    "FieldStabilizer": {
        "classification": "UNRESOLVED_CONFLICT_GAP",
        "execution": "RESOURCE_PROXY_ONLY",
        "lab_effect": "earlier recovery sensitivity only",
        "resource": "v21 powered shield-support resource proxy",
        "disposition": "no invented combat effect",
    },
    "AuxiliaryPowerAndBatteries": {
        "classification": "UNRESOLVED_CONFLICT_GAP",
        "execution": "RESOURCE_PROXY_ONLY",
        "lab_effect": "no final combat value",
        "resource": "v20-v21 explicit bounded/proxy envelopes",
        "disposition": "remain metadata/resource hypotheses; no free sustained TP",
    },
    "RepairAndEW_AUX": {
        "classification": "UNRESOLVED_CONFLICT_GAP",
        "execution": "RESOURCE_PROXY_ONLY",
        "lab_effect": "sensitivity/proxy only",
        "resource": "v20-v21 resource proxies",
        "disposition": "no invented combat effect",
    },
}


def _idx(tl: int) -> int:
    if tl < 1 or tl > 9:
        raise ValueError(tl)
    return tl - 1


def pds_base_chance_for_effective(matrix: CandidateMatrix, family: str, tl: int) -> int:
    target = int(PDS_EFFECTIVE[family]["chance"][_idx(tl)])
    targeting = int(matrix.p("computer", tl).get("targetingPp", 0))
    return max(0, target - targeting)


def apply_deep_combat_surface_reconciliation(matrix: CandidateMatrix) -> CandidateMatrix:
    """Apply CP142's deep combat-surface candidate in memory only.

    CP139's DEF/RES/offense/Swarmer foundation is applied first. This function
    then closes fields explicitly carried by the latest full-combat lab and
    corrects PDS chance semantics. CP138/full-map values remain wherever the lab
    did not supersede them. The source numerical matrix is never written.
    """
    apply_combat_model_candidate(matrix)
    # CP139 already deep-copies. Keep this guard for direct use on unusual matrices.
    matrix.doc = copy.deepcopy(matrix.doc)
    matrix.profiles = matrix.doc["profiles"]
    matrix.branches = {row["id"]: row for row in matrix.doc["branches"]}
    matrix.reconciliation_profile = "cp142-combat-surface-deep-reconciliation-v0.1"
    matrix.deep_reconciliation_aux = copy.deepcopy(AUX_RECONCILIATION)
    matrix.deep_reconciliation_source = LAB_SOURCE

    for tl in TL:
        i = _idx(tl)
        # Hull durability is a combat characteristic in the v17-v19 same-TL
        # reference. Installation Space/capacity remains the CP138/v22C resource axis.
        matrix.p("hull", tl)["hullPoints"] = int(HULL_POINTS[i])

        shield = matrix.p("shield", tl)
        shield["capacity"] = int(SHIELD_CAPACITY[i])
        shield["baseRecharge"] = int(SHIELD_BASE_RECHARGE[i])
        shield["tacticalRechargePerTp"] = int(SHIELD_TACTICAL_PER_TP[i])
        shield["tacticalRechargeCapTp"] = int(SHIELD_TACTICAL_CAP_TP[i])
        # shield space and obsolete shieldArmor are intentionally retained from
        # the resource/control matrix; DEF/RES ignores shieldArmor.

        armor = matrix.p("armor", tl)
        armor["ai"] = int(ARMOR_AI[i])
        armor["baseRegeneration"] = 0
        armor["tacticalRegenerationPerTp"] = int(ARMOR_REGEN_PER_TP[i])
        armor["tacticalRegenerationCapTp"] = int(ARMOR_REGEN_CAP_TP[i])
        armor["combatRegenerationReserveAi"] = int(ARMOR_REGEN_RESERVE[i])
        # legacy AP remains in the source profile for control compatibility but
        # is not consulted by def-res-v1 damage resolution.

        # Explicit continuity assertions: latest combat-lab reference agrees with
        # CP138 on these values, so no numerical rewrite is necessary.
        dc = matrix.p("damage_control", tl)
        assert int(dc.get("preparedRepairKits", -1)) == DAMAGE_CONTROL_KITS[i]
        assert int(dc.get("hullRepairChancePp", -1)) == DAMAGE_CONTROL_HULL_REPAIR_PP[i]
        assert int(dc.get("hullRestoredPerSuccessfulKit", -1)) == DAMAGE_CONTROL_HULL_PER_SUCCESS[i]
        assert int(dc.get("capacity", -1)) == DAMAGE_CONTROL_CAPACITY[i]
        assert int(matrix.p("computer", tl).get("targetingPp", -1)) == COMPUTER_TARGET_PP[i]
        assert int(matrix.p("kinetic_main", tl).get("ammo", -1)) == KINETIC_AMMO[i]
        assert int(matrix.p("missile_delivery", tl).get("flights", -1)) == MISSILE_FLIGHTS[i]

    fam_key = {"Kinetic": "kinetic_pds", "Energy": "energy_pds", "AMM": "amm_pds"}
    for family, data in PDS_EFFECTIVE.items():
        for tl in TL:
            i = _idx(tl)
            row = matrix.p(fam_key[family], tl)
            row["baseChancePp"] = pds_base_chance_for_effective(matrix, family, tl)
            row["reactionCapacity"] = int(data["rc"][i])
            row["ammo"] = data["ammo"][i]
            if family == "AMM":
                row["interceptRange"] = int(data["range"][i])
            # Space/readiness TP are deliberately NOT rewritten: v20 explicitly
            # retained CP138 resource inputs rather than inferring them from v19.
    return matrix


def build_deep_resource_matrix(repo: Path, matrix_relative: str, ensemble_id: str,
                               ensemble_rows: list[dict[str, str]], tl_rows: list[dict[str, str]]) -> CandidateMatrix:
    # Import lazily to avoid a module cycle. v22C remains the later resource
    # experiment authority; CP142 changes combat characteristics, not the six
    # resource-envelope definitions.
    from .stage_a_integration_analysis import build_resource_matrix
    matrix = build_resource_matrix(repo, matrix_relative, ensemble_id, ensemble_rows, tl_rows)
    return apply_deep_combat_surface_reconciliation(matrix)


def reconciliation_profile(matrix: CandidateMatrix | None = None) -> dict[str, Any]:
    effective = {f: list(v["chance"]) for f, v in PDS_EFFECTIVE.items()}
    return {
        "profile": "cp142-combat-surface-deep-reconciliation-v0.1",
        "fullCombatEvidence": LAB_SOURCE,
        "resourceEvidence": RESOURCE_SOURCE,
        "fallbackAuthority": CP138_SOURCE,
        "hullPoints": list(HULL_POINTS),
        "shield": {
            "capacity": list(SHIELD_CAPACITY),
            "baseRecharge": list(SHIELD_BASE_RECHARGE),
            "tacticalRechargePerTp": list(SHIELD_TACTICAL_PER_TP),
            "tacticalRechargeCapTp": list(SHIELD_TACTICAL_CAP_TP),
        },
        "armor": {
            "ai": list(ARMOR_AI),
            "baseRegeneration": [0] * 9,
            "tacticalRegenerationPerTp": list(ARMOR_REGEN_PER_TP),
            "tacticalRegenerationCapTp": list(ARMOR_REGEN_CAP_TP),
            "combatRegenerationReserveAi": list(ARMOR_REGEN_RESERVE),
        },
        "pdsEffectiveChancePp": effective,
        "pdsBaseChancePp": ({
            f: [pds_base_chance_for_effective(matrix, f, tl) for tl in TL] for f in PDS_EFFECTIVE
        } if matrix is not None else None),
        "aux": copy.deepcopy(AUX_RECONCILIATION),
        "unresolvedExperimental": [
            "AMM range-1 third opportunity: tested experimentally; not promoted by v19",
            "Ablative Armor full-map state/installation integration",
            "Powered Reactive Armor RES mapping: response diagnostic/resource proxy only",
            "Shield Booster/Field Stabilizer and other TBD AUX combat effects",
        ],
    }
