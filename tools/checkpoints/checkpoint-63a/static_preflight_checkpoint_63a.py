from pathlib import Path
import hashlib
import json
import re
import sys

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


required = [
    "README.md",
    "docs/README.md",
    "docs/Prototype_TODO.md",
    "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_5.json",
    "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_9.json",
    "docs/design/player_technology/TL1_35_Space_Operational_Sensor_Acquisition_And_EW_Study_v0_1.md",
    "docs/design/testing/checkpoint_63_validation_suite_policy_v0_1.json",
    "docs/design/testing/Checkpoint_63_Validation_Tiers.md",
    "docs/validation/Checkpoint_63a_Passive_Core_Gate_Hotfix.md",
    "docs/validation/archive/Checkpoint_63_TL1_Operational_Sensor_Acquisition_And_EW.md",
    "docs/validation/archive/Checkpoint_62_TL1_Tactical_Power_Doctrine_And_Reactor_Output_Sensitivity.md",
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/tl1-itc06-35-space-operational-sensor-acquisition-ew.json",
    "tools/calibration/checkpoints/checkpoint-63.json",
    "tools/calibration/checkpoints/checkpoint-63-deep-calibration.json",
    "tools/checkpoints/checkpoint-63a/apply_checkpoint_63a.ps1",
    "tools/checkpoints/checkpoint-63a/test_checkpoint_63a_contract.ps1",
    "tools/checkpoints/checkpoint-63a/static_preflight_checkpoint_63a.py",
    "CHECKPOINT_63A_SHA256SUMS.txt",
]
for rel in required:
    ok((ROOT / rel).is_file(), f"missing required path {rel}")

study = load(
    "src/StarCluster.ScenarioRunner/Scenarios/TL1Calibration/"
    "tl1-itc06-35-space-operational-sensor-acquisition-ew.json"
)
baseline = load(
    "docs/design/player_technology/tl1_35_space_player_cruiser_baseline_v0_5.json"
)
profiles = load(
    "src/StarCluster.ScenarioRunner/Scenarios/ArchitectureTechnology/"
    "tl1-tl2-standard-runtime-profiles-v0_3.json"
)
policy = load("docs/design/testing/checkpoint_63_validation_suite_policy_v0_1.json")
active = load("tools/calibration/checkpoints/checkpoint-63.json")
deep = load("tools/calibration/checkpoints/checkpoint-63-deep-calibration.json")
schema = load(
    "docs/design/player_technology/tl1_integrated_tactical_combat_schema_v0_9.json"
)

# Study identity, frozen construction envelope, and paired matrix.
ok(study.get("id") == "tl1-itc06-35-space-operational-sensor-acquisition-ew", "study id")
ok(len(study.get("builds", [])) == 6, "build count")
ok(len(study.get("variants", [])) == 72, "variant count")
ids = [variant.get("id") for variant in study.get("variants", [])]
ok(len(ids) == len(set(ids)) == 72, "variant ids unique")

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
    calculated = (
        25
        + 5 * int(build.get("mainWeaponCount", 0))
        + 6 * int(build.get("mainReactorCount", 0))
        + (3 if build.get("activeSensor") else 0)
        + (3 if build.get("shieldGenerator") else 0)
        + 2 * int(build.get("kineticPdsCount", 0))
    )
    # Mandatory 25 includes one weapon and one reactor; count only extras here.
    calculated = (
        25
        + 6 * max(0, int(build.get("mainWeaponCount", 0)) - 1)
        + 6 * max(0, int(build.get("mainReactorCount", 0)) - 1)
        + (3 if build.get("activeSensor") else 0)
        + (3 if build.get("shieldGenerator") else 0)
        + 2 * int(build.get("kineticPdsCount", 0))
    )
    ok(calculated == build.get("usedSpace"), f"computed space {build_id}")
    ok(35 - calculated == build.get("freeSupportSpace"), f"free space {build_id}")

