from __future__ import annotations

import csv
import io
import json
import shutil
import statistics
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from .baseline_foundation import BaselineCatalog, _build_to_ecology, enumerate_legal_builds
from .ecology import EcologyVariant
from .fidelity_attribution_analysis import (
    ALL_TELEMETRY_CONTRACT,
    FidelityTask,
    _plans_for_task,
    execute_streaming,
    generate_tasks,
)
from .canonical_combat import FULL_MAP_GEOMETRY, mirror_equivalent, run_trial_full_map
from .study import canonicalize_relocated_references, load_json
from .whole_ladder_analysis import _normalized_pair_row, _write_csv

SCHEMA = "star-cluster-cp127-main-subsystem-stabilization-v0.1"
RESULT_SCHEMA = "star-cluster-cp127-main-subsystem-stabilization-results-v0.1"
DEFAULT_STUDY = "docs/archive/testing/pre-cp165-active/cp127_main_subsystem_tl_stabilization_study_v0_1.json"


def validate_study(doc: dict[str, Any]) -> list[str]:
    doc = canonicalize_relocated_references(doc)
    errors: list[str] = []
    expected = {
        "schemaVersion": SCHEMA,
        "checkpoint": 127,
        "acceptedEvidenceCheckpoint": 126,
        "acceptedReferenceBaseline": 123,
        "acceptedImplementationBaseline": 122,
        "sourceMatrix": "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json",
        "shipTechnologyPolicy": "pure_same_tl_components_per_ship",
        "mixedTlShipsExecuted": False,
        "substantiveTrialsPerVariant": 100,
        "recommendedJobs": 24,
    }
    for k, v in expected.items():
        if doc.get(k) != v:
            errors.append(k)
    for k, v in {
        "legalBuilds": 9427,
        "finalBaselineTasks": 18646,
        "finalBaselineVariants": 74584,
        "tl5Tl6AblationSampleTasks": 120,
        "tl5Tl6AblationConditions": 9,
        "tl5Tl6AblationVariants": 4320,
        "tl8EnergySampleTasks": 120,
        "tl8EnergyConditions": 4,
        "tl8EnergyVariants": 7680,
        "generatedVariants": 86584,
        "pipelineSmokeTrials": 86584,
        "substantiveTrials": 8658400,
        "telemetryMetrics": 61,
    }.items():
        if int(doc.get("expected", {}).get(k, -1)) != v:
            errors.append(f"expected.{k}")
    if doc.get("automaticPromotion") is not False or doc.get("balanceValidated") is not False:
        errors.append("promotionBoundary")
    inv = doc.get("movementInvariants", {})
    if inv.get("stlStandardMove") != "Drive TL" or inv.get("operationalMissileMove") != "Missile Drive TL + 1":
        errors.append("movementInvariants")
    if doc.get("ftlStrategicLadder") != [1, 2, 3, 4, 4, 6, 7, 9, 12]:
        errors.append("ftlStrategicLadder")
    return errors


def _even_sample(tasks: list[FidelityTask], count: int) -> list[FidelityTask]:
    tasks = sorted(tasks, key=lambda x: x.task_id)
    if len(tasks) <= count:
        return tasks
    return [tasks[(i * len(tasks)) // count] for i in range(count)]


def _override_matrix(repo: Path, source: str, overrides: list[dict[str, Any]], path: Path) -> str:
    doc = load_json(repo / source)
    for o in overrides:
        row = doc["profiles"][o["profile"]][str(o["tl"])]
        row[o["field"]] = o["value"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return path.relative_to(repo).as_posix()


def _tasks_for_plan(builds: list, pairing_seed: int) -> tuple[list[FidelityTask], list[FidelityTask], list[FidelityTask], list[FidelityTask]]:
    all_tasks = generate_tasks(builds, pairing_seed)
    final = [t for t in all_tasks if t.group in {"adjacent_population", "matched_composition", "late_missile_geometry"}]
    tl56 = _even_sample([t for t in all_tasks if t.group == "matched_composition" and (t.tl_low, t.tl_high) == (5, 6)], 120)
    e8 = _even_sample([t for t in all_tasks if t.group == "energy_isolation" and t.tl_low == 8], 120)
    return all_tasks, final, tl56, e8


def _count_variants(tasks: list[FidelityTask]) -> int:
    return sum(t.variant_count for t in tasks)


def _numeric_change_rows(repo: Path) -> list[dict[str, Any]]:
    old = load_json(repo / "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json")
    new = load_json(repo / "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_4.json")
    rows = []
    for profile in sorted(new["profiles"]):
        for tl in range(1, 10):
            a, b = old["profiles"][profile][str(tl)], new["profiles"][profile][str(tl)]
            for field in sorted(set(a) | set(b)):
                av, bv = a.get(field), b.get(field)
                if isinstance(av, (int, float)) and not isinstance(av, bool) and isinstance(bv, (int, float)) and not isinstance(bv, bool) and av != bv:
                    rows.append({"profile": profile, "tl": tl, "field": field, "cp123_cp126_value": av, "cp127_candidate": bv, "delta": bv-av})
    return rows


def build_plan(repo: Path, study_path: Path, outdir: Path | None = None) -> dict[str, Any]:
    doc = load_json(study_path)
    errors = validate_study(doc)
    if errors:
        raise ValueError("CP127 study validation failed: " + ", ".join(errors))
    catalog = BaselineCatalog(repo, doc["sourceMatrix"])
    raw, builds = enumerate_legal_builds(catalog)
    if raw != 14112 or len(builds) != 9427:
        raise ValueError(f"legal-build drift: {raw}/{len(builds)}")
    all_tasks, final, tl56, e8 = _tasks_for_plan(builds, int(doc["pairingSeed"]))
    counts = {
        "finalBaselineTasks": len(final),
        "finalBaselineVariants": _count_variants(final),
        "tl5Tl6AblationSampleTasks": len(tl56),
        "tl5Tl6AblationVariants": _count_variants(tl56) * len(doc["tl5Tl6Ablations"]),
        "tl8EnergySampleTasks": len(e8),
        "tl8EnergyVariants": _count_variants(e8) * len(doc["tl8EnergyFactorial"]),
    }
    counts["generatedVariants"] = counts["finalBaselineVariants"] + counts["tl5Tl6AblationVariants"] + counts["tl8EnergyVariants"]
    failed = []
    for key, actual in counts.items():
        if int(doc["expected"].get(key, -1)) != int(actual):
            failed.append(f"{key}:{actual}!={doc['expected'].get(key)}")
    planned = counts["generatedVariants"] * int(doc["substantiveTrialsPerVariant"])
    if planned != int(doc["expected"]["substantiveTrials"]):
        failed.append(f"substantiveTrials:{planned}!={doc['expected']['substantiveTrials']}")
    changes = _numeric_change_rows(repo)
    if len(changes) != 9:
        failed.append(f"numeric-leaf-changes:{len(changes)}!=9")
    for tl in range(1, 10):
        if int(catalog.p("stl", tl)["move"]) != tl:
            failed.append(f"stl-move-tl{tl}")
        if int(catalog.p("missile_delivery", tl)["missileMove"]) != tl + 1:
            failed.append(f"missile-move-tl{tl}")
    if [int(catalog.p("ftl", tl)["strategicMove"]) for tl in range(1, 10)] != doc["ftlStrategicLadder"]:
        failed.append("ftl-ladder")
    e = catalog.p("energy_main", 8)
    if [e["lowDamage"], e["standardDamage"], e["highDamage"]] != [7, 10, 12]:
        failed.append("tl8-energy-damage")
    summary = {
        "schemaVersion": RESULT_SCHEMA,
        "checkpoint": 127,
        "mode": "plan",
        "rawBuildCombinations": raw,
        "legalBuilds": len(builds),
        **counts,
        "pipelineSmokeTrials": counts["generatedVariants"],
        "substantiveTrialsPerVariant": int(doc["substantiveTrialsPerVariant"]),
        "plannedSubstantiveTrials": planned,
        "telemetryMetrics": len(ALL_TELEMETRY_CONTRACT),
        "numericLeafChangesFromCp123": len(changes),
        "mixedTlShipsExecuted": False,
        "balanceValidated": False,
        "automaticPromotion": False,
        "failedGates": failed,
    }
    if outdir is not None:
        outdir.mkdir(parents=True, exist_ok=True)
        _write_csv(outdir / "numerical_change_ledger.csv", changes)
        _write_csv(outdir / "final_baseline_tasks.csv", [t.__dict__ if hasattr(t, "__dict__") else {k:getattr(t,k) for k in t.__dataclass_fields__} for t in final])
        _write_csv(outdir / "tl5_tl6_sample_tasks.csv", [t.__dict__ if hasattr(t, "__dict__") else {k:getattr(t,k) for k in t.__dataclass_fields__} for t in tl56])
        _write_csv(outdir / "tl8_energy_sample_tasks.csv", [t.__dict__ if hasattr(t, "__dict__") else {k:getattr(t,k) for k in t.__dataclass_fields__} for t in e8])
        (outdir / "analysis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {"doc": doc, "catalog": catalog, "builds": builds, "allTasks": all_tasks, "finalTasks": final, "tl56Tasks": tl56, "energyTasks": e8, "summary": summary}


def run_symmetry_gate(repo: Path, study_path: Path, outdir: Path) -> dict[str, Any]:
    plan = build_plan(repo, study_path, None)
    doc, catalog, builds = plan["doc"], plan["catalog"], plan["builds"]
    by_tl = {tl: sorted([b for b in builds if b.tl == tl], key=lambda b:b.id) for tl in range(1, 10)}
    comparisons = 0; mismatches = []
    trials = int(doc["symmetryGate"]["trialsPerCase"]); cases_per_tl = int(doc["symmetryGate"]["casesPerTl"])
    for tl in range(1, 10):
        group = by_tl[tl]; pairs=[]
        for i in range(cases_per_tl-1):
            left = group[(i+1)*len(group)//(cases_per_tl+1)]
            right = group[(cases_per_tl-i)*len(group)//(cases_per_tl+2)]
            if left.id == right.id: right = group[(group.index(right)+1)%len(group)]
            pairs.append((left,right,f"distinct-{i+1}"))
        same=group[len(group)//2]; pairs.append((same,same,"identical-build"))
        for case_index,(left,right,label) in enumerate(pairs):
            for first in ("SideAFirst","SideBFirst"):
                mirrored="SideBFirst" if first=="SideAFirst" else "SideAFirst"
                scenario=f"cp127-symmetry-tl{tl}-{case_index}-{label}"
                e1=_build_to_ecology(left,"cp127-symmetry"); e2=_build_to_ecology(right,"cp127-symmetry")
                for trial in range(trials):
                    v1=EcologyVariant(f"sym-{tl}-{case_index}-a",tl,e1,e2,first,geometry=FULL_MAP_GEOMETRY,population="cp127_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship1",physical_id_b=scenario+":ship2")
                    v2=EcologyVariant(f"sym-{tl}-{case_index}-b",tl,e2,e1,mirrored,geometry=FULL_MAP_GEOMETRY,population="cp127_symmetry",scenario_group=scenario,physical_id_a=scenario+":ship2",physical_id_b=scenario+":ship1")
                    r1=run_trial_full_map(catalog.matrix,v1,int(doc["masterSeed"]),trial)
                    r2=run_trial_full_map(catalog.matrix,v2,int(doc["masterSeed"]),trial)
                    comparisons += 1
                    if not mirror_equivalent(r1,r2):
                        mismatches.append({"tl":tl,"case":label,"first":first,"trial":trial,"build1":left.id,"build2":right.id})
                        if len(mismatches) >= 20: break
                if len(mismatches) >= 20: break
            if len(mismatches) >= 20: break
        if len(mismatches) >= 20: break
    expected=9*cases_per_tl*2*trials
    failed=[]
    if comparisons != expected: failed.append(f"comparisons:{comparisons}!={expected}")
    if mismatches: failed.append(f"mirror-mismatches:{len(mismatches)}")
    outdir.mkdir(parents=True,exist_ok=True)
    _write_csv(outdir/"symmetry_mismatches.csv",mismatches,["tl","case","first","trial","build1","build2"] if not mismatches else None)
    result={"schemaVersion":RESULT_SCHEMA,"checkpoint":127,"mode":"symmetry_gate","comparisons":comparisons,"combatExecutions":comparisons*2,"mismatches":len(mismatches),"failedGates":failed}
    (outdir/"analysis.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def _run_condition(repo: Path, source_matrix: str, master_seed: int, tasks: list[FidelityTask], overrides: list[dict[str, Any]], outdir: Path, trials: int, jobs: int) -> tuple[Path, float]:
    outdir.mkdir(parents=True, exist_ok=True)
    matrix_path = outdir / "derived_matrix.json"
    rel = _override_matrix(repo, source_matrix, overrides, matrix_path)
    doc = {"sourceMatrix": rel, "masterSeed": master_seed}
    csv_path = outdir / "variants.csv"
    elapsed = execute_streaming(repo, doc, tasks, csv_path, trials, jobs)
    return csv_path, elapsed


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _normalize_variant_rows(rows: list[dict[str,str]]) -> list[dict[str,Any]]:
    out=[]; current=""; buf=[]
    def finish():
        nonlocal buf
        if buf:
            pr=_normalized_pair_row(buf); pr["study_group"]=buf[0]["study_group"]; pr["condition"]=buf[0]["condition"]; pr["task_id"]=buf[0]["task_id"]; out.append(pr); buf=[]
    for r in rows:
        if current and r["pairing_id"] != current: finish()
        current=r["pairing_id"];buf.append(r)
    finish(); return out


def _weighted_high(rows: list[dict[str,Any]]) -> dict[str,float]:
    tw=sum(float(r["design_weight"]) for r in rows)
    if tw<=0:return {"higher_tl_conditional_win_rate":0.0,"unresolved_rate":0.0,"mean_turns":0.0}
    return {
        "higher_tl_conditional_win_rate":sum(float(r["design_weight"])*(1-float(r["build_1_conditional_win_rate"])) for r in rows)/tw,
        "unresolved_rate":sum(float(r["design_weight"])*float(r["unresolved_rate"]) for r in rows)/tw,
        "mean_turns":sum(float(r["design_weight"])*float(r["mean_turns"]) for r in rows)/tw,
    }


def _summary_by_transition(pair_rows: list[dict[str,Any]], group: str) -> list[dict[str,Any]]:
    out=[]
    for lo in range(1,9):
        rr=[r for r in pair_rows if r["study_group"]==group and int(r["tl_1"])==lo and int(r["tl_2"])==lo+1]
        s=_weighted_high(rr); s.update({"low_tl":lo,"high_tl":lo+1,"base_pairings":len(rr)}); out.append(s)
    return out


def _perspective_attacker_win(rows: list[dict[str,str]]) -> float:
    vals=[]
    for r in rows:
        ca=float(r["conditional_win_rate_a"])
        vals.append(ca if r["orientation"]=="forward" else 1-ca)
    return sum(vals)/len(vals) if vals else 0.0


def _load_cp126_csv(repo: Path, archive_rel: str, rel: str) -> list[dict[str,str]]:
    with zipfile.ZipFile(repo/archive_rel) as z:
        data=z.read("checkpoint-126/fidelity-era-attribution-study/"+rel).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(data)))


def _analyze_outputs(repo: Path, doc: dict[str,Any], root: Path, trials: int, expected_variants: int) -> dict[str,Any]:
    final_rows=_read_rows(root/"final-baseline"/"variants.csv")
    pairs=_normalize_variant_rows(final_rows)
    adj=_summary_by_transition(pairs,"adjacent_population"); matched=_summary_by_transition(pairs,"matched_composition")
    _write_csv(root/"adjacent_population_summary.csv",adj); _write_csv(root/"matched_composition_summary.csv",matched)

    late=[]
    for tl in (8,9):
        rr=[r for r in pairs if r["study_group"]=="late_missile_geometry" and int(r["tl_1"])==tl]
        tw=sum(float(x["design_weight"]) for x in rr)
        late.append({"tl":tl,"base_pairings":len(rr),"unresolved_rate":sum(float(x["design_weight"])*float(x["unresolved_rate"]) for x in rr)/tw,"mean_turns":sum(float(x["design_weight"])*float(x["mean_turns"]) for x in rr)/tw,"mean_mover_order_swing":sum(float(x["design_weight"])*float(x["mover_order_swing"]) for x in rr)/tw})
    _write_csv(root/"late_missile_summary.csv",late)

    # CP126 direct controls.
    old_adj=_load_cp126_csv(repo,doc["cp126NativeArchive"],"adjacent_population_summary.csv")
    old_mat=_load_cp126_csv(repo,doc["cp126NativeArchive"],"matched_composition_summary.csv")
    comp=[]
    for label,newrows,oldrows in [("adjacent_population",adj,old_adj),("matched_composition",matched,old_mat)]:
        oldmap={(int(x["low_tl"]),int(x["high_tl"])):x for x in oldrows}
        for n in newrows:
            o=oldmap[(n["low_tl"],n["high_tl"])]
            comp.append({"lane":label,"low_tl":n["low_tl"],"high_tl":n["high_tl"],"cp126_higher_tl_win_rate":float(o["higher_tl_conditional_win_rate"]),"cp127_higher_tl_win_rate":n["higher_tl_conditional_win_rate"],"delta_pp":100*(n["higher_tl_conditional_win_rate"]-float(o["higher_tl_conditional_win_rate"])),"cp126_unresolved_rate":float(o["unresolved_rate"]),"cp127_unresolved_rate":n["unresolved_rate"]})
    _write_csv(root/"cp126_transition_comparison.csv",comp)

    # TL5->6 ablation. Candidate rows come from the final-baseline matched sample IDs.
    sample_ids={t["task_id"] for t in csv.DictReader((root/"plan"/"tl5_tl6_sample_tasks.csv").open(newline="",encoding="utf-8"))}
    base_pairs=[r for r in pairs if r["study_group"]=="matched_composition" and r["task_id"] in sample_ids]
    base_variants=[r for r in final_rows if r["study_group"]=="matched_composition" and r["task_id"] in sample_ids]
    ablation=[]
    def summarize_ablation(name:str, variant_rows:list[dict[str,str]], pair_rows_local:list[dict[str,Any]]):
        s=_weighted_high(pair_rows_local)
        row={"condition":name,"all_higher_tl_win_rate":s["higher_tl_conditional_win_rate"],"unresolved_rate":s["unresolved_rate"],"mean_turns":s["mean_turns"]}
        for fam in ("Kinetic","Energy","Missile"):
            vals=[]
            for vr in variant_rows:
                high_side="a" if int(vr["side_a_tl"])==6 else "b"
                high_fam=vr[f"side_{high_side}_weapon_family"]
                if high_fam!=fam: continue
                ca=float(vr["conditional_win_rate_a"]); vals.append(ca if high_side=="a" else 1-ca)
            row[f"{fam.lower()}_higher_tl_win_rate"]=sum(vals)/len(vals) if vals else 0.0
        return row
    candidate=summarize_ablation("candidate",base_variants,base_pairs); ablation.append(candidate)
    for cond in doc["tl5Tl6Ablations"]:
        vr=_read_rows(root/"tl5-tl6-ablation"/cond["id"]/"variants.csv"); pr=_normalize_variant_rows(vr)
        ablation.append(summarize_ablation(cond["id"],vr,pr))
    for r in ablation:
        r["delta_vs_candidate_pp"]=100*(r["all_higher_tl_win_rate"]-candidate["all_higher_tl_win_rate"])
    _write_csv(root/"tl5_tl6_ablation_summary.csv",ablation)

    # TL8 Energy 2x2 factorial.
    energy=[]
    for cond in doc["tl8EnergyFactorial"]:
        rows=_read_rows(root/"tl8-energy-factorial"/cond["id"]/"variants.csv")
        vals={}
        for c in ("Energy_noShield","Energy_Shield","Kinetic_noShield","Kinetic_Shield"):
            vals[c]=_perspective_attacker_win([r for r in rows if r["condition"]==c])
        energy.append({"condition":cond["id"],**{k+"_win_rate":v for k,v in vals.items()},"energy_minus_kinetic_no_shield_pp":100*(vals["Energy_noShield"]-vals["Kinetic_noShield"]),"energy_minus_kinetic_shield_pp":100*(vals["Energy_Shield"]-vals["Kinetic_Shield"])})
    _write_csv(root/"tl8_energy_factorial_summary.csv",energy)

    variant_files=[root/"final-baseline"/"variants.csv"]+[root/"tl5-tl6-ablation"/c["id"]/"variants.csv" for c in doc["tl5Tl6Ablations"]]+[root/"tl8-energy-factorial"/c["id"]/"variants.csv" for c in doc["tl8EnergyFactorial"]]
    variants=0;errors=0
    for p in variant_files:
        for r in _read_rows(p): variants+=1;errors+=int(r["errors"])
    failed=[]
    if variants!=expected_variants: failed.append(f"variant-count:{variants}!={expected_variants}")
    if errors: failed.append(f"trial-errors:{errors}")
    result={"schemaVersion":RESULT_SCHEMA,"checkpoint":127,"mode":"substantive" if trials>1 else "smoke","variants":variants,"trialsPerVariant":trials,"totalTrials":variants*trials,"trialErrors":errors,"telemetryMetrics":len(ALL_TELEMETRY_CONTRACT),"mixedTlShipsExecuted":False,"balanceValidated":False,"automaticPromotion":False,"failedGates":failed,"reviewSignals":{"transitionComparison":comp,"tl5Tl6Ablation":ablation,"tl8EnergyFactorial":energy,"lateMissile":late}}
    (root/"analysis.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def _run_all(repo: Path, study_path: Path, outdir: Path, trials: int, jobs: int) -> dict[str,Any]:
    plan=build_plan(repo,study_path,outdir/"plan");doc=plan["doc"]
    elapsed={}
    p,e=_run_condition(repo,doc["sourceMatrix"],int(doc["masterSeed"]),plan["finalTasks"],[],outdir/"final-baseline",trials,jobs); elapsed["finalBaseline"]=e
    for cond in doc["tl5Tl6Ablations"]:
        _,e=_run_condition(repo,doc["sourceMatrix"],int(doc["masterSeed"]),plan["tl56Tasks"],cond["overrides"],outdir/"tl5-tl6-ablation"/cond["id"],trials,jobs);elapsed["tl5_"+cond["id"]]=e
    for cond in doc["tl8EnergyFactorial"]:
        _,e=_run_condition(repo,doc["sourceMatrix"],int(doc["masterSeed"]),plan["energyTasks"],cond["overrides"],outdir/"tl8-energy-factorial"/cond["id"],trials,jobs);elapsed["energy_"+cond["id"]]=e
    result=_analyze_outputs(repo,doc,outdir,trials,int(doc["expected"]["generatedVariants"]));result["elapsedSecondsByLane"]=elapsed
    (outdir/"analysis.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return result


def run_main_subsystem_stabilization(repo: Path, study_path: Path, outdir: Path, *, mode: str, trials: int | None=None, jobs: int=24) -> dict[str,Any]:
    if mode=="plan": return build_plan(repo,study_path,outdir)["summary"]
    if mode=="symmetry": return run_symmetry_gate(repo,study_path,outdir)
    doc=load_json(study_path)
    if mode=="smoke": return _run_all(repo,study_path,outdir,1,jobs)
    if mode=="run": return _run_all(repo,study_path,outdir,int(trials if trials is not None else doc["substantiveTrialsPerVariant"]),jobs)
    raise ValueError(f"unknown CP127 mode: {mode}")
