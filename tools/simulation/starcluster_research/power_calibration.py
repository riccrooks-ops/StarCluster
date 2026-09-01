from __future__ import annotations

import csv
import itertools
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .rng import XorShift64, derive_seed


SCHEMA_VERSION = "star-cluster-power-reactor-calibration-v1"
DOCTRINES = {
    "offense": {
        "fire": 0.88,
        "peak": 0.30,
        "sensor_high": 0.25,
        "sensor_low": 0.65,
        "ecm": 0.35,
        "eccm": 0.50,
        "shield": 0.30,
        "pds": 0.15,
        "stl_overload": 0.08,
    },
    "ew_contested": {
        "fire": 0.70,
        "peak": 0.22,
        "sensor_high": 0.60,
        "sensor_low": 0.37,
        "ecm": 0.85,
        "eccm": 0.90,
        "shield": 0.35,
        "pds": 0.18,
        "stl_overload": 0.05,
    },
    "defense": {
        "fire": 0.45,
        "peak": 0.15,
        "sensor_high": 0.30,
        "sensor_low": 0.60,
        "ecm": 0.65,
        "eccm": 0.70,
        "shield": 0.80,
        "pds": 0.75,
        "stl_overload": 0.08,
    },
    "mixed": {
        "fire": 0.72,
        "peak": 0.25,
        "sensor_high": 0.35,
        "sensor_low": 0.55,
        "ecm": 0.55,
        "eccm": 0.60,
        "shield": 0.55,
        "pds": 0.40,
        "stl_overload": 0.10,
    },
}


class PowerStudyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Reactor:
    id: str
    tl: int
    technology: str
    space: int
    operational: int
    degraded: int
    emergency: int
    family: str
    status: str


@dataclass(frozen=True, slots=True)
class WeaponPart:
    id: str
    family: str
    space: int
    standard_tp: int
    peak_tp: int


@dataclass(frozen=True, slots=True)
class Loadout:
    tl: int
    capacity: int
    used_space: int
    weapon_name: str
    weapons: tuple[WeaponPart, ...]
    shield: bool
    ecm: bool
    eccm: bool
    pds_counts: tuple[int, int, int]
    pds_tps: tuple[int, int, int]
    base_space_without_reactor: int

    @property
    def free_space(self) -> int:
        return self.capacity - self.used_space

    @property
    def main_count(self) -> int:
        return len(self.weapons)

    @property
    def pds_total(self) -> int:
        return sum(self.pds_counts)

    @property
    def ew_count(self) -> int:
        return int(self.ecm) + int(self.eccm)


@dataclass(frozen=True, slots=True)
class DemandVector:
    routine: int
    offense: int
    defense: int
    full: int


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise PowerStudyError(f"cannot read JSON {path}: {exc}") from exc


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if doc.get("checkpoint") != "110":
        errors.append('checkpoint must be the string "110"')
    if not isinstance(doc.get("matrixPath"), str):
        errors.append("matrixPath must be a string")
    if not isinstance(doc.get("masterSeed"), int) or isinstance(doc.get("masterSeed"), bool):
        errors.append("masterSeed must be an integer")
    for key in ("maxPdsBatteries", "minimumTurnSamples", "maximumTurnSamples", "turnSampleBatch", "encountersPerVariant", "turnsPerEncounter"):
        value = doc.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{key} must be a positive integer")
    width = doc.get("targetWilsonHalfWidth")
    if not isinstance(width, (int, float)) or isinstance(width, bool) or not (0 < float(width) < 0.1):
        errors.append("targetWilsonHalfWidth must be a number between 0 and 0.1")
    if doc.get("maximumTurnSamples", 0) < doc.get("minimumTurnSamples", 0):
        errors.append("maximumTurnSamples must be >= minimumTurnSamples")
    if doc.get("turnSampleBatch", 1) > doc.get("maximumTurnSamples", 0):
        errors.append("turnSampleBatch cannot exceed maximumTurnSamples")
    if doc.get("reactorCountMaximum") != 2:
        errors.append("reactorCountMaximum must remain 2 under the current cruiser construction baseline")
    if doc.get("mainWeaponCountMaximum") != 2:
        errors.append("mainWeaponCountMaximum must remain 2 under the current cruiser construction baseline")
    doctrines = doc.get("doctrines")
    if doctrines != list(DOCTRINES):
        errors.append(f"doctrines must be {list(DOCTRINES)}")
    policy = doc.get("interpretationPolicy")
    if not isinstance(policy, dict):
        errors.append("interpretationPolicy must be an object")
    else:
        if policy.get("automaticPromotion") is not False:
            errors.append("interpretationPolicy.automaticPromotion must be false")
        if policy.get("noTargetWinRate") is not True:
            errors.append("interpretationPolicy.noTargetWinRate must be true")
        if policy.get("noRequiredFullSimultaneousDemandCoverage") is not True:
            errors.append("interpretationPolicy.noRequiredFullSimultaneousDemandCoverage must be true")
        if policy.get("productionRuntime") != "C# / Godot":
            errors.append("interpretationPolicy.productionRuntime must remain C# / Godot")
    return errors


def _profiles(matrix: dict[str, Any], family: str) -> dict[str, Any]:
    profiles = matrix.get("profiles", {})
    if family not in profiles:
        raise PowerStudyError(f"matrix missing profile family {family}")
    return profiles[family]


