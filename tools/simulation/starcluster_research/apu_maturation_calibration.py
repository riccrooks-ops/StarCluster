from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .ecology import CandidateMatrix, EcologyBuild, EcologyVariant
from .reactor_aux_power_calibration import (
    _base_cruiser_space,
    _write_csv,
    _write_json,
    main_supply,
    max_stack,
    resolved_tier_count,
    select_carrier,
)
from .reactor_tp_equilibrium import (
    COMBAT_DOCTRINE,
    DOCTRINES,
    PowerLoadout,
    _allocate,
    _pf4_aux_registry,
    _turn_requests,
    demand_states,
    enumerate_loadouts,
)
from .research_execution_baseline_pf4 import load_research_execution_baseline_pf4
from .rng import XorShift64, derive_seed
from .study import load_json

SCHEMA = "star-cluster-cp163-apu-maturation-stacking-resilience-v0.1"
STACK_TIERS: tuple[int | str, ...] = (1, 2, 3, "MAX")


def trajectories(doc: dict[str, Any]) -> dict[str, list[int]]:
    return {str(x["id"]): [int(v) for v in x["operationalTpByTl"]] for x in doc["apuTrajectories"]}


def apu_tp_for_trajectory(doc: dict[str, Any], trajectory_id: str, tl: int) -> int:
    return trajectories(doc)[trajectory_id][tl - 1]


def candidate_tps_for_tl(doc: dict[str, Any], tl: int) -> list[int]:
    vals = {row[tl - 1] for row in trajectories(doc).values()}
    for probe in doc.get("latePlus3BoundaryProbes", []):
        if int(probe["tl"]) == tl:
            vals.add(int(probe["apuTp"]))
    return sorted(int(x) for x in vals)


def validate_study(doc: dict[str, Any]) -> list[str]:
    e: list[str] = []
    if doc.get("schemaVersion") != SCHEMA:
        e.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 163:
        e.append("checkpoint")
    if int(doc.get("acceptedBaselineCheckpoint", 0)) != 162 or doc.get("pendingFinalizationBaselineId") != "CP160-PF4":
        e.append("baseline")
    if int(doc.get("mainReactorSpace", 0)) != 6 or doc.get("mainReactorOffsetsFromPf4") != [-1, 0, 1]:
        e.append("mainReactor")
    if int(doc.get("apuSpace", 0)) != 2:
        e.append("apuSpace")
    expected = {
        "APU_FLAT_1": [1,1,1,1,1,1,1,1,1],
        "APU_MATURE_TL5": [1,1,1,1,2,2,2,2,2],
        "APU_MATURE_TL6": [1,1,1,1,1,2,2,2,2],
        "APU_MATURE_TL7": [1,1,1,1,1,1,2,2,2],
        "APU_MATURE_TL8": [1,1,1,1,1,1,1,2,2],
    }
    if trajectories(doc) != expected:
        e.append("apuTrajectories")
    probes = {(int(x["tl"]), int(x["apuTp"])) for x in doc.get("latePlus3BoundaryProbes", [])}
    if probes != {(8,3),(9,3)}:
        e.append("lateBoundary")
    sp = doc.get("stackingPolicy", {})
    if sp.get("installationCountCapImposed") is not False or sp.get("screenEveryLegalCountStatic") is not True or sp.get("stochasticAndCombatTiers") != [1,2,3,"MAX"]:
        e.append("stackingPolicy")
    rp = doc.get("resiliencePolicy", {})
    if int(rp.get("apuFlexibleTpWhenDegraded", -1)) != 0 or rp.get("singleUnitFailureIsIndependent") is not True or rp.get("fullIntegratedComponentDamageExecutionDeferred") is not True:
        e.append("resiliencePolicy")
    if doc.get("stochasticDoctrines") != list(DOCTRINES):
        e.append("doctrines")
    if int(doc.get("stochasticTurnSamplesPerVariant", 0)) != 5000 or int(doc.get("combatTrialsPerCell", 0)) != 2000:
        e.append("scale")
    naming = doc.get("namingPolicy", {})
    if naming.get("userFacingName") != "Auxiliary Power Unit" or naming.get("abbreviation") != "APU" or naming.get("cp162LegacyResearchName") != "Auxiliary Reactor":
        e.append("namingPolicy")
    p = doc.get("interpretationPolicy", {})
    if any(p.get(k) is not False for k in ("automaticPromotion", "productionAuthorityChanged", "conceptChanged", "tuningAllowed")):
        e.append("promotionBoundary")
    required_true = (
        "noTargetWinRate", "noUniversalUtilizationTarget", "balanceMeansDistinctViableChoices",
        "mainReactorSixSpaceFrozenForThisPass", "apuTwoSpaceFrozenForThisPass",
        "mainReactorLocalOffsetsRetained", "unrestrictedApuStackingMustRemainExplicitlyScreened",
        "countCapMayBeRecommendedOnlyIfEconomicsOrResilienceFailToBoundStacking",
        "apuMustRemainGranularSupplementNotMainReactorReplacement", "maturationTimingMustBeEvidenceDriven",
        "playerBaseCruiserAndBroadLegalEnvelopeBothRetained",
    )
    if not all(p.get(k) is True for k in required_true):
        e.append("interpretationPolicy")
    return e


