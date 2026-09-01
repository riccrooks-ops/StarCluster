from __future__ import annotations

import csv
import json
import math
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, fields
from multiprocessing import get_context
from pathlib import Path
from itertools import product
from typing import Any, Iterable

from .rng import XorShift64, derive_seed
from .study import load_json
from .canonical_mechanics import CANONICAL_DAMAGE_MODEL, resolve_layered_damage
from .tactical_package_utility import TacticalPackageCandidate, choose_tactical_package

MAP_RADIUS = 5
MAX_TURNS = 60
START_FUEL = 100
DAMAGE_MODEL = "layered_defense_hull_only"


@dataclass(frozen=True, slots=True)
class EcologyBuild:
    id: str
    tl: int
    archetype: str
    weapon_family: str
    main_count: int
    reactor_count: int
    shield: bool
    ecm: bool
    eccm: bool
    pds_family: str | None
    shield_hardener: bool
    capacity: int
    combat_space: int
    mission_aux_space: int
    missile_payload: str = "GP"
    armor_profile: str = "mainline"
    auxiliary_profiles: tuple[str, ...] = ()
    # Research-only installed renewable Tactical Power that is additive rather
    # than multiplied by main-Reactor count. CP162 uses this for Auxiliary
    # Reactor calibration; all historical builds retain the default zero.
    auxiliary_power_tp: int = 0
    auxiliary_reactor_count: int = 0

    @property
    def used_space(self) -> int:
        return self.combat_space + self.mission_aux_space


@dataclass(frozen=True, slots=True)
class EcologyVariant:
    id: str
    tl: int
    side_a: EcologyBuild
    side_b: EcologyBuild
    movement_order: str
    geometry: str = "radius5_axial_opposite_edges"
    population: str = "same_tl_frontier_exact_fill"
    start_q_a: int = -MAP_RADIUS
    start_q_b: int = MAP_RADIUS
    max_turns: int = MAX_TURNS
    scenario_group: str = "primary_ecology"
    perturbation: str = "baseline"
    # Optional physical-ship identities used by the CP126 full-map consumer.
    # Historical consumers ignore them. Keeping identity separate from Side A/B
    # allows side-swap symmetry and common-random-number sensitivity studies,
    # including matchups between two ships with the same build ID.
    physical_id_a: str = ""
    physical_id_b: str = ""


@dataclass(slots=True)
class SideTelemetry:
    movement_hexes: int = 0
    movement_fuel: int = 0
    map_boundary_blocks: int = 0
    range_changes: int = 0
    track_driven_closure_hexes: int = 0
    min_range: int = 10
    passive_turns: int = 0
    active_low_turns: int = 0
    active_high_turns: int = 0
    sensor_overload_requests: int = 0
    sensor_overload_activations: int = 0
    firm_track_turns: int = 0
    approximate_track_turns: int = 0
    direct_firm_shots: int = 0
    direct_approximate_shots: int = 0
    direct_standard_range_shots: int = 0
    direct_extended_range_shots: int = 0
    direct_stacked_penalty_shots: int = 0
    direct_accuracy_penalty_pp_total: int = 0
    energy_low_shots: int = 0
    energy_standard_shots: int = 0
    energy_overload_shots: int = 0
    energy_overload_strain_added: int = 0
    energy_max_strain: int = 0
    no_track_turns: int = 0
    ecm_active_turns: int = 0
    eccm_active_turns: int = 0
    ecm_downgrade_events: int = 0
    eccm_restore_events: int = 0
    burnthrough_preservation_events: int = 0
    ecm_overload_requests: int = 0
    ecm_overload_activations: int = 0
    eccm_overload_requests: int = 0
    eccm_overload_activations: int = 0
    reactor_overload_requests: int = 0
    reactor_overload_activations: int = 0
    reactor_overload_power_unlocked: int = 0
    reactor_max_strain: int = 0
    stl_overload_requests: int = 0
    stl_overload_activations: int = 0
    power_available_total: int = 0
    power_spent_total: int = 0
    power_sensor: int = 0
    power_ecm: int = 0
    power_eccm: int = 0
    power_pds: int = 0
    power_weapons: int = 0
    power_shield_recharge: int = 0
    power_shield_hardener: int = 0
    power_aux_energized_armor: int = 0
    power_aux_field_stabilizer: int = 0
    power_shortfall_events: int = 0
    weapon_power_shortfalls: int = 0
    pds_power_shortfalls: int = 0
    acquisition_power_shortfalls: int = 0
    shield_recharge_opportunities: int = 0
    shield_recharge_denied_by_reserve: int = 0
    shield_base_restored: int = 0
    shield_tactical_restored: int = 0
    shield_reconstitutions: int = 0
    armor_regen_opportunities: int = 0
    armor_regen_tp_spent: int = 0
    armor_regen_restored: int = 0
    armor_regen_reserve_initial: int = 0
    armor_regen_reserve_spent: int = 0
    armor_regen_reserve_exhaustions: int = 0
    armor_regen_denied_exhausted: int = 0
    shield_collapse_events: int = 0
    armor_collapse_events: int = 0
    first_shield_damage_turn: int = 0
    first_shield_collapse_turn: int = 0
    first_armor_damage_turn: int = 0
    first_armor_collapse_turn: int = 0
    first_hull_damage_turn: int = 0
    direct_shots: int = 0
    direct_hits: int = 0
    missile_launches: int = 0
    missile_terminal_arrivals: int = 0
    missile_guidance_attempts: int = 0
    missile_hits: int = 0
    pds_attempts: int = 0
    pds_intercepts: int = 0
    pds_range_one_attempts: int = 0
    pds_range_one_intercepts: int = 0
    pds_overcharge_attempts: int = 0
    pds_overcharge_strain_added: int = 0
    pds_max_strain: int = 0
    raw_damage_on_hit: int = 0
    shield_armor_prevented: int = 0
    shield_absorbed: int = 0
    armor_prevented: int = 0
    armor_integrity_damage: int = 0
    armor_protection_damage: int = 0
    hull_damage: int = 0
    direct_raw_damage: int = 0
    direct_hull_damage: int = 0
    missile_raw_damage: int = 0
    missile_hull_damage: int = 0
    payload_shield_bonus_damage: int = 0
    shield_recharge_suppressed: int = 0
    payload_switches: int = 0
    payload_gp_launches: int = 0
    payload_specialist_launches: int = 0
    kinetic_specialist_shots: int = 0
    assessment_shield_absorption_observed: int = 0
    assessment_no_penetration_observed: int = 0
    assessment_armor_contact_observed: int = 0
    assessment_hull_penetration_observed: int = 0
    assessment_shield_absent_observed: int = 0
    direct_fire_eligible_actions: int = 0
    missile_launch_eligible_actions: int = 0
    damage_packets_resolved: int = 0
    def_res_packets: int = 0
    shield_deflections: int = 0
    shield_def_effective_pp_total: float = 0.0
    armor_resisted_damage: float = 0.0
    shield_penetration_bypassed: int = 0
    armor_penetration_bypassed: int = 0
    damage_control_attempts: int = 0
    damage_control_successes: int = 0
    damage_control_kits_consumed: int = 0
    damage_control_tp_spent: int = 0
    damage_control_hull_queued: int = 0
    damage_control_hull_restored: int = 0
    aux_shield_battery_discharges: int = 0
    aux_shield_battery_restored: int = 0
    aux_shield_battery_wasted: int = 0
    aux_ablative_absorbed: int = 0
    aux_ablative_depleted_events: int = 0
    aux_energized_active_turns: int = 0
    aux_field_stabilizer_active_turns: int = 0
    aux_damage_control_bonus_attempts: int = 0
    cp146_weapon_core_funded_turns: int = 0
    cp146_weapon_core_starved_turns: int = 0
    cp146_active_sensor_default_turns: int = 0
    cp146_passive_sensor_fallback_turns: int = 0
    cp146_unknown_opponent_turns: int = 0
    cp146_known_opponent_turns: int = 0
    cp146_pds_unknown_readiness_turns: int = 0
    cp146_pds_imminent_threat_turns: int = 0
    cp146_pds_irrelevant_suppressed_turns: int = 0
    cp146_hardener_unknown_readiness_turns: int = 0
    cp146_hardener_relevant_turns: int = 0
    cp146_hardener_irrelevant_suppressed_turns: int = 0
    cp146_held_main_declarations: int = 0
    cp146_held_main_attempts: int = 0
    cp146_held_main_intercepts: int = 0
    cp146_held_main_unused: int = 0
    cp147_package_decisions: int = 0
    cp147_direct_package_selections: int = 0
    cp147_held_package_selections: int = 0
    cp147_pds_package_selections: int = 0
    cp147_passive_utility_fallbacks: int = 0
    cp147_recovery_reserve_turns: int = 0
    cp147_recovery_reserved_tp: int = 0
    cp147_offense_utility_milli: int = 0
    cp147_defense_utility_milli: int = 0
    cp147_inbound_threat_turns: int = 0
    cp147_observed_threat_turns: int = 0
    cp147_terminal_hull_risk_turns: int = 0
    cp147_sole_main_defensive_diversions: int = 0
    cp147_sole_main_diversions_without_hull_risk: int = 0


@dataclass(slots=True)
class SideState:
    build: EcologyBuild
    q: int
    hull: int
    hull_max: int
    armor_integrity: int
    armor_protection: int
    armor_max: int
    shield: int
    shield_max: int
    fuel: int = START_FUEL
    weapon_ammo: int | None = None
    pds_ammo: int | None = None
    repair_kits_remaining: int = 0
    pending_hull_repair: int = 0
    armor_regen_reserve_remaining: int = 0
    armor_regen_reserve_exhaustion_recorded: bool = False
    reactor_strain: int = 0
    energy_weapon_strain: int = 0
    pds_strain: int = 0
    contact: bool = False
    last_track: str = "None"
    demonstrated_range: int = 0
    recharge_suppression_pending: int = 0
    observed_shield_absorption: bool = False
    observed_no_penetration_streak: int = 0
    observed_armor_contact: bool = False
    observed_hull_penetration: bool = False
    observed_no_shield_effect_latest: bool = False
    last_payload_id: str = ""
    known_opponent_weapon_family: str | None = None
    known_opponent_weapon_turn: int = 0
    known_opponent_missile_profile: str | None = None
    known_opponent_missile_expected_raw_per_subflight: float = 0.0
    known_opponent_missile_pds_penalty_pp: int = 0
    known_opponent_missile_subflights: int = 0
    cp147_inbound_subflights: int = 0
    cp147_inbound_expected_raw_total: float = 0.0
    cp147_inbound_pds_penalty_pp: int = 0
    cp147_terminal_threats: tuple[tuple[float, int, float], ...] = ()
    shield_battery_charges_remaining: int = 0
    ablative_integrity: float = 0.0
    ablative_max: float = 0.0
    telemetry: SideTelemetry = field(default_factory=SideTelemetry)


@dataclass(slots=True)
class MissileState:
    owner: str
    eta: int
    damage: int
    spen: int
    apen: int
    guidance: int
    packets: int = 1
    pds_intercept_penalty_pp: int = 0
    profile_id: str = "GP"


@dataclass(frozen=True, slots=True)
class EcologyTrialResult:
    winner: str
    unresolved: bool
    turns: int
    final_range: int
    min_range: int
    hull_a: int
    hull_b: int
    armor_a: int
    armor_b: int
    shield_a: int
    shield_b: int
    side_a: SideTelemetry
    side_b: SideTelemetry
    error: str = ""


class CandidateMatrix:
    def __init__(
        self,
        repo: Path,
        matrix_relative_path: str = "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_1.json",
    ):
        self.path = repo / matrix_relative_path
        self.doc = load_json(self.path)
        self.profiles = self.doc["profiles"]
        self.branches = {row["id"]: row for row in self.doc["branches"]}

    def p(self, family: str, tl: int) -> dict[str, Any]:
        return self.profiles[family][str(tl)]

    def capacity(self, tl: int) -> int:
        return int(self.p("hull", tl)["capacity"])

    def space(self, family: str, tl: int) -> int:
        return int(self.p(family, tl).get("space", 0))

    def weapon_profile(self, family: str, tl: int) -> dict[str, Any]:
        key = {"Kinetic": "kinetic_main", "Energy": "energy_main", "Missile": "missile_delivery"}[family]
        return self.p(key, tl)

    def pds_profile(self, family: str, tl: int) -> dict[str, Any]:
        key = {"Kinetic": "kinetic_pds", "Energy": "energy_pds", "AMM": "amm_pds"}[family]
        return self.p(key, tl)


ARCHETYPE_SPECS = (
    # name, main_count, reactor_count, shield, ecm, eccm, pds, hardener
    ("balanced", 1, 1, True, True, True, None, False),
    ("dual-main", 2, 1, False, False, True, None, False),
    ("dual-reactor", 1, 2, False, True, False, None, False),
)


def _specialist_spec(family: str, tl: int):
    if family == "Kinetic":
        return ("ew-specialist", 1, 1, False, True, True, "Kinetic", False)
    if family == "Energy":
        return ("defense-specialist", 1, 1, True, False, True, "Energy", tl >= 3)
    return ("missile-defense", 1, 1, True, False, True, "AMM", tl >= 3)


def build_space(matrix: CandidateMatrix, tl: int, family: str, main_count: int, reactor_count: int,
                shield: bool, ecm: bool, eccm: bool, pds_family: str | None, hardener: bool) -> int:
    total = (
        main_count * matrix.space({"Kinetic": "kinetic_main", "Energy": "energy_main", "Missile": "missile_delivery"}[family], tl)
        + reactor_count * matrix.space("reactor", tl)
        + matrix.space("stl", tl)
        + matrix.space("ftl", tl)
        + matrix.space("computer", tl)
        + matrix.space("sensor", tl)
    )
    if shield:
        total += matrix.space("shield", tl)
    if ecm:
        total += matrix.space("ecm", tl)
    if eccm:
        total += matrix.space("eccm", tl)
    if pds_family:
        total += matrix.space({"Kinetic": "kinetic_pds", "Energy": "energy_pds", "AMM": "amm_pds"}[pds_family], tl)
    if hardener:
        total += int(matrix.branches["shield-hardener"]["space"])
    return total


def generate_primary_builds(matrix: CandidateMatrix) -> list[EcologyBuild]:
    builds: list[EcologyBuild] = []
    for tl in range(1, 10):
        for family in ("Kinetic", "Energy", "Missile"):
            specs = list(ARCHETYPE_SPECS) + [_specialist_spec(family, tl)]
            for name, main_count, reactor_count, shield, ecm, eccm, pds_family, hardener in specs:
                combat_space = build_space(matrix, tl, family, main_count, reactor_count, shield, ecm, eccm, pds_family, hardener)
                capacity = matrix.capacity(tl)
                if combat_space > capacity:
                    continue
                mission_aux_space = capacity - combat_space
                bid = f"tl{tl}-{family.lower()}-{name}"
                builds.append(EcologyBuild(
                    bid, tl, name, family, main_count, reactor_count, shield, ecm, eccm,
                    pds_family, hardener, capacity, combat_space, mission_aux_space,
                ))
    builds.sort(key=lambda x: x.id)
    return builds


def generate_primary_variants(builds: list[EcologyBuild]) -> list[EcologyVariant]:
    variants: list[EcologyVariant] = []
    by_tl: dict[int, list[EcologyBuild]] = {}
    for b in builds:
        by_tl.setdefault(b.tl, []).append(b)
    for tl in range(1, 10):
        group = sorted(by_tl.get(tl, []), key=lambda x: x.id)
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                base = f"tl{tl}-{a.id}__vs__{b.id}"
                variants.append(EcologyVariant(base + "-afirst", tl, a, b, "SideAFirst"))
                variants.append(EcologyVariant(base + "-bfirst", tl, a, b, "SideBFirst"))
    return variants


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-same-tl-build-ecology-v0.1":
        errors.append("schemaVersion")
    if doc.get("checkpoint") != "111":
        errors.append("checkpoint")
    if doc.get("damageModel") != DAMAGE_MODEL:
        errors.append("damageModel")
    if doc.get("primaryPopulation") != "same_tl_frontier_exact_fill":
        errors.append("primaryPopulation")
    if doc.get("missionAuxFiller", {}).get("tacticalEffect") is not False:
        errors.append("missionAuxFiller.tacticalEffect")
    if doc.get("mixedTlPopulation", {}).get("executed") is not False:
        errors.append("mixedTlPopulation.executed")
    trials = doc.get("trialsPerVariant")
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 1:
        errors.append("trialsPerVariant")
    return errors


