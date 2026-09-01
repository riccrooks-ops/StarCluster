#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

EXPECTED_PHASES = (
    "Movement",
    "ElectronicWarfare",
    "DirectFire",
    "MissileAndInterception",
    "Damage",
    "DamageControl",
)


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


def docx_text(path: Path) -> str:
    req(path.is_file(), f"missing Concept document {path}")
    parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        for name in ("word/document.xml", "docProps/core.xml"):
            req(name in names, f"Concept missing {name}")
            root = ET.fromstring(archive.read(name))
            parts.extend(node.text or "" for node in root.iter())
        for name in sorted(n for n in names if n.startswith("word/header") and n.endswith(".xml")):
            root = ET.fromstring(archive.read(name))
            parts.extend(node.text or "" for node in root.iter())
    return " ".join(parts)


def validate_definition(repo: Path):
    definition = js(repo / "tools/checkpoints/checkpoint-132/checkpoint_132_definition.json")
    req(definition["checkpoint"] == 132, "checkpoint identity")
    req(definition.get("replacementOrdinal") == 5 and definition.get("replacementLabel") == "Corrected Replacement 5", "CP132 corrected-replacement identity")
    req(definition.get("supersedesCorrectedReplacement1ArchiveSha256") == "02e0ebe2e7a913648f5750e95285cf39c9db4d1e0938db1cf8792286cf032ffb", "CP132 Corrected Replacement 1 provenance")
    req(definition.get("supersedesCorrectedReplacement2ArchiveSha256") == "7aebf77888190a025d7c317cb5e24e218f015a17c5fec13fbc6e6bcf951e24f8", "CP132 Corrected Replacement 3 provenance")
    req(definition.get("supersedesCorrectedReplacement3ArchiveSha256") == "89f76127c83f54095f165a0ff38af0abb78cbaf756d307d259203a93216dbca8", "CP132 Corrected Replacement 3 provenance")
    req(definition.get("supersedesCorrectedReplacement4ArchiveSha256") == "55c956ecc49d385f0263e5df513ccffdf2ea9b911eea09cd34cdfaa710a7e88b", "CP132 Corrected Replacement 4 provenance")
    req(definition.get("supersedesAuthoredArchiveSha256") == "88ed1b44a3fcfce065fbfaa80a47aaf1ad94f7f8b10ad276c70bc2cc1c1828d0", "CP132 corrected-replacement provenance")
    req(definition["acceptedEvidenceCheckpoint"] == 131, "accepted CP131 evidence boundary")
    req(definition["acceptedNumericalCheckpoint"] == 128, "accepted CP128 numerical boundary")
    req(definition["canonicalKernelVersion"] == "0.1", "canonical kernel version")
    req(definition["canonicalDamageModel"] == "penetration-hardening-v1", "damage model")
    req(definition["technologyValuesChanged"] is False, "CP132 must not change technology values")
    req(definition["productionSourceChanged"] is True and definition["researchSimulationChanged"] is True, "CP132 implementation scope")
    req(definition["scenarioDefinitionsChanged"] is True and definition["scenarioDefinitionChangesAreMechanicsSynchronizationOnly"] is True, "scenario mechanics-synchronization boundary")
    req(definition["conceptChanged"] is True and definition["monteCarloStudy"] is False and definition["declaredSubstantiveTrials"] == 0, "Concept/no-Monte-Carlo boundary")
    req(definition["expectedPythonTests"] == 196 and definition["expectedXunitTests"] == 910, "test-count contract")
    req(definition["expectedScenarioRunnerSelfTests"] == 70 and definition["expectedResearchParityCases"] == 25, "runner/parity contract")
    return definition


