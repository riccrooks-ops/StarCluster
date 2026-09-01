from __future__ import annotations

import copy
import csv
import json
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import fields
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

from .ecology import CandidateMatrix, DAMAGE_MODEL, SideTelemetry, _shield_armor, _weapon
from .study import load_json
from .weapon_family_analysis import (
    FamilyCatalog,
    FamilyVariant,
    _effective_profile,
    _target_fixture_rows,
    _write_csv,
    build_variants,
    run_family_trial,
)
from .weapon_sensitivity_analysis import _summary_rows

SCHEMA = "star-cluster-damage-resolution-scale-study-v0.1"
RESULT_SCHEMA = "star-cluster-damage-resolution-scale-results-v0.1"

# Telemetry expressed in the damage/defense point domain.  Every one of these
# must scale exactly with the candidate integer resolution in an equivalence run.
DAMAGE_TELEMETRY_FIELDS = {
    "shield_base_restored",
    "shield_tactical_restored",
    "raw_damage_on_hit",
    "shield_armor_prevented",
    "shield_absorbed",
    "armor_prevented",
    "armor_integrity_damage",
    "armor_protection_damage",
    "hull_damage",
    "direct_raw_damage",
    "direct_hull_damage",
    "missile_raw_damage",
    "missile_hull_damage",
    "payload_shield_bonus_damage",
    "shield_recharge_suppressed",
    "shield_penetration_bypassed",
    "armor_penetration_bypassed",
    "damage_control_hull_restored",
}

MATRIX_DAMAGE_FIELDS: dict[str, tuple[str, ...]] = {
    "hull": ("hullPoints",),
    "armor": ("ap", "ai"),
    "shield": ("capacity", "baseRecharge", "tacticalRechargePerTp", "shieldArmor"),
    "kinetic_main": ("damage", "spen", "apen"),
    "energy_main": ("lowDamage", "standardDamage", "highDamage", "spen", "apen"),
    "missile_delivery": ("warheadDamage", "spen", "apen"),
}

PROFILE_DAMAGE_FIELDS = (
    "damage",
    "damageDelta",
    "spen",
    "spenDelta",
    "apen",
    "apenDelta",
    "shieldBonusDamage",
    "shieldArmorReduction",
    "rechargeSuppression",
)

FIXTURE_DAMAGE_FIELDS = (
    "armorProtectionDelta",
    "armorIntegrityDelta",
    "armorProtectionOverride",
    "armorIntegrityOverride",
    "shieldCapacityDelta",
    "shieldRechargeBonus",
    "hullDelta",
)


class DamageScaledMatrix(CandidateMatrix):
    """Research-only proxy that increases integer resolution without changing design ratios."""

    def __init__(self, repo: Path, scale: int):
        if scale < 1:
            raise ValueError("damage scale must be >= 1")
        super().__init__(repo)
        self.damage_scale = int(scale)
        if self.damage_scale == 1:
            return
        self.doc = copy.deepcopy(self.doc)
        self.profiles = self.doc["profiles"]
        self.branches = {row["id"]: row for row in self.doc["branches"]}
        for family, names in MATRIX_DAMAGE_FIELDS.items():
            for row in self.profiles.get(family, {}).values():
                for name in names:
                    if row.get(name) is not None:
                        row[name] = int(row[name]) * self.damage_scale


