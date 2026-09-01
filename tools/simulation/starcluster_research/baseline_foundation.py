from __future__ import annotations

import csv
import json
import statistics
import time
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Iterable

from .canonical_mechanics import resolve_layered_damage
from .ecology import (
    CandidateMatrix,
    EcologyBuild,
    EcologyVariant,
    SideTelemetry,
    _aggregate_variant,
    _apply_damage,
    _create_side,
    _weapon,
    run_trial,
)
from .study import canonicalize_relocated_references, load_json

SCHEMA = "star-cluster-cp123-executable-baseline-foundation-v0.1"
RESULT_SCHEMA = "star-cluster-cp124-executable-baseline-foundation-results-v0.1"
DEFAULT_MATRIX = "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json"
MASTER_SEED = 12420260816


@dataclass(frozen=True, slots=True)
class BaselineBuild:
    id: str
    tl: int
    weapon_family: str
    missile_payload: str
    main_count: int
    reactor_count: int
    shield: bool
    ecm_count: int
    eccm_count: int
    pds_family: str
    shield_hardener: bool
    capacity: int
    combat_space: int
    mission_aux_space: int
    space_class: str
    operational_power: int
    nominal_power_demand: int
    max_discretionary_power_demand: int
    nominal_power_margin: int
    effective_ecm_rating: int
    effective_eccm_rating: int

    @property
    def used_space(self) -> int:
        return self.combat_space + self.mission_aux_space


