from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Callable

from .canonical_combat import run_trial_full_map
from .ecology import EcologyBuild, LEGACY_COMBAT_DOCTRINE, UTILITY_COMBAT_DOCTRINE
from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from .study import canonicalize_relocated_references, load_json

RESULT_SCHEMA = "star-cluster-cp144-whole-combat-stage-a-response-surface-result-v0.1"
CP148_RESULT_SCHEMA = "star-cluster-cp148-whole-combat-stage-a-tactical-utility-response-surface-result-v0.1"
CP144_RECORDED_KERNEL_VERSION = "0.5"
CP148_RECORDED_KERNEL_VERSION = "0.7"

EXPECTED_SCENARIOS = 6850
EXPECTED_RESOURCES = 5
EXPECTED_STRATA = 10
EXPECTED_PAIRINGS = 137
HARD_TURN_SENTINEL = 60
LONG_RESOLVED_TURN = 25
DEFAULT_TRIALS_PER_SCENARIO = 500
EXPECTED_SUBSTANTIVE_TRIALS = EXPECTED_SCENARIOS * DEFAULT_TRIALS_PER_SCENARIO

_WORKER_MATRICES: dict[str, Any] | None = None

SIDE_TELEMETRY_FIELDS = (
    "movement_hexes", "movement_fuel", "map_boundary_blocks", "range_changes", "track_driven_closure_hexes",
    "firm_track_turns", "approximate_track_turns", "no_track_turns", "ecm_active_turns", "eccm_active_turns",
    "ecm_downgrade_events", "eccm_restore_events", "burnthrough_preservation_events",
    "sensor_overload_requests", "sensor_overload_activations", "ecm_overload_requests", "ecm_overload_activations",
    "eccm_overload_requests", "eccm_overload_activations", "reactor_overload_requests", "reactor_overload_activations",
    "reactor_overload_power_unlocked", "stl_overload_requests", "stl_overload_activations",
    "power_available_total", "power_spent_total", "power_sensor", "power_ecm", "power_eccm", "power_pds",
    "power_weapons", "power_shield_recharge", "power_shield_hardener", "power_shortfall_events",
    "weapon_power_shortfalls", "pds_power_shortfalls", "acquisition_power_shortfalls",
    "shield_base_restored", "shield_tactical_restored", "armor_regen_restored", "damage_control_hull_restored",
    "shield_collapse_events", "armor_collapse_events", "direct_shots", "direct_hits", "missile_launches",
    "missile_terminal_arrivals", "missile_guidance_attempts", "missile_hits", "pds_attempts", "pds_intercepts",
    "raw_damage_on_hit", "shield_absorbed", "armor_integrity_damage", "hull_damage", "direct_raw_damage",
    "direct_hull_damage", "missile_raw_damage", "missile_hull_damage", "def_res_packets", "shield_deflections",
    "armor_resisted_damage", "damage_control_attempts", "damage_control_successes",
    "energy_low_shots", "energy_standard_shots", "energy_overload_shots", "energy_overload_strain_added", "energy_max_strain",
    "cp146_weapon_core_funded_turns", "cp146_weapon_core_starved_turns",
    "cp146_active_sensor_default_turns", "cp146_passive_sensor_fallback_turns",
    "cp146_unknown_opponent_turns", "cp146_known_opponent_turns",
    "cp146_pds_unknown_readiness_turns", "cp146_pds_imminent_threat_turns", "cp146_pds_irrelevant_suppressed_turns",
    "cp146_hardener_unknown_readiness_turns", "cp146_hardener_relevant_turns", "cp146_hardener_irrelevant_suppressed_turns",
    "cp146_held_main_declarations", "cp146_held_main_attempts", "cp146_held_main_intercepts", "cp146_held_main_unused",
    "cp147_package_decisions", "cp147_direct_package_selections", "cp147_held_package_selections",
    "cp147_pds_package_selections", "cp147_passive_utility_fallbacks", "cp147_recovery_reserve_turns",
    "cp147_recovery_reserved_tp", "cp147_offense_utility_milli", "cp147_defense_utility_milli",
    "cp147_inbound_threat_turns", "cp147_observed_threat_turns", "cp147_terminal_hull_risk_turns",
    "cp147_sole_main_defensive_diversions", "cp147_sole_main_diversions_without_hull_risk",
)