def scale_family_study_doc(doc: dict[str, Any], scale: int) -> dict[str, Any]:
    """Return a deep scaled copy of an existing family study document."""
    if scale < 1:
        raise ValueError("damage scale must be >= 1")
    out = copy.deepcopy(doc)
    if scale == 1:
        return out
    for key in ("missileProfiles", "kineticProfiles"):
        for row in out.get(key, []):
            for name in PROFILE_DAMAGE_FIELDS:
                if row.get(name) is not None:
                    row[name] = int(row[name]) * scale
            for packet in row.get("orderedPackets", []):
                for name in ("damage", "spen", "apen"):
                    if packet.get(name) is not None:
                        packet[name] = int(packet[name]) * scale
    for row in out.get("targetFixtures", []):
        for name in FIXTURE_DAMAGE_FIELDS:
            if row.get(name) is not None:
                row[name] = int(row[name]) * scale
    return out


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 121:
        errors.append("checkpoint")
    if int(doc.get("acceptedBaseline", 0)) != 119:
        errors.append("acceptedBaseline")
    if int(doc.get("supersedesCandidate", 0)) != 120:
        errors.append("supersedesCandidate")
    if doc.get("damageModel") != DAMAGE_MODEL:
        errors.append("damageModel")
    if doc.get("internalDamageCriticalsSimulated") is not False:
        errors.append("internalDamageCriticalsSimulated")
    if doc.get("automaticPromotion") is not False:
        errors.append("automaticPromotion")
    if int(doc.get("damageScale", 0)) != 2:
        errors.append("damageScale")
    if int(doc.get("equivalenceTrialsPerVariant", 0)) < 1:
        errors.append("equivalenceTrialsPerVariant")
    if int(doc.get("authoringEquivalenceTrialsPerVariant", 0)) < 1:
        errors.append("authoringEquivalenceTrialsPerVariant")
    if int(doc.get("trialsPerVariant", 0)) < 1 or int(doc.get("authoringTrialsPerVariant", 0)) < 1:
        errors.append("trialCounts")
    if [int(x) for x in doc.get("primaryCalibrationTls", [])] != [2, 3, 4, 5, 6]:
        errors.append("primaryCalibrationTls")
    if [int(x) for x in doc.get("advancedValidationTls", [])] != [7]:
        errors.append("advancedValidationTls")
    if [int(x) for x in doc.get("endpointStressTls", [])] != [8, 9]:
        errors.append("endpointStressTls")
    if not doc.get("equivalenceSourceStudy"):
        errors.append("equivalenceSourceStudy")

    fixture_ids = [str(x.get("id")) for x in doc.get("targetFixtures", [])]
    if len(fixture_ids) != len(set(fixture_ids)):
        errors.append("duplicateTargetFixtures")
    offense = set(str(x) for x in doc.get("offenseFixtureIds", []))
    controls = set(str(x) for x in doc.get("defensePerturbationFixtureIds", []))
    if not offense or not controls or not offense.issubset(set(fixture_ids)) or not controls.issubset(set(fixture_ids)):
        errors.append("fixturePartitions")
    for fid in offense:
        row = next((x for x in doc.get("targetFixtures", []) if str(x.get("id")) == fid), None)
        if not row or row.get("classification") != "legal_build":
            errors.append(f"offenseFixtureClassification:{fid}")
    for fid in controls:
        row = next((x for x in doc.get("targetFixtures", []) if str(x.get("id")) == fid), None)
        if not row or row.get("classification") != "controlled_fixture":
            errors.append(f"defenseFixtureClassification:{fid}")

    missile = {str(x.get("id")): x for x in doc.get("missileProfiles", [])}
    kinetic = {str(x.get("id")): x for x in doc.get("kineticProfiles", [])}
    if "gp-current" not in missile or "gp-current" not in kinetic:
        errors.append("references")
    # Half-step offense probes must actually exercise odd scaled-domain values.
    odd_damage = [int(x["damage"]) for x in doc.get("missileProfiles", []) if x.get("damage") is not None and int(x["damage"]) % 2 == 1]
    odd_kinetic = [int(x.get("damageDelta", 0)) for x in doc.get("kineticProfiles", []) if int(x.get("damageDelta", 0)) % 2 == 1]
    if not odd_damage or not odd_kinetic:
        errors.append("oddHalfStepOffenseMissing")
    if not any(any(int(row.get(k, 0) or 0) % 2 == 1 for k in FIXTURE_DAMAGE_FIELDS) for row in doc.get("targetFixtures", []) if row.get("classification") == "controlled_fixture"):
        errors.append("oddHalfStepDefenseMissing")

    known = {"Missile": set(missile), "Kinetic": set(kinetic), "Energy": {"energy-native"}}
    for series in doc.get("offenseSeries", []):
        fam = str(series.get("family"))
        profiles = [str(x) for x in series.get("profiles", [])]
        if fam not in known or len(profiles) != 3 or any(p not in known[fam] for p in profiles):
            errors.append(f"offenseSeries:{series.get('id')}")
        if not series.get("tls"):
            errors.append(f"offenseSeriesTls:{series.get('id')}")
    for series in doc.get("defenseSeries", []):
        ids = [str(series.get(k, "")) for k in ("baselineFixture", "halfFixture", "fullFixture")]
        if any(x not in fixture_ids for x in ids) or len(set(ids)) != 3:
            errors.append(f"defenseSeries:{series.get('id')}")
        if not series.get("tls"):
            errors.append(f"defenseSeriesTls:{series.get('id')}")

    refs = doc.get("defenseReferenceProfiles", {})
    if refs != {"Missile": "gp-current", "Kinetic": "gp-current", "Energy": "energy-native"}:
        errors.append("defenseReferenceProfiles")
    if str(doc.get("defenseReferenceAttackerArchetype")) != "balanced":
        errors.append("defenseReferenceAttackerArchetype")
    if doc.get("specialistPairingIds") or doc.get("adaptivePairingIds"):
        errors.append("specialistMenuReintroduced")
    return errors