def _weapon(matrix: CandidateMatrix, build: EcologyBuild) -> dict[str, Any]:
    p = matrix.weapon_profile(build.weapon_family, build.tl)
    if build.weapon_family == "Kinetic":
        max_range = int(p.get("maxRange", p.get("range", 0)))
        standard_range = int(p.get("standardRange", max_range))
        return {
            "family": "Kinetic", "count": build.main_count, "range": max_range, "standard_range": standard_range, "max_range": max_range,
            "accuracy": int(p["accuracyPp"]), "damage": int(p["damage"]), "spen": int(p["spen"]), "apen": int(p["apen"]),
            "power": int(p["firingTp"]), "ammo": int(p["ammo"]),
        }
    if build.weapon_family == "Energy":
        max_range = int(p.get("maxRange", p.get("range", 0)))
        standard_range = int(p.get("standardRange", max_range))
        overload_power = int(p.get("overloadTp", p.get("highTp", math.ceil(int(p["standardTp"]) * 1.5))))
        overload_damage = int(p.get("overloadDamage", p.get("highDamage", math.ceil(int(p["standardDamage"]) * 1.5))))
        return {
            "family": "Energy", "count": build.main_count, "range": max_range, "standard_range": standard_range, "max_range": max_range,
            "accuracy": int(p["accuracyPp"]), "spen": int(p["spen"]), "apen": int(p["apen"]), "ammo": None,
            "standard_damage": int(p["standardDamage"]), "standard_power": int(p["standardTp"]),
            "overload_damage": overload_damage, "overload_power": overload_power,
            "high_damage": overload_damage, "high_power": overload_power,
            "low_damage": int(p["lowDamage"]), "low_power": int(p["lowTp"]),
            "strain_limit": int(p.get("strainLimit", 2)), "overload_adds_strain": bool(p.get("overloadAddsStrain", True)),
        }
    # Historical matrices stored guidance and warhead characteristics directly on
    # missile_delivery.  CP123+ separates delivery, guidance/seeker, GP warhead,
    # and Swarmer Flight profiles.  Preserve the historical shape when present,
    # otherwise compose the executable profile from the separated authorities.
    if "warheadDamage" in p:
        return {
            "family": "Missile", "count": build.main_count, "range": int(p["range"]), "accuracy": 0,
            "damage": int(p["warheadDamage"]), "spen": int(p["spen"]), "apen": int(p["apen"]), "power": int(p["launchTp"]),
            "ammo": int(p["flights"]), "missile_move": int(p["missileMove"]), "guidance": int(p["guidanceBaseHit"]),
            "terminal_seeker": bool(p.get("terminalSeeker", False)), "local_approx": bool(p.get("localApproxCanAcquire", False)),
            "packets": 1, "pds_intercept_penalty_pp": 0, "profile_id": "GP",
        }
    guidance = matrix.p("missile_guidance", build.tl)
    payload = str(getattr(build, "missile_payload", "GP") or "GP")
    if payload.lower() == "swarmer":
        sw = matrix.p("missile_swarmer", build.tl)
        if not bool(sw.get("available", False)):
            raise ValueError(f"Swarmer Missile Flight unavailable at TL{build.tl}")
        if getattr(matrix, "damage_model", None) == "def-res-v1":
            return {
                "family": "Missile", "count": build.main_count, "range": int(p["range"]), "accuracy": 0,
                "damage": float(sw["packetDamage"]), "spen": int(sw["spen"]), "apen": int(sw["apen"]), "power": int(p["launchTp"]),
                "ammo": int(p["flights"]), "missile_move": int(p["missileMove"]),
                "guidance": int(guidance["guidanceBaseHit"]),
                "terminal_seeker": bool(guidance.get("terminalSeeker", False)), "local_approx": bool(guidance.get("localApproxCanAcquire", False)),
                "packets": 1, "subflights": int(sw.get("subFlightCount", 2)),
                "pds_intercept_penalty_pp": 0, "profile_id": "Swarmer",
            }
        return {
            "family": "Missile", "count": build.main_count, "range": int(p["range"]), "accuracy": 0,
            "damage": int(sw["packetDamage"]), "spen": int(sw["spen"]), "apen": int(sw["apen"]), "power": int(p["launchTp"]),
            "ammo": int(p["flights"]), "missile_move": int(p["missileMove"]),
            "guidance": max(1, min(99, int(guidance["guidanceBaseHit"]) + int(sw["terminalGuidanceBonusPp"]))),
            "terminal_seeker": bool(guidance.get("terminalSeeker", False)), "local_approx": bool(guidance.get("localApproxCanAcquire", False)),
            "packets": int(sw["packetCount"]), "pds_intercept_penalty_pp": int(sw["pdsInterceptPenaltyPp"]), "profile_id": "Swarmer",
        }
    gp = matrix.p("missile_gp_warhead", build.tl)
    return {
        "family": "Missile", "count": build.main_count, "range": int(p["range"]), "accuracy": 0,
        "damage": int(gp["damage"]), "spen": int(gp["spen"]), "apen": int(gp["apen"]), "power": int(p["launchTp"]),
        "ammo": int(p["flights"]), "missile_move": int(p["missileMove"]), "guidance": int(guidance["guidanceBaseHit"]),
        "terminal_seeker": bool(guidance.get("terminalSeeker", False)), "local_approx": bool(guidance.get("localApproxCanAcquire", False)),
        "packets": 1, "pds_intercept_penalty_pp": 0, "profile_id": "GP",
    }


def _preferred_weapon_power(w: dict[str, Any]) -> int:
    if w["family"] == "Energy":
        return w["standard_power"] * w["count"]
    return w["power"] * w["count"]


def _cp158_aux_rows(matrix: CandidateMatrix, build: EcologyBuild) -> list[dict[str, Any]]:
    registry = getattr(matrix, "cp158_aux_profiles", {})
    return [registry[x] for x in build.auxiliary_profiles if x in registry]

def _cp158_aux_kind(matrix: CandidateMatrix, build: EcologyBuild, kind: str) -> dict[str, Any] | None:
    return next((r for r in _cp158_aux_rows(matrix, build) if r.get("kind") == kind), None)

def _armor_profile(matrix: CandidateMatrix, build: EcologyBuild) -> dict[str, Any]:
    if build.armor_profile == "mainline":
        row = dict(matrix.p("armor", build.tl))
        crystal = _cp158_aux_kind(matrix, build, "crystalline_armor")
        if crystal is not None:
            row["ai"] = int(row["ai"]) + int(crystal.get("capacity_bonus", 0))
            row["baseRegeneration"] = 0
            row["tacticalRegenerationPerTp"] = 0
            row["tacticalRegenerationCapTp"] = 0
            row["combatRegenerationReserveAi"] = 0
            row["cp158ArmorResBonusPp"] = float(crystal.get("res_bonus_pp", 0))
            row["technology"] = "CP158 Crystalline Armor candidate"
        return row
    if build.armor_profile == "A_b1":
        if build.tl != 6:
            raise ValueError("A_b1 Crystalline Armor is numerically seeded only at TL6 in the CP133 candidate baseline")
        seeds = matrix.doc.get("candidateBranchSeeds", [])
        seed = next((row for row in seeds if row.get("id") == "A_b1"), None)
        if seed is None:
            raise ValueError("A_b1 candidate seed is missing from the numerical authority")
        row = dict(seed["tl6"])
        row.update({"tl": 6, "space": 0, "baseRegeneration": 0, "tacticalRegenerationPerTp": 0,
                    "technology": seed.get("name", "Crystalline composite armor")})
        return row
    raise ValueError(f"unknown armor profile {build.armor_profile!r}")


def _create_side(matrix: CandidateMatrix, build: EcologyBuild, q: int) -> SideState:
    hull = matrix.p("hull", build.tl)
    armor = _armor_profile(matrix, build)
    shield = matrix.p("shield", build.tl)
    weapon = _weapon(matrix, build)
    pds_ammo = None
    if build.pds_family:
        ammo = matrix.pds_profile(build.pds_family, build.tl).get("ammo")
        pds_ammo = None if ammo is None else int(ammo)
    dc = matrix.p("damage_control", build.tl) if "damage_control" in matrix.profiles else {}
    # Legacy matrices before CP137 omit the reserve field and therefore retain
    # their historical unlimited tactical-regeneration semantics. CP137+ profiles
    # encode an explicit finite reserve (or zero for non-regenerative Armor).
    reserve = int(armor["combatRegenerationReserveAi"]) if "combatRegenerationReserveAi" in armor else -1
    aux_rows = _cp158_aux_rows(matrix, build)
    shield_bonus = sum(int(r.get("capacity_bonus", 0)) for r in aux_rows if r.get("kind") == "shield_booster")
    weapon_ammo = None if weapon["ammo"] is None else int(weapon["ammo"]) * build.main_count
    if weapon_ammo is not None:
        if weapon["family"] == "Kinetic": weapon_ammo += sum(int(r.get("ammo_bonus",0)) for r in aux_rows if r.get("kind") == "kinetic_magazine")
        if weapon["family"] == "Missile": weapon_ammo += sum(int(r.get("ammo_bonus",0)) for r in aux_rows if r.get("kind") == "missile_magazine")
    battery_charges = sum(int(r.get("charges",0)) for r in aux_rows if r.get("kind") == "shield_battery")
    ablative = sum(float(r.get("ablative_integrity",0)) for r in aux_rows if r.get("kind") == "ablative_armor")
    extra_kits = sum(int(r.get("extra_repair_kits",0)) for r in aux_rows if r.get("kind") == "repair_drone")
    shield_cap = (int(shield["capacity"]) + shield_bonus) if build.shield else 0
    side = SideState(
        build=build, q=q, hull=int(hull["hullPoints"]), hull_max=int(hull["hullPoints"]), armor_integrity=int(armor["ai"]),
        armor_protection=int(armor["ap"]), armor_max=int(armor["ai"]), shield=shield_cap, shield_max=shield_cap,
        weapon_ammo=weapon_ammo,
        pds_ammo=pds_ammo, repair_kits_remaining=int(dc.get("preparedRepairKits", 0))+extra_kits,
        armor_regen_reserve_remaining=reserve, shield_battery_charges_remaining=battery_charges,
        ablative_integrity=ablative, ablative_max=ablative,
    )
    side.telemetry.armor_regen_reserve_initial = reserve
    return side


def _range(a: SideState, b: SideState) -> int:
    return abs(a.q - b.q)


def _max_normal_firm(matrix: CandidateMatrix, build: EcologyBuild) -> int:
    s = matrix.p("sensor", build.tl)
    vals = [int(s["passiveFirm"]), int(s["activeLowFirm"])]
    if s.get("activeHighFirm") is not None:
        vals.append(int(s["activeHighFirm"]))
    return max(vals)


def _desired_range(matrix: CandidateMatrix, side: SideState) -> int:
    w = _weapon(matrix, side.build)
    return min(int(w["range"]), _max_normal_firm(matrix, side.build))


def _move_one(side: SideState, target: SideState, matrix: CandidateMatrix, contact_before: bool) -> None:
    t = side.telemetry
    old_q = side.q
    old_range = _range(side, target)
    if side.fuel < 2:
        return
    if not contact_before:
        if side.q < 0:
            desired_q = min(0, side.q + 1)
        elif side.q > 0:
            desired_q = max(0, side.q - 1)
        else:
            desired_q = side.q
        move = abs(desired_q - side.q)
    else:
        move_cap = int(matrix.p("stl", side.build.tl)["move"])
        current = old_range
        # Standing doctrine: physical/preferred weapon range is not attack eligibility.
        # If contact exists but the previous legal acquisition window still failed to
        # produce Firm, continue closing on the next Movement decision rather than
        # holding indefinitely at a range where the ship cannot attack.
        track_driven_closure = side.last_track != "Firm"
        desired = 0 if track_driven_closure else _desired_range(matrix, side)
        if current > desired:
            direction = 1 if target.q > side.q else -1
            move = min(move_cap, current - desired)
            desired_q = side.q + direction * move
            # Do not cross the target; same-hex is legal.
            if direction > 0:
                desired_q = min(desired_q, target.q)
            else:
                desired_q = max(desired_q, target.q)
            if track_driven_closure:
                t.track_driven_closure_hexes += abs(desired_q - side.q)
        elif current < desired:
            direction = -1 if target.q > side.q else 1
            move = min(move_cap, desired - current)
            desired_q = side.q + direction * move
        else:
            desired_q = side.q
            move = 0
    bounded_q = max(-MAP_RADIUS, min(MAP_RADIUS, desired_q))
    if bounded_q != desired_q:
        t.map_boundary_blocks += 1
    max_by_fuel = side.fuel // 2
    actual_move = min(abs(bounded_q - side.q), max_by_fuel)
    if actual_move:
        direction = 1 if bounded_q > side.q else -1
        side.q += direction * actual_move
        side.fuel -= actual_move * 2
        t.movement_hexes += actual_move
        t.movement_fuel += actual_move * 2
    new_range = _range(side, target)
    if new_range != old_range:
        t.range_changes += 1
    t.min_range = min(t.min_range, new_range)


LEGACY_COMBAT_DOCTRINE = "cp145_legacy"
CONTEXTUAL_COMBAT_DOCTRINE = "cp146_contextual"
UTILITY_COMBAT_DOCTRINE = "cp147_tactical_utility"


def _base_sensor_mode(matrix: CandidateMatrix, side: EcologyBuild, range_hex: int, power_budget: int):
    s = matrix.p("sensor", side.tl)
    modes: list[tuple[str, int, int, int]] = [("passive", int(s["passiveFirm"]), int(s["passiveApprox"]), 0)]
    modes.append(("low", int(s["activeLowFirm"]), int(s["activeLowApprox"]), int(s["activeLowTp"])))
    if s.get("activeHighFirm") is not None and s.get("activeHighTp") is not None:
        modes.append(("high", int(s["activeHighFirm"]), int(s["activeHighApprox"]), int(s["activeHighTp"])))
    firm = [m for m in modes if range_hex <= m[1] and m[3] <= power_budget]
    if firm:
        return min(firm, key=lambda m: (m[3], 0 if m[0] == "passive" else 1))
    approx = [m for m in modes if range_hex <= m[2] and m[3] <= power_budget]
    if approx:
        return min(approx, key=lambda m: (m[3], -m[2]))
    affordable = [m for m in modes if m[3] <= power_budget]
    return max(affordable, key=lambda m: (m[2], m[1], -m[3])) if affordable else modes[0]


def _track_from_mode(mode, range_hex: int) -> str:
    _, firm, approx, _ = mode
    if range_hex <= firm:
        return "Firm"
    if range_hex <= approx:
        return "Approximate"
    return "None"


def _pds_profile(matrix: CandidateMatrix, side: EcologyBuild):
    if not side.pds_family:
        return None
    return matrix.pds_profile(side.pds_family, side.tl)


def _pds_readiness_options(profile: dict[str, Any] | None, side: SideState) -> list[tuple[str, int, int]]:
    """Return legal (id, TP, RC) states for the current PDS profile.

    Historical profiles expose only reactionCapacity/readinessTp.  CP154 research
    candidates may additionally expose explicit rc1Tp/rc2Tp/rc3Tp tiers plus a
    safeReactionCapacity and extraReactionStrain.  The latter lets Energy-PDS
    buy an extra reaction with TP while the safe-only AI refuses to cross the
    PDS Strain Limit.
    """
    if profile is None:
        return [("pds0", 0, 0)]
    max_rc=max(0,int(profile.get("reactionCapacity",0)))
    if side.pds_ammo is not None:
        max_rc=min(max_rc,max(0,int(side.pds_ammo)))
    out=[("pds0",0,0)]
    explicit=any(k in profile for k in ("rc1Tp","rc2Tp","rc3Tp"))
    if explicit:
        safe_rc=max(0,int(profile.get("safeReactionCapacity",max_rc)))
        strain_per=max(0,int(profile.get("extraReactionStrain",0)))
        strain_limit=max(0,int(profile.get("strainLimit",0)))
        for rc in range(1,max_rc+1):
            key=f"rc{rc}Tp"
            if key not in profile or profile.get(key) is None: continue
            if rc>safe_rc and strain_per>0 and int(side.pds_strain)>=strain_limit:
                continue
            out.append((f"pds{rc}",max(0,int(profile[key])),rc))
    else:
        cost=max(0,int(profile.get("readinessTp",0)))
        if max_rc>0: out.append(("pdsfull",cost,max_rc))
        if max_rc>=2 and cost>=2: out.append(("pdspartial",1,1))
    # Remove duplicate TP/RC states while retaining deterministic order.
    seen=set(); dedup=[]
    for row in out:
        key=(row[1],row[2])
        if key in seen: continue
        seen.add(key); dedup.append(row)
    return dedup


