#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

MATRIX_SHA = "3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194"
CP146_NATIVE_SHA = "4df5a59531e4662df7e0b05f7fd4855606158aaeff6fea46c0b49426ae15e939"
SKIP = "docs/validation/evidence/checkpoint-147/CP147_REPOSITORY_SHA256SUMS.txt"


def req(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rows(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def manifest(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            h, rel = line.split("  ", 1); out[rel] = h
    return out


def owned(repo: Path) -> list[str]:
    out: list[str] = []
    for p in repo.rglob("*"):
        if not p.is_file(): continue
        rel = p.relative_to(repo).as_posix(); wrapped = "/" + rel
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in wrapped or rel.endswith(".pyc") or "/bin/" in wrapped or "/obj/" in wrapped or "/TestResults/" in wrapped: continue
        if rel == SKIP: continue
        out.append(rel)
    return sorted(out)


def validate_manifest(repo: Path) -> int:
    path = repo / SKIP; req(path.is_file(), "CP147 repository manifest missing")
    entries = manifest(path); current = owned(repo)
    req(set(entries) == set(current), f"manifest path drift missing={sorted(set(entries)-set(current))[:8]} extra={sorted(set(current)-set(entries))[:8]}")
    for rel, expected in entries.items():
        req(sha(repo / rel) == expected, f"manifest hash drift: {rel}")
    return len(entries)


def validate_cp144_smoke(root: Path) -> dict:
    base = root / "cp144-stage-a-smoke-merged"; req((base / "summary.json").is_file(), "CP144 legacy smoke summary missing")
    s = js(base / "summary.json")
    req(s["passed"] is True and not s.get("gates", {}).get("failed", []), "CP144 legacy smoke gates")
    req(s["stageAScenarios"] == 6850 and s["integrationSmokeTrials"] == 6850 and s["executionErrors"] == 0, "CP144 legacy smoke coverage")
    req(s["resolved"] == 6785 and s["resolvedGe25"] == 9 and s["turnCapSentinels"] == 65 and s["safeStalemates"] == 0, "CP144 legacy smoke deterministic signature")
    req(s["nonstandoffOpenOrders"] == 0 and s["sourceMatrixUnmodified"] is True and s["substantiveCombatTrials"] == 0, "CP144 legacy smoke scope")
    rs = rows(base / "whole_combat_smoke_results.csv")
    req(len(rs) == 6850 and all(not r["error"] and int(r["nonstandoff_open_orders"]) == 0 for r in rs), "CP144 legacy smoke rows")
    return s


def validate_utility(root: Path) -> dict:
    base = root / "tactical-package-utility"; req((base / "summary.json").is_file(), "CP147 utility summary missing")
    s = js(base / "summary.json")
    req(s["passed"] is True and not s.get("failedGates", []), "CP147 utility gates")
    req(s["checkpoint"] == 147 and s["baseCheckpoint"] == 146, "CP147 utility identity")
    req(s["scenariosPerDoctrine"] == 252 and s["trialsPerScenarioPerDoctrine"] == 25, "CP147 utility scenario scope")
    req(s["combatTrialsPerDoctrine"] == 6300 and s["totalCombatTrials"] == 12600, "CP147 utility trial scope")
    req(s["acceptedCp146FieldMismatches"] == 0, "CP146 contextual reproduction mismatch")
    req(s["sourceMatrixUnmodified"] is True and s["tuningAllowed"] is False and s["automaticPromotion"] is False and s["stageBAutomatic"] is False, "CP147 numerical/promotion boundary")
    req(s["cp147TurnCapSentinels"] == 0 and s["cp147Tl2TurnCapSentinels"] == 0 and s["cp147NewSaturatedTurnCapCells"] == 0, "CP147 duration/starvation regression")
    req(s["cp147PackageDecisions"] > 0 and s["cp147DirectPackageSelections"] > 0 and s["cp147HeldPackageSelections"] > 0 and s["cp147HeldMainAttempts"] > 0 and s["cp147PdsPackageSelections"] > 0, "CP147 utility action coverage")
    req(s["cp147SoleMainDiversionsWithoutHullRisk"] == 0, "CP147 invalid sole-main diversion")

    expected = {
        "cp146_replay_results.csv": 252,
        "cp147_replay_results.csv": 252,
        "cp146_reproduction_audit.csv": 252,
        "utility_delta_results.csv": 252,
        "tp_starvation_before_after.csv": 6,
        "utility_action_summary.csv": 8,
        "missile_action_selection_summary.csv": 24,
    }
    loaded = {}
    for name, count in expected.items():
        p = base / name; req(p.is_file(), f"missing CP147 utility artifact: {name}")
        loaded[name] = rows(p); req(len(loaded[name]) == count, f"{name} expected {count} rows got {len(loaded[name])}")
    req(all(int(r["field_mismatches"]) == 0 for r in loaded["cp146_reproduction_audit.csv"]), "CP146 reproduction audit contains mismatches")
    req(sum(int(r["held_package_selections"]) for r in loaded["missile_action_selection_summary.csv"]) > 0, "natural Held Main selection not represented in missile summary")
    req(sum(int(r["held_main_attempts"]) for r in loaded["missile_action_selection_summary.csv"]) > 0, "Held Main resolver not exercised")
    req(sum(int(r["sole_main_diversions_without_hull_risk"]) for r in loaded["missile_action_selection_summary.csv"]) == 0, "invalid sole-main diversion in missile summary")
    return s


def validate_native(root: Path, final: bool) -> dict:
    name = "CP147_NATIVE_ACCEPTANCE_SUMMARY.json" if final else "CP147_REPOSITORY_ONLY_ACCEPTANCE.json"
    s = js(root / name)
    req(s["checkpoint"] == 147 and not s.get("failedGates", []), "native identity/gates")
    req(s["python"].startswith("Python 3.13") and s["dotnetSdk"] == "8.0.423" and s["buildPassed"] is True, "native runtimes/build")
    req(s["pythonTestsPassed"] == 346 and s["xunitPassed"] == 934 and s["xunitFailed"] == 0 and s["xunitSkipped"] == 0, "unit-test counts")
    req(s["scenarioRunnerSelfTestsPassed"] == 70 and s["researchParityPassed"] == 25, "deterministic/parity gates")
    req(s["cp139FocusedTestsPassed"] == 9 and s["cp140FocusedTestsPassed"] == 10 and s["cp141FocusedTestsPassed"] == 10 and s["cp142FocusedTestsPassed"] == 12 and s["cp143FocusedTestsPassed"] == 12 and s["cp144FocusedTestsPassed"] == 11 and s["cp145FocusedTestsPassed"] == 12 and s["cp146FocusedTestsPassed"] == 18 and s["cp147FocusedTestsPassed"] == 18, "focused-test counts")
    req(s["cp146DoctrineFixtureCases"] == 9 and s["cp147UtilityFixtureCases"] == 10, "shared fixture counts")
    req(s["cp142ReconciliationLedgerRows"] == 531 and s["cp142ChangedRows"] == 72 and s["cp142ExplicitUnresolvedRows"] == 7, "CP142 reconciliation regression")
    req(s["acceptedCp146EvidenceHashLocked"] is True and s["sourceMatrixUnmodified"] is True, "CP146 provenance/matrix boundary")
    req(s["tuningAllowed"] is False and s["automaticPromotion"] is False and s["stageBAutomatic"] is False, "native promotion boundary")
    req(s["cp144SmokeResolved"] == 6785 and s["cp144SmokeResolvedGe25"] == 9 and s["cp144SmokeTurnCapSentinels"] == 65 and s["cp144SmokeSafeStalemates"] == 0 and s["cp144SmokeNonstandoffOpenOrders"] == 0, "CP144 legacy smoke regression")
    if final:
        req(s["repositoryOnlyAccepted"] is True and s["utilityValidationCompleted"] is True, "final sequencing/completion")
        req(s["utilityScenariosPerVersion"] == 252 and s["utilityTrialsPerScenario"] == 25 and s["utilityCombatTrialsPerVersion"] == 6300 and s["totalUtilityCombatTrials"] == 12600, "final utility coverage")
        req(s["acceptedCp146FieldMismatches"] == 0 and s["cp147TurnCapSentinels"] == 0 and s["cp147Tl2TurnCapSentinels"] == 0 and s["cp147NewSaturatedTurnCapCells"] == 0, "final duration/reproduction gates")
        req(s["cp147PackageDecisions"] > 0 and s["cp147DirectPackageSelections"] > 0 and s["cp147HeldPackageSelections"] > 0 and s["cp147HeldMainAttempts"] > 0 and s["cp147PdsPackageSelections"] > 0, "final action coverage")
        req(s["cp147SoleMainDiversionsWithoutHullRisk"] == 0, "final invalid sole-main diversion")
    else:
        req(s["utilityValidationCompleted"] is False and s["totalUtilityCombatTrials"] == 0, "RepositoryOnly must not execute CP147 utility study")
    return s


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--native-results"); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        d = js(repo / "tools/checkpoints/checkpoint-147/checkpoint_147_definition.json")
        req(d["checkpoint"] == 147 and d["expectedPythonTests"] == 346 and d["expectedXunitTests"] == 934 and d["expectedTotalUtilityCombatTrials"] == 12600, "definition")
        count = validate_manifest(repo); json_count = 0
        for p in repo.rglob("*.json"):
            rel = p.relative_to(repo).as_posix(); wrapped = "/" + rel
            if rel.startswith("out/") or "/bin/" in wrapped or "/obj/" in wrapped: continue
            json.loads(p.read_text(encoding="utf-8-sig")); json_count += 1
        req(sha(repo / "docs/design/player_technology/technology_numerical_matrix_v0_9.json") == MATRIX_SHA, "source matrix drift")
        study = js(repo / "docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_study_v0_1.json")
        req(study["submittedCp146NativeResultsArchiveSha256"] == CP146_NATIVE_SHA, "submitted CP146 native archive provenance drift")
        if args.native_results:
            native = Path(args.native_results).resolve(); final = (native / "CP147_NATIVE_ACCEPTANCE_SUMMARY.json").is_file()
            validate_native(native, final); validate_cp144_smoke(native)
            if final: validate_utility(native)
        print(f"       CP147 contract verified: {count} repository-owned files; {json_count} JSON files; CP146 provenance hash-locked; matrix frozen; 12,600 logic-only utility trials bound; Stage B disabled.")
        return 0
    except Exception as exc:
        print(f"CP147 contract failure: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
