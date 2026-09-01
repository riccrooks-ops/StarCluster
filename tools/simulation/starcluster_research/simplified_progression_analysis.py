from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .ecology import CandidateMatrix, DAMAGE_MODEL
from .study import load_json
from .weapon_family_analysis import (
    FamilyCatalog,
    build_variants,
    execute,
    _target_fixture_rows,
    _write_csv,
)

SCHEMA = "star-cluster-simplified-weapon-progression-v0.1"
RESULT_SCHEMA = "star-cluster-simplified-weapon-progression-results-v0.1"


def _ids(doc: dict[str, Any], key: str) -> set[str]:
    return {str(x.get("id")) for x in doc.get(key, [])}


def _priority(doc: dict[str, Any], tl: int) -> str:
    if tl in [int(x) for x in doc.get("primaryCalibrationTls", [])]:
        return "primary"
    if tl in [int(x) for x in doc.get("advancedValidationTls", [])]:
        return "advanced"
    return "endpoint_stress"


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 118:
        errors.append("checkpoint")
    if int(doc.get("acceptedBaseline", 0)) != 117:
        errors.append("acceptedBaseline")
    if doc.get("damageModel") != DAMAGE_MODEL:
        errors.append("damageModel")
    if doc.get("automaticPromotion") is not False:
        errors.append("automaticPromotion")
    if int(doc.get("trialsPerVariant", 0)) < 1 or int(doc.get("authoringTrialsPerVariant", 0)) < 1:
        errors.append("trialCounts")

    primary = [int(x) for x in doc.get("primaryCalibrationTls", [])]
    advanced = [int(x) for x in doc.get("advancedValidationTls", [])]
    endpoint = [int(x) for x in doc.get("endpointStressTls", [])]
    if primary != [1, 2, 3, 4, 5, 6] or advanced != [7] or endpoint != [8, 9]:
        errors.append("tlPriority")
    if sorted(set(primary + advanced + endpoint)) != list(range(1, 10)):
        errors.append("tlPriorityCoverage")
    if [int(x) for x in doc.get("missileStudyTls", [])] != list(range(1, 10)):
        errors.append("missileStudyTls")
    if [int(x) for x in doc.get("kineticStudyTls", [])] != list(range(1, 10)):
        errors.append("kineticStudyTls")
    if doc.get("energyReferenceTls") not in ([], None):
        errors.append("energyReferenceTls")
    if doc.get("specialistPairingIds") or doc.get("adaptivePairingIds") or doc.get("specialistPairingIdsByTl") or doc.get("adaptivePairingIdsByTl"):
        errors.append("legacyWarheadMenuReintroduced")

    fixtures = doc.get("targetFixtures", [])
    fixture_ids = [str(x.get("id")) for x in fixtures]
    required = {
        "balanced-layered-legal",
        "shield-heavy-legal",
        "armor-exposed-legal",
        "pds-heavy-legal",
        "armor-heavy-fixture",
        "light-fixture",
    }
    if len(fixture_ids) != len(set(fixture_ids)):
        errors.append("duplicateTargetFixture")
    if set(fixture_ids) != required:
        errors.append("targetFixtureSet")
    for row in fixtures:
        if row.get("classification") not in ("legal_build", "controlled_fixture"):
            errors.append(f"targetFixtureClassification:{row.get('id')}")

    mids = _ids(doc, "missileProfiles")
    kids = _ids(doc, "kineticProfiles")
    required_m = {
        "gp-current",
        "missile-fission-gp-d6",
        "missile-fusion-gp-d6",
        "missile-fusion-gp-d7",
        "missile-antimatter-gp-d7",
        "missile-antimatter-gp-d8",
        "swarmer-early-a",
        "swarmer-early-b",
        "swarmer-mid-a",
        "swarmer-mid-b",
        "swarmer-mature-a",
        "swarmer-mature-b",
    }
    required_k = {
        "gp-current",
        "kinetic-smart-plus5",
        "kinetic-smart-plus10",
        "kinetic-smart-plus15",
        "kinetic-damage-plus1",
        "kinetic-apen-plus1",
    }
    if not required_m <= mids:
        errors.append("requiredMissileProfiles")
    if not required_k <= kids:
        errors.append("requiredKineticProfiles")

    for row in doc.get("missileProfiles", []):
        pid = str(row.get("id"))
        tls = [int(x) for x in row.get("studyTls", [])]
        if not tls:
            errors.append(f"missileStudyTls:{pid}")
        if pid == "gp-current":
            continue
        if "-gp-" in pid:
            if int(row.get("spen", -99)) != 1 or int(row.get("apen", -99)) != 2:
                errors.append(f"gpPenetrationCreep:{pid}")
            if row.get("guidanceDelta", 0) or row.get("pdsInterceptPenaltyPp", 0) or int(row.get("packets", 1)) != 1:
                errors.append(f"gpSpecialistLeakage:{pid}")
        if pid.startswith("swarmer-"):
            if int(row.get("packets", 1)) < 2:
                errors.append(f"swarmerPackets:{pid}")
            if int(row.get("guidanceDelta", 0)) <= 0:
                errors.append(f"swarmerCoverage:{pid}")
            if int(row.get("pdsInterceptPenaltyPp", 0)) < 0 or int(row.get("pdsInterceptPenaltyPp", 0)) > 20:
                errors.append(f"swarmerPdsBound:{pid}")
            if any(int(row.get(k, 0)) != 0 for k in ("shieldBonusDamage", "shieldArmorReduction", "rechargeSuppression")):
                errors.append(f"swarmerSpecialistLeakage:{pid}")
    # The introduction search must actually include early TLs; active CP117 placement is not pre-assumed.
    swarm_tls = sorted({int(tl) for row in doc.get("missileProfiles", []) if str(row.get("id", "")).startswith("swarmer-") for tl in row.get("studyTls", [])})
    if not {1, 2, 3} <= set(swarm_tls) or not {5, 6, 7} <= set(swarm_tls):
        errors.append("swarmerIntroductionMaturationCoverage")

    for row in doc.get("kineticProfiles", []):
        pid = str(row.get("id"))
        if pid == "gp-current":
            continue
        if int(row.get("packets", 1)) != 1 or row.get("orderedPackets"):
            errors.append(f"kineticAmmoMenuCreep:{pid}")
        if any(int(row.get(k, 0)) != 0 for k in ("shieldBonusDamage", "shieldArmorReduction", "rechargeSuppression", "guidanceDelta", "pdsInterceptPenaltyPp")):
            errors.append(f"kineticForeignMechanic:{pid}")
        changed = sum(bool(int(row.get(k, 0))) for k in ("accuracyDelta", "damageDelta", "apenDelta"))
        if changed != 1:
            errors.append(f"kineticSingleAxisControl:{pid}")
        if int(row.get("spenDelta", 0)) != 0 or row.get("spen") is not None:
            errors.append(f"kineticSpenIdentityDrift:{pid}")

    for tl in range(1, 10):
        if doc.get("contemporaryGpByTl", {}).get(str(tl)) != ["gp-current"]:
            errors.append(f"contemporaryGpByTl:{tl}")
    return errors


