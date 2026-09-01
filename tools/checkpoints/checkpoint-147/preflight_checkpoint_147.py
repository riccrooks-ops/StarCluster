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
CP146_SUBMITTED_NATIVE_SHA = "4df5a59531e4662df7e0b05f7fd4855606158aaeff6fea46c0b49426ae15e939"
CP146_MANIFEST = "docs/validation/evidence/checkpoint-146/CP146_REPOSITORY_SHA256SUMS.txt"
CP146_MANIFEST_SHA = "cccc757d08337ab156d13308411b84331d59aff9962d30492ba4b37fc1430450"
CP147_MANIFEST = "docs/validation/evidence/checkpoint-147/CP147_REPOSITORY_SHA256SUMS.txt"

ALLOWED_CP146_CHANGES = {
    "README.md",
    "CHAT_README.md",
    "docs/README.md",
    "docs/Prototype_TODO.md",
    "docs/development/Canonical_Combat_Simulation_Kernel.md",
    "docs/validation/README.md",
    "tools/simulation/starcluster_research/canonical_combat.py",
    "tools/simulation/starcluster_research/cli.py",
    "tools/simulation/starcluster_research/ecology.py",
    "tools/simulation/starcluster_research/stage_a_diagnostic_attribution.py",
    "tools/simulation/tests/test_cp132_canonical_kernel.py",
    "tools/simulation/tests/test_cp135_recharge_damcon_rebaseline.py",
    "tools/simulation/tests/test_cp136_armor_rebaseline.py",
    "tools/simulation/tests/test_cp137_finite_armor_regeneration.py",
    "tools/simulation/tests/test_cp141_combat_duration_stalemate.py",
    "tools/simulation/tests/test_cp144_whole_combat_stage_a_response_surface.py",
    "tools/simulation/tests/test_cp146_combat_resource_doctrine.py",
}

CP147_ADDITIONS = {
    "docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_parity_fixtures_v0_1.json",
    "docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_study_v0_1.json",
    "docs/validation/Checkpoint_147_Tactical_Package_Utility_And_Powered_Resource_Allocation.md",
    "docs/validation/evidence/checkpoint-147/accepted-cp146/CP146_ACCEPTED_CONTEXTUAL_REPLAY_RESULTS.csv",
    "docs/validation/evidence/checkpoint-147/accepted-cp146/CP146_ACCEPTED_DOCTRINE_SUMMARY.json",
    "docs/validation/evidence/checkpoint-147/accepted-cp146/CP146_NATIVE_ACCEPTANCE_SUMMARY.json",
    "src/StarCluster.Core/Combat/Tactics/TacticalPackageUtilityService.cs",
    "tests/StarCluster.Tests/Combat/Tactics/TacticalPackageUtilityServiceTests.cs",
    "tools/simulation/starcluster_research/tactical_package_utility.py",
    "tools/simulation/starcluster_research/tactical_package_utility_validation.py",
    "tools/simulation/tests/test_cp147_tactical_package_utility.py",
    "tools/checkpoints/checkpoint-147/apply_checkpoint_147.ps1",
    "tools/checkpoints/checkpoint-147/checkpoint_147_definition.json",
    "tools/checkpoints/checkpoint-147/preflight_checkpoint_147.py",
    "tools/checkpoints/checkpoint-147/test_checkpoint_147_contract.py",
}

NEW_CS = {
    "src/StarCluster.Core/Combat/Tactics/TacticalPackageUtilityService.cs",
    "tests/StarCluster.Tests/Combat/Tactics/TacticalPackageUtilityServiceTests.cs",
}


def req(value, message):
    if not value:
        raise AssertionError(message)


def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def js(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_manifest(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            h, rel = line.split("  ", 1); out[rel] = h
    return out


def owned(repo: Path) -> set[str]:
    out: set[str] = set()
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(repo).as_posix(); wrapped = "/" + rel
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in wrapped or rel.endswith(".pyc") or "/bin/" in wrapped or "/obj/" in wrapped or "/TestResults/" in wrapped:
            continue
        if rel == CP147_MANIFEST:
            continue
        out.add(rel)
    return out


def count_suite(suite) -> int:
    return sum(count_suite(x) if isinstance(x, unittest.TestSuite) else 1 for x in suite)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-147/checkpoint_147_definition.json")
        req(definition["checkpoint"] == 147 and definition["baseCheckpoint"] == 146, "checkpoint identity")
        req(definition["expectedPythonTests"] == 346 and definition["expectedPythonTestModules"] == 38, "Python test contract")
        req(definition["expectedXunitTests"] == 934 and definition["expectedScenarioRunnerSelfTests"] == 70, "native regression contract")
        req(definition["expectedFocusedCp147Tests"] == 18 and definition["expectedCp147UtilityFixtureCases"] == 10 and definition["expectedCp146DoctrineFixtureCases"] == 9, "CP147 focused/fixture contract")
        req(definition["expectedUtilityScenariosPerVersion"] == 252 and definition["expectedCombatTrialsPerDoctrine"] == 6300 and definition["expectedTotalUtilityCombatTrials"] == 12600, "utility study scope")
        req(definition["tuningAllowed"] is False and definition["automaticPromotion"] is False and definition["stageBAutomatic"] is False, "promotion boundary")

        req(sha(repo / "docs/design/player_technology/technology_numerical_matrix_v0_9.json") == MATRIX_SHA, "Technology Numerical Matrix drift")
        req(sha(repo / "docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx") == CONCEPT_SHA, "Concept v0.7x drift")
        cp146_path = repo / CP146_MANIFEST
        req(cp146_path.is_file() and sha(cp146_path) == CP146_MANIFEST_SHA, "accepted CP146 repository manifest drift")
        cp146 = read_manifest(cp146_path)

        frozen = 0
        for rel, expected in cp146.items():
            req((repo / rel).is_file(), f"missing CP146-owned file: {rel}")
            if rel in ALLOWED_CP146_CHANGES:
                continue
            req(sha(repo / rel) == expected, f"unexpected CP146 baseline drift: {rel}")
            frozen += 1

        cp146_cs = {rel for rel in cp146 if rel.endswith(".cs")}
        current_cs = {p.relative_to(repo).as_posix() for p in repo.rglob("*.cs") if "/bin/" not in ("/" + p.relative_to(repo).as_posix()) and "/obj/" not in ("/" + p.relative_to(repo).as_posix())}
        req(current_cs == cp146_cs | NEW_CS, f"C# path-set drift added={sorted(current_cs-(cp146_cs|NEW_CS))[:5]} missing={sorted((cp146_cs|NEW_CS)-current_cs)[:5]}")
        for rel in cp146_cs:
            req(sha(repo / rel) == cp146[rel], f"CP146 inherited C# drift: {rel}")

        expected_paths = set(cp146) | {CP146_MANIFEST} | CP147_ADDITIONS
        current_paths = owned(repo)
        req(current_paths == expected_paths, f"CP147 repository path drift added={sorted(current_paths-expected_paths)[:8]} missing={sorted(expected_paths-current_paths)[:8]}")

        study = js(repo / "docs/archive/testing/pre-cp165-active/cp147_tactical_package_utility_study_v0_1.json")
        req(study["checkpoint"] == 147 and study["baseCheckpoint"] == 146, "study identity")
        req(study["submittedCp146NativeResultsArchiveSha256"] == CP146_SUBMITTED_NATIVE_SHA, "submitted CP146 native provenance drift")
        req(study["masterSeed"] == 140001 and study["expectedTotalCombatTrials"] == 12600, "study seed/trial scope")
        req(study["tuningAllowed"] is False and study["automaticPromotion"] is False and study["stageBAutomatic"] is False, "study promotion boundary")

        accepted_summary = js(repo / study["acceptedCp146NativeSummary"])
        req(accepted_summary["checkpoint"] == 146 and accepted_summary["repositoryOnlyAccepted"] is True, "accepted CP146 native summary identity")
        req(accepted_summary["pythonTestsPassed"] == 328 and accepted_summary["xunitPassed"] == 926 and accepted_summary["totalDoctrineCombatTrials"] == 12600, "accepted CP146 native regression identity")
        req(accepted_summary["acceptedCp145LegacyFieldMismatches"] == 0 and accepted_summary["contextualWeaponCoreStarvedTurns"] == 0, "accepted CP146 behavioral identity")

        sim = repo / "tools/simulation"; sys.path.insert(0, str(sim))
        from starcluster_research.tactical_package_utility import decide_contract_case
        from starcluster_research.tactical_package_utility_validation import validate_population, validate_study
        from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
        study_errors = validate_study(study); pop_errors = validate_population(repo, study)
        req(study_errors == [], f"CP147 study validation: {study_errors}")
        req(pop_errors == [], f"CP147 population validation: {pop_errors}")
        req(CANONICAL_COMBAT_KERNEL_VERSION == "0.7", "CP147 kernel version")
        fixture = js(repo / study["utilityParityFixtures"])
        req(fixture.get("checkpoint") == 147 and len(fixture["cases"]) == 10, "shared utility fixture case count")
        for case in fixture["cases"]:
            req(decide_contract_case(case)["selectedId"] == case["expectedSelectedId"], f"Python utility fixture mismatch: {case['id']}")

        kernel = (repo / "tools/simulation/starcluster_research/canonical_combat.py").read_text(encoding="utf-8")
        for marker in ("UTILITY_COMBAT_DOCTRINE", "_cp147_expected_terminal_loss", "_cp147_project_terminal_threats", "held_main_interception"):
            req(marker in kernel, f"CP147 kernel marker missing: {marker}")
        ecology = (repo / "tools/simulation/starcluster_research/ecology.py").read_text(encoding="utf-8")
        for marker in ("UTILITY_COMBAT_DOCTRINE", "_plan_once_utility", "_cp147_turn_start_reserve_estimate", "cp147_sole_main_diversions_without_hull_risk"):
            req(marker in ecology, f"CP147 ecology marker missing: {marker}")
        service = (repo / "src/StarCluster.Core/Combat/Tactics/TacticalPackageUtilityService.cs").read_text(encoding="utf-8")
        for marker in ("TacticalPackageCandidate", "Choose", "OffenseUtilityMilli", "DefenseUtilityMilli", "HeldMainBanks"):
            req(marker in service, f"CP147 C# utility marker missing: {marker}")

        suite = unittest.defaultTestLoader.discover(str(repo / "tools/simulation/tests"), pattern="test_*.py")
        total = count_suite(suite); modules = len(list((repo / "tools/simulation/tests").glob("test_*.py")))
        req(total == 346 and modules == 38, f"Python discovery mismatch: tests={total} modules={modules}")

        print(f"CP147 preflight PASS: {frozen} inherited CP146-owned files frozen; {len(cp146_cs)} inherited C# files frozen; 2 declared new C# files; {len(current_paths)} repository-owned paths; Python discovery {total}/{modules}; matrix/Concept unchanged; accepted CP146 evidence hash-locked.")
        return 0
    except Exception as exc:
        print(f"CP147 preflight failure: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
