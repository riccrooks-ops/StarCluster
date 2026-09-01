from __future__ import annotations

from dataclasses import dataclass
import math


CANONICAL_DAMAGE_MODEL = "penetration-hardening-v1"
DIRECT_FIRE_APPROXIMATE_TRACK_PENALTY_PP = -25
DIRECT_FIRE_EXTENDED_RANGE_PENALTY_PP = -10


def direct_fire_accuracy_modifier(*, track: str, range_hex: int, standard_range: int, max_range: int) -> int:
    if range_hex < 0 or standard_range < 0 or max_range < standard_range:
        raise ValueError("invalid direct-fire range inputs")
    if range_hex > max_range:
        raise ValueError("direct-fire attack is beyond Maximum Range")
    if track not in ("Firm", "Approximate"):
        raise ValueError("direct-fire attack requires Firm or Approximate track")
    modifier = DIRECT_FIRE_APPROXIMATE_TRACK_PENALTY_PP if track == "Approximate" else 0
    if range_hex > standard_range:
        modifier += DIRECT_FIRE_EXTENDED_RANGE_PENALTY_PP
    return modifier


def energy_output_modes(standard_tp: int, standard_damage: int) -> dict[str, tuple[int, int]]:
    if standard_tp < 0 or standard_damage < 0:
        raise ValueError("Energy standard output cannot be negative")
    return {
        "Low": (math.ceil(standard_tp / 2), math.ceil(standard_damage / 2)),
        "Standard": (standard_tp, standard_damage),
        "Overload": (math.ceil(standard_tp * 1.5), math.ceil(standard_damage * 1.5)),
    }


@dataclass(frozen=True, slots=True)
class LayeredDamageResult:
    """Pure one-shield/one-primary-armor layered-damage result.

    Shield Capacity (SC) and Armor Integrity (AI) are the only ordinary
    defensive hit-point pools. Shield Armor (SA) and Armor Protection (AP)
    are penetration-hardening ratings: they reduce SPEN/APEN while their
    associated layer has at least one point remaining. They never absorb
    ordinary damage and are never consumed by damage resolution.
    """

    incoming_damage: int
    raw_spen: int
    raw_apen: int
    shield_hardening: int
    effective_spen: int
    shield_penetration_resisted: int
    shield_bypass: int
    shield_facing_damage: int
    shield_absorbed: int
    shield_overflow: int
    damage_to_armor: int
    armor_hardening: int
    effective_apen: int
    armor_penetration_resisted: int
    armor_bypass: int
    armor_facing_damage: int
    armor_absorbed: int
    armor_overflow: int
    hull_damage: int
    overkill_damage: int
    final_shield: int
    final_armor_integrity: int
    final_hull: int


def _nonnegative(name: str, value: int) -> int:
    value = int(value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def resolve_layered_damage(
    *,
    shield: int,
    armor_integrity: int,
    armor_protection: int,
    hull: int,
    damage: int,
    spen: int = 0,
    apen: int = 0,
    shield_armor: int = 0,
    temporary_armor_hardening: int = 0,
) -> LayeredDamageResult:
    """Resolve one deterministic damage packet through SC -> AI -> Hull.

    Rules:
    - Penetration never creates damage.
    - While SC > 0, effective SPEN = max(0, SPEN - SA). Up to that much
      packet damage bypasses SC. Remaining damage attacks SC; overflow joins
      the bypassed damage at Armor.
    - When SC == 0, SA is inactive and all packet damage proceeds to Armor.
    - While AI > 0, effective APEN = max(0, APEN - AP). Up to that much
      damage reaching Armor bypasses AI. Remaining damage attacks AI;
      overflow joins bypassed damage at Hull.
    - When AI == 0, AP is inactive and all damage reaching Armor proceeds to
      Hull.
    - SA/AP are hardening ratings only. They do not absorb ordinary damage,
      do not lose points, and do not become secondary durability tracks.
    """

    shield = _nonnegative("shield", shield)
    armor_integrity = _nonnegative("armor_integrity", armor_integrity)
    armor_protection = _nonnegative("armor_protection", armor_protection)
    hull = _nonnegative("hull", hull)
    damage = _nonnegative("damage", damage)
    spen = _nonnegative("spen", spen)
    apen = _nonnegative("apen", apen)
    shield_armor = _nonnegative("shield_armor", shield_armor)
    temporary_armor_hardening = _nonnegative(
        "temporary_armor_hardening", temporary_armor_hardening
    )

    if shield > 0:
        effective_spen = max(0, spen - shield_armor)
        shield_penetration_resisted = spen - effective_spen
        shield_bypass = min(damage, effective_spen)
        shield_facing = damage - shield_bypass
        shield_absorbed = min(shield, shield_facing)
        final_shield = shield - shield_absorbed
        shield_overflow = shield_facing - shield_absorbed
        damage_to_armor = shield_bypass + shield_overflow
        active_shield_hardening = shield_armor
    else:
        # There is no live shield layer to penetrate or harden.
        effective_spen = 0
        shield_penetration_resisted = 0
        shield_bypass = 0
        shield_facing = 0
        shield_absorbed = 0
        final_shield = 0
        shield_overflow = damage
        damage_to_armor = damage
        active_shield_hardening = 0

    if armor_integrity > 0:
        active_armor_hardening = armor_protection + temporary_armor_hardening
        effective_apen = max(0, apen - active_armor_hardening)
        armor_penetration_resisted = apen - effective_apen
        armor_bypass = min(damage_to_armor, effective_apen)
        armor_facing = damage_to_armor - armor_bypass
        armor_absorbed = min(armor_integrity, armor_facing)
        final_armor = armor_integrity - armor_absorbed
        armor_overflow = armor_facing - armor_absorbed
        damage_to_hull = armor_bypass + armor_overflow
    else:
        active_armor_hardening = 0
        effective_apen = 0
        armor_penetration_resisted = 0
        armor_bypass = 0
        armor_facing = 0
        armor_absorbed = 0
        final_armor = 0
        armor_overflow = damage_to_armor
        damage_to_hull = damage_to_armor

    hull_damage = min(hull, damage_to_hull)
    final_hull = hull - hull_damage
    overkill = damage_to_hull - hull_damage

    return LayeredDamageResult(
        incoming_damage=damage,
        raw_spen=spen,
        raw_apen=apen,
        shield_hardening=active_shield_hardening,
        effective_spen=effective_spen,
        shield_penetration_resisted=shield_penetration_resisted,
        shield_bypass=shield_bypass,
        shield_facing_damage=shield_facing,
        shield_absorbed=shield_absorbed,
        shield_overflow=shield_overflow,
        damage_to_armor=damage_to_armor,
        armor_hardening=active_armor_hardening,
        effective_apen=effective_apen,
        armor_penetration_resisted=armor_penetration_resisted,
        armor_bypass=armor_bypass,
        armor_facing_damage=armor_facing,
        armor_absorbed=armor_absorbed,
        armor_overflow=armor_overflow,
        hull_damage=hull_damage,
        overkill_damage=overkill,
        final_shield=final_shield,
        final_armor_integrity=final_armor,
        final_hull=final_hull,
    )

# CP139 research-only DEF/RES candidate. The production/default combat model remains
# penetration-hardening-v1; callers must opt in explicitly.
DEF_RES_DAMAGE_MODEL = "def-res-v1"
SHIELD_DEF_EFFECTIVE_CAP_PP = 45.0
ARMOR_RES_EFFECTIVE_CAP_PP = 95.0


@dataclass(frozen=True, slots=True)
class DefResDamageResult:
    incoming_damage: float
    effective_def_pp: float
    deflected: bool
    shield_absorbed: float
    shield_overflow: float
    damage_to_armor: float
    effective_res_pp: float
    armor_resisted_damage: float
    armor_damage: float
    armor_overflow_raw: float
    hull_damage: float
    overkill_damage: float
    final_shield: float
    final_armor_integrity: float
    final_hull: float


def _nonnegative_float(name: str, value: float) -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} cannot be negative")
    return value


