from __future__ import annotations

import csv
import json
import math
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, fields
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

from .ecology import (
    CandidateMatrix,
    EcologyBuild,
    SideState,
    SideTelemetry,
    MAP_RADIUS,
    MAX_TURNS,
    DAMAGE_MODEL,
    build_space,
    generate_primary_builds,
    _create_side,
    _range,
    _begin_turn_recharge,
    _move_one,
    _plan_once,
    _maybe_reactor_overload,
    _record_plan,
    _weapon,
    _hit_chance,
    _shield_armor,
    _apply_damage,
)
from .rng import XorShift64, derive_seed
from .study import load_json


@dataclass(frozen=True, slots=True)
class FamilyProfile:
    id: str
    family: str
    role: str
    study_tls: tuple[int, ...]
    generation: str = ""
    damage: int | None = None
    damage_delta: int = 0
    spen: int | None = None
    spen_delta: int = 0
    apen: int | None = None
    apen_delta: int = 0
    accuracy_delta: int = 0
    packets: int = 1
    ordered_packets: tuple[tuple[int, int, int], ...] = ()
    shield_bonus_damage: int = 0
    shield_armor_reduction: int = 0
    recharge_suppression: int = 0
    guidance_delta: int = 0
    pds_intercept_penalty_pp: int = 0

    @property
    def is_gp(self) -> bool:
        return self.id == "gp-current" or "-gp-" in self.id


@dataclass(frozen=True, slots=True)
class TargetFixture:
    id: str
    base_family: str
    base_archetype: str
    classification: str
    role: str
    remove_shield: bool = False
    remove_pds: bool = False
    remove_hardener: bool = False
    armor_protection_delta: int = 0
    armor_integrity_delta: int = 0
    armor_protection_override: int | None = None
    armor_integrity_override: int | None = None
    shield_capacity_delta: int = 0
    shield_recharge_bonus: int = 0
    hull_delta: int = 0


@dataclass(frozen=True, slots=True)
class FamilyVariant:
    id: str
    tl: int
    side_a: EcologyBuild
    side_b: EcologyBuild
    movement_order: str
    side_a_profile: str
    scenario_group: str
    target_fixture: str
    target_classification: str
    start_q_a: int = -MAP_RADIUS
    start_q_b: int = MAP_RADIUS
    max_turns: int = MAX_TURNS
    population: str = "targeted_same_tl_weapon_family_characteristic"


@dataclass(slots=True)
class FamilyMissileState:
    owner: str
    eta: int
    guidance: int
    profile_id: str
    damage: int
    spen: int
    apen: int
    packets: int
    shield_bonus_damage: int
    shield_armor_reduction: int
    recharge_suppression: int
    pds_intercept_penalty_pp: int


@dataclass(frozen=True, slots=True)
class FamilyTrialResult:
    winner: str
    unresolved: bool
    turns: int
    hull_a: int
    hull_b: int
    armor_a: int
    armor_b: int
    shield_a: int
    shield_b: int
    side_a: SideTelemetry
    side_b: SideTelemetry
    error: str = ""


