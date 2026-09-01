from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from .canonical_mechanics import DEF_RES_DAMAGE_MODEL
from .ecology import CandidateMatrix

CURRENT_BASELINE_RELATIVE = "docs/design/player_technology/current_working_technology_baseline.json"
CURRENT_AUX_RELATIVE = "docs/design/player_technology/auxiliary_component_catalog.json"
CURRENT_SPACE_RELATIVE = "docs/design/player_technology/component_installation_space_catalog.json"
CURRENT_COMBAT_REFERENCE_RELATIVE = "docs/design/combat/Combat_System_Reference.md"

# CP165 CR3 native-accepted current-authority bytes. CP166 is diagnostic only;
# drift in these files must create a new checkpoint rather than silently alter
# the population being studied.
EXPECTED_SHA256 = {
    CURRENT_BASELINE_RELATIVE: "e937ce7f48fb86da3b42a9492e7ad7cc18c456051cdfac1f4712f7e60b29eda8",
    CURRENT_AUX_RELATIVE: "431b512b5d054b20ead8efd05a11c05193461f22872840541355907e50289598",
    CURRENT_SPACE_RELATIVE: "2567a8dceca1a6584e631ec3a233bcc09306d3e47d0dabd5ce1e582be09aff87",
    CURRENT_COMBAT_REFERENCE_RELATIVE: "10bcafbce2c14a0a72d861013c06b257f43d83f9109c5d06be73fc7348286c0b",
}

_AUX_KIND = {
    "shield_battery": "shield_battery",
    "shield_booster": "shield_booster",
    "shield_hardener": "shield_hardener",
    "ablative_armor": "ablative_armor",
    "energized_armor": "energized_armor",
    "crystalline_armor": "crystalline_armor",
    "field_stabilizer": "field_stabilizer",
    "repair_drone_bay": "repair_drone",
    "kinetic_magazine": "kinetic_magazine",
    "missile_magazine": "missile_magazine",
}