TELEMETRY_CONTRACT: tuple[dict[str, Any], ...] = (
    {"metric":"movement_hexes","dimension":"movement","owner":"actor","kind":"raw_counter"},
    {"metric":"movement_fuel","dimension":"fuel","owner":"actor","kind":"raw_counter"},
    {"metric":"map_boundary_blocks","dimension":"movement","owner":"actor","kind":"raw_counter"},
    {"metric":"range_changes","dimension":"geometry","owner":"actor","kind":"raw_counter"},
    {"metric":"track_driven_closure_hexes","dimension":"geometry","owner":"actor","kind":"raw_counter"},
    {"metric":"firm_track_turns","dimension":"information","owner":"observer","kind":"raw_counter"},
    {"metric":"approximate_track_turns","dimension":"information","owner":"observer","kind":"raw_counter"},
    {"metric":"no_track_turns","dimension":"information","owner":"observer","kind":"raw_counter"},
    {"metric":"ecm_active_turns","dimension":"ew","owner":"actor","kind":"raw_counter"},
    {"metric":"eccm_active_turns","dimension":"ew","owner":"actor","kind":"raw_counter"},
    {"metric":"ecm_downgrade_events","dimension":"ew","owner":"observer","kind":"raw_counter"},
    {"metric":"eccm_restore_events","dimension":"ew","owner":"observer","kind":"raw_counter"},
    {"metric":"burnthrough_preservation_events","dimension":"ew","owner":"observer","kind":"raw_counter"},
    {"metric":"power_available_total","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_spent_total","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_sensor","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_ecm","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_eccm","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_pds","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_weapons","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_shield_recharge","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_shield_hardener","dimension":"power","owner":"actor","kind":"raw_quantity"},
    {"metric":"power_shortfall_events","dimension":"power","owner":"actor","kind":"raw_counter"},
    {"metric":"reactor_overload_activations","dimension":"overload","owner":"actor","kind":"raw_counter"},
    {"metric":"direct_fire_eligible_actions","dimension":"attack_eligibility","owner":"attacker","kind":"raw_counter"},
    {"metric":"missile_launch_eligible_actions","dimension":"attack_eligibility","owner":"attacker","kind":"raw_counter"},
    {"metric":"direct_shots","dimension":"weapon","owner":"attacker","kind":"raw_counter"},
    {"metric":"direct_hits","dimension":"weapon","owner":"attacker","kind":"raw_counter"},
    {"metric":"missile_launches","dimension":"missile","owner":"attacker","kind":"raw_counter"},
    {"metric":"missile_terminal_arrivals","dimension":"missile","owner":"target","kind":"raw_counter"},
    {"metric":"missile_guidance_attempts","dimension":"missile","owner":"target","kind":"raw_counter"},
    {"metric":"missile_hits","dimension":"missile","owner":"target","kind":"raw_counter"},
    {"metric":"pds_attempts","dimension":"pds","owner":"defender","kind":"raw_counter"},
    {"metric":"pds_intercepts","dimension":"pds","owner":"defender","kind":"raw_counter"},
    {"metric":"damage_packets_resolved","dimension":"damage","owner":"target","kind":"raw_counter"},
    {"metric":"raw_damage_on_hit","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"shield_penetration_bypassed","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"shield_armor_prevented","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"shield_absorbed","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"armor_penetration_bypassed","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"armor_prevented","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"armor_integrity_damage","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"armor_protection_damage","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"hull_damage","dimension":"damage","owner":"target","kind":"raw_quantity"},
    {"metric":"damage_control_attempts","dimension":"damage_control","owner":"repairing_ship","kind":"raw_counter"},
    {"metric":"damage_control_successes","dimension":"damage_control","owner":"repairing_ship","kind":"raw_counter"},
    {"metric":"damage_control_hull_restored","dimension":"damage_control","owner":"repairing_ship","kind":"raw_quantity"},
)


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


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 124:
        errors.append("checkpoint")
    if int(doc.get("acceptedReferenceBaseline", 0)) != 123:
        errors.append("acceptedReferenceBaseline")
    if int(doc.get("acceptedImplementationBaseline", 0)) != 122:
        errors.append("acceptedImplementationBaseline")
    if doc.get("sourceMatrix") != DEFAULT_MATRIX:
        errors.append("sourceMatrix")
    if doc.get("automaticPromotion") is not False or doc.get("balanceValidated") is not False:
        errors.append("promotionBoundary")
    if int(doc.get("substantiveMonteCarloTrials", -1)) != 0:
        errors.append("substantiveMonteCarloTrials")
    if int(doc.get("pipelineSmokeTrialsPerVariant", 0)) != 1:
        errors.append("pipelineSmokeTrialsPerVariant")
    if int(doc.get("expectedProfileRows", 0)) != 180:
        errors.append("expectedProfileRows")
    if int(doc.get("expectedRawBuildCombinations", 0)) != 14112:
        errors.append("expectedRawBuildCombinations")
    if int(doc.get("expectedLegalBuilds", 0)) != 9427:
        errors.append("expectedLegalBuilds")
    if int(doc.get("expectedPipelineSmokeVariants", 0)) != 70:
        errors.append("expectedPipelineSmokeVariants")
    if int(doc.get("expectedInstrumentationProbes", 0)) != 9:
        errors.append("expectedInstrumentationProbes")
    if int(doc.get("expectedTelemetryContractMetrics", 0)) != 47:
        errors.append("expectedTelemetryContractMetrics")
    if doc.get("mixedTlPopulation", {}).get("executed") is not False:
        errors.append("mixedTlPopulation")
    return errors