class FamilyCatalog:
    def __init__(self, doc: dict[str, Any]):
        self.missile: dict[str, FamilyProfile] = {}
        self.kinetic: dict[str, FamilyProfile] = {}
        for family_key, target in (("missileProfiles", self.missile), ("kineticProfiles", self.kinetic)):
            for row in doc.get(family_key, []):
                ordered = tuple(
                    (int(p["damage"]), int(p.get("spen", 0)), int(p.get("apen", 0)))
                    for p in row.get("orderedPackets", [])
                )
                p = FamilyProfile(
                    id=str(row["id"]),
                    family=str(row["family"]),
                    role=str(row["role"]),
                    study_tls=tuple(int(x) for x in row.get("studyTls", [])),
                    generation=str(row.get("generation", "")),
                    damage=row.get("damage"),
                    damage_delta=int(row.get("damageDelta", 0)),
                    spen=row.get("spen"),
                    spen_delta=int(row.get("spenDelta", 0)),
                    apen=row.get("apen"),
                    apen_delta=int(row.get("apenDelta", 0)),
                    accuracy_delta=int(row.get("accuracyDelta", 0)),
                    packets=int(row.get("packets", 1)),
                    ordered_packets=ordered,
                    shield_bonus_damage=int(row.get("shieldBonusDamage", 0)),
                    shield_armor_reduction=int(row.get("shieldArmorReduction", 0)),
                    recharge_suppression=int(row.get("rechargeSuppression", 0)),
                    guidance_delta=int(row.get("guidanceDelta", 0)),
                    pds_intercept_penalty_pp=int(row.get("pdsInterceptPenaltyPp", 0)),
                )
                target[p.id] = p
        self.fixtures: dict[str, TargetFixture] = {}
        for row in doc.get("targetFixtures", []):
            f = TargetFixture(
                id=str(row["id"]),
                base_family=str(row["baseFamily"]),
                base_archetype=str(row["baseArchetype"]),
                classification=str(row["classification"]),
                role=str(row["role"]),
                remove_shield=bool(row.get("removeShield", False)),
                remove_pds=bool(row.get("removePds", False)),
                remove_hardener=bool(row.get("removeHardener", False)),
                armor_protection_delta=int(row.get("armorProtectionDelta", 0)),
                armor_integrity_delta=int(row.get("armorIntegrityDelta", 0)),
                armor_protection_override=(None if row.get("armorProtectionOverride") is None else int(row["armorProtectionOverride"])),
                armor_integrity_override=(None if row.get("armorIntegrityOverride") is None else int(row["armorIntegrityOverride"])),
                shield_capacity_delta=int(row.get("shieldCapacityDelta", 0)),
                shield_recharge_bonus=int(row.get("shieldRechargeBonus", 0)),
                hull_delta=int(row.get("hullDelta", 0)),
            )
            self.fixtures[f.id] = f

    def get(self, family: str, profile_id: str) -> FamilyProfile:
        table = self.missile if family == "Missile" else self.kinetic
        return table[profile_id]


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-weapon-family-payload-space-v0.2":
        errors.append("schemaVersion")
    if doc.get("checkpoint") != 115:
        errors.append("checkpoint")
    if doc.get("acceptedBaseline") != 114:
        errors.append("acceptedBaseline")
    if doc.get("damageModel") != DAMAGE_MODEL:
        errors.append("damageModel")
    if doc.get("automaticPromotion") is not False:
        errors.append("automaticPromotion")
    if int(doc.get("trialsPerVariant", 0)) < 1:
        errors.append("trialsPerVariant")
    if int(doc.get("authoringTrialsPerVariant", 0)) < 1:
        errors.append("authoringTrialsPerVariant")

    fixtures = doc.get("targetFixtures", [])
    fixture_ids = [x.get("id") for x in fixtures]
    if len(fixture_ids) != len(set(fixture_ids)):
        errors.append("duplicateTargetFixture")
    if not {"shield-heavy-legal", "shield-overmatch-fixture", "armor-exposed-legal", "armor-heavy-fixture", "light-fixture", "pds-heavy-legal"} <= set(fixture_ids):
        errors.append("requiredTargetFixtures")
    for row in fixtures:
        if row.get("classification") not in ("legal_build", "controlled_fixture"):
            errors.append(f"targetFixtureClassification:{row.get('id')}")

    for key, family in (("missileProfiles", "Missile"), ("kineticProfiles", "Kinetic")):
        ids = [x.get("id") for x in doc.get(key, [])]
        if len(ids) != len(set(ids)):
            errors.append(f"duplicate:{key}")
        for row in doc.get(key, []):
            if row.get("family") != family:
                errors.append(f"family:{row.get('id')}")
            if not row.get("studyTls"):
                errors.append(f"studyTls:{row.get('id')}")
            if int(row.get("packets", 1)) < 1 or int(row.get("packets", 1)) > 3:
                errors.append(f"packets:{row.get('id')}")
            ordered = row.get("orderedPackets", [])
            if ordered and row.get("packets") not in (None, 1):
                errors.append(f"orderedPacketsWithPackets:{row.get('id')}")
            if len(ordered) > 3:
                errors.append(f"orderedPackets:{row.get('id')}")
    mid = {x["id"] for x in doc.get("missileProfiles", [])}
    kid = {x["id"] for x in doc.get("kineticProfiles", [])}
    for pid in ("gp-current", "missile-fission-gp-c", "missile-fusion-gp-c", "missile-antimatter-gp-c", "missile-shaped", "missile-shield-pressure", "missile-shield-recharge"):
        if pid not in mid:
            errors.append(f"requiredMissile:{pid}")
    for pid in ("gp-current", "kinetic-smart-plus10", "kinetic-dense-b", "kinetic-saturation-a", "kinetic-tandem-a", "kinetic-tandem-b-reverse"):
        if pid not in kid:
            errors.append(f"requiredKinetic:{pid}")
    for tl, ids in doc.get("contemporaryGpByTl", {}).items():
        for pid in ids:
            if pid not in mid:
                errors.append(f"contemporaryGp:{tl}:{pid}")
    for pid in doc.get("specialistPairingIds", []):
        if pid not in mid:
            errors.append(f"specialistPairing:{pid}")
    for pid in doc.get("adaptivePairingIds", []):
        if pid not in mid:
            errors.append(f"adaptivePairing:{pid}")
    return errors


def _clone_build(
    matrix: CandidateMatrix,
    base: EcologyBuild,
    suffix: str,
    *,
    shield: bool | None = None,
    pds_family: str | None | object = "KEEP",
    hardener: bool | None = None,
) -> EcologyBuild:
    shield_v = base.shield if shield is None else shield
    pds_v = base.pds_family if pds_family == "KEEP" else pds_family
    hard_v = base.shield_hardener if hardener is None else hardener
    if not shield_v:
        hard_v = False
    combat = build_space(
        matrix,
        base.tl,
        base.weapon_family,
        base.main_count,
        base.reactor_count,
        shield_v,
        base.ecm,
        base.eccm,
        pds_v,
        hard_v,
    )
    cap = matrix.capacity(base.tl)
    if combat > cap:
        raise ValueError(f"build overflow {base.id} {suffix} {combat}>{cap}")
    return EcologyBuild(
        f"{base.id}-{suffix}",
        base.tl,
        f"{base.archetype}-{suffix}",
        base.weapon_family,
        base.main_count,
        base.reactor_count,
        shield_v,
        base.ecm,
        base.eccm,
        pds_v,
        hard_v,
        cap,
        combat,
        cap - combat,
    )


