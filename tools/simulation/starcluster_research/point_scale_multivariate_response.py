from __future__ import annotations

import copy
import csv
import hashlib
import itertools
import json
import math
import statistics
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import fields
from multiprocessing import get_context
from pathlib import Path
from typing import Any

from .canonical_combat import run_trial_full_map
from .combat_surface_deep_reconciliation import build_deep_resource_matrix
from .ecology import SideTelemetry, UTILITY_COMBAT_DOCTRINE
from .stage_a_integration_analysis import _read_csv, _resource_rows, bind_scenario
from .study import load_json
from . import whole_combat_stage_a_response_surface as wc

RESULT_SCHEMA = "star-cluster-cp151-point-scale-multivariate-response-result-v0.1"
SCALE = 2
OA_RUNS = 243
TRIALS_PER_CELL = 25
EXPECTED_STAGE_A = 6850
EXPECTED_CONTEXTS_BY_TL = {1: 450, **{tl: 800 for tl in range(2, 10)}}
SMOKE_CONTEXTS_PER_TL = 50
K_RESEARCH_DAMAGE_OLD_SCALE = {1: 5, 2: 5, 3: 6, 4: 7, 5: 7, 6: 8, 7: 8, 8: 10, 9: 10}

FACTORS = (
    "k_damage",
    "e_low_damage",
    "e_standard_damage",
    "e_overload_damage",
    "gp_damage",
    "swarmer_packet_damage",
    "hull_capacity",
    "shield_capacity",
    "armor_capacity",
    "shield_regen",
    "armor_repair",
    "k_apen",
    "e_spen",
)

POINT_FACTORS = {
    "k_damage", "e_low_damage", "e_standard_damage", "e_overload_damage", "gp_damage",
    "swarmer_packet_damage", "hull_capacity", "shield_capacity", "armor_capacity",
    "shield_regen", "armor_repair",
}
PENETRATION_FACTORS = {"k_apen", "e_spen"}

EVIDENCE_HASHES = {
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_NATIVE_ACCEPTANCE_SUMMARY.json": "527e8e18df609a5f58d76d8cd3bb765d4e7c16752a8b17cdaecf8266507b56a3",
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_TL_RESPONSE.CSV": "43930ed4a34c6f61e879c21b3b87af29b3013adccb8c9572048e9873b63ec24c",
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_OPPONENT_RESPONSE.CSV": "8ea769a0e5ed6e2a3e5205438ca3c442c20b6801e93345cf2818f8e57a271e1c",
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_ARMOR_ROLE_RESPONSE.CSV": "2f07d0ce15054ee1c36f2c2dff15f53731bd6cfaa7d020a5ba247ae304dc706c",
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_PARAMETER_MARGINALS.CSV": "2d569d933e0e7b87f2b0ba016705172c3ad221c966eab9a1bf96d31419d8169f",
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_PAIRWISE_RESPONSE.CSV": "2527dd715cb7cde2acc757c5021e47466e8838ac451fdfa34ee35ee6e9afbbd7",
    "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_KINETIC_REFINEMENT_CANDIDATE_LEDGER.CSV": "aa89b13212b4c9fd40d56dd7948ea3ae035cf5d895274ab4ca5ba4dfecf100f0",
}

# Equivalence intentionally excludes Hull Damage Control because CP151's user-approved
# rescaling scope leaves hull repair magnitude unchanged.  All other scaled core point
# quantities are expected to preserve same-seed combat behavior exactly.
NON_POINT_TELEMETRY_EQ_FIELDS = (
    "movement_hexes", "movement_fuel", "range_changes", "firm_track_turns", "approximate_track_turns", "no_track_turns",
    "direct_shots", "direct_hits", "missile_launches", "missile_terminal_arrivals", "missile_guidance_attempts", "missile_hits",
    "pds_attempts", "pds_intercepts", "shield_deflections", "damage_packets_resolved", "def_res_packets",
    "cp147_package_decisions", "cp147_direct_package_selections", "cp147_held_package_selections", "cp147_pds_package_selections",
    "cp147_passive_utility_fallbacks", "cp147_recovery_reserve_turns", "cp147_recovery_reserved_tp",
)


def _sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8"); return
    cols: list[str] = []
    for row in rows:
        for key in row:
            if key not in cols: cols.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def _round_half_up(value: float) -> int:
    return int(math.floor(float(value) + 0.5))


def active_factors(tl: int) -> tuple[str, ...]:
    out = list(FACTORS)
    if int(tl) == 1:
        out.remove("swarmer_packet_damage")
    if int(tl) < 6:
        out.remove("armor_repair")
    return tuple(out)


def _projective_columns() -> list[tuple[int, ...]]:
    # Pairwise-independent 3-level columns over GF(3). Seed the unit vectors so
    # the first five columns span the full 3^5 run space, then append the rest.
    units = [tuple(1 if i == j else 0 for i in range(5)) for j in range(5)]
    cols: list[tuple[int, ...]] = list(units)
    for v in itertools.product(range(3), repeat=5):
        if not any(v): continue
        first = next(x for x in v if x)
        inv = 1 if first == 1 else 2
        norm = tuple((x * inv) % 3 for x in v)
        if norm not in cols: cols.append(norm)
    return cols


_OA_COLS = _projective_columns()


