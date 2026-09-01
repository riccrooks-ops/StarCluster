from __future__ import annotations

import copy
import csv
import hashlib
import itertools
import json
import math
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .direct_fire_joint_refinement import (
    _Agg as DirectAgg,
    _apply_cp151_center,
    _candidate_side,
    _contexts as direct_contexts,
    _read_csv,
    _resource_rows,
    _write_csv,
)
from .stage_a_integration_analysis import bind_scenario
from .study import load_json
from . import whole_combat_stage_a_response_surface as wc

RESULT_SCHEMA = "star-cluster-cp153-four-main-ladder-synthesis-result-v0.1"
EXPECTED_STAGE_A = 6850
E_FACTORS = (
    "low_damage", "standard_damage", "overload_damage", "accuracy", "standard_range", "max_range",
    "low_tp", "standard_gap", "overload_gap", "spen", "strain_limit",
)
E_PAIRWISE_CANDIDATES_PER_TL = 264
E_TOTAL_CANDIDATES_PER_TL = 422
E_TRIALS = 75
E_CONTEXTS_BY_TL = {1: 200, **{tl: 300 for tl in range(2, 10)}}
E_CELLS = sum(E_TOTAL_CANDIDATES_PER_TL * E_CONTEXTS_BY_TL[tl] for tl in range(1, 10))
E_COMBATS = E_CELLS * E_TRIALS
E_SMOKE_CONTEXTS = 50
E_SMOKE_COMBATS = E_TOTAL_CANDIDATES_PER_TL * E_SMOKE_CONTEXTS * 9
K_LADDERS = 6
E_LADDERS = 8
GP_LADDERS = 3
SW_LADDERS = 3
PACKAGE_COUNT = K_LADDERS * E_LADDERS * GP_LADDERS * SW_LADDERS
SCREEN_CONTEXTS = 1370
SCREEN_TRIALS = 20
SCREEN_CELLS = PACKAGE_COUNT * SCREEN_CONTEXTS
SCREEN_COMBATS = SCREEN_CELLS * SCREEN_TRIALS
DEEP_PACKAGES = 12
DEEP_TRIALS = 100
DEEP_CELLS = DEEP_PACKAGES * EXPECTED_STAGE_A
DEEP_COMBATS = DEEP_CELLS * DEEP_TRIALS
SUBSTANTIVE_COMBATS = E_COMBATS + SCREEN_COMBATS + DEEP_COMBATS

CP152_EVIDENCE_HASHES = {
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_NATIVE_ACCEPTANCE_SUMMARY.json": "a6e0969d8f1203958bd43e21bab3f9a5d8bd16a1ef22b2d84d75daf08e964c7b",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_CANDIDATE_SUMMARY.csv": "761aeb4686b25986ff2c7e753cdf5ce518e405c4e9ee4ec8096493bb9d5a9cc7",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_FACTOR_MARGINALS.csv": "d02e82a28e91e4a43aade06b443655e8c70ddfc855b780fbaf345bb9a85ee262",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_PAIRWISE_RESPONSE.csv": "011f9327b944ae4a8a68d84618a6edc66ddf085c66494d8d44bb10c349447dcb",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_CANDIDATE_SUMMARY.csv": "517e777f9a27234e56f86cbaac5e15f0e9ce465c54ea53f2c89e294fa51d4d37",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_FACTOR_MARGINALS.csv": "46e9a7999f5a719c7e9ad0698f17e7f71d4dc0e32cf709c6eb69931e87c9fc8c",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_PAIRWISE_RESPONSE.csv": "065bf01ea3cb371ea7721ee5e41623a34f299b050f4a17848615f12c53000854",
    "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_JOINT_RESPONSE.csv": "49c6096d7d64be4e3881c125880abc0d2b6e660724cbd6146342dc49189b6b76",
}


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _read_cp152_evidence(repo: Path) -> dict[str, Any]:
    for rel, expected in CP152_EVIDENCE_HASHES.items():
        p = repo / rel
        if not p.is_file() or _sha(p) != expected:
            raise ValueError(f"CP153 accepted CP152 evidence hash mismatch: {rel}")
    summary = json.loads((repo / "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_NATIVE_ACCEPTANCE_SUMMARY.json").read_text(encoding="utf-8-sig"))
    if int(summary.get("checkpoint", 0)) != 152 or int(summary.get("substantiveCombatTrials", 0)) != 48195000 or int(summary.get("substantiveErrorTrials", -1)) != 0:
        raise ValueError("CP153 accepted CP152 evidence does not prove native completion")
    return summary


def _base_matrix(repo: Path, doc: dict[str, Any], resource: str):
    er, tr = _resource_rows(repo, doc)
    return _apply_cp151_center(build_deep_resource_matrix(repo, doc["matrix"], resource, er, tr))


def _copy_matrix(m: Any):
    x = copy.deepcopy(m); x.doc = copy.deepcopy(m.doc); x.profiles = x.doc["profiles"]; x.branches = {r["id"]: r for r in x.doc["branches"]}; return x


def _energy_center(doc: dict[str, Any], tl: int) -> dict[str, int]:
    c = doc["energyClosureCenters"][str(tl)]
    return {k: int(v) for k, v in c.items()}


def energy_factor_levels(doc: dict[str, Any], tl: int) -> dict[str, list[int]]:
    c = _energy_center(doc, tl)
    def tri(name: str, step: int, floor: int = 0, ceiling: int | None = None) -> list[int]:
        vals = [max(floor, c[name] - step), c[name], c[name] + step]
        if ceiling is not None: vals = [min(ceiling, x) for x in vals]
        if len(set(vals)) != 3: raise ValueError(f"CP153 E factor {name} TL{tl} does not have three distinct levels: {vals}")
        return vals
    gap = lambda name: [1, 2, 3] if c[name] <= 2 else [2, 3, 4]
    return {
        "low_damage": tri("low_damage", 2, 1),
        "standard_damage": tri("standard_damage", 2, 1),
        "overload_damage": tri("overload_damage", 2, 1),
        "accuracy": tri("accuracy", 5, 5, 95),
        "standard_range": tri("standard_range", 1, 1),
        "max_range": tri("max_range", 1, 2),
        "low_tp": tri("low_tp", 1, 1),
        "standard_gap": gap("standard_gap"),
        "overload_gap": gap("overload_gap"),
        "spen": tri("spen", 2, 0),
        "strain_limit": [1, 2, 3, 4],
    }


def _level_code(levels: list[int], center: int, value: int) -> int:
    # Use the level-index displacement, not merely sign(value-center). Some legal
    # factors (notably early TP gaps) have the accepted center at the low edge,
    # so their two non-center levels must remain separately identifiable.
    return int(levels.index(value) - levels.index(center))


def _projective_columns(dim: int) -> list[tuple[int, ...]]:
    cols = [tuple(1 if i == j else 0 for i in range(dim)) for j in range(dim)]
    for v in itertools.product(range(3), repeat=dim):
        if not any(v): continue
        first = next(x for x in v if x); inv = 1 if first == 1 else 2; norm = tuple((x * inv) % 3 for x in v)
        if norm not in cols: cols.append(norm)
    return cols


def _compound_symbols(block: str) -> list[dict[str, int]]:
    cols = _projective_columns(4)
    offset = 0 if block == "A" else 11
    selected = cols[offset:offset + len(E_FACTORS)]
    if len(selected) != len(E_FACTORS): selected = (cols[offset:] + cols[:len(E_FACTORS) - len(cols[offset:])])
    out = []
    for base in itertools.product(range(3), repeat=4):
        row: dict[str, int] = {}
        for name, col in zip(E_FACTORS, selected):
            row[name] = int(sum(a * b for a, b in zip(base, col)) % 3)
        out.append(row)
    return out