def _fixture_build(matrix: CandidateMatrix, by_id: dict[str, EcologyBuild], tl: int, fixture: TargetFixture) -> EcologyBuild:
    fid = fixture.base_family.lower()
    base = by_id[f"tl{tl}-{fid}-{fixture.base_archetype}"]
    if not (fixture.remove_shield or fixture.remove_pds or fixture.remove_hardener):
        return base
    suffix = fixture.id
    return _clone_build(
        matrix,
        base,
        suffix,
        shield=(False if fixture.remove_shield else None),
        pds_family=(None if fixture.remove_pds else "KEEP"),
        hardener=(False if fixture.remove_hardener else None),
    )


def _apply_fixture_state(side: SideState, fixture: TargetFixture) -> None:
    if fixture.hull_delta:
        side.hull = max(1, side.hull + fixture.hull_delta)
    if fixture.shield_capacity_delta and side.build.shield:
        side.shield_max = max(0, side.shield_max + fixture.shield_capacity_delta)
        side.shield = max(0, side.shield + fixture.shield_capacity_delta)
    if fixture.armor_protection_override is not None:
        side.armor_protection = max(0, fixture.armor_protection_override)
    else:
        side.armor_protection = max(0, side.armor_protection + fixture.armor_protection_delta)
    if fixture.armor_integrity_override is not None:
        side.armor_integrity = max(0, fixture.armor_integrity_override)
    else:
        side.armor_integrity = max(0, side.armor_integrity + fixture.armor_integrity_delta)


def _fixture_bonus_recharge(side: SideState, fixture: TargetFixture) -> None:
    if fixture.shield_recharge_bonus <= 0 or side.shield >= side.shield_max:
        return
    restored = min(side.shield_max - side.shield, fixture.shield_recharge_bonus)
    if restored > 0:
        side.shield += restored
        side.telemetry.shield_base_restored += restored


def _profile_ids_for_tl(table: dict[str, FamilyProfile], tl: int) -> list[str]:
    return sorted(p.id for p in table.values() if tl in p.study_tls)


def _pair_id(gp_id: str, specialist_id: str, adaptive: bool = False) -> str:
    return f"{'adaptive-pair' if adaptive else 'pair'}::{gp_id}::{specialist_id}"


def _parse_pair(profile_id: str) -> tuple[str, str, bool] | None:
    parts = profile_id.split("::")
    if len(parts) == 3 and parts[0] in ("pair", "adaptive-pair"):
        return parts[1], parts[2], parts[0] == "adaptive-pair"
    return None


def build_variants(repo: Path, doc: dict[str, Any]) -> tuple[list[EcologyBuild], list[FamilyVariant]]:
    matrix = CandidateMatrix(repo)
    primary = generate_primary_builds(matrix)
    by = {b.id: b for b in primary}
    catalog = FamilyCatalog(doc)
    all_builds = {b.id: b for b in primary}
    variants: list[FamilyVariant] = []
    orders = (("SideAFirst", "afirst"), ("SideBFirst", "bfirst"))

    def targets_for_tl(tl: int) -> list[tuple[TargetFixture, EcologyBuild]]:
        out = []
        for fixture in catalog.fixtures.values():
            b = _fixture_build(matrix, by, tl, fixture)
            all_builds[b.id] = b
            out.append((fixture, b))
        return sorted(out, key=lambda x: x[0].id)

    # Missile progression and specialist pairing. Pair/adaptive-pair modes require dual launchers.
    for tl in doc["missileStudyTls"]:
        targets = targets_for_tl(int(tl))
        attackers = [by[f"tl{tl}-missile-balanced"], by[f"tl{tl}-missile-dual-main"]]
        fixed = _profile_ids_for_tl(catalog.missile, int(tl))
        contemporary = list(doc["contemporaryGpByTl"][str(tl)])
        specialist_ids = list(doc.get("specialistPairingIdsByTl", {}).get(str(tl), doc.get("specialistPairingIds", [])))
        adaptive_ids = list(doc.get("adaptivePairingIdsByTl", {}).get(str(tl), doc.get("adaptivePairingIds", [])))
        paired = [_pair_id(gp, sp, False) for gp in contemporary for sp in specialist_ids]
        adaptive = [_pair_id(gp, sp, True) for gp in contemporary for sp in adaptive_ids]
        for atk in attackers:
            profile_ids = list(fixed)
            if atk.main_count >= 2:
                profile_ids += paired + adaptive
            for fixture, target in targets:
                for profile_id in sorted(profile_ids):
                    for order, suffix in orders:
                        vid = f"family-missile-tl{tl}-{atk.archetype}-{profile_id.replace('::','-')}-vs-{fixture.id}-{suffix}"
                        variants.append(FamilyVariant(vid, int(tl), atk, target, order, profile_id, "missile_family_characteristic", fixture.id, fixture.classification))

    # Kinetic modes. One battery remains one hit roll; saturation/tandem only alter accuracy/packet resolution.
    for tl in doc["kineticStudyTls"]:
        targets = targets_for_tl(int(tl))
        attackers = [by[f"tl{tl}-kinetic-balanced"], by[f"tl{tl}-kinetic-dual-main"]]
        profile_ids = _profile_ids_for_tl(catalog.kinetic, int(tl))
        for atk in attackers:
            for fixture, target in targets:
                for profile_id in profile_ids:
                    for order, suffix in orders:
                        vid = f"family-kinetic-tl{tl}-{atk.archetype}-{profile_id}-vs-{fixture.id}-{suffix}"
                        variants.append(FamilyVariant(vid, int(tl), atk, target, order, profile_id, "kinetic_family_characteristic", fixture.id, fixture.classification))

    # Energy references retain native low/standard/high power doctrine and serve only as family-identity controls.
    for tl in doc["energyReferenceTls"]:
        targets = targets_for_tl(int(tl))
        attackers = [by[f"tl{tl}-energy-balanced"], by[f"tl{tl}-energy-dual-main"]]
        for atk in attackers:
            for fixture, target in targets:
                for order, suffix in orders:
                    vid = f"family-energy-tl{tl}-{atk.archetype}-native-vs-{fixture.id}-{suffix}"
                    variants.append(FamilyVariant(vid, int(tl), atk, target, order, "energy-native", "energy_family_reference", fixture.id, fixture.classification))

    variants.sort(key=lambda v: v.id)
    return sorted(all_builds.values(), key=lambda b: b.id), variants