def _oa_codes(names: tuple[str, ...]) -> list[dict[str, int]]:
    if len(names) > len(_OA_COLS): raise ValueError("too many CP151 factors for OA(243)")
    cols = _OA_COLS[:len(names)]
    symbol_to_code = {0: 0, 1: -1, 2: 1}
    rows: list[dict[str, int]] = []
    for base in itertools.product(range(3), repeat=5):
        row: dict[str, int] = {}
        for name, col in zip(names, cols):
            sym = sum(a*b for a, b in zip(base, col)) % 3
            row[name] = symbol_to_code[sym]
        rows.append(row)
    return rows


def _candidate_codes_for_tl(tl: int) -> list[dict[str, Any]]:
    names = active_factors(tl)
    rows: list[dict[str, Any]] = []
    seen: set[tuple[int, ...]] = set()
    for codes in _oa_codes(names):
        full = {f: int(codes.get(f, 0)) for f in FACTORS}
        key = tuple(full[f] for f in FACTORS)
        if key in seen: continue
        seen.add(key); rows.append({"design_class": "oa243", **full})
    for f in names:
        for d in (-1, 1):
            full = {x: 0 for x in FACTORS}; full[f] = d
            key = tuple(full[x] for x in FACTORS)
            if key in seen: continue
            seen.add(key); rows.append({"design_class": "axial", **full})
    return rows


EXPECTED_CANDIDATES_BY_TL = {tl: len(_candidate_codes_for_tl(tl)) for tl in range(1, 10)}
EXPECTED_TL_CANDIDATES = sum(EXPECTED_CANDIDATES_BY_TL.values())
EXPECTED_CANDIDATE_CONTEXT_CELLS = sum(EXPECTED_CANDIDATES_BY_TL[tl] * EXPECTED_CONTEXTS_BY_TL[tl] for tl in range(1, 10))
EXPECTED_SUBSTANTIVE_COMBATS = EXPECTED_CANDIDATE_CONTEXT_CELLS * TRIALS_PER_CELL
EXPECTED_SMOKE_COMBATS = EXPECTED_TL_CANDIDATES * SMOKE_CONTEXTS_PER_TL


def _read_evidence(repo: Path) -> dict[str, Any]:
    for rel, expected in EVIDENCE_HASHES.items():
        p = repo / rel
        if not p.is_file() or _sha(p) != expected:
            raise ValueError(f"CP151 accepted CP150 evidence hash mismatch: {rel}")
    summary = json.loads((repo / "docs/validation/evidence/checkpoint-151/accepted-cp150/CP150_NATIVE_ACCEPTANCE_SUMMARY.json").read_text(encoding="utf-8-sig"))
    if int(summary.get("checkpoint", 0)) != 150 or int(summary.get("substantiveCombatTrials", 0)) != 20580000 or int(summary.get("substantiveErrorTrials", -1)) != 0:
        raise ValueError("CP151 accepted CP150 evidence does not prove native 20.58M completion")
    return summary


def _base_matrix(repo: Path, doc: dict[str, Any], resource: str):
    er, tr = _resource_rows(repo, doc)
    return build_deep_resource_matrix(repo, doc["matrix"], resource, er, tr)


def _copy_matrix(matrix: Any):
    m = copy.deepcopy(matrix)
    m.doc = copy.deepcopy(matrix.doc)
    m.profiles = m.doc["profiles"]
    m.branches = {row["id"]: row for row in m.doc["branches"]}
    return m


def _scale_branch_armor(m: Any, delta: int = 0) -> None:
    for seed in m.doc.get("candidateBranchSeeds", []):
        if seed.get("id") == "A_b1" and isinstance(seed.get("tl6"), dict):
            tl6 = seed["tl6"]
            tl6["ai"] = max(1, int(tl6.get("ai", 0)) * SCALE + int(delta))


def _apply_exact_scale(m: Any, *, disable_hull_damage_control: bool = False) -> Any:
    m = _copy_matrix(m)
    for tl in range(1, 10):
        k = m.p("kinetic_main", tl); k["damage"] = float(k["damage"]) * SCALE
        e = m.p("energy_main", tl)
        for key in ("lowDamage", "standardDamage", "overloadDamage", "highDamage"):
            if key in e: e[key] = float(e[key]) * SCALE
        gp = m.p("missile_gp_warhead", tl); gp["damage"] = float(gp["damage"]) * SCALE
        if tl >= 2:
            sw = m.p("missile_swarmer", tl); sw["packetDamage"] = float(sw["packetDamage"]) * SCALE
        h = m.p("hull", tl); h["hullPoints"] = float(h["hullPoints"]) * SCALE
        sh = m.p("shield", tl); sh["capacity"] = float(sh["capacity"]) * SCALE
        if float(sh.get("tacticalRechargePerTp", 0)) > 0: sh["tacticalRechargePerTp"] = float(sh["tacticalRechargePerTp"]) * SCALE
        if float(sh.get("baseRecharge", 0)) > 0: sh["baseRecharge"] = float(sh["baseRecharge"]) * SCALE
        ar = m.p("armor", tl); ar["ai"] = float(ar["ai"]) * SCALE
        if float(ar.get("tacticalRegenerationPerTp", 0)) > 0: ar["tacticalRegenerationPerTp"] = float(ar["tacticalRegenerationPerTp"]) * SCALE
        if float(ar.get("baseRegeneration", 0)) > 0: ar["baseRegeneration"] = float(ar["baseRegeneration"]) * SCALE
        if int(ar.get("combatRegenerationReserveAi", 0)) > 0: ar["combatRegenerationReserveAi"] = int(ar["combatRegenerationReserveAi"]) * SCALE
        if disable_hull_damage_control:
            dc = m.p("damage_control", tl); dc["preparedRepairKits"] = 0
    _scale_branch_armor(m, 0)
    return m