regimes = {
    "established-firm-control": ("EstablishedFirm", 0),
    "operational-passive-clear": ("PassiveOnly", 0),
    "operational-auto-active-clear": ("AutoActive", 0),
    "operational-auto-active-ew1": ("AutoActive", 1),
}
families = ["Kinetic", "Energy", "Missile"]
for build_id, expected in expected_builds.items():
    main_count = expected[0]
    for family in families:
        lane = [
            variant
            for variant in study.get("variants", [])
            if variant.get("sideABuildId") == build_id
            and variant.get("sideAFamily") == family
        ]
        ok(len(lane) == 4, f"paired lane count {build_id}/{family}")
        ok(
            len({variant.get("comparisonGroup") for variant in lane}) == 1,
            f"paired comparison group {build_id}/{family}",
        )
        actual_regimes = {
            (
                variant.get("profileLabel"),
                variant.get("sideATrackPolicy"),
                variant.get("sideANetEwRangePenalty"),
            )
            for variant in lane
        }
        expected_regimes = {
            (label, values[0], values[1]) for label, values in regimes.items()
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
                variant.get("movementMode") == "OpponentAwareRange"
                and variant.get("initialRangeHexes") == 4
                for variant in lane
            ),
            f"movement controls {build_id}/{family}",
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

# Production profile and baseline interpretation guardrails.
prod = next(
    (profile for profile in profiles.get("profiles", []) if profile.get("id") == "tl1-production"),
    {},
)
ok(prod.get("powerAndControl", {}).get("reactorOutput") == 5, "production reactor unchanged at 5")
ok(baseline.get("checkpoint") == 63, "baseline checkpoint")
ok(baseline.get("installationSpace", {}).get("playerCruiserTotal") == 35, "35 Space baseline")
sensor_study = baseline.get("operationalSensorAcquisitionStudy", {})
ok(sensor_study.get("variantCount") == 72, "baseline sensor variant count")
ok(sensor_study.get("productionReactorOutput") == 5, "baseline sensor production reactor")
ok(sensor_study.get("tacticalPowerDoctrine") == "FullVolleyFirst", "baseline FullVolleyFirst")
ok(sensor_study.get("balanceTargetsBlocking") is False, "no blocking balance target")
envelope = sensor_study.get("acceptedSensorEnvelope", {})
ok(
    envelope == {
        "passiveFirm": 3,
        "passiveApproximate": 5,
        "active1Power": 1,
        "active1Firm": 5,
        "active1Approximate": 7,
        "active2Power": 2,
        "active2Firm": 6,
        "active2Approximate": 9,
    },
    "accepted sensor envelope",
)
ok("Energy APEN" in sensor_study.get("latentCapabilityRule", ""), "latent APEN guardrail")

# Schema must expose new controls while retaining Checkpoint 62 controls.
props = schema.get("$defs", {}).get("variant", {}).get("properties", {})
for key in [
    "sideATrackPolicy",
    "sideBTrackPolicy",
    "sideANetEwRangePenalty",
    "sideBNetEwRangePenalty",
    "sideATacticalPowerDoctrine",
    "sideBTacticalPowerDoctrine",
    "sideAReactorOutputOverride",
    "sideBReactorOutputOverride",
]:
    ok(key in props, f"schema field {key}")
ok(
    props.get("sideATrackPolicy", {}).get("enum")
    == ["EstablishedFirm", "PassiveOnly", "AutoActive"],
    "schema track enum",
)
ok(
    props.get("sideANetEwRangePenalty", {}).get("minimum") == 0
    and props.get("sideANetEwRangePenalty", {}).get("maximum") == 3,
    "schema EW bounds",
)

# Validation tiers and workload sizes.
ok(active.get("checkpointMetrics", {}).get("stageCount") == 8, "active stages")
ok(active.get("checkpointMetrics", {}).get("monteCarloVariantCount") == 72, "active variants")
ok(active.get("checkpointMetrics", {}).get("trialsAtDefault") == 720000, "active trials")
ok(deep.get("checkpointMetrics", {}).get("stageCount") == 22, "deep stages")
ok(deep.get("checkpointMetrics", {}).get("monteCarloVariantCount") == 1260, "deep variants")
ok(deep.get("checkpointMetrics", {}).get("trialsAtDefault") == 12600000, "deep trials")
active_ids = [stage.get("id") for stage in active.get("stages", [])]
deep_ids = [stage.get("id") for stage in deep.get("stages", [])]
ok(
    active_ids[3:5] == ["tl1-installation-space-envelope", "tl1-operational-sensor-acquisition-ew"],
    "active construction/sensor order",
)
ok(
    deep_ids[4:7]
    == [
        "tl1-operational-sensor-acquisition-ew",
        "tl1-power-doctrine-reactor-sensitivity",
        "tl1-composed-ship-odd-build-combat",
    ],
    "deep current/historical order",
)
must = policy.get("mustAlwaysRunStageIds", [])
deep_only = policy.get("deepCalibrationStageIds", [])
ok(len(must) == 8 and "tl1-operational-sensor-acquisition-ew" in must, "policy active count/current study")
ok("tl1-power-doctrine-reactor-sensitivity" not in must, "CP62 retired from active")
ok(
    len(deep_only) == 14
    and "tl1-power-doctrine-reactor-sensitivity" in deep_only
    and "tl1-composed-ship-odd-build-combat" in deep_only,
    "policy deep-only count/history",
)
notes = policy.get("notes", {})
ok(notes.get("activeMonteCarloVariants") == 72, "policy active variants")
ok(notes.get("deepMonteCarloVariants") == 1260, "policy deep variants")
ok(notes.get("productionReactorOutput") == 5, "policy production reactor")
ok(notes.get("powerDoctrine") == "FullVolleyFirst", "policy doctrine")
ok(notes.get("balanceTargetsBlocking") is False, "policy no balance targets")
ok(notes.get("deepCalibrationRequiredForCheckpoint63Acceptance") is False, "deep not required")

# Implementation tokens and simple source-shape smoke checks.
runner_path = ROOT / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatRunner.cs"
docs_path = ROOT / "src/StarCluster.ScenarioRunner/TL1Calibration/Tl1IntegratedTacticalCombatDocuments.cs"
runner = runner_path.read_text(encoding="utf-8")
docs = docs_path.read_text(encoding="utf-8")
for token in [
    "Tl1OperationalSensorStudyId",
    "RequiredTl1OperationalSensorVariantCount",
    "Tl1SensorEnvelope",
    "SensorTurnState",
    "AllocateOperationalSensor",
    "ResolveTrackQuality",
    "TrackUnavailable",
    "WriteTl1OperationalSensorReview",
    "operational-sensor-acquisition-matrix.csv",
    "operational-sensor-paired-review.csv",
    "tl1-c63-sensorless-auto-passive-parity",
    "A lane may legitimately remain NoTrack",
    "sensorlessBuildIds.All",
    "tl1-c63-outcomes-review-only",
]:
    ok(token in runner, f"runner token {token}")
for token in [
    "Tl1OperationalTrackPolicy",
    "sideATrackPolicy",
    "sideBTrackPolicy",
    "sideANetEwRangePenalty",
    "sideBNetEwRangePenalty",
]:
    ok(token in docs, f"document model token {token}")
ok(
    "Tl1OperationalTrackPolicy.EstablishedFirm" in docs,
    "track policy defaults preserve historical established-Firm behavior",
)
for text, name in [(runner, "runner"), (docs, "documents")]:
    ok(text.count("{") == text.count("}"), f"{name} brace count")
    ok(text.count("(") == text.count(")"), f"{name} paren count")
    ok(text.count("[") == text.count("]"), f"{name} bracket count")

