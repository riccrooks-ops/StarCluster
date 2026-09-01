#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except Exception:  # pragma: no cover - native acceptance still validates runner input
    Draft202012Validator = None

CHECKS = 0
FAILURES: list[str] = []


def check(condition: bool, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        FAILURES.append(message)


def load_json(path: Path):
    check(path.is_file(), f"missing JSON: {path}")
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        FAILURES.append(f"invalid JSON {path}: {exc}")
        return {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return re.sub(r"\s+", " ", xml)


def find_matching(text: str, open_index: int, open_char="(", close_char=")") -> int:
    depth = 0
    in_string = False
    verbatim = False
    escape = False
    i = open_index
    while i < len(text):
        ch = text[i]
        if in_string:
            if verbatim:
                if ch == '"':
                    if i + 1 < len(text) and text[i + 1] == '"':
                        i += 1
                    else:
                        in_string = False
                        verbatim = False
            else:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
        else:
            if ch == '"':
                in_string = True
                verbatim = i > 0 and text[i - 1] == '@'
            elif ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    return i
        i += 1
    raise ValueError("unmatched delimiter")


def top_level_argument_count(body: str) -> int:
    if not body.strip():
        return 0
    depths = {"(": 0, "[": 0, "{": 0, "<": 0}
    closes = {")": "(", "]": "[", "}": "{", ">": "<"}
    commas = 0
    in_string = False
    escape = False
    for ch in body:
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch in depths:
            depths[ch] += 1
        elif ch in closes:
            key = closes[ch]
            if depths[key] > 0:
                depths[key] -= 1
        elif ch == "," and all(v == 0 for v in depths.values()):
            commas += 1
    return commas + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", required=True)
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()

    paths = {
        "concept": root / "docs/Star_Cluster_Game_Concept_v0.6d.docx",
        "baseline": root / "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_7.json",
        "schema": root / "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_11.json",
        "study": root / "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc08-bilateral-tactical-geometry-fuel-movement-order.json",
        "policy": root / "docs/design/testing/checkpoint_65_validation_suite_policy_v0_1.json",
        "active": root / "tools/calibration/checkpoints/checkpoint-65.json",
        "deep": root / "tools/calibration/checkpoints/checkpoint-65-deep-calibration.json",
        "runbook": root / "docs/validation/Checkpoint_65_TL1_Bilateral_Tactical_Geometry_Fuel_And_Movement_Order.md",
        "design": root / "docs/design/player_technology/TL1_Bilateral_Tactical_Geometry_Fuel_And_Movement_Order_Study_v0_1.md",
        "runner": root / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs",
        "documents": root / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs",
        "resolver": root / "src/StarCluster.Core/Combat/Tactics/FiniteTacticalMovementResolver.cs",
        "fuel": root / "src/StarCluster.Core/Combat/Tactics/TacticalFuelRules.cs",
        "manifest": root / "CHECKPOINT_65_SHA256SUMS.txt",
    }
    for name, path in paths.items():
        check(path.is_file(), f"missing required {name}: {path.relative_to(root)}")

    check(not (root / "docs/Star_Cluster_Game_Concept_v0.6c.docx").exists(),
          "superseded active Concept v0.6c must not remain beside v0.6d")

    baseline = load_json(paths["baseline"])
    schema = load_json(paths["schema"])
    study = load_json(paths["study"])
    policy = load_json(paths["policy"])
    active = load_json(paths["active"])
    deep = load_json(paths["deep"])

    check(baseline.get("checkpoint") == 65, "baseline checkpoint must be 65")
    bstudy = baseline.get("bilateralTacticalGeometryFuelMovementOrderStudy", {})
    check(bstudy.get("variantCount") == 54, "baseline must specify 54 CP65 variants")
    check(bstudy.get("productionReactorOutput") == 5, "production reactor must remain 5 TP")
    check(bstudy.get("map", {}).get("radius") == 5, "baseline map radius must be 5")
    check(bstudy.get("map", {}).get("diameter") == 11, "baseline map diameter must be 11")
    check(bstudy.get("map", {}).get("cellCount") == 91, "baseline map must contain 91 cells")
    fuel = bstudy.get("fuel", {})
    check(fuel.get("startingFuel") == 200, "baseline starting fuel must be 200")
    check(fuel.get("fuelPerTraversedHex") == 2, "baseline movement fuel must be 2/hex")
    check(fuel.get("evasiveManeuverFlatFuelPerTurn") == 1, "baseline EvM fuel must be flat +1")
    check(bstudy.get("balanceTargetsBlocking") is False, "CP65 balance outcomes must be non-blocking")

    check(study.get("id") == "tl1-itc08-bilateral-tactical-geometry-fuel-movement-order", "study ID mismatch")
    variants = study.get("variants", [])
    check(len(variants) == 54, f"expected 54 variants, found {len(variants)}")
    check(len(study.get("builds", [])) == 1, "CP65 must isolate one balanced build")
    ids = [v.get("id") for v in variants]
    check(len(ids) == len(set(ids)), "variant IDs must be unique")
    groups = Counter(v.get("comparisonGroup") for v in variants)
    check(len(groups) == 27, f"expected 27 paired comparison groups, found {len(groups)}")
    for group, count in groups.items():
        check(count == 2, f"comparison group {group} must contain exactly two movement-order bounds")

    families = {"Kinetic", "Energy", "Missile"}
    regimes = {
        ("OpponentAwareRange", "EstablishedFirm", 0),
        ("TrackAwareOpponentRange", "AcquisitionFirstAutoActive", 0),
        ("TrackAwareOpponentRange", "AcquisitionFirstAutoActive", 1),
    }
    for fa in families:
        for fb in families:
            for movement, track, ew in regimes:
                lane = [v for v in variants if v.get("sideAFamily") == fa and v.get("sideBFamily") == fb and
                        v.get("movementMode") == movement and v.get("sideATrackPolicy") == track and
                        v.get("sideBTrackPolicy") == track and v.get("sideANetEwRangePenalty") == ew and
                        v.get("sideBNetEwRangePenalty") == ew]
                check(len(lane) == 2, f"missing mirrored pair {fa}/{fb}/{movement}/EW{ew}")
                check({v.get("movementOrder") for v in lane} == {"SideAFirst", "SideBFirst"},
                      f"movement-order bounds incomplete for {fa}/{fb}/{movement}/EW{ew}")
                if lane:
                    check(len({v.get("comparisonGroup") for v in lane}) == 1,
                          f"paired seeds drifted for {fa}/{fb}/{movement}/EW{ew}")
                for v in lane:
                    check(v.get("tacticalMapRadius") == 5, f"{v.get('id')} map radius drift")
                    check(v.get("initialRangeHexes") == 4, f"{v.get('id')} initial range drift")
                    check(v.get("startingFuel") == 200 and v.get("movementFuelPerHex") == 2 and v.get("evasiveManeuverFuelCost") == 1,
                          f"{v.get('id')} fuel contract drift")
                    check(v.get("sideAReactorOutputOverride") == 5 and v.get("sideBReactorOutputOverride") == 5,
                          f"{v.get('id')} reactor-output drift")
                    check(v.get("sideATacticalPowerDoctrine") == "FullVolleyFirst" and v.get("sideBTacticalPowerDoctrine") == "FullVolleyFirst",
                          f"{v.get('id')} power-doctrine drift")
                    check(v.get("evasiveManeuversEnabled") is False and v.get("escapeDisengagementEnabled") is False,
                          f"{v.get('id')} EvM/disengagement isolation drift")

    if Draft202012Validator is not None:
        schema_errors = list(Draft202012Validator(schema).iter_errors(study))
        check(not schema_errors, "schema v0.11 validation failed: " + "; ".join(e.message for e in schema_errors[:3]))
    else:
        check(True, "jsonschema module unavailable; native runner remains authoritative")

    props = schema.get("$defs", {}).get("variant", {}).get("properties", {})
    check(set(props.get("movementOrder", {}).get("enum", [])) >= {"SideAFirst", "SideBFirst"}, "schema missing movement-order enum")
    for prop in ("tacticalMapRadius", "startingFuel", "movementFuelPerHex", "evasiveManeuverFuelCost"):
        check(prop in props, f"schema missing {prop}")

    check(active.get("checkpointId") == "65" and deep.get("checkpointId") == "65", "checkpoint ID binding mismatch")
    check(active.get("manifestFile") == "CHECKPOINT_65_SHA256SUMS.txt" and deep.get("manifestFile") == "CHECKPOINT_65_SHA256SUMS.txt", "manifest binding mismatch")
    check(active.get("outputRoot") == "out/checkpoint-65", "normal output root mismatch")
    check(deep.get("outputRoot") == "out/checkpoint-65-deep-calibration", "deep output root mismatch")
    check(active.get("checkpointMetrics", {}).get("stageCount") == 8, "normal stage count mismatch")
    check(active.get("checkpointMetrics", {}).get("monteCarloVariantCount") == 54, "normal MC count mismatch")
    check(active.get("checkpointMetrics", {}).get("trialsAtDefault") == 540000, "normal trial count mismatch")
    check(deep.get("checkpointMetrics", {}).get("stageCount") == 24, "deep stage count mismatch")
    check(deep.get("checkpointMetrics", {}).get("monteCarloVariantCount") == 1404, "deep MC count mismatch")
    check(deep.get("checkpointMetrics", {}).get("trialsAtDefault") == 14040000, "deep trial count mismatch")
    active_ids = [s.get("id") for s in active.get("stages", [])]
    deep_ids = [s.get("id") for s in deep.get("stages", [])]
    check(active_ids[4:5] == ["tl1-bilateral-tactical-geometry"], "current stochastic stage must occupy normal slot 5")
    check(deep_ids[4:6] == ["tl1-bilateral-tactical-geometry", "tl1-track-aware-movement-acquisition"], "deep current/historical stage order mismatch")
    check(policy.get("normal", {}).get("monteCarloVariantCount") == 54, "validation policy normal MC mismatch")
    check(policy.get("deepCalibration", {}).get("monteCarloVariantCount") == 1404, "validation policy deep MC mismatch")

    concept_text = docx_text(paths["concept"])
    for phrase in [
        "Game Concept",
        "Design Draft",
        "Version 0.6d",
        "200 tactical fuel",
        "2 fuel",
        "flat 1 fuel for the turn",
        "final end-of-Movement",
        "closest approach",
        "Movement order never reopens the pre-Movement Tactical Power boundary",
        "radius-5",
        "91 cells",
        "Overload is never an open-ended conversion",
        "TL1 component cannot accept arbitrary extra TP",
    ]:
        check(phrase.lower() in concept_text.lower(), f"Concept v0.6d missing agreed guidance phrase: {phrase}")

    historical_hashes = {
        "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_10.json": "a3dd05cc60bfd6146b150003634eaa4e2b23f2024b7e28ed201668ddc1be7f0a",
        "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_6.json": "251765cc513339d9f66a92cfe86210fd5769738c139bf7e22008e493025f5581",
        "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc07-35-space-track-aware-movement-acquisition.json": "7aa5d9ed17a4584289acc7428331f5942b0d8b44bd7707c8ad649d19d38cbe1c",
    }
    for rel, expected in historical_hashes.items():
        path = root / rel
        check(path.is_file(), f"missing accepted CP64 historical input {rel}")
        if path.is_file():
            check(sha256(path) == expected, f"accepted CP64 historical input changed: {rel}")

    runner = paths["runner"].read_text(encoding="utf-8")
    documents = paths["documents"].read_text(encoding="utf-8")
    resolver = paths["resolver"].read_text(encoding="utf-8")
    fuel_src = paths["fuel"].read_text(encoding="utf-8")
    for token in [
        "Tl1BilateralTacticalGeometryStudyId",
        "FiniteTacticalMovementResolver.Resolve",
        "AdvanceMissilesFiniteMap",
        "tl1-c65-fuel-accounting",
        "tl1-c65-finite-range-bounds",
        "tl1-c65-final-position-combat-geometry",
        "bilateral-geometry-movement-order-paired-review.csv",
    ]:
        check(token in runner, f"runner missing CP65 token {token}")
    for token in ["Tl1IntegratedMovementOrder", "tacticalMapRadius", "movementOrder", "startingFuel", "movementFuelPerHex", "evasiveManeuverFuelCost"]:
        check(token in documents, f"document model missing {token}")
    check("InteriorMargin" in resolver and "map.Cells" in resolver and "BuildShortestPath" in resolver, "finite movement resolver shape mismatch")
    check("new(200, 2, 1)" in fuel_src and "MovementCost" in fuel_src and "AffordableMovementHexes" in fuel_src, "tactical fuel source mismatch")
    check(runner.count("{") == runner.count("}"), "runner brace count mismatch")
    check(runner.count("(") == runner.count(")"), "runner parenthesis count mismatch")

    # Constructor/record shape regression check.
    record_marker = "public sealed record Tl1IntegratedTacticalCombatVariantSummary("
    ri = runner.index(record_marker) + len(record_marker) - 1
    re_ = find_matching(runner, ri)
    record_count = top_level_argument_count(runner[ri + 1:re_])
    ctor_marker = "return new Tl1IntegratedTacticalCombatVariantSummary("
    ci = runner.index(ctor_marker) + len(ctor_marker) - 1
    ce = find_matching(runner, ci)
    ctor_count = top_level_argument_count(runner[ci + 1:ce])
    check(record_count == ctor_count, f"summary record/constructor arity mismatch: {record_count} vs {ctor_count}")

    # variants.csv header/row shape regression check.
    csv_header_marker = '"variant_id", "comparison_group"'
    hp = runner.index(csv_header_marker)
    hs = runner.rfind("new[]", 0, hp)
    hb = runner.index("{", hs)
    he = find_matching(runner, hb, "{", "}")
    csv_header_count = top_level_argument_count(runner[hb + 1:he])
    rs = runner.index("new[]", he)
    rb = runner.index("{", rs)
    re_row = find_matching(runner, rb, "{", "}")
    csv_row_count = top_level_argument_count(runner[rb + 1:re_row])
    check(csv_header_count == csv_row_count,
          f"variants.csv header/row arity mismatch: {csv_header_count} vs {csv_row_count}")

    test_files = [
        root / "tests/StarCluster.Tests/Combat/Tactics/FiniteTacticalMovementResolverTests.cs",
        root / "tests/StarCluster.Tests/Combat/Tactics/TacticalFuelRulesTests.cs",
    ]
    for path in test_files:
        check(path.is_file(), f"missing CP65 unit test {path.relative_to(root)}")

    validation_files = list((root / "docs/validation").glob("Checkpoint_*.md"))
    check(len(validation_files) == 1 and validation_files[0].name == paths["runbook"].name,
          "exactly one CP65 active validation runbook must remain")
    root_txt = list(root.glob("*.txt"))
    check(len(root_txt) == 1 and root_txt[0].name == "CHECKPOINT_65_SHA256SUMS.txt",
          "repository root must contain only current CP65 manifest as .txt")
    archived_txt = list((root / "docs/archive").rglob("*.txt")) if (root / "docs/archive").exists() else []
    check(not archived_txt, "generated checkpoint .txt clutter remains under docs/archive")

    # Full repository manifest verification is part of the static preflight.
    if paths["manifest"].is_file():
        manifest_lines = [line for line in paths["manifest"].read_text(encoding="utf-8").splitlines() if line.strip()]
        listed: set[str] = set()
        for line in manifest_lines:
            parts = line.split("  ", 1)
            check(len(parts) == 2, f"malformed manifest line: {line[:80]}")
            if len(parts) != 2:
                continue
            expected, rel = parts
            listed.add(rel)
            path = root / rel
            check(path.is_file(), f"manifest missing file: {rel}")
            if path.is_file():
                check(sha256(path) == expected, f"manifest hash mismatch: {rel}")
        owned = set()
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel == "CHECKPOINT_65_SHA256SUMS.txt" or rel.startswith("out/") or "/bin/" in f"/{rel}" or "/obj/" in f"/{rel}":
                continue
            owned.add(rel)
        check(owned == listed, f"manifest ownership mismatch: missing={len(owned-listed)} unexpected={len(listed-owned)}")

    if FAILURES:
        print(f"Checkpoint 65 static preflight FAILED: {CHECKS - len(FAILURES)}/{CHECKS} checks passed.")
        for failure in FAILURES:
            print(f"FAILED: {failure}")
        return 1
    print(f"Checkpoint 65 static preflight: {CHECKS}/{CHECKS} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
