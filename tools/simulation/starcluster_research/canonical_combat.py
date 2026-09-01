from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field, fields
from typing import Any

from .ecology import (
    CandidateMatrix,
    CONTEXTUAL_COMBAT_DOCTRINE,
    UTILITY_COMBAT_DOCTRINE,
    LEGACY_COMBAT_DOCTRINE,
    EcologyBuild,
    EcologyVariant,
    SideState,
    SideTelemetry,
    _apply_damage,
    _apply_armor_regeneration,
    _armor_profile,
    _base_sensor_mode,
    _attempt_hull_damage_control,
    _begin_turn_recharge,
    _create_side,
    _cp158_aux_kind,
    _hit_chance,
    _maybe_reactor_overload,
    _plan_once,
    _record_plan,
    _pds_max_attempts_per_flight,
    _shield_armor,
    _weapon,
)
from .canonical_mechanics import CANONICAL_DAMAGE_MODEL, DEF_RES_DAMAGE_MODEL, resolve_def_res_damage, resolve_layered_damage
from .rng import XorShift64, derive_seed
from .tactical_geometry import (
    HexCoord,
    HexMap,
    RangeOrder,
    TacticalOrderPlan,
    advance_missile_finite_map,
    resolve_finite_movement,
    resolve_search_toward_center,
)

FULL_MAP_GEOMETRY = "radius5_full_hex_adaptive"
FULL_MAP_RADIUS = 5

CANONICAL_COMBAT_KERNEL_VERSION = "0.7"
CANONICAL_VISIBLE_PHASES = (
    "Movement",
    "ElectronicWarfare",
    "DirectFire",
    "MissileAndInterception",
    "Damage",
    "DamageControl",
)
CANONICAL_INTERNAL_WINDOWS = (
    "TurnRefresh",
    "PreMovementTacticalPower",
)
STANDARD_START_A = HexCoord(-FULL_MAP_RADIUS, 0)
STANDARD_START_B = HexCoord(FULL_MAP_RADIUS, 0)
STANDARD_START_RANGE = 10
PRECONTACT_SEARCH_HEXES_PER_ACTIVATION = 1


@dataclass(frozen=True, slots=True)
class CanonicalCombatRules:
    kernel_version: str = CANONICAL_COMBAT_KERNEL_VERSION
    damage_model: str = CANONICAL_DAMAGE_MODEL
    map_radius: int = FULL_MAP_RADIUS
    start_a: HexCoord = STANDARD_START_A
    start_b: HexCoord = STANDARD_START_B
    precontact_search_hexes: int = PRECONTACT_SEARCH_HEXES_PER_ACTIVATION
    visible_phases: tuple[str, ...] = CANONICAL_VISIBLE_PHASES
    internal_windows: tuple[str, ...] = CANONICAL_INTERNAL_WINDOWS


CANONICAL_RULES = CanonicalCombatRules()


@dataclass(frozen=True, slots=True)
class DamageCommit:
    source_phase: str
    owner: str
    target: str
    source: str
    damage: float
    spen: int
    apen: int
    target_hardener_active: bool
    target_energized_active: bool = False
    target_field_stabilizer_active: bool = False


def _phase_event(event_sink: list[dict[str, Any]] | None, turn: int, phase: str) -> None:
    if event_sink is not None:
        event_sink.append({"turn": turn, "event": "phase", "phase": phase})


@dataclass(slots=True)
class CombatBlackboard:
    contact_established: bool = False
    contact_turn: int | None = None
    last_track: str | None = None
    last_track_range: int | None = None
    closest_track_failure_range: int | None = None
    maximum_own_attack_range: int | None = None
    maximum_observed_opponent_attack_range: int | None = None
    last_opponent_ecm_emission: bool = False
    last_opponent_active_sensor_emission: bool = False
    last_firm_track_degraded_by_ecm: bool = False
    known_opponent_weapon_family: str | None = None
    known_opponent_weapon_turn: int | None = None

    def establish_contact(self, turn: int) -> None:
        self.contact_established = True
        if self.contact_turn is None:
            self.contact_turn = turn

    def record_track(self, range_hex: int, track: str, opponent_ecm: bool, opponent_active_sensor: bool,
                     degraded_by_ecm: bool) -> None:
        self.last_track = track
        self.last_track_range = range_hex
        self.last_opponent_ecm_emission = opponent_ecm
        self.last_opponent_active_sensor_emission = opponent_active_sensor
        self.last_firm_track_degraded_by_ecm = degraded_by_ecm
        if track != "Firm":
            self.closest_track_failure_range = (
                range_hex if self.closest_track_failure_range is None
                else min(self.closest_track_failure_range, range_hex)
            )

    def record_own_attack(self, range_hex: int) -> None:
        self.maximum_own_attack_range = (
            range_hex if self.maximum_own_attack_range is None
            else max(self.maximum_own_attack_range, range_hex)
        )

    def record_observed_attack(self, range_hex: int) -> None:
        self.maximum_observed_opponent_attack_range = (
            range_hex if self.maximum_observed_opponent_attack_range is None
            else max(self.maximum_observed_opponent_attack_range, range_hex)
        )


@dataclass(slots=True)
class FullMapTelemetry:
    search_moves: int = 0
    adaptive_close_orders: int = 0
    adaptive_open_orders: int = 0
    adaptive_maintain_orders: int = 0
    adaptive_standoff_orders: int = 0
    boundary_end_moves: int = 0
    contact_established_turn: int = 0
    missile_movement_hexes: int = 0
    missile_reroutes: int = 0
    missile_target_movement_reroutes: int = 0
    missile_range_exhausted: int = 0
    maximum_missile_distance_traveled: int = 0
    maximum_own_attack_range: int = 0
    maximum_observed_opponent_attack_range: int = 0


@dataclass(slots=True)
class FullMapMissile:
    owner: str
    target: str
    coordinate: HexCoord
    last_target_coordinate: HexCoord
    damage: float
    spen: int
    apen: int
    guidance: int
    speed: int
    maximum_travel: int
    distance_traveled: int = 0
    packets: int = 1
    pds_intercept_penalty_pp: int = 0
    profile_id: str = "GP"
    flight_id: int = 0
    magazine_flight_id: int = 0
    launch_turn: int = 0
    range_one_window_eligible: bool = False


@dataclass(frozen=True, slots=True)
class FullMapTrialResult:
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
    full_a: FullMapTelemetry
    full_b: FullMapTelemetry
    final_q_a: int
    final_r_a: int
    final_q_b: int
    final_r_b: int
    error: str = ""
    termination_cause: str = ""
    last_damage_state_change_turn: int = 0
    final_missiles_in_flight: int = 0


def _range(a: HexCoord, b: HexCoord) -> int:
    return a.distance_to(b)


def _physical_ids(variant: EcologyVariant) -> dict[str, str]:
    if variant.physical_id_a and variant.physical_id_b:
        if variant.physical_id_a == variant.physical_id_b:
            raise ValueError("full-map physical ship identities must be distinct")
        return {"A": variant.physical_id_a, "B": variant.physical_id_b}
    if variant.side_a.id != variant.side_b.id:
        return {"A": variant.side_a.id, "B": variant.side_b.id}
    # Backward-compatible fallback for ad-hoc identical-build probes. CP126
    # planned studies always provide explicit physical identities.
    return {"A": f"{variant.side_a.id}|left", "B": f"{variant.side_b.id}|right"}


def _physical_symmetry_key(variant: EcologyVariant) -> str:
    physical = _physical_ids(variant)
    lo, hi = sorted(physical.values())
    # Do not include side label, mover order, or perturbation. Event streams
    # belong to the physical ships, so mirror and sensitivity variants use
    # common random numbers and differ only through the mechanic being tested.
    return f"{lo}|{hi}|scenario={variant.scenario_group}"


def _rngs(variant: EcologyVariant, master_seed: int, trial_index: int) -> tuple[dict[tuple[str, str], XorShift64], dict[str, str]]:
    key = _physical_symmetry_key(variant)
    physical = _physical_ids(variant)
    streams = {
        (pid, stream): XorShift64(derive_seed(master_seed, key, trial_index, pid, stream))
        for pid in set(physical.values())
        for stream in ("direct", "held", "guidance", "pds", "damcon", "defense")
    }
    return streams, physical


def _max_weapon_range(matrix: CandidateMatrix, side: SideState) -> int:
    return int(_weapon(matrix, side.build)["range"])


def _preferred_weapon_range(matrix: CandidateMatrix, side: SideState) -> int:
    w = _weapon(matrix, side.build)
    return int(w["range"] if w["family"] == "Missile" else w.get("standard_range", w["range"]))


def _choose_order(matrix: CandidateMatrix, side: SideState, current_range: int,
                  blackboard: CombatBlackboard) -> tuple[TacticalOrderPlan, str]:
    if not blackboard.contact_established:
        return TacticalOrderPlan(RangeOrder.CLOSE, None, "pre-contact search"), "search"
    if blackboard.last_track is not None and blackboard.last_track != "Firm" and blackboard.last_track_range is not None:
        # Production C# AdaptiveEngage closes one hex inside the most recently
        # failed observable range.  It does NOT target the weapon family's
        # preferred/max range while recovering track.  Keep this branch in
        # lockstep with AdaptiveEngageTacticalPolicy.MoveTowardRange.
        desired = max(0, min(current_range, blackboard.last_track_range) - 1)
        if current_range > desired:
            return TacticalOrderPlan(RangeOrder.CLOSE, desired, "previous non-Firm track; close"), "track_close"
        if current_range < desired:
            return TacticalOrderPlan(RangeOrder.OPEN, desired, "previous non-Firm track; reopen"), "track_close"
        return TacticalOrderPlan(RangeOrder.MAINTAIN, desired, "previous non-Firm track at desired range"), "track_close"
    own = blackboard.maximum_own_attack_range
    opp = blackboard.maximum_observed_opponent_attack_range
    if own is not None and (opp is None or opp < own):
        if current_range < own:
            return TacticalOrderPlan(RangeOrder.OPEN, own, "preserve demonstrated one-sided standoff"), "standoff"
        if current_range > own:
            return TacticalOrderPlan(RangeOrder.CLOSE, own, "recover demonstrated one-sided standoff"), "standoff"
        return TacticalOrderPlan(RangeOrder.MAINTAIN, own, "hold demonstrated one-sided standoff"), "standoff"
    maximum = _max_weapon_range(matrix, side)
    if current_range > maximum:
        return TacticalOrderPlan(RangeOrder.CLOSE, maximum, "close to own physical weapon envelope"), "envelope"
    # Production C# AdaptiveEngage deliberately holds the CURRENT range once
    # the target is inside the ship's physical weapon envelope.  This gives the
    # actual track/engagement state time to prove whether the range is usable,
    # instead of reopening toward a theoretical preferred weapon range and
    # voluntarily throwing away a Firm firing solution.
    return TacticalOrderPlan(RangeOrder.MAINTAIN, current_range, "inside own weapon envelope; hold current range to test actual track/engagement state"), "envelope_hold"