class BaselineCatalog:
    def __init__(self, repo: Path, matrix_relative_path: str = DEFAULT_MATRIX):
        self.repo = repo
        self.matrix_relative_path = matrix_relative_path
        self.matrix = CandidateMatrix(repo, matrix_relative_path)
        self.doc = self.matrix.doc
        self.profiles = self.doc["profiles"]
        self.branches = {row["id"]: row for row in self.doc.get("branches", [])}

    def p(self, family: str, tl: int) -> dict[str, Any]:
        return self.profiles[family][str(tl)]

    def profile_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for family in self.doc.get("profileOrder", list(self.profiles)):
            for tl in range(1, 10):
                row = self.p(family, tl)
                stats = {k:v for k,v in row.items() if k not in {"tl","technology","notes","newTech"}}
                rows.append({
                    "family": family,
                    "tl": tl,
                    "technology": row.get("technology", ""),
                    "new_tech": bool(row.get("newTech", False)),
                    "available": bool(row.get("available", True)),
                    "space": row.get("space", ""),
                    "characteristics_json": json.dumps(stats, sort_keys=True, separators=(",", ":")),
                })
        return rows

    def missile_operational_profile(self, tl: int, payload: str) -> dict[str, Any]:
        delivery = self.p("missile_delivery", tl)
        guidance = self.p("missile_guidance", tl)
        if payload == "Swarmer":
            sw = self.p("missile_swarmer", tl)
            if not sw.get("available", False):
                raise ValueError(f"Swarmer unavailable at TL{tl}")
            return {
                "payload": payload, "range": int(delivery["range"]), "missileMove": int(delivery["missileMove"]),
                "launchTp": int(delivery["launchTp"]), "flights": int(delivery["flights"]),
                "guidance": max(1, min(99, int(guidance["guidanceBaseHit"]) + int(sw["terminalGuidanceBonusPp"]))),
                "commandDatalink": bool(guidance["commandDatalink"]), "onboardNav": bool(guidance["onboardNav"]),
                "terminalSeeker": bool(guidance["terminalSeeker"]), "localApproxCanAcquire": bool(guidance["localApproxCanAcquire"]),
                "packets": int(sw["packetCount"]), "damage": int(sw["packetDamage"]), "spen": int(sw["spen"]), "apen": int(sw["apen"]),
                "pdsInterceptPenaltyPp": int(sw["pdsInterceptPenaltyPp"]),
            }
        gp = self.p("missile_gp_warhead", tl)
        return {
            "payload": "GP", "range": int(delivery["range"]), "missileMove": int(delivery["missileMove"]),
            "launchTp": int(delivery["launchTp"]), "flights": int(delivery["flights"]), "guidance": int(guidance["guidanceBaseHit"]),
            "commandDatalink": bool(guidance["commandDatalink"]), "onboardNav": bool(guidance["onboardNav"]),
            "terminalSeeker": bool(guidance["terminalSeeker"]), "localApproxCanAcquire": bool(guidance["localApproxCanAcquire"]),
            "packets": 1, "damage": int(gp["damage"]), "spen": int(gp["spen"]), "apen": int(gp["apen"]),
            "pdsInterceptPenaltyPp": 0,
        }


def _hardener_available(catalog: BaselineCatalog, tl: int) -> bool:
    branch = catalog.branches.get("shield-hardener")
    return bool(branch and tl >= int(branch["tl"]))


def _weapon_space_key(family: str) -> str:
    return {"Kinetic":"kinetic_main", "Energy":"energy_main", "Missile":"missile_delivery"}[family]


def _pds_space_key(family: str) -> str:
    return {"Kinetic":"kinetic_pds", "Energy":"energy_pds", "AMM":"amm_pds"}[family]


def _power_cost(catalog: BaselineCatalog, family: str, tl: int, main_count: int) -> int:
    p = catalog.p(_weapon_space_key(family), tl)
    if family == "Energy":
        return int(p["standardTp"]) * main_count
    return int(p["firingTp"] if family == "Kinetic" else p["launchTp"]) * main_count


def _ew_power(row: dict[str, Any], installed: bool) -> int:
    return int(row.get("fullStrengthTp", 0)) if installed else 0