def validate_cp131_acceptance(repo: Path, definition: dict):
    root = repo / "docs/validation/evidence/checkpoint-132/accepted-cp131"
    summary = js(root / "CP131_NATIVE_ACCEPTANCE_SUMMARY.json")
    req(summary["checkpoint"] == 131 and summary["failedGates"] == [], "accepted CP131 native identity")
    req(summary["pythonTestsPassed"] == 190 and summary["xunitPassed"] == 907, "accepted CP131 tests")
    req(summary["scenarioRunnerSelfTestsPassed"] == 70 and summary["researchParityPassed"] == 25, "accepted CP131 runner/parity")
    req(summary["substantiveTrials"] == 47693600 and summary["substantiveTrialErrors"] == 0, "accepted CP131 substantive evidence")
    provenance = js(root / "CP131_ACCEPTED_BASELINE_PROVENANCE.json")
    req(provenance["fullRepositoryArchiveSha256"] == definition["acceptedCp131RepositoryArchiveSha256"], "CP131 repository archive provenance")
    archive = root / "CP131_NATIVE_RESULTS_ORIGINAL.zip"
    expected = definition["acceptedCp131NativeResultsSha256"]
    req(provenance["nativeResultsArchiveSha256"] == expected and sha(archive) == expected, "CP131 native results archive provenance")


def validate_frozen_numerical(repo: Path, definition: dict):
    checked = 0
    for rel, expected in definition["frozenNumericalFiles"].items():
        path = repo / rel
        req(path.is_file(), f"frozen numerical file missing: {rel}")
        req(sha(path) == expected, f"frozen numerical file drift: {rel}")
        checked += 1
    return checked


def validate_concept(repo: Path):
    active = sorted(repo.glob("docs/Star_Cluster_Game_Concept_v*.docx"))
    req([p.name for p in active] == ["Star_Cluster_Game_Concept_v0.7t.docx"], f"active Concept set drift: {[p.name for p in active]}")
    req((repo / "docs/archive/concepts/Star_Cluster_Game_Concept_v0.7s.docx").is_file(), "v0.7s must be archived")
    content = docx_text(active[0])
    for phrase in (
        "Star Cluster Game Concept v0.7t",
        "Effective SPEN",
        "Shield Armor",
        "Effective APEN",
        "Armor Protection",
        "Armor Integrity",
        "Damage Control",
    ):
        req(phrase.lower() in content.lower(), f"Concept missing CP132 phrase: {phrase}")
    req("penetration" in content.lower() and "hardening" in content.lower(), "Concept must describe penetration hardening")