def _tier_count(rows: list[PowerLoadout], tier: int | str) -> int:
    return resolved_tier_count(rows, 2, tier)


def static_analysis(repo: Path, study_path: Path, out: Path) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("CP163 study invalid: " + ", ".join(errs))
    m = load_research_execution_baseline_pf4(repo)
    all_rows = enumerate_loadouts(m, reactor_space=6)
    rows = [x for x in all_rows if x.reactor_count == 1]
    states = ("core", "routine", "offense", "defense", "recovery", "full")

    ledger: list[dict[str, Any]] = []
    labels = {str(x["id"]): str(x["label"]) for x in doc["apuTrajectories"]}
    for tid, vals in trajectories(doc).items():
        first_two = next((i + 1 for i, v in enumerate(vals) if v >= 2), None)
        for tl, tp in enumerate(vals, 1):
            ledger.append({"trajectory_id": tid, "trajectory_label": labels[tid], "tl": tl, "apu_space": 2, "apu_tp": tp, "first_tl_at_plus2": first_two or "NONE"})
    _write_csv(out / "apu_trajectory_ledger.csv", ledger)

    density: list[dict[str, Any]] = []
    for tl in range(1, 10):
        main_tp = int(m.p("reactor", tl)["operationalTp"])
        for tp in candidate_tps_for_tl(doc, tl):
            copies = (main_tp + tp - 1) // tp
            density.append({
                "tl": tl, "apu_space": 2, "apu_tp": tp, "tp_per_space": tp / 2,
                "pf4_main_tp": main_tp, "copies_to_meet_or_exceed_one_main": copies,
                "space_to_meet_or_exceed_one_main": copies * 2,
                "matches_main_with_less_than_6_space": int(copies * 2 < 6),
                "matches_main_with_at_most_6_space": int(copies * 2 <= 6),
                "three_apu_space": 6, "three_apu_tp": 3 * tp,
                "three_apu_tp_as_fraction_of_main": (3 * tp) / main_tp,
            })
    _write_csv(out / "apu_power_density_by_tl.csv", density)

    base_rows: list[dict[str, Any]] = []
    for tl in range(1, 10):
        cap = int(m.p("hull", tl)["capacity"])
        one = _base_cruiser_space(m, tl, reactors=1, mains=1)
        two_r = _base_cruiser_space(m, tl, reactors=2, mains=1)
        two_m = _base_cruiser_space(m, tl, reactors=1, mains=2)
        base_rows.append({
            "tl": tl, "capacity": cap, "base_cruiser_space": one, "base_cruiser_free_space": cap - one,
            "second_main_reactor_space": two_r, "second_main_reactor_fits": int(two_r <= cap),
            "second_main_weapon_space": two_m, "second_main_weapon_fits": int(two_m <= cap),
            "apu_space_each": 2, "max_apu_copies_on_intact_base_cruiser": max(0, (cap - one) // 2),
        })
    _write_csv(out / "player_base_cruiser_fit.csv", base_rows)

    agg: dict[tuple[int,int,int,int], dict[str, Any]] = {}
    for l in rows:
        ds = demand_states(m, l)
        for tp in candidate_tps_for_tl(doc, l.tl):
            mx = max_stack(l, 2)
            for n in range(mx + 1):
                for off in doc["mainReactorOffsetsFromPf4"]:
                    supply = main_supply(m, l.tl, int(off)) + n * tp
                    key = (l.tl, tp, n, int(off))
                    a = agg.setdefault(key, {
                        "tl": l.tl, "apu_space": 2, "apu_tp": tp, "apu_count": n, "main_offset": int(off),
                        "eligible_architectures": 0, "max_carrier_stack_observed": 0,
                        **{f"supports_{st}": 0 for st in states},
                    })
                    a["eligible_architectures"] += 1
                    a["max_carrier_stack_observed"] = max(int(a["max_carrier_stack_observed"]), mx)
                    for st in states:
                        a[f"supports_{st}"] += int(supply >= ds[st])
    support: list[dict[str, Any]] = []
    for _, a in sorted(agg.items()):
        denom = max(1, int(a["eligible_architectures"]))
        r = dict(a)
        for st in states:
            r[f"support_rate_{st}"] = a[f"supports_{st}"] / denom
        r["total_apu_space"] = 2 * int(a["apu_count"])
        r["total_apu_tp"] = int(a["apu_tp"]) * int(a["apu_count"])
        r["effective_supply"] = main_supply(m, int(a["tl"]), int(a["main_offset"])) + r["total_apu_tp"]
        support.append(r)
    _write_csv(out / "legal_apu_stack_support.csv", support)

    # Structural resilience: no probability assumptions. Losing one APU removes only that unit's flexible TP.
    resilience: list[dict[str, Any]] = []
    for tl in range(1, 10):
        tlrows = [x for x in rows if x.tl == tl]
        mx = max((max_stack(x, 2) for x in tlrows), default=0)
        main_tp = int(m.p("reactor", tl)["operationalTp"])
        for tp in candidate_tps_for_tl(doc, tl):
            for n in range(1, mx + 1):
                for failed in range(0, n + 1):
                    retained = (n - failed) * tp
                    resilience.append({
                        "tl": tl, "apu_tp": tp, "apu_count": n, "apu_space": 2 * n,
                        "failed_apu_units": failed, "initial_apu_tp": n * tp, "retained_apu_tp": retained,
                        "apu_tp_lost": failed * tp, "retained_fraction": retained / max(1, n * tp),
                        "single_unit_loss_tp": tp, "pf4_main_tp": main_tp,
                        "single_apu_loss_as_fraction_of_main": tp / main_tp,
                        "equal_six_space_stack": int(n == 3),
                        "six_space_stack_tp_fraction_of_main": ((3 * tp) / main_tp) if n == 3 else "",
                    })
    _write_csv(out / "apu_component_failure_surface.csv", resilience)

    carriers: list[dict[str, Any]] = []
    for tl in range(1, 10):
        tlrows = [x for x in rows if x.tl == tl]
        for tp in candidate_tps_for_tl(doc, tl):
            for tier in STACK_TIERS:
                cnt = _tier_count(tlrows, tier)
                if cnt <= 0:
                    continue
                l = select_carrier(m, rows, tl=tl, space_each=2, count=cnt)
                if l is None:
                    continue
                ds = demand_states(m, l)
                carriers.append({
                    "tl": tl, "apu_tp": tp, "stack_tier": tier, "apu_count": cnt,
                    "carrier_id": l.id, "weapon": l.weapon, "used_space_before_apu": l.used_space,
                    "free_space_before_apu": l.free_space, "used_space_after_apu": l.used_space + cnt * 2,
                    "demand_full": ds["full"], "demand_offense": ds["offense"], "demand_defense": ds["defense"],
                })
    _write_csv(out / "apu_stack_carriers.csv", carriers)

    summary = {
        "mode": "static", "passed": True, "legalPoweredArchitectures": len(all_rows),
        "oneMainReactorArchitectures": len(rows), "uniqueTlLocalApuPoints": sum(len(candidate_tps_for_tl(doc, tl)) for tl in range(1,10)),
        "trajectoryRows": len(ledger), "densityRows": len(density), "baseCruiserRows": len(base_rows),
        "legalStackSupportRows": len(support), "resilienceRows": len(resilience), "carrierRows": len(carriers),
        "installationCountCapImposed": False, "automaticPromotion": False, "tuningAllowed": False,
    }
    _write_json(out / "summary.json", summary)
    return summary


def _stoch_one(repo_s: str, doc: dict[str, Any], l: PowerLoadout, apu_tp: int, tier: int | str, count: int, main_offset: int, doctrine: str):
    repo = Path(repo_s)
    m = load_research_execution_baseline_pf4(repo)
    samples = int(doc["stochasticTurnSamplesPerVariant"])
    seed = derive_seed(int(doc["masterSeed"]), "cp163-stochastic", l.id, apu_tp, str(tier), count, main_offset, doctrine)
    rng = XorShift64(seed)
    supply = main_supply(m, l.tl, main_offset) + count * apu_tp
    hist = Counter()
    short = denied = 0
    group_req = Counter()
    group_fund = Counter()
    for _ in range(samples):
        req = _turn_requests(m, l, doctrine, rng)
        d = sum(x.cost for x in req)
        hist[d] += 1
        a = _allocate(req, supply, doctrine)
        short += int(a["denied_tp"] > 0)
        denied += a["denied_tp"]
        for x in req:
            group_req[x.group] += 1
        for g, n in a["funded"].items():
            group_fund[g] += n
    row = {
        "tl": l.tl, "carrier_id": l.id, "weapon": l.weapon, "apu_space_each": 2, "apu_tp": apu_tp,
        "stack_tier": tier, "apu_count": count, "total_apu_space": 2 * count, "total_apu_tp": apu_tp * count,
        "main_offset": main_offset, "main_supply": main_supply(m, l.tl, main_offset), "total_supply": supply,
        "doctrine": doctrine, "samples": samples, "mean_demand": sum(k*v for k,v in hist.items()) / samples,
        "shortfall_rate": short / samples, "mean_denied_tp": denied / samples,
    }
    alloc = []
    for g in sorted(group_req):
        alloc.append({
            **{k: row[k] for k in ("tl","carrier_id","weapon","apu_tp","stack_tier","apu_count","main_offset","doctrine","total_supply")},
            "group": g, "requests": group_req[g], "funded": group_fund[g], "funding_rate": group_fund[g] / max(1, group_req[g]),
        })
    return row, alloc


def _stoch_unpack(x):
    return _stoch_one(*x)


def _trajectory_stochastic(rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tid in trajectories(doc):
        for tier in STACK_TIERS:
            for off in doc["mainReactorOffsetsFromPf4"]:
                rr = [r for r in rows if str(r["stack_tier"]) == str(tier) and int(r["main_offset"]) == int(off) and int(r["apu_tp"]) == apu_tp_for_trajectory(doc, tid, int(r["tl"]))]
                if not rr:
                    continue
                out.append({
                    "trajectory_id": tid, "stack_tier": tier, "main_offset": int(off), "variants": len(rr),
                    "mean_shortfall_rate": statistics.fmean(float(r["shortfall_rate"]) for r in rr),
                    "mean_denied_tp": statistics.fmean(float(r["mean_denied_tp"]) for r in rr),
                    "mean_total_supply": statistics.fmean(float(r["total_supply"]) for r in rr),
                })
    return out


def run_stochastic(repo: Path, study_path: Path, static_dir: Path, out: Path, jobs: int = 24) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("CP163 study invalid: " + ", ".join(errs))
    m = load_research_execution_baseline_pf4(repo)
    rows = [x for x in enumerate_loadouts(m, reactor_space=6) if x.reactor_count == 1]
    tasks = []
    for tl in range(1, 10):
        tlrows = [x for x in rows if x.tl == tl]
        for tp in candidate_tps_for_tl(doc, tl):
            for tier in STACK_TIERS:
                cnt = _tier_count(tlrows, tier)
                if cnt <= 0:
                    continue
                l = select_carrier(m, rows, tl=tl, space_each=2, count=cnt)
                if l is None:
                    continue
                for off in doc["mainReactorOffsetsFromPf4"]:
                    for doctrine in doc["stochasticDoctrines"]:
                        tasks.append((str(repo), doc, l, tp, tier, cnt, int(off), doctrine))
    if jobs <= 1:
        res = [_stoch_unpack(x) for x in tasks]
    else:
        ctx = get_context("spawn" if os.name == "nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(jobs, len(tasks)), mp_context=ctx) as ex:
            res = list(ex.map(_stoch_unpack, tasks, chunksize=1))
    rows_out = [x[0] for x in res]
    alloc = [z for x in res for z in x[1]]
    rows_out.sort(key=lambda r: (r["tl"], r["apu_tp"], str(r["stack_tier"]), r["main_offset"], r["doctrine"]))
    _write_csv(out / "stochastic_apu_response.csv", rows_out)
    _write_csv(out / "allocation_outcomes.csv", alloc)
    groups = defaultdict(list)
    for r in rows_out:
        groups[(r["tl"], r["apu_tp"], str(r["stack_tier"]), r["main_offset"])].append(r)
    sums = []
    for k, rr in sorted(groups.items(), key=lambda x: (x[0][0],x[0][1],x[0][2],x[0][3])):
        sums.append({
            "tl": k[0], "apu_tp": k[1], "stack_tier": k[2], "main_offset": k[3], "variants": len(rr),
            "mean_shortfall_rate": statistics.fmean(float(r["shortfall_rate"]) for r in rr),
            "mean_denied_tp": statistics.fmean(float(r["mean_denied_tp"]) for r in rr),
            "mean_total_supply": statistics.fmean(float(r["total_supply"]) for r in rr),
        })
    _write_csv(out / "stochastic_apu_summary_by_tl.csv", sums)
    _write_csv(out / "trajectory_stochastic_summary.csv", _trajectory_stochastic(rows_out, doc))
    summary = {
        "mode": "stochastic", "passed": True, "variants": len(rows_out),
        "samplesPerVariant": int(doc["stochasticTurnSamplesPerVariant"]),
        "turnSamples": len(rows_out) * int(doc["stochasticTurnSamplesPerVariant"]),
        "allocationRows": len(alloc), "automaticPromotion": False, "tuningAllowed": False,
    }
    _write_json(out / "summary.json", summary)
    return summary


def _to_ecology(m: CandidateMatrix, l: PowerLoadout, ids: dict[tuple[str,int],str], *, apu_tp: int, apu_count: int, label: str) -> EcologyBuild:
    aux = []
    if l.hardener and ("shieldHardener", l.tl) in ids:
        aux.append(ids[("shieldHardener", l.tl)])
    if l.energized and ("energizedArmor", l.tl) in ids:
        aux.append(ids[("energizedArmor", l.tl)])
    if l.stabilizer and ("fieldStabilizer", l.tl) in ids:
        aux.append(ids[("fieldStabilizer", l.tl)])
    if l.drone and ("repairDroneBay", l.tl) in ids:
        aux.append(ids[("repairDroneBay", l.tl)])
    if l.crystalline and ("crystallineArmor", l.tl) in ids:
        aux.append(ids[("crystallineArmor", l.tl)])
    fam = {"K":"Kinetic", "E":"Energy", "M":"Missile", "SW":"Missile"}[l.weapon]
    pds = {"NONE":None, "K":"Kinetic", "E":"Energy", "AMM":"AMM"}[l.pds]
    used = l.used_space + 2 * apu_count
    if used > l.capacity:
        raise ValueError("illegal CP163 combat carrier")
    return EcologyBuild(
        id=f"CP163-{label}-{l.id}-APU2S{apu_tp}T-x{apu_count}", tl=l.tl, archetype="cp163-apu-carrier",
        weapon_family=fam, main_count=l.main_count, reactor_count=l.reactor_count, shield=l.shield, ecm=l.ecm,
        eccm=l.eccm, pds_family=pds, shield_hardener=l.hardener, capacity=l.capacity, combat_space=used,
        mission_aux_space=l.capacity-used, missile_payload=("Swarmer" if l.weapon=="SW" else "GP"), armor_profile="mainline",
        auxiliary_profiles=tuple(aux), auxiliary_power_tp=apu_tp * apu_count, auxiliary_reactor_count=apu_count,
    )


def combat_contexts(repo: Path, study_path: Path, tl: int) -> list[tuple[EcologyVariant,int,int|str,int,int]]:
    doc = load_json(study_path)
    m = load_research_execution_baseline_pf4(repo)
    ids = _pf4_aux_registry(m)
    rows = [x for x in enumerate_loadouts(m, reactor_space=6) if x.reactor_count == 1 and x.tl == tl]
    out = []
    for tp in candidate_tps_for_tl(doc, tl):
        for tier in STACK_TIERS:
            cnt = _tier_count(rows, tier)
            if cnt <= 0:
                continue
            for w in doc["combatWeaponFamilies"]:
                l = select_carrier(m, rows, tl=tl, space_each=2, count=cnt, weapon=w)
                if l is None:
                    continue
                base = _to_ecology(m, l, ids, apu_tp=tp, apu_count=0, label="BASE")
                aug = _to_ecology(m, l, ids, apu_tp=tp, apu_count=cnt, label="STACK")
                for swap, (a,b) in enumerate(((aug,base),(base,aug))):
                    label = f"{w}_APU2S_{tp}TP_{tier}_x{cnt}_{'STACKvsBASE' if swap==0 else 'BASEvsSTACK'}"
                    v = EcologyVariant(
                        id=f"CP163-TL{tl}-{label}", tl=tl, side_a=a, side_b=b,
                        movement_order=("SideAFirst" if swap==0 else "SideBFirst"),
                        population="cp163_apu_maturation_stack_safety", scenario_group=label,
                    )
                    out.append((v, tp, tier, cnt, swap))
    return out


_C_REPO: Path | None = None
_C_DOC: dict[str, Any] | None = None
_C_CACHE: dict[tuple[int,int], CandidateMatrix] = {}


def _combat_init(repo_s: str, study_s: str, doc: dict[str, Any]):
    global _C_REPO, _C_DOC, _C_CACHE
    _C_REPO = Path(repo_s)
    _C_DOC = doc
    _C_CACHE = {}


def _combat_matrix(tl: int, off: int) -> CandidateMatrix:
    key = (tl, off)
    if key not in _C_CACHE:
        m = load_research_execution_baseline_pf4(_C_REPO)
        _pf4_aux_registry(m)
        m = copy.deepcopy(m)
        m.doc = copy.deepcopy(m.doc)
        m.profiles = m.doc["profiles"]
        m.branches = {r["id"]: r for r in m.doc.get("branches", [])}
        m.p("reactor", tl)["operationalTp"] = main_supply(m, tl, off)
        _C_CACHE[key] = m
    return _C_CACHE[key]


def _combat_task(args):
    v, tp, tier, cnt, swap, off, seed, trials = args
    m = _combat_matrix(v.tl, off)
    aw = bw = dr = caps = err = turns = 0
    sa = defaultdict(float)
    sb = defaultdict(float)
    metrics = (
        "power_available_total", "power_spent_total", "power_shortfall_events", "weapon_power_shortfalls",
        "pds_power_shortfalls", "acquisition_power_shortfalls", "power_sensor", "power_ecm", "power_eccm",
        "power_pds", "power_weapons", "power_shield_recharge", "power_shield_hardener",
        "power_aux_energized_armor", "power_aux_field_stabilizer", "reactor_overload_activations", "damage_control_tp_spent",
    )
    for j in range(trials):
        r = run_trial_full_map(m, v, seed, j, combat_doctrine=COMBAT_DOCTRINE)
        err += int(bool(r.error))
        caps += int(r.termination_cause == "TURN_CAP_SENTINEL")
        turns += r.turns
        if r.winner == "A": aw += 1
        elif r.winner == "B": bw += 1
        else: dr += 1
        for k in metrics:
            sa[k] += float(getattr(r.side_a, k, 0))
            sb[k] += float(getattr(r.side_b, k, 0))
    row = {
        "tl": v.tl, "scenario_id": v.id, "scenario_group": v.scenario_group, "apu_space_each": 2,
        "apu_tp": tp, "stack_tier": tier, "apu_count": cnt, "total_apu_space": 2*cnt, "total_apu_tp": tp*cnt,
        "main_offset": off, "main_supply": main_supply(load_research_execution_baseline_pf4(_C_REPO), v.tl, off),
        "trials": trials, "a_wins": aw, "b_wins": bw, "draws": dr, "a_decisive_share": aw/max(1,aw+bw),
        "mean_turns": turns/max(1,trials), "turn_cap_sentinels": caps, "error_trials": err,
        "side_a_build": v.side_a.id, "side_b_build": v.side_b.id,
        "side_a_apu_count": v.side_a.auxiliary_reactor_count, "side_b_apu_count": v.side_b.auxiliary_reactor_count,
    }
    for k in metrics:
        row["mean_a_" + k] = sa[k] / trials
        row["mean_b_" + k] = sb[k] / trials
    return row


def run_combat_batch(repo: Path, study_path: Path, out: Path, tl: int, jobs: int = 24) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("CP163 study invalid: " + ", ".join(errs))
    ctxs = combat_contexts(repo, study_path, tl)
    trials = int(doc["combatTrialsPerCell"])
    tasks = []
    for v, tp, tier, cnt, swap in ctxs:
        for off in doc["mainReactorOffsetsFromPf4"]:
            tasks.append((v, tp, tier, cnt, swap, int(off), derive_seed(int(doc["masterSeed"]), "cp163-combat", tl, v.id, off), trials))
    if jobs <= 1:
        _combat_init(str(repo), str(study_path), doc)
        rows = [_combat_task(x) for x in tasks]
    else:
        ctx = get_context("spawn" if os.name == "nt" else "fork")
        with ProcessPoolExecutor(max_workers=min(jobs, len(tasks)), mp_context=ctx, initializer=_combat_init, initargs=(str(repo), str(study_path), doc)) as ex:
            rows = list(ex.map(_combat_task, tasks, chunksize=1))
    rows.sort(key=lambda r: (r["scenario_id"], r["main_offset"]))
    _write_csv(out / "combat_response.csv", rows)
    summary = {
        "mode":"combat-batch", "passed": not any(int(r["error_trials"]) for r in rows), "tl":tl,
        "contexts":len(ctxs), "mainOffsetCandidates":3, "cells":len(rows), "trialsPerCell":trials,
        "combatTrials":len(rows)*trials, "turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows),
        "errorTrials":sum(int(r["error_trials"]) for r in rows), "automaticPromotion":False,
    }
    _write_json(out / "summary.json", summary)
    return summary


def _normalize_stack_result(r: dict[str, Any]) -> tuple[int,int,int]:
    a_stack = int(r["side_a_apu_count"]) > 0
    wins = int(r["a_wins"] if a_stack else r["b_wins"])
    losses = int(r["b_wins"] if a_stack else r["a_wins"])
    draws = int(r["draws"])
    return wins, losses, draws


def _trajectory_combat(rows: list[dict[str, Any]], doc: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for tid in trajectories(doc):
        for tier in STACK_TIERS:
            for off in doc["mainReactorOffsetsFromPf4"]:
                rr = [r for r in rows if str(r["stack_tier"]) == str(tier) and int(r["main_offset"]) == int(off) and int(r["apu_tp"]) == apu_tp_for_trajectory(doc, tid, int(r["tl"]))]
                if not rr:
                    continue
                wins = losses = draws = trials = caps = 0
                for r in rr:
                    w,l,d = _normalize_stack_result(r)
                    wins += w; losses += l; draws += d; trials += int(r["trials"]); caps += int(r["turn_cap_sentinels"])
                out.append({
                    "trajectory_id":tid, "stack_tier":tier, "main_offset":int(off), "cells":len(rr),
                    "combat_trials":trials, "stack_wins":wins, "base_wins":losses, "draws":draws,
                    "stack_decisive_share":wins/max(1,wins+losses), "turn_cap_rate":caps/max(1,trials),
                })
    return out


def merge_combat(batch_root: Path, out: Path, study_path: Path) -> dict[str, Any]:
    doc = load_json(study_path)
    rows = []
    audit = []
    for p in sorted(batch_root.rglob("summary.json")):
        sm = json.loads(p.read_text(encoding="utf-8-sig"))
        data = p.parent / "combat_response.csv"
        ok = sm.get("mode") == "combat-batch" and bool(sm.get("passed")) and data.is_file()
        n = 0
        if ok:
            with data.open(encoding="utf-8-sig", newline="") as f:
                rr = list(csv.DictReader(f))
                rows.extend(rr)
                n = len(rr)
        audit.append({"batch":p.parent.name,"tl":sm.get("tl",""),"passed":int(ok),"rows":n,"combat_trials":sm.get("combatTrials",0),"turn_caps":sm.get("turnCapSentinels",0),"errors":sm.get("errorTrials",0)})
    rows.sort(key=lambda r:(int(r["tl"]),int(r["apu_tp"]),str(r["stack_tier"]),int(r["main_offset"]),r["scenario_id"]))
    _write_csv(out / "combat_response.csv", rows)
    _write_csv(out / "batch_merge_audit.csv", audit)

    groups = defaultdict(list)
    for r in rows:
        groups[(int(r["tl"]),int(r["apu_tp"]),str(r["stack_tier"]),int(r["main_offset"]))].append(r)
    sums = []
    for k, rr in sorted(groups.items(), key=lambda x:(x[0][0],x[0][1],x[0][2],x[0][3])):
        wins=losses=draws=trials=caps=0
        for r in rr:
            w,l,d=_normalize_stack_result(r);wins+=w;losses+=l;draws+=d;trials+=int(r["trials"]);caps+=int(r["turn_cap_sentinels"])
        sums.append({"tl":k[0],"apu_tp":k[1],"stack_tier":k[2],"main_offset":k[3],"cells":len(rr),"combat_trials":trials,"stack_wins":wins,"base_wins":losses,"draws":draws,"stack_decisive_share":wins/max(1,wins+losses),"turn_cap_rate":caps/max(1,trials)})
    _write_csv(out / "combat_apu_summary_by_tl.csv", sums)
    _write_csv(out / "trajectory_combat_summary.csv", _trajectory_combat(rows, doc))
    summary = {
        "mode":"combat-merged", "passed":len(audit)==9 and all(x["passed"] for x in audit) and not any(int(r["error_trials"]) for r in rows),
        "batches":len(audit), "cells":len(rows), "combatTrials":sum(int(r["trials"]) for r in rows),
        "turnCapSentinels":sum(int(r["turn_cap_sentinels"]) for r in rows), "errorTrials":sum(int(r["error_trials"]) for r in rows),
        "automaticPromotion":False,
    }
    _write_json(out / "summary.json", summary)
    return summary


def plan(repo: Path, study_path: Path, out: Path) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc)
    if errs:
        raise ValueError("CP163 study invalid: " + ", ".join(errs))
    m = load_research_execution_baseline_pf4(repo)
    all_rows = enumerate_loadouts(m, reactor_space=6)
    rows = [x for x in all_rows if x.reactor_count == 1]
    stoch = 0
    for tl in range(1,10):
        tlrows=[x for x in rows if x.tl==tl]
        for tp in candidate_tps_for_tl(doc,tl):
            for tier in STACK_TIERS:
                cnt=_tier_count(tlrows,tier)
                if cnt<=0:continue
                l=select_carrier(m,rows,tl=tl,space_each=2,count=cnt)
                if l is None:continue
                stoch += len(doc["mainReactorOffsetsFromPf4"]) * len(doc["stochasticDoctrines"])
    ctx = {tl: len(combat_contexts(repo, study_path, tl)) for tl in range(1,10)}
    cells = sum(ctx.values()) * len(doc["mainReactorOffsetsFromPf4"])
    combat = cells * int(doc["combatTrialsPerCell"])
    summary = {
        "mode":"plan", "passed":True, "baselineId":"CP160-PF4", "acceptedDiagnosticCheckpoint":162,
        "legalPoweredArchitectures":len(all_rows), "oneMainReactorArchitectures":len(rows), "mainReactorSpace":6,
        "mainOffsets":doc["mainReactorOffsetsFromPf4"], "apuSpace":2,
        "trajectoryCandidates":len(doc["apuTrajectories"]), "uniqueTlLocalApuPoints":sum(len(candidate_tps_for_tl(doc,tl)) for tl in range(1,10)),
        "installationCountCapImposed":False, "stochasticVariants":stoch,
        "stochasticTurnSamples":stoch*int(doc["stochasticTurnSamplesPerVariant"]),
        "combatContextsByTl":ctx, "combatContexts":sum(ctx.values()), "combatCells":cells, "combatTrials":combat,
        "automaticPromotion":False, "tuningAllowed":False,
    }
    _write_json(out / "summary.json", summary)
    return summary


def smoke(repo: Path, study_path: Path, out: Path) -> dict[str, Any]:
    doc=load_json(study_path);m=load_research_execution_baseline_pf4(repo);rows=[x for x in enumerate_loadouts(m,reactor_space=6) if x.reactor_count==1];checks=[]
    checks.append({"probe":"main_reactor_space_6","passed":int(all(int(m.p("reactor",t)["space"])==6 for t in range(1,10)))})
    checks.append({"probe":"apu_space_2","passed":int(int(doc["apuSpace"])==2)})
    checks.append({"probe":"tl5_maturation_present","passed":int(apu_tp_for_trajectory(doc,"APU_MATURE_TL5",4)==1 and apu_tp_for_trajectory(doc,"APU_MATURE_TL5",5)==2)})
    checks.append({"probe":"late_plus3_boundary_present","passed":int(candidate_tps_for_tl(doc,8)==[1,2,3] and candidate_tps_for_tl(doc,9)==[1,2,3])})
    tlrows=[x for x in rows if x.tl==9];cnt=_tier_count(tlrows,3);c=select_carrier(m,rows,tl=9,space_each=2,count=cnt,weapon="E");checks.append({"probe":"three_apu_carrier_exists","passed":int(c is not None)})
    ctxs=combat_contexts(repo,study_path,8);v,tp,tier,cnt,swap=next(x for x in ctxs if x[1]==3 and str(x[2])=="1" and x[3]==1);_combat_init(str(repo),str(study_path),doc);r=_combat_task((v,tp,tier,cnt,swap,0,derive_seed(int(doc["masterSeed"]),"smoke"),2));checks.append({"probe":"live_late_plus3_combat","passed":int(r["error_trials"]==0 and max(v.side_a.auxiliary_power_tp,v.side_b.auxiliary_power_tp)==3)})
    _write_csv(out/"cp163_smoke.csv",checks);summary={"mode":"smoke","passed":all(x["passed"] for x in checks),"probes":len(checks),"combatTrials":2};_write_json(out/"summary.json",summary);return summary


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument("--repo",required=True);ap.add_argument("--study",required=True);sp=ap.add_subparsers(dest="cmd",required=True)
    for n in ("plan","smoke","static"):
        p=sp.add_parser(n);p.add_argument("--out",required=True)
    p=sp.add_parser("stochastic");p.add_argument("--static-dir",required=True);p.add_argument("--out",required=True);p.add_argument("--jobs",type=int,default=24)
    p=sp.add_parser("combat-batch");p.add_argument("--tl",type=int,required=True);p.add_argument("--out",required=True);p.add_argument("--jobs",type=int,default=24)
    p=sp.add_parser("merge-combat");p.add_argument("--batches",required=True);p.add_argument("--out",required=True)
    a=ap.parse_args(argv);repo=Path(a.repo).resolve();study=Path(a.study).resolve();out=Path(a.out).resolve()
    if a.cmd=="plan":r=plan(repo,study,out)
    elif a.cmd=="smoke":r=smoke(repo,study,out)
    elif a.cmd=="static":r=static_analysis(repo,study,out)
    elif a.cmd=="stochastic":r=run_stochastic(repo,study,Path(a.static_dir),out,a.jobs)
    elif a.cmd=="combat-batch":r=run_combat_batch(repo,study,out,a.tl,a.jobs)
    elif a.cmd=="merge-combat":r=merge_combat(Path(a.batches),out,study)
    else:raise SystemExit(2)
    print(json.dumps(r,indent=2));return 0 if r.get("passed",False) else 1


if __name__=="__main__":
    raise SystemExit(main())
