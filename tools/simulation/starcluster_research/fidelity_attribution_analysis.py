from __future__ import annotations

import csv
import io
import json
import math
import shutil
import statistics
import time
import zipfile
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
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
from .ecology import CandidateMatrix, EcologyVariant
from .canonical_combat import (
    FULL_MAP_GEOMETRY,
    FullMapTelemetry,
    aggregate_full_map_variant,
    mirror_equivalent,
    run_trial_full_map,
)
from .rng import derive_seed
from .study import canonicalize_relocated_references, load_json
from .whole_ladder_analysis import (
    PAIRING_SEED,
    WeightedOutcome,
    _build_meta,
    _normalized_pair_row,
    _profile_name,
    _shuffle,
    _write_csv,
    generate_pairings,
)

SCHEMA = "star-cluster-cp126-system-map-fidelity-era-attribution-v0.1"
RESULT_SCHEMA = "star-cluster-cp126-system-map-fidelity-era-attribution-results-v0.1"
DEFAULT_STUDY = "docs/archive/testing/pre-cp165-active/cp126_system_map_fidelity_era_attribution_study_v0_1.json"
MASTER_SEED = 12620260816

FULL_MAP_TELEMETRY_CONTRACT: tuple[dict[str, str], ...] = (
    {"metric":"search_moves","dimension":"movement","owner":"actor","kind":"raw_counter"},
    {"metric":"adaptive_close_orders","dimension":"tactics","owner":"actor","kind":"raw_counter"},
    {"metric":"adaptive_open_orders","dimension":"tactics","owner":"actor","kind":"raw_counter"},
    {"metric":"adaptive_maintain_orders","dimension":"tactics","owner":"actor","kind":"raw_counter"},
    {"metric":"adaptive_standoff_orders","dimension":"tactics","owner":"actor","kind":"raw_counter"},
    {"metric":"boundary_end_moves","dimension":"movement","owner":"actor","kind":"raw_counter"},
    {"metric":"contact_established_turn","dimension":"information","owner":"observer","kind":"raw_turn"},
    {"metric":"missile_movement_hexes","dimension":"missile_geometry","owner":"attacker","kind":"raw_counter"},
    {"metric":"missile_reroutes","dimension":"missile_geometry","owner":"attacker","kind":"raw_counter"},
    {"metric":"missile_target_movement_reroutes","dimension":"missile_geometry","owner":"attacker","kind":"raw_counter"},
    {"metric":"missile_range_exhausted","dimension":"missile_geometry","owner":"attacker","kind":"raw_counter"},
    {"metric":"maximum_missile_distance_traveled","dimension":"missile_geometry","owner":"attacker","kind":"raw_quantity"},
    {"metric":"maximum_own_attack_range","dimension":"tactics","owner":"actor","kind":"raw_quantity"},
    {"metric":"maximum_observed_opponent_attack_range","dimension":"tactics","owner":"observer","kind":"raw_quantity"},
)
ALL_TELEMETRY_CONTRACT = TELEMETRY_CONTRACT + FULL_MAP_TELEMETRY_CONTRACT

ERA_CLASS = {
    (1,2): "baseline_to_low_entry",
    (2,3): "low_maturation",
    (3,4): "low_maturation",
    (4,5): "low_to_mid_boundary",
    (5,6): "mid_maturation_integration",
    (6,7): "mid_maturation",
    (7,8): "mid_to_high_boundary",
    (8,9): "high_maturation",
}


@dataclass(frozen=True, slots=True)
class FidelityTask:
    task_id: str
    group: str
    kind: str
    tl_low: int
    tl_high: int
    build_1_id: str
    build_2_id: str
    build_3_id: str = ""
    build_4_id: str = ""
    design_weight: float = 1.0

    @property
    def variant_count(self) -> int:
        return 4 if self.kind == "pair" else 16


@dataclass(frozen=True, slots=True)
class FidelityVariantPlan:
    variant: EcologyVariant
    task_id: str
    pairing_id: str
    group: str
    condition: str
    canonical_tl_1: int
    canonical_tl_2: int
    build_1_id: str
    build_2_id: str
    orientation: str
    side_a_tl: int
    side_b_tl: int
    base_design_weight: float
    side_a_meta: dict[str, Any]
    side_b_meta: dict[str, Any]


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    expected_top = {
        "schemaVersion": SCHEMA,
        "checkpoint": 126,
        "acceptedPureTlStudy": 125,
        "acceptedReferenceBaseline": 123,
        "acceptedInstrumentationBaseline": 124,
        "sourceMatrix": DEFAULT_MATRIX,
        "shipTechnologyPolicy": "pure_same_tl_components_per_ship",
        "mixedTlShipsExecuted": False,
        "substantiveTrialsPerVariant": 250,
        "recommendedJobs": 24,
    }
    for key, value in expected_top.items():
        if doc.get(key) != value:
            errors.append(key)
    expected_counts = {
        "legalBuilds": 9427,
        "adjacentPopulationTasks": 9220,
        "matchedCompositionTasks": 7699,
        "movementHotspotTasks": 4008,
        "swarmerLifecycleTasks": 1296,
        "energyIsolationTasks": 1728,
        "lateMissileGeometryTasks": 1727,
        "compactTasks": 25678,
        "generatedVariants": 139000,
        "pipelineSmokeTrials": 139000,
        "substantiveTrials": 34750000,
        "telemetryMetrics": 61,
    }
    for key, value in expected_counts.items():
        if int(doc.get("expected", {}).get(key, -1)) != value:
            errors.append(f"expected.{key}")
    if doc.get("automaticPromotion") is not False or doc.get("balanceValidated") is not False:
        errors.append("promotionBoundary")
    if doc.get("fullMap", {}).get("radius") != 5 or doc.get("fullMap", {}).get("cells") != 91:
        errors.append("fullMap")
    if doc.get("fullMap", {}).get("preContactSearchHexesPerActivation") != 1:
        errors.append("fullMap.preContactSearchHexesPerActivation")
    if doc.get("fullMap", {}).get("actualMissilePursuit") is not True:
        errors.append("fullMap.actualMissilePursuit")
    if doc.get("symmetryGate", {}).get("blocking") is not True:
        errors.append("symmetryGate.blocking")
    return errors