def _candidate_from_values(base_matrix: Any, tl: int, values: dict[str, int], codes: dict[str, int], design_class: str, active: int, idx: int) -> dict[str, Any]:
    base = base_matrix.p("energy_main", tl)
    base_low = int(base["lowTp"]); base_std_gap = int(base["standardTp"]) - base_low; base_over_gap = int(base["overloadTp"]) - int(base["standardTp"])
    max_range = max(int(values["max_range"]), int(values["standard_range"]))
    return {
        "lane": "E", "candidate_id": f"EC{tl:02d}-{idx:03d}", "tl": tl, "candidate_index": idx,
        "design_class": design_class, "active_factor_count": active,
        **{f"code_{f}": int(codes[f]) for f in E_FACTORS},
        "candidate_low_damage": int(values["low_damage"]),
        "candidate_standard_damage": int(values["standard_damage"]),
        "candidate_overload_damage": int(values["overload_damage"]),
        "candidate_accuracy": int(values["accuracy"]),
        "candidate_standard_range": int(values["standard_range"]),
        "candidate_max_range": max_range,
        "candidate_low_tp": int(values["low_tp"]),
        "candidate_standard_gap": int(values["standard_gap"]),
        "candidate_overload_gap": int(values["overload_gap"]),
        "candidate_low_tp_delta": int(values["low_tp"]) - base_low,
        "candidate_standard_gap_delta": int(values["standard_gap"]) - base_std_gap,
        "candidate_overload_gap_delta": int(values["overload_gap"]) - base_over_gap,
        "candidate_spen": int(values["spen"]),
        "candidate_strain_limit": int(values["strain_limit"]),
        "candidate_standard_tp": int(values["low_tp"]) + int(values["standard_gap"]),
        "candidate_overload_tp": int(values["low_tp"]) + int(values["standard_gap"]) + int(values["overload_gap"]),
        "apen_policy": "fixed_zero", "forced_overload_policy": "safe_only_normal_doctrine; forced overload remains emergency mechanic outside optimizer",
        "promotion_allowed": 0,
    }