def enumerate_legal_builds(catalog: BaselineCatalog) -> tuple[int, list[BaselineBuild]]:
    raw = 0
    builds: list[BaselineBuild] = []
    for tl in range(1, 10):
        capacity = int(catalog.p("hull", tl)["capacity"])
        hardener_states = ((False, False), (True, False))
        if _hardener_available(catalog, tl):
            hardener_states = ((False, False), (True, False), (True, True))
        for family in ("Kinetic", "Energy", "Missile"):
            payloads = ("Standard",)
            if family == "Missile":
                payloads = ("GP",) + (("Swarmer",) if catalog.p("missile_swarmer", tl).get("available", False) else ())
            for payload in payloads:
                for main_count in (1,2):
                    for reactor_count in (1,2):
                        for shield, hardener in hardener_states:
                            for ecm_count in (0,1,2):
                                for eccm_count in (0,1,2):
                                    for pds in ("", "Kinetic", "Energy", "AMM"):
                                        raw += 1
                                        combat_space = (
                                            main_count * int(catalog.p(_weapon_space_key(family), tl).get("space", 0))
                                            + reactor_count * int(catalog.p("reactor", tl).get("space", 0))
                                            + int(catalog.p("stl", tl).get("space", 0))
                                            + int(catalog.p("ftl", tl).get("space", 0))
                                            + int(catalog.p("computer", tl).get("space", 0))
                                            + int(catalog.p("sensor", tl).get("space", 0))
                                            + (int(catalog.p("shield", tl).get("space", 0)) if shield else 0)
                                            + ecm_count * int(catalog.p("ecm", tl).get("space", 0))
                                            + eccm_count * int(catalog.p("eccm", tl).get("space", 0))
                                            + (int(catalog.p(_pds_space_key(pds), tl).get("space", 0)) if pds else 0)
                                            + (int(catalog.branches["shield-hardener"]["space"]) if hardener else 0)
                                        )
                                        if combat_space > capacity:
                                            continue
                                        residual = capacity - combat_space
                                        space_class = "exact_fill" if residual == 0 else ("near_fill" if residual <= 2 else "mission_aux_fill")
                                        reactor = catalog.p("reactor", tl)
                                        power_available = int(reactor["operationalTp"]) * reactor_count
                                        nominal = (
                                            int(catalog.p("sensor", tl).get("activeLowTp", 0) or 0)
                                            + _ew_power(catalog.p("ecm", tl), ecm_count > 0)
                                            + _ew_power(catalog.p("eccm", tl), eccm_count > 0)
                                            + (int(catalog.p(_pds_space_key(pds), tl).get("readinessTp", 0)) if pds else 0)
                                            + (1 if hardener else 0)
                                            + _power_cost(catalog, family, tl, main_count)
                                        )
                                        shield = bool(shield)
                                        max_demand = nominal + (int(catalog.p("shield", tl).get("tacticalRechargeCapTp", 0)) if shield else 0)
                                        ecm_rating = int(catalog.p("ecm", tl).get("rating", 0)) if ecm_count else 0
                                        eccm_rating = int(catalog.p("eccm", tl).get("rating", 0)) if eccm_count else 0
                                        bid = f"tl{tl}-{family.lower()}-{payload.lower()}-m{main_count}r{reactor_count}-s{int(shield)}h{int(hardener)}-em{ecm_count}ec{eccm_count}-p{pds.lower() or '0'}"
                                        builds.append(BaselineBuild(
                                            bid, tl, family, payload, main_count, reactor_count, shield, ecm_count, eccm_count, pds,
                                            hardener, capacity, combat_space, residual, space_class, power_available, nominal, max_demand,
                                            power_available - nominal, ecm_rating, eccm_rating,
                                        ))
    builds.sort(key=lambda b:b.id)
    return raw, builds


def _build_to_ecology(b: BaselineBuild, archetype: str) -> EcologyBuild:
    return EcologyBuild(
        id=b.id, tl=b.tl, archetype=archetype, weapon_family=b.weapon_family,
        main_count=b.main_count, reactor_count=b.reactor_count, shield=b.shield,
        ecm=b.ecm_count > 0, eccm=b.eccm_count > 0, pds_family=(b.pds_family or None),
        shield_hardener=b.shield_hardener, capacity=b.capacity, combat_space=b.combat_space,
        mission_aux_space=b.mission_aux_space, missile_payload=(b.missile_payload if b.weapon_family == "Missile" else "GP"),
    )