_TRANSLATE = {
    "restore": "restore",
    "charges": "charges",
    "capacityBonus": "capacity_bonus",
    "defBonusPp": "def_bonus_pp",
    "ablativeIntegrity": "ablative_integrity",
    "resBonusPp": "res_bonus_pp",
    "spenReduction": "spen_reduction",
    "additionalPreparedRepairKits": "extra_repair_kits",
    "droneAttemptTp": "drone_attempt_tp",
    "additionalActionsPerPhase": "additional_actions_per_phase",
    "differentTargetRequired": "different_target_required",
    "sameTargetRerollAllowed": "same_target_reroll_allowed",
    "ammoBonus": "ammo_bonus",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def authority_identity(repo: Path) -> dict[str, Any]:
    repo = Path(repo)
    rows = []
    for rel, expected in EXPECTED_SHA256.items():
        path = repo / rel
        actual = _sha(path) if path.is_file() else "MISSING"
        rows.append({"path": rel, "expectedSha256": expected, "actualSha256": actual, "matches": actual == expected})
    return {
        "baselineId": "CP165-CURRENT-WORKING",
        "checkpoint": 165,
        "status": "NATIVE_ACCEPTED_CURRENT_WORKING_DESIGN_PRE_WHOLE_SYSTEM_PROMOTION",
        "files": rows,
        "passed": all(r["matches"] for r in rows),
    }


def _current_aux_registry(aux_doc: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[tuple[str, int], str]]:
    registry: dict[str, dict[str, Any]] = {}
    ids: dict[tuple[str, int], str] = {}
    for component in aux_doc.get("components", []):
        cid = str(component.get("id", ""))
        if cid == "apu" or cid not in _AUX_KIND:
            continue
        first = int(component.get("firstTl", 99))
        for tl_s, spec in component.get("byTl", {}).items():
            tl = int(tl_s)
            if tl < first:
                continue
            aid = f"CW-{cid}-TL{tl}"
            row: dict[str, Any] = {
                "candidate_id": aid,
                "family": cid,
                "kind": _AUX_KIND[cid],
                "tl": tl,
                "space": int(component.get("space", 0)),
                "tp": int(spec.get("tp", spec.get("droneAttemptTp", 0)) or 0),
                "source_checkpoint": int(component.get("sourceCheckpoint", 164 if cid == "apu" else 0) or 0),
            }
            for src, dst in _TRANSLATE.items():
                if src in spec:
                    row[dst] = spec[src]
            if cid == "shield_battery":
                row["trigger_fraction"] = 0.5
            registry[aid] = row
            ids[(cid, tl)] = aid
    return registry, ids


def load_current_working_matrix(repo: Path, *, verify_hashes: bool = True) -> CandidateMatrix:
    """Load CP165's current-working design into the validated full-map kernel.

    CandidateMatrix historically expects a production-compatibility document
    containing a ``branches`` list and legacy Armor ``ap`` field.  CP165's
    current-working authority intentionally removed those obsolete fields.
    This adapter adds only in-memory compatibility shims that are ignored by
    DEF/RES damage resolution; no current authority file is modified.
    """
    repo = Path(repo)
    identity = authority_identity(repo)
    if verify_hashes and not identity["passed"]:
        bad = [r["path"] for r in identity["files"] if not r["matches"]]
        raise ValueError("CP165 current-working authority hash drift: " + ", ".join(bad))

    baseline = copy.deepcopy(_load(repo / CURRENT_BASELINE_RELATIVE))
    aux_doc = _load(repo / CURRENT_AUX_RELATIVE)

    # Instantiate without CandidateMatrix.__init__ because the current-working
    # file intentionally has no historical branches array.
    matrix = object.__new__(CandidateMatrix)
    matrix.path = repo / CURRENT_BASELINE_RELATIVE
    matrix.doc = baseline
    matrix.profiles = baseline["profiles"]
    matrix.branches = {"shield-hardener": {"id": "shield-hardener", "space": 1}}

    # Legacy SideState construction still owns an unused Armor-Protection slot.
    # DEF/RES never consults it, so zero is the neutral compatibility value.
    for tl in range(1, 10):
        matrix.p("armor", tl).setdefault("ap", 0)
        matrix.p("shield", tl).setdefault("shieldArmor", 0)

    rules = baseline["combatRules"]
    matrix.doc["combatModifiers"] = {
        "directFireApproximateTrackPenaltyPp": int(rules["directFireApproximateTrackPenaltyPp"]),
        "directFireExtendedRangePenaltyPp": int(rules["directFireExtendedRangePenaltyPp"]),
    }
    matrix.damage_model = DEF_RES_DAMAGE_MODEL
    matrix.def_res_shield_def_pp = {int(k): float(v) for k, v in baseline["damageModel"]["shieldDefByTlPp"].items()}
    matrix.def_res_armor_res_pp = {int(k): float(v) for k, v in baseline["damageModel"]["armorResByTlPp"].items()}
    matrix.def_res_hardener_bonus_pp = 0.0  # current hardener bonus comes from its TL-specific AUX row.
    matrix.reconciliation_profile = "cp166-current-working-whole-system"
    registry, ids = _current_aux_registry(aux_doc)
    matrix.cp158_aux_profiles = registry
    matrix.current_aux_ids = ids
    matrix.current_aux_catalog = aux_doc
    matrix.current_space_catalog = _load(repo / CURRENT_SPACE_RELATIVE)
    matrix.current_authority_identity = identity
    return matrix


def aux_id(matrix: CandidateMatrix, component_id: str, tl: int) -> str | None:
    return getattr(matrix, "current_aux_ids", {}).get((component_id, int(tl)))


def aux_row(matrix: CandidateMatrix, component_id: str, tl: int) -> dict[str, Any] | None:
    aid = aux_id(matrix, component_id, tl)
    if aid is None:
        return None
    return dict(getattr(matrix, "cp158_aux_profiles", {}).get(aid, {}))


def apu_profile(matrix: CandidateMatrix, tl: int) -> dict[str, Any]:
    comp = next(x for x in matrix.current_aux_catalog["components"] if x["id"] == "apu")
    return {
        "space": int(comp["space"]),
        "operationalTp": int(comp["byTl"][str(int(tl))]["operationalTp"]),
        "countCap": None,
    }


def execution_coverage() -> list[dict[str, Any]]:
    """Truthful CP166 execution boundary; no invented mechanics."""
    return [
        {"system": "same-TL current numerical profiles", "status": "EXECUTABLE", "notes": "CP165 current-working authority is loaded directly and hash-locked."},
        {"system": "DEF/RES, Shield/Armor, direct fire, Missile/Swarmer", "status": "EXECUTABLE", "notes": "Canonical full-map kernel with current TL values."},
        {"system": "movement/range/fuel and adaptive engagement", "status": "EXECUTABLE", "notes": "Radius-5 finite map and CP147 tactical utility doctrine."},
        {"system": "Sensors/ECM/ECCM", "status": "EXECUTABLE", "notes": "One effective installation of each; redundant copies are not outcome-distinct while component damage is absent."},
        {"system": "Kinetic/Energy/AMM PDS", "status": "EXECUTABLE_SINGLE_INSTALLATION", "notes": "One PDS family per executable build in CP166 Stage A."},
        {"system": "Main Reactor Operational TP", "status": "EXECUTABLE", "notes": "Current 5-13 TP ladder; multiple same-TL Main Reactors add output."},
        {"system": "APU Operational TP", "status": "EXECUTABLE", "notes": "2 Space, +1 TP TL1-4 / +2 TP TL5-9, additive with unrestricted count subject to Space."},
        {"system": "Shield Battery/Booster/Hardener, Ablative/Energized/Crystalline Armor, Field Stabilizer, magazines", "status": "EXECUTABLE", "notes": "Current selected AUX execution centers are carried into the full-map kernel."},
        {"system": "Hull Damage Control", "status": "EXECUTABLE", "notes": "Current crew Hull repair and Repair Kit consumption."},
        {"system": "Main Reactor Degraded/Emergency transitions", "status": "DEFERRED_SAME_TL_INTEGRATION", "notes": "Values are authoritative; combat component-state transitions are not yet represented."},
        {"system": "APU damaged/distributed resilience", "status": "DEFERRED_SAME_TL_INTEGRATION", "notes": "Operational stacking executes; independent component damage does not."},
        {"system": "Repair Drone distinct-target component action", "status": "DEFERRED_SAME_TL_INTEGRATION", "notes": "Additional prepared kits execute; component repair targets do not yet exist in the kernel, so no same-Hull reroll is invented."},
        {"system": "mixed-family multiple Main Weapons", "status": "DEFERRED_SAME_TL_INTEGRATION", "notes": "CP166 executable census supports homogeneous multi-Main packages only; mixed K/E/M packages require multi-weapon action planning."},
        {"system": "multiple simultaneous PDS installations/families", "status": "DEFERRED_SAME_TL_INTEGRATION", "notes": "Reaction-capacity sharing/stacking semantics require explicit integration before execution."},
        {"system": "redundant ECM/ECCM/PDS copies", "status": "DEFERRED_COMPONENT_RESILIENCE", "notes": "Legal redundancy has no intact-state benefit and becomes outcome-distinct only when component damage is integrated."},
        {"system": "non-explicit repeated AUX stacking", "status": "NOT_INFERRED", "notes": "CP166 does not invent multiplicity semantics where the current catalog leaves multiplicity unresolved."},
    ]
