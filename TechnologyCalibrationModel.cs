using System.Text.Json;

namespace StarCluster.ScenarioRunner;

public sealed record PreparedTechnologyCalibrationVariant(
    string Id,
    RepresentativeMissileProfileDocument Profile,
    TechnologyLevelCalibrationDocument MissileTechnology,
    int PdsTechnologyLevel,
    TechnologyLevelCalibrationDocument TargetEcmTechnology,
    int PdsInterceptionChancePercent,
    int EffectiveAttackChancePercent,
    double AcquisitionSuccessProbability,
    double ExpectedTerminalEntryInterception,
    double ExpectedPreTerminalAttackInterception,
    double ExpectedAttackResolution,
    double ExpectedEffectiveHit,
    ScenarioDocument Scenario);

public static class TechnologyCalibrationModel
{
    public static IReadOnlyList<PreparedTechnologyCalibrationVariant> PrepareVariants(
        TechnologyCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        ScenarioDocument baseScenario)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(catalog);
        ArgumentNullException.ThrowIfNull(baseScenario);
        Validate(study, catalog, baseScenario);

        IReadOnlyDictionary<string, RepresentativeMissileProfileDocument> profiles =
            catalog.MissileProfiles.ToDictionary(item => item.Id, StringComparer.Ordinal);
        IReadOnlyDictionary<int, TechnologyLevelCalibrationDocument> technology =
            catalog.TechnologyLevels.ToDictionary(item => item.TechnologyLevel);
        var variants = new List<PreparedTechnologyCalibrationVariant>();

        foreach (string profileId in study.MissileProfiles)
        {
            RepresentativeMissileProfileDocument profile = profiles[profileId];
            foreach (int missileTl in study.MissileTechnologyLevels)
            {
                TechnologyLevelCalibrationDocument missileTechnology = technology[missileTl];
                foreach (int pdsTl in study.PdsTechnologyLevels)
                {
                    int pdsChance = CalculatePdsInterceptionChancePercent(
                        catalog.Pds,
                        pdsTl,
                        missileTl);
                    foreach (int ecmTl in study.TargetEcmTechnologyLevels)
                    {
                        TechnologyLevelCalibrationDocument targetEcmTechnology = technology[ecmTl];
                        string variantId = CreateVariantId(profileId, missileTl, pdsTl, ecmTl);
                        ScenarioDocument scenario = MaterializeScenario(
                            baseScenario,
                            variantId,
                            profile,
                            missileTechnology,
                            pdsTl,
                            targetEcmTechnology,
                            pdsChance,
                            catalog);
                        int effectiveAttackChance = Math.Clamp(
                            missileTechnology.GuidanceBaseHitChancePercent +
                            (profile.SeekerInstalled
                                ? missileTechnology.SeekerAccuracyBonusPercent
                                : 0),
                            catalog.MinimumHitChancePercent,
                            catalog.MaximumHitChancePercent);
                        double acquisitionSuccess = CalculateAcquisitionSuccessProbability(
                            profile,
                            missileTechnology,
                            targetEcmTechnology,
                            catalog);
                        double pds = pdsChance / 100.0;
                        double entry = pds;
                        double preAttack = (1.0 - pds) * acquisitionSuccess * pds;
                        double attackResolution =
                            (1.0 - pds) * acquisitionSuccess * (1.0 - pds);
                        double effectiveHit =
                            attackResolution * (effectiveAttackChance / 100.0);

                        variants.Add(new PreparedTechnologyCalibrationVariant(
                            variantId,
                            profile,
                            missileTechnology,
                            pdsTl,
                            targetEcmTechnology,
                            pdsChance,
                            effectiveAttackChance,
                            acquisitionSuccess,
                            entry,
                            preAttack,
                            attackResolution,
                            effectiveHit,
                            scenario));
                    }
                }
            }
        }