def profile(matrix: dict[str, Any], family: str, tl: int) -> dict[str, Any]:
    rows = _profiles(matrix, family)
    try:
        return rows[str(tl)]
    except KeyError as exc:
        raise PowerStudyError(f"matrix missing {family} TL{tl}") from exc


def _parse_first_tp(text: str) -> int:
    match = re.search(r"(?:Standard\s+)?(\d+)\s*TP", text, re.IGNORECASE)
    return int(match.group(1)) if match else 0


def reactor_catalog(matrix: dict[str, Any]) -> list[Reactor]:
    reactors: list[Reactor] = []
    for tl in range(1, 10):
        row = profile(matrix, "reactor", tl)
        reactors.append(
            Reactor(
                id=f"reactor-tl{tl}",
                tl=tl,
                technology=row["technology"],
                space=int(row["space"]),
                operational=int(row["operationalTp"]),
                degraded=int(row["degradedTp"]),
                emergency=int(row["emergencyTp"]),
                family=str(row.get("family", "standard")),
                status="primary",
            )
        )
    for branch in matrix.get("branches", []):
        if not str(branch.get("id", "")).startswith("power-fission-revival"):
            continue
        values = [int(x) for x in re.findall(r"\d+", str(branch.get("numeric", "")))]
        if len(values) < 3:
            raise PowerStudyError(f"cannot parse fission-revival reactor outputs: {branch.get('id')}")
        reactors.append(
            Reactor(
                id=str(branch["id"]),
                tl=int(branch["tl"]),
                technology=str(branch["technology"]),
                space=int(branch["space"]),
                operational=values[0],
                degraded=values[1],
                emergency=values[2],
                family="fission",
                status="legacy_revival_branch",
            )
        )
    return sorted(reactors, key=lambda x: (x.tl, x.status != "primary", x.id))


def standard_reactor(matrix: dict[str, Any], tl: int) -> Reactor:
    return next(r for r in reactor_catalog(matrix) if r.id == f"reactor-tl{tl}")


def standard_weapon_parts(matrix: dict[str, Any], tl: int) -> list[WeaponPart]:
    kinetic = profile(matrix, "kinetic_main", tl)
    energy = profile(matrix, "energy_main", tl)
    missile = profile(matrix, "missile_delivery", tl)
    return [
        WeaponPart("kinetic_main", "Kinetic", int(kinetic["space"]), int(kinetic["firingTp"]), int(kinetic["firingTp"])),
        WeaponPart("energy_main", "Energy", int(energy["space"]), int(energy["standardTp"]), int(energy["highTp"])),
        WeaponPart("missile_delivery", "Missile", int(missile["space"]), int(missile["launchTp"]), int(missile["launchTp"])),
    ]


def branch_weapon_parts(matrix: dict[str, Any], tl: int) -> list[WeaponPart]:
    parts: list[WeaponPart] = []
    for branch in matrix.get("branches", []):
        if int(branch.get("tl", 99)) > tl:
            continue
        if branch.get("expression") != "installed_component":
            continue
        owner = branch.get("owner")
        if owner not in ("Energy Weapons", "Projectile Weapons"):
            continue
        space = branch.get("space")
        if not isinstance(space, int):
            continue
        power = _parse_first_tp(str(branch.get("numeric", "")))
        family = "Energy" if owner == "Energy Weapons" else "Kinetic"
        parts.append(WeaponPart(str(branch["id"]), family, int(space), power, power))
    return parts


def weapon_packages(matrix: dict[str, Any], tl: int, *, include_branches: bool = False) -> list[tuple[WeaponPart, ...]]:
    parts = standard_weapon_parts(matrix, tl)
    if include_branches:
        parts = parts + branch_weapon_parts(matrix, tl)
    packages: list[tuple[WeaponPart, ...]] = []
    for i, first in enumerate(parts):
        packages.append((first,))
        for second in parts[i:]:
            packages.append((first, second))
    return packages


def pds_allocations(matrix: dict[str, Any], tl: int, maximum: int) -> Iterable[tuple[tuple[int, int, int], int, tuple[int, int, int]]]:
    families = [profile(matrix, f, tl) for f in ("kinetic_pds", "energy_pds", "amm_pds")]
    spaces = tuple(int(x["space"]) for x in families)
    tps = tuple(int(x["readinessTp"]) for x in families)
    for total in range(maximum + 1):
        for kinetic in range(total + 1):
            for energy in range(total - kinetic + 1):
                amm = total - kinetic - energy
                counts = (kinetic, energy, amm)
                yield counts, sum(c * s for c, s in zip(counts, spaces)), tps


