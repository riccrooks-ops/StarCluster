from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .baseline_foundation import BaselineBuild, BaselineCatalog, enumerate_legal_builds
from .missile_progression_analysis import (
    _accepted_baseline,
    _context_rows,
    _family,
    _run_candidate,
    _same_tl_missile_tasks,
    _weighted,
)
from .main_subsystem_stabilization_analysis import _read_rows, _normalize_variant_rows
from .study import canonicalize_relocated_references, load_json
from .whole_ladder_analysis import _write_csv

SCHEMA = "star-cluster-cp131-late-missile-warhead-maturation-v0.1"
RESULT_SCHEMA = "star-cluster-cp131-late-missile-warhead-maturation-results-v0.1"
DEFAULT_STUDY = "docs/archive/testing/pre-cp165-active/cp131_late_missile_warhead_maturation_study_v0_1.json"


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    expected = {
        "schemaVersion": SCHEMA,
        "checkpoint": 131,
        "acceptedBaselineCheckpoint": 130,
        "acceptedNumericalCheckpoint": 128,
        "acceptedImplementationBaseline": 122,
        "sourceMatrix": "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json",
        "technologyValuesChanged": False,
        "productionSourceChanged": False,
        "scenarioDefinitionsChanged": False,
        "mixedTlShipsExecuted": False,
        "automaticPromotion": False,
        "recommendedJobs": 24,
        "trialsPerVariant": 100,
    }
    for key, value in expected.items():
        if doc.get(key) != value:
            errors.append(key)
    primary = doc.get("latePrimarySweep", {})
    expected_grid = {
        "8": ([15, 16, 17, 18, 19], [3, 4, 5, 6], 4, (17, 3, 4, "d17_sp3")),
        "9": ([16, 17, 18, 19, 20], [4, 5, 6, 7], 5, (18, 4, 5, "d18_sp4_ap5")),
    }
    for tl, (damages, spens, apen, anchor) in expected_grid.items():
        row = primary.get(tl, {})
        if row.get("damageValues") != damages or row.get("spenValues") != spens or row.get("apen") != apen:
            errors.append(f"latePrimarySweep.{tl}")
        a = row.get("anchor", {})
        if (a.get("damage"), a.get("spen"), a.get("apen"), a.get("cp130Candidate")) != anchor:
            errors.append(f"latePrimarySweep.{tl}.anchor")
    probes = doc.get("tl9Apen6ThresholdProbes", [])
    expected_probes = [(16,4,6),(17,5,6),(18,4,6),(18,6,6),(19,6,6),(20,7,6)]
    if [(r.get("damage"), r.get("spen"), r.get("apen")) for r in probes] != expected_probes:
        errors.append("tl9Apen6ThresholdProbes")
    if doc.get("acceptedCp130Tl1To7Plus2Baseline") != "docs/validation/evidence/checkpoint-131/accepted-cp130/tl1_7_plus2_baseline.csv":
        errors.append("acceptedCp130Tl1To7Plus2Baseline")
    if doc.get("acceptedCp130LateAnchorBaseline") != "docs/validation/evidence/checkpoint-131/accepted-cp130/late_anchor_baseline.csv":
        errors.append("acceptedCp130LateAnchorBaseline")
    return errors


def _candidate_id(damage: int, spen: int, apen: int) -> str:
    return f"d{damage}_sp{spen}_ap{apen}"


