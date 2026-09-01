from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Callable, Iterable

from .canonical_combat import run_trial_full_map
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant
from .research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from .rng import XorShift64, derive_seed
from .study import load_json

SCHEMA = "star-cluster-cp161-reactor-tp-equilibrium-v0.1"
COMBAT_DOCTRINE = "cp147_tactical_utility"
WEAPONS = ("K", "E", "M", "SW")
PDS_FAMILIES = ("NONE", "K", "E", "AMM")
STATES = ("core", "routine", "offense", "defense", "recovery", "full")

DOCTRINES: dict[str, dict[str, float]] = {
    "OFFENSE": {
        "fire": .92, "energy_overload": .28, "sensor_high": .28, "sensor_low": .62,
        "ecm": .38, "eccm": .48, "pds": .12, "shield_recharge": .30, "armor_regen": .22,
        "hardener": .42, "energized": .38, "stabilizer": .30, "damage_control": .05,
        "drone": .70, "stl_overload": .10,
    },
    "EW_CONTEST": {
        "fire": .76, "energy_overload": .20, "sensor_high": .68, "sensor_low": .29,
        "ecm": .90, "eccm": .92, "pds": .18, "shield_recharge": .38, "armor_regen": .28,
        "hardener": .52, "energized": .48, "stabilizer": .48, "damage_control": .08,
        "drone": .72, "stl_overload": .06,
    },
    "MISSILE_DEFENSE": {
        "fire": .58, "energy_overload": .12, "sensor_high": .50, "sensor_low": .45,
        "ecm": .42, "eccm": .72, "pds": .92, "shield_recharge": .76, "armor_regen": .62,
        "hardener": .80, "energized": .78, "stabilizer": .68, "damage_control": .15,
        "drone": .80, "stl_overload": .05,
    },
    "DAMAGE_CRISIS": {
        "fire": .44, "energy_overload": .08, "sensor_high": .24, "sensor_low": .66,
        "ecm": .40, "eccm": .52, "pds": .55, "shield_recharge": .94, "armor_regen": .92,
        "hardener": .90, "energized": .92, "stabilizer": .76, "damage_control": .88,
        "drone": .84, "stl_overload": .04,
    },
    "PURSUIT_BURST": {
        "fire": .84, "energy_overload": .40, "sensor_high": .52, "sensor_low": .42,
        "ecm": .52, "eccm": .58, "pds": .16, "shield_recharge": .30, "armor_regen": .20,
        "hardener": .36, "energized": .34, "stabilizer": .30, "damage_control": .05,
        "drone": .68, "stl_overload": .48,
    },
    "MIXED": {
        "fire": .72, "energy_overload": .22, "sensor_high": .38, "sensor_low": .54,
        "ecm": .56, "eccm": .62, "pds": .44, "shield_recharge": .58, "armor_regen": .48,
        "hardener": .62, "energized": .60, "stabilizer": .48, "damage_control": .12,
        "drone": .76, "stl_overload": .12,
    },
}

PRIORITY: dict[str, tuple[str, ...]] = {
    "OFFENSE": ("sensor", "weapon", "eccm", "ecm", "pds", "shield_hardener", "field_stabilizer", "energized_armor", "shield_recharge", "armor_regen", "damage_control", "repair_drone", "stl_overload"),
    "EW_CONTEST": ("sensor", "eccm", "weapon", "ecm", "pds", "shield_hardener", "field_stabilizer", "energized_armor", "shield_recharge", "armor_regen", "damage_control", "repair_drone", "stl_overload"),
    "MISSILE_DEFENSE": ("sensor", "pds", "weapon", "shield_hardener", "field_stabilizer", "energized_armor", "shield_recharge", "armor_regen", "eccm", "ecm", "damage_control", "repair_drone", "stl_overload"),
    "DAMAGE_CRISIS": ("sensor", "damage_control", "repair_drone", "shield_recharge", "armor_regen", "pds", "weapon", "shield_hardener", "energized_armor", "field_stabilizer", "eccm", "ecm", "stl_overload"),
    "PURSUIT_BURST": ("sensor", "weapon", "stl_overload", "eccm", "ecm", "pds", "shield_hardener", "field_stabilizer", "energized_armor", "shield_recharge", "armor_regen", "damage_control", "repair_drone"),
    "MIXED": ("sensor", "weapon", "pds", "eccm", "shield_hardener", "field_stabilizer", "energized_armor", "ecm", "shield_recharge", "armor_regen", "damage_control", "repair_drone", "stl_overload"),
}


@dataclass(frozen=True, slots=True)
class PowerLoadout:
    id: str
    tl: int
    weapon: str
    main_count: int
    reactor_count: int
    shield: bool
    ecm: bool
    eccm: bool
    pds: str
    crystalline: bool
    hardener: bool
    energized: bool
    stabilizer: bool
    drone: bool
    capacity: int
    used_space: int
    free_space: int

    @property
    def powered_aux_count(self) -> int:
        return int(self.hardener) + int(self.energized) + int(self.stabilizer) + int(self.drone)


@dataclass(frozen=True, slots=True)
class Request:
    group: str
    cost: int
    full_cost: int | None = None
    fallback_cost: int | None = None


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 161:
        errors.append("checkpoint")
    if int(doc.get("acceptedBaselineCheckpoint", 0)) != 160 or doc.get("pendingFinalizationBaselineId") != "CP160-PF4":
        errors.append("baseline")
    sweep = doc.get("operationalSupplySweep", {})
    if int(sweep.get("minimumTp", 0)) != 2 or int(sweep.get("maximumTp", 0)) != 30:
        errors.append("operationalSupplySweep")
    if doc.get("reactorSpaceSweep") != [4, 5, 6, 7, 8]:
        errors.append("reactorSpaceSweep")
    if doc.get("combatSupplyOffsetsFromPf4") != [-4, -2, 0, 2, 4, 6, 8]:
        errors.append("combatSupplyOffsetsFromPf4")
    if int(doc.get("combatTrialsPerCell", 0)) != 2000 or int(doc.get("combatContextsPerTl", 0)) != 36:
        errors.append("combatScale")
    if int(doc.get("stochasticTurnSamplesPerVariant", 0)) != 12000 or int(doc.get("representativeLoadoutsPerTl", 0)) != 12:
        errors.append("stochasticScale")
    if doc.get("doctrines") != list(DOCTRINES):
        errors.append("doctrines")
    p = doc.get("interpretationPolicy", {})
    required_false = ("automaticPromotion", "productionAuthorityChanged", "conceptChanged", "tuningAllowed")
    if any(p.get(k) is not False for k in required_false):
        errors.append("promotionBoundary")
    if not all(p.get(k) is True for k in ("noTargetWinRate", "noRequiredFullSimultaneousDemandCoverage", "noUniversalUtilizationTarget", "balanceMeansDistinctViableChoices", "currentReactorLadderIsScaffoldNotAnswer", "auxMagnitudeArchitectureRemainClosedUnlessIntegrationInvalidates")):
        errors.append("interpretationPolicy")
    return errors


def _aux(matrix: CandidateMatrix, key: str, tl: int) -> dict[str, Any] | None:
    row = matrix.doc.get("pendingFinalizationAuxProfiles", {}).get(key)
    if not row or tl < int(row.get("firstTl", 99)):
        return None
    spec = row.get("byTl", {}).get(str(tl))
    if spec is None:
        return None
    return {**row, **spec}