def enumerate_loadouts(matrix: dict[str, Any], tl: int, reactor: Reactor, maximum_pds: int) -> list[Loadout]:
    hull = profile(matrix, "hull", tl)
    capacity = int(hull["capacity"])
    fixed_without_reactor = sum(
        int(profile(matrix, family, tl)["space"])
        for family in ("stl", "ftl", "computer", "sensor")
    )
    shield = profile(matrix, "shield", tl)
    ecm = profile(matrix, "ecm", tl)
    eccm = profile(matrix, "eccm", tl)
    rows: list[Loadout] = []
    for weapons in weapon_packages(matrix, tl, include_branches=False):
        weapon_space = sum(w.space for w in weapons)
        for shield_on, ecm_on, eccm_on in itertools.product((False, True), repeat=3):
            fixed = (
                fixed_without_reactor
                + reactor.space
                + weapon_space
                + (int(shield["space"]) if shield_on else 0)
                + (int(ecm["space"]) if ecm_on else 0)
                + (int(eccm["space"]) if eccm_on else 0)
            )
            for counts, pds_space, pds_tps in pds_allocations(matrix, tl, maximum_pds):
                used = fixed + pds_space
                if used > capacity:
                    continue
                rows.append(
                    Loadout(
                        tl=tl,
                        capacity=capacity,
                        used_space=used,
                        weapon_name="+".join(w.id for w in weapons),
                        weapons=weapons,
                        shield=shield_on,
                        ecm=ecm_on,
                        eccm=eccm_on,
                        pds_counts=counts,
                        pds_tps=pds_tps,
                        base_space_without_reactor=fixed_without_reactor,
                    )
                )
    return rows


def demand_vector(matrix: dict[str, Any], loadout: Loadout) -> DemandVector:
    tl = loadout.tl
    sensor = profile(matrix, "sensor", tl)
    shield = profile(matrix, "shield", tl)
    sensor_low = int(sensor.get("activeLowTp") or 0)
    sensor_high = sensor.get("activeHighTp")
    sensor_high = sensor_low if sensor_high is None else int(sensor_high)
    ew = (int(profile(matrix, "ecm", tl)["fullStrengthTp"]) if loadout.ecm else 0) + (
        int(profile(matrix, "eccm", tl)["fullStrengthTp"]) if loadout.eccm else 0
    )
    pds = sum(c * tp for c, tp in zip(loadout.pds_counts, loadout.pds_tps))
    weapon_standard = sum(w.standard_tp for w in loadout.weapons)
    weapon_peak = sum(w.peak_tp for w in loadout.weapons)
    routine = weapon_standard + sensor_low + ew + (1 if loadout.shield else 0)
    offense = weapon_peak + sensor_high + ew + (1 if loadout.shield else 0)
    defense = sensor_high + ew + (int(shield["tacticalRechargeCapTp"]) if loadout.shield else 0) + pds
    full = offense + (int(shield["tacticalRechargeCapTp"]) - 1 if loadout.shield else 0) + pds + int(profile(matrix, "stl", tl)["overloadTp"])
    return DemandVector(routine, offense, defense, full)


def loadout_cell(loadout: Loadout) -> str:
    if loadout.pds_total == 0:
        pds = "pds0"
    elif loadout.pds_total <= 2:
        pds = "pds1-2"
    else:
        pds = "pds3-5"
    ew = "ew2" if loadout.ew_count == 2 else "ew1" if loadout.ew_count == 1 else "ew0"
    return "|".join(("dual" if loadout.main_count == 2 else "single", pds, "shield" if loadout.shield else "noshield", ew))


def _quantile(values: list[int], p: float) -> int:
    if not values:
        return 0
    values = sorted(values)
    return values[round((len(values) - 1) * p)]


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _wilson_half_width(successes: int, n: int, z: float = 1.959963984540054) -> float:
    if n <= 0:
        return 1.0
    p = successes / n
    den = 1.0 + z * z / n
    term = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / den
    return term


def representative_loadouts(matrix: dict[str, Any], rows: list[Loadout]) -> list[tuple[str, Loadout]]:
    if not rows:
        return []
    vectors = {id(row): demand_vector(matrix, row) for row in rows}
    median_full = statistics.median(v.full for v in vectors.values())
    picks: list[tuple[str, Loadout]] = []
    seen: set[tuple[Any, ...]] = set()

    def signature(row: Loadout) -> tuple[Any, ...]:
        return row.weapon_name, row.shield, row.ecm, row.eccm, row.pds_counts, row.used_space

    def add(name: str, candidates: list[Loadout], key, reverse: bool = False) -> None:
        if not candidates:
            return
        row = sorted(candidates, key=key, reverse=reverse)[0]
        sig = signature(row)
        if sig not in seen:
            seen.add(sig)
            picks.append((name, row))

    add("lean", rows, lambda x: (vectors[id(x)].full, x.used_space))
    add("median", rows, lambda x: (abs(vectors[id(x)].full - median_full), -x.used_space))
    add("max-full-demand", rows, lambda x: (vectors[id(x)].full, x.used_space), True)
    add("max-pds", rows, lambda x: (x.pds_total, vectors[id(x)].full, x.used_space), True)
    add("dual-energy", [x for x in rows if x.weapon_name == "energy_main+energy_main"], lambda x: (vectors[id(x)].full, x.used_space), True)
    add("ew-shield", [x for x in rows if x.ecm and x.eccm and x.shield], lambda x: (abs(vectors[id(x)].full - median_full), -x.used_space))
    mixed = [x for x in rows if "+" in x.weapon_name and len({w.family for w in x.weapons}) > 1]
    add("mixed-dual", mixed, lambda x: (vectors[id(x)].full, x.used_space), True)
    add("missile-fortress", [x for x in rows if any(w.family == "Missile" for w in x.weapons) and x.shield], lambda x: (x.pds_total, vectors[id(x)].full, x.used_space), True)

    # Named archetypes can collapse onto the same exact loadout at some TLs.
    # Fill remaining slots from distinct population cells so the stochastic study
    # preserves breadth rather than silently shrinking to a few extreme designs.
    covered_cells = {loadout_cell(row) for _, row in picks}
    for cell in sorted({loadout_cell(row) for row in rows}):
        if len(picks) >= 8:
            break
        if cell in covered_cells:
            continue
        candidates = [row for row in rows if loadout_cell(row) == cell and signature(row) not in seen]
        if not candidates:
            continue
        row = sorted(candidates, key=lambda x: (abs(vectors[id(x)].full - median_full), -x.used_space, x.weapon_name, x.pds_counts))[0]
        sig = signature(row)
        seen.add(sig)
        covered_cells.add(cell)
        picks.append((f"cell-{cell}", row))

    if len(picks) < 8:
        # Final deterministic quantile-like fill from any remaining distinct loadouts.
        for row in sorted(rows, key=lambda x: (vectors[id(x)].full, x.used_space, x.weapon_name, x.pds_counts)):
            if len(picks) >= 8:
                break
            sig = signature(row)
            if sig in seen:
                continue
            seen.add(sig)
            picks.append((f"coverage-{len(picks)+1}", row))
    return picks[:8]


