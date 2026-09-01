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
            digest, rel = line.split("  ", 1)
            out[rel] = digest
    return out


def validate_results(native: Path) -> None:
    s = js(native / "CP127_NATIVE_ACCEPTANCE_SUMMARY.json")
    req(s["checkpoint"] == 127 and s["acceptedEvidenceCheckpoint"] == 126, "native identity")
    req(s["dotnetSdk"] == "8.0.423" and s["buildPassed"] is True and s["buildWarningsAsErrors"] is True, "native build")
    req(s["pythonTestsPassed"] == 170 and s["xunitPassed"] == 907 and s["xunitFailed"] == 0 and s["xunitSkipped"] == 0, "test counts")
    req(s["scenarioRunnerSelfTestsPassed"] == 70 and s["researchParityPassed"] == 25, "self-test/parity counts")
    req(s.get("pythonDependencyPolicy") == "stdlib-only" and s.get("thirdPartyPythonPackagesAllowed") == [], "stdlib-only Python dependency policy")
    req(s["symmetryComparisons"] == 2250 and s["symmetryCombatExecutions"] == 4500 and s["symmetryMismatches"] == 0, "symmetry gate")
    req(s["legalBuilds"] == 9427 and s["finalBaselineTasks"] == 18646 and s["finalBaselineVariants"] == 74584, "final baseline counts")
    req(s["tl5Tl6AblationVariants"] == 4320 and s["tl8EnergyVariants"] == 7680 and s["generatedVariants"] == 86584, "diagnostic counts")
    req(s["pipelineSmokeTrials"] == 86584 and s["telemetryContractMetrics"] == 61, "smoke/telemetry")
    req(s["technologyValuesChanged"] is True and s["numericLeafChanges"] == 9, "technology change boundary")
    req(s["productionSourceChanged"] is False and s["mixedTlShipsExecuted"] is False, "implementation/pure-TL boundary")
    req(s["auxiliaryNumericalStabilizationDeferred"] is True, "AUX deferral")
    req(s["balanceValidated"] is False and s["automaticPromotion"] is False, "promotion boundary")
    req(s["failedGates"] == [], "native failed gates")

    plan = js(native / "study-plan/analysis.json")
    req(plan["failedGates"] == [] and plan["legalBuilds"] == 9427 and plan["generatedVariants"] == 86584, "plan evidence")
    req(plan["finalBaselineTasks"] == 18646 and plan["finalBaselineVariants"] == 74584, "plan final baseline")
    req(plan["tl5Tl6AblationVariants"] == 4320 and plan["tl8EnergyVariants"] == 7680, "plan diagnostic lanes")
    req(plan["plannedSubstantiveTrials"] == 8658400 and plan["telemetryMetrics"] == 61, "planned workload")

    sym = js(native / "symmetry-gate/analysis.json")
    req(sym["failedGates"] == [] and sym["comparisons"] == 2250 and sym["combatExecutions"] == 4500 and sym["mismatches"] == 0, "symmetry evidence")

    smoke = js(native / "pipeline-smoke/analysis.json")
    req(smoke["failedGates"] == [] and smoke["variants"] == 86584 and smoke["totalTrials"] == 86584 and smoke["trialErrors"] == 0, "pipeline smoke")
    req(smoke["telemetryMetrics"] == 61 and smoke["mixedTlShipsExecuted"] is False, "smoke semantics")

    if not s["repositoryOnly"]:
        req(s["substantiveTrialsPerVariant"] == 100 and s["substantiveTrials"] == 8658400, "substantive workload")
        a = js(native / "main-subsystem-stabilization-study/analysis.json")
        req(a["failedGates"] == [] and a["variants"] == 86584 and a["totalTrials"] == 8658400 and a["trialErrors"] == 0, "substantive integrity")
        req(a["telemetryMetrics"] == 61 and a["mixedTlShipsExecuted"] is False, "substantive semantics")
        for name in (
            "adjacent_population_summary.csv",
            "matched_composition_summary.csv",
            "late_missile_summary.csv",
            "cp126_transition_comparison.csv",
            "tl5_tl6_ablation_summary.csv",
            "tl8_energy_factorial_summary.csv",
        ):
            req((native / "main-subsystem-stabilization-study" / name).is_file(), f"missing substantive output {name}")
    else:
        req(s["substantiveTrials"] == 0, "RepositoryOnly substantive trials")


def validate_manifest(repo: Path) -> int:
    p = repo / "docs/validation/evidence/checkpoint-127/CP127_REPOSITORY_SHA256SUMS.txt"
    m = manifest(p)
    current = []
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        wrapped = "/" + rel
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in wrapped or rel.endswith(".pyc") or "/bin/" in wrapped or "/obj/" in wrapped or "/TestResults/" in wrapped:
            continue
        if rel == "docs/validation/evidence/checkpoint-127/CP127_REPOSITORY_SHA256SUMS.txt":
            continue
        current.append(rel)
    req(set(current) == set(m), f"manifest path drift missing={sorted(set(m)-set(current))[:5]} extra={sorted(set(current)-set(m))[:5]}")
    for rel, digest in m.items():
        req(sha(repo / rel) == digest, f"manifest hash drift: {rel}")
    return len(m)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--native-results")
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        print("       Validating CP127 definition and accepted CP126 evidence...")
        d = js(repo / "tools/checkpoints/checkpoint-127/checkpoint_127_definition.json")
        req(d["checkpoint"] == 127 and d["expectedVariants"] == 86584 and d["expectedSubstantiveTrials"] == 8658400, "definition")
        req(d.get("expectedPythonTests") == 170 and d.get("pythonDependencyPolicy") == "stdlib-only" and d.get("thirdPartyPythonPackagesAllowed") == [], "Python dependency policy")
        cp126 = js(repo / "docs/validation/evidence/checkpoint-127/CP126_NATIVE_ACCEPTANCE_SUMMARY.json")
        req(cp126["checkpoint"] == 126 and cp126["failedGates"] == [], "CP126 provenance")
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
        print(f"       CP127 contract verified: {count} repository-owned files; {njson} JSON files; 9,427 pure-TL builds; 18,646 final-baseline tasks; 86,584 total variants; 2,250 zero-mismatch symmetry comparisons required; 8,658,400 substantive trials when normal; exactly nine numerical leaves changed; mixed-TL ships excluded; most AUX numerical stabilization deferred.")
        return 0
    except Exception as exc:
        print(f"CP127 contract failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
