#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def req(value, message):
    if not value:
        raise AssertionError(message)


def text(path: Path) -> str:
    req(path.is_file(), f"Missing {path}")
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
    out = {}
    for line in text(path).splitlines():
        if line.strip():
            h, rel = line.split("  ", 1)
            out[rel] = h
    return out


def validate_results(native: Path) -> None:
    s = js(native / "CP126_NATIVE_ACCEPTANCE_SUMMARY.json")
    req(s["checkpoint"] == 126 and s["acceptedPureTlStudy"] == 125, "native identity")
    req(s["dotnetSdk"] == "8.0.423" and s["buildPassed"] is True and s["buildWarningsAsErrors"] is True, "native build")
    req(s["pythonTestsPassed"] == 160 and s["xunitPassed"] == 907 and s["xunitFailed"] == 0, "test counts")
    req(s["scenarioRunnerSelfTestsPassed"] == 70 and s["researchParityPassed"] == 25, "self-test/parity counts")
    req(s["symmetryComparisons"] == 2250 and s["symmetryMismatches"] == 0, "symmetry gate")
    req(s["legalBuilds"] == 9427 and s["compactTasks"] == 25678 and s["generatedVariants"] == 139000, "plan counts")
    req(s["pipelineSmokeTrials"] == 139000 and s["telemetryContractMetrics"] == 61, "smoke/telemetry")
    req(s["sameTlComponentsPerShip"] is True and s["mixedTlShipsExecuted"] is False, "pure-TL semantics")
    req(s["technologyValuesChanged"] is False and s["balanceValidated"] is False and s["automaticPromotion"] is False, "promotion boundary")
    req(s["failedGates"] == [], "native failed gates")

    plan = js(native / "study-plan/analysis.json")
    req(plan["failedGates"] == [] and plan["compactTasks"] == 25678 and plan["generatedVariants"] == 139000, "plan evidence")
    req(plan["plannedSubstantiveTrials"] == 34750000 and plan["telemetryMetrics"] == 61, "planned workload")
    sym = js(native / "symmetry-gate/analysis.json")
    req(sym["failedGates"] == [] and sym["comparisons"] == 2250 and sym["combatExecutions"] == 4500 and sym["mismatches"] == 0, "symmetry evidence")
    smoke = js(native / "full-map-smoke/analysis.json")
    req(smoke["failedGates"] == [] and smoke["totalTrials"] == 139000 and smoke["trialErrors"] == 0, "full-map smoke")

    if not s["repositoryOnly"]:
        req(s["substantiveTrialsPerVariant"] == 250 and s["substantiveTrials"] == 34750000, "substantive workload")
        a = js(native / "fidelity-era-attribution-study/analysis.json")
        req(a["failedGates"] == [] and a["variants"] == 139000 and a["totalTrials"] == 34750000 and a["trialErrors"] == 0, "substantive integrity")
        req(a["telemetryMetrics"] == 61 and a["mixedTlShipsExecuted"] is False, "substantive semantics")
        for name in (
            "variants.csv", "normalized_pairing_outcomes.csv", "adjacent_population_summary.csv",
            "matched_composition_summary.csv", "era_boundary_attribution_summary.csv",
            "adjacent_telemetry_summary.csv", "geometry_delta_summary.csv", "movement_geometry_comparison.csv",
            "late_missile_geometry_summary.csv", "swarmer_lifecycle_summary.csv", "energy_isolation_summary.csv",
        ):
            req((native / "fidelity-era-attribution-study" / name).is_file(), f"missing substantive output {name}")
    else:
        req(s["substantiveTrials"] == 0, "RepositoryOnly substantive trials")


def validate_manifest(repo: Path) -> int:
    p = repo / "docs/validation/evidence/checkpoint-126/CP126_REPOSITORY_SHA256SUMS.txt"
    m = manifest(p)
    current = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in "/" + rel or rel.endswith(".pyc") or "/bin/" in "/" + rel or "/obj/" in "/" + rel:
            continue
        if rel == "docs/validation/evidence/checkpoint-126/CP126_REPOSITORY_SHA256SUMS.txt":
            continue
        current.append(rel)
    req(set(current) == set(m), f"manifest path drift missing={sorted(set(m)-set(current))[:5]} extra={sorted(set(current)-set(m))[:5]}")
    for rel, h in m.items():
        req(sha(repo / rel) == h, f"manifest hash drift: {rel}")
    return len(m)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--native-results")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        print("       Validating CP126 definition, accepted CP125 provenance, and fidelity/attribution authorities...")
        d = js(repo / "tools/checkpoints/checkpoint-126/checkpoint_126_definition.json")
        req(d["checkpoint"] == 126 and d["expectedVariants"] == 139000, "definition")
        p = js(repo / "docs/validation/evidence/checkpoint-126/CP126_ACCEPTED_CP125_NATIVE_SUMMARY.json")
        req(p["acceptedCheckpoint"] == 125 and p["failedGates"] == [], "CP125 provenance")
        if args.native_results:
            validate_results(Path(args.native_results).resolve())
        print("       Parsing owned JSON corpus...")
        njson = 0
        for pth in repo.rglob("*.json"):
            rel = pth.relative_to(repo).as_posix()
            if rel.startswith("out/") or "/bin/" in "/" + rel or "/obj/" in "/" + rel:
                continue
            json.loads(pth.read_text(encoding="utf-8-sig"))
            njson += 1
        print("       Validating full repository manifest...")
        count = validate_manifest(repo)
        print(f"       CP126 contract verified: {count} repository-owned files; {njson} JSON files; 9,427 pure-TL builds; 25,678 tasks; 139,000 full-map variants; 2,250 zero-mismatch symmetry comparisons required; 34,750,000 substantive trials when normal; mixed-TL ships excluded.")
        return 0
    except Exception as exc:
        print(f"CP126 contract failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