def _record_order(extra: FullMapTelemetry, plan: TacticalOrderPlan, reason_class: str) -> None:
    if reason_class == "search":
        return
    if plan.range_order == RangeOrder.CLOSE:
        extra.adaptive_close_orders += 1
    elif plan.range_order == RangeOrder.OPEN:
        extra.adaptive_open_orders += 1
    else:
        extra.adaptive_maintain_orders += 1
    if reason_class == "standoff":
        extra.adaptive_standoff_orders += 1


def _move_side(map_: HexMap, matrix: CandidateMatrix, side: SideState, target: SideState,
               side_coord: HexCoord, target_coord: HexCoord, blackboard: CombatBlackboard,
               extra: FullMapTelemetry, *, orientation_reference: HexCoord | None = None,
               label: str = "", turn: int = 0,
               event_sink: list[dict[str, Any]] | None = None) -> tuple[HexCoord, bool]:
    t = side.telemetry
    old_range = _range(side_coord, target_coord)
    if side.fuel < 2:
        return side_coord, False
    move_cap = min(int(matrix.p("stl", side.build.tl)["move"]), side.fuel // 2)
    plan, reason_class = _choose_order(matrix, side, old_range, blackboard)
    _record_order(extra, plan, reason_class)
    if not blackboard.contact_established:
        move = resolve_search_toward_center(map_, side_coord, move_cap)
        # Fill target-aware range data for instrumentation only.
        destination = move.destination
        movement_hexes = move.movement_hexes
        extra.search_moves += movement_hexes
        ended = move.ended_on_boundary
    else:
        move = resolve_finite_movement(
            map_, side_coord, target_coord, move_cap, plan, orientation_reference
        )
        destination = move.destination
        movement_hexes = move.movement_hexes
        ended = move.ended_on_boundary
    if movement_hexes:
        side.fuel -= movement_hexes * 2
        t.movement_hexes += movement_hexes
        t.movement_fuel += movement_hexes * 2
    if ended and movement_hexes:
        extra.boundary_end_moves += 1
    new_range = _range(destination, target_coord)
    if new_range != old_range:
        t.range_changes += 1
    if reason_class == "track_close" and new_range < old_range:
        t.track_driven_closure_hexes += movement_hexes
    t.min_range = min(t.min_range, new_range)
    # A map boundary block is only recorded when an Open order cannot realize
    # its desired range despite using the entire legal movement allowance.
    if (plan.range_order == RangeOrder.OPEN and movement_hexes < move_cap and
            plan.desired_range is not None and new_range < plan.desired_range):
        t.map_boundary_blocks += 1
    if event_sink is not None:
        event_sink.append({
            "turn": turn, "event": "movement", "side": label,
            "origin": [side_coord.q, side_coord.r],
            "target": [target_coord.q, target_coord.r],
            "destination": [destination.q, destination.r],
            "movement_hexes": movement_hexes, "old_range": old_range, "new_range": new_range,
            "order": plan.range_order.value, "desired_range": plan.desired_range,
            "reason_class": reason_class,
        })
    return destination, new_range != old_range


def _update_pre_movement_contact(turn: int, matrix: CandidateMatrix, observer: SideState,
                                 target: SideState, observer_coord: HexCoord, target_coord: HexCoord,
                                 blackboard: CombatBlackboard, target_emissions: tuple[bool, bool]) -> None:
    if blackboard.contact_established:
        return
    passive_approx = int(matrix.p("sensor", observer.build.tl)["passiveApprox"])
    if target_emissions[0] or target_emissions[1] or _range(observer_coord, target_coord) <= passive_approx:
        blackboard.establish_contact(turn)


def _sync_blackboard_summary(bb: CombatBlackboard, extra: FullMapTelemetry) -> None:
    extra.contact_established_turn = int(bb.contact_turn or 0)
    extra.maximum_own_attack_range = int(bb.maximum_own_attack_range or 0)
    extra.maximum_observed_opponent_attack_range = int(bb.maximum_observed_opponent_attack_range or 0)


def _cp147_expected_terminal_loss(matrix: CandidateMatrix, target: SideState, missile: FullMapMissile) -> tuple[float, float]:
    """Expected structural and Hull loss if one terminal subflight is not intercepted.

    CP147 uses the defender's *current* ordinary layers and the observed inbound
    missile packet.  Optional hardeners are intentionally excluded because the
    utility selector is deciding whether to power them.  DEF/RES deflection is
    integrated as probability rather than consuming RNG.
    """
    packets = max(1, int(missile.packets))
    initial = (float(target.shield), float(target.armor_integrity), float(target.hull))

    if getattr(matrix, "damage_model", CANONICAL_DAMAGE_MODEL) == DEF_RES_DAMAGE_MODEL:
        # Carry a tiny exact state distribution across packets so this remains
        # correct if a future observed missile contains more than one packet.
        states: dict[tuple[float, float, float], float] = {initial: 1.0}
        base_def = float(getattr(matrix, "def_res_shield_def_pp", {}).get(target.build.tl, 0.0))
        armor_res = float(getattr(matrix, "def_res_armor_res_pp", {}).get(target.build.tl, 0.0))
        for _ in range(packets):
            nxt: dict[tuple[float, float, float], float] = {}
            for (shield, armor, hull), probability in states.items():
                effective_def = min(45.0, max(0.0, base_def - float(missile.spen))) if shield > 0 else 0.0
                p_deflect = effective_def / 100.0
                if p_deflect > 0.0:
                    key = (shield, armor, hull)
                    nxt[key] = nxt.get(key, 0.0) + probability * p_deflect
                p_hit = 1.0 - p_deflect
                if p_hit > 0.0:
                    result = resolve_def_res_damage(
                        shield=shield, armor_integrity=armor, hull=hull,
                        damage=float(missile.damage), spen=float(missile.spen), apen=float(missile.apen),
                        shield_def_pp=base_def, armor_res_pp=armor_res, defense_roll=100,
                    )
                    key = (float(result.final_shield), float(result.final_armor_integrity), float(result.final_hull))
                    nxt[key] = nxt.get(key, 0.0) + probability * p_hit
            states = nxt
        expected_shield = sum(state[0] * probability for state, probability in states.items())
        expected_armor = sum(state[1] * probability for state, probability in states.items())
        expected_hull = sum(state[2] * probability for state, probability in states.items())
    else:
        shield, armor, hull = (int(round(initial[0])), int(round(initial[1])), int(round(initial[2])))
        for _ in range(packets):
            result = resolve_layered_damage(
                shield=shield, armor_integrity=armor, armor_protection=int(target.armor_protection), hull=hull,
                damage=int(round(missile.damage)), spen=int(missile.spen), apen=int(missile.apen),
                shield_armor=_shield_armor(matrix, target, False),
            )
            shield, armor, hull = result.final_shield, result.final_armor_integrity, result.final_hull
        expected_shield, expected_armor, expected_hull = float(shield), float(armor), float(hull)

    structural_loss = max(0.0, sum(initial) - (expected_shield + expected_armor + expected_hull))
    hull_loss = max(0.0, initial[2] - expected_hull)
    return structural_loss, hull_loss



def _cp147_project_terminal_threats(
    matrix: CandidateMatrix, target: SideState, target_coord: HexCoord, missiles: list[FullMapMissile]
) -> tuple[tuple[float, int, float], ...]:
    """Project currently observable subflights able to enter terminal this Missile phase."""
    projected: list[tuple[float, int, float]] = []
    for missile in missiles:
        current = _range(missile.coordinate, target_coord)
        travel_left = max(0, int(missile.maximum_travel) - int(missile.distance_traveled))
        step = min(max(0, int(missile.speed)), travel_left)
        if current <= step and current <= travel_left:
            expected_structural, expected_hull = _cp147_expected_terminal_loss(matrix, target, missile)
            guidance_fraction = max(0, min(100, int(missile.guidance))) / 100.0
            projected.append((
                expected_structural * guidance_fraction,
                int(missile.pds_intercept_penalty_pp),
                expected_hull * guidance_fraction,
            ))
    return tuple(projected)


def _apply_committed_damage(matrix: CandidateMatrix, target: SideState, commit: DamageCommit, defense_roll: int | None, turn: int) -> None:
    if getattr(matrix, "damage_model", CANONICAL_DAMAGE_MODEL) != DEF_RES_DAMAGE_MODEL:
        _apply_damage(
            target, int(commit.damage), commit.spen, commit.apen,
            _shield_armor(matrix, target, commit.target_hardener_active), commit.source, turn
        )
        return

    t = target.telemetry
    before_shield = float(target.shield)
    before_armor = float(target.armor_integrity)
    before_hull = float(target.hull)
    base_def = float(getattr(matrix, "def_res_shield_def_pp", {}).get(target.build.tl, 0.0))
    if commit.target_hardener_active:
        hp=_cp158_aux_kind(matrix,target.build,"shield_hardener")
        base_def += float(hp.get("def_bonus_pp",getattr(matrix,"def_res_hardener_bonus_pp",10.0))) if hp is not None else float(getattr(matrix, "def_res_hardener_bonus_pp", 10.0))
    effective_spen=float(commit.spen)
    if commit.target_field_stabilizer_active:
        fp=_cp158_aux_kind(matrix,target.build,"field_stabilizer")
        if fp is not None: effective_spen=max(0.0,effective_spen-float(fp.get("spen_reduction",0)))
    armor_res = float(getattr(matrix, "def_res_armor_res_pp", {}).get(target.build.tl, 0.0))
    armor_res += float(_armor_profile(matrix,target.build).get("cp158ArmorResBonusPp",0.0))
    if commit.target_energized_active:
        ep=_cp158_aux_kind(matrix,target.build,"energized_armor")
        if ep is not None: armor_res += float(ep.get("res_bonus_pp",0.0))
    if target.ablative_integrity > 0:
        shield_result=resolve_def_res_damage(shield=before_shield,armor_integrity=0,hull=1000000,damage=float(commit.damage),spen=effective_spen,apen=0,shield_def_pp=base_def,armor_res_pp=0,defense_roll=int(defense_roll or 100))
        remaining=float(shield_result.hull_damage)
        ablative_abs=min(float(target.ablative_integrity),remaining); target.ablative_integrity -= ablative_abs; remaining -= ablative_abs
        if ablative_abs>0:
            t.aux_ablative_absorbed += int(round(ablative_abs))
            if target.ablative_integrity<=0: t.aux_ablative_depleted_events += 1
        armor_result=resolve_def_res_damage(shield=0,armor_integrity=before_armor,hull=before_hull,damage=remaining,spen=0,apen=float(commit.apen),shield_def_pp=0,armor_res_pp=armor_res,defense_roll=100)
        class _Combined: pass
        result=_Combined(); result.final_shield=shield_result.final_shield; result.final_armor_integrity=armor_result.final_armor_integrity; result.final_hull=armor_result.final_hull
        result.incoming_damage=float(commit.damage); result.effective_def_pp=shield_result.effective_def_pp; result.deflected=shield_result.deflected; result.shield_absorbed=shield_result.shield_absorbed
        result.armor_damage=armor_result.armor_damage; result.armor_resisted_damage=armor_result.armor_resisted_damage; result.hull_damage=armor_result.hull_damage
    else:
        result = resolve_def_res_damage(shield=before_shield,armor_integrity=before_armor,hull=before_hull,damage=float(commit.damage),spen=effective_spen,apen=float(commit.apen),shield_def_pp=base_def,armor_res_pp=armor_res,defense_roll=int(defense_roll or 100))
    target.shield = result.final_shield
    target.armor_integrity = result.final_armor_integrity
    target.hull = result.final_hull

    t.damage_packets_resolved += 1
    t.def_res_packets += 1
    t.shield_def_effective_pp_total += result.effective_def_pp
    if result.deflected:
        t.shield_deflections += 1
    if before_shield > target.shield and t.first_shield_damage_turn == 0 and turn > 0:
        t.first_shield_damage_turn = turn
    if before_shield > 0 and target.shield <= 0:
        t.shield_collapse_events += 1
        if t.first_shield_collapse_turn == 0 and turn > 0:
            t.first_shield_collapse_turn = turn
    if before_armor > target.armor_integrity and t.first_armor_damage_turn == 0 and turn > 0:
        t.first_armor_damage_turn = turn
    if before_armor > 0 and target.armor_integrity <= 0:
        t.armor_collapse_events += 1
        if t.first_armor_collapse_turn == 0 and turn > 0:
            t.first_armor_collapse_turn = turn
    if before_hull > target.hull and t.first_hull_damage_turn == 0 and turn > 0:
        t.first_hull_damage_turn = turn

    t.raw_damage_on_hit += result.incoming_damage
    t.shield_absorbed += result.shield_absorbed
    t.armor_integrity_damage += result.armor_damage
    t.armor_resisted_damage += result.armor_resisted_damage
    t.hull_damage += result.hull_damage
    if commit.source == "direct":
        t.direct_raw_damage += result.incoming_damage
        t.direct_hull_damage += result.hull_damage
    else:
        t.missile_raw_damage += result.incoming_damage
        t.missile_hull_damage += result.hull_damage



def _cp140_tactical_recharge_request(matrix: CandidateMatrix, side: SideState) -> int:
    """Policy-qualified tactical Shield recharge request before TP allocation.

    This is observational only. It mirrors the executable recharge opportunity/cap
    without changing the existing recharge policy or consuming RNG/state.
    """
    if not side.build.shield or side.shield <= 0 and getattr(matrix, "damage_model", None) == DEF_RES_DAMAGE_MODEL:
        return 0
    if side.shield >= side.shield_max:
        return 0
    sp = matrix.p("shield", side.build.tl)
    after_base = min(side.shield_max, side.shield + int(sp.get("baseRecharge", 0)))
    missing = max(0, side.shield_max - after_base)
    per_tp = max(1, int(sp.get("tacticalRechargePerTp", 1)))
    cap = max(0, int(sp.get("tacticalRechargeCapTp", 0)))
    return min(cap, math.ceil(missing / per_tp)) if missing > 0 else 0


def _cp140_plan_action_requests(matrix: CandidateMatrix, side: SideState, target: SideState, range_hex: int,
                                inbound: int, opponent_ecm_on: bool, shield_request_tp: int,
                                combat_doctrine: str = LEGACY_COMBAT_DOCTRINE) -> list[dict[str, Any]]:
    """Return desirable legal TP actions under the current policy with effectively unlimited TP.

    The shadow plan calls the same policy function used by combat but has no RNG and
    no state mutation.  It therefore measures counterfactual demand without changing
    tactical choices or the random streams.
    """
    shadow = _plan_once(matrix, side, target, range_hex, inbound, 10**6, opponent_ecm_on, combat_doctrine)
    actions: list[dict[str, Any]] = []
    if shield_request_tp > 0:
        actions.append({"id": "shield_recharge", "requested": int(shield_request_tp), "category": "shield"})
    for key, ident, cat in (
        ("ecm_cost", "ecm", "ecm"),
        ("eccm_cost", "eccm", "eccm"),
        ("sensor_cost", "sensor", "sensor"),
        ("hardener_power", "shield_hardener", "shield"),
        ("pds_power", "pds", "pds"),
    ):
        cost = int(shadow.get(key, 0) or 0)
        if cost > 0:
            actions.append({"id": ident, "requested": cost, "category": cat})
    for i, wp in enumerate(shadow.get("weapon_plans", []), start=1):
        if wp is not None and int(wp[0]) > 0:
            actions.append({"id": f"weapon_{i}", "requested": int(wp[0]), "category": "weapon"})
    return actions


def _cp140_plan_allocations(plan: dict[str, Any], shield_spend: int) -> dict[str, int]:
    alloc: dict[str, int] = {}
    if shield_spend > 0:
        alloc["shield_recharge"] = int(shield_spend)
    for key, ident in (
        ("ecm_cost", "ecm"), ("eccm_cost", "eccm"), ("sensor_cost", "sensor"),
        ("hardener_power", "shield_hardener"), ("pds_power", "pds"),
    ):
        cost = int(plan.get(key, 0) or 0)
        if cost > 0:
            alloc[ident] = cost
    for i, wp in enumerate(plan.get("weapon_plans", []), start=1):
        if wp is not None and int(wp[0]) > 0:
            alloc[f"weapon_{i}"] = int(wp[0])
    return alloc


def _cp140_damage_control_request(matrix: CandidateMatrix, side: SideState) -> int:
    if side.hull <= 0 or side.hull >= side.hull_max or side.repair_kits_remaining <= 0:
        return 0
    return max(0, int(matrix.p("damage_control", side.build.tl).get("attemptTp", 1)))


def _cp140_armor_regen_request(matrix: CandidateMatrix, side: SideState) -> int:
    profile = _armor_profile(matrix, side.build)
    per_tp = int(profile.get("tacticalRegenerationPerTp", 0))
    cap_tp = int(profile.get("tacticalRegenerationCapTp", 0))
    if per_tp <= 0 or cap_tp <= 0 or side.armor_integrity >= side.armor_max or side.armor_regen_reserve_remaining == 0:
        return 0
    missing = max(0, side.armor_max - side.armor_integrity)
    max_restore = missing if side.armor_regen_reserve_remaining < 0 else min(missing, side.armor_regen_reserve_remaining)
    return min(cap_tp, math.ceil(max_restore / per_tp)) if max_restore > 0 else 0


def _cp140_finalize_turn_row(*, context: dict[str, Any], trial_index: int, turn: int, label: str,
                             side: SideState, plan: dict[str, Any], range_hex: int, inbound: int,
                             reactor_tp: int, overload_tp: int, shield_spend: int,
                             desired_actions: list[dict[str, Any]], allocations: dict[str, int],
                             dc_request: int, dc_spend: int, armor_request: int, armor_spend: int) -> dict[str, Any]:
    if dc_request > 0:
        desired_actions.append({"id": "damage_control", "requested": int(dc_request), "category": "damage_control"})
    if armor_request > 0:
        desired_actions.append({"id": "armor_regen", "requested": int(armor_request), "category": "armor"})
    if dc_spend > 0:
        allocations["damage_control"] = int(dc_spend)
    if armor_spend > 0:
        allocations["armor_regen"] = int(armor_spend)
    requested = sum(int(x["requested"]) for x in desired_actions)
    allocated = sum(int(v) for v in allocations.values())
    denied = sum(max(0, int(x["requested"]) - int(allocations.get(str(x["id"]), 0))) for x in desired_actions)
    full_funded = sum(int(allocations.get(str(x["id"]), 0)) >= int(x["requested"]) for x in desired_actions)
    denied_actions = sum(int(allocations.get(str(x["id"]), 0)) < int(x["requested"]) for x in desired_actions)
    categories = ("weapon", "pds", "sensor", "ecm", "eccm", "shield", "armor", "damage_control")
    requested_by_category = {
        cat: sum(int(x["requested"]) for x in desired_actions if str(x.get("category", "")) == cat)
        for cat in categories
    }
    denied_by_category = {
        cat: sum(
            max(0, int(x["requested"]) - int(allocations.get(str(x["id"]), 0)))
            for x in desired_actions if str(x.get("category", "")) == cat
        )
        for cat in categories
    }
    supply = int(reactor_tp) + int(overload_tp)
    w = _weapon(context["matrix"], side.build)
    chosen = [k for k, v in allocations.items() if int(v) > 0]
    return {
        "trial_id": f"{context.get('scenario_id','scenario')}:{trial_index}",
        "scenario_id": context.get("scenario_id", ""), "turn": turn, "side_id": label,
        "tl": side.build.tl, "weapon_variant": context.get(f"weapon_{label.lower()}", side.build.weapon_family),
        "resource_ensemble_id": context.get("resource_ensemble_id", ""), "reactor_condition": "Undamaged",
        "reactor_tp_available": int(reactor_tp), "aux_tp_supply": 0,
        "tp_requested_total": requested, "tp_allocated_total": allocated, "tp_denied_total": denied,
        "tp_requested_weapon": requested_by_category["weapon"], "tp_denied_weapon": denied_by_category["weapon"],
        "tp_requested_pds": requested_by_category["pds"], "tp_denied_pds": denied_by_category["pds"],
        "tp_requested_sensor": requested_by_category["sensor"], "tp_denied_sensor": denied_by_category["sensor"],
        "tp_requested_ecm": requested_by_category["ecm"], "tp_denied_ecm": denied_by_category["ecm"],
        "tp_requested_eccm": requested_by_category["eccm"], "tp_denied_eccm": denied_by_category["eccm"],
        "tp_requested_shield": requested_by_category["shield"], "tp_denied_shield": denied_by_category["shield"],
        "tp_requested_armor": requested_by_category["armor"], "tp_denied_armor": denied_by_category["armor"],
        "tp_requested_damage_control": requested_by_category["damage_control"], "tp_denied_damage_control": denied_by_category["damage_control"],
        "tp_weapon": sum(v for k,v in allocations.items() if k.startswith("weapon_")),
        "tp_pds": int(allocations.get("pds",0)), "tp_sensor": int(allocations.get("sensor",0)),
        "tp_ecm": int(allocations.get("ecm",0)), "tp_eccm": int(allocations.get("eccm",0)),
        "tp_shield": int(allocations.get("shield_recharge",0))+int(allocations.get("shield_hardener",0)),
        "tp_armor": int(allocations.get("armor_regen",0)), "tp_damage_control": int(allocations.get("damage_control",0)),
        "tp_stl": 0, "tp_aux": 0, "tp_overload": int(overload_tp),
        "desirable_action_count": len(desired_actions), "funded_action_count": full_funded,
        "denied_action_count": denied_actions,
        "tp_conflict_flag": int(len(desired_actions) >= 2 and denied > 0 and requested > supply),
        "strain_reactor": int(side.reactor_strain), "strain_weapon": int(side.energy_weapon_strain),
        "strain_sensor": 0, "strain_ecm": 0, "strain_eccm": 0, "strain_stl": 0,
        "range_hex": int(range_hex), "track_quality": str(plan.get("track", "None")),
        "fuel_remaining": int(side.fuel),
        "kinetic_ammo_remaining": int(side.weapon_ammo) if side.build.weapon_family == "Kinetic" and side.weapon_ammo is not None else "",
        "missile_flights_remaining": int(side.weapon_ammo) if side.build.weapon_family == "Missile" and side.weapon_ammo is not None else "",
        "pds_ammo_remaining": int(side.pds_ammo) if side.pds_ammo is not None else "",
        "shield_remaining": side.shield, "armor_remaining": side.armor_integrity, "hull_remaining": side.hull,
        "primary_weapon_condition": "Undamaged", "sensor_condition": "Undamaged",
        "pds_condition": "Undamaged" if side.build.pds_family else "NotInstalled",
        "inbound_missile_flights": int(inbound), "pds_threat_flag": int(bool(plan.get("pds_threat", False))),
        "pds_reaction_capacity_planned": int(plan.get("pds_rc", 0)),
        "chosen_action_summary": "+".join(chosen) if chosen else "none",
        "tp_headroom_after_desired": supply - requested,
        "weapon_family_runtime": str(w.get("family", side.build.weapon_family)),
    }


def _cp146_selected_sensor_track(matrix: CandidateMatrix, side: SideState, sensor_mode: str, range_hex: int) -> str:
    s = matrix.p("sensor", side.build.tl)
    if sensor_mode == "passive":
        firm, approx = int(s["passiveFirm"]), int(s["passiveApprox"])
    elif sensor_mode == "high" and s.get("activeHighFirm") is not None:
        firm, approx = int(s["activeHighFirm"]), int(s["activeHighApprox"])
    else:
        firm, approx = int(s["activeLowFirm"]), int(s["activeLowApprox"])
    if range_hex <= firm:
        return "Firm"
    if range_hex <= approx:
        return "Approximate"
    return "None"



def _resolve_cp146_held_main_layer(
    matrix: CandidateMatrix,
    target_label: str,
    target: SideState,
    plan: dict[str, Any],
    terminal: list[FullMapMissile],
    missiles: list[FullMapMissile],
    target_coord: HexCoord,
    held_rng: XorShift64,
    turn: int,
    event_sink: list[dict[str, Any]] | None = None,
) -> None:
    """Resolve CP146 Held Main interception attempts for one defending side.

    The helper is intentionally narrow and mutates the supplied missile lists,
    plan power accounting, ammunition, and side telemetry exactly as the
    canonical whole-combat kernel does.  Extracting it makes the parity-restored
    anti-missile path directly testable without inventing a special scenario API.
    """
    held_indices = [i for i, action in enumerate(plan.get("weapon_actions", [])) if action == "hold_missile"]
    if not held_indices:
        return

    enemy_candidates = [m for m in terminal + missiles if m.target == target_label]
    enemy_candidates.sort(key=lambda m: (_range(m.coordinate, target_coord), m.launch_turn, m.flight_id))
    w = _weapon(matrix, target.build)
    for held_index in held_indices:
        weapon_plans = plan.get("weapon_plans", [])
        wp = weapon_plans[held_index] if held_index < len(weapon_plans) else None
        if wp is None:
            continue
        eligible = next((
            m for m in enemy_candidates
            if _range(m.coordinate, target_coord) <= int(w["range"])
            and _cp146_selected_sensor_track(
                matrix, target, str(plan.get("sensor_mode", "passive")),
                _range(m.coordinate, target_coord),
            ) == "Firm"
        ), None)
        if eligible is None or (target.weapon_ammo is not None and target.weapon_ammo <= 0):
            target.telemetry.cp146_held_main_unused += 1
            released = int(wp[0])
            plan["remaining"] = int(plan.get("remaining", 0)) + released
            target.telemetry.power_weapons -= released
            target.telemetry.power_spent_total -= released
            if event_sink is not None:
                event_sink.append({
                    "turn": turn, "event": "held_main_unused",
                    "side": target_label, "released_tp": released,
                })
            continue

        target.telemetry.cp146_held_main_attempts += 1
        if target.weapon_ammo is not None:
            target.weapon_ammo -= 1
        chance = max(5, min(95, 50 + int(w["accuracy"]) + int(matrix.p("computer", target.build.tl)["targetingPp"])))
        hit = held_rng.d100() <= chance
        if hit:
            target.telemetry.cp146_held_main_intercepts += 1
            enemy_candidates.remove(eligible)
            if eligible in terminal:
                terminal.remove(eligible)
            if eligible in missiles:
                missiles.remove(eligible)
        if event_sink is not None:
            event_sink.append({
                "turn": turn, "event": "held_main_interception",
                "side": target_label, "weapon_family": str(w["family"]),
                "target_flight_id": eligible.flight_id,
                "magazine_flight_id": eligible.magazine_flight_id,
                "chance": chance, "intercepted": int(hit),
                "range": _range(eligible.coordinate, target_coord),
                "missile_track": "Firm",
            })

def _primary_offense_permanently_exhausted(side: SideState) -> bool:
    """Return True only when the installed primary weapon can never fire again.

    Energy weapons have no magazine and therefore never satisfy this predicate.
    Kinetic and Missile weapons are permanently exhausted only when their finite
    primary ammunition reaches zero.  This is deliberately narrower than a
    generic "cannot fire now" test: range, track, TP, fuel, recharge, and
    temporary tactical state are never treated as permanent stalemate evidence.
    """
    return side.weapon_ammo is not None and int(side.weapon_ammo) <= 0


def _mutual_offensive_exhaustion(a: SideState, b: SideState, missiles: list[FullMapMissile]) -> bool:
    """Conservative no-path-to-victory detector for finite primary offense.

    Pending missile flights remain live offensive paths, so mutual magazine
    exhaustion becomes a stalemate only after all already-launched flights have
    either hit, been intercepted, or exhausted their range.
    """
    return (
        _primary_offense_permanently_exhausted(a)
        and _primary_offense_permanently_exhausted(b)
        and not missiles
    )


def run_trial_full_map(matrix: CandidateMatrix, variant: EcologyVariant, master_seed: int, trial_index: int,
                       event_sink: list[dict[str, Any]] | None = None,
                       turn_telemetry_sink: list[dict[str, Any]] | None = None,
                       telemetry_context: dict[str, Any] | None = None,
                       combat_doctrine: str = LEGACY_COMBAT_DOCTRINE) -> FullMapTrialResult:
    try:
        map_ = HexMap.create_hexagon(FULL_MAP_RADIUS)
        a = _create_side(matrix, variant.side_a, -FULL_MAP_RADIUS)
        b = _create_side(matrix, variant.side_b, FULL_MAP_RADIUS)
        coord = {"A": HexCoord(int(variant.start_q_a), 0), "B": HexCoord(int(variant.start_q_b), 0)}
        if coord["A"] not in map_.cells or coord["B"] not in map_.cells or coord["A"] == coord["B"]:
            raise ValueError(f"invalid full-map starting coordinates {coord['A']} {coord['B']}")
        orientation_reference = dict(coord)
        bb = {"A": CombatBlackboard(), "B": CombatBlackboard()}
        extra = {"A": FullMapTelemetry(), "B": FullMapTelemetry()}
        emissions: dict[str, tuple[bool, bool]] = {"A": (False, False), "B": (False, False)}
        rngs, physical = _rngs(variant, master_seed, trial_index)
        missiles: list[FullMapMissile] = []
        missile_serial = 0
        magazine_flight_serial = 0
        overall_min = _range(coord["A"], coord["B"])
        last_damage_state_change_turn = 0

        for turn in range(1, variant.max_turns + 1):
            _phase_event(event_sink, turn, "TurnRefresh")
            inbound_a = sum(m.target == "A" for m in missiles)
            inbound_b = sum(m.target == "B" for m in missiles)
            if combat_doctrine in (CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE):
                if inbound_a > 0:
                    if a.known_opponent_weapon_family is None:
                        a.known_opponent_weapon_family = "Missile"
                        a.known_opponent_weapon_turn = turn
                        bb["A"].known_opponent_weapon_family = "Missile"
                        bb["A"].known_opponent_weapon_turn = turn
                    observed = next((m for m in missiles if m.target == "A"), None)
                    a.known_opponent_missile_profile = observed.profile_id if observed is not None else a.known_opponent_missile_profile
                    if combat_doctrine == UTILITY_COMBAT_DOCTRINE and observed is not None:
                        a.known_opponent_missile_expected_raw_per_subflight = float(observed.damage) * max(1,int(observed.packets)) * max(0,min(100,int(observed.guidance))) / 100.0
                        a.known_opponent_missile_pds_penalty_pp = int(observed.pds_intercept_penalty_pp)
                        a.known_opponent_missile_subflights = 2 if observed.profile_id == "Swarmer" else 1
                if inbound_b > 0:
                    if b.known_opponent_weapon_family is None:
                        b.known_opponent_weapon_family = "Missile"
                        b.known_opponent_weapon_turn = turn
                        bb["B"].known_opponent_weapon_family = "Missile"
                        bb["B"].known_opponent_weapon_turn = turn
                    observed = next((m for m in missiles if m.target == "B"), None)
                    b.known_opponent_missile_profile = observed.profile_id if observed is not None else b.known_opponent_missile_profile
                    if combat_doctrine == UTILITY_COMBAT_DOCTRINE and observed is not None:
                        b.known_opponent_missile_expected_raw_per_subflight = float(observed.damage) * max(1,int(observed.packets)) * max(0,min(100,int(observed.guidance))) / 100.0
                        b.known_opponent_missile_pds_penalty_pp = int(observed.pds_intercept_penalty_pp)
                        b.known_opponent_missile_subflights = 2 if observed.profile_id == "Swarmer" else 1
            if combat_doctrine == UTILITY_COMBAT_DOCTRINE:
                # Turn-Refresh TP decisions can see the actual positions of already
                # observed inbound missiles. Forecast terminal entry from the current
                # geometry so tactical Shield recharge does not pre-consume TP needed
                # by an immediate terminal-defense package. Movement may later change
                # this forecast; the post-Movement planner recomputes it exactly.
                a.cp147_terminal_threats = _cp147_project_terminal_threats(matrix, a, coord["A"], [m for m in missiles if m.target == "A"])
                b.cp147_terminal_threats = _cp147_project_terminal_threats(matrix, b, coord["B"], [m for m in missiles if m.target == "B"])

            shield_request_a = _cp140_tactical_recharge_request(matrix, a) if turn_telemetry_sink is not None else 0
            shield_request_b = _cp140_tactical_recharge_request(matrix, b) if turn_telemetry_sink is not None else 0
            reactor_tp_a = int(matrix.p("reactor", a.build.tl)["operationalTp"]) * a.build.reactor_count
            reactor_tp_b = int(matrix.p("reactor", b.build.tl)["operationalTp"]) * b.build.reactor_count
            power_a, shield_spend_a = _begin_turn_recharge(matrix, a, b, inbound_a, combat_doctrine)
            power_b, shield_spend_b = _begin_turn_recharge(matrix, b, a, inbound_b, combat_doctrine)

            _phase_event(event_sink, turn, "PreMovementTacticalPower")
            _phase_event(event_sink, turn, "Movement")

            # Both sides receive the same pre-Movement observable state.
            _update_pre_movement_contact(turn, matrix, a, b, coord["A"], coord["B"], bb["A"], emissions["B"])
            _update_pre_movement_contact(turn, matrix, b, a, coord["B"], coord["A"], bb["B"], emissions["A"])

            order = ("A", "B") if variant.movement_order == "SideAFirst" else ("B", "A")
            states = {"A": a, "B": b}
            for mover in order:
                other = "B" if mover == "A" else "A"
                states_m, states_o = states[mover], states[other]
                coord[mover], _ = _move_side(
                    map_, matrix, states_m, states_o, coord[mover], coord[other], bb[mover], extra[mover],
                    orientation_reference=orientation_reference[mover],
                    label=mover, turn=turn, event_sink=event_sink
                )
                # The second mover may legitimately gain contact from the first
                # mover's new geometry, matching the accepted sequential movement model.
                _update_pre_movement_contact(
                    turn, matrix, states_o, states_m, coord[other], coord[mover], bb[other], emissions[mover]
                )

            range_hex = _range(coord["A"], coord["B"])
            overall_min = min(overall_min, range_hex)
            a.telemetry.min_range = min(a.telemetry.min_range, range_hex)
            b.telemetry.min_range = min(b.telemetry.min_range, range_hex)

            if combat_doctrine == UTILITY_COMBAT_DOCTRINE:
                # CP147 observes only missiles already in flight.  Project whether
                # each can reach terminal this Missile phase from the post-Movement
                # geometry without consulting the hidden opponent build.
                for target_label, target_state in (("A", a), ("B", b)):
                    target_state.cp147_terminal_threats = _cp147_project_terminal_threats(
                        matrix, target_state, coord[target_label], [m for m in missiles if m.target == target_label]
                    )
                    target_state.cp147_inbound_subflights=sum(1 for m in missiles if m.target==target_label)
                    target_state.cp147_inbound_expected_raw_total=sum(float(m.damage)*max(1,int(m.packets))*max(0,min(100,int(m.guidance)))/100.0 for m in missiles if m.target==target_label)
                    penalties=[int(m.pds_intercept_penalty_pp) for m in missiles if m.target==target_label]
                    target_state.cp147_inbound_pds_penalty_pp=round(sum(penalties)/len(penalties)) if penalties else 0

            _phase_event(event_sink, turn, "ElectronicWarfare")

            # Simultaneous ECM declaration, then bilateral sensor/ECCM resolution.
            pre_a = _plan_once(matrix, a, b, range_hex, inbound_a, power_a, False, combat_doctrine)
            pre_b = _plan_once(matrix, b, a, range_hex, inbound_b, power_b, False, combat_doctrine)
            ecm_a, ecm_b = bool(pre_a["ecm_on"]), bool(pre_b["ecm_on"])
            pa, available_a = _maybe_reactor_overload(matrix, a, b, range_hex, inbound_a, power_a, ecm_b, combat_doctrine)
            pb, available_b = _maybe_reactor_overload(matrix, b, a, range_hex, inbound_b, power_b, ecm_a, combat_doctrine)
            desired_actions: dict[str, list[dict[str, Any]]] = {"A": [], "B": []}
            allocations: dict[str, dict[str, int]] = {"A": {}, "B": {}}
            if turn_telemetry_sink is not None:
                desired_actions["A"] = _cp140_plan_action_requests(matrix, a, b, range_hex, inbound_a, ecm_b, shield_request_a, combat_doctrine)
                desired_actions["B"] = _cp140_plan_action_requests(matrix, b, a, range_hex, inbound_b, ecm_a, shield_request_b, combat_doctrine)
                allocations["A"] = _cp140_plan_allocations(pa, shield_spend_a)
                allocations["B"] = _cp140_plan_allocations(pb, shield_spend_b)
            _record_plan(a, pa, power_a, inbound_a)
            _record_plan(b, pb, power_b, inbound_b)

            active_a = pa["sensor_mode"] != "passive"
            active_b = pb["sensor_mode"] != "passive"
            emissions = {"A": (bool(pa["ecm_on"]), active_a), "B": (bool(pb["ecm_on"]), active_b)}

            for label, side, plan, opp_em in (("A", a, pa, emissions["B"]), ("B", b, pb, emissions["A"])):
                if plan["track"] != "None" or opp_em[0] or opp_em[1]:
                    bb[label].establish_contact(turn)
                if bb[label].contact_established:
                    bb[label].record_track(
                        range_hex, str(plan["track"]), opp_em[0], opp_em[1], bool(plan["ecm_downgrade"])
                    )
                side.contact = bb[label].contact_established
                side.last_track = str(plan["track"])

            _phase_event(event_sink, turn, "DirectFire")
            damage_queue: list[DamageCommit] = []
            commits: list[tuple[str, SideState, bool, int, int, int, bool, bool, bool]] = []
            plans = {"A": pa, "B": pb}
            for label, side, target in (("A", a, b), ("B", b, a)):
                plan = plans[label]
                other = "B" if label == "A" else "A"
                w = _weapon(matrix, side.build)
                # Missile launches belong to the later Missile / Interception
                # phase. Direct Fire only commits non-Missile batteries.
                if w["family"] == "Missile":
                    continue
                if plan["track"] not in ("Firm", "Approximate") or range_hex > int(w["range"]):
                    continue
                action_happened = False
                side.telemetry.direct_fire_eligible_actions += int(w["count"])
                for weapon_index, wp in enumerate(plan["weapon_plans"]):
                    if wp is None:
                        continue
                    if plan.get("weapon_actions", [None] * len(plan["weapon_plans"]))[weapon_index] == "hold_missile":
                        continue
                    if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                        continue
                    if side.weapon_ammo is not None:
                        side.weapon_ammo -= 1
                    _, damage, accuracy = wp
                    standard_range = int(w.get("standard_range", w["range"]))
                    track_penalty = int(matrix.doc.get("combatModifiers", {}).get("directFireApproximateTrackPenaltyPp", -25)) if plan["track"] == "Approximate" else 0
                    range_penalty = int(matrix.doc.get("combatModifiers", {}).get("directFireExtendedRangePenaltyPp", -10)) if range_hex > standard_range else 0
                    total_penalty = track_penalty + range_penalty
                    chance = _hit_chance(matrix, side.build, range_hex, accuracy, str(plan["track"]), standard_range, int(w["range"]))
                    hit = rngs[(physical[label], "direct")].d100() <= chance
                    side.telemetry.direct_shots += 1
                    if plan["track"] == "Approximate": side.telemetry.direct_approximate_shots += 1
                    else: side.telemetry.direct_firm_shots += 1
                    if range_hex > standard_range: side.telemetry.direct_extended_range_shots += 1
                    else: side.telemetry.direct_standard_range_shots += 1
                    if plan["track"] == "Approximate" and range_hex > standard_range: side.telemetry.direct_stacked_penalty_shots += 1
                    side.telemetry.direct_accuracy_penalty_pp_total += total_penalty
                    if hit:
                        side.telemetry.direct_hits += 1
                    target_plan = plans[other]
                    commits.append((label, target, hit, int(damage), int(w["spen"]), int(w["apen"]), bool(target_plan["hardener_active"]), bool(target_plan.get("energized_armor_active",False)), bool(target_plan.get("field_stabilizer_active",False))))
                    action_happened = True
                    if event_sink is not None:
                        event_sink.append({"turn":turn,"event":"direct_fire","side":label,"range":range_hex,"track":str(plan["track"]),"penalty_pp":total_penalty,"mode":plan.get("weapon_modes", [None]*len(plan["weapon_plans"]))[weapon_index],"chance":chance,"hit":hit,"damage":int(damage)})
                if action_happened:
                    if plan["track"] == "Firm" and range_hex <= int(w.get("standard_range", w["range"])):
                        bb[label].record_own_attack(range_hex)
                    bb[other].establish_contact(turn)
                    bb[other].record_observed_attack(range_hex)
                    if combat_doctrine in (CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE) and states[other].known_opponent_weapon_family is None:
                        states[other].known_opponent_weapon_family = str(w["family"])
                        states[other].known_opponent_weapon_turn = turn
                        bb[other].known_opponent_weapon_family = str(w["family"])
                        bb[other].known_opponent_weapon_turn = turn
                        if event_sink is not None:
                            event_sink.append({"turn": turn, "event": "opponent_capability_revealed", "observer": other, "weapon_family": str(w["family"]), "source": "direct_fire"})

            # Direct attacks are committed now but damage is deferred to the
            # canonical Damage phase. This preserves simultaneous commitment: a
            # ship destroyed later in the turn still resolves its already-
            # committed volley. Resolution order follows movement/activation
            # order without canceling an already committed opposing volley.
            for resolving_owner in order:
                for owner, target, hit, damage, spen, apen, target_hardener, target_energized, target_stabilizer in commits:
                    if owner != resolving_owner or not hit:
                        continue
                    target_label = "B" if owner == "A" else "A"
                    damage_queue.append(DamageCommit(
                        "DirectFire", owner, target_label, "direct", damage, spen, apen, target_hardener, target_energized, target_stabilizer
                    ))

            _phase_event(event_sink, turn, "MissileAndInterception")

            # Missile launch is part of Missile / Interception, not Direct Fire.
            # Newly launched flights may move during this same Missile phase.
            for label, side in (("A", a), ("B", b)):
                plan = plans[label]
                other = "B" if label == "A" else "A"
                w = _weapon(matrix, side.build)
                if w["family"] != "Missile":
                    continue
                action_happened = False
                ammo_before = int(side.weapon_ammo) if side.weapon_ammo is not None else -1
                planned_weapon_actions = sum(wp is not None for wp in plan.get("weapon_plans", []))
                desired_weapon_tp = sum(int(x.get("requested", 0)) for x in desired_actions.get(label, []) if x.get("category") == "weapon")
                allocated_weapon_tp = sum(int(v) for k, v in allocations.get(label, {}).items() if str(k).startswith("weapon_"))
                launch_block_reason = "READY"
                if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                    launch_block_reason = "AMMO_EXHAUSTED"
                elif plan["track"] != "Firm":
                    launch_block_reason = "NO_FIRM_TRACK"
                elif range_hex > int(w["range"]):
                    launch_block_reason = "OUT_OF_RANGE"
                elif planned_weapon_actions <= 0:
                    launch_block_reason = "NO_WEAPON_PLAN"
                if plan["track"] == "Firm" and range_hex <= int(w["range"]):
                    side.telemetry.missile_launch_eligible_actions += int(w["count"])
                    for wp in plan["weapon_plans"]:
                        if wp is None:
                            continue
                        if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                            continue
                        if side.weapon_ammo is not None:
                            side.weapon_ammo -= 1
                        subflights = max(1, int(w.get("subflights", 1)))
                        magazine_flight_serial += 1
                        magazine_id = magazine_flight_serial
                        first_serial = missile_serial + 1
                        for _subflight in range(subflights):
                            missile_serial += 1
                            missiles.append(FullMapMissile(
                                owner=label,
                                target=other,
                                coordinate=coord[label],
                                last_target_coordinate=coord[other],
                                damage=float(w["damage"]), spen=int(w["spen"]), apen=int(w["apen"]),
                                guidance=int(w["guidance"]), speed=max(1, int(w["missile_move"])),
                                maximum_travel=int(w["range"]), packets=max(1, int(w.get("packets", 1))),
                                pds_intercept_penalty_pp=int(w.get("pds_intercept_penalty_pp", 0)),
                                profile_id=str(w.get("profile_id", "GP")),
                                flight_id=missile_serial, magazine_flight_id=magazine_id, launch_turn=turn,
                            ))
                        # A reconciled Swarmer still consumes and records one magazine Flight.
                        side.telemetry.missile_launches += 1
                        if str(w.get("profile_id", "GP")) == "GP":
                            side.telemetry.payload_gp_launches += 1
                        else:
                            side.telemetry.payload_specialist_launches += 1
                        action_happened = True
                        if event_sink is not None:
                            event_sink.append({
                                "turn": turn, "event": "missile_launch", "side": label, "target": other,
                                "profile_id": str(w.get("profile_id", "GP")), "magazine_flight_id": magazine_id, "subflights": subflights,
                                "first_flight_id": first_serial, "last_flight_id": missile_serial,
                                "range": range_hex, "track": str(plan["track"]),
                                "ammo_remaining": int(side.weapon_ammo) if side.weapon_ammo is not None else "",
                                "allocated_weapon_tp": allocated_weapon_tp, "desired_weapon_tp": desired_weapon_tp,
                            })
                if event_sink is not None:
                    if action_happened:
                        decision = "LAUNCHED"
                    else:
                        decision = launch_block_reason
                    event_sink.append({
                        "turn": turn, "event": "missile_launch_decision", "side": label,
                        "range": range_hex, "track": str(plan["track"]), "track_no_ew": str(plan.get("track_no_ew", "None")),
                        "sensor_mode": str(plan.get("sensor_mode", "passive")), "ecm_downgrade": int(bool(plan.get("ecm_downgrade", False))),
                        "weapon_range": int(w["range"]),
                        "ammo_before": ammo_before,
                        "ammo_after": int(side.weapon_ammo) if side.weapon_ammo is not None else -1,
                        "planned_weapon_actions": planned_weapon_actions,
                        "desired_weapon_tp": desired_weapon_tp, "allocated_weapon_tp": allocated_weapon_tp,
                        "decision": decision,
                    })
                if action_happened:
                    bb[label].record_own_attack(range_hex)
                    bb[other].establish_contact(turn)
                    bb[other].record_observed_attack(range_hex)
                    if combat_doctrine in (CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE):
                        first_reveal = states[other].known_opponent_weapon_family is None
                        if first_reveal:
                            states[other].known_opponent_weapon_family = "Missile"
                            states[other].known_opponent_weapon_turn = turn
                            bb[other].known_opponent_weapon_family = "Missile"
                            bb[other].known_opponent_weapon_turn = turn
                        states[other].known_opponent_missile_profile = str(w.get("profile_id", "GP"))
                        if combat_doctrine == UTILITY_COMBAT_DOCTRINE:
                            states[other].known_opponent_missile_expected_raw_per_subflight = float(w["damage"]) * max(1,int(w.get("packets",1))) * max(0,min(100,int(w["guidance"]))) / 100.0
                            states[other].known_opponent_missile_pds_penalty_pp = int(w.get("pds_intercept_penalty_pp",0))
                            states[other].known_opponent_missile_subflights = int(w.get("subflights",1))
                        if event_sink is not None and first_reveal:
                            event_sink.append({"turn": turn, "event": "opponent_capability_revealed", "observer": other, "weapon_family": "Missile", "missile_profile": str(w.get("profile_id", "GP")), "source": "missile_launch"})

            # Real finite-map missile pursuit against the current post-Movement target coordinate.
            terminal: list[FullMapMissile] = []
            survivors: list[FullMapMissile] = []
            for m in missiles:
                target_coord = coord[m.target]
                owner_state = a if m.owner == "A" else b
                owner_extra = extra[m.owner]
                owner_extra.missile_reroutes += 1
                if target_coord != m.last_target_coordinate:
                    owner_extra.missile_target_movement_reroutes += 1
                pre_advance_range = m.coordinate.distance_to(target_coord)
                adv = advance_missile_finite_map(
                    map_, m.coordinate, target_coord, m.speed, m.maximum_travel, m.distance_traveled
                )
                m.coordinate = adv.destination
                m.distance_traveled = adv.total_distance_traveled
                m.last_target_coordinate = target_coord
                owner_extra.missile_movement_hexes += adv.distance_traveled_this_phase
                owner_extra.maximum_missile_distance_traveled = max(
                    owner_extra.maximum_missile_distance_traveled, m.distance_traveled
                )
                if adv.range_exhausted:
                    owner_extra.missile_range_exhausted += 1
                    if event_sink is not None:
                        event_sink.append({
                            "turn": turn, "event": "missile_range_exhausted", "owner": m.owner, "target": m.target,
                            "profile_id": m.profile_id, "flight_id": m.flight_id, "magazine_flight_id": m.magazine_flight_id, "launch_turn": m.launch_turn,
                            "elapsed_turns": turn - m.launch_turn, "distance": m.distance_traveled,
                        })
                    continue
                if adv.terminal:
                    # CP154 research support: an AMM RC3 profile may expose one
                    # distinct range-1 opportunity before the Flight enters the
                    # target hex. A flight launched already in the target hex did
                    # not traverse that window. This flag is inert for historical
                    # profiles and does not alter production C# semantics.
                    m.range_one_window_eligible = pre_advance_range >= 1
                    terminal.append(m)
                else:
                    survivors.append(m)
            missiles = survivors

            # CP154 research-only AMM RC3 layer. RC and engagement windows are
            # distinct: RC3 exposes one range-1 opportunity plus the two ordinary
            # terminal windows. The early shot resolves against the magazine Flight
            # before Swarmer terminal subflights are individually exposed. If it
            # misses, remaining RC stays committed to that first arriving Flight
            # before later Flights may consume capacity.
            pds_preterminal_used = {"A": 0, "B": 0}
            for target_label, target, plan in (("A", a, pa), ("B", b, pb)):
                pds = plan.get("pds")
                planned_rc = int(plan.get("pds_rc", 0))
                if not (pds is not None and bool(pds.get("rangeOneAttempt", False)) and planned_rc >= 3):
                    continue
                groups: list[tuple[int, list[FullMapMissile]]] = []
                seen_mag: set[int] = set()
                for mm in terminal:
                    if mm.target != target_label or not mm.range_one_window_eligible:
                        continue
                    mid = int(mm.magazine_flight_id)
                    if mid in seen_mag:
                        continue
                    seen_mag.add(mid)
                    groups.append((mid, [x for x in terminal if x.target == target_label and int(x.magazine_flight_id) == mid]))
                for mid, group in groups:
                    if pds_preterminal_used[target_label] >= planned_rc:
                        break
                    if target.pds_ammo is not None and target.pds_ammo <= 0:
                        break
                    rep = group[0]
                    target.telemetry.pds_attempts += 1
                    target.telemetry.pds_range_one_attempts += 1
                    pds_preterminal_used[target_label] += 1
                    if target.pds_ammo is not None:
                        target.pds_ammo -= 1
                    chance = min(95, int(pds["baseChancePp"]) + int(matrix.p("computer", target.build.tl)["targetingPp"]))
                    chance = max(0, chance - int(rep.pds_intercept_penalty_pp))
                    hit = rngs[(physical[target_label], "pds")].d100() <= chance
                    if event_sink is not None:
                        event_sink.append({"turn":turn,"event":"pds_range_one_attempt","target":target_label,"magazine_flight_id":mid,"chance":chance,"intercepted":int(hit)})
                    if hit:
                        target.telemetry.pds_intercepts += 1
                        target.telemetry.pds_range_one_intercepts += 1
                        terminal = [x for x in terminal if not (x.target == target_label and int(x.magazine_flight_id) == mid)]
                        # The first Flight is gone; remaining RC may be offered to
                        # the next arriving Flight's range-1 window.
                        continue
                    # Miss: remaining RC belongs to the same first Flight at its
                    # two terminal windows, so do not skip ahead to another Flight.
                    break

            # CP146 restores the accepted Held Main layer to the whole-combat
            # research kernel. One K/E bank held during Direct Fire may make one
            # Firm-track interception attempt before terminal PDS. The accepted
            # C# calibration uses base 50 + weapon accuracy + Tactical Computer
            # with no ordinary ship-target range penalty; eligibility is bounded
            # by the weapon's missile-interception maximum range.
            if combat_doctrine in (CONTEXTUAL_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE):
                for target_label, target, plan in (("A", a, pa), ("B", b, pb)):
                    _resolve_cp146_held_main_layer(
                        matrix, target_label, target, plan, terminal, missiles,
                        coord[target_label], rngs[(physical[target_label], "held")],
                        turn, event_sink,
                    )

            for target_label, target, plan in (("A", a, pa), ("B", b, pb)):
                threats = [m for m in terminal if m.target == target_label]
                reaction_used = int(pds_preterminal_used.get(target_label, 0))
                pds = plan["pds"]
                pds_ammo_before = int(target.pds_ammo) if target.pds_ammo is not None else -1
                zero_attempt_flights = 0
                one_attempt_flights = 0
                two_attempt_flights = 0
                first_attempt_intercepts = 0
                second_attempt_intercepts = 0
                unserved_attempt_opportunities = 0
                attempts_by_magazine: dict[int, list[int]] = {}
                for m in threats:
                    target.telemetry.missile_terminal_arrivals += 1
                    intercepted = False
                    attempts_on_flight = 0
                    last_pds_chance = 0
                    while reaction_used < int(plan["pds_rc"]) and attempts_on_flight < 2:
                        if target.pds_ammo is not None and target.pds_ammo <= 0:
                            break
                        target.telemetry.pds_attempts += 1
                        reaction_used += 1
                        attempts_on_flight += 1
                        if pds is not None:
                            safe_rc = int(pds.get("safeReactionCapacity", pds.get("reactionCapacity", 0)))
                            strain_per = int(pds.get("extraReactionStrain", 0))
                            # Strain is incurred only when an overcharged reaction
                            # is actually fired, not merely when TP was reserved.
                            if strain_per > 0 and reaction_used > safe_rc:
                                target.pds_strain += strain_per
                                target.telemetry.pds_overcharge_attempts += 1
                                target.telemetry.pds_overcharge_strain_added += strain_per
                                target.telemetry.pds_max_strain = max(target.telemetry.pds_max_strain, target.pds_strain)
                        if target.pds_ammo is not None:
                            target.pds_ammo -= 1
                        chance = 0
                        if pds is not None:
                            chance = min(95, int(pds["baseChancePp"]) + int(matrix.p("computer", target.build.tl)["targetingPp"]))
                        chance = max(0, chance - int(m.pds_intercept_penalty_pp))
                        last_pds_chance = chance
                        if rngs[(physical[target_label], "pds")].d100() <= chance:
                            target.telemetry.pds_intercepts += 1
                            intercepted = True
                            if event_sink is not None:
                                event_sink.append({"turn":turn,"event":"pds_intercept","target":target_label,"chance":chance})
                            break
                    if attempts_on_flight == 0:
                        zero_attempt_flights += 1
                    elif attempts_on_flight == 1:
                        one_attempt_flights += 1
                    else:
                        two_attempt_flights += 1
                    attempts_by_magazine.setdefault(int(m.magazine_flight_id), []).append(int(attempts_on_flight))
                    if intercepted and attempts_on_flight == 1:
                        first_attempt_intercepts += 1
                    elif intercepted and attempts_on_flight == 2:
                        second_attempt_intercepts += 1
                    if not intercepted:
                        unserved_attempt_opportunities += max(0, 2 - attempts_on_flight)
                    guidance_attempted = not intercepted
                    guidance_success = False
                    if guidance_attempted:
                        target.telemetry.missile_guidance_attempts += 1
                        guidance_success = rngs[(physical[m.owner], "guidance")].d100() <= int(m.guidance)
                        if guidance_success:
                            target.telemetry.missile_hits += 1
                            for _ in range(m.packets):
                                damage_queue.append(DamageCommit(
                                    "MissileAndInterception", m.owner, target_label, "missile",
                                    m.damage, m.spen, m.apen, bool(plan["hardener_active"]), bool(plan.get("energized_armor_active",False)), bool(plan.get("field_stabilizer_active",False))
                                ))
                            target.contact = True
                            if event_sink is not None:
                                event_sink.append({"turn":turn,"event":"missile_hit","target":target_label,"damage":m.damage,"packets":m.packets})
                    if event_sink is not None:
                        event_sink.append({
                            "turn": turn, "event": "missile_terminal", "owner": m.owner, "target": target_label,
                            "profile_id": m.profile_id, "flight_id": m.flight_id, "launch_turn": m.launch_turn,
                            "elapsed_turns": turn - m.launch_turn, "distance": m.distance_traveled,
                            "pds_attempts": attempts_on_flight, "pds_intercepted": int(intercepted),
                            "pds_chance_last": last_pds_chance, "guidance_attempted": int(guidance_attempted),
                            "guidance_chance": int(m.guidance), "guidance_success": int(guidance_success),
                            "packets": int(m.packets), "damage_per_packet": float(m.damage),
                        })
                if event_sink is not None and threats:
                    magazine_flights = len(attempts_by_magazine)
                    magazine_any = sum(any(v > 0 for v in vals) for vals in attempts_by_magazine.values())
                    magazine_full = sum(all(v > 0 for v in vals) for vals in attempts_by_magazine.values())
                    magazine_partial = sum(any(v > 0 for v in vals) and not all(v > 0 for v in vals) for vals in attempts_by_magazine.values())
                    event_sink.append({
                        "turn": turn, "event": "pds_terminal_phase", "target": target_label,
                        "pds_family": str(target.build.pds_family or "NONE"),
                        # Legacy CP145 names retained as aliases. In CP146 the
                        # explicit terms distinguish one magazine Flight from the
                        # PDS-visible subflights generated by a Swarmer.
                        "threat_flights": len(threats),
                        "pds_visible_subflights": len(threats),
                        "terminal_magazine_flights": int(magazine_flights),
                        "magazine_flights_with_any_pds_attempt": int(magazine_any),
                        "magazine_flights_fully_covered": int(magazine_full),
                        "magazine_flights_partially_covered": int(magazine_partial),
                        "subflights_with_0_attempts": int(zero_attempt_flights),
                        "subflights_with_1_attempt": int(one_attempt_flights),
                        "subflights_with_2_attempts": int(two_attempt_flights),
                        "configured_reaction_capacity": int(pds.get("reactionCapacity", 0)) if pds is not None else 0,
                        "planned_reaction_capacity": int(plan.get("pds_rc", 0)),
                        "pds_readiness_tp": int(plan.get("pds_power", 0)),
                        "preterminal_range_one_attempts_used": int(pds_preterminal_used.get(target_label, 0)),
                        "reaction_attempts_used": int(reaction_used),
                        "zero_attempt_flights": int(zero_attempt_flights),
                        "one_attempt_flights": int(one_attempt_flights),
                        "two_attempt_flights": int(two_attempt_flights),
                        "first_attempt_intercepts": int(first_attempt_intercepts),
                        "second_attempt_intercepts": int(second_attempt_intercepts),
                        "unserved_attempt_opportunities": int(unserved_attempt_opportunities),
                        "rc_saturated": int(int(plan.get("pds_rc", 0)) > 0 and reaction_used >= int(plan.get("pds_rc", 0)) and unserved_attempt_opportunities > 0),
                        "zero_rc_with_threat": int(pds is not None and int(plan.get("pds_rc", 0)) == 0),
                        "pds_ammo_before": pds_ammo_before,
                        "pds_ammo_after": int(target.pds_ammo) if target.pds_ammo is not None else -1,
                    })

            if event_sink is not None:
                event_sink.append({
                    "turn": turn, "event": "missile_inventory",
                    "in_flight_a": sum(m.owner == "A" for m in missiles),
                    "in_flight_b": sum(m.owner == "B" for m in missiles),
                    "ammo_a": int(a.weapon_ammo) if a.build.weapon_family == "Missile" and a.weapon_ammo is not None else "",
                    "ammo_b": int(b.weapon_ammo) if b.build.weapon_family == "Missile" and b.weapon_ammo is not None else "",
                })

            _phase_event(event_sink, turn, "Damage")
            # Fixed phase order is the deterministic package-order authority:
            # Direct Fire commitments first, then terminal Missile packages.
            # All packages were committed before any damage is revealed.
            for commit in damage_queue:
                target = a if commit.target == "A" else b
                if target.hull <= 0:
                    # Pending destruction: later committed packets are overkill
                    # and do not continue stripping ordinary defensive state.
                    if event_sink is not None:
                        event_sink.append({
                            "turn": turn, "event": "overkill", "target": commit.target,
                            "source": commit.source, "damage": commit.damage,
                        })
                    continue
                defense_roll = None
                if getattr(matrix, "damage_model", CANONICAL_DAMAGE_MODEL) == DEF_RES_DAMAGE_MODEL:
                    defense_roll = rngs[(physical[commit.target], "defense")].d100()
                before_damage_state = (float(target.shield), float(target.armor_integrity), float(target.hull))
                _apply_committed_damage(matrix, target, commit, defense_roll, turn)
                after_damage_state = (float(target.shield), float(target.armor_integrity), float(target.hull))
                if any(after < before for before, after in zip(before_damage_state, after_damage_state)):
                    last_damage_state_change_turn = turn
                target.contact = True

            _sync_blackboard_summary(bb["A"], extra["A"])
            _sync_blackboard_summary(bb["B"], extra["B"])

            _phase_event(event_sink, turn, "DamageControl")
            # CP135 activates the existing Hull-repair Damage Control contract in the
            # same full-map kernel. The study doctrine is intentionally narrow and
            # consistent: if Hull is damaged, a surviving ship spends 1 TP + 1 Repair
            # Kit for one Hull attempt; success queues to the next Turn Refresh.
            # Component repair is not exercised. Any remaining Damage-Control-window
            # TP may then drive the separate built-in Armor regeneration capability.
            for label, side in (("A", a), ("B", b)):
                plan = plans[label]
                if side.hull <= 0:
                    if turn_telemetry_sink is not None:
                        context = dict(telemetry_context or {})
                        context["matrix"] = matrix
                        reactor_tp = reactor_tp_a if label == "A" else reactor_tp_b
                        available = available_a if label == "A" else available_b
                        pre_recharge_available = power_a if label == "A" else power_b
                        shield_spend = shield_spend_a if label == "A" else shield_spend_b
                        overload_tp = max(0, int(available) - int(pre_recharge_available))
                        turn_telemetry_sink.append(_cp140_finalize_turn_row(
                            context=context, trial_index=trial_index, turn=turn, label=label, side=side, plan=plan,
                            range_hex=range_hex, inbound=(inbound_a if label == "A" else inbound_b), reactor_tp=reactor_tp, overload_tp=overload_tp,
                            shield_spend=shield_spend, desired_actions=desired_actions[label], allocations=allocations[label],
                            dc_request=0, dc_spend=0, armor_request=0, armor_spend=0,
                        ))
                    continue
                remaining = int(plan.get("remaining", 0))
                dc_request = _cp140_damage_control_request(matrix, side) if turn_telemetry_sink is not None else 0
                spent_dc = _attempt_hull_damage_control(
                    matrix, side, remaining, rngs[(physical[label], "damcon")].d100()
                )
                remaining -= spent_dc
                armor_request = _cp140_armor_regen_request(matrix, side) if turn_telemetry_sink is not None else 0
                spent_regen = _apply_armor_regeneration(matrix, side, remaining)
                if event_sink is not None and spent_dc:
                    event_sink.append({"turn": turn, "event": "hull_damage_control", "side": label, "tp": spent_dc, "kits_remaining": side.repair_kits_remaining, "queued_hull": side.pending_hull_repair})
                if event_sink is not None and spent_regen:
                    event_sink.append({"turn": turn, "event": "armor_regeneration", "side": label, "tp": spent_regen, "armor": side.armor_integrity, "combat_regen_reserve_remaining": side.armor_regen_reserve_remaining})
                if turn_telemetry_sink is not None:
                    context = dict(telemetry_context or {})
                    context["matrix"] = matrix
                    reactor_tp = reactor_tp_a if label == "A" else reactor_tp_b
                    available = available_a if label == "A" else available_b
                    pre_recharge_available = power_a if label == "A" else power_b
                    shield_spend = shield_spend_a if label == "A" else shield_spend_b
                    overload_tp = max(0, int(available) - int(pre_recharge_available))
                    turn_telemetry_sink.append(_cp140_finalize_turn_row(
                        context=context, trial_index=trial_index, turn=turn, label=label, side=side, plan=plan,
                        range_hex=range_hex, inbound=(inbound_a if label == "A" else inbound_b), reactor_tp=reactor_tp, overload_tp=overload_tp,
                        shield_spend=shield_spend, desired_actions=desired_actions[label], allocations=allocations[label],
                        dc_request=dc_request, dc_spend=spent_dc, armor_request=armor_request, armor_spend=spent_regen,
                    ))

            if event_sink is not None:
                for state_label, state_side, state_plan in (("A", a, pa), ("B", b, pb)):
                    event_sink.append({
                        "turn": turn, "event": "missile_turn_state", "side": state_label,
                        "range": range_hex, "track": str(state_plan.get("track", "None")),
                        "shield": float(state_side.shield), "armor": float(state_side.armor_integrity), "hull": float(state_side.hull),
                        "shield_restored_total": int(state_side.telemetry.shield_base_restored + state_side.telemetry.shield_tactical_restored),
                        "armor_restored_total": int(state_side.telemetry.armor_regen_restored),
                        "hull_restored_total": int(state_side.telemetry.damage_control_hull_restored),
                        "missile_launches_total": int(state_side.telemetry.missile_launches),
                        "missile_ammo_remaining": int(state_side.weapon_ammo) if state_side.build.weapon_family == "Missile" and state_side.weapon_ammo is not None else "",
                        "tp_weapon": sum(int(v) for k, v in allocations.get(state_label, {}).items() if str(k).startswith("weapon_")),
                        "tp_conflict_flag": int(
                            len(desired_actions.get(state_label, [])) >= 2
                            and sum(max(0, int(x["requested"]) - int(allocations.get(state_label, {}).get(str(x["id"]), 0))) for x in desired_actions.get(state_label, [])) > 0
                            and sum(int(x["requested"]) for x in desired_actions.get(state_label, [])) > (reactor_tp_a + max(0, available_a - power_a) if state_label == "A" else reactor_tp_b + max(0, available_b - power_b))
                        ),
                    })

            if a.hull <= 0 or b.hull <= 0:
                winner = "Draw" if a.hull <= 0 and b.hull <= 0 else ("B" if a.hull <= 0 else "A")
                cause = "MUTUAL_DESTRUCTION" if winner == "Draw" else ("SIDE_A_DESTROYED" if winner == "B" else "SIDE_B_DESTROYED")
                return FullMapTrialResult(
                    winner, False, turn, range_hex, overall_min, a.hull, b.hull,
                    a.armor_integrity, b.armor_integrity, a.shield, b.shield,
                    a.telemetry, b.telemetry, extra["A"], extra["B"],
                    coord["A"].q, coord["A"].r, coord["B"].q, coord["B"].r,
                    termination_cause=cause,
                    last_damage_state_change_turn=last_damage_state_change_turn,
                    final_missiles_in_flight=len(missiles),
                )

            if _mutual_offensive_exhaustion(a, b, missiles):
                return FullMapTrialResult(
                    "Unresolved", True, turn, range_hex, overall_min, a.hull, b.hull,
                    a.armor_integrity, b.armor_integrity, a.shield, b.shield,
                    a.telemetry, b.telemetry, extra["A"], extra["B"],
                    coord["A"].q, coord["A"].r, coord["B"].q, coord["B"].r,
                    termination_cause="STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION",
                    last_damage_state_change_turn=last_damage_state_change_turn,
                    final_missiles_in_flight=0,
                )

        return FullMapTrialResult(
            "Unresolved", True, variant.max_turns, _range(coord["A"], coord["B"]), overall_min,
            a.hull, b.hull, a.armor_integrity, b.armor_integrity, a.shield, b.shield,
            a.telemetry, b.telemetry, extra["A"], extra["B"],
            coord["A"].q, coord["A"].r, coord["B"].q, coord["B"].r,
            termination_cause="TURN_CAP_SENTINEL",
            last_damage_state_change_turn=last_damage_state_change_turn,
            final_missiles_in_flight=len(missiles),
        )
    except Exception as exc:
        blank = SideTelemetry()
        extra_blank = FullMapTelemetry()
        return FullMapTrialResult(
            "Error", False, 0, 10, 10, 0, 0, 0, 0, 0, 0,
            blank, blank, extra_blank, extra_blank, -5, 0, 5, 0,
            f"{type(exc).__name__}: {exc}",
            termination_cause="ERROR",
        )


def aggregate_full_map_variant(variant: EcologyVariant, results: list[FullMapTrialResult]) -> dict[str, Any]:
    valid = [r for r in results if not r.error]
    n = len(results)
    wins = {k: sum(1 for r in results if r.winner == k) for k in ("A","B","Draw","Unresolved","Error")}
    row: dict[str, Any] = {
        "variant_id": variant.id,
        "tl": variant.tl,
        "movement_order": variant.movement_order,
        "geometry": FULL_MAP_GEOMETRY,
        "population": variant.population,
        "scenario_group": variant.scenario_group,
        "perturbation": variant.perturbation,
        "start_range": 10,
        "max_turns": variant.max_turns,
        "side_a_build": variant.side_a.id, "side_b_build": variant.side_b.id,
        "side_a_family": variant.side_a.weapon_family, "side_b_family": variant.side_b.weapon_family,
        "side_a_archetype": variant.side_a.archetype, "side_b_archetype": variant.side_b.archetype,
        "trials": n,
        "wins_a": wins["A"], "wins_b": wins["B"], "draws": wins["Draw"],
        "unresolved": wins["Unresolved"], "errors": wins["Error"],
        "win_rate_a": wins["A"] / max(1, n), "win_rate_b": wins["B"] / max(1, n),
        "draw_rate": wins["Draw"] / max(1, n),
        "conditional_win_rate_a": wins["A"] / max(1, wins["A"] + wins["B"]),
        "unresolved_rate": wins["Unresolved"] / max(1, n),
        "mean_turns": statistics.fmean(r.turns for r in valid) if valid else 0.0,
        "mean_final_range": statistics.fmean(r.final_range for r in valid) if valid else 0.0,
        "mean_min_range": statistics.fmean(r.min_range for r in valid) if valid else 0.0,
        "mean_final_hull_a": statistics.fmean(r.hull_a for r in valid) if valid else 0.0,
        "mean_final_hull_b": statistics.fmean(r.hull_b for r in valid) if valid else 0.0,
        "mean_final_armor_a": statistics.fmean(r.armor_a for r in valid) if valid else 0.0,
        "mean_final_armor_b": statistics.fmean(r.armor_b for r in valid) if valid else 0.0,
        "mean_final_shield_a": statistics.fmean(r.shield_a for r in valid) if valid else 0.0,
        "mean_final_shield_b": statistics.fmean(r.shield_b for r in valid) if valid else 0.0,
        "first_error": next((r.error for r in results if r.error), ""),
    }
    for prefix, attr in (("a", "side_a"), ("b", "side_b")):
        for f in fields(SideTelemetry):
            vals = [getattr(getattr(r, attr), f.name) for r in valid]
            row[f"mean_{prefix}_{f.name}"] = statistics.fmean(vals) if vals else 0.0
    for prefix, attr in (("a", "full_a"), ("b", "full_b")):
        for f in fields(FullMapTelemetry):
            vals = [getattr(getattr(r, attr), f.name) for r in valid]
            row[f"mean_{prefix}_{f.name}"] = statistics.fmean(vals) if vals else 0.0
    return row


def mirror_equivalent(first: FullMapTrialResult, second: FullMapTrialResult) -> bool:
    swap = {"A":"B","B":"A","Draw":"Draw","Unresolved":"Unresolved","Error":"Error"}
    if second.winner != swap[first.winner] or second.unresolved != first.unresolved or second.turns != first.turns:
        return False
    if (first.hull_a, first.hull_b, first.armor_a, first.armor_b, first.shield_a, first.shield_b) != (
        second.hull_b, second.hull_a, second.armor_b, second.armor_a, second.shield_b, second.shield_a
    ):
        return False
    # CP126 removes coordinate-handed tie breaks and uses physical/event RNG
    # streams, so side-swapped mover-swapped encounters must reproduce exactly.
    for f in fields(SideTelemetry):
        if getattr(first.side_a, f.name) != getattr(second.side_b, f.name):
            return False
        if getattr(first.side_b, f.name) != getattr(second.side_a, f.name):
            return False
    for f in fields(FullMapTelemetry):
        if getattr(first.full_a, f.name) != getattr(second.full_b, f.name):
            return False
        if getattr(first.full_b, f.name) != getattr(second.full_a, f.name):
            return False
    return True
