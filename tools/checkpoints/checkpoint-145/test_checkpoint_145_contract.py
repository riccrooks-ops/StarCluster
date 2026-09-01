#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

SKIP = "docs/validation/evidence/checkpoint-145/CP145_REPOSITORY_SHA256SUMS.txt"
MATRIX_SHA = "3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194"
CP144_SUBMITTED_ARCHIVE_SHA = "71bd2b81980701292d6cd463b2a225752274a1045ea4e813c83e5728e9f961fd"
CP144_SCENARIO_SURFACE_SHA = "ffa17024e0aed42be2def3f6b9e64a492da5c52d7d512cc31552aa19d6a132fd"
CP144_PARETO_SHA = "a60975cb58afdf735d27aac4692182eb7080dfcf10f15c419194177fc2df6e15"
CP144_SUMMARY_SHA = "ce3eef4f9a9b31d12c99bedb84715f27549d6e4ec79f2ec02163beedea21dd93"


def req(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def manifest(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            h, rel = line.split("  ", 1); out[rel] = h
    return out


def owned(repo: Path) -> list[str]:
    out = []
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(repo).as_posix(); wrapped = "/" + rel
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in wrapped or rel.endswith(".pyc") or "/bin/" in wrapped or "/obj/" in wrapped or "/TestResults/" in wrapped:
            continue
        if rel == SKIP:
            continue
        out.append(rel)
    return sorted(out)


def validate_manifest(repo: Path) -> int:
    path = repo / SKIP; req(path.is_file(), "CP145 repository manifest missing")
    entries = manifest(path); current = owned(repo)
    req(set(entries) == set(current), f"manifest path drift missing={sorted(set(entries)-set(current))[:8]} extra={sorted(set(current)-set(entries))[:8]}")
    for rel, expected in entries.items():
        req(sha(repo / rel) == expected, f"manifest hash drift: {rel}")
    return len(entries)


def validate_cp144_smoke(root: Path) -> dict:
    base = root / "cp144-stage-a-smoke-merged"; req((base / "summary.json").is_file(), "CP144 smoke regression summary missing")
    s = js(base / "summary.json")
    req(s["passed"] is True and int(s.get("failedGates", 0)) == 0 and not s.get("gates", {}).get("failed", []), "CP144 smoke regression gates")
    req(s["stageAScenarios"] == 6850 and s["integrationSmokeTrials"] == 6850 and s["executionErrors"] == 0, "CP144 smoke regression coverage")
    req(s["resourceEnvironmentCount"] == 5 and s["scenarioStrataCount"] == 10 and s["orderedSameTlWeaponPairings"] == 137, "CP144 smoke regression factorial")
    req(s["resolved"] == 6785 and s["resolvedGe25"] == 9 and s["turnCapSentinels"] == 65 and s["safeStalemates"] == 0, "CP144 smoke deterministic signature")
    req(s["nonstandoffOpenOrders"] == 0 and s["sourceMatrixUnmodified"] is True and s["substantiveCombatTrials"] == 0, "CP144 smoke movement/scope")
    rows = read_rows(base / "whole_combat_smoke_results.csv")
    req(len(rows) == 6850 and len({r["scenario_id"] for r in rows}) == 6850, "CP144 smoke result rows")
    req(all(not r["error"] and int(r["turn_telemetry_coverage_pass"]) == 1 and int(r["nonstandoff_open_orders"]) == 0 for r in rows), "CP144 smoke execution/telemetry")
    audit = read_rows(base / "batch_merge_audit.csv"); req(len(audit) == 7 and all(int(r["passed"]) for r in audit), "CP144 smoke batch audit")
    return s


def validate_diagnostic(root: Path) -> dict:
    base = root / "stage-a-diagnostic-attribution"; req((base / "summary.json").is_file(), "CP145 diagnostic summary missing")
    s = js(base / "summary.json")
    req(s["passed"] is True and not s.get("failedGates", []), "CP145 diagnostic gates")
    req(s["checkpoint"] == 145 and s["baseCheckpoint"] == 144, "CP145 diagnostic identity")
    req(s["acceptedCp144Scenarios"] == 6850 and s["acceptedCp144SubstantiveTrials"] == 3425000, "accepted CP144 decomposition scope")
    req(s["diagnosticScenarios"] == 252 and s["diagnosticTrialsPerScenario"] == 25 and s["diagnosticCombatTrials"] == 6300, "diagnostic replay scope")
    req(s["pdsOpportunityScenarios"] == 204 and s["tpStarvationScenarios"] == 48, "diagnostic family scope")
    req(s["sourceMatrixUnmodified"] is True and s["tuningAllowed"] is False and s["automaticPromotion"] is False and s["stageBAutomatic"] is False, "diagnostic interpretation boundary")
    req(float(s["originalParetoWinFastCorrelation"]) > 0.99, "original Pareto redundancy diagnostic")
    req(s["strategicParetoRows"] == 35 and s["kineticAttributionRows"] == 350 and s["kineticVsEnergyAttributionRows"] == 350 and s["energyResourceRows"] == 45 and s["pdsBaselineRows"] == 255, "accepted-surface attribution row counts")

    expected = {
        "diagnostic_replay_results.csv": 252,
        "pds_opportunity_replay.csv": 204,
        "tp_starvation_replay.csv": 48,
        "pareto_objective_diagnostics.csv": 3,
        "strategic_viability_surface.csv": 35,
        "kinetic_attribution.csv": 350,
        "kinetic_tl_summary.csv": 9,
        "kinetic_vs_energy_attribution.csv": 350,
        "kinetic_vs_energy_tl_summary.csv": 9,
        "energy_resource_attribution.csv": 45,
        "pds_baseline_attribution.csv": 255,
        "duration_hotspots.csv": 100,
    }
    loaded = {}
    for name, count in expected.items():
        p = base / name; req(p.is_file(), f"missing CP145 diagnostic artifact: {name}")
        loaded[name] = read_rows(p); req(len(loaded[name]) == count, f"{name} expected {count} rows got {len(loaded[name])}")
    replay = loaded["diagnostic_replay_results.csv"]
    req(sum(int(r["trials"]) for r in replay) == 6300 and all(int(r["trials"]) == 25 for r in replay), "diagnostic trial counts")
    req(all(int(r["error_trials"]) == 0 and int(r["nonstandoff_open_orders"]) == 0 for r in replay), "diagnostic execution/movement regression")
    pds = loaded["pds_opportunity_replay.csv"]
    req(sum(int(r["a_pds_threat_flights"]) + int(r["b_pds_threat_flights"]) for r in pds) > 0, "PDS opportunity telemetry not exercised")
    req(sum(int(r["a_pds_attempts_used"]) + int(r["b_pds_attempts_used"]) for r in pds) > 0, "PDS attempt telemetry not exercised")
    tp = loaded["tp_starvation_replay.csv"]
    req(sum(float(r["a_tp_denied_per_turn"]) + float(r["b_tp_denied_per_turn"]) for r in tp) > 0, "TP denial telemetry not exercised")
    category = base / "tp_starvation_category_summary.csv"; req(category.is_file() and len(read_rows(category)) > 0, "TP category summary missing/empty")
    return s


def validate_native(root: Path, final: bool) -> dict:
    name = "CP145_NATIVE_ACCEPTANCE_SUMMARY.json" if final else "CP145_REPOSITORY_ONLY_ACCEPTANCE.json"
    s = js(root / name); failed = s.get("failedGates", [])
    req(s["checkpoint"] == 145 and (failed == [] or failed == 0) and not s.get("gates", {}).get("failed", []), "native identity/gates")
    req(s["python"].startswith("Python 3.13") and s["dotnetSdk"] == "8.0.423" and s["buildPassed"] is True, "native runtimes/build")
    req(s["pythonTestsPassed"] == 310 and s["xunitPassed"] == 916 and s["xunitFailed"] == 0 and s["xunitSkipped"] == 0, "unit-test counts")
    req(s["scenarioRunnerSelfTestsPassed"] == 70 and s["researchParityPassed"] == 25, "deterministic/parity gates")
    req(s["cp139FocusedTestsPassed"] == 9 and s["cp140FocusedTestsPassed"] == 10 and s["cp141FocusedTestsPassed"] == 10 and s["cp142FocusedTestsPassed"] == 12 and s["cp143FocusedTestsPassed"] == 12 and s["cp144FocusedTestsPassed"] == 11 and s["cp145FocusedTestsPassed"] == 12, "focused-test counts")
    req(s["cp142ReconciliationLedgerRows"] == 531 and s["cp142ChangedRows"] == 72 and s["cp142ExplicitUnresolvedRows"] == 7, "CP142 reconciliation regression")
    req(s["acceptedCp144StageAScenarios"] == 6850 and s["acceptedCp144SubstantiveCombatTrials"] == 3425000 and s["acceptedCp144EvidenceHashLocked"] is True, "accepted CP144 provenance")
    req(s["cp144SmokeResolved"] == 6785 and s["cp144SmokeResolvedGe25"] == 9 and s["cp144SmokeTurnCapSentinels"] == 65 and s["cp144SmokeSafeStalemates"] == 0 and s["cp144SmokeNonstandoffOpenOrders"] == 0, "CP144 smoke regression signature")
    req(s["sourceMatrixUnmodified"] is True and s["tuningAllowed"] is False and s["automaticPromotion"] is False and s["stageBAutomatic"] is False, "native scope")
    if final:
        req(s["repositoryOnlyAccepted"] is True and s["diagnosticAttributionCompleted"] is True, "final sequencing/completion")
        req(s["diagnosticScenarios"] == 252 and s["diagnosticTrialsPerScenario"] == 25 and s["diagnosticCombatTrials"] == 6300, "final diagnostic coverage")
        req(s["pdsOpportunityScenarios"] == 204 and s["tpStarvationScenarios"] == 48, "final diagnostic families")
    else:
        req(s["diagnosticCombatTrials"] == 0 and s["diagnosticAttributionCompleted"] is False, "RepositoryOnly must not execute CP145 diagnostic replays")
    return s


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--native-results"); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        d = js(repo / "tools/checkpoints/checkpoint-145/checkpoint_145_definition.json")
        req(d["checkpoint"] == 145 and d["expectedPythonTests"] == 310 and d["expectedXunitTests"] == 916 and d["expectedDiagnosticCombatTrials"] == 6300, "definition")
        count = validate_manifest(repo); json_count = 0
        for p in repo.rglob("*.json"):
            rel = p.relative_to(repo).as_posix(); wrapped = "/" + rel
            if rel.startswith("out/") or "/bin/" in wrapped or "/obj/" in wrapped:
                continue
            json.loads(p.read_text(encoding="utf-8-sig")); json_count += 1
        req(sha(repo / "docs/design/player_technology/technology_numerical_matrix_v0_9.json") == MATRIX_SHA, "source matrix drift")
        study = js(repo / "docs/archive/testing/pre-cp165-active/cp145_stage_a_diagnostic_attribution_study_v0_1.json")
        req(study["submittedCp144NativeResultsArchiveSha256"] == CP144_SUBMITTED_ARCHIVE_SHA, "submitted CP144 archive provenance drift")
        req(sha(repo / study["acceptedCp144ScenarioSurface"]) == CP144_SCENARIO_SURFACE_SHA, "accepted CP144 scenario surface hash drift")
        req(sha(repo / study["acceptedCp144ParetoSurface"]) == CP144_PARETO_SHA, "accepted CP144 Pareto surface hash drift")
        req(sha(repo / study["acceptedCp144Summary"]) == CP144_SUMMARY_SHA, "accepted CP144 summary hash drift")
        if args.native_results:
            native = Path(args.native_results).resolve(); final = (native / "CP145_NATIVE_ACCEPTANCE_SUMMARY.json").is_file()
            validate_native(native, final); validate_cp144_smoke(native)
            if final:
                validate_diagnostic(native)
        print(f"       CP145 contract verified: {count} repository-owned files; {json_count} JSON files; native-accepted CP144 evidence hash-locked; 252/6,300 zero-tuning diagnostic scope bound; source matrix frozen; Stage B disabled.")
        return 0
    except Exception as exc:
        print(f"CP145 contract failure: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
