from __future__ import annotations

import csv
import json
import math
import shutil
import statistics
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from .baseline_foundation import BaselineBuild, BaselineCatalog, enumerate_legal_builds
from .fidelity_attribution_analysis import (
    ALL_TELEMETRY_CONTRACT,
    FidelityTask,
    _composition_key,
    _matched_pairs,
    execute_streaming,
)
from .canonical_combat import FULL_MAP_GEOMETRY, mirror_equivalent, run_trial_full_map
from .ecology import EcologyVariant
from .baseline_foundation import _build_to_ecology
from .main_subsystem_stabilization_analysis import _override_matrix, _read_rows, _normalize_variant_rows, _weighted_high
from .study import canonicalize_relocated_references, load_json
from .whole_ladder_analysis import WeightedOutcome, generate_pairings, pairing_coverage, _write_csv, _normalized_pair_row

SCHEMA = "star-cluster-cp129-whole-ladder-pure-tl-sensitivity-v0.1"
RESULT_SCHEMA = "star-cluster-cp129-whole-ladder-pure-tl-sensitivity-results-v0.1"
DEFAULT_STUDY = "docs/archive/testing/pre-cp165-active/cp129_whole_ladder_pure_tl_sensitivity_study_v0_1.json"


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    expected_top = {
        "schemaVersion": SCHEMA,
        "checkpoint": 129,
        "acceptedBaselineCheckpoint": 128,
        "acceptedStabilizationCheckpoint": 127,
        "acceptedImplementationBaseline": 122,
        "sourceMatrix": "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_5.json",
        "shipTechnologyPolicy": "pure_same_tl_components_per_ship",
        "mixedTlShipsExecuted": False,
        "counterfactualHoldbacksAreLegalMixedTlBuilds": False,
        "automaticPromotion": False,
        "balanceValidated": False,
        "technologyValuesChanged": False,
        "wholeLadderTrialsPerVariant": 100,
        "mainOnlyAdjacentTrialsPerVariant": 100,
        "sensitivityTrialsPerVariant": 50,
        "recommendedJobs": 24,
    }
    for key, value in expected_top.items():
        if doc.get(key) != value:
            errors.append(key)
    sym = doc.get("symmetryGate", {})
    if sym.get("blocking") is not True or int(sym.get("expectedComparisons", 0)) != 2250 or int(sym.get("expectedCombatExecutions", 0)) != 4500:
        errors.append("symmetryGate")
    packages = doc.get("performanceHoldbackBoundary", {}).get("packages", [])
    if [p.get("id") for p in packages] != ["hull", "armor", "reactor", "stl", "computer", "sensor", "ecm", "eccm", "shield", "offense"]:
        errors.append("performanceHoldbackBoundary.packages")
    construction = doc.get("constructionEnvelopeSensitivity", {}).get("packages", [])
    if [p.get("id") for p in construction] != ["hull_capacity", "reactor_space", "stl_space", "ftl_space", "computer_space", "sensor_space", "shield_space", "offense_space"]:
        errors.append("constructionEnvelopeSensitivity.packages")
    if doc.get("mainOnlyAdjacentControl", {}).get("excludedOptionalChoices") != ["PDS", "Shield Hardener"]:
        errors.append("mainOnlyAdjacentControl.excludedOptionalChoices")
    exp = doc.get("expected", {})
    expected_counts = {
        "rawBuildCombinations": 14112,
        "legalBuilds": 9427,
        "canonicalTlCells": 45,
        "wholeLadderBasePairings": 70034,
        "wholeLadderVariants": 280136,
        "mainOnlyLegalBuilds": 1856,
        "mainOnlyAdjacentBasePairings": 1784,
        "mainOnlyAdjacentVariants": 7136,
        "matchedCompositionTasks": 7699,
        "matchedCompositionVariantsPerCondition": 30796,
        "sensitivityConditions": 11,
        "sensitivityVariants": 338756,
        "generatedVariants": 626028,
        "pipelineSmokeTrials": 626028,
        "wholeLadderSubstantiveTrials": 28013600,
        "mainOnlyAdjacentSubstantiveTrials": 713600,
        "sensitivitySubstantiveTrials": 16937800,
        "substantiveTrials": 45665000,
        "telemetryMetrics": 61,
    }
    for key, value in expected_counts.items():
        if int(exp.get(key, -1)) != value:
            errors.append(f"expected.{key}")
    return errors


def _task_rows(tasks: Iterable[FidelityTask]) -> list[dict[str, Any]]:
    return [{
        "task_id": t.task_id,
        "group": t.group,
        "tl_low": t.tl_low,
        "tl_high": t.tl_high,
        "build_1": t.build_1_id,
        "build_2": t.build_2_id,
        "design_weight": t.design_weight,
        "variants": t.variant_count,
    } for t in tasks]


def _whole_ladder_tasks(builds: list[BaselineBuild], pairing_seed: int) -> tuple[list[FidelityTask], dict[str, Any]]:
    pairings = generate_pairings(builds, pairing_seed)
    coverage = pairing_coverage(builds, pairings)
    tasks = [FidelityTask(p.pairing_id, "whole_ladder", "pair", p.tl_1, p.tl_2, p.build_1.id, p.build_2.id, design_weight=p.design_weight) for p in pairings]
    tasks.sort(key=lambda t: t.task_id)
    return tasks, coverage


def _main_only_adjacent_tasks(builds: list[BaselineBuild], pairing_seed: int) -> tuple[list[BaselineBuild], list[FidelityTask]]:
    main_only = [b for b in builds if not b.pds_family and not b.shield_hardener]
    pairings = generate_pairings(main_only, pairing_seed)
    tasks = [FidelityTask("mainonly-" + p.pairing_id, "main_only_adjacent", "pair", p.tl_1, p.tl_2, p.build_1.id, p.build_2.id, design_weight=p.design_weight)
             for p in pairings if p.tl_2 == p.tl_1 + 1]
    tasks.sort(key=lambda t: t.task_id)
    return main_only, tasks


