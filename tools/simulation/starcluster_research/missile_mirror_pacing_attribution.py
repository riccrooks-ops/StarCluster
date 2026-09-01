from __future__ import annotations

import csv
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from .study import canonicalize_relocated_references, load_json

RESULT_SCHEMA = "star-cluster-cp143-missile-mirror-pacing-attribution-result-v0.1"
EXPECTED_MISSILE_MIRROR_SCENARIOS = 1980
HARD_TURN_SENTINEL = 60
LONG_RESOLVED_TURN = 25

_WORKER_MATRICES: dict[str, Any] | None = None


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


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-cp143-missile-mirror-pacing-attribution-study-v0.1": errors.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 143: errors.append("checkpoint")
    if int(doc.get("baseCheckpoint", 0)) != 142: errors.append("baseCheckpoint")
    if int(doc.get("expectedMissileMirrorScenarios", 0)) != EXPECTED_MISSILE_MIRROR_SCENARIOS: errors.append("expectedMissileMirrorScenarios")
    if int(doc.get("hardTurnSentinel", 0)) != HARD_TURN_SENTINEL: errors.append("hardTurnSentinel")
    if int(doc.get("longResolvedTurn", 0)) != LONG_RESOLVED_TURN: errors.append("longResolvedTurn")
    if bool(doc.get("tuningAllowed", True)): errors.append("tuningAllowed")
    if bool(doc.get("automaticPromotion", True)): errors.append("automaticPromotion")
    if int(doc.get("substantiveCombatTrials", -1)) != 0: errors.append("substantiveCombatTrials")
    if doc.get("scope") != "missile-mirror-attribution-only": errors.append("scope")
    if not doc.get("pairedBaselineReference"): errors.append("pairedBaselineReference")
    if not doc.get("pairedBaselineReferenceSha256"): errors.append("pairedBaselineReferenceSha256")
    return errors


def _missile_rows(repo: Path, doc: dict[str, Any]) -> list[dict[str, str]]:
    rows = _read_csv(repo / doc["stageAExperimentManifest"])
    return [r for r in rows if r["side_a_weapon"].startswith("M_") and r["side_b_weapon"].startswith("M_")]


def _worker_init(repo_text: str, matrix_relative: str, ensemble_rows: list[dict[str, str]], tl_rows: list[dict[str, str]]) -> None:
    global _WORKER_MATRICES
    repo = Path(repo_text)
    eids = sorted({r["ensemble_id"] for r in ensemble_rows})
    _WORKER_MATRICES = {eid: build_deep_resource_matrix(repo, matrix_relative, eid, ensemble_rows, tl_rows) for eid in eids}


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _median(values: list[float]) -> float:
    return statistics.median(values) if values else 0.0


def _gaps(turns: list[int]) -> list[int]:
    uniq = sorted(set(turns))
    return [b - a for a, b in zip(uniq, uniq[1:])]