def validate_fixture_and_python_kernel(repo: Path):
    fixture = js(repo / "docs/archive/testing/pre-cp165-active/canonical_combat_kernel_fixtures_v0_1.json")
    req(fixture["schemaVersion"] == "star-cluster-canonical-combat-kernel-fixtures-v0.1", "fixture schema")
    req(fixture["checkpoint"] == 132 and fixture["kernelVersion"] == "0.1", "fixture identity")
    req(fixture["damageModel"] == "penetration-hardening-v1", "fixture damage model")
    req(tuple(fixture["visibleTurnPhases"]) == EXPECTED_PHASES, "fixture visible phases")
    req(fixture["mapRadius"] == 5 and fixture["expectedCellCount"] == 91 and fixture["standardStartRange"] == 10, "fixture map contract")
    req(fixture["standardStartA"] == [-5, 0] and fixture["standardStartB"] == [5, 0], "fixture standard starts")
    req(fixture["preContactSearchHexesPerActivation"] == 1, "fixture precontact search")
    req(len(fixture["damageCases"]) == 5, "fixture damage-case count")
    zero_armor_cases = [case for case in fixture["damageCases"] if case["expected"]["damageToArmor"] == 0]
    req(len(zero_armor_cases) == 1, "fixture must retain exactly one zero-damage-to-Armor case")
    zero_expected = zero_armor_cases[0]["expected"]
    for field in ("effectiveApen", "armorPenetrationResisted", "armorBypass", "armorIntegrityDamage"):
        req(zero_expected[field] == 0, f"zero-damage-to-Armor fixture must report {field}=0")

    sys.path.insert(0, str(repo / "tools/simulation"))
    from starcluster_research.canonical_mechanics import CANONICAL_DAMAGE_MODEL, resolve_layered_damage
    from starcluster_research.canonical_combat import (
        CANONICAL_COMBAT_KERNEL_VERSION,
        CANONICAL_VISIBLE_PHASES,
        PRECONTACT_SEARCH_HEXES_PER_ACTIVATION,
        STANDARD_START_A,
        STANDARD_START_B,
        STANDARD_START_RANGE,
    )
    req(CANONICAL_DAMAGE_MODEL == "penetration-hardening-v1", "Python damage model constant")
    req(CANONICAL_COMBAT_KERNEL_VERSION == "0.1", "Python kernel version")
    req(tuple(CANONICAL_VISIBLE_PHASES) == EXPECTED_PHASES, "Python visible phases")
    req((STANDARD_START_A.q, STANDARD_START_A.r) == (-5, 0) and (STANDARD_START_B.q, STANDARD_START_B.r) == (5, 0) and STANDARD_START_RANGE == 10, "Python standard starts")
    req(PRECONTACT_SEARCH_HEXES_PER_ACTIVATION == 1, "Python precontact search")

    for case in fixture["damageCases"]:
        initial = case["initial"]
        packet = case["packet"]
        result = resolve_layered_damage(
            damage=packet["damage"],
            spen=packet["spen"],
            apen=packet["apen"],
            shield=initial["shield"],
            shield_armor=initial["shieldArmor"],
            armor_integrity=initial["armorIntegrity"],
            armor_protection=initial["armorProtection"],
            hull=initial["hull"],
        )
        expected = case["expected"]
        actual = {
            "effectiveSpen": result.effective_spen,
            "shieldPenetrationResisted": result.shield_penetration_resisted,
            "shieldBypass": result.shield_bypass,
            "shieldAbsorbed": result.shield_absorbed,
            "damageToArmor": result.damage_to_armor,
            "effectiveApen": result.effective_apen,
            "armorPenetrationResisted": result.armor_penetration_resisted,
            "armorBypass": result.armor_bypass,
            "armorIntegrityDamage": result.armor_absorbed,
            "hullDamage": result.hull_damage,
            "finalShield": result.final_shield,
            "finalArmorIntegrity": result.final_armor_integrity,
            "finalArmorProtection": initial["armorProtection"],
            "finalHull": result.final_hull,
        }
        req(actual == expected, f"Python fixture {case['id']} mismatch: {actual} != {expected}")
    return len(fixture["damageCases"])


def validate_python_routing(repo: Path):
    research = repo / "tools/simulation/starcluster_research"
    facade = text(research / "full_map_ecology.py")
    req("canonical_combat" in facade and "def run_trial_full_map" not in facade, "full_map_ecology must remain compatibility facade")
    for rel in (
        "fidelity_attribution_analysis.py",
        "main_subsystem_stabilization_analysis.py",
        "whole_ladder_sensitivity_analysis.py",
    ):
        body = text(research / rel)
        req("canonical_combat" in body, f"active consumer must route through canonical_combat: {rel}")
        req("from .full_map_ecology" not in body, f"active consumer must not route through legacy facade: {rel}")
    for rel in ("ecology.py", "combat.py", "baseline_foundation.py"):
        req("canonical_mechanics" in text(research / rel), f"damage consumer must route through canonical_mechanics: {rel}")


