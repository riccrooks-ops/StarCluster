#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOTS_FROZEN = ("src/", "tests/", "docs/design/player_technology/")
RESEARCH_ROOT = "tools/simulation/starcluster_research/"
TEST_ROOT = "tools/simulation/tests/"


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


def validate_cp130_native(repo: Path):
    root = repo / "docs/validation/evidence/checkpoint-131"
    summary = js(root / "CP130_NATIVE_ACCEPTANCE_SUMMARY.json")
    req(summary["checkpoint"] == 130 and summary["failedGates"] == [], "accepted CP130 native summary")
    req(summary["pythonTestsPassed"] == 183 and summary["xunitPassed"] == 907, "accepted CP130 native test counts")
    req(summary["scenarioRunnerSelfTestsPassed"] == 70 and summary["researchParityPassed"] == 25, "accepted CP130 native runner/parity counts")
    req(summary["substantiveTrials"] == 24099600 and summary["substantiveTrialErrors"] == 0, "accepted CP130 substantive evidence")
    req(summary["pipelineSmokeTrials"] == 240996 and summary["pipelineSmokeTrialErrors"] == 0, "accepted CP130 smoke evidence")
    req(summary["symmetryMismatches"] == 0, "accepted CP130 symmetry evidence")
    prov = js(root / "CP130_NATIVE_RESULTS_ARCHIVE_PROVENANCE.json")
    archive = root / "CP130_NATIVE_RESULTS_ORIGINAL.zip"
    req(prov["sha256"] == "76046a208d25434747ee434094d39e3549ee033b95bde15d3c023fcdad957a17", "accepted CP130 result archive declared hash")
    req(sha(archive) == prov["sha256"] and archive.stat().st_size == int(prov["sizeBytes"]), "accepted CP130 result archive bytes")
    refs = root / "accepted-cp130"
    req(sha(refs / "family_plot_inputs.csv") == prov["familyPlotInputsSha256"], "accepted CP130 family plot evidence hash")
    req(sha(refs / "missile_context_telemetry.csv") == prov["missileContextTelemetrySha256"], "accepted CP130 context evidence hash")


def validate_frozen_cp130(repo: Path) -> int:
    manifest_path = repo / "docs/validation/evidence/checkpoint-130/CP130_REPOSITORY_SHA256SUMS.txt"
    req(sha(manifest_path) == "221fdda44c7db8c4071e915aff2791a7987160afec82bb572bc1e9261349c461", "CP130 repository manifest hash")
    entries = manifest(manifest_path)
    checked = 0
    for rel, digest in entries.items():
        freeze = rel.startswith(ROOTS_FROZEN)
        freeze = freeze or (rel.startswith(RESEARCH_ROOT) and rel != RESEARCH_ROOT + "cli.py")
        freeze = freeze or rel.startswith(TEST_ROOT)
        freeze = freeze or rel in {
            "docs/Star_Cluster_Game_Concept_v0.7s.docx",
            "tools/checkpoints/prepackage_repository_hygiene.py",
            "docs/archive/testing/pre-cp165-active/cp130_missile_main_progression_and_family_viability_study_v0_1.json",
        }
        if not freeze:
            continue
        path = repo / rel
        req(path.is_file(), f"frozen CP130 file missing: {rel}")
        req(sha(path) == digest, f"frozen CP130 file drift: {rel}")
        checked += 1
    req(checked > 690, f"frozen CP130 surface unexpectedly small: {checked}")
    return checked


def validate_stdlib(repo: Path) -> int:
    files = list((repo / "tools/simulation/starcluster_research").glob("*.py")) + list((repo / "tools/checkpoints/checkpoint-131").glob("*.py"))
    allowed = set(sys.stdlib_module_names) | {"starcluster_research"}
    bad: list[str] = []
    for path in files:
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
    return len(files)


def validate_plan(repo: Path):
    sys.path.insert(0, str(repo / "tools/simulation"))
    from starcluster_research.missile_late_maturation_analysis import build_plan
    study = repo / "docs/archive/testing/pre-cp165-active/cp131_late_missile_warhead_maturation_study_v0_1.json"
    plan = build_plan(repo, study, None)["summary"]
    req(plan["failedGates"] == [], "CP131 plan gates")
    req(plan["legalBuilds"] == 9427, "CP131 legal-build count")
    req(plan["candidateCountsByTl"] == {"8": 20, "9": 26}, "CP131 candidate counts")
    req(plan["generatedVariants"] == 476936 and plan["substantiveTrials"] == 47693600, "CP131 workload counts")
    return plan


def validate_reference_rows(repo: Path):
    root = repo / "docs/validation/evidence/checkpoint-131/accepted-cp130"
    with (root / "tl1_7_plus2_baseline.csv").open(newline="", encoding="utf-8") as f:
        plus = list(csv.DictReader(f))
    with (root / "late_anchor_baseline.csv").open(newline="", encoding="utf-8") as f:
        anchors = list(csv.DictReader(f))
    req([int(r["tl"]) for r in plus] == list(range(1, 8)), "CP130 TL1-TL7 +2 reference coverage")
    req(all(r["candidate"] == "damage_plus_2" for r in plus), "CP130 TL1-TL7 +2 reference identity")
    req([(int(r["tl"]), int(r["gp_damage"]), int(r["gp_spen"]), int(r["gp_apen"])) for r in anchors] == [(8,17,3,4),(9,18,4,5)], "CP130 late anchor reference")


def validate_docs(repo: Path):
    for rel in (
        "CHAT_README.md",
        "README.md",
        "docs/Prototype_TODO.md",
        "docs/README.md",
        "docs/validation/README.md",
        "docs/archive/testing/pre-cp165-active/CP131_Late_Missile_Warhead_Maturation_Study_v0_1.md",
        "docs/validation/Checkpoint_131_Late_Missile_Warhead_Maturation.md",
    ):
        body = text(repo / rel)
        req("131" in body or "CP131" in body, f"{rel} not CP131-aware")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    try:
        definition = js(repo / "tools/checkpoints/checkpoint-131/checkpoint_131_definition.json")
        req(definition["checkpoint"] == 131 and definition["expectedPythonTests"] == 190, "checkpoint definition")
        req(definition["technologyValuesChanged"] is False and definition["productionSourceChanged"] is False and definition["scenarioDefinitionsChanged"] is False, "frozen production/value boundary")
        req(definition["jobsConfigurable"] and definition["minimumJobs"] == 1 and definition["maximumJobs"] == 61, "Jobs contract")
        print("       Validating native-accepted CP130 evidence...")
        validate_cp130_native(repo)
        print("       Validating frozen CP130 production/numerical/pre-existing research surfaces...")
        count = validate_frozen_cp130(repo)
        print(f"       Frozen CP130 files verified: {count}.")
        print("       Validating stdlib-only active Python surface...")
        count = validate_stdlib(repo)
        print(f"       Active Python files inspected: {count}; no third-party packages.")
        print("       Reconstructing CP131 late-Missile maturation plan...")
        plan = validate_plan(repo)
        print(f"       CP131 plan: {plan['legalBuilds']} legal builds; {plan['generatedVariants']} variants; {plan['substantiveTrials']} substantive engagements.")
        print("       Validating accepted CP130 +2 and late-anchor reference evidence...")
        validate_reference_rows(repo)
        print("       Validating checkpoint-aware documentation...")
        validate_docs(repo)
        print("       CP131 preflight passed: CP130 accepted; current Tech Table frozen; late Missile candidates research-only; no legal mixed-TL ships.")
        return 0
    except Exception as exc:
        print(f"CP131 preflight failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