def _side_metrics(events: list[dict[str, Any]], side: str, turns: int) -> dict[str, Any]:
    decisions = [e for e in events if e.get("event") == "missile_launch_decision" and e.get("side") == side]
    launches = [e for e in events if e.get("event") == "missile_launch" and e.get("side") == side]
    terminals = [e for e in events if e.get("event") == "missile_terminal" and e.get("owner") == side]
    exhausted = [e for e in events if e.get("event") == "missile_range_exhausted" and e.get("owner") == side]
    inventory = [e for e in events if e.get("event") == "missile_inventory"]
    states = [e for e in events if e.get("event") == "missile_turn_state" and e.get("side") == side]
    moves = [e for e in events if e.get("event") == "movement" and e.get("side") == side]
    launch_turns = [int(e["turn"]) for e in launches]
    terminal_turns = [int(e["turn"]) for e in terminals]
    hit_turns = [int(e["turn"]) for e in terminals if int(e.get("guidance_success", 0))]
    transit = [int(e.get("elapsed_turns", 0)) for e in terminals]
    terminal_pds_attempts = sum(int(e.get("pds_attempts", 0)) for e in terminals)
    terminal_intercepts = sum(int(e.get("pds_intercepted", 0)) for e in terminals)
    guidance_attempts = sum(int(e.get("guidance_attempted", 0)) for e in terminals)
    guidance_hits = sum(int(e.get("guidance_success", 0)) for e in terminals)
    decision_counts = Counter(str(e.get("decision", "")) for e in decisions)
    tp_denied_no_plan = sum(
        1 for e in decisions
        if e.get("decision") == "NO_WEAPON_PLAN" and int(e.get("desired_weapon_tp", 0)) > int(e.get("allocated_weapon_tp", 0))
    )
    no_firm_geometry = sum(1 for e in decisions if e.get("decision") == "NO_FIRM_TRACK" and e.get("track_no_ew") != "Firm")
    no_firm_ew = sum(1 for e in decisions if e.get("decision") == "NO_FIRM_TRACK" and e.get("track_no_ew") == "Firm" and int(e.get("ecm_downgrade", 0)))
    no_firm_other = max(0, decision_counts["NO_FIRM_TRACK"] - no_firm_geometry - no_firm_ew)
    effective_open = sum(1 for e in moves if e.get("reason_class") == "effective_range" and e.get("order") == "Open")
    track_close_close = sum(1 for e in moves if e.get("reason_class") == "track_close" and e.get("order") == "Close")
    track_close_open = sum(1 for e in moves if e.get("reason_class") == "track_close" and e.get("order") == "Open")
    effective_open_hexes = sum(int(e.get("movement_hexes", 0)) for e in moves if e.get("reason_class") == "effective_range" and e.get("order") == "Open")
    track_close_hexes = sum(int(e.get("movement_hexes", 0)) for e in moves if e.get("reason_class") == "track_close" and e.get("order") == "Close")
    inflight_key = "in_flight_a" if side == "A" else "in_flight_b"
    inflight = [int(e.get(inflight_key, 0)) for e in inventory]
    last_state = states[-1] if states else {}
    subflights = sum(int(e.get("subflights", 1)) for e in launches)
    return {
        f"first_launch_turn_{side.lower()}": min(launch_turns) if launch_turns else 0,
        f"first_terminal_turn_{side.lower()}": min(terminal_turns) if terminal_turns else 0,
        f"first_hit_turn_{side.lower()}": min(hit_turns) if hit_turns else 0,
        f"launches_{side.lower()}": len(launches),
        f"subflights_launched_{side.lower()}": subflights,
        f"terminal_arrivals_{side.lower()}": len(terminals),
        f"pds_attempts_against_{side.lower()}": terminal_pds_attempts,
        f"pds_intercepts_against_{side.lower()}": terminal_intercepts,
        f"guidance_attempts_{side.lower()}": guidance_attempts,
        f"guidance_hits_{side.lower()}": guidance_hits,
        f"range_exhaustions_{side.lower()}": len(exhausted),
        f"mean_terminal_transit_turns_{side.lower()}": _mean([float(x) for x in transit]),
        f"max_terminal_transit_turns_{side.lower()}": max(transit) if transit else 0,
        f"mean_launch_gap_turns_{side.lower()}": _mean([float(x) for x in _gaps(launch_turns)]),
        f"max_launch_gap_turns_{side.lower()}": max(_gaps(launch_turns)) if _gaps(launch_turns) else 0,
        f"mean_terminal_gap_turns_{side.lower()}": _mean([float(x) for x in _gaps(terminal_turns)]),
        f"max_terminal_gap_turns_{side.lower()}": max(_gaps(terminal_turns)) if _gaps(terminal_turns) else 0,
        f"inflight_turn_exposure_{side.lower()}": sum(inflight),
        f"peak_inflight_{side.lower()}": max(inflight) if inflight else 0,
        f"decision_turns_{side.lower()}": len(decisions),
        f"decision_launched_{side.lower()}": decision_counts["LAUNCHED"],
        f"decision_no_firm_track_{side.lower()}": decision_counts["NO_FIRM_TRACK"],
        f"decision_out_of_range_{side.lower()}": decision_counts["OUT_OF_RANGE"],
        f"decision_no_weapon_plan_{side.lower()}": decision_counts["NO_WEAPON_PLAN"],
        f"decision_ammo_exhausted_{side.lower()}": decision_counts["AMMO_EXHAUSTED"],
        f"decision_ready_no_launch_{side.lower()}": decision_counts["READY"],
        f"tp_denied_no_weapon_plan_turns_{side.lower()}": tp_denied_no_plan,
        f"no_firm_geometry_or_acquisition_turns_{side.lower()}": no_firm_geometry,
        f"no_firm_ew_downgrade_turns_{side.lower()}": no_firm_ew,
        f"no_firm_other_turns_{side.lower()}": no_firm_other,
        f"effective_range_open_turns_{side.lower()}": effective_open,
        f"track_close_close_turns_{side.lower()}": track_close_close,
        f"track_close_open_turns_{side.lower()}": track_close_open,
        f"effective_range_open_hexes_{side.lower()}": effective_open_hexes,
        f"track_close_close_hexes_{side.lower()}": track_close_hexes,
        f"final_shield_restored_total_{side.lower()}": int(last_state.get("shield_restored_total", 0) or 0),
        f"final_armor_restored_total_{side.lower()}": int(last_state.get("armor_restored_total", 0) or 0),
        f"final_hull_restored_total_{side.lower()}": int(last_state.get("hull_restored_total", 0) or 0),
        f"tp_conflict_turns_{side.lower()}": sum(int(e.get("tp_conflict_flag", 0)) for e in states),
        f"observed_turns_{side.lower()}": len(states),
        f"launch_turn_fraction_{side.lower()}": (decision_counts["LAUNCHED"] / max(1, turns)),
        f"no_firm_track_fraction_{side.lower()}": (decision_counts["NO_FIRM_TRACK"] / max(1, turns)),
        f"out_of_range_fraction_{side.lower()}": (decision_counts["OUT_OF_RANGE"] / max(1, turns)),
        f"no_weapon_plan_fraction_{side.lower()}": (decision_counts["NO_WEAPON_PLAN"] / max(1, turns)),
        f"ammo_exhausted_fraction_{side.lower()}": (decision_counts["AMMO_EXHAUSTED"] / max(1, turns)),
    }


def _dominant_signal(row: dict[str, Any]) -> str:
    if row["termination_cause"] == "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION": return "OFFENSIVE_EXHAUSTION"
    if not int(row["turn_cap_flag"]) and not int(row["resolved_ge25_flag"]): return "HEALTHY_UNDER25"
    turns = max(1, int(row["turns"]))
    no_track = (int(row["decision_no_firm_track_a"]) + int(row["decision_no_firm_track_b"])) / (2 * turns)
    no_track_geometry = (int(row["no_firm_geometry_or_acquisition_turns_a"]) + int(row["no_firm_geometry_or_acquisition_turns_b"])) / (2 * turns)
    no_track_ew = (int(row["no_firm_ew_downgrade_turns_a"]) + int(row["no_firm_ew_downgrade_turns_b"])) / (2 * turns)
    out_range = (int(row["decision_out_of_range_a"]) + int(row["decision_out_of_range_b"])) / (2 * turns)
    no_plan_tp = (int(row["tp_denied_no_weapon_plan_turns_a"]) + int(row["tp_denied_no_weapon_plan_turns_b"])) / (2 * turns)
    effective_open = int(row["effective_range_open_turns_a"]) + int(row["effective_range_open_turns_b"] )
    track_close = int(row["track_close_close_turns_a"]) + int(row["track_close_close_turns_b"])
    terminals = int(row["terminal_arrivals_a"]) + int(row["terminal_arrivals_b"])
    intercepts = int(row["pds_intercepts_against_a"]) + int(row["pds_intercepts_against_b"])
    guidance_attempts = int(row["guidance_attempts_a"]) + int(row["guidance_attempts_b"])
    guidance_hits = int(row["guidance_hits_a"]) + int(row["guidance_hits_b"])
    pds_rate = intercepts / max(1, terminals)
    guidance_fail = (guidance_attempts - guidance_hits) / max(1, guidance_attempts)
    recovery = float(row["total_defensive_recovery"])
    gross = float(row["total_missile_raw_damage"])
    recovery_fraction = recovery / max(1.0, gross)
    cadence = max(float(row["mean_launch_gap_turns_combined"]), float(row["mean_terminal_gap_turns_combined"]))
    if no_plan_tp >= 0.25: return "TP_LAUNCH_DENIAL"
    if no_track_geometry >= 0.25 and effective_open > 0 and track_close > 0: return "SENSOR_WEAPON_ENVELOPE_OSCILLATION"
    if no_track_ew >= 0.20: return "EW_TRACK_SUPPRESSION"
    if no_track + out_range >= 0.35: return "GEOMETRY_OR_TRACK"
    if pds_rate >= 0.40 and terminals >= 4: return "PDS_SUPPRESSION"
    if guidance_fail >= 0.30 and guidance_attempts >= 4: return "GUIDANCE_ATTRITION"
    if recovery_fraction >= 0.50 and gross > 0: return "DEFENSIVE_RECOVERY"
    if cadence >= 3.0: return "DELIVERY_CADENCE"
    return "ACTIVE_ATTRITION_OR_MIXED"


def _result_row(idx: int, source: dict[str, str], result: Any, events: list[dict[str, Any]], turn_rows: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = result.winner in ("A", "B", "Draw") and not result.unresolved and not result.error
    row: dict[str, Any] = {
        "scenario_index": idx, "scenario_id": source["scenario_id"], "tl": int(source["tl"]),
        "side_a_weapon": source["side_a_weapon"], "side_b_weapon": source["side_b_weapon"],
        "weapon_pair": f"{source['side_a_weapon']}->{source['side_b_weapon']}",
        "resource_ensemble_id": source["resource_ensemble_id"], "scenario_stratum": source["scenario_stratum"],
        "winner": result.winner, "unresolved": int(result.unresolved), "error": result.error,
        "turns": int(result.turns), "termination_cause": result.termination_cause,
        "resolved_flag": int(resolved), "resolved_ge25_flag": int(resolved and result.turns >= LONG_RESOLVED_TURN),
        "turn_cap_flag": int(result.termination_cause == "TURN_CAP_SENTINEL"),
        "safe_stalemate_flag": int(result.termination_cause == "STALEMATE_MUTUAL_OFFENSIVE_EXHAUSTION"),
        "event_rows": len(events), "turn_telemetry_rows": len(turn_rows),
        "turn_telemetry_coverage_pass": int(len(turn_rows) == 2 * int(result.turns)),
        "final_missiles_in_flight": int(result.final_missiles_in_flight),
        "min_range": int(result.min_range), "final_range": int(result.final_range),
    }
    row.update(_side_metrics(events, "A", int(result.turns)))
    row.update(_side_metrics(events, "B", int(result.turns)))
    row["mean_launch_gap_turns_combined"] = _mean([float(row["mean_launch_gap_turns_a"]), float(row["mean_launch_gap_turns_b"])])
    row["mean_terminal_gap_turns_combined"] = _mean([float(row["mean_terminal_gap_turns_a"]), float(row["mean_terminal_gap_turns_b"])])
    row["mean_terminal_transit_turns_combined"] = _mean([float(row["mean_terminal_transit_turns_a"]), float(row["mean_terminal_transit_turns_b"])])
    row["total_terminals"] = int(row["terminal_arrivals_a"]) + int(row["terminal_arrivals_b"])
    row["total_pds_attempts"] = int(row["pds_attempts_against_a"]) + int(row["pds_attempts_against_b"])
    row["total_pds_intercepts"] = int(row["pds_intercepts_against_a"]) + int(row["pds_intercepts_against_b"])
    row["total_guidance_attempts"] = int(row["guidance_attempts_a"]) + int(row["guidance_attempts_b"])
    row["total_guidance_hits"] = int(row["guidance_hits_a"]) + int(row["guidance_hits_b"])
    row["total_range_exhaustions"] = int(row["range_exhaustions_a"]) + int(row["range_exhaustions_b"])
    row["total_launches"] = int(row["launches_a"]) + int(row["launches_b"])
    row["total_subflights_launched"] = int(row["subflights_launched_a"]) + int(row["subflights_launched_b"])
    row["total_inflight_turn_exposure"] = int(row["inflight_turn_exposure_a"]) + int(row["inflight_turn_exposure_b"])
    row["total_no_firm_geometry_or_acquisition_turns"] = int(row["no_firm_geometry_or_acquisition_turns_a"]) + int(row["no_firm_geometry_or_acquisition_turns_b"])
    row["total_no_firm_ew_downgrade_turns"] = int(row["no_firm_ew_downgrade_turns_a"]) + int(row["no_firm_ew_downgrade_turns_b"])
    row["total_effective_range_open_turns"] = int(row["effective_range_open_turns_a"]) + int(row["effective_range_open_turns_b"])
    row["total_track_close_close_turns"] = int(row["track_close_close_turns_a"]) + int(row["track_close_close_turns_b"])
    row["total_defensive_recovery"] = (
        int(row["final_shield_restored_total_a"]) + int(row["final_shield_restored_total_b"]) +
        int(row["final_armor_restored_total_a"]) + int(row["final_armor_restored_total_b"]) +
        int(row["final_hull_restored_total_a"]) + int(row["final_hull_restored_total_b"])
    )
    row["total_missile_raw_damage"] = float(result.side_a.missile_raw_damage) + float(result.side_b.missile_raw_damage)
    row["total_missile_hull_damage"] = float(result.side_a.missile_hull_damage) + float(result.side_b.missile_hull_damage)
    row["pds_intercept_fraction_of_terminals"] = row["total_pds_intercepts"] / max(1, row["total_terminals"])
    row["guidance_success_fraction"] = row["total_guidance_hits"] / max(1, row["total_guidance_attempts"])
    row["recovery_fraction_of_missile_raw_damage"] = row["total_defensive_recovery"] / max(1.0, row["total_missile_raw_damage"])
    row["dominant_pacing_signal"] = _dominant_signal(row)
    return row


def _execute_task(args: tuple[int, dict[str, str], Any, int, bool]) -> dict[str, Any]:
    idx, source, bound, seed, keep_events = args
    if _WORKER_MATRICES is None: raise RuntimeError("CP143 worker matrices not initialized")
    matrix = _WORKER_MATRICES[source["resource_ensemble_id"]]
    events: list[dict[str, Any]] = []
    turn_rows: list[dict[str, Any]] = []
    ctx = {"scenario_id": source["scenario_id"], "resource_ensemble_id": source["resource_ensemble_id"], "weapon_a": source["side_a_weapon"], "weapon_b": source["side_b_weapon"]}
    result = run_trial_full_map(matrix, replace(bound.variant, max_turns=HARD_TURN_SENTINEL), seed, 0, event_sink=events, turn_telemetry_sink=turn_rows, telemetry_context=ctx)
    row = _result_row(idx, source, result, events, turn_rows)
    return {"index": idx, "row": row, "events": events if keep_events else []}


def _q(values: list[int], frac: float) -> float:
    if not values: return 0.0
    vals = sorted(values); pos = (len(vals) - 1) * frac; lo = int(pos); hi = min(len(vals)-1, lo+1); f = pos-lo
    return vals[lo]*(1-f)+vals[hi]*f


def _group_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = {
        "OVERALL": lambda r: "ALL",
        "TL": lambda r: f"TL{r['tl']}",
        "STRATUM": lambda r: r["scenario_stratum"],
        "WEAPON_PAIR": lambda r: r["weapon_pair"],
        "RESOURCE": lambda r: r["resource_ensemble_id"],
        "PAIR_X_STRATUM": lambda r: f"{r['weapon_pair']}|{r['scenario_stratum']}",
        "TL_X_PAIR": lambda r: f"TL{r['tl']}|{r['weapon_pair']}",
    }
    out: list[dict[str, Any]] = []
    for gtype, fn in specs.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows: groups[fn(r)].append(r)
        for key in sorted(groups):
            g = groups[key]; resolved=[r for r in g if int(r["resolved_flag"])]
            turns=[int(r["turns"]) for r in resolved]
            terminals=sum(int(r["total_terminals"]) for r in g); intercepts=sum(int(r["total_pds_intercepts"]) for r in g)
            guide_attempts=sum(int(r["total_guidance_attempts"]) for r in g); guide_hits=sum(int(r["total_guidance_hits"]) for r in g)
            gross=sum(float(r["total_missile_raw_damage"]) for r in g); recovery=sum(float(r["total_defensive_recovery"]) for r in g)
            decision_den = max(1, sum(2*int(r["turns"]) for r in g))
            out.append({
                "group_type": gtype, "group_key": key, "scenarios": len(g), "resolved": len(resolved),
                "turn_cap_sentinels": sum(int(r["turn_cap_flag"]) for r in g), "safe_stalemates": sum(int(r["safe_stalemate_flag"]) for r in g),
                "resolved_ge25": sum(int(r["resolved_ge25_flag"]) for r in g),
                "median_resolved_turns": _q(turns,0.5), "p90_resolved_turns": _q(turns,0.9), "p95_resolved_turns": _q(turns,0.95),
                "mean_first_launch_turn": _mean([float(x) for r in g for x in (r["first_launch_turn_a"],r["first_launch_turn_b"]) if int(x)>0]),
                "mean_first_terminal_turn": _mean([float(x) for r in g for x in (r["first_terminal_turn_a"],r["first_terminal_turn_b"]) if int(x)>0]),
                "mean_terminal_transit_turns": _mean([float(r["mean_terminal_transit_turns_combined"]) for r in g]),
                "mean_launch_gap_turns": _mean([float(r["mean_launch_gap_turns_combined"]) for r in g]),
                "mean_terminal_gap_turns": _mean([float(r["mean_terminal_gap_turns_combined"]) for r in g]),
                "terminal_arrivals": terminals, "pds_intercepts": intercepts,
                "pds_intercept_fraction_of_terminals": intercepts/max(1,terminals),
                "guidance_attempts": guide_attempts, "guidance_hits": guide_hits,
                "guidance_success_fraction": guide_hits/max(1,guide_attempts),
                "range_exhaustions": sum(int(r["total_range_exhaustions"]) for r in g),
                "launches": sum(int(r["total_launches"]) for r in g),
                "subflights_launched": sum(int(r["total_subflights_launched"]) for r in g),
                "inflight_turn_exposure": sum(int(r["total_inflight_turn_exposure"]) for r in g),
                "no_firm_track_turn_fraction": sum(int(r["decision_no_firm_track_a"])+int(r["decision_no_firm_track_b"]) for r in g)/decision_den,
                "no_firm_geometry_or_acquisition_turn_fraction": sum(int(r["total_no_firm_geometry_or_acquisition_turns"]) for r in g)/decision_den,
                "no_firm_ew_downgrade_turn_fraction": sum(int(r["total_no_firm_ew_downgrade_turns"]) for r in g)/decision_den,
                "effective_range_open_turn_fraction": sum(int(r["total_effective_range_open_turns"]) for r in g)/decision_den,
                "track_close_close_turn_fraction": sum(int(r["total_track_close_close_turns"]) for r in g)/decision_den,
                "out_of_range_turn_fraction": sum(int(r["decision_out_of_range_a"])+int(r["decision_out_of_range_b"]) for r in g)/decision_den,
                "no_weapon_plan_turn_fraction": sum(int(r["decision_no_weapon_plan_a"])+int(r["decision_no_weapon_plan_b"]) for r in g)/decision_den,
                "tp_denied_no_weapon_plan_turn_fraction": sum(int(r["tp_denied_no_weapon_plan_turns_a"])+int(r["tp_denied_no_weapon_plan_turns_b"]) for r in g)/decision_den,
                "ammo_exhausted_turn_fraction": sum(int(r["decision_ammo_exhausted_a"])+int(r["decision_ammo_exhausted_b"]) for r in g)/decision_den,
                "total_missile_raw_damage": gross, "total_defensive_recovery": recovery,
                "recovery_fraction_of_missile_raw_damage": recovery/max(1.0,gross),
            })
    return out


def _signal_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out=[]
    for scope, keyfn in (("OVERALL",lambda r:"ALL"),("STRATUM",lambda r:r["scenario_stratum"]),("WEAPON_PAIR",lambda r:r["weapon_pair"]),("TL",lambda r:f"TL{r['tl']}")):
        groups: dict[str,list[dict[str,Any]]] = defaultdict(list)
        for r in rows: groups[keyfn(r)].append(r)
        for key,g in sorted(groups.items()):
            counts=Counter(r["dominant_pacing_signal"] for r in g)
            for signal,count in sorted(counts.items()):
                out.append({"group_type":scope,"group_key":key,"signal":signal,"scenarios":count,"fraction":count/max(1,len(g))})
    return out


def _equivalence_rows(repo: Path, doc: dict[str, Any], rows: list[dict[str, str]], matrices: dict[str, Any]) -> list[dict[str, Any]]:
    # Twelve deterministic probes span early/mid/late TL, GP/Swarmer mirrors, PDS/no-PDS and power pressure.
    wanted=[]
    specs=[
        (2,"M_GP","M_GP","BALANCED_CORE_NO_PDS"),(2,"M_SWARMER","M_SWARMER","KINETIC_PDS_PRESSURE"),
        (3,"M_GP","M_SWARMER","ENERGY_PDS_PRESSURE"),(3,"M_SWARMER","M_GP","AMM_PDS_PRESSURE"),
        (5,"M_GP","M_GP","POWER_CRISIS"),(5,"M_SWARMER","M_SWARMER","SHIELD_PRESSURE"),
        (6,"M_GP","M_SWARMER","MOBILITY_STANDOFF"),(6,"M_SWARMER","M_GP","EW_CONTEST"),
        (8,"M_GP","M_GP","RECOVERY_ATTRITION"),(8,"M_SWARMER","M_SWARMER","AMM_PDS_PRESSURE"),
        (9,"M_GP","M_SWARMER","BALANCED_CORE_NO_PDS"),(9,"M_SWARMER","M_GP","POWER_CRISIS"),
    ]
    for tl,a,b,s in specs:
        r=next(x for x in rows if int(x["tl"])==tl and x["side_a_weapon"]==a and x["side_b_weapon"]==b and x["scenario_stratum"]==s and x["resource_ensemble_id"]=="R1_CENTRAL_NO_MAJOR")
        wanted.append(r)
    out=[]
    for r in wanted:
        matrix=matrices[r["resource_ensemble_id"]]; bound=bind_scenario(matrix,r); variant=replace(bound.variant,max_turns=HARD_TURN_SENTINEL)
        off_turns=[]; on_turns=[]; events=[]
        ctx={"scenario_id":r["scenario_id"],"resource_ensemble_id":r["resource_ensemble_id"],"weapon_a":r["side_a_weapon"],"weapon_b":r["side_b_weapon"]}
        off=run_trial_full_map(matrix,variant,int(doc["masterSeed"]),0,turn_telemetry_sink=off_turns,telemetry_context=ctx)
        on=run_trial_full_map(matrix,variant,int(doc["masterSeed"]),0,event_sink=events,turn_telemetry_sink=on_turns,telemetry_context=ctx)
        off_hash=hashlib.sha256(json.dumps(asdict(off),sort_keys=True,separators=(",",":")).encode()).hexdigest()
        on_hash=hashlib.sha256(json.dumps(asdict(on),sort_keys=True,separators=(",",":")).encode()).hexdigest()
        off_turn_hash=hashlib.sha256(json.dumps(off_turns,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        on_turn_hash=hashlib.sha256(json.dumps(on_turns,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        out.append({"scenario_id":r["scenario_id"],"tl":tl,"weapon_pair":f"{a}->{b}","stratum":s,
                    "result_equivalent":int(off_hash==on_hash),"turn_telemetry_equivalent":int(off_turn_hash==on_turn_hash),
                    "off_result_sha256":off_hash,"on_result_sha256":on_hash,"event_rows":len(events)})
    return out


def run_batch(repo: Path, study_path: Path, outdir: Path, jobs: int=24, batch_start: int=0, batch_end: int|None=None) -> dict[str, Any]:
    doc=load_json(study_path); errors=validate_study(doc)
    if errors:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True)
    rows=_missile_rows(repo,doc); ensemble_rows,tl_rows=_resource_rows(repo,doc); source_matrix=repo/doc["matrix"]; before=_sha(source_matrix)
    matrices={eid:build_deep_resource_matrix(repo,doc["matrix"],eid,ensemble_rows,tl_rows) for eid in sorted({r["ensemble_id"] for r in ensemble_rows})}
    bindings=[bind_scenario(matrices[r["resource_ensemble_id"]],r) for r in rows]
    start=max(0,int(batch_start)); end=len(rows) if batch_end is None else min(len(rows),int(batch_end))
    tasks=[(i,rows[i],bindings[i],int(doc["masterSeed"]),True) for i in range(start,end)]
    jobs=max(1,min(int(jobs),len(tasks)))
    if jobs==1:
        _worker_init(str(repo),doc["matrix"],ensemble_rows,tl_rows); completed=[_execute_task(t) for t in tasks]
    else:
        ctx=get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],ensemble_rows,tl_rows)) as ex:
            completed=list(ex.map(_execute_task,tasks,chunksize=4))
    completed.sort(key=lambda x:x["index"]); result_rows=[x["row"] for x in completed]
    # Persist raw timeline only for this batch's worst and fastest case per pair x stratum, limiting artifact size.
    by_group: dict[str,list[dict[str,Any]]] = defaultdict(list)
    for x in completed: by_group[f"{x['row']['weapon_pair']}|{x['row']['scenario_stratum']}"] .append(x)
    selected=set()
    for group in by_group.values():
        worst=max(group,key=lambda x:(int(x["row"]["turns"]),x["row"]["scenario_id"])); fastest=min(group,key=lambda x:(int(x["row"]["turns"]),x["row"]["scenario_id"]))
        selected.add(worst["row"]["scenario_id"]); selected.add(fastest["row"]["scenario_id"])
    timeline=[]
    for x in completed:
        if x["row"]["scenario_id"] not in selected: continue
        for e in x["events"]:
            if e.get("event") not in {"movement","missile_launch_decision","missile_launch","missile_terminal","missile_range_exhausted","missile_inventory","missile_turn_state"}: continue
            z={"scenario_id":x["row"]["scenario_id"],"tl":x["row"]["tl"],"weapon_pair":x["row"]["weapon_pair"],"resource_ensemble_id":x["row"]["resource_ensemble_id"],"scenario_stratum":x["row"]["scenario_stratum"]}; z.update(e); timeline.append(z)
    _write_csv(outdir/"missile_mirror_attribution_results.csv",result_rows); _write_csv(outdir/"missile_mirror_timeline_sample.csv",timeline)
    after=_sha(source_matrix); failures=[]
    if len(result_rows)!=end-start:failures.append("scenario-count")
    if any(r["error"] for r in result_rows):failures.append("execution-errors")
    if any(not int(r["turn_telemetry_coverage_pass"]) for r in result_rows):failures.append("turn-telemetry-coverage")
    if before!=after:failures.append("source-matrix-modified")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":143,"baseCheckpoint":142,"passed":not failures,"failedGates":failures,
             "batchStart":start,"batchEnd":end,"scenarios":len(result_rows),"executionErrors":sum(bool(r["error"]) for r in result_rows),
             "resolved":sum(int(r["resolved_flag"]) for r in result_rows),"resolvedGe25":sum(int(r["resolved_ge25_flag"]) for r in result_rows),
             "turnCapSentinels":sum(int(r["turn_cap_flag"]) for r in result_rows),"safeStalemates":sum(int(r["safe_stalemate_flag"]) for r in result_rows),
             "sourceMatrixUnmodified":before==after,"substantiveCombatTrials":0,"tuningAllowed":False,"promotionAllowed":False,
             "interpretation":"Bounded one-trial missile-mirror pacing attribution only; no balance tuning or promotion."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary


def merge_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    doc=load_json(study_path); errors=validate_study(doc)
    if errors:return {"schemaVersion":RESULT_SCHEMA,"passed":False,"failedGates":["study-validation:"+",".join(errors)]}
    outdir.mkdir(parents=True,exist_ok=True); source_matrix=repo/doc["matrix"]; before=_sha(source_matrix)
    all_rows=[]; all_timeline=[]; audits=[]; expected=0
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp=d/"summary.json"; rp=d/"missile_mirror_attribution_results.csv"
        if not sp.exists() or not rp.exists():continue
        payload=json.loads(sp.read_text()); start=int(payload["batchStart"]); end=int(payload["batchEnd"]); rows=_read_csv(rp)
        ok=bool(payload["passed"]) and start==expected and len(rows)==end-start
        audits.append({"batch":d.name,"start":start,"end":end,"scenarios":len(rows),"passed":int(ok)})
        if not ok: expected=-1
        elif expected>=0: expected=end
        all_rows.extend(rows)
        tp=d/"missile_mirror_timeline_sample.csv"
        if tp.exists() and tp.stat().st_size: all_timeline.extend(_read_csv(tp))
    all_rows.sort(key=lambda r:int(r["scenario_index"])); failures=[]
    if expected!=EXPECTED_MISSILE_MIRROR_SCENARIOS:failures.append("batch-contiguity")
    if len(all_rows)!=EXPECTED_MISSILE_MIRROR_SCENARIOS:failures.append("scenario-count")
    ids=[r["scenario_id"] for r in all_rows]
    if len(ids)!=len(set(ids)):failures.append("duplicate-scenario")
    if any(r["error"] for r in all_rows):failures.append("execution-errors")
    if before!=_sha(source_matrix):failures.append("source-matrix-modified")
    groups=_group_summary(all_rows); signals=_signal_summary(all_rows)
    reference_path=repo/doc["pairedBaselineReference"]
    reference_rows=_read_csv(reference_path)
    reference_map={r["scenario_id"]:r for r in reference_rows}
    reference_hash=_sha(reference_path)
    if reference_hash != doc["pairedBaselineReferenceSha256"]: failures.append("cp142-reference-hash")
    if len(reference_rows) != EXPECTED_MISSILE_MIRROR_SCENARIOS: failures.append("cp142-reference-count")
    paired=[]
    for r in all_rows:
        ref=reference_map.get(r["scenario_id"])
        same=bool(ref) and all(str(r[k])==str(ref[k]) for k in ("winner","unresolved","turns","termination_cause"))
        paired.append({"scenario_id":r["scenario_id"],"winner":r["winner"],"turns":r["turns"],"termination_cause":r["termination_cause"],
                       "cp142_winner":ref["winner"] if ref else "","cp142_turns":ref["turns"] if ref else "","cp142_termination_cause":ref["termination_cause"] if ref else "",
                       "exact_cp142_outcome_match":int(same)})
    if any(not int(r["exact_cp142_outcome_match"]) for r in paired): failures.append("cp142-paired-outcome-drift")
    ensemble_rows,tl_rows=_resource_rows(repo,doc); matrices={eid:build_deep_resource_matrix(repo,doc["matrix"],eid,ensemble_rows,tl_rows) for eid in sorted({r["ensemble_id"] for r in ensemble_rows})}
    equivalence=_equivalence_rows(repo,doc,_missile_rows(repo,doc),matrices)
    if any(not int(r["result_equivalent"]) or not int(r["turn_telemetry_equivalent"]) for r in equivalence):failures.append("instrumentation-nonneutral")
    _write_csv(outdir/"missile_mirror_attribution_results.csv",all_rows); _write_csv(outdir/"missile_mirror_group_summary.csv",groups)
    _write_csv(outdir/"missile_mirror_pacing_signal_summary.csv",signals); _write_csv(outdir/"instrumentation_equivalence.csv",equivalence)
    _write_csv(outdir/"cp142_paired_outcome_equivalence.csv",paired)
    _write_csv(outdir/"missile_mirror_timeline_sample.csv",all_timeline); _write_csv(outdir/"batch_merge_audit.csv",audits)
    overall=next(r for r in groups if r["group_type"]=="OVERALL")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":143,"baseCheckpoint":142,"passed":not failures,"failedGates":failures,
             "missileMirrorScenarios":len(all_rows),"executionErrors":sum(bool(r["error"]) for r in all_rows),
             "resolved":int(overall["resolved"]),"resolvedGe25":int(overall["resolved_ge25"]),"turnCapSentinels":int(overall["turn_cap_sentinels"]),
             "safeStalemates":int(overall["safe_stalemates"]),"medianResolvedTurns":overall["median_resolved_turns"],"p90ResolvedTurns":overall["p90_resolved_turns"],
             "instrumentationEquivalenceCases":len(equivalence),"instrumentationEquivalencePassed":sum(int(r["result_equivalent"]) and int(r["turn_telemetry_equivalent"]) for r in equivalence),
             "cp142PairedOutcomeReferenceCases":len(reference_rows),"cp142PairedOutcomeMatches":sum(int(r["exact_cp142_outcome_match"]) for r in paired),
             "cp142PairedOutcomeReferenceSha256":reference_hash,
             "sourceMatrixUnmodified":before==_sha(source_matrix),"hardTurnSentinel":HARD_TURN_SENTINEL,"longResolvedTurn":LONG_RESOLVED_TURN,
             "substantiveCombatTrials":0,"tuningAllowed":False,"promotionAllowed":False,
             "nextStage":"whole-combat substantive Stage A after collapsing executable-equivalent R5 resource level",
             "interpretation":"Mechanism attribution only. One-trial frequencies identify where time is spent; they are not balance probabilities."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
