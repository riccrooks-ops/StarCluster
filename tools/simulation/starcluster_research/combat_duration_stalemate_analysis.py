from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .stage_a_integration_analysis import (
    STAGE_A_SCENARIOS,
    _read_csv,
    _resource_rows,
    bind_scenario,
    build_resource_matrix,
)
from .study import canonicalize_relocated_references, load_json

RESULT_SCHEMA = "star-cluster-cp141-combat-duration-stalemate-result-v0.1"
HARD_TURN_SENTINEL = 60
LONG_RESOLVED_TURN = 25
RECENT_WINDOW = 10
RECOVERY_DOMINANCE_FRACTION = 0.75


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
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-cp141-combat-duration-stalemate-study-v0.1": errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 141: errors.append("checkpoint")
    if int(doc.get("baseCheckpoint", 0)) != 140: errors.append("baseCheckpoint")
    if int(doc.get("expectedStageAScenarios", 0)) != STAGE_A_SCENARIOS: errors.append("expectedStageAScenarios")
    if int(doc.get("hardTurnSentinel", 0)) != HARD_TURN_SENTINEL: errors.append("hardTurnSentinel")
    if int(doc.get("longResolvedTurn", 0)) != LONG_RESOLVED_TURN: errors.append("longResolvedTurn")
    if bool(doc.get("extendTurnCap", True)): errors.append("extendTurnCap")
    if int(doc.get("substantiveCombatTrials", -1)) != 0: errors.append("substantiveCombatTrials")
    if bool(doc.get("automaticPromotion")): errors.append("automaticPromotion")
    return errors


_CP141_WORKER_MATRICES = None


def _worker_init(repo_text: str, matrix_relative: str, ensemble_rows: list[dict[str, str]], tl_rows: list[dict[str, str]]) -> None:
    global _CP141_WORKER_MATRICES
    repo = Path(repo_text)
    ids = sorted({r["ensemble_id"] for r in ensemble_rows})
    _CP141_WORKER_MATRICES = {
        eid: build_resource_matrix(repo, matrix_relative, eid, ensemble_rows, tl_rows)
        for eid in ids
    }


def _pair_turns(turn_rows: list[dict[str, Any]]) -> dict[int, dict[str, dict[str, Any]]]:
    paired: dict[int, dict[str, dict[str, Any]]] = {}
    for row in turn_rows:
        paired.setdefault(int(row["turn"]), {})[str(row["side_id"])] = row
    return paired


def _gross_damage(result) -> float:
    a, b = result.side_a, result.side_b
    return float(
        a.shield_absorbed + a.armor_integrity_damage + a.hull_damage
        + b.shield_absorbed + b.armor_integrity_damage + b.hull_damage
    )


def _recovery_total(result) -> tuple[float, float, float, float, float]:
    a, b = result.side_a, result.side_b
    shield_base = float(a.shield_base_restored + b.shield_base_restored)
    shield_tactical = float(a.shield_tactical_restored + b.shield_tactical_restored)
    armor = float(a.armor_regen_restored + b.armor_regen_restored)
    hull = float(a.damage_control_hull_restored + b.damage_control_hull_restored)
    return shield_base + shield_tactical + armor + hull, shield_base, shield_tactical, armor, hull


