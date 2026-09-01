#!/usr/bin/env python3
"""Checkpoint 31 environment-independent release contract validator.

This preflight intentionally avoids .NET and Godot. It verifies the complete
repository manifest, active-document normalization, exact data/study/test
cardinalities, documentation markers, OOXML workbook/DOCX content, and basic
source-structure contracts before a Windows compiler/runtime acceptance run.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

BASELINE_SHA = "624c46e991022b187fb01804d6e094389fcce5996d2b91589277d0bde94c55f5"
EXPECTED_MANIFEST_COUNT = 640
ALLOWED_TOP_LEVEL = (
    re.compile(r"^StarCluster_Checkpoint_.*\.zip(?:\.sha256\.txt)?$", re.I),
)


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_text(path: Path) -> str:
    require(path.is_file(), f"Required file is missing: {path}")
    return path.read_text(encoding="utf-8-sig")


def allowed_unmanifested(relative: str) -> bool:
    p = relative.replace("\\", "/")
    if p.startswith((".git/", ".vs/", ".vscode/", ".idea/", "out/", "src/StarCluster.Game/.godot/")):
        return True
    if re.search(r"(^|/)(bin|obj|TestResults)/", p):
        return True
    if re.search(r"\.(user|userosscache|sln\.docstates|uid)$", p, re.I):
        return True
    if re.search(r"(^|/)(\.suo|\.DS_Store|Thumbs\.db)$", p, re.I):
        return True
    if "/" not in p:
        if re.match(r"^Checkpoint_.*Readme\.txt$", p, re.I):
            return p == "Checkpoint_31_Readme.txt"
        if re.match(r"^CHECKPOINT_.*SHA256SUMS\.txt$", p, re.I):
            return p == "CHECKPOINT_31_SHA256SUMS.txt"
        return any(rx.match(p) for rx in ALLOWED_TOP_LEVEL)
    return False


def parse_manifest(root: Path) -> dict[str, str]:
    manifest_path = root / "CHECKPOINT_31_SHA256SUMS.txt"
    require(manifest_path.is_file(), "CHECKPOINT_31_SHA256SUMS.txt is missing")
    entries: dict[str, str] = {}
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.startswith("#"):
            continue
        m = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", raw)
        require(m is not None, f"Malformed manifest line: {raw}")
        digest, rel = m.group(1).lower(), m.group(2).replace("\\", "/")
        require(rel != "CHECKPOINT_31_SHA256SUMS.txt", "Manifest must not contain itself")
        require(not rel.startswith("/") and ".." not in Path(rel).parts, f"Unsafe manifest path: {rel}")
        require(rel not in entries, f"Duplicate manifest path: {rel}")
        entries[rel] = digest
    require(len(entries) == EXPECTED_MANIFEST_COUNT,
            f"Manifest count is {len(entries)}, expected {EXPECTED_MANIFEST_COUNT}")
    for rel, expected in entries.items():
        path = root / rel
        require(path.is_file(), f"Manifest file missing: {rel}")
        actual = sha256(path)
        require(actual == expected, f"Manifest hash mismatch for {rel}: {actual} != {expected}")
    unexpected = []
    manifest_abs = manifest_path.resolve()
    for path in root.rglob("*"):
        if not path.is_file() or path.resolve() == manifest_abs:
            continue
        rel = path.relative_to(root).as_posix()
        if rel in entries or allowed_unmanifested(rel):
            continue
        unexpected.append(rel)
    require(not unexpected, "Unexpected repository-owned files:\n" + "\n".join(sorted(unexpected)))
    return entries


def active_document_contract(root: Path) -> None:
    concepts = sorted((root / "docs").glob("Star_Cluster_Game_Concept_v*.docx"))
    require([p.name for p in concepts] == ["Star_Cluster_Game_Concept_v0.4c.docx"],
            f"Active Concept set is invalid: {[p.name for p in concepts]}")
    runbooks = sorted((root / "docs/validation").glob("Checkpoint_*.md"))
    require([p.name for p in runbooks] == ["Checkpoint_31_TL1_Layered_Defensive_Systems_Calibration.md"],
            f"Active validation runbook set is invalid: {[p.name for p in runbooks]}")
    require((root / "docs/archive/Star_Cluster_Game_Concept_v0.4b.docx").is_file(),
            "Archived Concept v0.4b is missing")
    require((root / "docs/validation/archive/Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md").is_file(),
            "Archived Checkpoint 30 validation runbook is missing")


def baseline_contract(root: Path) -> None:
    path = root / "docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_1.csv"
    require(sha256(path) == BASELINE_SHA, "TL1 baseline hash mismatch")
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    require(len(rows) == 127, f"Expected 127 baseline rows; found {len(rows)}")
    require(len({r["parameter_id"] for r in rows}) == 127, "Baseline parameter IDs are not unique")
    values = {r["parameter_id"]: r["value"] for r in rows}
    expected = {
        "reactor_output": "5",
        "shield_capacity": "2",
        "kinetic_ammo": "100",
        "missile_ammo": "25",
        "kinetic_pds_ammo": "50",
        "amm_pds_ammo": "25",
        "ammunition_ready_package": "1",
    }
    for key, value in expected.items():
        require(values.get(key) == value, f"Baseline {key} is {values.get(key)!r}, expected {value!r}")

    for path in (root / "src/StarCluster.ScenarioRunner/Scenarios").rglob("*.json"):
        try:
            doc = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            raise ContractError(f"Invalid JSON {path}: {exc}") from exc
        if "baselineSha256" in doc:
            require(doc["baselineSha256"].lower() == BASELINE_SHA,
                    f"Scenario baseline hash mismatch: {path.relative_to(root)}")


def reciprocal_contract(variants: list[dict], label: str) -> dict[str, dict]:
    by_id = {str(v.get("id", "")): v for v in variants}
    require(len(by_id) == len(variants) and "" not in by_id, f"{label} IDs are empty or duplicated")
    shared_fields = (
        "category", "shieldCapacity", "shieldArmor", "baseShieldRecharge",
        "armorProtection", "armorIntegrity", "hull", "rangeHexes",
        "rangePenaltyPerHex", "turnCap",
    )
    for v in variants:
        pair = v.get("pairId")
        asymmetric = v.get("sideA") != v.get("sideB")
        require(not asymmetric or pair not in (None, ""),
                f"Asymmetric {label} {v['id']} lacks a reciprocal side swap")
        if pair in (None, ""):
            continue
        require(pair in by_id, f"{label} {v['id']} references missing pair {pair}")
        partner = by_id[pair]
        require(partner.get("pairId") == v["id"],
                f"{label} pair {v['id']}/{pair} is not reciprocal")
        require(v.get("sideA") == partner.get("sideB") and
                v.get("sideB") == partner.get("sideA"),
                f"{label} pair {v['id']}/{pair} is not an exact side swap")
        for field in shared_fields:
            require(v.get(field) == partner.get(field),
                    f"{label} pair {v['id']}/{pair} differs in shared field {field}")
    return by_id


def pds_contract(root: Path) -> None:
    path = root / "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-pds01-interception-study.json"
    study = json.loads(read_text(path))
    schema = json.loads(read_text(root / "docs/design/player_technology/tl1_pds_calibration_schema_v0_1.json"))
    require(study["schemaVersion"] == "star-cluster-tl1-pds-calibration-v1", "PDS schemaVersion mismatch")
    require(schema["$id"] == "star-cluster-tl1-pds-calibration-v1", "PDS schema ID mismatch")
    require(schema["properties"]["variants"]["minItems"] == 59 and schema["properties"]["variants"]["maxItems"] == 59,
            "PDS schema must require 59 variants")
    require(study["baselineSha256"] == BASELINE_SHA and study["trialsPerVariant"] == 10000,
            "PDS baseline/trial contract mismatch")
    variants = study["variants"]
    require(len(variants) == 59, f"Expected 59 PDS variants; found {len(variants)}")
    by_id = reciprocal_contract(variants, "PDS variant")
    profiles = {
        "pds-kpds-v-m-r2": ("kinetic", 1, 1, 35, 50, False),
        "pds-ammpds-v-m-r2": ("amm", 1, 1, 50, 25, False),
        "pds-epds-v-m-r2": ("energy", 2, 1, 40, 0, True),
    }
    for ident, expected in profiles.items():
        side = by_id[ident]["sideA"]
        actual = (side["pdsFamily"], side["pdsPowerCost"], side["pdsReactionCapacity"],
                  side["pdsInterceptionChance"], side["pdsAmmunition"], side["pdsUnlimitedAmmunition"])
        require(actual == expected, f"Canonical PDS profile mismatch for {ident}: {actual}")
        require(side["computerBonus"] == 10, f"Operational Targeting Computer assistance missing from {ident}")
        require(by_id[ident]["sideB"]["ammunition"] == 25, f"Main missile total is not 25 in {ident}")
    require(by_id["pds-kpds-ammo2-r2"]["sideA"]["pdsAmmunition"] == 2, "PDS ammo2 sensitivity is missing")
    require(by_id["pds-kpds-reaction2-r2"]["sideA"]["pdsReactionCapacity"] == 2, "PDS RC2 sensitivity is missing")


def defensive_contract(root: Path) -> None:
    path = root / "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-ds01-layered-defensive-systems-study.json"
    study = json.loads(read_text(path))
    schema = json.loads(read_text(root / "docs/design/player_technology/tl1_defensive_calibration_schema_v0_1.json"))
    require(study["schemaVersion"] == "star-cluster-tl1-defensive-calibration-v1", "Defensive schemaVersion mismatch")
    require(schema["$id"] == "star-cluster-tl1-defensive-calibration-v1", "Defensive schema ID mismatch")
    require(schema["properties"]["variants"]["minItems"] == 171 and schema["properties"]["variants"]["maxItems"] == 171,
            "Defensive schema must require 171 variants")
    require(study["baselineSha256"] == BASELINE_SHA and study["trialsPerVariant"] == 10000,
            "Defensive baseline/trial contract mismatch")
    variants = study["variants"]
    require(len(variants) == 171, f"Expected 171 defensive variants; found {len(variants)}")
    by_id = reciprocal_contract(variants, "Defensive variant")
    expected_counts = {
        "accepted-control": 6,
        "pds-rule-correction": 36,
        "sensor-ew-boundary": 57,
        "shield-defense": 36,
        "layered-defense": 36,
    }
    require(Counter(v["category"] for v in variants) == Counter(expected_counts),
            f"Defensive category counts drifted: {Counter(v['category'] for v in variants)}")
    for ident in (
        "ds-pds-amm-tc10-evm-r2",
        "ds-pds-kinetic-tc0-steady-r2",
        "ds-ew-missile-active1-ecm-denied-r5",
        "ds-ew-missile-active1-eccm-restored-r5",
        "ds-shield-hardener-v-missile-r2",
        "ds-shield-battery-v-energy-r2",
        "ds-layer-energy-full-package-r2",
        "ds-layer-amm-saturation-r2",
    ):
        require(ident in by_id, f"Required defensive variant is missing: {ident}")


def test_contract(root: Path) -> None:
    facts = theories = inline = 0
    for path in (root / "tests").rglob("*.cs"):
        text = read_text(path)
        facts += len(re.findall(r"\[Fact\]", text))
        theories += len(re.findall(r"\[Theory\]", text))
        inline += len(re.findall(r"\[InlineData\(", text))
    require((facts, theories, inline, facts + inline) == (562, 20, 80, 642),
            f"Static test cardinality drifted: facts {facts}, theories {theories}, inline {inline}, cases {facts + inline}")
    checks = {
        "tests/StarCluster.Tests/Combat/DirectFire/Tl1PdsCalibrationTests.cs": (
            "Operational_targeting_computer_assists_pds_by_ten_points",
            "Degraded_targeting_computer_assists_pds_by_five_points",
            "Own_evm_does_not_reduce_amm_interception_chance",
            "Kinetic_pds_consumes_and_reloads_one_ready_package_on_a_miss",
        ),
        "tests/StarCluster.Tests/Combat/DirectFire/Tl1DefensiveSystemsCalibrationTests.cs": (
            "CriticalMissRoll",
            "CriticalHitRoll",
            "Passive_sensors_require_range_three_or_less_for_a_firm_solution",
            "Net_ecm_shrinks_the_firm_range_after_active_sensor_extension",
            "Eccm_cancels_equal_ecm_and_restores_the_firm_solution",
            "Shield_hardener_adds_one_shield_armor_while_powered",
            "Tactical_recharge_uses_only_missing_capacity_after_base_recharge",
            "Shield_battery_uses_one_charge_on_the_next_turn_after_collapse",
        ),
        "tests/StarCluster.Tests/Combat/Weapons/WeaponStateTests.cs": (
            "AmmunitionFedWeaponStartsWithOneReadyPackage",
            "AutomaticLoaderKeepsOnePackageReadyUntilTheLastShot",
        ),
    }
    for rel, markers in checks.items():
        text = read_text(root / rel)
        for marker in markers:
            require(marker in text, f"{rel} lacks marker {marker}")
    defense_text = read_text(
        root / "tests/StarCluster.Tests/Combat/DirectFire/Tl1DefensiveSystemsCalibrationTests.cs")
    require(defense_text.count(".Run(CriticalMissRoll, CriticalHitRoll);") == 4,
            "The four forced defender-hit simulator runs do not use the explicit roll-direction helpers")


def strip_csharp_literals_and_comments(text: str) -> str:
    """Blank C# strings, chars, and comments while preserving newlines."""
    out: list[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if c == "/" and n == "/":
            out.extend("  ")
            i += 2
            while i < len(text) and text[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if c == "/" and n == "*":
            out.extend("  ")
            i += 2
            while i < len(text):
                if text[i:i + 2] == "*/":
                    out.extend("  ")
                    i += 2
                    break
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            else:
                raise ContractError("Unterminated C# block comment")
            continue
        if c == "'":
            out.append(" ")
            i += 1
            while i < len(text):
                if text[i] == "\\":
                    out.extend("  "[: min(2, len(text) - i)])
                    i += 2
                    continue
                ch = text[i]
                out.append("\n" if ch == "\n" else " ")
                i += 1
                if ch == "'":
                    break
            else:
                raise ContractError("Unterminated C# character literal")
            continue
        if c == '"':
            quote_count = 1
            while i + quote_count < len(text) and text[i + quote_count] == '"':
                quote_count += 1
            raw = quote_count >= 3
            prefix = text[max(0, i - 2):i]
            verbatim = not raw and "@" in prefix
            delimiter = '"' * quote_count if raw else '"'
            out.extend(" " * quote_count)
            i += quote_count
            while i < len(text):
                if raw and text.startswith(delimiter, i):
                    out.extend(" " * quote_count)
                    i += quote_count
                    break
                if not raw and verbatim and text.startswith('""', i):
                    out.extend("  ")
                    i += 2
                    continue
                if not raw and not verbatim and text[i] == "\\":
                    out.extend("  "[: min(2, len(text) - i)])
                    i += 2
                    continue
                ch = text[i]
                out.append("\n" if ch == "\n" else " ")
                i += 1
                if not raw and ch == '"':
                    break
            else:
                raise ContractError("Unterminated C# string literal")
            continue
        out.append(c)
        i += 1
    return "".join(out)


def assert_balanced_delimiters(text: str, label: str) -> None:
    pairs = {")": "(", "}": "{", "]": "["}
    stack: list[tuple[str, int]] = []
    for offset, char in enumerate(text):
        if char in "({[":
            stack.append((char, offset))
        elif char in pairs:
            require(stack and stack[-1][0] == pairs[char],
                    f"Delimiter mismatch in {label} at offset {offset}")
            stack.pop()
    require(not stack, f"Unclosed delimiter in {label}: {stack[-1] if stack else ''}")


def parenthesized_body(text: str, open_offset: int, label: str) -> str:
    require(open_offset < len(text) and text[open_offset] == "(",
            f"Expected opening parenthesis for {label}")
    depth = 0
    for offset in range(open_offset, len(text)):
        char = text[offset]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[open_offset + 1:offset]
    raise ContractError(f"Unclosed parenthesized expression for {label}")


def top_level_argument_count(body: str, label: str) -> int:
    if not body.strip():
        return 0
    stack: list[str] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    count = 1
    for offset, char in enumerate(body):
        if char in "([{":
            stack.append(char)
        elif char in pairs:
            require(stack and stack[-1] == pairs[char],
                    f"Nested delimiter mismatch in {label} at offset {offset}")
            stack.pop()
        elif char == "," and not stack:
            count += 1
    require(not stack, f"Nested delimiter remains open in {label}")
    return count


def record_arity(text: str, record_name: str, label: str) -> int:
    stripped = strip_csharp_literals_and_comments(text)
    match = re.search(r"\brecord\s+" + re.escape(record_name) + r"\s*\(", stripped)
    require(match is not None, f"Record {record_name} is missing from {label}")
    open_offset = stripped.find("(", match.start())
    body = parenthesized_body(stripped, open_offset, f"{label}:{record_name}")
    # Duplicate positional property names are a compile failure that delimiter checks miss.
    names = re.findall(r"(?:^|,)\s*[A-Za-z_][A-Za-z0-9_<>?., ]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|,|$)", body)
    require(len(names) == len(set(names)),
            f"Record {record_name} has duplicate positional property names in {label}")
    return top_level_argument_count(body, f"{label}:{record_name}")


def constructor_arity_after(
        text: str,
        anchor: str,
        label: str,
        constructor_token: str = "new(") -> int:
    stripped = strip_csharp_literals_and_comments(text)
    anchor_offset = stripped.find(anchor)
    require(anchor_offset >= 0, f"Constructor anchor is missing in {label}: {anchor}")
    token_offset = stripped.find(constructor_token, anchor_offset)
    require(token_offset >= 0, f"Constructor token is missing in {label}: {constructor_token}")
    open_offset = stripped.find("(", token_offset)
    body = parenthesized_body(stripped, open_offset, f"{label}:{anchor}")
    return top_level_argument_count(body, f"{label}:{anchor}")


def csharp_arity_contract(root: Path) -> None:
    simulator_rel = "src/StarCluster.Core/Combat/DirectFire/Tl1WeaponMatrixSimulator.cs"
    simulator = read_text(root / simulator_rel)
    expected_records = {
        "Tl1WeaponMatrixSideProfile": 32,
        "Tl1WeaponMatrixProfile": 11,
        "Tl1WeaponMatrixResult": 54,
        "TurnSystemState": 7,
    }
    for name, expected in expected_records.items():
        actual = record_arity(simulator, name, simulator_rel)
        require(actual == expected,
                f"{simulator_rel} record {name} has arity {actual}, expected {expected}")
    actual_result = constructor_arity_after(
        simulator,
        "private static Tl1WeaponMatrixResult CreateResult",
        simulator_rel)
    require(actual_result == expected_records["Tl1WeaponMatrixResult"],
            f"CreateResult maps {actual_result} values, expected 54")

    runners = {
        "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1WeaponMatrixRunner.cs":
            (("TrialResult", 14), ("VariantSummary", 21)),
        "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1PdsCalibrationRunner.cs":
            (("TrialResult", 22), ("VariantSummary", 29)),
        "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1DefensiveCalibrationRunner.cs":
            (("TrialResult", 38), ("VariantSummary", 43)),
    }
    for rel, records in runners.items():
        text = read_text(root / rel)
        profile_count = constructor_arity_after(
            text, "private static Tl1WeaponMatrixProfile ToProfile", rel)
        side_count = constructor_arity_after(
            text, "private static Tl1WeaponMatrixSideProfile ToSide", rel)
        require(profile_count == 11, f"{rel} ToProfile maps {profile_count} values, expected 11")
        require(side_count == 32, f"{rel} ToSide maps {side_count} values, expected 32")
        for name, expected in records:
            actual = record_arity(text, name, rel)
            require(actual == expected,
                    f"{rel} record {name} has arity {actual}, expected {expected}")
        trial_new = constructor_arity_after(text, "public static TrialResult From", rel)
        require(trial_new == records[0][1],
                f"{rel} TrialResult.From maps {trial_new} values, expected {records[0][1]}")
        summary_new = constructor_arity_after(
            text,
            "return new VariantSummary",
            rel,
            "new VariantSummary(")
        require(summary_new == records[1][1],
                f"{rel} VariantSummary.Create maps {summary_new} values, expected {records[1][1]}")


def csharp_structure_contract(root: Path) -> None:
    # Lightweight lexical balance catches packaging/truncation damage; Windows compilation remains authoritative.
    for path in (root / "src").rglob("*.cs"):
        stripped = strip_csharp_literals_and_comments(read_text(path))
        assert_balanced_delimiters(stripped, str(path.relative_to(root)))
    markers = {
        "src/StarCluster.Core/Combat/Weapons/AmmunitionFeedState.cs": ("ReadyPackages", "ReservePackages", "TotalPackages", "Consume"),
        "src/StarCluster.Core/Combat/DirectFire/Tl1WeaponMatrixSimulator.cs": ("SensorTrackGateEnabled", "PdsReadyAmmunitionA", "FirmTrackTurnsA", "ShieldBatteryChargesUsedA"),
        "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1DefensiveCalibrationRunner.cs": ("RequiredVariantCount = 171", "sensor-ew-boundary", "side-swap-track"),
        "src/StarCluster.ScenarioRunner/Program.cs": ("tl1-defensive-calibration", "tl1-defensive-calibration-preflight", "checkpoint-31-tl1-defensive-calibration"),
    }
    for rel, required in markers.items():
        text = read_text(root / rel)
        for marker in required:
            require(marker in text, f"{rel} lacks marker {marker}")


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.startswith("word/") and n.endswith(".xml")]
        parts = []
        for name in names:
            root = ET.fromstring(zf.read(name))
            parts.extend(node.text or "" for node in root.iter() if node.tag.endswith("}t"))
        return re.sub(r"\s+", " ", " ".join(parts))


def document_contract(root: Path) -> None:
    files = {
        "README.md": ("Checkpoint 31", "v0.4c", "642 engine-independent tests", "171 layered defensive-system variants"),
        "Checkpoint_31_Readme.txt": ("Checkpoint 31", "Ready Package", "171 layered defensive-system variants"),
        "docs/checkpoints/Checkpoint_31_TL1_Layered_Defensive_Systems_Calibration.md": ("Ready Package", "Targeting Computer", "AMM", "ECM", "ECCM", "Shield Battery", "171 variants"),
        "docs/validation/Checkpoint_31_TL1_Layered_Defensive_Systems_Calibration.md": ("642 engine-independent tests", "171 layered defensive-system variants", "idempotent"),
        "docs/design/player_technology/TL1_Layered_Defensive_Systems_Calibration_Plan_v0_1.md": ("50 packages", "25 interceptors", "Firm through range 3", "171 variants"),
    }
    for rel, markers in files.items():
        text = read_text(root / rel)
        for marker in markers:
            require(marker in text, f"{rel} lacks marker {marker}")
    concept = docx_text(root / "docs/Star_Cluster_Game_Concept_v0.4c.docx")
    for marker in (
        "Checkpoint 31 - TL1 Layered Defensive Systems Calibration",
        "Ready Package and ammunition normalization",
        "Sensor and electronic-warfare layer",
        "Shield-defense layer",
        "171 variants at 10,000 trials each",
        "D-262", "D-269", "END OF DRAFT v0.4c",
    ):
        require(marker in concept, f"Concept v0.4c lacks marker {marker}")


def workbook_contract(root: Path) -> None:
    path = root / "docs/design/player_technology/StarCluster_Player_TL_Framework_Draft_v0_11.xlsx"
    require(path.is_file(), "Workbook v0.11 is missing")
    with zipfile.ZipFile(path) as zf:
        require(not any(n.startswith("xl/tables/") for n in zf.namelist()), "Workbook contains structured table parts")
        wb = zf.read("xl/workbook.xml").decode("utf-8")
        required_sheets = (
            "Overview", "TL1 Baseline", "TL1 Loadouts", "TL1 Test Matrix", "Phase A Runtime",
            "TL1 Phase B", "TL1 Calibration", "Checkpoint 28 Energy", "Checkpoint 29 Matrix",
            "Checkpoint 30 PDS", "Checkpoint 31 Defense", "Component Schema", "Checkpoint 25 Plan",
            "TL Matrix", "Components", "Compatibility Profiles", "Adaptation Rules", "Reference Library",
            "Reference Insights", "Design Reconciliation", "Level Themes", "Design Decisions", "Sources Used",
        )
        for sheet in required_sheets:
            require(f'name="{sheet}"' in wb, f"Workbook sheet is missing: {sheet}")
        xml = "".join(
            zf.read(n).decode("utf-8", errors="replace")
            for n in zf.namelist()
            if n.startswith("xl/") and n.endswith(".xml")
        )
        for marker in (
            "Checkpoint 30 PDS Control - Corrected by Checkpoint 31",
            "Checkpoint 31 - TL1 Layered Defensive Systems Calibration",
            "171 variants x 10,000 trials", "Ready Package", "Targeting Computer assistance", "D-269",
        ):
            require(marker in xml, f"Workbook lacks marker {marker}")


def powershell_structure_contract(root: Path) -> None:
    for path in (root / "tools/checkpoints/checkpoint-31").glob("*.ps1"):
        text = read_text(path)
        require("__MANIFEST_COUNT__" not in text, f"Unresolved manifest placeholder in {path.relative_to(root)}")
        cleaned: list[str] = []
        i = 0
        quote: str | None = None
        while i < len(text):
            c = text[i]
            if quote is not None:
                if c == "`":
                    cleaned.append(" ")
                    if i + 1 < len(text):
                        cleaned.append("\n" if text[i + 1] == "\n" else " ")
                    i += 2
                    continue
                if quote == "'" and text.startswith("''", i):
                    cleaned.extend("  ")
                    i += 2
                    continue
                if c == quote:
                    quote = None
                cleaned.append("\n" if c == "\n" else " ")
                i += 1
                continue
            if c in "'\"":
                quote = c
                cleaned.append(" ")
                i += 1
                continue
            if c == "#":
                while i < len(text) and text[i] != "\n":
                    cleaned.append(" ")
                    i += 1
                continue
            cleaned.append(c)
            i += 1
        require(quote is None, f"Unterminated PowerShell quote in {path.relative_to(root)}")
        assert_balanced_delimiters("".join(cleaned), str(path.relative_to(root)))
        functions = re.findall(r"(?im)^function\s+([A-Za-z0-9_-]+)\s*\{", text)
        require(len(functions) == len({name.lower() for name in functions}),
                f"Duplicate PowerShell function in {path.relative_to(root)}")


def script_contract(root: Path) -> None:
    apply = read_text(root / "tools/checkpoints/checkpoint-31/apply_checkpoint_31.ps1")
    for marker in (
        "[1/14]", "[14/14]", "Running 642 engine-independent tests",
        "Running 171 TL1 layered defensive-system variants", "Engine-independent tests passed: 642.",
        "TL1 layered defensive-system calibration passed: 171 variants",
        "finally { Pop-Location }",
    ):
        require(marker in apply, f"Checkpoint 31 apply script lacks marker {marker}")
    for rel, markers in {
        "tools/checkpoints/checkpoint-31/build_checkpoint_31_release.ps1": ("Checkpoint 31", "static_preflight_checkpoint_31.py", "validate_checkpoint_31_release.ps1"),
        "tools/checkpoints/checkpoint-31/validate_checkpoint_31_release.ps1": ("Checkpoint 31", "apply_checkpoint_31.ps1", "RepositoryContractOnly"),
    }.items():
        text = read_text(root / rel)
        for marker in markers:
            require(marker in text, f"{rel} lacks marker {marker}")


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    require((root / "StarCluster.sln").is_file(), f"Repository root could not be resolved from {__file__}")
    parse_manifest(root)
    active_document_contract(root)
    baseline_contract(root)
    pds_contract(root)
    defensive_contract(root)
    test_contract(root)
    csharp_structure_contract(root)
    csharp_arity_contract(root)
    document_contract(root)
    workbook_contract(root)
    powershell_structure_contract(root)
    script_contract(root)
    print("Checkpoint 31 static preflight: PASS")
    print(f"  manifest files: {EXPECTED_MANIFEST_COUNT}")
    print("  baseline: 127 rows / exact SHA-256")
    print("  tests: 642 cases")
    print("  studies: 29 kinetic / 31 energy / 48 matrix / 59 PDS / 171 defense")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"Checkpoint 31 static preflight: FAIL\n  {exc}", file=sys.stderr)
        raise SystemExit(1)