def validate_csharp_contract(repo: Path):
    resolver = text(repo / "src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs")
    for phrase in (
        "packet.ShieldPenetration - defense.ShieldArmor",
        "packet.ArmorPenetration - armorHardening",
        "Math.Min(\n                incomingToLayer,\n                effectiveArmorPenetration)",
        "layer.CurrentIntegrity <= 0",
    ):
        req(phrase in resolver, f"C# resolver missing canonical expression: {phrase}")
    req("ApplyProtectionDamage" not in resolver, "C# resolver must not strip AP")
    armor_state = text(repo / "src/StarCluster.Core/Combat/Damage/ArmorLayerState.cs")
    req("ApplyProtectionDamage" not in armor_state, "ArmorLayerState must not expose destructible AP")

    phase_enum = text(repo / "src/StarCluster.Core/Combat/TacticalTurnPhase.cs")
    phase_state = text(repo / "src/StarCluster.Core/Combat/TacticalTurnState.cs")
    for phase in EXPECTED_PHASES:
        req(phase in phase_enum, f"C# phase enum missing {phase}")
    req("Phase = TacticalTurnPhase.ElectronicWarfare" in phase_state, "C# state must advance Movement to EW")
    main = text(repo / "src/StarCluster.Game/Scripts/Main.cs")
    req("TacticalTurnPhase.Movement => TacticalTurnPhase.ElectronicWarfare" in main, "game phase transition to EW")
    req("case TacticalTurnPhase.ElectronicWarfare:" in main, "game EW phase handler")

    fixture_test = text(repo / "tests/StarCluster.Tests/Combat/Damage/CanonicalCombatKernelFixtureTests.cs")
    req("using StarCluster.Core.Combat;" in fixture_test, "canonical C# fixture test must import StarCluster.Core.Combat for TacticalTurnState/TacticalTurnPhase")
    req("using StarCluster.Core.Combat.Damage;" in fixture_test, "canonical C# fixture test must import StarCluster.Core.Combat.Damage for layered-damage types")
    req("if (expectedDamageToArmor == 0)" in fixture_test, "canonical C# fixture test must branch when no damage reaches Armor")
    req("Assert.Empty(result.ArmorLayers);" in fixture_test, "canonical C# fixture test must accept no armor diagnostic when damageToArmor is zero")
    req("ArmorLayerDamageResolution armor = Assert.Single(result.ArmorLayers);" in fixture_test, "canonical C# fixture test must still require one armor diagnostic when damage reaches the single fixture layer")
    combat_sources = {
        "src/StarCluster.Core/Combat/TacticalTurnState.cs": ("namespace StarCluster.Core.Combat;", "public sealed class TacticalTurnState"),
        "src/StarCluster.Core/Combat/TacticalTurnPhase.cs": ("namespace StarCluster.Core.Combat;", "public enum TacticalTurnPhase"),
        "src/StarCluster.Core/Combat/Damage/LayeredDefenseState.cs": ("namespace StarCluster.Core.Combat.Damage;", "public sealed class LayeredDefenseState"),
        "src/StarCluster.Core/Combat/Damage/ArmorLayerState.cs": ("namespace StarCluster.Core.Combat.Damage;", "public sealed class ArmorLayerState"),
        "src/StarCluster.Core/Combat/Damage/LayeredDamageResolver.cs": ("namespace StarCluster.Core.Combat.Damage;", "public static class LayeredDamageResolver"),
        "src/StarCluster.Core/Combat/Damage/AttackPacket.cs": ("namespace StarCluster.Core.Combat.Damage;", "public sealed record AttackPacket"),
        "src/StarCluster.Core/Combat/Damage/LayeredDamageResolution.cs": ("namespace StarCluster.Core.Combat.Damage;", "public sealed record LayeredDamageResolution"),
    }
    for rel, phrases in combat_sources.items():
        source = text(repo / rel)
        for phrase in phrases:
            req(phrase in source, f"canonical C# fixture dependency drift: {rel} missing {phrase}")
    for symbol in (
        "LayeredDefenseState", "ArmorLayerState", "LayeredDamageResolution", "LayeredDamageResolver",
        "AttackPacket", "ArmorLayerDamageResolution", "TacticalTurnState", "TacticalTurnPhase",
    ):
        req(symbol in fixture_test, f"canonical C# fixture no longer exercises expected symbol: {symbol}")


