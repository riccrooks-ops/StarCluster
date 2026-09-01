from pathlib import Path
import hashlib
import json
import re
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[3]
errors = []
checks = 0


def ok(condition, message):
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def load(rel):
    path = ROOT / rel
    ok(path.is_file(), f"missing {rel}")
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"json parse {rel}: {exc}")
        return {}


def sha256(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def count_top_level_items(text):
    """Count comma-separated C# items while ignoring nested calls/generics/strings."""
    depth_round = depth_square = depth_curly = depth_angle = 0
    in_string = False
    verbatim = False
    escape = False
    commas = 0
    has_nonspace = False
    i = 0
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
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
            i += 1
            continue
        if ch == '@' and i + 1 < len(text) and text[i + 1] == '"':
            in_string = True
            verbatim = True
            has_nonspace = True
            i += 2
            continue
        if ch == '"':
            in_string = True
            has_nonspace = True
            i += 1
            continue
        if not ch.isspace():
            has_nonspace = True
        if ch == '(': depth_round += 1
        elif ch == ')': depth_round -= 1
        elif ch == '[': depth_square += 1
        elif ch == ']': depth_square -= 1
        elif ch == '{': depth_curly += 1
        elif ch == '}': depth_curly -= 1
        elif ch == '<': depth_angle += 1
        elif ch == '>' and depth_angle > 0: depth_angle -= 1
        elif ch == ',' and depth_round == depth_square == depth_curly == depth_angle == 0:
            commas += 1
        i += 1
    return 0 if not has_nonspace else commas + 1


required = [
    "README.md",
    "docs/README.md",
    "docs/Prototype_TODO.md",
    "docs/Star_Cluster_Game_Concept_v0.6c.docx",
    "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_6.json",
    "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_5.json",
    "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_10.json",
    "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_9.json",
    "docs/design/player_technology/TL1_35_Space_Track_Aware_Movement_And_Acquisition_Study_v0_1.md",
    "docs/design/player_technology/TL1_35_Space_Operational_Sensor_Acquisition_And_EW_Study_v0_1.md",
    "docs/design/testing/checkpoint_64_validation_suite_policy_v0_1.json",
    "docs/design/testing/Checkpoint_64_Validation_Tiers.md",
    "docs/validation/Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md",
    "docs/validation/archive/Checkpoint_63b_Manifest_Binding_Hotfix.md",
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc07-35-space-track-aware-movement-acquisition.json",
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc06-35-space-operational-sensor-acquisition-ew.json",
    "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs",
    "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs",
    "tools/calibration/checkpoints/checkpoint-64.json",
    "tools/calibration/checkpoints/checkpoint-64-deep-calibration.json",
    "tools/checkpoints/checkpoint-64/apply_checkpoint_64.ps1",
    "tools/checkpoints/checkpoint-64/test_checkpoint_64_contract.ps1",
    "tools/checkpoints/checkpoint-64/static_preflight_checkpoint_64.py",
    "CHECKPOINT_64_SHA256SUMS.txt",
]
for rel in required:
    ok((ROOT / rel).is_file(), f"missing required path {rel}")

study = load(
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/"
    "tl1-itc07-35-space-track-aware-movement-acquisition.json"
)
historical_study = load(
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/"
    "tl1-itc06-35-space-operational-sensor-acquisition-ew.json"
)
baseline = load(
    "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_6.json"
)
profiles = load(
    "src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/"
    "tl1-tl2-standard-runtime-profiles-v0_3.json"
)
policy = load("docs/design/testing/checkpoint_64_validation_suite_policy_v0_1.json")
active = load("tools/calibration/checkpoints/checkpoint-64.json")
deep = load("tools/calibration/checkpoints/checkpoint-64-deep-calibration.json")
schema = load(
    "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_10.json"
)

# Checkpoint identity and harness/manifest binding. These assertions are kept
# explicit because 63a demonstrated that a correct package manifest is not
# enough if the active checkpoint definition still references an old one.
ok(active.get("checkpointId") == "64", "active checkpoint id 64")
ok(deep.get("checkpointId") == "64", "deep checkpoint id 64")
ok(active.get("manifestFile") == "CHECKPOINT_64_SHA256SUMS.txt", "active manifest binding")
ok(deep.get("manifestFile") == "CHECKPOINT_64_SHA256SUMS.txt", "deep manifest binding")
ok(active.get("outputRoot") == "out/checkpoint-64", "active output root")
ok(deep.get("outputRoot") == "out/checkpoint-64-deep-calibration", "deep output root")
runbook = "docs/validation/Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md"
ok(runbook in active.get("documentation", []), "active runbook binding")
ok(runbook in deep.get("documentation", []), "deep runbook binding")

# Study identity, construction envelope, and exact five-regime paired matrix.
ok(study.get("id") == "tl1-itc07-35-space-track-aware-movement-acquisition", "study id")
ok(study.get("masterSeed") == 640100, "study master seed")
ok(study.get("trialsPerVariant") == 10000, "study default trial count")
ok(len(study.get("builds", [])) == 6, "build count")
ok(len(study.get("variants", [])) == 90, "variant count")
ids = [variant.get("id") for variant in study.get("variants", [])]
ok(len(ids) == len(set(ids)) == 90, "variant ids unique")

expected_builds = {
    "balanced_generalist_major": (1, 1, True, True, 1, 33, 2),
    "dual_main_striker_major": (2, 1, True, False, 0, 34, 1),
    "dual_reactor_power_core": (1, 2, True, False, 0, 34, 1),
    "pds_saturator": (1, 1, False, False, 5, 35, 0),
    "dual_main_dual_pds": (2, 1, False, False, 2, 35, 0),
    "shielded_pds_fortress": (1, 1, False, True, 3, 34, 1),
}
builds = {build.get("id"): build for build in study.get("builds", [])}
ok(set(builds) == set(expected_builds), "build ids exact")
for build_id, expected in expected_builds.items():
    build = builds.get(build_id, {})
    actual = (
        build.get("mainWeaponCount"),
        build.get("mainReactorCount"),
        build.get("activeSensor"),
        build.get("shieldGenerator"),
        build.get("kineticPdsCount"),
        build.get("usedSpace"),
        build.get("freeSupportSpace"),
    )
    ok(actual == expected, f"frozen build arithmetic {build_id}: {actual}")
    computed = (
        13
        + 6 * int(build.get("mainWeaponCount", 0))
        + 6 * int(build.get("mainReactorCount", 0))
        + (3 if build.get("activeSensor") else 0)
        + (3 if build.get("shieldGenerator") else 0)
        + 2 * int(build.get("kineticPdsCount", 0))
    )
    ok(computed == build.get("usedSpace"), f"computed used space {build_id}")
    ok(35 - computed == build.get("freeSupportSpace"), f"computed free space {build_id}")

regimes = {
    "established-firm-control": ("EstablishedFirm", 0, "OpponentAwareRange"),
    "legacy-auto-active-clear": ("AutoActive", 0, "OpponentAwareRange"),
    "track-aware-auto-active-clear": (
        "AcquisitionFirstAutoActive", 0, "TrackAwareOpponentRange"
    ),
    "legacy-auto-active-ew1": ("AutoActive", 1, "OpponentAwareRange"),
    "track-aware-auto-active-ew1": (
        "AcquisitionFirstAutoActive", 1, "TrackAwareOpponentRange"
    ),
}
families = ["Kinetic", "Energy", "Missile"]
all_variants = study.get("variants", [])
for build_id, expected in expected_builds.items():
    main_count = expected[0]
    for family in families:
        lane = [
            variant for variant in all_variants
            if variant.get("sideABuildId") == build_id
            and variant.get("sideAFamily") == family
        ]
        ok(len(lane) == 5, f"paired lane count {build_id}/{family}")
        ok(
            len({variant.get("comparisonGroup") for variant in lane}) == 1,
            f"paired comparison group {build_id}/{family}",
        )
        actual_regimes = {
            (
                variant.get("profileLabel"),
                variant.get("sideATrackPolicy"),
                variant.get("sideANetEwRangePenalty"),
                variant.get("movementMode"),
            )
            for variant in lane
        }
        expected_regimes = {
            (label, values[0], values[1], values[2])
            for label, values in regimes.items()
        }
        ok(actual_regimes == expected_regimes, f"regime coverage {build_id}/{family}")
        ok(
            all(
                variant.get("sideBBuildId") == "balanced_generalist_major"
                and variant.get("sideBFamily") == "Missile"
                for variant in lane
            ),
            f"opponent control {build_id}/{family}",
        )
        ok(
            all(
                variant.get("sideATacticalPowerDoctrine") == "FullVolleyFirst"
                and variant.get("sideBTacticalPowerDoctrine") == "FullVolleyFirst"
                and variant.get("sideAReactorOutputOverride") == 5
                and variant.get("sideBReactorOutputOverride") == 5
                for variant in lane
            ),
            f"power controls {build_id}/{family}",
        )
        ok(
            all(
                variant.get("sideBTrackPolicy") == "EstablishedFirm"
                and variant.get("sideBNetEwRangePenalty") == 0
                for variant in lane
            ),
            f"Side B track control {build_id}/{family}",
        )
        ok(
            all(
                variant.get("sideAProfileId") == "tl1-production"
                and variant.get("sideBProfileId") == "tl1-production"
                and variant.get("sideAAuxiliaryProfileId") == "aux-r53-none-tl1"
                and variant.get("sideBAuxiliaryProfileId") == "aux-r53-none-tl1"
                for variant in lane
            ),
            f"profile controls {build_id}/{family}",
        )
        ok(
            all(
                variant.get("initialRangeHexes") == 4
                and variant.get("protectedCompartmentation") is False
                and variant.get("damageControl") == "ComponentFirstReserveOne"
                and variant.get("baseShieldRechargeEnabled") is True
                and variant.get("evasiveManeuversEnabled") is False
                and variant.get("pdsEnabled") is True
                and variant.get("escapeDisengagementEnabled") is False
                and variant.get("sideABackgroundTacticalPowerCommitment") == 0
                and variant.get("sideBBackgroundTacticalPowerCommitment") == 0
                for variant in lane
            ),
            f"frozen combat controls {build_id}/{family}",
        )
        if main_count == 2:
            ok(
                all(variant.get("sideASecondaryFamily") == family for variant in lane),
                f"dual-main family duplication {build_id}/{family}",
            )
        else:
            ok(
                all("sideASecondaryFamily" not in variant for variant in lane),
                f"single-main no secondary {build_id}/{family}",
            )
        ok(
            all("sideBSecondaryFamily" not in variant for variant in lane),
            f"Side B single-main {build_id}/{family}",
        )

ok(
    sum(
        1 for variant in all_variants
        if variant.get("movementMode") == "TrackAwareOpponentRange"
        and variant.get("sideATrackPolicy") == "AcquisitionFirstAutoActive"
    ) == 36,
    "36 track-aware/acquisition-first variants",
)
ok(
    sum(1 for variant in all_variants if variant.get("profileLabel") == "track-aware-auto-active-clear") == 18,
    "18 clear track-aware variants",
)
ok(
    sum(1 for variant in all_variants if variant.get("profileLabel") == "track-aware-auto-active-ew1") == 18,
    "18 EW1 track-aware variants",
)

# Production profile and machine-readable interpretation guardrails.
prod = next(
    (profile for profile in profiles.get("profiles", []) if profile.get("id") == "tl1-production"),
    {},
)
ok(prod.get("powerAndControl", {}).get("reactorOutput") == 5, "production reactor unchanged at 5")
ok(baseline.get("checkpoint") == 64, "baseline checkpoint")
ok(baseline.get("installationSpace", {}).get("playerCruiserTotal") == 35, "35 Space baseline")
ok(baseline.get("installationSpace", {}).get("mandatoryCoreTotal") == 25, "25 Space mandatory core")
accepted63 = baseline.get("acceptedCheckpoint63bInterpretation", {})
ok(accepted63.get("status") == "accepted", "CP63b accepted interpretation retained")
ok(accepted63.get("productionReactorOutput") == 5, "CP63b production reactor retained")
ok(accepted63.get("offensiveIsolationDoctrine") == "FullVolleyFirst", "CP63b doctrine retained")
track_study = baseline.get("trackAwareMovementAcquisitionStudy", {})
ok(track_study.get("variantCount") == 90, "baseline CP64 variant count")
ok(track_study.get("productionReactorOutput") == 5, "baseline CP64 production reactor")
ok(track_study.get("tacticalPowerDoctrine") == "FullVolleyFirst", "baseline CP64 doctrine")
ok(track_study.get("balanceTargetsBlocking") is False, "baseline no target balance gate")
ok("equal-or-faster" in track_study.get("standoffRule", ""), "baseline valid standoff rule")
ok("Energy APEN" in track_study.get("latentCapabilityRule", ""), "baseline latent APEN rule")

# Schema v0.10 must validate the new study and expose the new opt-in controls.
try:
    jsonschema.Draft202012Validator(schema).validate(study)
    ok(True, "study validates against schema v0.10")
except Exception as exc:
    ok(False, f"schema validation failed: {exc}")
props = schema.get("$defs", {}).get("variant", {}).get("properties", {})
ok(
    props.get("movementMode", {}).get("enum")
    == [
        "HoldRange2", "HoldRange3", "HoldRange4", "HoldRange5",
        "ScriptedPursuit", "PreferredRange", "OpponentAwareRange",
        "TrackAwareOpponentRange",
    ],
    "schema movement enum exact",
)
ok(
    props.get("sideATrackPolicy", {}).get("enum")
    == ["EstablishedFirm", "PassiveOnly", "AutoActive", "AcquisitionFirstAutoActive"],
    "schema Side A track enum exact",
)
ok(
    props.get("sideBTrackPolicy", {}).get("enum")
    == ["EstablishedFirm", "PassiveOnly", "AutoActive", "AcquisitionFirstAutoActive"],
    "schema Side B track enum exact",
)
for key in [
    "sideANetEwRangePenalty", "sideBNetEwRangePenalty",
    "sideATacticalPowerDoctrine", "sideBTacticalPowerDoctrine",
    "sideAReactorOutputOverride", "sideBReactorOutputOverride",
]:
    ok(key in props, f"schema field {key}")

# Accepted Checkpoint 63 historical contracts must remain byte-stable. These
# hashes are from the accepted Checkpoint 63b full-repository baseline.
historical_hashes = {
    "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_9.json":
        "064750fedd1aa84c62ea03c6c7386b4352ed43f5eae402e27a303cc1ce9967e5",
    "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_5.json":
        "9907db1281bf71a67539037a5719f4c6cd39f4c95165eebfed1241189e0464b5",
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc06-35-space-operational-sensor-acquisition-ew.json":
        "863399db046d6e1c396cb977657d68825c538295049c56ade5b2ab64a1b86c64",
}
for rel, expected_hash in historical_hashes.items():
    ok(sha256(rel) == expected_hash, f"accepted CP63b historical file unchanged: {rel}")
ok(historical_study.get("id") == "tl1-itc06-35-space-operational-sensor-acquisition-ew", "historical CP63 study identity")
ok(len(historical_study.get("variants", [])) == 72, "historical CP63 variant count")

# Validation tiers and workload sizes.
ok(active.get("checkpointMetrics", {}).get("stageCount") == 8, "active stages")
ok(active.get("checkpointMetrics", {}).get("monteCarloVariantCount") == 90, "active variants")
ok(active.get("checkpointMetrics", {}).get("trialsAtDefault") == 900000, "active trials")
ok(deep.get("checkpointMetrics", {}).get("stageCount") == 23, "deep stages")
ok(deep.get("checkpointMetrics", {}).get("monteCarloVariantCount") == 1350, "deep variants")
ok(deep.get("checkpointMetrics", {}).get("trialsAtDefault") == 13500000, "deep trials")
active_ids = [stage.get("id") for stage in active.get("stages", [])]
deep_ids = [stage.get("id") for stage in deep.get("stages", [])]
ok(len(active_ids) == 8 and active_ids[3:5] == ["tl1-installation-space-envelope", "tl1-track-aware-movement-acquisition"], "active study order")
ok(
    len(deep_ids) == 23
    and deep_ids[4:8] == [
        "tl1-track-aware-movement-acquisition",
        "tl1-operational-sensor-acquisition-ew",
        "tl1-power-doctrine-reactor-sensitivity",
        "tl1-composed-ship-odd-build-combat",
    ],
    "deep current/historical order",
)
must = policy.get("mustAlwaysRunStageIds", [])
deep_only = policy.get("deepCalibrationStageIds", [])
ok(len(must) == 8 and "tl1-track-aware-movement-acquisition" in must, "policy current study active")
ok("tl1-operational-sensor-acquisition-ew" not in must, "CP63 retired from active normal suite")
ok(
    len(deep_only) == 15
    and deep_only[0] == "tl1-operational-sensor-acquisition-ew"
    and "tl1-power-doctrine-reactor-sensitivity" in deep_only
    and "tl1-composed-ship-odd-build-combat" in deep_only,
    "policy deep historical studies",
)
notes = policy.get("notes", {})
ok(notes.get("activeMonteCarloVariants") == 90, "policy active variants")
ok(notes.get("deepMonteCarloVariants") == 1350, "policy deep variants")
ok(notes.get("productionReactorOutput") == 5, "policy production reactor")
ok(notes.get("powerDoctrine") == "FullVolleyFirst", "policy doctrine")
ok(notes.get("balanceTargetsBlocking") is False, "policy no balance targets")
ok(notes.get("deepCalibrationRequiredForCheckpoint64Acceptance") is False, "deep not required")

# Implementation tokens and source-shape smoke checks. This cannot replace a
# native .NET compile, but it catches enum/switch wiring and common generator
# mistakes before handoff.
runner_path = ROOT / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs"
docs_path = ROOT / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs"
runner = runner_path.read_text(encoding="utf-8")
docs = docs_path.read_text(encoding="utf-8")
for token in [
    "Tl1TrackAwareAcquisitionStudyId",
    "RequiredTl1TrackAwareAcquisitionVariantCount",
    "TrackAwareDoctrineFor",
    "MaximumFirmRangeForMovementPlan",
    "Tl1IntegratedMovementMode.TrackAwareOpponentRange",
    "Tl1OperationalTrackPolicy.AcquisitionFirstAutoActive",
    "side.Power.SpendablePower",
    "WriteTl1TrackAwareAcquisitionReview",
    "track-aware-acquisition-matrix.csv",
    "track-aware-acquisition-paired-review.csv",
    "tl1-c64-track-aware-coverage",
    "tl1-c64-production-controls-preserved",
    "tl1-c64-acquisition-first-active-sensor-exercised",
    "tl1-c64-sensorless-never-fakes-active-power",
    "tl1-c64-track-aware-response-observed",
    "sensorless ships are not required to defeat equal-speed standoff",
    "tl1-c64-opponent-firm-control",
    "tl1-c64-standoff-remains-valid",
    "tl1-c64-outcomes-review-only",
]:
    ok(token in runner, f"runner token {token}")
for token in [
    "TrackAwareOpponentRange",
    "AcquisitionFirstAutoActive",
    "sideATrackPolicy",
    "sideBTrackPolicy",
    "sideANetEwRangePenalty",
    "sideBNetEwRangePenalty",
]:
    ok(token in docs, f"document model token {token}")
ok("Tl1OperationalTrackPolicy.EstablishedFirm" in docs, "historical track default remains EstablishedFirm")

# Ensure historical CP63 coverage logic was not accidentally expanded by the
# new enum. It should explicitly retain only the three legacy policy values.
legacy_policy_snippet = re.search(
    r"legacyTrackPolicies\s*=\s*new\[\]\s*\{(?P<body>.*?)\};",
    runner,
    re.S,
)
if legacy_policy_snippet:
    body = legacy_policy_snippet.group("body")
    ok("EstablishedFirm" in body and "PassiveOnly" in body and "AutoActive" in body, "CP63 legacy policies retained")
    ok("AcquisitionFirstAutoActive" not in body, "CP64 policy excluded from CP63 historical matrix")
else:
    # Source may use a differently named inline array; verify the exact explicit
    # legacy tuple markers instead of requiring one spelling.
    ok(
        "Tl1OperationalTrackPolicy.EstablishedFirm" in runner
        and "Tl1OperationalTrackPolicy.PassiveOnly" in runner
        and "Tl1OperationalTrackPolicy.AutoActive" in runner,
        "legacy track-policy source markers retained",
    )

for text, name in [(runner, "runner"), (docs, "documents")]:
    ok(text.count("{") == text.count("}"), f"{name} brace count")
    ok(text.count("(") == text.count(")"), f"{name} paren count")
    ok(text.count("[") == text.count("]"), f"{name} bracket count")

# Summary constructor/record shape and CSV output field count. These are useful
# compile-adjacent checks because the integrated summary is intentionally wide.
record_match = re.search(
    r"public sealed record Tl1IntegratedTacticalCombatVariantSummary\((?P<body>.*?)\)\s*;",
    runner,
    re.S,
)
ctor_match = re.search(
    r"return new Tl1IntegratedTacticalCombatVariantSummary\((?P<body>.*?)\);",
    runner,
    re.S,
)
if record_match and ctor_match:
    record_body = record_match.group("body")
    ctor_body = ctor_match.group("body")
    record_count = count_top_level_items(record_body)
    ctor_count = count_top_level_items(ctor_body)
    ok(record_count == ctor_count, f"summary record/constructor argument parity {record_count}/{ctor_count}")
    ok(record_count >= 100, "summary record remains wide telemetry contract")
else:
    ok(False, "could not locate integrated summary record/constructor")

# Documentation guardrails.
for rel in [
    "README.md",
    "docs/README.md",
    "docs/Prototype_TODO.md",
    "docs/design/player_technology/TL1_35_Space_Track_Aware_Movement_And_Acquisition_Study_v0_1.md",
    "docs/validation/Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md",
]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    ok(("5 TP" in text or "5-TP" in text or "5 Tactical Power" in text), f"5 TP documented {rel}")
    ok("FullVolleyFirst" in text, f"FullVolleyFirst documented {rel}")
    ok("target win" in text.lower() or "win-rate target" in text.lower(), f"no target-win doctrine documented {rel}")

study_doc = (ROOT / "docs/design/player_technology/TL1_35_Space_Track_Aware_Movement_And_Acquisition_Study_v0_1.md").read_text(encoding="utf-8")
ok("TrackAwareOpponentRange" in study_doc, "track-aware movement documented")
ok("AcquisitionFirstAutoActive" in study_doc, "acquisition-first sensing documented")
ok("equal-or-faster" in study_doc and "standoff" in study_doc.lower(), "valid standoff documented")
ok("APEN" in study_doc, "latent APEN documented")

# Packaging hygiene and active runbook status.
root_txt = sorted(path.name for path in ROOT.glob("*.txt"))
ok(root_txt == ["CHECKPOINT_64_SHA256SUMS.txt"], f"root txt hygiene {root_txt}")
archive_txt = list((ROOT / "docs/archive").rglob("*.txt"))
ok(not archive_txt, f"docs/archive txt hygiene: {[str(p.relative_to(ROOT)) for p in archive_txt[:5]]}")
active_runbooks = list((ROOT / "docs/validation").glob("*.md"))
ok(
    len(active_runbooks) == 1
    and active_runbooks[0].name == "Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md",
    "single active validation runbook",
)
ok(
    (ROOT / "docs/validation/archive/Checkpoint_63b_Manifest_Binding_Hotfix.md").is_file(),
    "accepted CP63b runbook archived",
)
apply_script = (ROOT / "tools/checkpoints/checkpoint-64/apply_checkpoint_64.ps1").read_text(encoding="utf-8")
ok("Checkpoint_*.md" in apply_script and "Checkpoint_64_TL1_Track_Aware_Movement_And_Acquisition.md" in apply_script, "overlay-safe active runbook cleanup")
ok("CHECKPOINT_(?!64" in apply_script, "overlay-safe stale manifest cleanup")

# Manifest format and independent content verification. The manifest excludes
# itself; the final archive should therefore contain exactly one additional
# entry beyond this list.
manifest = ROOT / "CHECKPOINT_64_SHA256SUMS.txt"
if manifest.is_file():
    entries = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        ok(bool(match), f"manifest line format {line[:100]}")
        if match:
            entries.append((match.group(1), match.group(2)))
    ok(len(entries) > 1000, "manifest substantial")
    paths = [rel for _, rel in entries]
    ok(len(paths) == len(set(paths)), "manifest paths unique")
    ok("CHECKPOINT_64_SHA256SUMS.txt" not in paths, "manifest excludes itself")
    for digest, rel in entries:
        path = ROOT / rel
        ok(path.is_file(), f"manifest file exists {rel}")
        if path.is_file():
            ok(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"manifest hash {rel}")

print(f"Checkpoint 64 static preflight: {checks - len(errors)}/{checks} checks passed.")
if errors:
    for error in errors[:120]:
        print("FAIL:", error)
    sys.exit(1)