FULL_TELEMETRY_FIELDS = (
    "adaptive_close_orders", "adaptive_open_orders", "adaptive_maintain_orders", "adaptive_standoff_orders",
    "boundary_end_moves", "missile_movement_hexes", "missile_reroutes", "missile_target_movement_reroutes",
    "missile_range_exhausted", "maximum_missile_distance_traveled",
)


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def _q(values: list[int], frac: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    pos = (len(vals) - 1) * frac
    lo = int(pos); hi = min(len(vals) - 1, lo + 1); f = pos - lo
    return vals[lo] * (1.0 - f) + vals[hi] * f


def _wilson(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    p = successes / n
    zz = z * z
    denom = 1.0 + zz / n
    center = (p + zz / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) / n) + zz / (4.0 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def _result_schema(doc: dict[str, Any]) -> str:
    return CP148_RESULT_SCHEMA if int(doc.get("checkpoint", 0)) == 148 else RESULT_SCHEMA


def _combat_doctrine(doc: dict[str, Any]) -> str:
    return UTILITY_COMBAT_DOCTRINE if int(doc.get("checkpoint", 0)) == 148 else LEGACY_COMBAT_DOCTRINE


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    checkpoint = int(doc.get("checkpoint", 0))
    if checkpoint == 144:
        if doc.get("schemaVersion") != "star-cluster-cp144-whole-combat-stage-a-response-surface-study-v0.1": errors.append("schemaVersion")
        if int(doc.get("baseCheckpoint", 0)) != 143: errors.append("baseCheckpoint")
        if doc.get("scope") != "whole-combat-stage-a-substantive-response-surface": errors.append("scope")
        if doc.get("canonicalCombatKernelVersion") != CP144_RECORDED_KERNEL_VERSION: errors.append("canonicalCombatKernelVersion")
    elif checkpoint == 148:
        if doc.get("schemaVersion") != "star-cluster-cp148-whole-combat-stage-a-tactical-utility-response-surface-study-v0.1": errors.append("schemaVersion")
        if int(doc.get("baseCheckpoint", 0)) != 147: errors.append("baseCheckpoint")
        if doc.get("scope") != "whole-combat-stage-a-tactical-utility-response-surface": errors.append("scope")
        if doc.get("canonicalCombatKernelVersion") != CP148_RECORDED_KERNEL_VERSION: errors.append("canonicalCombatKernelVersion")
        if doc.get("combatDoctrine") != UTILITY_COMBAT_DOCTRINE: errors.append("combatDoctrine")
        if doc.get("baseMaxTpDemandPolicy") != "all-installed-normal-combat-demand-no-overload": errors.append("baseMaxTpDemandPolicy")
        if doc.get("strategicParetoPolicy") != "combat-gated-before-resource-robustness": errors.append("strategicParetoPolicy")
    else:
        errors.append("checkpoint")
    if int(doc.get("expectedStageAScenarios", 0)) != EXPECTED_SCENARIOS: errors.append("expectedStageAScenarios")
    if int(doc.get("expectedResourceEnvironments", 0)) != EXPECTED_RESOURCES: errors.append("expectedResourceEnvironments")
    if int(doc.get("expectedScenarioStrata", 0)) != EXPECTED_STRATA: errors.append("expectedScenarioStrata")
    if int(doc.get("expectedOrderedSameTlWeaponPairings", 0)) != EXPECTED_PAIRINGS: errors.append("expectedOrderedSameTlWeaponPairings")
    if int(doc.get("integrationSmokeTrials", 0)) != EXPECTED_SCENARIOS: errors.append("integrationSmokeTrials")
    if int(doc.get("substantiveTrialsPerScenario", 0)) != DEFAULT_TRIALS_PER_SCENARIO: errors.append("substantiveTrialsPerScenario")
    if int(doc.get("substantiveCombatTrials", 0)) != EXPECTED_SUBSTANTIVE_TRIALS: errors.append("substantiveCombatTrials")
    if int(doc.get("hardTurnSentinel", 0)) != HARD_TURN_SENTINEL: errors.append("hardTurnSentinel")
    if int(doc.get("longResolvedTurn", 0)) != LONG_RESOLVED_TURN: errors.append("longResolvedTurn")
    if bool(doc.get("tuningAllowed", True)): errors.append("tuningAllowed")
    if bool(doc.get("automaticPromotion", True)): errors.append("automaticPromotion")
    if bool(doc.get("stageBAutomatic", True)): errors.append("stageBAutomatic")
    return errors


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    manifest = _read_csv(repo / doc["stageAExperimentManifest"])
    ensemble_rows, tl_rows = _resource_rows(repo, doc)
    if len(manifest) != EXPECTED_SCENARIOS: failures.append("manifest-count")
    ids = [r["scenario_id"] for r in manifest]
    if len(ids) != len(set(ids)): failures.append("duplicate-scenario-id")
    resources = sorted({r["resource_ensemble_id"] for r in manifest})
    expected_resources = sorted({r["ensemble_id"] for r in ensemble_rows})
    if resources != expected_resources or len(resources) != EXPECTED_RESOURCES: failures.append("resource-crossing")
    if "R5_CENTRAL_HIGH_DEMAND" in resources: failures.append("duplicate-r5-not-collapsed")
    if len(tl_rows) != EXPECTED_RESOURCES * 9: failures.append("resource-tl-row-count")
    strata = {r["scenario_stratum"] for r in manifest}
    if len(strata) != EXPECTED_STRATA: failures.append("stratum-crossing")
    # 137 ordered same-TL pairings per resource/stratum crossing: total population is
    # 137 x 5 x 10, while the manifest contains one row per exact cell.
    pairing_keys = {(int(r["tl"]), r["side_a_weapon"], r["side_b_weapon"]) for r in manifest}
    if len(pairing_keys) != EXPECTED_PAIRINGS: failures.append("ordered-pairing-count")
    counts = Counter(r["resource_ensemble_id"] for r in manifest)
    if set(counts.values()) != {EXPECTED_PAIRINGS * EXPECTED_STRATA}: failures.append("resource-balance")
    counts = Counter(r["scenario_stratum"] for r in manifest)
    if set(counts.values()) != {EXPECTED_PAIRINGS * EXPECTED_RESOURCES}: failures.append("stratum-balance")
    if any(int(r.get("planned_trials", 0)) != DEFAULT_TRIALS_PER_SCENARIO for r in manifest): failures.append("planned-trials")
    return failures


def _base_max_installed_tp_demand(matrix: Any, build: EcologyBuild) -> tuple[int, dict[str, int]]:
    """Maximum simultaneous normal combat TP demand for installed systems.

    This deliberately excludes every overload mode.  It uses Energy Standard, normal
    K/M firing/launch demand, Active-Low Sensor, full-strength EW, configured PDS
    readiness, Shield Hardener, maximum normal tactical Shield recharge, mainline
    Armor tactical regeneration, and one Damage-Control attempt.  STL normal movement
    is zero TP in the accepted model and therefore contributes zero.
    """
    tl = int(build.tl)
    weapon = matrix.weapon_profile(build.weapon_family, tl)
    if build.weapon_family == "Energy":
        weapon_tp = int(weapon.get("standardTp", 0)) * int(build.main_count)
    elif build.weapon_family == "Kinetic":
        weapon_tp = int(weapon.get("firingTp", 0)) * int(build.main_count)
    else:
        weapon_tp = int(weapon.get("launchTp", 0)) * int(build.main_count)
    parts = {
        "weapon": weapon_tp,
        "sensor": int(matrix.p("sensor", tl).get("activeLowTp", 0) or 0),
        "ecm": int(matrix.p("ecm", tl).get("fullStrengthTp", 0) or 0) if build.ecm else 0,
        "eccm": int(matrix.p("eccm", tl).get("fullStrengthTp", 0) or 0) if build.eccm else 0,
        "pds": int(matrix.pds_profile(build.pds_family, tl).get("readinessTp", 0) or 0) if build.pds_family else 0,
        "shield_hardener": 1 if build.shield_hardener and build.shield else 0,
        "shield_recharge": int(matrix.p("shield", tl).get("tacticalRechargeCapTp", 0) or 0) if build.shield else 0,
        "armor_regen": int(matrix.p("armor", tl).get("tacticalRegenerationCapTp", 0) or 0),
        "damage_control": int(matrix.p("damage_control", tl).get("attemptTp", 0) or 0),
    }
    return sum(parts.values()), parts


def _worker_init(repo_text: str, matrix_relative: str,
                 ensemble_rows: list[dict[str, str]], tl_rows: list[dict[str, str]]) -> None:
    global _WORKER_MATRICES
    repo = Path(repo_text)
    ids = sorted({r["ensemble_id"] for r in ensemble_rows})
    _WORKER_MATRICES = {
        eid: build_deep_resource_matrix(repo, matrix_relative, eid, ensemble_rows, tl_rows)
        for eid in ids
    }


def _last_turn_by_side(turn_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in turn_rows:
        out[str(row["side_id"])] = row
    return out


def _movement_open_nonstandoff(result) -> int:
    return max(0, int(result.full_a.adaptive_open_orders - result.full_a.adaptive_standoff_orders)) + max(0, int(result.full_b.adaptive_open_orders - result.full_b.adaptive_standoff_orders))


def _smoke_task(args: tuple[int, dict[str, str], Any, int, str]) -> dict[str, Any]:
    idx, source, bound, master_seed, combat_doctrine = args
    if _WORKER_MATRICES is None:
        raise RuntimeError("CP144 worker matrices are not initialized")
    matrix = _WORKER_MATRICES[source["resource_ensemble_id"]]
    variant = replace(bound.variant, max_turns=HARD_TURN_SENTINEL)
    turns: list[dict[str, Any]] = []
    ctx = {"scenario_id":source["scenario_id"],"resource_ensemble_id":source["resource_ensemble_id"],"weapon_a":source["side_a_weapon"],"weapon_b":source["side_b_weapon"]}
    result = run_trial_full_map(matrix, variant, master_seed, 0, turn_telemetry_sink=turns, telemetry_context=ctx, combat_doctrine=combat_doctrine)
    last = _last_turn_by_side(turns)
    resolved = result.winner in ("A", "B", "Draw") and not result.unresolved and not result.error
    return {
        "index":idx,
        "scenario_id":source["scenario_id"],"tl":int(source["tl"]),"side_a_weapon":source["side_a_weapon"],"side_b_weapon":source["side_b_weapon"],
        "resource_ensemble_id":source["resource_ensemble_id"],"scenario_stratum":source["scenario_stratum"],
        "winner":result.winner,"unresolved":int(result.unresolved),"error":result.error,"turns":result.turns,"termination_cause":result.termination_cause,
        "resolved_flag":int(resolved),"resolved_ge25_flag":int(resolved and result.turns >= LONG_RESOLVED_TURN),
        "turn_cap_flag":int(result.termination_cause == "TURN_CAP_SENTINEL"),"safe_stalemate_flag":int(result.termination_cause == "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION"),
        "turn_telemetry_rows":len(turns),"expected_turn_telemetry_rows":2*result.turns,"turn_telemetry_coverage_pass":int(len(turns)==2*result.turns),
        "tp_conflict_turns_a":sum(int(r["tp_conflict_flag"]) for r in turns if r["side_id"]=="A"),
        "tp_conflict_turns_b":sum(int(r["tp_conflict_flag"]) for r in turns if r["side_id"]=="B"),
        "tp_denied_a":sum(int(r["tp_denied_total"]) for r in turns if r["side_id"]=="A"),
        "tp_denied_b":sum(int(r["tp_denied_total"]) for r in turns if r["side_id"]=="B"),
        "nonstandoff_open_orders":_movement_open_nonstandoff(result),
        "standoff_open_orders":int(result.full_a.adaptive_standoff_orders + result.full_b.adaptive_standoff_orders),
        "track_closure_hexes":int(result.side_a.track_driven_closure_hexes + result.side_b.track_driven_closure_hexes),
        "final_weapon_ammo_a":last.get("A",{}).get("kinetic_ammo_remaining","") if last.get("A",{}).get("kinetic_ammo_remaining","")!="" else last.get("A",{}).get("missile_flights_remaining",""),
        "final_weapon_ammo_b":last.get("B",{}).get("kinetic_ammo_remaining","") if last.get("B",{}).get("kinetic_ammo_remaining","")!="" else last.get("B",{}).get("missile_flights_remaining",""),
    }


def run_smoke_batch(repo: Path, study_path: Path, outdir: Path, jobs: int=24,
                    batch_start: int=0, batch_end: int|None=None) -> dict[str, Any]:
    doc=load_json(study_path); errors=validate_study(doc)+validate_population(repo,doc)
    if errors:return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True)
    manifest=_read_csv(repo/doc["stageAExperimentManifest"]); er,tr=_resource_rows(repo,doc); source=repo/doc["matrix"]; before=_sha(source)
    mats={eid:build_deep_resource_matrix(repo,doc["matrix"],eid,er,tr) for eid in sorted({r["ensemble_id"] for r in er})}
    bindings=[bind_scenario(mats[r["resource_ensemble_id"]],r) for r in manifest]
    start=max(0,int(batch_start)); end=len(manifest) if batch_end is None else min(len(manifest),int(batch_end))
    if start>=end:return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["invalid-batch-range"]}
    doctrine=_combat_doctrine(doc); tasks=[(i,manifest[i],bindings[i],int(doc["masterSeed"]),doctrine) for i in range(start,end)]
    jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc["matrix"],er,tr); completed=[_smoke_task(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],er,tr)) as ex:
            completed=list(ex.map(_smoke_task,tasks,chunksize=8))
    completed.sort(key=lambda r:r["index"]); rows=[{k:v for k,v in r.items() if k!="index"} for r in completed]
    _write_csv(outdir/"whole_combat_smoke_results.csv",rows)
    after=_sha(source); failures=[]
    if len(rows)!=end-start:failures.append("scenario-count")
    if any(r["error"] for r in rows):failures.append("execution-errors")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in rows):failures.append("turn-telemetry-coverage")
    if any(int(r["turns"])>HARD_TURN_SENTINEL for r in rows):failures.append("turn-sentinel-exceeded")
    # After CP144 parity closure, the only legal AdaptiveEngage Open orders inside
    # contact are demonstrated one-sided standoff orders. The old preferred-range
    # reopen path must be absent from the broad smoke.
    if any(int(r["nonstandoff_open_orders"])!=0 for r in rows):failures.append("engage-adaptive-nonstandoff-open-regression")
    if before!=after:failures.append("source-matrix-modified")
    summary={
        "schemaVersion":_result_schema(doc),"checkpoint":int(doc["checkpoint"]),"baseCheckpoint":int(doc["baseCheckpoint"]),"mode":"smoke-batch","passed":not failures,"failedGates":failures,
        "batchStart":start,"batchEnd":end,"scenarios":len(rows),"executionErrors":sum(bool(r["error"]) for r in rows),
        "resolved":sum(int(r["resolved_flag"]) for r in rows),"resolvedGe25":sum(int(r["resolved_ge25_flag"]) for r in rows),
        "turnCapSentinels":sum(int(r["turn_cap_flag"]) for r in rows),"safeStalemates":sum(int(r["safe_stalemate_flag"]) for r in rows),
        "nonstandoffOpenOrders":sum(int(r["nonstandoff_open_orders"]) for r in rows),"sourceMatrixUnmodified":before==after,
        "substantiveCombatTrials":0,"promotionAllowed":False,
    }
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def merge_smoke_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    doc=load_json(study_path); errors=validate_study(doc)+validate_population(repo,doc)
    if errors:return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True); manifest=_read_csv(repo/doc["stageAExperimentManifest"]); source=repo/doc["matrix"]; before=_sha(source)
    rows=[]; audits=[]; expected=0
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json"; rp=d/"whole_combat_smoke_results.csv"
        if not sp.exists() or not rp.exists():continue
        payload=json.loads(sp.read_text(encoding="utf-8-sig")); analysis=payload.get("analysis",payload)
        start=int(analysis["batchStart"]); end=int(analysis["batchEnd"]); br=_read_csv(rp)
        ids_match=[r["scenario_id"] for r in manifest[start:end]]==[r["scenario_id"] for r in br]
        ok=bool(analysis.get("passed",False)) and start==expected and len(br)==end-start and ids_match
        audits.append({"batch":d.name,"start":start,"end":end,"scenarios":len(br),"ids_match":int(ids_match),"passed":int(ok)})
        if not ok: continue
        rows.extend(br); expected=end
    failures=[]
    if expected!=len(manifest):failures.append("batch-coverage-incomplete")
    if len(rows)!=EXPECTED_SCENARIOS:failures.append("merged-scenario-count")
    if any(r["error"] for r in rows):failures.append("merged-execution-errors")
    if any(int(r["nonstandoff_open_orders"])!=0 for r in rows):failures.append("engage-adaptive-nonstandoff-open-regression")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in rows):failures.append("turn-telemetry-coverage")
    after=_sha(source)
    if before!=after:failures.append("source-matrix-modified")
    _write_csv(outdir/"batch_merge_audit.csv",audits); _write_csv(outdir/"whole_combat_smoke_results.csv",rows)
    # Compact diagnostic groups only; this smoke remains execution evidence.
    groups=[]
    for gtype,keyfn in (
        ("OVERALL",lambda r:"ALL"),("TL",lambda r:f"TL{r['tl']}"),("STRATUM",lambda r:r["scenario_stratum"]),
        ("WEAPON_PAIR",lambda r:f"{r['side_a_weapon']}->{r['side_b_weapon']}")
    ):
        tmp=defaultdict(list)
        for r in rows:tmp[keyfn(r)].append(r)
        for key,g in sorted(tmp.items()):
            resolved=[r for r in g if int(r["resolved_flag"])]; turns=[int(r["turns"]) for r in resolved]
            groups.append({"group_type":gtype,"group_key":key,"scenarios":len(g),"resolved":len(resolved),
                           "resolved_ge25":sum(int(r["resolved_ge25_flag"]) for r in g),"turn_cap_sentinels":sum(int(r["turn_cap_flag"]) for r in g),
                           "safe_stalemates":sum(int(r["safe_stalemate_flag"]) for r in g),"median_resolved_turns":statistics.median(turns) if turns else "",
                           "tp_conflict_turns":sum(int(r["tp_conflict_turns_a"])+int(r["tp_conflict_turns_b"]) for r in g)})
    _write_csv(outdir/"whole_combat_smoke_group_summary.csv",groups)
    summary={"schemaVersion":_result_schema(doc),"checkpoint":int(doc["checkpoint"]),"baseCheckpoint":int(doc["baseCheckpoint"]),"mode":"merged-smoke","passed":not failures,"failedGates":failures,
             "stageAScenarios":len(rows),"integrationSmokeTrials":len(rows),"executionErrors":sum(bool(r["error"]) for r in rows),
             "resolved":sum(int(r["resolved_flag"]) for r in rows),"resolvedGe25":sum(int(r["resolved_ge25_flag"]) for r in rows),
             "turnCapSentinels":sum(int(r["turn_cap_flag"]) for r in rows),"safeStalemates":sum(int(r["safe_stalemate_flag"]) for r in rows),
             "nonstandoffOpenOrders":sum(int(r["nonstandoff_open_orders"]) for r in rows),"resourceEnvironmentCount":EXPECTED_RESOURCES,
             "scenarioStrataCount":EXPECTED_STRATA,"orderedSameTlWeaponPairings":EXPECTED_PAIRINGS,"sourceMatrixUnmodified":before==after,
             "substantiveCombatTrials":0,"stageASubstantiveReady":not failures,"promotionAllowed":False}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def _add(sum_map: dict[str, float], key: str, value: Any) -> None:
    sum_map[key] = sum_map.get(key, 0.0) + float(value or 0)