def _research_center_actual(base: Any, tl: int) -> dict[str, Any]:
    k = base.p("kinetic_main", tl); e = base.p("energy_main", tl); gp = base.p("missile_gp_warhead", tl)
    sh = base.p("shield", tl); ar = base.p("armor", tl); hull = base.p("hull", tl)
    sw_exact = None; sw_integer = None
    if tl >= 2:
        sw_exact = float(base.p("missile_swarmer", tl)["packetDamage"]) * SCALE
        sw_integer = _round_half_up(sw_exact)
    return {
        "accepted_k_damage": float(k["damage"]),
        "exact_scaled_accepted_k_damage": float(k["damage"]) * SCALE,
        "k_damage": int(K_RESEARCH_DAMAGE_OLD_SCALE[tl] * SCALE),
        "e_low_damage": int(round(float(e["lowDamage"]) * SCALE)),
        "e_standard_damage": int(round(float(e["standardDamage"]) * SCALE)),
        "e_overload_damage": int(round(float(e["overloadDamage"]) * SCALE)),
        "gp_damage": int(round(float(gp["damage"]) * SCALE)),
        "swarmer_exact_scaled_packet_damage": sw_exact,
        "swarmer_packet_damage": sw_integer,
        "hull_capacity": int(round(float(hull["hullPoints"]) * SCALE)),
        "shield_capacity": int(round(float(sh["capacity"]) * SCALE)),
        "armor_capacity": int(round(float(ar["ai"]) * SCALE)),
        "shield_regen": 2 if float(sh.get("tacticalRechargePerTp", 0)) > 0 else 0,
        "armor_repair": 2 if float(ar.get("tacticalRegenerationPerTp", 0)) > 0 else 0,
        "armor_repair_reserve": int(ar.get("combatRegenerationReserveAi", 0)) * SCALE,
        "k_apen": int(k["apen"]),
        "e_spen": int(e["spen"]),
    }


