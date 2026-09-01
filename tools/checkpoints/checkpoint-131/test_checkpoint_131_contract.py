#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path


def req(value, message):
    if not value:
        raise AssertionError(message)


def text(path: Path) -> str:
    req(path.is_file(), f"missing {path}")
    return path.read_text(encoding="utf-8-sig")


def js(path: Path):
    return json.loads(text(path))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text(path).splitlines():
        if line.strip():
            digest, rel = line.split("  ", 1)
            out[rel] = digest
    return out


def owned_files(repo: Path) -> list[str]:
    out: list[str] = []
    skip = "docs/validation/evidence/checkpoint-131/CP131_REPOSITORY_SHA256SUMS.txt"
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        wrapped = "/" + rel
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in wrapped or rel.endswith(".pyc") or "/bin/" in wrapped or "/obj/" in wrapped or "/TestResults/" in wrapped:
            continue
        if rel == skip:
            continue
        out.append(rel)
    return sorted(out)


def validate_manifest(repo: Path) -> int:
    path = repo / "docs/validation/evidence/checkpoint-131/CP131_REPOSITORY_SHA256SUMS.txt"
    entries = manifest(path)
    current = owned_files(repo)
    req(set(current) == set(entries), f"manifest path drift missing={sorted(set(entries)-set(current))[:5]} extra={sorted(set(current)-set(entries))[:5]}")
    for rel, digest in entries.items():
        req(sha(repo / rel) == digest, f"manifest hash drift: {rel}")
    return len(entries)


def validate_repo_only(native: Path):
    summary = js(native / "CP131_REPOSITORY_ONLY_ACCEPTANCE.json")
    req(summary["checkpoint"] == 131 and summary["repositoryOnly"] is True and summary["failedGates"] == [], "repository-only identity")
    req(summary["python"].startswith("Python 3.13") and summary["dotnetSdk"] == "8.0.423", "runtime versions")
    req(summary["pythonTestsPassed"] == 190 and summary["xunitPassed"] == 907 and summary["xunitFailed"] == 0 and summary["xunitSkipped"] == 0, "test counts")
    req(summary["scenarioRunnerSelfTestsPassed"] == 70 and summary["researchParityPassed"] == 25, "self-test/parity")
    req(summary["technologyValuesChanged"] is False and summary["productionSourceChanged"] is False and summary["scenarioDefinitionsChanged"] is False, "frozen values/production")
    req(summary["missileCandidatesResearchOnly"] is True and summary["auxMagazineExecuted"] is False and summary["swarmerChanged"] is False, "candidate boundary")
    req(summary["acceptedCp130Tl1To7Plus2CarriedForward"] is True and summary["acceptedCp130LateAnchorReplayRequired"] is True, "CP130 evidence boundary")
    req(summary["legalBuilds"] == 9427 and summary["generatedVariants"] == 476936 and summary["pipelineSmokeTrials"] == 476936 and summary["pipelineSmokeTrialErrors"] == 0, "plan/smoke")
    req(summary["symmetryComparisons"] == 2250 and summary["symmetryCombatExecutions"] == 4500 and summary["symmetryMismatches"] == 0, "symmetry")
    req(1 <= int(summary["repositoryOnlyJobs"]) <= 61 and summary["substantiveTrials"] == 0, "repository-only Jobs/substantive boundary")
    plan = js(native / "plan/analysis.json")
    smoke = js(native / "smoke/analysis.json")
    sym = js(native / "symmetry/analysis.json")
    req(plan["checkpoint"] == 131 and plan["mode"] == "plan" and plan["failedGates"] == [], "plan output")
    req(plan["candidateCountsByTl"] == {"8": 20, "9": 26}, "plan candidate shape")
    req(smoke["checkpoint"] == 131 and smoke["mode"] == "smoke" and smoke["variants"] == 476936 and smoke["trialErrors"] == 0 and smoke["failedGates"] == [], "smoke output")
    req(sym["checkpoint"] == 129 and sym["mode"] == "symmetry_gate" and sym["mismatches"] == 0 and sym["failedGates"] == [], "inherited symmetry output")
    return summary