def _effective_profile(base: dict[str, Any], p: FamilyProfile) -> dict[str, Any]:
    if p.id == "gp-current":
        return {
            "id": p.id,
            "damage": int(base["damage"]),
            "spen": int(base["spen"]),
            "apen": int(base["apen"]),
            "accuracy": int(base.get("accuracy", 0)),
            "packets": 1,
            "ordered_packets": (),
            "shield_bonus_damage": 0,
            "shield_armor_reduction": 0,
            "recharge_suppression": 0,
            "guidance_delta": 0,
            "pds_intercept_penalty_pp": 0,
        }
    bd = int(base["damage"])
    return {
        "id": p.id,
        "damage": max(0, int(p.damage if p.damage is not None else bd + p.damage_delta)),
        "spen": max(0, int(p.spen if p.spen is not None else int(base["spen"]) + p.spen_delta)),
        "apen": max(0, int(p.apen if p.apen is not None else int(base["apen"]) + p.apen_delta)),
        "accuracy": int(base.get("accuracy", 0)) + p.accuracy_delta,
        "packets": p.packets,
        "ordered_packets": p.ordered_packets,
        "shield_bonus_damage": p.shield_bonus_damage,
        "shield_armor_reduction": p.shield_armor_reduction,
        "recharge_suppression": p.recharge_suppression,
        "guidance_delta": p.guidance_delta,
        "pds_intercept_penalty_pp": p.pds_intercept_penalty_pp,
    }


def _missile_profile_for_launch(side: SideState, catalog: FamilyCatalog, doctrine_id: str, weapon_index: int) -> FamilyProfile:
    pair = _parse_pair(doctrine_id)
    if pair is None:
        return catalog.missile[doctrine_id]
    gp_id, specialist_id, adaptive = pair
    gp = catalog.missile[gp_id]
    specialist = catalog.missile[specialist_id]
    active = True
    if adaptive:
        active = bool(
            side.observed_shield_absorption
            and side.observed_no_penetration_streak >= 2
            and not side.observed_no_shield_effect_latest
            and not side.observed_hull_penetration
        )
        state = f"{doctrine_id}:{'active' if active else 'gp'}"
        if side.last_payload_id and side.last_payload_id != state:
            side.telemetry.payload_switches += 1
        side.last_payload_id = state
    if weapon_index % 2 == 0 and active:
        return specialist
    return gp


def _observe_resolution(observer: SideState, result: dict[str, int], firm: bool) -> None:
    if not firm:
        return
    shield_effect = (result.get("shield_armor_prevented", 0) + result.get("shield_absorbed", 0) + result.get("shield_bonus_damage", 0)) > 0
    armor_contact = (result.get("armor_prevented", 0) + result.get("armor_integrity", 0) + result.get("armor_protection", 0)) > 0
    hull = result.get("hull", 0) > 0
    if shield_effect:
        if not observer.observed_shield_absorption:
            observer.telemetry.assessment_shield_absorption_observed += 1
        observer.observed_shield_absorption = True
        observer.observed_no_shield_effect_latest = False
    elif armor_contact or hull:
        if not observer.observed_no_shield_effect_latest:
            observer.telemetry.assessment_shield_absent_observed += 1
        observer.observed_no_shield_effect_latest = True
    if armor_contact:
        if not observer.observed_armor_contact:
            observer.telemetry.assessment_armor_contact_observed += 1
        observer.observed_armor_contact = True
    if hull:
        if not observer.observed_hull_penetration:
            observer.telemetry.assessment_hull_penetration_observed += 1
        observer.observed_hull_penetration = True
    armor_damage = (result.get("armor_integrity", 0) + result.get("armor_protection", 0)) > 0
    if shield_effect and not armor_damage and not hull:
        observer.observed_no_penetration_streak += 1
        observer.telemetry.assessment_no_penetration_observed += 1
    elif armor_damage or hull or observer.observed_no_shield_effect_latest:
        observer.observed_no_penetration_streak = 0


