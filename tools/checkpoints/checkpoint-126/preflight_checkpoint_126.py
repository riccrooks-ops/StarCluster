#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

CP125_ZIP_SHA = "e26f4a79075cd3bb395213d9a4da7d9e3708fecd3dbd3b5a29911c24ea63ecf0"
ALLOWED_CS_DELTA = {
    "src/StarCluster.Core/Combat/Tactics/FiniteTacticalMovementResolver.cs",
    "src/StarCluster.Core/Combat/Tactics/FiniteMissileMovementResolver.cs",
    "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs",
    "tests/StarCluster.Tests/Combat/Tactics/SystemMapResearchParityTests.cs",
}
FROZEN_TECH_AUTHORITIES = (
    "docs/archive/player_technology/pre-cp165-active/technology_numerical_matrix_v0_3.json",
    "docs/archive/player_technology/pre-cp165-active/technology_family_storyboard_v1_5.json",
    "docs/archive/player_technology/pre-cp165-active/technology_component_table_v0_5.json",
    "docs/archive/player_technology/pre-cp165-active/technology_idea_register_v1_6.json",
)


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


def validate_cp125(repo: Path) -> None:
    archive = repo / "docs/validation/evidence/checkpoint-126/CP125_NATIVE_RESULTS_ORIGINAL.zip"
    req(archive.is_file() and sha(archive) == CP125_ZIP_SHA, "accepted CP125 archive/hash")
    with zipfile.ZipFile(archive) as z:
        raw = json.loads(z.read("checkpoint-125/CP125_NATIVE_ACCEPTANCE_SUMMARY.json").decode("utf-8-sig"))
    req(raw["checkpoint"] == 125 and raw["pythonTestsPassed"] == 152 and raw["researchParityPassed"] == 25, "CP125 identity")
    req(raw["pipelineSmokeTrials"] == 280136 and raw["substantiveTrials"] == 56027200, "CP125 workload")
    req(raw["failedGates"] == [] and raw["mixedTlShipsExecuted"] is False, "CP125 accepted semantics")
    prov = js(repo / "docs/validation/evidence/checkpoint-126/CP126_ACCEPTED_CP125_NATIVE_SUMMARY.json")
    req(prov["acceptedCheckpoint"] == 125 and prov["sourceArchiveSha256"] == CP125_ZIP_SHA, "CP125 provenance summary")


def validate_source_delta(repo: Path) -> None:
    old = manifest(repo / "docs/validation/evidence/checkpoint-125/CP125_REPOSITORY_SHA256SUMS.txt")
    current_cs = set()
    for prefix in ("src", "tests/StarCluster.Tests"):
        base = repo / prefix
        current_cs.update(p.relative_to(repo).as_posix() for p in base.rglob("*.cs") if "bin" not in p.parts and "obj" not in p.parts)
    old_cs = {rel for rel in old if rel.endswith(".cs") and rel.startswith(("src/", "tests/StarCluster.Tests/"))}
    changed = {rel for rel in current_cs & old_cs if sha(repo / rel) != old[rel]}
    added = current_cs - old_cs
    removed = old_cs - current_cs
    req(removed == set(), f"unexpected removed C# files: {sorted(removed)}")
    req(changed | added == ALLOWED_CS_DELTA, f"unexpected CP126 C# delta: changed={sorted(changed)} added={sorted(added)}")
    for rel in FROZEN_TECH_AUTHORITIES:
        req(rel in old and sha(repo / rel) == old[rel], f"technology authority drift: {rel}")

    movement = text(repo / "src/StarCluster.Core/Combat/Tactics/FiniteTacticalMovementResolver.cs")
    missile = text(repo / "src/StarCluster.Core/Combat/Tactics/FiniteMissileMovementResolver.cs")
    runner = text(repo / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs")
    tests = text(repo / "tests/StarCluster.Tests/Combat/Tactics/SystemMapResearchParityTests.cs")
    for snippet in ("RelativeTie", "tieBreakReference", "AbsoluteCross", "NegativeDot2"):
        req(snippet in movement, f"finite-movement orientation-neutral binding: {snippet}")
    for snippet in ("FiniteMissileMovementResolver", "RelativeTie", "RangeExhausted"):
        req(snippet in missile, f"finite-Missile resolver binding: {snippet}")
    req("FiniteMissileMovementResolver.Resolve" in runner and "encounterBearingA" in runner and "encounterBearingB" in runner, "ScenarioRunner finite geometry integration")
    req("SharedResearchFixtureMatchesProductionGeometryPrimitives" in tests and "FiniteMovementAndMissilePursuitRespectPhysicalMirrorSymmetry" in tests, "native geometry tests")


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        return "".join((e.text or "") for e in root.iter() if e.tag.endswith("}t"))


def validate_docs(repo: Path) -> None:
    active = list((repo / "docs").glob("Star_Cluster_Game_Concept_v0.7*.docx"))
    req([p.name for p in active] == ["Star_Cluster_Game_Concept_v0.7q.docx"], f"active Concept mismatch: {active}")
    req((repo / "docs/archive/concepts/Star_Cluster_Game_Concept_v0.7p.docx").is_file(), "archived v0.7p Concept")
    dt = docx_text(active[0]).lower()
    for phrase in (
        "8.12 finite system map encounter fidelity",
        "91 legal hexes",
        "range 10 apart",
        "adaptive engage",
        "target's current post-movement coordinate",
        "tl2-tl4",
        "tl5-tl7",
        "tl8-tl9",
        "autonomous distributed swarmer",
    ):
        req(phrase.lower() in dt, f"Concept missing: {phrase}")
    with zipfile.ZipFile(active[0]) as z:
        header = "".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.startswith("word/header") and n.endswith(".xml"))
        core = z.read("docProps/core.xml").decode("utf-8", "ignore")
    req("v0.7q" in header and "Star Cluster Game Concept v0.7q" in core and "<cp:version>0.7q</cp:version>" in core, "Concept version metadata")
    for rel in (
        "README.md", "CHAT_README.md", "docs/README.md", "docs/Prototype_TODO.md",
        "docs/design/testing/README.md", "docs/design/player_technology/README.md",
        "docs/archive/testing/pre-cp165-active/CP126_System_Map_Fidelity_And_Era_Boundary_Attribution_Study_v0_1.md",
        "docs/archive/testing/pre-cp165-active/Telemetry_Instrumentation_Contract_v0_2.md",
        "docs/development/Simulation_Development_Guidelines.md",
    ):
        t = text(repo / rel).lower()
        req("126" in t or "cp126" in t, f"active documentation not CP126-aware: {rel}")