def candidate_ledger(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    _read_evidence(repo)
    er, tr = _resource_rows(repo, doc)
    central = build_deep_resource_matrix(repo, doc["matrix"], "R1_CENTRAL_NO_MAJOR", er, tr)
    rows: list[dict[str, Any]] = []
    for tl in range(1, 10):
        center = _research_center_actual(central, tl)
        for i, codes in enumerate(_candidate_codes_for_tl(tl)):
            actual = {f: center.get(f) for f in FACTORS}
            for f in active_factors(tl):
                actual[f] = int(center[f]) + int(codes[f])
            rows.append({
                "candidate_id": f"PS{tl:02d}-{i:03d}", "tl": tl, "candidate_index": i,
                "design_class": codes["design_class"], "active_factor_count": len(active_factors(tl)),
                **{f"code_{f}": int(codes[f]) for f in FACTORS},
                **{f"candidate_{f}": ("" if actual.get(f) is None else actual.get(f)) for f in FACTORS},
                "center_exact_scaled_accepted_k_damage": center["exact_scaled_accepted_k_damage"],
                "center_swarmer_exact_scaled_packet_damage": "" if center["swarmer_exact_scaled_packet_damage"] is None else center["swarmer_exact_scaled_packet_damage"],
                "center_armor_repair_reserve": center["armor_repair_reserve"],
                "point_scale": SCALE,
                "k_accuracy_policy": "unchanged_cp150_executable_profile",
                "def_res_policy": "unchanged_dimensionless",
                "tp_range_space_policy": "unchanged",
                "missile_penetration_policy": "remain_zero",
                "promotion_allowed": 0,
            })
    return rows


def design_summary(repo: Path, doc: dict[str, Any]) -> list[dict[str, Any]]:
    led = candidate_ledger(repo, doc); out = []
    for tl in range(1, 10):
        rs = [r for r in led if int(r["tl"]) == tl]
        out.append({
            "tl": tl, "candidates": len(rs), "oa_candidates": sum(r["design_class"] == "oa243" for r in rs),
            "axial_candidates": sum(r["design_class"] == "axial" for r in rs),
            "active_factors": ";".join(active_factors(tl)), "active_factor_count": len(active_factors(tl)),
            "stage_a_contexts": EXPECTED_CONTEXTS_BY_TL[tl], "candidate_context_cells": len(rs) * EXPECTED_CONTEXTS_BY_TL[tl],
            "substantive_trials": len(rs) * EXPECTED_CONTEXTS_BY_TL[tl] * TRIALS_PER_CELL,
        })
    return out


def aux_scaling_audit(repo: Path) -> list[dict[str, Any]]:
    return [
        {"item": "A_b1 Crystalline Armor", "status": "executable_alternate_armor_profile", "cp151_action": "scale AI x2 with Armor-capacity domain; no repair added", "swept": 1},
        {"item": "Ablative Armor Layer", "status": "known lab profile but not Stage-A executable", "cp151_action": "record x2 point-domain equivalence only; do not invent full-map integration", "swept": 0},
        {"item": "Shield Booster", "status": "resource proxy; magnitude TBD", "cp151_action": "defer numeric sweep until executable magnitude exists", "swept": 0},
        {"item": "Shield Power Stabilizer", "status": "resource proxy; magnitude TBD", "cp151_action": "defer numeric sweep until executable magnitude exists", "swept": 0},
        {"item": "Shield Hardener", "status": "executable +DEF percentage", "cp151_action": "unchanged: DEF is dimensionless and outside point-scale conversion", "swept": 0},
        {"item": "Energized Armor Controller", "status": "candidate-only magnitude TBD", "cp151_action": "defer; do not invent RES/point bonus", "swept": 0},
    ]


def validate_study(doc: dict[str, Any]) -> list[str]:
    e: list[str] = []
    if doc.get("schemaVersion") != "star-cluster-cp151-point-scale-multivariate-response-study-v0.1": e.append("schemaVersion")
    if int(doc.get("checkpoint", 0)) != 151: e.append("checkpoint")
    if int(doc.get("baseCheckpoint", 0)) != 150: e.append("baseCheckpoint")
    if int(doc.get("pointScale", 0)) != SCALE: e.append("pointScale")
    if doc.get("combatDoctrine") != UTILITY_COMBAT_DOCTRINE: e.append("combatDoctrine")
    if doc.get("damageModel") != "def-res-v1": e.append("damageModel")
    if doc.get("stageAExperimentManifest") != "docs/archive/testing/pre-cp165-active/cp144_stage_a_experiment_manifest.csv": e.append("manifest")
    if int(doc.get("substantiveTrialsPerCandidateContext", 0)) != TRIALS_PER_CELL: e.append("trials")
    if int(doc.get("expectedTlCandidates", 0)) != EXPECTED_TL_CANDIDATES: e.append("candidateCount")
    if int(doc.get("expectedCandidateContextCells", 0)) != EXPECTED_CANDIDATE_CONTEXT_CELLS: e.append("cellCount")
    if int(doc.get("substantiveCombatTrials", 0)) != EXPECTED_SUBSTANTIVE_COMBATS: e.append("combatCount")
    if int(doc.get("smokeCombatTrials", 0)) != EXPECTED_SMOKE_COMBATS: e.append("smokeCount")
    if doc.get("scaledFields") != ["weapon DAM", "Hull capacity", "Shield capacity", "Armor capacity"]: e.append("scaledFields")
    if doc.get("unchangedFields") != ["ACC", "DEF", "RES", "TP", "range", "Space"]: e.append("unchangedFields")
    if doc.get("penetrationSweep") != {"K_APEN": [-1,0,1], "E_SPEN": [-1,0,1], "missile_APEN_SPEN": [0]}: e.append("penetrationSweep")
    if bool(doc.get("tuningAllowed", True)) or bool(doc.get("automaticPromotion", True)) or bool(doc.get("stageBAutomatic", True)): e.append("promotionBoundary")
    return e


def validate_population(repo: Path, doc: dict[str, Any]) -> list[str]:
    e: list[str] = []
    _read_evidence(repo)
    manifest = _read_csv(repo / doc["stageAExperimentManifest"])
    if len(manifest) != EXPECTED_STAGE_A: e.append("stageA-count")
    counts = Counter(int(r["tl"]) for r in manifest)
    if dict(counts) != EXPECTED_CONTEXTS_BY_TL: e.append("tl-context-count")
    led = candidate_ledger(repo, doc)
    if len(led) != EXPECTED_TL_CANDIDATES or len({(r["tl"], r["candidate_id"]) for r in led}) != len(led): e.append("candidate-ledger")
    for tl, expected in EXPECTED_CANDIDATES_BY_TL.items():
        if sum(int(r["tl"]) == tl for r in led) != expected: e.append(f"tl{tl}-candidate-count")
    if any(int(r["code_swarmer_packet_damage"]) != 0 for r in led if int(r["tl"]) == 1): e.append("tl1-swarmer")
    if any(int(r["code_armor_repair"]) != 0 for r in led if int(r["tl"]) < 6): e.append("early-armor-repair")
    if any(int(r["promotion_allowed"]) != 0 for r in led): e.append("promotion")
    return e


def smoke_contexts(repo: Path, doc: dict[str, Any], tl: int) -> list[dict[str, str]]:
    manifest = [r for r in _read_csv(repo / doc["stageAExperimentManifest"]) if int(r["tl"]) == int(tl)]
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for r in manifest: groups[(r["resource_ensemble_id"], r["scenario_stratum"])].append(r)
    out = []
    for key in sorted(groups):
        rs = sorted(groups[key], key=lambda x: x["scenario_id"])
        # Rotate selected pairing deterministically by TL/resource/stratum so smoke
        # does not repeatedly exercise the same weapon pairing.
        pos = (int(tl) + sum(ord(ch) for ch in (key[0] + key[1]))) % len(rs)
        out.append(rs[pos])
    if len(out) != SMOKE_CONTEXTS_PER_TL: raise ValueError(f"CP151 TL{tl} smoke contexts {len(out)} != {SMOKE_CONTEXTS_PER_TL}")
    return out


def _apply_research_candidate(base: Any, tl: int, c: dict[str, Any]) -> Any:
    m = _copy_matrix(base)
    # Only the scenario TL is changed; Stage-A scenarios are same-TL.
    k = m.p("kinetic_main", tl); k["damage"] = int(c["candidate_k_damage"]); k["apen"] = int(c["candidate_k_apen"]); k["spen"] = 0
    e = m.p("energy_main", tl)
    e["lowDamage"] = int(c["candidate_e_low_damage"]); e["standardDamage"] = int(c["candidate_e_standard_damage"])
    e["overloadDamage"] = int(c["candidate_e_overload_damage"]); e["highDamage"] = int(c["candidate_e_overload_damage"]); e["spen"] = int(c["candidate_e_spen"]); e["apen"] = 0
    gp = m.p("missile_gp_warhead", tl); gp["damage"] = int(c["candidate_gp_damage"]); gp["spen"] = 0; gp["apen"] = 0
    if tl >= 2:
        sw = m.p("missile_swarmer", tl); sw["packetDamage"] = int(c["candidate_swarmer_packet_damage"]); sw["spen"] = 0; sw["apen"] = 0
    h = m.p("hull", tl); h["hullPoints"] = int(c["candidate_hull_capacity"])
    sh = m.p("shield", tl); sh["capacity"] = int(c["candidate_shield_capacity"]); sh["tacticalRechargePerTp"] = int(c["candidate_shield_regen"])
    ar = m.p("armor", tl); ar["ai"] = int(c["candidate_armor_capacity"])
    if tl >= 6:
        ar["tacticalRegenerationPerTp"] = int(c["candidate_armor_repair"])
        ar["combatRegenerationReserveAi"] = int(c["center_armor_repair_reserve"])
    _scale_branch_armor(m, int(c["code_armor_capacity"]) if tl == 6 else 0)
    return m


_WORKER_BASE: dict[str, Any] | None = None
_WORKER_CANDIDATES: dict[str, dict[str, Any]] | None = None
_WORKER_CACHE: dict[tuple[str, int, str], Any] | None = None


def _worker_init(repo_text: str, doc: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    global _WORKER_BASE, _WORKER_CANDIDATES, _WORKER_CACHE
    repo = Path(repo_text); er, tr = _resource_rows(repo, doc)
    _WORKER_BASE = {eid: build_deep_resource_matrix(repo, doc["matrix"], eid, er, tr) for eid in sorted({r["ensemble_id"] for r in er})}
    _WORKER_CANDIDATES = {r["candidate_id"]: r for r in candidates}; _WORKER_CACHE = {}


def _matrix_for(resource: str, tl: int, candidate_id: str):
    if _WORKER_BASE is None or _WORKER_CANDIDATES is None or _WORKER_CACHE is None: raise RuntimeError("CP151 worker not initialized")
    key = (resource, int(tl), candidate_id)
    if key not in _WORKER_CACHE:
        _WORKER_CACHE[key] = _apply_research_candidate(_WORKER_BASE[resource], int(tl), _WORKER_CANDIDATES[candidate_id])
    return _WORKER_CACHE[key]


def _candidate_task(args: tuple[int, dict[str, str], dict[str, Any], int, int]) -> dict[str, Any]:
    idx, source, c, seed, trials = args; tl = int(source["tl"])
    matrix = _matrix_for(source["resource_ensemble_id"], tl, c["candidate_id"])
    bound = bind_scenario(matrix, source)
    # Reuse the accepted CP148 per-scenario aggregation contract on the candidate matrix.
    wc._WORKER_MATRICES = {source["resource_ensemble_id"]: matrix}
    row = wc._substantive_task((idx, source, bound, seed, trials, UTILITY_COMBAT_DOCTRINE))
    row.update({"candidate_id": c["candidate_id"], "candidate_index": c["candidate_index"], "design_class": c["design_class"]})
    for f in FACTORS:
        row[f"code_{f}"] = int(c[f"code_{f}"])
        row[f"candidate_{f}"] = c[f"candidate_{f}"]
    return row


def run_plan(repo: Path, study_path: Path, outdir: Path) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc); outdir.mkdir(parents=True, exist_ok=True)
    led = candidate_ledger(repo, doc); ds = design_summary(repo, doc); aux = aux_scaling_audit(repo)
    _write_csv(outdir / "point_scale_candidate_ledger.csv", led); _write_csv(outdir / "point_scale_design_summary.csv", ds); _write_csv(outdir / "point_scale_aux_scaling_audit.csv", aux)
    summary = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 151, "mode": "plan", "passed": not errs, "failedGates": errs,
               "tlCandidateCount": len(led), "candidateContextCells": EXPECTED_CANDIDATE_CONTEXT_CELLS, "trialsPerCandidateContext": TRIALS_PER_CELL,
               "substantiveCombatTrials": EXPECTED_SUBSTANTIVE_COMBATS, "smokeCombatTrials": EXPECTED_SMOKE_COMBATS, "oaRunsPerTl": OA_RUNS,
               "pointScale": SCALE, "automaticPromotion": False, "stageBAutomatic": False}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8"); return summary