def _composition_key(b: BaselineBuild) -> tuple[Any, ...]:
    return (
        b.weapon_family, b.missile_payload, b.main_count, b.reactor_count, b.shield,
        b.ecm_count, b.eccm_count, b.pds_family, b.shield_hardener,
    )


def _swarmer_attacker_key(b: BaselineBuild) -> tuple[Any, ...]:
    return (b.main_count, b.reactor_count, b.shield, b.ecm_count, b.eccm_count, b.pds_family, b.shield_hardener)


def _swarmer_defender_key(b: BaselineBuild) -> tuple[Any, ...]:
    return (b.weapon_family, b.missile_payload, b.main_count, b.reactor_count, b.shield, b.ecm_count, b.eccm_count, b.shield_hardener)


def _energy_attacker_key(b: BaselineBuild) -> tuple[Any, ...]:
    return (b.main_count, b.reactor_count, b.shield, b.ecm_count, b.eccm_count, b.pds_family, b.shield_hardener)


def _energy_defender_key(b: BaselineBuild) -> tuple[Any, ...]:
    return (b.weapon_family, b.missile_payload, b.main_count, b.reactor_count, b.ecm_count, b.eccm_count, b.pds_family, b.shield_hardener)


def _matched_pairs(left: Iterable[BaselineBuild], right: Iterable[BaselineBuild], key_fn) -> list[tuple[BaselineBuild, BaselineBuild]]:
    a = {key_fn(b): b for b in left}
    b = {key_fn(x): x for x in right}
    return [(a[k], b[k]) for k in sorted(set(a) & set(b), key=repr)]


def generate_tasks(builds: list[BaselineBuild], pairing_seed: int = PAIRING_SEED) -> list[FidelityTask]:
    by_tl = {tl: [b for b in builds if b.tl == tl] for tl in range(1,10)}
    tasks: list[FidelityTask] = []
    cp125 = generate_pairings(builds, pairing_seed)

    for p in cp125:
        if p.tl_2 == p.tl_1 + 1:
            tasks.append(FidelityTask(
                p.pairing_id, "adjacent_population", "pair", p.tl_1, p.tl_2,
                p.build_1.id, p.build_2.id, design_weight=p.design_weight,
            ))

    for low in range(1,9):
        pairs = _matched_pairs(by_tl[low], by_tl[low+1], _composition_key)
        for i, (a,b) in enumerate(pairs, start=1):
            tasks.append(FidelityTask(
                f"matched-tl{low:02d}-tl{low+1:02d}-p{i:05d}",
                "matched_composition", "pair", low, low+1, a.id, b.id,
            ))

    for p in cp125:
        if p.tl_1 == p.tl_2 and p.tl_1 in (2,7):
            tasks.append(FidelityTask(
                p.pairing_id, "movement_hotspot", "pair", p.tl_1, p.tl_2,
                p.build_1.id, p.build_2.id, design_weight=p.design_weight,
            ))

    for tl in (7,8,9):
        gp = [b for b in by_tl[tl] if b.weapon_family == "Missile" and b.missile_payload == "GP"]
        sw = [b for b in by_tl[tl] if b.weapon_family == "Missile" and b.missile_payload == "Swarmer"]
        attackers = _matched_pairs(gp, sw, _swarmer_attacker_key)
        no_pds = [b for b in by_tl[tl] if b.pds_family == ""]
        amm = [b for b in by_tl[tl] if b.pds_family == "AMM"]
        defenders = _matched_pairs(no_pds, amm, _swarmer_defender_key)
        attackers = _shuffle([pair for pair in attackers], derive_seed(pairing_seed, "swarmer", tl, "attack"))
        defenders = _shuffle([pair for pair in defenders], derive_seed(pairing_seed, "swarmer", tl, "defense"))
        count = max(len(attackers), len(defenders))
        for i in range(count):
            gp_b, sw_b = attackers[i % len(attackers)]
            no_b, amm_b = defenders[i % len(defenders)]
            tasks.append(FidelityTask(
                f"swarmer-tl{tl:02d}-p{i+1:04d}", "swarmer_lifecycle", "quad", tl, tl,
                gp_b.id, sw_b.id, no_b.id, amm_b.id,
            ))

    # Reuse exact CP125 same-TL Missile-vs-Missile pair IDs at TL8/TL9 so
    # late-Missile unresolved duration and pursuit behavior can be compared
    # directly against the frozen axial-lane control.
    for p in cp125:
        if (
            p.tl_1 == p.tl_2
            and p.tl_1 in (8, 9)
            and p.build_1.weapon_family == "Missile"
            and p.build_2.weapon_family == "Missile"
        ):
            tasks.append(FidelityTask(
                p.pairing_id, "late_missile_geometry", "pair", p.tl_1, p.tl_2,
                p.build_1.id, p.build_2.id, design_weight=p.design_weight,
            ))

    for tl in (7,8,9):
        energy = [b for b in by_tl[tl] if b.weapon_family == "Energy"]
        kinetic = [b for b in by_tl[tl] if b.weapon_family == "Kinetic"]
        attackers = _matched_pairs(energy, kinetic, _energy_attacker_key)
        no_shield = [b for b in by_tl[tl] if not b.shield]
        shield = [b for b in by_tl[tl] if b.shield]
        defenders = _matched_pairs(no_shield, shield, _energy_defender_key)
        attackers = _shuffle([pair for pair in attackers], derive_seed(pairing_seed, "energy", tl, "attack"))
        defenders = _shuffle([pair for pair in defenders], derive_seed(pairing_seed, "energy", tl, "defense"))
        count = max(len(attackers), len(defenders))
        for i in range(count):
            e_b, k_b = attackers[i % len(attackers)]
            no_b, sh_b = defenders[i % len(defenders)]
            tasks.append(FidelityTask(
                f"energy-tl{tl:02d}-p{i+1:04d}", "energy_isolation", "quad", tl, tl,
                e_b.id, k_b.id, no_b.id, sh_b.id,
            ))

    tasks.sort(key=lambda x: (x.group, x.task_id))
    return tasks


