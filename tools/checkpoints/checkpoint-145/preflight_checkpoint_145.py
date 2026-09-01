#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unittest
from pathlib import Path

MATRIX_SHA = "3088b0a9eb45f6bf505c24513e8bb2ac878819db4ab464ccfea330243c82f194"
CONCEPT_SHA = "f76ca6ce488ccb5ad1352f7d38b8c3d4657c12ed64d0c93cc45d2db605cc632f"
CP144_SUBMITTED_ARCHIVE_SHA = "71bd2b81980701292d6cd463b2a225752274a1045ea4e813c83e5728e9f961fd"
CP144_SUMMARY_SHA = "ce3eef4f9a9b31d12c99bedb84715f27549d6e4ec79f2ec02163beedea21dd93"
CP144_SCENARIO_SURFACE_SHA = "ffa17024e0aed42be2def3f6b9e64a492da5c52d7d512cc31552aa19d6a132fd"
CP144_PARETO_SHA = "a60975cb58afdf735d27aac4692182eb7080dfcf10f15c419194177fc2df6e15"
CP144_PAIRWISE_SHA = "deb412591a006278c823b1cd24429e2412046390d123d41e7d3e812fa59078ad"
CP144_MANIFEST = "docs/validation/evidence/checkpoint-144/CP144_REPOSITORY_SHA256SUMS.txt"
ALLOWED_CP144_CHANGES = {
    "README.md",
    "CHAT_README.md",
    "docs/validation/README.md",
    "tools/simulation/starcluster_research/canonical_combat.py",
    "tools/simulation/starcluster_research/cli.py",
}


def req(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_manifest(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            h, rel = line.split("  ", 1); out[rel] = h
    return out


def count_suite(suite) -> int:
    return sum(count_suite(x) if isinstance(x, unittest.TestSuite) else 1 for x in suite)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-145/checkpoint_145_definition.json")
        req(definition["checkpoint"] == 145 and definition["baseCheckpoint"] == 144, "checkpoint identity")
        req(definition["expectedPythonTests"] == 310 and definition["expectedPythonTestModules"] == 36, "Python test contract")
        req(definition["expectedXunitTests"] == 916 and definition["expectedScenarioRunnerSelfTests"] == 70, "native regression contract")
        req(definition["expectedDiagnosticScenarios"] == 252 and definition["expectedDiagnosticCombatTrials"] == 6300, "diagnostic scope")
        req(definition["expectedPdsOpportunityScenarios"] == 204 and definition["expectedTpStarvationScenarios"] == 48, "diagnostic families")
        req(definition["diagnosticTrialsPerScenario"] == 25 and definition["hardTurnSentinel"] == 60 and definition["longResolvedTurn"] == 25, "diagnostic boundaries")
        req(definition["tuningAllowed"] is False and definition["automaticPromotion"] is False and definition["stageBAutomatic"] is False, "promotion boundary")

        req(sha(repo / "docs/design/player_technology/technology_numerical_matrix_v0_9.json") == MATRIX_SHA, "Technology Numerical Matrix drift")
        req(sha(repo / "docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx") == CONCEPT_SHA, "Concept v0.7x drift")

        # Freeze every CP144-owned file except the five explicitly documented CP145 edits.
        cp144_path = repo / CP144_MANIFEST; req(cp144_path.is_file(), "CP144 repository manifest missing")
        cp144 = read_manifest(cp144_path); frozen = 0
        for rel, expected in cp144.items():
            if rel in ALLOWED_CP144_CHANGES:
                req((repo / rel).is_file(), f"allowed CP145 edit path missing: {rel}")
                continue
            req((repo / rel).is_file(), f"missing CP144-owned file: {rel}")
            req(sha(repo / rel) == expected, f"unexpected CP144 baseline drift: {rel}")
            frozen += 1
        # No new C# may appear; all C# remains byte-identical to native-accepted CP144.
        cp144_cs = {rel for rel in cp144 if rel.endswith(".cs")}
        current_cs = {p.relative_to(repo).as_posix() for p in repo.rglob("*.cs") if "/bin/" not in ("/" + p.relative_to(repo).as_posix()) and "/obj/" not in ("/" + p.relative_to(repo).as_posix())}
        req(current_cs == cp144_cs, f"C# path-set drift added={sorted(current_cs-cp144_cs)[:5]} missing={sorted(cp144_cs-current_cs)[:5]}")
        for rel in cp144_cs:
            req(sha(repo / rel) == cp144[rel], f"CP144 C# drift: {rel}")

        required = (
            "docs/archive/testing/pre-cp165-active/cp145_stage_a_diagnostic_attribution_study_v0_1.json",
            "docs/archive/testing/pre-cp165-active/cp145_diagnostic_replay_manifest.csv",
            "tools/simulation/starcluster_research/stage_a_diagnostic_attribution.py",
            "tools/simulation/tests/test_cp145_stage_a_diagnostic_attribution.py",
            "docs/validation/evidence/checkpoint-145/accepted-cp144/CP144_ACCEPTED_SCENARIO_RESPONSE_SURFACE.csv",
            "docs/validation/evidence/checkpoint-145/accepted-cp144/CP144_ACCEPTED_PARETO_CHOICE_SURFACE.csv",
            "docs/validation/evidence/checkpoint-145/accepted-cp144/CP144_NATIVE_ACCEPTANCE_SUMMARY.json",
            "docs/validation/evidence/checkpoint-145/accepted-cp144/CP144_ACCEPTED_BASELINE_PROVENANCE.json",
            "docs/validation/Checkpoint_145_Stage_A_Diagnostic_Attribution_And_Strategic_Viability.md",
        )
        for rel in required:
            req((repo / rel).is_file(), f"missing CP145 dependency: {rel}")

        study = js(repo / "docs/archive/testing/pre-cp165-active/cp145_stage_a_diagnostic_attribution_study_v0_1.json")
        req(study["checkpoint"] == 145 and study["baseCheckpoint"] == 144, "study identity")
        req(study["masterSeed"] == 140001, "CP145 must replay exact CP144 master seed")
        req(study["diagnosticCombatTrials"] == 6300 and study["diagnosticTrialsPerScenario"] == 25, "study diagnostic trials")
        req(study["tuningAllowed"] is False and study["automaticPromotion"] is False and study["stageBAutomatic"] is False, "study promotion boundary")
        summary = repo / study["acceptedCp144Summary"]
        scenario = repo / study["acceptedCp144ScenarioSurface"]
        pareto_surface = repo / study["acceptedCp144ParetoSurface"]
        req(study["submittedCp144NativeResultsArchiveSha256"] == CP144_SUBMITTED_ARCHIVE_SHA, "submitted CP144 archive provenance drift")
        req(sha(summary) == CP144_SUMMARY_SHA == study["acceptedCp144SummarySha256"], "accepted CP144 summary drift")
        req(sha(scenario) == CP144_SCENARIO_SURFACE_SHA == study["acceptedScenarioSurfaceSha256"], "accepted CP144 scenario surface drift")
        req(sha(pareto_surface) == CP144_PARETO_SHA == study["acceptedParetoSurfaceSha256"], "accepted CP144 Pareto surface drift")
        req(study["acceptedPairwiseSurfaceSha256"] == CP144_PAIRWISE_SHA, "accepted CP144 pairwise binding")
        accepted = js(summary)
        req(accepted["checkpoint"] == 144 and accepted["substantiveStageACompleted"] is True and accepted["substantiveCombatTrials"] == 3425000, "accepted CP144 native completion")
        req(accepted["pythonTestsPassed"] == 298 and accepted["xunitPassed"] == 916 and accepted["cp144FocusedTestsPassed"] == 11, "accepted CP144 regression identity")

        sim = repo / "tools/simulation"; sys.path.insert(0, str(sim))
        from starcluster_research.stage_a_diagnostic_attribution import _accepted_surfaces, validate_population, validate_study
        req(validate_study(study) == [], f"CP145 study validation: {validate_study(study)}")
        req(validate_population(repo, study) == [], f"CP145 population validation: {validate_population(repo, study)}")
        rows, pareto, _ = _accepted_surfaces(repo, study)
        req(len(rows) == 6850 and sum(int(r["trials"]) for r in rows) == 3425000, "accepted CP144 response surface coverage")
        req(len(pareto) == 6850, "accepted CP144 Pareto surface coverage")

        kernel = (repo / "tools/simulation/starcluster_research/canonical_combat.py").read_text(encoding="utf-8")
        for marker in ("tp_requested_weapon", "tp_denied_weapon", "pds_terminal_phase", "unserved_attempt_opportunities", "pds_reaction_capacity_planned"):
            req(marker in kernel, f"CP145 telemetry marker missing: {marker}")

        suite = unittest.defaultTestLoader.discover(str(repo / "tools/simulation/tests"), pattern="test_*.py")
        total = count_suite(suite); modules = len(list((repo / "tools/simulation/tests").glob("test_*.py")))
        req(total == 310, f"Python discovery expected 310 got {total}")
        req(modules == 36, f"Python test modules expected 36 got {modules}")
        print(f"       CP145 preflight passed: native-accepted CP144 frozen across {frozen} unchanged owned files and all {len(cp144_cs)} C# files; accepted 3,425,000-trial surface hash-locked; 252 diagnostic identities / 6,300 exact-seed trials declared; 310 Python tests in 36 modules discovered; tuning/promotion/Stage B disabled.")
        return 0
    except Exception as exc:
        print(f"CP145 preflight failure: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