def _pds_max_attempts_per_flight(profile: dict[str, Any] | None, planned_rc: int) -> int:
    if profile is not None and bool(profile.get("rangeOneAttempt",False)) and int(planned_rc)>=3:
        return 3
    return min(2,max(0,int(planned_rc)))


def _missile_threat(target: SideState, inbound: int) -> bool:
    # Match the accepted C# preserve-combat-package doctrine: a known Missile-family
    # opponent is itself enough to justify PDS readiness, even before the first flight
    # is already on the map. This prevents one-turn terminal flights from bypassing
    # the legal terminal-defense window merely because they were launched this turn.
    return inbound > 0 or target.build.weapon_family == "Missile"


def _reserve_estimate(matrix: CandidateMatrix, side: SideState, target: SideState, inbound: int, range_hex: int) -> int:
    # Preserve the immediate combat package before optional ECM or tactical recharge.
    w = _weapon(matrix, side.build)
    reserve = _preferred_weapon_power(w) if range_hex <= int(w["range"]) else 0
    pds = _pds_profile(matrix, side.build)
    if _missile_threat(target, inbound) and pds:
        reserve += int(pds["readinessTp"])
    s = matrix.p("sensor", side.build.tl)
    if range_hex > int(s["passiveFirm"]):
        reserve += int(s["activeLowTp"])
    return reserve


def _cp146_core_reserve_estimate(matrix: CandidateMatrix, side: SideState, range_hex: int) -> int:
    w = _weapon(matrix, side.build)
    weapon = _preferred_weapon_power(w) if range_hex <= int(w["range"]) else 0
    sensor = matrix.p("sensor", side.build.tl)
    active_low = int(sensor.get("activeLowTp", 0))
    # Active Sensor plus the preferred normal weapon package is the CP146 core.
    return weapon + active_low


def _begin_turn_recharge(matrix: CandidateMatrix, side: SideState, target: SideState, inbound: int,
                         combat_doctrine: str = LEGACY_COMBAT_DOCTRINE) -> tuple[int, int]:
    """Return (base reactor power after recharge, tactical recharge TP spent)."""
    if side.pending_hull_repair > 0 and side.hull > 0:
        restored = min(side.pending_hull_repair, max(0, side.hull_max - side.hull))
        side.hull += restored
        side.telemetry.damage_control_hull_restored += restored
        side.pending_hull_repair = 0
    r = matrix.p("reactor", side.build.tl)
    total = int(r["operationalTp"]) * side.build.reactor_count + int(getattr(side.build, "auxiliary_power_tp", 0))
    t = side.telemetry
    t.power_available_total += total
    if not side.build.shield:
        return total, 0
    # CP139 research candidate: once SC reaches zero the field is collapsed for
    # the remainder of the engagement. The CP138/default path remains restartable.
    if getattr(matrix, "damage_model", None) == "def-res-v1" and side.shield <= 0:
        return total, 0
    sp = matrix.p("shield", side.build.tl)
    battery = _cp158_aux_kind(matrix, side.build, "shield_battery")
    if battery is not None and side.shield_battery_charges_remaining > 0 and 0 < side.shield <= side.shield_max * float(battery.get("trigger_fraction", 0.5)):
        restore = int(battery.get("restore", 0)); missing = max(0, side.shield_max - side.shield)
        if restore > 0 and missing > 0:
            actual=min(restore,missing); side.shield += actual; side.shield_battery_charges_remaining -= 1
            t.aux_shield_battery_discharges += 1; t.aux_shield_battery_restored += actual; t.aux_shield_battery_wasted += max(0,restore-actual)
    suppression = max(0, int(side.recharge_suppression_pending)) if side.shield < side.shield_max else 0
    if suppression:
        side.recharge_suppression_pending = 0
    before = side.shield
    base_request = min(side.shield_max - side.shield, int(sp["baseRecharge"]))
    base_suppressed = min(base_request, suppression)
    base_restore = base_request - base_suppressed
    side.shield += base_restore
    t.shield_base_restored += base_restore
    t.shield_recharge_suppressed += base_suppressed
    suppression -= base_suppressed
    if before == 0 and side.shield > 0:
        t.shield_reconstitutions += 1
    if side.shield >= side.shield_max:
        return total, 0
    t.shield_recharge_opportunities += 1
    if combat_doctrine == UTILITY_COMBAT_DOCTRINE:
        reserve = _cp147_turn_start_reserve_estimate(matrix, side, target, inbound, _range(side, target))
    elif combat_doctrine == CONTEXTUAL_COMBAT_DOCTRINE:
        reserve = _cp146_core_reserve_estimate(matrix, side, _range(side, target))
    else:
        reserve = _reserve_estimate(matrix, side, target, inbound, _range(side, target))
    if total <= reserve:
        t.shield_recharge_denied_by_reserve += 1
        return total, 0
    per_tp = max(1, int(sp["tacticalRechargePerTp"]))
    missing = side.shield_max - side.shield
    need_tp = math.ceil(missing / per_tp)
    spend = min(need_tp, int(sp["tacticalRechargeCapTp"]), total - reserve)
    if spend <= 0:
        t.shield_recharge_denied_by_reserve += 1
        return total, 0
    requested = min(missing, spend * per_tp)
    tactical_suppressed = min(requested, suppression)
    restored = requested - tactical_suppressed
    side.shield += restored
    t.power_shield_recharge += spend
    t.power_spent_total += spend
    t.shield_tactical_restored += restored
    t.shield_recharge_suppressed += tactical_suppressed
    return total - spend, spend


def _plan_once_legacy(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int, inbound: int,
                      available_power: int, opponent_ecm_on: bool) -> dict[str, Any]:
    t = side.telemetry
    rem = available_power
    w = _weapon(matrix, side.build)
    pds = _pds_profile(matrix, side.build)

    # Optional ECM declares first but only if it does not consume the estimated immediate combat package.
    ecm = matrix.p("ecm", side.build.tl)
    ecm_cost = int(ecm["fullStrengthTp"]) if side.build.ecm else 0
    reserve = _reserve_estimate(matrix, side, target, inbound, range_hex)
    ecm_on = bool(side.build.ecm and rem - ecm_cost >= max(0, reserve))
    if ecm_on:
        rem -= ecm_cost

    # Sensor + ECCM acquisition. ECCM is a response to observed hostile ECM, not hidden opponent rating.
    eccm = matrix.p("eccm", side.build.tl)
    eccm_cost = int(eccm["fullStrengthTp"]) if side.build.eccm else 0
    eccm_on = bool(side.build.eccm and opponent_ecm_on and rem >= eccm_cost)
    eccm_rating = int(eccm["rating"]) if eccm_on else 0
    if eccm_on:
        rem -= eccm_cost

    mode = _base_sensor_mode(matrix, side.build, range_hex, rem)
    sensor_cost = int(mode[3])
    if sensor_cost > rem:
        mode = ("passive", int(matrix.p("sensor", side.build.tl)["passiveFirm"]), int(matrix.p("sensor", side.build.tl)["passiveApprox"]), 0)
        sensor_cost = 0
    rem -= sensor_cost
    track_no_ew = _track_from_mode(mode, range_hex)
    track = track_no_ew
    ecm_downgrade = False
    eccm_restore = False
    burnthrough_preserved = False
    burnthrough = 1 if range_hex == 0 else 0
    if opponent_ecm_on and track_no_ew == "Firm":
        opp_ecm = matrix.p("ecm", target.build.tl)
        opp_rating = int(opp_ecm["rating"])
        dr = int(matrix.p("sensor", side.build.tl)["dr"])
        # Carry forward the accepted +1 same-hex Burn-through Resistance geometry
        # control. Higher-TL burn-through improvements are not assumed.
        burnthrough = 1 if range_hex == 0 else 0
        resistance = dr + burnthrough
        net = max(0, opp_rating - eccm_rating)
        if net > resistance:
            track = "Approximate"
            ecm_downgrade = True
        elif opp_rating > resistance and eccm_rating > 0:
            eccm_restore = True
        elif burnthrough > 0 and opp_rating - eccm_rating > dr and net <= resistance:
            burnthrough_preserved = True
        else:
            burnthrough_preserved = False
    else:
        burnthrough = 1 if range_hex == 0 else 0
        burnthrough_preserved = False

    # Powered shield hardener is a real 1-TP sustained package, not a free defense.
    hardener_active = False
    hardener_power = 0
    if side.build.shield_hardener and side.build.shield and side.shield > 0:
        # Preserve enough power for at least one immediately legal weapon use before turning the hardener on.
        min_weapon = 0
        direct_track_ok = track in ("Firm", "Approximate") if w["family"] != "Missile" else track == "Firm"
        if direct_track_ok and range_hex <= int(w["range"]):
            min_weapon = int(w["low_power"] if w["family"] == "Energy" else w["power"])
        if rem - 1 >= min_weapon:
            hardener_active = True
            hardener_power = 1
            rem -= 1

    # Terminal PDS package. Preserve readiness against a known Missile-family
    # opponent as well as already-inbound flights, matching the accepted C# doctrine.
    pds_threat = _missile_threat(target, inbound)
    pds_rc = 0
    pds_power = 0
    if pds_threat and pds:
        cost = int(pds["readinessTp"])
        if rem >= cost:
            pds_power = cost
            pds_rc = int(pds["reactionCapacity"])
            rem -= cost
        else:
            # Mature RC2 systems can fall back to RC1 at half/one TP when that is consistent with the accepted scalable model.
            if int(pds["reactionCapacity"]) >= 2 and cost >= 2 and rem >= 1:
                pds_power = 1
                pds_rc = 1
                rem -= 1

    weapon_plans: list[tuple[int, int, int] | None] = []  # power, damage, accuracy
    weapon_modes: list[str | None] = []
    attack_track_ok = track == "Firm" if w["family"] == "Missile" else track in ("Firm", "Approximate")
    if attack_track_ok and range_hex <= int(w["range"]):
        for _ in range(w["count"]):
            mode_name: str | None = None
            if w["family"] == "Energy":
                can_safe_overload = side.energy_weapon_strain < int(w.get("strain_limit", 2))
                if can_safe_overload and rem >= int(w["overload_power"]):
                    plan = (int(w["overload_power"]), int(w["overload_damage"]), int(w["accuracy"]))
                    mode_name = "Overload"
                elif rem >= int(w["standard_power"]):
                    plan = (int(w["standard_power"]), int(w["standard_damage"]), int(w["accuracy"]))
                    mode_name = "Standard"
                elif rem >= int(w["low_power"]):
                    plan = (int(w["low_power"]), int(w["low_damage"]), int(w["accuracy"]))
                    mode_name = "Low"
                else:
                    plan = None
            else:
                cost = int(w["power"])
                plan = (cost, int(w["damage"]), int(w["accuracy"])) if rem >= cost else None
            if plan:
                rem -= plan[0]
            weapon_plans.append(plan)
            weapon_modes.append(mode_name)
    else:
        weapon_plans = [None] * int(w["count"])
        weapon_modes = [None] * int(w["count"])

    spent = available_power - rem
    return {
        "ecm_on": ecm_on, "ecm_cost": ecm_cost if ecm_on else 0,
        "eccm_on": eccm_on, "eccm_cost": eccm_cost if eccm_on else 0,
        "sensor_mode": mode[0], "sensor_cost": sensor_cost, "track": track, "track_no_ew": track_no_ew,
        "ecm_downgrade": ecm_downgrade, "eccm_restore": eccm_restore,
        "burnthrough_resistance": burnthrough, "burnthrough_preserved": burnthrough_preserved,
        "hardener_active": hardener_active, "hardener_power": hardener_power,
        "pds_rc": pds_rc, "pds_power": pds_power, "pds": pds, "pds_threat": pds_threat,
        "weapon_plans": weapon_plans, "weapon_modes": weapon_modes, "spent": spent, "remaining": rem,
    }


def _cp146_min_weapon_power(w: dict[str, Any]) -> int:
    if w["family"] == "Energy":
        return int(w["low_power"]) * int(w["count"])
    return int(w["power"]) * int(w["count"])


def _cp146_preferred_sensor_mode(matrix: CandidateMatrix, side: SideState, range_hex: int,
                                 available_power: int, weapon_reserve: int) -> tuple[str, int, int, int]:
    """Established-combat sensor doctrine: Active is normal; Passive is a TP fallback.

    Active Low is preferred when it can preserve the minimum main-weapon package.
    Active High is used only when Low cannot provide a usable track and High can.
    Passive remains legal when active sensing would starve the main weapon.
    """
    s = matrix.p("sensor", side.build.tl)
    passive = ("passive", int(s["passiveFirm"]), int(s["passiveApprox"]), 0)
    low = ("low", int(s["activeLowFirm"]), int(s["activeLowApprox"]), int(s["activeLowTp"]))
    high = None
    if s.get("activeHighFirm") is not None and s.get("activeHighTp") is not None:
        high = ("high", int(s["activeHighFirm"]), int(s["activeHighApprox"]), int(s["activeHighTp"]))

    def usable(mode: tuple[str, int, int, int]) -> bool:
        track = _track_from_mode(mode, range_hex)
        w = _weapon(matrix, side.build)
        return track == "Firm" if w["family"] == "Missile" else track in ("Firm", "Approximate")

    active_candidates = [low] + ([high] if high is not None else [])
    for mode in active_candidates:
        if mode[3] <= available_power and available_power - mode[3] >= weapon_reserve and usable(mode):
            return mode
    if usable(passive) and available_power >= weapon_reserve:
        return passive
    # If a powered sensor is required to create any attack opportunity, use the
    # least expensive active mode that does so, even when only part of the desired
    # weapon package can then be funded.
    for mode in active_candidates:
        if mode[3] <= available_power and usable(mode):
            return mode
    affordable = [m for m in active_candidates if m[3] <= available_power]
    if affordable:
        return max(affordable, key=lambda m: (m[2], m[1], -m[3]))
    return passive


def _cp146_immediate_missile_threat(matrix: CandidateMatrix, side: SideState, target: SideState,
                                    inbound: int, range_hex: int) -> tuple[bool, str]:
    if inbound > 0:
        return True, "INBOUND"
    known = side.known_opponent_weapon_family
    if known == "Missile":
        target_weapon = _weapon(matrix, target.build)
        if range_hex <= int(target_weapon.get("missile_move", 0)) and range_hex <= int(target_weapon["range"]):
            return True, "KNOWN_SAME_TURN_TERMINAL"
        return False, "KNOWN_MISSILE_NOT_IMMINENT"
    if known is None:
        return False, "UNKNOWN_READINESS"
    return False, "KNOWN_NON_MISSILE"


def _cp146_apply_ecm_to_track(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int,
                              track_no_ew: str, opponent_ecm_on: bool, eccm_rating: int) -> tuple[str, bool, bool, bool, int]:
    track = track_no_ew
    ecm_downgrade = False
    eccm_restore = False
    burnthrough_preserved = False
    burnthrough = 1 if range_hex == 0 else 0
    if opponent_ecm_on and track_no_ew == "Firm":
        opp_ecm = matrix.p("ecm", target.build.tl)
        opp_rating = int(opp_ecm["rating"])
        dr = int(matrix.p("sensor", side.build.tl)["dr"])
        resistance = dr + burnthrough
        net = max(0, opp_rating - eccm_rating)
        if net > resistance:
            track = "Approximate"
            ecm_downgrade = True
        elif opp_rating > resistance and eccm_rating > 0:
            eccm_restore = True
        elif burnthrough > 0 and opp_rating - eccm_rating > dr and net <= resistance:
            burnthrough_preserved = True
    return track, ecm_downgrade, eccm_restore, burnthrough_preserved, burnthrough