def sample_turn_demand(matrix: dict[str, Any], loadout: Loadout, doctrine: str, rng: XorShift64) -> int:
    config = DOCTRINES[doctrine]
    tl = loadout.tl
    total = 0
    for weapon in loadout.weapons:
        if rng.random() < config["fire"]:
            if weapon.peak_tp > weapon.standard_tp and rng.random() < config["peak"]:
                total += weapon.peak_tp
            else:
                total += weapon.standard_tp
    sensor = profile(matrix, "sensor", tl)
    high = sensor.get("activeHighTp")
    low = int(sensor.get("activeLowTp") or 0)
    roll = rng.random()
    if high is not None and roll < config["sensor_high"]:
        total += int(high)
    elif roll < config["sensor_high"] + config["sensor_low"]:
        total += low
    if loadout.ecm and rng.random() < config["ecm"]:
        total += int(profile(matrix, "ecm", tl)["fullStrengthTp"])
    if loadout.eccm and rng.random() < config["eccm"]:
        total += int(profile(matrix, "eccm", tl)["fullStrengthTp"])
    if loadout.shield and rng.random() < config["shield"]:
        cap = int(profile(matrix, "shield", tl)["tacticalRechargeCapTp"])
        if cap > 0:
            total += rng.randint(1, cap)
    if loadout.pds_total and rng.random() < config["pds"]:
        for count, power in zip(loadout.pds_counts, loadout.pds_tps):
            for _ in range(count):
                if rng.random() < 0.72:
                    total += power
    if rng.random() < config["stl_overload"]:
        total += int(profile(matrix, "stl", tl)["overloadTp"])
    return total


def _aggregate_envelope(matrix: dict[str, Any], tl: int, reactor: Reactor, rows: list[Loadout]) -> list[dict[str, Any]]:
    vectors = [(row, demand_vector(matrix, row)) for row in rows]
    result: list[dict[str, Any]] = []
    for state, supply in (("operational", reactor.operational), ("degraded", reactor.degraded), ("emergency", reactor.emergency)):
        for metric in ("routine", "offense", "defense", "full"):
            vals = [getattr(v, metric) for _, v in vectors]
            result.append(
                {
                    "tl": tl,
                    "reactor": reactor.id,
                    "reactor_technology": reactor.technology,
                    "reactor_state": state,
                    "supply_tp": supply,
                    "metric": metric,
                    "legal_builds": len(rows),
                    "median_demand": statistics.median(vals) if vals else 0,
                    "p90_demand": _quantile(vals, 0.90),
                    "p95_demand": _quantile(vals, 0.95),
                    "maximum_demand": max(vals) if vals else 0,
                    "supported_fraction": sum(v <= supply for v in vals) / len(vals) if vals else 0.0,
                }
            )
    return result


def _sensitivity(matrix: dict[str, Any], tl: int, reactor: Reactor, rows: list[Loadout], radius: int = 2) -> list[dict[str, Any]]:
    vectors = [demand_vector(matrix, row) for row in rows]
    result: list[dict[str, Any]] = []
    for supply in range(max(0, reactor.operational - radius), reactor.operational + radius + 1):
        for metric in ("routine", "offense", "defense", "full"):
            vals = [getattr(v, metric) for v in vectors]
            result.append(
                {
                    "tl": tl,
                    "candidate_operational_tp": reactor.operational,
                    "tested_supply_tp": supply,
                    "delta": supply - reactor.operational,
                    "metric": metric,
                    "supported_fraction": sum(v <= supply for v in vals) / len(vals) if vals else 0.0,
                }
            )
    return result


def _pareto_frontier(reactors: list[Reactor], available_tl: int) -> list[Reactor]:
    available = [r for r in reactors if r.tl <= available_tl]
    frontier: list[Reactor] = []
    for a in available:
        dominated = False
        for b in available:
            if b.id == a.id:
                continue
            weak = b.space <= a.space and b.operational >= a.operational and b.degraded >= a.degraded and b.emergency >= a.emergency
            strict = b.space < a.space or b.operational > a.operational or b.degraded > a.degraded or b.emergency > a.emergency
            if weak and strict:
                dominated = True
                break
        if not dominated:
            frontier.append(a)
    return sorted(frontier, key=lambda r: (r.space, -r.operational, -r.degraded, -r.emergency, r.id))