def energy_candidate_ledger(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    _read_cp152_evidence(repo)
    all_rows: list[dict[str, Any]] = []
    base_matrix = _base_matrix(repo, doc, "R1_CENTRAL_NO_MAJOR")
    for tl in range(1, 10):
        levels = energy_factor_levels(doc, tl); centers = _energy_center(doc, tl)
        signatures: dict[tuple[int, ...], tuple[dict[str, int], str, int]] = {}
        zero = {f: 0 for f in E_FACTORS}
        center_values = {f: centers[f] for f in E_FACTORS}
        signatures[tuple(center_values[f] for f in E_FACTORS)] = (zero, "pairwise_center", 0)
        # Complete support<=2 isolation design: every 3x3 pair is observed with all other factors centered;
        # strain has four levels, so every strain x other-factor pair is 4x3.
        alternatives = {f: [x for x in levels[f] if x != centers[f]] for f in E_FACTORS}
        for f in E_FACTORS:
            for v in alternatives[f]:
                vals = dict(center_values); vals[f] = v
                codes = dict(zero); codes[f] = _level_code(levels[f], centers[f], v)
                signatures[tuple(vals[x] for x in E_FACTORS)] = (codes, "pairwise_axis", 1)
        for i, f1 in enumerate(E_FACTORS):
            for f2 in E_FACTORS[i + 1:]:
                for v1, v2 in itertools.product(alternatives[f1], alternatives[f2]):
                    vals = dict(center_values); vals[f1] = v1; vals[f2] = v2
                    codes = dict(zero); codes[f1] = _level_code(levels[f1], centers[f1], v1); codes[f2] = _level_code(levels[f2], centers[f2], v2)
                    signatures[tuple(vals[x] for x in E_FACTORS)] = (codes, "pairwise_isolation", 2)
        if len(signatures) != E_PAIRWISE_CANDIDATES_PER_TL: raise ValueError(f"CP153 TL{tl} pairwise design {len(signatures)} != {E_PAIRWISE_CANDIDATES_PER_TL}")
        # Two 81-run compound OAs validate multi-factor behavior away from the pairwise center.
        for block in ("A", "B"):
            for symbols in _compound_symbols(block):
                vals = dict(center_values); codes = dict(zero)
                for f in E_FACTORS:
                    sym = int(symbols[f])
                    if sym == 0:
                        value = centers[f]
                    elif f == "strain_limit":
                        # Block A validates the immediate 1/3 alternatives around the
                        # accepted center; block B deliberately reaches the new limit-4
                        # boundary without expanding the entire design to four levels.
                        value = ([1, 3] if block == "A" else [1, 4])[sym - 1]
                    else:
                        value = alternatives[f][sym - 1]
                    vals[f] = int(value)
                    codes[f] = _level_code(levels[f], centers[f], int(value))
                sig = tuple(vals[x] for x in E_FACTORS)
                if sig not in signatures: signatures[sig] = (codes, f"compound_oa81_{block}", sum(1 for x in codes.values() if x != 0))
        if len(signatures) != E_TOTAL_CANDIDATES_PER_TL: raise ValueError(f"CP153 TL{tl} total E design {len(signatures)} != {E_TOTAL_CANDIDATES_PER_TL}")
        for idx, (sig, meta) in enumerate(signatures.items()):
            values = {f: sig[i] for i, f in enumerate(E_FACTORS)}; codes, design_class, active = meta
            all_rows.append(_candidate_from_values(base_matrix, tl, values, codes, design_class, active, idx))
    return all_rows


def _screen_contexts(repo: Path, doc: dict[str, Any]) -> list[dict[str, str]]:
    rows = _read_csv(repo / doc["stageAExperimentManifest"]); groups: dict[tuple[Any, ...], list[dict[str, str]]] = defaultdict(list)
    for r in rows: groups[(int(r["tl"]), r["side_a_weapon"], r["side_b_weapon"], r["scenario_stratum"])].append(r)
    out = []
    for key in sorted(groups, key=lambda x: tuple(str(y) for y in x)):
        g = sorted(groups[key], key=lambda r: r["resource_ensemble_id"])
        pos = (key[0] + sum(ord(ch) for ch in "|".join(map(str, key[1:])))) % len(g)
        out.append(g[pos])
    if len(out) != SCREEN_CONTEXTS: raise ValueError(f"CP153 screen panel {len(out)} != {SCREEN_CONTEXTS}")
    return out


def validate_study(doc: dict[str, Any]) -> list[str]:
    e = []
    if doc.get("schemaVersion") != "star-cluster-cp153-four-main-ladder-synthesis-study-v0.1": e.append("schema")
    if int(doc.get("checkpoint", 0)) != 153 or int(doc.get("baseCheckpoint", 0)) != 152: e.append("checkpoint")
    if int(doc.get("energyCandidatesPerTl", 0)) != E_TOTAL_CANDIDATES_PER_TL or int(doc.get("energyPairwiseCandidatesPerTl", 0)) != E_PAIRWISE_CANDIDATES_PER_TL: e.append("energy-design")
    if int(doc.get("energyTrialsPerCell", 0)) != E_TRIALS or int(doc.get("expectedEnergyCombatTrials", 0)) != E_COMBATS: e.append("energy-scale")
    if int(doc.get("wholeLadderPackageCount", 0)) != PACKAGE_COUNT or int(doc.get("screenCombatTrials", 0)) != SCREEN_COMBATS or int(doc.get("deepCombatTrials", 0)) != DEEP_COMBATS: e.append("package-scale")
    if int(doc.get("expectedTotalCombatTrials", 0)) != SUBSTANTIVE_COMBATS: e.append("total-scale")
    if doc.get("heldFixed") != ["Hull capacity", "Shield capacity", "Armor capacity", "Shield Regen=2", "Armor Repair=2", "PDS", "AUX", "ECM/ECCM/Sensor", "Reactor ladder", "DEF/RES", "movement and missile cadence"]: e.append("held-fixed")
    if bool(doc.get("automaticPromotion", True)) or bool(doc.get("tuningAllowed", True)) or bool(doc.get("stageBAutomatic", True)): e.append("promotion")
    return e


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    e = []; _read_cp152_evidence(repo)
    man = _read_csv(repo / doc["stageAExperimentManifest"])
    if len(man) != EXPECTED_STAGE_A: e.append("stage-a")
    led = energy_candidate_ledger(repo, doc)
    if len(led) != E_TOTAL_CANDIDATES_PER_TL * 9: e.append("energy-candidate-count")
    for tl in range(1, 10):
        if len(direct_contexts(repo, doc, "E", tl)) != E_CONTEXTS_BY_TL[tl]: e.append(f"E-contexts-{tl}")
    if len(_screen_contexts(repo, doc)) != SCREEN_CONTEXTS: e.append("screen-panel")
    return e


def run_plan(repo: Path, study_path: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc); outdir.mkdir(parents=True, exist_ok=True)
    led = energy_candidate_ledger(repo, doc); _write_csv(outdir / "energy_closure_candidate_ledger.csv", led); _write_csv(outdir / "four_main_screen_context_panel.csv", _screen_contexts(repo, doc))
    rows = []
    for tl in range(1, 10):
        rows.append({"tl": tl, "energy_candidates": E_TOTAL_CANDIDATES_PER_TL, "energy_pairwise_candidates": E_PAIRWISE_CANDIDATES_PER_TL, "energy_contexts": E_CONTEXTS_BY_TL[tl], "energy_trials_per_cell": E_TRIALS, "energy_combats": E_TOTAL_CANDIDATES_PER_TL * E_CONTEXTS_BY_TL[tl] * E_TRIALS})
    _write_csv(outdir / "energy_closure_design_summary.csv", rows)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": "plan", "passed": not errs, "failedGates": errs,
         "energyTlCandidates": len(led), "energyCandidateContextCells": E_CELLS, "energyCombatTrials": E_COMBATS, "energySmokeCombatTrials": E_SMOKE_COMBATS,
         "kLadders": K_LADDERS, "eLadders": E_LADDERS, "gpLadders": GP_LADDERS, "swLadders": SW_LADDERS, "wholeLadderPackages": PACKAGE_COUNT,
         "screenContexts": SCREEN_CONTEXTS, "screenCombatTrials": SCREEN_COMBATS, "deepPackages": DEEP_PACKAGES, "deepCombatTrials": DEEP_COMBATS,
         "totalCombatTrials": SUBSTANTIVE_COMBATS, "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


# ---------- Energy closure execution ----------

_E_BASE: dict[str, Any] | None = None
_E_CANDS: dict[str, dict[str, Any]] | None = None
_E_CACHE: dict[tuple[str, int, str], Any] | None = None


def _e_worker_init(repo_text: str, doc: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    global _E_BASE, _E_CANDS, _E_CACHE
    repo = Path(repo_text); er, tr = _resource_rows(repo, doc); resources = sorted({r["ensemble_id"] for r in er})
    _E_BASE = {rid: _apply_cp151_center(build_deep_resource_matrix(repo, doc["matrix"], rid, er, tr)) for rid in resources}
    _E_CANDS = {r["candidate_id"]: r for r in candidates}; _E_CACHE = {}


def _apply_e_candidate(base: Any, tl: int, c: dict[str, Any]) -> Any:
    m = _copy_matrix(base); e = m.p("energy_main", tl)
    e["lowDamage"] = int(c["candidate_low_damage"]); e["standardDamage"] = int(c["candidate_standard_damage"]); e["overloadDamage"] = int(c["candidate_overload_damage"]); e["highDamage"] = int(c["candidate_overload_damage"])
    e["accuracyPp"] = int(c["candidate_accuracy"]); e["standardRange"] = int(c["candidate_standard_range"]); e["maxRange"] = max(int(c["candidate_max_range"]), int(e["standardRange"]))
    e["lowTp"] = int(c["candidate_low_tp"]); e["standardTp"] = int(c["candidate_standard_tp"]); e["overloadTp"] = int(c["candidate_overload_tp"]); e["spen"] = int(c["candidate_spen"]); e["apen"] = 0; e["strainLimit"] = int(c["candidate_strain_limit"])
    return m


def _e_matrix(resource: str, tl: int, cid: str):
    if _E_BASE is None or _E_CANDS is None or _E_CACHE is None: raise RuntimeError("CP153 E worker not initialized")
    key = (resource, tl, cid)
    if key not in _E_CACHE: _E_CACHE[key] = _apply_e_candidate(_E_BASE[resource], tl, _E_CANDS[cid])
    return _E_CACHE[key]


def _e_task(args: tuple[int, dict[str, str], dict[str, Any], int, int]) -> dict[str, Any]:
    idx, src, c, seed, trials = args; tl = int(src["tl"]); m = _e_matrix(src["resource_ensemble_id"], tl, c["candidate_id"]); bound = bind_scenario(m, src)
    wc._WORKER_MATRICES = {src["resource_ensemble_id"]: m}
    row = wc._substantive_task((idx, src, bound, seed, trials, doc_doctrine := "cp147_tactical_utility")); row.update({"lane": "E", "candidate_id": c["candidate_id"], "candidate_index": c["candidate_index"]})
    for k, v in c.items():
        if k.startswith("candidate_") or k.startswith("code_") or k in ("design_class", "active_factor_count"): row[k] = v
    return row


def _energy_smoke_contexts(repo: Path, doc: dict[str, Any], tl: int) -> list[dict[str, str]]:
    rs = direct_contexts(repo, doc, "E", tl); groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in rs: groups[(r["resource_ensemble_id"], r["scenario_stratum"])].append(r)
    out = []
    for key in sorted(groups):
        g = sorted(groups[key], key=lambda r: r["scenario_id"]); pos = (tl + sum(ord(x) for x in (key[0] + key[1] + "E153"))) % len(g); out.append(g[pos])
    if len(out) != E_SMOKE_CONTEXTS: raise ValueError(f"CP153 E TL{tl} smoke contexts {len(out)} != {E_SMOKE_CONTEXTS}")
    return out


def run_energy_batch(repo: Path, study_path: Path, outdir: Path, jobs: int = 24, tl: int = 1, candidate_start: int = 0, candidate_end: int | None = None, trials: int | None = None, smoke_panel: bool = False) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    led = [r for r in energy_candidate_ledger(repo, doc) if int(r["tl"]) == tl]; start = max(0, candidate_start); end = len(led) if candidate_end is None else min(len(led), candidate_end); selected = led[start:end]
    if not selected: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["empty-batch"]}
    contexts = _energy_smoke_contexts(repo, doc, tl) if smoke_panel else direct_contexts(repo, doc, "E", tl); ntrials = int(trials or E_TRIALS); tasks = []; idx = 0
    for c in selected:
        for src in contexts: tasks.append((idx, src, c, int(doc["masterSeed"]), ntrials)); idx += 1
    outdir.mkdir(parents=True, exist_ok=True); jobs = max(1, min(jobs, len(tasks)))
    if jobs == 1:
        _e_worker_init(str(repo), doc, selected); rows = [_e_task(t) for t in tasks]
    else:
        ctx = get_context("spawn"); chunksize = min(16, max(1, len(tasks) // max(1, jobs * 8)))
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_e_worker_init, initargs=(str(repo), doc, selected)) as ex: rows = list(ex.map(_e_task, tasks, chunksize=chunksize))
    rows.sort(key=lambda r: (int(r["candidate_index"]), int(r["scenario_index"]))); _write_csv(outdir / "energy_closure_candidate_context_results.csv", rows)
    failures = []
    if len(rows) != len(selected) * len(contexts): failures.append("row-count")
    if any(int(r["error_trials"]) for r in rows): failures.append("errors")
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": "energy-batch", "lane": "E", "passed": not failures, "failedGates": failures, "tl": tl, "smokePanel": smoke_panel,
         "candidateStart": start, "candidateEnd": end, "candidates": len(selected), "contextsPerCandidate": len(contexts), "candidateContextCells": len(rows), "trialsPerContext": ntrials,
         "combatTrials": len(rows) * ntrials, "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in rows), "errors": sum(int(r["error_trials"]) for r in rows)}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


def _combine_agg(z: DirectAgg, a: DirectAgg) -> None:
    z.trials += a.trials; z.wins += a.wins; z.draws += a.draws; z.turns += a.turns; z.duration += a.duration; z.caps += a.caps; z.errors += a.errors; z.damage += a.damage; z.mode_low += a.mode_low; z.mode_std += a.mode_std; z.mode_over += a.mode_over; z.tp_fulfill += a.tp_fulfill; z.tp_weight += a.tp_weight


def merge_energy(repo: Path, study_path: Path, batch_root: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc); outdir.mkdir(parents=True, exist_ok=True)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    ledger = energy_candidate_ledger(repo, doc); led = {(int(r["tl"]), r["candidate_id"]): r for r in ledger}; groups = {}; opp = {}; res = {}; strata = {}; factor = {}; pair = {}; isolated_factor = {}; isolated_pair = {}; audits = []; seen = set(); total_rows = total_trials = total_caps = total_errors = 0
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp = d / "summary.json"; rp = d / "energy_closure_candidate_context_results.csv"
        if not sp.exists() or not rp.exists(): continue
        s = json.loads(sp.read_text(encoding="utf-8-sig")); ok = bool(s.get("passed")) and not bool(s.get("smokePanel")) and int(s.get("trialsPerContext", 0)) == E_TRIALS and int(s.get("errors", -1)) == 0; nr = nt = 0
        if ok:
            with rp.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    nr += 1; n = int(r["trials"]); nt += n; total_rows += 1; total_trials += n; total_caps += int(r["turn_cap_sentinels"]); total_errors += int(r["error_trials"]); key = (int(r["tl"]), r["candidate_id"], r["scenario_id"])
                    if key in seen: continue
                    seen.add(key); tl = int(r["tl"]); cid = r["candidate_id"]; c = led[(tl, cid)]; side = _candidate_side(r, "E"); opponent = r["side_b_weapon"] if side == "A" else r["side_a_weapon"]
                    for g, k in ((groups, (tl, cid)), (opp, (tl, cid, opponent)), (res, (tl, cid, r["resource_ensemble_id"])), (strata, (tl, cid, r["scenario_stratum"]))): g.setdefault(k, DirectAgg()).add(r, side)
                    active = {f for f in E_FACTORS if int(c[f"code_{f}"]) != 0}
                    for f1 in E_FACTORS:
                        factor.setdefault((tl, f1, int(c[f"code_{f1}"]), cid), DirectAgg()).add(r, side)
                        if active.issubset({f1}): isolated_factor.setdefault((tl, f1, int(c[f"code_{f1}"])), DirectAgg()).add(r, side)
                    for i, f1 in enumerate(E_FACTORS):
                        for f2 in E_FACTORS[i + 1:]:
                            pair.setdefault((tl, f1, int(c[f"code_{f1}"]), f2, int(c[f"code_{f2}"])), DirectAgg()).add(r, side)
                            if active.issubset({f1, f2}): isolated_pair.setdefault((tl, f1, int(c[f"code_{f1}"]), f2, int(c[f"code_{f2}"])), DirectAgg()).add(r, side)
        audits.append({"batch": d.name, "rows": nr, "combat_trials": nt, "passed": int(ok)})
    if total_rows != E_CELLS: errs.append("row-count")
    if total_trials != E_COMBATS: errs.append("trial-count")
    if len(seen) != E_CELLS: errs.append("coverage")
    if total_errors: errs.append("errors")
    def conv(g, names): return [{**{n: v for n, v in zip(names, k)}, **a.row()} for k, a in sorted(g.items(), key=lambda kv: tuple(str(x) for x in kv[0]))]
    overall = conv(groups, ("tl", "candidate_id")); opponent = conv(opp, ("tl", "candidate_id", "opponent")); resource = conv(res, ("tl", "candidate_id", "resource_ensemble_id")); stratum = conv(strata, ("tl", "candidate_id", "scenario_stratum"))
    factor2 = {}
    for (tl, f, level, cid), a in factor.items(): _combine_agg(factor2.setdefault((tl, f, level), DirectAgg()), a)
    marginals = conv(factor2, ("tl", "factor", "level")); interactions = conv(pair, ("tl", "factor_1", "level_1", "factor_2", "level_2"))
    isolated_marginals = conv(isolated_factor, ("tl", "factor", "level")); isolated_interactions = conv(isolated_pair, ("tl", "factor_1", "level_1", "factor_2", "level_2"))
    opp_index = defaultdict(list); res_index = defaultdict(list)
    for r in opponent: opp_index[(int(r["tl"]), r["candidate_id"])].append(r)
    for r in resource: res_index[(int(r["tl"]), r["candidate_id"])].append(r)
    enriched = []
    for r in overall:
        key = (int(r["tl"]), r["candidate_id"]); c = led[key]; ors = opp_index[key]; rrs = res_index[key]
        enriched.append({**r, **{k: v for k, v in c.items() if k.startswith("candidate_") or k in ("design_class", "active_factor_count")}, "min_opponent_win_rate": min(float(x["win_rate"]) for x in ors), "max_opponent_win_rate": max(float(x["win_rate"]) for x in ors), "resource_win_rate_range": max(float(x["win_rate"]) for x in rrs) - min(float(x["win_rate"]) for x in rrs), "promotion_allowed": 0})
    _write_csv(outdir / "batch_merge_audit.csv", audits); _write_csv(outdir / "energy_closure_candidate_summary.csv", enriched); _write_csv(outdir / "energy_closure_candidate_opponent_response.csv", opponent); _write_csv(outdir / "energy_closure_candidate_resource_response.csv", resource); _write_csv(outdir / "energy_closure_candidate_stratum_response.csv", stratum); _write_csv(outdir / "energy_closure_factor_marginals.csv", marginals); _write_csv(outdir / "energy_closure_pairwise_response.csv", interactions); _write_csv(outdir / "energy_closure_isolated_factor_response.csv", isolated_marginals); _write_csv(outdir / "energy_closure_isolated_pairwise_response.csv", isolated_interactions)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": "energy-merged", "passed": not errs, "failedGates": errs, "candidateContextCells": total_rows, "combatTrials": total_trials, "turnCapSentinels": total_caps, "errorTrials": total_errors, "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


# ---------- Whole-ladder synthesis ----------

def _decisive(r: dict[str, Any]) -> float:
    wr = float(r.get("win_rate", 0)); dr = float(r.get("draw_rate", 0)); denom = max(1e-9, 1.0 - dr); return max(0.0, min(1.0, wr / denom))


def _local_cost(r: dict[str, Any], family: str) -> float:
    dec = _decisive(r); cost = 1.6 * abs(dec - 0.5) + 0.35 * float(r.get("resource_win_rate_range", 0) or 0) + 0.6 * max(0.0, 0.33 - float(r.get("min_opponent_win_rate", 0.33) or 0.33))
    if family == "E":
        ov = float(r.get("energy_overload_shot_share", 0) or 0); st = float(r.get("energy_standard_shot_share", 0) or 0)
        cost += 1.8 * max(0.0, ov - 0.30) + 0.7 * max(0.0, 0.55 - st)
    return cost


def _normalize_cp152_e(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    p = repo / "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_E_CANDIDATE_SUMMARY.csv"; rows = _read_csv(p); base = _base_matrix(repo, doc, "R1_CENTRAL_NO_MAJOR"); out = []
    for r in rows:
        tl = int(r["tl"]); e = base.p("energy_main", tl); low = max(1, int(e["lowTp"]) + int(float(r["candidate_low_tp_delta"]))); sg = max(1, int(e["standardTp"]) - int(e["lowTp"]) + int(float(r["candidate_standard_gap_delta"]))); og = max(1, int(e["overloadTp"]) - int(e["standardTp"]) + int(float(r["candidate_overload_gap_delta"])));
        x = dict(r); x["candidate_id"] = "CP152_" + r["candidate_id"]; x["source"] = "accepted_cp152"; x["candidate_max_range"] = str(max(int(float(r["candidate_max_range"])), int(float(r["candidate_standard_range"])))); x["candidate_low_tp"] = str(low); x["candidate_standard_gap"] = str(sg); x["candidate_overload_gap"] = str(og); x["candidate_standard_tp"] = str(low + sg); x["candidate_overload_tp"] = str(low + sg + og); out.append(x)
    return out


def _normalize_cp153_e(merged: Path) -> list[dict[str, Any]]:
    rows = _read_csv(merged / "energy_closure_candidate_summary.csv")
    for r in rows: r["source"] = "cp153_closure"
    return rows


def _beam_ladders(candidates_by_tl: dict[int, list[dict[str, Any]]], family: str, count: int, center_matrix: Any) -> list[list[dict[str, Any]]]:
    fields = ("candidate_damage", "candidate_accuracy", "candidate_standard_range", "candidate_max_range") if family == "K" else ("candidate_low_damage", "candidate_standard_damage", "candidate_overload_damage", "candidate_accuracy", "candidate_standard_range", "candidate_max_range", "candidate_spen", "candidate_strain_limit")
    local = {}
    for tl in range(1, 10):
        uniq = {}
        for r in candidates_by_tl[tl]:
            sig = tuple(int(float(r[f])) for f in fields)
            if family == "E": sig += (int(float(r["candidate_low_tp"])), int(float(r["candidate_standard_gap"])), int(float(r["candidate_overload_gap"])))
            if sig not in uniq or _local_cost(r, family) < _local_cost(uniq[sig], family): uniq[sig] = r
        local[tl] = sorted(uniq.values(), key=lambda r: (_local_cost(r, family), r["candidate_id"]))[:90]
    beam: list[tuple[float, list[dict[str, Any]]]] = [(0.0, [])]
    for tl in range(1, 10):
        nxt = []
        for cost, path in beam:
            for r in local[tl]:
                if family == "E" and not (int(float(r["candidate_low_damage"])) < int(float(r["candidate_standard_damage"])) <= int(float(r["candidate_overload_damage"]))): continue
                if path:
                    q = path[-1]
                    if any(int(float(r[f])) < int(float(q[f])) for f in fields): continue
                jump = 0.0
                if path:
                    q = path[-1]
                    if family == "K": jump = 0.003 * sum(max(0, int(float(r[f])) - int(float(q[f])) - lim) for f, lim in (("candidate_damage", 4), ("candidate_accuracy", 10), ("candidate_standard_range", 1), ("candidate_max_range", 2)))
                    else: jump = 0.002 * sum(max(0, int(float(r[f])) - int(float(q[f])) - lim) for f, lim in (("candidate_standard_damage", 4), ("candidate_overload_damage", 4), ("candidate_accuracy", 10), ("candidate_standard_range", 1), ("candidate_max_range", 2), ("candidate_strain_limit", 1)))
                nxt.append((cost + _local_cost(r, family) + jump, path + [r]))
        nxt.sort(key=lambda x: (x[0], tuple(r["candidate_id"] for r in x[1]))); beam = nxt[:5000]
        if not beam: raise ValueError(f"CP153 could not build coherent {family} ladder through TL{tl}")
    # Greedy diversity over the best beam. E explicitly favors distinct Strain Limit trajectories.
    chosen = []
    for cost, path in beam[:1200]:
        core = tuple(tuple(int(float(r[f])) for f in fields) for r in path); strain = tuple(int(float(r["candidate_strain_limit"])) for r in path) if family == "E" else ()
        if any(core == x[2] for x in chosen): continue
        if family == "E" and sum(1 for x in chosen if x[3] == strain) >= 1 and len(chosen) < min(4, count): continue
        chosen.append((cost, path, core, strain))
        if len(chosen) >= count: break
    if len(chosen) < count:
        for cost, path in beam:
            core = tuple(tuple(int(float(r[f])) for f in fields) for r in path); strain = tuple(int(float(r["candidate_strain_limit"])) for r in path) if family == "E" else ()
            if any(core == x[2] for x in chosen): continue
            chosen.append((cost, path, core, strain))
            if len(chosen) >= count: break
    if len(chosen) != count: raise ValueError(f"CP153 {family} ladder count {len(chosen)} != {count}")
    return [x[1] for x in chosen]


def _k_ladders(repo: Path, doc: dict[str, Any]) -> list[list[dict[str, Any]]]:
    rows = _read_csv(repo / "docs/validation/evidence/checkpoint-153/accepted-cp152/CP152_DIRECT_FIRE_K_CANDIDATE_SUMMARY.csv"); by = defaultdict(list)
    for r in rows:
        r = dict(r); r["candidate_max_range"] = str(max(int(float(r["candidate_max_range"])), int(float(r["candidate_standard_range"])))); by[int(r["tl"])].append(r)
    return _beam_ladders(by, "K", K_LADDERS, _base_matrix(repo, doc, "R1_CENTRAL_NO_MAJOR"))


def _e_ladders(repo: Path, doc: dict[str, Any], merged: Path) -> list[list[dict[str, Any]]]:
    by = defaultdict(list)
    for r in _normalize_cp152_e(repo, doc) + _normalize_cp153_e(merged): by[int(r["tl"])].append(r)
    return _beam_ladders(by, "E", E_LADDERS, _base_matrix(repo, doc, "R1_CENTRAL_NO_MAJOR"))


def _missile_ladder_options(repo: Path, doc: dict[str, Any], family: str) -> list[dict[int, int]]:
    # CP151 exported dedicated axial candidates after the OA block. Use those exact
    # tested points rather than trying to infer an axis row from the OA itself.
    root = repo / "docs/validation/evidence/checkpoint-152/accepted-cp151"
    ledger = _read_csv(root / "CP151_POINT_SCALE_CANDIDATE_LEDGER.CSV")
    response = _read_csv(root / "CP151_POINT_SCALE_CANDIDATE_FAMILY_RESPONSE.CSV")
    axial = _read_csv(root / "CP151_POINT_SCALE_AXIAL_FAMILY_EFFECTS.CSV")
    factor = "gp_damage" if family == "M_GP" else "swarmer_packet_damage"
    candidate_field = "candidate_gp_damage" if family == "M_GP" else "candidate_swarmer_packet_damage"
    weapon = family
    lindex = {(int(r["tl"]), r["candidate_id"]): r for r in ledger}
    rindex = {(int(r["tl"]), r["candidate_id"], r["weapon"]): r for r in response}
    centers = _base_matrix(repo, doc, "R1_CENTRAL_NO_MAJOR")
    tls = list(range(1, 10)) if family == "M_GP" else list(range(2, 10))
    profile = "missile_gp_warhead" if family == "M_GP" else "missile_swarmer"
    value_field = "damage" if family == "M_GP" else "packetDamage"
    basevals = {tl: int(centers.p(profile, tl)[value_field]) for tl in tls}
    by_tl: dict[int, dict[int, float]] = {}
    actual_by_tl: dict[int, dict[int, int]] = {}
    for tl in tls:
        center_id = f"PS{tl:02d}-000"
        rr0 = rindex[(tl, center_id, weapon)]
        by_tl[tl] = {0: abs(_decisive(rr0) - 0.5)}
        actual_by_tl[tl] = {0: basevals[tl]}
        for direction in (-1, 1):
            ar = next((r for r in axial if int(r["tl"]) == tl and r["factor"] == factor and int(r["direction"]) == direction and r["weapon"] == weapon), None)
            if ar is None: raise ValueError(f"CP153 missing CP151 axial {factor} TL{tl} direction {direction}")
            cid = ar["candidate_id"]
            rr = rindex[(tl, cid, weapon)]
            by_tl[tl][direction] = abs(_decisive(rr) - 0.5)
            actual_by_tl[tl][direction] = int(float(lindex[(tl, cid)][candidate_field]))
    ranked = []
    for seq in itertools.product((-1, 0, 1), repeat=len(tls)):
        actual = {tl: actual_by_tl[tl][seq[i]] for i, tl in enumerate(tls)}
        if any(actual[tls[i]] < actual[tls[i - 1]] for i in range(1, len(tls))): continue
        cost = sum(by_tl[tl][seq[i]] for i, tl in enumerate(tls)) + 0.015 * sum(abs(seq[i] - seq[i - 1]) for i in range(1, len(seq)))
        ranked.append((cost, seq, actual))
    ranked.sort(key=lambda x: (x[0], x[1]))
    center = {tl: basevals[tl] for tl in tls}
    options = [center]
    for _, seq, actual in ranked:
        if all(x == 0 for x in seq): continue
        if actual not in options: options.append(actual)
        if len(options) == 3: break
    if len(options) != 3: raise ValueError(f"CP153 {family} missile ladder options {len(options)} != 3")
    return options


def synthesize_ladders(repo: Path, study_path: Path, energy_merged: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc); outdir.mkdir(parents=True, exist_ok=True)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    ks = _k_ladders(repo, doc); es = _e_ladders(repo, doc, energy_merged); gps = _missile_ladder_options(repo, doc, "M_GP"); sws = _missile_ladder_options(repo, doc, "M_SWARMER"); base = _base_matrix(repo, doc, "R1_CENTRAL_NO_MAJOR")
    krows = []; erows = []; mrows = []
    for i, ladder in enumerate(ks):
        for tl, r in enumerate(ladder, 1):
            krows.append({"ladder_id": f"K{i+1}", "rank": i + 1, "tl": tl, "source_candidate_id": r["candidate_id"], "damage": int(float(r["candidate_damage"])), "accuracy": int(float(r["candidate_accuracy"])), "standard_range": int(float(r["candidate_standard_range"])), "max_range": max(int(float(r["candidate_max_range"])), int(float(r["candidate_standard_range"]))), "apen": int(base.p("kinetic_main", tl)["apen"]), "selection_cost": _local_cost(r, "K"), "promotion_allowed": 0})
    for i, ladder in enumerate(es):
        for tl, r in enumerate(ladder, 1):
            erows.append({"ladder_id": f"E{i+1}", "rank": i + 1, "tl": tl, "source_candidate_id": r["candidate_id"], "source": r.get("source", "cp153_closure"), "low_damage": int(float(r["candidate_low_damage"])), "standard_damage": int(float(r["candidate_standard_damage"])), "overload_damage": int(float(r["candidate_overload_damage"])), "accuracy": int(float(r["candidate_accuracy"])), "standard_range": int(float(r["candidate_standard_range"])), "max_range": max(int(float(r["candidate_max_range"])), int(float(r["candidate_standard_range"]))), "low_tp": int(float(r["candidate_low_tp"])), "standard_gap": int(float(r["candidate_standard_gap"])), "overload_gap": int(float(r["candidate_overload_gap"])), "spen": int(float(r["candidate_spen"])), "strain_limit": int(float(r["candidate_strain_limit"])), "selection_cost": _local_cost(r, "E"), "promotion_allowed": 0})
    for fam, opts in (("M_GP", gps), ("M_SWARMER", sws)):
        for i, opt in enumerate(opts):
            for tl in range(1, 10):
                if fam == "M_SWARMER" and tl == 1: continue
                mrows.append({"family": fam, "ladder_id": ("M" if fam == "M_GP" else "SW") + str(i + 1), "rank": i + 1, "tl": tl, "damage": opt[tl], "promotion_allowed": 0})
    _write_csv(outdir / "kinetic_ladder_candidates.csv", krows); _write_csv(outdir / "energy_ladder_candidates.csv", erows); _write_csv(outdir / "missile_ladder_candidates.csv", mrows)
    kmap = defaultdict(dict); emap = defaultdict(dict); mmap = defaultdict(dict); swmap = defaultdict(dict)
    for r in krows: kmap[r["ladder_id"]][int(r["tl"])] = r
    for r in erows: emap[r["ladder_id"]][int(r["tl"])] = r
    for r in mrows: (mmap if r["family"] == "M_GP" else swmap)[r["ladder_id"]][int(r["tl"])] = r
    packages = []; pidx = 0
    for kid, eid, mid, sid in itertools.product(sorted(kmap), sorted(emap), sorted(mmap), sorted(swmap)):
        pid = f"FM{pidx:03d}"; pidx += 1
        for tl in range(1, 10):
            k = kmap[kid][tl]; e = emap[eid][tl]; m = mmap[mid][tl]; sw = swmap[sid].get(tl)
            packages.append({"package_id": pid, "package_index": pidx - 1, "k_ladder": kid, "e_ladder": eid, "m_ladder": mid, "sw_ladder": sid, "tl": tl,
                             "k_damage": k["damage"], "k_accuracy": k["accuracy"], "k_standard_range": k["standard_range"], "k_max_range": k["max_range"], "k_apen": k["apen"],
                             "e_low_damage": e["low_damage"], "e_standard_damage": e["standard_damage"], "e_overload_damage": e["overload_damage"], "e_accuracy": e["accuracy"], "e_standard_range": e["standard_range"], "e_max_range": e["max_range"], "e_low_tp": e["low_tp"], "e_standard_gap": e["standard_gap"], "e_overload_gap": e["overload_gap"], "e_spen": e["spen"], "e_strain_limit": e["strain_limit"],
                             "m_damage": m["damage"], "sw_packet_damage": "" if sw is None else sw["damage"], "promotion_allowed": 0})
    _write_csv(outdir / "four_main_package_tl_ledger.csv", packages)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": "ladder-selection", "passed": len(packages) == PACKAGE_COUNT * 9, "failedGates": [] if len(packages) == PACKAGE_COUNT * 9 else ["package-count"], "kLadders": len(ks), "eLadders": len(es), "gpLadders": len(gps), "swLadders": len(sws), "packages": PACKAGE_COUNT, "packageTlRows": len(packages), "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


# ---------- Four-family package execution ----------

_P_BASE: dict[str, Any] | None = None
_P_ROWS: dict[tuple[str, int], dict[str, Any]] | None = None
_P_CACHE: dict[tuple[str, int, str], Any] | None = None


def _read_package_rows(path: Path) -> list[dict[str, Any]]:
    rows = _read_csv(path); out = []
    for r in rows:
        x = dict(r); x["package_index"] = int(x["package_index"]); x["tl"] = int(x["tl"])
        for k in list(x):
            if k.startswith(("k_", "e_", "m_", "sw_")) and k not in ("k_ladder", "e_ladder", "m_ladder", "sw_ladder") and x[k] != "":
                try: x[k] = int(float(x[k]))
                except ValueError: pass
        out.append(x)
    return out


def _p_worker_init(repo_text: str, doc: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    global _P_BASE, _P_ROWS, _P_CACHE
    repo = Path(repo_text); er, tr = _resource_rows(repo, doc); resources = sorted({r["ensemble_id"] for r in er}); _P_BASE = {rid: _apply_cp151_center(build_deep_resource_matrix(repo, doc["matrix"], rid, er, tr)) for rid in resources}; _P_ROWS = {(r["package_id"], int(r["tl"])): r for r in rows}; _P_CACHE = {}


def _apply_package(base: Any, tl: int, r: dict[str, Any]) -> Any:
    m = _copy_matrix(base); k = m.p("kinetic_main", tl); k["damage"] = int(r["k_damage"]); k["accuracyPp"] = int(r["k_accuracy"]); k["standardRange"] = int(r["k_standard_range"]); k["maxRange"] = max(int(r["k_max_range"]), int(k["standardRange"])); k["apen"] = int(r["k_apen"]); k["spen"] = 0
    e = m.p("energy_main", tl); e["lowDamage"] = int(r["e_low_damage"]); e["standardDamage"] = int(r["e_standard_damage"]); e["overloadDamage"] = int(r["e_overload_damage"]); e["highDamage"] = int(r["e_overload_damage"]); e["accuracyPp"] = int(r["e_accuracy"]); e["standardRange"] = int(r["e_standard_range"]); e["maxRange"] = max(int(r["e_max_range"]), int(e["standardRange"])); e["lowTp"] = int(r["e_low_tp"]); e["standardTp"] = int(r["e_low_tp"]) + int(r["e_standard_gap"]); e["overloadTp"] = e["standardTp"] + int(r["e_overload_gap"]); e["spen"] = int(r["e_spen"]); e["apen"] = 0; e["strainLimit"] = int(r["e_strain_limit"])
    gp = m.p("missile_gp_warhead", tl); gp["damage"] = int(r["m_damage"]); gp["apen"] = 0; gp["spen"] = 0
    if tl >= 2 and r.get("sw_packet_damage", "") != "":
        sw = m.p("missile_swarmer", tl); sw["packetDamage"] = int(r["sw_packet_damage"]); sw["apen"] = 0; sw["spen"] = 0
    return m


def _p_matrix(resource: str, tl: int, pid: str):
    if _P_BASE is None or _P_ROWS is None or _P_CACHE is None: raise RuntimeError("CP153 package worker not initialized")
    key = (resource, tl, pid)
    if key not in _P_CACHE: _P_CACHE[key] = _apply_package(_P_BASE[resource], tl, _P_ROWS[(pid, tl)])
    return _P_CACHE[key]


def _p_task(args: tuple[int, dict[str, str], str, int, int]) -> dict[str, Any]:
    idx, src, pid, seed, trials = args; tl = int(src["tl"]); m = _p_matrix(src["resource_ensemble_id"], tl, pid); bound = bind_scenario(m, src); wc._WORKER_MATRICES = {src["resource_ensemble_id"]: m}; row = wc._substantive_task((idx, src, bound, seed, trials, "cp147_tactical_utility")); row.update({"package_id": pid}); return row


def run_package_batch(repo: Path, study_path: Path, package_ledger_path: Path, outdir: Path, mode: str, jobs: int = 24, package_start: int = 0, package_end: int | None = None, trials: int | None = None) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    rows = _read_package_rows(package_ledger_path); by = defaultdict(list)
    for r in rows: by[r["package_id"]].append(r)
    ids = sorted(by, key=lambda pid: min(int(x["package_index"]) for x in by[pid])); start = max(0, package_start); end = len(ids) if package_end is None else min(len(ids), package_end); selected_ids = ids[start:end]
    if not selected_ids: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["empty-package-batch"]}
    selected_rows = [r for pid in selected_ids for r in by[pid]]; contexts = _screen_contexts(repo, doc) if mode == "screen" else _read_csv(repo / doc["stageAExperimentManifest"]); ntrials = int(trials or (SCREEN_TRIALS if mode == "screen" else DEEP_TRIALS)); tasks = []; idx = 0
    for pid in selected_ids:
        for src in contexts: tasks.append((idx, src, pid, int(doc["masterSeed"]) + (400000 if mode == "screen" else 800000), ntrials)); idx += 1
    outdir.mkdir(parents=True, exist_ok=True); jobs = max(1, min(jobs, len(tasks)))
    if jobs == 1:
        _p_worker_init(str(repo), doc, selected_rows); result = [_p_task(t) for t in tasks]
    else:
        ctx = get_context("spawn"); chunksize = min(16, max(1, len(tasks) // max(1, jobs * 8)))
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_p_worker_init, initargs=(str(repo), doc, selected_rows)) as ex: result = list(ex.map(_p_task, tasks, chunksize=chunksize))
    result.sort(key=lambda r: (r["package_id"], int(r["scenario_index"]))); _write_csv(outdir / "four_main_package_context_results.csv", result); failures = []
    if len(result) != len(selected_ids) * len(contexts): failures.append("row-count")
    if any(int(r["error_trials"]) for r in result): failures.append("errors")
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": f"package-{mode}-batch", "passed": not failures, "failedGates": failures, "packageStart": start, "packageEnd": end, "packages": len(selected_ids), "contextsPerPackage": len(contexts), "packageContextCells": len(result), "trialsPerContext": ntrials, "combatTrials": len(result) * ntrials, "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in result), "errors": sum(int(r["error_trials"]) for r in result)}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


class _FamilyAgg:
    def __init__(self): self.trials = self.wins = self.losses = self.draws = 0; self.turns = self.duration = self.caps = self.errors = 0; self.e_low = self.e_std = self.e_over = 0.0
    def add_family(self, r: dict[str, str], side: str):
        n = int(r["trials"]); w = int(r["a_wins"] if side == "A" else r["b_wins"]); d = int(r["draws"]); self.trials += n; self.wins += w; self.draws += d; self.losses += n - w - d; self.turns += float(r["mean_turns_all"]) * n; self.duration += float(r["gameplay_duration_concern_rate"]) * n; self.caps += int(r["turn_cap_sentinels"]); self.errors += int(r["error_trials"])
        if (side == "A" and r["side_a_weapon"] == "E") or (side == "B" and r["side_b_weapon"] == "E"):
            low = side.lower(); self.e_low += float(r.get(f"mean_{low}_energy_low_shots", 0) or 0) * n; self.e_std += float(r.get(f"mean_{low}_energy_standard_shots", 0) or 0) * n; self.e_over += float(r.get(f"mean_{low}_energy_overload_shots", 0) or 0) * n
    def row(self):
        n = self.trials or 1; decisive_n = self.wins + self.losses; modes = self.e_low + self.e_std + self.e_over
        return {"trials": self.trials, "wins": self.wins, "losses": self.losses, "draws": self.draws, "win_rate": self.wins / n, "draw_rate": self.draws / n, "decisive_win_share": self.wins / decisive_n if decisive_n else 0.5, "mean_turns": self.turns / n, "duration_concern_rate": self.duration / n, "turn_cap_sentinels": self.caps, "error_trials": self.errors, "energy_low_shot_share": self.e_low / modes if modes else 0.0, "energy_standard_shot_share": self.e_std / modes if modes else 0.0, "energy_overload_shot_share": self.e_over / modes if modes else 0.0}


def merge_packages(repo: Path, study_path: Path, package_ledger_path: Path, batch_root: Path, outdir: Path, mode: str) -> dict[str, Any]:
    doc = load_json(study_path); outdir.mkdir(parents=True, exist_ok=True); expected_trials = SCREEN_TRIALS if mode == "screen" else DEEP_TRIALS; expected_packages = PACKAGE_COUNT if mode == "screen" else DEEP_PACKAGES; expected_contexts = SCREEN_CONTEXTS if mode == "screen" else EXPECTED_STAGE_A; expected_cells = expected_packages * expected_contexts; expected_combats = expected_cells * expected_trials
    package_rows = _read_package_rows(package_ledger_path); pmeta = {}
    for r in package_rows: pmeta.setdefault(r["package_id"], {k: r[k] for k in ("package_id", "package_index", "k_ladder", "e_ladder", "m_ladder", "sw_ladder")})
    fam = {}; pair = {}; strata = {}; overall = {}; audits = []; seen = set(); rowsn = trials = caps = errors = 0
    order = {"K": 0, "E": 1, "M_GP": 2, "M_SWARMER": 3}
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp = d / "summary.json"; rp = d / "four_main_package_context_results.csv"
        if not sp.exists() or not rp.exists(): continue
        s = json.loads(sp.read_text(encoding="utf-8-sig")); ok = bool(s.get("passed")) and int(s.get("trialsPerContext", 0)) == expected_trials and int(s.get("errors", -1)) == 0 and s.get("mode") == f"package-{mode}-batch"; nr = nt = 0
        if ok:
            with rp.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    nr += 1; n = int(r["trials"]); nt += n; rowsn += 1; trials += n; caps += int(r["turn_cap_sentinels"]); errors += int(r["error_trials"]); key = (r["package_id"], r["scenario_id"])
                    if key in seen: continue
                    seen.add(key); pid = r["package_id"]; a = r["side_a_weapon"]; b = r["side_b_weapon"]; overall.setdefault(pid, _FamilyAgg()).add_family(r, "A")
                    if a != b:
                        fam.setdefault((pid, a), _FamilyAgg()).add_family(r, "A"); fam.setdefault((pid, b), _FamilyAgg()).add_family(r, "B")
                        first, second = (a, b) if order[a] < order[b] else (b, a); side = "A" if a == first else "B"; pair.setdefault((pid, first, second), _FamilyAgg()).add_family(r, side)
                        strata.setdefault((pid, a, r["scenario_stratum"]), _FamilyAgg()).add_family(r, "A"); strata.setdefault((pid, b, r["scenario_stratum"]), _FamilyAgg()).add_family(r, "B")
        audits.append({"batch": d.name, "rows": nr, "combat_trials": nt, "passed": int(ok)})
    errs = []
    if rowsn != expected_cells: errs.append("row-count")
    if trials != expected_combats: errs.append("trial-count")
    if len(seen) != expected_cells: errs.append("coverage")
    if errors: errs.append("errors")
    def conv(g, names): return [{**{n: v for n, v in zip(names, k if isinstance(k, tuple) else (k,))}, **a.row()} for k, a in sorted(g.items(), key=lambda kv: tuple(str(x) for x in (kv[0] if isinstance(kv[0], tuple) else (kv[0],))))]
    fam_rows = conv(fam, ("package_id", "family")); pair_rows = conv(pair, ("package_id", "family_1", "family_2")); stratum_rows = conv(strata, ("package_id", "family", "scenario_stratum")); family_index = defaultdict(list); pair_index = defaultdict(list); stratum_index = defaultdict(list)
    for r in fam_rows: family_index[r["package_id"]].append(r)
    for r in pair_rows: pair_index[r["package_id"]].append(r)
    for r in stratum_rows: stratum_index[r["package_id"]].append(r)
    summary_rows = []
    for pid in sorted(pmeta, key=lambda x: int(pmeta[x]["package_index"])):
        if pid not in family_index: continue
        fr = family_index[pid]; pr = pair_index[pid]; sr = stratum_index[pid]; fdev = max(abs(float(x["decisive_win_share"]) - 0.5) for x in fr); pdev = max(abs(float(x["decisive_win_share"]) - 0.5) for x in pr); minf = min(float(x["decisive_win_share"]) for x in fr); maxf = max(float(x["decisive_win_share"]) for x in fr); strdev = max(abs(float(x["decisive_win_share"]) - 0.5) for x in sr); e = next((x for x in fr if x["family"] == "E"), None); ov = float(e["energy_overload_shot_share"]) if e else 0.0; std = float(e["energy_standard_shot_share"]) if e else 0.0; low = float(e["energy_low_shot_share"]) if e else 0.0; score = 2.0 * pdev + 0.8 * fdev + 0.25 * strdev + 1.5 * max(0.0, ov - 0.30) + 0.5 * max(0.0, 0.55 - std)
        summary_rows.append({**pmeta[pid], "min_family_decisive_share": minf, "max_family_decisive_share": maxf, "max_family_decisive_deviation": fdev, "max_pair_decisive_deviation": pdev, "max_stratum_family_decisive_deviation": strdev, "energy_low_shot_share": low, "energy_standard_shot_share": std, "energy_overload_shot_share": ov, "selection_score": score, "promotion_allowed": 0})
    _write_csv(outdir / "batch_merge_audit.csv", audits); _write_csv(outdir / f"four_main_{mode}_package_summary.csv", summary_rows); _write_csv(outdir / f"four_main_{mode}_family_response.csv", fam_rows); _write_csv(outdir / f"four_main_{mode}_pair_response.csv", pair_rows); _write_csv(outdir / f"four_main_{mode}_stratum_response.csv", stratum_rows)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": f"package-{mode}-merged", "passed": not errs, "failedGates": errs, "packages": len(summary_rows), "packageContextCells": rowsn, "combatTrials": trials, "turnCapSentinels": caps, "errorTrials": errors, "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s


def select_deep(repo: Path, study_path: Path, full_package_ledger: Path, screen_merged: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); outdir.mkdir(parents=True, exist_ok=True); summary = _read_csv(screen_merged / "four_main_screen_package_summary.csv"); summary.sort(key=lambda r: (float(r["selection_score"]), r["package_id"])); chosen = []; used_e = set()
    # Preserve Strain/energy-ladder diversity first: best package from each E ladder.
    for r in summary:
        if r["e_ladder"] not in used_e:
            chosen.append(r); used_e.add(r["e_ladder"])
        if len(used_e) == E_LADDERS: break
    for r in summary:
        if r["package_id"] in {x["package_id"] for x in chosen}: continue
        chosen.append(r)
        if len(chosen) >= DEEP_PACKAGES: break
    chosen = chosen[:DEEP_PACKAGES]; ids = {r["package_id"] for r in chosen}; rows = [r for r in _read_package_rows(full_package_ledger) if r["package_id"] in ids]; order = {r["package_id"]: i for i, r in enumerate(chosen)}; rows.sort(key=lambda r: (order[r["package_id"]], int(r["tl"]))); _write_csv(outdir / "four_main_deep_shortlist.csv", [{"deep_rank": i + 1, **r} for i, r in enumerate(chosen)]); _write_csv(outdir / "four_main_deep_package_tl_ledger.csv", rows)
    s = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 153, "mode": "deep-selection", "passed": len(chosen) == DEEP_PACKAGES and len(rows) == DEEP_PACKAGES * 9, "failedGates": [] if len(chosen) == DEEP_PACKAGES and len(rows) == DEEP_PACKAGES * 9 else ["deep-count"], "deepPackages": len(chosen), "packageTlRows": len(rows), "energyLaddersRepresented": len({r["e_ladder"] for r in chosen}), "automaticPromotion": False}
    (outdir / "summary.json").write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8"); return s