def validate_scenario_phase_plumbing(repo: Path):
    phase_index = {name: idx for idx, name in enumerate(EXPECTED_PHASES)}
    for name in ("command-guided-live-datalink.json", "search-fuel-exhaustion.json", "seeker-search-then-hit.json"):
        data = js(repo / "src/StarCluster.ScenarioRunner/Scenarios" / name)
        phase = data.get("initialPhase", "Movement")
        for action in data.get("actions", []):
            kind = action.get("type")
            if kind == "advancePhase":
                idx = phase_index[phase]
                phase = EXPECTED_PHASES[(idx + 1) % len(EXPECTED_PHASES)]
            elif kind == "advanceMissile":
                req(phase == "MissileAndInterception", f"{name}: advanceMissile reached in {phase}")
    generated = text(repo / "src/StarCluster.ScenarioRunner/FullFlightCalibrationModel.cs")
    marker = 'actions.Add(new ActionDocument { Type = "advancePhase" });'
    req(generated.count(marker) >= 6, "full-flight action builder must include six-phase traversal")


def validate_active_damage_scenarios(repo: Path):
    root = repo / "src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseA"
    a01 = js(root / "tl1-a01-shield-bypass-capacity.json")
    a02 = js(root / "tl1-a02-armor-ai-ap-sequence.json")
    serialized = json.dumps({"a01": a01, "a02": a02}).lower()
    req("shield armor hardens spen" in serialized, "TL1 A01 must exercise SA penetration hardening")
    req("armor protection is hardening only" in serialized, "TL1 A02 must exercise AP as hardening")
    req("damage after armor integrity depletes armor protection" not in serialized, "active TL1 damage corpus retains destructible-AP language")
    for case in a02["cases"]:
        for layer in case["expected"].get("defense", {}).get("armorLayers", []):
            req(layer.get("currentProtection", 1) != 0, "active TL1 damage corpus must not expect AP destruction")
    c04 = next(c for c in a02["cases"] if c["id"] == "a02-c04")
    req(c04["input"]["packet"]["armorPenetration"] == 3, "TL1 A02 APEN hardening probe")
    req(c04["expected"]["resolution"]["armorLayers"][0]["effectiveArmorPenetration"] == 1, "TL1 A02 effective APEN expectation")

    a11 = js(root / "tl1-a11-weapon-resource-packets.json")
    a11_serialized = json.dumps(a11).lower()
    req('"damageprevented"' not in a11_serialized and '"effectiveprotection"' not in a11_serialized,
        "TL1 A11 retains pre-CP132 AP-as-damage-reduction assertions")
    for case_id, apen_key in (("a11-c03", "energy_apen"), ("a11-c04", "missile_warhead_apen")):
        case = next(c for c in a11["cases"] if c["id"] == case_id)
        resolution = case["expected"]["fire"]["damageResolution"]
        req(resolution.get("damageToArmor") == 1 and resolution.get("hullDamage") == 1,
            f"{case_id} must expect one APEN-enabled Hull damage under penetration-hardening-v1")
        armor = resolution["armorLayers"][0]
        req(armor.get("effectiveArmorPenetration") == {"$baseline": apen_key} and armor.get("armorBypass") == 1,
            f"{case_id} must assert canonical APEN bypass rather than AP damage reduction")
        req(armor.get("integrityDamage") == 0 and armor.get("armorFacingDamage") == 0,
            f"{case_id} APEN bypass must not also damage Armor Integrity")
        hull_expectation = case["expected"]["defense"]["currentHull"]
        req(hull_expectation == {"$subtract": [{"$input": "$.defense.currentHull"}, {"$actual": "$.fire.damageResolution.hullDamage"}]},
            f"{case_id} final Hull expectation must follow canonical hullDamage")