def _cp147_turn_start_reserve_estimate(matrix: CandidateMatrix, side: SideState, target: SideState,
                                       inbound: int, range_hex: int) -> int:
    """Forecast the minimum package that Turn-Refresh tactical recharge must not consume."""
    reserve = _cp146_core_reserve_estimate(matrix, side, range_hex)
    pds = _pds_profile(matrix, side.build)
    pds_has_ammo = pds is not None and (side.pds_ammo is None or int(side.pds_ammo) > 0)
    missile_relevant, reason = _cp146_immediate_missile_threat(matrix, side, target, inbound, range_hex)
    terminal_forecast = bool(side.cp147_terminal_threats)
    # An in-flight missile reserves PDS TP at Turn Refresh only when the observed
    # current geometry can reach terminal this turn.  A previously demonstrated
    # launcher may also justify same-turn readiness at short range.  Distant
    # in-flight missiles do not suppress tactical Shield recharge merely by existing.
    if pds_has_ammo and (terminal_forecast or (missile_relevant and reason == "KNOWN_SAME_TURN_TERMINAL")):
        reserve += int(pds["readinessTp"])
    # Known Energy offense makes Shield Hardener part of the forecasted combat
    # package; tactical recharge cannot spend its TP first. Unknown-threat
    # hardener readiness remains residual, consistent with the post-Movement plan.
    if side.build.shield_hardener and side.build.shield and side.shield > 0 and side.known_opponent_weapon_family == "Energy":
        reserve += 1
    return reserve


def _cp147_expected_intercepted(threats: int, held_attempts: int, held_p: float,
                                pds_rc: int, pds_p: float, max_attempts_per_flight: int = 2) -> float:
    """Expected identical subflights intercepted by Held Main then sequential PDS.

    Mirrors the canonical ordering: every Held bank gets one attempt before PDS;
    PDS then spends up to the profile's legal attempts on the current subflight
    before moving on. Historical/local PDS remains capped at two; CP154 AMM RC3
    may expose one range-1 plus two terminal opportunities.
    """
    threats = max(0, int(threats)); held_attempts = max(0, int(held_attempts)); pds_rc = max(0, int(pds_rc))
    held_p = max(0.0, min(1.0, float(held_p))); pds_p = max(0.0, min(1.0, float(pds_p)))
    memo_pds: dict[tuple[int, int], float] = {}
    def pds_ev(n: int, rc: int) -> float:
        key=(n,rc)
        if key in memo_pds: return memo_pds[key]
        if n <= 0 or rc <= 0:
            return 0.0
        attempts=min(max(1,int(max_attempts_per_flight)),rc)
        # Sequential attempts stay on the first arriving flight until it is
        # destroyed or its legal windows are exhausted; unused RC then spills
        # to the next flight.
        miss=1.0; val=0.0
        for used in range(1,attempts+1):
            val += miss*pds_p*(1.0+pds_ev(n-1,rc-used))
            miss *= (1.0-pds_p)
        val += miss*pds_ev(n-1,rc-attempts)
        memo_pds[key]=val
        return val
    memo_held: dict[tuple[int, int], float] = {}
    def held_ev(n: int, h: int) -> float:
        key=(n,h)
        if key in memo_held: return memo_held[key]
        if n <= 0:
            return 0.0
        if h <= 0:
            return pds_ev(n,pds_rc)
        val = held_p * (1.0 + held_ev(n-1,h-1)) + (1.0-held_p) * held_ev(n,h-1)
        memo_held[key]=val
        return val
    return held_ev(threats, held_attempts)


def _cp147_recovery_candidates(matrix: CandidateMatrix, side: SideState) -> list[tuple[str, int, int]]:
    """Return current-state recovery opportunities as (id, TP, utility_milli)."""
    out: list[tuple[str,int,int]]=[]
    if side.hull > 0 and side.hull < side.hull_max and side.repair_kits_remaining > 0:
        dc=matrix.p("damage_control", side.build.tl)
        cost=max(0,int(dc.get("attemptTp",1)))
        restore=max(0,min(side.hull_max-side.hull,int(dc.get("hullRestoredPerSuccessfulKit",1))))
        chance=max(0,min(100,int(dc.get("hullRepairChancePp",0))))
        if cost>0 and restore>0 and chance>0:
            out.append(("damage_control",cost,chance*restore*10))
    profile=_armor_profile(matrix,side.build)
    per_tp=max(0,int(profile.get("tacticalRegenerationPerTp",0)))
    cap=max(0,int(profile.get("tacticalRegenerationCapTp",0)))
    if per_tp>0 and cap>0 and side.armor_integrity < side.armor_max and side.armor_regen_reserve_remaining != 0:
        missing=max(0,side.armor_max-side.armor_integrity)
        max_restore=missing if side.armor_regen_reserve_remaining < 0 else min(missing,side.armor_regen_reserve_remaining)
        for i in range(min(cap, math.ceil(max_restore/per_tp))):
            restored=min(per_tp,max(0,max_restore-i*per_tp))
            if restored>0: out.append((f"armor_regen_{i+1}",1,int(restored*1000)))
    return out


def _plan_once_utility(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int, inbound: int,
                       available_power: int, opponent_ecm_on: bool) -> dict[str, Any]:
    """CP147 bounded expected-utility Tactical Power/action package selection.

    Hidden enemy build data is never queried for utility.  Offensive utility comes
    from own weapon mechanics; defensive missile utility comes only from already
    observed/projected terminal threats or a previously observed missile profile.
    Unknown capability can justify residual readiness but contributes no invented
    numeric threat value.
    """
    w=_weapon(matrix,side.build); pds=_pds_profile(matrix,side.build); known=side.known_opponent_weapon_family
    weapon_has_ammo=side.weapon_ammo is None or int(side.weapon_ammo)>0
    pds_has_ammo=bool(pds is not None and (side.pds_ammo is None or int(side.pds_ammo)>0))

    # Projected terminal subflights observed in the full-map kernel.  If no
    # current flight exists but a previously observed Missile profile can launch
    # into terminal this turn, use that demonstrated profile rather than hidden
    # build data.
    terminal=list(side.cp147_terminal_threats)
    pds_imminent,pds_reason=_cp146_immediate_missile_threat(matrix,side,target,inbound,range_hex)
    if not terminal and pds_reason == "KNOWN_SAME_TURN_TERMINAL" and side.known_opponent_missile_expected_raw_per_subflight > 0:
        count=max(1,int(side.known_opponent_missile_subflights or 1))
        terminal=[(float(side.known_opponent_missile_expected_raw_per_subflight),int(side.known_opponent_missile_pds_penalty_pp),0.0) for _ in range(count)]
    threat_count=len(terminal)
    threat_ev=(sum(float(x[0]) for x in terminal)/threat_count) if threat_count else 0.0
    penalty=round(sum(int(x[1]) for x in terminal)/threat_count) if threat_count else 0
    critical_hull_threat=any(float(x[2]) > 0.0 for x in terminal)

    sensor=matrix.p("sensor",side.build.tl)
    sensor_modes=[("low",int(sensor["activeLowFirm"]),int(sensor["activeLowApprox"]),int(sensor["activeLowTp"]))]
    if sensor.get("activeHighFirm") is not None and sensor.get("activeHighTp") is not None:
        sensor_modes.append(("high",int(sensor["activeHighFirm"]),int(sensor["activeHighApprox"]),int(sensor["activeHighTp"])))
    sensor_modes.append(("passive",int(sensor["passiveFirm"]),int(sensor["passiveApprox"]),0))

    eccm=matrix.p("eccm",side.build.tl); eccm_cost=int(eccm["fullStrengthTp"]) if side.build.eccm else 0
    candidates: list[TacticalPackageCandidate]=[]
    payloads: dict[str,dict[str,Any]]={}
    comp_bonus=int(matrix.p("computer",side.build.tl)["targetingPp"])
    max_banks=int(w["count"])
    if side.weapon_ammo is not None:
        max_banks=min(max_banks,max(0,int(side.weapon_ammo)))

    for smode in sensor_modes:
        sensor_cost=int(smode[3])
        if sensor_cost>available_power: continue
        track_no_ew=_track_from_mode(smode,range_hex)
        eccm_options=[False]
        no_eccm=_cp146_apply_ecm_to_track(matrix,side,target,range_hex,track_no_ew,opponent_ecm_on,0)
        if side.build.eccm and opponent_ecm_on and eccm_cost <= available_power-sensor_cost:
            with_eccm=_cp146_apply_ecm_to_track(matrix,side,target,range_hex,track_no_ew,True,int(eccm["rating"]))
            if with_eccm[0] != no_eccm[0]: eccm_options.append(True)
        for eccm_on in eccm_options:
            apply=_cp146_apply_ecm_to_track(matrix,side,target,range_hex,track_no_ew,opponent_ecm_on,int(eccm["rating"]) if eccm_on else 0)
            track,ecm_downgrade,eccm_restore,burnthrough_preserved,burnthrough=apply
            base_cost=sensor_cost+(eccm_cost if eccm_on else 0)
            if base_cost>available_power: continue
            active=smode[0] != "passive"
            firm=track == "Firm"
            ship_attack_ok=weapon_has_ammo and range_hex <= int(w["range"]) and (firm if w["family"]=="Missile" else track in ("Firm","Approximate"))
            direct_options: list[tuple[str,str|None,int,int]]=[("off",None,0,0)]
            if ship_attack_ok and max_banks>0:
                if w["family"]=="Energy":
                    chance=_hit_chance(matrix,side.build,range_hex,int(w["accuracy"]),track,int(w.get("standard_range",w["range"])),int(w["range"]))
                    direct_options += [
                        ("direct_low","Low",int(w["low_power"]),chance*int(w["low_damage"])*10),
                        ("direct_standard","Standard",int(w["standard_power"]),chance*int(w["standard_damage"])*10),
                    ]
                elif w["family"]=="Kinetic":
                    chance=_hit_chance(matrix,side.build,range_hex,int(w["accuracy"]),track,int(w.get("standard_range",w["range"])),int(w["range"]))
                    direct_options.append(("direct",None,int(w["power"]),chance*int(w["damage"])*10))
                else:
                    subflights=max(1,int(w.get("subflights",1)))
                    direct_options.append(("launch",None,int(w["power"]),int(w["guidance"])*float(w["damage"])*int(w.get("packets",1))*subflights*10))
            held_chance=max(5,min(95,50+int(w.get("accuracy",0))+comp_bonus))/100.0 if w["family"] in ("Kinetic","Energy") else 0.0
            # Terminal missiles are at the defender's hex when held fire resolves.
            # Their Firm-track eligibility is therefore evaluated at range 0, not
            # at the separate enemy-ship range used for direct fire.
            held_missile_track_ok = _track_from_mode(smode, 0) == "Firm"
            held_track_ok = bool(threat_count and w["family"] in ("Kinetic","Energy") and held_missile_track_ok)
            bank_options=list(direct_options)
            if held_track_ok and max_banks>0 and (not ship_attack_ok or max_banks>=2 or critical_hull_threat):
                if w["family"]=="Energy": bank_options.append(("hold","Low",int(w["low_power"]),0))
                else: bank_options.append(("hold",None,int(w["power"]),0))

            pds_options=[("pds0",0,0)]
            if pds_has_ammo and threat_count>0:
                pds_options=_pds_readiness_options(pds,side)
            pds_chance=(max(0,min(95,int(pds["baseChancePp"])+comp_bonus-penalty))/100.0) if pds is not None else 0.0

            for pds_id,pds_cost,pds_rc in pds_options:
                for combo in product(bank_options, repeat=max_banks):
                    # Identical banks may be represented in either order; canonicalize.
                    if max_banks==2 and combo[0][0] > combo[1][0]: continue
                    actions=[x[0] for x in combo]
                    funded=sum(a!="off" for a in actions); held=sum(a=="hold" for a in actions)
                    if side.weapon_ammo is not None and funded>int(side.weapon_ammo): continue
                    if ship_attack_ok and max_banks==1 and funded==0 and pds_rc>0 and not critical_hull_threat:
                        continue
                    weapon_cost=sum(int(x[2]) for x in combo)
                    total_cost=base_cost+pds_cost+weapon_cost
                    if total_cost>available_power: continue
                    offense=sum(int(round(float(x[3]))) for x in combo)
                    defense=0
                    if threat_count>0 and (held>0 or pds_rc>0):
                        intercepted=_cp147_expected_intercepted(threat_count,held,held_chance,pds_rc,pds_chance,_pds_max_attempts_per_flight(pds,pds_rc))
                        defense=int(round(intercepted*threat_ev*1000.0))
                    cid=f"{smode[0]}-e{int(eccm_on)}-{pds_id}-"+"_".join(actions or ["none"])
                    cand=TacticalPackageCandidate(cid,total_cost,offense,defense,funded,held,pds_rc,active,firm)
                    candidates.append(cand)
                    payloads[cid]={"sensor_mode":smode,"track":track,"track_no_ew":track_no_ew,"ecm_downgrade":ecm_downgrade,"eccm_restore":eccm_restore,"burnthrough_preserved":burnthrough_preserved,"burnthrough":burnthrough,"eccm_on":eccm_on,"combo":combo,"pds_cost":pds_cost,"pds_rc":pds_rc,"ship_attack_ok":ship_attack_ok}

    if not candidates:
        # At minimum a zero-cost passive/off package must exist, but retain a
        # defensive fallback for malformed future profiles.
        return _plan_once_contextual(matrix,side,target,range_hex,inbound,available_power,opponent_ecm_on)
    selected=choose_tactical_package(candidates,int(available_power)); data=payloads[selected.id]
    smode=data["sensor_mode"]; sensor_cost=int(smode[3]); eccm_on=bool(data["eccm_on"])
    combo=list(data["combo"]); pds_rc=int(data["pds_rc"]); pds_power=int(data["pds_cost"])
    rem=int(available_power)-int(selected.tactical_power)
    weapon_plans=[]; weapon_modes=[]; weapon_actions=[]
    for action,mode_name,cost,_utility in combo:
        if action=="off":
            weapon_plans.append(None); weapon_modes.append(None); weapon_actions.append(None); continue
        if w["family"]=="Energy":
            damage=int(w["low_damage"] if mode_name=="Low" else w["standard_damage"])
            weapon_plans.append((int(cost),damage,int(w["accuracy"])))
        elif w["family"]=="Kinetic": weapon_plans.append((int(cost),int(w["damage"]),int(w["accuracy"])))
        else: weapon_plans.append((int(cost),int(w.get("damage",0)),int(w.get("accuracy",0))))
        weapon_modes.append(mode_name); weapon_actions.append("hold_missile" if action=="hold" else "ship")
    # Restore declared bank cardinality when finite ammo reduced the action search.
    while len(weapon_plans)<int(w["count"]):
        weapon_plans.append(None); weapon_modes.append(None); weapon_actions.append(None)

    # Known Energy defense is immediately relevant; unknown specialist readiness
    # is residual only and cannot displace the selected sensor/main/PDS package.
    hardener_active=False; hardener_power=0; hardener_reason="NOT_INSTALLED"
    if side.build.shield_hardener and side.build.shield and side.shield>0:
        hardener_reason="UNKNOWN_READINESS" if known is None else ("KNOWN_ENERGY_THREAT" if known=="Energy" else "KNOWN_IRRELEVANT")
        hardener_aux=_cp158_aux_kind(matrix,side.build,"shield_hardener")
        hardener_cost=int(hardener_aux.get("tp",1)) if hardener_aux is not None else 1
        if hardener_reason=="KNOWN_ENERGY_THREAT" and rem>=hardener_cost:
            hardener_active=True; hardener_power=hardener_cost; rem-=hardener_cost

    # Compare residual Energy-overload upgrades against already-damaged recovery
    # in the same structural-point utility units.  Recovery TP is left in plan
    # remaining so the canonical DamageControl phase can consume it later.
    recovery=_cp147_recovery_candidates(matrix,side)
    recovery.sort(key=lambda x:(x[2]/max(1,x[1]),x[2],-x[1],x[0]),reverse=True)
    recovery_reserved=0; recovery_utility=0
    overload_options=[]
    if w["family"]=="Energy" and side.energy_weapon_strain < int(w.get("strain_limit",2)):
        chance=_hit_chance(matrix,side.build,range_hex,int(w["accuracy"]),str(data["track"]),int(w.get("standard_range",w["range"])),int(w["range"]))
        for i,(wp,mode_name,action) in enumerate(zip(weapon_plans,weapon_modes,weapon_actions)):
            if wp is not None and mode_name=="Standard" and action=="ship":
                extra=int(w["overload_power"])-int(w["standard_power"])
                marginal=chance*(int(w["overload_damage"])-int(w["standard_damage"]))*10
                if extra>0 and marginal>0: overload_options.append((i,extra,int(marginal)))
    residual_actions=[("recovery",x[0],x[1],x[2]) for x in recovery]+[("overload",str(i),cost,util) for i,cost,util in overload_options]
    residual_actions.sort(key=lambda x:(x[3]/max(1,x[2]), 1 if x[0]=="overload" else 0, x[3], -x[2], x[1]),reverse=True)
    overload_selected=[]
    for kind,ident,cost,util in residual_actions:
        if cost>rem: continue
        if kind=="recovery":
            recovery_reserved += cost; recovery_utility += util; rem -= cost
        else:
            idx=int(ident)
            if idx in overload_selected: continue
            overload_selected.append(idx); rem-=cost
            weapon_plans[idx]=(int(w["overload_power"]),int(w["overload_damage"]),int(w["accuracy"])); weapon_modes[idx]="Overload"

    # Put recovery reserve back into the end-of-turn available pool; it is
    # intentionally unavailable to lower-priority readiness/ECM spending.
    free_rem=rem
    if known is None:
        if pds_has_ammo and pds_rc==0:
            affordable=[x for x in _pds_readiness_options(pds,side) if x[2]>0 and x[1]<=free_rem]
            if affordable:
                _pid,pds_power,pds_rc=max(affordable,key=lambda x:(x[2],-x[1])); free_rem-=pds_power
        hardener_aux=_cp158_aux_kind(matrix,side.build,"shield_hardener")
        hardener_cost=int(hardener_aux.get("tp",1)) if hardener_aux is not None else 1
        if side.build.shield_hardener and side.build.shield and side.shield>0 and not hardener_active and free_rem>=hardener_cost:
            hardener_active=True; hardener_power=hardener_cost; free_rem-=hardener_cost
    energized=_cp158_aux_kind(matrix,side.build,"energized_armor")
    energized_active=False; energized_power=0
    if energized is not None and side.armor_integrity>0:
        cost=int(energized.get("tp",0))
        if cost<=free_rem and (side.shield <= side.shield_max*0.5 or side.armor_integrity < side.armor_max or known in ("Kinetic","Energy","Missile")):
            energized_active=True; energized_power=cost; free_rem-=cost
    stabilizer=_cp158_aux_kind(matrix,side.build,"field_stabilizer")
    field_stabilizer_active=False; field_stabilizer_power=0
    if stabilizer is not None and side.build.shield and side.shield>0 and known in ("Energy","Missile"):
        cost=int(stabilizer.get("tp",0))
        if cost<=free_rem: field_stabilizer_active=True; field_stabilizer_power=cost; free_rem-=cost
    ecm=matrix.p("ecm",side.build.tl); ecm_cost=int(ecm["fullStrengthTp"]) if side.build.ecm else 0
    ecm_on=bool(side.build.ecm and ecm_cost<=free_rem)
    if ecm_on: free_rem-=ecm_cost
    rem=free_rem+recovery_reserved

    return {
        "combat_doctrine":UTILITY_COMBAT_DOCTRINE,"opponent_weapon_knowledge":known or "Unknown",
        "weapon_core_opportunity":bool(data.get("ship_attack_ok",False)),"weapon_has_ammo":weapon_has_ammo,"pds_has_ammo":pds_has_ammo,
        "ecm_on":ecm_on,"ecm_cost":ecm_cost if ecm_on else 0,"eccm_on":eccm_on,"eccm_cost":eccm_cost if eccm_on else 0,
        "sensor_mode":smode[0],"sensor_cost":sensor_cost,"track":data["track"],"track_no_ew":data["track_no_ew"],
        "ecm_downgrade":data["ecm_downgrade"],"eccm_restore":data["eccm_restore"],"burnthrough_resistance":data["burnthrough"],"burnthrough_preserved":data["burnthrough_preserved"],
        "hardener_active":hardener_active,"hardener_power":hardener_power,"hardener_reason":hardener_reason,
        "energized_armor_active":energized_active,"energized_armor_power":energized_power,
        "field_stabilizer_active":field_stabilizer_active,"field_stabilizer_power":field_stabilizer_power,
        "pds_rc":pds_rc,"pds_power":pds_power,"pds":pds,"pds_threat":bool(threat_count),
        "pds_reason":"PROJECTED_TERMINAL" if threat_count else pds_reason,"pds_unknown_readiness":bool(known is None and not threat_count),
        "weapon_plans":weapon_plans,"weapon_modes":weapon_modes,"weapon_actions":weapon_actions,
        "held_main_declared":int(any(x=="hold_missile" for x in weapon_actions)),
        "package_id":selected.id,"package_utility_milli":selected.total_utility_milli,
        "package_offense_utility_milli":selected.offense_utility_milli,"package_defense_utility_milli":selected.defense_utility_milli,
        "recovery_reserved_tp":recovery_reserved,"recovery_utility_milli":recovery_utility,
        "terminal_threat_subflights":threat_count,"critical_hull_threat":critical_hull_threat,"spent":int(available_power)-rem,"remaining":rem,
    }