def _apply_profile_hit(target: SideState, prof: dict[str, Any], shield_armor: int, source: str) -> dict[str, int]:
    total = {
        "shield_armor_prevented": 0,
        "shield_absorbed": 0,
        "armor_prevented": 0,
        "armor_integrity": 0,
        "armor_protection": 0,
        "hull": 0,
        "shield_bonus_damage": 0,
    }
    bonus = min(target.shield, int(prof.get("shield_bonus_damage", 0)))
    if bonus:
        target.shield -= bonus
        target.telemetry.shield_absorbed += bonus
        target.telemetry.payload_shield_bonus_damage += bonus
        total["shield_absorbed"] += bonus
        total["shield_bonus_damage"] += bonus
    effective_shield_armor = max(0, shield_armor - int(prof.get("shield_armor_reduction", 0)))
    ordered = tuple(prof.get("ordered_packets", ()))
    if ordered:
        packet_rows = ordered
    else:
        packet_rows = tuple((int(prof["damage"]), int(prof["spen"]), int(prof["apen"])) for _ in range(max(1, int(prof.get("packets", 1)))))
    for damage, spen, apen in packet_rows:
        r = _apply_damage(target, int(damage), int(spen), int(apen), effective_shield_armor, source)
        for k in ("shield_armor_prevented", "shield_absorbed", "armor_prevented", "armor_integrity", "armor_protection", "hull"):
            total[k] += int(r[k])
    if int(prof.get("recharge_suppression", 0)) > 0 and (total["shield_armor_prevented"] + total["shield_absorbed"] + total["shield_bonus_damage"]) > 0:
        target.recharge_suppression_pending = max(target.recharge_suppression_pending, int(prof["recharge_suppression"]))
    return total