def validate_active_csharp_damage_tests(repo: Path):
    kinetic = text(repo / "tests/StarCluster.Tests/Combat/DirectFire/Tl1KineticDuelCalibrationTests.cs")
    req("ArmorProtectionTwoWithoutApenDoesNotDeleteOrdinaryDamage" in kinetic,
        "TL1 Kinetic calibration must assert AP does not delete ordinary damage")
    req("ArmorProtectionTwoFullyHardensApenTwo" in kinetic,
        "TL1 Kinetic calibration must assert AP hardens APEN")
    req("ArmorProtectionTwoWithoutApenSlowsDamageFourToTurnEleven" not in kinetic,
        "TL1 Kinetic calibration retains pre-CP132 AP damage-reduction assertion")
    req("ApenTwoReducesArmorProtectionTwoDuelFromElevenToSevenTurns" not in kinetic,
        "TL1 Kinetic calibration retains pre-CP132 APEN/AP suppression assertion")
    req(kinetic.count("Assert.Equal(6, result.Turns);") >= 2,
        "TL1 Kinetic AP/APEN current-contract probes must retain the six-turn baseline")
    req(kinetic.count("CurrentProtection);") >= 4,
        "TL1 Kinetic AP/APEN probes must verify AP remains persistent")

    defensive = text(repo / "tests/StarCluster.Tests/Combat/DirectFire/Tl1DefensiveSystemsCalibrationTests.cs")
    req("Shield_hardener_resists_spen_without_deleting_ordinary_damage" in defensive,
        "Shield Hardener calibration must test SA as SPEN hardening")
    req("Shield_hardener_adds_one_shield_armor_while_powered" not in defensive,
        "Shield Hardener calibration retains ambiguous pre-CP132 damage-reduction fixture")
    for phrase in (
        "shieldCapacity: 4",
        "Assert.Equal(0, hardened.SideA.Defense.CurrentShieldCapacity);",
        "Assert.Equal(1, control.SideA.Defense.CurrentShieldCapacity);",
        "Assert.Equal(4, hardened.SideA.Defense.ArmorLayers.Single().CurrentIntegrity);",
        "Assert.Equal(3, control.SideA.Defense.ArmorLayers.Single().CurrentIntegrity);",
    ):
        req(phrase in defensive, f"Shield Hardener current-contract probe missing: {phrase}")

def validate_python_test_discovery(repo: Path, definition: dict):
    start = repo / "tools/simulation/tests"
    old_path = list(sys.path)
    try:
        all_suite = unittest.defaultTestLoader.discover(str(start), pattern="test_*.py")
        req(all_suite.countTestCases() == definition["expectedPythonTests"], f"Python self-test discovery count mismatch: expected {definition['expectedPythonTests']}, observed {all_suite.countTestCases()}")
        canonical_suite = unittest.defaultTestLoader.discover(str(start), pattern="test_cp132_canonical_kernel.py")
        req(canonical_suite.countTestCases() == 6, f"canonical-kernel discovery count mismatch: expected 6, observed {canonical_suite.countTestCases()}")
    finally:
        sys.path[:] = old_path


def validate_wrapper_command(repo: Path):
    wrapper = text(repo / "tools/checkpoints/checkpoint-132/apply_checkpoint_132.ps1")
    all_required = "'-B','-m','unittest','discover','-s','tools/simulation/tests','-p','test_*.py'"
    canonical_required = "'-B','-m','unittest','discover','-v','-s','tools/simulation/tests','-p','test_cp132_canonical_kernel.py'"
    req(all_required in wrapper, "CP132 wrapper must run the full Python unittest suite through direct discovery")
    req(canonical_required in wrapper, "CP132 wrapper must run canonical tests through direct unittest discovery so starcluster_research imports resolve")
    req("Invoke-Captured 'CP132 Python self-tests'" not in wrapper, "CP132 wrapper must not capture unittest stderr through PowerShell error records")
    req("Invoke-Captured 'CP132 canonical-kernel tests'" not in wrapper, "CP132 wrapper must not capture canonical unittest stderr through PowerShell error records")
    req("tools.simulation.tests.test_cp132_canonical_kernel" not in wrapper, "CP132 wrapper retains broken dotted canonical-test invocation")
    req("Invoke-Captured 'CP132 xUnit suite'" not in wrapper, "CP132 wrapper must let dotnet test complete its TRX before evaluating failures")
    req("$xunitExitCode=$LASTEXITCODE" in wrapper, "CP132 wrapper must preserve the completed xUnit process exit code")
    req("See $trxPath for the complete result set." in wrapper, "CP132 wrapper must point failed acceptance to the complete xUnit TRX")