def _reactor_frontier_rows(reactors: list[Reactor]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for available_tl in range(1, 10):
        frontier_ids = {r.id for r in _pareto_frontier(reactors, available_tl)}
        for reactor in [r for r in reactors if r.tl <= available_tl]:
            rows.append(
                {
                    "available_tl": available_tl,
                    "reactor": reactor.id,
                    "reactor_tl": reactor.tl,
                    "technology": reactor.technology,
                    "family": reactor.family,
                    "status": reactor.status,
                    "space": reactor.space,
                    "operational_tp": reactor.operational,
                    "degraded_tp": reactor.degraded,
                    "emergency_tp": reactor.emergency,
                    "operational_tp_per_space": reactor.operational / reactor.space,
                    "degraded_fraction": reactor.degraded / reactor.operational if reactor.operational else 0.0,
                    "emergency_fraction": reactor.emergency / reactor.operational if reactor.operational else 0.0,
                    "pareto_frontier": reactor.id in frontier_ids,
                }
            )
    return rows


def _legacy_stack_rows(matrix: dict[str, Any], reactors: list[Reactor], maximum_pds: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for tl in range(1, 10):
        current = standard_reactor(matrix, tl)
        current_rows = enumerate_loadouts(matrix, tl, current, maximum_pds)
        by_signature = {
            (x.weapon_name, x.shield, x.ecm, x.eccm, x.pds_counts): x for x in current_rows
        }
        available = [r for r in reactors if r.tl <= tl]
        legacy = [r for r in available if r.id != current.id]
        for old in legacy:
            # Replace one current reactor with either one old or two old reactors; compare against the same non-reactor package.
            for count in (1, 2):
                supported = 0
                legal = 0
                full_supported = 0
                for row in by_signature.values():
                    nonreactor = row.used_space - current.space
                    used = nonreactor + old.space * count
                    if used > row.capacity:
                        continue
                    legal += 1
                    supply = old.operational * count
                    if supply >= current.operational:
                        supported += 1
                    if demand_vector(matrix, row).full <= supply:
                        full_supported += 1
                result.append(
                    {
                        "ship_tl": tl,
                        "current_reactor": current.id,
                        "legacy_reactor": old.id,
                        "legacy_count": count,
                        "legacy_space": old.space * count,
                        "legacy_operational_tp": old.operational * count,
                        "current_space": current.space,
                        "current_operational_tp": current.operational,
                        "same_package_legal_count": legal,
                        "supply_at_least_current_count": supported,
                        "full_demand_supported_count": full_supported,
                        "full_demand_supported_fraction": full_supported / legal if legal else 0.0,
                    }
                )
    return result



def _current_stack_rows(matrix: dict[str, Any], maximum_pds: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for tl in range(1, 10):
        current = standard_reactor(matrix, tl)
        rows = enumerate_loadouts(matrix, tl, current, maximum_pds)
        legal = 0
        full_supported = 0
        for row in rows:
            nonreactor = row.used_space - current.space
            used = nonreactor + 2 * current.space
            if used > row.capacity:
                continue
            legal += 1
            if demand_vector(matrix, row).full <= 2 * current.operational:
                full_supported += 1
        result.append({
            "tl": tl,
            "reactor": current.id,
            "single_reactor_space": current.space,
            "single_reactor_operational_tp": current.operational,
            "single_reactor_legal_build_count": len(rows),
            "same_package_two_reactor_legal_count": legal,
            "same_package_two_reactor_legal_fraction": legal / len(rows) if rows else 0.0,
            "two_reactor_space": 2 * current.space,
            "two_reactor_operational_tp": 2 * current.operational,
            "two_reactor_full_demand_supported_count": full_supported,
            "two_reactor_full_demand_supported_fraction": full_supported / legal if legal else 0.0,
            "note": "Same non-reactor package; adding the second Reactor consumes additional Space and is optional, not required progression."
        })
    return result

def _branch_support_options(matrix: dict[str, Any], tl: int) -> tuple[list[tuple[str, int, int]], list[tuple[str, int, int]]]:
    armor = [("none", 0, 0)]
    shields: list[tuple[str, int, int]] = []
    for branch in matrix.get("branches", []):
        if int(branch.get("tl", 99)) > tl or branch.get("expression") != "optional_component":
            continue
        owner = branch.get("owner")
        space = branch.get("space")
        if not isinstance(space, int):
            continue
        power = _parse_first_tp(str(branch.get("numeric", "")))
        if owner == "Armor":
            armor.append((str(branch["id"]), int(space), power))
        elif owner == "Shields":
            shields.append((str(branch["id"]), int(space), power))
    return armor, shields


def branch_hotspot(matrix: dict[str, Any], tl: int, reactor: Reactor, maximum_pds: int) -> dict[str, Any]:
    capacity = int(profile(matrix, "hull", tl)["capacity"])
    base = sum(int(profile(matrix, f, tl)["space"]) for f in ("stl", "ftl", "computer", "sensor")) + reactor.space
    shield = profile(matrix, "shield", tl)
    ecm = profile(matrix, "ecm", tl)
    eccm = profile(matrix, "eccm", tl)
    sensor = profile(matrix, "sensor", tl)
    sensor_high = sensor.get("activeHighTp")
    sensor_high = int(sensor.get("activeLowTp") or 0) if sensor_high is None else int(sensor_high)
    weapons = standard_weapon_parts(matrix, tl) + branch_weapon_parts(matrix, tl)
    armor_options, shield_supports = _branch_support_options(matrix, tl)
    shield_subsets: list[tuple[str, int, int]] = []
    for mask in range(1 << len(shield_supports)):
        selected = [shield_supports[i] for i in range(len(shield_supports)) if mask & (1 << i)]
        shield_subsets.append(("+".join(x[0] for x in selected) or "none", sum(x[1] for x in selected), sum(x[2] for x in selected)))
    best: tuple[tuple[int, int, int, int, int], dict[str, Any]] | None = None
    combinations = 0
    pds = list(pds_allocations(matrix, tl, maximum_pds))
    for i, first in enumerate(weapons):
        for second in [None] + weapons[i:]:
            package = (first,) if second is None else (first, second)
            weapon_space = sum(x.space for x in package)
            weapon_power = sum(x.peak_tp for x in package)
            for armor in armor_options:
                for shield_support in shield_subsets:
                    fixed = base + weapon_space + int(shield["space"]) + int(ecm["space"]) + int(eccm["space"]) + armor[1] + shield_support[1]
                    if fixed > capacity:
                        continue
                    for counts, pds_space, pds_tps in pds:
                        used = fixed + pds_space
                        if used > capacity:
                            continue
                        pds_power = sum(c * tp for c, tp in zip(counts, pds_tps))
                        demand = (
                            weapon_power
                            + sensor_high
                            + int(ecm["fullStrengthTp"])
                            + int(eccm["fullStrengthTp"])
                            + int(shield["tacticalRechargeCapTp"])
                            + armor[2]
                            + shield_support[2]
                            + pds_power
                            + int(profile(matrix, "stl", tl)["overloadTp"])
                        )
                        combinations += 1
                        key = (demand, used, pds_power, weapon_power, armor[2] + shield_support[2])
                        payload = {
                            "tl": tl,
                            "reactor": reactor.id,
                            "reactor_operational_tp": reactor.operational,
                            "reactor_space": reactor.space,
                            "capacity": capacity,
                            "examined_legal_branch_combinations": combinations,
                            "maximum_full_demand": demand,
                            "power_gap": demand - reactor.operational,
                            "used_space": used,
                            "free_space": capacity - used,
                            "weapons": "+".join(x.id for x in package),
                            "weapon_peak_tp": weapon_power,
                            "armor_support": armor[0],
                            "shield_support": shield_support[0],
                            "support_tp": armor[2] + shield_support[2],
                            "pds_counts": "/".join(str(x) for x in counts),
                            "pds_tp": pds_power,
                        }
                        if best is None or key > best[0]:
                            best = (key, payload)
    if best is None:
        raise PowerStudyError(f"no branch hotspot could be constructed at TL{tl}")
    payload = best[1]
    payload["examined_legal_branch_combinations"] = combinations
    return payload


def _sample_variant(
    matrix: dict[str, Any],
    loadout: Loadout,
    doctrine: str,
    reactor: Reactor,
    study: dict[str, Any],
    representative_name: str,
) -> dict[str, Any]:
    minimum = int(study["minimumTurnSamples"])
    maximum = int(study["maximumTurnSamples"])
    batch = int(study["turnSampleBatch"])
    target = float(study["targetWilsonHalfWidth"])
    seed = derive_seed(int(study["masterSeed"]), "turn-demand", loadout.tl, representative_name, doctrine)
    rng = XorShift64(seed)
    supply_values = list(range(max(0, reactor.operational - 2), reactor.operational + 3))
    shortfalls = Counter({s: 0 for s in supply_values})
    histogram: Counter[int] = Counter()
    n = 0
    while n < maximum:
        current = min(batch, maximum - n)
        for _ in range(current):
            demand = sample_turn_demand(matrix, loadout, doctrine, rng)
            histogram[demand] += 1
            for supply in supply_values:
                if demand > supply:
                    shortfalls[supply] += 1
        n += current
        if n >= minimum and _wilson_half_width(shortfalls[reactor.operational], n) <= target:
            break
    mean_demand = sum(k * v for k, v in histogram.items()) / n
    result: dict[str, Any] = {
        "tl": loadout.tl,
        "representative": representative_name,
        "doctrine": doctrine,
        "samples": n,
        "used_space": loadout.used_space,
        "capacity": loadout.capacity,
        "weapon_package": loadout.weapon_name,
        "pds_total": loadout.pds_total,
        "shield": loadout.shield,
        "ecm": loadout.ecm,
        "eccm": loadout.eccm,
        "mean_demand": mean_demand,
        "p95_demand": _hist_quantile(histogram, n, 0.95),
        "candidate_supply": reactor.operational,
        "candidate_shortfall_rate": shortfalls[reactor.operational] / n,
        "candidate_one_point_shortfall_rate": histogram.get(reactor.operational + 1, 0) / n,
        "candidate_severe_shortfall_rate": sum(v for k, v in histogram.items() if k > reactor.operational + 1) / n,
        "candidate_wilson_half_width": _wilson_half_width(shortfalls[reactor.operational], n),
        "degraded_supply": reactor.degraded,
        "degraded_shortfall_rate": sum(v for k, v in histogram.items() if k > reactor.degraded) / n,
        "emergency_supply": reactor.emergency,
        "emergency_shortfall_rate": sum(v for k, v in histogram.items() if k > reactor.emergency) / n,
    }
    for supply in supply_values:
        result[f"shortfall_supply_{supply}"] = shortfalls[supply] / n
    return result


def _hist_quantile(hist: Counter[int], total: int, p: float) -> int:
    threshold = total * p
    acc = 0
    for key in sorted(hist):
        acc += hist[key]
        if acc >= threshold:
            return key
    return max(hist) if hist else 0


def _expected_capped_binomial_uses(turns: int, probability: float, limit: int) -> float:
    if turns <= 0 or limit <= 0 or probability <= 0:
        return 0.0
    if probability >= 1:
        return float(min(turns, limit))
    expected = 0.0
    # E[min(X,L)] = sum_{k=1..L} P(X >= k), X ~ Binomial(turns,p).
    for k in range(1, limit + 1):
        below = 0.0
        for j in range(k):
            below += math.comb(turns, j) * (probability ** j) * ((1.0 - probability) ** (turns - j))
        expected += max(0.0, 1.0 - below)
    return expected


def _encounter_overload_variant(
    matrix: dict[str, Any],
    loadout: Loadout,
    doctrine: str,
    reactor: Reactor,
    study: dict[str, Any],
    representative_name: str,
    sampled: dict[str, Any],
) -> dict[str, Any]:
    encounters = int(study["encountersPerVariant"])
    turns = int(study["turnsPerEncounter"])
    one_point_rate = float(sampled["candidate_one_point_shortfall_rate"])
    severe_rate = float(sampled["candidate_severe_shortfall_rate"])
    raw_rate = one_point_rate + severe_rate
    strain_limit = int(profile(matrix, "reactor", loadout.tl).get("strainLimit", 2))
    expected_uses = _expected_capped_binomial_uses(turns, one_point_rate, strain_limit)
    residual_one_point_rate = max(0.0, (one_point_rate * turns - expected_uses) / turns)
    assisted_rate = severe_rate + residual_one_point_rate
    # The overload calculation is exact conditional on the adaptive turn-demand estimate.
    # encountersPerVariant is retained as the equivalent encounter population represented
    # in reporting, without wasting millions of extra RNG calls on a closed-form process.
    return {
        "tl": loadout.tl,
        "representative": representative_name,
        "doctrine": doctrine,
        "equivalent_encounters": encounters,
        "turns_per_encounter": turns,
        "equivalent_encounter_turns": encounters * turns,
        "raw_shortfall_rate": raw_rate,
        "one_point_shortfall_rate": one_point_rate,
        "severe_shortfall_rate": severe_rate,
        "safe_overload_assisted_shortfall_rate": assisted_rate,
        "expected_safe_overloads_per_encounter": expected_uses,
        "safe_overload_strain_limit": strain_limit,
        "method": "closed_form_binomial_over_adaptive_turn_demand_estimate",
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _group_stochastic(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[int(row["tl"])].append(row)
    result: list[dict[str, Any]] = []
    for tl, items in sorted(grouped.items()):
        candidate_supply = int(items[0]["candidate_supply"])
        supplies = sorted(int(k.removeprefix("shortfall_supply_")) for k in items[0] if k.startswith("shortfall_supply_"))
        row: dict[str, Any] = {
            "tl": tl,
            "candidate_supply": candidate_supply,
            "variants": len(items),
            "total_turn_samples": sum(int(x["samples"]) for x in items),
            "mean_demand": _mean([float(x["mean_demand"]) for x in items]),
            "mean_candidate_shortfall_rate": _mean([float(x["candidate_shortfall_rate"]) for x in items]),
            "mean_degraded_shortfall_rate": _mean([float(x["degraded_shortfall_rate"]) for x in items]),
            "mean_emergency_shortfall_rate": _mean([float(x["emergency_shortfall_rate"]) for x in items]),
        }
        for supply in supplies:
            row[f"mean_shortfall_supply_{supply}"] = _mean([float(x[f"shortfall_supply_{supply}"]) for x in items])
        result.append(row)
    return result


def run_power_calibration(repo: Path, study_path: Path, output_dir: Path) -> dict[str, Any]:
    study = load_json(study_path)
    errors = validate_study(study)
    if errors:
        raise PowerStudyError("; ".join(errors))
    matrix = load_json(repo / str(study["matrixPath"]))
    if matrix.get("schemaVersion") != "star-cluster-whole-ladder-numerical-matrix-v0.1":
        raise PowerStudyError("CP110 requires the CP109 whole-ladder numerical matrix v0.1 as its source candidate")
    max_pds = int(study["maxPdsBatteries"])
    reactors = reactor_catalog(matrix)
    frontier = _reactor_frontier_rows(reactors)
    envelope: list[dict[str, Any]] = []
    sensitivity: list[dict[str, Any]] = []
    representatives_rows: list[dict[str, Any]] = []
    stochastic: list[dict[str, Any]] = []
    overload: list[dict[str, Any]] = []
    hotspots: list[dict[str, Any]] = []
    legal_counts: dict[int, int] = {}
    cell_counts: dict[int, int] = {}
    for tl in range(1, 10):
        reactor = standard_reactor(matrix, tl)
        rows = enumerate_loadouts(matrix, tl, reactor, max_pds)
        legal_counts[tl] = len(rows)
        cell_counts[tl] = len({loadout_cell(x) for x in rows})
        envelope.extend(_aggregate_envelope(matrix, tl, reactor, rows))
        sensitivity.extend(_sensitivity(matrix, tl, reactor, rows))
        hotspots.append(branch_hotspot(matrix, tl, reactor, max_pds))
        reps = representative_loadouts(matrix, rows)
        for name, loadout in reps:
            vector = demand_vector(matrix, loadout)
            representatives_rows.append(
                {
                    "tl": tl,
                    "representative": name,
                    "used_space": loadout.used_space,
                    "capacity": loadout.capacity,
                    "weapon_package": loadout.weapon_name,
                    "pds_counts": "/".join(str(x) for x in loadout.pds_counts),
                    "shield": loadout.shield,
                    "ecm": loadout.ecm,
                    "eccm": loadout.eccm,
                    "routine_demand": vector.routine,
                    "offense_demand": vector.offense,
                    "defense_demand": vector.defense,
                    "full_demand": vector.full,
                    "reactor_operational_tp": reactor.operational,
                    "reactor_degraded_tp": reactor.degraded,
                    "reactor_emergency_tp": reactor.emergency,
                }
            )
            for doctrine in study["doctrines"]:
                sampled = _sample_variant(matrix, loadout, doctrine, reactor, study, name)
                stochastic.append(sampled)
                overload.append(_encounter_overload_variant(matrix, loadout, doctrine, reactor, study, name, sampled))
    legacy = _legacy_stack_rows(matrix, reactors, max_pds)
    current_stacking = _current_stack_rows(matrix, max_pds)
    stochastic_tl = _group_stochastic(stochastic)

    # Descriptive signals, not blocking balance targets.
    interpretation_signals: list[dict[str, Any]] = []
    for tl in range(1, 10):
        reactor = standard_reactor(matrix, tl)
        front = [x for x in frontier if x["available_tl"] == tl and x["reactor"] == reactor.id][0]
        op_full = next(x for x in envelope if x["tl"] == tl and x["reactor_state"] == "operational" and x["metric"] == "full")
        deg_routine = next(x for x in envelope if x["tl"] == tl and x["reactor_state"] == "degraded" and x["metric"] == "routine")
        stochastic_row = next(x for x in stochastic_tl if x["tl"] == tl)
        hotspot = next(x for x in hotspots if x["tl"] == tl)
        interpretation_signals.append(
            {
                "tl": tl,
                "reactor": reactor.id,
                "technology": reactor.technology,
                "pareto_frontier": bool(front["pareto_frontier"]),
                "operational_tp_per_space": front["operational_tp_per_space"],
                "full_envelope_supported_fraction": op_full["supported_fraction"],
                "degraded_routine_supported_fraction": deg_routine["supported_fraction"],
                "stochastic_candidate_shortfall_rate": stochastic_row["mean_candidate_shortfall_rate"],
                "stochastic_degraded_shortfall_rate": stochastic_row["mean_degraded_shortfall_rate"],
                "branch_hotspot_power_gap": hotspot["power_gap"],
                "note": "descriptive diagnostic only; no fixed target band is a release gate",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "reactor_frontier.csv", frontier)
    _write_csv(output_dir / "power_envelope.csv", envelope)
    _write_csv(output_dir / "operational_sensitivity.csv", sensitivity)
    _write_csv(output_dir / "representative_loadouts.csv", representatives_rows)
    _write_csv(output_dir / "stochastic_variants.csv", stochastic)
    _write_csv(output_dir / "stochastic_tl_summary.csv", stochastic_tl)
    _write_csv(output_dir / "overload_encounters.csv", overload)
    _write_csv(output_dir / "legacy_reactor_stacking.csv", legacy)
    _write_csv(output_dir / "current_reactor_stacking.csv", current_stacking)
    _write_csv(output_dir / "branch_power_hotspots.csv", hotspots)
    _write_csv(output_dir / "interpretation_signals.csv", interpretation_signals)

    total_turn_samples = sum(int(x["samples"]) for x in stochastic)
    total_encounter_turns = sum(int(x["equivalent_encounter_turns"]) for x in overload)
    result = {
        "schemaVersion": "star-cluster-power-reactor-calibration-results-v1",
        "checkpoint": "110",
        "matrixSource": str(study["matrixPath"]),
        "legalBuildCounts": {str(k): v for k, v in legal_counts.items()},
        "populationCellCounts": {str(k): v for k, v in cell_counts.items()},
        "reactorCandidates": len(reactors),
        "frontierRows": len(frontier),
        "envelopeRows": len(envelope),
        "sensitivityRows": len(sensitivity),
        "representativeLoadouts": len(representatives_rows),
        "stochasticVariants": len(stochastic),
        "turnSamples": total_turn_samples,
        "overloadEncounterVariants": len(overload),
        "overloadEncounterTurns": total_encounter_turns,
        "branchHotspotRows": len(hotspots),
        "legacyStackRows": len(legacy),
        "currentStackRows": len(current_stacking),
        "interpretationSignals": interpretation_signals,
        "automaticPromotion": False,
        "blockingBalanceTargets": False,
        "trialErrors": 0,
        "failedGates": [],
        "interpretation": "Power/Reactor calibration evidence only. Candidate numbers may be retained or revised by human review; no value is automatically promoted into the C#/Godot runtime.",
    }
    (output_dir / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