def run_batch(repo: Path, study_path: Path, outdir: Path, jobs: int = 24, tl: int = 1,
              candidate_start: int = 0, candidate_end: int | None = None, trials: int | None = None,
              smoke_panel: bool = False) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    ledger = [r for r in candidate_ledger(repo, doc) if int(r["tl"]) == int(tl)]
    start = max(0, int(candidate_start)); end = len(ledger) if candidate_end is None else min(len(ledger), int(candidate_end)); selected = ledger[start:end]
    if not selected: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": ["empty-candidate-batch"]}
    contexts = smoke_contexts(repo, doc, tl) if smoke_panel else [r for r in _read_csv(repo / doc["stageAExperimentManifest"]) if int(r["tl"]) == int(tl)]
    ntrials = int(trials or doc["substantiveTrialsPerCandidateContext"]); tasks = []; idx = 0
    for c in selected:
        for src in contexts: tasks.append((idx, src, c, int(doc["masterSeed"]), ntrials)); idx += 1
    outdir.mkdir(parents=True, exist_ok=True); jobs = max(1, min(int(jobs), len(tasks)))
    if jobs == 1:
        _worker_init(str(repo), doc, selected); rows = [_candidate_task(t) for t in tasks]
    else:
        ctx = get_context("spawn"); chunksize = min(16, max(1, len(tasks) // max(1, jobs * 8)))
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_worker_init, initargs=(str(repo), doc, selected)) as ex:
            rows = list(ex.map(_candidate_task, tasks, chunksize=chunksize))
    rows.sort(key=lambda r: (int(r["candidate_index"]), int(r["scenario_index"])))
    _write_csv(outdir / "point_scale_candidate_context_results.csv", rows)
    failures = []
    if len(rows) != len(selected) * len(contexts): failures.append("row-count")
    if any(int(r["error_trials"]) for r in rows): failures.append("execution-errors")
    summary = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 151, "mode": "batch", "passed": not failures, "failedGates": failures,
               "tl": int(tl), "smokePanel": bool(smoke_panel), "candidateStart": start, "candidateEnd": end, "candidates": len(selected),
               "contextsPerCandidate": len(contexts), "candidateContextCells": len(rows), "trialsPerContext": ntrials, "combatTrials": len(rows) * ntrials,
               "turnCapSentinels": sum(int(r["turn_cap_sentinels"]) for r in rows), "errors": sum(int(r["error_trials"]) for r in rows)}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8"); return summary