def validate_final(native: Path):
    prior = validate_repo_only(native)
    summary = js(native / "CP131_NATIVE_ACCEPTANCE_SUMMARY.json")
    req(summary["checkpoint"] == 131 and summary["repositoryOnly"] is False and summary["failedGates"] == [], "final identity")
    for key in ("python", "dotnetSdk", "pythonTestsPassed", "xunitPassed", "scenarioRunnerSelfTestsPassed", "researchParityPassed", "generatedVariants", "pipelineSmokeTrials", "symmetryComparisons", "symmetryMismatches"):
        req(summary[key] == prior[key], f"final/prior mismatch {key}")
    req(1 <= int(summary["substantiveJobs"]) <= 61 and summary["substantiveTrials"] == 47693600 and summary["substantiveTrialErrors"] == 0, "substantive workload")
    req(summary["technologyValuesChanged"] is False and summary["missileCandidatesResearchOnly"] is True and summary["cp130LateAnchorReplicationPassed"] is True, "final boundary/replication")
    analysis = js(native / "substantive/analysis.json")
    req(analysis["checkpoint"] == 131 and analysis["mode"] == "substantive" and analysis["variants"] == 476936 and analysis["totalTrials"] == 47693600 and analysis["trialErrors"] == 0 and analysis["failedGates"] == [], "substantive analysis")
    with (native / "substantive/family_plot_inputs.csv").open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    req(len(rows) == 46, "family plot candidate row count")
    req(sum(int(r["tl"]) == 8 for r in rows) == 20 and sum(int(r["tl"]) == 9 for r in rows) == 26, "family plot TL counts")
    with (native / "substantive/cp130_anchor_replication.csv").open(newline="", encoding="utf-8") as f:
        replication = list(csv.DictReader(f))
    req(len(replication) == 20 and all(abs(float(r["delta"])) <= 1e-12 for r in replication), "accepted CP130 anchor replication")
    with (native / "substantive/tl9_apen6_threshold_effects.csv").open(newline="", encoding="utf-8") as f:
        apen = list(csv.DictReader(f))
    req(len(apen) == 6, "TL9 APEN6 threshold effect rows")
    req((native / "substantive/missile_context_telemetry.csv").is_file(), "context telemetry missing")
    req(not list((native / "substantive/candidates").rglob("variants.csv")), "raw substantive variant detail should be discarded on success")
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--native-results")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-131/checkpoint_131_definition.json")
        req(definition["checkpoint"] == 131 and definition["expectedPythonTests"] == 190 and definition["monteCarloStudy"] is True, "definition")
        req(definition["expectedGeneratedVariants"] == 476936 and definition["expectedSubstantiveTrials"] == 47693600, "definition workload")
        accepted = js(repo / "docs/validation/evidence/checkpoint-131/CP130_NATIVE_ACCEPTANCE_SUMMARY.json")
        req(accepted["checkpoint"] == 130 and accepted["failedGates"] == [] and accepted["substantiveTrials"] == 24099600, "accepted CP130 evidence")
        if args.native_results:
            native = Path(args.native_results).resolve()
            if (native / "CP131_NATIVE_ACCEPTANCE_SUMMARY.json").is_file():
                validate_final(native)
            else:
                validate_repo_only(native)
        json_count = 0
        for path in repo.rglob("*.json"):
            rel = path.relative_to(repo).as_posix()
            wrapped = "/" + rel
            if rel.startswith("out/") or "/bin/" in wrapped or "/obj/" in wrapped:
                continue
            json.loads(path.read_text(encoding="utf-8-sig"))
            json_count += 1
        count = validate_manifest(repo)
        print(f"       CP131 contract verified: {count} repository-owned files; {json_count} JSON files; CP130 accepted; current numerical authority frozen; late Missile candidates research-only.")
        return 0
    except Exception as exc:
        print(f"CP131 contract failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