def validate_fixture(repo: Path) -> None:
    fixture = js(repo / "docs/archive/testing/pre-cp165-active/system_map_research_parity_fixtures_v0_1.json")
    req(fixture["mapRadius"] == 5 and fixture["expectedCellCount"] == 91, "shared geometry fixture map")
    req(len(fixture.get("searchCases", [])) >= 2 and len(fixture.get("movementCases", [])) >= 4 and len(fixture.get("missileCases", [])) >= 4, "shared geometry fixture coverage")


def validate_plan(repo: Path) -> None:
    sys.path.insert(0, str(repo / "tools/simulation"))
    from starcluster_research.fidelity_attribution_analysis import ALL_TELEMETRY_CONTRACT, build_plan, validate_study
    study_path = repo / "docs/archive/testing/pre-cp165-active/cp126_system_map_fidelity_era_attribution_study_v0_1.json"
    study = js(study_path)
    req(validate_study(study) == [], "CP126 study validation")
    result = build_plan(repo, study_path, None)["summary"]
    req(result["failedGates"] == [], f"CP126 plan gates: {result['failedGates']}")
    req(result["legalBuilds"] == 9427 and result["compactTasks"] == 25678 and result["generatedVariants"] == 139000, "CP126 plan counts")
    req(result["plannedSubstantiveTrials"] == 34750000 and result["telemetryMetrics"] == 61, "CP126 workload/telemetry")
    groups = result["groupCounts"]
    req(groups["late_missile_geometry"]["tasks"] == 1727 and groups["late_missile_geometry"]["variants"] == 6908, "late Missile lane")
    req(len(ALL_TELEMETRY_CONTRACT) == 61, "telemetry contract count")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()
    repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-126/checkpoint_126_definition.json")
        req(definition["checkpoint"] == 126 and definition["expectedXunitTests"] == 907, "definition")
        print("       Validating accepted CP125 provenance and frozen CP123 technology authorities...")
        validate_cp125(repo)
        validate_source_delta(repo)
        print("       Validating full-System-Map study, 61-metric instrumentation, and shared geometry fixture...")
        validate_fixture(repo)
        validate_plan(repo)
        print("       Validating active Concept/documentation and explicit pure-TL/Swarmer-era boundaries...")
        validate_docs(repo)
        print("       CP126 preflight: CP125 control preserved; full radius-5/91-cell research map; orientation-neutral ship/Missile ties; 9,427 pure-TL builds; 25,678 tasks; 139,000 variants; 34,750,000 substantive trials; 61 telemetry metrics; mixed-TL ships excluded.")
        return 0
    except Exception as exc:
        print(f"CP126 preflight failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
