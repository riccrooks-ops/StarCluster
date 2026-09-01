from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .ecology import CandidateMatrix, DAMAGE_MODEL, _weapon
from .study import load_json
from .weapon_family_analysis import FamilyCatalog, build_variants, execute, _target_fixture_rows, _write_csv, _effective_profile

SCHEMA = "star-cluster-weapon-progression-sensitivity-v0.1"
RESULT_SCHEMA = "star-cluster-weapon-progression-sensitivity-results-v0.1"


def _priority(doc: dict[str, Any], tl: int) -> str:
    if tl in [int(x) for x in doc.get("primaryCalibrationTls", [])]:
        return "primary"
    if tl in [int(x) for x in doc.get("advancedValidationTls", [])]:
        return "advanced"
    return "endpoint_stress"


def _profiles_by_id(doc: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for key in ("missileProfiles", "kineticProfiles"):
        for row in doc.get(key, []):
            out[(str(row["family"]), str(row["id"]))] = row
    return out


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 120:
        errors.append("checkpoint")
    if int(doc.get("acceptedBaseline", 0)) != 119:
        errors.append("acceptedBaseline")
    if doc.get("damageModel") != DAMAGE_MODEL:
        errors.append("damageModel")
    if doc.get("internalDamageCriticalsSimulated") is not False:
        errors.append("internalDamageCriticalsSimulated")
    if doc.get("automaticPromotion") is not False:
        errors.append("automaticPromotion")
    if int(doc.get("trialsPerVariant", 0)) < 1 or int(doc.get("authoringTrialsPerVariant", 0)) < 1:
        errors.append("trialCounts")

    if [int(x) for x in doc.get("primaryCalibrationTls", [])] != [1, 2, 3, 4, 5, 6]:
        errors.append("primaryCalibrationTls")
    if [int(x) for x in doc.get("advancedValidationTls", [])] != [7]:
        errors.append("advancedValidationTls")
    if [int(x) for x in doc.get("endpointStressTls", [])] != [8, 9]:
        errors.append("endpointStressTls")
    for key in ("missileStudyTls", "kineticStudyTls", "energyReferenceTls"):
        if [int(x) for x in doc.get(key, [])] != list(range(1, 10)):
            errors.append(key)
    if doc.get("specialistPairingIds") or doc.get("adaptivePairingIds") or doc.get("specialistPairingIdsByTl") or doc.get("adaptivePairingIdsByTl"):
        errors.append("legacyPayloadMenuReintroduced")

    fixtures = doc.get("targetFixtures", [])
    fixture_ids = [str(x.get("id")) for x in fixtures]
    required_legal = {
        "energy-balanced-legal", "energy-defense-legal",
        "kinetic-balanced-legal", "kinetic-ew-legal",
        "missile-balanced-legal", "missile-defense-legal",
    }
    if not required_legal.issubset(set(fixture_ids)) or len(fixture_ids) != len(set(fixture_ids)):
        errors.append("targetFixtureSet")
    if "missile-defense-no-pds-control" not in fixture_ids or "armor-heavy-control" not in fixture_ids or "light-control" not in fixture_ids:
        errors.append("controlledFixtures")
    classes = {str(x.get("classification")) for x in fixtures}
    if not classes.issubset({"legal_build", "controlled_fixture"}):
        errors.append("targetFixtureClassification")
    pds_control = next((x for x in fixtures if x.get("id") == "missile-defense-no-pds-control"), None)
    if not pds_control or pds_control.get("baseFamily") != "Missile" or pds_control.get("baseArchetype") != "missile-defense" or pds_control.get("removePds") is not True:
        errors.append("pdsIsolationControl")

    profiles = _profiles_by_id(doc)
    mids = {pid for (fam, pid) in profiles if fam == "Missile"}
    kids = {pid for (fam, pid) in profiles if fam == "Kinetic"}
    if "gp-current" not in mids or "gp-current" not in kids:
        errors.append("references")
    required_gp = {"missile-gp-d4", "missile-gp-d6", "missile-gp-d7", "missile-gp-d8", "missile-gp-d9"}
    if not required_gp.issubset(mids):
        errors.append("gpYieldProfiles")
    required_k = {"kinetic-acc-plus5", "kinetic-acc-plus10", "kinetic-acc-plus15", "kinetic-damage-plus1", "kinetic-apen-plus1"}
    if not required_k.issubset(kids):
        errors.append("kineticSensitivityProfiles")

    for (fam, pid), row in profiles.items():
        if not row.get("studyTls"):
            errors.append(f"studyTls:{fam}:{pid}")
            continue
        packets = int(row.get("packets", 1))
        if packets < 1 or packets > 2:
            errors.append(f"packetCount:{fam}:{pid}")
        if fam == "Missile" and (pid == "gp-current" or pid.startswith("missile-gp-")):
            if pid != "gp-current":
                if int(row.get("spen", -1)) != 1 or int(row.get("apen", -1)) != 2:
                    errors.append(f"gpPenetrationDrift:{pid}")
                if int(row.get("packets", 1)) != 1 or int(row.get("guidanceDelta", 0)) != 0 or int(row.get("pdsInterceptPenaltyPp", 0)) != 0:
                    errors.append(f"gpSpecialistLeakage:{pid}")
        if fam == "Missile" and pid.startswith("sw-"):
            if int(row.get("packets", 0)) != 2:
                errors.append(f"swarmerNotTwoPacket:{pid}")
            if int(row.get("spen", -1)) != 0 or int(row.get("apen", -1)) != 0:
                errors.append(f"swarmerPenetrationLeakage:{pid}")
            if int(row.get("guidanceDelta", 0)) not in (0, 5, 10, 15):
                errors.append(f"swarmerAccuracyAxis:{pid}")
            if int(row.get("pdsInterceptPenaltyPp", 0)) not in (0, 5, 10, 15):
                errors.append(f"swarmerPdsAxis:{pid}")
            if 1 in [int(x) for x in row.get("studyTls", [])]:
                errors.append(f"swarmerBeforeTl2:{pid}")
        if fam == "Kinetic" and pid != "gp-current":
            deltas = {
                "accuracy": int(row.get("accuracyDelta", 0)),
                "damage": int(row.get("damageDelta", 0)),
                "spen": int(row.get("spenDelta", 0)),
                "apen": int(row.get("apenDelta", 0)),
            }
            if deltas["spen"] != 0 or int(row.get("packets", 1)) != 1 or row.get("orderedPackets"):
                errors.append(f"kineticKissLeakage:{pid}")
            nonzero = sum(v != 0 for v in deltas.values())
            if nonzero != 1:
                errors.append(f"kineticMultiAxis:{pid}")
            if pid.startswith("kinetic-acc-") and deltas["accuracy"] not in (5, 10, 15):
                errors.append(f"kineticAccAxis:{pid}")

    comparisons = doc.get("sensitivityComparisons", [])
    comp_ids = [str(x.get("id")) for x in comparisons]
    if len(comp_ids) != len(set(comp_ids)) or len(comparisons) < 20:
        errors.append("sensitivityComparisons")
    for c in comparisons:
        fam = str(c.get("family"))
        if (fam, str(c.get("baseline"))) not in profiles or (fam, str(c.get("comparison"))) not in profiles:
            errors.append(f"comparisonProfile:{c.get('id')}")
        if not c.get("tls"):
            errors.append(f"comparisonTls:{c.get('id')}")

    paths = doc.get("candidateProgressionPaths", [])
    path_ids = [str(x.get("id")) for x in paths]
    if len(path_ids) != len(set(path_ids)) or not {"gp-cp119-frontier", "gp-maturity-delayed", "gp-hybrid-early-fission-late-fusion", "kinetic-smart-plus5", "energy-native"}.issubset(set(path_ids)):
        errors.append("candidateProgressionPaths")
    for path in paths:
        fam = str(path.get("family"))
        mapping = path.get("profilesByTl", {})
        if sorted(int(k) for k in mapping.keys()) != list(range(1, 10)):
            errors.append(f"pathTLCoverage:{path.get('id')}")
            continue
        for tl, pid in mapping.items():
            if fam == "Energy":
                if pid != "energy-native":
                    errors.append(f"energyPath:{path.get('id')}:{tl}")
            elif (fam, str(pid)) not in profiles:
                errors.append(f"pathProfile:{path.get('id')}:{tl}:{pid}")
    return errors


def _profile_meta(repo: Path, doc: dict[str, Any], builds: list[Any]) -> dict[tuple[int, str, str], dict[str, Any]]:
    matrix = CandidateMatrix(repo)
    catalog = FamilyCatalog(doc)
    by_id = {b.id: b for b in builds}
    out: dict[tuple[int, str, str], dict[str, Any]] = {}
    for tl in range(1, 10):
        for fam, table, build_id in (
            ("Missile", catalog.missile, f"tl{tl}-missile-balanced"),
            ("Kinetic", catalog.kinetic, f"tl{tl}-kinetic-balanced"),
        ):
            b = by_id[build_id]
            base = _weapon(matrix, b)
            for pid, p in table.items():
                if tl not in p.study_tls:
                    continue
                eff = _effective_profile(base, p)
                out[(tl, fam, pid)] = {
                    "damage": int(eff["damage"]), "spen": int(eff["spen"]), "apen": int(eff["apen"]),
                    "accuracy_delta": int(p.accuracy_delta), "guidance_delta": int(p.guidance_delta),
                    "packets": int(eff["packets"]), "pds_penalty_pp": int(p.pds_intercept_penalty_pp),
                    "total_nominal_damage": int(eff["damage"]) * int(eff["packets"]),
                    "classification": str(next((r.get("classification", "") for r in doc.get("missileProfiles" if fam == "Missile" else "kineticProfiles", []) if r.get("id") == pid), "")),
                }
    return out


def _fixture_meta(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(x["id"]): x for x in doc.get("targetFixtures", [])}


def _summary_rows(rows: list[dict[str, Any]], doc: dict[str, Any], meta: dict[tuple[int, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    fixtures = _fixture_meta(doc)
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        fam = {"missile_family_characteristic": "Missile", "kinetic_family_characteristic": "Kinetic", "energy_family_reference": "Energy"}[r["scenario_group"]]
        grouped[(int(r["tl"]), fam, str(r["side_a_profile"]), str(r["target_fixture"]), str(r["side_a_archetype"]))].append(r)
    out: list[dict[str, Any]] = []
    for (tl, fam, profile, fixture, archetype), rs in sorted(grouped.items()):
        f = fixtures[fixture]
        direct_shots = statistics.fmean(float(x["mean_a_direct_shots"]) for x in rs)
        direct_hits = statistics.fmean(float(x["mean_a_direct_hits"]) for x in rs)
        missile_launches = statistics.fmean(float(x["mean_a_missile_launches"]) for x in rs)
        # Missile terminal guidance/hit telemetry is recorded on the target side;
        # launch telemetry remains on the attacking side.  Keep these paired
        # explicitly so guidance sensitivity cannot silently read the wrong ship.
        missile_guidance_attempts = statistics.fmean(float(x["mean_b_missile_guidance_attempts"]) for x in rs)
        missile_hits = statistics.fmean(float(x["mean_b_missile_hits"]) for x in rs)
        pds_attempts = statistics.fmean(float(x["mean_b_pds_attempts"]) for x in rs)
        pds_intercepts = statistics.fmean(float(x["mean_b_pds_intercepts"]) for x in rs)
        pm = meta.get((tl, fam, profile), {})
        out.append({
            "tl": tl, "priority": _priority(doc, tl), "attacker_family": fam, "profile": profile,
            "profile_classification": pm.get("classification", "reference" if fam == "Energy" else ""),
            "attacker_archetype": archetype, "target_fixture": fixture, "target_classification": f["classification"],
            "target_family": f["baseFamily"], "target_archetype": f["baseArchetype"], "variants": len(rs),
            "damage": pm.get("damage", "mode-driven" if fam == "Energy" else "native"),
            "spen": pm.get("spen", "native"), "apen": pm.get("apen", "native"),
            "packets": pm.get("packets", 1), "total_nominal_damage": pm.get("total_nominal_damage", "mode-driven" if fam == "Energy" else "native"),
            "accuracy_delta": pm.get("accuracy_delta", 0), "guidance_delta": pm.get("guidance_delta", 0), "pds_penalty_pp": pm.get("pds_penalty_pp", 0),
            "mean_conditional_win_rate": statistics.fmean(float(x["conditional_win_rate_a"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
            "mean_target_hull_damage": statistics.fmean(float(x["mean_b_hull_damage"]) for x in rs),
            "mean_target_armor_damage": statistics.fmean(float(x["mean_b_armor_integrity_damage"]) for x in rs),
            "mean_target_shield_absorbed": statistics.fmean(float(x["mean_b_shield_absorbed"]) for x in rs),
            "direct_hit_rate": direct_hits / direct_shots if direct_shots else 0.0,
            "missile_hit_per_launch": missile_hits / missile_launches if missile_launches else 0.0,
            "missile_hit_per_guidance_attempt": missile_hits / missile_guidance_attempts if missile_guidance_attempts else 0.0,
            "pds_intercept_per_attempt": pds_intercepts / pds_attempts if pds_attempts else 0.0,
            "mean_defender_pds_attempts": pds_attempts,
            "mean_defender_pds_intercepts": pds_intercepts,
        })
    return out


def _legal_average(rows: list[dict[str, Any]], *, family: str | None = None, profile: str | None = None, tl: int | None = None) -> list[dict[str, Any]]:
    out = [r for r in rows if r["target_classification"] == "legal_build"]
    if family is not None:
        out = [r for r in out if r["attacker_family"] == family]
    if profile is not None:
        out = [r for r in out if r["profile"] == profile]
    if tl is not None:
        out = [r for r in out if int(r["tl"]) == tl]
    return out


def _gp_yield_summary(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in summary:
        if r["attacker_family"] != "Missile" or r["target_classification"] != "legal_build":
            continue
        if r["profile"] != "gp-current" and not r["profile"].startswith("missile-gp-"):
            continue
        grouped[(int(r["tl"]), r["profile"])].append(r)
    raw = []
    for (tl, pid), rs in sorted(grouped.items()):
        damage = int(rs[0]["damage"])
        raw.append({
            "tl": tl, "priority": rs[0]["priority"], "profile": pid, "damage": damage,
            "spen": rs[0]["spen"], "apen": rs[0]["apen"], "summary_rows": len(rs),
            "mean_conditional_win_rate": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
            "mean_target_hull_damage": statistics.fmean(float(x["mean_target_hull_damage"]) for x in rs),
            "mean_target_shield_absorbed": statistics.fmean(float(x["mean_target_shield_absorbed"]) for x in rs),
        })
    by_tl: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for r in raw:
        by_tl[int(r["tl"])].append(r)
    out = []
    for tl in sorted(by_tl):
        prev = None
        for r in sorted(by_tl[tl], key=lambda x: (int(x["damage"]), x["profile"])):
            rr = dict(r)
            rr["delta_win_rate_vs_prev_damage"] = "" if prev is None else float(r["mean_conditional_win_rate"]) - float(prev["mean_conditional_win_rate"])
            rr["delta_hull_damage_vs_prev_damage"] = "" if prev is None else float(r["mean_target_hull_damage"]) - float(prev["mean_target_hull_damage"])
            rr["damage_step"] = "" if prev is None else int(r["damage"]) - int(prev["damage"])
            out.append(rr)
            prev = r
    return out


def _aggregate_profile(summary: list[dict[str, Any]], family: str, profile: str, tl: int, legal_only: bool = True) -> dict[str, float] | None:
    rs = [r for r in summary if int(r["tl"]) == tl and r["attacker_family"] == family and r["profile"] == profile and (not legal_only or r["target_classification"] == "legal_build")]
    if not rs:
        return None
    return {
        "win": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
        "unresolved": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
        "turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
        "hull": statistics.fmean(float(x["mean_target_hull_damage"]) for x in rs),
        "direct_hit": statistics.fmean(float(x["direct_hit_rate"]) for x in rs),
        "missile_hit": statistics.fmean(float(x["missile_hit_per_launch"]) for x in rs),
        "missile_guidance_hit": statistics.fmean(float(x["missile_hit_per_guidance_attempt"]) for x in rs),
        "pds_intercept": statistics.fmean(float(x["pds_intercept_per_attempt"]) for x in rs),
    }


def _sensitivity_deltas(summary: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in doc.get("sensitivityComparisons", []):
        family = str(c["family"])
        for tl in [int(x) for x in c.get("tls", [])]:
            b = _aggregate_profile(summary, family, str(c["baseline"]), tl, legal_only=True)
            q = _aggregate_profile(summary, family, str(c["comparison"]), tl, legal_only=True)
            if b is None or q is None:
                continue
            out.append({
                "comparison_id": c["id"], "family": family, "axis": c["axis"], "tl": tl, "priority": _priority(doc, tl),
                "baseline_profile": c["baseline"], "comparison_profile": c["comparison"], "scope": "legal_target_average",
                "delta_conditional_win_rate": q["win"] - b["win"],
                "delta_unresolved_rate": q["unresolved"] - b["unresolved"],
                "delta_mean_turns": q["turns"] - b["turns"],
                "delta_target_hull_damage": q["hull"] - b["hull"],
                "delta_direct_hit_rate": q["direct_hit"] - b["direct_hit"],
                "delta_missile_hit_per_launch": q["missile_hit"] - b["missile_hit"],
                "delta_missile_hit_per_guidance_attempt": q["missile_guidance_hit"] - b["missile_guidance_hit"],
                "delta_pds_intercept_per_attempt": q["pds_intercept"] - b["pds_intercept"],
            })
    return out


def _swarmer_profile_summary(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in summary:
        if r["attacker_family"] == "Missile" and r["profile"].startswith("sw-") and r["target_classification"] == "legal_build":
            grouped[(int(r["tl"]), r["profile"])].append(r)
    out = []
    for (tl, pid), rs in sorted(grouped.items()):
        out.append({
            "tl": tl, "priority": rs[0]["priority"], "profile": pid, "packet_damage": rs[0]["damage"], "packets": rs[0]["packets"],
            "total_nominal_damage": rs[0]["total_nominal_damage"], "guidance_delta": rs[0]["guidance_delta"], "pds_penalty_pp": rs[0]["pds_penalty_pp"],
            "mean_conditional_win_rate": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
            "mean_target_hull_damage": statistics.fmean(float(x["mean_target_hull_damage"]) for x in rs),
            "missile_hit_per_launch": statistics.fmean(float(x["missile_hit_per_launch"]) for x in rs),
            "missile_hit_per_guidance_attempt": statistics.fmean(float(x["missile_hit_per_guidance_attempt"]) for x in rs),
            "pds_intercept_per_attempt": statistics.fmean(float(x["pds_intercept_per_attempt"]) for x in rs),
        })
    return out


def _pds_isolation(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx = {(int(r["tl"]), r["attacker_family"], r["profile"], r["attacker_archetype"], r["target_fixture"]): r for r in summary}
    out = []
    profiles = sorted({(int(r["tl"]), r["profile"], r["attacker_archetype"]) for r in summary if r["attacker_family"] == "Missile"})
    for tl, pid, archetype in profiles:
        with_pds = idx.get((tl, "Missile", pid, archetype, "missile-defense-legal"))
        no_pds = idx.get((tl, "Missile", pid, archetype, "missile-defense-no-pds-control"))
        if not with_pds or not no_pds:
            continue
        out.append({
            "tl": tl, "priority": with_pds["priority"], "profile": pid, "attacker_archetype": archetype,
            "packets": with_pds["packets"], "packet_damage": with_pds["damage"], "guidance_delta": with_pds["guidance_delta"], "pds_penalty_pp": with_pds["pds_penalty_pp"],
            "with_pds_win_rate": with_pds["mean_conditional_win_rate"], "no_pds_win_rate": no_pds["mean_conditional_win_rate"],
            "pds_cost_to_attacker_win_rate": float(no_pds["mean_conditional_win_rate"]) - float(with_pds["mean_conditional_win_rate"]),
            "with_pds_missile_hit_per_launch": with_pds["missile_hit_per_launch"], "no_pds_missile_hit_per_launch": no_pds["missile_hit_per_launch"],
            "with_pds_missile_hit_per_guidance_attempt": with_pds["missile_hit_per_guidance_attempt"], "no_pds_missile_hit_per_guidance_attempt": no_pds["missile_hit_per_guidance_attempt"],
            "with_pds_intercept_per_attempt": with_pds["pds_intercept_per_attempt"],
            "with_pds_attempts": with_pds["mean_defender_pds_attempts"], "with_pds_intercepts": with_pds["mean_defender_pds_intercepts"],
        })
    return out


def _kinetic_summary(summary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = defaultdict(list)
    for r in summary:
        if r["attacker_family"] == "Kinetic" and r["target_classification"] == "legal_build":
            grouped[(int(r["tl"]), r["profile"])].append(r)
    out = []
    for (tl, pid), rs in sorted(grouped.items()):
        out.append({
            "tl": tl, "priority": rs[0]["priority"], "profile": pid, "accuracy_delta": rs[0]["accuracy_delta"],
            "damage": rs[0]["damage"], "spen": rs[0]["spen"], "apen": rs[0]["apen"],
            "mean_conditional_win_rate": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
            "direct_hit_rate": statistics.fmean(float(x["direct_hit_rate"]) for x in rs),
            "mean_target_hull_damage": statistics.fmean(float(x["mean_target_hull_damage"]) for x in rs),
        })
    return out


def _path_rows(summary: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in doc.get("candidateProgressionPaths", []):
        fam = str(path["family"])
        for tl in range(1, 10):
            pid = str(path["profilesByTl"][str(tl)])
            rs = [r for r in summary if int(r["tl"]) == tl and r["attacker_family"] == fam and r["profile"] == pid and r["target_classification"] == "legal_build"]
            if not rs:
                continue
            out.append({
                "path_id": path["id"], "family": fam, "tl": tl, "priority": _priority(doc, tl), "profile": pid,
                "mean_conditional_win_rate": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
                "mean_unresolved_rate": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
                "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
                "mean_target_hull_damage": statistics.fmean(float(x["mean_target_hull_damage"]) for x in rs),
            })
    return out


def _path_tier_summary(path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in path_rows:
        grouped[(r["path_id"], r["family"], r["priority"])].append(r)
    out = []
    for (pid, fam, priority), rs in sorted(grouped.items()):
        out.append({
            "path_id": pid, "family": fam, "priority": priority, "tls": ",".join(str(x["tl"]) for x in sorted(rs, key=lambda x: x["tl"])),
            "mean_conditional_win_rate": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
            "mean_unresolved_rate": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
            "mean_turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
        })
    return out


def _movement_rows(raw_rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = defaultdict(dict)
    for r in raw_rows:
        fam = {"missile_family_characteristic": "Missile", "kinetic_family_characteristic": "Kinetic", "energy_family_reference": "Energy"}[r["scenario_group"]]
        key = (int(r["tl"]), fam, r["side_a_profile"], r["side_a_archetype"], r["target_fixture"])
        grouped[key][r["movement_order"]] = r
    out = []
    for (tl, fam, pid, archetype, fixture), pair in sorted(grouped.items()):
        if "SideAFirst" not in pair or "SideBFirst" not in pair:
            continue
        a, b = pair["SideAFirst"], pair["SideBFirst"]
        out.append({
            "tl": tl, "priority": _priority(doc, tl), "family": fam, "profile": pid, "attacker_archetype": archetype, "target_fixture": fixture,
            "side_a_first_win_rate": float(a["conditional_win_rate_a"]), "side_b_first_win_rate": float(b["conditional_win_rate_a"]),
            "movement_order_swing_pp": abs(float(a["conditional_win_rate_a"]) - float(b["conditional_win_rate_a"])) * 100.0,
        })
    return out


def _profile_catalog_rows(repo: Path, doc: dict[str, Any], meta: dict[tuple[int, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [{
        "family": "Energy", "profile_id": "energy-native", "classification": "reference", "study_tls": "1,2,3,4,5,6,7,8,9",
        "role": "Native Energy reference; unchanged.", "damage": "mode-driven", "spen": "native", "apen": "native", "accuracy_delta": 0,
        "guidance_delta": 0, "packets": 1, "pds_intercept_penalty_pp": 0, "first_tl_effective_total_nominal_damage": "mode-driven",
    }]
    for key in ("missileProfiles", "kineticProfiles"):
        for p in doc.get(key, []):
            fam, pid = str(p["family"]), str(p["id"])
            first_tl = min(int(x) for x in p["studyTls"])
            m = meta[(first_tl, fam, pid)]
            rows.append({
                "family": fam, "profile_id": pid, "classification": p.get("classification", ""),
                "study_tls": ",".join(str(x) for x in p.get("studyTls", [])), "role": p.get("role", ""),
                "damage": p.get("damage", "native"), "spen": p.get("spen", "native"), "apen": p.get("apen", "native"),
                "accuracy_delta": p.get("accuracyDelta", 0), "guidance_delta": p.get("guidanceDelta", 0),
                "packets": p.get("packets", 1), "pds_intercept_penalty_pp": p.get("pdsInterceptPenaltyPp", 0),
                "first_tl_effective_total_nominal_damage": m["total_nominal_damage"],
            })
    return rows


def run_weapon_sensitivity_analysis(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 1) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("invalid CP120 study: " + ",".join(errors))
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
    meta = _profile_meta(repo, doc, builds)
    catalog = FamilyCatalog(doc)
    _write_csv(outdir / "target_fixtures.csv", _target_fixture_rows(CandidateMatrix(repo), catalog, doc, repo))
    _write_csv(outdir / "profile_catalog.csv", _profile_catalog_rows(repo, doc, meta))
    summary = _summary_rows(rows, doc, meta)
    gp = _gp_yield_summary(summary)
    sw = _swarmer_profile_summary(summary)
    sensitivity = _sensitivity_deltas(summary, doc)
    pds = _pds_isolation(summary)
    kinetic = _kinetic_summary(summary)
    paths = _path_rows(summary, doc)
    path_tiers = _path_tier_summary(paths)
    movement = _movement_rows(rows, doc)
    _write_csv(outdir / "integration_summary.csv", summary)
    _write_csv(outdir / "gp_yield_sensitivity.csv", gp)
    _write_csv(outdir / "swarmer_sensitivity.csv", sw)
    _write_csv(outdir / "sensitivity_delta_summary.csv", sensitivity)
    _write_csv(outdir / "pds_isolation_summary.csv", pds)
    _write_csv(outdir / "kinetic_sensitivity.csv", kinetic)
    _write_csv(outdir / "progression_path_summary.csv", paths)
    _write_csv(outdir / "progression_path_tier_summary.csv", path_tiers)
    _write_csv(outdir / "movement_order_summary.csv", movement)

    failures: list[str] = []
    if any(int(r["errors"]) for r in rows):
        failures.append("trial-errors")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("exact-fill-builds")
    if not any(r["scenario_group"] == "energy_family_reference" and float(r["mean_a_direct_shots"]) > 0 for r in rows):
        failures.append("energy-reference-telemetry")
    if not any(r["scenario_group"] == "kinetic_family_characteristic" and str(r["side_a_profile"]).startswith("kinetic-acc-") and float(r["mean_a_direct_shots"]) > 0 for r in rows):
        failures.append("kinetic-accuracy-telemetry")
    if not any(r["scenario_group"] == "missile_family_characteristic" and str(r["side_a_profile"]).startswith("missile-gp-") and float(r["mean_a_missile_launches"]) > 0 for r in rows):
        failures.append("gp-yield-telemetry")
    if not any(r["scenario_group"] == "missile_family_characteristic" and str(r["side_a_profile"]).startswith("sw-") and float(r["mean_b_pds_attempts"]) > 0 for r in rows):
        failures.append("swarmer-pds-telemetry")
    if not pds:
        failures.append("pds-isolation-output")
    if not sensitivity:
        failures.append("sensitivity-delta-output")
    if not gp or not kinetic or not sw:
        failures.append("sensitivity-summary-output")

    counts = defaultdict(int)
    priorities = defaultdict(int)
    for v in variants:
        counts[v.scenario_group] += 1
        priorities[_priority(doc, v.tl)] += 1
    if priorities["primary"] <= priorities["advanced"] + priorities["endpoint_stress"]:
        failures.append("primary-not-dominant")
    max_primary_swing = max((float(r["movement_order_swing_pp"]) for r in movement if r["priority"] == "primary" and _fixture_meta(doc)[r["target_fixture"]]["classification"] == "legal_build"), default=0.0)
    result = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 120,
        "acceptedBaseline": 119,
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
        "controlledFixtureCount": sum(1 for x in doc["targetFixtures"] if x["classification"] == "controlled_fixture"),
        "missileProfileCount": len(catalog.missile),
        "kineticProfileCount": len(catalog.kinetic),
        "energyReferenceProfileCount": 1,
        "sensitivityComparisonCount": len(doc.get("sensitivityComparisons", [])),
        "candidateProgressionPathCount": len(doc.get("candidateProgressionPaths", [])),
        "primaryCalibrationTls": doc["primaryCalibrationTls"],
        "advancedValidationTls": doc["advancedValidationTls"],
        "endpointStressTls": doc["endpointStressTls"],
        "maxPrimaryLegalMovementOrderSwingPp": max_primary_swing,
        "interpretation": "CP120 maps numerical sensitivities around the simplified weapon architecture without reopening mechanical design. GP Missile profiles vary yield only; Swarmer remains exactly two packets with bounded coverage/PDS axes; Kinetic profiles are automatic single-axis controls. TL1-TL6 dominate inference. Outcome magnitudes are review evidence only and never automatic promotion gates.",
    }
    (outdir / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