def _cap_diagnostic(result, turn_rows: list[dict[str, Any]]) -> dict[str, Any]:
    paired = _pair_turns(turn_rows)
    final_turn = int(result.turns)
    window_start = max(1, final_turn - RECENT_WINDOW + 1)
    start = paired.get(window_start, {})
    final = paired.get(final_turn, {})
    recent = [r for r in turn_rows if int(r["turn"]) >= window_start]

    def structural(rows: dict[str, dict[str, Any]]) -> float:
        if "A" not in rows or "B" not in rows:
            return 0.0
        return sum(float(rows[s]["hull_remaining"]) + float(rows[s]["armor_remaining"]) for s in ("A", "B"))

    def shield(rows: dict[str, dict[str, Any]]) -> float:
        if "A" not in rows or "B" not in rows:
            return 0.0
        return sum(float(rows[s]["shield_remaining"]) for s in ("A", "B"))

    structural_progress = structural(start) - structural(final)
    shield_progress = shield(start) - shield(final)
    weapon_desired = sum("weapon_" in str(r.get("chosen_action_summary", "")) for r in recent)
    firm_rows = sum(str(r.get("track_quality", "")) == "Firm" for r in recent)
    conflict_rows = sum(int(r.get("tp_conflict_flag", 0)) for r in recent)
    denied_tp = sum(int(r.get("tp_denied_total", 0)) for r in recent)
    ranges = [int(r["range_hex"]) for r in recent]

    attacks = int(result.side_a.direct_shots + result.side_a.missile_launches + result.side_b.direct_shots + result.side_b.missile_launches)
    hits = int(result.side_a.direct_hits + result.side_a.missile_hits + result.side_b.direct_hits + result.side_b.missile_hits)
    packets = int(result.side_a.def_res_packets + result.side_b.def_res_packets)
    gross = _gross_damage(result)
    recovery, shield_base, shield_tactical, armor_recovery, hull_recovery = _recovery_total(result)
    recovery_fraction = (recovery / gross) if gross > 0 else 0.0

    # This is a diagnostic partition, not an automatic gameplay termination rule.
    # The priority is deliberately transparent and conservative. Only mutual finite
    # offensive exhaustion terminates early in the canonical kernel.
    if attacks == 0:
        signal = "NO_OFFENSIVE_ACTION"
    elif packets == 0:
        signal = "OFFENSE_WITHOUT_DAMAGE_CONNECTION"
    elif weapon_desired == 0:
        signal = "NO_RECENT_WEAPON_DEMAND"
    elif structural_progress > 0:
        signal = "ACTIVE_ATTRITION_AT_CAP"
    elif gross > 0 and recovery_fraction >= RECOVERY_DOMINANCE_FRACTION:
        signal = "DEFENSIVE_RECOVERY_LOOP"
    elif firm_rows == 0:
        signal = "TRACK_DEADLOCK"
    elif conflict_rows >= RECENT_WINDOW:
        signal = "TP_PRESSURE_DEADLOCK"
    else:
        signal = "NO_NET_STRUCTURAL_PROGRESS"

    final_a = final.get("A", {})
    final_b = final.get("B", {})
    return {
        "dominant_cap_signal": signal,
        "recent_window_turns": RECENT_WINDOW,
        "last_damage_state_change_turn": int(result.last_damage_state_change_turn),
        "turns_since_last_damage_state_change": final_turn - int(result.last_damage_state_change_turn or 0),
        "attacks_total": attacks,
        "hits_total": hits,
        "def_res_packets_total": packets,
        "gross_damage_total": gross,
        "recovery_total": recovery,
        "recovery_fraction_of_gross_damage": recovery_fraction,
        "shield_base_restored": shield_base,
        "shield_tactical_restored": shield_tactical,
        "armor_regen_restored": armor_recovery,
        "hull_restored": hull_recovery,
        "structural_progress_last10": structural_progress,
        "shield_progress_last10": shield_progress,
        "weapon_desired_rows_last10": weapon_desired,
        "firm_track_rows_last10": firm_rows,
        "tp_conflict_rows_last10": conflict_rows,
        "tp_denied_last10": denied_tp,
        "range_min_last10": min(ranges) if ranges else "",
        "range_max_last10": max(ranges) if ranges else "",
        "final_range": int(result.final_range),
        "final_hull_a": result.hull_a, "final_hull_b": result.hull_b,
        "final_armor_a": result.armor_a, "final_armor_b": result.armor_b,
        "final_shield_a": result.shield_a, "final_shield_b": result.shield_b,
        "final_weapon_ammo_a": (final_a.get("kinetic_ammo_remaining", "") if final_a.get("kinetic_ammo_remaining", "") != "" else final_a.get("missile_flights_remaining", "")),
        "final_weapon_ammo_b": (final_b.get("kinetic_ammo_remaining", "") if final_b.get("kinetic_ammo_remaining", "") != "" else final_b.get("missile_flights_remaining", "")),
        "final_missiles_in_flight": int(result.final_missiles_in_flight),
    }


def _execute_task(args: tuple[int, dict[str, str], Any, int]) -> dict[str, Any]:
    idx, source, bound, master_seed = args
    if _CP141_WORKER_MATRICES is None:
        raise RuntimeError("CP141 worker matrices are not initialized")
    matrix = _CP141_WORKER_MATRICES[source["resource_ensemble_id"]]
    variant = replace(bound.variant, max_turns=HARD_TURN_SENTINEL)
    turn_rows: list[dict[str, Any]] = []
    ctx = {
        "scenario_id": source["scenario_id"], "resource_ensemble_id": source["resource_ensemble_id"],
        "weapon_a": source["side_a_weapon"], "weapon_b": source["side_b_weapon"],
    }
    result = run_trial_full_map(matrix, variant, master_seed, 0, turn_telemetry_sink=turn_rows, telemetry_context=ctx)
    resolved = result.winner in ("A", "B", "Draw") and not result.unresolved and not result.error
    long_resolved = bool(resolved and result.turns >= LONG_RESOLVED_TURN)
    duration_class = (
        "ERROR" if result.error else
        "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION" if result.termination_cause == "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION" else
        "TURN_CAP_SENTINEL" if result.termination_cause == "TURN_CAP_SENTINEL" else
        "RESOLVED_LONG_GE25" if long_resolved else
        "RESOLVED_UNDER25"
    )
    row = {
        "scenario_index": idx, "scenario_id": source["scenario_id"], "tl": int(source["tl"]),
        "side_a_weapon": source["side_a_weapon"], "side_b_weapon": source["side_b_weapon"],
        "resource_ensemble_id": source["resource_ensemble_id"], "scenario_stratum": source["scenario_stratum"],
        "winner": result.winner, "unresolved": int(result.unresolved), "error": result.error,
        "turns": int(result.turns), "hard_turn_sentinel": HARD_TURN_SENTINEL,
        "termination_cause": result.termination_cause, "duration_class": duration_class,
        "resolved_flag": int(resolved), "resolved_under25_flag": int(resolved and result.turns < LONG_RESOLVED_TURN),
        "resolved_ge25_flag": int(long_resolved), "resolved_by10_flag": int(resolved and result.turns <= 10),
        "resolved_by15_flag": int(resolved and result.turns <= 15), "resolved_by20_flag": int(resolved and result.turns <= 20),
        "turn_cap_flag": int(result.termination_cause == "TURN_CAP_SENTINEL"),
        "safe_stalemate_flag": int(result.termination_cause == "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION"),
        "turn_telemetry_rows": len(turn_rows), "expected_turn_telemetry_rows": 2 * int(result.turns),
        "turn_telemetry_coverage_pass": int(len(turn_rows) == 2 * int(result.turns)),
    }
    diagnostic = None
    if result.termination_cause == "TURN_CAP_SENTINEL":
        diagnostic = {k: row[k] for k in ("scenario_index","scenario_id","tl","side_a_weapon","side_b_weapon","resource_ensemble_id","scenario_stratum","turns","termination_cause")}
        diagnostic.update(_cap_diagnostic(result, turn_rows))
    return {"index": idx, "row": row, "diagnostic": diagnostic}


def _group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs: list[dict[str, Any]] = []
    group_specs = {
        "OVERALL": lambda r: "ALL",
        "TL": lambda r: f"TL{r['tl']}",
        "STRATUM": lambda r: r["scenario_stratum"],
        "WEAPON_PAIR": lambda r: f"{r['side_a_weapon']}->{r['side_b_weapon']}",
        "RESOURCE": lambda r: r["resource_ensemble_id"],
    }
    for group_type, key_fn in group_specs.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows: groups[key_fn(r)].append(r)
        for key in sorted(groups):
            g = groups[key]
            resolved = [r for r in g if int(r["resolved_flag"])]
            turns = sorted(int(r["turns"]) for r in resolved)
            def q(frac: float) -> float | str:
                if not turns: return ""
                pos = (len(turns) - 1) * frac; lo = int(pos); hi = min(len(turns)-1, lo+1); f = pos-lo
                return turns[lo]*(1-f)+turns[hi]*f
            outputs.append({
                "group_type": group_type, "group_key": key, "scenarios": len(g), "resolved": len(resolved),
                "safe_stalemates": sum(int(r["safe_stalemate_flag"]) for r in g),
                "turn_cap_sentinels": sum(int(r["turn_cap_flag"]) for r in g),
                "resolved_under25": sum(int(r["resolved_under25_flag"]) for r in g),
                "resolved_ge25": sum(int(r["resolved_ge25_flag"]) for r in g),
                "resolved_ge25_rate_of_resolved": (sum(int(r["resolved_ge25_flag"]) for r in g)/len(resolved)) if resolved else 0.0,
                "resolved_by10": sum(int(r["resolved_by10_flag"]) for r in g),
                "resolved_by15": sum(int(r["resolved_by15_flag"]) for r in g),
                "resolved_by20": sum(int(r["resolved_by20_flag"]) for r in g),
                "median_resolved_turns": q(0.5), "p75_resolved_turns": q(0.75), "p90_resolved_turns": q(0.9), "p95_resolved_turns": q(0.95),
            })
    return outputs


def run_batch(repo: Path, study_path: Path, outdir: Path, jobs: int = 24, batch_start: int = 0, batch_end: int | None = None) -> dict[str, Any]:
    doc = load_json(study_path); errors = validate_study(doc)
    if errors: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = _read_csv(repo / doc["stageAExperimentManifest"])
    ensemble_rows, tl_rows = _resource_rows(repo, doc)
    source_matrix = repo / doc["matrix"]; before_hash = _sha(source_matrix)
    matrices = {eid: build_resource_matrix(repo, doc["matrix"], eid, ensemble_rows, tl_rows) for eid in sorted({r["ensemble_id"] for r in ensemble_rows})}
    bindings = [bind_scenario(matrices[r["resource_ensemble_id"]], r) for r in manifest]
    start=max(0,int(batch_start)); end=len(bindings) if batch_end is None else min(len(bindings),int(batch_end))
    if start>=end: return {"schemaVersion": RESULT_SCHEMA,"passed":False,"failedGates":["invalid-batch-range"]}
    tasks=[(i,manifest[i],bindings[i],int(doc["masterSeed"])) for i in range(start,end)]
    jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc["matrix"],ensemble_rows,tl_rows); completed=[_execute_task(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],ensemble_rows,tl_rows)) as ex:
            completed=list(ex.map(_execute_task,tasks,chunksize=8))
    completed.sort(key=lambda x:x["index"])
    rows=[x["row"] for x in completed]; diags=[x["diagnostic"] for x in completed if x["diagnostic"] is not None]
    _write_csv(outdir/"duration_smoke_results.csv",rows); _write_csv(outdir/"turn_cap_diagnostics.csv",diags)
    after_hash=_sha(source_matrix)
    failures=[]
    if len(rows)!=end-start: failures.append("scenario-count")
    if any(r["error"] for r in rows): failures.append("execution-errors")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in rows): failures.append("turn-telemetry-coverage")
    if any(int(r["turns"])>HARD_TURN_SENTINEL for r in rows): failures.append("turn-sentinel-exceeded")
    if before_hash!=after_hash: failures.append("source-matrix-modified")
    summary={
        "schemaVersion":RESULT_SCHEMA,"checkpoint":141,"baseCheckpoint":140,"passed":not failures,"failedGates":failures,
        "batchStart":start,"batchEnd":end,"scenarios":len(rows),"executionErrors":sum(bool(r["error"]) for r in rows),
        "resolved":sum(int(r["resolved_flag"]) for r in rows),"resolvedGe25":sum(int(r["resolved_ge25_flag"]) for r in rows),
        "safeStalemates":sum(int(r["safe_stalemate_flag"]) for r in rows),"turnCapSentinels":sum(int(r["turn_cap_flag"]) for r in rows),
        "hardTurnSentinel":HARD_TURN_SENTINEL,"longResolvedTurn":LONG_RESOLVED_TURN,"sourceMatrixUnmodified":before_hash==after_hash,
        "substantiveCombatTrials":0,"promotionAllowed":False,
        "interpretation":"Duration/stalemate semantics and one-trial execution diagnostics only; never balance evidence.",
    }
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def merge_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    doc=load_json(study_path); errors=validate_study(doc)
    if errors:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True)
    manifest=_read_csv(repo/doc["stageAExperimentManifest"]); source_matrix=repo/doc["matrix"]; before_hash=_sha(source_matrix)
    rows=[]; diags=[]; audits=[]; expected=0
    for d in sorted([p for p in batch_root.iterdir() if p.is_dir()]):
        summary_path=d/"summary.json"; result_path=d/"duration_smoke_results.csv"
        if not summary_path.exists() or not result_path.exists(): continue
        payload=json.loads(summary_path.read_text()); analysis=payload.get("analysis",payload)
        start=int(analysis["batchStart"]); end=int(analysis["batchEnd"])
        batch_rows=_read_csv(result_path); batch_diags=_read_csv(d/"turn_cap_diagnostics.csv") if (d/"turn_cap_diagnostics.csv").exists() and (d/"turn_cap_diagnostics.csv").stat().st_size else []
        pass_batch=bool(analysis.get("passed",payload.get("passed",False))) and start==expected and len(batch_rows)==end-start
        expected_ids=[r["scenario_id"] for r in manifest[start:end]]; actual_ids=[r["scenario_id"] for r in batch_rows]
        ids_match=expected_ids==actual_ids; pass_batch=pass_batch and ids_match
        audits.append({"batch":d.name,"start":start,"end":end,"scenarios":len(batch_rows),"ids_match":int(ids_match),"passed":int(pass_batch)})
        if not pass_batch: continue
        rows.extend(batch_rows); diags.extend(batch_diags); expected=end
    failures=[]
    if expected!=len(manifest): failures.append("batch-coverage-incomplete")
    if len(rows)!=STAGE_A_SCENARIOS: failures.append("merged-scenario-count")
    if any(r["error"] for r in rows): failures.append("merged-execution-errors")
    if any(int(r["turns"])>HARD_TURN_SENTINEL for r in rows): failures.append("merged-turn-sentinel-exceeded")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in rows): failures.append("merged-turn-telemetry-coverage")
    after_hash=_sha(source_matrix)
    if before_hash!=after_hash: failures.append("source-matrix-modified")
    _write_csv(outdir/"batch_merge_audit.csv",audits); _write_csv(outdir/"duration_smoke_results.csv",rows); _write_csv(outdir/"turn_cap_diagnostics.csv",diags)
    group_rows=_group_rows(rows); _write_csv(outdir/"duration_group_summary.csv",group_rows)
    cause_counts=Counter(r["termination_cause"] for r in rows); _write_csv(outdir/"termination_cause_summary.csv",[{"termination_cause":k,"scenarios":v} for k,v in sorted(cause_counts.items())])
    signal_counts=Counter(r["dominant_cap_signal"] for r in diags); _write_csv(outdir/"turn_cap_signal_summary.csv",[{"dominant_cap_signal":k,"scenarios":v} for k,v in sorted(signal_counts.items())])
    resolved=[r for r in rows if int(r["resolved_flag"])]
    long_resolved=sum(int(r["resolved_ge25_flag"]) for r in rows); caps=sum(int(r["turn_cap_flag"]) for r in rows); stalemates=sum(int(r["safe_stalemate_flag"]) for r in rows)
    gameplay_concern=long_resolved+caps
    overall=next((r for r in group_rows if r["group_type"]=="OVERALL"),{})
    summary={
        "schemaVersion":RESULT_SCHEMA,"checkpoint":141,"baseCheckpoint":140,"passed":not failures,"failedGates":failures,
        "stageAScenarios":len(rows),"resolved":len(resolved),"resolvedUnder25":sum(int(r["resolved_under25_flag"]) for r in rows),
        "resolvedGe25":long_resolved,"resolvedGe25RateOfResolved":(long_resolved/len(resolved)) if resolved else 0.0,
        "safeStalemates":stalemates,"turnCapSentinels":caps,"gameplayDurationConcernScenarios":gameplay_concern,
        "gameplayDurationConcernRate":(gameplay_concern/len(rows)) if rows else 0.0,
        "medianResolvedTurns":overall.get("median_resolved_turns",""),"p90ResolvedTurns":overall.get("p90_resolved_turns",""),"p95ResolvedTurns":overall.get("p95_resolved_turns",""),
        "hardTurnSentinel":HARD_TURN_SENTINEL,"longResolvedTurn":LONG_RESOLVED_TURN,"turnCapDiagnosticRows":len(diags),
        "batchCount":len(audits),"isolatedProcessBatching":True,
        "sourceMatrixUnmodified":before_hash==after_hash,"stageASubstantiveMeasurementReady":not failures,
        "substantiveCombatTrials":0,"promotionAllowed":False,
        "interpretation":"CP141 closes duration/stalemate measurement semantics. Long/cap frequencies from one-trial smoke are diagnostics, not final balance rates.",
    }
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
