from __future__ import annotations

import csv
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

from .baseline_foundation import BaselineBuild, BaselineCatalog, enumerate_legal_builds
from .fidelity_attribution_analysis import FidelityTask
from .main_subsystem_stabilization_analysis import _override_matrix, _read_rows, _normalize_variant_rows
from .study import canonicalize_relocated_references, load_json
from .whole_ladder_analysis import generate_pairings, _write_csv
from .whole_ladder_sensitivity_analysis import _run_tasks

SCHEMA = "star-cluster-cp130-missile-main-progression-v0.1"
RESULT_SCHEMA = "star-cluster-cp130-missile-main-progression-results-v0.1"
DEFAULT_STUDY = "docs/archive/testing/pre-cp165-active/cp130_missile_main_progression_and_family_viability_study_v0_1.json"


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    expected = {
        "schemaVersion": SCHEMA,
        "checkpoint": 130,
        "acceptedBaselineCheckpoint": 129,
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
    for k, v in expected.items():
        if doc.get(k) != v:
            errors.append(k)
    if doc.get("tl1To7DamageDeltas") != [0, 1, 2]:
        errors.append("tl1To7DamageDeltas")
    late = doc.get("lateWarheadCandidates", {})
    for tl in (8, 9):
        rows = late.get(str(tl), [])
        if not rows or rows[0].get("id") != "control":
            errors.append(f"lateWarheadCandidates.{tl}")
            continue
        ids = [r.get("id") for r in rows]
        if len(ids) != len(set(ids)):
            errors.append(f"lateWarheadCandidates.{tl}.duplicate")
    if doc.get("acceptedCp129ChartBaseline") != "docs/validation/evidence/checkpoint-130/accepted-cp129/same_tl_family_chart_baseline.csv":
        errors.append("acceptedCp129ChartBaseline")
    return errors


def _family(build: BaselineBuild) -> str:
    return build.weapon_family


def _profile(build: BaselineBuild) -> str:
    return f"Missile-{build.missile_payload}" if build.weapon_family == "Missile" else build.weapon_family


def _same_tl_missile_tasks(builds: list[BaselineBuild], pairing_seed: int) -> dict[int, list[FidelityTask]]:
    pairings = generate_pairings(builds, pairing_seed)
    out: dict[int, list[FidelityTask]] = {tl: [] for tl in range(1, 10)}
    allowed = {("Energy", "Missile"), ("Kinetic", "Missile"), ("Missile", "Missile")}
    for p in pairings:
        if p.tl_1 != p.tl_2:
            continue
        fams = tuple(sorted((_family(p.build_1), _family(p.build_2))))
        if fams not in allowed:
            continue
        out[p.tl_1].append(FidelityTask(
            p.pairing_id, "cp130_same_tl_family", "pair", p.tl_1, p.tl_2,
            p.build_1.id, p.build_2.id, design_weight=p.design_weight,
        ))
    for tl in out:
        out[tl].sort(key=lambda t: t.task_id)
    return out


def _candidate_rows(repo: Path, doc: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    source = load_json(repo / doc["sourceMatrix"])
    out: dict[int, list[dict[str, Any]]] = {}
    for tl in range(1, 8):
        base = source["profiles"]["missile_gp_warhead"][str(tl)]
        rows = []
        for delta in doc["tl1To7DamageDeltas"]:
            rows.append({
                "id": "control" if delta == 0 else f"damage_plus_{delta}",
                "tl": tl,
                "damage": int(base["damage"]) + int(delta),
                "spen": int(base["spen"]),
                "apen": int(base["apen"]),
                "damageDelta": int(delta), "spenDelta": 0, "apenDelta": 0,
                "class": "control" if delta == 0 else "tl1_7_damage_sensitivity",
            })
        out[tl] = rows
    for tl in (8, 9):
        base = source["profiles"]["missile_gp_warhead"][str(tl)]
        rows = []
        for row in doc["lateWarheadCandidates"][str(tl)]:
            d = int(row.get("damageDelta", 0)); s = int(row.get("spenDelta", 0)); a = int(row.get("apenDelta", 0))
            rows.append({
                "id": row["id"], "tl": tl,
                "damage": int(base["damage"]) + d,
                "spen": int(base["spen"]) + s,
                "apen": int(base["apen"]) + a,
                "damageDelta": d, "spenDelta": s, "apenDelta": a,
                "class": row.get("class", "late_maturation_sensitivity"),
            })
        out[tl] = rows
    return out


def _task_rows(by_tl: dict[int, list[FidelityTask]]) -> list[dict[str, Any]]:
    rows = []
    for tl in range(1, 10):
        for t in by_tl[tl]:
            rows.append({"task_id": t.task_id, "tl": tl, "build_1": t.build_1_id, "build_2": t.build_2_id,
                         "design_weight": t.design_weight, "variants": t.variant_count})
    return rows


def build_plan(repo: Path, study_path: Path, outdir: Path | None = None) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("CP130 study validation failed: " + ", ".join(errors))
    catalog = BaselineCatalog(repo, doc["sourceMatrix"])
    raw, builds = enumerate_legal_builds(catalog)
    if raw != 14112 or len(builds) != 9427:
        raise ValueError(f"legal-build drift: {raw}/{len(builds)}")
    tasks = _same_tl_missile_tasks(builds, int(doc["pairingSeed"]))
    candidates = _candidate_rows(repo, doc)
    task_counts = {str(tl): len(tasks[tl]) for tl in range(1, 10)}
    variant_counts = {str(tl): sum(t.variant_count for t in tasks[tl]) for tl in range(1, 10)}
    candidate_counts = {str(tl): len(candidates[tl]) for tl in range(1, 10)}
    generated = sum(variant_counts[str(tl)] * candidate_counts[str(tl)] for tl in range(1, 10))
    substantive = generated * int(doc["trialsPerVariant"])
    summary = {
        "schemaVersion": RESULT_SCHEMA, "checkpoint": 130, "mode": "plan",
        "rawBuildCombinations": raw, "legalBuilds": len(builds),
        "sameTlMissilePairTasksByTl": task_counts,
        "sameTlMissileVariantsPerCandidateByTl": variant_counts,
        "candidateCountsByTl": candidate_counts,
        "generatedVariants": generated, "pipelineSmokeTrials": generated,
        "substantiveTrials": substantive,
        "technologyValuesChanged": False, "mixedTlShipsExecuted": False,
        "automaticPromotion": False, "failedGates": [],
    }
    exp = doc.get("expected", {})
    for key in ("rawBuildCombinations", "legalBuilds", "generatedVariants", "pipelineSmokeTrials", "substantiveTrials"):
        if key in exp and int(summary[key]) != int(exp[key]):
            summary["failedGates"].append(f"{key}:{summary[key]}!={exp[key]}")
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        _write_csv(outdir / "same_tl_missile_tasks.csv", _task_rows(tasks))
        _write_csv(outdir / "candidate_ledger.csv", [r for tl in range(1,10) for r in candidates[tl]])
        (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"doc": doc, "catalog": catalog, "builds": builds, "tasks": tasks, "candidates": candidates, "summary": summary}


def _candidate_overrides(c: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"profile": "missile_gp_warhead", "tl": c["tl"], "field": "damage", "value": c["damage"]},
        {"profile": "missile_gp_warhead", "tl": c["tl"], "field": "spen", "value": c["spen"]},
        {"profile": "missile_gp_warhead", "tl": c["tl"], "field": "apen", "value": c["apen"]},
    ]


def _weighted(rows: list[dict[str, Any]], field: str) -> float:
    tw = sum(float(r["design_weight"]) for r in rows)
    return sum(float(r["design_weight"]) * float(r[field]) for r in rows) / tw if tw else 0.0


def _direct_win(rows: list[dict[str, Any]], build_map: dict[str, BaselineBuild], direct_family: str) -> float:
    tw = 0.0; acc = 0.0
    for r in rows:
        b1 = build_map[r["build_1"]]; b2 = build_map[r["build_2"]]
        fams = {_family(b1), _family(b2)}
        if fams != {direct_family, "Missile"}:
            continue
        w = float(r["build_1_conditional_win_rate"])
        val = w if _family(b1) == direct_family else 1.0 - w
        wt = float(r["design_weight"]); tw += wt; acc += wt * val
    return acc / tw if tw else 0.0


def _pair_summary(pair_rows: list[dict[str, Any]], build_map: dict[str, BaselineBuild], c: dict[str, Any], accepted: dict[int, dict[str, str]]) -> dict[str, Any]:
    tl = int(c["tl"])
    mm = [r for r in pair_rows if _family(build_map[r["build_1"]]) == "Missile" and _family(build_map[r["build_2"]]) == "Missile"]
    gpmm = [r for r in mm if build_map[r["build_1"]].missile_payload == "GP" and build_map[r["build_2"]].missile_payload == "GP"]
    out = {
        "tl": tl, "candidate": c["id"], "candidate_class": c["class"],
        "gp_damage": c["damage"], "gp_spen": c["spen"], "gp_apen": c["apen"],
        "kinetic_mirror_mean_turns": float(accepted[tl]["kinetic_mirror_mean_turns"]),
        "energy_mirror_mean_turns": float(accepted[tl]["energy_mirror_mean_turns"]),
        "missile_mirror_mean_turns": _weighted(mm, "mean_turns"),
        "missile_mirror_unresolved_rate": _weighted(mm, "unresolved_rate"),
        "kinetic_vs_missile_conditional_win_rate": _direct_win(pair_rows, build_map, "Kinetic"),
        "energy_vs_missile_conditional_win_rate": _direct_win(pair_rows, build_map, "Energy"),
        "gp_mirror_mean_turns": _weighted(gpmm, "mean_turns"),
        "gp_mirror_unresolved_rate": _weighted(gpmm, "unresolved_rate"),
    }
    # GP-only cross-family comparisons.
    for fam, key in (("Kinetic", "kinetic"), ("Energy", "energy")):
        x=[]
        for r in pair_rows:
            b1=build_map[r["build_1"]]; b2=build_map[r["build_2"]]
            if {_family(b1),_family(b2)} != {fam,"Missile"}: continue
            mb = b1 if _family(b1)=="Missile" else b2
            if mb.missile_payload != "GP": continue
            x.append(r)
        out[f"{key}_vs_gp_conditional_win_rate"] = _direct_win(x, build_map, fam)
        out[f"{key}_vs_gp_unresolved_rate"] = _weighted(x, "unresolved_rate")
    # Single-main vs single-main GP diagnostic.
    for fam, key in (("Kinetic", "kinetic"), ("Energy", "energy")):
        x=[]
        for r in pair_rows:
            b1=build_map[r["build_1"]]; b2=build_map[r["build_2"]]
            if {_family(b1),_family(b2)} != {fam,"Missile"}: continue
            mb = b1 if _family(b1)=="Missile" else b2; db = b1 if _family(b1)==fam else b2
            if mb.missile_payload=="GP" and mb.main_count==1 and db.main_count==1:
                x.append(r)
        out[f"single_main_{key}_vs_gp_conditional_win_rate"] = _direct_win(x, build_map, fam)
        out[f"single_main_{key}_vs_gp_unresolved_rate"] = _weighted(x, "unresolved_rate")
        out[f"single_main_{key}_vs_gp_mean_turns"] = _weighted(x, "mean_turns")
    return out


def _context_rows(variant_rows: list[dict[str, str]], build_map: dict[str, BaselineBuild], c: dict[str, Any], flights_per_main: int) -> list[dict[str, Any]]:
    buckets: dict[tuple[str,str], dict[str,float]] = defaultdict(lambda: defaultdict(float))
    for r in variant_rows:
        ba=build_map[r["side_a_build"]]; bb=build_map[r["side_b_build"]]
        if (_family(ba)=="Missile") == (_family(bb)=="Missile"):
            continue
        mb, db = (ba,bb) if _family(ba)=="Missile" else (bb,ba)
        ms, ds = ("a","b") if _family(ba)=="Missile" else ("b","a")
        opp = _family(db)
        contexts = ["all", "pds" if db.pds_family else "no_pds", "shield" if db.shield else "no_shield"]
        if mb.missile_payload=="GP": contexts.append("gp_only")
        if mb.missile_payload=="GP" and mb.main_count==1 and db.main_count==1: contexts.append("single_main_gp")
        wt=float(r["base_design_weight"])*int(r["trials"])/4.0
        ca=float(r["conditional_win_rate_a"]); missile_win=ca if ms=="a" else 1-ca
        launches=float(r[f"mean_{ms}_missile_launches"]); cap=max(1, mb.main_count*flights_per_main)
        values={
            "weight":wt,"missile_win":missile_win,"unresolved":float(r["unresolved_rate"]),"turns":float(r["mean_turns"]),
            "launches":launches,"magazine_fraction":launches/cap,
            "terminal_arrivals":float(r[f"mean_{ds}_missile_terminal_arrivals"]),
            "missile_hits":float(r[f"mean_{ds}_missile_hits"]),
            "pds_attempts":float(r[f"mean_{ds}_pds_attempts"]),"pds_intercepts":float(r[f"mean_{ds}_pds_intercepts"]),
            "shield_absorbed":float(r[f"mean_{ds}_shield_absorbed"]),"armor_prevented":float(r[f"mean_{ds}_armor_prevented"]),
            "hull_damage":float(r[f"mean_{ds}_hull_damage"]),
            "firm_track_turns":float(r[f"mean_{ms}_firm_track_turns"]),
        }
        for ctx in contexts:
            b=buckets[(opp,ctx)]; b["weight"]+=wt
            for k,v in values.items():
                if k!="weight": b[k]+=wt*v
    out=[]
    for (opp,ctx),b in sorted(buckets.items()):
        w=b["weight"]
        row={"tl":c["tl"],"candidate":c["id"],"opponent_family":opp,"context":ctx,"weight":w}
        for k,v in b.items():
            if k!="weight": row[k]=v/w if w else 0.0
        out.append(row)
    return out


def _accepted_baseline(repo: Path, rel: str) -> dict[int, dict[str, str]]:
    rows=_read_rows(repo/rel)
    return {int(r["tl"]):r for r in rows}


def _run_candidate(repo: Path, doc: dict[str, Any], tasks: list[FidelityTask], c: dict[str, Any], root: Path, trials: int, jobs: int) -> tuple[list[dict[str,Any]], list[dict[str,str]], float]:
    cdir=root/f"tl{c['tl']}"/c["id"]
    cdir.mkdir(parents=True,exist_ok=True)
    derived=cdir/"derived_matrix.json"
    source=_override_matrix(repo,doc["sourceMatrix"],_candidate_overrides(c),derived)
    path,elapsed=_run_tasks(repo,source,int(doc["masterSeed"]),tasks,cdir,trials,jobs)
    vr=_read_rows(path); pr=_normalize_variant_rows(vr)
    return pr,vr,elapsed


def _run_all(repo: Path, study_path: Path, outdir: Path, trials: int, jobs: int, smoke: bool) -> dict[str, Any]:
    plan=build_plan(repo,study_path,outdir/"plan")
    doc=plan["doc"]; builds=plan["builds"]; build_map={b.id:b for b in builds}
    accepted=_accepted_baseline(repo,doc["acceptedCp129ChartBaseline"])
    summary_rows=[]; context=[]; lane=[]; errors=0; variants=0
    flights=int(load_json(repo/doc["sourceMatrix"])["profiles"]["missile_delivery"]["1"]["flights"])
    for tl in range(1,10):
        for c in plan["candidates"][tl]:
            pr,vr,elapsed=_run_candidate(repo,doc,plan["tasks"][tl],c,outdir/"candidates",trials,jobs)
            errors += sum(int(r["errors"]) for r in vr); variants += len(vr)
            summary_rows.append(_pair_summary(pr,build_map,c,accepted))
            context.extend(_context_rows(vr,build_map,c,flights))
            lane.append({"tl":tl,"candidate":c["id"],"variants":len(vr),"trials_per_variant":trials,"elapsed_seconds":elapsed,"trial_errors":sum(int(r["errors"]) for r in vr)})
            # Keep raw detail only for failed lanes. Successful detail is reproducible and would bloat the handoff.
            if not any(int(r["errors"]) for r in vr):
                (outdir/"candidates"/f"tl{tl}"/c["id"] / "variants.csv").unlink(missing_ok=True)
                (outdir/"candidates"/f"tl{tl}"/c["id"] / "derived_matrix.json").unlink(missing_ok=True)
    _write_csv(outdir/"family_plot_inputs.csv",summary_rows)
    _write_csv(outdir/"missile_context_telemetry.csv",context)
    _write_csv(outdir/"lane_summary.csv",lane)
    # Blocking accepted CP129 control replication is meaningful only at the accepted
    # 100-trial substantive depth. The one-trial smoke validates execution/schema only.
    replication=[]; failed=[]
    if trials == int(doc["trialsPerVariant"]):
        for r in summary_rows:
            if r["candidate"]!="control": continue
            old=accepted[int(r["tl"])]
            checks={
                "missile_mirror_mean_turns":float(old["missile_mirror_mean_turns"]),
                "missile_mirror_unresolved_rate":float(old["missile_mirror_unresolved_rate"]),
                "kinetic_vs_missile_conditional_win_rate":float(old["kinetic_vs_missile_conditional_win_rate"]),
                "energy_vs_missile_conditional_win_rate":float(old["energy_vs_missile_conditional_win_rate"]),
            }
            for metric,ov in checks.items():
                nv=float(r[metric]); delta=nv-ov
                replication.append({"tl":r["tl"],"metric":metric,"cp129":ov,"cp130_control":nv,"delta":delta})
                if abs(delta)>1e-12: failed.append(f"cp129-replication-tl{r['tl']}-{metric}:{delta}")
        _write_csv(outdir/"cp129_control_replication.csv",replication)
    expected=int(doc["expected"]["generatedVariants"])
    if variants!=expected: failed.append(f"variant-count:{variants}!={expected}")
    if errors: failed.append(f"trial-errors:{errors}")
    result={"schemaVersion":RESULT_SCHEMA,"checkpoint":130,"mode":"smoke" if smoke else "substantive","variants":variants,
            "trialsPerVariant":trials,"totalTrials":variants*trials,"trialErrors":errors,"candidateRows":len(summary_rows),
            "technologyValuesChanged":False,"mixedTlShipsExecuted":False,"automaticPromotion":False,"rawVariantDetailRetained":bool(errors),
            "failedGates":failed}
    (outdir/"analysis.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def run_missile_progression(repo: Path, study_path: Path, outdir: Path, *, mode: str, jobs: int=24) -> dict[str, Any]:
    if mode=="plan": return build_plan(repo,study_path,outdir)["summary"]
    doc=load_json(study_path)
    if mode=="smoke": return _run_all(repo,study_path,outdir,1,jobs,True)
    if mode=="run": return _run_all(repo,study_path,outdir,int(doc["trialsPerVariant"]),jobs,False)
    raise ValueError(f"unknown CP130 mode: {mode}")