def _candidate_rows(doc: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = {8: [], 9: []}
    for tl in (8, 9):
        cfg = doc["latePrimarySweep"][str(tl)]
        for damage in cfg["damageValues"]:
            for spen in cfg["spenValues"]:
                apen = int(cfg["apen"])
                out[tl].append({
                    "id": _candidate_id(int(damage), int(spen), apen),
                    "tl": tl,
                    "damage": int(damage),
                    "spen": int(spen),
                    "apen": apen,
                    "class": "primary_damage_spen_sweep",
                    "isApen6Probe": False,
                })
    for probe in doc["tl9Apen6ThresholdProbes"]:
        row = {
            "id": _candidate_id(int(probe["damage"]), int(probe["spen"]), int(probe["apen"])),
            "tl": 9,
            "damage": int(probe["damage"]),
            "spen": int(probe["spen"]),
            "apen": int(probe["apen"]),
            "class": probe["class"],
            "isApen6Probe": True,
        }
        out[9].append(row)
    for tl in out:
        ids = [r["id"] for r in out[tl]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate CP131 candidate ID at TL{tl}")
    return out


def _task_rows(tasks: dict[int, list[Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tl in (8, 9):
        for t in tasks[tl]:
            rows.append({
                "task_id": t.task_id,
                "tl": tl,
                "build_1": t.build_1_id,
                "build_2": t.build_2_id,
                "design_weight": t.design_weight,
                "variants": t.variant_count,
            })
    return rows


def build_plan(repo: Path, study_path: Path, outdir: Path | None = None) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("CP131 study validation failed: " + ", ".join(errors))
    catalog = BaselineCatalog(repo, doc["sourceMatrix"])
    raw, builds = enumerate_legal_builds(catalog)
    if raw != 14112 or len(builds) != 9427:
        raise ValueError(f"legal-build drift: {raw}/{len(builds)}")
    all_tasks = _same_tl_missile_tasks(builds, int(doc["pairingSeed"]))
    tasks = {8: all_tasks[8], 9: all_tasks[9]}
    candidates = _candidate_rows(doc)
    task_counts = {str(tl): len(tasks[tl]) for tl in (8, 9)}
    variant_counts = {str(tl): sum(t.variant_count for t in tasks[tl]) for tl in (8, 9)}
    candidate_counts = {str(tl): len(candidates[tl]) for tl in (8, 9)}
    generated = sum(variant_counts[str(tl)] * candidate_counts[str(tl)] for tl in (8, 9))
    substantive = generated * int(doc["trialsPerVariant"])
    summary = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 131,
        "mode": "plan",
        "rawBuildCombinations": raw,
        "legalBuilds": len(builds),
        "sameTlMissilePairTasksByTl": task_counts,
        "sameTlMissileVariantsPerCandidateByTl": variant_counts,
        "candidateCountsByTl": candidate_counts,
        "generatedVariants": generated,
        "pipelineSmokeTrials": generated,
        "substantiveTrials": substantive,
        "technologyValuesChanged": False,
        "mixedTlShipsExecuted": False,
        "automaticPromotion": False,
        "failedGates": [],
    }
    exp = doc.get("expected", {})
    for key in ("rawBuildCombinations", "legalBuilds", "generatedVariants", "pipelineSmokeTrials", "substantiveTrials"):
        if key in exp and int(summary[key]) != int(exp[key]):
            summary["failedGates"].append(f"{key}:{summary[key]}!={exp[key]}")
    if int(exp.get("tl8Candidates", candidate_counts["8"])) != candidate_counts["8"]:
        summary["failedGates"].append("tl8-candidate-count")
    if int(exp.get("tl9Candidates", candidate_counts["9"])) != candidate_counts["9"]:
        summary["failedGates"].append("tl9-candidate-count")
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        _write_csv(outdir / "late_missile_tasks.csv", _task_rows(tasks))
        _write_csv(outdir / "candidate_ledger.csv", [r for tl in (8, 9) for r in candidates[tl]])
        (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"doc": doc, "catalog": catalog, "builds": builds, "tasks": tasks, "candidates": candidates, "summary": summary}


def _missile_win(rows: list[dict[str, Any]], build_map: dict[str, BaselineBuild], *, gp_only: bool = False, single_main: bool = False) -> float:
    total_weight = 0.0
    weighted_win = 0.0
    for r in rows:
        b1, b2 = build_map[r["build_1"]], build_map[r["build_2"]]
        fams = {_family(b1), _family(b2)}
        if "Missile" not in fams or not ("Kinetic" in fams or "Energy" in fams):
            continue
        mb = b1 if _family(b1) == "Missile" else b2
        db = b2 if mb is b1 else b1
        if gp_only and mb.missile_payload != "GP":
            continue
        if single_main and not (mb.missile_payload == "GP" and mb.main_count == 1 and db.main_count == 1):
            continue
        b1_win = float(r["build_1_conditional_win_rate"])
        missile_win = b1_win if _family(b1) == "Missile" else 1.0 - b1_win
        wt = float(r["design_weight"])
        total_weight += wt
        weighted_win += wt * missile_win
    return weighted_win / total_weight if total_weight else 0.0


def _direct_win(rows: list[dict[str, Any]], build_map: dict[str, BaselineBuild], direct_family: str, *, gp_only: bool = False, single_main: bool = False) -> float:
    total_weight = 0.0
    weighted_win = 0.0
    for r in rows:
        b1, b2 = build_map[r["build_1"]], build_map[r["build_2"]]
        if {_family(b1), _family(b2)} != {direct_family, "Missile"}:
            continue
        mb = b1 if _family(b1) == "Missile" else b2
        db = b2 if mb is b1 else b1
        if gp_only and mb.missile_payload != "GP":
            continue
        if single_main and not (mb.missile_payload == "GP" and mb.main_count == 1 and db.main_count == 1):
            continue
        b1_win = float(r["build_1_conditional_win_rate"])
        direct_win = b1_win if _family(b1) == direct_family else 1.0 - b1_win
        wt = float(r["design_weight"])
        total_weight += wt
        weighted_win += wt * direct_win
    return weighted_win / total_weight if total_weight else 0.0


def _pair_summary(pair_rows: list[dict[str, Any]], build_map: dict[str, BaselineBuild], c: dict[str, Any], accepted: dict[int, dict[str, str]]) -> dict[str, Any]:
    tl = int(c["tl"])
    mm = [r for r in pair_rows if _family(build_map[r["build_1"]]) == "Missile" and _family(build_map[r["build_2"]]) == "Missile"]
    gpmm = [r for r in mm if build_map[r["build_1"]].missile_payload == "GP" and build_map[r["build_2"]].missile_payload == "GP"]
    out = {
        "tl": tl,
        "candidate": c["id"],
        "candidate_class": c["class"],
        "gp_damage": c["damage"],
        "gp_spen": c["spen"],
        "gp_apen": c["apen"],
        "kinetic_mirror_mean_turns": float(accepted[tl]["kinetic_mirror_mean_turns"]),
        "energy_mirror_mean_turns": float(accepted[tl]["energy_mirror_mean_turns"]),
        "missile_mirror_mean_turns": _weighted(mm, "mean_turns"),
        "missile_mirror_unresolved_rate": _weighted(mm, "unresolved_rate"),
        "kinetic_vs_missile_conditional_win_rate": _direct_win(pair_rows, build_map, "Kinetic"),
        "energy_vs_missile_conditional_win_rate": _direct_win(pair_rows, build_map, "Energy"),
        "missile_family_win_vs_k_e": _missile_win(pair_rows, build_map),
        "gp_missile_win_vs_k_e": _missile_win(pair_rows, build_map, gp_only=True),
        "single_main_gp_missile_win_vs_k_e": _missile_win(pair_rows, build_map, gp_only=True, single_main=True),
        "gp_mirror_mean_turns": _weighted(gpmm, "mean_turns"),
        "gp_mirror_unresolved_rate": _weighted(gpmm, "unresolved_rate"),
    }
    for fam, key in (("Kinetic", "kinetic"), ("Energy", "energy")):
        out[f"{key}_vs_gp_conditional_win_rate"] = _direct_win(pair_rows, build_map, fam, gp_only=True)
        out[f"single_main_{key}_vs_gp_conditional_win_rate"] = _direct_win(pair_rows, build_map, fam, gp_only=True, single_main=True)
    return out


def _anchor_replication(summary_rows: list[dict[str, Any]], accepted_rows: list[dict[str, str]], doc: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    by_value = {(int(r["tl"]), int(r["gp_damage"]), int(r["gp_spen"]), int(r["gp_apen"])): r for r in summary_rows}
    replication: list[dict[str, Any]] = []
    failed: list[str] = []
    metrics = [
        "missile_mirror_mean_turns",
        "missile_mirror_unresolved_rate",
        "kinetic_vs_missile_conditional_win_rate",
        "energy_vs_missile_conditional_win_rate",
        "gp_mirror_mean_turns",
        "gp_mirror_unresolved_rate",
        "kinetic_vs_gp_conditional_win_rate",
        "energy_vs_gp_conditional_win_rate",
        "single_main_kinetic_vs_gp_conditional_win_rate",
        "single_main_energy_vs_gp_conditional_win_rate",
    ]
    for old in accepted_rows:
        key = (int(old["tl"]), int(old["gp_damage"]), int(old["gp_spen"]), int(old["gp_apen"]))
        new = by_value.get(key)
        if new is None:
            failed.append(f"missing-anchor:{key}")
            continue
        for metric in metrics:
            ov = float(old[metric]); nv = float(new[metric]); delta = nv - ov
            replication.append({"tl": key[0], "damage": key[1], "spen": key[2], "apen": key[3], "metric": metric, "cp130": ov, "cp131": nv, "delta": delta})
            if abs(delta) > 1e-12:
                failed.append(f"cp130-anchor-tl{key[0]}-{metric}:{delta}")
    return replication, failed


def _apen6_effects(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(int(r["tl"]), int(r["gp_damage"]), int(r["gp_spen"]), int(r["gp_apen"])): r for r in summary_rows}
    metrics = [
        "single_main_gp_missile_win_vs_k_e",
        "missile_family_win_vs_k_e",
        "missile_mirror_mean_turns",
        "missile_mirror_unresolved_rate",
        "kinetic_vs_missile_conditional_win_rate",
        "energy_vs_missile_conditional_win_rate",
    ]
    rows: list[dict[str, Any]] = []
    for (tl, damage, spen, apen), hi in sorted(lookup.items()):
        if tl != 9 or apen != 6:
            continue
        lo = lookup.get((9, damage, spen, 5))
        if lo is None:
            continue
        row: dict[str, Any] = {"tl": 9, "damage": damage, "spen": spen, "base_apen": 5, "probe_apen": 6}
        for metric in metrics:
            row[f"apen5_{metric}"] = float(lo[metric])
            row[f"apen6_{metric}"] = float(hi[metric])
            row[f"delta_{metric}"] = float(hi[metric]) - float(lo[metric])
        rows.append(row)
    return rows


def _run_all(repo: Path, study_path: Path, outdir: Path, trials: int, jobs: int, smoke: bool) -> dict[str, Any]:
    plan = build_plan(repo, study_path, outdir / "plan")
    doc = plan["doc"]
    builds = plan["builds"]
    build_map = {b.id: b for b in builds}
    accepted = _accepted_baseline(repo, doc["acceptedCp130LateAnchorBaseline"])
    accepted_anchor_rows = _read_rows(repo / doc["acceptedCp130LateAnchorBaseline"])
    summary_rows: list[dict[str, Any]] = []
    context_rows: list[dict[str, Any]] = []
    lane_rows: list[dict[str, Any]] = []
    errors = 0
    variants = 0
    flights = int(load_json(repo / doc["sourceMatrix"])["profiles"]["missile_delivery"]["1"]["flights"])
    for tl in (8, 9):
        for candidate in plan["candidates"][tl]:
            pair_rows, variant_rows, elapsed = _run_candidate(repo, doc, plan["tasks"][tl], candidate, outdir / "candidates", trials, jobs)
            lane_errors = sum(int(r["errors"]) for r in variant_rows)
            errors += lane_errors
            variants += len(variant_rows)
            summary_rows.append(_pair_summary(pair_rows, build_map, candidate, accepted))
            context_rows.extend(_context_rows(variant_rows, build_map, candidate, flights))
            lane_rows.append({
                "tl": tl,
                "candidate": candidate["id"],
                "candidate_class": candidate["class"],
                "variants": len(variant_rows),
                "trials_per_variant": trials,
                "elapsed_seconds": elapsed,
                "trial_errors": lane_errors,
            })
            if not lane_errors:
                lane_dir = outdir / "candidates" / f"tl{tl}" / candidate["id"]
                (lane_dir / "variants.csv").unlink(missing_ok=True)
                (lane_dir / "derived_matrix.json").unlink(missing_ok=True)
    _write_csv(outdir / "family_plot_inputs.csv", summary_rows)
    _write_csv(outdir / "missile_context_telemetry.csv", context_rows)
    _write_csv(outdir / "lane_summary.csv", lane_rows)
    _write_csv(outdir / "tl9_apen6_threshold_effects.csv", _apen6_effects(summary_rows))

    failed: list[str] = []
    replication_rows: list[dict[str, Any]] = []
    if trials == int(doc["trialsPerVariant"]):
        replication_rows, replication_failed = _anchor_replication(summary_rows, accepted_anchor_rows, doc)
        failed.extend(replication_failed)
        _write_csv(outdir / "cp130_anchor_replication.csv", replication_rows)
    expected = int(doc["expected"]["generatedVariants"])
    if variants != expected:
        failed.append(f"variant-count:{variants}!={expected}")
    if errors:
        failed.append(f"trial-errors:{errors}")
    result = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 131,
        "mode": "smoke" if smoke else "substantive",
        "variants": variants,
        "trialsPerVariant": trials,
        "totalTrials": variants * trials,
        "trialErrors": errors,
        "candidateRows": len(summary_rows),
        "tl8CandidateRows": sum(1 for r in summary_rows if int(r["tl"]) == 8),
        "tl9CandidateRows": sum(1 for r in summary_rows if int(r["tl"]) == 9),
        "tl9Apen6ProbeRows": sum(1 for r in summary_rows if int(r["tl"]) == 9 and int(r["gp_apen"]) == 6),
        "technologyValuesChanged": False,
        "mixedTlShipsExecuted": False,
        "automaticPromotion": False,
        "rawVariantDetailRetained": bool(errors),
        "failedGates": failed,
    }
    (outdir / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def run_late_missile_maturation(repo: Path, study_path: Path, outdir: Path, *, mode: str, jobs: int = 24) -> dict[str, Any]:
    if mode == "plan":
        return build_plan(repo, study_path, outdir)["summary"]
    doc = load_json(study_path)
    if mode == "smoke":
        return _run_all(repo, study_path, outdir, 1, jobs, True)
    if mode == "run":
        return _run_all(repo, study_path, outdir, int(doc["trialsPerVariant"]), jobs, False)
    raise ValueError(f"unknown CP131 mode: {mode}")
