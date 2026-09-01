from __future__ import annotations

import copy
import csv
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .combat_model_reconciliation import apply_combat_model_candidate
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant, build_space
from .study import canonicalize_relocated_references, load_json, resolve_relocated_path

RESULT_SCHEMA = "star-cluster-cp140-stage-a-integration-result-v0.1"
STAGE_A_SCENARIOS = 8220
SMOKE_TRIALS = 8220
WEAPON_MAP = {"K": "Kinetic", "E": "Energy", "M_GP": "Missile", "M_SWARMER": "Missile"}
PAYLOAD_MAP = {"K": "GP", "E": "GP", "M_GP": "GP", "M_SWARMER": "Swarmer"}
PDS_BY_STRATUM = {
    "KINETIC_PDS_PRESSURE": "Kinetic",
    "ENERGY_PDS_PRESSURE": "Energy",
    "AMM_PDS_PRESSURE": "AMM",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with resolve_relocated_path(path).open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


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


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-cp140-stage-a-integration-study-v0.1": errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 140: errors.append("checkpoint")
    if int(doc.get("baseCheckpoint", 0)) != 139: errors.append("baseCheckpoint")
    if doc.get("researchDamageModel") != "def-res-v1": errors.append("researchDamageModel")
    if int(doc.get("expectedStageAScenarios", 0)) != STAGE_A_SCENARIOS: errors.append("expectedStageAScenarios")
    if int(doc.get("integrationSmokeTrials", 0)) != SMOKE_TRIALS: errors.append("integrationSmokeTrials")
    if int(doc.get("substantiveCombatTrials", -1)) != 0: errors.append("substantiveCombatTrials")
    if bool(doc.get("automaticPromotion")): errors.append("automaticPromotion")
    return errors


def _energy_mode_tp(standard: int) -> tuple[int, int, int]:
    # v22B-S.1 resource trajectories define Energy Standard TP. Preserve the
    # accepted low/standard/overload ordering by retaining the historical 0.5x/1.5x
    # relation, rounded upward to integer Tactical Power.
    low = max(1, (standard + 1) // 2)
    overload = max(standard + 1, (3 * standard + 1) // 2)
    return low, standard, overload


def _resource_rows(repo: Path, doc: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    return _read_csv(repo / doc["resourceEnsemble"]), _read_csv(repo / doc["resourceEnsembleTl"])


def build_resource_matrix(repo: Path, matrix_relative: str, ensemble_id: str,
                          ensemble_rows: list[dict[str, str]], tl_rows: list[dict[str, str]]) -> CandidateMatrix:
    matrix = CandidateMatrix(repo, matrix_relative)
    apply_combat_model_candidate(matrix)
    ensemble = next(r for r in ensemble_rows if r["ensemble_id"] == ensemble_id)
    per_tl = {int(r["tl"]): r for r in tl_rows if r["ensemble_id"] == ensemble_id}
    if len(per_tl) != 9:
        raise ValueError(f"resource ensemble {ensemble_id} must have nine TL rows")
    matrix.resource_ensemble_id = ensemble_id
    matrix.resource_ensemble_role = ensemble["ensemble_role"]
    matrix.resource_aux_proxy_profile = ensemble["aux_proxy_profile"]
    matrix.resource_aux_proxy_execution = "metadata_only_no_fake_tp_demand"

    # Supply and firing demand bind directly to the native-validated v22C rows.
    for tl in range(1, 10):
        row = per_tl[tl]
        reactor = matrix.p("reactor", tl)
        reactor["operationalTp"] = int(row["reactor_undamaged_operational_tp"])
        reactor["degradedTp"] = int(row["reactor_degraded_tp"])
        reactor["emergencyTp"] = int(row["reactor_damaged_emergency_tp"])
        matrix.p("kinetic_main", tl)["firingTp"] = int(row["K_weapon_tp"])
        low, standard, overload = _energy_mode_tp(int(row["E_weapon_tp"]))
        energy = matrix.p("energy_main", tl)
        energy["lowTp"], energy["standardTp"], energy["overloadTp"] = low, standard, overload
        matrix.p("missile_delivery", tl)["launchTp"] = int(row["M_weapon_tp"])

    # Weapon Space is explicit for all current v22C candidates. Historical retains CP139/CP138 values.
    if ensemble["weapon_space_pattern"] == "Equal6":
        for tl in range(1, 10):
            for key in ("kinetic_main", "energy_main", "missile_delivery"):
                matrix.p(key, tl)["space"] = 6

    # v22B-S.1 miniaturization semantics: a false lineage uses its TL1 footprint
    # throughout; a true lineage retains the current TL-specific footprint.
    mini = ensemble["miniaturization"]
    tl1_space = {key: int(matrix.p(key, 1)["space"]) for key in ("reactor", "stl", "ftl", "computer", "sensor", "shield")}
    if mini == "Selective_NoMajorMini":
        freeze = ("reactor", "stl", "ftl")
    elif mini == "Selective_PropulsionMini":
        freeze = ("reactor",)
    elif mini == "NoMini":
        freeze = ("reactor", "stl", "ftl", "computer", "sensor", "shield")
    else:
        freeze = ()
    for key in freeze:
        for tl in range(1, 10):
            matrix.p(key, tl)["space"] = tl1_space[key]
    return matrix


@dataclass(frozen=True, slots=True)
class BoundScenario:
    source: dict[str, str]
    variant: EcologyVariant
    build_policy_a: str
    build_policy_b: str
    start_range: int
    aux_proxy_binding: str


def _features_for_stratum(stratum: str, tl: int) -> dict[str, Any]:
    base = dict(shield=True, ecm=False, eccm=False, pds=None, hardener=False, armor="mainline", max_turns=60, start=(-5, 5))
    if stratum in PDS_BY_STRATUM:
        base["pds"] = PDS_BY_STRATUM[stratum]
    elif stratum == "SHIELD_PRESSURE":
        base["hardener"] = tl >= 3
    elif stratum == "ARMOR_PRESSURE":
        base["shield"] = False
    elif stratum == "EW_CONTEST":
        base["ecm"] = True; base["eccm"] = True
    elif stratum == "MOBILITY_STANDOFF":
        base["start"] = (-3, 3)
    elif stratum == "RECOVERY_ATTRITION":
        base["hardener"] = tl >= 3; base["max_turns"] = 90
    elif stratum == "POWER_CRISIS":
        base["ecm"] = True; base["eccm"] = True; base["pds"] = "AMM"; base["hardener"] = tl >= 3; base["start"] = (-2, 1)
    elif stratum != "BALANCED_CORE_NO_PDS":
        raise ValueError(f"unknown Stage A stratum {stratum}")
    return base


def _make_build(matrix: CandidateMatrix, tl: int, weapon_variant: str, stratum: str, side: str) -> tuple[EcologyBuild, str]:
    fam = WEAPON_MAP[weapon_variant]
    payload = PAYLOAD_MAP[weapon_variant]
    f = _features_for_stratum(stratum, tl)
    combat = build_space(matrix, tl, fam, 1, 1, bool(f["shield"]), bool(f["ecm"]), bool(f["eccm"]), f["pds"], bool(f["hardener"]))
    cap = matrix.capacity(tl)
    if combat > cap:
        raise ValueError(f"illegal Stage A build {stratum} TL{tl} {weapon_variant} {side}: {combat}>{cap}")
    policy = "+".join([
        "shield" if f["shield"] else "no-shield", "mainline-armor",
        "ecm" if f["ecm"] else "no-ecm", "eccm" if f["eccm"] else "no-eccm",
        (str(f["pds"]) + "-pds") if f["pds"] else "no-pds",
        "shield-hardener" if f["hardener"] else "no-hardener",
    ])
    b = EcologyBuild(
        id=f"cp140-{matrix.resource_ensemble_id.lower()}-tl{tl}-{weapon_variant.lower()}-{stratum.lower()}-{side.lower()}",
        tl=tl, archetype=f"cp140-{stratum.lower()}", weapon_family=fam, main_count=1, reactor_count=1,
        shield=bool(f["shield"]), ecm=bool(f["ecm"]), eccm=bool(f["eccm"]), pds_family=f["pds"],
        shield_hardener=bool(f["hardener"]), capacity=cap, combat_space=combat, mission_aux_space=cap-combat,
        missile_payload=payload, armor_profile=str(f["armor"]),
    )
    return b, policy


def bind_scenario(matrix: CandidateMatrix, row: dict[str, str]) -> BoundScenario:
    tl = int(row["tl"]); stratum = row["scenario_stratum"]
    a, pa = _make_build(matrix, tl, row["side_a_weapon"], stratum, "A")
    b, pb = _make_build(matrix, tl, row["side_b_weapon"], stratum, "B")
    f = _features_for_stratum(stratum, tl)
    qa, qb = f["start"]
    group = f"cp140-{row['scenario_id']}"
    variant = EcologyVariant(
        id=row["scenario_id"], tl=tl, side_a=a, side_b=b, movement_order="SideAFirst",
        geometry=row["geometry"], population="cp140-v22c-stage-a-integration", start_q_a=int(qa), start_q_b=int(qb),
        max_turns=int(f["max_turns"]), scenario_group=group,
        physical_id_a=group+":ship-a", physical_id_b=group+":ship-b",
    )
    return BoundScenario(row, variant, pa, pb, abs(int(qb)-int(qa)), getattr(matrix, "resource_aux_proxy_execution", ""))


def _battle_metrics(result, turn_rows: list[dict[str, Any]], side: str) -> dict[str, Any]:
    own = result.side_a if side == "A" else result.side_b
    relevant = [r for r in turn_rows if r["side_id"] == side]
    received = result.side_a if side == "A" else result.side_b
    opponent_received = result.side_b if side == "A" else result.side_a
    damage_received = received.hull_damage + received.armor_integrity_damage + received.shield_absorbed
    damage_inflicted = opponent_received.hull_damage + opponent_received.armor_integrity_damage + opponent_received.shield_absorbed
    last = relevant[-1] if relevant else {}
    primary_remaining = last.get("kinetic_ammo_remaining", "") if last.get("kinetic_ammo_remaining", "") != "" else last.get("missile_flights_remaining", "")
    primary_exhausted = primary_remaining != "" and int(primary_remaining) <= 0
    pds_remaining = last.get("pds_ammo_remaining", "")
    pds_exhausted = pds_remaining != "" and int(pds_remaining) <= 0
    return {
        "winner": result.winner, "turns_elapsed": result.turns, "mission_success": "",
        "damage_inflicted": damage_inflicted, "damage_received": damage_received,
        "tp_conflict_turns": sum(int(r["tp_conflict_flag"]) for r in relevant),
        "tp_denied_total_battle": sum(int(r["tp_denied_total"]) for r in relevant),
        "tp_headroom_turns": sum(int(r.get("tp_headroom_after_desired", 0)) > 0 for r in relevant),
        "overload_count": int(own.reactor_overload_activations + own.energy_overload_shots), "forced_overload_count": 0,
        "weapon_shots": int(own.direct_shots + own.missile_launches), "missile_flights_launched": int(own.missile_launches),
        "pds_attempts": int(own.pds_attempts), "fuel_used": int(own.movement_fuel),
        "ammo_exhausted_flag": int(primary_exhausted or pds_exhausted),
    }


def _binding_row(bound: BoundScenario) -> dict[str, Any]:
    row = bound.source
    v = bound.variant
    return {
        **row,
        "bound": 1, "start_range": bound.start_range, "max_turns": v.max_turns,
        "build_a": v.side_a.id, "build_b": v.side_b.id,
        "build_policy_a": bound.build_policy_a, "build_policy_b": bound.build_policy_b,
        "combat_space_a": v.side_a.combat_space, "combat_space_b": v.side_b.combat_space,
        "mission_aux_space_a": v.side_a.mission_aux_space, "mission_aux_space_b": v.side_b.mission_aux_space,
        "aux_proxy_binding": bound.aux_proxy_binding,
    }


def _validate_contract_rows(manifest: list[dict[str, str]], telemetry_contract: dict[str, Any],
                            turn_rows: list[dict[str, Any]], battle_rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    if len(manifest) != STAGE_A_SCENARIOS: failures.append("stage_a_manifest_count")
    ids = [r["scenario_id"] for r in manifest]
    if len(ids) != len(set(ids)): failures.append("stage_a_duplicate_scenario_id")
    required_turn = [x["field"] for x in telemetry_contract["turn_fields"]]
    if turn_rows:
        missing = [x for x in required_turn if x not in turn_rows[0]]
        if missing: failures.append("turn_telemetry_missing:" + ",".join(missing))
    required_battle = [x["field"] for x in telemetry_contract["battle_fields"]]
    if battle_rows:
        missing = [x for x in required_battle if x not in battle_rows[0]]
        if missing: failures.append("battle_telemetry_missing:" + ",".join(missing))
    return failures


def _instrumentation_equivalence_rows(matrices: dict[str, CandidateMatrix], bindings: list[BoundScenario],
                                       master_seed: int) -> list[dict[str, Any]]:
    """Replay a representative deterministic set with telemetry disabled/enabled.

    Equality here is deliberately strict: the complete FullMapTrialResult, including
    all existing SideTelemetry/FullMapTelemetry fields and final coordinates, must be
    identical.  The CP140 shadow-demand instrumentation therefore cannot consume RNG
    or alter executable tactical state.
    """
    selected: list[BoundScenario] = []
    seen: set[str] = set()
    for stratum in sorted({b.source["scenario_stratum"] for b in bindings}):
        candidate = next(b for b in bindings if b.source["scenario_stratum"] == stratum)
        if candidate.source["scenario_id"] not in seen:
            selected.append(candidate); seen.add(candidate.source["scenario_id"])
    for ensemble_id in ("R4_TIGHT_HIGH_DEMAND", "R5_CENTRAL_HIGH_DEMAND"):
        candidate = next(b for b in bindings if b.source["resource_ensemble_id"] == ensemble_id and b.source["scenario_stratum"] == "POWER_CRISIS")
        if candidate.source["scenario_id"] not in seen:
            selected.append(candidate); seen.add(candidate.source["scenario_id"])
    rows: list[dict[str, Any]] = []
    for i, bound in enumerate(selected):
        matrix = matrices[bound.source["resource_ensemble_id"]]
        base = run_trial_full_map(matrix, bound.variant, master_seed, 9000 + i)
        sink: list[dict[str, Any]] = []
        ctx = {
            "scenario_id": bound.source["scenario_id"], "resource_ensemble_id": bound.source["resource_ensemble_id"],
            "weapon_a": bound.source["side_a_weapon"], "weapon_b": bound.source["side_b_weapon"],
        }
        observed = run_trial_full_map(matrix, bound.variant, master_seed, 9000 + i,
                                      turn_telemetry_sink=sink, telemetry_context=ctx)
        identical = asdict(base) == asdict(observed)
        rows.append({
            "scenario_id": bound.source["scenario_id"], "scenario_stratum": bound.source["scenario_stratum"],
            "resource_ensemble_id": bound.source["resource_ensemble_id"], "trial_index": 9000 + i,
            "result_identical": int(identical), "winner_without": base.winner, "winner_with": observed.winner,
            "turns_without": base.turns, "turns_with": observed.turns, "telemetry_rows": len(sink),
            "error_without": base.error, "error_with": observed.error,
        })
    return rows


_CP140_WORKER_MATRICES: dict[str, CandidateMatrix] | None = None


def _cp140_worker_init(repo_text: str, matrix_relative: str,
                       ensemble_rows: list[dict[str, str]], tl_rows: list[dict[str, str]]) -> None:
    global _CP140_WORKER_MATRICES
    repo = Path(repo_text)
    ids = sorted({r["ensemble_id"] for r in ensemble_rows})
    _CP140_WORKER_MATRICES = {
        eid: build_resource_matrix(repo, matrix_relative, eid, ensemble_rows, tl_rows)
        for eid in ids
    }


def _cp140_execute_bound_task(args: tuple[int, BoundScenario, int]) -> dict[str, Any]:
    idx, bound, master_seed = args
    if _CP140_WORKER_MATRICES is None:
        raise RuntimeError("CP140 worker matrices are not initialized")
    matrix = _CP140_WORKER_MATRICES[bound.source["resource_ensemble_id"]]
    local_turns: list[dict[str, Any]] = []
    ctx = {
        "scenario_id": bound.source["scenario_id"], "resource_ensemble_id": bound.source["resource_ensemble_id"],
        "weapon_a": bound.source["side_a_weapon"], "weapon_b": bound.source["side_b_weapon"],
    }
    result = run_trial_full_map(matrix, bound.variant, master_seed, 0,
                                turn_telemetry_sink=local_turns, telemetry_context=ctx)
    smoke = {
        "scenario_id": bound.source["scenario_id"], "tl": bound.source["tl"],
        "side_a_weapon": bound.source["side_a_weapon"], "side_b_weapon": bound.source["side_b_weapon"],
        "resource_ensemble_id": bound.source["resource_ensemble_id"], "scenario_stratum": bound.source["scenario_stratum"],
        "winner": result.winner, "turns": result.turns, "unresolved": int(result.unresolved), "error": result.error,
        "turn_telemetry_rows": len(local_turns), "expected_turn_telemetry_rows": 2 * result.turns,
        "telemetry_row_coverage_pass": int(len(local_turns) == 2 * result.turns),
        "tp_conflict_turns_a": sum(int(r["tp_conflict_flag"]) for r in local_turns if r["side_id"] == "A"),
        "tp_conflict_turns_b": sum(int(r["tp_conflict_flag"]) for r in local_turns if r["side_id"] == "B"),
        "tp_denied_a": sum(int(r["tp_denied_total"]) for r in local_turns if r["side_id"] == "A"),
        "tp_denied_b": sum(int(r["tp_denied_total"]) for r in local_turns if r["side_id"] == "B"),
        "def_res_packets_a": result.side_a.def_res_packets, "def_res_packets_b": result.side_b.def_res_packets,
    }
    battles = []
    for side in ("A", "B"):
        bm = _battle_metrics(result, local_turns, side)
        battles.append({"scenario_id": bound.source["scenario_id"], "trial_id": f"{bound.source['scenario_id']}:0", "side_id": side, **bm})
    samples: list[dict[str, Any]] = []
    for side_label in ("A", "B"):
        side_rows = [r for r in local_turns if r["side_id"] == side_label]
        if not side_rows:
            continue
        chosen = [side_rows[0], side_rows[-1]]
        conflict = next((r for r in side_rows if int(r["tp_conflict_flag"])), None)
        if conflict is not None:
            chosen.append(conflict)
        seen_rows: set[tuple[int, str]] = set()
        for r in chosen:
            key = (int(r["turn"]), str(r["side_id"]))
            if key not in seen_rows:
                samples.append(dict(r)); seen_rows.add(key)
    first_turn = dict(local_turns[0]) if local_turns else None
    schema_consistent = int(not local_turns or all(tuple(r.keys()) == tuple(local_turns[0].keys()) for r in local_turns))
    return {
        "index": idx, "smoke": smoke, "turn_count": len(local_turns),
        "turn_first": first_turn, "turn_samples": samples,
        "turn_schema_consistent": schema_consistent, "battles": battles,
    }


def _execute_smoke_parallel(repo: Path, matrix_relative: str, ensemble_rows: list[dict[str, str]],
                            tl_rows: list[dict[str, str]], bindings: list[BoundScenario],
                            master_seed: int, jobs: int,
                            batch_size: int = 1024) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, list[dict[str, Any]], dict[str, Any] | None, int]:
    """Execute the one-trial smoke with bounded-memory telemetry aggregation.

    Every turn is observed and contributes to coverage/conflict/battle aggregates in
    the worker. CP140 persists a deterministic turn-level sample rather than a raw
    all-turn CSV. Worker pools are deliberately recycled between deterministic
    batches: long-lived processes in this telemetry-heavy workload accumulate enough
    allocator state to produce severe late-run slowdown, while fresh pools reproduce
    identical results and keep native acceptance practical.
    """
    jobs = max(1, min(int(jobs), len(bindings)))
    tasks = [(i, b, master_seed) for i, b in enumerate(bindings)]
    smoke_rows: list[dict[str, Any]] = []
    battle_rows: list[dict[str, Any]] = []
    turn_samples: list[dict[str, Any]] = []
    turn_count = 0
    first_turn: dict[str, Any] | None = None
    schema_consistency_pass = 0

    def consume(completed) -> None:
        nonlocal turn_count, first_turn, schema_consistency_pass
        for item in completed:
            smoke_rows.append(item["smoke"])
            battle_rows.extend(item["battles"])
            turn_samples.extend(item["turn_samples"])
            turn_count += int(item["turn_count"])
            schema_consistency_pass += int(item["turn_schema_consistent"])
            if first_turn is None and item["turn_first"] is not None:
                first_turn = dict(item["turn_first"])

    if jobs == 1:
        _cp140_worker_init(str(repo), matrix_relative, ensemble_rows, tl_rows)
        consume(_cp140_execute_bound_task(t) for t in tasks)
    else:
        ctx = get_context("spawn")
        step = max(1, int(batch_size))
        for offset in range(0, len(tasks), step):
            batch = tasks[offset:offset + step]
            with ProcessPoolExecutor(
                max_workers=min(jobs, len(batch)), mp_context=ctx, initializer=_cp140_worker_init,
                initargs=(str(repo), matrix_relative, ensemble_rows, tl_rows),
            ) as ex:
                consume(ex.map(_cp140_execute_bound_task, batch, chunksize=8))
    return smoke_rows, battle_rows, turn_count, turn_samples, first_turn, schema_consistency_pass


def run_integration(repo: Path, study_path: Path, outdir: Path, mode: str = "smoke", jobs: int = 24,
                    batch_start: int = 0, batch_end: int | None = None) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["study-validation:"+",".join(errors)]}
    if mode not in ("plan", "smoke"):
        raise ValueError("CP140 supports plan/smoke only; substantive Stage A is intentionally deferred")
    outdir.mkdir(parents=True, exist_ok=True)
    source_matrix = repo / doc["matrix"]
    before_hash = _sha(source_matrix)
    manifest = _read_csv(repo / doc["stageAExperimentManifest"])
    batch_start = max(0, int(batch_start))
    batch_end = len(manifest) if batch_end is None else min(len(manifest), int(batch_end))
    if batch_start >= batch_end:
        return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["invalid-batch-range"], "batchStart": batch_start, "batchEnd": batch_end}
    ensemble_rows, tl_rows = _resource_rows(repo, doc)
    turn_contract = load_json(repo / doc["telemetryContract"])
    strata_registry = load_json(repo / doc["scenarioStrata"])

    matrices = {eid: build_resource_matrix(repo, doc["matrix"], eid, ensemble_rows, tl_rows) for eid in sorted({r["ensemble_id"] for r in ensemble_rows})}
    bindings: list[BoundScenario] = []
    binding_failures: list[dict[str, Any]] = []
    for row in manifest:
        try:
            bindings.append(bind_scenario(matrices[row["resource_ensemble_id"]], row))
        except Exception as exc:
            binding_failures.append({"scenario_id": row.get("scenario_id",""), "error": f"{type(exc).__name__}: {exc}"})
    _write_csv(outdir / "scenario_bindings.csv", [_binding_row(b) for b in (bindings if mode == "plan" else bindings[batch_start:batch_end])] + binding_failures)

    # Resource binding audit: exact executable values after the CP139 combat overlay and v22C resource overlay.
    resource_audit: list[dict[str, Any]] = []
    for er in ensemble_rows:
        m = matrices[er["ensemble_id"]]
        for tl in range(1, 10):
            k=m.p("kinetic_main",tl); e=m.p("energy_main",tl); mm=m.p("missile_delivery",tl); r=m.p("reactor",tl)
            resource_audit.append({
                "ensemble_id":er["ensemble_id"],"tl":tl,"reactor_operational_tp":r["operationalTp"],"reactor_degraded_tp":r["degradedTp"],"reactor_emergency_tp":r["emergencyTp"],
                "K_firing_tp":k["firingTp"],"E_low_tp":e["lowTp"],"E_standard_tp":e["standardTp"],"E_overload_tp":e["overloadTp"],"M_launch_tp":mm["launchTp"],
                "K_space":k["space"],"E_space":e["space"],"M_space":mm["space"],"reactor_space":r["space"],"stl_space":m.p("stl",tl)["space"],"ftl_space":m.p("ftl",tl)["space"],
                "aux_proxy_profile":er["aux_proxy_profile"],"aux_proxy_execution":"metadata_only_no_fake_tp_demand",
            })
    _write_csv(outdir / "resource_binding_audit.csv", resource_audit)

    stratum_audit = []
    for rec in strata_registry["records"]:
        sid=rec["stratum_id"]; rows=[b for b in bindings if b.source["scenario_stratum"]==sid]
        stratum_audit.append({"stratum_id":sid,"expected_scenarios":822,"bound_scenarios":len(rows),"start_ranges":";".join(map(str,sorted({b.start_range for b in rows}))),"max_turns":";".join(map(str,sorted({b.variant.max_turns for b in rows}))),"binding_rule":rec["binding_rule"]})
    _write_csv(outdir / "stratum_binding_audit.csv", stratum_audit)

    failures: list[str] = []
    if binding_failures: failures.append("scenario_binding_failures")
    if len(bindings) != STAGE_A_SCENARIOS: failures.append("bound_scenario_count")
    if len(resource_audit) != 54: failures.append("resource_binding_count")
    if any(r["bound_scenarios"] != 822 for r in stratum_audit): failures.append("stratum_binding_count")

    smoke_rows: list[dict[str, Any]] = []
    battle_rows: list[dict[str, Any]] = []
    turn_telemetry_count = 0
    turn_sample_rows: list[dict[str, Any]] = []
    first_turn_row: dict[str, Any] | None = None
    turn_schema_consistency_pass = 0
    equivalence_rows: list[dict[str, Any]] = []
    execution_bindings = bindings[batch_start:batch_end]
    expected_smoke = len(execution_bindings)
    full_execution = batch_start == 0 and batch_end == len(bindings)
    if mode == "smoke" and not failures:
        if full_execution:
            equivalence_rows = _instrumentation_equivalence_rows(matrices, bindings, int(doc["masterSeed"]))
            _write_csv(outdir / "instrumentation_equivalence.csv", equivalence_rows)
            if not equivalence_rows or any(not int(r["result_identical"]) or r["error_without"] or r["error_with"] for r in equivalence_rows):
                failures.append("instrumentation_changes_combat")
        if failures:
            # Fail closed before the 8,220-case smoke if observational equivalence fails.
            pass
        if not failures:
            smoke_rows, battle_rows, turn_telemetry_count, turn_sample_rows, first_turn_row, turn_schema_consistency_pass = _execute_smoke_parallel(
                repo, doc["matrix"], ensemble_rows, tl_rows, execution_bindings, int(doc["masterSeed"]), jobs
            )
        _write_csv(outdir / "stage_a_smoke_results.csv", smoke_rows)
        _write_csv(outdir / "turn_tp_telemetry_sample.csv", turn_sample_rows)
        _write_csv(outdir / "battle_telemetry.csv", battle_rows)
        if len(smoke_rows) != expected_smoke: failures.append("smoke_result_count")
        if any(r["error"] for r in smoke_rows): failures.append("smoke_execution_errors")
        if turn_telemetry_count <= 0 or first_turn_row is None: failures.append("turn_telemetry_empty")
        if any(not int(r["telemetry_row_coverage_pass"]) for r in smoke_rows): failures.append("turn_telemetry_coverage")
        if turn_schema_consistency_pass != expected_smoke: failures.append("turn_telemetry_schema_consistency")
        if len(battle_rows) != 2 * expected_smoke: failures.append("battle_telemetry_count")
        failures.extend(_validate_contract_rows(manifest, turn_contract, ([first_turn_row] if first_turn_row else []), battle_rows))

    after_hash = _sha(source_matrix)
    if before_hash != after_hash: failures.append("source_matrix_modified")
    # R1 and R5 intentionally differ only in the abstract AUX demand proxy at this
    # integration stage. We retain both IDs but never invent unimplemented TP demand.
    aux_proxy_note = "Moderate/ModerateHighDemand remain explicit provenance axes; abstract active-TP proxy is not injected into combat."
    summary = {
        "schemaVersion": RESULT_SCHEMA, "checkpoint": 140, "baseCheckpoint": 139,
        "passed": not failures, "failedGates": failures, "mode": mode,
        "researchDamageModel": "def-res-v1", "sourceMatrixSha256Before": before_hash, "sourceMatrixSha256After": after_hash,
        "sourceMatrixUnmodified": before_hash == after_hash, "stageAScenarios": len(manifest), "boundScenarios": len(bindings),
        "integrationSmokeTrials": len(smoke_rows), "smokeErrors": sum(bool(r["error"]) for r in smoke_rows),
        "turnTelemetryRowsObserved": int(turn_telemetry_count), "turnTelemetryRowsPersistedSample": len(turn_sample_rows), "turnTelemetrySchemaConsistencyPass": int(turn_schema_consistency_pass), "turnTelemetryPersistence": "deterministic_first_final_first_conflict_per_side", "battleTelemetryRows": len(battle_rows), "instrumentationEquivalenceCases": len(equivalence_rows), "instrumentationEquivalencePass": sum(int(r["result_identical"]) for r in equivalence_rows), "turnTelemetryCoveragePass": sum(int(r.get("telemetry_row_coverage_pass",0)) for r in smoke_rows), "resourceEnvironmentCount": len(matrices), "scenarioStrataCount": len(stratum_audit),
        "batchStart": batch_start, "batchEnd": batch_end, "batchScenarioCount": expected_smoke, "fullSmokeInThisProcess": full_execution,
        "stageAExecutionReady": bool(mode == "smoke" and full_execution and not failures), "smokeJobs": int(jobs), "substantiveCombatTrials": 0, "promotionAllowed": False,
        "auxProxyExecutionBoundary": aux_proxy_note,
        "interpretation": "CP140 is integration/execution evidence only. The 8,220 one-trial smoke is never combat-balance evidence.",
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return summary


def merge_integration_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    """Merge independently executed CP140 smoke batches into the authoritative Stage-A smoke.

    Batches are independent Python processes in the native wrapper.  The merge verifies
    exact contiguous manifest coverage and all per-batch gates before declaring Stage A
    execution-ready.  It does not execute substantive balance trials.
    """
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["study-validation:" + ",".join(errors)]}
    outdir.mkdir(parents=True, exist_ok=True)
    source_matrix = repo / doc["matrix"]
    before_hash = _sha(source_matrix)
    manifest = _read_csv(repo / doc["stageAExperimentManifest"])
    telemetry_contract = load_json(repo / doc["telemetryContract"])

    # Recreate the complete binding/resource/stratum audits once in the merged result.
    plan_summary = run_integration(repo, study_path, outdir, mode="plan", jobs=1)
    failures: list[str] = []
    if not plan_summary.get("passed"):
        failures.append("merged-plan-validation")

    batch_records: list[tuple[int, int, Path, dict[str, Any]]] = []
    for child in sorted(batch_root.iterdir() if batch_root.exists() else []):
        if not child.is_dir() or not child.name.startswith("batch_"):
            continue
        sp = child / "summary.json"
        if not sp.exists():
            continue
        raw = json.loads(sp.read_text(encoding="utf-8-sig"))
        analysis = raw.get("analysis", raw)
        start = int(analysis.get("batchStart", -1)); end = int(analysis.get("batchEnd", -1))
        batch_records.append((start, end, child, analysis))
    batch_records.sort(key=lambda x: x[0])
    if not batch_records:
        failures.append("no-smoke-batches")

    expected_start = 0
    smoke_rows: list[dict[str, Any]] = []
    battle_rows: list[dict[str, Any]] = []
    turn_samples: list[dict[str, Any]] = []
    batch_audit: list[dict[str, Any]] = []
    turn_observed = 0
    schema_pass = 0
    for start, end, child, analysis in batch_records:
        batch_failures: list[str] = []
        if start != expected_start or end <= start or end > len(manifest):
            batch_failures.append("range")
        if not bool(analysis.get("passed", False)) or list(analysis.get("failedGates", [])):
            batch_failures.append("batch-gates")
        expected_ids = [r["scenario_id"] for r in manifest[max(0, start):max(0, end)]]
        try:
            sr = _read_csv(child / "stage_a_smoke_results.csv")
            br = _read_csv(child / "battle_telemetry.csv")
            tr = _read_csv(child / "turn_tp_telemetry_sample.csv")
        except Exception as exc:
            batch_failures.append(f"read:{type(exc).__name__}")
            sr=[]; br=[]; tr=[]
        if [r.get("scenario_id", "") for r in sr] != expected_ids:
            batch_failures.append("scenario-order")
        if len(br) != 2 * len(expected_ids):
            batch_failures.append("battle-count")
        if any(r.get("error") for r in sr):
            batch_failures.append("smoke-errors")
        if any(int(r.get("telemetry_row_coverage_pass", 0)) != 1 for r in sr):
            batch_failures.append("turn-coverage")
        batch_audit.append({
            "batch_dir": child.name, "start": start, "end": end, "expected_scenarios": max(0, end-start),
            "smoke_rows": len(sr), "battle_rows": len(br), "turn_sample_rows": len(tr),
            "turn_rows_observed": int(analysis.get("turnTelemetryRowsObserved", 0)),
            "schema_consistency_pass": int(analysis.get("turnTelemetrySchemaConsistencyPass", 0)),
            "status": "PASS" if not batch_failures else "FAIL", "failures": ";".join(batch_failures),
        })
        if batch_failures:
            failures.append("batch:" + child.name + ":" + ",".join(batch_failures))
        smoke_rows.extend(sr); battle_rows.extend(br); turn_samples.extend(tr)
        turn_observed += int(analysis.get("turnTelemetryRowsObserved", 0))
        schema_pass += int(analysis.get("turnTelemetrySchemaConsistencyPass", 0))
        expected_start = end
    if expected_start != len(manifest): failures.append("batch-coverage-incomplete")
    if len(smoke_rows) != STAGE_A_SCENARIOS: failures.append("merged-smoke-count")
    if len(battle_rows) != 2 * STAGE_A_SCENARIOS: failures.append("merged-battle-count")
    if schema_pass != STAGE_A_SCENARIOS: failures.append("merged-turn-schema-consistency")

    required_turn = {x["field"] for x in telemetry_contract["turn_fields"]}
    required_battle = {x["field"] for x in telemetry_contract["battle_fields"]}
    if not turn_samples or not required_turn.issubset(turn_samples[0].keys()): failures.append("merged-turn-contract")
    if not battle_rows or not required_battle.issubset(battle_rows[0].keys()): failures.append("merged-battle-contract")

    # Strict observational-equivalence replay is performed once at merge time.
    ensemble_rows, tl_rows = _resource_rows(repo, doc)
    matrices = {eid: build_resource_matrix(repo, doc["matrix"], eid, ensemble_rows, tl_rows) for eid in sorted({r["ensemble_id"] for r in ensemble_rows})}
    bindings = [bind_scenario(matrices[r["resource_ensemble_id"]], r) for r in manifest]
    equivalence_rows = _instrumentation_equivalence_rows(matrices, bindings, int(doc["masterSeed"]))
    if len(equivalence_rows) != 12 or any(not int(r["result_identical"]) or r["error_without"] or r["error_with"] for r in equivalence_rows):
        failures.append("instrumentation-changes-combat")

    # Integration-only conflict coverage. These counts are never balance evidence.
    conflict_groups: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in smoke_rows:
        key = (int(row["tl"]), row["resource_ensemble_id"], row["scenario_stratum"])
        g = conflict_groups.setdefault(key, {"tl":key[0],"resource_ensemble_id":key[1],"scenario_stratum":key[2],"scenarios":0,"scenarios_with_conflict":0,"tp_conflict_turns":0,"tp_denied_total":0})
        g["scenarios"] += 1
        c = int(row["tp_conflict_turns_a"]) + int(row["tp_conflict_turns_b"])
        d = int(row["tp_denied_a"]) + int(row["tp_denied_b"])
        g["scenarios_with_conflict"] += int(c > 0); g["tp_conflict_turns"] += c; g["tp_denied_total"] += d
    conflict_rows = [conflict_groups[k] for k in sorted(conflict_groups)]
    total_conflicts = sum(int(r["tp_conflict_turns"]) for r in conflict_rows)
    power_crisis_conflicts = sum(int(r["tp_conflict_turns"]) for r in conflict_rows if r["scenario_stratum"] == "POWER_CRISIS")
    if total_conflicts <= 0: failures.append("tp-conflict-telemetry-unexercised")
    if power_crisis_conflicts <= 0: failures.append("power-crisis-no-tp-conflicts")

    # Explicitly record executable equivalence classes among resource envelopes.  At
    # CP140 R1/R5 remain distinct provenance labels but share mechanics because the
    # abstract ModerateHighDemand AUX proxy is not injected as fake TP demand.
    sig_rows: list[dict[str, Any]] = []
    signatures: dict[str, str] = {}
    for er in ensemble_rows:
        eid = er["ensemble_id"]; m = matrices[eid]
        payload=[]
        for tl in range(1,10):
            payload.append({
                "tl":tl,"reactor":m.p("reactor",tl),"kinetic":m.p("kinetic_main",tl),
                "energy":m.p("energy_main",tl),"missile":m.p("missile_delivery",tl),
                "stl_space":m.p("stl",tl)["space"],"ftl_space":m.p("ftl",tl)["space"],
            })
        sig=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        signatures[eid]=sig
    for eid in sorted(signatures):
        peers=[x for x in sorted(signatures) if signatures[x]==signatures[eid]]
        er=next(r for r in ensemble_rows if r["ensemble_id"]==eid)
        sig_rows.append({"ensemble_id":eid,"execution_signature_sha256":signatures[eid],"execution_equivalence_class":";".join(peers),"aux_proxy_profile":er["aux_proxy_profile"],"aux_proxy_execution":"metadata_only_no_fake_tp_demand"})

    _write_csv(outdir / "batch_merge_audit.csv", batch_audit)
    _write_csv(outdir / "stage_a_smoke_results.csv", smoke_rows)
    _write_csv(outdir / "turn_tp_telemetry_sample.csv", turn_samples)
    _write_csv(outdir / "battle_telemetry.csv", battle_rows)
    _write_csv(outdir / "instrumentation_equivalence.csv", equivalence_rows)
    _write_csv(outdir / "tp_conflict_coverage.csv", conflict_rows)
    _write_csv(outdir / "resource_execution_equivalence.csv", sig_rows)

    after_hash = _sha(source_matrix)
    if before_hash != after_hash: failures.append("source-matrix-modified")
    summary = {
        "schemaVersion": RESULT_SCHEMA, "checkpoint": 140, "baseCheckpoint": 139,
        "passed": not failures, "failedGates": failures, "mode": "merged-smoke",
        "researchDamageModel": "def-res-v1", "sourceMatrixSha256Before": before_hash,
        "sourceMatrixSha256After": after_hash, "sourceMatrixUnmodified": before_hash == after_hash,
        "stageAScenarios": len(manifest), "boundScenarios": int(plan_summary.get("boundScenarios", 0)),
        "integrationSmokeTrials": len(smoke_rows), "smokeErrors": sum(bool(r.get("error")) for r in smoke_rows),
        "batchCount": len(batch_records), "isolatedProcessBatching": True,
        "turnTelemetryRowsObserved": turn_observed, "turnTelemetryRowsPersistedSample": len(turn_samples),
        "turnTelemetrySchemaConsistencyPass": schema_pass,
        "turnTelemetryPersistence": "deterministic_first_final_first_conflict_per_side",
        "battleTelemetryRows": len(battle_rows),
        "instrumentationEquivalenceCases": len(equivalence_rows),
        "instrumentationEquivalencePass": sum(int(r["result_identical"]) for r in equivalence_rows),
        "tpConflictTurnsObserved": total_conflicts, "powerCrisisTpConflictTurnsObserved": power_crisis_conflicts,
        "resourceEnvironmentCount": len(matrices), "scenarioStrataCount": 10,
        "stageAExecutionReady": not failures, "substantiveCombatTrials": 0, "promotionAllowed": False,
        "auxProxyExecutionBoundary": "Moderate/ModerateHighDemand remain provenance axes; abstract active TP is not injected. Execution-equivalent envelopes are reported explicitly.",
        "interpretation": "CP140 is integration/execution evidence only. The 8,220 one-trial smoke is never combat-balance evidence.",
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return summary