def _matched_tasks(builds: list[BaselineBuild]) -> list[FidelityTask]:
    by_tl = {tl: [b for b in builds if b.tl == tl] for tl in range(1, 10)}
    tasks: list[FidelityTask] = []
    for low in range(1, 9):
        pairs = _matched_pairs(by_tl[low], by_tl[low + 1], _composition_key)
        for i, (a, b) in enumerate(pairs, start=1):
            tasks.append(FidelityTask(
                f"matched-tl{low:02d}-tl{low+1:02d}-p{i:05d}",
                "matched_sensitivity",
                "pair",
                low,
                low + 1,
                a.id,
                b.id,
                design_weight=1.0,
            ))
    tasks.sort(key=lambda t: t.task_id)
    return tasks


def _package_map(doc: dict[str, Any], key: str) -> dict[str, dict[str, list[str]]]:
    rows = doc[key]["packages"]
    return {row["id"]: row["profiles"] for row in rows}


def performance_overrides_for_transition(repo: Path, doc: dict[str, Any], package_id: str, high_tl: int) -> list[dict[str, Any]]:
    source = load_json(repo / doc["sourceMatrix"])
    packages = _package_map(doc, "performanceHoldbackBoundary")
    if package_id not in packages:
        raise ValueError(f"unknown CP129 performance package {package_id}")
    out: list[dict[str, Any]] = []
    for profile, fields in packages[package_id].items():
        low = source["profiles"][profile][str(high_tl - 1)]
        high = source["profiles"][profile][str(high_tl)]
        if profile == "missile_swarmer" and low.get("available", True) is False:
            continue
        for field in fields:
            if field not in low or field not in high:
                continue
            if low[field] != high[field]:
                out.append({"profile": profile, "tl": high_tl, "field": field, "value": low[field], "baselineValue": high[field]})
    return out


def construction_overrides_for_transition(repo: Path, doc: dict[str, Any], package_id: str, high_tl: int) -> list[dict[str, Any]]:
    source = load_json(repo / doc["sourceMatrix"])
    packages = _package_map(doc, "constructionEnvelopeSensitivity")
    if package_id not in packages:
        raise ValueError(f"unknown CP129 construction package {package_id}")
    out: list[dict[str, Any]] = []
    for profile, fields in packages[package_id].items():
        low = source["profiles"][profile][str(high_tl - 1)]
        high = source["profiles"][profile][str(high_tl)]
        for field in fields:
            if field in low and field in high and low[field] != high[field]:
                out.append({"profile": profile, "tl": high_tl, "field": field, "value": low[field], "baselineValue": high[field]})
    return out


def _construction_sensitivity(repo: Path, doc: dict[str, Any], baseline_builds: list[BaselineBuild], scratch: Path | None = None) -> list[dict[str, Any]]:
    baseline_by_tl = {tl: [b for b in baseline_builds if b.tl == tl] for tl in range(1, 10)}
    rows: list[dict[str, Any]] = []
    root = scratch or repo / "out" / ".cp129-construction-plan"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)
    try:
        for high_tl in range(2, 10):
            for package in doc["constructionEnvelopeSensitivity"]["packages"]:
                package_id = package["id"]
                overrides = construction_overrides_for_transition(repo, doc, package_id, high_tl)
                if overrides:
                    matrix = root / f"tl{high_tl:02d}-{package_id}.json"
                    rel = _override_matrix(repo, doc["sourceMatrix"], overrides, matrix)
                    _, builds = enumerate_legal_builds(BaselineCatalog(repo, rel))
                    held = [b for b in builds if b.tl == high_tl]
                else:
                    held = baseline_by_tl[high_tl]
                baseline = baseline_by_tl[high_tl]
                b_ids = {b.id for b in baseline}
                h_ids = {b.id for b in held}
                rows.append({
                    "low_tl": high_tl - 1,
                    "high_tl": high_tl,
                    "package": package_id,
                    "changed_fields": len(overrides),
                    "baseline_legal_builds": len(baseline),
                    "holdback_legal_builds": len(held),
                    "legal_build_delta": len(held) - len(baseline),
                    "baseline_only_builds": len(b_ids - h_ids),
                    "holdback_only_builds": len(h_ids - b_ids),
                    "overrides_json": json.dumps(overrides, sort_keys=True, separators=(",", ":")),
                })
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return rows


def _holdback_ledger(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for high_tl in range(2, 10):
        for package in doc["performanceHoldbackBoundary"]["packages"]:
            for o in performance_overrides_for_transition(repo, doc, package["id"], high_tl):
                rows.append({
                    "low_tl": high_tl - 1,
                    "high_tl": high_tl,
                    "package": package["id"],
                    "profile": o["profile"],
                    "field": o["field"],
                    "baseline_value": json.dumps(o["baselineValue"], ensure_ascii=False),
                    "holdback_value": json.dumps(o["value"], ensure_ascii=False),
                })
    return rows


def build_plan(repo: Path, study_path: Path, outdir: Path | None = None) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("invalid CP129 study: " + ",".join(errors))
    catalog = BaselineCatalog(repo, doc["sourceMatrix"])
    raw, builds = enumerate_legal_builds(catalog)
    whole, coverage = _whole_ladder_tasks(builds, int(doc["pairingSeed"]))
    main_only_builds, main_only = _main_only_adjacent_tasks(builds, int(doc["pairingSeed"]))
    matched = _matched_tasks(builds)
    conditions = ["baseline"] + [p["id"] for p in doc["performanceHoldbackBoundary"]["packages"]]
    whole_variants = sum(t.variant_count for t in whole)
    main_variants = sum(t.variant_count for t in main_only)
    matched_per = sum(t.variant_count for t in matched)
    sensitivity_variants = matched_per * len(conditions)
    generated = whole_variants + main_variants + sensitivity_variants
    substantive = (
        whole_variants * int(doc["wholeLadderTrialsPerVariant"])
        + main_variants * int(doc["mainOnlyAdjacentTrialsPerVariant"])
        + sensitivity_variants * int(doc["sensitivityTrialsPerVariant"])
    )
    exp = doc["expected"]
    checks = {
        "rawBuildCombinations": raw,
        "legalBuilds": len(builds),
        "canonicalTlCells": coverage["canonicalTlCells"],
        "wholeLadderBasePairings": len(whole),
        "wholeLadderVariants": whole_variants,
        "mainOnlyLegalBuilds": len(main_only_builds),
        "mainOnlyAdjacentBasePairings": len(main_only),
        "mainOnlyAdjacentVariants": main_variants,
        "matchedCompositionTasks": len(matched),
        "matchedCompositionVariantsPerCondition": matched_per,
        "sensitivityConditions": len(conditions),
        "sensitivityVariants": sensitivity_variants,
        "generatedVariants": generated,
        "pipelineSmokeTrials": generated,
        "wholeLadderSubstantiveTrials": whole_variants * int(doc["wholeLadderTrialsPerVariant"]),
        "mainOnlyAdjacentSubstantiveTrials": main_variants * int(doc["mainOnlyAdjacentTrialsPerVariant"]),
        "sensitivitySubstantiveTrials": sensitivity_variants * int(doc["sensitivityTrialsPerVariant"]),
        "substantiveTrials": substantive,
        "telemetryMetrics": len(ALL_TELEMETRY_CONTRACT),
    }
    failed = [f"{k}:{v}!={exp[k]}" for k, v in checks.items() if int(v) != int(exp[k])]
    if coverage["missingCoverage"]:
        failed.append("whole-ladder-missing-build-opponent-tl-coverage")
    # Pure-TL and fixed-composition invariants.
    build_map = {b.id: b for b in builds}
    for task in whole + main_only + matched:
        if build_map[task.build_1_id].tl != task.tl_low or build_map[task.build_2_id].tl != task.tl_high:
            failed.append("task-tl-identity")
            break
    for task in matched:
        if _composition_key(build_map[task.build_1_id]) != _composition_key(build_map[task.build_2_id]):
            failed.append("matched-composition-drift")
            break
    for task in main_only:
        if build_map[task.build_1_id].pds_family or build_map[task.build_2_id].pds_family or build_map[task.build_1_id].shield_hardener or build_map[task.build_2_id].shield_hardener:
            failed.append("main-only-aux-leak")
            break
    summary = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 129,
        "mode": "plan",
        **checks,
        "conditions": conditions,
        "mixedTlShipsExecuted": False,
        "counterfactualHoldbacksAreLegalMixedTlBuilds": False,
        "technologyValuesChanged": False,
        "automaticPromotion": False,
        "balanceValidated": False,
        "failedGates": failed,
    }
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        _write_csv(outdir / "whole_ladder_tasks.csv", _task_rows(whole))
        _write_csv(outdir / "main_only_adjacent_tasks.csv", _task_rows(main_only))
        _write_csv(outdir / "matched_sensitivity_tasks.csv", _task_rows(matched))
        _write_csv(outdir / "performance_holdback_ledger.csv", _holdback_ledger(repo, doc))
        _write_csv(outdir / "construction_envelope_sensitivity.csv", _construction_sensitivity(repo, doc, builds, outdir / ".construction-scratch"))
        (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"doc": doc, "catalog": catalog, "builds": builds, "wholeTasks": whole, "mainOnlyTasks": main_only, "matchedTasks": matched, "coverage": coverage, "summary": summary}


def run_symmetry_gate(repo: Path, study_path: Path, outdir: Path) -> dict[str, Any]:
    plan = build_plan(repo, study_path, None)
    doc, catalog, builds = plan["doc"], plan["catalog"], plan["builds"]
    by_tl = {tl: sorted([b for b in builds if b.tl == tl], key=lambda b: b.id) for tl in range(1, 10)}
    comparisons = 0
    mismatches: list[dict[str, Any]] = []
    trials = int(doc["symmetryGate"]["trialsPerCase"])
    cases_per_tl = int(doc["symmetryGate"]["casesPerTl"])
    for tl in range(1, 10):
        group = by_tl[tl]
        pairs: list[tuple[BaselineBuild, BaselineBuild, str]] = []
        for i in range(cases_per_tl - 1):
            left = group[(i + 1) * len(group) // (cases_per_tl + 1)]
            right = group[(cases_per_tl - i) * len(group) // (cases_per_tl + 2)]
            if left.id == right.id:
                right = group[(group.index(right) + 1) % len(group)]
            pairs.append((left, right, f"distinct-{i+1}"))
        same = group[len(group) // 2]
        pairs.append((same, same, "identical-build"))
        for case_index, (left, right, label) in enumerate(pairs):
            for first in ("SideAFirst", "SideBFirst"):
                mirrored = "SideBFirst" if first == "SideAFirst" else "SideAFirst"
                scenario = f"cp129-symmetry-tl{tl}-{case_index}-{label}"
                e1 = _build_to_ecology(left, "cp129-symmetry")
                e2 = _build_to_ecology(right, "cp129-symmetry")
                for trial in range(trials):
                    v1 = EcologyVariant(f"sym-{tl}-{case_index}-a", tl, e1, e2, first, geometry=FULL_MAP_GEOMETRY,
                                        population="cp129_symmetry", scenario_group=scenario,
                                        physical_id_a=scenario + ":ship1", physical_id_b=scenario + ":ship2")
                    v2 = EcologyVariant(f"sym-{tl}-{case_index}-b", tl, e2, e1, mirrored, geometry=FULL_MAP_GEOMETRY,
                                        population="cp129_symmetry", scenario_group=scenario,
                                        physical_id_a=scenario + ":ship2", physical_id_b=scenario + ":ship1")
                    r1 = run_trial_full_map(catalog.matrix, v1, int(doc["masterSeed"]), trial)
                    r2 = run_trial_full_map(catalog.matrix, v2, int(doc["masterSeed"]), trial)
                    comparisons += 1
                    if not mirror_equivalent(r1, r2):
                        mismatches.append({"tl": tl, "case": label, "first": first, "trial": trial, "build1": left.id, "build2": right.id})
                        if len(mismatches) >= 20:
                            break
                if len(mismatches) >= 20:
                    break
            if len(mismatches) >= 20:
                break
        if len(mismatches) >= 20:
            break
    expected = int(doc["symmetryGate"]["expectedComparisons"])
    failed: list[str] = []
    if comparisons != expected:
        failed.append(f"comparisons:{comparisons}!={expected}")
    if mismatches:
        failed.append(f"mirror-mismatches:{len(mismatches)}")
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "symmetry_mismatches.csv", mismatches, ["tl", "case", "first", "trial", "build1", "build2"] if mismatches else None)
    summary = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 129, "mode": "symmetry_gate", "comparisons": comparisons,
               "combatExecutions": comparisons * 2, "mismatches": len(mismatches), "failedGates": failed}
    (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def _run_tasks(repo: Path, source_matrix: str, master_seed: int, tasks: list[FidelityTask], outdir: Path, trials: int, jobs: int) -> tuple[Path, float]:
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / "variants.csv"
    elapsed = execute_streaming(repo, {"sourceMatrix": source_matrix, "masterSeed": master_seed}, tasks, csv_path, trials, jobs)
    return csv_path, elapsed


def _run_holdback(repo: Path, doc: dict[str, Any], tasks: list[FidelityTask], package: str, high_tl: int, outdir: Path, trials: int, jobs: int) -> tuple[Path, float, int]:
    overrides = performance_overrides_for_transition(repo, doc, package, high_tl)
    outdir.mkdir(parents=True, exist_ok=True)
    derived = outdir / "derived_matrix.json"
    source = _override_matrix(repo, doc["sourceMatrix"], overrides, derived) if overrides else doc["sourceMatrix"]
    csv_path, elapsed = _run_tasks(repo, source, int(doc["masterSeed"]), tasks, outdir, trials, jobs)
    return csv_path, elapsed, len(overrides)


def _count_variant_file(path: Path) -> tuple[int, int]:
    variants = 0
    errors = 0
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            variants += 1
            errors += int(row["errors"])
    return variants, errors


def _smoke_lane_row(lane: str, path: Path, elapsed: float) -> dict[str, Any]:
    variants, errors = _count_variant_file(path)
    return {"lane": lane, "variants": variants, "trial_errors": errors, "elapsed_seconds": elapsed, "changed_fields": 0}


def run_smoke(repo: Path, study_path: Path, outdir: Path, jobs: int = 24) -> dict[str, Any]:
    plan = build_plan(repo, study_path, outdir / "plan")
    doc = plan["doc"]
    rows: list[dict[str, Any]] = []
    # Gate lanes use the real consumer but discard successful one-trial variant detail after counting.
    p, e = _run_tasks(repo, doc["sourceMatrix"], int(doc["masterSeed"]), plan["wholeTasks"], outdir / "whole-ladder", 1, jobs)
    rows.append(_smoke_lane_row("whole_ladder", p, e))
    p.unlink(missing_ok=True)
    p, e = _run_tasks(repo, doc["sourceMatrix"], int(doc["masterSeed"]), plan["mainOnlyTasks"], outdir / "main-only-adjacent", 1, jobs)
    rows.append(_smoke_lane_row("main_only_adjacent", p, e))
    p.unlink(missing_ok=True)
    p, e = _run_tasks(repo, doc["sourceMatrix"], int(doc["masterSeed"]), plan["matchedTasks"], outdir / "sensitivity" / "baseline", 1, jobs)
    rows.append(_smoke_lane_row("sensitivity_baseline", p, e))
    p.unlink(missing_ok=True)
    by_transition = {(lo, lo + 1): [t for t in plan["matchedTasks"] if t.tl_low == lo] for lo in range(1, 9)}
    for package in [p["id"] for p in doc["performanceHoldbackBoundary"]["packages"]]:
        for low in range(1, 9):
            high = low + 1
            path, elapsed, changed = _run_holdback(repo, doc, by_transition[(low, high)], package, high,
                                                    outdir / "sensitivity" / f"tl{low}-tl{high}" / package, 1, jobs)
            row = _smoke_lane_row(f"holdback_tl{low}_tl{high}_{package}", path, elapsed)
            row["changed_fields"] = changed
            rows.append(row)
            path.unlink(missing_ok=True)
    _write_csv(outdir / "smoke_lane_summary.csv", rows, ["lane", "variants", "trial_errors", "elapsed_seconds", "changed_fields"])
    variants = sum(int(r["variants"]) for r in rows)
    errors = sum(int(r["trial_errors"]) for r in rows)
    failed: list[str] = []
    if variants != int(doc["expected"]["pipelineSmokeTrials"]):
        failed.append(f"smoke-count:{variants}!={doc['expected']['pipelineSmokeTrials']}")
    if errors:
        failed.append(f"trial-errors:{errors}")
    result = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 129, "mode": "smoke", "variants": variants, "totalTrials": variants,
              "trialErrors": errors, "laneExecutions": len(rows), "failedGates": failed}
    (outdir / "analysis.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def _normalize_file(path: Path, group_override: str | None = None) -> list[dict[str, Any]]:
    rows = _read_rows(path)
    pairs = _normalize_variant_rows(rows)
    if group_override is not None:
        for p in pairs:
            p["study_group"] = group_override
    return pairs


def _weighted_pair_stats(rows: list[dict[str, Any]], *, high: bool = False) -> dict[str, float]:
    return _weighted_high(rows) if high else _weighted_low(rows)


def _weighted_low(rows: list[dict[str, Any]]) -> dict[str, float]:
    tw = sum(float(r["design_weight"]) for r in rows)
    if tw <= 0:
        return {"conditional_win_rate": 0.0, "unresolved_rate": 0.0, "mean_turns": 0.0}
    return {
        "conditional_win_rate": sum(float(r["design_weight"]) * float(r["build_1_conditional_win_rate"]) for r in rows) / tw,
        "unresolved_rate": sum(float(r["design_weight"]) * float(r["unresolved_rate"]) for r in rows) / tw,
        "mean_turns": sum(float(r["design_weight"]) * float(r["mean_turns"]) for r in rows) / tw,
    }


def _weapon_family(profile: str) -> str:
    return "Missile" if profile.startswith("Missile") else profile


def _whole_ladder_analysis(repo: Path, doc: dict[str, Any], path: Path, outdir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    # Stream the wide raw variant file. CP129 has 61 telemetry metrics per side; materializing all
    # 280k rows as Python dictionaries would multiply memory use far beyond the CSV size.
    pair_rows: list[dict[str, Any]] = []
    telem_acc: dict[tuple[int,int], dict[str,float]] = defaultdict(lambda: defaultdict(float))
    telem_w: dict[tuple[int,int], float] = defaultdict(float)
    variant_count = 0
    current_pair = ""
    buf: list[dict[str,str]] = []

    def finish_pair() -> None:
        nonlocal buf
        if not buf:
            return
        pr = _normalized_pair_row(buf)
        pr["study_group"] = "whole_ladder"
        pair_rows.append(pr)
        buf = []

    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            variant_count += 1
            key=(int(r["canonical_tl_1"]),int(r["canonical_tl_2"]))
            b1=r["build_1_id"]; side1="a" if r["side_a_build"]==b1 else "b"; side2="b" if side1=="a" else "a"
            wt=float(r["base_design_weight"])*int(r["trials"])/4.0
            telem_w[key]+=wt
            for metric in ALL_TELEMETRY_CONTRACT:
                name=metric["metric"]
                telem_acc[key]["build1_"+name]+=wt*float(r[f"mean_{side1}_{name}"])
                telem_acc[key]["build2_"+name]+=wt*float(r[f"mean_{side2}_{name}"])
            if current_pair and r["pairing_id"] != current_pair:
                finish_pair()
            current_pair=r["pairing_id"]
            buf.append(r)
    finish_pair()
    _write_csv(outdir / "pairing_outcomes.csv", pair_rows)

    canonical: list[dict[str, Any]] = []
    ordered: list[dict[str, Any]] = []
    adjacent: list[dict[str, Any]] = []
    movement: list[dict[str, Any]] = []
    for a in range(1, 10):
        for b in range(a, 10):
            rr = [r for r in pair_rows if int(r["tl_1"]) == a and int(r["tl_2"]) == b]
            low = _weighted_low(rr)
            canonical.append({"tl_1": a, "tl_2": b, "delta_tl": b - a, "base_pairings": len(rr),
                              "tl1_conditional_win_rate": low["conditional_win_rate"] if a != b else 0.5,
                              "tl2_conditional_win_rate": (1.0 - low["conditional_win_rate"]) if a != b else 0.5,
                              "unresolved_rate": low["unresolved_rate"], "mean_turns": low["mean_turns"]})
            if a == b:
                ordered.append({"side_a_tl": a, "side_b_tl": b, "delta_tl_a_minus_b": 0, "side_a_conditional_win_rate": 0.5,
                                "unresolved_rate": low["unresolved_rate"], "mean_turns": low["mean_turns"], "base_pairings": len(rr)})
            else:
                ordered.append({"side_a_tl": a, "side_b_tl": b, "delta_tl_a_minus_b": a-b, "side_a_conditional_win_rate": low["conditional_win_rate"],
                                "unresolved_rate": low["unresolved_rate"], "mean_turns": low["mean_turns"], "base_pairings": len(rr)})
                ordered.append({"side_a_tl": b, "side_b_tl": a, "delta_tl_a_minus_b": b-a, "side_a_conditional_win_rate": 1.0-low["conditional_win_rate"],
                                "unresolved_rate": low["unresolved_rate"], "mean_turns": low["mean_turns"], "base_pairings": len(rr)})
                if b == a + 1:
                    high = _weighted_high(rr)
                    adjacent.append({"higher_tl_conditional_win_rate": high["higher_tl_conditional_win_rate"], "unresolved_rate": high["unresolved_rate"],
                                     "mean_turns": high["mean_turns"], "low_tl": a, "high_tl": b, "base_pairings": len(rr)})
            weights = [float(r["design_weight"]) for r in rr]
            swings = [float(r["mover_order_swing"]) for r in rr]
            tw = sum(weights)
            movement.append({"tl_1": a, "tl_2": b, "delta_tl": b-a, "base_pairings": len(rr),
                             "weighted_mean_mover_order_swing": sum(w*s for w,s in zip(weights,swings))/tw if tw else 0.0,
                             "median_mover_order_swing": statistics.median(swings) if swings else 0.0,
                             "p95_mover_order_swing": sorted(swings)[min(len(swings)-1, math.floor(.95*(len(swings)-1)))] if swings else 0.0,
                             "max_mover_order_swing": max(swings, default=0.0)})
    ordered.sort(key=lambda r: (r["side_a_tl"], r["side_b_tl"]))
    _write_csv(outdir / "canonical_tl_matchup_summary.csv", canonical)
    _write_csv(outdir / "tl_matchup_summary.csv", ordered)
    _write_csv(outdir / "adjacent_population_summary.csv", adjacent)
    _write_csv(outdir / "movement_order_summary.csv", movement)

    delta: list[dict[str, Any]] = []
    for d in range(0, 9):
        rr = [r for r in pair_rows if int(r["delta_tl"]) == d]
        if d == 0:
            tw = sum(float(r["design_weight"]) for r in rr)
            unresolved = sum(float(r["design_weight"])*float(r["unresolved_rate"]) for r in rr)/tw if tw else 0.0
            turns = sum(float(r["design_weight"])*float(r["mean_turns"]) for r in rr)/tw if tw else 0.0
            highwin = 0.5
        else:
            st = _weighted_high(rr); tw = sum(float(r["design_weight"]) for r in rr); unresolved=st["unresolved_rate"]; turns=st["mean_turns"]; highwin=st["higher_tl_conditional_win_rate"]
        delta.append({"delta_tl": d, "base_pairings": len(rr), "population_weight": tw, "higher_tl_conditional_win_rate": highwin,
                      "mean_unresolved_rate": unresolved, "mean_turns": turns})
    _write_csv(outdir / "delta_tl_summary.csv", delta)

    family_groups: dict[tuple[int,int,str,str], list[dict[str,Any]]] = defaultdict(list)
    for r in pair_rows:
        family_groups[(int(r["tl_1"]), int(r["tl_2"]), r["build_1_profile"], r["build_2_profile"])].append(r)
    family_rows: list[dict[str, Any]] = []
    for (a,b,p1,p2), rr in sorted(family_groups.items()):
        st = _weighted_low(rr)
        family_rows.append({"tl_1":a,"tl_2":b,"profile_1":p1,"profile_2":p2,"base_pairings":len(rr),
                            "profile_1_conditional_win_rate":st["conditional_win_rate"],"unresolved_rate":st["unresolved_rate"],"mean_turns":st["mean_turns"]})
    _write_csv(outdir / "family_matchup_summary.csv", family_rows)

    telem_rows=[]
    for key in sorted(telem_w):
        den=telem_w[key]; tr={"tl_1":key[0],"tl_2":key[1],"weighted_trials":den}
        for metric in ALL_TELEMETRY_CONTRACT:
            name=metric["metric"]; tr["tl1_"+name]=telem_acc[key]["build1_"+name]/den; tr["tl2_"+name]=telem_acc[key]["build2_"+name]/den
        telem_rows.append(tr)
    _write_csv(outdir / "tl_telemetry_summary.csv", telem_rows)

    # Blocking accepted-CP127 adjacent control replication.
    cp127_path = repo / doc["wholeLadderControl"]["acceptedCp127AdjacentSummary"]
    with cp127_path.open(newline="", encoding="utf-8-sig") as f:
        cp127 = {(int(r["low_tl"]), int(r["high_tl"])): r for r in csv.DictReader(f)}
    comp: list[dict[str, Any]] = []
    control_failures: list[str] = []
    for r in adjacent:
        old=cp127[(r["low_tl"],r["high_tl"])]
        row={"low_tl":r["low_tl"],"high_tl":r["high_tl"],"cp127_higher_tl_win_rate":float(old["higher_tl_conditional_win_rate"]),
             "cp129_higher_tl_win_rate":r["higher_tl_conditional_win_rate"],"win_delta":r["higher_tl_conditional_win_rate"]-float(old["higher_tl_conditional_win_rate"]),
             "cp127_unresolved_rate":float(old["unresolved_rate"]),"cp129_unresolved_rate":r["unresolved_rate"],"unresolved_delta":r["unresolved_rate"]-float(old["unresolved_rate"]),
             "cp127_mean_turns":float(old["mean_turns"]),"cp129_mean_turns":r["mean_turns"],"turn_delta":r["mean_turns"]-float(old["mean_turns"]),
             "cp127_base_pairings":int(old["base_pairings"]),"cp129_base_pairings":r["base_pairings"]}
        comp.append(row)
        if row["cp127_base_pairings"] != row["cp129_base_pairings"] or abs(row["win_delta"]) > 1e-12 or abs(row["unresolved_delta"]) > 1e-12 or abs(row["turn_delta"]) > 1e-12:
            control_failures.append(f"TL{r['low_tl']}-TL{r['high_tl']}")
    _write_csv(outdir / "cp127_adjacent_replication.csv", comp)
    return {"pairings":len(pair_rows),"variants":variant_count,"adjacent":adjacent,"delta":delta,"controlFailures":control_failures}, pair_rows, control_failures


def _main_only_analysis(path: Path, outdir: Path) -> tuple[list[dict[str, Any]], int, int]:
    rows=_read_rows(path);pairs=_normalize_variant_rows(rows)
    summary=[]
    for low in range(1,9):
        rr=[r for r in pairs if int(r["tl_1"])==low and int(r["tl_2"])==low+1]
        s=_weighted_high(rr)
        summary.append({"low_tl":low,"high_tl":low+1,"base_pairings":len(rr),"higher_tl_conditional_win_rate":s["higher_tl_conditional_win_rate"],
                        "unresolved_rate":s["unresolved_rate"],"mean_turns":s["mean_turns"]})
    _write_csv(outdir/"pairing_outcomes.csv",pairs)
    _write_csv(outdir/"main_only_adjacent_summary.csv",summary)
    return summary,len(rows),sum(int(r["errors"]) for r in rows)


def _sensitivity_analysis(repo: Path, doc: dict[str, Any], root: Path, baseline_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int, list[str]]:
    baseline_rows=_read_rows(baseline_path); baseline_pairs=_normalize_variant_rows(baseline_rows)
    baseline_by_transition={(lo,lo+1):[r for r in baseline_pairs if int(r["tl_1"])==lo] for lo in range(1,9)}
    transition_rows=[]; family_rows=[]; total_variants=len(baseline_rows); total_errors=sum(int(r["errors"]) for r in baseline_rows); exact_fail=[]
    for low in range(1,9):
        base=baseline_by_transition[(low,low+1)]; bs=_weighted_high(base)
        transition_rows.append({"low_tl":low,"high_tl":low+1,"package":"baseline","changed_fields":0,"base_pairings":len(base),
                                "higher_tl_conditional_win_rate":bs["higher_tl_conditional_win_rate"],"delta_vs_baseline_pp":0.0,
                                "unresolved_rate":bs["unresolved_rate"],"unresolved_delta_pp":0.0,"mean_turns":bs["mean_turns"],"turn_delta":0.0})
        for fam in ("Kinetic","Energy","Missile"):
            rr=[r for r in base if _weapon_family(r["build_2_profile"])==fam]; fs=_weighted_high(rr)
            family_rows.append({"low_tl":low,"high_tl":low+1,"package":"baseline","weapon_family":fam,"changed_fields":0,"base_pairings":len(rr),
                                "higher_tl_conditional_win_rate":fs["higher_tl_conditional_win_rate"],"delta_vs_baseline_pp":0.0,"unresolved_rate":fs["unresolved_rate"],"mean_turns":fs["mean_turns"]})
    for package in [p["id"] for p in doc["performanceHoldbackBoundary"]["packages"]]:
        for low in range(1,9):
            high=low+1; path=root/f"tl{low}-tl{high}"/package/"variants.csv"; rows=_read_rows(path); pairs=_normalize_variant_rows(rows)
            total_variants+=len(rows); total_errors+=sum(int(r["errors"]) for r in rows)
            base=baseline_by_transition[(low,high)]; bs=_weighted_high(base); hs=_weighted_high(pairs)
            changed=len(performance_overrides_for_transition(repo,doc,package,high))
            transition_rows.append({"low_tl":low,"high_tl":high,"package":package,"changed_fields":changed,"base_pairings":len(pairs),
                                    "higher_tl_conditional_win_rate":hs["higher_tl_conditional_win_rate"],"delta_vs_baseline_pp":100*(hs["higher_tl_conditional_win_rate"]-bs["higher_tl_conditional_win_rate"]),
                                    "unresolved_rate":hs["unresolved_rate"],"unresolved_delta_pp":100*(hs["unresolved_rate"]-bs["unresolved_rate"]),
                                    "mean_turns":hs["mean_turns"],"turn_delta":hs["mean_turns"]-bs["mean_turns"]})
            if changed==0:
                # Common-random-number exactness: a no-op holdback must be bit-identical at aggregate level.
                if hs != bs:
                    exact_fail.append(f"TL{low}-TL{high}:{package}")
            for fam in ("Kinetic","Energy","Missile"):
                rr=[r for r in pairs if _weapon_family(r["build_2_profile"])==fam]
                br=[r for r in base if _weapon_family(r["build_2_profile"])==fam]
                fs=_weighted_high(rr); bfs=_weighted_high(br)
                family_rows.append({"low_tl":low,"high_tl":high,"package":package,"weapon_family":fam,"changed_fields":changed,"base_pairings":len(rr),
                                    "higher_tl_conditional_win_rate":fs["higher_tl_conditional_win_rate"],"delta_vs_baseline_pp":100*(fs["higher_tl_conditional_win_rate"]-bfs["higher_tl_conditional_win_rate"]),
                                    "unresolved_rate":fs["unresolved_rate"],"mean_turns":fs["mean_turns"]})
    _write_csv(root/"subsystem_holdback_summary.csv",transition_rows)
    _write_csv(root/"subsystem_holdback_family_summary.csv",family_rows)
    # Ranking is descriptive: marginal effects are not additive shares.
    ranking=[]
    for package in [p["id"] for p in doc["performanceHoldbackBoundary"]["packages"]]:
        rr=[r for r in transition_rows if r["package"]==package and int(r["changed_fields"])>0]
        if rr:
            effects=[float(r["delta_vs_baseline_pp"]) for r in rr]
            strongest=min(rr,key=lambda r:float(r["delta_vs_baseline_pp"]))
            ranking.append({"package":package,"changed_transitions":len(rr),"mean_holdback_delta_pp":statistics.fmean(effects),
                            "mean_absolute_delta_pp":statistics.fmean(abs(x) for x in effects),"most_negative_delta_pp":min(effects),"most_positive_delta_pp":max(effects),
                            "strongest_contribution_transition":f"TL{strongest['low_tl']}->TL{strongest['high_tl']}"})
        else:
            ranking.append({"package":package,"changed_transitions":0,"mean_holdback_delta_pp":0.0,"mean_absolute_delta_pp":0.0,"most_negative_delta_pp":0.0,"most_positive_delta_pp":0.0,"strongest_contribution_transition":""})
    ranking.sort(key=lambda r:(-float(r["mean_absolute_delta_pp"]),r["package"]))
    _write_csv(root/"subsystem_influence_ranking.csv",ranking)
    return transition_rows,family_rows,total_variants,total_errors,exact_fail


def _aux_influence(all_adj: list[dict[str,Any]], main_adj: list[dict[str,Any]], path: Path) -> list[dict[str,Any]]:
    amap={(int(r["low_tl"]),int(r["high_tl"])):r for r in all_adj}; mmap={(int(r["low_tl"]),int(r["high_tl"])):r for r in main_adj}
    rows=[]
    for key in sorted(amap):
        a=amap[key];m=mmap[key]
        rows.append({"low_tl":key[0],"high_tl":key[1],"all_options_high_win":a["higher_tl_conditional_win_rate"],"main_only_high_win":m["higher_tl_conditional_win_rate"],
                     "all_minus_main_only_pp":100*(a["higher_tl_conditional_win_rate"]-m["higher_tl_conditional_win_rate"]),
                     "all_options_unresolved":a["unresolved_rate"],"main_only_unresolved":m["unresolved_rate"],"unresolved_delta_pp":100*(a["unresolved_rate"]-m["unresolved_rate"])})
    _write_csv(path,rows);return rows


def run_substantive(repo: Path, study_path: Path, outdir: Path, jobs: int = 24) -> dict[str, Any]:
    plan=build_plan(repo,study_path,outdir/"plan");doc=plan["doc"];outdir.mkdir(parents=True,exist_ok=True)
    elapsed: dict[str,float]={}
    whole_path,e=_run_tasks(repo,doc["sourceMatrix"],int(doc["masterSeed"]),plan["wholeTasks"],outdir/"whole-ladder",int(doc["wholeLadderTrialsPerVariant"]),jobs);elapsed["wholeLadder"]=e
    main_path,e=_run_tasks(repo,doc["sourceMatrix"],int(doc["masterSeed"]),plan["mainOnlyTasks"],outdir/"main-only-adjacent",int(doc["mainOnlyAdjacentTrialsPerVariant"]),jobs);elapsed["mainOnlyAdjacent"]=e
    baseline_path,e=_run_tasks(repo,doc["sourceMatrix"],int(doc["masterSeed"]),plan["matchedTasks"],outdir/"sensitivity"/"baseline",int(doc["sensitivityTrialsPerVariant"]),jobs);elapsed["sensitivityBaseline"]=e
    by_transition={(lo,lo+1):[t for t in plan["matchedTasks"] if t.tl_low==lo] for lo in range(1,9)}
    for package in [p["id"] for p in doc["performanceHoldbackBoundary"]["packages"]]:
        for low in range(1,9):
            high=low+1
            _,e,_=_run_holdback(repo,doc,by_transition[(low,high)],package,high,outdir/"sensitivity"/f"tl{low}-tl{high}"/package,int(doc["sensitivityTrialsPerVariant"]),jobs)
            elapsed[f"sensitivity_tl{low}_tl{high}_{package}"]=e

    whole_summary,_,control_fail=_whole_ladder_analysis(repo,doc,whole_path,outdir/"whole-ladder")
    main_summary,main_variants,main_errors=_main_only_analysis(main_path,outdir/"main-only-adjacent")
    sens_rows,_,sens_variants,sens_errors,no_op_fail=_sensitivity_analysis(repo,doc,outdir/"sensitivity",baseline_path)
    aux_rows=_aux_influence(whole_summary["adjacent"],main_summary,outdir/"aux_boundary_influence_summary.csv")
    whole_variants,whole_errors=_count_variant_file(whole_path)
    total_variants=whole_variants+main_variants+sens_variants
    total_errors=whole_errors+main_errors+sens_errors
    planned=(whole_variants*int(doc["wholeLadderTrialsPerVariant"])+main_variants*int(doc["mainOnlyAdjacentTrialsPerVariant"])+sens_variants*int(doc["sensitivityTrialsPerVariant"]))
    failed=[]
    if total_variants!=int(doc["expected"]["generatedVariants"]):failed.append(f"variant-count:{total_variants}!={doc['expected']['generatedVariants']}")
    if planned!=int(doc["expected"]["substantiveTrials"]):failed.append(f"trial-count:{planned}!={doc['expected']['substantiveTrials']}")
    if total_errors:failed.append(f"trial-errors:{total_errors}")
    if control_fail:failed.append("accepted-cp127-adjacent-control-replication:"+",".join(control_fail))
    if no_op_fail:failed.append("no-op-holdback-common-random-number-drift:"+",".join(no_op_fail))
    result={"schemaVersion":RESULT_SCHEMA,"checkpoint":129,"mode":"substantive","variants":total_variants,"totalTrials":planned,"trialErrors":total_errors,
            "wholeLadderVariants":whole_variants,"mainOnlyAdjacentVariants":main_variants,"sensitivityVariants":sens_variants,"telemetryMetrics":len(ALL_TELEMETRY_CONTRACT),
            "symmetryGeometry":FULL_MAP_GEOMETRY,"mixedTlShipsExecuted":False,"counterfactualHoldbacksAreLegalMixedTlBuilds":False,"technologyValuesChanged":False,
            "automaticPromotion":False,"balanceValidated":False,"failedGates":failed,"elapsedSecondsByLane":elapsed,
            "rawVariantDetailRetained":False,"rawVariantRetentionPolicy":"transient-consumer-output-removed-after-aggregate-analysis",
            "reviewSignals":{"deltaTlSummary":whole_summary["delta"],"adjacentSummary":whole_summary["adjacent"],"auxBoundaryInfluence":aux_rows,"subsystemHoldbackSummary":sens_rows}}
    (outdir/"analysis.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    # The accepted summaries/pairing aggregates are the durable evidence. Raw per-variant CSVs and
    # transition-specific derived matrices are transient and would otherwise make the native-results
    # handoff unnecessarily large. They remain exactly reproducible from the study definition/seeds.
    for raw in outdir.rglob("variants.csv"):
        raw.unlink(missing_ok=True)
    for derived in outdir.rglob("derived_matrix.json"):
        derived.unlink(missing_ok=True)
    return result


def run_whole_ladder_sensitivity(repo: Path, study_path: Path, outdir: Path, *, mode: str, jobs: int = 24) -> dict[str, Any]:
    if mode == "plan":
        return build_plan(repo, study_path, outdir)["summary"]
    if mode == "symmetry":
        return run_symmetry_gate(repo, study_path, outdir)
    if mode == "smoke":
        return run_smoke(repo, study_path, outdir, jobs)
    if mode == "run":
        return run_substantive(repo, study_path, outdir, jobs)
    raise ValueError(f"unknown CP129 mode: {mode}")