        return variants
            .OrderBy(item => item.Id, StringComparer.Ordinal)
            .ToArray();
    }

    public static int CalculatePdsInterceptionChancePercent(
        PdsTechnologyCalibrationDocument calibration,
        int pdsTechnologyLevel,
        int missileTechnologyLevel)
    {
        ArgumentNullException.ThrowIfNull(calibration);
        int raw = checked(
            calibration.EqualTechnologyInterceptionChancePercent +
            ((pdsTechnologyLevel - missileTechnologyLevel) *
             calibration.InterceptionChancePercentPerTechnologyDelta));
        return Math.Clamp(
            raw,
            calibration.MinimumInterceptionChancePercent,
            calibration.MaximumInterceptionChancePercent);
    }

    public static double CalculateAcquisitionSuccessProbability(
        RepresentativeMissileProfileDocument profile,
        TechnologyLevelCalibrationDocument missileTechnology,
        TechnologyLevelCalibrationDocument targetEcmTechnology,
        TechnologyProfileCatalogDocument catalog)
    {
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(missileTechnology);
        ArgumentNullException.ThrowIfNull(targetEcmTechnology);
        ArgumentNullException.ThrowIfNull(catalog);

        if (!profile.SeekerInstalled || profile.SensorInstalled)
        {
            return 1.0;
        }

        int netEcm = Math.Max(
            0,
            targetEcmTechnology.TerminalEcmStrength -
            missileTechnology.SeekerEccmStrength);
        int raw = checked(
            missileTechnology.SeekerBaseAcquisitionChancePercent -
            (netEcm * catalog.AcquisitionPenaltyPercentPerNetEcmStrength));
        int chance = Math.Clamp(
            raw,
            catalog.MinimumAcquisitionChancePercent,
            catalog.MaximumAcquisitionChancePercent);
        return chance / 100.0;
    }

    public static string CreateVariantId(
        string profileId,
        int missileTechnologyLevel,
        int pdsTechnologyLevel,
        int targetEcmTechnologyLevel) =>
        $"{profileId}-m{missileTechnologyLevel}-p{pdsTechnologyLevel}-e{targetEcmTechnologyLevel}";

    public static void Validate(
        TechnologyCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        ScenarioDocument baseScenario)
    {
        if (study.SchemaVersion != 1)
        {
            throw new InvalidOperationException(
                $"Unsupported calibration study schema version {study.SchemaVersion}; expected 1.");
        }
        if (catalog.SchemaVersion != 1)
        {
            throw new InvalidOperationException(
                $"Unsupported calibration catalog schema version {catalog.SchemaVersion}; expected 1.");
        }
        if (string.IsNullOrWhiteSpace(study.Id) || string.IsNullOrWhiteSpace(catalog.Id))
        {
            throw new InvalidOperationException(
                "Calibration study and profile catalog require stable IDs.");
        }
        if (string.IsNullOrWhiteSpace(study.BaseScenario) ||
            string.IsNullOrWhiteSpace(study.ProfileCatalog))
        {
            throw new InvalidOperationException(
                "Calibration study requires baseScenario and profileCatalog paths.");
        }
        if (study.TrialsPerVariant <= 0)
        {
            throw new InvalidOperationException("trialsPerVariant must be positive.");
        }
        if (study.MaximumAbsoluteError is < 0.0 or > 1.0)
        {
            throw new InvalidOperationException(
                "maximumAbsoluteError must be from 0 through 1.");
        }
        if (study.MinimumPracticalMarginalDelta is < 0.0 or > 1.0)
        {
            throw new InvalidOperationException(
                "minimumPracticalMarginalDelta must be from 0 through 1.");
        }
        if (study.MarginalFamilywiseAlpha is <= 0.0 or >= 1.0)
        {
            throw new InvalidOperationException(
                "marginalFamilywiseAlpha must be greater than 0 and less than 1.");
        }
        if (study.MissileProfiles.Count == 0 ||
            study.MissileTechnologyLevels.Count == 0 ||
            study.PdsTechnologyLevels.Count == 0 ||
            study.TargetEcmTechnologyLevels.Count == 0)
        {
            throw new InvalidOperationException(
                "Calibration study axes cannot be empty.");
        }
        RequireUniqueAxis(study.MissileProfiles, "missileProfiles", StringComparer.Ordinal);
        RequireUniqueAxis(study.MissileTechnologyLevels, "missileTechnologyLevels");
        RequireUniqueAxis(study.PdsTechnologyLevels, "pdsTechnologyLevels");
        RequireUniqueAxis(study.TargetEcmTechnologyLevels, "targetEcmTechnologyLevels");
        if (baseScenario.Missiles.Count != 1 || baseScenario.Defenses.Count != 1)
        {
            throw new InvalidOperationException(
                "Checkpoint 20 calibration requires exactly one Missile Flight and one standard PDS definition.");
        }
        if (catalog.ControlSensorFirmRange <= 0 ||
            catalog.ControlSensorApproximateRange < catalog.ControlSensorFirmRange)
        {
            throw new InvalidOperationException(
                "Calibration control sensor ranges are invalid.");
        }
        if (catalog.MinimumHitChancePercent < 0 ||
            catalog.MaximumHitChancePercent > 100 ||
            catalog.MinimumHitChancePercent > catalog.MaximumHitChancePercent ||
            catalog.MinimumAcquisitionChancePercent < 0 ||
            catalog.MaximumAcquisitionChancePercent > 100 ||
            catalog.MinimumAcquisitionChancePercent > catalog.MaximumAcquisitionChancePercent)
        {
            throw new InvalidOperationException(
                "Calibration hit/acquisition bounds are invalid.");
        }
        if (catalog.AcquisitionPenaltyPercentPerNetEcmStrength < 0)
        {
            throw new InvalidOperationException(
                "Acquisition penalty per net ECM strength cannot be negative.");
        }

        string[] duplicateProfiles = catalog.MissileProfiles
            .GroupBy(item => item.Id, StringComparer.Ordinal)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();
        if (catalog.MissileProfiles.Any(item => string.IsNullOrWhiteSpace(item.Id)))
        {
            throw new InvalidOperationException(
                "Calibration profile IDs cannot be empty.");
        }
        if (duplicateProfiles.Length > 0)
        {
            throw new InvalidOperationException(
                "Calibration profile IDs must be unique: " +
                string.Join(", ", duplicateProfiles));
        }
        int[] duplicateTechnology = catalog.TechnologyLevels
            .GroupBy(item => item.TechnologyLevel)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();
        if (duplicateTechnology.Length > 0)
        {
            throw new InvalidOperationException(
                "Calibration technology levels must be unique: " +
                string.Join(", ", duplicateTechnology));
        }

        IReadOnlyDictionary<string, RepresentativeMissileProfileDocument> profiles =
            catalog.MissileProfiles.ToDictionary(item => item.Id, StringComparer.Ordinal);
        foreach (string profileId in study.MissileProfiles.Distinct(StringComparer.Ordinal))
        {
            if (!profiles.ContainsKey(profileId))
            {
                throw new InvalidOperationException(
                    $"Calibration profile '{profileId}' was not found in catalog '{catalog.Id}'.");
            }
        }
        IReadOnlyDictionary<int, TechnologyLevelCalibrationDocument> technology =
            catalog.TechnologyLevels.ToDictionary(item => item.TechnologyLevel);
        foreach (int level in study.MissileTechnologyLevels
                     .Concat(study.PdsTechnologyLevels)
                     .Concat(study.TargetEcmTechnologyLevels)
                     .Distinct())
        {
            if (!technology.ContainsKey(level))
            {
                throw new InvalidOperationException(
                    $"Calibration technology level {level} was not found in catalog '{catalog.Id}'.");
            }
        }

        foreach (TechnologyLevelCalibrationDocument level in catalog.TechnologyLevels)
        {
            ValidateTechnologyLevel(level);
        }
        ValidatePds(catalog.Pds);
    }

    private static ScenarioDocument MaterializeScenario(
        ScenarioDocument baseScenario,
        string variantId,
        RepresentativeMissileProfileDocument profile,
        TechnologyLevelCalibrationDocument missileTechnology,
        int pdsTechnologyLevel,
        TechnologyLevelCalibrationDocument targetEcmTechnology,
        int pdsChance,
        TechnologyProfileCatalogDocument catalog)
    {
        ScenarioDocument scenario = Clone(baseScenario);
        scenario.Id = variantId;
        scenario.Name =
            $"{profile.Name}: missile TL {missileTechnology.TechnologyLevel}, " +
            $"PDS TL {pdsTechnologyLevel}, target ECM TL {targetEcmTechnology.TechnologyLevel}";
        scenario.Description =
            "Checkpoint 20 representative-profile terminal calibration variant.";

        MissileDocument missile = scenario.Missiles.Single();
        missile.Flight.TechnologyLevel = missileTechnology.TechnologyLevel;
        missile.Flight.Speed = missileTechnology.FlightSpeedHexesPerTurn;
        missile.Flight.MaximumRange = missileTechnology.MaximumRangeHexes;
        missile.Datalink.TechnologyLevel = missileTechnology.TechnologyLevel;
        missile.Datalink.IsInstalled = profile.DatalinkInstalled;
        missile.Datalink.MaximumRetainedReportAgePhases =
            missileTechnology.DatalinkRetainedReportAgePhases;
        missile.Sensor.TechnologyLevel = missileTechnology.TechnologyLevel;
        missile.Sensor.IsInstalled = profile.SensorInstalled;
        missile.Sensor.FirmRange = missileTechnology.SensorFirmRangeHexes;
        missile.Sensor.ApproximateRange = missileTechnology.SensorApproximateRangeHexes;
        missile.Sensor.ActiveModeBonus = missileTechnology.SensorActiveModeBonusHexes;
        missile.Sensor.MaximumLocalTrackAgeEpochs =
            missileTechnology.SensorMaximumLocalTrackAgeEpochs;
        missile.Terminal.GuidanceComputer.TechnologyLevel =
            missileTechnology.TechnologyLevel;
        missile.Terminal.GuidanceComputer.BaseHitChance =
            missileTechnology.GuidanceBaseHitChancePercent;
        missile.Terminal.GuidanceComputer.MinimumHitChance =
            catalog.MinimumHitChancePercent;
        missile.Terminal.GuidanceComputer.MaximumHitChance =
            catalog.MaximumHitChancePercent;
        missile.Terminal.Seeker.TechnologyLevel = missileTechnology.TechnologyLevel;
        missile.Terminal.Seeker.IsInstalled = profile.SeekerInstalled;
        missile.Terminal.Seeker.BaseAcquisitionChance =
            missileTechnology.SeekerBaseAcquisitionChancePercent;
        missile.Terminal.Seeker.TerminalEccmStrength =
            missileTechnology.SeekerEccmStrength;
        missile.Terminal.Seeker.AccuracyBonus =
            missileTechnology.SeekerAccuracyBonusPercent;
        missile.Terminal.Seeker.MinimumAcquisitionChance =
            catalog.MinimumAcquisitionChancePercent;
        missile.Terminal.Seeker.MaximumAcquisitionChance =
            catalog.MaximumAcquisitionChancePercent;
        missile.Terminal.AcquisitionPenaltyPerNetEcm =
            catalog.AcquisitionPenaltyPercentPerNetEcmStrength;

        DefenseDocument defense = scenario.Defenses.Single();
        defense.TechnologyLevel = pdsTechnologyLevel;
        defense.Range = catalog.Pds.RangeHexes;
        defense.MaximumAttemptsPerPhase = catalog.Pds.MaximumAttemptsPerPhase;
        defense.InterceptionChancePercent = pdsChance;

        ShipDocument target = scenario.Ships.Single(item =>
            string.Equals(item.Id, missile.TargetId, StringComparison.Ordinal));
        target.ElectronicWarfare.TechnologyLevel =
            targetEcmTechnology.TechnologyLevel;
        target.ElectronicWarfare.JammingRangePenalty =
            targetEcmTechnology.TerminalEcmStrength;
        target.ElectronicWarfare.CounterJammingStrength = 0;
        target.JammingEnabled = true;

        foreach (ShipDocument ship in scenario.Ships)
        {
            ship.Sensor.FirmRange = Math.Max(
                ship.Sensor.FirmRange,
                catalog.ControlSensorFirmRange);
            ship.Sensor.ApproximateRange = Math.Max(
                ship.Sensor.ApproximateRange,
                catalog.ControlSensorApproximateRange);
        }

        IReadOnlyList<string> failures = ScenarioPreflightValidator.Validate(scenario);
        if (failures.Count > 0)
        {
            throw new InvalidOperationException(
                $"Calibration variant '{variantId}' scenario preflight failed: " +
                string.Join("; ", failures));
        }
        return scenario;
    }

    private static ScenarioDocument Clone(ScenarioDocument source)
    {
        string json = ScenarioDocumentSerialization.SerializeCanonical(source);
        return JsonSerializer.Deserialize<ScenarioDocument>(
            json,
            ScenarioDocumentSerialization.ReadOptions) ??
            throw new InvalidOperationException("Could not clone calibration base scenario.");
    }

    private static void ValidateTechnologyLevel(TechnologyLevelCalibrationDocument level)
    {
        if (level.TechnologyLevel is < 1 or > 9)
        {
            throw new InvalidOperationException(
                $"Technology level {level.TechnologyLevel} must be from 1 through 9.");
        }
        if (level.FlightSpeedHexesPerTurn <= 0 ||
            level.ShipMovementHexesPerTurn <= 0 ||
            level.MaximumRangeHexes <= 0 ||
            level.DatalinkRetainedReportAgePhases < 0 ||
            level.SensorFirmRangeHexes < 0 ||
            level.SensorApproximateRangeHexes < level.SensorFirmRangeHexes ||
            level.SensorActiveModeBonusHexes < 0 ||
            level.SensorMaximumLocalTrackAgeEpochs < 0 ||
            level.TerminalEcmStrength < 0)
        {
            throw new InvalidOperationException(
                $"Technology level {level.TechnologyLevel} contains invalid non-percentage values.");
        }
        foreach (int value in new[]
                 {
                     level.GuidanceBaseHitChancePercent,
                     level.SeekerBaseAcquisitionChancePercent,
                     level.SeekerAccuracyBonusPercent,
                 })
        {
            if (value is < 0 or > 100)
            {
                throw new InvalidOperationException(
                    $"Technology level {level.TechnologyLevel} contains a percentage outside 0 through 100.");
            }
        }
        if (level.SeekerEccmStrength < 0)
        {
            throw new InvalidOperationException(
                $"Technology level {level.TechnologyLevel} seeker ECCM cannot be negative.");
        }
    }

    private static void ValidatePds(PdsTechnologyCalibrationDocument pds)
    {
        if (pds.EqualTechnologyInterceptionChancePercent is < 0 or > 100 ||
            pds.InterceptionChancePercentPerTechnologyDelta < 0 ||
            pds.MinimumInterceptionChancePercent is < 0 or > 100 ||
            pds.MaximumInterceptionChancePercent is < 0 or > 100 ||
            pds.MinimumInterceptionChancePercent > pds.MaximumInterceptionChancePercent ||
            pds.EqualTechnologyInterceptionChancePercent < pds.MinimumInterceptionChancePercent ||
            pds.EqualTechnologyInterceptionChancePercent > pds.MaximumInterceptionChancePercent ||
            pds.RangeHexes < 0 ||
            pds.MaximumAttemptsPerPhase <= 0)
        {
            throw new InvalidOperationException("PDS calibration values are invalid.");
        }
    }

    private static void RequireUniqueAxis<T>(
        IReadOnlyCollection<T> values,
        string axisName,
        IEqualityComparer<T>? comparer = null)
    {
        comparer ??= EqualityComparer<T>.Default;
        T[] duplicates = values
            .GroupBy(value => value, comparer)
            .Where(group => group.Count() > 1)
            .Select(group => group.Key)
            .ToArray();
        if (duplicates.Length > 0)
        {
            throw new InvalidOperationException(
                $"Calibration study axis '{axisName}' contains duplicate value(s): " +
                string.Join(", ", duplicates));
        }
    }
}