def _weapon_row(matrix: CandidateMatrix, weapon: str, tl: int) -> dict[str, Any]:
    if weapon == "K":
        p = matrix.p("kinetic_main", tl)
        return {"space": int(p["space"]), "standard": int(p["firingTp"]), "peak": int(p["firingTp"]), "low": int(p["firingTp"])}
    if weapon == "E":
        p = matrix.p("energy_main", tl)
        return {"space": int(p["space"]), "standard": int(p["standardTp"]), "peak": int(p["overloadTp"]), "low": int(p["lowTp"])}
    if weapon in ("M", "SW"):
        p = matrix.p("missile_delivery", tl)
        return {"space": int(p["space"]), "standard": int(p["launchTp"]), "peak": int(p["launchTp"]), "low": int(p["launchTp"])}
    raise ValueError(weapon)


def _pds_row(matrix: CandidateMatrix, family: str, tl: int) -> dict[str, Any] | None:
    if family == "NONE":
        return None
    key = {"K": "kinetic_pds", "E": "energy_pds", "AMM": "amm_pds"}[family]
    return matrix.p(key, tl)


def _core_space(matrix: CandidateMatrix, tl: int, weapon: str, main_count: int, reactor_count: int, reactor_space: int) -> int:
    return (
        int(matrix.p("stl", tl)["space"]) + int(matrix.p("ftl", tl)["space"]) +
        int(matrix.p("computer", tl)["space"]) + int(matrix.p("sensor", tl)["space"]) +
        int(_weapon_row(matrix, weapon, tl)["space"]) * main_count + reactor_space * reactor_count
    )


def enumerate_loadouts(matrix: CandidateMatrix, *, reactor_space: int = 6) -> list[PowerLoadout]:
    rows: list[PowerLoadout] = []
    for tl in range(1, 10):
        capacity = int(matrix.p("hull", tl)["capacity"])
        weapons = ("K", "E", "M") + (("SW",) if bool(matrix.p("missile_swarmer", tl).get("available", False)) else ())
        crystal_available = _aux(matrix, "crystallineArmor", tl) is not None
        hardener_available = _aux(matrix, "shieldHardener", tl) is not None
        energized_available = _aux(matrix, "energizedArmor", tl) is not None
        stabilizer_available = _aux(matrix, "fieldStabilizer", tl) is not None
        drone_available = _aux(matrix, "repairDroneBay", tl) is not None
        for weapon in weapons:
            for main_count in (1, 2):
                for reactor_count in (1, 2):
                    base = _core_space(matrix, tl, weapon, main_count, reactor_count, reactor_space)
                    if base > capacity:
                        continue
                    for shield in (False, True):
                        s0 = base + (int(matrix.p("shield", tl)["space"]) if shield else 0)
                        if s0 > capacity:
                            continue
                        for ecm in (False, True):
                            s1 = s0 + (int(matrix.p("ecm", tl)["space"]) if ecm else 0)
                            if s1 > capacity:
                                continue
                            for eccm in (False, True):
                                s2 = s1 + (int(matrix.p("eccm", tl)["space"]) if eccm else 0)
                                if s2 > capacity:
                                    continue
                                for pds in PDS_FAMILIES:
                                    pr = _pds_row(matrix, pds, tl)
                                    s3 = s2 + (int(pr["space"]) if pr else 0)
                                    if s3 > capacity:
                                        continue
                                    for crystalline in ((False, True) if crystal_available else (False,)):
                                        for hardener in ((False, True) if hardener_available and shield else (False,)):
                                            hs = int(_aux(matrix, "shieldHardener", tl)["space"]) if hardener else 0
                                            for energized in ((False, True) if energized_available else (False,)):
                                                es = int(_aux(matrix, "energizedArmor", tl)["space"]) if energized else 0
                                                for stabilizer in ((False, True) if stabilizer_available and shield else (False,)):
                                                    fs = int(_aux(matrix, "fieldStabilizer", tl)["space"]) if stabilizer else 0
                                                    for drone in ((False, True) if drone_available else (False,)):
                                                        ds = int(_aux(matrix, "repairDroneBay", tl)["space"]) if drone else 0
                                                        used = s3 + hs + es + fs + ds
                                                        if used > capacity:
                                                            continue
                                                        lid = (
                                                            f"tl{tl}-{weapon}-m{main_count}r{reactor_count}-s{int(shield)}-"
                                                            f"ew{int(ecm)}{int(eccm)}-p{pds}-c{int(crystalline)}-"
                                                            f"h{int(hardener)}e{int(energized)}f{int(stabilizer)}d{int(drone)}"
                                                        )
                                                        rows.append(PowerLoadout(
                                                            lid, tl, weapon, main_count, reactor_count, shield, ecm, eccm, pds,
                                                            crystalline, hardener, energized, stabilizer, drone, capacity, used, capacity - used
                                                        ))
    rows.sort(key=lambda x: x.id)
    return rows


def _costs(matrix: CandidateMatrix, l: PowerLoadout, overrides: dict[str, int] | None = None) -> dict[str, int]:
    overrides = overrides or {}
    tl = l.tl
    w = _weapon_row(matrix, l.weapon, tl)
    sensor = matrix.p("sensor", tl)
    high = sensor.get("activeHighTp")
    high = int(sensor.get("activeLowTp", 0) or 0) if high is None else int(high)
    pds = _pds_row(matrix, l.pds, tl)
    armor = matrix.p("armor", tl)
    dc = matrix.p("damage_control", tl)
    base = {
        "weapon_standard": int(w["standard"]), "weapon_peak": int(w["peak"]), "weapon_low": int(w["low"]),
        "sensor_low": int(sensor.get("activeLowTp", 0) or 0), "sensor_high": high,
        "ecm": int(matrix.p("ecm", tl)["fullStrengthTp"]) if l.ecm else 0,
        "eccm": int(matrix.p("eccm", tl)["fullStrengthTp"]) if l.eccm else 0,
        "pds": int(pds["readinessTp"]) if pds else 0,
        "shield_recharge": int(matrix.p("shield", tl).get("tacticalRechargeCapTp", 0)) if l.shield else 0,
        "armor_regen": 0 if l.crystalline else int(armor.get("tacticalRegenerationCapTp", 0)),
        "hardener": int(_aux(matrix, "shieldHardener", tl).get("tp", 0)) if l.hardener else 0,
        "energized": int(_aux(matrix, "energizedArmor", tl).get("tp", 0)) if l.energized else 0,
        "stabilizer": int(_aux(matrix, "fieldStabilizer", tl).get("tp", 0)) if l.stabilizer else 0,
        "damage_control": int(dc.get("attemptTp", 1)),
        "drone": int(_aux(matrix, "repairDroneBay", tl).get("droneAttemptTp", dc.get("attemptTp", 1))) if l.drone else 0,
        "stl_overload": int(matrix.p("stl", tl).get("overloadTp", 0)),
    }
    base.update({k: max(0, int(v)) for k, v in overrides.items()})
    return base