def _priority(doc: dict[str, Any], tl: int) -> str:
    if tl in [int(x) for x in doc.get("primaryCalibrationTls", [])]:
        return "primary"
    if tl in [int(x) for x in doc.get("advancedValidationTls", [])]:
        return "advanced"
    return "endpoint_stress"


def _filter_halfstep_variants(doc: dict[str, Any], variants: list[FamilyVariant]) -> list[FamilyVariant]:
    offense = set(str(x) for x in doc["offenseFixtureIds"])
    controls = set(str(x) for x in doc["defensePerturbationFixtureIds"])
    refs = {str(k): str(v) for k, v in doc["defenseReferenceProfiles"].items()}
    archetype = str(doc["defenseReferenceAttackerArchetype"])
    out: list[FamilyVariant] = []
    for v in variants:
        family = {"missile_family_characteristic": "Missile", "kinetic_family_characteristic": "Kinetic", "energy_family_reference": "Energy"}[v.scenario_group]
        if v.target_fixture in offense:
            out.append(v)
            continue
        if v.target_fixture in controls and v.side_a.archetype == archetype and v.side_a_profile == refs[family]:
            out.append(v)
    out.sort(key=lambda x: x.id)
    return out


def build_halfstep_variants(repo: Path, doc: dict[str, Any]) -> tuple[list[Any], list[FamilyVariant]]:
    builds, variants = build_variants(repo, doc)
    return builds, _filter_halfstep_variants(doc, variants)


_EQ_LEGACY_MATRIX: CandidateMatrix | None = None
_EQ_SCALED_MATRIX: DamageScaledMatrix | None = None
_EQ_LEGACY_CATALOG: FamilyCatalog | None = None
_EQ_SCALED_CATALOG: FamilyCatalog | None = None
_EQ_SCALE = 2


def _init_equivalence_worker(repo: str, source_doc: dict[str, Any], scale: int) -> None:
    global _EQ_LEGACY_MATRIX, _EQ_SCALED_MATRIX, _EQ_LEGACY_CATALOG, _EQ_SCALED_CATALOG, _EQ_SCALE
    root = Path(repo)
    _EQ_LEGACY_MATRIX = CandidateMatrix(root)
    _EQ_SCALED_MATRIX = DamageScaledMatrix(root, scale)
    _EQ_LEGACY_CATALOG = FamilyCatalog(source_doc)
    _EQ_SCALED_CATALOG = FamilyCatalog(scale_family_study_doc(source_doc, scale))
    _EQ_SCALE = scale


def _telemetry_mismatches(legacy: SideTelemetry, scaled: SideTelemetry, scale: int, prefix: str) -> list[str]:
    out: list[str] = []
    for f in fields(SideTelemetry):
        lv = int(getattr(legacy, f.name))
        sv = int(getattr(scaled, f.name))
        expected = lv * scale if f.name in DAMAGE_TELEMETRY_FIELDS else lv
        if sv != expected:
            out.append(f"{prefix}.{f.name}:{lv}->{sv},expected={expected}")
    return out