_EQ_LEGACY: dict[str, Any] | None = None
_EQ_SCALED: dict[str, Any] | None = None


def _equivalence_worker_init(repo_text: str, doc: dict[str, Any]) -> None:
    global _EQ_LEGACY, _EQ_SCALED
    repo = Path(repo_text); er, tr = _resource_rows(repo, doc); resources = sorted({r["ensemble_id"] for r in er})
    _EQ_LEGACY = {}; _EQ_SCALED = {}
    for resource in resources:
        base = build_deep_resource_matrix(repo, doc["matrix"], resource, er, tr)
        legacy = _copy_matrix(base); scaled = _apply_exact_scale(base, disable_hull_damage_control=True)
        for tl in range(1, 10): legacy.p("damage_control", tl)["preparedRepairKits"] = 0
        _EQ_LEGACY[resource] = legacy; _EQ_SCALED[resource] = scaled


def _eq_task(args: tuple[int, dict[str, str], int]) -> dict[str, Any]:
    idx, src, seed = args
    if _EQ_LEGACY is None or _EQ_SCALED is None: raise RuntimeError("CP151 equivalence worker not initialized")
    legacy = _EQ_LEGACY[src["resource_ensemble_id"]]; scaled = _EQ_SCALED[src["resource_ensemble_id"]]
    bl = bind_scenario(legacy, src); bs = bind_scenario(scaled, src)
    rl = run_trial_full_map(legacy, bl.variant, seed, 0, combat_doctrine=UTILITY_COMBAT_DOCTRINE)
    rs = run_trial_full_map(scaled, bs.variant, seed, 0, combat_doctrine=UTILITY_COMBAT_DOCTRINE)
    diffs: list[str] = []
    for name in ("winner", "unresolved", "turns", "termination_cause", "final_range", "min_range", "error"):
        if getattr(rl, name) != getattr(rs, name): diffs.append(name)
    for name in ("hull_a", "hull_b", "armor_a", "armor_b", "shield_a", "shield_b"):
        if abs(float(getattr(rs, name)) - float(getattr(rl, name)) * SCALE) > 1e-8: diffs.append(name)
    for side_name in ("side_a", "side_b"):
        a = getattr(rl, side_name); b = getattr(rs, side_name)
        for f in NON_POINT_TELEMETRY_EQ_FIELDS:
            if getattr(a, f) != getattr(b, f): diffs.append(f"{side_name}.{f}")
    return {"scenario_index": idx, "scenario_id": src["scenario_id"], "tl": int(src["tl"]), "resource_ensemble_id": src["resource_ensemble_id"],
            "side_a_weapon": src["side_a_weapon"], "side_b_weapon": src["side_b_weapon"], "mismatch": int(bool(diffs)), "mismatch_fields": ";".join(diffs[:30])}


def run_equivalence(repo: Path, study_path: Path, outdir: Path, jobs: int = 24) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc); outdir.mkdir(parents=True, exist_ok=True)
    if errs: return {"schemaVersion": RESULT_SCHEMA, "passed": False, "failedGates": errs}
    manifest = _read_csv(repo / doc["stageAExperimentManifest"]); tasks = [(i, r, int(doc["equivalenceSeed"])) for i, r in enumerate(manifest)]
    jobs = max(1, min(int(jobs), len(tasks)))
    if jobs == 1:
        _equivalence_worker_init(str(repo), doc); rows = [_eq_task(t) for t in tasks]
    else:
        ctx = get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx, initializer=_equivalence_worker_init, initargs=(str(repo), doc)) as ex:
            rows = list(ex.map(_eq_task, tasks, chunksize=8))
    rows.sort(key=lambda x: int(x["scenario_index"])); _write_csv(outdir / "point_scale_equivalence_audit.csv", rows)
    mismatches = sum(int(r["mismatch"]) for r in rows)
    summary = {"schemaVersion": RESULT_SCHEMA, "checkpoint": 151, "mode": "equivalence", "passed": mismatches == 0, "failedGates": ([] if mismatches == 0 else ["equivalence-mismatch"]),
               "pairedScenarioIdentities": len(rows), "legacyCombatExecutions": len(rows), "scaledCombatExecutions": len(rows), "mismatchedScenarioIdentities": mismatches,
               "hullDamageControlPolicy": "disabled-in-both-equivalence-arms-because-user-approved-CP151-scope-leaves-hull-repair-unscaled", "pointScale": SCALE}
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8"); return summary