def run_family_trial(matrix: CandidateMatrix, catalog: FamilyCatalog, variant: FamilyVariant, master_seed: int, trial_index: int) -> FamilyTrialResult:
    try:
        a = _create_side(matrix, variant.side_a, variant.start_q_a)
        b = _create_side(matrix, variant.side_b, variant.start_q_b)
        fixture = catalog.fixtures[variant.target_fixture]
        _apply_fixture_state(b, fixture)
        rng = XorShift64(derive_seed(master_seed, variant.id, trial_index))
        missiles: list[FamilyMissileState] = []
        for turn in range(1, variant.max_turns + 1):
            inbound_a = sum(m.owner == "B" for m in missiles)
            inbound_b = sum(m.owner == "A" for m in missiles)
            power_a, _ = _begin_turn_recharge(matrix, a, b, inbound_a)
            power_b, _ = _begin_turn_recharge(matrix, b, a, inbound_b)
            _fixture_bonus_recharge(b, fixture)
            if variant.movement_order == "SideAFirst":
                _move_one(a, b, matrix, a.contact)
                _move_one(b, a, matrix, b.contact)
            else:
                _move_one(b, a, matrix, b.contact)
                _move_one(a, b, matrix, a.contact)
            rhex = _range(a, b)
            pre_a = _plan_once(matrix, a, b, rhex, inbound_a, power_a, False)
            pre_b = _plan_once(matrix, b, a, rhex, inbound_b, power_b, False)
            ecm_a = pre_a["ecm_on"]
            ecm_b = pre_b["ecm_on"]
            pa, _ = _maybe_reactor_overload(matrix, a, b, rhex, inbound_a, power_a, ecm_b)
            pb, _ = _maybe_reactor_overload(matrix, b, a, rhex, inbound_b, power_b, ecm_a)
            _record_plan(a, pa, power_a, inbound_a)
            _record_plan(b, pb, power_b, inbound_b)
            a.last_track = pa["track"]
            b.last_track = pb["track"]
            a.contact |= pa["track"] != "None"
            b.contact |= pb["track"] != "None"

            direct: list[tuple[SideState, SideState, dict[str, Any], bool, dict[str, Any]]] = []
            for label, side, target, plan, doctrine in (
                ("A", a, b, pa, variant.side_a_profile),
                ("B", b, a, pb, "defender-native"),
            ):
                w = _weapon(matrix, side.build)
                if w["family"] == "Missile":
                    if plan["track"] == "Firm" and rhex <= int(w["range"]):
                        for weapon_index, wp in enumerate(plan["weapon_plans"]):
                            if wp is None:
                                continue
                            if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                                continue
                            if side.weapon_ammo is not None:
                                side.weapon_ammo -= 1
                            if label == "A" and variant.scenario_group == "missile_family_characteristic":
                                pp = _missile_profile_for_launch(side, catalog, doctrine, weapon_index)
                            else:
                                pp = catalog.missile["gp-current"]
                            eff = _effective_profile(w, pp)
                            if pp.is_gp:
                                side.telemetry.payload_gp_launches += 1
                            else:
                                side.telemetry.payload_specialist_launches += 1
                            eta = max(1, math.ceil(rhex / max(1, int(w["missile_move"]))))
                            missiles.append(
                                FamilyMissileState(
                                    label,
                                    eta,
                                    max(1, min(99, int(w["guidance"]) + int(eff.get("guidance_delta", 0)))),
                                    pp.id,
                                    int(eff["damage"]),
                                    int(eff["spen"]),
                                    int(eff["apen"]),
                                    int(eff["packets"]),
                                    int(eff["shield_bonus_damage"]),
                                    int(eff["shield_armor_reduction"]),
                                    int(eff["recharge_suppression"]),
                                    int(eff.get("pds_intercept_penalty_pp", 0)),
                                )
                            )
                            side.telemetry.missile_launches += 1
                            side.demonstrated_range = max(side.demonstrated_range, rhex)
                    continue

                if plan["track"] != "Firm" or rhex > int(w["range"]):
                    continue
                for wp in plan["weapon_plans"]:
                    if wp is None:
                        continue
                    if side.weapon_ammo is not None and side.weapon_ammo <= 0:
                        continue
                    if side.weapon_ammo is not None:
                        side.weapon_ammo -= 1
                    if w["family"] == "Energy":
                        _, wp_damage, wp_accuracy = wp
                        eff = {
                            "id": "energy-native",
                            "damage": int(wp_damage),
                            "spen": int(w["spen"]),
                            "apen": int(w["apen"]),
                            "accuracy": int(wp_accuracy),
                            "packets": 1,
                            "ordered_packets": (),
                            "shield_bonus_damage": 0,
                            "shield_armor_reduction": 0,
                            "recharge_suppression": 0,
                        }
                        pp_id = "energy-native"
                    else:
                        if label == "A" and variant.scenario_group == "kinetic_family_characteristic":
                            pp = catalog.kinetic[doctrine]
                        else:
                            pp = catalog.kinetic["gp-current"]
                        eff = _effective_profile(w, pp)
                        pp_id = pp.id
                    chance = _hit_chance(matrix, side.build, rhex, int(eff["accuracy"]))
                    hit = rng.d100() <= chance
                    side.telemetry.direct_shots += 1
                    if w["family"] == "Kinetic" and pp_id != "gp-current":
                        side.telemetry.kinetic_specialist_shots += 1
                    if hit:
                        side.telemetry.direct_hits += 1
                    direct.append((side, target, plan, hit, eff))
                    side.demonstrated_range = max(side.demonstrated_range, rhex)

            for shooter, target, plan, hit, eff in direct:
                if hit:
                    active_plan = pb if shooter is a else pa
                    res = _apply_profile_hit(target, eff, _shield_armor(matrix, target, bool(active_plan["hardener_active"])), "direct")
                    _observe_resolution(shooter, res, shooter.last_track == "Firm")
                    target.contact = True

            for m in missiles:
                m.eta -= 1
            terminal = [m for m in missiles if m.eta <= 0]
            if terminal:
                for target_label, target, plan, shooter in (("A", a, pa, b), ("B", b, pb, a)):
                    threats = [m for m in terminal if m.owner != target_label]
                    reaction_used = 0
                    intercepted: set[int] = set()
                    pds = plan["pds"]
                    for m in threats:
                        target.telemetry.missile_terminal_arrivals += 1
                        attempts = 0
                        while reaction_used < int(plan["pds_rc"]) and attempts < 2:
                            if target.pds_ammo is not None and target.pds_ammo <= 0:
                                break
                            target.telemetry.pds_attempts += 1
                            reaction_used += 1
                            attempts += 1
                            if target.pds_ammo is not None:
                                target.pds_ammo -= 1
                            chance = 0 if pds is None else min(95, int(pds["baseChancePp"]) + int(matrix.p("computer", target.build.tl)["targetingPp"]))
                            chance = max(0, chance - int(m.pds_intercept_penalty_pp))
                            if rng.d100() <= chance:
                                target.telemetry.pds_intercepts += 1
                                intercepted.add(id(m))
                                break
                        if id(m) in intercepted:
                            continue
                        target.telemetry.missile_guidance_attempts += 1
                        if rng.d100() <= int(m.guidance):
                            target.telemetry.missile_hits += 1
                            eff = {
                                "damage": m.damage,
                                "spen": m.spen,
                                "apen": m.apen,
                                "packets": m.packets,
                                "ordered_packets": (),
                                "shield_bonus_damage": m.shield_bonus_damage,
                                "shield_armor_reduction": m.shield_armor_reduction,
                                "recharge_suppression": m.recharge_suppression,
                            }
                            res = _apply_profile_hit(target, eff, _shield_armor(matrix, target, bool(plan["hardener_active"])), "missile")
                            _observe_resolution(shooter, res, shooter.last_track == "Firm")
                            target.contact = True
                missiles = [m for m in missiles if m.eta > 0]

            if a.hull <= 0 or b.hull <= 0:
                winner = "Draw" if a.hull <= 0 and b.hull <= 0 else ("B" if a.hull <= 0 else "A")
                return FamilyTrialResult(winner, False, turn, a.hull, b.hull, a.armor_integrity, b.armor_integrity, a.shield, b.shield, a.telemetry, b.telemetry)
        return FamilyTrialResult("Unresolved", True, variant.max_turns, a.hull, b.hull, a.armor_integrity, b.armor_integrity, a.shield, b.shield, a.telemetry, b.telemetry)
    except Exception as exc:
        blank = SideTelemetry()
        return FamilyTrialResult("Error", False, 0, 0, 0, 0, 0, 0, 0, blank, blank, f"{type(exc).__name__}: {exc}")


_WORKER_MATRIX: CandidateMatrix | None = None
_WORKER_CATALOG: FamilyCatalog | None = None


def _init_worker(repo: str, doc: dict[str, Any]):
    global _WORKER_MATRIX, _WORKER_CATALOG
    _WORKER_MATRIX = CandidateMatrix(Path(repo))
    _WORKER_CATALOG = FamilyCatalog(doc)


def _mean(results: list[FamilyTrialResult], side: str, name: str) -> float:
    vals = [getattr(r.side_a if side == "a" else r.side_b, name) for r in results if not r.error]
    return statistics.fmean(vals) if vals else 0.0