def _compare_trial(legacy: Any, scaled: Any, scale: int) -> list[str]:
    out: list[str] = []
    for name in ("winner", "unresolved", "turns", "error"):
        if getattr(legacy, name) != getattr(scaled, name):
            out.append(f"{name}:{getattr(legacy, name)!r}->{getattr(scaled, name)!r}")
    for name in ("hull_a", "hull_b", "armor_a", "armor_b", "shield_a", "shield_b"):
        lv = int(getattr(legacy, name))
        sv = int(getattr(scaled, name))
        if sv != lv * scale:
            out.append(f"{name}:{lv}->{sv},expected={lv * scale}")
    out.extend(_telemetry_mismatches(legacy.side_a, scaled.side_a, scale, "side_a"))
    out.extend(_telemetry_mismatches(legacy.side_b, scaled.side_b, scale, "side_b"))
    return out


def _equivalence_task(args: tuple[FamilyVariant, int, int]) -> dict[str, Any]:
    variant, master_seed, trials = args
    assert _EQ_LEGACY_MATRIX is not None and _EQ_SCALED_MATRIX is not None
    assert _EQ_LEGACY_CATALOG is not None and _EQ_SCALED_CATALOG is not None
    mismatches = 0
    first: list[str] = []
    first_trial = -1
    for trial in range(trials):
        legacy = run_family_trial(_EQ_LEGACY_MATRIX, _EQ_LEGACY_CATALOG, variant, master_seed, trial)
        scaled = run_family_trial(_EQ_SCALED_MATRIX, _EQ_SCALED_CATALOG, variant, master_seed, trial)
        diff = _compare_trial(legacy, scaled, _EQ_SCALE)
        if diff:
            mismatches += 1
            if not first:
                first = diff[:12]
                first_trial = trial
    return {
        "variant_id": variant.id,
        "tl": variant.tl,
        "scenario_group": variant.scenario_group,
        "target_fixture": variant.target_fixture,
        "side_a_profile": variant.side_a_profile,
        "movement_order": variant.movement_order,
        "paired_trials": trials,
        "mismatched_trials": mismatches,
        "first_mismatch_trial": first_trial,
        "first_mismatch": " | ".join(first),
    }


def run_equivalence(repo: Path, source_doc: dict[str, Any], scale: int, trials: int, jobs: int) -> tuple[list[dict[str, Any]], float]:
    _, variants = build_variants(repo, source_doc)
    jobs = max(1, min(int(jobs), len(variants)))
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if jobs == 1:
        _init_equivalence_worker(str(repo), source_doc, scale)
        rows = [_equivalence_task((v, int(source_doc["masterSeed"]), trials)) for v in variants]
    else:
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_init_equivalence_worker, initargs=(str(repo), source_doc, scale)) as ex:
            futures = [ex.submit(_equivalence_task, (v, int(source_doc["masterSeed"]), trials)) for v in variants]
            for fut in as_completed(futures):
                rows.append(fut.result())
    rows.sort(key=lambda x: x["variant_id"])
    return rows, time.perf_counter() - start


_HS_MATRIX: DamageScaledMatrix | None = None
_HS_CATALOG: FamilyCatalog | None = None


def _init_halfstep_worker(repo: str, doc: dict[str, Any]) -> None:
    global _HS_MATRIX, _HS_CATALOG
    root = Path(repo)
    _HS_MATRIX = DamageScaledMatrix(root, int(doc["damageScale"]))
    _HS_CATALOG = FamilyCatalog(doc)


def _aggregate_trial_results(v: FamilyVariant, results: list[Any]) -> dict[str, Any]:
    # Keep the exact raw-column contract used by weapon_family_analysis._aggregate
    # without reaching into its process-global worker state.
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
            vals = [getattr(r.side_a if side == "a" else r.side_b, f.name) for r in valid]
            row[f"mean_{side}_{f.name}"] = statistics.fmean(vals) if vals else 0.0
    return row


def _halfstep_task(args: tuple[FamilyVariant, int, int]) -> dict[str, Any]:
    variant, master_seed, trials = args
    assert _HS_MATRIX is not None and _HS_CATALOG is not None
    return _aggregate_trial_results(variant, [run_family_trial(_HS_MATRIX, _HS_CATALOG, variant, master_seed, i) for i in range(trials)])