class _Agg:
    __slots__ = ("trials", "wins", "draws", "turns", "duration", "caps", "damage_adv", "errors")
    def __init__(self): self.trials = self.wins = self.draws = self.duration = self.caps = self.errors = 0; self.turns = self.damage_adv = 0.0
    def add(self, trials: int, wins: int, draws: int, mean_turns: float, duration_rate: float, damage_adv: float, caps: int, errors: int):
        self.trials += trials; self.wins += wins; self.draws += draws; self.turns += mean_turns * trials; self.duration += duration_rate * trials; self.damage_adv += damage_adv * trials; self.caps += caps; self.errors += errors
    def row(self) -> dict[str, Any]:
        n = self.trials
        return {"trials": n, "wins": self.wins, "win_rate": self.wins/n if n else 0.0, "draw_rate": self.draws/n if n else 0.0,
                "mean_turns": self.turns/n if n else 0.0, "duration_concern_rate": self.duration/n if n else 0.0,
                "mean_damage_advantage": self.damage_adv/n if n else 0.0, "turn_cap_sentinels": self.caps, "error_trials": self.errors}


def _add_family(groups: dict[Any, _Agg], key: Any, r: dict[str, str], side: str) -> None:
    n = int(r["trials"]); wins = int(r["a_wins"] if side == "A" else r["b_wins"]); draws = int(r["draws"])
    damage = float(r["a_damage_advantage_mean"]); damage = damage if side == "A" else -damage
    groups.setdefault(key, _Agg()).add(n, wins, draws, float(r["mean_turns_all"]), float(r["gameplay_duration_concern_rate"]), damage, int(r["turn_cap_sentinels"]), int(r["error_trials"]))


def merge_batches(repo: Path, study_path: Path, batch_root: Path, outdir: Path, expected_trials: int | None = None) -> dict[str, Any]:
    doc = load_json(study_path); errs = validate_study(doc) + validate_population(repo, doc); ntrials = int(expected_trials or doc["substantiveTrialsPerCandidateContext"]); outdir.mkdir(parents=True, exist_ok=True)
    ledger = candidate_ledger(repo, doc); led = {(int(r["tl"]), r["candidate_id"]): r for r in ledger}
    cand_family: dict[Any, _Agg] = {}; cand_pair: dict[Any, _Agg] = {}; cand_resource: dict[Any, _Agg] = {}; cand_stratum: dict[Any, _Agg] = {}
    factor_family: dict[Any, _Agg] = {}; pair_factor_family: dict[Any, _Agg] = {}
    audits = []; center_rows: list[dict[str, Any]] = []; total_rows = total_trials = total_caps = total_errors = 0
    seen_cells: set[tuple[int, str, str]] = set()
    center_id_by_tl = {}
    for tl in range(1, 10):
        center = next(r for r in ledger if int(r["tl"]) == tl and r["design_class"] == "oa243" and all(int(r[f"code_{f}"]) == 0 for f in FACTORS))
        center_id_by_tl[tl] = center["candidate_id"]
    for d in sorted(p for p in batch_root.iterdir() if p.is_dir()):
        sp = d / "summary.json"; rp = d / "point_scale_candidate_context_results.csv"
        if not sp.exists() or not rp.exists(): continue
        s = json.loads(sp.read_text(encoding="utf-8-sig")); ok = bool(s.get("passed", False)) and not s.get("smokePanel", False) and int(s.get("trialsPerContext", 0)) == ntrials and int(s.get("errors", -1)) == 0
        rows_in_batch = 0; trials_in_batch = 0
        if ok:
            with rp.open(encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f):
                    rows_in_batch += 1; n = int(r["trials"]); trials_in_batch += n; total_rows += 1; total_trials += n; total_caps += int(r["turn_cap_sentinels"]); total_errors += int(r["error_trials"])
                    tl = int(r["tl"]); cid = r["candidate_id"]; keycell = (tl, cid, r["scenario_id"])
                    if keycell in seen_cells: errs.append("duplicate-cell"); continue
                    seen_cells.add(keycell); c = led[(tl, cid)]
                    for side, weapon in (("A", r["side_a_weapon"]), ("B", r["side_b_weapon"])):
                        _add_family(cand_family, (tl, cid, weapon), r, side)
                        _add_family(cand_resource, (tl, cid, weapon, r["resource_ensemble_id"]), r, side)
                        _add_family(cand_stratum, (tl, cid, weapon, r["scenario_stratum"]), r, side)
                        if c["design_class"] == "oa243":
                            for factor in active_factors(tl):
                                _add_family(factor_family, (tl, factor, int(c[f"code_{factor}"]), weapon), r, side)
                            af = active_factors(tl)
                            for i, f1 in enumerate(af):
                                for f2 in af[i+1:]:
                                    _add_family(pair_factor_family, (tl, f1, int(c[f"code_{f1}"]), f2, int(c[f"code_{f2}"]), weapon), r, side)
                    a = r["side_a_weapon"]; b = r["side_b_weapon"]
                    if a != b:
                        x, y = sorted((a, b)); side_x = "A" if a == x else "B"
                        _add_family(cand_pair, (tl, cid, x, y), r, side_x)
                    if cid == center_id_by_tl[tl]: center_rows.append(dict(r))
        audits.append({"batch": d.name, "tl": s.get("tl"), "candidate_start": s.get("candidateStart"), "candidate_end": s.get("candidateEnd"), "rows": rows_in_batch, "combat_trials": trials_in_batch, "passed": int(ok)})
    if total_rows != EXPECTED_CANDIDATE_CONTEXT_CELLS: errs.append("merged-row-count")
    if total_trials != EXPECTED_SUBSTANTIVE_COMBATS: errs.append("merged-trial-count")
    if total_errors: errs.append("execution-errors")
    if len(seen_cells) != EXPECTED_CANDIDATE_CONTEXT_CELLS: errs.append("cell-coverage")

    def rows_from(groups, names):
        out=[]
        for key, agg in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
            out.append({**{n:v for n,v in zip(names,key)}, **agg.row()})
        return out
    cf = rows_from(cand_family, ("tl","candidate_id","weapon")); cp = rows_from(cand_pair, ("tl","candidate_id","weapon_x","weapon_y"))
    cr = rows_from(cand_resource, ("tl","candidate_id","weapon","resource_ensemble_id")); cs = rows_from(cand_stratum, ("tl","candidate_id","weapon","scenario_stratum"))
    ff = rows_from(factor_family, ("tl","factor","level","weapon")); pf = rows_from(pair_factor_family, ("tl","factor_1","level_1","factor_2","level_2","weapon"))
    # Candidate summary derives family spread and weakest/strongest family response.
    fam_by = defaultdict(list)
    for r in cf: fam_by[(int(r["tl"]), r["candidate_id"])].append(r)
    candidate_summary=[]
    for key, rs in sorted(fam_by.items()):
        rates=[float(x["win_rate"]) for x in rs]; tl,cid=key; c=led[(tl,cid)]
        candidate_summary.append({"tl":tl,"candidate_id":cid,"design_class":c["design_class"],"families":len(rs),"mean_family_win_rate":statistics.fmean(rates),"min_family_win_rate":min(rates),"max_family_win_rate":max(rates),"family_win_rate_range":max(rates)-min(rates),"family_win_rate_stdev":statistics.pstdev(rates) if len(rates)>1 else 0.0,"promotion_allowed":0})
    # Pure axial effects relative to the exact research-center OA row.
    cf_index={(int(r["tl"]),r["candidate_id"],r["weapon"]):r for r in cf}; axial=[]
    for tl in range(1,10):
        center_id=center_id_by_tl[tl]
        for factor in active_factors(tl):
            for d in (-1,1):
                c=next(x for x in ledger if int(x["tl"])==tl and int(x[f"code_{factor}"])==d and all(int(x[f"code_{o}"])==0 for o in FACTORS if o!=factor))
                for weapon in sorted({x["weapon"] for x in cf if int(x["tl"])==tl and x["candidate_id"]==center_id}):
                    base=cf_index[(tl,center_id,weapon)]; rr=cf_index[(tl,c["candidate_id"],weapon)]
                    axial.append({"tl":tl,"factor":factor,"direction":d,"candidate_id":c["candidate_id"],"weapon":weapon,"win_rate":rr["win_rate"],"delta_win_rate_vs_center":float(rr["win_rate"])-float(base["win_rate"]),"delta_mean_turns_vs_center":float(rr["mean_turns"])-float(base["mean_turns"]),"delta_damage_advantage_vs_center":float(rr["mean_damage_advantage"])-float(base["mean_damage_advantage"])})
    _write_csv(outdir/"batch_merge_audit.csv",audits); _write_csv(outdir/"point_scale_candidate_ledger.csv",ledger); _write_csv(outdir/"point_scale_design_summary.csv",design_summary(repo,doc)); _write_csv(outdir/"point_scale_aux_scaling_audit.csv",aux_scaling_audit(repo))
    _write_csv(outdir/"point_scale_candidate_summary.csv",candidate_summary); _write_csv(outdir/"point_scale_candidate_family_response.csv",cf); _write_csv(outdir/"point_scale_candidate_pair_response.csv",cp); _write_csv(outdir/"point_scale_candidate_resource_response.csv",cr); _write_csv(outdir/"point_scale_candidate_stratum_response.csv",cs)
    _write_csv(outdir/"point_scale_factor_family_marginals.csv",ff); _write_csv(outdir/"point_scale_pairwise_factor_family_response.csv",pf); _write_csv(outdir/"point_scale_axial_family_effects.csv",axial); _write_csv(outdir/"research_center_scenario_response.csv",center_rows)
    summary={"schemaVersion":RESULT_SCHEMA,"checkpoint":151,"mode":"merged-substantive","passed":not errs,"failedGates":sorted(set(errs)),"tlCandidateCount":EXPECTED_TL_CANDIDATES,"candidateContextCells":total_rows,"trialsPerCandidateContext":ntrials,"substantiveCombatTrials":total_trials,"turnCapSentinels":total_caps,"errorTrials":total_errors,"researchCenterScenarioRows":len(center_rows),"pointScale":SCALE,"tuningAllowed":False,"automaticPromotion":False,"stageBAutomatic":False,"interpretation":"CP151 fine-grained x2 offensive/defensive point-scale response surface. K research center carries CP150 damage findings; ACC/DEF/RES/TP/range/Space remain unchanged. K APEN and E SPEN are ±1 response dimensions only. Swarmer equivalence retains exact doubled float; substantive research uses neighboring integer packet values."}
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); return summary