def _plan_once_contextual(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int, inbound: int,
                          available_power: int, opponent_ecm_on: bool) -> dict[str, Any]:
    """CP146 information-limited, context-sensitive combat-resource doctrine."""
    rem = int(available_power)
    w = _weapon(matrix, side.build)
    pds = _pds_profile(matrix, side.build)
    known = side.known_opponent_weapon_family

    # 1. Established combat defaults to Active Sensor, but not when doing so
    # would needlessly starve the minimum useful main-weapon package.
    weapon_has_ammo = side.weapon_ammo is None or int(side.weapon_ammo) > 0
    weapon_reserve = _cp146_min_weapon_power(w) if weapon_has_ammo and range_hex <= int(w["range"]) else 0
    mode = _cp146_preferred_sensor_mode(matrix, side, range_hex, rem, weapon_reserve)
    sensor_cost = int(mode[3])
    rem -= sensor_cost
    track_no_ew = _track_from_mode(mode, range_hex)

    # 2. ECCM is reactive. It is considered only when hostile ECM is actually
    # observed and only if it restores a Firm track that ECM would otherwise degrade.
    track, ecm_downgrade, _, burnthrough_preserved, burnthrough = _cp146_apply_ecm_to_track(
        matrix, side, target, range_hex, track_no_ew, opponent_ecm_on, 0
    )
    eccm = matrix.p("eccm", side.build.tl)
    eccm_cost = int(eccm["fullStrengthTp"]) if side.build.eccm else 0
    eccm_on = False
    eccm_restore = False
    if side.build.eccm and opponent_ecm_on and ecm_downgrade and rem >= eccm_cost:
        with_eccm = _cp146_apply_ecm_to_track(
            matrix, side, target, range_hex, track_no_ew, True, int(eccm["rating"])
        )
        candidate_track = with_eccm[0]
        minimum_weapon = _cp146_min_weapon_power(w) if weapon_has_ammo and range_hex <= int(w["range"]) else 0
        if candidate_track == "Firm" and rem - eccm_cost >= minimum_weapon:
            eccm_on = True
            rem -= eccm_cost
            track, ecm_downgrade, eccm_restore, burnthrough_preserved, burnthrough = with_eccm

    # 3. Determine whether a missile threat is immediate. Held-main commitment
    # is decided only after actual PDS capacity is known, so a K/E gun does not
    # abandon offense merely because a launcher has been identified.
    pds_imminent, pds_reason = _cp146_immediate_missile_threat(matrix, side, target, inbound, range_hex)
    held_needed = False

    # 4. Main weapons are part of the core combat package. Energy uses Standard
    # as the normal doctrine and falls back to Low under TP pressure. Overload is
    # considered later only from residual power.
    weapon_plans: list[tuple[int, int, int] | None] = []
    weapon_modes: list[str | None] = []
    weapon_actions: list[str | None] = []
    attack_track_ok = track == "Firm" if w["family"] == "Missile" else track in ("Firm", "Approximate")
    weapon_core_opportunity = bool(weapon_has_ammo and attack_track_ok and range_hex <= int(w["range"]))
    if weapon_core_opportunity:
        for idx in range(int(w["count"])):
            plan = None
            mode_name = None
            if w["family"] == "Energy":
                if rem >= int(w["standard_power"]):
                    plan = (int(w["standard_power"]), int(w["standard_damage"]), int(w["accuracy"]))
                    mode_name = "Standard"
                elif rem >= int(w["low_power"]):
                    plan = (int(w["low_power"]), int(w["low_damage"]), int(w["accuracy"]))
                    mode_name = "Low"
            else:
                cost = int(w["power"])
                if rem >= cost:
                    plan = (cost, int(w.get("damage", 0)), int(w.get("accuracy", 0)))
            if plan is not None:
                rem -= int(plan[0])
            weapon_plans.append(plan)
            weapon_modes.append(mode_name)
            weapon_actions.append("ship" if plan is not None else None)
    else:
        weapon_plans = [None] * int(w["count"])
        weapon_modes = [None] * int(w["count"])
        weapon_actions = [None] * int(w["count"])

    # 5. Contextual defenses use only residual TP. Unknown capability justifies
    # readiness, but never at the expense of the already-funded core package.
    pds_rc = 0
    pds_power = 0
    pds_has_ammo = bool(pds is not None and (side.pds_ammo is None or int(side.pds_ammo) > 0))
    pds_unknown_readiness = bool(known is None and pds_has_ammo and inbound <= 0)
    pds_should_power = bool(pds_has_ammo and (pds_imminent or pds_unknown_readiness))
    if pds_should_power:
        cost = int(pds["readinessTp"])
        if rem >= cost:
            pds_power = cost
            pds_rc = int(pds["reactionCapacity"])
            rem -= cost
        elif int(pds["reactionCapacity"]) >= 2 and cost >= 2 and rem >= 1:
            pds_power = 1
            pds_rc = 1
            rem -= 1

    # Held Main is a supplemental layer, not an automatic replacement for
    # offense. A legal single-main ship attack remains a ship attack. A dual-main
    # ship may hold one funded bank when imminent subflights exceed funded PDS RC.
    # If no legal ship-fire opportunity exists, one K/E bank may instead be funded
    # as a held interception fallback for threat capacity that PDS cannot cover.
    expected_pds_subflights = int(inbound)
    if expected_pds_subflights <= 0 and pds_reason == "KNOWN_SAME_TURN_TERMINAL":
        profile = side.known_opponent_missile_profile
        expected_pds_subflights = 2 if profile == "Swarmer" else 1
    funded_weapon_banks = sum(x is not None for x in weapon_plans)
    excess_threat = max(0, expected_pds_subflights - int(pds_rc))
    held_needed = False
    if w["family"] in ("Kinetic", "Energy") and excess_threat > 0:
        if weapon_core_opportunity and funded_weapon_banks >= 2:
            first_funded = next(i for i, x in enumerate(weapon_plans) if x is not None)
            weapon_actions[first_funded] = "hold_missile"
            held_needed = True
        elif not weapon_core_opportunity:
            # No useful ship shot is being sacrificed. Fund one normal K/E bank
            # from residual TP to cover an otherwise-unserved missile opportunity.
            hold_plan = None
            hold_mode = None
            if w["family"] == "Energy":
                if rem >= int(w["standard_power"]):
                    hold_plan = (int(w["standard_power"]), int(w["standard_damage"]), int(w["accuracy"]))
                    hold_mode = "Standard"
                elif rem >= int(w["low_power"]):
                    hold_plan = (int(w["low_power"]), int(w["low_damage"]), int(w["accuracy"]))
                    hold_mode = "Low"
            else:
                cost = int(w["power"])
                if rem >= cost:
                    hold_plan = (cost, int(w.get("damage", 0)), int(w.get("accuracy", 0)))
            if hold_plan is not None:
                rem -= int(hold_plan[0])
                weapon_plans[0] = hold_plan
                weapon_modes[0] = hold_mode
                weapon_actions[0] = "hold_missile"
                held_needed = True
                funded_weapon_banks = 1

    hardener_active = False
    hardener_power = 0
    hardener_reason = "NOT_INSTALLED"
    if side.build.shield_hardener and side.build.shield and side.shield > 0:
        if known is None:
            hardener_reason = "UNKNOWN_READINESS"
        elif known == "Energy":
            hardener_reason = "KNOWN_ENERGY_THREAT"
        else:
            hardener_reason = "KNOWN_IRRELEVANT"
        if hardener_reason != "KNOWN_IRRELEVANT" and rem >= 1:
            hardener_active = True
            hardener_power = 1
            rem -= 1

    # ECM is a discretionary residual defense. It never consumes the core package.
    ecm = matrix.p("ecm", side.build.tl)
    ecm_cost = int(ecm["fullStrengthTp"]) if side.build.ecm else 0
    ecm_on = bool(side.build.ecm and rem >= ecm_cost)
    if ecm_on:
        rem -= ecm_cost

    # Upgrade a funded Energy Standard shot to Overload only from residual TP and
    # only inside the safe strain policy. This cannot de-fund a contextual defense.
    if w["family"] == "Energy" and side.energy_weapon_strain < int(w.get("strain_limit", 2)):
        for i, plan in enumerate(weapon_plans):
            if plan is None or weapon_modes[i] != "Standard" or weapon_actions[i] == "hold_missile":
                continue
            extra = int(w["overload_power"]) - int(w["standard_power"])
            if extra > 0 and rem >= extra:
                rem -= extra
                weapon_plans[i] = (int(w["overload_power"]), int(w["overload_damage"]), int(w["accuracy"]))
                weapon_modes[i] = "Overload"

    spent = int(available_power) - rem
    return {
        "combat_doctrine": CONTEXTUAL_COMBAT_DOCTRINE,
        "opponent_weapon_knowledge": known or "Unknown",
        "weapon_core_opportunity": weapon_core_opportunity,
        "weapon_has_ammo": weapon_has_ammo,
        "pds_has_ammo": pds_has_ammo,
        "ecm_on": ecm_on, "ecm_cost": ecm_cost if ecm_on else 0,
        "eccm_on": eccm_on, "eccm_cost": eccm_cost if eccm_on else 0,
        "sensor_mode": mode[0], "sensor_cost": sensor_cost, "track": track, "track_no_ew": track_no_ew,
        "ecm_downgrade": ecm_downgrade, "eccm_restore": eccm_restore,
        "burnthrough_resistance": burnthrough, "burnthrough_preserved": burnthrough_preserved,
        "hardener_active": hardener_active, "hardener_power": hardener_power, "hardener_reason": hardener_reason,
        "pds_rc": pds_rc, "pds_power": pds_power, "pds": pds, "pds_threat": pds_imminent,
        "pds_reason": pds_reason, "pds_unknown_readiness": pds_unknown_readiness,
        "weapon_plans": weapon_plans, "weapon_modes": weapon_modes, "weapon_actions": weapon_actions,
        "held_main_declared": int(any(x == "hold_missile" for x in weapon_actions)),
        "spent": spent, "remaining": rem,
    }


def _plan_once(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int, inbound: int,
               available_power: int, opponent_ecm_on: bool,
               combat_doctrine: str = LEGACY_COMBAT_DOCTRINE) -> dict[str, Any]:
    if combat_doctrine == UTILITY_COMBAT_DOCTRINE:
        return _plan_once_utility(matrix, side, target, range_hex, inbound, available_power, opponent_ecm_on)
    if combat_doctrine == CONTEXTUAL_COMBAT_DOCTRINE:
        return _plan_once_contextual(matrix, side, target, range_hex, inbound, available_power, opponent_ecm_on)
    if combat_doctrine != LEGACY_COMBAT_DOCTRINE:
        raise ValueError(f"unknown combat doctrine {combat_doctrine!r}")
    plan = _plan_once_legacy(matrix, side, target, range_hex, inbound, available_power, opponent_ecm_on)
    plan.setdefault("combat_doctrine", LEGACY_COMBAT_DOCTRINE)
    plan.setdefault("opponent_weapon_knowledge", target.build.weapon_family)
    plan.setdefault("hardener_reason", "LEGACY_STATIC")
    plan.setdefault("pds_reason", "LEGACY_STATIC")
    plan.setdefault("pds_unknown_readiness", False)
    plan.setdefault("weapon_actions", ["ship" if x is not None else None for x in plan["weapon_plans"]])
    plan.setdefault("held_main_declared", 0)
    return plan


def _plan_turn(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int, inbound: int,
               base_power: int, opponent_ecm_hint: bool, combat_doctrine: str = LEGACY_COMBAT_DOCTRINE) -> dict[str, Any]:
    # First compute ECM declarations using own package reservation. Then recompute both sides externally with declared ECM hints.
    return _plan_once(matrix, side, target, range_hex, inbound, base_power, opponent_ecm_hint, combat_doctrine)