def resolve_def_res_damage(
    *,
    shield: float,
    armor_integrity: float,
    hull: float,
    damage: float,
    spen: float = 0,
    apen: float = 0,
    shield_def_pp: float = 0,
    armor_res_pp: float = 0,
    defense_roll: int = 100,
) -> DefResDamageResult:
    """Resolve one CP139 research-only DEF/RES packet.

    Shield DEF is a whole-packet deflection probability. SPEN reduces DEF before
    the 45 pp effective cap. If the packet is not deflected, Shield Capacity
    absorbs raw damage normally and overflow continues inward.

    Armor RES is continuous fractional mitigation. APEN reduces RES before the
    95 pp effective cap. If the packet collapses Armor partway through, RES is
    applied only to the raw amount required to consume the remaining Armor; the
    unused raw portion then reaches Hull unmitigated.
    """
    shield = _nonnegative_float("shield", shield)
    armor_integrity = _nonnegative_float("armor_integrity", armor_integrity)
    hull = _nonnegative_float("hull", hull)
    damage = _nonnegative_float("damage", damage)
    spen = _nonnegative_float("spen", spen)
    apen = _nonnegative_float("apen", apen)
    shield_def_pp = _nonnegative_float("shield_def_pp", shield_def_pp)
    armor_res_pp = _nonnegative_float("armor_res_pp", armor_res_pp)
    defense_roll = int(defense_roll)
    if not 1 <= defense_roll <= 100:
        raise ValueError("defense_roll must be 1..100")

    if shield > 0:
        effective_def = min(SHIELD_DEF_EFFECTIVE_CAP_PP, max(0.0, shield_def_pp - spen))
        deflected = defense_roll <= effective_def
    else:
        effective_def = 0.0
        deflected = False

    if deflected or damage <= 0:
        return DefResDamageResult(
            damage, effective_def, deflected, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, shield, armor_integrity, hull,
        )

    if shield > 0:
        shield_absorbed = min(shield, damage)
        final_shield = shield - shield_absorbed
        shield_overflow = damage - shield_absorbed
    else:
        shield_absorbed = 0.0
        final_shield = 0.0
        shield_overflow = damage
    damage_to_armor = shield_overflow

    effective_res = 0.0
    armor_resisted = 0.0
    armor_damage = 0.0
    armor_overflow_raw = damage_to_armor
    final_armor = armor_integrity
    if armor_integrity > 0 and damage_to_armor > 0:
        effective_res = min(ARMOR_RES_EFFECTIVE_CAP_PP, max(0.0, armor_res_pp - apen))
        pass_fraction = 1.0 - effective_res / 100.0
        raw_to_collapse = armor_integrity / pass_fraction
        raw_against_armor = min(damage_to_armor, raw_to_collapse)
        armor_damage = raw_against_armor * pass_fraction
        armor_resisted = raw_against_armor - armor_damage
        final_armor = max(0.0, armor_integrity - armor_damage)
        armor_overflow_raw = max(0.0, damage_to_armor - raw_against_armor)

    hull_damage = min(hull, armor_overflow_raw)
    final_hull = hull - hull_damage
    overkill = armor_overflow_raw - hull_damage
    return DefResDamageResult(
        damage, effective_def, False, shield_absorbed, shield_overflow,
        damage_to_armor, effective_res, armor_resisted, armor_damage,
        armor_overflow_raw, hull_damage, overkill, final_shield, final_armor,
        final_hull,
    )