def _aggregate(v: FamilyVariant, results: list[FamilyTrialResult]) -> dict[str, Any]:
    n = len(results)
    wins = {k: sum(r.winner == k for r in results) for k in ("A", "B", "Draw", "Unresolved", "Error")}
    valid = [r for r in results if not r.error]
    row: dict[str, Any] = {
        "variant_id": v.id,
        "tl": v.tl,
        "scenario_group": v.scenario_group,
        "target_fixture": v.target_fixture,
        "target_classification": v.target_classification,
        "movement_order": v.movement_order,
        "side_a_build": v.side_a.id,
        "side_b_build": v.side_b.id,
        "side_a_family": v.side_a.weapon_family,
        "side_b_family": v.side_b.weapon_family,
        "side_a_archetype": v.side_a.archetype,
        "side_b_archetype": v.side_b.archetype,
        "side_a_profile": v.side_a_profile,
        "trials": n,
        "wins_a": wins["A"],
        "wins_b": wins["B"],
        "draws": wins["Draw"],
        "unresolved": wins["Unresolved"],
        "errors": wins["Error"],
        "conditional_win_rate_a": wins["A"] / max(1, wins["A"] + wins["B"]),
        "unresolved_rate": wins["Unresolved"] / n if n else 0.0,
        "mean_turns": statistics.fmean(r.turns for r in valid) if valid else 0.0,
        "mean_final_hull_a": statistics.fmean(r.hull_a for r in valid) if valid else 0.0,
        "mean_final_hull_b": statistics.fmean(r.hull_b for r in valid) if valid else 0.0,
        "mean_final_armor_b": statistics.fmean(r.armor_b for r in valid) if valid else 0.0,
        "mean_final_shield_b": statistics.fmean(r.shield_b for r in valid) if valid else 0.0,
    }
    for side in ("a", "b"):
        for f in fields(SideTelemetry):
            row[f"mean_{side}_{f.name}"] = _mean(results, side, f.name)
    return row


def _task(args):
    v, seed, trials = args
    assert _WORKER_MATRIX is not None and _WORKER_CATALOG is not None
    return _aggregate(v, [run_family_trial(_WORKER_MATRIX, _WORKER_CATALOG, v, seed, i) for i in range(trials)])


def _chunk(args):
    vs, seed, trials = args
    return [_task((v, seed, trials)) for v in vs]


def execute(repo: Path, doc: dict[str, Any], variants: list[FamilyVariant], trials: int, jobs: int) -> tuple[list[dict[str, Any]], float]:
    jobs = max(1, min(jobs, len(variants)))
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if jobs == 1:
        _init_worker(str(repo), doc)
        rows = [_task((v, int(doc["masterSeed"]), trials)) for v in variants]
    else:
        chunks = [[] for _ in range(min(len(variants), max(jobs, jobs * 4)))]
        for i, v in enumerate(variants):
            chunks[i % len(chunks)].append(v)
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_init_worker, initargs=(str(repo), doc)) as ex:
            futures = [ex.submit(_chunk, (c, int(doc["masterSeed"]), trials)) for c in chunks if c]
            for f in as_completed(futures):
                rows.extend(f.result())
    rows.sort(key=lambda r: r["variant_id"])
    return rows, time.perf_counter() - start


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


def _summary(rows: list[dict[str, Any]], group: str) -> list[dict[str, Any]]:
    d: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["scenario_group"] == group:
            d[(int(r["tl"]), r["side_a_profile"], r["target_fixture"], r["target_classification"], r["side_a_archetype"])].append(r)
    out: list[dict[str, Any]] = []
    for (tl, profile, target, classification, attacker), rs in sorted(d.items()):
        out.append(
            {
                "tl": tl,
                "profile": profile,
                "target_fixture": target,
                "target_classification": classification,
                "attacker_archetype": attacker,
                "variants": len(rs),
                "mean_conditional_win_rate": statistics.fmean(float(x["conditional_win_rate_a"]) for x in rs),
                "mean_unresolved_rate": statistics.fmean(float(x["unresolved_rate"]) for x in rs),
                "mean_direct_hits": statistics.fmean(float(x["mean_a_direct_hits"]) for x in rs),
                "mean_missile_hits": statistics.fmean(float(x["mean_b_missile_hits"] if group == "missile_family_characteristic" else x["mean_a_missile_hits"]) for x in rs),
                "mean_target_shield_absorbed": statistics.fmean(float(x["mean_b_shield_absorbed"]) for x in rs),
                "mean_target_recharge_suppressed": statistics.fmean(float(x["mean_b_shield_recharge_suppressed"]) for x in rs),
                "mean_target_armor_damage": statistics.fmean(float(x["mean_b_armor_integrity_damage"]) for x in rs),
                "mean_target_hull_damage": statistics.fmean(float(x["mean_b_hull_damage"]) for x in rs),
                "mean_payload_gp_launches": statistics.fmean(float(x["mean_a_payload_gp_launches"]) for x in rs),
                "mean_payload_specialist_launches": statistics.fmean(float(x["mean_a_payload_specialist_launches"]) for x in rs),
                "mean_payload_switches": statistics.fmean(float(x["mean_a_payload_switches"]) for x in rs),
            }
        )
    return out