def demand_states(matrix: CandidateMatrix, l: PowerLoadout, overrides: dict[str, int] | None = None) -> dict[str, int]:
    c = _costs(matrix, l, overrides)
    weapon_standard = c["weapon_standard"] * l.main_count
    weapon_peak = c["weapon_peak"] * l.main_count
    common_defense = c["hardener"] + c["energized"] + c["stabilizer"]
    core = weapon_standard + c["sensor_low"]
    routine = core + c["ecm"] + c["eccm"]
    offense = weapon_peak + c["sensor_high"] + c["ecm"] + c["eccm"]
    defense = c["sensor_high"] + c["ecm"] + c["eccm"] + c["pds"] + c["shield_recharge"] + c["armor_regen"] + common_defense
    recovery = c["sensor_low"] + c["shield_recharge"] + c["armor_regen"] + common_defense + c["damage_control"] + c["drone"]
    full = weapon_peak + c["sensor_high"] + c["ecm"] + c["eccm"] + c["pds"] + c["shield_recharge"] + c["armor_regen"] + common_defense + c["damage_control"] + c["drone"] + c["stl_overload"]
    return {"core": core, "routine": routine, "offense": offense, "defense": defense, "recovery": recovery, "full": full}


def _q(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    pos = (len(vals) - 1) * p
    lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    if lo == hi:
        return float(vals[lo])
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def static_analysis(repo: Path, study_path: Path, out: Path) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("CP161 study invalid: " + ", ".join(errs))
    m = load_research_execution_baseline_pf4(repo)
    rows = enumerate_loadouts(m, reactor_space=6)
    loadout_rows: list[dict[str, Any]] = []
    state_cache: dict[str, dict[str, int]] = {}
    for l in rows:
        st = demand_states(m, l); state_cache[l.id] = st
        loadout_rows.append({
            **{k: getattr(l, k) for k in ("id", "tl", "weapon", "main_count", "reactor_count", "shield", "ecm", "eccm", "pds", "crystalline", "hardener", "energized", "stabilizer", "drone", "capacity", "used_space", "free_space")},
            "powered_aux_count": l.powered_aux_count, **{f"demand_{k}": v for k, v in st.items()},
        })
    _write_csv(out / "architecture_loadouts.csv", loadout_rows)

    pop_groups: dict[tuple[Any, ...], list[PowerLoadout]] = defaultdict(list)
    for l in rows:
        pop_groups[(l.tl, l.weapon, l.main_count, l.reactor_count, l.pds, l.powered_aux_count, l.crystalline)].append(l)
    pop_rows = []
    for key, items in sorted(pop_groups.items()):
        pop_rows.append({
            "tl": key[0], "weapon": key[1], "main_count": key[2], "reactor_count": key[3], "pds": key[4],
            "powered_aux_count": key[5], "crystalline": key[6], "loadouts": len(items),
            "mean_used_space": statistics.fmean(x.used_space for x in items), "mean_free_space": statistics.fmean(x.free_space for x in items),
        })
    _write_csv(out / "architecture_population.csv", pop_rows)

    smin = int(doc["operationalSupplySweep"]["minimumTp"]); smax = int(doc["operationalSupplySweep"]["maximumTp"])
    support_rows: list[dict[str, Any]] = []
    for tl in range(1, 10):
        for rc in (1, 2):
            sub = [l for l in rows if l.tl == tl and l.reactor_count == rc]
            for state in STATES:
                vals = [state_cache[l.id][state] for l in sub]
                for supply_per in range(smin, smax + 1):
                    total = supply_per * rc
                    support_rows.append({
                        "tl": tl, "reactor_count": rc, "state": state, "supply_per_reactor": supply_per, "total_supply": total,
                        "loadouts": len(vals), "supported_fraction": sum(v <= total for v in vals) / len(vals) if vals else 0.0,
                        "mean_demand": statistics.fmean(vals) if vals else 0.0, "p10_demand": _q(vals, .10), "p50_demand": _q(vals, .50),
                        "p90_demand": _q(vals, .90), "p95_demand": _q(vals, .95), "mean_margin": statistics.fmean(total - v for v in vals) if vals else 0.0,
                    })
    _write_csv(out / "static_supply_response.csv", support_rows)

    current_rows = []
    for tl in range(1, 10):
        r = m.p("reactor", tl)
        one = [l for l in rows if l.tl == tl and l.reactor_count == 1]
        for state in STATES:
            vals = [state_cache[l.id][state] for l in one]
            for name, supply in (("operational", int(r["operationalTp"])), ("degraded", int(r["degradedTp"])), ("emergency", int(r["emergencyTp"]))):
                current_rows.append({
                    "tl": tl, "reactor_state": name, "supply": supply, "demand_state": state, "loadouts": len(vals),
                    "supported_fraction": sum(v <= supply for v in vals) / len(vals) if vals else 0.0,
                    "mean_shortfall_tp": statistics.fmean(max(0, v - supply) for v in vals) if vals else 0.0,
                    "p50_demand": _q(vals, .5), "p90_demand": _q(vals, .9), "p95_demand": _q(vals, .95),
                })
    _write_csv(out / "current_reactor_state_support.csv", current_rows)

    space_rows = []
    for rs in doc["reactorSpaceSweep"]:
        ss = enumerate_loadouts(m, reactor_space=int(rs))
        for tl in range(1, 10):
            one = [x for x in ss if x.tl == tl and x.reactor_count == 1]
            two = [x for x in ss if x.tl == tl and x.reactor_count == 2]
            can_add = [x for x in one if x.used_space + int(rs) <= x.capacity]
            space_rows.append({
                "tl": tl, "reactor_space": rs, "one_reactor_loadouts": len(one), "two_reactor_loadouts": len(two),
                "one_reactor_mean_free_space": statistics.fmean(x.free_space for x in one) if one else 0.0,
                "one_reactor_p50_free_space": _q([x.free_space for x in one], .5),
                "one_architectures_that_can_add_second": len(can_add),
                "fraction_one_architectures_that_can_add_second": len(can_add) / len(one) if one else 0.0,
                "fraction_add_second_and_retain_2_aux_slots": sum((x.free_space - int(rs)) >= 2 for x in can_add) / len(one) if one else 0.0,
                "fraction_add_second_and_retain_4_aux_slots": sum((x.free_space - int(rs)) >= 4 for x in can_add) / len(one) if one else 0.0,
                "second_reactor_aux_slot_opportunity_cost": int(rs),
            })
    _write_csv(out / "reactor_space_sensitivity.csv", space_rows)

    cost_rows = _cost_sensitivity(m, rows)
    _write_csv(out / "tp_cost_one_factor_sensitivity.csv", cost_rows)

    reps = representative_loadouts(m, [l for l in rows if l.reactor_count == 1], int(doc["representativeLoadoutsPerTl"]))
    rep_rows = []
    for tag, l in reps:
        rep_rows.append({"representative": tag, **{k: getattr(l, k) for k in ("id", "tl", "weapon", "main_count", "shield", "ecm", "eccm", "pds", "crystalline", "hardener", "energized", "stabilizer", "drone", "capacity", "used_space", "free_space")}, **{f"demand_{k}": v for k, v in state_cache[l.id].items()}})
    _write_csv(out / "representative_loadouts.csv", rep_rows)

    summary = {
        "mode": "static", "passed": True, "baselineId": "CP160-PF4", "reactorSpace": 6,
        "legalPoweredArchitectures": len(rows), "oneReactorArchitectures": sum(x.reactor_count == 1 for x in rows),
        "twoReactorArchitectures": sum(x.reactor_count == 2 for x in rows), "staticSupplyRows": len(support_rows),
        "reactorSpaceRows": len(space_rows), "costSensitivityRows": len(cost_rows), "representativeLoadouts": len(reps),
        "automaticPromotion": False, "tuningAllowed": False,
    }
    _write_json(out / "summary.json", summary)
    return summary


def _lever_overrides(matrix: CandidateMatrix, l: PowerLoadout, lever: str, delta: int) -> dict[str, int]:
    c = _costs(matrix, l)
    out: dict[str, int] = {}
    def adj(key: str) -> None:
        out[key] = max(0, int(c[key]) + delta)
    if lever == "kinetic_weapon" and l.weapon == "K":
        adj("weapon_standard"); adj("weapon_peak"); adj("weapon_low")
    elif lever == "energy_standard" and l.weapon == "E":
        adj("weapon_standard")
    elif lever == "energy_overload" and l.weapon == "E":
        adj("weapon_peak")
    elif lever == "missile_weapon" and l.weapon in ("M", "SW"):
        adj("weapon_standard"); adj("weapon_peak"); adj("weapon_low")
    elif lever == "sensor_active":
        adj("sensor_low"); adj("sensor_high")
    elif lever == "ecm" and l.ecm:
        adj("ecm")
    elif lever == "eccm" and l.eccm:
        adj("eccm")
    elif lever == "pds_readiness" and l.pds != "NONE":
        adj("pds")
    elif lever == "shield_recharge_cap" and l.shield:
        adj("shield_recharge")
    elif lever == "armor_regeneration_cap" and not l.crystalline:
        adj("armor_regen")
    elif lever == "shield_hardener" and l.hardener:
        adj("hardener")
    elif lever == "energized_armor" and l.energized:
        adj("energized")
    elif lever == "field_stabilizer" and l.stabilizer:
        adj("stabilizer")
    elif lever == "damage_control":
        adj("damage_control")
        if l.drone:
            adj("drone")
    return out


def _cost_sensitivity(matrix: CandidateMatrix, rows: list[PowerLoadout]) -> list[dict[str, Any]]:
    levers = ("kinetic_weapon", "energy_standard", "energy_overload", "missile_weapon", "sensor_active", "ecm", "eccm", "pds_readiness", "shield_recharge_cap", "armor_regeneration_cap", "shield_hardener", "energized_armor", "field_stabilizer", "damage_control")
    out = []
    for tl in range(1, 10):
        supply = int(matrix.p("reactor", tl)["operationalTp"])
        one = [l for l in rows if l.tl == tl and l.reactor_count == 1]
        base_states = {l.id: demand_states(matrix, l) for l in one}
        for lever in levers:
            for delta in (-1, 1):
                for state in STATES:
                    relevant = []
                    for l in one:
                        ov = _lever_overrides(matrix, l, lever, delta)
                        if not ov:
                            continue
                        relevant.append(demand_states(matrix, l, ov)[state])
                    if not relevant:
                        continue
                    baseline_relevant = [base_states[l.id][state] for l in one if _lever_overrides(matrix, l, lever, delta)]
                    out.append({
                        "tl": tl, "lever": lever, "delta": delta, "demand_state": state, "reactor_supply": supply,
                        "relevant_loadouts": len(relevant),
                        "baseline_supported_fraction": sum(v <= supply for v in baseline_relevant) / len(baseline_relevant),
                        "perturbed_supported_fraction": sum(v <= supply for v in relevant) / len(relevant),
                        "supported_fraction_delta": (sum(v <= supply for v in relevant) - sum(v <= supply for v in baseline_relevant)) / len(relevant),
                        "baseline_mean_demand": statistics.fmean(baseline_relevant), "perturbed_mean_demand": statistics.fmean(relevant),
                    })
    return out


def representative_loadouts(matrix: CandidateMatrix, rows: list[PowerLoadout], count_per_tl: int = 12) -> list[tuple[str, PowerLoadout]]:
    out: list[tuple[str, PowerLoadout]] = []
    for tl in range(1, 10):
        pool = [x for x in rows if x.tl == tl]
        states = {x.id: demand_states(matrix, x) for x in pool}
        seen: set[str] = set()
        picks: list[tuple[str, PowerLoadout]] = []
        def add(tag: str, candidates: list[PowerLoadout], key: Callable[[PowerLoadout], Any], reverse: bool = False) -> None:
            candidates = [x for x in candidates if x.id not in seen]
            if not candidates:
                return
            x = sorted(candidates, key=key, reverse=reverse)[0]
            seen.add(x.id); picks.append((tag, x))
        add("lean", pool, lambda x: (states[x.id]["routine"], x.used_space, x.id))
        med = statistics.median(states[x.id]["full"] for x in pool)
        add("median", pool, lambda x: (abs(states[x.id]["full"] - med), -x.used_space, x.id))
        add("max-full", pool, lambda x: (states[x.id]["full"], x.used_space, x.id), True)
        add("dual-hot", [x for x in pool if x.main_count == 2], lambda x: (states[x.id]["full"], x.powered_aux_count, x.used_space), True)
        for w, tag in (("K", "kinetic"), ("E", "energy"), ("M", "missile"), ("SW", "swarmer")):
            add(tag, [x for x in pool if x.weapon == w and x.main_count == 1], lambda x: (x.powered_aux_count + int(x.shield) + int(x.ecm) + int(x.eccm), states[x.id]["full"], x.used_space), True)
        add("pds-fortress", [x for x in pool if x.pds != "NONE" and x.shield], lambda x: (states[x.id]["defense"], x.powered_aux_count, x.used_space), True)
        add("ew-heavy", [x for x in pool if x.ecm and x.eccm], lambda x: (states[x.id]["offense"], x.powered_aux_count, x.used_space), True)
        add("shield-specialist", [x for x in pool if x.shield and (x.hardener or x.stabilizer)], lambda x: (states[x.id]["defense"], x.powered_aux_count, x.used_space), True)
        add("armor-specialist", [x for x in pool if x.crystalline or x.energized], lambda x: (states[x.id]["defense"], x.powered_aux_count, x.used_space), True)
        add("repair-crisis", [x for x in pool if x.drone], lambda x: (states[x.id]["recovery"], x.powered_aux_count, x.used_space), True)
        if len(picks) < count_per_tl:
            for x in sorted(pool, key=lambda x: (states[x.id]["full"], x.used_space, x.id), reverse=True):
                if len(picks) >= count_per_tl:
                    break
                if x.id in seen:
                    continue
                seen.add(x.id); picks.append((f"coverage-{len(picks)+1}", x))
        out.extend((f"TL{tl}-{tag}", x) for tag, x in picks[:count_per_tl])
    return out


def _activation(rng: XorShift64, p: float) -> bool:
    return rng.random() < p


def _turn_requests(matrix: CandidateMatrix, l: PowerLoadout, doctrine: str, rng: XorShift64) -> list[Request]:
    cfg = DOCTRINES[doctrine]; c = _costs(matrix, l); req: list[Request] = []
    if _activation(rng, cfg["fire"]):
        for _ in range(l.main_count):
            if l.weapon == "E":
                if _activation(rng, cfg["energy_overload"]):
                    req.append(Request("weapon", c["weapon_peak"], c["weapon_peak"], c["weapon_standard"] if c["weapon_standard"] < c["weapon_peak"] else c["weapon_low"]))
                else:
                    req.append(Request("weapon", c["weapon_standard"], c["weapon_standard"], c["weapon_low"] if c["weapon_low"] < c["weapon_standard"] else None))
            else:
                req.append(Request("weapon", c["weapon_standard"]))
    roll = rng.random()
    if roll < cfg["sensor_high"]:
        req.append(Request("sensor", c["sensor_high"], c["sensor_high"], c["sensor_low"] if c["sensor_low"] < c["sensor_high"] else None))
    elif roll < cfg["sensor_high"] + cfg["sensor_low"]:
        req.append(Request("sensor", c["sensor_low"]))
    if l.ecm and _activation(rng, cfg["ecm"]): req.append(Request("ecm", c["ecm"]))
    if l.eccm and _activation(rng, cfg["eccm"]): req.append(Request("eccm", c["eccm"]))
    if l.pds != "NONE" and _activation(rng, cfg["pds"]): req.append(Request("pds", c["pds"]))
    if l.shield and c["shield_recharge"] > 0 and _activation(rng, cfg["shield_recharge"]): req.append(Request("shield_recharge", rng.randint(1, c["shield_recharge"])))
    if c["armor_regen"] > 0 and _activation(rng, cfg["armor_regen"]): req.append(Request("armor_regen", rng.randint(1, c["armor_regen"])))
    if l.hardener and _activation(rng, cfg["hardener"]): req.append(Request("shield_hardener", c["hardener"]))
    if l.energized and _activation(rng, cfg["energized"]): req.append(Request("energized_armor", c["energized"]))
    if l.stabilizer and _activation(rng, cfg["stabilizer"]): req.append(Request("field_stabilizer", c["stabilizer"]))
    dc_on = _activation(rng, cfg["damage_control"])
    if dc_on:
        req.append(Request("damage_control", c["damage_control"]))
        if l.drone and _activation(rng, cfg["drone"]): req.append(Request("repair_drone", c["drone"]))
    if _activation(rng, cfg["stl_overload"]): req.append(Request("stl_overload", c["stl_overload"]))
    return [x for x in req if x.cost > 0]


def _allocate(requests: list[Request], supply: int, doctrine: str) -> dict[str, Any]:
    priority = {name: i for i, name in enumerate(PRIORITY[doctrine])}
    ordered = sorted(enumerate(requests), key=lambda z: (priority.get(z[1].group, 999), z[0]))
    rem = max(0, int(supply)); funded_tp = 0; requested_tp = sum(x.cost for x in requests)
    requested = Counter(x.group for x in requests); funded = Counter(); fallback = Counter()
    for _, r in ordered:
        use = r.cost
        if use <= rem:
            rem -= use; funded_tp += use; funded[r.group] += 1
            continue
        if r.fallback_cost is not None and int(r.fallback_cost) <= rem:
            use = int(r.fallback_cost); rem -= use; funded_tp += use; funded[r.group] += 1; fallback[r.group] += 1
    return {"requested_tp": requested_tp, "funded_tp": funded_tp, "denied_tp": max(0, requested_tp - funded_tp), "requested": requested, "funded": funded, "fallback": fallback, "remaining": rem}


def _hist_quantile(hist: Counter[int], n: int, p: float) -> int:
    target = n * p; acc = 0
    for k in sorted(hist):
        acc += hist[k]
        if acc >= target: return k
    return max(hist) if hist else 0


def _stochastic_one(repo: str, study_doc: dict[str, Any], l: PowerLoadout, tag: str, doctrine: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    matrix = load_research_execution_baseline_pf4(Path(repo)); n = int(study_doc["stochasticTurnSamplesPerVariant"])
    rng = XorShift64(derive_seed(int(study_doc["masterSeed"]), "cp161-demand", l.id, doctrine))
    hist: Counter[int] = Counter(); comp_req_tp = Counter(); comp_req_n = Counter()
    current = int(matrix.p("reactor", l.tl)["operationalTp"])
    eval_supplies = sorted(set(max(0, current + int(x)) for x in study_doc["combatSupplyOffsetsFromPf4"]))
    alloc = {s: {"turns": 0, "raw_short": 0, "denied_tp": 0, "funded_tp": 0, "requested_tp": 0, "requested": Counter(), "funded": Counter(), "fallback": Counter()} for s in eval_supplies}
    for _ in range(n):
        requests = _turn_requests(matrix, l, doctrine, rng); total = sum(r.cost for r in requests); hist[total] += 1
        for r in requests: comp_req_tp[r.group] += r.cost; comp_req_n[r.group] += 1
        for s in eval_supplies:
            a = _allocate(requests, s, doctrine); z = alloc[s]; z["turns"] += 1; z["raw_short"] += int(total > s); z["denied_tp"] += a["denied_tp"]; z["funded_tp"] += a["funded_tp"]; z["requested_tp"] += a["requested_tp"]; z["requested"].update(a["requested"]); z["funded"].update(a["funded"]); z["fallback"].update(a["fallback"])
    variant = {
        "representative": tag, "loadout_id": l.id, "tl": l.tl, "weapon": l.weapon, "doctrine": doctrine, "samples": n,
        "mean_demand": sum(k*v for k,v in hist.items()) / n, "p50_demand": _hist_quantile(hist,n,.50), "p90_demand": _hist_quantile(hist,n,.90), "p95_demand": _hist_quantile(hist,n,.95), "p99_demand": _hist_quantile(hist,n,.99),
        "current_supply": current, "current_shortfall_rate": sum(v for k,v in hist.items() if k > current) / n,
        "degraded_supply": int(matrix.p("reactor", l.tl)["degradedTp"]), "degraded_shortfall_rate": sum(v for k,v in hist.items() if k > int(matrix.p("reactor", l.tl)["degradedTp"])) / n,
        "emergency_supply": int(matrix.p("reactor", l.tl)["emergencyTp"]), "emergency_shortfall_rate": sum(v for k,v in hist.items() if k > int(matrix.p("reactor", l.tl)["emergencyTp"])) / n,
    }
    supply_rows = []
    for s in range(int(study_doc["operationalSupplySweep"]["minimumTp"]), int(study_doc["operationalSupplySweep"]["maximumTp"])+1):
        supply_rows.append({"representative":tag,"tl":l.tl,"weapon":l.weapon,"doctrine":doctrine,"supply":s,"samples":n,"shortfall_rate":sum(v for k,v in hist.items() if k>s)/n,"mean_shortfall_tp":sum(max(0,k-s)*v for k,v in hist.items())/n,"mean_slack_tp":sum(max(0,s-k)*v for k,v in hist.items())/n})
    alloc_rows = []
    groups = tuple(PRIORITY[doctrine])
    for s,z in alloc.items():
        row = {"representative":tag,"tl":l.tl,"weapon":l.weapon,"doctrine":doctrine,"supply":s,"offset_from_pf4":s-current,"samples":n,"raw_shortfall_rate":z["raw_short"]/n,"mean_requested_tp":z["requested_tp"]/n,"mean_funded_tp":z["funded_tp"]/n,"mean_denied_tp":z["denied_tp"]/n}
        for g in groups:
            rq=z["requested"][g]; fd=z["funded"][g]; fb=z["fallback"][g]
            row[f"{g}_requests"] = rq; row[f"{g}_funding_rate"] = fd/rq if rq else 1.0; row[f"{g}_fallback_rate"] = fb/rq if rq else 0.0
        alloc_rows.append(row)
    for g in sorted(comp_req_n):
        variant[f"requested_tp_{g}"] = comp_req_tp[g]/n; variant[f"request_rate_{g}"] = comp_req_n[g]/n
    return variant, supply_rows, alloc_rows


def run_stochastic(repo: Path, study_path: Path, static_dir: Path, out: Path, jobs: int = 24) -> dict[str, Any]:
    doc = load_json(study_path); errs=validate_study(doc)
    if errs: raise ValueError("CP161 study invalid: "+", ".join(errs))
    matrix=load_research_execution_baseline_pf4(repo); allrows=enumerate_loadouts(matrix,reactor_space=6); reps=representative_loadouts(matrix,[x for x in allrows if x.reactor_count==1],int(doc["representativeLoadoutsPerTl"]))
    tasks=[(str(repo),doc,l,tag,d) for tag,l in reps for d in doc["doctrines"]]
    results=[]
    if jobs<=1:
        results=[_stochastic_one(*t) for t in tasks]
    else:
        ctx=get_context("spawn" if os.name=="nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(int(jobs),len(tasks)),mp_context=ctx) as ex:
            results=list(ex.map(_stochastic_unpack,tasks,chunksize=1))
    variants=[x[0] for x in results]; supply=[r for x in results for r in x[1]]; alloc=[r for x in results for r in x[2]]
    _write_csv(out/"stochastic_variants.csv",variants); _write_csv(out/"stochastic_supply_response.csv",supply); _write_csv(out/"allocation_outcomes.csv",alloc)
    aggregate=[]
    groups=defaultdict(list)
    for r in variants: groups[(int(r["tl"]),r["doctrine"])].append(r)
    for (tl,d),rr in sorted(groups.items()):
        aggregate.append({"tl":tl,"doctrine":d,"variants":len(rr),"turn_samples":sum(int(x["samples"]) for x in rr),"mean_demand":statistics.fmean(float(x["mean_demand"]) for x in rr),"mean_current_shortfall_rate":statistics.fmean(float(x["current_shortfall_rate"]) for x in rr),"mean_degraded_shortfall_rate":statistics.fmean(float(x["degraded_shortfall_rate"]) for x in rr),"mean_emergency_shortfall_rate":statistics.fmean(float(x["emergency_shortfall_rate"]) for x in rr)})
    _write_csv(out/"stochastic_tl_doctrine_summary.csv",aggregate)
    summary={"mode":"stochastic","passed":True,"representativeLoadouts":len(reps),"doctrines":len(doc["doctrines"]),"variants":len(variants),"samplesPerVariant":int(doc["stochasticTurnSamplesPerVariant"]),"turnSamples":sum(int(x["samples"]) for x in variants),"supplyResponseRows":len(supply),"allocationRows":len(alloc),"automaticPromotion":False,"tuningAllowed":False}
    _write_json(out/"summary.json",summary);return summary


def _stochastic_unpack(args):
    return _stochastic_one(*args)


def _pf4_aux_registry(matrix: CandidateMatrix) -> dict[tuple[str,int], str]:
    registry: dict[str, dict[str, Any]] = {}; ids: dict[tuple[str,int],str]={}
    mapping = {
        "shieldBattery": "shield_battery", "shieldBooster": "shield_booster", "shieldHardener": "shield_hardener",
        "ablativeArmor": "ablative_armor", "crystallineArmor": "crystalline_armor", "energizedArmor": "energized_armor",
        "fieldStabilizer": "field_stabilizer", "repairDroneBay": "repair_drone", "kineticMagazine": "kinetic_magazine", "missileMagazine": "missile_magazine",
    }
    for key,kind in mapping.items():
        row=matrix.doc.get("pendingFinalizationAuxProfiles",{}).get(key)
        if not row: continue
        for tl_s,spec in row.get("byTl",{}).items():
            tl=int(tl_s); aid=f"PF4-{key}-TL{tl}"; ids[(key,tl)]=aid
            r={"candidate_id":aid,"family":key,"kind":kind,"tl":tl,"space":int(row.get("space",0)),"tp":int(spec.get("tp",spec.get("droneAttemptTp",0)) or 0)}
            translate={"restore":"restore","charges":"charges","capacityBonus":"capacity_bonus","defBonusPp":"def_bonus_pp","ablativeIntegrity":"ablative_integrity","resBonusPp":"res_bonus_pp","spenReduction":"spen_reduction","additionalPreparedRepairKits":"extra_repair_kits","droneAttemptTp":"drone_attempt_tp","ammoBonus":"ammo_bonus"}
            for src,dst in translate.items():
                if src in spec:r[dst]=spec[src]
            if kind=="shield_battery":r["trigger_fraction"]=0.5
            registry[aid]=r
    matrix.cp158_aux_profiles=registry
    return ids


def _combat_build(matrix: CandidateMatrix, tl:int, weapon:str, role:str, ids:dict[tuple[str,int],str]) -> EcologyBuild:
    capacity=int(matrix.p("hull",tl)["capacity"]); main=2 if role=="hot" else 1; reactor=2 if role=="dualR" else 1
    used=_core_space(matrix,tl,weapon,main,reactor,int(matrix.p("reactor",tl)["space"])); shield=False;ecm=False;eccm=False;pds=None;hard=False;crystal=False;aux=[]
    def fit(space:int)->bool:return used+space<=capacity
    def add_core(name:str,space:int):
        nonlocal used; used+=space
    if role in ("balanced","pdsK","pdsE","pdsA","crystal","dualR") or (role=="hot" and fit(int(matrix.p("shield",tl)["space"]))):
        sp=int(matrix.p("shield",tl)["space"])
        if fit(sp):shield=True;add_core("shield",sp)
    if role in ("balanced","hot","dualR"):
        sp=int(matrix.p("ecm",tl)["space"])
        if fit(sp):ecm=True;add_core("ecm",sp)
    if role in ("balanced","hot","dualR","pdsK","pdsE","pdsA","crystal"):
        sp=int(matrix.p("eccm",tl)["space"])
        if fit(sp):eccm=True;add_core("eccm",sp)
    if role.startswith("pds"):
        pf={"pdsK":"K","pdsE":"E","pdsA":"AMM"}[role];pr=_pds_row(matrix,pf,tl);sp=int(pr["space"])
        if fit(sp):pds={"K":"Kinetic","E":"Energy","AMM":"AMM"}[pf];add_core("pds",sp)
    def add_aux(key:str):
        nonlocal used,hard,crystal
        aid=ids.get((key,tl));row=_aux(matrix,key,tl)
        if not aid or not row:return
        sp=int(row.get("space",0))
        if not fit(sp):return
        if key in ("shieldHardener","fieldStabilizer","shieldBattery","shieldBooster") and not shield:return
        used+=sp;aux.append(aid)
        if key=="shieldHardener":hard=True
        if key=="crystallineArmor":crystal=True
    if role=="balanced":
        for k in ("shieldBattery","ablativeArmor","shieldHardener","repairDroneBay","energizedArmor","fieldStabilizer"):add_aux(k)
    elif role.startswith("pds"):
        for k in ("shieldBooster","shieldBattery","shieldHardener","fieldStabilizer","repairDroneBay"):add_aux(k)
    elif role=="crystal":
        for k in ("crystallineArmor","ablativeArmor","energizedArmor","repairDroneBay","shieldHardener"):add_aux(k)
    elif role=="hot":
        for k in ("shieldHardener","energizedArmor","fieldStabilizer"):add_aux(k)
    elif role=="dualR":
        for k in ("shieldBattery","ablativeArmor","shieldHardener","repairDroneBay","energizedArmor","fieldStabilizer"):add_aux(k)
    fam={"K":"Kinetic","E":"Energy","M":"Missile","SW":"Missile"}[weapon]
    return EcologyBuild(id=f"CP161-TL{tl}-{weapon}-{role}",tl=tl,archetype=f"cp161-{role}",weapon_family=fam,main_count=main,reactor_count=reactor,shield=shield,ecm=ecm,eccm=eccm,pds_family=pds,shield_hardener=hard,capacity=capacity,combat_space=used,mission_aux_space=capacity-used,missile_payload=("Swarmer" if weapon=="SW" else "GP"),armor_profile="mainline",auxiliary_profiles=tuple(aux))


def combat_contexts(repo: Path, tl:int) -> list[EcologyVariant]:
    m=load_research_execution_baseline_pf4(repo);ids=_pf4_aux_registry(m)
    roles={}
    for w in ("K","E","M")+(("SW",) if bool(m.p("missile_swarmer",tl).get("available",False)) else ()):
        for role in ("balanced","pdsK","pdsE","pdsA","crystal","hot","dualR"):
            roles[(w,role)] = _combat_build(m,tl,w,role,ids)
    sw="SW" if ("SW","balanced") in roles else "M"
    pairings=[
        (("K","balanced"),("E","balanced"),"K_BAL_vs_E_BAL"),
        (("E","balanced"),("K","balanced"),"E_BAL_vs_K_BAL"),
        (("K","crystal"),("E","balanced"),"K_CRY_vs_E_BAL"),
        (("E","balanced"),("K","crystal"),"E_BAL_vs_K_CRY"),
        (("M","balanced"),("K","pdsK"),"M_vs_KPDS"),
        (("M","balanced"),("E","pdsE"),"M_vs_EPDS"),
        (("M","balanced"),("K","pdsA"),"M_vs_AMM"),
        ((sw,"balanced"),("K","pdsA"),f"{sw}_vs_AMM"),
        (("K","hot"),("E","balanced"),"K_HOT_vs_E_BAL"),
        (("E","hot"),("K","balanced"),"E_HOT_vs_K_BAL"),
        (("M","hot"),("K","balanced"),"M_HOT_vs_K_BAL"),
        ((sw,"hot"),("E","balanced"),f"{sw}_HOT_vs_E_BAL"),
        (("K","balanced"),("K","dualR"),"K_1R_vs_K_2R"),
        (("K","dualR"),("K","balanced"),"K_2R_vs_K_1R"),
        (("E","balanced"),("E","dualR"),"E_1R_vs_E_2R"),
        (("E","dualR"),("E","balanced"),"E_2R_vs_E_1R"),
        (("M","balanced"),("M","dualR"),"M_1R_vs_M_2R"),
        (("M","dualR"),("M","balanced"),"M_2R_vs_M_1R"),
    ]
    variants=[]
    for i,(ak,bk,label) in enumerate(pairings):
        a=roles[ak];b=roles[bk]
        for order in ("SideAFirst","SideBFirst"):
            variants.append(EcologyVariant(id=f"CP161-TL{tl}-{label}-{order}",tl=tl,side_a=a,side_b=b,movement_order=order,population="cp161_reactor_tp_combat_sensitivity",scenario_group=label))
    return variants


_C_REPO: Path|None=None; _C_DOC:dict[str,Any]|None=None; _C_CACHE:dict[tuple[int,int],CandidateMatrix]={}
def _combat_init(repo:str,doc:dict[str,Any]):
    global _C_REPO,_C_DOC,_C_CACHE;_C_REPO=Path(repo);_C_DOC=doc;_C_CACHE={}
def _combat_matrix(tl:int,supply:int)->CandidateMatrix:
    key=(tl,supply)
    if key not in _C_CACHE:
        m=load_research_execution_baseline_pf4(_C_REPO);_pf4_aux_registry(m);m=copy.deepcopy(m);m.doc=copy.deepcopy(m.doc);m.profiles=m.doc["profiles"];m.branches={r["id"]:r for r in m.doc.get("branches",[])};m.p("reactor",tl)["operationalTp"]=int(supply);_C_CACHE[key]=m
    return _C_CACHE[key]
def _combat_task(args):
    idx,variant,supply,seed,trials=args;m=_combat_matrix(variant.tl,supply);aw=bw=dr=caps=err=turns=0;sa=defaultdict(float);sb=defaultdict(float)
    metrics=("power_available_total","power_spent_total","power_shortfall_events","weapon_power_shortfalls","pds_power_shortfalls","acquisition_power_shortfalls","power_sensor","power_ecm","power_eccm","power_pds","power_weapons","power_shield_recharge","power_shield_hardener","power_aux_energized_armor","power_aux_field_stabilizer","reactor_overload_activations","damage_control_tp_spent","cp147_recovery_reserved_tp","cp147_package_decisions")
    for j in range(trials):
        r=run_trial_full_map(m,variant,seed,j,combat_doctrine=COMBAT_DOCTRINE);err+=int(bool(r.error));caps+=int(r.termination_cause=="TURN_CAP_SENTINEL");turns+=r.turns
        if r.winner=="A":aw+=1
        elif r.winner=="B":bw+=1
        else:dr+=1
        for k in metrics:sa[k]+=float(getattr(r.side_a,k,0));sb[k]+=float(getattr(r.side_b,k,0))
    base=int(load_research_execution_baseline_pf4(_C_REPO).p("reactor",variant.tl)["operationalTp"])
    row={"tl":variant.tl,"scenario_id":variant.id,"scenario_group":variant.scenario_group,"movement_order":variant.movement_order,"supply":supply,"offset_from_pf4":supply-base,"trials":trials,"a_wins":aw,"b_wins":bw,"draws":dr,"a_decisive_share":aw/max(1,aw+bw),"mean_turns":turns/max(1,trials),"turn_cap_sentinels":caps,"error_trials":err,"side_a_build":variant.side_a.id,"side_b_build":variant.side_b.id}
    for k in metrics:row["mean_a_"+k]=sa[k]/trials;row["mean_b_"+k]=sb[k]/trials
    return row


def run_combat_batch(repo:Path,study_path:Path,out:Path,tl:int,jobs:int=24)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP161 study invalid: "+", ".join(errs))
    variants=combat_contexts(repo,tl);base=int(load_research_execution_baseline_pf4(repo).p("reactor",tl)["operationalTp"]);supplies=[max(2,base+int(x)) for x in doc["combatSupplyOffsetsFromPf4"]];trials=int(doc["combatTrialsPerCell"]);tasks=[]
    for i,v in enumerate(variants):
        for s in supplies:tasks.append((i,v,s,derive_seed(int(doc["masterSeed"]),"cp161-combat",tl,v.id),trials))
    if jobs<=1:
        _combat_init(str(repo),doc);rows=[_combat_task(t) for t in tasks]
    else:
        ctx=get_context("spawn" if os.name=="nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(int(jobs),len(tasks)),mp_context=ctx,initializer=_combat_init,initargs=(str(repo),doc)) as ex:rows=list(ex.map(_combat_task,tasks,chunksize=1))
    rows.sort(key=lambda x:(x["scenario_id"],x["supply"]));_write_csv(out/"combat_response.csv",rows)
    summary={"mode":"combat-batch","passed":not any(int(x["error_trials"]) for x in rows),"tl":tl,"contexts":len(variants),"supplyCandidates":len(supplies),"cells":len(rows),"trialsPerCell":trials,"combatTrials":len(rows)*trials,"turnCapSentinels":sum(int(x["turn_cap_sentinels"]) for x in rows),"errorTrials":sum(int(x["error_trials"]) for x in rows),"automaticPromotion":False}
    _write_json(out/"summary.json",summary);return summary


def merge_combat(batch_root:Path,out:Path)->dict[str,Any]:
    rows=[];audit=[]
    for p in sorted(batch_root.rglob("summary.json")):
        sm=json.loads(p.read_text(encoding="utf-8-sig"));data=p.parent/"combat_response.csv";ok=sm.get("mode")=="combat-batch" and bool(sm.get("passed")) and data.is_file();n=0
        if ok:
            with data.open(encoding="utf-8-sig",newline="") as f:r=list(csv.DictReader(f));rows.extend(r);n=len(r)
        audit.append({"batch":p.parent.name,"tl":sm.get("tl",""),"passed":int(ok),"rows":n,"combat_trials":sm.get("combatTrials",0),"turn_caps":sm.get("turnCapSentinels",0),"errors":sm.get("errorTrials",0)})
    rows.sort(key=lambda x:(int(x["tl"]),x["scenario_id"],int(x["supply"])));_write_csv(out/"combat_response.csv",rows);_write_csv(out/"batch_merge_audit.csv",audit)
    agg=defaultdict(list)
    for r in rows:agg[(int(r["tl"]),int(r["supply"]))].append(r)
    sums=[]
    for (tl,s),rr in sorted(agg.items()):
        sums.append({"tl":tl,"supply":s,"offset_from_pf4":int(rr[0]["offset_from_pf4"]),"cells":len(rr),"combat_trials":sum(int(x["trials"]) for x in rr),"mean_turns":statistics.fmean(float(x["mean_turns"]) for x in rr),"turn_cap_rate":sum(int(x["turn_cap_sentinels"]) for x in rr)/sum(int(x["trials"]) for x in rr),"mean_side_a_power_shortfalls":statistics.fmean(float(x["mean_a_power_shortfall_events"]) for x in rr),"mean_side_b_power_shortfalls":statistics.fmean(float(x["mean_b_power_shortfall_events"]) for x in rr),"mean_side_a_weapon_shortfalls":statistics.fmean(float(x["mean_a_weapon_power_shortfalls"]) for x in rr),"mean_side_b_weapon_shortfalls":statistics.fmean(float(x["mean_b_weapon_power_shortfalls"]) for x in rr),"error_trials":sum(int(x["error_trials"]) for x in rr)})
    _write_csv(out/"combat_supply_summary.csv",sums)
    summary={"mode":"combat-merged","passed":len(audit)==9 and all(int(x["passed"]) for x in audit) and not any(int(r["error_trials"]) for r in rows),"batches":len(audit),"cells":len(rows),"combatTrials":sum(int(r["trials"]) for r in rows),"turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),"errorTrials":sum(int(r["error_trials"]) for r in rows),"automaticPromotion":False}
    _write_json(out/"summary.json",summary);return summary


def plan(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);errs=validate_study(doc)
    if errs:raise ValueError("CP161 study invalid: "+", ".join(errs))
    m=load_research_execution_baseline_pf4(repo);rows=enumerate_loadouts(m,reactor_space=6);reps=representative_loadouts(m,[x for x in rows if x.reactor_count==1],int(doc["representativeLoadoutsPerTl"]));ctx={tl:len(combat_contexts(repo,tl)) for tl in range(1,10)}
    combat=sum(ctx.values())*len(doc["combatSupplyOffsetsFromPf4"])*int(doc["combatTrialsPerCell"]);samples=len(reps)*len(doc["doctrines"])*int(doc["stochasticTurnSamplesPerVariant"])
    summary={"mode":"plan","passed":True,"baselineId":"CP160-PF4","legalPoweredArchitectures":len(rows),"oneReactorArchitectures":sum(x.reactor_count==1 for x in rows),"twoReactorArchitectures":sum(x.reactor_count==2 for x in rows),"representativeLoadouts":len(reps),"stochasticVariants":len(reps)*len(doc["doctrines"]),"stochasticTurnSamples":samples,"combatContextsByTl":ctx,"combatContexts":sum(ctx.values()),"combatSupplyCandidatesPerTl":len(doc["combatSupplyOffsetsFromPf4"]),"combatCells":sum(ctx.values())*len(doc["combatSupplyOffsetsFromPf4"]),"combatTrials":combat,"operationalSupplySweep":"2-30 TP","reactorSpaceSweep":doc["reactorSpaceSweep"],"automaticPromotion":False,"tuningAllowed":False}
    _write_json(out/"summary.json",summary);return summary


def smoke(repo:Path,study_path:Path,out:Path)->dict[str,Any]:
    doc=load_json(study_path);m=load_research_execution_baseline_pf4(repo);rows=enumerate_loadouts(m);checks=[]
    checks.append({"probe":"loadout_population","passed":int(len(rows)>1000)})
    l=next(x for x in rows if x.tl==9 and x.weapon=="E" and x.reactor_count==1 and x.main_count==2 and x.shield and x.ecm and x.eccm and x.drone)
    st=demand_states(m,l);checks.append({"probe":"full_demand_exceeds_core","passed":int(st["full"]>st["core"])})
    v=combat_contexts(repo,9)[0];ids=_pf4_aux_registry(m);checks.append({"probe":"pf4_aux_registry","passed":int(bool(ids) and any(v.side_a.auxiliary_profiles))})
    _combat_init(str(repo),doc);base=int(m.p("reactor",9)["operationalTp"]);r1=_combat_task((0,v,max(2,base-2),derive_seed(int(doc["masterSeed"]),"smoke-low"),1));r2=_combat_task((1,v,base+8,derive_seed(int(doc["masterSeed"]),"smoke-high"),1));checks.append({"probe":"combat_low_high","passed":int(r1["error_trials"]==0 and r2["error_trials"]==0)})
    v2=next(x for x in combat_contexts(repo,9) if x.side_a.reactor_count==2 or x.side_b.reactor_count==2);r3=_combat_task((2,v2,base,derive_seed(int(doc["masterSeed"]),"smoke-two-reactor"),1));checks.append({"probe":"combat_second_reactor","passed":int(r3["error_trials"]==0)})
    _write_csv(out/"reactor_tp_smoke.csv",checks);summary={"mode":"smoke","passed":all(int(x["passed"]) for x in checks),"probes":len(checks),"combatTrials":3};_write_json(out/"summary.json",summary);return summary


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--study",required=True);sp=ap.add_subparsers(dest="cmd",required=True)
    for name in ("plan","smoke","static"):
        p=sp.add_parser(name);p.add_argument("--out",required=True)
    p=sp.add_parser("stochastic");p.add_argument("--static-dir",required=True);p.add_argument("--out",required=True);p.add_argument("--jobs",type=int,default=24)
    p=sp.add_parser("combat-batch");p.add_argument("--tl",type=int,required=True);p.add_argument("--out",required=True);p.add_argument("--jobs",type=int,default=24)
    p=sp.add_parser("merge-combat");p.add_argument("--batches",required=True);p.add_argument("--out",required=True)
    a=ap.parse_args(argv);repo=Path(a.repo).resolve();study=Path(a.study).resolve();out=Path(a.out).resolve()
    if a.cmd=="plan":res=plan(repo,study,out)
    elif a.cmd=="smoke":res=smoke(repo,study,out)
    elif a.cmd=="static":res=static_analysis(repo,study,out)
    elif a.cmd=="stochastic":res=run_stochastic(repo,study,Path(a.static_dir),out,a.jobs)
    elif a.cmd=="combat-batch":res=run_combat_batch(repo,study,out,a.tl,a.jobs)
    elif a.cmd=="merge-combat":res=merge_combat(Path(a.batches),out)
    else:raise SystemExit(2)
    print(json.dumps(res,indent=2));return 0 if res.get("passed",False) else 1


if __name__=="__main__":
    raise SystemExit(main())