def _pick(builds: list[BaselineBuild], tl: int, family: str, *, payload: str | None = None, role: str = "balanced") -> BaselineBuild:
    candidates = [b for b in builds if b.tl == tl and b.weapon_family == family and (payload is None or b.missile_payload == payload)]
    if role == "balanced":
        preferred = [b for b in candidates if b.main_count==1 and b.reactor_count==1 and b.shield and b.ecm_count==1 and b.eccm_count==1 and not b.pds_family and not b.shield_hardener]
    elif role == "defense":
        pds = "AMM" if family == "Missile" else family
        preferred = [b for b in candidates if b.main_count==1 and b.reactor_count==1 and b.shield and b.ecm_count==0 and b.eccm_count==1 and b.pds_family==pds]
    elif role == "missile_defense":
        preferred = [b for b in candidates if b.main_count==1 and b.reactor_count==1 and b.shield and b.ecm_count==0 and b.eccm_count==1 and b.pds_family=="AMM"]
    elif role == "power_hotspot":
        preferred = [b for b in candidates if b.main_count==2 and b.reactor_count==1 and b.nominal_power_margin <= 0]
    else:
        preferred = []
    pool = preferred or candidates
    if not pool:
        raise ValueError(f"no build for TL{tl} {family} {payload} {role}")
    return sorted(pool, key=lambda b:(b.mission_aux_space, b.id))[0]


def pipeline_smoke(repo: Path, catalog: BaselineCatalog, builds: list[BaselineBuild]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    variants: list[EcologyVariant] = []
    for tl in range(1,10):
        pairs = [
            (_pick(builds,tl,"Kinetic",role="balanced"), _pick(builds,tl,"Energy",role="defense"), "kinetic_vs_energy"),
            (_pick(builds,tl,"Energy",role="balanced"), _pick(builds,tl,"Kinetic",role="defense"), "energy_vs_kinetic"),
            (_pick(builds,tl,"Missile",payload="GP",role="balanced"), _pick(builds,tl,"Kinetic",role="missile_defense"), "missile_gp_vs_defense"),
        ]
        if tl >= 2:
            pairs.append((_pick(builds,tl,"Missile",payload="Swarmer",role="balanced"), _pick(builds,tl,"Kinetic",role="missile_defense"), "swarmer_vs_defense"))
        for a,b,group in pairs:
            ea, eb = _build_to_ecology(a, "cp124-smoke-attacker"), _build_to_ecology(b, "cp124-smoke-defender")
            for order in ("SideAFirst","SideBFirst"):
                variants.append(EcologyVariant(
                    id=f"cp124-tl{tl}-{group}-{order.lower()}", tl=tl, side_a=ea, side_b=eb,
                    movement_order=order, population="cp124_zero_weight_pipeline_smoke", scenario_group=group,
                ))
    matrix = catalog.matrix
    rows: list[dict[str, Any]] = []
    for i,v in enumerate(variants):
        result = run_trial(matrix, v, MASTER_SEED, i)
        rows.append(_aggregate_variant(v,[result]))
    return rows, [{"variant_id":v.id,"tl":v.tl,"scenario_group":v.scenario_group,"movement_order":v.movement_order,"side_a":v.side_a.id,"side_b":v.side_b.id} for v in variants]


def _damage_oracle(shield: int, armor_integrity: int, armor_protection: int, damage: int, spen: int, apen: int, shield_armor: int) -> dict[str,int]:
    r=resolve_layered_damage(
        shield=shield,armor_integrity=armor_integrity,armor_protection=armor_protection,
        hull=10**9,damage=damage,spen=spen,apen=apen,shield_armor=shield_armor)
    return {
        "shield_penetration_bypassed":r.shield_bypass,
        "shield_armor_prevented":r.shield_penetration_resisted,
        "shield_absorbed":r.shield_absorbed,
        "armor_penetration_bypassed":r.armor_bypass,
        "armor_prevented":r.armor_penetration_resisted,
        "armor_integrity_damage":r.armor_absorbed,
        "armor_protection_damage":0,
        "hull_damage":r.hull_damage,
    }


def resolve_hull_repair(profile: dict[str, Any], missing_hull: int, roll: int, telemetry: SideTelemetry | None = None) -> int:
    t = telemetry if telemetry is not None else SideTelemetry()
    t.damage_control_attempts += 1
    if roll <= int(profile["hullRepairChancePp"]):
        t.damage_control_successes += 1
        restored = min(max(0, missing_hull), int(profile["hullRestoredPerSuccessfulKit"]))
        t.damage_control_hull_restored += restored
        return restored
    return 0


def instrumentation_probes(repo: Path, catalog: BaselineCatalog, builds: list[BaselineBuild], smoke_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    # Exact layer-accounting oracle against the live damage resolver.
    target_build = _build_to_ecology(_pick(builds,5,"Energy",role="defense"), "damage-probe")
    target = _create_side(catalog.matrix, target_build, 0)
    target.shield = target.shield_max = 9
    target.armor_integrity = 12
    target.armor_protection = 3
    before = (target.shield,target.armor_integrity,target.armor_protection,target.hull)
    oracle = _damage_oracle(*before[:3], 13, 3, 4, 2)
    _apply_damage(target,13,3,4,2,"direct")
    actual = {k:getattr(target.telemetry,k) for k in oracle}
    probes.append({"probe":"damage-layer-oracle","passed":actual==oracle,"expected":json.dumps(oracle,sort_keys=True),"actual":json.dumps(actual,sort_keys=True)})

    # Two-packet Flight must remain one launch/terminal roll but two damage packets after a hit.
    sw = catalog.missile_operational_profile(5,"Swarmer")
    gp = catalog.missile_operational_profile(5,"GP")
    probes.append({"probe":"missile-profile-composition","passed":sw["packets"]==2 and gp["packets"]==1 and sw["pdsInterceptPenaltyPp"]==10 and sw["guidance"]==gp["guidance"]+10,"expected":"split delivery/guidance/payload composition","actual":json.dumps({"gp":gp,"swarmer":sw},sort_keys=True)})

    # Damage Control reference consumer: production yield changes are explicit TL characteristics.
    dc_expect = {1:1,7:2,9:3}
    for tl,y in dc_expect.items():
        t=SideTelemetry(); restored=resolve_hull_repair(catalog.p("damage_control",tl),10,1,t)
        probes.append({"probe":f"damage-control-tl{tl}","passed":restored==y and t.damage_control_attempts==1 and t.damage_control_successes==1 and t.damage_control_hull_restored==y,"expected":f"1 attempt / 1 success / {y} Hull","actual":json.dumps({"restored":restored,"attempts":t.damage_control_attempts,"successes":t.damage_control_successes,"telemetryHull":t.damage_control_hull_restored})})
    t=SideTelemetry(); restored=resolve_hull_repair(catalog.p("damage_control",9),10,100,t)
    probes.append({"probe":"damage-control-failure","passed":restored==0 and t.damage_control_attempts==1 and t.damage_control_successes==0,"expected":"failed attempt consumes no Hull restoration","actual":json.dumps({"restored":restored,"attempts":t.damage_control_attempts,"successes":t.damage_control_successes})})

    # Same-type EW redundancy is representable but never additive.
    redundant = next(b for b in builds if b.tl==5 and b.ecm_count==2 and b.eccm_count==2)
    probes.append({"probe":"ew-redundancy-nonadditive","passed":redundant.effective_ecm_rating==int(catalog.p("ecm",5)["rating"]) and redundant.effective_eccm_rating==int(catalog.p("eccm",5)["rating"]),"expected":"duplicate installations consume Space but highest rating only","actual":json.dumps({"ecmCount":redundant.ecm_count,"effectiveEcm":redundant.effective_ecm_rating,"eccmCount":redundant.eccm_count,"effectiveEccm":redundant.effective_eccm_rating})})

    # Source-side ownership: launches on attacker, terminal/guidance/hits on target.
    missile_rows=[r for r in smoke_rows if r["scenario_group"] in ("missile_gp_vs_defense","swarmer_vs_defense")]
    owner_ok=bool(missile_rows) and all(float(r["mean_a_missile_launches"])>=0 and float(r["mean_a_missile_guidance_attempts"])==0 and float(r["mean_a_missile_hits"])==0 for r in missile_rows if float(r["mean_a_missile_launches"])>0)
    # Require at least one exercised target-side terminal/guidance event across the smoke.
    owner_ok = owner_ok and any(float(r["mean_b_missile_guidance_attempts"])>0 for r in missile_rows)
    probes.append({"probe":"missile-telemetry-ownership","passed":owner_ok,"expected":"attacker owns launches; target owns terminal/guidance/hit telemetry","actual":json.dumps({"rows":len(missile_rows),"guidanceRows":sum(float(r["mean_b_missile_guidance_attempts"])>0 for r in missile_rows)})})

    # Contract metrics must exist in the dataclass so derived summaries are reconstructible from raw counters.
    names=set(SideTelemetry.__dataclass_fields__)
    required={x["metric"] for x in TELEMETRY_CONTRACT}
    probes.append({"probe":"telemetry-schema-complete","passed":required<=names,"expected":f"{len(required)} required raw metrics","actual":json.dumps({"required":len(required),"present":len(required & names),"missing":sorted(required-names)})})
    return probes


def _build_rows(builds: list[BaselineBuild]) -> list[dict[str, Any]]:
    return [asdict(b) | {"used_space":b.used_space} for b in builds]


def _tl_summary(builds: list[BaselineBuild]) -> list[dict[str, Any]]:
    out=[]
    for tl in range(1,10):
        bs=[b for b in builds if b.tl==tl]
        out.append({
            "tl":tl,"legal_builds":len(bs),"exact_fill":sum(b.space_class=="exact_fill" for b in bs),
            "near_fill":sum(b.space_class=="near_fill" for b in bs),"mission_aux_fill":sum(b.space_class=="mission_aux_fill" for b in bs),
            "kinetic":sum(b.weapon_family=="Kinetic" for b in bs),"energy":sum(b.weapon_family=="Energy" for b in bs),
            "missile_gp":sum(b.weapon_family=="Missile" and b.missile_payload=="GP" for b in bs),
            "missile_swarmer":sum(b.weapon_family=="Missile" and b.missile_payload=="Swarmer" for b in bs),
            "dual_main":sum(b.main_count==2 for b in bs),"dual_reactor":sum(b.reactor_count==2 for b in bs),
            "redundant_ecm":sum(b.ecm_count==2 for b in bs),"redundant_eccm":sum(b.eccm_count==2 for b in bs),
            "nominal_power_shortfall_builds":sum(b.nominal_power_margin<0 for b in bs),
            "min_nominal_power_margin":min((b.nominal_power_margin for b in bs),default=0),
            "mean_mission_aux_space":statistics.fmean(b.mission_aux_space for b in bs) if bs else 0.0,
        })
    return out


def run_baseline_foundation(repo: Path, study_path: Path, outdir: Path) -> dict[str, Any]:
    doc=load_json(study_path)
    errs=validate_study(doc)
    if errs:
        raise ValueError("invalid CP124 foundation study: "+",".join(errs))
    started=time.perf_counter()
    catalog=BaselineCatalog(repo,doc["sourceMatrix"])
    raw,builds=enumerate_legal_builds(catalog)
    smoke_rows,smoke_variants=pipeline_smoke(repo,catalog,builds)
    probes=instrumentation_probes(repo,catalog,builds,smoke_rows)
    outdir.mkdir(parents=True,exist_ok=True)
    _write_csv(outdir/"executable_catalog.csv",catalog.profile_rows())
    _write_csv(outdir/"legal_builds.csv",_build_rows(builds))
    _write_csv(outdir/"tl_build_summary.csv",_tl_summary(builds))
    _write_csv(outdir/"pipeline_smoke_variants.csv",smoke_variants)
    _write_csv(outdir/"pipeline_smoke_results.csv",smoke_rows)
    _write_csv(outdir/"instrumentation_probes.csv",probes)
    (outdir/"telemetry_contract.json").write_text(json.dumps({"schemaVersion":"star-cluster-telemetry-contract-v0.1","checkpoint":124,"metrics":list(TELEMETRY_CONTRACT)},indent=2)+"\n",encoding="utf-8")

    failures=[]
    if len(catalog.profile_rows()) != int(doc["expectedProfileRows"]):
        failures.append("catalog-profile-count")
    if raw != int(doc["expectedRawBuildCombinations"]):
        failures.append("raw-build-count")
    if len(builds) != int(doc["expectedLegalBuilds"]):
        failures.append("legal-build-count")
    expected_by_tl={int(k):int(v) for k,v in doc.get("expectedLegalBuildsByTl",{}).items()}
    observed_by_tl={tl:sum(b.tl==tl for b in builds) for tl in range(1,10)}
    if observed_by_tl != expected_by_tl:
        failures.append("legal-build-count-by-tl")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("mission-aux-fill-accounting")
    for tl in range(1,10):
        bs=[b for b in builds if b.tl==tl]
        if {b.weapon_family for b in bs}!={"Kinetic","Energy","Missile"}:
            failures.append(f"family-coverage-tl{tl}")
        if not any(b.weapon_family=="Missile" and b.missile_payload=="GP" for b in bs):
            failures.append(f"gp-missile-coverage-tl{tl}")
        if tl>=2 and not any(b.weapon_family=="Missile" and b.missile_payload=="Swarmer" for b in bs):
            failures.append(f"swarmer-coverage-tl{tl}")
    if any(int(r["errors"]) for r in smoke_rows):
        failures.append("pipeline-smoke-trial-errors")
    if len(smoke_rows)!=int(doc["expectedPipelineSmokeVariants"]):
        failures.append("pipeline-smoke-count")
    if len(probes)!=int(doc["expectedInstrumentationProbes"]):
        failures.append("instrumentation-probe-count")
    if len(TELEMETRY_CONTRACT)!=int(doc["expectedTelemetryContractMetrics"]):
        failures.append("telemetry-contract-count")
    if any(not bool(p["passed"]) for p in probes):
        failures += ["probe:"+str(p["probe"]) for p in probes if not bool(p["passed"])]
    if not any(float(r["mean_a_direct_fire_eligible_actions"])>0 for r in smoke_rows):
        failures.append("direct-eligibility-not-exercised")
    if not any(float(r["mean_a_missile_launch_eligible_actions"])>0 for r in smoke_rows):
        failures.append("missile-eligibility-not-exercised")
    if not any(float(r["mean_b_damage_packets_resolved"])>=2 for r in smoke_rows if r["scenario_group"]=="swarmer_vs_defense"):
        failures.append("swarmer-packet-telemetry-not-exercised")

    summary={
        "schemaVersion":RESULT_SCHEMA,"checkpoint":124,"acceptedReferenceBaseline":123,"acceptedImplementationBaseline":122,
        "sourceMatrix":doc["sourceMatrix"],"profileFamilies":len(catalog.profiles),"profileRows":len(catalog.profile_rows()),
        "rawBuildCombinations":raw,"legalBuilds":len(builds),"pipelineSmokeVariants":len(smoke_rows),"pipelineSmokeTrials":len(smoke_rows),
        "instrumentationProbeCount":len(probes),"telemetryContractMetricCount":len(TELEMETRY_CONTRACT),
        "substantiveMonteCarloTrials":0,"balanceValidated":False,"automaticPromotion":False,
        "elapsedSeconds":time.perf_counter()-started,"failedGates":failures,
    }
    (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
