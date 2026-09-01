from __future__ import annotations

import csv
import hashlib
import itertools
import json
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Callable

from .canonical_combat import run_trial_full_map
from .direct_fire_joint_refinement import _write_csv
from .ecology import EcologyBuild, EcologyVariant, build_space
from .pds_lifecycle_closure import (
    _apply_pds_candidate,
    _gp_ladder,
    _main_matrix,
    _resources,
    _trial_row,
    _weapon_code,
)
from .stage_a_integration_analysis import _features_for_stratum, PAYLOAD_MAP, WEAPON_MAP
from .study import load_json

RESULT_SCHEMA = "star-cluster-cp155-pds-architecture-resynthesis-result-v0.1"
FAMILIES = ("Kinetic", "Energy", "AMM")
K_CHANCE = (0, 2, 5, 8, 10, 12, 15, 18)
E_CHANCE = (0, 5, 10, 15, 20)
AMM_CHANCE = (0, 5, 10, 15, 20)
K_AMMO = 75
AMM_AMMO = 25
SCREEN_TRIALS = 30
BASELINE_TRIALS = 200
DEEP_TRIALS = 100
LADDERS_PER_FAMILY = 10
DEEP_LADDERS = 30

CP154_EVIDENCE_HASHES = {
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_NATIVE_ACCEPTANCE_SUMMARY.json": "72bace740f8feac93a038d0e1c9d73fcbbff8ae12b20f4c8d089f43ce0427a3d",
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_CANDIDATE_SUMMARY.csv": "3366323015b2bcc0b4437a6f0a869977e8f593655cf25c701566d9bf4f43e1a9",
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_CANDIDATE_ATTACKER_RESPONSE.csv": "9b547b251e8a9ded6bd4678be1337c390c6f157a0ec3ded657ae7ef0229e512a",
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_LADDER_CANDIDATES.csv": "029c9cd8af305f5fd41345da3d5685affd4f67a7d0a1968de55b536f7c3debbe",
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_DEEP_LADDER_SUMMARY.csv": "b21331aea6eb63519155a1eb882a5ebfc1a38e12888d525c40b6a05f7da9bb22",
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_DEEP_RESPONSE.csv": "4f7363127b4cd1d28f6aef2d2e7edc2485d6ee449730cac56ddc641c030297f4",
    "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_PDS_TRIAD_SHORTLIST.csv": "7837d6ea401e6b4760e93cd7bd29a8dc6ca2e394a5dce4082d10960f8da7c4de",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _accepted_cp154(repo: Path) -> None:
    for rel, expected in CP154_EVIDENCE_HASHES.items():
        p = repo / rel
        if not p.is_file() or _sha(p) != expected:
            raise ValueError(f"CP155 accepted CP154 evidence hash mismatch: {rel}")
    s = json.loads((repo / "docs/validation/evidence/checkpoint-155/accepted-cp154/CP154_NATIVE_ACCEPTANCE_SUMMARY.json").read_text(encoding="utf-8-sig"))
    if int(s.get("checkpoint", 0)) != 154 or int(s.get("substantiveCombatTrials", 0)) != 32729400 or int(s.get("substantiveErrorTrials", -1)) != 0:
        raise ValueError("CP155 accepted CP154 evidence does not prove native completion")


def _attackers(tl: int) -> tuple[str, ...]:
    return ("GP_M2", "GP_M3") if tl == 1 else ("GP_M2", "GP_M3", "SW2")


def _primary_defenders(_: int) -> tuple[str, ...]:
    return ("K1", "E7")


def _robustness_defenders(tl: int) -> tuple[str, ...]:
    return ("M2",) if tl == 1 else ("M2", "SW2")


def primary_contexts(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    resources = _resources(repo, doc)
    strata = list(doc["candidateDesign"]["strata"])
    out: list[dict[str, Any]] = []
    idx = 0
    for tl in range(1, 10):
        for att, defn, stratum, rid in itertools.product(_attackers(tl), _primary_defenders(tl), strata, resources):
            out.append({
                "scenario_index": idx,
                "scenario_id": f"cp155-p-{tl}-{att}-{defn}-{stratum}-{rid}",
                "context_class": "PRIMARY",
                "tl": tl,
                "attacker": att,
                "defender": defn,
                "side_a_weapon": _weapon_code(att),
                "side_b_weapon": _weapon_code(defn),
                "gp_ladder": _gp_ladder(att),
                "resource_ensemble_id": rid,
                "scenario_stratum": stratum,
                "geometry": "radius5_full_hex_adaptive",
            })
            idx += 1
    return out


def robustness_contexts(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    strata = list(doc["candidateDesign"]["strata"])
    rid = "R1_CENTRAL_NO_MAJOR"
    out: list[dict[str, Any]] = []
    idx = 0
    for tl in range(1, 10):
        for att, defn, stratum in itertools.product(_attackers(tl), _robustness_defenders(tl), strata):
            out.append({
                "scenario_index": idx,
                "scenario_id": f"cp155-r-{tl}-{att}-{defn}-{stratum}-{rid}",
                "context_class": "ROBUSTNESS",
                "tl": tl,
                "attacker": att,
                "defender": defn,
                "side_a_weapon": _weapon_code(att),
                "side_b_weapon": _weapon_code(defn),
                "gp_ladder": _gp_ladder(att),
                "resource_ensemble_id": rid,
                "scenario_stratum": stratum,
                "geometry": "radius5_full_hex_adaptive",
            })
            idx += 1
    return out


def deep_contexts(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    out = primary_contexts(repo, doc) + robustness_contexts(repo, doc)
    for i, r in enumerate(out):
        r["scenario_index"] = i
    return out


def _energy_profiles() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rc1 in (1, 2, 3):
        out.append({"reaction_capacity": 1, "rc1_tp": rc1, "rc2_tp": "", "safe_rc": 1, "extra_strain": 0, "strain_limit": 0, "mode": "RC1"})
        for delta in (1, 2):
            rc2 = rc1 + delta
            out.append({"reaction_capacity": 2, "rc1_tp": rc1, "rc2_tp": rc2, "safe_rc": 2, "extra_strain": 0, "strain_limit": 0, "mode": "RC2_SAFE"})
            for limit in (1, 2):
                out.append({"reaction_capacity": 2, "rc1_tp": rc1, "rc2_tp": rc2, "safe_rc": 1, "extra_strain": 1, "strain_limit": limit, "mode": "RC2_OVERCHARGED"})
    return out


def _amm_profiles(tl: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tp in (1, 2):
        out.append({"reaction_capacity": 1, "rc1_tp": tp, "rc2_tp": "", "rc3_tp": "", "range_one": 0, "mode": "RC1"})
    for rc1, rc2 in ((1, 2), (1, 3), (2, 3)):
        out.append({"reaction_capacity": 2, "rc1_tp": rc1, "rc2_tp": rc2, "rc3_tp": "", "range_one": 0, "mode": "RC2"})
    if tl >= 5:
        for rc1, rc2, rc3 in ((1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4)):
            out.append({"reaction_capacity": 3, "rc1_tp": rc1, "rc2_tp": rc2, "rc3_tp": rc3, "range_one": 1, "mode": "RC3_RANGE1"})
    return out


def candidate_ledger(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    _accepted_cp154(repo)
    out: list[dict[str, Any]] = []
    for tl in range(1, 10):
        idx = 0
        for chance, rc, tp in itertools.product(K_CHANCE, (1, 2), (1, 2, 3, 4)):
            out.append({
                "family": "Kinetic", "candidate_id": f"K155-{tl:02d}-{idx:03d}", "tl": tl, "candidate_index": idx,
                "base_chance_pp": chance, "reaction_capacity": rc,
                "rc1_tp": tp if rc == 1 else 1, "rc2_tp": "" if rc == 1 else tp, "rc3_tp": "",
                "readiness_tp": tp, "ammo": K_AMMO, "range_one": 0,
                "safe_rc": rc, "extra_strain": 0, "strain_limit": 0, "mode": f"RC{rc}", "promotion_allowed": 0,
            })
            idx += 1
        idx = 0
        for chance, p in itertools.product(E_CHANCE, _energy_profiles()):
            full_tp = int(p["rc1_tp"] if p["reaction_capacity"] == 1 else p["rc2_tp"])
            out.append({
                "family": "Energy", "candidate_id": f"E155-{tl:02d}-{idx:03d}", "tl": tl, "candidate_index": idx,
                "base_chance_pp": chance, "reaction_capacity": p["reaction_capacity"], "rc1_tp": p["rc1_tp"], "rc2_tp": p["rc2_tp"], "rc3_tp": "",
                "readiness_tp": full_tp, "ammo": "", "range_one": 0, "safe_rc": p["safe_rc"], "extra_strain": p["extra_strain"], "strain_limit": p["strain_limit"], "mode": p["mode"], "promotion_allowed": 0,
            })
            idx += 1
        idx = 0
        for chance, p in itertools.product(AMM_CHANCE, _amm_profiles(tl)):
            rc = int(p["reaction_capacity"])
            full_tp = int(p["rc1_tp"] if rc == 1 else p["rc2_tp"] if rc == 2 else p["rc3_tp"])
            out.append({
                "family": "AMM", "candidate_id": f"A155-{tl:02d}-{idx:03d}", "tl": tl, "candidate_index": idx,
                "base_chance_pp": chance, "reaction_capacity": rc, "rc1_tp": p["rc1_tp"], "rc2_tp": p["rc2_tp"], "rc3_tp": p["rc3_tp"],
                "readiness_tp": full_tp, "ammo": AMM_AMMO, "range_one": p["range_one"], "safe_rc": rc,
                "extra_strain": 0, "strain_limit": 0, "mode": p["mode"], "promotion_allowed": 0,
            })
            idx += 1
    return out


def validate_study(doc: dict[str, Any]) -> list[str]:
    e: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-cp155-pds-architecture-resynthesis-study-v0.1": e.append("schema")
    if int(doc.get("checkpoint", 0)) != 155 or int(doc.get("baseCheckpoint", 0)) != 154: e.append("checkpoint")
    if doc.get("combatDoctrine") != "cp147_tactical_utility": e.append("doctrine")
    if doc.get("automaticPromotion") or doc.get("tuningAllowed"): e.append("promotion")
    forbidden = str(doc.get("balancePhilosophy", {}).get("forbiddenSelectorObjective", "")).lower()
    if "no global distance-to-50" not in forbidden or "no inter-family" not in forbidden: e.append("non-equality-guardrail")
    return e


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    try:
        _accepted_cp154(repo)
    except Exception as ex:
        return [str(ex)]
    rows = candidate_ledger(repo, doc)
    e: list[str] = []
    expected = {"Kinetic": 64 * 9, "Energy": 105 * 9, "AMM": 25 * 4 + 45 * 5}
    for fam, n in expected.items():
        if sum(r["family"] == fam for r in rows) != n: e.append(f"candidate-count-{fam}")
    if any(r["family"] in ("Kinetic", "Energy") and int(r["reaction_capacity"]) > 2 for r in rows): e.append("local-rc3")
    if any(r["family"] != "AMM" and int(r["range_one"]) for r in rows): e.append("non-amm-range1")
    if any(r["family"] == "AMM" and int(r["reaction_capacity"]) == 3 and not int(r["range_one"]) for r in rows): e.append("amm-rc3-no-range1")
    if any(r["family"] == "AMM" and int(r["reaction_capacity"]) == 3 and int(r["tl"]) < 5 for r in rows): e.append("early-amm-rc3")
    if any(r["family"] == "Kinetic" and int(r["ammo"]) != K_AMMO for r in rows): e.append("k-ammo-varied")
    if any(r["family"] == "AMM" and int(r["ammo"]) != AMM_AMMO for r in rows): e.append("amm-ammo-varied")
    return e


def run_plan(repo: Path, study_path: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path)
    errs = validate_study(doc) + validate_population(repo, doc)
    rows = candidate_ledger(repo, doc) if not errs else []
    primary = primary_contexts(repo, doc) if not errs else []
    robust = robustness_contexts(repo, doc) if not errs else []
    outdir.mkdir(parents=True, exist_ok=True)
    _write_csv(outdir / "pds_candidate_ledger.csv", rows)
    _write_csv(outdir / "pds_primary_contexts.csv", primary)
    _write_csv(outdir / "pds_robustness_contexts.csv", robust)
    counts = []
    screen_cells = 0
    for fam in FAMILIES:
        for tl in range(1, 10):
            n = sum(r["family"] == fam and int(r["tl"]) == tl for r in rows)
            c = sum(int(x["tl"]) == tl for x in primary)
            counts.append({"family": fam, "tl": tl, "candidates": n, "primary_contexts": c})
            screen_cells += n * c
    _write_csv(outdir / "pds_candidate_counts.csv", counts)
    baseline_combats = len(primary) * BASELINE_TRIALS
    screen_combats = screen_cells * SCREEN_TRIALS
    deep_per = len(primary) + len(robust)
    deep_combats = DEEP_LADDERS * deep_per * DEEP_TRIALS
    s = {
        "schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "plan", "passed": not errs, "failedGates": errs,
        "candidateTlRows": len(rows), "primaryContexts": len(primary), "robustnessContexts": len(robust), "deepContextsPerLadder": deep_per,
        "baselineCombatTrials": baseline_combats, "screenCandidateContextCells": screen_cells, "screenCombatTrials": screen_combats,
        "deepLadders": DEEP_LADDERS, "deepCombatTrials": deep_combats, "substantiveCombatTrials": baseline_combats + screen_combats + deep_combats,
        "automaticPromotion": False,
    }
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    return s


def _bind(matrix: Any, src: dict[str, Any], pds_family: str | None) -> EcologyVariant:
    tl = int(src["tl"]); stratum = src["scenario_stratum"]; f = _features_for_stratum(stratum, tl); qa, qb = f["start"]
    def make(side: str, weapon_variant: str, pds: str | None):
        fam = WEAPON_MAP[weapon_variant]; payload = PAYLOAD_MAP[weapon_variant]
        combat = build_space(matrix, tl, fam, 1, 1, bool(f["shield"]), bool(f["ecm"]), bool(f["eccm"]), pds, bool(f["hardener"]))
        cap = matrix.capacity(tl)
        if combat > cap: raise ValueError(f"illegal CP155 build {tl} {weapon_variant} {pds}: {combat}>{cap}")
        return EcologyBuild(id=f"cp155-{src['scenario_id']}-{side}", tl=tl, archetype=f"cp155-{stratum.lower()}", weapon_family=fam, main_count=1, reactor_count=1, shield=bool(f["shield"]), ecm=bool(f["ecm"]), eccm=bool(f["eccm"]), pds_family=pds, shield_hardener=bool(f["hardener"]), capacity=cap, combat_space=combat, mission_aux_space=cap-combat, missile_payload=payload, armor_profile=str(f["armor"]))
    a = make("A", src["side_a_weapon"], None); b = make("B", src["side_b_weapon"], pds_family)
    group = f"cp155-{src['scenario_id']}"
    return EcologyVariant(id=src["scenario_id"], tl=tl, side_a=a, side_b=b, movement_order="SideAFirst", geometry=src["geometry"], population="cp155-pds-architecture-resynthesis", start_q_a=int(qa), start_q_b=int(qb), max_turns=int(f["max_turns"]), scenario_group=group, physical_id_a=group + ":ship-a", physical_id_b=group + ":ship-b")


_B_REPO: Path | None = None
_B_DOC: dict[str, Any] | None = None
_B_BASE: dict[tuple[str, int, str], Any] | None = None


def _baseline_init(repo_text: str, doc: dict[str, Any]):
    global _B_REPO, _B_DOC, _B_BASE
    _B_REPO = Path(repo_text); _B_DOC = doc; _B_BASE = {}


def _baseline_task(args):
    idx, src, seed, trials = args
    assert _B_REPO is not None and _B_DOC is not None and _B_BASE is not None
    key = (src["resource_ensemble_id"], int(src["tl"]), src["gp_ladder"])
    if key not in _B_BASE: _B_BASE[key] = _main_matrix(_B_REPO, _B_DOC, key[0], key[1], key[2])
    m = _B_BASE[key]; v = _bind(m, src, None)
    return _trial_row(m, v, src, "NO_PDS", "None", seed + idx * 1009, trials)


def run_baseline(repo: Path, study_path: Path, outdir: Path, jobs: int = 24, trials: int | None = None) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    contexts = primary_contexts(repo, doc); ntrials = int(trials or BASELINE_TRIALS)
    tasks = [(i, src, int(doc["masterSeed"]) - 500000, ntrials) for i, src in enumerate(contexts)]
    outdir.mkdir(parents=True, exist_ok=True); jobs = max(1, min(jobs, len(tasks)))
    if jobs == 1:
        _baseline_init(str(repo), doc); result = [_baseline_task(t) for t in tasks]
    else:
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_baseline_init, initargs=(str(repo), doc)) as ex:
            result = list(ex.map(_baseline_task, tasks, chunksize=min(12, max(1, len(tasks) // max(1, jobs * 8)))))
    result.sort(key=lambda r: int(r["scenario_index"])); _write_csv(outdir / "pds_no_pds_baseline.csv", result)
    errs = []
    if len(result) != len(contexts): errs.append("row-count")
    if any(int(r["error_trials"]) for r in result): errs.append("errors")
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "no-pds-baseline", "passed": not errs, "failedGates": errs, "contexts": len(result), "trialsPerCell": ntrials, "combatTrials": len(result) * ntrials, "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in result), "errors": sum(int(r["error_trials"]) for r in result), "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


_C_REPO: Path | None = None
_C_DOC: dict[str, Any] | None = None
_C_CANDS: dict[str, dict[str, Any]] | None = None
_C_BASE: dict[tuple[str, int, str], Any] | None = None
_C_CACHE: dict[tuple[str, int, str, str], Any] | None = None


def _candidate_init(repo_text: str, doc: dict[str, Any], candidates: list[dict[str, Any]]):
    global _C_REPO, _C_DOC, _C_CANDS, _C_BASE, _C_CACHE
    _C_REPO = Path(repo_text); _C_DOC = doc; _C_CANDS = {r["candidate_id"]: r for r in candidates}; _C_BASE = {}; _C_CACHE = {}


def _candidate_task(args):
    idx, src, cid, family, seed, trials = args
    assert _C_REPO is not None and _C_DOC is not None and _C_CANDS is not None and _C_BASE is not None and _C_CACHE is not None
    key = (src["resource_ensemble_id"], int(src["tl"]), src["gp_ladder"])
    if key not in _C_BASE: _C_BASE[key] = _main_matrix(_C_REPO, _C_DOC, key[0], key[1], key[2])
    ckey = (key[0], key[1], key[2], cid)
    if ckey not in _C_CACHE: _C_CACHE[ckey] = _apply_pds_candidate(_C_BASE[key], _C_CANDS[cid])
    m = _C_CACHE[ckey]; v = _bind(m, src, family)
    return _trial_row(m, v, src, cid, family, seed + idx * 1013, trials)


def run_candidate_batch(repo: Path, study_path: Path, outdir: Path, family: str, tl: int, candidate_start: int = 0, candidate_end: int | None = None, jobs: int = 24, trials: int | None = None, smoke: bool = False) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    allc = [r for r in candidate_ledger(repo, doc) if r["family"] == family and int(r["tl"]) == int(tl)]
    start = max(0, candidate_start); end = len(allc) if candidate_end is None else min(len(allc), candidate_end); cands = allc[start:end]
    if not cands: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["empty-candidate-batch"]}
    contexts = [x for x in primary_contexts(repo, doc) if int(x["tl"]) == int(tl)]
    if smoke: contexts = contexts[:min(6, len(contexts))]
    ntrials = int(trials or (1 if smoke else SCREEN_TRIALS)); tasks = []; idx = 0
    for c in cands:
        for src in contexts:
            tasks.append((idx, src, c["candidate_id"], family, int(doc["masterSeed"]), ntrials)); idx += 1
    outdir.mkdir(parents=True, exist_ok=True); jobs = max(1, min(jobs, len(tasks)))
    if jobs == 1:
        _candidate_init(str(repo), doc, cands); result = [_candidate_task(t) for t in tasks]
    else:
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_candidate_init, initargs=(str(repo), doc, cands)) as ex:
            result = list(ex.map(_candidate_task, tasks, chunksize=min(12, max(1, len(tasks) // max(1, jobs * 8)))))
    result.sort(key=lambda r: (r["candidate_id"], int(r["scenario_index"]))); _write_csv(outdir / "pds_candidate_context_results.csv", result)
    e: list[str] = []
    if len(result) != len(cands) * len(contexts): e.append("row-count")
    if any(int(r["error_trials"]) for r in result): e.append("errors")
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "candidate-smoke" if smoke else "candidate-screen-batch", "passed": not e, "failedGates": e, "family": family, "tl": tl, "candidateStart": start, "candidateEnd": end, "candidates": len(cands), "contextsPerCandidate": len(contexts), "candidateContextCells": len(result), "trialsPerCell": ntrials, "combatTrials": len(result) * ntrials, "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in result), "errors": sum(int(r["error_trials"]) for r in result), "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


def _share(w: int, l: int) -> float:
    return w / max(1, w + l)


def _baseline_map(baseline_dir: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv(baseline_dir / "pds_no_pds_baseline.csv")
    return {r["scenario_id"]: r for r in rows}


def _aggregate_candidate_rows(rows: list[dict[str, str]], meta: dict[str, dict[str, Any]], baseline: dict[str, dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    groups = defaultdict(list)
    for r in rows: groups[r["candidate_id"]].append(r)
    summary: list[dict[str, Any]] = []; responses: list[dict[str, Any]] = []
    for cid, rs in groups.items():
        m = meta[cid]
        cw = sum(int(r["b_wins"]) for r in rs); cl = sum(int(r["a_wins"]) for r in rs); cd = sum(int(r["draws"]) for r in rs)
        brs = [baseline[r["scenario_id"]] for r in rs]
        bw = sum(int(r["b_wins"]) for r in brs); bl = sum(int(r["a_wins"]) for r in brs)
        cand_share = _share(cw, cl); base_share = _share(bw, bl); uplift = cand_share - base_share
        pa = sum(float(r["mean_b_pds_attempts"]) * int(r["trials"]) for r in rs)
        pi = sum(float(r["mean_b_pds_intercepts"]) * int(r["trials"]) for r in rs)
        pp = sum(float(r["mean_b_power_pds"]) * int(r["trials"]) for r in rs)
        ov = sum(float(r["mean_b_pds_overcharge_attempts"]) * int(r["trials"]) for r in rs)
        ro = sum(float(r["mean_b_pds_range_one_attempts"]) * int(r["trials"]) for r in rs)
        dimension_uplift: dict[tuple[str, str], float] = {}
        for dim in ("attacker", "defender", "scenario_stratum", "resource_ensemble_id"):
            levels = sorted({str(r[dim]) for r in rs})
            for level in levels:
                cr = [r for r in rs if str(r[dim]) == level]; bb = [baseline[r["scenario_id"]] for r in cr]
                cs = _share(sum(int(r["b_wins"]) for r in cr), sum(int(r["a_wins"]) for r in cr))
                bs = _share(sum(int(r["b_wins"]) for r in bb), sum(int(r["a_wins"]) for r in bb))
                du = cs - bs; dimension_uplift[(dim, level)] = du
                responses.append({"candidate_id": cid, "family": m["family"], "tl": m["tl"], "dimension": dim, "level": level, "candidate_defender_decisive_share": cs, "no_pds_defender_decisive_share": bs, "protection_uplift": du})
        gp_vals = [v for (dim, level), v in dimension_uplift.items() if dim == "attacker" and level.startswith("GP_")]
        sw_vals = [v for (dim, level), v in dimension_uplift.items() if dim == "attacker" and level == "SW2"]
        summary.append({**m, "trials": sum(int(r["trials"]) for r in rs), "defender_wins": cw, "attacker_wins": cl, "draws": cd,
            "candidate_defender_decisive_share": cand_share, "no_pds_defender_decisive_share": base_share, "protection_uplift": uplift,
            "gp_protection_uplift": sum(gp_vals) / max(1, len(gp_vals)), "sw_protection_uplift": (sum(sw_vals) / len(sw_vals) if sw_vals else ""),
            "k_defender_uplift": dimension_uplift.get(("defender", "K1"), ""), "e_defender_uplift": dimension_uplift.get(("defender", "E7"), ""),
            "pds_attempts": pa, "pds_intercepts": pi, "intercept_rate_per_attempt": pi / max(1e-9, pa), "pds_tp_per_attempt": pp / max(1e-9, pa),
            "overcharge_attempt_share": ov / max(1e-9, pa), "range_one_attempt_share": ro / max(1e-9, pa), "promotion_allowed": 0})
    summary.sort(key=lambda r: (r["family"], int(r["tl"]), float(r["protection_uplift"]), r["candidate_id"]))
    return summary, responses


def merge_candidate_batches(repo: Path, study_path: Path, baseline_dir: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); meta = {r["candidate_id"]: r for r in candidate_ledger(repo, doc)}; baseline = _baseline_map(baseline_dir)
    rows: list[dict[str, str]] = []; seen = set(); audit = []; errors = 0
    for d in sorted(p for p in batch_root.rglob("*") if p.is_dir()):
        sp = d / "summary.json"; rp = d / "pds_candidate_context_results.csv"
        if not sp.exists() or not rp.exists(): continue
        s = json.loads(sp.read_text(encoding="utf-8-sig")); ok = bool(s.get("passed")) and s.get("mode") == "candidate-screen-batch" and int(s.get("errors", -1)) == 0; nr = 0
        if ok:
            for r in _read_csv(rp):
                key = (r["candidate_id"], r["scenario_id"])
                if key in seen: continue
                seen.add(key); rows.append(r); nr += 1; errors += int(r["error_trials"])
        audit.append({"batch": str(d.relative_to(batch_root)), "rows": nr, "passed": int(ok)})
    expected = sum(1 for c in meta.values() for x in primary_contexts(repo, doc) if int(x["tl"]) == int(c["tl"]))
    errs: list[str] = []
    if len(rows) != expected: errs.append("coverage")
    if errors: errs.append("errors")
    summary, responses = _aggregate_candidate_rows(rows, meta, baseline)
    outdir.mkdir(parents=True, exist_ok=True); _write_csv(outdir / "batch_merge_audit.csv", audit); _write_csv(outdir / "pds_candidate_summary.csv", summary); _write_csv(outdir / "pds_candidate_response.csv", responses)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "candidate-merged", "passed": not errs, "failedGates": errs, "candidateContextCells": len(rows), "candidates": len(summary), "combatTrials": sum(int(r["trials"]) for r in rows), "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in rows), "errorTrials": errors, "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


def _num(r: dict[str, Any], key: str) -> int:
    v = r.get(key, "")
    return 0 if v in ("", None) else int(float(v))


def _compatible(prev: dict[str, Any], cur: dict[str, Any], family: str) -> bool:
    if _num(cur, "base_chance_pp") < _num(prev, "base_chance_pp"): return False
    if _num(cur, "reaction_capacity") < _num(prev, "reaction_capacity"): return False
    if family == "Kinetic":
        if _num(cur, "reaction_capacity") == _num(prev, "reaction_capacity") and _num(cur, "readiness_tp") > _num(prev, "readiness_tp"): return False
    elif family == "Energy":
        if _num(cur, "rc1_tp") > _num(prev, "rc1_tp"): return False
        if cur["mode"] == prev["mode"] and _num(cur, "readiness_tp") > _num(prev, "readiness_tp"): return False
        if prev["mode"] == "RC2_SAFE" and cur["mode"] != "RC2_SAFE": return False
        if prev["mode"] == "RC2_OVERCHARGED" and cur["mode"] == "RC1": return False
        if prev["mode"] == "RC2_OVERCHARGED" and cur["mode"] == "RC2_OVERCHARGED" and _num(cur, "strain_limit") < _num(prev, "strain_limit"): return False
    else:
        if _num(cur, "reaction_capacity") == _num(prev, "reaction_capacity") and _num(cur, "readiness_tp") > _num(prev, "readiness_tp"): return False
        if _num(prev, "range_one") and not _num(cur, "range_one"): return False
    return True


def _quantile_rank(rows: list[dict[str, Any]]) -> dict[str, float]:
    ordered = sorted(rows, key=lambda r: (float(r["protection_uplift"]), r["candidate_id"]))
    n = len(ordered)
    if n <= 1: return {ordered[0]["candidate_id"]: 0.5} if ordered else {}
    return {r["candidate_id"]: i / (n - 1) for i, r in enumerate(ordered)}


def _template_filter(family: str, label: str, tl: int, r: dict[str, Any]) -> bool:
    rc = _num(r, "reaction_capacity")
    if family == "Kinetic":
        # K-RC1-* or K-RC2-TLx-*
        if label.startswith("K-RC1"): return rc == 1
        unlock = int(label.split("TL")[1].split("-")[0])
        return rc == (1 if tl < unlock else 2)
    if family == "Energy":
        if label.startswith("E-RC1"): return r["mode"] == "RC1"
        parts = label.split("-")
        unlock = int(parts[2][2:])
        strain = int(parts[3][2:])
        safe_at = 0 if "SAFE" not in parts else int(parts[parts.index("SAFE") + 1][2:])
        if tl < unlock: return r["mode"] == "RC1"
        if safe_at and tl >= safe_at: return r["mode"] == "RC2_SAFE"
        return r["mode"] == "RC2_OVERCHARGED" and _num(r, "strain_limit") == strain
    if label.startswith("A-RC1"): return rc == 1
    if "RC3" not in label:
        unlock2 = int(label.split("TL")[1].split("-")[0])
        return rc == (1 if tl < unlock2 else 2)
    # A-RC2-TL3-RC3-TL7
    bits = label.split("-"); u2 = int(bits[2][2:]); u3 = int(bits[4][2:])
    want = 1 if tl < u2 else 2 if tl < u3 else 3
    return rc == want and (_num(r, "range_one") == (1 if want == 3 else 0))


def _templates() -> dict[str, list[tuple[str, float]]]:
    return {
        "Kinetic": [
            ("K-RC1-LOW", .35), ("K-RC1-HIGH", .65),
            ("K-RC2-TL6-LOW", .35), ("K-RC2-TL6-HIGH", .65),
            ("K-RC2-TL7-LOW", .35), ("K-RC2-TL7-HIGH", .65),
            ("K-RC2-TL8-MID", .50), ("K-RC2-TL8-HIGH", .70),
            ("K-RC2-TL9-LOW", .35), ("K-RC2-TL9-HIGH", .65),
        ],
        "Energy": [
            ("E-RC1-LOW", .35), ("E-RC1-HIGH", .65),
            ("E-OC-TL4-SL1", .50), ("E-OC-TL4-SL2", .50),
            ("E-OC-TL5-SL1", .50), ("E-OC-TL5-SL2", .50),
            ("E-OC-TL4-SL1-SAFE-TL7", .50), ("E-OC-TL4-SL2-SAFE-TL7", .50),
            ("E-OC-TL5-SL1-SAFE-TL8", .50), ("E-OC-TL5-SL2-SAFE-TL8", .50),
        ],
        "AMM": [
            ("A-RC1-MID", .50),
            ("A-RC2-TL2-MID", .50), ("A-RC2-TL3-MID", .50), ("A-RC2-TL4-MID", .50),
            ("A-RC2-TL3-RC3-TL5", .50), ("A-RC2-TL3-RC3-TL6", .50),
            ("A-RC2-TL3-RC3-TL7", .35), ("A-RC2-TL3-RC3-TL7", .65),
            ("A-RC2-TL3-RC3-TL8", .50), ("A-RC2-TL3-RC3-TL9", .50),
        ],
    }


def _path_for_template(by_tl: dict[int, list[dict[str, Any]]], family: str, label: str, target_q: float) -> tuple[float, list[dict[str, Any]]] | None:
    ranks = {tl: _quantile_rank([r for r in rows if _template_filter(family, label, tl, r)]) for tl, rows in by_tl.items()}
    first = [r for r in by_tl[1] if _template_filter(family, label, 1, r)]
    beam: list[tuple[float, list[dict[str, Any]]]] = []
    for r in first:
        q = ranks[1].get(r["candidate_id"], .5); beam.append((abs(q - target_q) + .005 * float(r["pds_tp_per_attempt"]), [r]))
    beam.sort(key=lambda x: (x[0], x[1][0]["candidate_id"])); beam = beam[:600]
    for tl in range(2, 10):
        allowed = [r for r in by_tl[tl] if _template_filter(family, label, tl, r)]
        nxt: list[tuple[float, list[dict[str, Any]]]] = []
        for cost, path in beam:
            prev = path[-1]
            for r in allowed:
                if not _compatible(prev, r, family): continue
                q = ranks[tl].get(r["candidate_id"], .5)
                tech = .002 * abs(_num(r, "base_chance_pp") - _num(prev, "base_chance_pp"))
                if _num(r, "reaction_capacity") != _num(prev, "reaction_capacity"): tech += .006
                nxt.append((cost + abs(q - target_q) + .005 * float(r["pds_tp_per_attempt"]) + tech, path + [r]))
        nxt.sort(key=lambda x: (x[0], tuple(r["candidate_id"] for r in x[1]))); beam = nxt[:600]
        if not beam: return None
    return beam[0]


def synthesize_ladders(repo: Path, study_path: Path, merged: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); raw = _read_csv(merged / "pds_candidate_summary.csv"); outdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for x0 in raw:
        x: dict[str, Any] = dict(x0)
        for k in ("tl", "base_chance_pp", "reaction_capacity", "readiness_tp", "rc1_tp", "safe_rc", "extra_strain", "strain_limit", "range_one"):
            if x.get(k, "") != "": x[k] = int(float(x[k]))
        for k in ("rc2_tp", "rc3_tp", "ammo"):
            if x.get(k, "") != "": x[k] = int(float(x[k]))
        for k in ("protection_uplift", "pds_tp_per_attempt", "overcharge_attempt_share", "range_one_attempt_share", "candidate_defender_decisive_share", "no_pds_defender_decisive_share"):
            x[k] = float(x[k])
        rows.append(x)
    allout: list[dict[str, Any]] = []; errs: list[str] = []
    templates = _templates()
    for family in FAMILIES:
        by = {tl: [r for r in rows if r["family"] == family and int(r["tl"]) == tl] for tl in range(1, 10)}
        chosen = []
        for slot, (label, q) in enumerate(templates[family], 1):
            got = _path_for_template(by, family, label, q)
            if got is None:
                errs.append(f"no-path-{label}"); continue
            cost, path = got; chosen.append((label, q, cost, path))
        prefix = {"Kinetic": "K155P", "Energy": "E155P", "AMM": "A155P"}[family]
        for rank, (label, q, cost, path) in enumerate(chosen, 1):
            lid = f"{prefix}{rank:02d}"
            for r in path:
                allout.append({"family": family, "ladder_id": lid, "rank": rank, "architecture_template": label, "strength_quantile_target": q, "ladder_selection_cost": cost,
                    **{k: r.get(k, "") for k in ("candidate_id", "tl", "base_chance_pp", "reaction_capacity", "rc1_tp", "rc2_tp", "rc3_tp", "readiness_tp", "ammo", "range_one", "safe_rc", "extra_strain", "strain_limit", "mode", "candidate_defender_decisive_share", "no_pds_defender_decisive_share", "protection_uplift", "gp_protection_uplift", "sw_protection_uplift", "pds_tp_per_attempt", "overcharge_attempt_share", "range_one_attempt_share")},
                    "promotion_allowed": 0})
    _write_csv(outdir / "pds_ladder_candidates.csv", allout)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "ladder-synthesis", "passed": not errs and len(allout) == DEEP_LADDERS * 9, "failedGates": errs, "laddersPerFamily": LADDERS_PER_FAMILY, "deepLadders": DEEP_LADDERS, "ladderTlRows": len(allout), "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


_D_REPO: Path | None = None
_D_DOC: dict[str, Any] | None = None
_D_ROWS: dict[tuple[str, int], dict[str, Any]] | None = None
_D_BASE: dict[tuple[str, int, str], Any] | None = None
_D_CACHE: dict[tuple[str, int, str, str], Any] | None = None


def _deep_init(repo_text: str, doc: dict[str, Any], rows: list[dict[str, Any]]):
    global _D_REPO, _D_DOC, _D_ROWS, _D_BASE, _D_CACHE
    _D_REPO = Path(repo_text); _D_DOC = doc; _D_ROWS = {(r["ladder_id"], int(r["tl"])): r for r in rows}; _D_BASE = {}; _D_CACHE = {}


def _deep_task(args):
    idx, src, lid, family, seed, trials = args
    assert _D_REPO is not None and _D_DOC is not None and _D_ROWS is not None and _D_BASE is not None and _D_CACHE is not None
    tl = int(src["tl"]); key = (src["resource_ensemble_id"], tl, src["gp_ladder"])
    if key not in _D_BASE: _D_BASE[key] = _main_matrix(_D_REPO, _D_DOC, key[0], tl, key[2])
    ckey = (key[0], tl, key[2], lid); cand = _D_ROWS[(lid, tl)]
    if ckey not in _D_CACHE: _D_CACHE[ckey] = _apply_pds_candidate(_D_BASE[key], cand)
    m = _D_CACHE[ckey]; v = _bind(m, src, family); row = _trial_row(m, v, src, cand["candidate_id"], family, seed + idx * 1019, trials); row["ladder_id"] = lid; row["context_class"] = src["context_class"]; return row


def run_deep_batch(repo: Path, study_path: Path, ladder_path: Path, outdir: Path, ladder_start: int = 0, ladder_end: int | None = None, jobs: int = 24, trials: int | None = None) -> dict[str, Any]:
    doc = load_json(study_path); rows = _read_csv(ladder_path); ids: list[str] = []; meta: dict[str, str] = {}
    for r in rows:
        if r["ladder_id"] not in ids: ids.append(r["ladder_id"]); meta[r["ladder_id"]] = r["family"]
    start = max(0, ladder_start); end = len(ids) if ladder_end is None else min(len(ids), ladder_end); sel = ids[start:end]
    if not sel: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["empty-deep-batch"]}
    selected = [r for r in rows if r["ladder_id"] in sel]; contexts = deep_contexts(repo, doc); ntrials = int(trials or DEEP_TRIALS); tasks = []; idx = 0
    for lid in sel:
        for src in contexts:
            tasks.append((idx, src, lid, meta[lid], int(doc["masterSeed"]) + 500000, ntrials)); idx += 1
    outdir.mkdir(parents=True, exist_ok=True); jobs = max(1, min(jobs, len(tasks)))
    if jobs == 1:
        _deep_init(str(repo), doc, selected); result = [_deep_task(t) for t in tasks]
    else:
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_deep_init, initargs=(str(repo), doc, selected)) as ex:
            result = list(ex.map(_deep_task, tasks, chunksize=min(12, max(1, len(tasks) // max(1, jobs * 8)))))
    result.sort(key=lambda r: (r["ladder_id"], int(r["scenario_index"]))); _write_csv(outdir / "pds_deep_context_results.csv", result)
    errs: list[str] = []
    if len(result) != len(sel) * len(contexts): errs.append("row-count")
    if any(int(r["error_trials"]) for r in result): errs.append("errors")
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "deep-batch", "passed": not errs, "failedGates": errs, "ladderStart": start, "ladderEnd": end, "ladders": len(sel), "contextsPerLadder": len(contexts), "ladderContextCells": len(result), "trialsPerCell": ntrials, "combatTrials": len(result) * ntrials, "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in result), "errors": sum(int(r["error_trials"]) for r in result), "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


def _longest_streak(flags: list[bool]) -> int:
    best = cur = 0
    for x in flags:
        if x: cur += 1; best = max(best, cur)
        else: cur = 0
    return best


def merge_deep(repo: Path, study_path: Path, baseline_dir: Path, ladder_path: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); ladder_rows = _read_csv(ladder_path); meta = {}; architecture = {}
    for r in ladder_rows:
        meta.setdefault(r["ladder_id"], r["family"]); architecture.setdefault(r["ladder_id"], r["architecture_template"])
    baseline = _baseline_map(baseline_dir); rows: list[dict[str, str]] = []; seen = set(); audit = []; errors = 0
    for d in sorted(p for p in batch_root.rglob("*") if p.is_dir()):
        sp = d / "summary.json"; rp = d / "pds_deep_context_results.csv"
        if not sp.exists() or not rp.exists(): continue
        s = json.loads(sp.read_text(encoding="utf-8-sig")); ok = bool(s.get("passed")) and s.get("mode") == "deep-batch" and int(s.get("errors", -1)) == 0; nr = 0
        if ok:
            for r in _read_csv(rp):
                key = (r["ladder_id"], r["scenario_id"])
                if key in seen: continue
                seen.add(key); rows.append(r); nr += 1; errors += int(r["error_trials"])
        audit.append({"batch": str(d.relative_to(batch_root)), "rows": nr, "passed": int(ok)})
    expected = DEEP_LADDERS * len(deep_contexts(repo, doc)); errs: list[str] = []
    if len(rows) != expected: errs.append("coverage")
    if errors: errs.append("errors")
    by = defaultdict(list)
    for r in rows: by[r["ladder_id"]].append(r)
    summary: list[dict[str, Any]] = []; responses: list[dict[str, Any]] = []
    tl_uplift: dict[tuple[str, int], float] = {}
    for lid, rs in by.items():
        fam = meta[lid]; primary = [r for r in rs if r.get("context_class") == "PRIMARY"]; robust = [r for r in rs if r.get("context_class") == "ROBUSTNESS"]
        cw = sum(int(r["b_wins"]) for r in primary); cl = sum(int(r["a_wins"]) for r in primary); cshare = _share(cw, cl)
        bb = [baseline[r["scenario_id"]] for r in primary]; bw = sum(int(r["b_wins"]) for r in bb); bl = sum(int(r["a_wins"]) for r in bb); bshare = _share(bw, bl); uplift = cshare - bshare
        rw = sum(int(r["b_wins"]) for r in robust); rl = sum(int(r["a_wins"]) for r in robust); robust_share = _share(rw, rl)
        pa = sum(float(r["mean_b_pds_attempts"]) * int(r["trials"]) for r in rs); pi = sum(float(r["mean_b_pds_intercepts"]) * int(r["trials"]) for r in rs); pp = sum(float(r["mean_b_power_pds"]) * int(r["trials"]) for r in rs); ov = sum(float(r["mean_b_pds_overcharge_attempts"]) * int(r["trials"]) for r in rs); ro = sum(float(r["mean_b_pds_range_one_attempts"]) * int(r["trials"]) for r in rs)
        dims: dict[tuple[str, str], float] = {}
        for dim in ("attacker", "defender", "resource_ensemble_id", "scenario_stratum", "tl"):
            levels = sorted({str(r[dim]) for r in primary})
            for level in levels:
                cr = [r for r in primary if str(r[dim]) == level]; br = [baseline[r["scenario_id"]] for r in cr]
                cs = _share(sum(int(r["b_wins"]) for r in cr), sum(int(r["a_wins"]) for r in cr)); bs = _share(sum(int(r["b_wins"]) for r in br), sum(int(r["a_wins"]) for r in br)); du = cs - bs; dims[(dim, level)] = du
                responses.append({"ladder_id": lid, "family": fam, "architecture_template": architecture[lid], "dimension": dim, "level": level, "candidate_defender_decisive_share": cs, "no_pds_defender_decisive_share": bs, "protection_uplift": du})
                if dim == "tl": tl_uplift[(lid, int(level))] = du
        gp = [v for (d, level), v in dims.items() if d == "attacker" and level.startswith("GP_")]; sw = [v for (d, level), v in dims.items() if d == "attacker" and level == "SW2"]
        summary.append({"ladder_id": lid, "family": fam, "architecture_template": architecture[lid], "trials": sum(int(r["trials"]) for r in rs),
            "primary_defender_decisive_share": cshare, "no_pds_defender_decisive_share": bshare, "mean_protection_uplift": uplift,
            "gp_protection_uplift": sum(gp) / max(1, len(gp)), "sw_protection_uplift": (sum(sw) / len(sw) if sw else ""),
            "k_defender_uplift": dims.get(("defender", "K1"), ""), "e_defender_uplift": dims.get(("defender", "E7"), ""), "robustness_defender_decisive_share": robust_share,
            "intercept_rate_per_attempt": pi / max(1e-9, pa), "pds_tp_per_attempt": pp / max(1e-9, pa), "overcharge_attempt_share": ov / max(1e-9, pa), "range_one_attempt_share": ro / max(1e-9, pa), "promotion_allowed": 0})
    summary.sort(key=lambda r: (r["family"], r["ladder_id"])); _write_csv(outdir / "batch_merge_audit.csv", audit); _write_csv(outdir / "pds_deep_ladder_summary.csv", summary); _write_csv(outdir / "pds_deep_response.csv", responses)
    famrows = {f: [r for r in summary if r["family"] == f] for f in FAMILIES}; triads: list[dict[str, Any]] = []
    for k, e, a in itertools.product(famrows["Kinetic"], famrows["Energy"], famrows["AMM"]):
        ids = {"Kinetic": k["ladder_id"], "Energy": e["ladder_id"], "AMM": a["ladder_id"]}; leads = {f: 0 for f in FAMILIES}; deficits = {f: [] for f in FAMILIES}
        for tl in range(1, 10):
            vals = {f: tl_uplift[(ids[f], tl)] for f in FAMILIES}; best = max(vals.values()); leader = max(FAMILIES, key=lambda f: (vals[f], -FAMILIES.index(f))); leads[leader] += 1
            for f in FAMILIES: deficits[f].append(best - vals[f])
        triads.append({"kinetic_ladder": ids["Kinetic"], "energy_ladder": ids["Energy"], "amm_ladder": ids["AMM"],
            "kinetic_lead_tls": leads["Kinetic"], "energy_lead_tls": leads["Energy"], "amm_lead_tls": leads["AMM"],
            "kinetic_max_deficit_pp": 100 * max(deficits["Kinetic"]), "energy_max_deficit_pp": 100 * max(deficits["Energy"]), "amm_max_deficit_pp": 100 * max(deficits["AMM"]),
            "kinetic_10pp_disadvantage_streak": _longest_streak([x >= .10 for x in deficits["Kinetic"]]), "energy_10pp_disadvantage_streak": _longest_streak([x >= .10 for x in deficits["Energy"]]), "amm_10pp_disadvantage_streak": _longest_streak([x >= .10 for x in deficits["AMM"]]),
            "persistent_dominance_watch": int(max(_longest_streak([x >= .10 for x in deficits[f]]) for f in FAMILIES) >= 5), "promotion_allowed": 0})
    triads.sort(key=lambda r: (r["persistent_dominance_watch"], max(r["kinetic_10pp_disadvantage_streak"], r["energy_10pp_disadvantage_streak"], r["amm_10pp_disadvantage_streak"]), r["kinetic_ladder"], r["energy_ladder"], r["amm_ladder"])); _write_csv(outdir / "pds_triad_viability_map.csv", triads)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 155, "mode": "deep-merged", "passed": not errs, "failedGates": errs, "ladders": len(summary), "ladderContextCells": len(rows), "combatTrials": sum(int(r["trials"]) for r in rows), "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in rows), "errorTrials": errors, "triadCombinations": len(triads), "equalizationObjectiveUsed": False, "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s