def _plan_quality(plan: dict[str, Any]):
    if plan.get("combat_doctrine") == UTILITY_COMBAT_DOCTRINE:
        return (int(plan.get("package_utility_milli",0)), int(plan.get("package_offense_utility_milli",0)), int(plan.get("package_defense_utility_milli",0)), 1 if plan.get("sensor_mode") != "passive" else 0)
    shots = sum(p is not None for p in plan["weapon_plans"])
    return (shots, int(plan["pds_rc"]), 1 if plan["track"] == "Firm" else 0, 1 if plan["track"] == "Approximate" else 0)


def _maybe_reactor_overload(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int, inbound: int,
                            base_power: int, opponent_ecm_hint: bool, combat_doctrine: str = LEGACY_COMBAT_DOCTRINE) -> tuple[dict[str, Any], int]:
    normal = _plan_turn(matrix, side, target, range_hex, inbound, base_power, opponent_ecm_hint, combat_doctrine)
    r = matrix.p("reactor", side.build.tl)
    gain = int(r.get("overloadGain", 0))
    limit = int(r.get("strainLimit", 0))
    if gain <= 0 or side.reactor_strain >= limit:
        return normal, base_power
    overloaded = _plan_turn(matrix, side, target, range_hex, inbound, base_power + gain, opponent_ecm_hint, combat_doctrine)
    if _plan_quality(overloaded) > _plan_quality(normal):
        side.telemetry.reactor_overload_requests += 1
        side.telemetry.reactor_overload_activations += 1
        side.telemetry.reactor_overload_power_unlocked += gain
        side.reactor_strain += 1
        side.telemetry.reactor_max_strain = max(side.telemetry.reactor_max_strain, side.reactor_strain)
        side.telemetry.power_available_total += gain
        return overloaded, base_power + gain
    return normal, base_power


def _record_plan(side: SideState, plan: dict[str, Any], available: int, inbound: int) -> None:
    t = side.telemetry
    mode = plan["sensor_mode"]
    if mode == "passive": t.passive_turns += 1
    elif mode == "low": t.active_low_turns += 1
    elif mode == "high": t.active_high_turns += 1
    if plan["track"] == "Firm": t.firm_track_turns += 1
    elif plan["track"] == "Approximate": t.approximate_track_turns += 1
    else: t.no_track_turns += 1
    if plan["ecm_on"]: t.ecm_active_turns += 1
    if plan["eccm_on"]: t.eccm_active_turns += 1
    if plan["ecm_downgrade"]: t.ecm_downgrade_events += 1
    if plan["eccm_restore"]: t.eccm_restore_events += 1
    if plan["burnthrough_preserved"]: t.burnthrough_preservation_events += 1
    if plan.get("combat_doctrine") in (CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE):
        if plan.get("opponent_weapon_knowledge") == "Unknown": t.cp146_unknown_opponent_turns += 1
        else: t.cp146_known_opponent_turns += 1
        if plan.get("sensor_mode") in ("low", "high"): t.cp146_active_sensor_default_turns += 1
        else: t.cp146_passive_sensor_fallback_turns += 1
        if plan.get("weapon_core_opportunity"):
            if any(x is not None for x in plan.get("weapon_plans", [])): t.cp146_weapon_core_funded_turns += 1
            else: t.cp146_weapon_core_starved_turns += 1
        if plan.get("pds_unknown_readiness") and int(plan.get("pds_power", 0)) > 0: t.cp146_pds_unknown_readiness_turns += 1
        if plan.get("pds_reason") in ("INBOUND", "KNOWN_SAME_TURN_TERMINAL") and int(plan.get("pds_power", 0)) > 0: t.cp146_pds_imminent_threat_turns += 1
        if plan.get("pds_reason") == "KNOWN_NON_MISSILE" and plan.get("pds") is not None: t.cp146_pds_irrelevant_suppressed_turns += 1
        if plan.get("hardener_reason") == "UNKNOWN_READINESS" and plan.get("hardener_active"): t.cp146_hardener_unknown_readiness_turns += 1
        if plan.get("hardener_reason") == "KNOWN_ENERGY_THREAT" and plan.get("hardener_active"): t.cp146_hardener_relevant_turns += 1
        if plan.get("hardener_reason") == "KNOWN_IRRELEVANT": t.cp146_hardener_irrelevant_suppressed_turns += 1
        if plan.get("held_main_declared"): t.cp146_held_main_declarations += 1
        if plan.get("combat_doctrine") == UTILITY_COMBAT_DOCTRINE:
            t.cp147_package_decisions += 1
            actions=plan.get("weapon_actions",[])
            if any(x=="ship" for x in actions): t.cp147_direct_package_selections += 1
            if any(x=="hold_missile" for x in actions): t.cp147_held_package_selections += 1
            if int(plan.get("pds_rc",0))>0 and bool(plan.get("pds_threat",False)): t.cp147_pds_package_selections += 1
            if plan.get("sensor_mode")=="passive": t.cp147_passive_utility_fallbacks += 1
            if int(plan.get("recovery_reserved_tp",0))>0:
                t.cp147_recovery_reserve_turns += 1
                t.cp147_recovery_reserved_tp += int(plan.get("recovery_reserved_tp",0))
            t.cp147_offense_utility_milli += int(plan.get("package_offense_utility_milli",0))
            t.cp147_defense_utility_milli += int(plan.get("package_defense_utility_milli",0))
            if int(plan.get("terminal_threat_subflights",0))>0: t.cp147_inbound_threat_turns += 1
            if bool(plan.get("critical_hull_threat",False)): t.cp147_terminal_hull_risk_turns += 1
            if side.known_opponent_missile_expected_raw_per_subflight>0: t.cp147_observed_threat_turns += 1
            if len(actions)==1 and any(x=="hold_missile" for x in actions) and bool(plan.get("weapon_core_opportunity",False)):
                t.cp147_sole_main_defensive_diversions += 1
                if not bool(plan.get("critical_hull_threat",False)):
                    t.cp147_sole_main_diversions_without_hull_risk += 1
    t.power_sensor += int(plan["sensor_cost"])
    t.power_ecm += int(plan["ecm_cost"])
    t.power_eccm += int(plan["eccm_cost"])
    t.power_pds += int(plan["pds_power"])
    t.power_shield_hardener += int(plan["hardener_power"])
    t.power_aux_energized_armor += int(plan.get("energized_armor_power",0)); t.power_aux_field_stabilizer += int(plan.get("field_stabilizer_power",0))
    if plan.get("energized_armor_active"): t.aux_energized_active_turns += 1
    if plan.get("field_stabilizer_active"): t.aux_field_stabilizer_active_turns += 1
    weapon_spend = sum(p[0] for p in plan["weapon_plans"] if p is not None)
    t.power_weapons += weapon_spend
    t.power_spent_total += int(plan["sensor_cost"]) + int(plan["ecm_cost"]) + int(plan["eccm_cost"]) + int(plan["hardener_power"]) + int(plan["pds_power"]) + int(plan.get("energized_armor_power",0)) + int(plan.get("field_stabilizer_power",0)) + weapon_spend
    for mode_name, wp in zip(plan.get("weapon_modes", []), plan["weapon_plans"]):
        if wp is None or mode_name is None:
            continue
        if mode_name == "Low": t.energy_low_shots += 1
        elif mode_name == "Standard": t.energy_standard_shots += 1
        elif mode_name == "Overload":
            t.energy_overload_shots += 1
            side.energy_weapon_strain += 1
            t.energy_overload_strain_added += 1
            t.energy_max_strain = max(t.energy_max_strain, side.energy_weapon_strain)
    if any(p is None for p in plan["weapon_plans"]) and plan["track"] in ("Firm", "Approximate"):
        t.weapon_power_shortfalls += 1
        t.power_shortfall_events += 1
    if plan["pds_threat"] and plan["pds"] is not None and plan["pds_rc"] == 0:
        t.pds_power_shortfalls += 1
        t.power_shortfall_events += 1
    if plan["track_no_ew"] != "None" and plan["sensor_mode"] == "passive" and available <= 0:
        t.acquisition_power_shortfalls += 1


def _hit_chance(matrix: CandidateMatrix, build: EcologyBuild, range_hex: int, accuracy: int,
                track: str = "Firm", standard_range: int | None = None, max_range: int | None = None) -> int:
    c = matrix.p("computer", build.tl)
    base = 50 + int(accuracy) + int(c["targetingPp"])
    if standard_range is None:
        profile = matrix.weapon_profile(build.weapon_family, build.tl)
        if "standardRange" not in profile:
            return max(5, min(95, base - 5 * range_hex))
        standard_range = int(profile["standardRange"])
        max_range = int(profile.get("maxRange", profile.get("range", standard_range)))
    modifier = 0
    if track == "Approximate":
        modifier += int(matrix.doc.get("combatModifiers", {}).get("directFireApproximateTrackPenaltyPp", -25))
    if range_hex > int(standard_range):
        modifier += int(matrix.doc.get("combatModifiers", {}).get("directFireExtendedRangePenaltyPp", -10))
    return max(5, min(95, base + modifier))


def _apply_damage(target: SideState, damage: int, spen: int, apen: int, shield_armor: int, source: str, turn: int = 0) -> dict[str, int]:
    """Apply the canonical SC/SA -> AI/AP -> Hull penetration-hardening model.

    Historical telemetry field names ``shield_armor_prevented`` and
    ``armor_prevented`` are retained as compatibility aliases. From the
    canonical penetration-hardening model onward they count penetration rating
    cancelled by SA/AP, not ordinary packet damage deleted by those ratings.
    ``armor_protection_damage`` remains zero because AP is no longer a
    destructible durability track.
    """
    t = target.telemetry
    t.damage_packets_resolved += 1
    before_shield = target.shield
    before_armor = target.armor_integrity
    before_hull = target.hull
    result = resolve_layered_damage(
        shield=target.shield,
        armor_integrity=target.armor_integrity,
        armor_protection=target.armor_protection,
        hull=target.hull,
        damage=int(damage),
        spen=int(spen),
        apen=int(apen),
        shield_armor=int(shield_armor),
    )
    target.shield = result.final_shield
    target.armor_integrity = result.final_armor_integrity
    target.hull = result.final_hull
    if before_shield > target.shield and t.first_shield_damage_turn == 0 and turn > 0:
        t.first_shield_damage_turn = turn
    if before_shield > 0 and target.shield == 0:
        t.shield_collapse_events += 1
        if t.first_shield_collapse_turn == 0 and turn > 0: t.first_shield_collapse_turn = turn
    if before_armor > target.armor_integrity and t.first_armor_damage_turn == 0 and turn > 0:
        t.first_armor_damage_turn = turn
    if before_armor > 0 and target.armor_integrity == 0:
        t.armor_collapse_events += 1
        if t.first_armor_collapse_turn == 0 and turn > 0: t.first_armor_collapse_turn = turn
    if before_hull > target.hull and t.first_hull_damage_turn == 0 and turn > 0:
        t.first_hull_damage_turn = turn

    t.raw_damage_on_hit += result.incoming_damage
    t.shield_penetration_bypassed += result.shield_bypass
    t.armor_penetration_bypassed += result.armor_bypass
    t.shield_armor_prevented += result.shield_penetration_resisted
    t.shield_absorbed += result.shield_absorbed
    t.armor_prevented += result.armor_penetration_resisted
    t.armor_integrity_damage += result.armor_absorbed
    # AP is hardening, not a second hit-point pool. Keep the legacy counter at 0.
    armor_protection_damage = 0
    t.armor_protection_damage += armor_protection_damage
    t.hull_damage += result.hull_damage
    if source == "direct":
        t.direct_raw_damage += result.incoming_damage
        t.direct_hull_damage += result.hull_damage
    else:
        t.missile_raw_damage += result.incoming_damage
        t.missile_hull_damage += result.hull_damage
    return {
        "damage_model": CANONICAL_DAMAGE_MODEL,
        "shield_armor_prevented": result.shield_penetration_resisted,
        "shield_penetration_hardened": result.shield_penetration_resisted,
        "shield_absorbed": result.shield_absorbed,
        "shield_bypass": result.shield_bypass,
        "armor_prevented": result.armor_penetration_resisted,
        "armor_penetration_hardened": result.armor_penetration_resisted,
        "armor_integrity": result.armor_absorbed,
        "armor_protection": 0,
        "armor_bypass": result.armor_bypass,
        "hull": result.hull_damage,
    }


def _apply_armor_regeneration(matrix: CandidateMatrix, side: SideState, available_power: int) -> int:
    profile = _armor_profile(matrix, side.build)
    per_tp = int(profile.get("tacticalRegenerationPerTp", 0))
    cap_tp = int(profile.get("tacticalRegenerationCapTp", 0))
    if per_tp <= 0 or cap_tp <= 0 or side.armor_integrity >= side.armor_max:
        return 0
    side.telemetry.armor_regen_opportunities += 1
    if side.armor_regen_reserve_remaining == 0:
        side.telemetry.armor_regen_denied_exhausted += 1
        if not side.armor_regen_reserve_exhaustion_recorded:
            side.telemetry.armor_regen_reserve_exhaustions += 1
            side.armor_regen_reserve_exhaustion_recorded = True
        return 0
    missing = side.armor_max - side.armor_integrity
    max_restore = missing if side.armor_regen_reserve_remaining < 0 else min(missing, side.armor_regen_reserve_remaining)
    spend = min(cap_tp, max(0, int(available_power)), math.ceil(max_restore / per_tp))
    if spend <= 0:
        return 0
    restored = min(max_restore, spend * per_tp)
    side.armor_integrity += restored
    if side.armor_regen_reserve_remaining >= 0:
        side.armor_regen_reserve_remaining -= restored
        side.telemetry.armor_regen_reserve_spent += restored
    side.telemetry.armor_regen_tp_spent += spend
    side.telemetry.armor_regen_restored += restored
    side.telemetry.power_spent_total += spend
    if side.armor_regen_reserve_remaining == 0 and not side.armor_regen_reserve_exhaustion_recorded:
        side.telemetry.armor_regen_reserve_exhaustions += 1
        side.armor_regen_reserve_exhaustion_recorded = True
    return spend


def _attempt_hull_damage_control(matrix: CandidateMatrix, side: SideState, available_power: int, roll: int) -> int:
    """Hull-only CP135 Damage Control doctrine. Returns TP spent (0 or 1)."""
    if side.hull <= 0 or side.hull >= side.hull_max or side.repair_kits_remaining <= 0:
        return 0
    dc = matrix.p("damage_control", side.build.tl)
    tp_cost = int(dc.get("attemptTp", 1))
    if tp_cost <= 0 or available_power < tp_cost:
        return 0
    side.telemetry.damage_control_attempts += 1
    side.telemetry.damage_control_kits_consumed += 1
    side.telemetry.damage_control_tp_spent += tp_cost
    side.telemetry.power_spent_total += tp_cost
    side.repair_kits_remaining -= 1
    drone = _cp158_aux_kind(matrix, side.build, "repair_drone")
    bonus = int(drone.get("chance_bonus_pp",0)) if drone is not None else 0
    if bonus: side.telemetry.aux_damage_control_bonus_attempts += 1
    if int(roll) <= min(100, int(dc.get("hullRepairChancePp", 0)) + bonus):
        side.telemetry.damage_control_successes += 1
        queued = min(max(0, side.hull_max - side.hull), int(dc.get("hullRestoredPerSuccessfulKit", 1)))
        side.pending_hull_repair += queued
        side.telemetry.damage_control_hull_queued += queued
    return tp_cost


def _shield_armor(matrix: CandidateMatrix, side: SideState, hardener_active: bool = False) -> int:
    if not side.build.shield or side.shield <= 0:
        return 0
    base = int(matrix.p("shield", side.build.tl).get("shieldArmor", 0))
    if hardener_active:
        # Damage-resolution scale studies may raise the integer granularity while
        # keeping the hardener's legacy-equivalent Shield Armor unchanged.
        # Production CandidateMatrix instances have no damage_scale attribute.
        hardener_armor = max(1, int(getattr(matrix, "damage_scale", 1)))
        return max(base, hardener_armor)
    return base


