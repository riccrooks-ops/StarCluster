#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

SKIP = "docs/validation/evidence/checkpoint-146/CP146_REPOSITORY_SHA256SUMS.txt"
MATRIX_SHA = "3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194"
CP145_NATIVE_SHA = "dada2c5120fb65e9c340ce6f9a5bbc40b32a195f98d89fcec9eba2382005aafa"


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
    path = repo / SKIP; req(path.is_file(), "CP146 repository manifest missing")
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


def validate_doctrine(root: Path) -> dict:
    base = root / "combat-resource-doctrine"; req((base / "summary.json").is_file(), "CP146 doctrine summary missing")
    s = js(base / "summary.json")
    req(s["passed"] is True and not s.get("failedGates", []), "CP146 doctrine gates")
    req(s["checkpoint"] == 146 and s["baseCheckpoint"] == 145, "CP146 doctrine identity")
    req(s["scenariosPerDoctrine"] == 252 and s["trialsPerScenarioPerDoctrine"] == 25, "CP146 doctrine scenario scope")
    req(s["combatTrialsPerDoctrine"] == 6300 and s["totalCombatTrials"] == 12600, "CP146 doctrine trial scope")
    req(s["acceptedCp145LegacyFieldMismatches"] == 0, "CP145 legacy reproduction mismatch")
    req(s["sourceMatrixUnmodified"] is True and s["tuningAllowed"] is False and s["automaticPromotion"] is False and s["stageBAutomatic"] is False, "CP146 numerical/promotion boundary")
    req(s["tl2LegacyTurnCaps"] > 0 and s["tl2ContextualTurnCaps"] <= s["tl2LegacyTurnCaps"] * 0.10, "CP146 TL2 turn-cap reduction")
    req(float(s["tl2ContextualMeanWeaponDenialTurnRate"]) < float(s["tl2LegacyMeanWeaponDenialTurnRate"]), "CP146 TL2 weapon-denial reduction")
    req(s["contextualWeaponCoreFundedTurns"] > 0 and s["contextualWeaponCoreStarvedTurns"] == 0, "CP146 legal weapon core funding")
    req(s["contextualNewSaturatedTurnCapCells"] == 0, "CP146 new saturated cell regression")
    req(s["contextualUnknownOpponentTurns"] > 0 and s["contextualKnownOpponentTurns"] > 0, "CP146 knowledge transition coverage")

    expected = {
        "legacy_replay_results.csv": 252,
        "contextual_replay_results.csv": 252,
        "legacy_reproduction_audit.csv": 252,
        "doctrine_delta_results.csv": 252,
        "tp_starvation_before_after.csv": 6,
        "contextual_activation_summary.csv": 8,
        "pds_magazine_subflight_coverage.csv": 12,
    }
    loaded = {}
    for name, count in expected.items():
        p = base / name; req(p.is_file(), f"missing CP146 doctrine artifact: {name}")
        loaded[name] = rows(p); req(len(loaded[name]) == count, f"{name} expected {count} rows got {len(loaded[name])}")
    req(all(int(r["field_mismatches"]) == 0 for r in loaded["legacy_reproduction_audit.csv"]), "legacy audit contains mismatches")
    req(sum(int(r["terminal_magazine_flights"]) for r in loaded["pds_magazine_subflight_coverage.csv"]) > 0, "magazine-flight PDS telemetry not exercised")
    req(sum(int(r["pds_visible_subflights"]) for r in loaded["pds_magazine_subflight_coverage.csv"]) > 0, "subflight PDS telemetry not exercised")
    return s


