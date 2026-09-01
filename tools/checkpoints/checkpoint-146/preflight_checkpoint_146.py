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
CP145_SUBMITTED_NATIVE_SHA = "dada2c5120fb65e9c340ce6f9a5bbc40b32a195f98d89fcec9eba2382005aafa"
CP145_MANIFEST = "docs/validation/evidence/checkpoint-145/CP145_REPOSITORY_SHA256SUMS.txt"
CP145_MANIFEST_SHA = "0b37d94d297f4316ab35cdd3a2fc1d465a125476e3796d8012715c538c8d6f5f"
CP146_MANIFEST = "docs/validation/evidence/checkpoint-146/CP146_REPOSITORY_SHA256SUMS.txt"

ALLOWED_CP145_CHANGES = {
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
    "tools/simulation/starcluster_research/whole_combat_stage_a_response_surface.py",
    "tools/simulation/tests/test_cp132_canonical_kernel.py",
    "tools/simulation/tests/test_cp135_recharge_damcon_rebaseline.py",
    "tools/simulation/tests/test_cp136_armor_rebaseline.py",
    "tools/simulation/tests/test_cp137_finite_armor_regeneration.py",
    "tools/simulation/tests/test_cp141_combat_duration_stalemate.py",
    "tools/simulation/tests/test_cp144_whole_combat_stage_a_response_surface.py",
}

CP146_ADDITIONS = {
    "docs/archive/testing/pre-cp165-active/cp146_combat_resource_doctrine_parity_fixtures_v0_1.json",
    "docs/archive/testing/pre-cp165-active/cp146_combat_resource_doctrine_study_v0_1.json",
    "docs/validation/Checkpoint_146_Combat_Resource_Doctrine_And_Contextual_System_Activation.md",
    "docs/validation/evidence/checkpoint-146/accepted-cp145/CP145_ACCEPTED_DIAGNOSTIC_REPLAY_RESULTS.csv",
    "docs/validation/evidence/checkpoint-146/accepted-cp145/CP145_ACCEPTED_DIAGNOSTIC_SUMMARY.json",
    "docs/validation/evidence/checkpoint-146/accepted-cp145/CP145_NATIVE_ACCEPTANCE_SUMMARY.json",
    "src/StarCluster.Core/Combat/Tactics/CombatResourceDoctrineService.cs",
    "tests/StarCluster.Tests/Combat/Tactics/CombatResourceDoctrineServiceTests.cs",
    "tools/simulation/starcluster_research/combat_resource_doctrine.py",
    "tools/simulation/starcluster_research/combat_resource_doctrine_validation.py",
    "tools/simulation/tests/test_cp146_combat_resource_doctrine.py",
    "tools/checkpoints/checkpoint-146/apply_checkpoint_146.ps1",
    "tools/checkpoints/checkpoint-146/checkpoint_146_definition.json",
    "tools/checkpoints/checkpoint-146/preflight_checkpoint_146.py",
    "tools/checkpoints/checkpoint-146/test_checkpoint_146_contract.py",
}

NEW_CS = {
    "src/StarCluster.Core/Combat/Tactics/CombatResourceDoctrineService.cs",
    "tests/StarCluster.Tests/Combat/Tactics/CombatResourceDoctrineServiceTests.cs",
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
        if rel == CP146_MANIFEST:
            continue
        out.add(rel)
    return out


def count_suite(suite) -> int:
    return sum(count_suite(x) if isinstance(x, unittest.TestSuite) else 1 for x in suite)


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); args = ap.parse_args(); repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-146/checkpoint_146_definition.json")
        req(definition["checkpoint"] == 146 and definition["baseCheckpoint"] == 145, "checkpoint identity")
        req(definition["expectedPythonTests"] == 328 and definition["expectedPythonTestModules"] == 37, "Python test contract")
        req(definition["expectedXunitTests"] == 926 and definition["expectedScenarioRunnerSelfTests"] == 70, "native regression contract")
        req(definition["expectedFocusedCp146Tests"] == 18 and definition["expectedCp146DoctrineFixtureCases"] == 9, "CP146 focused/fixture contract")
        req(definition["expectedDoctrineScenariosPerVersion"] == 252 and definition["expectedCombatTrialsPerDoctrine"] == 6300 and definition["expectedTotalDoctrineCombatTrials"] == 12600, "doctrine study scope")
        req(definition["tuningAllowed"] is False and definition["automaticPromotion"] is False and definition["stageBAutomatic"] is False, "promotion boundary")

        req(sha(repo / "docs/design/player_technology/technology_numerical_matrix_v0_9.json") == MATRIX_SHA, "Technology Numerical Matrix drift")
        req(sha(repo / "docs/archive/concepts/Star_Cluster_Game_Concept_v0.7x.docx") == CONCEPT_SHA, "Concept v0.7x drift")
        cp145_path = repo / CP145_MANIFEST
        req(cp145_path.is_file() and sha(cp145_path) == CP145_MANIFEST_SHA, "accepted CP145 repository manifest drift")
        cp145 = read_manifest(cp145_path)

        frozen = 0
        for rel, expected in cp145.items():
            req((repo / rel).is_file(), f"missing CP145-owned file: {rel}")
            if rel in ALLOWED_CP145_CHANGES:
                continue
            req(sha(repo / rel) == expected, f"unexpected CP145 baseline drift: {rel}")
            frozen += 1

        # Existing CP145 C# stays byte-frozen; only the declared CP146 service/test may be added.
        cp145_cs = {rel for rel in cp145 if rel.endswith(".cs")}
        current_cs = {p.relative_to(repo).as_posix() for p in repo.rglob("*.cs") if "/bin/" not in ("/" + p.relative_to(repo).as_posix()) and "/obj/" not in ("/" + p.relative_to(repo).as_posix())}
        req(current_cs == cp145_cs | NEW_CS, f"C# path-set drift added={sorted(current_cs-(cp145_cs|NEW_CS))[:5]} missing={sorted((cp145_cs|NEW_CS)-current_cs)[:5]}")
        for rel in cp145_cs:
            req(sha(repo / rel) == cp145[rel], f"CP145 inherited C# drift: {rel}")

        expected_paths = set(cp145) | {CP145_MANIFEST} | CP146_ADDITIONS
        current_paths = owned(repo)
        req(current_paths == expected_paths, f"CP146 repository path drift added={sorted(current_paths-expected_paths)[:8]} missing={sorted(expected_paths-current_paths)[:8]}")

        study = js(repo / "docs/archive/testing/pre-cp165-active/cp146_combat_resource_doctrine_study_v0_1.json")
        req(study["checkpoint"] == 146 and study["baseCheckpoint"] == 145, "study identity")
        req(study["submittedCp145NativeResultsArchiveSha256"] == CP145_SUBMITTED_NATIVE_SHA, "submitted CP145 native provenance drift")
        req(study["masterSeed"] == 140001 and study["expectedTotalCombatTrials"] == 12600, "study seed/trial scope")
        req(study["tuningAllowed"] is False and study["automaticPromotion"] is False and study["stageBAutomatic"] is False, "study promotion boundary")

        accepted_summary = js(repo / study["acceptedCp145NativeSummary"])
        req(accepted_summary["checkpoint"] == 145 and accepted_summary["repositoryOnlyAccepted"] is True, "accepted CP145 native summary identity")
        req(accepted_summary["pythonTestsPassed"] == 310 and accepted_summary["xunitPassed"] == 916 and accepted_summary["diagnosticCombatTrials"] == 6300, "accepted CP145 native regression identity")

        sim = repo / "tools/simulation"; sys.path.insert(0, str(sim))
        from starcluster_research.combat_resource_doctrine import decide_contract_case
        from starcluster_research.combat_resource_doctrine_validation import validate_population, validate_study
        from starcluster_research.canonical_combat import CANONICAL_COMBAT_KERNEL_VERSION
        req(validate_study(study) == [], f"CP146 study validation: {validate_study(study)}")
        req(validate_population(repo, study) == [], f"CP146 population validation: {validate_population(repo, study)}")
        req(CANONICAL_COMBAT_KERNEL_VERSION == "0.6", "CP146 kernel version")
        fixture = js(repo / study["doctrineParityFixtures"])
        req(len(fixture["cases"]) == 9, "shared doctrine fixture case count")
        for case in fixture["cases"]:
            req(decide_contract_case(case) == case["expected"], f"Python doctrine fixture mismatch: {case['id']}")

        kernel = (repo / "tools/simulation/starcluster_research/canonical_combat.py").read_text(encoding="utf-8")
        for marker in ("LEGACY_COMBAT_DOCTRINE", "CONTEXTUAL_COMBAT_DOCTRINE", "held_main_interception", "terminal_magazine_flights", "pds_visible_subflights", "opponent_capability_revealed"):
            req(marker in kernel, f"CP146 kernel marker missing: {marker}")
        service = (repo / "src/StarCluster.Core/Combat/Tactics/CombatResourceDoctrineService.cs").read_text(encoding="utf-8")
        for marker in ("ObservedOffensiveCapability", "LegalMainWeaponShipAttack", "HeldMainWeaponBanks", "OpponentEcmObserved"):
            req(marker in service, f"CP146 C# doctrine marker missing: {marker}")

        suite = unittest.defaultTestLoader.discover(str(repo / "tools/simulation/tests"), pattern="test_*.py")
        total = count_suite(suite); modules = len(list((repo / "tools/simulation/tests").glob("test_*.py")))
        req(total == 328, f"Python discovery expected 328 got {total}")
        req(modules == 37, f"Python test modules expected 37 got {modules}")
        print(f"       CP146 preflight passed: {frozen} inherited CP145-owned files frozen plus {len(cp145_cs)} inherited C# files; exactly 2 declared new C# files; matrix/concept unchanged; 252 x 25 x 2 = 12,600 zero-tuning doctrine trials declared; 328 Python tests in 37 modules discovered.")
        return 0
    except Exception as exc:
        print(f"CP146 preflight failure: {exc}", file=sys.stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