def _substantive_task(args: tuple[int, dict[str, str], Any, int, int, str]) -> dict[str, Any]:
    idx, source, bound, master_seed, trials, combat_doctrine = args
    if _WORKER_MATRICES is None:
        raise RuntimeError("CP144 worker matrices are not initialized")
    matrix=_WORKER_MATRICES[source["resource_ensemble_id"]]; variant=replace(bound.variant,max_turns=HARD_TURN_SENTINEL)
    counts=Counter(); turns_resolved: list[int]=[]; turns_all: list[int]=[]; sums: dict[str,float]={}; errors=[]
    initial_hull=float(matrix.p("hull",int(source["tl"]))["hullPoints"])
    initial_armor=float(matrix.p("armor",int(source["tl"]))["ai"])
    initial_shield=float(matrix.p("shield",int(source["tl"]))["capacity"]) if bound.variant.side_a.shield else 0.0
    base_max_a, base_parts_a = _base_max_installed_tp_demand(matrix, bound.variant.side_a)
    base_max_b, base_parts_b = _base_max_installed_tp_demand(matrix, bound.variant.side_b)
    base_reactor_a = int(matrix.p("reactor", int(source["tl"]))["operationalTp"]) * int(bound.variant.side_a.reactor_count)
    base_reactor_b = int(matrix.p("reactor", int(source["tl"]))["operationalTp"]) * int(bound.variant.side_b.reactor_count)
    peak_allocated = {"a": 0, "b": 0}
    for trial_index in range(trials):
        turn_rows: list[dict[str,Any]]=[]
        ctx={"scenario_id":source["scenario_id"],"resource_ensemble_id":source["resource_ensemble_id"],"weapon_a":source["side_a_weapon"],"weapon_b":source["side_b_weapon"]}
        result=run_trial_full_map(matrix,variant,master_seed,trial_index,turn_telemetry_sink=turn_rows,telemetry_context=ctx,combat_doctrine=combat_doctrine)
        turns_all.append(int(result.turns))
        if result.error:
            counts["error"]+=1; errors.append(result.error); continue
        if result.termination_cause=="STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION":counts["safe_stalemate"]+=1
        elif result.termination_cause=="TURN_CAP_SENTINEL":counts["turn_cap"]+=1
        elif result.unresolved:counts["unresolved_other"]+=1
        elif result.winner=="A":counts["a_win"]+=1
        elif result.winner=="B":counts["b_win"]+=1
        elif result.winner=="Draw":counts["draw"]+=1
        resolved=(not result.unresolved and result.winner in ("A","B","Draw"))
        if resolved:
            counts["resolved"]+=1;turns_resolved.append(int(result.turns))
            if result.turns < LONG_RESOLVED_TURN:counts["resolved_under25"]+=1
            else:counts["resolved_ge25"]+=1
            if result.turns<=10:counts["resolved_by10"]+=1
            if result.turns<=15:counts["resolved_by15"]+=1
            if result.turns<=20:counts["resolved_by20"]+=1
            if result.winner=="A" and result.turns < LONG_RESOLVED_TURN:counts["a_fast_win"]+=1
            if result.winner=="B" and result.turns < LONG_RESOLVED_TURN:counts["b_fast_win"]+=1
        for label,tel,full in (("a",result.side_a,result.full_a),("b",result.side_b,result.full_b)):
            for field in SIDE_TELEMETRY_FIELDS:_add(sums,f"{label}_{field}",getattr(tel,field))
            for field in FULL_TELEMETRY_FIELDS:_add(sums,f"{label}_{field}",getattr(full,field))
        # Damage counters live on the receiving side, so inflicted A is received B.
        _add(sums,"a_damage_inflicted",result.side_b.shield_absorbed+result.side_b.armor_integrity_damage+result.side_b.hull_damage)
        _add(sums,"b_damage_inflicted",result.side_a.shield_absorbed+result.side_a.armor_integrity_damage+result.side_a.hull_damage)
        _add(sums,"a_recovery",result.side_a.shield_base_restored+result.side_a.shield_tactical_restored+result.side_a.armor_regen_restored+result.side_a.damage_control_hull_restored)
        _add(sums,"b_recovery",result.side_b.shield_base_restored+result.side_b.shield_tactical_restored+result.side_b.armor_regen_restored+result.side_b.damage_control_hull_restored)
        _add(sums,"final_hull_a",result.hull_a);_add(sums,"final_hull_b",result.hull_b);_add(sums,"final_armor_a",result.armor_a);_add(sums,"final_armor_b",result.armor_b);_add(sums,"final_shield_a",result.shield_a);_add(sums,"final_shield_b",result.shield_b)
        _add(sums,"final_range",result.final_range);_add(sums,"min_range",result.min_range)
        # Turn-level decision-pressure telemetry is aggregated and discarded per trial.
        last=_last_turn_by_side(turn_rows)
        for label in ("A","B"):
            side_rows=[r for r in turn_rows if r["side_id"]==label]
            low=label.lower(); _add(sums,f"{low}_side_turns",len(side_rows))
            _add(sums,f"{low}_tp_conflict_turns",sum(int(r["tp_conflict_flag"]) for r in side_rows))
            _add(sums,f"{low}_tp_requested",sum(int(r["tp_requested_total"]) for r in side_rows))
            _add(sums,f"{low}_tp_allocated",sum(int(r["tp_allocated_total"]) for r in side_rows))
            if side_rows:
                peak_allocated[low] = max(peak_allocated[low], max(int(r["tp_allocated_total"]) for r in side_rows))
            _add(sums,f"{low}_tp_denied",sum(int(r["tp_denied_total"]) for r in side_rows))
            _add(sums,f"{low}_desirable_actions",sum(int(r["desirable_action_count"]) for r in side_rows))
            _add(sums,f"{low}_denied_actions",sum(int(r["denied_action_count"]) for r in side_rows))
            _add(sums,f"{low}_firm_turn_rows",sum(str(r["track_quality"])=="Firm" for r in side_rows))
            lr=last.get(label,{})
            ammo=lr.get("kinetic_ammo_remaining","") if lr.get("kinetic_ammo_remaining","")!="" else lr.get("missile_flights_remaining","")
            if ammo!="" and int(ammo)==0:counts[f"{low}_primary_ammo_exhausted"]+=1
            pds=lr.get("pds_ammo_remaining","")
            if pds!="" and int(pds)==0:counts[f"{low}_pds_ammo_exhausted"]+=1
            if lr and int(lr.get("fuel_remaining",1))==0:counts[f"{low}_fuel_exhausted"]+=1
    n=trials; decisive=counts["a_win"]+counts["b_win"]; a_lo,a_hi=_wilson(counts["a_win"],n); b_lo,b_hi=_wilson(counts["b_win"],n)
    row={
        "scenario_index":idx,"scenario_id":source["scenario_id"],"tl":int(source["tl"]),"side_a_weapon":source["side_a_weapon"],"side_b_weapon":source["side_b_weapon"],
        "resource_ensemble_id":source["resource_ensemble_id"],"scenario_stratum":source["scenario_stratum"],"trials":n,
        "a_wins":counts["a_win"],"b_wins":counts["b_win"],"draws":counts["draw"],"resolved":counts["resolved"],
        "safe_stalemates":counts["safe_stalemate"],"turn_cap_sentinels":counts["turn_cap"],"unresolved_other":counts["unresolved_other"],"error_trials":counts["error"],
        "resolved_under25":counts["resolved_under25"],"resolved_ge25":counts["resolved_ge25"],"resolved_by10":counts["resolved_by10"],"resolved_by15":counts["resolved_by15"],"resolved_by20":counts["resolved_by20"],
        "a_fast_wins_under25":counts["a_fast_win"],"b_fast_wins_under25":counts["b_fast_win"],
        "a_win_rate":counts["a_win"]/n,"a_win_wilson_low":a_lo,"a_win_wilson_high":a_hi,
        "b_win_rate":counts["b_win"]/n,"b_win_wilson_low":b_lo,"b_win_wilson_high":b_hi,
        "a_decisive_win_share":counts["a_win"]/decisive if decisive else 0.5,"b_decisive_win_share":counts["b_win"]/decisive if decisive else 0.5,
        "resolved_rate":counts["resolved"]/n,"resolved_under25_rate":counts["resolved_under25"]/n,"resolved_ge25_rate":counts["resolved_ge25"]/n,
        "gameplay_duration_concern_rate":(counts["resolved_ge25"]+counts["turn_cap"])/n,"turn_cap_rate":counts["turn_cap"]/n,"safe_stalemate_rate":counts["safe_stalemate"]/n,
        "mean_turns_all":statistics.fmean(turns_all) if turns_all else 0.0,"mean_resolved_turns":statistics.fmean(turns_resolved) if turns_resolved else 0.0,
        "median_resolved_turns":statistics.median(turns_resolved) if turns_resolved else 0.0,"p90_resolved_turns":_q(turns_resolved,0.90),"p95_resolved_turns":_q(turns_resolved,0.95),
        "initial_hull":initial_hull,"initial_armor":initial_armor,"initial_shield_when_installed":initial_shield,
        "a_primary_ammo_exhausted_rate":counts["a_primary_ammo_exhausted"]/n,"b_primary_ammo_exhausted_rate":counts["b_primary_ammo_exhausted"]/n,
        "a_pds_ammo_exhausted_rate":counts["a_pds_ammo_exhausted"]/n,"b_pds_ammo_exhausted_rate":counts["b_pds_ammo_exhausted"]/n,
        "a_fuel_exhausted_rate":counts["a_fuel_exhausted"]/n,"b_fuel_exhausted_rate":counts["b_fuel_exhausted"]/n,
        "unique_error_messages":";".join(sorted(set(errors)))[:1000],
        "a_base_reactor_tp":base_reactor_a,"b_base_reactor_tp":base_reactor_b,
        "a_base_max_installed_tp_demand":base_max_a,"b_base_max_installed_tp_demand":base_max_b,
        "a_peak_tp_allocated_per_turn":peak_allocated["a"],"b_peak_tp_allocated_per_turn":peak_allocated["b"],
    }
    for part, value in base_parts_a.items(): row[f"a_base_max_tp_{part}"] = value
    for part, value in base_parts_b.items(): row[f"b_base_max_tp_{part}"] = value
    for key,value in sorted(sums.items()):row[f"mean_{key}"]=value/n
    # Derived rates normalize turn-level telemetry by actual side-turn exposure.
    for label in ("a","b"):
        side_turns=sums.get(f"{label}_side_turns",0.0)
        row[f"{label}_tp_conflict_turn_rate"]=sums.get(f"{label}_tp_conflict_turns",0.0)/side_turns if side_turns else 0.0
        row[f"{label}_tp_denied_per_side_turn"]=sums.get(f"{label}_tp_denied",0.0)/side_turns if side_turns else 0.0
        row[f"{label}_firm_track_turn_rate"]=sums.get(f"{label}_firm_turn_rows",0.0)/side_turns if side_turns else 0.0
        requested=sums.get(f"{label}_tp_requested",0.0);row[f"{label}_tp_fulfillment_rate"]=sums.get(f"{label}_tp_allocated",0.0)/requested if requested else 1.0
        allocated=sums.get(f"{label}_tp_allocated",0.0);row[f"{label}_mean_tp_allocated_per_turn"]=allocated/side_turns if side_turns else 0.0
        base_max=float(row[f"{label}_base_max_installed_tp_demand"]);row[f"{label}_mean_allocated_vs_base_max_demand"]=row[f"{label}_mean_tp_allocated_per_turn"]/base_max if base_max else 0.0
        row[f"{label}_peak_allocated_vs_base_max_demand"]=float(row[f"{label}_peak_tp_allocated_per_turn"])/base_max if base_max else 0.0
        reactor=float(row[f"{label}_base_reactor_tp"]);row[f"{label}_base_max_demand_vs_reactor"]=base_max/reactor if reactor else 0.0
        shots=sums.get(f"{label}_direct_shots",0.0);row[f"{label}_direct_hit_rate"]=sums.get(f"{label}_direct_hits",0.0)/shots if shots else 0.0
        guidance=sums.get(f"{label}_missile_guidance_attempts",0.0);row[f"{label}_missile_guidance_success_rate"]=sums.get(f"{label}_missile_hits",0.0)/guidance if guidance else 0.0
        pds=sums.get(f"{label}_pds_attempts",0.0);row[f"{label}_pds_intercept_per_attempt"]=sums.get(f"{label}_pds_intercepts",0.0)/pds if pds else 0.0
        opens=sums.get(f"{label}_adaptive_open_orders",0.0);standoff=sums.get(f"{label}_adaptive_standoff_orders",0.0)
        row[f"{label}_nonstandoff_open_orders_mean"]=max(0.0,opens-standoff)/n
    row["a_damage_advantage_mean"]=row.get("mean_a_damage_inflicted",0.0)-row.get("mean_b_damage_inflicted",0.0)
    return row


def run_substantive_batch(repo: Path, study_path: Path, outdir: Path, jobs: int=24,
                          batch_start: int=0, batch_end: int|None=None,
                          trials_per_scenario: int|None=None) -> dict[str,Any]:
    doc=load_json(study_path); errors=validate_study(doc)+validate_population(repo,doc)
    if errors:return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    trials=int(trials_per_scenario or doc["substantiveTrialsPerScenario"])
    if trials<=0 or trials>int(doc["substantiveTrialsPerScenario"]):
        return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["invalid-trials-per-scenario"]}
    outdir.mkdir(parents=True,exist_ok=True);manifest=_read_csv(repo/doc["stageAExperimentManifest"]);er,tr=_resource_rows(repo,doc);source=repo/doc["matrix"];before=_sha(source)
    mats={eid:build_deep_resource_matrix(repo,doc["matrix"],eid,er,tr) for eid in sorted({r["ensemble_id"] for r in er})};bindings=[bind_scenario(mats[r["resource_ensemble_id"]],r) for r in manifest]
    start=max(0,int(batch_start));end=len(manifest) if batch_end is None else min(len(manifest),int(batch_end))
    if start>=end:return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["invalid-batch-range"]}
    doctrine=_combat_doctrine(doc); tasks=[(i,manifest[i],bindings[i],int(doc["masterSeed"]),trials,doctrine) for i in range(start,end)];jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc["matrix"],er,tr);completed=[_substantive_task(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],er,tr)) as ex:
            completed=list(ex.map(_substantive_task,tasks,chunksize=1))
    completed.sort(key=lambda r:r["scenario_index"]);_write_csv(outdir/"scenario_response_surface.csv",completed)
    after=_sha(source);failures=[]
    if len(completed)!=end-start:failures.append("scenario-count")
    if any(int(r["trials"])!=trials for r in completed):failures.append("trial-count")
    if any(int(r["error_trials"])!=0 for r in completed):failures.append("trial-errors")
    if any(float(r["a_nonstandoff_open_orders_mean"])>0 or float(r["b_nonstandoff_open_orders_mean"])>0 for r in completed):failures.append("engage-adaptive-nonstandoff-open-regression")
    if before!=after:failures.append("source-matrix-modified")
    summary={"schemaVersion":_result_schema(doc),"checkpoint":int(doc["checkpoint"]),"baseCheckpoint":int(doc["baseCheckpoint"]),"mode":"substantive-batch","passed":not failures,"failedGates":failures,
             "batchStart":start,"batchEnd":end,"scenarios":len(completed),"trialsPerScenario":trials,"combatTrials":len(completed)*trials,
             "trialErrors":sum(int(r["error_trials"]) for r in completed),"sourceMatrixUnmodified":before==after,"promotionAllowed":False,
             "interpretation":"Substantive Stage-A response-surface evidence; no automatic tuning or promotion."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary


def _aggregate_rows(rows: list[dict[str,Any]], keys: tuple[str,...]) -> list[dict[str,Any]]:
    groups=defaultdict(list)
    for r in rows:groups[tuple(r[k] for k in keys)].append(r)
    out=[]
    for key,g in sorted(groups.items()):
        trials=sum(int(r["trials"]) for r in g);a=sum(int(r["a_wins"]) for r in g);b=sum(int(r["b_wins"]) for r in g);draw=sum(int(r["draws"]) for r in g);resolved=sum(int(r["resolved"]) for r in g);long=sum(int(r["resolved_ge25"]) for r in g);caps=sum(int(r["turn_cap_sentinels"]) for r in g);stale=sum(int(r["safe_stalemates"]) for r in g);afast=sum(int(r["a_fast_wins_under25"]) for r in g)
        alo,ahi=_wilson(a,trials)
        row={k:v for k,v in zip(keys,key)};row.update({"scenario_cells":len(g),"trials":trials,"a_wins":a,"b_wins":b,"draws":draw,"resolved":resolved,"resolved_ge25":long,"turn_cap_sentinels":caps,"safe_stalemates":stale,
            "a_win_rate":a/trials if trials else 0.0,"a_win_wilson_low":alo,"a_win_wilson_high":ahi,"a_fast_win_rate":afast/trials if trials else 0.0,"resolved_rate":resolved/trials if trials else 0.0,
            "gameplay_duration_concern_rate":(long+caps)/trials if trials else 0.0,"turn_cap_rate":caps/trials if trials else 0.0,
            "mean_turns_all":sum(float(r["mean_turns_all"])*int(r["trials"]) for r in g)/trials if trials else 0.0,
            "mean_a_damage_advantage":sum(float(r["a_damage_advantage_mean"])*int(r["trials"]) for r in g)/trials if trials else 0.0,
            "a_tp_conflict_turn_rate":sum(float(r["a_tp_conflict_turn_rate"])*float(r.get("mean_a_side_turns",0))*int(r["trials"]) for r in g)/max(1.0,sum(float(r.get("mean_a_side_turns",0))*int(r["trials"]) for r in g)),
            "b_tp_conflict_turn_rate":sum(float(r["b_tp_conflict_turn_rate"])*float(r.get("mean_b_side_turns",0))*int(r["trials"]) for r in g)/max(1.0,sum(float(r.get("mean_b_side_turns",0))*int(r["trials"]) for r in g)),
            "a_tp_fulfillment_rate":sum(float(r["a_tp_fulfillment_rate"])*float(r.get("mean_a_tp_requested",0))*int(r["trials"]) for r in g)/max(1.0,sum(float(r.get("mean_a_tp_requested",0))*int(r["trials"]) for r in g)),
            "b_tp_fulfillment_rate":sum(float(r["b_tp_fulfillment_rate"])*float(r.get("mean_b_tp_requested",0))*int(r["trials"]) for r in g)/max(1.0,sum(float(r.get("mean_b_tp_requested",0))*int(r["trials"]) for r in g)),
            "a_firm_track_turn_rate":sum(float(r["a_firm_track_turn_rate"])*float(r.get("mean_a_side_turns",0))*int(r["trials"]) for r in g)/max(1.0,sum(float(r.get("mean_a_side_turns",0))*int(r["trials"]) for r in g)),
            "b_firm_track_turn_rate":sum(float(r["b_firm_track_turn_rate"])*float(r.get("mean_b_side_turns",0))*int(r["trials"]) for r in g)/max(1.0,sum(float(r.get("mean_b_side_turns",0))*int(r["trials"]) for r in g)),
        })
        out.append(row)
    return out


def _counter_effects(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    indexed={(r["tl"],r["resource_ensemble_id"],r["side_a_weapon"],r["side_b_weapon"],r["scenario_stratum"]):r for r in rows};out=[]
    for r in rows:
        if r["scenario_stratum"]=="BALANCED_CORE_NO_PDS":continue
        base=indexed.get((r["tl"],r["resource_ensemble_id"],r["side_a_weapon"],r["side_b_weapon"],"BALANCED_CORE_NO_PDS"))
        if not base:continue
        out.append({"tl":r["tl"],"resource_ensemble_id":r["resource_ensemble_id"],"side_a_weapon":r["side_a_weapon"],"side_b_weapon":r["side_b_weapon"],"counter_stratum":r["scenario_stratum"],
                    "delta_a_win_rate":float(r["a_win_rate"])-float(base["a_win_rate"]),"delta_duration_concern_rate":float(r["gameplay_duration_concern_rate"])-float(base["gameplay_duration_concern_rate"]),
                    "delta_mean_turns":float(r["mean_turns_all"])-float(base["mean_turns_all"]),"delta_a_tp_conflict_turn_rate":float(r["a_tp_conflict_turn_rate"])-float(base["a_tp_conflict_turn_rate"]),
                    "counter_a_win_rate":r["a_win_rate"],"balanced_a_win_rate":base["a_win_rate"]})
    return out


def _resource_effects(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    indexed={(r["tl"],r["resource_ensemble_id"],r["side_a_weapon"],r["side_b_weapon"],r["scenario_stratum"]):r for r in rows};out=[]
    for r in rows:
        if r["resource_ensemble_id"]=="R1_CENTRAL_NO_MAJOR":continue
        base=indexed.get((r["tl"],"R1_CENTRAL_NO_MAJOR",r["side_a_weapon"],r["side_b_weapon"],r["scenario_stratum"]))
        if not base:continue
        out.append({"tl":r["tl"],"resource_ensemble_id":r["resource_ensemble_id"],"side_a_weapon":r["side_a_weapon"],"side_b_weapon":r["side_b_weapon"],"scenario_stratum":r["scenario_stratum"],
                    "delta_a_win_rate_vs_r1":float(r["a_win_rate"])-float(base["a_win_rate"]),"delta_duration_concern_rate_vs_r1":float(r["gameplay_duration_concern_rate"])-float(base["gameplay_duration_concern_rate"]),
                    "delta_a_tp_conflict_turn_rate_vs_r1":float(r["a_tp_conflict_turn_rate"])-float(base["a_tp_conflict_turn_rate"]),"delta_mean_turns_vs_r1":float(r["mean_turns_all"])-float(base["mean_turns_all"])})
    return out


def _pairwise_symmetric(rows: list[dict[str,Any]]) -> list[dict[str,Any]]:
    idx={(r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],r["side_a_weapon"],r["side_b_weapon"]):r for r in rows};out=[];seen=set()
    for r in rows:
        a,b=r["side_a_weapon"],r["side_b_weapon"]
        if a==b:continue
        low,high=sorted((a,b));key=(r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],low,high)
        if key in seen:continue
        seen.add(key);xy=idx.get((r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],low,high));yx=idx.get((r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],high,low))
        if not xy or not yx:continue
        n=int(xy["trials"])+int(yx["trials"]);low_wins=int(xy["a_wins"])+int(yx["b_wins"]);high_wins=int(xy["b_wins"])+int(yx["a_wins"]);draws=int(xy["draws"])+int(yx["draws"]);unresolved=n-low_wins-high_wins-draws
        low_lo,low_hi=_wilson(low_wins,n);high_lo,high_hi=_wilson(high_wins,n);decisive=low_wins+high_wins
        out.append({"tl":r["tl"],"resource_ensemble_id":r["resource_ensemble_id"],"scenario_stratum":r["scenario_stratum"],"weapon_x":low,"weapon_y":high,"paired_trials":n,
                    "weapon_x_win_rate":low_wins/n,"weapon_x_wilson_low":low_lo,"weapon_x_wilson_high":low_hi,"weapon_y_win_rate":high_wins/n,"weapon_y_wilson_low":high_lo,"weapon_y_wilson_high":high_hi,
                    "draw_rate":draws/n,"unresolved_rate":unresolved/n,"weapon_x_decisive_share":low_wins/decisive if decisive else 0.5,"weapon_y_decisive_share":high_wins/decisive if decisive else 0.5,
                    "x_as_a_win_rate":float(xy["a_win_rate"]),"x_as_b_win_rate":int(yx["b_wins"])/int(yx["trials"]),"side_order_gap":float(xy["a_win_rate"])-(int(yx["b_wins"])/int(yx["trials"]))})
    return out


def _pareto(rows: list[dict[str,Any]]) -> tuple[list[dict[str,Any]],list[dict[str,Any]]]:
    idx={(r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],r["side_a_weapon"],r["side_b_weapon"]):r for r in rows}
    contexts=defaultdict(set)
    for r in rows: contexts[(r["tl"],r["resource_ensemble_id"],r["scenario_stratum"],r["side_b_weapon"])].add(r["side_a_weapon"])
    detail=[];counts=Counter();totals=Counter()
    for context,candidate_names in sorted(contexts.items()):
        tl,res,stratum,opponent=context;candidates=[]
        for cand in sorted(candidate_names):
            ca=idx.get((tl,res,stratum,cand,opponent))
            if ca is None:continue
            if cand==opponent:
                n=int(ca["trials"]);decisive=int(ca["a_wins"])+int(ca["b_wins"]);fast=int(ca["a_fast_wins_under25"])+int(ca["b_fast_wins_under25"])
                win_rate=0.5*decisive/n if n else 0.0;fast_rate=0.5*fast/n if n else 0.0;damage_adv=0.0;paired_trials=n
            else:
                cb=idx.get((tl,res,stratum,opponent,cand))
                if cb is None:continue
                paired_trials=int(ca["trials"])+int(cb["trials"]);wins=int(ca["a_wins"])+int(cb["b_wins"]);fast=int(ca["a_fast_wins_under25"])+int(cb["b_fast_wins_under25"])
                win_rate=wins/paired_trials if paired_trials else 0.0;fast_rate=fast/paired_trials if paired_trials else 0.0
                damage_adv=(float(ca["a_damage_advantage_mean"])*int(ca["trials"])-float(cb["a_damage_advantage_mean"])*int(cb["trials"]))/paired_trials if paired_trials else 0.0
            candidates.append({"candidate":cand,"paired_trials":paired_trials,"win_rate":win_rate,"fast_rate":fast_rate,"damage_adv":damage_adv})
        for c in candidates:
            metrics=(c["win_rate"],c["fast_rate"],c["damage_adv"]);dominated_by=[]
            for o in candidates:
                if o is c:continue
                om=(o["win_rate"],o["fast_rate"],o["damage_adv"])
                if all(x>=y-1e-12 for x,y in zip(om,metrics)) and any(x>y+1e-12 for x,y in zip(om,metrics)):
                    dominated_by.append(o["candidate"])
            viable=not dominated_by;counts[(tl,c["candidate"])]+=int(viable);totals[(tl,c["candidate"])]+=1
            detail.append({"tl":tl,"resource_ensemble_id":res,"scenario_stratum":stratum,"opponent_weapon":opponent,"candidate_weapon":c["candidate"],
                           "paired_trials":c["paired_trials"],"side_symmetric_win_rate":c["win_rate"],"side_symmetric_fast_win_rate":c["fast_rate"],"side_symmetric_damage_advantage_mean":c["damage_adv"],
                           "pareto_viable":int(viable),"dominated_by":";".join(sorted(dominated_by))})
    summary=[]
    for key,total in sorted(totals.items()):summary.append({"tl":key[0],"weapon":key[1],"contexts":total,"pareto_viable_contexts":counts[key],"pareto_participation_rate":counts[key]/total if total else 0.0})
    return detail,summary


def _tp_load_surfaces(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expanded: list[dict[str, Any]] = []
    for r in rows:
        for side in ("a", "b"):
            weapon = r["side_a_weapon"] if side == "a" else r["side_b_weapon"]
            expanded.append({
                "tl": int(r["tl"]), "weapon": weapon, "resource_ensemble_id": r["resource_ensemble_id"],
                "scenario_stratum": r["scenario_stratum"], "opponent_weapon": r["side_b_weapon"] if side == "a" else r["side_a_weapon"],
                "base_reactor_tp": float(r[f"{side}_base_reactor_tp"]),
                "base_max_installed_tp_demand": float(r[f"{side}_base_max_installed_tp_demand"]),
                "mean_tp_allocated_per_turn": float(r[f"{side}_mean_tp_allocated_per_turn"]),
                "peak_tp_allocated_per_turn": float(r[f"{side}_peak_tp_allocated_per_turn"]),
                "mean_allocated_vs_base_max_demand": float(r[f"{side}_mean_allocated_vs_base_max_demand"]),
                "peak_allocated_vs_base_max_demand": float(r[f"{side}_peak_allocated_vs_base_max_demand"]),
                "base_max_demand_vs_reactor": float(r[f"{side}_base_max_demand_vs_reactor"]),
            })
    def agg(keys: tuple[str, ...]) -> list[dict[str, Any]]:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for x in expanded: groups[tuple(x[k] for k in keys)].append(x)
        out: list[dict[str, Any]] = []
        metrics = ("base_reactor_tp","base_max_installed_tp_demand","mean_tp_allocated_per_turn","peak_tp_allocated_per_turn","mean_allocated_vs_base_max_demand","peak_allocated_vs_base_max_demand","base_max_demand_vs_reactor")
        for key, rs in sorted(groups.items()):
            row = {k:v for k,v in zip(keys,key)}; row["contexts"] = len(rs)
            for m in metrics: row[f"mean_{m}"] = statistics.fmean(float(x[m]) for x in rs)
            out.append(row)
        return out
    return agg(("tl","weapon","resource_ensemble_id","scenario_stratum")), agg(("tl","weapon"))


def _candidate_context_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    idx={(int(r["tl"]),r["resource_ensemble_id"],r["scenario_stratum"],r["side_a_weapon"],r["side_b_weapon"]):r for r in rows}
    out=[]
    for r in rows:
        tl=int(r["tl"]);res=r["resource_ensemble_id"];stratum=r["scenario_stratum"];cand=r["side_a_weapon"];opp=r["side_b_weapon"]
        ca=r
        if cand==opp:
            n=int(ca["trials"]); decisive=int(ca["a_wins"])+int(ca["b_wins"])
            win=0.5*decisive/n if n else 0.0; damage=0.0
            tp=(float(ca["a_mean_allocated_vs_base_max_demand"])+float(ca["b_mean_allocated_vs_base_max_demand"]))/2
            fulfill=(float(ca["a_tp_fulfillment_rate"])+float(ca["b_tp_fulfillment_rate"]))/2
            ammo=(float(ca["a_primary_ammo_exhausted_rate"])+float(ca["b_primary_ammo_exhausted_rate"]))/2
        else:
            cb=idx.get((tl,res,stratum,opp,cand))
            if cb is None: continue
            n=int(ca["trials"])+int(cb["trials"]); wins=int(ca["a_wins"])+int(cb["b_wins"])
            win=wins/n if n else 0.0
            damage=(float(ca["a_damage_advantage_mean"])*int(ca["trials"])-float(cb["a_damage_advantage_mean"])*int(cb["trials"]))/n if n else 0.0
            tp=(float(ca["a_mean_allocated_vs_base_max_demand"])*int(ca["trials"])+float(cb["b_mean_allocated_vs_base_max_demand"])*int(cb["trials"]))/n
            fulfill=(float(ca["a_tp_fulfillment_rate"])*int(ca["trials"])+float(cb["b_tp_fulfillment_rate"])*int(cb["trials"]))/n
            ammo=(float(ca["a_primary_ammo_exhausted_rate"])*int(ca["trials"])+float(cb["b_primary_ammo_exhausted_rate"])*int(cb["trials"]))/n
        out.append({"tl":tl,"resource_ensemble_id":res,"scenario_stratum":stratum,"candidate_weapon":cand,"opponent_weapon":opp,
                    "win_rate":win,"damage_advantage":damage,"tp_fulfillment_rate":fulfill,"allocated_vs_base_max_demand":tp,
                    "ammo_exhausted_rate":ammo,"duration_concern_rate":float(ca["gameplay_duration_concern_rate"])})
    return out


def _combat_gated_strategic_viability(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    contexts=_candidate_context_rows(rows); groups=defaultdict(list)
    for r in contexts: groups[(r["tl"],r["candidate_weapon"])].append(r)
    result=[]
    for (tl,weapon),rs in sorted(groups.items()):
        wins=[float(x["win_rate"]) for x in rs]; by_res=defaultdict(list); by_stratum=defaultdict(list)
        for x in rs:
            by_res[x["resource_ensemble_id"]].append(float(x["win_rate"])); by_stratum[x["scenario_stratum"]].append(float(x["win_rate"]))
        result.append({"tl":tl,"weapon":weapon,"contexts":len(rs),"mean_win_rate":statistics.fmean(wins),"p25_win_rate":_q(wins,.25),"p90_win_rate":_q(wins,.90),
                       "mean_damage_advantage":statistics.fmean(float(x["damage_advantage"]) for x in rs),"worst_resource_mean_win_rate":min(statistics.fmean(v) for v in by_res.values()),
                       "worst_stratum_mean_win_rate":min(statistics.fmean(v) for v in by_stratum.values()),"mean_tp_fulfillment_rate":statistics.fmean(float(x["tp_fulfillment_rate"]) for x in rs),
                       "mean_allocated_vs_base_max_demand":statistics.fmean(float(x["allocated_vs_base_max_demand"]) for x in rs),"mean_primary_ammo_exhausted_rate":statistics.fmean(float(x["ammo_exhausted_rate"]) for x in rs),
                       "mean_duration_concern_rate":statistics.fmean(float(x["duration_concern_rate"]) for x in rs)})
    for tl in sorted({int(r["tl"]) for r in result}):
        tlrows=[r for r in result if int(r["tl"])==tl]
        for c in tlrows:
            combat=(c["mean_win_rate"],c["p25_win_rate"],c["p90_win_rate"],c["mean_damage_advantage"]); dom=[]
            for o in tlrows:
                if o is c: continue
                om=(o["mean_win_rate"],o["p25_win_rate"],o["p90_win_rate"],o["mean_damage_advantage"])
                if all(x>=y-1e-12 for x,y in zip(om,combat)) and any(x>y+1e-12 for x,y in zip(om,combat)): dom.append(o["weapon"])
            c["combat_viability_gate"]=int(not dom); c["combat_dominated_by"]=";".join(sorted(dom))
        eligible=[r for r in tlrows if r["combat_viability_gate"]]
        for c in tlrows:
            strategic_dom=[]
            if c["combat_viability_gate"]:
                metrics=(c["mean_win_rate"],c["p25_win_rate"],c["p90_win_rate"],c["worst_resource_mean_win_rate"],c["worst_stratum_mean_win_rate"],c["mean_tp_fulfillment_rate"],1-c["mean_primary_ammo_exhausted_rate"],1-c["mean_duration_concern_rate"])
                for o in eligible:
                    if o is c: continue
                    om=(o["mean_win_rate"],o["p25_win_rate"],o["p90_win_rate"],o["worst_resource_mean_win_rate"],o["worst_stratum_mean_win_rate"],o["mean_tp_fulfillment_rate"],1-o["mean_primary_ammo_exhausted_rate"],1-o["mean_duration_concern_rate"])
                    if all(x>=y-1e-12 for x,y in zip(om,metrics)) and any(x>y+1e-12 for x,y in zip(om,metrics)): strategic_dom.append(o["weapon"])
            c["strategic_pareto_eligible"]=int(c["combat_viability_gate"]); c["strategic_pareto_viable"]=int(c["combat_viability_gate"] and not strategic_dom); c["strategic_dominated_by"]=";".join(sorted(strategic_dom))
            c["resource_or_robustness_only_frontier"]=0
    return result


def _role_response_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    role_map={"K": {"ARMOR_PRESSURE"}, "E": {"SHIELD_PRESSURE"}, "M_GP": {"BALANCED_CORE_NO_PDS"}, "M_SWARMER": {"KINETIC_PDS_PRESSURE","ENERGY_PDS_PRESSURE","AMM_PDS_PRESSURE"}}
    contexts=_candidate_context_rows(rows); groups=defaultdict(list)
    for r in contexts:
        if r["scenario_stratum"] in role_map.get(r["candidate_weapon"], set()): groups[(r["tl"],r["candidate_weapon"])].append(r)
    out=[]
    for (tl,w),rs in sorted(groups.items()):
        out.append({"tl":tl,"weapon":w,"role_contexts":len(rs),"role_mean_win_rate":statistics.fmean(float(x["win_rate"]) for x in rs),"role_mean_damage_advantage":statistics.fmean(float(x["damage_advantage"]) for x in rs),"role_mean_tp_fulfillment_rate":statistics.fmean(float(x["tp_fulfillment_rate"]) for x in rs)})
    return out


def merge_substantive_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path,
                              expected_trials_per_scenario: int|None=None) -> dict[str,Any]:
    doc=load_json(study_path);errors=validate_study(doc)+validate_population(repo,doc)
    if errors:return {"schemaVersion":_result_schema(doc),"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    expected_trials=int(expected_trials_per_scenario or doc["substantiveTrialsPerScenario"]);outdir.mkdir(parents=True,exist_ok=True);manifest=_read_csv(repo/doc["stageAExperimentManifest"]);source=repo/doc["matrix"];before=_sha(source)
    rows=[];audits=[];expected=0
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json";rp=d/"scenario_response_surface.csv"
        if not sp.exists() or not rp.exists():continue
        payload=json.loads(sp.read_text(encoding="utf-8-sig"));analysis=payload.get("analysis",payload);start=int(analysis["batchStart"]);end=int(analysis["batchEnd"]);br=_read_csv(rp)
        ids=[r["scenario_id"] for r in manifest[start:end]]==[r["scenario_id"] for r in br];ok=bool(analysis.get("passed",False)) and start==expected and len(br)==end-start and ids and all(int(r["trials"])==expected_trials for r in br)
        audits.append({"batch":d.name,"start":start,"end":end,"scenario_cells":len(br),"combat_trials":sum(int(r["trials"]) for r in br),"ids_match":int(ids),"passed":int(ok)})
        if not ok:continue
        rows.extend(br);expected=end
    failures=[]
    if expected!=len(manifest):failures.append("batch-coverage-incomplete")
    if len(rows)!=EXPECTED_SCENARIOS:failures.append("merged-scenario-count")
    total_trials=sum(int(r["trials"]) for r in rows)
    target_total=EXPECTED_SCENARIOS*expected_trials
    if total_trials!=target_total:failures.append("merged-trial-count")
    if any(int(r["error_trials"])!=0 for r in rows):failures.append("trial-errors")
    if any(float(r["a_nonstandoff_open_orders_mean"])>0 or float(r["b_nonstandoff_open_orders_mean"])>0 for r in rows):failures.append("engage-adaptive-nonstandoff-open-regression")
    after=_sha(source)
    if before!=after:failures.append("source-matrix-modified")
    _write_csv(outdir/"batch_merge_audit.csv",audits);_write_csv(outdir/"scenario_response_surface.csv",rows)
    tl_weapon=_aggregate_rows(rows,("tl","side_a_weapon"));pair_tl=_aggregate_rows(rows,("tl","side_a_weapon","side_b_weapon"));stratum=_aggregate_rows(rows,("tl","scenario_stratum","side_a_weapon"));resource=_aggregate_rows(rows,("tl","resource_ensemble_id","side_a_weapon"));overall_weapon=_aggregate_rows(rows,("side_a_weapon",))
    _write_csv(outdir/"weapon_tl_response_curves.csv",tl_weapon);_write_csv(outdir/"weapon_pair_tl_response_curves.csv",pair_tl);_write_csv(outdir/"stratum_response_surface.csv",stratum);_write_csv(outdir/"resource_response_surface.csv",resource);_write_csv(outdir/"weapon_overall_response.csv",overall_weapon)
    _write_csv(outdir/"counter_effects.csv",_counter_effects(rows));_write_csv(outdir/"resource_effects.csv",_resource_effects(rows));_write_csv(outdir/"pairwise_symmetric_response.csv",_pairwise_symmetric(rows));pareto_detail,pareto_summary=_pareto(rows);_write_csv(outdir/"pareto_choice_surface.csv",pareto_detail);_write_csv(outdir/"pareto_participation_summary.csv",pareto_summary)
    extra_artifacts=[]
    if int(doc.get("checkpoint",0)) == 148:
        tp_detail,tp_tl=_tp_load_surfaces(rows);_write_csv(outdir/"tp_load_response_surface.csv",tp_detail);_write_csv(outdir/"tp_load_weapon_tl_summary.csv",tp_tl)
        strategic=_combat_gated_strategic_viability(rows);_write_csv(outdir/"combat_gated_strategic_viability.csv",strategic)
        roles=_role_response_summary(rows);_write_csv(outdir/"role_response_summary.csv",roles)
        extra_artifacts=["tp_load_response_surface.csv","tp_load_weapon_tl_summary.csv","combat_gated_strategic_viability.csv","role_response_summary.csv"]
    # High-level diagnostics are descriptive only. No threshold here changes mechanics or promotes values.
    total_a=sum(int(r["a_wins"]) for r in rows);total_b=sum(int(r["b_wins"]) for r in rows);total_caps=sum(int(r["turn_cap_sentinels"]) for r in rows);total_long=sum(int(r["resolved_ge25"]) for r in rows);total_stale=sum(int(r["safe_stalemates"]) for r in rows)
    summary={"schemaVersion":_result_schema(doc),"checkpoint":int(doc["checkpoint"]),"baseCheckpoint":int(doc["baseCheckpoint"]),"mode":"merged-substantive","passed":not failures,"failedGates":failures,
             "stageAScenarios":len(rows),"resourceEnvironmentCount":EXPECTED_RESOURCES,"scenarioStrataCount":EXPECTED_STRATA,"orderedSameTlWeaponPairings":EXPECTED_PAIRINGS,
             "trialsPerScenario":expected_trials,"substantiveCombatTrials":total_trials,"aWins":total_a,"bWins":total_b,"draws":sum(int(r["draws"]) for r in rows),
             "turnCapSentinels":total_caps,"resolvedGe25":total_long,"safeStalemates":total_stale,"gameplayDurationConcernRate":(total_caps+total_long)/total_trials if total_trials else 0.0,
             "sourceMatrixUnmodified":before==after,"automaticPromotion":False,"tuningAllowed":False,"stageBAutomatic":False,
             "combatDoctrine":_combat_doctrine(doc),
             "baseMaxTpDemandPolicy":doc.get("baseMaxTpDemandPolicy","historical-not-recorded"),
             "strategicParetoPolicy":doc.get("strategicParetoPolicy","historical-original"),
             "responseArtifacts":["scenario_response_surface.csv","weapon_tl_response_curves.csv","weapon_pair_tl_response_curves.csv","stratum_response_surface.csv","resource_response_surface.csv","weapon_overall_response.csv","counter_effects.csv","resource_effects.csv","pairwise_symmetric_response.csv","pareto_choice_surface.csv","pareto_participation_summary.csv"]+extra_artifacts,
             "interpretation":"Broad substantive whole-combat Stage-A response surface under the study-selected doctrine. Review role/combat viability and multivariate evidence before any tuning; Stage B is not automatic."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8");return summary