def _target_fixture_rows(matrix: CandidateMatrix, catalog: FamilyCatalog, doc: dict[str, Any], repo: Path) -> list[dict[str, Any]]:
    primary = generate_primary_builds(matrix)
    by = {b.id: b for b in primary}
    tls = sorted(set(int(x) for x in doc["missileStudyTls"] + doc["kineticStudyTls"] + doc["energyReferenceTls"]))
    rows = []
    for tl in tls:
        for fixture in sorted(catalog.fixtures.values(), key=lambda x: x.id):
            b = _fixture_build(matrix, by, tl, fixture)
            side = _create_side(matrix, b, MAP_RADIUS)
            _apply_fixture_state(side, fixture)
            shield = matrix.p("shield", tl)
            rows.append(
                {
                    "tl": tl,
                    "target_fixture": fixture.id,
                    "classification": fixture.classification,
                    "underlying_build": b.id,
                    "used_space": b.used_space,
                    "capacity": b.capacity,
                    "initial_shield": side.shield,
                    "shield_base_recharge": (int(shield["baseRecharge"]) + fixture.shield_recharge_bonus) if b.shield else 0,
                    "armor_protection": side.armor_protection,
                    "armor_integrity": side.armor_integrity,
                    "hull": side.hull,
                    "pds_family": b.pds_family or "-",
                    "hardener": b.shield_hardener,
                    "role": fixture.role,
                }
            )
    return rows


def run_weapon_family_analysis(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 1) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("invalid CP115 study: " + ",".join(errs))
    builds, variants = build_variants(repo, doc)
    trials = int(trials_override or doc["trialsPerVariant"])
    rows, elapsed = execute(repo, doc, variants, trials, jobs)
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "variants.csv", rows)
    _write_csv(
        outdir / "builds.csv",
        [
            {
                "build_id": b.id,
                "tl": b.tl,
                "family": b.weapon_family,
                "archetype": b.archetype,
                "combat_space": b.combat_space,
                "mission_aux_space": b.mission_aux_space,
                "capacity": b.capacity,
                "used_space": b.used_space,
                "free_space": b.capacity - b.used_space,
            }
            for b in builds
        ],
    )
    catalog = FamilyCatalog(doc)
    target_rows = _target_fixture_rows(CandidateMatrix(repo), catalog, doc, repo)
    _write_csv(outdir / "target_fixtures.csv", target_rows)
    missile = _summary(rows, "missile_family_characteristic")
    kinetic = _summary(rows, "kinetic_family_characteristic")
    energy = _summary(rows, "energy_family_reference")
    _write_csv(outdir / "missile_family_summary.csv", missile)
    _write_csv(outdir / "kinetic_family_summary.csv", kinetic)
    _write_csv(outdir / "energy_reference_summary.csv", energy)

    failures: list[str] = []
    if any(int(r["errors"]) for r in rows):
        failures.append("trial-errors")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("exact-fill-underlying-builds")
    if not any(r["target_classification"] == "controlled_fixture" for r in rows):
        failures.append("controlled-fixture-coverage")
    if not any(str(r["side_a_profile"]).startswith("pair::") and float(r["mean_a_payload_gp_launches"]) > 0 and float(r["mean_a_payload_specialist_launches"]) > 0 for r in rows):
        failures.append("mixed-contemporary-gp-telemetry")
    if not any("kinetic-saturation" in str(r["side_a_profile"]) and float(r["mean_a_kinetic_specialist_shots"]) > 0 for r in rows):
        failures.append("kinetic-saturation-telemetry")
    if not any("kinetic-tandem" in str(r["side_a_profile"]) and float(r["mean_a_kinetic_specialist_shots"]) > 0 for r in rows):
        failures.append("kinetic-tandem-telemetry")
    if not any(r["scenario_group"] == "energy_family_reference" and float(r["mean_a_direct_shots"]) > 0 for r in rows):
        failures.append("energy-reference-telemetry")

    by_group = defaultdict(int)
    for v in variants:
        by_group[v.scenario_group] += 1
    analysis = {
        "schemaVersion": "star-cluster-weapon-family-payload-space-results-v0.2",
        "checkpoint": 115,
        "damageModel": DAMAGE_MODEL,
        "internalDamageCriticalsSimulated": False,
        "trialsPerVariant": trials,
        "variants": len(variants),
        "variantCounts": dict(sorted(by_group.items())),
        "totalTrials": len(variants) * trials,
        "elapsedSeconds": elapsed,
        "failedGates": failures,
        "automaticPromotion": False,
        "targetFixtureCount": len(catalog.fixtures),
        "controlledFixtureCount": sum(f.classification == "controlled_fixture" for f in catalog.fixtures.values()),
        "adaptivePairRows": sum(str(r["side_a_profile"]).startswith("adaptive-pair::") for r in rows),
        "adaptivePairRowsWithSwitches": sum(str(r["side_a_profile"]).startswith("adaptive-pair::") and float(r["mean_a_payload_switches"]) > 0 for r in rows),
        "adaptivePairSwitchTelemetryObserved": any(str(r["side_a_profile"]).startswith("adaptive-pair::") and float(r["mean_a_payload_switches"]) > 0 for r in rows),
        "missileFamilySummary": missile,
        "kineticFamilySummary": kinetic,
        "energyReferenceSummary": energy,
        "interpretation": "Exploratory weapon-family characteristic-space evidence only. Asymmetric family strengths are intentional; controlled fixtures expose niches and are not legal-build balance gates. No CP109/CP110/Concept/Storyboard or C#/Godot production value is promoted by CP115.",
    }
    (outdir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis
