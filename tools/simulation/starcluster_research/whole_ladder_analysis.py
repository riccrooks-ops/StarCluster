from __future__ import annotations

import csv
import json
import math
import os
import shutil
import statistics
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, fields
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

from .baseline_foundation import (
    DEFAULT_MATRIX,
    TELEMETRY_CONTRACT,
    BaselineBuild,
    BaselineCatalog,
    _build_to_ecology,
    enumerate_legal_builds,
)
from .ecology import CandidateMatrix, EcologyTrialResult, EcologyVariant, SideTelemetry, _aggregate_variant, run_trial
from .rng import XorShift64, derive_seed
from .study import canonicalize_relocated_references, load_json

SCHEMA = "star-cluster-cp125-pure-tl-whole-ladder-study-v0.1"
RESULT_SCHEMA = "star-cluster-cp125-pure-tl-whole-ladder-results-v0.1"
DEFAULT_STUDY = "docs/archive/testing/pre-cp165-active/cp125_pure_tl_whole_ladder_integrated_progression_study_v0_1.json"
MASTER_SEED = 12520260816
PAIRING_SEED = 0x12520260816


@dataclass(frozen=True, slots=True)
class LadderPairing:
    pairing_id: str
    tl_1: int
    tl_2: int
    build_1: BaselineBuild
    build_2: BaselineBuild
    sample_round: int
    canonical_population_pairs: int
    design_weight: float

    @property
    def delta_tl(self) -> int:
        return self.tl_2 - self.tl_1


@dataclass(frozen=True, slots=True)
class PairTask:
    pairing_id: str
    tl_1: int
    tl_2: int
    build_1_id: str
    build_2_id: str
    design_weight: float


@dataclass(frozen=True, slots=True)
class VariantPlan:
    variant: EcologyVariant
    pairing_id: str
    canonical_tl_1: int
    canonical_tl_2: int
    delta_tl: int
    build_1_id: str
    build_2_id: str
    orientation: str
    side_a_tl: int
    side_b_tl: int
    base_design_weight: float
    ordered_cell_variant_weight: float
    mirror_variant_weight: float
    side_a_meta: dict[str, Any]
    side_b_meta: dict[str, Any]


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    expected = {
        "schemaVersion": SCHEMA,
        "checkpoint": 125,
        "acceptedReferenceBaseline": 123,
        "acceptedInstrumentationBaseline": 124,
        "acceptedImplementationBaseline": 122,
        "sourceMatrix": DEFAULT_MATRIX,
        "legalBuilds": 9427,
        "canonicalTlCells": 45,
        "orderedTlCells": 81,
        "basePairings": 70034,
        "generatedVariants": 280136,
        "buildOpponentTlCoverage": 84843,
        "pipelineSmokeTrials": 280136,
        "substantiveTrialsPerVariant": 200,
        "substantiveTrials": 56027200,
        "sameTlPairingRounds": 2,
    }
    for key, value in expected.items():
        actual = doc.get("expected", {}).get(key) if key in {
            "legalBuilds", "canonicalTlCells", "orderedTlCells", "basePairings", "generatedVariants",
            "buildOpponentTlCoverage", "pipelineSmokeTrials", "substantiveTrials"
        } else doc.get(key)
        if actual != value:
            errors.append(key)
    if doc.get("shipTechnologyPolicy") != "pure_same_tl_components_per_ship":
        errors.append("shipTechnologyPolicy")
    if doc.get("mixedTlShipsExecuted") is not False:
        errors.append("mixedTlShipsExecuted")
    if doc.get("automaticPromotion") is not False or doc.get("balanceValidated") is not False:
        errors.append("promotionBoundary")
    if doc.get("pairingDesign", {}).get("allBuildsEveryOpponentTl") is not True:
        errors.append("pairingDesign.allBuildsEveryOpponentTl")
    if doc.get("pairingDesign", {}).get("bothSideAssignments") is not True:
        errors.append("pairingDesign.bothSideAssignments")
    if doc.get("pairingDesign", {}).get("bothMovementOrders") is not True:
        errors.append("pairingDesign.bothMovementOrders")
    if int(doc.get("recommendedJobs", 0)) != 24:
        errors.append("recommendedJobs")
    return errors


def _shuffle(items: list[BaselineBuild], seed: int) -> list[BaselineBuild]:
    out = list(items)
    rng = XorShift64(seed)
    for i in range(len(out) - 1, 0, -1):
        j = rng.next_u64() % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def _same_tl_offsets(n: int) -> tuple[int, int]:
    if n < 5:
        raise ValueError("same-TL coverage requires at least five builds")
    first = 1
    second = max(2, n // 3)
    if second == n // 2 and n % 2 == 0:
        second += 1
    if second in (first, n - first, 0, n):
        second = max(2, n // 4)
    if second in (first, n - first, 0, n) or (n % 2 == 0 and second == n // 2):
        second = 3
    return first, second


def generate_pairings(builds: list[BaselineBuild], pairing_seed: int = PAIRING_SEED) -> list[LadderPairing]:
    by_tl = {tl: sorted((b for b in builds if b.tl == tl), key=lambda b: b.id) for tl in range(1, 10)}
    out: list[LadderPairing] = []
    for tl1 in range(1, 10):
        for tl2 in range(tl1, 10):
            a = _shuffle(by_tl[tl1], derive_seed(pairing_seed, "tl", tl1, tl2, "a"))
            b = _shuffle(by_tl[tl2], derive_seed(pairing_seed, "tl", tl1, tl2, "b"))
            pop = len(a) * len(b) if tl1 != tl2 else len(a) * (len(a) - 1) // 2
            if tl1 != tl2:
                count = max(len(a), len(b))
                weight = pop / count
                for i in range(count):
                    out.append(LadderPairing(
                        f"tl{tl1:02d}-tl{tl2:02d}-p{i+1:05d}", tl1, tl2,
                        a[i % len(a)], b[i % len(b)], 1, pop, weight,
                    ))
            else:
                offsets = _same_tl_offsets(len(a))
                count = len(a) * len(offsets)
                weight = pop / count
                seen: set[tuple[str, str]] = set()
                ordinal = 0
                for round_index, offset in enumerate(offsets, start=1):
                    for i in range(len(a)):
                        x, y = a[i], a[(i + offset) % len(a)]
                        key = tuple(sorted((x.id, y.id)))
                        if key in seen:
                            raise ValueError(f"duplicate same-TL pairing in TL{tl1}: {key}")
                        seen.add(key)
                        ordinal += 1
                        out.append(LadderPairing(
                            f"tl{tl1:02d}-tl{tl2:02d}-p{ordinal:05d}", tl1, tl2,
                            x, y, round_index, pop, weight,
                        ))
    return out


def pairing_coverage(builds: list[BaselineBuild], pairings: list[LadderPairing]) -> dict[str, Any]:
    by_tl = {tl: {b.id for b in builds if b.tl == tl} for tl in range(1, 10)}
    selected: dict[tuple[int, int], dict[int, set[str]]] = {}
    pair_counts: dict[tuple[int, int], int] = defaultdict(int)
    for p in pairings:
        key = (p.tl_1, p.tl_2)
        selected.setdefault(key, {p.tl_1: set(), p.tl_2: set()})
        selected[key][p.tl_1].add(p.build_1.id)
        selected[key][p.tl_2].add(p.build_2.id)
        pair_counts[key] += 1
    missing: list[str] = []
    coverage_count = 0
    for tl1 in range(1, 10):
        for tl2 in range(tl1, 10):
            key = (tl1, tl2)
            for tl in sorted(set(key)):
                got = selected.get(key, {}).get(tl, set())
                expected = by_tl[tl]
                coverage_count += len(got)
                if got != expected:
                    missing_ids = sorted(expected - got)
                    missing.append(f"TL{tl1}-TL{tl2}:TL{tl}:{len(missing_ids)}")
    # For a diagonal cell, coverage is one build set; for each off-diagonal cell, two.
    expected_relationship_coverage = sum(len(by_tl[tl]) * 9 for tl in range(1, 10))
    return {
        "canonicalTlCells": len(pair_counts),
        "buildOpponentTlCoverage": coverage_count,
        "expectedBuildOpponentTlCoverage": expected_relationship_coverage,
        "missingCoverage": missing,
        "pairCounts": {f"TL{a}-TL{b}": pair_counts[(a, b)] for a in range(1, 10) for b in range(a, 10)},
    }


def _profile_name(b: BaselineBuild) -> str:
    if b.weapon_family != "Missile":
        return b.weapon_family
    return f"Missile-{b.missile_payload}"


def _build_meta(b: BaselineBuild) -> dict[str, Any]:
    return {
        "build_id": b.id,
        "tl": b.tl,
        "weapon_profile": _profile_name(b),
        "weapon_family": b.weapon_family,
        "missile_payload": b.missile_payload,
        "main_count": b.main_count,
        "reactor_count": b.reactor_count,
        "shield": b.shield,
        "ecm_count": b.ecm_count,
        "eccm_count": b.eccm_count,
        "pds_family": b.pds_family,
        "shield_hardener": b.shield_hardener,
        "space_class": b.space_class,
        "combat_space": b.combat_space,
        "mission_aux_space": b.mission_aux_space,
        "capacity": b.capacity,
        "operational_power": b.operational_power,
        "nominal_power_demand": b.nominal_power_demand,
        "nominal_power_margin": b.nominal_power_margin,
    }


def _pair_task(p: LadderPairing) -> PairTask:
    return PairTask(p.pairing_id, p.tl_1, p.tl_2, p.build_1.id, p.build_2.id, p.design_weight)


def _plans_for_pair_task(task: PairTask, build_map: dict[str, BaselineBuild]) -> list[VariantPlan]:
    p1, p2 = build_map[task.build_1_id], build_map[task.build_2_id]
    proxy = LadderPairing(task.pairing_id, task.tl_1, task.tl_2, p1, p2, 0,
                          (len(build_map) if False else 0), task.design_weight)
    plans: list[VariantPlan] = []
    orientations = (("forward", p1, p2), ("reverse", p2, p1))
    for orientation, a0, b0 in orientations:
        ea = _build_to_ecology(a0, "cp125-pure-tl")
        eb = _build_to_ecology(b0, "cp125-pure-tl")
        orientation_weight = task.design_weight if task.tl_1 != task.tl_2 else task.design_weight / 2.0
        ordered_variant_weight = orientation_weight / 2.0
        mirror_variant_weight = task.design_weight / 4.0
        for movement in ("SideAFirst", "SideBFirst"):
            suffix = "afirst" if movement == "SideAFirst" else "bfirst"
            variant = EcologyVariant(
                id=f"{task.pairing_id}-{orientation}-{suffix}", tl=a0.tl, side_a=ea, side_b=eb,
                movement_order=movement, population="cp125_pure_tl_whole_ladder",
                scenario_group="pure_tl_whole_ladder",
            )
            plans.append(VariantPlan(
                variant=variant, pairing_id=task.pairing_id, canonical_tl_1=task.tl_1,
                canonical_tl_2=task.tl_2, delta_tl=task.tl_2-task.tl_1,
                build_1_id=p1.id, build_2_id=p2.id, orientation=orientation,
                side_a_tl=a0.tl, side_b_tl=b0.tl, base_design_weight=task.design_weight,
                ordered_cell_variant_weight=ordered_variant_weight, mirror_variant_weight=mirror_variant_weight,
                side_a_meta=_build_meta(a0), side_b_meta=_build_meta(b0),
            ))
    return plans


def generate_variants(pairings: list[LadderPairing]) -> list[VariantPlan]:
    build_map = {b.id:b for p in pairings for b in (p.build_1,p.build_2)}
    plans: list[VariantPlan] = []
    for p in pairings:
        plans.extend(_plans_for_pair_task(_pair_task(p), build_map))
    plans.sort(key=lambda x: x.variant.id)
    return plans


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    names = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=names)
        writer.writeheader()
        writer.writerows(rows)


def _build_rows(builds: list[BaselineBuild]) -> list[dict[str, Any]]:
    return [asdict(b) | {"used_space": b.used_space, "weapon_profile": _profile_name(b)} for b in builds]


def _pairing_rows(pairings: list[LadderPairing]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for p in pairings:
        rows.append({
            "pairing_id": p.pairing_id,
            "tl_1": p.tl_1,
            "tl_2": p.tl_2,
            "delta_tl": p.delta_tl,
            "build_1": p.build_1.id,
            "build_2": p.build_2.id,
            "build_1_profile": _profile_name(p.build_1),
            "build_2_profile": _profile_name(p.build_2),
            "sample_round": p.sample_round,
            "canonical_population_pairs": p.canonical_population_pairs,
            "design_weight": p.design_weight,
        })
    return rows


def _plan_summary(builds: list[BaselineBuild], pairings: list[LadderPairing], coverage: dict[str, Any], doc: dict[str, Any]) -> dict[str, Any]:
    population = len(builds) * (len(builds) - 1) // 2
    return {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 125,
        "mode": "plan",
        "legalBuilds": len(builds),
        "canonicalPairPopulation": population,
        "canonicalTlCells": 45,
        "orderedTlCells": 81,
        "basePairings": len(pairings),
        "generatedVariants": len(pairings) * 4,
        "buildOpponentTlCoverage": coverage["buildOpponentTlCoverage"],
        "sameTlPairingRounds": int(doc["sameTlPairingRounds"]),
        "bothSideAssignments": True,
        "bothMovementOrders": True,
        "substantiveTrialsPerVariant": int(doc["substantiveTrialsPerVariant"]),
        "plannedSubstantiveTrials": len(pairings) * 4 * int(doc["substantiveTrialsPerVariant"]),
        "pipelineSmokeTrials": len(pairings) * 4,
        "mixedTlShipsExecuted": False,
        "automaticPromotion": False,
        "balanceValidated": False,
        "failedGates": [],
    }


def build_plan(repo: Path, study_path: Path, outdir: Path | None = None) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("invalid CP125 study: " + ",".join(errors))
    catalog = BaselineCatalog(repo, doc["sourceMatrix"])
    raw, builds = enumerate_legal_builds(catalog)
    if raw != 14112 or len(builds) != 9427:
        raise ValueError(f"CP124 legal-build foundation drift: {raw}/{len(builds)}")
    pairings = generate_pairings(builds, int(doc["pairingSeed"]))
    coverage = pairing_coverage(builds, pairings)
    summary = _plan_summary(builds, pairings, coverage, doc)
    failures: list[str] = []
    expected = doc["expected"]
    checks = {
        "canonical-tl-cells": (coverage["canonicalTlCells"], int(expected["canonicalTlCells"])),
        "base-pairings": (len(pairings), int(expected["basePairings"])),
        "generated-variants": (len(pairings) * 4, int(expected["generatedVariants"])),
        "build-opponent-tl-coverage": (coverage["buildOpponentTlCoverage"], int(expected["buildOpponentTlCoverage"])),
        "planned-substantive-trials": (summary["plannedSubstantiveTrials"], int(expected["substantiveTrials"])),
    }
    for name, (actual, exp) in checks.items():
        if actual != exp:
            failures.append(f"{name}:{actual}!={exp}")
    if coverage["missingCoverage"]:
        failures.append("missing-build-opponent-tl-coverage")
    if len({p.pairing_id for p in pairings}) != len(pairings):
        failures.append("duplicate-pairing-id")
    # Population weights must reproduce every canonical cell exactly.
    weight_by_cell: dict[tuple[int, int], float] = defaultdict(float)
    pop_by_cell: dict[tuple[int, int], int] = {}
    for p in pairings:
        key = (p.tl_1, p.tl_2)
        weight_by_cell[key] += p.design_weight
        pop_by_cell[key] = p.canonical_population_pairs
    for key, total in weight_by_cell.items():
        if not math.isclose(total, float(pop_by_cell[key]), rel_tol=0.0, abs_tol=1e-6):
            failures.append(f"weight-reconstruction-TL{key[0]}-TL{key[1]}")
    summary["failedGates"] = failures
    summary["pairCountsByCell"] = coverage["pairCounts"]
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        _write_csv(outdir / "legal_builds.csv", _build_rows(builds))
        _write_csv(outdir / "pairings.csv", _pairing_rows(pairings))
        (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"doc": doc, "catalog": catalog, "builds": builds, "pairings": pairings, "coverage": coverage, "summary": summary}


_WHOLE_MATRIX: CandidateMatrix | None = None
_WHOLE_BUILD_MAP: dict[str, BaselineBuild] | None = None


def _init_whole_worker(repo: str, matrix_relative_path: str) -> None:
    global _WHOLE_MATRIX, _WHOLE_BUILD_MAP
    root = Path(repo)
    catalog = BaselineCatalog(root, matrix_relative_path)
    _WHOLE_MATRIX = catalog.matrix
    _, builds = enumerate_legal_builds(catalog)
    _WHOLE_BUILD_MAP = {b.id:b for b in builds}


def _variant_metadata(plan: VariantPlan) -> dict[str, Any]:
    a, b = plan.side_a_meta, plan.side_b_meta
    row: dict[str, Any] = {
        "pairing_id": plan.pairing_id,
        "canonical_tl_1": plan.canonical_tl_1,
        "canonical_tl_2": plan.canonical_tl_2,
        "delta_tl": plan.delta_tl,
        "build_1_id": plan.build_1_id,
        "build_2_id": plan.build_2_id,
        "orientation": plan.orientation,
        "side_a_tl": plan.side_a_tl,
        "side_b_tl": plan.side_b_tl,
        "base_design_weight": plan.base_design_weight,
        "ordered_cell_variant_weight": plan.ordered_cell_variant_weight,
        "mirror_variant_weight": plan.mirror_variant_weight,
    }
    for prefix, meta in (("side_a_", a), ("side_b_", b)):
        for key, value in meta.items():
            if key == "build_id":
                continue
            row[prefix + key] = value
    return row


def _run_substantive_chunk(args: tuple[int, list[PairTask], int, int]) -> tuple[int, list[dict[str, Any]]]:
    chunk_index, tasks, master_seed, trials = args
    assert _WHOLE_MATRIX is not None and _WHOLE_BUILD_MAP is not None
    rows: list[dict[str, Any]] = []
    for task in tasks:
        for plan in _plans_for_pair_task(task, _WHOLE_BUILD_MAP):
            results = [run_trial(_WHOLE_MATRIX, plan.variant, master_seed, i) for i in range(trials)]
            row = _aggregate_variant(plan.variant, results)
            row.update(_variant_metadata(plan))
            rows.append(row)
    rows.sort(key=lambda r: str(r["variant_id"]))
    return chunk_index, rows


def _run_smoke_chunk(args: tuple[list[PairTask], int]) -> dict[str, Any]:
    tasks, master_seed = args
    assert _WHOLE_MATRIX is not None and _WHOLE_BUILD_MAP is not None
    cell_counts: dict[str, int] = defaultdict(int)
    winners: dict[str, int] = defaultdict(int)
    failures: list[dict[str, str]] = []
    executed = 0
    for task in tasks:
        for plan in _plans_for_pair_task(task, _WHOLE_BUILD_MAP):
            result = run_trial(_WHOLE_MATRIX, plan.variant, master_seed, 0)
            executed += 1
            cell = f"TL{plan.side_a_tl}-TL{plan.side_b_tl}"
            cell_counts[cell] += 1
            winners[result.winner] += 1
            if result.error:
                failures.append({"variant_id": plan.variant.id, "error": result.error})
    return {"executed": executed, "cell_counts": dict(cell_counts), "winners": dict(winners), "failures": failures}


def _chunks(items: list[Any], count: int) -> list[list[Any]]:
    count = max(1, min(count, len(items)))
    size = math.ceil(len(items) / count)
    return [items[i:i + size] for i in range(0, len(items), size)]


def run_full_pipeline_smoke(repo: Path, study_path: Path, outdir: Path, jobs: int = 24) -> dict[str, Any]:
    plan = build_plan(repo, study_path, outdir / "plan")
    doc, pairings = plan["doc"], plan["pairings"]
    tasks = [_pair_task(p) for p in pairings]
    jobs = max(1, min(int(jobs), len(tasks)))
    started = time.perf_counter()
    aggregate_cells: dict[str, int] = defaultdict(int)
    aggregate_winners: dict[str, int] = defaultdict(int)
    failures: list[dict[str, str]] = []
    if jobs == 1:
        _init_whole_worker(str(repo), doc["sourceMatrix"])
        results = [_run_smoke_chunk((tasks, int(doc["masterSeed"]))) ]
    else:
        chunks = _chunks(tasks, jobs * 8)
        ctx = get_context("spawn")
        results = []
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_init_whole_worker, initargs=(str(repo), doc["sourceMatrix"])) as ex:
            futures = [ex.submit(_run_smoke_chunk, (chunk, int(doc["masterSeed"]))) for chunk in chunks]
            for future in as_completed(futures):
                results.append(future.result())
    executed = 0
    for result in results:
        executed += int(result["executed"])
        for key, value in result["cell_counts"].items():
            aggregate_cells[key] += int(value)
        for key, value in result["winners"].items():
            aggregate_winners[key] += int(value)
        failures.extend(result["failures"])
    elapsed = time.perf_counter() - started
    expected = int(doc["expected"]["pipelineSmokeTrials"])
    failed_gates: list[str] = []
    if executed != expected:
        failed_gates.append(f"smoke-count:{executed}!={expected}")
    if failures:
        failed_gates.append(f"smoke-trial-errors:{len(failures)}")
    if len(aggregate_cells) != 81:
        failed_gates.append(f"ordered-tl-cell-coverage:{len(aggregate_cells)}!=81")
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "smoke_failures.csv", failures, ["variant_id", "error"] if failures else None)
    cell_rows = []
    for a in range(1, 10):
        for b in range(1, 10):
            cell_rows.append({"side_a_tl": a, "side_b_tl": b, "variants_executed": aggregate_cells.get(f"TL{a}-TL{b}", 0)})
    _write_csv(outdir / "smoke_tl_cell_summary.csv", cell_rows)
    summary = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 125,
        "mode": "full_pipeline_smoke",
        "variants": len(pairings) * 4,
        "trialsPerVariant": 1,
        "totalTrials": executed,
        "orderedTlCells": len(aggregate_cells),
        "winners": dict(sorted(aggregate_winners.items())),
        "trialErrors": len(failures),
        "elapsedSeconds": elapsed,
        "failedGates": failed_gates,
    }
    (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def _chunk_csv_path(tempdir: Path, index: int) -> Path:
    return tempdir / f"chunk-{index:05d}.csv"


def _write_chunk_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def _merge_chunk_csvs(tempdir: Path, output: Path) -> None:
    chunks = sorted(tempdir.glob("chunk-*.csv"))
    if not chunks:
        output.write_text("", encoding="utf-8")
        return
    with output.open("wb") as out:
        for i, chunk in enumerate(chunks):
            data = chunk.read_bytes()
            if i == 0:
                out.write(data)
            else:
                nl = data.find(b"\n")
                if nl >= 0:
                    out.write(data[nl + 1:])


def execute_substantive_streaming(repo: Path, doc: dict[str, Any], pairings: list[LadderPairing], out_csv: Path, trials: int, jobs: int) -> float:
    tasks = [_pair_task(p) for p in pairings]
    jobs = max(1, min(int(jobs), len(tasks)))
    started = time.perf_counter()
    chunk_count = min(len(tasks), max(jobs, jobs * 8))
    chunks = _chunks(tasks, chunk_count)
    tempdir = out_csv.parent / ".variant_chunks"
    if tempdir.exists():
        shutil.rmtree(tempdir)
    tempdir.mkdir(parents=True)
    try:
        if jobs == 1:
            _init_whole_worker(str(repo), doc["sourceMatrix"])
            for idx, chunk in enumerate(chunks):
                _, rows = _run_substantive_chunk((idx, chunk, int(doc["masterSeed"]), trials))
                _write_chunk_csv(_chunk_csv_path(tempdir, idx), rows)
        else:
            ctx = get_context("spawn")
            with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_init_whole_worker, initargs=(str(repo), doc["sourceMatrix"])) as ex:
                futures = [ex.submit(_run_substantive_chunk, (idx, chunk, int(doc["masterSeed"]), trials)) for idx, chunk in enumerate(chunks)]
                for future in as_completed(futures):
                    idx, rows = future.result()
                    _write_chunk_csv(_chunk_csv_path(tempdir, idx), rows)
        _merge_chunk_csvs(tempdir, out_csv)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)
    return time.perf_counter() - started


class WeightedOutcome:
    __slots__ = ("weight_trials", "wins", "losses", "draws", "unresolved", "errors", "turns")
    def __init__(self) -> None:
        self.weight_trials = 0.0
        self.wins = 0.0
        self.losses = 0.0
        self.draws = 0.0
        self.unresolved = 0.0
        self.errors = 0.0
        self.turns = 0.0

    def add(self, row: dict[str, str], weight: float, perspective: str = "A") -> None:
        trials = int(row["trials"])
        self.weight_trials += weight * trials
        if perspective == "A":
            self.wins += weight * int(row["wins_a"])
            self.losses += weight * int(row["wins_b"])
        else:
            self.wins += weight * int(row["wins_b"])
            self.losses += weight * int(row["wins_a"])
        self.draws += weight * int(row["draws"])
        self.unresolved += weight * int(row["unresolved"])
        self.errors += weight * int(row["errors"])
        self.turns += weight * trials * float(row["mean_turns"])

    def row(self) -> dict[str, Any]:
        decisive = self.wins + self.losses
        return {
            "weighted_trials": self.weight_trials,
            "conditional_win_rate": self.wins / decisive if decisive else 0.0,
            "draw_rate": self.draws / self.weight_trials if self.weight_trials else 0.0,
            "unresolved_rate": self.unresolved / self.weight_trials if self.weight_trials else 0.0,
            "error_rate": self.errors / self.weight_trials if self.weight_trials else 0.0,
            "mean_turns": self.turns / self.weight_trials if self.weight_trials else 0.0,
        }


def _pair_group_key(row: dict[str, str]) -> str:
    return row["pairing_id"]


def _normalized_pair_row(rows: list[dict[str, str]]) -> dict[str, Any]:
    if len(rows) != 4:
        raise ValueError(f"pairing {rows[0].get('pairing_id','?')} has {len(rows)} variants")
    first = rows[0]
    build1, build2 = first["build_1_id"], first["build_2_id"]
    outcome1 = WeightedOutcome()
    move_first = WeightedOutcome()
    move_second = WeightedOutcome()
    # Equal mirror weight inside the pairing: every variant represents one of four symmetry mirrors.
    for r in rows:
        perspective = "A" if r["side_a_build"] == build1 else "B"
        outcome1.add(r, 0.25, perspective)
        build1_moves_first = (r["movement_order"] == "SideAFirst" and perspective == "A") or (r["movement_order"] == "SideBFirst" and perspective == "B")
        (move_first if build1_moves_first else move_second).add(r, 0.5, perspective)
    overall = outcome1.row()
    mf, ms = move_first.row(), move_second.row()
    return {
        "pairing_id": first["pairing_id"],
        "tl_1": int(first["canonical_tl_1"]),
        "tl_2": int(first["canonical_tl_2"]),
        "delta_tl": int(first["delta_tl"]),
        "build_1": build1,
        "build_2": build2,
        "build_1_profile": first["side_a_weapon_profile"] if first["side_a_build"] == build1 else first["side_b_weapon_profile"],
        "build_2_profile": first["side_b_weapon_profile"] if first["side_b_build"] == build2 else first["side_a_weapon_profile"],
        "design_weight": float(first["base_design_weight"]),
        "build_1_conditional_win_rate": overall["conditional_win_rate"],
        "draw_rate": overall["draw_rate"],
        "unresolved_rate": overall["unresolved_rate"],
        "mean_turns": overall["mean_turns"],
        "build_1_first_win_rate": mf["conditional_win_rate"],
        "build_2_first_build_1_win_rate": ms["conditional_win_rate"],
        "mover_order_swing": abs(mf["conditional_win_rate"] - ms["conditional_win_rate"]),
    }


