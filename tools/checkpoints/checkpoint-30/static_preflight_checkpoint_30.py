#!/usr/bin/env python3
"""Checkpoint 30 static pre-archive contract validator.

This script verifies the six environment-independent release gates agreed for
Star Cluster checkpoint archives. It intentionally does not claim to compile or
execute the Windows/.NET acceptance suite.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

import jsonschema

MANIFEST = "CHECKPOINT_30_SHA256SUMS.txt"
BASELINE_SHA = "11913725247f43c7a11c4d5fd06a2182586ca0d91d49abd9236af5b398088dcb"
ACTIVE_RUNBOOK = "Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md"
ACTIVE_CONCEPT = "Star_Cluster_Game_Concept_v0.4b.docx"

class CheckFailure(RuntimeError):
    pass

def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")

def quoted_literals(text: str) -> list[str]:
    out: list[str] = []
    for match in re.finditer(r"'((?:''|[^'])*)'|\"((?:`.|[^\"])*)\"", text, re.S):
        if match.group(1) is not None:
            out.append(match.group(1).replace("''", "'"))
        else:
            out.append(re.sub(r"`(.)", r"\1", match.group(2)))
    return out

def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        data = zf.read("word/document.xml")
    root = ET.fromstring(data)
    texts = [node.text or "" for node in root.iter() if node.tag.endswith("}t")]
    return re.sub(r"\s+", " ", " ".join(texts)).strip()

def workbook_contract(path: Path) -> tuple[list[str], str, list[str]]:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        require(not any(n.startswith("xl/tables/") for n in names), "Workbook contains prohibited structured table parts")
        root = ET.fromstring(zf.read("xl/workbook.xml"))
        sheets = [node.attrib["name"] for node in root.iter() if node.tag.endswith("}sheet")]
        chunks: list[str] = []
        formula_errors: list[str] = []
        for name in names:
            if name.startswith("xl/") and name.endswith(".xml"):
                raw = zf.read(name).decode("utf-8", errors="replace")
                chunks.append(raw)
                for token in ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"):
                    if token in raw:
                        formula_errors.append(f"{name}:{token}")
        return sheets, "".join(chunks), formula_errors

def allowed_unmanifested(rel: str) -> bool:
    p = rel.replace("\\", "/")
    if p.startswith((".git/", ".vs/", ".vscode/", ".idea/", "out/", "src/StarCluster.Game/.godot/")):
        return True
    if re.search(r"(^|/)(bin|obj|TestResults)/", p):
        return True
    if re.search(r"\.(user|userosscache|sln\.docstates|uid)$", p, re.I):
        return True
    if re.search(r"(^|/)(\.suo|\.DS_Store|Thumbs\.db)$", p, re.I):
        return True
    if "/" not in p and (re.match(r"^Checkpoint_.*Readme\.txt$", p, re.I) or re.match(r"^CHECKPOINT_.*SHA256SUMS\.txt$", p, re.I) or re.search(r"\.zip(\.sha256\.txt)?$", p, re.I)):
        return True
    return p in {
        "collect_checkpoint_23_missing_baseline_files.ps1",
        "collect_checkpoint_23a_missing_baseline_files.ps1",
        "Checkpoint_23_Missing_Baseline_Capture_Instructions.txt",
        "Checkpoint_23a_Missing_Baseline_Capture_Instructions.txt",
    }

def parse_manifest(root: Path) -> dict[str, str]:
    path = root / MANIFEST
    require(path.is_file(), f"Missing {MANIFEST}")
    result: dict[str, str] = {}
    for lineno, line in enumerate(read_text(path).splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        m = re.fullmatch(r"([0-9a-fA-F]{64})  (.+)", line)
        require(m is not None, f"Malformed manifest line {lineno}: {line}")
        digest, rel = m.group(1).lower(), m.group(2).replace("\\", "/")
        require(rel != MANIFEST, "Manifest contains itself")
        require(rel not in result, f"Duplicate manifest path: {rel}")
        pp = PurePosixPath(rel)
        require(not pp.is_absolute() and ".." not in pp.parts, f"Unsafe manifest path: {rel}")
        result[rel] = digest
    return result

def verify_manifest(root: Path) -> int:
    entries = parse_manifest(root)
    for rel, expected in entries.items():
        path = root / rel
        require(path.is_file(), f"Manifest file missing: {rel}")
        require(sha256(path) == expected, f"Manifest hash mismatch: {rel}")
    extras: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == MANIFEST or rel in entries or allowed_unmanifested(rel):
            continue
        extras.append(rel)
    require(not extras, "Repository-owned files not locked by manifest:\n" + "\n".join(sorted(extras)))
    return len(entries)

def strip_c_like(text: str) -> str:
    out: list[str] = []
    i = 0
    state = "code"
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if c == "/" and n == "/": state, i = "line", i + 2; out.extend("  "); continue
            if c == "/" and n == "*": state, i = "block", i + 2; out.extend("  "); continue
            if c == '"': state = "string"; out.append(" "); i += 1; continue
            if c == "'": state = "char"; out.append(" "); i += 1; continue
            out.append(c); i += 1; continue
        if state == "line":
            if c == "\n": state = "code"; out.append("\n")
            else: out.append(" ")
            i += 1; continue
        if state == "block":
            if c == "*" and n == "/": state, i = "code", i + 2; out.extend("  ")
            else: out.append("\n" if c == "\n" else " "); i += 1
            continue
        if state in {"string", "char"}:
            if c == "\\": out.extend("  "); i += 2; continue
            if (state == "string" and c == '"') or (state == "char" and c == "'"): state = "code"
            out.append("\n" if c == "\n" else " "); i += 1
    require(state in {"code", "line"}, f"Unterminated C# lexical state: {state}")
    return "".join(out)

def balanced(text: str, path: str) -> None:
    pairs = {')': '(', ']': '[', '}': '{'}
    stack: list[tuple[str, int]] = []
    for i, c in enumerate(text):
        if c in "([{": stack.append((c, i))
        elif c in pairs:
            require(stack and stack[-1][0] == pairs[c], f"Delimiter mismatch in {path} at offset {i}")
            stack.pop()
    require(not stack, f"Unclosed delimiter in {path}: {stack[-1] if stack else ''}")

def extract_balanced_parentheses(text: str, start: int) -> str:
    require(start < len(text) and text[start] == "(", "Balanced extraction must begin at '('")
    depth = 0
    state = "code"
    i = start
    while i < len(text):
        c = text[i]
        n = text[i + 1] if i + 1 < len(text) else ""
        if state == "code":
            if c == "/" and n == "/": state = "line"; i += 2; continue
            if c == "/" and n == "*": state = "block"; i += 2; continue
            if c == '"': state = "string"; i += 1; continue
            if c == "'": state = "char"; i += 1; continue
            if c == "(": depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0: return text[start + 1:i]
            i += 1; continue
        if state == "line":
            if c == "\n": state = "code"
            i += 1; continue
        if state == "block":
            if c == "*" and n == "/": state = "code"; i += 2
            else: i += 1
            continue
        if state in {"string", "char"}:
            if c == "\\": i += 2; continue
            if (state == "string" and c == '"') or (state == "char" and c == "'"): state = "code"
            i += 1
    raise CheckFailure("Unclosed parenthesized expression")

def top_level_argument_count(body: str) -> int:
    if not body.strip(): return 0
    depth = 0
    state = "code"
    count = 1
    i = 0
    while i < len(body):
        c = body[i]
        n = body[i + 1] if i + 1 < len(body) else ""
        if state == "code":
            if c == "/" and n == "/": state = "line"; i += 2; continue
            if c == "/" and n == "*": state = "block"; i += 2; continue
            if c == '"': state = "string"; i += 1; continue
            if c == "'": state = "char"; i += 1; continue
            if c in "([{<": depth += 1
            elif c in ")]}>": depth -= 1
            elif c == "," and depth == 0: count += 1
            i += 1; continue
        if state == "line":
            if c == "\n": state = "code"
            i += 1; continue
        if state == "block":
            if c == "*" and n == "/": state = "code"; i += 2
            else: i += 1
            continue
        if state in {"string", "char"}:
            if c == "\\": i += 2; continue
            if (state == "string" and c == '"') or (state == "char" and c == "'"): state = "code"
            i += 1
    require(depth == 0, "Unbalanced argument expression")
    return count

def count_parenthesized_after(text: str, marker: str, occurrence: int = 1) -> int:
    pos = -1
    for _ in range(occurrence):
        pos = text.find(marker, pos + 1)
        require(pos >= 0, f"Marker not found for arity check: {marker}")
    open_pos = text.find("(", pos + len(marker))
    require(open_pos >= 0, f"No parenthesis after marker: {marker}")
    return top_level_argument_count(extract_balanced_parentheses(text, open_pos))

def check_csharp(root: Path) -> int:
    files = list(root.glob("src/**/*.cs")) + list(root.glob("tests/**/*.cs"))
    for path in files:
        text = read_text(path)
        require("<<<<<<<" not in text and ">>>>>>>" not in text, f"Merge marker in {path}")
        balanced(strip_c_like(text), str(path))
    # New surface contracts that catch common constructor/result drift.
    sim = read_text(root / "src/StarCluster.Core/Combat/DirectFire/Tl1WeaponMatrixSimulator.cs")
    require(sim.count("private static bool ResolvePdsAgainstMissile(") == 1, "ResolvePdsAgainstMissile must be declared exactly once")
    require("bool pdsReady,\n        ref int attemptsUsedThisTurn" in sim, "PDS resolver signature is malformed")
    runner = read_text(root / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1PdsCalibrationRunner.cs")
    require(runner.count("private sealed record VariantSummary(") == 1, "PDS VariantSummary must be declared exactly once")
    require("new Tl1WeaponMatrixSimulator(ToProfile(variant)).Run(" in runner, "PDS runner does not invoke the shared simulator")

    # Catch malformed edits that a delimiter-only check cannot see.
    for path in files:
        code = strip_c_like(read_text(path))
        require(re.search(r"\belse\s+else\b", code) is None, f"Duplicate else keyword in {path}")
        require(re.search(r"\breturn\s+return\b", code) is None, f"Duplicate return keyword in {path}")
        for match in re.finditer(r"\belse\b", code):
            tail = code[match.end():]
            next_token = re.search(r"\S+", tail)
            require(next_token is not None and (next_token.group(0).startswith("{") or next_token.group(0).startswith("if")), f"Malformed else clause in {path} near offset {match.start()}")

    require(count_parenthesized_after(sim, "public sealed record Tl1WeaponMatrixSideProfile") == 21, "Tl1WeaponMatrixSideProfile must contain 21 fields")
    require(count_parenthesized_after(sim, "public sealed record Tl1WeaponMatrixResult") == 30, "Tl1WeaponMatrixResult must contain 30 fields")
    result_marker = "Tl1WeaponMatrixResult Result(Tl1DuelOutcome outcome, int completedTurns) =>"
    result_pos = sim.find(result_marker)
    require(result_pos >= 0, "Local Tl1WeaponMatrixResult constructor was not found")
    new_pos = sim.find("new", result_pos + len(result_marker))
    result_open = sim.find("(", new_pos)
    require(new_pos >= 0 and result_open >= 0 and top_level_argument_count(extract_balanced_parentheses(sim, result_open)) == 30, "Local Tl1WeaponMatrixResult constructor must pass 30 arguments")
    require(count_parenthesized_after(runner, "private static Tl1WeaponMatrixSideProfile ToSide") == 1, "PDS ToSide signature drifted")
    runner_new = runner.find("=>\n        new(", runner.find("private static Tl1WeaponMatrixSideProfile ToSide"))
    require(runner_new >= 0, "PDS ToSide constructor was not found")
    require(top_level_argument_count(extract_balanced_parentheses(runner, runner.find("(", runner_new))) == 21, "PDS ToSide must map 21 fields")
    wm_runner = read_text(root / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1WeaponMatrixRunner.cs")
    wm_new = wm_runner.find("=> new(", wm_runner.find("private static Tl1WeaponMatrixSideProfile ToSide"))
    require(wm_new >= 0, "Weapon-matrix ToSide constructor was not found")
    require(top_level_argument_count(extract_balanced_parentheses(wm_runner, wm_runner.find("(", wm_new))) == 21, "Weapon-matrix ToSide must map 21 fields")
    return len(files)

def check_powershell(root: Path, allow_manifest_placeholder: bool = False) -> int:
    files = list(root.glob("tools/**/*.ps1"))
    for path in files:
        text = read_text(path)
        require(allow_manifest_placeholder or "__MANIFEST_COUNT__" not in text, f"Unresolved manifest placeholder in {path}")
        require("<<<<<<<" not in text and ">>>>>>>" not in text, f"Merge marker in {path}")
        # Conservative removal of comments and quoted strings for delimiter checks.
        cleaned = []
        i = 0
        quote: str | None = None
        while i < len(text):
            c = text[i]
            if quote:
                if c == '`': cleaned.extend("  "); i += 2; continue
                if c == quote:
                    if quote == "'" and i + 1 < len(text) and text[i + 1] == "'": cleaned.extend("  "); i += 2; continue
                    quote = None
                cleaned.append("\n" if c == "\n" else " "); i += 1; continue
            if c in "'\"": quote = c; cleaned.append(" "); i += 1; continue
            if c == '#':
                while i < len(text) and text[i] != "\n": cleaned.append(" "); i += 1
                continue
            cleaned.append(c); i += 1
        require(quote is None, f"Unterminated PowerShell quote in {path}")
        balanced("".join(cleaned), str(path))
        funcs = re.findall(r"(?im)^function\s+([A-Za-z0-9_-]+)\s*\{", text)
        require(len(funcs) == len(set(f.lower() for f in funcs)), f"Duplicate PowerShell function in {path}")
    apply = read_text(root / "tools/checkpoints/checkpoint-30/apply_checkpoint_30.ps1")
    require("try {" in apply and "finally { Pop-Location }" in apply, "Checkpoint 30 apply script lacks complete try/finally")
    require("[13/13]" in apply and "Engine-independent tests passed: 627." in apply, "Checkpoint 30 apply footer/count contract is stale")
    return len(files)

def check_literal_assertions(root: Path) -> tuple[int, int, int]:
    script = read_text(root / "tools/checkpoints/checkpoint-30/apply_checkpoint_30.ps1")
    text_contracts = 0; docx_contracts = 0; markers = 0
    # These calls are formatted with a literal path then @(...), then a literal description.
    pattern = re.compile(r"Assert-(FileContains|FileNotContains|DocxContains)\s+'([^']+)'\s+@\((.*?)\)\s+'[^']+'", re.S)
    for kind, raw_path, array_body in pattern.findall(script):
        rel = raw_path.replace(".\\", "").replace("\\", "/")
        path = root / rel
        require(path.is_file(), f"Assertion target missing: {rel}")
        values = quoted_literals(array_body)
        require(values, f"Assertion has no literal markers: {rel}")
        markers += len(values)
        if kind == "DocxContains":
            haystack = docx_text(path); docx_contracts += 1
        else:
            haystack = read_text(path); text_contracts += 1
        for value in values:
            if kind == "FileNotContains": require(value not in haystack, f"Prohibited marker in {rel}: {value}")
            else: require(value in haystack, f"Required marker missing in {rel}: {value}")
    require(text_contracts >= 9, f"Too few literal text contracts discovered: {text_contracts}")
    require(docx_contracts >= 1, "No DOCX contract discovered")
    return text_contracts, docx_contracts, markers

def check_phase_b(root: Path) -> int:
    files = sorted((root / "src/StarCluster.ScenarioRunner/Scenarios/TL1PhaseB").glob("*.json"))
    require(len(files) == 7, f"Expected 7 Phase B documents; found {len(files)}")
    count = 0
    def outcome(roll: int, chance: int) -> str:
        if roll == 1: return "CriticalMiss"
        if roll == 100: return "CriticalHit"
        return "Hit" if roll > 100 - chance else "Miss"
    for path in files:
        d = json.loads(read_text(path))
        require(d["schemaVersion"] == "star-cluster-tl1-phase-b-v1", f"Bad Phase B schema: {path.name}")
        for c in d["cases"]:
            count += 1
            chance_a = max(5, min(95, 50 + int(c["weaponAccuracy"]) + int(c["computerBonus"]) - 5*int(c["rangeHexes"]) - (10 if c["targetEvasive"] else 0) - (5 if c["shooterEvasive"] else 0)))
            require(int(c["expectedChance"]) == chance_a, f"Phase B expectedChance mismatch: {c['id']}")
            if c["operation"] == "Roll" and c.get("expectedOutcomeA"):
                require(c["expectedOutcomeA"] == outcome(int(c["rollA"]), chance_a), f"Phase B roll mismatch: {c['id']}")
            if c["operation"] == "SimultaneousVolley":
                chance_b = max(5, min(95, 50 + int(c["weaponAccuracy"]) + int(c["computerBonus"]) - 5*int(c["rangeHexes"]) - (10 if c["shooterEvasive"] else 0) - (5 if c["targetEvasive"] else 0)))
                oa, ob = outcome(int(c["rollA"]), chance_a), outcome(int(c["rollB"]), chance_b)
                require(not c.get("expectedOutcomeA") or c["expectedOutcomeA"] == oa, f"Phase B A outcome mismatch: {c['id']}")
                require(not c.get("expectedOutcomeB") or c["expectedOutcomeB"] == ob, f"Phase B B outcome mismatch: {c['id']}")
                ha = max(0, int(c["hullA"]) - (int(c["damageB"]) if ob in {"Hit","CriticalHit"} else 0))
                hb = max(0, int(c["hullB"]) - (int(c["damageA"]) if oa in {"Hit","CriticalHit"} else 0))
                require(int(c["expectedHullA"]) == ha and int(c["expectedHullB"]) == hb, f"Phase B hull mismatch: {c['id']}")
                require(bool(c["expectedMutualDestruction"]) == (ha == 0 and hb == 0), f"Phase B mutual mismatch: {c['id']}")
    require(count == 36, f"Expected 36 Phase B cases; found {count}")
    return count

def check_studies(root: Path) -> dict[str, int]:
    base = root / "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration"
    specs = {
        "kinetic": ("tl1-kc01-kinetic-interaction-study.json", 29),
        "energy": ("tl1-ec01-energy-interaction-study.json", 31),
        "weapon": ("tl1-wm01-complete-weapon-matrix.json", 48),
        "pds": ("tl1-pds01-interception-study.json", 59),
    }
    counts: dict[str,int] = {}
    docs = {}
    for key, (name, expected) in specs.items():
        doc = json.loads(read_text(base / name)); docs[key] = doc
        count = len(doc["variants"]); counts[key] = count
        require(count == expected, f"{key} variant count {count}, expected {expected}")
        require(doc["baselineSha256"].lower() == BASELINE_SHA, f"{key} baseline hash mismatch")
        ids = [v["id"] for v in doc["variants"]]
        require(len(ids) == len(set(ids)), f"Duplicate {key} variant ID")
        byid = {v["id"]: v for v in doc["variants"]}
        for v in doc["variants"]:
            pair = v.get("pairId")
            if pair:
                require(pair in byid, f"{key} missing pair {pair}")
                if key == "pds":
                    partner = byid[pair]
                    require(partner.get("pairId") == v["id"], f"{key} nonreciprocal pair {v['id']}/{pair}")
                    require(v["sideA"] == partner["sideB"] and v["sideB"] == partner["sideA"], f"{key} pair is not an exact side swap: {v['id']}/{pair}")
                    for field in set(v) | set(partner):
                        if field not in {"id", "label", "pairId", "sideA", "sideB"}:
                            require(v.get(field) == partner.get(field), f"{key} pair differs in {field}: {v['id']}/{pair}")
    pds = docs["pds"]; byid = {v["id"]:v for v in pds["variants"]}
    def profile(vid: str, fam: str, power: int, reaction: int, chance: int, ammo: int, unlimited: bool) -> None:
        s = byid[vid]["sideA"]
        require((s["pdsFamily"],s["pdsPowerCost"],s["pdsReactionCapacity"],s["pdsInterceptionChance"],s["pdsAmmunition"],s["pdsUnlimitedAmmunition"]) == (fam,power,reaction,chance,ammo,unlimited), f"Bad PDS profile: {vid}")
    profile("pds-kpds-v-m-r2","kinetic",1,1,35,12,False)
    profile("pds-ammpds-v-m-r2","amm",1,1,50,6,False)
    profile("pds-epds-v-m-r2","energy",2,1,40,0,True)
    require(byid["pds-kpds-v-saturation-r2"]["sideB"]["missileLaunchesPerTurn"] == 2, "Saturation variant is not two launches")
    require(byid["pds-kpds-reaction2-r2"]["sideA"]["pdsReactionCapacity"] == 2, "RC2 variant invalid")
    require(byid["pds-kpds-ammo2-r2"]["sideA"]["pdsAmmunition"] == 2, "Ammo2 variant invalid")
    return counts

def check_schema_and_data(root: Path) -> tuple[int,int,int]:
    schema = json.loads(read_text(root / "docs/design/player_technology/tl1_pds_calibration_schema_v0_1.json"))
    require(schema.get("$id") == "star-cluster-tl1-pds-calibration-v1", "PDS schema ID mismatch")
    require(schema["properties"]["variants"]["minItems"] == 59 and schema["properties"]["variants"]["maxItems"] == 59, "PDS schema variant cardinality mismatch")
    study = json.loads(read_text(root / "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-pds01-interception-study.json"))
    jsonschema.Draft202012Validator.check_schema(schema)
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(study), key=lambda e: list(e.path))
    require(not errors, "PDS study JSON schema validation failed: " + "; ".join(error.message for error in errors[:10]))
    baseline = root / "docs/archive/player_technology/pre-cp165-active/tl1_core_combat_numerical_baseline_v0_1.csv"
    require(sha256(baseline) == BASELINE_SHA, "Accepted baseline hash mismatch")
    with baseline.open(encoding="utf-8-sig", newline="") as f: base_rows = list(csv.DictReader(f))
    require(len(base_rows) == 126, f"Expected 126 baseline rows; found {len(base_rows)}")
    scenario = root / "docs/design/player_technology/tl1_core_combat_test_scenarios_v0_2.csv"
    with scenario.open(encoding="utf-8-sig", newline="") as f: scenario_rows = list(csv.DictReader(f))
    require(len(scenario_rows) == 62, f"Expected 62 scenario rows; found {len(scenario_rows)}")
    crows = [r for r in scenario_rows if r["scenario_id"].startswith("TL1-C")]
    require(len(crows) == 9, f"Expected 9 Phase C rows; found {len(crows)}")
    require(all(r["implementation_status"] == "implemented_checkpoint_30" for r in crows[:7]), "C01-C07 must be implemented_checkpoint_30")
    return len(base_rows), len(scenario_rows), len(crows)

def check_tests(root: Path) -> dict[str,int]:
    files = {
        "direct": (root/"tests/StarCluster.Tests/Combat/DirectFire/Tl1DirectFireAccuracyTests.cs",10,3),
        "kinetic": (root/"tests/StarCluster.Tests/Combat/DirectFire/Tl1KineticDuelCalibrationTests.cs",8,0),
        "energy": (root/"tests/StarCluster.Tests/Combat/DirectFire/Tl1EnergyDuelCalibrationTests.cs",10,0),
        "matrix": (root/"tests/StarCluster.Tests/Combat/DirectFire/Tl1WeaponMatrixTests.cs",8,0),
        "pds": (root/"tests/StarCluster.Tests/Combat/DirectFire/Tl1PdsCalibrationTests.cs",12,0),
    }
    out={}
    for key,(path,facts,theories) in files.items():
        text=read_text(path); af=text.count("[Fact]"); at=text.count("[Theory]")
        require((af,at)==(facts,theories),f"{key} test annotation count {(af,at)}, expected {(facts,theories)}")
        out[key]=af+at
    pds_text=read_text(files["pds"][0])
    for marker in ("Pds_readiness_locks_power_before_weapon_commitment","Kinetic_pds_consumes_ammunition_on_a_miss","Reaction_capacity_one_allows_one_attempt_against_saturation","Unpowered_pds_does_not_attempt_interception","Own_evm_reduces_pds_chance_by_five_points"):
        require(marker in pds_text,f"PDS test marker missing: {marker}")

    all_test_text = "\n".join(read_text(path) for path in (root / "tests/StarCluster.Tests").rglob("*.cs"))
    fact_count = all_test_text.count("[Fact]")
    theory_count = all_test_text.count("[Theory]")
    inline_count = all_test_text.count("[InlineData(")
    member_count = all_test_text.count("[MemberData(")
    class_count = all_test_text.count("[ClassData(")
    require(member_count == 0 and class_count == 0, "Static test cardinality requires explicit handling for MemberData/ClassData")
    test_case_count = fact_count + inline_count
    require((fact_count, theory_count, inline_count, test_case_count) == (547, 20, 80, 627), f"Static test cardinality drifted: facts {fact_count}, theories {theory_count}, inline rows {inline_count}, cases {test_case_count}")
    out["total"] = test_case_count
    return out

def check_release_metadata(root: Path) -> int:
    contracts = {
        "README.md": ("Checkpoint 30", "v0.4b", "59 PDS/interception variants", "627 engine-independent tests"),
        "Checkpoint_30_Readme.txt": ("Checkpoint 30", "PDS", "59"),
        "docs/checkpoints/Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md": ("59-variant", "Kinetic PDS", "AMM PDS", "Energy PDS"),
        "docs/validation/Checkpoint_30_TL1_PDS_And_Missile_Interception_Calibration.md": ("627 engine-independent tests", "59 PDS/interception variants", "idempotent"),
    }
    markers = 0
    for rel, values in contracts.items():
        path = root / rel
        require(path.is_file(), f"Release metadata file missing: {rel}")
        text = read_text(path)
        folded = text.casefold()
        for value in values:
            require(value.casefold() in folded, f"Release metadata marker missing in {rel}: {value}")
            markers += 1
    apply = read_text(root / "tools/checkpoints/checkpoint-30/apply_checkpoint_30.ps1")
    for value in ("Running 627 engine-independent tests", "Running 59 TL1 PDS/interception variants", "Engine-independent tests passed: 627.", "TL1 PDS/interception calibration passed: 59 variants"):
        require(value in apply, f"Apply-script release count marker missing: {value}")
        markers += 1
    return markers

def check_active_state(root: Path) -> None:
    active_runbooks = sorted(p.name for p in (root/"docs/validation").glob("Checkpoint_*.md"))
    active_concepts = sorted(p.name for p in (root/"docs").glob("Star_Cluster_Game_Concept_v*.docx"))
    require(active_runbooks == [ACTIVE_RUNBOOK], f"Active runbooks invalid: {active_runbooks}")
    require(active_concepts == [ACTIVE_CONCEPT], f"Active concepts invalid: {active_concepts}")
    require((root/"docs/validation/archive/Checkpoint_29_Revised_Evasive_Maneuvering_And_Complete_TL1_Weapon_Matrix.md").is_file(), "Archived CP29 runbook missing")
    require((root/"docs/archive/Star_Cluster_Game_Concept_v0.4a.docx").is_file(), "Archived Concept v0.4a missing")

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default=".")
    ap.add_argument("--skip-manifest",action="store_true")
    args=ap.parse_args()
    root=Path(args.root).resolve()
    require(root.is_dir(),f"Root does not exist: {root}")
    check_active_state(root)
    release_markers = check_release_metadata(root)
    text_contracts,docx_contracts,markers=check_literal_assertions(root)
    concept=docx_text(root/"docs"/ACTIVE_CONCEPT)
    for marker in ("Checkpoint 30 - TL1 PDS and Missile-Interception Calibration","D-258","D-261","END OF DRAFT v0.4b"):
        require(marker in concept,f"Concept marker missing: {marker}")
    sheets,workbook_xml,formula_errors=workbook_contract(root/"docs/design/player_technology/StarCluster_Player_TL_Framework_Draft_v0_10.xlsx")
    required_sheets=["Checkpoint 28 Energy","Checkpoint 29 Matrix","Checkpoint 30 PDS"]
    for s in required_sheets: require(s in sheets,f"Workbook sheet missing: {s}")
    for m in ("D-261","Checkpoint 30 - TL1 PDS and Interception Calibration","59 variants x 10,000 trials","Reaction Capacity"):
        require(m in workbook_xml,f"Workbook marker missing: {m}")
    require(not formula_errors,"Workbook formula error markers: "+", ".join(formula_errors))
    phase_b=check_phase_b(root)
    studies=check_studies(root)
    base_rows,scenario_rows,crows=check_schema_and_data(root)
    tests=check_tests(root)
    cs_count=check_csharp(root)
    ps_count=check_powershell(root, allow_manifest_placeholder=args.skip_manifest)
    # Parse every JSON file in the packaged repository.
    json_count=0
    for p in root.rglob("*.json"):
        if any(part in {"bin","obj","out",".godot"} for part in p.parts): continue
        json.loads(read_text(p)); json_count+=1
    manifest_count=None if args.skip_manifest else verify_manifest(root)
    print("Checkpoint 30 static preflight: PASS")
    print(f"  literal contracts: {text_contracts} text, {docx_contracts} DOCX, {markers} markers")
    print(f"  release metadata: {release_markers} identity/count markers verified")
    print(f"  workbook: {len(sheets)} sheets, required markers present, no formula-error tokens")
    print(f"  Phase B: {phase_b} deterministic cases recalculated")
    print(f"  studies: kinetic {studies['kinetic']}, energy {studies['energy']}, weapon {studies['weapon']}, PDS {studies['pds']}")
    print(f"  data: {base_rows} baseline rows, {scenario_rows} matrix rows, {crows} Phase C rows")
    print(f"  tests: {tests['total']} statically enumerated cases; focal annotations direct {tests['direct']}, kinetic {tests['kinetic']}, energy {tests['energy']}, matrix {tests['matrix']}, PDS {tests['pds']}")
    print(f"  source structure: {cs_count} C# files, {ps_count} PowerShell files")
    print(f"  JSON: {json_count} files parsed")
    print(f"  active state: {ACTIVE_RUNBOOK}; {ACTIVE_CONCEPT}")
    if manifest_count is not None: print(f"  manifest: {manifest_count} files hash-verified; no repository-owned extras")
    else: print("  manifest: skipped for pre-manifest authoring pass")
    print("  Windows PowerShell/.NET compile and runtime validation: not executed by this static preflight")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except CheckFailure as exc:
        print(f"Checkpoint 30 static preflight: FAIL\n  {exc}",file=sys.stderr)
        raise SystemExit(1)