# Documentation guardrails.
for rel in [
    "README.md",
    "docs/README.md",
    "docs/Prototype_TODO.md",
    "docs/design/player_technology/TL1_35_Space_Operational_Sensor_Acquisition_And_EW_Study_v0_1.md",
    "docs/validation/Checkpoint_63a_Passive_Core_Gate_Hotfix.md",
    "docs/validation/archive/Checkpoint_63_TL1_Operational_Sensor_Acquisition_And_EW.md",
]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    ok(("5 TP" in text or "5-TP" in text or "5 Tactical Power" in text), f"5 TP documented {rel}")
    ok("FullVolleyFirst" in text, f"FullVolleyFirst documented {rel}")

study_doc = (ROOT / "docs/design/player_technology/TL1_35_Space_Operational_Sensor_Acquisition_And_EW_Study_v0_1.md").read_text(encoding="utf-8")
ok("passive" in study_doc.lower() and "blind" in study_doc.lower(), "passive-only is not blind documented")
ok("APEN" in study_doc, "latent APEN documented")
ok("target win" in study_doc.lower(), "no target-win doctrine documented")
hotfix_doc = (ROOT / "docs/validation/Checkpoint_63a_Passive_Core_Gate_Hotfix.md").read_text(encoding="utf-8")
ok("out-of-range result" in hotfix_doc.lower() and "not a blind ship" in hotfix_doc.lower(), "CP63a gate correction documented")

# Packaging hygiene and active runbook status.
root_txt = sorted(path.name for path in ROOT.glob("*.txt"))
ok(root_txt == ["CHECKPOINT_63A_SHA256SUMS.txt"], f"root txt hygiene {root_txt}")
archive_txt = list((ROOT / "docs/archive").rglob("*.txt"))
ok(not archive_txt, f"docs/archive txt hygiene: {[str(p.relative_to(ROOT)) for p in archive_txt[:5]]}")
active_runbooks = list((ROOT / "docs/validation").glob("*.md"))
ok(
    len(active_runbooks) == 1
    and active_runbooks[0].name == "Checkpoint_63a_Passive_Core_Gate_Hotfix.md",
    "single active validation runbook",
)
ok(
    (ROOT / "docs/validation/archive/Checkpoint_63_TL1_Operational_Sensor_Acquisition_And_EW.md").is_file(),
    "superseded CP63 runbook archived",
)
ok(
    (ROOT / "docs/validation/archive/Checkpoint_62_TL1_Tactical_Power_Doctrine_And_Reactor_Output_Sensitivity.md").is_file(),
    "CP62 runbook archived",
)
apply_script = (ROOT / "tools/checkpoints/checkpoint-63a/apply_checkpoint_63a.ps1").read_text(encoding="utf-8")
ok("Checkpoint_*.md" in apply_script and "Checkpoint_63a_Passive_Core_Gate_Hotfix.md" in apply_script, "overlay-safe stale active runbook cleanup")

# Manifest format and independent content hash verification.
manifest = ROOT / "CHECKPOINT_63A_SHA256SUMS.txt"
if manifest.is_file():
    entries = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        ok(bool(match), f"manifest line format {line[:100]}")
        if match:
            entries.append((match.group(1), match.group(2)))
    ok(len(entries) > 100, "manifest substantial")
    paths = {rel for _, rel in entries}
    ok("CHECKPOINT_63A_SHA256SUMS.txt" not in paths, "manifest excludes itself")
    for digest, rel in entries:
        path = ROOT / rel
        ok(path.is_file(), f"manifest file exists {rel}")
        if path.is_file():
            ok(hashlib.sha256(path.read_bytes()).hexdigest() == digest, f"manifest hash {rel}")

print(f"Checkpoint 63a static preflight: {checks - len(errors)}/{checks} checks passed.")
if errors:
    for error in errors[:80]:
        print("FAIL:", error)
    sys.exit(1)