def execute_halfstep(repo: Path, doc: dict[str, Any], variants: list[FamilyVariant], trials: int, jobs: int) -> tuple[list[dict[str, Any]], float]:
    jobs = max(1, min(int(jobs), len(variants)))
    start = time.perf_counter()
    rows: list[dict[str, Any]] = []
    if jobs == 1:
        _init_halfstep_worker(str(repo), doc)
        rows = [_halfstep_task((v, int(doc["masterSeed"]), trials)) for v in variants]
    else:
        chunks = [[] for _ in range(min(len(variants), max(jobs, jobs * 4)))]
        for i, variant in enumerate(variants):
            chunks[i % len(chunks)].append(variant)

        def task_chunk(vs: list[FamilyVariant]) -> list[dict[str, Any]]:
            return [_halfstep_task((v, int(doc["masterSeed"]), trials)) for v in vs]

        # Local nested functions are not spawn-picklable; submit one variant per
        # future instead. Variant count is intentionally bounded (~2k).
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_init_halfstep_worker, initargs=(str(repo), doc)) as ex:
            futures = [ex.submit(_halfstep_task, (v, int(doc["masterSeed"]), trials)) for v in variants]
            for fut in as_completed(futures):
                rows.append(fut.result())
    rows.sort(key=lambda x: x["variant_id"])
    return rows, time.perf_counter() - start


def _profile_meta_scaled(repo: Path, doc: dict[str, Any], builds: list[Any]) -> dict[tuple[int, str, str], dict[str, Any]]:
    matrix = DamageScaledMatrix(repo, int(doc["damageScale"]))
    catalog = FamilyCatalog(doc)
    by_id = {b.id: b for b in builds}
    out: dict[tuple[int, str, str], dict[str, Any]] = {}
    for tl in sorted(set(int(x) for x in doc["missileStudyTls"] + doc["kineticStudyTls"])):
        for fam, table, build_id in (
            ("Missile", catalog.missile, f"tl{tl}-missile-balanced"),
            ("Kinetic", catalog.kinetic, f"tl{tl}-kinetic-balanced"),
        ):
            if build_id not in by_id:
                continue
            base = _weapon(matrix, by_id[build_id])
            source_rows = doc["missileProfiles" if fam == "Missile" else "kineticProfiles"]
            class_by = {str(x["id"]): str(x.get("classification", "")) for x in source_rows}
            for pid, profile in table.items():
                if tl not in profile.study_tls:
                    continue
                eff = _effective_profile(base, profile)
                out[(tl, fam, pid)] = {
                    "damage": int(eff["damage"]),
                    "spen": int(eff["spen"]),
                    "apen": int(eff["apen"]),
                    "accuracy_delta": int(profile.accuracy_delta),
                    "guidance_delta": int(profile.guidance_delta),
                    "packets": int(eff["packets"]),
                    "pds_penalty_pp": int(profile.pds_intercept_penalty_pp),
                    "total_nominal_damage": int(eff["damage"]) * int(eff["packets"]),
                    "classification": class_by.get(pid, ""),
                }
    return out


def _aggregate_summary(summary: list[dict[str, Any]], family: str, profile: str, tl: int) -> dict[str, float] | None:
    rs = [r for r in summary if int(r["tl"]) == tl and r["attacker_family"] == family and r["profile"] == profile and r["target_classification"] == "legal_build"]
    if not rs:
        return None
    return {
        "win": statistics.fmean(float(x["mean_conditional_win_rate"]) for x in rs),
        "unresolved": statistics.fmean(float(x["mean_unresolved_rate"]) for x in rs),
        "turns": statistics.fmean(float(x["mean_turns"]) for x in rs),
        "hull": statistics.fmean(float(x["mean_target_hull_damage"]) for x in rs),
        "missile_guidance_hit": statistics.fmean(float(x["missile_hit_per_guidance_attempt"]) for x in rs),
        "pds": statistics.fmean(float(x["pds_intercept_per_attempt"]) for x in rs),
        "direct_hit": statistics.fmean(float(x["direct_hit_rate"]) for x in rs),
    }


def _offense_series_rows(summary: list[dict[str, Any]], doc: dict[str, Any], meta: dict[tuple[int, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    scale = int(doc["damageScale"])
    for series in doc.get("offenseSeries", []):
        fam = str(series["family"])
        p0, p1, p2 = [str(x) for x in series["profiles"]]
        for tl in [int(x) for x in series["tls"]]:
            vals = [_aggregate_summary(summary, fam, p, tl) for p in (p0, p1, p2)]
            if any(v is None for v in vals):
                continue
            a, b, c = vals  # type: ignore[misc]
            d1 = float(b["win"]) - float(a["win"])
            d2 = float(c["win"]) - float(b["win"])
            full = float(c["win"]) - float(a["win"])
            m0 = meta.get((tl, fam, p0), {})
            m1 = meta.get((tl, fam, p1), {})
            m2 = meta.get((tl, fam, p2), {})
            out.append({
                "series_id": series["id"],
                "axis": series["axis"],
                "family": fam,
                "tl": tl,
                "priority": _priority(doc, tl),
                "low_profile": p0,
                "half_profile": p1,
                "full_profile": p2,
                "low_damage_scaled": m0.get("damage", "mode-driven"),
                "half_damage_scaled": m1.get("damage", "mode-driven"),
                "full_damage_scaled": m2.get("damage", "mode-driven"),
                "low_damage_legacy_equivalent": (float(m0["damage"]) / scale if isinstance(m0.get("damage"), int) else ""),
                "half_damage_legacy_equivalent": (float(m1["damage"]) / scale if isinstance(m1.get("damage"), int) else ""),
                "full_damage_legacy_equivalent": (float(m2["damage"]) / scale if isinstance(m2.get("damage"), int) else ""),
                "low_win_rate": a["win"],
                "half_win_rate": b["win"],
                "full_win_rate": c["win"],
                "first_half_delta_pp": d1 * 100.0,
                "second_half_delta_pp": d2 * 100.0,
                "full_step_delta_pp": full * 100.0,
                "first_half_share_of_full": (d1 / full if abs(full) > 1e-12 else ""),
                "max_half_step_pp": max(abs(d1), abs(d2)) * 100.0,
                "delta_target_hull_first_half_scaled": float(b["hull"]) - float(a["hull"]),
                "delta_target_hull_second_half_scaled": float(c["hull"]) - float(b["hull"]),
                "delta_missile_guidance_hit_first_half": float(b["missile_guidance_hit"]) - float(a["missile_guidance_hit"]),
                "delta_direct_hit_first_half": float(b["direct_hit"]) - float(a["direct_hit"]),
            })
    return out


def _summary_index(summary: list[dict[str, Any]]) -> dict[tuple[int, str, str, str, str], dict[str, Any]]:
    return {(int(r["tl"]), str(r["attacker_family"]), str(r["profile"]), str(r["attacker_archetype"]), str(r["target_fixture"])): r for r in summary}


def _defense_series_rows(summary: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    idx = _summary_index(summary)
    out: list[dict[str, Any]] = []
    archetype = str(doc["defenseReferenceAttackerArchetype"])
    refs = {str(k): str(v) for k, v in doc["defenseReferenceProfiles"].items()}
    for series in doc.get("defenseSeries", []):
        base = str(series["baselineFixture"])
        half = str(series["halfFixture"])
        full = str(series["fullFixture"])
        for tl in [int(x) for x in series["tls"]]:
            for fam in ("Energy", "Kinetic", "Missile"):
                profile = refs[fam]
                rows = [idx.get((tl, fam, profile, archetype, fid)) for fid in (base, half, full)]
                if any(r is None for r in rows):
                    continue
                a, b, c = rows  # type: ignore[misc]
                wa = float(a["mean_conditional_win_rate"])
                wb = float(b["mean_conditional_win_rate"])
                wc = float(c["mean_conditional_win_rate"])
                d1 = wb - wa
                d2 = wc - wb
                total = wc - wa
                out.append({
                    "series_id": series["id"],
                    "axis": series["axis"],
                    "attacker_family": fam,
                    "tl": tl,
                    "priority": _priority(doc, tl),
                    "profile": profile,
                    "baseline_fixture": base,
                    "half_fixture": half,
                    "full_fixture": full,
                    "baseline_attacker_win_rate": wa,
                    "half_attacker_win_rate": wb,
                    "full_attacker_win_rate": wc,
                    "first_half_delta_pp": d1 * 100.0,
                    "second_half_delta_pp": d2 * 100.0,
                    "full_step_delta_pp": total * 100.0,
                    "first_half_share_of_full": (d1 / total if abs(total) > 1e-12 else ""),
                    "max_half_step_pp": max(abs(d1), abs(d2)) * 100.0,
                    "baseline_target_hull_damage_scaled": float(a["mean_target_hull_damage"]),
                    "half_target_hull_damage_scaled": float(b["mean_target_hull_damage"]),
                    "full_target_hull_damage_scaled": float(c["mean_target_hull_damage"]),
                })
    return out


def _equivalence_overview(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_pairs = sum(int(r["paired_trials"]) for r in rows)
    mismatched = sum(int(r["mismatched_trials"]) for r in rows)
    variants_bad = sum(int(r["mismatched_trials"]) > 0 for r in rows)
    return {
        "variants": len(rows),
        "pairedTrials": total_pairs,
        "mismatchedTrials": mismatched,
        "variantsWithMismatch": variants_bad,
        "exact": mismatched == 0,
    }


def _normalized_target_rows(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    scale = int(doc["damageScale"])
    matrix = DamageScaledMatrix(repo, scale)
    catalog = FamilyCatalog(doc)
    rows = _target_fixture_rows(matrix, catalog, doc, repo)
    for r in rows:
        for name in ("initial_shield", "shield_base_recharge", "armor_protection", "armor_integrity", "hull"):
            r[f"{name}_legacy_equivalent"] = float(r[name]) / scale
    return rows


def _packet_resolution_surface(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic static surface proving odd values occupy real layer states."""
    from .ecology import _apply_damage, _create_side
    from .weapon_family_analysis import _apply_fixture_state

    scale = int(doc["damageScale"])
    matrix = DamageScaledMatrix(repo, scale)
    catalog = FamilyCatalog(doc)
    builds, _ = build_halfstep_variants(repo, doc)
    by = {b.id: b for b in builds}
    rows: list[dict[str, Any]] = []
    # Representative primary/advanced TLs and all three defensive layers.
    for tl in (3, 4, 5, 6, 7):
        fixture = catalog.fixtures["energy-defense-legal"]
        base = by[f"tl{tl}-energy-defense-specialist"]
        for damage in range(8, 19):
            for spen, apen in ((2, 4), (3, 4), (2, 5)):
                side = _create_side(matrix, base, 0)
                _apply_fixture_state(side, fixture)
                start = (side.shield, side.armor_integrity, side.armor_protection, side.hull)
                res = _apply_damage(side, damage, spen, apen, _shield_armor(matrix, side, side.build.shield_hardener), "direct")
                rows.append({
                    "tl": tl,
                    "damage_scaled": damage,
                    "damage_legacy_equivalent": damage / scale,
                    "spen_scaled": spen,
                    "spen_legacy_equivalent": spen / scale,
                    "apen_scaled": apen,
                    "apen_legacy_equivalent": apen / scale,
                    "start_shield": start[0],
                    "start_ai": start[1],
                    "start_ap": start[2],
                    "start_hull": start[3],
                    "shield_armor_prevented": res["shield_armor_prevented"],
                    "shield_absorbed": res["shield_absorbed"],
                    "armor_prevented": res["armor_prevented"],
                    "armor_integrity_damage": res["armor_integrity"],
                    "armor_protection_damage": res["armor_protection"],
                    "hull_damage": res["hull"],
                })
    return rows


def run_damage_resolution_analysis(
    repo: Path,
    study_path: Path,
    outdir: Path,
    trials_override: int | None = None,
    equivalence_trials_override: int | None = None,
    jobs: int = 1,
) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("invalid CP121 damage-resolution study: " + ",".join(errors))
    source_doc = load_json(repo / str(doc["equivalenceSourceStudy"]))
    scale = int(doc["damageScale"])
    eq_trials = int(equivalence_trials_override or doc["equivalenceTrialsPerVariant"])
    trials = int(trials_override or doc["trialsPerVariant"])

    equivalence_rows, eq_elapsed = run_equivalence(repo, source_doc, scale, eq_trials, jobs)
    builds, variants = build_halfstep_variants(repo, doc)
    rows, elapsed = execute_halfstep(repo, doc, variants, trials, jobs)
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "equivalence_variants.csv", equivalence_rows)
    _write_csv(outdir / "variants.csv", rows)
    _write_csv(outdir / "builds.csv", [{
        "build_id": b.id,
        "tl": b.tl,
        "family": b.weapon_family,
        "archetype": b.archetype,
        "combat_space": b.combat_space,
        "mission_aux_space": b.mission_aux_space,
        "capacity": b.capacity,
        "used_space": b.used_space,
        "free_space": b.capacity - b.used_space,
    } for b in builds])

    meta = _profile_meta_scaled(repo, doc, builds)
    summary = _summary_rows(rows, doc, meta)
    offense = _offense_series_rows(summary, doc, meta)
    defense = _defense_series_rows(summary, doc)
    target_rows = _normalized_target_rows(repo, doc)
    surface = _packet_resolution_surface(repo, doc)
    _write_csv(outdir / "integration_summary.csv", summary)
    _write_csv(outdir / "offense_halfstep_summary.csv", offense)
    _write_csv(outdir / "defense_halfstep_summary.csv", defense)
    _write_csv(outdir / "target_fixtures.csv", target_rows)
    _write_csv(outdir / "packet_resolution_surface.csv", surface)

    eq = _equivalence_overview(equivalence_rows)
    trial_errors = sum(int(r["errors"]) for r in rows)
    counts: dict[str, int] = defaultdict(int)
    priorities: dict[str, int] = defaultdict(int)
    for v in variants:
        counts[v.scenario_group] += 1
        priorities[_priority(doc, v.tl)] += 1
    failures: list[str] = []
    if not eq["exact"]:
        failures.append("x2-equivalence-mismatch")
    if trial_errors:
        failures.append("trial-errors")
    if not offense:
        failures.append("offense-halfstep-output")
    if not defense:
        failures.append("defense-halfstep-output")
    if not surface or not any(int(r["damage_scaled"]) % 2 == 1 for r in surface):
        failures.append("odd-packet-surface")
    if any(b.used_space != b.capacity for b in builds):
        failures.append("exact-fill-builds")
    if priorities.get("primary", 0) <= priorities.get("advanced", 0):
        failures.append("primary-not-dominant")

    result = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 121,
        "acceptedBaseline": 119,
        "supersedesCandidate": 120,
        "damageModel": DAMAGE_MODEL,
        "internalDamageCriticalsSimulated": False,
        "damageScale": scale,
        "legacyEquivalentResolutionPerPoint": 1.0 / scale,
        "equivalenceTrialsPerVariant": eq_trials,
        "equivalenceVariants": eq["variants"],
        "equivalencePairedTrials": eq["pairedTrials"],
        "equivalenceMismatchedTrials": eq["mismatchedTrials"],
        "equivalenceVariantsWithMismatch": eq["variantsWithMismatch"],
        "equivalenceExact": eq["exact"],
        "equivalenceElapsedSeconds": eq_elapsed,
        "trialsPerVariant": trials,
        "variants": len(variants),
        "variantCounts": dict(sorted(counts.items())),
        "priorityVariantCounts": dict(sorted(priorities.items())),
        "totalTrials": len(variants) * trials,
        "elapsedSeconds": elapsed,
        "trialErrors": trial_errors,
        "offenseSeriesRows": len(offense),
        "defenseSeriesRows": len(defense),
        "packetResolutionRows": len(surface),
        "failedGates": failures,
        "automaticPromotion": False,
        "interpretation": (
            "CP121 first requires exact paired outcome equivalence between the legacy integer damage domain and an x2 research-only conversion, then measures odd scaled-domain half-steps around CP120's principal offensive cliffs and selected Hull/Shield/Armor defense axes. Internal H/X criticals remain outside this research combat consumer; their cadence is audited separately and cannot be inferred from the Monte Carlo results. No numerical value or x2 scale is promoted automatically."
        ),
    }
    (outdir / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