def validate_docs(repo: Path):
    required = {
        "CHAT_README.md": ("Checkpoint 132", "canonical"),
        "README.md": ("Checkpoint 132", "canonical"),
        "docs/README.md": ("Checkpoint 132", "v0.7t"),
        "docs/development/Canonical_Combat_Simulation_Kernel.md": ("penetration-hardening-v1", "Electronic Warfare"),
        "docs/development/Simulation_Development_Guidelines.md": ("Canonical combat-kernel requirement", "explicit"),
        "docs/validation/Checkpoint_132_Canonical_Combat_Kernel_And_Defense_Semantics.md": ("native Windows acceptance required", "stale xUnit", "zero"),
    }
    for rel, phrases in required.items():
        body = text(repo / rel)
        for phrase in phrases:
            req(phrase.lower() in body.lower(), f"{rel} missing '{phrase}'")


def validate_stdlib(repo: Path) -> int:
    paths = list((repo / "tools/simulation/starcluster_research").glob("*.py"))
    paths += list((repo / "tools/checkpoints/checkpoint-132").glob("*.py"))
    allowed = set(sys.stdlib_module_names) | {"starcluster_research"}
    bad: list[str] = []
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [item.name.split(".")[0] for item in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                if name not in allowed:
                    bad.append(f"{path.relative_to(repo)}:{name}")
    req(not bad, "third-party Python import(s): " + ", ".join(bad[:8]))
    return len(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        definition = validate_definition(repo)
        print("       Validating accepted CP131 native baseline and provenance...")
        validate_cp131_acceptance(repo, definition)
        print("       Verifying CP128/current numerical authority bytes remain frozen...")
        frozen = validate_frozen_numerical(repo, definition)
        print(f"       Frozen numerical artifacts verified: {frozen}.")
        print("       Validating active Concept v0.7t defense semantics...")
        validate_concept(repo)
        print("       Validating shared canonical fixture and Python mechanics/kernel...")
        cases = validate_fixture_and_python_kernel(repo)
        print(f"       Canonical damage fixtures verified: {cases}.")
        print("       Validating research-consumer routing through canonical modules...")
        validate_python_routing(repo)
        print("       Validating production C# damage/phase contract statically...")
        validate_csharp_contract(repo)
        print("       Validating six-phase ScenarioRunner plumbing...")
        validate_scenario_phase_plumbing(repo)
        print("       Validating active TL1 damage scenarios and C# calibration assertions against the canonical model...")
        validate_active_damage_scenarios(repo)
        validate_active_csharp_damage_tests(repo)
        print("       Validating Python unittest discovery counts and native-wrapper invocation shape...")
        validate_python_test_discovery(repo, definition)
        validate_wrapper_command(repo)
        print("       Validating checkpoint-aware documentation...")
        validate_docs(repo)
        inspected = validate_stdlib(repo)
        print(f"       Active Python files inspected: {inspected}; stdlib-only policy intact.")
        print("       CP132 preflight passed: CP131 accepted; numerical values frozen; canonical kernel/defense contract coherent; no Monte Carlo study declared.")
        return 0
    except Exception as exc:
        print(f"CP132 preflight failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