def validate_native(root: Path, final: bool) -> dict:
    name = "CP146_NATIVE_ACCEPTANCE_SUMMARY.json" if final else "CP146_REPOSITORY_ONLY_ACCEPTANCE.json"
    s = js(root / name)
    req(s["checkpoint"] == 146 and not s.get("failedGates", []), "native identity/gates")
    req(s["python"].startswith("Python 3.13") and s["dotnetSdk"] == "8.0.423" and s["buildPassed"] is True, "native runtimes/build")
    req(s["pythonTestsPassed"] == 328 and s["xunitPassed"] == 926 and s["xunitFailed"] == 0 and s["xunitSkipped"] == 0, "unit-test counts")
    req(s["scenarioRunnerSelfTestsPassed"] == 70 and s["researchParityPassed"] == 25, "deterministic/parity gates")
    req(s["cp139FocusedTestsPassed"] == 9 and s["cp140FocusedTestsPassed"] == 10 and s["cp141FocusedTestsPassed"] == 10 and s["cp142FocusedTestsPassed"] == 12 and s["cp143FocusedTestsPassed"] == 12 and s["cp144FocusedTestsPassed"] == 11 and s["cp145FocusedTestsPassed"] == 12 and s["cp146FocusedTestsPassed"] == 18, "focused-test counts")
    req(s["cp146DoctrineFixtureCases"] == 9, "shared doctrine fixture count")
    req(s["cp142ReconciliationLedgerRows"] == 531 and s["cp142ChangedRows"] == 72 and s["cp142ExplicitUnresolvedRows"] == 7, "CP142 reconciliation regression")
    req(s["acceptedCp145EvidenceHashLocked"] is True and s["sourceMatrixUnmodified"] is True, "CP145 provenance/matrix boundary")
    req(s["tuningAllowed"] is False and s["automaticPromotion"] is False and s["stageBAutomatic"] is False, "native promotion boundary")
    req(s["cp144SmokeResolved"] == 6785 and s["cp144SmokeResolvedGe25"] == 9 and s["cp144SmokeTurnCapSentinels"] == 65 and s["cp144SmokeSafeStalemates"] == 0 and s["cp144SmokeNonstandoffOpenOrders"] == 0, "CP144 legacy smoke regression")
    if final:
        req(s["repositoryOnlyAccepted"] is True and s["doctrineValidationCompleted"] is True, "final sequencing/completion")
        req(s["doctrineScenariosPerVersion"] == 252 and s["doctrineTrialsPerScenario"] == 25 and s["doctrineCombatTrialsPerVersion"] == 6300 and s["totalDoctrineCombatTrials"] == 12600, "final doctrine coverage")
        req(s["acceptedCp145LegacyFieldMismatches"] == 0 and s["contextualWeaponCoreStarvedTurns"] == 0 and s["contextualNewSaturatedTurnCapCells"] == 0, "final contextual behavior gates")
    else:
        req(s["doctrineValidationCompleted"] is False and s["totalDoctrineCombatTrials"] == 0, "RepositoryOnly must not execute CP146 doctrine study")
    return s


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--native-results"); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        d = js(repo / "tools/checkpoints/checkpoint-146/checkpoint_146_definition.json")
        req(d["checkpoint"] == 146 and d["expectedPythonTests"] == 328 and d["expectedXunitTests"] == 926 and d["expectedTotalDoctrineCombatTrials"] == 12600, "definition")
        count = validate_manifest(repo); json_count = 0
        for p in repo.rglob("*.json"):
            rel = p.relative_to(repo).as_posix(); wrapped = "/" + rel
            if rel.startswith("out/") or "/bin/" in wrapped or "/obj/" in wrapped: continue
            json.loads(p.read_text(encoding="utf-8-sig")); json_count += 1
        req(sha(repo / "docs/design/player_technology/technology_numerical_matrix_v0_9.json") == MATRIX_SHA, "source matrix drift")
        study = js(repo / "docs/archive/testing/pre-cp165-active/cp146_combat_resource_doctrine_study_v0_1.json")
        req(study["submittedCp145NativeResultsArchiveSha256"] == CP145_NATIVE_SHA, "submitted CP145 native archive provenance drift")
        if args.native_results:
            native = Path(args.native_results).resolve(); final = (native / "CP146_NATIVE_ACCEPTANCE_SUMMARY.json").is_file()
            validate_native(native, final); validate_cp144_smoke(native)
            if final: validate_doctrine(native)
        print(f"       CP146 contract verified: {count} repository-owned files; {json_count} JSON files; CP145 provenance hash-locked; matrix frozen; 12,600 logic-only doctrine trials bound; Stage B disabled.")
        return 0
    except Exception as exc:
        print(f"CP146 contract failure: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