def _profile_catalog_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("missileProfiles", "kineticProfiles"):
        for p in doc.get(key, []):
            rows.append({
                "family": p.get("family", ""),
                "profile_id": p.get("id", ""),
                "role": p.get("role", ""),
                "study_tls": ",".join(str(x) for x in p.get("studyTls", [])),
                "damage": p.get("damage", ""),
                "damage_delta": p.get("damageDelta", 0),
                "spen": p.get("spen", ""),
                "spen_delta": p.get("spenDelta", 0),
                "apen": p.get("apen", ""),
                "apen_delta": p.get("apenDelta", 0),
                "accuracy_delta": p.get("accuracyDelta", 0),
                "guidance_delta": p.get("guidanceDelta", 0),
                "packets": p.get("packets", 1),
                "pds_intercept_penalty_pp": p.get("pdsInterceptPenaltyPp", 0),
                "classification": p.get("classification", "candidate"),
            })
    return rows


def _summaries(rows: list[dict[str, Any]], doc: dict[str, Any], group: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if r["scenario_group"] == group:
            grouped[(int(r["tl"]), r["side_a_profile"], r["target_fixture"], r["target_classification"], r["side_a_archetype"])].append(r)
    out: list[dict[str, Any]] = []
    for (tl, profile, fixture, classification, archetype), rs in sorted(grouped.items()):
        pds_attempts = statistics.fmean(float(x["mean_b_pds_attempts"]) for x in rs)
        pds_intercepts = statistics.fmean(float(x["mean_b_pds_intercepts"]) for x in rs)
        direct_shots = statistics.fmean(float(x["mean_a_direct_shots"]) for x in rs)
        direct_hits = statistics.fmean(float(x["mean_a_direct_hits"]) for x in rs)
        guidance_attempts = statistics.fmean(float(x["mean_b_missile_guidance_attempts"] if group == "missile_family_characteristic" else 0) for x in rs)
        # Missile hit/guidance telemetry is stored on the target side; launches remain on the shooter side.
        missile_hits = statistics.fmean(float(x["mean_b_missile_hits"]) for x in rs)
        missile_launches = statistics.fmean(float(x["mean_a_missile_launches"]) for x in rs)
        out.append({
            "tl": tl,
            "priority": _priority(doc, tl),
            "profile": profile,
            "target_fixture": fixture,
            "target_classification": classification,
            "attacker_archetype": archetype,
            "variants": len(rs),
            "mean_conditional_win_rate": statistics.fmean(float(x["conditional_win_rate_a"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
            "mean_direct_shots": direct_shots,
            "mean_direct_hits": direct_hits,
            "direct_hit_rate": direct_hits / direct_shots if direct_shots > 0 else 0.0,
            "mean_missile_launches": missile_launches,
            "mean_missile_hits": missile_hits,
            "missile_hit_per_launch": missile_hits / missile_launches if missile_launches > 0 else 0.0,
            "mean_defender_pds_attempts": pds_attempts,
            "mean_defender_pds_intercepts": pds_intercepts,
            "pds_intercept_per_attempt": pds_intercepts / pds_attempts if pds_attempts > 0 else 0.0,
            "mean_target_shield_absorbed": statistics.fmean(float(x["mean_b_shield_absorbed"]) for x in rs),
            "mean_target_armor_integrity_damage": statistics.fmean(float(x["mean_b_armor_integrity_damage"]) for x in rs),
            "mean_target_hull_damage": statistics.fmean(float(x["mean_b_hull_damage"]) for x in rs),
        })
    return out


def _pds_probe_rows(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
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
                "tl": tl,
                "priority": _priority(doc, tl),
                "profile": p.id,
                "native_guidance": int(missile["guidanceBaseHit"]),
                "profile_guidance_delta": p.guidance_delta,
                "effective_guidance": max(1, min(99, int(missile["guidanceBaseHit"]) + p.guidance_delta)),
                "native_pds_intercept_chance": base,
                "profile_pds_penalty_pp": p.pds_intercept_penalty_pp,
                "effective_pds_intercept_chance": max(0, base - p.pds_intercept_penalty_pp),
                "packets": p.packets,
                "packet_damage": p.damage if p.damage is not None else int(missile["warheadDamage"]),
                "total_nominal_packet_damage": p.packets * int(p.damage if p.damage is not None else missile["warheadDamage"]),
            })
    return rows


def run_simplified_progression_analysis(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 1) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("invalid CP118 study: " + ",".join(errs))
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
    _write_csv(outdir / "pds_guidance_probe.csv", _pds_probe_rows(repo, doc))
    missile = _summaries(rows, doc, "missile_family_characteristic")
    kinetic = _summaries(rows, doc, "kinetic_family_characteristic")
    _write_csv(outdir / "missile_progression_summary.csv", missile)
    _write_csv(outdir / "kinetic_progression_summary.csv", kinetic)

    failures: list[str] = []
    if any(int(r["errors"]) for r in rows):
        failures.append("trial-errors")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("exact-fill-underlying-builds")
    if not any(str(r["side_a_profile"]).startswith("swarmer-") and float(r["mean_a_payload_specialist_launches"]) > 0 for r in rows):
        failures.append("swarmer-launch-telemetry")
    if not any(str(r["side_a_profile"]).startswith("swarmer-") and r["target_fixture"] == "pds-heavy-legal" and float(r["mean_b_pds_attempts"]) > 0 for r in rows):
        failures.append("swarmer-pds-coverage")
    if not any(str(r["side_a_profile"]).startswith("kinetic-smart-") and float(r["mean_a_direct_shots"]) > 0 for r in rows):
        failures.append("kinetic-smart-telemetry")
    if not any(int(r["tl"]) <= 6 for r in rows) or not any(int(r["tl"]) == 7 for r in rows) or not any(int(r["tl"]) >= 8 for r in rows):
        failures.append("tl-priority-coverage")

    counts = defaultdict(int)
    for v in variants:
        counts[v.scenario_group] += 1
    priority_counts = defaultdict(int)
    for v in variants:
        priority_counts[_priority(doc, v.tl)] += 1
    analysis = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 118,
        "acceptedBaseline": 117,
        "damageModel": DAMAGE_MODEL,
        "internalDamageCriticalsSimulated": False,
        "trialsPerVariant": trials,
        "variants": len(variants),
        "variantCounts": dict(sorted(counts.items())),
        "priorityVariantCounts": dict(sorted(priority_counts.items())),
        "totalTrials": len(variants) * trials,
        "elapsedSeconds": elapsed,
        "failedGates": failures,
        "automaticPromotion": False,
        "targetFixtureCount": len(catalog.fixtures),
        "controlledFixtureCount": sum(f.classification == "controlled_fixture" for f in catalog.fixtures.values()),
        "missileProfileCount": len(catalog.missile),
        "kineticProfileCount": len(catalog.kinetic),
        "primaryCalibrationTls": doc["primaryCalibrationTls"],
        "advancedValidationTls": doc["advancedValidationTls"],
        "endpointStressTls": doc["endpointStressTls"],
        "interpretation": "CP118 is a KISS-focused progression study. TL1-TL6 are primary evidence, TL7 advanced validation, TL8-TL9 endpoint stress. GP Missile candidates vary yield without penetration creep; Swarmer candidates vary coverage/packetization/PDS saturation; Kinetic candidates are automatic single-axis progression controls, not selectable ammunition. No outcome threshold promotes a candidate.",
    }
    (outdir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis
