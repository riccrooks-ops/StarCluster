from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .ecology import CandidateMatrix, DAMAGE_MODEL, MAP_RADIUS, _create_side, _shield_armor, _weapon, generate_primary_builds
from .study import load_json
from .weapon_family_analysis import (
    FamilyCatalog,
    FamilyProfile,
    build_variants,
    execute,
    _apply_fixture_state,
    _apply_profile_hit,
    _effective_profile,
    _fixture_build,
    _summary,
    _target_fixture_rows,
    _write_csv,
)

SCHEMA = "star-cluster-warhead-role-generation-v0.1"
RESULT_SCHEMA = "star-cluster-warhead-role-generation-results-v0.1"


def _profile_map(doc: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in doc.get(key, [])}


def validate_study(doc: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        errors.append("schemaVersion")
    if doc.get("checkpoint") != 116:
        errors.append("checkpoint")
    if str(doc.get("acceptedBaseline")) != "115a":
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
    fixture_ids = [str(x.get("id")) for x in fixtures]
    if len(fixture_ids) != len(set(fixture_ids)):
        errors.append("duplicateTargetFixture")
    required_fixtures = {
        "shield-heavy-legal",
        "shield-isolated-legal",
        "shield-overmatch-fixture",
        "balanced-layered-legal",
        "armor-exposed-legal",
        "pds-heavy-legal",
        "armor-heavy-fixture",
        "light-fixture",
    }
    if not required_fixtures <= set(fixture_ids):
        errors.append("requiredTargetFixtures")
    for row in fixtures:
        if row.get("classification") not in ("legal_build", "controlled_fixture"):
            errors.append(f"targetFixtureClassification:{row.get('id')}")

    missile = _profile_map(doc, "missileProfiles")
    kinetic = _profile_map(doc, "kineticProfiles")
    if len(missile) != len(doc.get("missileProfiles", [])):
        errors.append("duplicate:missileProfiles")
    if len(kinetic) != len(doc.get("kineticProfiles", [])):
        errors.append("duplicate:kineticProfiles")
    for key, family in (("missileProfiles", "Missile"), ("kineticProfiles", "Kinetic")):
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

    baseline = doc.get("gpBaselinePenetration", {})
    baseline_sp = int(baseline.get("spen", -1))
    baseline_ap = int(baseline.get("apen", -1))
    if baseline_sp < 0 or baseline_ap < 0:
        errors.append("gpBaselinePenetration")
    pure_ids: list[str] = []
    for tl, ids in doc.get("pureGpByTl", {}).items():
        if not ids:
            errors.append(f"pureGpByTl:{tl}")
        for pid in ids:
            pure_ids.append(pid)
            row = missile.get(pid)
            if row is None:
                errors.append(f"missingPureGp:{pid}")
                continue
            if int(row.get("spen", -99)) != baseline_sp or int(row.get("apen", -99)) != baseline_ap:
                errors.append(f"gpPurityPenetration:{pid}")
            if int(tl) not in [int(x) for x in row.get("studyTls", [])]:
                errors.append(f"gpPurityTl:{pid}:{tl}")
    generation_order = list(doc.get("generationOrder", []))
    anchor_damage: list[int] = []
    for generation in generation_order:
        anchor_id = doc.get("generationGpAnchor", {}).get(generation)
        row = missile.get(anchor_id) if anchor_id else None
        if row is None:
            errors.append(f"generationGpAnchor:{generation}")
        else:
            anchor_damage.append(int(row.get("damage", 0)))
    if anchor_damage and any(b <= a for a, b in zip(anchor_damage, anchor_damage[1:])):
        errors.append("generationYieldProgression")

    for tl, pid in doc.get("penetrationBundledGpByTl", {}).items():
        row = missile.get(pid)
        if row is None:
            errors.append(f"penetrationBundledGp:{tl}:{pid}")
            continue
        if int(row.get("spen", baseline_sp)) <= baseline_sp and int(row.get("apen", baseline_ap)) <= baseline_ap:
            errors.append(f"penetrationBundledGpNoLeakage:{pid}")

    for map_key, axis in (("spenOnlyGpByTl", "spen"), ("apenOnlyGpByTl", "apen")):
        for tl, pid in doc.get(map_key, {}).items():
            row = missile.get(pid)
            if row is None:
                errors.append(f"{map_key}:{tl}:{pid}")
                continue
            if axis == "spen":
                if int(row.get("spen", baseline_sp)) <= baseline_sp or int(row.get("apen", baseline_ap)) != baseline_ap:
                    errors.append(f"{map_key}:axis:{pid}")
            else:
                if int(row.get("apen", baseline_ap)) <= baseline_ap or int(row.get("spen", baseline_sp)) != baseline_sp:
                    errors.append(f"{map_key}:axis:{pid}")

    for map_key in ("specialistPairingIdsByTl", "adaptivePairingIdsByTl"):
        for tl, ids in doc.get(map_key, {}).items():
            for pid in ids:
                row = missile.get(pid)
                if row is None:
                    errors.append(f"{map_key}:missing:{tl}:{pid}")
                elif int(tl) not in [int(x) for x in row.get("studyTls", [])]:
                    errors.append(f"{map_key}:tl:{tl}:{pid}")

    for tl, anchor_id in doc.get("contemporaryGpByTl", {}).items():
        for pid in anchor_id:
            if pid not in missile:
                errors.append(f"contemporaryGpMissing:{tl}:{pid}")
            elif pid not in doc.get("pureGpByTl", {}).get(str(tl), []):
                errors.append(f"contemporaryGpNotPure:{tl}:{pid}")

    for tl, ids in doc.get("specialistPairingIdsByTl", {}).items():
        anchors = doc.get("contemporaryGpByTl", {}).get(str(tl), [])
        if not anchors:
            continue
        anchor = missile.get(anchors[0])
        if anchor is None:
            continue
        for pid in ids:
            row = missile.get(pid)
            if row is None:
                continue
            # A selectable specialist must give something up versus the contemporary GP anchor.
            strictly_no_worse = (
                int(row.get("damage", 0)) >= int(anchor.get("damage", 0))
                and int(row.get("spen", 0)) >= int(anchor.get("spen", 0))
                and int(row.get("apen", 0)) >= int(anchor.get("apen", 0))
            )
            if strictly_no_worse:
                errors.append(f"specialistStrictDominance:{tl}:{pid}")

    required_kinetic = {"gp-current", "kinetic-smart-plus10", "kinetic-dense-b"}
    if not required_kinetic <= set(kinetic):
        errors.append("requiredKineticProfiles")
    if not any("saturation" in pid for pid in kinetic):
        errors.append("requiredKineticSaturation")
    if not any("tandem" in pid for pid in kinetic):
        errors.append("requiredKineticTandem")
    return errors


def _profile_catalog_rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("missileProfiles", "kineticProfiles"):
        for p in doc.get(key, []):
            rows.append(
                {
                    "family": p.get("family", ""),
                    "profile_id": p.get("id", ""),
                    "profile_class": p.get("profileClass", ""),
                    "generation": p.get("generation", ""),
                    "study_tls": ",".join(str(x) for x in p.get("studyTls", [])),
                    "damage": "" if p.get("damage") is None else p.get("damage"),
                    "damage_delta": p.get("damageDelta", 0),
                    "spen": "" if p.get("spen") is None else p.get("spen"),
                    "spen_delta": p.get("spenDelta", 0),
                    "apen": "" if p.get("apen") is None else p.get("apen"),
                    "apen_delta": p.get("apenDelta", 0),
                    "accuracy_delta": p.get("accuracyDelta", 0),
                    "packets": p.get("packets", 1),
                    "ordered_packets": json.dumps(p.get("orderedPackets", []), separators=(",", ":")),
                    "shield_bonus_damage": p.get("shieldBonusDamage", 0),
                    "shield_armor_reduction": p.get("shieldArmorReduction", 0),
                    "recharge_suppression": p.get("rechargeSuppression", 0),
                    "role": p.get("role", ""),
                }
            )
    return rows


def _packet_probe_rows(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    matrix = CandidateMatrix(repo)
    primary = generate_primary_builds(matrix)
    by = {b.id: b for b in primary}
    catalog = FamilyCatalog(doc)
    rows: list[dict[str, Any]] = []
    families = (
        ("Missile", catalog.missile, [int(x) for x in doc.get("missileStudyTls", [])]),
        ("Kinetic", catalog.kinetic, [int(x) for x in doc.get("kineticStudyTls", [])]),
    )
    for family, table, tls in families:
        for tl in tls:
            attacker = by[f"tl{tl}-{family.lower()}-balanced"]
            base_weapon = _weapon(matrix, attacker)
            for profile in sorted((p for p in table.values() if tl in p.study_tls), key=lambda p: p.id):
                eff = _effective_profile(base_weapon, profile)
                for fixture in sorted(catalog.fixtures.values(), key=lambda f: f.id):
                    target_build = _fixture_build(matrix, by, tl, fixture)
                    target = _create_side(matrix, target_build, MAP_RADIUS)
                    _apply_fixture_state(target, fixture)
                    before = (target.shield, target.armor_integrity, target.hull)
                    hardener_active = bool(target_build.shield_hardener and target.shield > 0)
                    shield_armor = _shield_armor(matrix, target, hardener_active)
                    result = _apply_profile_hit(target, eff, shield_armor, "probe")
                    rows.append(
                        {
                            "family": family,
                            "tl": tl,
                            "profile_id": profile.id,
                            "generation": profile.generation,
                            "target_fixture": fixture.id,
                            "target_classification": fixture.classification,
                            "effective_damage": eff["damage"],
                            "effective_spen": eff["spen"],
                            "effective_apen": eff["apen"],
                            "effective_accuracy": eff["accuracy"],
                            "packets": eff["packets"],
                            "ordered_packets": json.dumps(eff["ordered_packets"], separators=(",", ":")),
                            "initial_shield": before[0],
                            "initial_armor_integrity": before[1],
                            "initial_hull": before[2],
                            "shield_armor": shield_armor,
                            "shield_armor_prevented": result["shield_armor_prevented"],
                            "shield_absorbed": result["shield_absorbed"],
                            "shield_bonus_damage": result["shield_bonus_damage"],
                            "armor_prevented": result["armor_prevented"],
                            "armor_integrity_damage": result["armor_integrity"],
                            "hull_damage": result["hull"],
                            "recharge_suppression_pending": target.recharge_suppression_pending,
                            "post_shield": target.shield,
                            "post_armor_integrity": target.armor_integrity,
                            "post_hull": target.hull,
                        }
                    )
    return rows


def run_role_generation_analysis(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 1) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("invalid CP116 study: " + ",".join(errs))
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
    _write_csv(outdir / "target_fixtures.csv", _target_fixture_rows(CandidateMatrix(repo), catalog, doc, repo))
    _write_csv(outdir / "profile_catalog.csv", _profile_catalog_rows(doc))
    probe_rows = _packet_probe_rows(repo, doc)
    _write_csv(outdir / "packet_layer_probe.csv", probe_rows)
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
    if not probe_rows or not any(int(r["hull_damage"]) > 0 for r in probe_rows):
        failures.append("packet-layer-probe-coverage")

    by_group = defaultdict(int)
    for v in variants:
        by_group[v.scenario_group] += 1
    pure_ids = {pid for ids in doc.get("pureGpByTl", {}).values() for pid in ids}
    penetration_ids = set(doc.get("penetrationBundledGpByTl", {}).values())
    specialist_ids = {pid for ids in doc.get("specialistPairingIdsByTl", {}).values() for pid in ids}
    analysis = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 116,
        "acceptedBaseline": "115a",
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
        "missileProfiles": len(catalog.missile),
        "kineticProfiles": len(catalog.kinetic),
        "pureGpProfileCount": len(pure_ids),
        "penetrationBundledGpControlCount": len(penetration_ids),
        "generationalSpecialistProfileCount": len(specialist_ids),
        "packetLayerProbeRows": len(probe_rows),
        "adaptivePairRows": sum(str(r["side_a_profile"]).startswith("adaptive-pair::") for r in rows),
        "adaptivePairRowsWithSwitches": sum(str(r["side_a_profile"]).startswith("adaptive-pair::") and float(r["mean_a_payload_switches"]) > 0 for r in rows),
        "missileFamilySummary": missile,
        "kineticFamilySummary": kinetic,
        "energyReferenceSummary": energy,
        "interpretation": "CP116 diagnostic evidence only. GP energetic maturation is tested separately from SPEN/APEN specialization; generational specialist payloads must pay explicit opportunity cost. Asymmetric family niches are intentional. No production or numerical value is automatically promoted.",
    }
    (outdir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis
