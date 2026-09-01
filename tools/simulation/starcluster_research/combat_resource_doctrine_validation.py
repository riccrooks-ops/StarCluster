from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .ecology import LEGACY_COMBAT_DOCTRINE, CONTEXTUAL_COMBAT_DOCTRINE
from .stage_a_diagnostic_attribution import _diag_task, _worker_init
from .stage_a_integration_analysis import _read_csv, _resource_rows
from .study import canonicalize_relocated_references, load_json

RESULT_SCHEMA = "star-cluster-cp146-combat-resource-doctrine-result-v0.1"
EXPECTED_SCENARIOS = 252
TRIALS_PER_SCENARIO = 25
EXPECTED_PER_DOCTRINE = EXPECTED_SCENARIOS * TRIALS_PER_SCENARIO


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    exact = {
        "schemaVersion": "star-cluster-cp146-combat-resource-doctrine-study-v0.1",
        "checkpoint": 146, "baseCheckpoint": 145,
        "legacyDoctrine": LEGACY_COMBAT_DOCTRINE,
        "candidateDoctrine": CONTEXTUAL_COMBAT_DOCTRINE,
        "expectedScenarios": EXPECTED_SCENARIOS,
        "trialsPerScenarioPerDoctrine": TRIALS_PER_SCENARIO,
        "expectedCombatTrialsPerDoctrine": EXPECTED_PER_DOCTRINE,
        "expectedTotalCombatTrials": 2 * EXPECTED_PER_DOCTRINE,
        "masterSeed": 140001,
        "tuningAllowed": False, "automaticPromotion": False, "stageBAutomatic": False,
    }
    for k, v in exact.items():
        if doc.get(k) != v: errors.append(f"{k}: expected {v!r}, found {doc.get(k)!r}")
    if len(doc.get("doctrineRequirements", [])) < 9: errors.append("doctrineRequirements incomplete")
    return errors


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    errors = validate_study(doc)
    for field, hash_field in (
        ("matrix", "matrixSha256"),
        ("acceptedCp145NativeSummary", "acceptedCp145NativeSummarySha256"),
        ("acceptedCp145DiagnosticSummary", "acceptedCp145DiagnosticSummarySha256"),
        ("acceptedCp145DiagnosticResults", "acceptedCp145DiagnosticResultsSha256"),
    ):
        p = repo / str(doc[field])
        if not p.is_file(): errors.append(f"missing {field}: {p}"); continue
        if _sha(p) != str(doc[hash_field]): errors.append(f"hash mismatch: {field}")
    manifest = _read_csv(repo / doc["diagnosticReplayManifest"])
    if len(manifest) != EXPECTED_SCENARIOS: errors.append(f"diagnostic replay rows: {len(manifest)}")
    ids = [r["scenario_id"] for r in manifest]
    if len(set(ids)) != len(ids): errors.append("diagnostic replay scenario ids are not unique")
    stage = _read_csv(repo / doc["stageAExperimentManifest"])
    stage_ids = {r["scenario_id"] for r in stage}
    missing = sorted(set(ids) - stage_ids)
    if missing: errors.append(f"diagnostic identities missing from CP144 manifest: {len(missing)}")
    accepted = _read_csv(repo / doc["acceptedCp145DiagnosticResults"])
    if len(accepted) != EXPECTED_SCENARIOS: errors.append(f"accepted CP145 diagnostic rows: {len(accepted)}")
    if {r["scenario_id"] for r in accepted} != set(ids): errors.append("accepted CP145 identities differ from replay manifest")
    fixture = load_json(repo / doc["doctrineParityFixtures"])
    if fixture.get("checkpoint") != 146 or len(fixture.get("cases", [])) < 8: errors.append("CP146 doctrine parity fixture invalid")
    return errors


def _same_value(a: str, b: Any) -> bool:
    if a == "" and (b == "" or b is None): return True
    try:
        av = float(a); bv = float(b)
        return math.isclose(av, bv, rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return str(a) == str(b)


def _legacy_comparison(accepted: list[dict[str, str]], replayed: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    accepted_by_id = {r["scenario_id"]: r for r in accepted}
    rows: list[dict[str, Any]] = []; mismatches = 0
    for row in replayed:
        old = accepted_by_id[row["scenario_id"]]
        bad: list[str] = []
        for field, value in old.items():
            if field not in row or not _same_value(value, row[field]): bad.append(field)
        mismatches += len(bad)
        rows.append({"scenario_id": row["scenario_id"], "matching_fields": len(old)-len(bad), "field_mismatches": len(bad), "mismatched_fields": ";".join(bad)})
    return rows, mismatches


def _doctrine_deltas(legacy: list[dict[str, Any]], contextual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old = {r["scenario_id"]: r for r in legacy}; out = []
    metrics = ("a_wins", "b_wins", "draws", "turn_cap_sentinels", "resolved_ge25", "mean_turns",
               "a_tp_conflict_turn_rate", "b_tp_conflict_turn_rate", "a_weapon_denial_turn_rate", "b_weapon_denial_turn_rate")
    for r in contextual:
        b = old[r["scenario_id"]]
        row = {k: r[k] for k in ("diagnostic_index","scenario_id","diagnostic_family","tl","side_a_weapon","side_b_weapon","resource_ensemble_id","scenario_stratum")}
        for m in metrics:
            row[f"legacy_{m}"] = b[m]; row[f"contextual_{m}"] = r[m]; row[f"delta_{m}"] = float(r[m]) - float(b[m])
        out.append(row)
    return out


def _tp_before_after(legacy: list[dict[str, Any]], contextual: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[int,str], dict[str,list[dict[str,Any]]]] = defaultdict(lambda:{"legacy":[],"contextual":[]})
    for label, rows in (("legacy", legacy),("contextual",contextual)):
        for r in rows:
            if r["diagnostic_family"] == "TP_STARVATION": groups[(int(r["tl"]),str(r["scenario_stratum"]))][label].append(r)
    out=[]
    for key,g in sorted(groups.items()):
        row={"tl":key[0],"scenario_stratum":key[1],"scenarios":len(g["legacy"])}
        for label in ("legacy","contextual"):
            rs=g[label]; combats=sum(int(x["trials"]) for x in rs); caps=sum(int(x["turn_cap_sentinels"]) for x in rs)
            denial=statistics.fmean((float(x["a_weapon_denial_turn_rate"])+float(x["b_weapon_denial_turn_rate"]))/2 for x in rs)
            conflict=statistics.fmean((float(x["a_tp_conflict_turn_rate"])+float(x["b_tp_conflict_turn_rate"]))/2 for x in rs)
            row[f"{label}_combats"]=combats; row[f"{label}_turn_caps"]=caps; row[f"{label}_turn_cap_rate"]=caps/combats if combats else 0.0
            row[f"{label}_mean_weapon_denial_turn_rate"]=denial; row[f"{label}_mean_tp_conflict_turn_rate"]=conflict
        row["delta_turn_cap_rate"]=row["contextual_turn_cap_rate"]-row["legacy_turn_cap_rate"]
        row["delta_weapon_denial_turn_rate"]=row["contextual_mean_weapon_denial_turn_rate"]-row["legacy_mean_weapon_denial_turn_rate"]
        out.append(row)
    return out


def _context_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str,str], list[tuple[dict[str,Any],str]]] = defaultdict(list)
    for r in rows:
        for low, weapon in (("a",r["side_a_weapon"]),("b",r["side_b_weapon"])):
            groups[(r["diagnostic_family"],weapon)].append((r,low))
    out=[]
    for key, rs in sorted(groups.items()):
        side_turns=sum(int(r.get(f"{low}_side_turns",0)) for r,low in rs)
        def sm(name:str)->int: return sum(int(float(r.get(f"{low}_{name}",0))) for r,low in rs)
        out.append({
            "diagnostic_family":key[0],"weapon":key[1],"scenario_sides":len(rs),"side_turns":side_turns,
            "weapon_core_funded_turns":sm("cp146_weapon_core_funded_turns"),"weapon_core_starved_turns":sm("cp146_weapon_core_starved_turns"),
            "active_sensor_turns":sm("cp146_active_sensor_default_turns"),"passive_fallback_turns":sm("cp146_passive_sensor_fallback_turns"),
            "unknown_opponent_turns":sm("cp146_unknown_opponent_turns"),"known_opponent_turns":sm("cp146_known_opponent_turns"),
            "pds_unknown_readiness_turns":sm("cp146_pds_unknown_readiness_turns"),"pds_imminent_threat_turns":sm("cp146_pds_imminent_threat_turns"),
            "pds_irrelevant_suppressed_turns":sm("cp146_pds_irrelevant_suppressed_turns"),
            "hardener_unknown_readiness_turns":sm("cp146_hardener_unknown_readiness_turns"),"hardener_relevant_turns":sm("cp146_hardener_relevant_turns"),
            "hardener_irrelevant_suppressed_turns":sm("cp146_hardener_irrelevant_suppressed_turns"),
            "held_main_declarations":sm("cp146_held_main_declarations"),"held_main_attempts":sm("cp146_held_main_attempts"),"held_main_intercepts":sm("cp146_held_main_intercepts"),"held_main_unused":sm("cp146_held_main_unused"),
            "direct_shots":sm("direct_shots"),"missile_launches":sm("missile_launches"),"pds_attempts":sm("pds_attempts"),"pds_intercepts":sm("pds_intercepts")})
    return out


def _pds_terminology(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str,str,str], list[tuple[dict[str,Any],str]]] = defaultdict(list)
    for r in rows:
        if r["diagnostic_family"] != "PDS_OPPORTUNITY": continue
        # Missile attacker is Side A in the CP145 selection; defender/PDS is Side B.
        groups[(r["side_a_weapon"],r["scenario_stratum"],r["resource_ensemble_id"])].append((r,"b"))
    out=[]
    for key,rs in sorted(groups.items()):
        def sm(name:str)->int:return sum(int(float(r.get(f"{low}_{name}",0))) for r,low in rs)
        mags=sm("terminal_magazine_flights"); visible=sm("pds_visible_subflights"); any_attempt=sm("magazine_flights_with_any_pds_attempt"); full=sm("magazine_flights_fully_covered"); partial=sm("magazine_flights_partially_covered")
        out.append({"missile_family":key[0],"scenario_stratum":key[1],"resource_ensemble_id":key[2],"scenario_rows":len(rs),
                    "terminal_magazine_flights":mags,"pds_visible_subflights":visible,"magazine_flights_with_any_pds_attempt":any_attempt,
                    "magazine_flights_fully_covered":full,"magazine_flights_partially_covered":partial,
                    "subflights_with_0_attempts":sm("subflights_with_0_attempts"),"subflights_with_1_attempt":sm("subflights_with_1_attempt"),"subflights_with_2_attempts":sm("subflights_with_2_attempts"),
                    "magazine_any_attempt_rate":any_attempt/mags if mags else 0.0,"full_coverage_rate":full/mags if mags else 0.0,"visible_subflights_per_magazine":visible/mags if mags else 0.0})
    return out


def run_analysis(repo: Path, study_path: Path, outdir: Path, jobs: int=24) -> dict[str, Any]:
    doc=load_json(study_path); failures=validate_population(repo,doc)
    if failures: return {"schemaVersion":RESULT_SCHEMA,"checkpoint":146,"passed":False,"failedGates":failures}
    outdir.mkdir(parents=True, exist_ok=True)
    replay_manifest=_read_csv(repo/doc["diagnosticReplayManifest"]); stage_manifest=_read_csv(repo/doc["stageAExperimentManifest"]); stage_by_id={r["scenario_id"]:r for r in stage_manifest}
    stage_doc=load_json(repo/doc["stageAStudy"]); er,tr=_resource_rows(repo,stage_doc); sources=[]
    for selection in replay_manifest:
        source=dict(stage_by_id[selection["scenario_id"]]); source.update(selection); sources.append(source)
    before=_sha(repo/doc["matrix"]); trials=int(doc["trialsPerScenarioPerDoctrine"]); seed=int(doc["masterSeed"])
    jobs=max(1,min(int(jobs),len(sources)))
    def execute(doctrine:str)->list[dict[str,Any]]:
        tasks=[(r,trials,seed,doctrine) for r in sources]
        if jobs==1:
            _worker_init(str(repo),doc["matrix"],er,tr); done=[_diag_task(t) for t in tasks]
        else:
            ctx=get_context("spawn" if os.name == "nt" else "fork")
            with ProcessPoolExecutor(max_workers=jobs,mp_context=ctx,initializer=_worker_init,initargs=(str(repo),doc["matrix"],er,tr)) as ex:
                done=list(ex.map(_diag_task,tasks,chunksize=1))
        done.sort(key=lambda r:int(r["diagnostic_index"])); return done
    legacy=execute(LEGACY_COMBAT_DOCTRINE); contextual=execute(CONTEXTUAL_COMBAT_DOCTRINE)
    _write_csv(outdir/"legacy_replay_results.csv",legacy); _write_csv(outdir/"contextual_replay_results.csv",contextual)
    accepted=_read_csv(repo/doc["acceptedCp145DiagnosticResults"]); compare,mismatches=_legacy_comparison(accepted,legacy); _write_csv(outdir/"legacy_reproduction_audit.csv",compare)
    deltas=_doctrine_deltas(legacy,contextual); _write_csv(outdir/"doctrine_delta_results.csv",deltas)
    tp=_tp_before_after(legacy,contextual); _write_csv(outdir/"tp_starvation_before_after.csv",tp)
    context=_context_summary(contextual); _write_csv(outdir/"contextual_activation_summary.csv",context)
    pds=_pds_terminology(contextual); _write_csv(outdir/"pds_magazine_subflight_coverage.csv",pds)
    after=_sha(repo/doc["matrix"])
    if mismatches: failures.append(f"accepted-cp145-legacy-reproduction:{mismatches}-field-mismatches")
    for label, rows in (("legacy",legacy),("contextual",contextual)):
        if len(rows)!=EXPECTED_SCENARIOS: failures.append(f"{label}-scenario-count")
        if sum(int(r["trials"]) for r in rows)!=EXPECTED_PER_DOCTRINE: failures.append(f"{label}-trial-count")
        if any(int(r["error_trials"]) for r in rows): failures.append(f"{label}-trial-errors")
        if any(int(r["nonstandoff_open_orders"]) for r in rows): failures.append(f"{label}-nonstandoff-open")
    if before!=after: failures.append("source-matrix-modified")
    # Behavior gates target the diagnosed pathological regions, not balance outcomes.
    tl2=[r for r in tp if int(r["tl"])==2 and r["scenario_stratum"] in {"EW_CONTEST","POWER_CRISIS"}]
    legacy_caps=sum(int(r["legacy_turn_caps"]) for r in tl2); contextual_caps=sum(int(r["contextual_turn_caps"]) for r in tl2)
    if legacy_caps <= 0: failures.append("tl2-legacy-pathology-not-reproduced")
    if contextual_caps > legacy_caps * 0.10: failures.append("tl2-contextual-turn-cap-reduction-below-90pct")
    legacy_denial=statistics.fmean(float(r["legacy_mean_weapon_denial_turn_rate"]) for r in tl2) if tl2 else 0.0
    contextual_denial=statistics.fmean(float(r["contextual_mean_weapon_denial_turn_rate"]) for r in tl2) if tl2 else 0.0
    if contextual_denial >= legacy_denial: failures.append("tl2-contextual-weapon-denial-not-reduced")
    old_by_id={r["scenario_id"]:r for r in legacy}
    new_saturated=[r["scenario_id"] for r in contextual if int(r["turn_cap_sentinels"]) == int(r["trials"]) and int(old_by_id[r["scenario_id"]]["turn_cap_sentinels"]) < int(old_by_id[r["scenario_id"]]["trials"])]
    if new_saturated: failures.append(f"contextual-created-saturated-turn-cap-cells:{len(new_saturated)}")
    core_funded=sum(int(r["weapon_core_funded_turns"]) for r in context); core_starved=sum(int(r["weapon_core_starved_turns"]) for r in context)
    if core_starved > 0: failures.append("contextual-legal-weapon-core-starvation-observed")
    if sum(int(r["unknown_opponent_turns"]) for r in context)<=0 or sum(int(r["known_opponent_turns"]) for r in context)<=0: failures.append("knowledge-transition-not-observed")
    if sum(int(r["pds_irrelevant_suppressed_turns"]) for r in context)<=0: failures.append("irrelevant-pds-suppression-not-observed")
    if sum(int(r["hardener_irrelevant_suppressed_turns"]) for r in context)<=0: failures.append("irrelevant-hardener-suppression-not-observed")
    if sum(int(r["active_sensor_turns"]) for r in context)<=0: failures.append("active-sensor-doctrine-not-observed")
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":146,"baseCheckpoint":145,"passed":not failures,"failedGates":failures,
             "scenariosPerDoctrine":len(contextual),"trialsPerScenarioPerDoctrine":trials,"combatTrialsPerDoctrine":sum(int(r["trials"]) for r in contextual),"totalCombatTrials":sum(int(r["trials"]) for r in legacy+contextual),
             "acceptedCp145LegacyFieldMismatches":mismatches,"sourceMatrixUnmodified":before==after,"tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,
             "tl2LegacyTurnCaps":legacy_caps,"tl2ContextualTurnCaps":contextual_caps,"tl2LegacyMeanWeaponDenialTurnRate":legacy_denial,"tl2ContextualMeanWeaponDenialTurnRate":contextual_denial,
             "contextualWeaponCoreFundedTurns":core_funded,"contextualWeaponCoreStarvedTurns":core_starved,"contextualNewSaturatedTurnCapCells":len(new_saturated),
             "contextualUnknownOpponentTurns":sum(int(r["unknown_opponent_turns"]) for r in context),"contextualKnownOpponentTurns":sum(int(r["known_opponent_turns"]) for r in context),
             "heldMainDeclarations":sum(int(r["held_main_declarations"]) for r in context),"heldMainAttempts":sum(int(r["held_main_attempts"]) for r in context),"heldMainIntercepts":sum(int(r["held_main_intercepts"]) for r in context),
             "interpretation":"Logic-only before/after doctrine validation. Outcome deltas are diagnostic and do not promote numerical balance changes."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    return summary