def run_trial(matrix: CandidateMatrix, variant: EcologyVariant, master_seed: int, trial_index: int,
              event_sink: list[dict[str, Any]] | None = None) -> EcologyTrialResult:
    try:
        a = _create_side(matrix, variant.side_a, variant.start_q_a)
        b = _create_side(matrix, variant.side_b, variant.start_q_b)
        rng = XorShift64(derive_seed(master_seed, variant.id, trial_index))
        missiles: list[MissileState] = []
        overall_min = _range(a, b)
        for turn in range(1, variant.max_turns + 1):
            inbound_a = sum(m.owner == "B" for m in missiles)
            inbound_b = sum(m.owner == "A" for m in missiles)
            power_a, _ = _begin_turn_recharge(matrix, a, b, inbound_a)
            power_b, _ = _begin_turn_recharge(matrix, b, a, inbound_b)

            # Movement uses only previously acquired contact; before contact each ship searches one hex toward map center.
            if variant.movement_order == "SideAFirst":
                _move_one(a, b, matrix, a.contact)
                _move_one(b, a, matrix, b.contact)
            else:
                _move_one(b, a, matrix, b.contact)
                _move_one(a, b, matrix, a.contact)
            range_hex = _range(a, b)
            overall_min = min(overall_min, range_hex)
            a.telemetry.min_range = min(a.telemetry.min_range, range_hex)
            b.telemetry.min_range = min(b.telemetry.min_range, range_hex)

            # First-pass ECM declarations are affordability-based and do not inspect hidden opponent ratings.
            pre_a = _plan_once(matrix, a, b, range_hex, inbound_a, power_a, False)
            pre_b = _plan_once(matrix, b, a, range_hex, inbound_b, power_b, False)
            ecm_a = pre_a["ecm_on"]
            ecm_b = pre_b["ecm_on"]

            pa, _ = _maybe_reactor_overload(matrix, a, b, range_hex, inbound_a, power_a, ecm_b)
            pb, _ = _maybe_reactor_overload(matrix, b, a, range_hex, inbound_b, power_b, ecm_a)
            _record_plan(a, pa, power_a, inbound_a)
            _record_plan(b, pb, power_b, inbound_b)

            a.last_track = pa["track"]
            b.last_track = pb["track"]
            if pa["track"] != "None": a.contact = True
            if pb["track"] != "None": b.contact = True

            commits: list[tuple[str, SideState, bool, int, int, int, bool]] = []
            for label, side, target, plan in (("A", a, b, pa), ("B", b, a, pb)):
                w = _weapon(matrix, side.build)
                if w["family"] == "Missile":
                    if plan["track"] == "Firm" and range_hex <= int(w["range"]):
                        side.telemetry.missile_launch_eligible_actions += int(w["count"])
                        for wp in plan["weapon_plans"]:
                            if wp is None:
                                continue
                            if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                                continue
                            if side.weapon_ammo is not None:
                                side.weapon_ammo -= 1
                            eta = max(1, math.ceil(range_hex / max(1, int(w["missile_move"]))))
                            missiles.append(MissileState(label, eta, int(w["damage"]), int(w["spen"]), int(w["apen"]), int(w["guidance"]), int(w.get("packets", 1)), int(w.get("pds_intercept_penalty_pp", 0)), str(w.get("profile_id", "GP"))))
                            side.telemetry.missile_launches += 1
                            if str(w.get("profile_id", "GP")) == "GP":
                                side.telemetry.payload_gp_launches += 1
                            else:
                                side.telemetry.payload_specialist_launches += 1
                            side.demonstrated_range = max(side.demonstrated_range, range_hex)
                    continue
                if plan["track"] != "Firm" or range_hex > int(w["range"]):
                    continue
                side.telemetry.direct_fire_eligible_actions += int(w["count"])
                for wp in plan["weapon_plans"]:
                    if wp is None:
                        continue
                    if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                        continue
                    if side.weapon_ammo is not None:
                        side.weapon_ammo -= 1
                    _, damage, accuracy = wp
                    chance = _hit_chance(matrix, side.build, range_hex, accuracy)
                    hit = rng.d100() <= chance
                    side.telemetry.direct_shots += 1
                    if hit:
                        side.telemetry.direct_hits += 1
                    target_plan = pb if label == "A" else pa
                    commits.append((label, target, hit, int(damage), int(w["spen"]), int(w["apen"]), bool(target_plan["hardener_active"])))
                    side.demonstrated_range = max(side.demonstrated_range, range_hex)
                    if event_sink is not None:
                        event_sink.append({"turn": turn, "event": "direct_fire", "side": label, "range": range_hex, "chance": chance, "hit": hit, "damage": int(damage)})
            for label, target, hit, damage, spen, apen, target_hardener in commits:
                if hit:
                    _apply_damage(target, damage, spen, apen, _shield_armor(matrix, target, target_hardener), "direct")
                    target.contact = True

            # Missile flight and terminal defense.
            for m in missiles:
                m.eta -= 1
            terminal = [m for m in missiles if m.eta <= 0]
            if terminal:
                for target_label, target, plan in (("A", a, pa), ("B", b, pb)):
                    threats = [m for m in terminal if m.owner != target_label]
                    reaction_used = 0
                    intercepted: set[int] = set()
                    pds = plan["pds"]
                    for m in threats:
                        target.telemetry.missile_terminal_arrivals += 1
                        attempts_on_flight = 0
                        while reaction_used < int(plan["pds_rc"]) and attempts_on_flight < 2:
                            if target.pds_ammo is not None and target.pds_ammo <= 0:
                                break
                            target.telemetry.pds_attempts += 1
                            reaction_used += 1
                            attempts_on_flight += 1
                            if target.pds_ammo is not None:
                                target.pds_ammo -= 1
                            chance = 0
                            if pds is not None:
                                chance = min(95, int(pds["baseChancePp"]) + int(matrix.p("computer", target.build.tl)["targetingPp"]))
                            chance = max(0, chance - int(m.pds_intercept_penalty_pp))
                            if rng.d100() <= chance:
                                target.telemetry.pds_intercepts += 1
                                intercepted.add(id(m))
                                if event_sink is not None:
                                    event_sink.append({"turn": turn, "event": "pds_intercept", "target": target_label, "chance": chance})
                                break
                        if id(m) in intercepted:
                            continue
                        target.telemetry.missile_guidance_attempts += 1
                        if rng.d100() <= int(m.guidance):
                            target.telemetry.missile_hits += 1
                            for _ in range(max(1, int(m.packets))):
                                _apply_damage(target, m.damage, m.spen, m.apen, _shield_armor(matrix, target, bool(plan["hardener_active"])), "missile")
                            target.contact = True
                            if event_sink is not None:
                                event_sink.append({"turn": turn, "event": "missile_hit", "target": target_label, "damage": m.damage})
                missiles = [m for m in missiles if m.eta > 0]

            if a.hull <= 0 or b.hull <= 0:
                winner = "Draw" if a.hull <= 0 and b.hull <= 0 else ("B" if a.hull <= 0 else "A")
                return EcologyTrialResult(winner, False, turn, range_hex, overall_min, a.hull, b.hull, a.armor_integrity, b.armor_integrity, a.shield, b.shield, a.telemetry, b.telemetry)

        return EcologyTrialResult("Unresolved", True, variant.max_turns, _range(a, b), overall_min, a.hull, b.hull, a.armor_integrity, b.armor_integrity, a.shield, b.shield, a.telemetry, b.telemetry)
    except Exception as exc:
        blank = SideTelemetry()
        return EcologyTrialResult("Error", False, 0, 10, 10, 0, 0, 0, 0, 0, 0, blank, blank, f"{type(exc).__name__}: {exc}")


_WORKER_MATRIX: CandidateMatrix | None = None


def _init_worker(repo: str):
    global _WORKER_MATRIX
    _WORKER_MATRIX = CandidateMatrix(Path(repo))


def _mean_side(results: list[EcologyTrialResult], side: str, name: str) -> float:
    vals = [getattr(r.side_a if side == "a" else r.side_b, name) for r in results if not r.error]
    return statistics.fmean(vals) if vals else 0.0


def _aggregate_variant(variant: EcologyVariant, results: list[EcologyTrialResult]) -> dict[str, Any]:
    n = len(results)
    valid = [r for r in results if not r.error]
    wins = {k: sum(1 for r in results if r.winner == k) for k in ("A", "B", "Draw", "Unresolved", "Error")}
    row: dict[str, Any] = {
        "variant_id": variant.id, "tl": variant.tl, "movement_order": variant.movement_order, "geometry": variant.geometry,
        "population": variant.population, "damage_model": DAMAGE_MODEL, "start_range": abs(variant.start_q_b - variant.start_q_a),
        "max_turns": variant.max_turns, "scenario_group": variant.scenario_group, "perturbation": variant.perturbation,
        "side_a_build": variant.side_a.id, "side_b_build": variant.side_b.id,
        "side_a_family": variant.side_a.weapon_family, "side_b_family": variant.side_b.weapon_family,
        "side_a_archetype": variant.side_a.archetype, "side_b_archetype": variant.side_b.archetype,
        "trials": n, "wins_a": wins["A"], "wins_b": wins["B"], "draws": wins["Draw"], "unresolved": wins["Unresolved"], "errors": wins["Error"],
        "win_rate_a": wins["A"] / n if n else 0.0, "win_rate_b": wins["B"] / n if n else 0.0,
        "draw_rate": wins["Draw"] / n if n else 0.0, "unresolved_rate": wins["Unresolved"] / n if n else 0.0,
        "conditional_win_rate_a": wins["A"] / max(1, wins["A"] + wins["B"]),
        "mean_turns": statistics.fmean(r.turns for r in valid) if valid else 0.0,
        "mean_final_range": statistics.fmean(r.final_range for r in valid) if valid else 0.0,
        "mean_min_range": statistics.fmean(r.min_range for r in valid) if valid else 0.0,
        "first_error": next((r.error for r in results if r.error), ""),
    }
    for side in ("a", "b"):
        prefix = f"mean_{side}_"
        for f in fields(SideTelemetry):
            row[prefix + f.name] = _mean_side(results, side, f.name)
    return row


def _run_variant_task(args):
    variant, master_seed, trials = args
    assert _WORKER_MATRIX is not None
    results = [run_trial(_WORKER_MATRIX, variant, master_seed, i) for i in range(trials)]
    return _aggregate_variant(variant, results)


def _run_chunk(args):
    variants, master_seed, trials = args
    return [_run_variant_task((v, master_seed, trials)) for v in variants]


def execute_variants(repo: Path, variants: list[EcologyVariant], master_seed: int, trials: int, jobs: int) -> tuple[list[dict[str, Any]], float]:
    jobs = max(1, min(jobs, len(variants)))
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if jobs == 1:
        _init_worker(str(repo))
        rows = [_run_variant_task((v, master_seed, trials)) for v in variants]
    else:
        chunk_count = min(len(variants), max(jobs, jobs * 4))
        chunks = [[] for _ in range(chunk_count)]
        for i, variant in enumerate(variants):
            chunks[i % chunk_count].append(variant)
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_init_worker, initargs=(str(repo),)) as ex:
            futures = [ex.submit(_run_chunk, (chunk, master_seed, trials)) for chunk in chunks if chunk]
            for f in as_completed(futures):
                rows.extend(f.result())
    rows.sort(key=lambda r: r["variant_id"])
    return rows, time.perf_counter() - started


def _write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _build_rows(builds: list[EcologyBuild]) -> list[dict[str, Any]]:
    return [
        {
            "build_id": b.id, "tl": b.tl, "archetype": b.archetype, "weapon_family": b.weapon_family,
            "main_count": b.main_count, "reactor_count": b.reactor_count, "shield": b.shield, "ecm": b.ecm,
            "eccm": b.eccm, "pds_family": b.pds_family or "", "shield_hardener": b.shield_hardener, "missile_payload": b.missile_payload,
            "combat_space": b.combat_space, "mission_aux_space": b.mission_aux_space, "used_space": b.used_space,
            "capacity": b.capacity, "free_space": b.capacity - b.used_space,
        }
        for b in builds
    ]