def analyze_substantive(variants_csv: Path, outdir: Path, expected_variants: int, trials: int) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    ordered: dict[tuple[int, int], WeightedOutcome] = defaultdict(WeightedOutcome)
    telemetry_sums: dict[tuple[int, int], dict[str, float]] = defaultdict(lambda: defaultdict(float))
    telemetry_weights: dict[tuple[int, int], float] = defaultdict(float)
    variant_count = 0
    trial_errors = 0
    pair_rows: list[dict[str, Any]] = []
    family: dict[tuple[int, int, str, str], WeightedOutcome] = defaultdict(WeightedOutcome)
    current_pair = ""
    current_rows: list[dict[str, str]] = []

    def finish_pair() -> None:
        nonlocal current_rows
        if not current_rows:
            return
        pr = _normalized_pair_row(current_rows)
        pair_rows.append(pr)
        current_rows = []

    with variants_csv.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            variant_count += 1
            trial_errors += int(row["errors"])
            key = (int(row["side_a_tl"]), int(row["side_b_tl"]))
            weight = float(row["ordered_cell_variant_weight"])
            ordered[key].add(row, weight, "A")
            fkey = (key[0], key[1], row["side_a_weapon_profile"], row["side_b_weapon_profile"])
            family[fkey].add(row, weight, "A")
            wt = weight * int(row["trials"])
            telemetry_weights[key] += wt
            for metric in TELEMETRY_CONTRACT:
                name = metric["metric"]
                telemetry_sums[key]["side_a_" + name] += wt * float(row["mean_a_" + name])
                telemetry_sums[key]["side_b_" + name] += wt * float(row["mean_b_" + name])
            if current_pair and row["pairing_id"] != current_pair:
                finish_pair()
            current_pair = row["pairing_id"]
            current_rows.append(row)
    finish_pair()

    tl_rows = []
    for a in range(1, 10):
        for b in range(1, 10):
            result = ordered[(a, b)].row()
            result.update({"side_a_tl": a, "side_b_tl": b, "delta_tl_a_minus_b": a - b})
            tl_rows.append(result)
    _write_csv(outdir / "tl_matchup_summary.csv", tl_rows)

    telemetry_rows = []
    for a in range(1, 10):
        for b in range(1, 10):
            key = (a, b)
            denom = telemetry_weights[key]
            r: dict[str, Any] = {"side_a_tl": a, "side_b_tl": b, "weighted_trials": denom}
            for metric in TELEMETRY_CONTRACT:
                name = metric["metric"]
                r["side_a_" + name] = telemetry_sums[key]["side_a_" + name] / denom if denom else 0.0
                r["side_b_" + name] = telemetry_sums[key]["side_b_" + name] / denom if denom else 0.0
            telemetry_rows.append(r)
    _write_csv(outdir / "tl_telemetry_summary.csv", telemetry_rows)

    family_rows = []
    for (a, b, pa, pb), acc in sorted(family.items()):
        r = acc.row()
        r.update({"side_a_tl": a, "side_b_tl": b, "side_a_profile": pa, "side_b_profile": pb})
        family_rows.append(r)
    _write_csv(outdir / "family_matchup_summary.csv", family_rows)

    # Pair-level normalized results support build, Delta-TL, and mover-order review without side-label contamination.
    _write_csv(outdir / "pairing_outcomes.csv", pair_rows)
    delta_acc: dict[int, WeightedOutcome] = defaultdict(WeightedOutcome)
    delta_simple: dict[int, list[tuple[float, float, float, float]]] = defaultdict(list)
    build_opp: dict[tuple[str, int], list[float]] = defaultdict(list)
    build_info: dict[str, tuple[int, str]] = {}
    movement_by_cell: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for pr in pair_rows:
        tl1, tl2 = int(pr["tl_1"]), int(pr["tl_2"])
        weight = float(pr["design_weight"])
        movement_by_cell[(tl1, tl2)].append((weight, float(pr["mover_order_swing"])))
        b1, b2 = pr["build_1"], pr["build_2"]
        build_info[b1] = (tl1, pr["build_1_profile"])
        build_info[b2] = (tl2, pr["build_2_profile"])
        build_opp[(b1, tl2)].append(float(pr["build_1_conditional_win_rate"]))
        build_opp[(b2, tl1)].append(1.0 - float(pr["build_1_conditional_win_rate"]))
        if tl2 > tl1:
            high_win = 1.0 - float(pr["build_1_conditional_win_rate"])
            delta_simple[tl2 - tl1].append((weight, high_win, float(pr["unresolved_rate"]), float(pr["mean_turns"])))
        else:
            # With both side assignments a same-TL population is structurally centered at 50%; retain actual unresolved/turn evidence.
            delta_simple[0].append((weight, 0.5, float(pr["unresolved_rate"]), float(pr["mean_turns"])))

    delta_rows = []
    for delta in range(0, 9):
        vals = delta_simple[delta]
        total_w = sum(v[0] for v in vals)
        delta_rows.append({
            "delta_tl": delta,
            "base_pairings": len(vals),
            "population_weight": total_w,
            "higher_tl_conditional_win_rate": (sum(w * x for w, x, _, _ in vals) / total_w if total_w else 0.5),
            "mean_unresolved_rate": (sum(w * x for w, _, x, _ in vals) / total_w if total_w else 0.0),
            "mean_turns": (sum(w * x for w, _, _, x in vals) / total_w if total_w else 0.0),
        })
    _write_csv(outdir / "delta_tl_summary.csv", delta_rows)

    build_rows = []
    for (bid, opp_tl), vals in sorted(build_opp.items()):
        tl, profile = build_info[bid]
        build_rows.append({
            "build_id": bid,
            "build_tl": tl,
            "opponent_tl": opp_tl,
            "weapon_profile": profile,
            "sampled_pairings": len(vals),
            "mean_conditional_win_rate": statistics.fmean(vals),
            "min_pairing_win_rate": min(vals),
            "max_pairing_win_rate": max(vals),
        })
    _write_csv(outdir / "build_opponent_tl_summary.csv", build_rows)

    move_rows = []
    for (a, b), vals in sorted(movement_by_cell.items()):
        tw = sum(w for w, _ in vals)
        swings = [s for _, s in vals]
        move_rows.append({
            "tl_1": a, "tl_2": b, "delta_tl": b - a, "base_pairings": len(vals),
            "weighted_mean_mover_order_swing": sum(w * s for w, s in vals) / tw if tw else 0.0,
            "median_mover_order_swing": statistics.median(swings) if swings else 0.0,
            "p95_mover_order_swing": sorted(swings)[min(len(swings)-1, math.floor(0.95 * (len(swings)-1)))] if swings else 0.0,
            "max_mover_order_swing": max(swings, default=0.0),
        })
    _write_csv(outdir / "movement_order_summary.csv", move_rows)

    failed: list[str] = []
    if variant_count != expected_variants:
        failed.append(f"variant-count:{variant_count}!={expected_variants}")
    if trial_errors:
        failed.append(f"trial-errors:{trial_errors}")
    if len(ordered) != 81:
        failed.append(f"ordered-tl-cells:{len(ordered)}!=81")
    if len(pair_rows) * 4 != variant_count:
        failed.append("pairing-mirror-integrity")
    if len(build_rows) != 84843:
        failed.append(f"build-opponent-tl-summary:{len(build_rows)}!=84843")
    analysis = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 125,
        "mode": "substantive",
        "variants": variant_count,
        "basePairings": len(pair_rows),
        "trialsPerVariant": trials,
        "totalTrials": variant_count * trials,
        "trialErrors": trial_errors,
        "orderedTlCells": len(ordered),
        "familySummaryRows": len(family_rows),
        "buildOpponentTlRows": len(build_rows),
        "telemetryMetrics": len(TELEMETRY_CONTRACT),
        "mixedTlShipsExecuted": False,
        "automaticPromotion": False,
        "balanceValidated": False,
        "failedGates": failed,
        "reviewSignals": {
            "balanceSignalsAreBlockingGates": False,
            "deltaTlSummary": delta_rows,
            "maxMovementOrderSwing": max((r["max_mover_order_swing"] for r in move_rows), default=0.0),
        },
    }
    (outdir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis


def run_substantive(repo: Path, study_path: Path, outdir: Path, trials_override: int | None = None, jobs: int = 24) -> dict[str, Any]:
    plan = build_plan(repo, study_path, outdir / "plan")
    doc, pairings = plan["doc"], plan["pairings"]
    trials = int(trials_override if trials_override is not None else doc["substantiveTrialsPerVariant"])
    outdir.mkdir(parents=True, exist_ok=True)
    elapsed = execute_substantive_streaming(repo, doc, pairings, outdir / "variants.csv", trials, jobs)
    analysis = analyze_substantive(outdir / "variants.csv", outdir, len(pairings) * 4, trials)
    analysis["elapsedSeconds"] = elapsed
    (outdir / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    return analysis


def run_whole_ladder_analysis(repo: Path, study_path: Path, outdir: Path, *, mode: str, trials: int | None = None, jobs: int = 24) -> dict[str, Any]:
    if mode == "plan":
        return build_plan(repo, study_path, outdir)["summary"]
    if mode == "smoke":
        return run_full_pipeline_smoke(repo, study_path, outdir, jobs)
    if mode == "run":
        return run_substantive(repo, study_path, outdir, trials, jobs)
    raise ValueError(f"unsupported whole-ladder mode: {mode}")