def _pair_plans(
    task: FidelityTask,
    build1: BaselineBuild,
    build2: BaselineBuild,
    condition: str,
    physical1: str,
    physical2: str,
) -> list[FidelityVariantPlan]:
    plans: list[FidelityVariantPlan] = []
    pairing_id = task.task_id if condition == "baseline" else f"{task.task_id}-{condition}"
    for orientation, a0, b0, phys_a, phys_b in (
        ("forward", build1, build2, physical1, physical2),
        ("reverse", build2, build1, physical2, physical1),
    ):
        ea = _build_to_ecology(a0, "cp126-full-map")
        eb = _build_to_ecology(b0, "cp126-full-map")
        for movement in ("SideAFirst", "SideBFirst"):
            suffix = "afirst" if movement == "SideAFirst" else "bfirst"
            variant = EcologyVariant(
                id=f"{pairing_id}-{orientation}-{suffix}",
                tl=a0.tl,
                side_a=ea,
                side_b=eb,
                movement_order=movement,
                geometry=FULL_MAP_GEOMETRY,
                population="cp126_fidelity_attribution",
                scenario_group=task.task_id,
                perturbation=condition,
                physical_id_a=phys_a,
                physical_id_b=phys_b,
            )
            plans.append(FidelityVariantPlan(
                variant, task.task_id, pairing_id, task.group, condition,
                build1.tl, build2.tl, build1.id, build2.id, orientation,
                a0.tl, b0.tl, task.design_weight, _build_meta(a0), _build_meta(b0),
            ))
    return plans


def _plans_for_task(task: FidelityTask, build_map: dict[str, BaselineBuild]) -> list[FidelityVariantPlan]:
    if task.kind == "pair":
        return _pair_plans(
            task, build_map[task.build_1_id], build_map[task.build_2_id], "baseline",
            f"{task.task_id}:ship1", f"{task.task_id}:ship2",
        )
    if task.group == "swarmer_lifecycle":
        gp, sw = build_map[task.build_1_id], build_map[task.build_2_id]
        no, amm = build_map[task.build_3_id], build_map[task.build_4_id]
        cases = (
            ("GP_noPDS", gp, no), ("GP_AMM", gp, amm),
            ("Swarmer_noPDS", sw, no), ("Swarmer_AMM", sw, amm),
        )
    elif task.group == "energy_isolation":
        energy, kinetic = build_map[task.build_1_id], build_map[task.build_2_id]
        no, shield = build_map[task.build_3_id], build_map[task.build_4_id]
        cases = (
            ("Energy_noShield", energy, no), ("Energy_Shield", energy, shield),
            ("Kinetic_noShield", kinetic, no), ("Kinetic_Shield", kinetic, shield),
        )
    else:
        raise ValueError(f"unknown quad task group: {task.group}")
    out: list[FidelityVariantPlan] = []
    for condition, attacker, defender in cases:
        out.extend(_pair_plans(
            task, attacker, defender, condition,
            f"{task.task_id}:attacker", f"{task.task_id}:defender",
        ))
    return out


def _variant_metadata(plan: FidelityVariantPlan) -> dict[str, Any]:
    row: dict[str, Any] = {
        "task_id": plan.task_id,
        "pairing_id": plan.pairing_id,
        "study_group": plan.group,
        "condition": plan.condition,
        "canonical_tl_1": plan.canonical_tl_1,
        "canonical_tl_2": plan.canonical_tl_2,
        "delta_tl": plan.canonical_tl_2 - plan.canonical_tl_1,
        "build_1_id": plan.build_1_id,
        "build_2_id": plan.build_2_id,
        "orientation": plan.orientation,
        "side_a_tl": plan.side_a_tl,
        "side_b_tl": plan.side_b_tl,
        "base_design_weight": plan.base_design_weight,
    }
    for prefix, meta in (("side_a_", plan.side_a_meta), ("side_b_", plan.side_b_meta)):
        for key, value in meta.items():
            if key == "build_id":
                continue
            row[prefix + key] = value
    return row


def _task_rows(tasks: list[FidelityTask]) -> list[dict[str, Any]]:
    return [
        {
            "task_id": t.task_id, "group": t.group, "kind": t.kind,
            "tl_low": t.tl_low, "tl_high": t.tl_high,
            "build_1": t.build_1_id, "build_2": t.build_2_id,
            "build_3": t.build_3_id, "build_4": t.build_4_id,
            "design_weight": t.design_weight, "variants": t.variant_count,
        }
        for t in tasks
    ]


def _count_by_group(tasks: list[FidelityTask]) -> dict[str, dict[str, int]]:
    groups: dict[str, dict[str,int]] = defaultdict(lambda: {"tasks":0,"variants":0})
    for task in tasks:
        groups[task.group]["tasks"] += 1
        groups[task.group]["variants"] += task.variant_count
    return dict(groups)


def _build_envelope_rows(builds: list[BaselineBuild]) -> list[dict[str, Any]]:
    by_tl = {tl:[b for b in builds if b.tl == tl] for tl in range(1,10)}
    rows=[]
    for low in range(1,9):
        a={_composition_key(b) for b in by_tl[low]}; b={_composition_key(x) for x in by_tl[low+1]}
        rows.append({
            "low_tl":low,"high_tl":low+1,"era_class":ERA_CLASS[(low,low+1)],
            "low_legal_builds":len(by_tl[low]),"high_legal_builds":len(by_tl[low+1]),
            "common_compositions":len(a & b),"high_only_compositions":len(b-a),"low_only_compositions":len(a-b),
            "low_dual_main":sum(x.main_count==2 for x in by_tl[low]),
            "high_dual_main":sum(x.main_count==2 for x in by_tl[low+1]),
            "low_dual_reactor":sum(x.reactor_count==2 for x in by_tl[low]),
            "high_dual_reactor":sum(x.reactor_count==2 for x in by_tl[low+1]),
        })
    return rows


def _transition_delta_rows(repo: Path, source_matrix: str) -> list[dict[str, Any]]:
    doc = json.loads((repo / source_matrix).read_text(encoding="utf-8"))
    rows=[]
    for low in range(1,9):
        for profile in doc["profileOrder"]:
            a=doc["profiles"][profile][str(low)]; b=doc["profiles"][profile][str(low+1)]
            for field in sorted(set(a) | set(b)):
                if field == "tl":
                    continue
                va, vb = a.get(field), b.get(field)
                if va == vb:
                    continue
                numeric_delta=""
                if isinstance(va,(int,float)) and not isinstance(va,bool) and isinstance(vb,(int,float)) and not isinstance(vb,bool):
                    numeric_delta=vb-va
                rows.append({
                    "low_tl":low,"high_tl":low+1,"era_class":ERA_CLASS[(low,low+1)],
                    "profile":profile,"field":field,"low_value":json.dumps(va,ensure_ascii=False),
                    "high_value":json.dumps(vb,ensure_ascii=False),"numeric_delta":numeric_delta,
                })
    return rows


def build_plan(repo: Path, study_path: Path, outdir: Path | None = None) -> dict[str, Any]:
    doc=load_json(study_path)
    errors=validate_study(doc)
    if errors:
        raise ValueError("invalid CP126 study: "+",".join(errors))
    catalog=BaselineCatalog(repo,doc["sourceMatrix"])
    raw,builds=enumerate_legal_builds(catalog)
    if raw != 14112 or len(builds) != 9427:
        raise ValueError(f"CP124 legal-build foundation drift: {raw}/{len(builds)}")
    tasks=generate_tasks(builds,int(doc["pairingSeed"]))
    groups=_count_by_group(tasks)
    variants=sum(t.variant_count for t in tasks)
    failed=[]
    expected=doc["expected"]
    checks={
        "compactTasks":len(tasks),"generatedVariants":variants,
        "adjacentPopulationTasks":groups.get("adjacent_population",{}).get("tasks",0),
        "matchedCompositionTasks":groups.get("matched_composition",{}).get("tasks",0),
        "movementHotspotTasks":groups.get("movement_hotspot",{}).get("tasks",0),
        "swarmerLifecycleTasks":groups.get("swarmer_lifecycle",{}).get("tasks",0),
        "energyIsolationTasks":groups.get("energy_isolation",{}).get("tasks",0),
        "lateMissileGeometryTasks":groups.get("late_missile_geometry",{}).get("tasks",0),
    }
    for key,actual in checks.items():
        if int(actual)!=int(expected[key]): failed.append(f"{key}:{actual}!={expected[key]}")
    planned=variants*int(doc["substantiveTrialsPerVariant"])
    if planned != int(expected["substantiveTrials"]): failed.append(f"substantiveTrials:{planned}!={expected['substantiveTrials']}")
    if len(ALL_TELEMETRY_CONTRACT)!=int(expected["telemetryMetrics"]): failed.append("telemetryMetrics")
    summary={
        "schemaVersion":RESULT_SCHEMA,"checkpoint":126,"mode":"plan","rawBuildCombinations":raw,"legalBuilds":len(builds),
        "compactTasks":len(tasks),"generatedVariants":variants,"pipelineSmokeTrials":variants,
        "substantiveTrialsPerVariant":int(doc["substantiveTrialsPerVariant"]),"plannedSubstantiveTrials":planned,
        "telemetryMetrics":len(ALL_TELEMETRY_CONTRACT),"groupCounts":groups,"mixedTlShipsExecuted":False,
        "balanceValidated":False,"automaticPromotion":False,"failedGates":failed,
    }
    if outdir is not None:
        outdir.mkdir(parents=True,exist_ok=True)
        _write_csv(outdir/"tasks.csv",_task_rows(tasks))
        _write_csv(outdir/"build_envelope_transitions.csv",_build_envelope_rows(builds))
        _write_csv(outdir/"technology_transition_delta_ledger.csv",_transition_delta_rows(repo,doc["sourceMatrix"]))
        (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return {"doc":doc,"catalog":catalog,"builds":builds,"tasks":tasks,"summary":summary}


_WORK_MATRIX: CandidateMatrix | None = None
_WORK_BUILD_MAP: dict[str,BaselineBuild] | None = None


def _init_worker(repo: str, matrix_relative_path: str) -> None:
    global _WORK_MATRIX,_WORK_BUILD_MAP
    catalog=BaselineCatalog(Path(repo),matrix_relative_path)
    _WORK_MATRIX=catalog.matrix
    _,builds=enumerate_legal_builds(catalog)
    _WORK_BUILD_MAP={b.id:b for b in builds}


def _run_task_chunk(args: tuple[int,list[FidelityTask],int,int]) -> tuple[int,list[dict[str,Any]]]:
    idx,tasks,seed,trials=args
    assert _WORK_MATRIX is not None and _WORK_BUILD_MAP is not None
    rows=[]
    for task in tasks:
        for plan in _plans_for_task(task,_WORK_BUILD_MAP):
            results=[run_trial_full_map(_WORK_MATRIX,plan.variant,seed,i) for i in range(trials)]
            row=aggregate_full_map_variant(plan.variant,results)
            row.update(_variant_metadata(plan))
            rows.append(row)
    rows.sort(key=lambda r:str(r["variant_id"]))
    return idx,rows


def _chunks(items:list[Any],count:int)->list[list[Any]]:
    count=max(1,min(count,len(items))); size=math.ceil(len(items)/count)
    return [items[i:i+size] for i in range(0,len(items),size)]


def _write_chunk(path:Path,rows:list[dict[str,Any]])->None:
    if not rows:return
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)


def _merge_chunks(tempdir:Path,output:Path)->None:
    chunks=sorted(tempdir.glob("chunk-*.csv"))
    with output.open("wb") as out:
        for i,p in enumerate(chunks):
            data=p.read_bytes()
            if i==0: out.write(data)
            else:
                nl=data.find(b"\n");out.write(data[nl+1:] if nl>=0 else data)


def execute_streaming(repo:Path,doc:dict[str,Any],tasks:list[FidelityTask],out_csv:Path,trials:int,jobs:int)->float:
    jobs=max(1,min(int(jobs),len(tasks))); started=time.perf_counter()
    chunks=_chunks(tasks,min(len(tasks),max(jobs,jobs*8)))
    tempdir=out_csv.parent/".variant_chunks"
    if tempdir.exists():shutil.rmtree(tempdir)
    tempdir.mkdir(parents=True)
    try:
        if jobs==1:
            _init_worker(str(repo),doc["sourceMatrix"])
            for idx,chunk in enumerate(chunks):
                _,rows=_run_task_chunk((idx,chunk,int(doc["masterSeed"]),trials));_write_chunk(tempdir/f"chunk-{idx:05d}.csv",rows)
        else:
            ctx=get_context("spawn")
            with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_init_worker,initargs=(str(repo),doc["sourceMatrix"])) as ex:
                futures=[ex.submit(_run_task_chunk,(idx,chunk,int(doc["masterSeed"]),trials)) for idx,chunk in enumerate(chunks)]
                for fut in as_completed(futures):
                    idx,rows=fut.result();_write_chunk(tempdir/f"chunk-{idx:05d}.csv",rows)
        _merge_chunks(tempdir,out_csv)
    finally:
        shutil.rmtree(tempdir,ignore_errors=True)
    return time.perf_counter()-started


def run_smoke(repo:Path,study_path:Path,outdir:Path,jobs:int=24)->dict[str,Any]:
    plan=build_plan(repo,study_path,outdir/"plan")
    doc,tasks=plan["doc"],plan["tasks"]
    outdir.mkdir(parents=True,exist_ok=True)
    elapsed=execute_streaming(repo,doc,tasks,outdir/"variants.csv",1,jobs)
    group_counts=defaultdict(int);errors=0;variants=0
    with (outdir/"variants.csv").open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            variants+=1;group_counts[row["study_group"]]+=1;errors+=int(row["errors"])
    failed=[]
    if variants!=int(doc["expected"]["pipelineSmokeTrials"]):failed.append(f"smoke-count:{variants}")
    if errors:failed.append(f"trial-errors:{errors}")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":126,"mode":"smoke","variants":variants,"totalTrials":variants,
             "trialErrors":errors,"groupVariantCounts":dict(group_counts),"elapsedSeconds":elapsed,"failedGates":failed}
    (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def run_symmetry_gate(repo:Path,study_path:Path,outdir:Path)->dict[str,Any]:
    plan=build_plan(repo,study_path,None);doc,catalog,builds=plan["doc"],plan["catalog"],plan["builds"]
    by_tl={tl:sorted([b for b in builds if b.tl==tl],key=lambda b:b.id) for tl in range(1,10)}
    comparisons=0;mismatches=[]
    trials=int(doc["symmetryGate"]["trialsPerCase"]); cases_per_tl=int(doc["symmetryGate"]["casesPerTl"])
    for tl in range(1,10):
        group=by_tl[tl]
        pairs=[]
        for i in range(cases_per_tl-1):
            left=group[(i+1)*len(group)//(cases_per_tl+1)]
            right=group[(cases_per_tl-i)*len(group)//(cases_per_tl+2)]
            if left.id==right.id:right=group[(group.index(right)+1)%len(group)]
            pairs.append((left,right,f"distinct-{i+1}"))
        same=group[len(group)//2];pairs.append((same,same,"identical-build"))
        for case_index,(left,right,label) in enumerate(pairs):
            for first in ("SideAFirst","SideBFirst"):
                mirrored="SideBFirst" if first=="SideAFirst" else "SideAFirst"
                scenario=f"cp126-symmetry-tl{tl}-{case_index}-{label}"
                e1=_build_to_ecology(left,"cp126-symmetry");e2=_build_to_ecology(right,"cp126-symmetry")
                for trial in range(trials):
                    v1=EcologyVariant(f"sym-{tl}-{case_index}-a",tl,e1,e2,first,geometry=FULL_MAP_GEOMETRY,
                        population="cp126_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship1",physical_id_b=scenario+":ship2")
                    v2=EcologyVariant(f"sym-{tl}-{case_index}-b",tl,e2,e1,mirrored,geometry=FULL_MAP_GEOMETRY,
                        population="cp126_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship2",physical_id_b=scenario+":ship1")
                    r1=run_trial_full_map(catalog.matrix,v1,int(doc["masterSeed"]),trial)
                    r2=run_trial_full_map(catalog.matrix,v2,int(doc["masterSeed"]),trial)
                    comparisons+=1
                    if not mirror_equivalent(r1,r2):
                        mismatches.append({"tl":tl,"case":label,"first":first,"trial":trial,"build1":left.id,"build2":right.id})
                        if len(mismatches)>=20:break
                if len(mismatches)>=20:break
            if len(mismatches)>=20:break
        if len(mismatches)>=20:break
    expected=9*cases_per_tl*2*trials
    failed=[]
    if comparisons!=expected:failed.append(f"comparisons:{comparisons}!={expected}")
    if mismatches:failed.append(f"mirror-mismatches:{len(mismatches)}")
    outdir.mkdir(parents=True,exist_ok=True)
    _write_csv(outdir/"symmetry_mismatches.csv",mismatches,["tl","case","first","trial","build1","build2"] if mismatches else None)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":126,"mode":"symmetry_gate","comparisons":comparisons,
             "combatExecutions":comparisons*2,"mismatches":len(mismatches),"failedGates":failed}
    (outdir/"analysis.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def _weighted_outcome(rows:list[dict[str,Any]], high:bool=False)->dict[str,float]:
    tw=sum(float(r["design_weight"]) for r in rows)
    if not tw:return {"conditional_win_rate":0.0,"unresolved_rate":0.0,"mean_turns":0.0}
    win=sum(float(r["design_weight"])*(1.0-float(r["build_1_conditional_win_rate"]) if high else float(r["build_1_conditional_win_rate"])) for r in rows)/tw
    return {"conditional_win_rate":win,
            "unresolved_rate":sum(float(r["design_weight"])*float(r["unresolved_rate"]) for r in rows)/tw,
            "mean_turns":sum(float(r["design_weight"])*float(r["mean_turns"]) for r in rows)/tw}


def _load_cp125_pairs(repo:Path,relative_archive:str)->list[dict[str,str]]:
    archive=repo/relative_archive
    with zipfile.ZipFile(archive) as z:
        name="checkpoint-125/pure-tl-whole-ladder-study/pairing_outcomes.csv"
        text=z.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def _movement_stats(rows:list[dict[str,Any]])->dict[str,float]:
    if not rows:return {"weighted_mean":0.0,"median":0.0,"p95":0.0,"max":0.0,"gt20":0.0,"gt50":0.0}
    tw=sum(float(r["design_weight"]) for r in rows); swings=[float(r["mover_order_swing"]) for r in rows]
    s=sorted(swings)
    return {
        "weighted_mean":sum(float(r["design_weight"])*float(r["mover_order_swing"]) for r in rows)/tw,
        "median":statistics.median(swings),"p95":s[min(len(s)-1,math.floor(.95*(len(s)-1)))],"max":max(swings),
        "gt20":sum(x>=.20 for x in swings)/len(swings),"gt50":sum(x>=.50 for x in swings)/len(swings),
    }


def _perspective_metric(row:dict[str,str], build1:str, metric:str, full:bool=False)->tuple[float,float]:
    side1="a" if row["side_a_build"]==build1 else "b"; side2="b" if side1=="a" else "a"
    return float(row[f"mean_{side1}_{metric}"]),float(row[f"mean_{side2}_{metric}"])


def analyze_substantive(repo:Path,doc:dict[str,Any],variants_csv:Path,outdir:Path,expected_variants:int,trials:int)->dict[str,Any]:
    outdir.mkdir(parents=True,exist_ok=True)
    pair_rows=[];current="";buffer=[];variant_count=0;trial_errors=0
    telemetry_acc:dict[tuple[str,int,int],dict[str,float]]=defaultdict(lambda:defaultdict(float))
    telemetry_w:dict[tuple[str,int,int],float]=defaultdict(float)
    isolation_acc:dict[tuple[str,int,str],dict[str,float]]=defaultdict(lambda:defaultdict(float))
    isolation_w:dict[tuple[str,int,str],float]=defaultdict(float)

    def finish():
        nonlocal buffer
        if not buffer:return
        pr=_normalized_pair_row(buffer)
        pr["study_group"]=buffer[0]["study_group"];pr["condition"]=buffer[0]["condition"];pr["task_id"]=buffer[0]["task_id"]
        pair_rows.append(pr);buffer=[]

    with variants_csv.open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            variant_count+=1;trial_errors+=int(row["errors"])
            if current and row["pairing_id"]!=current:finish()
            current=row["pairing_id"];buffer.append(row)
            group=row["study_group"]
            if group in ("adjacent_population","matched_composition"):
                low=int(row["canonical_tl_1"]);high=int(row["canonical_tl_2"]);key=(group,low,high)
                weight=float(row["base_design_weight"])/4.0*int(row["trials"]);telemetry_w[key]+=weight
                high_build=row["build_2_id"]
                high_side="a" if row["side_a_build"]==high_build else "b";low_side="b" if high_side=="a" else "a"
                for metric in ALL_TELEMETRY_CONTRACT:
                    name=metric["metric"]
                    telemetry_acc[key]["high_"+name]+=weight*float(row[f"mean_{high_side}_{name}"])
                    telemetry_acc[key]["low_"+name]+=weight*float(row[f"mean_{low_side}_{name}"])
            if group in ("swarmer_lifecycle","energy_isolation"):
                tl=int(row["canonical_tl_1"]);cond=row["condition"];key=(group,tl,cond)
                weight=float(row["base_design_weight"])/4.0*int(row["trials"]);isolation_w[key]+=weight
                attacker=row["build_1_id"]
                a_side="a" if row["side_a_build"]==attacker else "b";d_side="b" if a_side=="a" else "a"
                # raw outcome counts are normalized later from pairing rows; telemetry is perspective-normalized here.
                for metric in ("missile_launches","direct_shots","direct_hits"):
                    isolation_acc[key]["attacker_"+metric]+=weight*float(row[f"mean_{a_side}_{metric}"])
                for metric in ("missile_terminal_arrivals","missile_guidance_attempts","missile_hits","pds_attempts","pds_intercepts",
                               "shield_penetration_bypassed","shield_absorbed","armor_penetration_bypassed","armor_prevented","hull_damage"):
                    isolation_acc[key]["defender_"+metric]+=weight*float(row[f"mean_{d_side}_{metric}"])
                for metric in ("missile_movement_hexes","missile_target_movement_reroutes","missile_range_exhausted","maximum_missile_distance_traveled"):
                    isolation_acc[key]["attacker_"+metric]+=weight*float(row[f"mean_{a_side}_{metric}"])
    finish()
    _write_csv(outdir/"normalized_pairing_outcomes.csv",pair_rows)

    adjacent=[];matched=[]
    for low in range(1,9):
        for group,target in (("adjacent_population",adjacent),("matched_composition",matched)):
            rows=[r for r in pair_rows if r["study_group"]==group and int(r["tl_1"])==low and int(r["tl_2"])==low+1]
            o=_weighted_outcome(rows,high=True)
            target.append({"low_tl":low,"high_tl":low+1,"era_class":ERA_CLASS[(low,low+1)],"base_pairings":len(rows),
                           "higher_tl_conditional_win_rate":o["conditional_win_rate"],"unresolved_rate":o["unresolved_rate"],"mean_turns":o["mean_turns"]})
    _write_csv(outdir/"adjacent_population_summary.csv",adjacent);_write_csv(outdir/"matched_composition_summary.csv",matched)

    envelope=_build_envelope_rows([b for _,b in sorted(_WORK_BUILD_MAP.items())] if _WORK_BUILD_MAP else enumerate_legal_builds(BaselineCatalog(repo,doc["sourceMatrix"]))[1])
    env={(r["low_tl"],r["high_tl"]):r for r in envelope};adjmap={(r["low_tl"],r["high_tl"]):r for r in adjacent};matmap={(r["low_tl"],r["high_tl"]):r for r in matched}
    era=[]
    for key in sorted(adjmap):
        a=adjmap[key];m=matmap[key];e=env[key]
        era.append({**e,"full_population_high_win":a["higher_tl_conditional_win_rate"],"matched_composition_high_win":m["higher_tl_conditional_win_rate"],
                    "population_minus_matched_pp":100*(a["higher_tl_conditional_win_rate"]-m["higher_tl_conditional_win_rate"])})
    _write_csv(outdir/"era_boundary_attribution_summary.csv",era)

    telemetry_rows=[]
    for key in sorted(telemetry_w):
        group,low,high=key;den=telemetry_w[key];r={"study_group":group,"low_tl":low,"high_tl":high,"weighted_trials":den}
        for metric in ALL_TELEMETRY_CONTRACT:
            name=metric["metric"];r["high_"+name]=telemetry_acc[key]["high_"+name]/den;r["low_"+name]=telemetry_acc[key]["low_"+name]/den
        telemetry_rows.append(r)
    _write_csv(outdir/"adjacent_telemetry_summary.csv",telemetry_rows)

    iso_outcome={(r["study_group"],int(r["tl_1"]),r["condition"]):r for r in pair_rows if r["study_group"] in ("swarmer_lifecycle","energy_isolation")}
    for group,filename in (("swarmer_lifecycle","swarmer_lifecycle_summary.csv"),("energy_isolation","energy_isolation_summary.csv")):
        rows=[]
        for key in sorted(k for k in isolation_w if k[0]==group):
            _,tl,cond=key;den=isolation_w[key];prs=[r for r in pair_rows if r["study_group"]==group and int(r["tl_1"])==tl and r["condition"]==cond]
            # Uniform design weights in these matched isolation lanes.
            win=statistics.fmean(float(r["build_1_conditional_win_rate"]) for r in prs)
            unresolved=statistics.fmean(float(r["unresolved_rate"]) for r in prs)
            row={"tl":tl,"condition":cond,"base_pairings":len(prs),"attacker_conditional_win_rate":win,"unresolved_rate":unresolved}
            for name,total in isolation_acc[key].items():row[name]=total/den
            rows.append(row)
        _write_csv(outdir/filename,rows)

    # Movement hotspots and direct axial/full-map comparison use exact CP125 pairing IDs.
    axial=_load_cp125_pairs(repo,doc["cp125NativeArchive"])
    geom=[]
    for low in range(1,9):
        full=[r for r in pair_rows if r["study_group"]=="adjacent_population" and int(r["tl_1"])==low]
        old=[r for r in axial if int(r["tl_1"])==low and int(r["tl_2"])==low+1]
        fo=_weighted_outcome(full,high=True);ao=_weighted_outcome(old,high=True)
        fms=_movement_stats(full);ams=_movement_stats(old)
        geom.append({"comparison":"adjacent_progression","tl_1":low,"tl_2":low+1,"era_class":ERA_CLASS[(low,low+1)],
                     "axial_high_win":ao["conditional_win_rate"],"full_map_high_win":fo["conditional_win_rate"],"delta_pp":100*(fo["conditional_win_rate"]-ao["conditional_win_rate"]),
                     "axial_unresolved":ao["unresolved_rate"],"full_map_unresolved":fo["unresolved_rate"],
                     "axial_weighted_mover_swing":ams["weighted_mean"],"full_map_weighted_mover_swing":fms["weighted_mean"],
                     "axial_p95_mover_swing":ams["p95"],"full_map_p95_mover_swing":fms["p95"]})
    _write_csv(outdir/"geometry_delta_summary.csv",geom)

    movement=[]
    for tl in (2,7):
        full=[r for r in pair_rows if r["study_group"]=="movement_hotspot" and int(r["tl_1"])==tl]
        old=[r for r in axial if int(r["tl_1"])==tl and int(r["tl_2"])==tl]
        fs=_movement_stats(full);os=_movement_stats(old)
        movement.append({"tl":tl,"base_pairings":len(full),**{"full_"+k:v for k,v in fs.items()},**{"axial_"+k:v for k,v in os.items()}})
    _write_csv(outdir/"movement_geometry_comparison.csv",movement)

    late_missile=[]
    for tl in (8,9):
        full=[r for r in pair_rows if r["study_group"]=="late_missile_geometry" and int(r["tl_1"])==tl]
        old=[r for r in axial if int(r["tl_1"])==tl and int(r["tl_2"])==tl and
             str(r.get("build_1_weapon_family", ""))=="Missile" and str(r.get("build_2_weapon_family", ""))=="Missile"]
        # Older CP125 pairing rows may identify families through profile names instead.
        if not old:
            full_ids={r["pairing_id"] for r in full}
            old=[r for r in axial if r["pairing_id"] in full_ids]
        fo=_weighted_outcome(full);ao=_weighted_outcome(old)
        late_missile.append({
            "tl":tl,"base_pairings":len(full),
            "axial_conditional_win_rate":ao["conditional_win_rate"],"full_map_conditional_win_rate":fo["conditional_win_rate"],
            "axial_unresolved_rate":ao["unresolved_rate"],"full_map_unresolved_rate":fo["unresolved_rate"],
            "axial_mean_turns":ao["mean_turns"],"full_map_mean_turns":fo["mean_turns"],
            **{"full_"+k:v for k,v in _movement_stats(full).items()},
            **{"axial_"+k:v for k,v in _movement_stats(old).items()},
        })
    _write_csv(outdir/"late_missile_geometry_summary.csv",late_missile)

    failed=[]
    if variant_count!=expected_variants:failed.append(f"variant-count:{variant_count}!={expected_variants}")
    if trial_errors:failed.append(f"trial-errors:{trial_errors}")
    if len(pair_rows)*4!=variant_count:failed.append("pairing-mirror-integrity")
    expected_pairs=9220+7699+4008+(1296*4)+(1728*4)+1727
    if len(pair_rows)!=expected_pairs:failed.append(f"normalized-pairings:{len(pair_rows)}!={expected_pairs}")
    analysis={"schemaVersion":RESULT_SCHEMA,"checkpoint":126,"mode":"substantive","variants":variant_count,"normalizedPairings":len(pair_rows),
              "trialsPerVariant":trials,"totalTrials":variant_count*trials,"trialErrors":trial_errors,"telemetryMetrics":len(ALL_TELEMETRY_CONTRACT),
              "geometry":FULL_MAP_GEOMETRY,"mixedTlShipsExecuted":False,"balanceValidated":False,"automaticPromotion":False,"failedGates":failed,
              "reviewSignals":{"balanceSignalsAreBlockingGates":False,"eraBoundarySummary":era,"geometryDeltaSummary":geom,"movementGeometryComparison":movement,"lateMissileGeometrySummary":late_missile}}
    (outdir/"analysis.json").write_text(json.dumps(analysis,indent=2)+"\n",encoding="utf-8")
    return analysis


def run_substantive(repo:Path,study_path:Path,outdir:Path,trials_override:int|None=None,jobs:int=24)->dict[str,Any]:
    plan=build_plan(repo,study_path,outdir/"plan");doc,tasks=plan["doc"],plan["tasks"]
    trials=int(trials_override if trials_override is not None else doc["substantiveTrialsPerVariant"])
    outdir.mkdir(parents=True,exist_ok=True)
    elapsed=execute_streaming(repo,doc,tasks,outdir/"variants.csv",trials,jobs)
    analysis=analyze_substantive(repo,doc,outdir/"variants.csv",outdir,sum(t.variant_count for t in tasks),trials)
    analysis["elapsedSeconds"]=elapsed;(outdir/"analysis.json").write_text(json.dumps(analysis,indent=2)+"\n",encoding="utf-8")
    return analysis


def run_fidelity_attribution(repo:Path,study_path:Path,outdir:Path,*,mode:str,trials:int|None=None,jobs:int=24)->dict[str,Any]:
    if mode=="plan":return build_plan(repo,study_path,outdir)["summary"]
    if mode=="symmetry":return run_symmetry_gate(repo,study_path,outdir)
    if mode=="smoke":return run_smoke(repo,study_path,outdir,jobs)
    if mode=="run":return run_substantive(repo,study_path,outdir,trials,jobs)
    raise ValueError(f"unknown CP126 mode: {mode}")