def _matched_bundle_rows(variant_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for r in variant_rows:
        base = r["variant_id"].rsplit("-", 1)[0]
        groups.setdefault(base, []).append(r)
    out = []
    for key, rows in sorted(groups.items()):
        if len(rows) != 2:
            continue
        a = rows[0]
        # Normalize Side A build's win rate across movement-order mirrors; orientation is fixed by construction.
        out.append({
            "bundle_id": key, "tl": int(a["tl"]), "side_a_build": a["side_a_build"], "side_b_build": a["side_b_build"],
            "side_a_family": a["side_a_family"], "side_b_family": a["side_b_family"],
            "side_a_archetype": a["side_a_archetype"], "side_b_archetype": a["side_b_archetype"],
            "variants": 2,
            "side_a_conditional_win_rate": statistics.fmean(float(r["conditional_win_rate_a"]) for r in rows),
            "unresolved_rate": statistics.fmean(float(r["unresolved_rate"]) for r in rows),
            "mean_turns": statistics.fmean(float(r["mean_turns"]) for r in rows),
            "movement_order_swing": abs(float(rows[0]["conditional_win_rate_a"]) - float(rows[1]["conditional_win_rate_a"])),
            "mean_power_shortfalls": statistics.fmean((float(r["mean_a_power_shortfall_events"]) + float(r["mean_b_power_shortfall_events"])) / 2 for r in rows),
            "mean_power_spent": statistics.fmean((float(r["mean_a_power_spent_total"]) + float(r["mean_b_power_spent_total"])) / 2 for r in rows),
            "mean_firm_track_turns": statistics.fmean((float(r["mean_a_firm_track_turns"]) + float(r["mean_b_firm_track_turns"])) / 2 for r in rows),
            "mean_approximate_track_turns": statistics.fmean((float(r["mean_a_approximate_track_turns"]) + float(r["mean_b_approximate_track_turns"])) / 2 for r in rows),
            "mean_ecm_downgrades": statistics.fmean((float(r["mean_a_ecm_downgrade_events"]) + float(r["mean_b_ecm_downgrade_events"])) / 2 for r in rows),
            "mean_eccm_restores": statistics.fmean((float(r["mean_a_eccm_restore_events"]) + float(r["mean_b_eccm_restore_events"])) / 2 for r in rows),
            "mean_reactor_overloads": statistics.fmean((float(r["mean_a_reactor_overload_activations"]) + float(r["mean_b_reactor_overload_activations"])) / 2 for r in rows),
            "mean_direct_shots": statistics.fmean((float(r["mean_a_direct_shots"]) + float(r["mean_b_direct_shots"])) / 2 for r in rows),
            "mean_direct_hits": statistics.fmean((float(r["mean_a_direct_hits"]) + float(r["mean_b_direct_hits"])) / 2 for r in rows),
            "mean_missile_launches": statistics.fmean((float(r["mean_a_missile_launches"]) + float(r["mean_b_missile_launches"])) / 2 for r in rows),
            "mean_missile_hits": statistics.fmean((float(r["mean_a_missile_hits"]) + float(r["mean_b_missile_hits"])) / 2 for r in rows),
            "mean_pds_attempts": statistics.fmean((float(r["mean_a_pds_attempts"]) + float(r["mean_b_pds_attempts"])) / 2 for r in rows),
            "mean_pds_intercepts": statistics.fmean((float(r["mean_a_pds_intercepts"]) + float(r["mean_b_pds_intercepts"])) / 2 for r in rows),
            "mean_shield_absorbed": statistics.fmean((float(r["mean_a_shield_absorbed"]) + float(r["mean_b_shield_absorbed"])) / 2 for r in rows),
            "mean_armor_prevented": statistics.fmean((float(r["mean_a_armor_prevented"]) + float(r["mean_b_armor_prevented"])) / 2 for r in rows),
            "mean_hull_damage": statistics.fmean((float(r["mean_a_hull_damage"]) + float(r["mean_b_hull_damage"])) / 2 for r in rows),
        })
    return out



def _build_mechanics_rows(builds: list[EcologyBuild], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    telemetry_names = [f.name for f in fields(SideTelemetry)]
    accum: dict[str, dict[str, list[float]]] = {b.id: {name: [] for name in telemetry_names} for b in builds}
    turns: dict[str, list[float]] = {b.id: [] for b in builds}
    unresolved: dict[str, list[float]] = {b.id: [] for b in builds}
    for row in rows:
        for side in ("a", "b"):
            bid = str(row[f"side_{side}_build"])
            turns[bid].append(float(row["mean_turns"]))
            unresolved[bid].append(float(row["unresolved_rate"]))
            for name in telemetry_names:
                accum[bid][name].append(float(row[f"mean_{side}_{name}"]))
    bmap = {b.id: b for b in builds}
    out: list[dict[str, Any]] = []
    for bid in sorted(accum):
        b = bmap[bid]
        row: dict[str, Any] = {
            "build_id": bid, "tl": b.tl, "family": b.weapon_family, "archetype": b.archetype,
            "main_count": b.main_count, "reactor_count": b.reactor_count, "mission_aux_space": b.mission_aux_space,
            "variant_appearances": len(turns[bid]),
            "mean_turns": statistics.fmean(turns[bid]) if turns[bid] else 0.0,
            "mean_unresolved_rate": statistics.fmean(unresolved[bid]) if unresolved[bid] else 0.0,
        }
        for name in telemetry_names:
            vals = accum[bid][name]
            row[f"mean_{name}"] = statistics.fmean(vals) if vals else 0.0
        out.append(row)
    return out

def _analysis(builds: list[EcologyBuild], variants: list[EcologyVariant], rows: list[dict[str, Any]], trials: int, elapsed: float) -> dict[str, Any]:
    failures: list[str] = []
    if any(int(r["errors"]) for r in rows):
        failures.append("trial-errors")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("exact-fill")
    by_tl = {tl: [b for b in builds if b.tl == tl] for tl in range(1, 10)}
    if any(len(v) < 9 for v in by_tl.values()):
        failures.append("minimum-builds-per-tl")
    if any({b.weapon_family for b in v} != {"Kinetic", "Energy", "Missile"} for v in by_tl.values()):
        failures.append("family-coverage")
    bundles = _matched_bundle_rows(rows)
    if len(bundles) * 2 != len(rows):
        failures.append("movement-mirror-shape")

    # Instrumentation gates require the study to actually exercise each major current mechanic.
    sums = {}
    telemetry_names = [f.name for f in fields(SideTelemetry)]
    for name in telemetry_names:
        sums[name] = sum(float(r[f"mean_a_{name}"]) + float(r[f"mean_b_{name}"]) for r in rows)
    required_nonzero = [
        "movement_hexes", "movement_fuel", "track_driven_closure_hexes", "active_low_turns", "firm_track_turns", "approximate_track_turns",
        "ecm_active_turns", "eccm_active_turns", "ecm_downgrade_events", "eccm_restore_events", "burnthrough_preservation_events",
        "reactor_overload_activations", "power_sensor", "power_ecm", "power_eccm", "power_pds", "power_weapons",
        "power_shield_recharge", "power_shield_hardener", "shield_base_restored", "shield_tactical_restored", "direct_shots", "direct_hits",
        "missile_launches", "missile_terminal_arrivals", "missile_guidance_attempts", "missile_hits", "pds_attempts",
        "pds_intercepts", "shield_absorbed", "armor_prevented", "armor_integrity_damage", "hull_damage",
    ]
    missing = [name for name in required_nonzero if sums.get(name, 0.0) <= 0.0]
    if missing:
        failures.append("instrumentation-nonzero:" + ",".join(missing))

    # No internal damage/critical telemetry exists in this consumer by design.
    tl_summary = []
    for tl in range(1, 10):
        tr = [r for r in rows if int(r["tl"]) == tl]
        br = [b for b in bundles if int(b["tl"]) == tl]
        tl_summary.append({
            "tl": tl, "builds": len(by_tl[tl]), "variants": len(tr), "bundles": len(br),
            "mean_unresolved_rate": statistics.fmean(float(r["unresolved_rate"]) for r in tr) if tr else 0.0,
            "mean_turns": statistics.fmean(float(r["mean_turns"]) for r in tr) if tr else 0.0,
            "mean_movement_order_swing": statistics.fmean(float(b["movement_order_swing"]) for b in br) if br else 0.0,
            "max_movement_order_swing": max((float(b["movement_order_swing"]) for b in br), default=0.0),
            "mean_mission_aux_space": statistics.fmean(b.mission_aux_space for b in by_tl[tl]),
        })

    # Build robustness is descriptive only. It is intentionally not a pass/fail balance target.
    opponent_rows: dict[str, list[float]] = {}
    for b in bundles:
        a = b["side_a_build"]; c = b["side_b_build"]
        wa = float(b["side_a_conditional_win_rate"])
        opponent_rows.setdefault(a, []).append(wa)
        opponent_rows.setdefault(c, []).append(1.0 - wa)
    build_summary = []
    build_map = {b.id: b for b in builds}
    for bid, vals in sorted(opponent_rows.items()):
        b = build_map[bid]
        build_summary.append({
            "build_id": bid, "tl": b.tl, "family": b.weapon_family, "archetype": b.archetype,
            "opponents": len(vals), "mean_conditional_win_rate": statistics.fmean(vals),
            "min_matchup_win_rate": min(vals), "max_matchup_win_rate": max(vals),
            "mission_aux_space": b.mission_aux_space,
            "dominance_review_signal": statistics.fmean(vals) >= 0.75,
            "weakness_review_signal": statistics.fmean(vals) <= 0.25,
        })

    family_rows = []
    fg: dict[tuple[int, str, str], list[float]] = {}
    for b in bundles:
        if str(b["side_a_family"]) == str(b["side_b_family"]):
            continue
        k = (int(b["tl"]), str(b["side_a_family"]), str(b["side_b_family"]))
        fg.setdefault(k, []).append(float(b["side_a_conditional_win_rate"]))
    for (tl, fa, fb), vals in sorted(fg.items()):
        family_rows.append({"tl": tl, "family_a": fa, "family_b": fb, "bundles": len(vals), "mean_family_a_conditional_win_rate": statistics.fmean(vals)})

    build_mechanics = _build_mechanics_rows(builds, rows)
    movement_flags = [b for b in bundles if float(b["movement_order_swing"]) >= 0.15]
    dominance_flags = [b for b in build_summary if b["dominance_review_signal"]]
    weakness_flags = [b for b in build_summary if b["weakness_review_signal"]]

    return {
        "schemaVersion": "star-cluster-same-tl-build-ecology-results-v0.1",
        "checkpoint": "111",
        "damageModel": DAMAGE_MODEL,
        "internalDamageCriticalsSimulated": False,
        "primaryPopulation": "same_tl_frontier_exact_fill",
        "mixedTlPopulationExecuted": False,
        "builds": len(builds), "variants": len(variants), "movementNeutralBundles": len(bundles),
        "trialsPerVariant": trials, "totalTrials": trials * len(rows), "elapsedSeconds": elapsed,
        "tlSummary": tl_summary,
        "instrumentationTotals": sums,
        "reviewSignals": {
            "movementOrderSensitiveBundlesAt15pp": len(movement_flags),
            "dominantBuildCandidatesAt75pctMean": len(dominance_flags),
            "weakBuildCandidatesAt25pctMean": len(weakness_flags),
            "balanceSignalsAreBlockingGates": False,
        },
        "failedGates": failures,
        "automaticPromotion": False,
        "interpretation": "Instrumentation/ecology evidence only. CP111 does not calibrate or promote CP109 numerical candidates. Exact-fill mission AUX space has zero tactical effect and records capacity that a player would plausibly spend on not-yet-numerical support systems rather than leaving empty.",
        "_bundleRows": bundles,
        "_buildSummary": build_summary,
        "_buildMechanics": build_mechanics,
        "_familyRows": family_rows,
    }



def run_overload_instrumentation_probes(repo: Path, outdir: Path) -> dict[str, Any]:
    """Zero-weight deterministic probes for overload value/accounting paths.

    The primary ecology doctrine intentionally uses only safe Reactor overload. These
    microprobes prove that the accepted/component-defined STL, Active Sensor, ECM,
    ECCM, and Reactor overload effects remain observable without allowing them to
    bias same-TL ecology results before an overload doctrine is separately reviewed.
    """
    matrix = CandidateMatrix(repo)
    rows: list[dict[str, Any]] = []

    stl = matrix.p("stl", 1)
    normal_move = int(stl["move"])
    overloaded_move = normal_move + int(stl["overloadMoveBonus"])
    rows.append({
        "probe_id": "stl-overload-i", "subsystem": "STL", "tl": 1,
        "normal_value": normal_move, "overloaded_value": overloaded_move,
        "normal_tp": 0, "overloaded_tp": int(stl["overloadTp"]),
        "extra_fuel": int(stl["overloadExtraFuel"]), "strain_added": 1,
        "observable_effect": f"Move {normal_move}->{overloaded_move}; +{int(stl['overloadExtraFuel'])} overload fuel",
        "passed": overloaded_move > normal_move and int(stl["strainLimit"]) >= 1,
    })

    sensor = matrix.p("sensor", 1)
    normal_firm = int(sensor["activeLowFirm"])
    overload_firm = int(sensor["overloadFirm"])
    overload_approx = int(sensor["overloadApprox"])
    # The accepted TL1 Overload-I contract is 3 TP total and reach-only.
    rows.append({
        "probe_id": "active-sensor-overload-i", "subsystem": "Sensor", "tl": 1,
        "normal_value": normal_firm, "overloaded_value": overload_firm,
        "normal_tp": int(sensor["activeLowTp"]), "overloaded_tp": 3,
        "extra_fuel": 0, "strain_added": 1,
        "observable_effect": f"Firm/Approx {normal_firm}/{int(sensor['activeLowApprox'])}->{overload_firm}/{overload_approx}; range only",
        "passed": overload_firm > normal_firm and overload_approx > int(sensor["activeLowApprox"]),
    })

    ecm = matrix.p("ecm", 1)
    rows.append({
        "probe_id": "ecm-overload-i", "subsystem": "ECM", "tl": 1,
        "normal_value": int(ecm["rating"]), "overloaded_value": int(ecm["rating"]) + int(ecm["overloadBonusRating"]),
        "normal_tp": int(ecm["fullStrengthTp"]), "overloaded_tp": int(ecm["fullStrengthTp"]) + int(ecm["overloadAdditionalTp"]),
        "extra_fuel": 0, "strain_added": 1,
        "observable_effect": "ECM rating increases by one for the remainder of the turn",
        "passed": int(ecm["overloadBonusRating"]) == 1 and int(ecm["strainLimit"]) >= 1,
    })

    eccm = matrix.p("eccm", 1)
    # Under DR0, hostile ECM2 downgrades Firm; ECCM2 restores it. This makes the
    # overload effect observable without reading a hidden jamming-margin value.
    hostile_ecm = 2
    normal_net = max(0, hostile_ecm - int(eccm["rating"]))
    overload_rating = int(eccm["rating"]) + int(eccm["overloadBonusRating"])
    overload_net = max(0, hostile_ecm - overload_rating)
    rows.append({
        "probe_id": "eccm-overload-i", "subsystem": "ECCM", "tl": 1,
        "normal_value": int(eccm["rating"]), "overloaded_value": overload_rating,
        "normal_tp": int(eccm["fullStrengthTp"]), "overloaded_tp": int(eccm["fullStrengthTp"]) + int(eccm["overloadAdditionalTp"]),
        "extra_fuel": 0, "strain_added": 1,
        "observable_effect": f"Against ECM2/DR0: residual jamming {normal_net}->{overload_net}; Firm restoration becomes possible",
        "passed": normal_net > 0 and overload_net == 0 and int(eccm["strainLimit"]) >= 1,
    })

    reactor = matrix.p("reactor", 1)
    rows.append({
        "probe_id": "reactor-overload-i", "subsystem": "Reactor", "tl": 1,
        "normal_value": int(reactor["operationalTp"]), "overloaded_value": int(reactor["operationalTp"]) + int(reactor["overloadGain"]),
        "normal_tp": int(reactor["operationalTp"]), "overloaded_tp": int(reactor["operationalTp"]) + int(reactor["overloadGain"]),
        "extra_fuel": 0, "strain_added": 1,
        "observable_effect": f"Available Tactical Power +{int(reactor['overloadGain'])} for the turn",
        "passed": int(reactor["overloadGain"]) > 0 and int(reactor["strainLimit"]) >= 1,
    })

    _write_csv(outdir / "overload_instrumentation_probes.csv", rows)
    failures = [str(r["probe_id"]) for r in rows if not bool(r["passed"])]
    return {"probes": len(rows), "passed": len(rows) - len(failures), "failed": failures}

def run_instrumentation_probes(repo: Path, outdir: Path) -> dict[str, Any]:
    """Deterministic, tiny probes whose purpose is to prove event/counter plumbing, not balance."""
    matrix = CandidateMatrix(repo)
    builds = generate_primary_builds(matrix)
    bmap = {b.id: b for b in builds}
    probes: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []

    def do(pid: str, a: str, b: str, seed: int, repetitions: int = 1):
        v = EcologyVariant(pid, bmap[a].tl, bmap[a], bmap[b], "SideAFirst", population="instrumentation_probe_zero_weight")
        totals = {"direct_shots":0, "missile_launches":0, "pds_attempts":0, "ecm_downgrades":0, "eccm_restores":0, "reactor_overloads":0, "hull_damage":0}
        first = None
        errors = []
        for i in range(repetitions):
            local_events: list[dict[str, Any]] = []
            r = run_trial(matrix, v, seed, i, local_events)
            if first is None: first = r
            if r.error: errors.append(r.error)
            totals["direct_shots"] += r.side_a.direct_shots + r.side_b.direct_shots
            totals["missile_launches"] += r.side_a.missile_launches + r.side_b.missile_launches
            totals["pds_attempts"] += r.side_a.pds_attempts + r.side_b.pds_attempts
            totals["ecm_downgrades"] += r.side_a.ecm_downgrade_events + r.side_b.ecm_downgrade_events
            totals["eccm_restores"] += r.side_a.eccm_restore_events + r.side_b.eccm_restore_events
            totals["reactor_overloads"] += r.side_a.reactor_overload_activations + r.side_b.reactor_overload_activations
            totals["hull_damage"] += r.side_a.hull_damage + r.side_b.hull_damage
            if i == 0:
                for e in local_events:
                    events.append({"probe_id": pid, **e})
        assert first is not None
        probes.append({
            "probe_id": pid, "side_a": a, "side_b": b, "repetitions": repetitions, "winner_first": first.winner, "turns_first": first.turns, "error": "; ".join(errors[:1]),
            **totals,
        })

    do("tl1-kinetic-vs-energy", "tl1-kinetic-balanced", "tl1-energy-balanced", 111001, 4)
    do("tl3-missile-vs-amm", "tl3-missile-balanced", "tl3-missile-missile-defense", 111002, 32)
    do("tl5-ew-vs-balanced", "tl5-kinetic-ew-specialist", "tl5-energy-balanced", 111003, 8)
    do("tl9-power-vs-dual-main", "tl9-energy-dual-reactor", "tl9-energy-dual-main", 111004, 8)

    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "instrumentation_probes.csv", probes)
    with (outdir / "probe_events.jsonl").open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, sort_keys=True) + "\n")
    failures = []
    if any(p["error"] for p in probes):
        failures.append("probe-errors")
    if sum(p["direct_shots"] for p in probes) <= 0:
        failures.append("probe-direct-fire")
    if sum(p["missile_launches"] for p in probes) <= 0 or sum(p["pds_attempts"] for p in probes) <= 0:
        failures.append("probe-missile-pds")
    overload = run_overload_instrumentation_probes(repo, outdir)
    if overload["failed"]:
        failures.append("probe-overload:" + ",".join(overload["failed"]))
    return {"probes": len(probes), "events": len(events), "overloadProbes": overload, "failedGates": failures}


def run_ecology(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 1) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise RuntimeError("ecology study validation failed: " + "; ".join(errors))
    matrix = CandidateMatrix(repo)
    builds = generate_primary_builds(matrix)
    variants = generate_primary_variants(builds)
    trials = int(trials_override if trials_override is not None else doc["trialsPerVariant"])
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "builds.csv", _build_rows(builds))
    probe = run_instrumentation_probes(repo, outdir)
    rows, elapsed = execute_variants(repo, variants, int(doc["masterSeed"]), trials, jobs)
    _write_csv(outdir / "variants.csv", rows)
    analysis = _analysis(builds, variants, rows, trials, elapsed)
    bundles = analysis.pop("_bundleRows")
    build_summary = analysis.pop("_buildSummary")
    build_mechanics = analysis.pop("_buildMechanics")
    family_rows = analysis.pop("_familyRows")
    if probe["failedGates"]:
        analysis["failedGates"].extend("probe:" + x for x in probe["failedGates"])
    analysis["instrumentationProbes"] = probe
    _write_csv(outdir / "movement_neutral_bundles.csv", bundles)
    _write_csv(outdir / "build_summary.csv", build_summary)
    _write_csv(outdir / "build_mechanics.csv", build_mechanics)
    _write_csv(outdir / "family_matchups.csv", family_rows)
    _write_csv(outdir / "tl_summary.csv", analysis["tlSummary"])
    coverage = [{"metric": k, "aggregate_mean_sum": v, "nonzero": v > 0} for k, v in sorted(analysis["instrumentationTotals"].items())]
    _write_csv(outdir / "instrumentation_coverage.csv", coverage)
    (outdir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis
