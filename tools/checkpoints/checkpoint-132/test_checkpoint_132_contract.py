#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SKIP_MANIFEST = "docs/validation/evidence/checkpoint-132/CP132_REPOSITORY_SHA256SUMS.txt"


def req(value, message: str):
    if not value:
        raise AssertionError(message)


def text(path: Path) -> str:
    req(path.is_file(), f"missing {path}")
    return path.read_text(encoding="utf-8-sig")


def js(path: Path):
    return json.loads(text(path))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
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
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo).as_posix()
        wrapped = "/" + rel
        if rel.startswith(("out/", ".git/")) or "/__pycache__/" in wrapped or rel.endswith(".pyc") or "/bin/" in wrapped or "/obj/" in wrapped or "/TestResults/" in wrapped:
            continue
        if rel == SKIP_MANIFEST:
            continue
        out.append(rel)
    return sorted(out)


def validate_manifest(repo: Path) -> int:
    path = repo / SKIP_MANIFEST
    req(path.is_file(), "CP132 repository manifest missing")
    entries = manifest(path)
    current = owned_files(repo)
    req(set(current) == set(entries), f"manifest path drift missing={sorted(set(entries)-set(current))[:5]} extra={sorted(set(current)-set(entries))[:5]}")
    for rel, digest in entries.items():
        req(sha(repo / rel) == digest, f"manifest hash drift: {rel}")
    return len(entries)


def validate_repository_only(native: Path, definition: dict):
    summary = js(native / "CP132_REPOSITORY_ONLY_ACCEPTANCE.json")
    req(summary["checkpoint"] == 132 and summary["repositoryOnly"] is True and summary["failedGates"] == [], "repository-only identity")
    req(summary["python"].startswith("Python 3.13") and summary["dotnetSdk"] == "8.0.423", "native runtime versions")
    req(summary["pythonTestsPassed"] == definition["expectedPythonTests"], "Python test count")
    req(summary["xunitTotal"] == definition["expectedXunitTests"] and summary["xunitPassed"] == definition["expectedXunitTests"], "xUnit test count")
    req(summary["xunitFailed"] == 0 and summary["xunitSkipped"] == 0, "xUnit failures/skips")
    req(summary["scenarioRunnerSelfTestsPassed"] == definition["expectedScenarioRunnerSelfTests"], "ScenarioRunner self-tests")
    req(summary["deterministicScenarioCorpusPassed"] is True and summary["tl1PhaseACorpusPassed"] is True, "deterministic ScenarioRunner corpora")
    req(summary["researchParityPassed"] == definition["expectedResearchParityCases"], "research parity")
    req(summary["canonicalDamageFixturesPassed"] == definition["expectedCanonicalDamageFixtures"], "canonical fixtures")
    req(summary["visibleTurnPhases"] == definition["expectedVisibleTurnPhases"], "visible phase count")
    req(summary["canonicalKernelVersion"] == definition["canonicalKernelVersion"] and summary["canonicalDamageModel"] == definition["canonicalDamageModel"], "canonical versions")
    req(summary["technologyValuesChanged"] is False and summary["substantiveTrials"] == 0, "numerical/Monte-Carlo boundary")
    req(summary["productionSourceChanged"] is True and summary["researchSimulationChanged"] is True, "implementation boundary")
    req(summary["scenarioDefinitionsChanged"] is True and summary["scenarioDefinitionChangesAreMechanicsSynchronizationOnly"] is True, "scenario mechanics-synchronization boundary")
    return summary


def validate_final(native: Path, definition: dict):
    prior = validate_repository_only(native, definition)
    summary = js(native / "CP132_NATIVE_ACCEPTANCE_SUMMARY.json")
    req(summary["checkpoint"] == 132 and summary["repositoryOnly"] is False and summary["failedGates"] == [], "final identity")
    for key in (
        "python", "dotnetSdk", "pythonTestsPassed", "xunitTotal", "xunitPassed", "scenarioRunnerSelfTestsPassed",
        "deterministicScenarioCorpusPassed", "tl1PhaseACorpusPassed", "researchParityPassed", "canonicalDamageFixturesPassed", "visibleTurnPhases", "canonicalKernelVersion", "canonicalDamageModel",
    ):
        req(summary[key] == prior[key], f"final/prior mismatch: {key}")
    req(summary["substantiveTrials"] == 0 and summary["technologyValuesChanged"] is False, "final zero-study/numerical boundary")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--native-results")
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-132/checkpoint_132_definition.json")
        req(definition["checkpoint"] == 132 and definition["monteCarloStudy"] is False, "definition identity")
        req(definition.get("replacementOrdinal") == 5 and definition.get("replacementLabel") == "Corrected Replacement 5", "corrected-replacement identity")
        req(definition.get("supersedesAuthoredArchiveSha256") == "88ed1b44a3fcfce065fbfaa80a47aaf1ad94f7f8b10ad276c70bc2cc1c1828d0", "original authored provenance")
        req(definition.get("supersedesCorrectedReplacement1ArchiveSha256") == "02e0ebe2e7a913648f5750e95285cf39c9db4d1e0938db1cf8792286cf032ffb", "Corrected Replacement 1 provenance")
        req(definition.get("supersedesCorrectedReplacement2ArchiveSha256") == "7aebf77888190a025d7c317cb5e24e218f015a17c5fec13fbc6e6bcf951e24f8", "Corrected Replacement 2 provenance")
        req(definition.get("supersedesCorrectedReplacement3ArchiveSha256") == "89f76127c83f54095f165a0ff38af0abb78cbaf756d307d259203a93216dbca8", "Corrected Replacement 3 provenance")
        req(definition.get("supersedesCorrectedReplacement4ArchiveSha256") == "55c956ecc49d385f0263e5df513ccffdf2ea9b911eea09cd34cdfaa710a7e88b", "Corrected Replacement 4 provenance")
        req(definition["declaredSubstantiveTrials"] == 0 and definition["technologyValuesChanged"] is False, "definition zero-study/numerical boundary")
        fixture_test = text(repo / "tests/StarCluster.Tests/Combat/Damage/CanonicalCombatKernelFixtureTests.cs")
        req("using StarCluster.Core.Combat;" in fixture_test, "canonical fixture missing StarCluster.Core.Combat using")
        req("using StarCluster.Core.Combat.Damage;" in fixture_test, "canonical fixture missing StarCluster.Core.Combat.Damage using")
        req("if (expectedDamageToArmor == 0)" in fixture_test and "Assert.Empty(result.ArmorLayers);" in fixture_test,
            "canonical C# fixture must handle zero damageToArmor without synthesizing an ArmorLayerDamageResolution")
        kinetic = text(repo / "tests/StarCluster.Tests/Combat/DirectFire/Tl1KineticDuelCalibrationTests.cs")
        req("ArmorProtectionTwoWithoutApenDoesNotDeleteOrdinaryDamage" in kinetic and
            "ArmorProtectionTwoFullyHardensApenTwo" in kinetic,
            "active TL1 Kinetic calibration is not synchronized with penetration-hardening-v1")
        defensive = text(repo / "tests/StarCluster.Tests/Combat/DirectFire/Tl1DefensiveSystemsCalibrationTests.cs")
        req("Shield_hardener_resists_spen_without_deleting_ordinary_damage" in defensive,
            "active Shield Hardener calibration is not synchronized with penetration-hardening-v1")
        a11 = js(repo / "src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA/tl1-a11-weapon-resource-packets.json")
        a11_serialized = json.dumps(a11).lower()
        req('"damageprevented"' not in a11_serialized and '"effectiveprotection"' not in a11_serialized,
            "active TL1 A11 scenario retains pre-CP132 AP damage-reduction assertions")
        for case_id in ("a11-c03", "a11-c04"):
            case = next(c for c in a11["cases"] if c["id"] == case_id)
            resolution = case["expected"]["fire"]["damageResolution"]
            req(resolution.get("damageToArmor") == 1 and resolution.get("hullDamage") == 1 and
                resolution["armorLayers"][0].get("armorBypass") == 1 and
                resolution["armorLayers"][0].get("integrityDamage") == 0,
                f"{case_id} is not synchronized with canonical APEN bypass semantics")
        wrapper = text(repo / "tools/checkpoints/checkpoint-132/apply_checkpoint_132.ps1")
        req("Invoke-Captured 'CP132 xUnit suite'" not in wrapper and "$xunitExitCode=$LASTEXITCODE" in wrapper,
            "xUnit wrapper must complete the TRX before acceptance evaluation")
        if args.native_results:
            native = Path(args.native_results).resolve()
            if (native / "CP132_NATIVE_ACCEPTANCE_SUMMARY.json").is_file():
                validate_final(native, definition)
            else:
                validate_repository_only(native, definition)
        json_count = 0
        for path in repo.rglob("*.json"):
            rel = path.relative_to(repo).as_posix()
            wrapped = "/" + rel
            if rel.startswith("out/") or "/bin/" in wrapped or "/obj/" in wrapped:
                continue
            json.loads(path.read_text(encoding="utf-8-sig"))
            json_count += 1
        count = validate_manifest(repo)
        print(f"       CP132 contract verified: {count} repository-owned files; {json_count} JSON files; canonical kernel 0.1; penetration-hardening-v1; numerical authority frozen; zero substantive trials.")
        return 0
    except Exception as exc:
        print(f"CP132 contract failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
