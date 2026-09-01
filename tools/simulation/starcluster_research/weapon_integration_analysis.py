from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .ecology import CandidateMatrix, DAMAGE_MODEL
from .study import load_json
from .weapon_family_analysis import FamilyCatalog, build_variants, execute, _target_fixture_rows, _write_csv

SCHEMA = "star-cluster-campaign-weapon-integration-v0.1"
RESULT_SCHEMA = "star-cluster-campaign-weapon-integration-results-v0.1"


def _priority(doc: dict[str, Any], tl: int) -> str:
    if tl in [int(x) for x in doc.get("primaryCalibrationTls", [])]:
        return "primary"
    if tl in [int(x) for x in doc.get("advancedValidationTls", [])]:
        return "advanced"
    return "endpoint_stress"


def _profile_ids(doc: dict[str, Any], key: str) -> set[str]:
    return {str(x.get("id")) for x in doc.get(key, [])}


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 119:
        errors.append("checkpoint")
    if int(doc.get("acceptedBaseline", 0)) != 118:
        errors.append("acceptedBaseline")
    if doc.get("damageModel") != DAMAGE_MODEL:
        errors.append("damageModel")
    if doc.get("internalDamageCriticalsSimulated") is not False:
        errors.append("internalDamageCriticalsSimulated")
    if doc.get("automaticPromotion") is not False:
        errors.append("automaticPromotion")
    if int(doc.get("trialsPerVariant", 0)) < 1 or int(doc.get("authoringTrialsPerVariant", 0)) < 1:
        errors.append("trialCounts")

    primary = [int(x) for x in doc.get("primaryCalibrationTls", [])]
    advanced = [int(x) for x in doc.get("advancedValidationTls", [])]
    endpoint = [int(x) for x in doc.get("endpointStressTls", [])]
    if primary != [1, 2, 3, 4, 5, 6] or advanced != [7] or endpoint != [8, 9]:
        errors.append("tlPriority")
    if [int(x) for x in doc.get("missileStudyTls", [])] != list(range(1, 10)):
        errors.append("missileStudyTls")
    if [int(x) for x in doc.get("kineticStudyTls", [])] != list(range(1, 10)):
        errors.append("kineticStudyTls")
    if [int(x) for x in doc.get("energyReferenceTls", [])] != list(range(1, 10)):
        errors.append("energyReferenceTls")
    if doc.get("specialistPairingIds") or doc.get("adaptivePairingIds") or doc.get("specialistPairingIdsByTl") or doc.get("adaptivePairingIdsByTl"):
        errors.append("legacyPayloadMenuReintroduced")

    fixtures = doc.get("targetFixtures", [])
    fixture_ids = [str(x.get("id")) for x in fixtures]
    required_fixtures = {
        "energy-balanced-legal", "energy-defense-legal",
        "kinetic-balanced-legal", "kinetic-ew-legal",
        "missile-balanced-legal", "missile-defense-legal",
    }
    if set(fixture_ids) != required_fixtures or len(fixture_ids) != len(set(fixture_ids)):
        errors.append("targetFixtureSet")
    if any(x.get("classification") != "legal_build" for x in fixtures):
        errors.append("nonLegalFixture")

    mids = _profile_ids(doc, "missileProfiles")
    kids = _profile_ids(doc, "kineticProfiles")
    required_missile = {
        "gp-current", "missile-working-fission-d6", "missile-working-fusion-d7",
        "missile-working-antimatter-d8", "swarmer-early-tl2", "swarmer-mid", "swarmer-mature",
    }
    required_kinetic = {"gp-current", "kinetic-working-smart-plus5"}
    if mids != required_missile:
        errors.append("missileProfileSet")
    if kids != required_kinetic:
        errors.append("kineticProfileSet")

    by_m = {str(x["id"]): x for x in doc.get("missileProfiles", [])}
    for pid in ("missile-working-fission-d6", "missile-working-fusion-d7", "missile-working-antimatter-d8"):
        p = by_m[pid]
        if int(p.get("spen", -1)) != 1 or int(p.get("apen", -1)) != 2:
            errors.append(f"gpPenetrationDrift:{pid}")
        if int(p.get("packets", 1)) != 1 or int(p.get("guidanceDelta", 0)) != 0 or int(p.get("pdsInterceptPenaltyPp", 0)) != 0:
            errors.append(f"gpSpecialistLeakage:{pid}")
    expected_gp = {
        "1": "gp-current", "2": "gp-current", "3": "missile-working-fission-d6", "4": "missile-working-fission-d6",
        "5": "missile-working-fusion-d7", "6": "missile-working-fusion-d7",
        "7": "missile-working-antimatter-d8", "8": "missile-working-antimatter-d8", "9": "missile-working-antimatter-d8",
    }
    if doc.get("workingMissileGpByTl") != expected_gp:
        errors.append("workingMissileGpByTl")

    sw = {pid: by_m[pid] for pid in ("swarmer-early-tl2", "swarmer-mid", "swarmer-mature")}
    if 1 in [int(x) for x in sw["swarmer-early-tl2"].get("studyTls", [])]:
        errors.append("swarmerMustStartTl2")
    expected_sw = {
        "swarmer-early-tl2": (2, 10, 10),
        "swarmer-mid": (3, 10, 10),
        "swarmer-mature": (4, 15, 15),
    }
    for pid, (damage, guidance, pds) in expected_sw.items():
        p = sw[pid]
        if int(p.get("packets", 1)) != 2 or int(p.get("damage", 0)) != damage:
            errors.append(f"swarmerPacketShape:{pid}")
        if int(p.get("spen", 0)) != 0 or int(p.get("apen", 0)) != 0:
            errors.append(f"swarmerPenetrationLeakage:{pid}")
        if int(p.get("guidanceDelta", 0)) != guidance or int(p.get("pdsInterceptPenaltyPp", 0)) != pds:
            errors.append(f"swarmerCoveragePds:{pid}")
    expected_sw_map = {
        "1": None, "2": "swarmer-early-tl2", "3": "swarmer-early-tl2", "4": "swarmer-mid", "5": "swarmer-mid",
        "6": "swarmer-mature", "7": "swarmer-mature", "8": "swarmer-mature", "9": "swarmer-mature",
    }
    if doc.get("workingSwarmerByTl") != expected_sw_map:
        errors.append("workingSwarmerByTl")

    kp = next(x for x in doc.get("kineticProfiles", []) if x["id"] == "kinetic-working-smart-plus5")
    if int(kp.get("accuracyDelta", 0)) != 5:
        errors.append("kineticAccuracyStep")
    if any(int(kp.get(k, 0)) != 0 for k in ("damageDelta", "spenDelta", "apenDelta")) or int(kp.get("packets", 1)) != 1 or kp.get("orderedPackets"):
        errors.append("kineticMultiAxisDrift")
    expected_k = {str(tl): ("gp-current" if tl <= 3 else "kinetic-working-smart-plus5") for tl in range(1, 10)}
    if doc.get("workingKineticByTl") != expected_k:
        errors.append("workingKineticByTl")
    return errors


def _profile_catalog_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [{
        "family": "Energy", "profile_id": "energy-native", "classification": "reference",
        "study_tls": "1,2,3,4,5,6,7,8,9", "role": "Native CP109 Energy profile with ordinary power/output doctrine.",
        "damage": "mode-driven", "spen": "native", "apen": "native", "accuracy_delta": 0,
        "guidance_delta": 0, "packets": 1, "pds_intercept_penalty_pp": 0,
    }]
    for key in ("missileProfiles", "kineticProfiles"):
        for p in doc.get(key, []):
            rows.append({
                "family": p.get("family", ""), "profile_id": p.get("id", ""), "classification": p.get("classification", ""),
                "study_tls": ",".join(str(x) for x in p.get("studyTls", [])), "role": p.get("role", ""),
                "damage": p.get("damage", "native"), "spen": p.get("spen", "native"), "apen": p.get("apen", "native"),
                "accuracy_delta": p.get("accuracyDelta", 0), "guidance_delta": p.get("guidanceDelta", 0),
                "packets": p.get("packets", 1), "pds_intercept_penalty_pp": p.get("pdsInterceptPenaltyPp", 0),
            })
    return rows


def _fixture_meta(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(x["id"]): x for x in doc.get("targetFixtures", [])}


def _summaries(rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    meta = _fixture_meta(doc)
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        family = {"missile_family_characteristic": "Missile", "kinetic_family_characteristic": "Kinetic", "energy_family_reference": "Energy"}[r["scenario_group"]]
        grouped[(int(r["tl"]), family, r["side_a_profile"], r["target_fixture"], r["side_a_archetype"])].append(r)
    out: list[dict[str, Any]] = []
    for (tl, family, profile, fixture, archetype), rs in sorted(grouped.items()):
        f = meta[fixture]
        direct_shots = statistics.fmean(float(x["mean_a_direct_shots"]) for x in rs)
        direct_hits = statistics.fmean(float(x["mean_a_direct_hits"]) for x in rs)
        missile_launches = statistics.fmean(float(x["mean_a_missile_launches"]) for x in rs)
        missile_hits = statistics.fmean(float(x["mean_b_missile_hits"]) for x in rs)
        pds_attempts = statistics.fmean(float(x["mean_b_pds_attempts"]) for x in rs)
        pds_intercepts = statistics.fmean(float(x["mean_b_pds_intercepts"]) for x in rs)
        out.append({
            "tl": tl, "priority": _priority(doc, tl), "attacker_family": family, "profile": profile,
            "attacker_archetype": archetype, "target_fixture": fixture,
            "target_family": f["baseFamily"], "target_archetype": f["baseArchetype"], "variants": len(rs),
            "mean_conditional_win_rate": statistics.fmean(float(x["conditional_win_rate_a"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
            "mean_target_hull_damage": statistics.fmean(float(x["mean_b_hull_damage"]) for x in rs),
            "mean_target_armor_integrity_damage": statistics.fmean(float(x["mean_b_armor_integrity_damage"]) for x in rs),
            "mean_target_shield_absorbed": statistics.fmean(float(x["mean_b_shield_absorbed"]) for x in rs),
            "direct_hit_rate": direct_hits / direct_shots if direct_shots else 0.0,
            "missile_hit_per_launch": missile_hits / missile_launches if missile_launches else 0.0,
            "pds_intercept_per_attempt": pds_intercepts / pds_attempts if pds_attempts else 0.0,
            "mean_defender_pds_attempts": pds_attempts,
            "mean_defender_pds_intercepts": pds_intercepts,
        })
    return out


def _configuration(doc: dict[str, Any], family: str, tl: int, profile: str) -> str | None:
    if family == "Energy" and profile == "energy-native":
        return "energy-native"
    if family == "Kinetic":
        if profile == "gp-current":
            return "kinetic-reference"
        if profile == doc["workingKineticByTl"][str(tl)]:
            return "kinetic-working"
    if family == "Missile":
        if profile == "gp-current":
            return "missile-reference"
        if profile == doc["workingMissileGpByTl"][str(tl)]:
            return "missile-working-gp"
        if profile == doc["workingSwarmerByTl"].get(str(tl)):
            return "missile-swarmer"
    return None


def _ecology_summary(summary_rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in summary_rows:
        cfg = _configuration(doc, r["attacker_family"], int(r["tl"]), r["profile"])
        if cfg:
            grouped[(int(r["tl"]), cfg)].append(r)
    out: list[dict[str, Any]] = []
    for (tl, cfg), rs in sorted(grouped.items()):
        target_means: dict[str, float] = {}
        for tf in sorted({r["target_fixture"] for r in rs}):
            vals = [float(r["mean_conditional_win_rate"]) for r in rs if r["target_fixture"] == tf]
            target_means[tf] = statistics.fmean(vals)
        worst = min(target_means, key=target_means.get)
        best = max(target_means, key=target_means.get)
        out.append({
            "tl": tl, "priority": _priority(doc, tl), "configuration": cfg,
            "summary_rows": len(rs),
            "mean_conditional_win_rate": statistics.fmean(float(r["mean_conditional_win_rate"]) for r in rs),
            "mean_unresolved_rate": statistics.fmean(float(r["mean_unresolved_rate"]) for r in rs),
            "mean_turns": statistics.fmean(float(r["mean_turns"]) for r in rs),
            "worst_target": worst, "worst_target_win_rate": target_means[worst],
            "best_target": best, "best_target_win_rate": target_means[best],
        })
    return out


def _delta_rows(summary_rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    idx = {(int(r["tl"]), r["attacker_family"], r["profile"], r["attacker_archetype"], r["target_fixture"]): r for r in summary_rows}
    out: list[dict[str, Any]] = []
    for r in summary_rows:
        fam = r["attacker_family"]
        if fam not in ("Missile", "Kinetic") or r["profile"] == "gp-current":
            continue
        ref = idx.get((int(r["tl"]), fam, "gp-current", r["attacker_archetype"], r["target_fixture"]))
        if not ref:
            continue
        out.append({
            "tl": int(r["tl"]), "priority": r["priority"], "family": fam, "profile": r["profile"],
            "attacker_archetype": r["attacker_archetype"], "target_fixture": r["target_fixture"],
            "target_family": r["target_family"],
            "delta_conditional_win_rate": float(r["mean_conditional_win_rate"]) - float(ref["mean_conditional_win_rate"]),
            "delta_unresolved_rate": float(r["mean_unresolved_rate"]) - float(ref["mean_unresolved_rate"]),
            "delta_mean_turns": float(r["mean_turns"]) - float(ref["mean_turns"]),
            "delta_target_hull_damage": float(r["mean_target_hull_damage"]) - float(ref["mean_target_hull_damage"]),
            "delta_direct_hit_rate": float(r["direct_hit_rate"]) - float(ref["direct_hit_rate"]),
            "delta_missile_hit_per_launch": float(r["missile_hit_per_launch"]) - float(ref["missile_hit_per_launch"]),
            "delta_pds_intercept_per_attempt": float(r["pds_intercept_per_attempt"]) - float(ref["pds_intercept_per_attempt"]),
        })
    return out


def _movement_rows(raw_rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in raw_rows:
        family = {"missile_family_characteristic": "Missile", "kinetic_family_characteristic": "Kinetic", "energy_family_reference": "Energy"}[r["scenario_group"]]
        key = (int(r["tl"]), family, r["side_a_profile"], r["side_a_archetype"], r["target_fixture"])
        grouped[key][r["movement_order"]] = r
    out = []
    for (tl, family, profile, archetype, fixture), pair in sorted(grouped.items()):
        if "SideAFirst" not in pair or "SideBFirst" not in pair:
            continue
        a, b = pair["SideAFirst"], pair["SideBFirst"]
        out.append({
            "tl": tl, "priority": _priority(doc, tl), "family": family, "profile": profile,
            "attacker_archetype": archetype, "target_fixture": fixture,
            "side_a_first_win_rate": float(a["conditional_win_rate_a"]),
            "side_b_first_win_rate": float(b["conditional_win_rate_a"]),
            "movement_order_swing_pp": abs(float(a["conditional_win_rate_a"]) - float(b["conditional_win_rate_a"])) * 100.0,
            "side_a_first_unresolved": float(a["unresolved_rate"]),
            "side_b_first_unresolved": float(b["unresolved_rate"]),
        })
    return out


def _tier_summary(ecology_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in ecology_rows:
        grouped[(r["priority"], r["configuration"])].append(r)
    out = []
    for (priority, cfg), rs in sorted(grouped.items()):
        out.append({
            "priority": priority, "configuration": cfg, "tls": ",".join(str(r["tl"]) for r in sorted(rs, key=lambda x: x["tl"])),
            "mean_conditional_win_rate": statistics.fmean(float(r["mean_conditional_win_rate"]) for r in rs),
            "mean_unresolved_rate": statistics.fmean(float(r["mean_unresolved_rate"]) for r in rs),
            "mean_turns": statistics.fmean(float(r["mean_turns"]) for r in rs),
        })
    return out


def _pds_guidance_probe(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = CandidateMatrix(repo)
    catalog = FamilyCatalog(doc)
    rows: list[dict[str, Any]] = []
    for tl in range(1, 10):
        computer = matrix.p("computer", tl)
        pds = matrix.p("amm_pds", tl)
        base = min(95, int(pds["baseChancePp"]) + int(computer["targetingPp"]))
        missile = matrix.p("missile_delivery", tl)
        for p in sorted(catalog.missile.values(), key=lambda x: x.id):
            if tl not in p.study_tls:
                continue
            rows.append({
                "tl": tl, "priority": _priority(doc, tl), "profile": p.id,
                "native_guidance": int(missile["guidanceBaseHit"]),
                "profile_guidance_delta": p.guidance_delta,
                "effective_guidance": max(1, min(99, int(missile["guidanceBaseHit"]) + p.guidance_delta)),
                "native_pds_intercept_chance": base,
                "profile_pds_penalty_pp": p.pds_intercept_penalty_pp,
                "effective_pds_intercept_chance": max(0, base - p.pds_intercept_penalty_pp),
                "packets": p.packets,
                "packet_damage": p.damage if p.damage is not None else int(missile["warheadDamage"]),
            })
    return rows


def run_weapon_integration_analysis(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 1) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("invalid CP119 study: " + ",".join(errors))
    builds, variants = build_variants(repo, doc)
    trials = int(trials_override or doc["trialsPerVariant"])
    rows, elapsed = execute(repo, doc, variants, trials, jobs)
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "variants.csv", rows)
    _write_csv(outdir / "builds.csv", [{
        "build_id": b.id, "tl": b.tl, "family": b.weapon_family, "archetype": b.archetype,
        "combat_space": b.combat_space, "mission_aux_space": b.mission_aux_space,
        "capacity": b.capacity, "used_space": b.used_space, "free_space": b.capacity - b.used_space,
    } for b in builds])
    catalog = FamilyCatalog(doc)
    _write_csv(outdir / "target_fixtures.csv", _target_fixture_rows(CandidateMatrix(repo), catalog, doc, repo))
    _write_csv(outdir / "profile_catalog.csv", _profile_catalog_rows(doc))
    _write_csv(outdir / "pds_guidance_probe.csv", _pds_guidance_probe(repo, doc))
    summaries = _summaries(rows, doc)
    ecology = _ecology_summary(summaries, doc)
    deltas = _delta_rows(summaries, doc)
    movement = _movement_rows(rows, doc)
    tiers = _tier_summary(ecology)
    _write_csv(outdir / "integration_summary.csv", summaries)
    _write_csv(outdir / "ecology_summary.csv", ecology)
    _write_csv(outdir / "candidate_delta_summary.csv", deltas)
    _write_csv(outdir / "movement_order_summary.csv", movement)
    _write_csv(outdir / "tier_summary.csv", tiers)

    failures: list[str] = []
    if any(int(r["errors"]) for r in rows):
        failures.append("trial-errors")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("exact-fill-builds")
    if not any(r["scenario_group"] == "energy_family_reference" and float(r["mean_a_direct_shots"]) > 0 for r in rows):
        failures.append("energy-reference-telemetry")
    if not any(r["scenario_group"] == "kinetic_family_characteristic" and r["side_a_profile"] == "kinetic-working-smart-plus5" and float(r["mean_a_direct_shots"]) > 0 for r in rows):
        failures.append("kinetic-working-telemetry")
    if not any(r["scenario_group"] == "missile_family_characteristic" and str(r["side_a_profile"]).startswith("missile-working-") and float(r["mean_a_missile_launches"]) > 0 for r in rows):
        failures.append("missile-working-gp-telemetry")
    if not any(r["scenario_group"] == "missile_family_characteristic" and str(r["side_a_profile"]).startswith("swarmer-") and float(r["mean_b_pds_attempts"]) > 0 for r in rows):
        failures.append("swarmer-pds-telemetry")
    if not any(int(r["tl"]) <= 6 for r in rows) or not any(int(r["tl"]) == 7 for r in rows) or not any(int(r["tl"]) >= 8 for r in rows):
        failures.append("tl-priority-coverage")

    counts = defaultdict(int)
    priorities = defaultdict(int)
    for v in variants:
        counts[v.scenario_group] += 1
        priorities[_priority(doc, v.tl)] += 1
    movement_working = [r for r in movement if _configuration(doc, r["family"], int(r["tl"]), r["profile"]) in ("energy-native", "kinetic-working", "missile-working-gp", "missile-swarmer")]
    max_swing = max((float(r["movement_order_swing_pp"]) for r in movement_working), default=0.0)
    primary_rows = [r for r in ecology if r["priority"] == "primary"]
    result = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 119,
        "acceptedBaseline": 118,
        "damageModel": DAMAGE_MODEL,
        "internalDamageCriticalsSimulated": False,
        "trialsPerVariant": trials,
        "variants": len(variants),
        "variantCounts": dict(sorted(counts.items())),
        "priorityVariantCounts": dict(sorted(priorities.items())),
        "totalTrials": len(variants) * trials,
        "elapsedSeconds": elapsed,
        "failedGates": failures,
        "automaticPromotion": False,
        "targetFixtureCount": len(catalog.fixtures),
        "controlledFixtureCount": 0,
        "missileProfileCount": len(catalog.missile),
        "kineticProfileCount": len(catalog.kinetic),
        "energyReferenceProfileCount": 1,
        "primaryCalibrationTls": doc["primaryCalibrationTls"],
        "advancedValidationTls": doc["advancedValidationTls"],
        "endpointStressTls": doc["endpointStressTls"],
        "workingMissileGpByTl": doc["workingMissileGpByTl"],
        "workingSwarmerByTl": doc["workingSwarmerByTl"],
        "workingKineticByTl": doc["workingKineticByTl"],
        "maxWorkingMovementOrderSwingPp": max_swing,
        "interpretation": "CP119 is a campaign-weighted same-TL integration ecology. It compares native Energy, a restrained +5 Kinetic smart-projectile working schedule, simple GP Missile yield milestones, and a TL2+ two-packet Swarmer branch against the same six legal exact-fill target packages. TL1-TL6 drive inference; TL7 is advanced validation; TL8-TL9 are endpoint stress. Outcome rates are review evidence only and never automatic promotion gates.",
    }
    (outdir / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
