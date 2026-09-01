namespace StarCluster.ScenarioRunner;

public enum FullFlightMapSizingMode
{
    OptimizedVariant,
    ReferenceRadius192,
}

public sealed record PreparedFullFlightCalibrationVariant(
    string Id,
    RepresentativeMissileProfileDocument Profile,
    TechnologyLevelCalibrationDocument MissileTechnology,
    TechnologyLevelCalibrationDocument TargetPropulsionTechnology,
    int FixedPdsTechnologyLevel,
    TechnologyLevelCalibrationDocument TargetEcmTechnology,
    int PdsInterceptionChancePercent,
    int SafetyTurnCap,
    string TargetMovementPolicy,
    string DatalinkCondition,
    ScenarioDocument Scenario);

public static class FullFlightCalibrationModel
{
    public const int ReferenceMapRadius = 192;
    public const int MinimumOptimizedMapRadius = 5;
    public const int OptimizedMapSafetyMargin = 2;

    public const string StationaryPolicy = "stationary";
    public const string StraightRetreatPolicy = "straight-retreat";
    public const string CrossingWeavePolicy = "crossing-weave";
    public const string TurnbackPolicy = "turnback";
    public const string LiveDatalink = "live";
    public const string OccludedDatalink = "occluded";

    private static readonly CoordinateDocument LauncherCoordinate = new() { Q = 10, R = 16 };
    private static readonly CoordinateDocument MissileCoordinate = new() { Q = 12, R = 16 };
    private static readonly CoordinateDocument InitialTargetCoordinate = new() { Q = 16, R = 12 };

    public static IReadOnlyList<PreparedFullFlightCalibrationVariant> PrepareVariants(
        FullFlightCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        FullFlightMapSizingMode mapSizingMode =
            FullFlightMapSizingMode.OptimizedVariant)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(catalog);
        Validate(study, catalog);

        IReadOnlyDictionary<string, RepresentativeMissileProfileDocument> profiles =
            catalog.MissileProfiles.ToDictionary(item => item.Id, StringComparer.Ordinal);
        IReadOnlyDictionary<int, TechnologyLevelCalibrationDocument> technology =
            catalog.TechnologyLevels.ToDictionary(item => item.TechnologyLevel);
        TechnologyLevelCalibrationDocument targetEcm =
            technology[study.FixedTargetEcmTechnologyLevel];
        var variants = new List<PreparedFullFlightCalibrationVariant>();

        foreach (string profileId in study.MissileProfiles)
        {
            RepresentativeMissileProfileDocument profile = profiles[profileId];
            foreach (int missileTl in study.MissileTechnologyLevels)
            {
                TechnologyLevelCalibrationDocument missileTechnology = technology[missileTl];
                int pdsChance = TechnologyCalibrationModel.CalculatePdsInterceptionChancePercent(
                    catalog.Pds,
                    study.FixedPdsTechnologyLevel,
                    missileTl);
                foreach (int targetTl in study.TargetPropulsionTechnologyLevels)
                {
                    TechnologyLevelCalibrationDocument targetTechnology = technology[targetTl];
                    foreach (string policy in study.TargetMovementPolicies)
                    {
                        foreach (string datalink in study.DatalinkConditions)
                        {
                            int safetyTurnCap = CalculateSafetyTurnCap(
                                study,
                                profile,
                                missileTechnology);
                            string id = CreateVariantId(
                                profileId,
                                missileTl,
                                targetTl,
                                policy,
                                datalink);
                            ScenarioDocument scenario = MaterializeScenario(
                                study,
                                catalog,
                                id,
                                profile,
                                missileTechnology,
                                targetTechnology,
                                targetEcm,
                                pdsChance,
                                safetyTurnCap,
                                policy,
                                datalink,
                                mapSizingMode);
                            variants.Add(new PreparedFullFlightCalibrationVariant(
                                id,
                                profile,
                                missileTechnology,
                                targetTechnology,
                                study.FixedPdsTechnologyLevel,
                                targetEcm,
                                pdsChance,
                                safetyTurnCap,
                                policy,
                                datalink,
                                scenario));
                        }
                    }
                }
            }
        }

        return variants
            .OrderBy(item => item.Id, StringComparer.Ordinal)
            .ToArray();
    }

    public static IReadOnlyList<PreparedFullFlightCalibrationVariant>
        PrepareSchedulerProofVariants(
            FullFlightCalibrationStudyDocument study,
            TechnologyProfileCatalogDocument catalog,
            FullFlightMapSizingMode mapSizingMode =
                FullFlightMapSizingMode.OptimizedVariant)
    {
        IReadOnlyList<PreparedFullFlightCalibrationVariant> all =
            PrepareVariants(study, catalog, mapSizingMode);
        IReadOnlyDictionary<string, PreparedFullFlightCalibrationVariant> byId =
            all.ToDictionary(item => item.Id, StringComparer.Ordinal);
        int[] targetLevels = study.TargetPropulsionTechnologyLevels
            .OrderBy(value => value)
            .ToArray();
        int targetTechnologyLevel = targetLevels[targetLevels.Length / 2];
        string[] proofPolicies =
        {
            StationaryPolicy,
            StraightRetreatPolicy,
            CrossingWeavePolicy,
            TurnbackPolicy,
        };
        if (proofPolicies.Any(policy =>
                !study.TargetMovementPolicies.Contains(policy, StringComparer.Ordinal)))
        {
            throw new InvalidOperationException(
                "The scheduler proof requires all four canonical relative-motion policies.");
        }

        var selected = new List<PreparedFullFlightCalibrationVariant>();
        for (int profileIndex = 0;
             profileIndex < study.MissileProfiles.Count;
             profileIndex++)
        {
            string profileId = study.MissileProfiles[profileIndex];
            for (int missileIndex = 0;
                 missileIndex < study.MissileTechnologyLevels.Count;
                 missileIndex++)
            {
                int missileTechnologyLevel =
                    study.MissileTechnologyLevels[missileIndex];
                string policy = proofPolicies[
                    (profileIndex + missileIndex) % proofPolicies.Length];
                foreach (string datalinkCondition in study.DatalinkConditions)
                {
                    string id = CreateVariantId(
                        profileId,
                        missileTechnologyLevel,
                        targetTechnologyLevel,
                        policy,
                        datalinkCondition);
                    selected.Add(byId[id]);
                }
            }
        }

        int expectedCount = checked(
            study.MissileProfiles.Count *
            study.MissileTechnologyLevels.Count *
            study.DatalinkConditions.Count);
        if (selected.Count != expectedCount ||
            selected.Select(item => item.Id)
                .Distinct(StringComparer.Ordinal)
                .Count() != expectedCount)
        {
            throw new InvalidOperationException(
                "The scheduler proof corpus did not produce its expected unique variants.");
        }

        return selected
            .OrderBy(item => item.Id, StringComparer.Ordinal)
            .ToArray();
    }

    public static int CalculateSafetyTurnCap(
        FullFlightCalibrationStudyDocument study,
        RepresentativeMissileProfileDocument profile,
        TechnologyLevelCalibrationDocument missileTechnology)
    {
        ArgumentNullException.ThrowIfNull(study);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(missileTechnology);

        int retainedGuidanceTurns = profile.DatalinkInstalled
            ? missileTechnology.DatalinkRetainedReportAgePhases
            : 0;
        int localTrackTurns = profile.SensorInstalled
            ? missileTechnology.SensorMaximumLocalTrackAgeEpochs
            : 0;
        int enduranceBound = checked(
            missileTechnology.MaximumRangeHexes +
            retainedGuidanceTurns +
            localTrackTurns +
            study.SafetyTurnBuffer);
        return Math.Max(study.MinimumSafetyTurns, enduranceBound);
    }

    public static string CreateVariantId(
        string profileId,
        int missileTechnologyLevel,
        int targetPropulsionTechnologyLevel,
        string targetMovementPolicy,
        string datalinkCondition) =>
        $"{profileId}-m{missileTechnologyLevel}-t{targetPropulsionTechnologyLevel}-" +
        $"{targetMovementPolicy}-{datalinkCondition}";

    public static void Validate(
        FullFlightCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog)
    {
        if (study.SchemaVersion != 2)
        {
            throw new InvalidOperationException(
                $"Unsupported full-flight calibration schema version {study.SchemaVersion}; expected 2.");
        }
        if (catalog.SchemaVersion != 1)
        {
            throw new InvalidOperationException(
                $"Unsupported technology profile catalog schema version {catalog.SchemaVersion}; expected 1.");
        }
        if (string.IsNullOrWhiteSpace(study.Id) ||
            string.IsNullOrWhiteSpace(study.Name) ||
            string.IsNullOrWhiteSpace(study.ProfileCatalog))
        {
            throw new InvalidOperationException(
                "Full-flight calibration requires stable id, name, and profileCatalog values.");
        }
        if (study.TrialsPerVariant <= 0 ||
            study.MinimumSafetyTurns <= 0 ||
            study.SafetyTurnBuffer < 0)
        {
            throw new InvalidOperationException(
                "Full-flight trialsPerVariant and minimumSafetyTurns must be positive, " +
                "and safetyTurnBuffer cannot be negative.");
        }
        if (study.MinimumPracticalMarginalDelta is < 0.0 or > 1.0 ||
            study.MarginalFamilywiseAlpha is <= 0.0 or >= 1.0)
        {
            throw new InvalidOperationException(
                "Full-flight marginal thresholds are outside their valid ranges.");
        }
        if (study.MissileProfiles.Count == 0 ||
            study.MissileTechnologyLevels.Count == 0 ||
            study.TargetPropulsionTechnologyLevels.Count == 0 ||
            study.TargetMovementPolicies.Count == 0 ||
            study.DatalinkConditions.Count == 0)
        {
            throw new InvalidOperationException(
                "Full-flight calibration axes cannot be empty.");
        }

        RequireUnique(study.MissileProfiles, "missileProfiles", StringComparer.Ordinal);
        RequireUnique(study.MissileTechnologyLevels, "missileTechnologyLevels");
        RequireUnique(
            study.TargetPropulsionTechnologyLevels,
            "targetPropulsionTechnologyLevels");
        RequireUnique(study.TargetMovementPolicies, "targetMovementPolicies", StringComparer.Ordinal);
        RequireUnique(study.DatalinkConditions, "datalinkConditions", StringComparer.Ordinal);

        IReadOnlyDictionary<string, RepresentativeMissileProfileDocument> profiles =
            catalog.MissileProfiles.ToDictionary(item => item.Id, StringComparer.Ordinal);
        foreach (string profileId in study.MissileProfiles)
        {
            if (!profiles.ContainsKey(profileId))
            {
                throw new InvalidOperationException(
                    $"Full-flight missile profile '{profileId}' was not found in catalog '{catalog.Id}'.");
            }
        }

        IReadOnlyDictionary<int, TechnologyLevelCalibrationDocument> technology =
            catalog.TechnologyLevels.ToDictionary(item => item.TechnologyLevel);
        foreach (int level in study.MissileTechnologyLevels
                     .Concat(study.TargetPropulsionTechnologyLevels)
                     .Append(study.FixedPdsTechnologyLevel)
                     .Append(study.FixedTargetEcmTechnologyLevel)
                     .Distinct())
        {
            if (!technology.ContainsKey(level))
            {
                throw new InvalidOperationException(
                    $"Full-flight technology level {level} was not found in catalog '{catalog.Id}'.");
            }
        }
        foreach (TechnologyLevelCalibrationDocument level in catalog.TechnologyLevels)
        {
            if (level.ShipMovementHexesPerTurn <= 0)
            {
                throw new InvalidOperationException(
                    $"Technology level {level.TechnologyLevel} requires a positive shipMovementHexesPerTurn value.");
            }
        }

        string[] supportedPolicies =
        {
            StationaryPolicy,
            StraightRetreatPolicy,
            CrossingWeavePolicy,
            TurnbackPolicy,
        };
        foreach (string policy in study.TargetMovementPolicies)
        {
            if (!supportedPolicies.Contains(policy, StringComparer.Ordinal))
            {
                throw new InvalidOperationException(
                    $"Unsupported target movement policy '{policy}'.");
            }
        }
        foreach (string condition in study.DatalinkConditions)
        {
            if (condition is not LiveDatalink and not OccludedDatalink)
            {
                throw new InvalidOperationException(
                    $"Unsupported datalink condition '{condition}'.");
            }
        }
    }

    private static ScenarioDocument MaterializeScenario(
        FullFlightCalibrationStudyDocument study,
        TechnologyProfileCatalogDocument catalog,
        string variantId,
        RepresentativeMissileProfileDocument profile,
        TechnologyLevelCalibrationDocument missileTechnology,
        TechnologyLevelCalibrationDocument targetTechnology,
        TechnologyLevelCalibrationDocument targetEcm,
        int pdsChance,
        int safetyTurnCap,
        string movementPolicy,
        string datalinkCondition,
        FullFlightMapSizingMode mapSizingMode)
    {
        var scenario = new ScenarioDocument
        {
            SchemaVersion = 1,
            Id = variantId,
            Name =
                $"{profile.Name}; missile TL {missileTechnology.TechnologyLevel}; " +
                $"target propulsion TL {targetTechnology.TechnologyLevel}; " +
                $"{movementPolicy}; {datalinkCondition} datalink",
            Description =
                "Checkpoint 21a full-flight pursuit, opportunity, horizon, and scheduler calibration variant.",
            RandomSeed = checked((int)(study.MasterSeed % int.MaxValue)),
            InitialTurnNumber = 1,
            InitialPhase = "Movement",
            ObservationEpoch = 1,
            InitialSequence = 0,
            StopWhenAllMissilesTerminal = true,
            OperationalTurnLimit = safetyTurnCap,
            Map = CreateMap(datalinkCondition, ReferenceMapRadius),
        };

        ShipDocument target = CreateShip(
            "ship-player",
            "Target Ship",
            "Player",
            CloneCoordinate(InitialTargetCoordinate),
            targetTechnology.TechnologyLevel,
            targetTechnology.ShipMovementHexesPerTurn,
            catalog,
            targetEcm,
            jammingEnabled: true);
        ShipDocument launcher = CreateShip(
            "ship-enemy",
            "Missile Launcher",
            "Enemy",
            CloneCoordinate(LauncherCoordinate),
            missileTechnology.TechnologyLevel,
            maximumMovement: 1,
            catalog,
            missileTechnology,
            jammingEnabled: false);
        scenario.Ships.Add(target);
        scenario.Ships.Add(launcher);
        scenario.PriorTracks.Add(CreatePriorTrack(
            launcher.Id,
            target.Id,
            InitialTargetCoordinate));
        scenario.PriorTracks.Add(CreatePriorTrack(
            target.Id,
            launcher.Id,
            LauncherCoordinate));
        scenario.Missiles.Add(CreateMissile(
            profile,
            missileTechnology,
            catalog,
            datalinkCondition));
        scenario.Defenses.Add(new DefenseDocument
        {
            Id = "pds-player",
            DefenderShipId = target.Id,
            Side = target.Side,
            SourceType = "PointDefenseSystem",
            TechnologyLevel = study.FixedPdsTechnologyLevel,
            Range = catalog.Pds.RangeHexes,
            MaximumAttemptsPerPhase = catalog.Pds.MaximumAttemptsPerPhase,
            InterceptionChancePercent = pdsChance,
            Priority = 0,
            RequiresLineOfSight = false,
            RequiresFirmTrack = false,
        });
        scenario.Actions.AddRange(CreateActions(
            safetyTurnCap,
            target.Id,
            "hostile-1",
            movementPolicy,
            targetTechnology.ShipMovementHexesPerTurn));
        if (mapSizingMode == FullFlightMapSizingMode.OptimizedVariant)
        {
            scenario.Map.Radius = CalculateOptimizedMapRadius(scenario);
        }
        else if (mapSizingMode != FullFlightMapSizingMode.ReferenceRadius192)
        {
            throw new InvalidOperationException(
                $"Unsupported full-flight map-sizing mode '{mapSizingMode}'.");
        }

        IReadOnlyList<string> failures = ScenarioPreflightValidator.Validate(scenario);
        if (failures.Count > 0)
        {
            throw new InvalidOperationException(
                $"Full-flight variant '{variantId}' scenario preflight failed: " +
                string.Join("; ", failures));
        }
        return scenario;
    }

    public static int CalculateOptimizedMapRadius(ScenarioDocument scenario)
    {
        int requiredRadius = CalculateRequiredExplicitCoordinateRadius(scenario);
        return Math.Max(
            MinimumOptimizedMapRadius,
            checked(requiredRadius + OptimizedMapSafetyMargin));
    }

    public static int CalculateRequiredExplicitCoordinateRadius(
        ScenarioDocument scenario)
    {
        ArgumentNullException.ThrowIfNull(scenario);
        var coordinates = new List<CoordinateDocument>
        {
            new() { Q = 0, R = 0 },
        };
        coordinates.AddRange(scenario.Map.Objects.Select(item => item.Position));
        coordinates.AddRange(scenario.Ships.Select(item => item.Position));
        coordinates.AddRange(scenario.PriorTracks.Select(item =>
            item.LastKnownPosition));
        foreach (MissileDocument missile in scenario.Missiles)
        {
            coordinates.Add(missile.LaunchPosition);
            coordinates.AddRange(missile.EnteredCoordinates);
            if (missile.RetainedDatalink is not null)
            {
                coordinates.Add(missile.RetainedDatalink.GuidancePosition);
            }
            if (missile.LocalTrack is not null)
            {
                coordinates.Add(missile.LocalTrack.GuidancePosition);
            }
        }
        coordinates.AddRange(scenario.Actions
            .Where(action => action.Destination is not null)
            .Select(action => action.Destination!));
        return coordinates.Max(CalculateCoordinateRadius);
    }

    public static int CalculateCoordinateRadius(CoordinateDocument coordinate)
    {
        ArgumentNullException.ThrowIfNull(coordinate);
        long q = Math.Abs((long)coordinate.Q);
        long r = Math.Abs((long)coordinate.R);
        long s = Math.Abs((long)coordinate.Q + coordinate.R);
        return checked((int)Math.Max(q, Math.Max(r, s)));
    }

    public static long CalculateHexCellCount(int radius)
    {
        if (radius < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(radius));
        }
        return checked(1L + (3L * radius * (radius + 1L)));
    }

    private static MapDocument CreateMap(
        string datalinkCondition,
        int radius)
    {
        var map = new MapDocument
        {
            Radius = radius,
            StarId = "star-primary",
            StarName = "Primary Star",
            EnvironmentId = "clear-space",
            EnvironmentRangePenalty = 0,
        };
        if (datalinkCondition == OccludedDatalink)
        {
            // A short occlusion screen blocks the launcher-to-missile corridor while
            // leaving the already flown route through (11,17) valid. The complete
            // scenario is shifted away from the star at (0,0), so the live-link
            // control variants cannot be accidentally occluded by the star.
            map.Objects.AddRange(new[]
            {
                CreateOccluder("datalink-occluder-a", 11, 14),
                CreateOccluder("datalink-occluder-b", 11, 15),
                CreateOccluder("datalink-occluder-c", 11, 16),
            });
        }
        return map;
    }

    private static MapObjectDocument CreateOccluder(string id, int q, int r) =>
        new()
        {
            Id = id,
            Name = "Datalink Occluder",
            Kind = "Planet",
            Position = new CoordinateDocument { Q = q, R = r },
        };

    private static ShipDocument CreateShip(
        string id,
        string name,
        string side,
        CoordinateDocument position,
        int technologyLevel,
        int maximumMovement,
        TechnologyProfileCatalogDocument catalog,
        TechnologyLevelCalibrationDocument electronicWarfareTechnology,
        bool jammingEnabled) =>
        new()
        {
            Id = id,
            Name = name,
            Side = side,
            Position = position,
            Movement = new MovementProfileDocument
            {
                TechnologyLevel = technologyLevel,
                MaximumHexesPerTurn = maximumMovement,
            },
            Sensor = new SensorProfileDocument
            {
                TechnologyLevel = technologyLevel,
                FirmRange = Math.Max(30, catalog.ControlSensorFirmRange),
                ApproximateRange = Math.Max(30, catalog.ControlSensorApproximateRange),
                RequiresLineOfSight = true,
                ActiveModeBonus = 4,
            },
            Computing = new ComputingProfileDocument
            {
                TechnologyLevel = technologyLevel,
                StaleRetentionUpdates = 4,
                UncertaintyGrowthPerMissedUpdate = 1,
            },
            Signature = new SignatureProfileDocument
            {
                Id = "standard-ship",
                BaselineRangeModifier = 0,
                ActiveEmissionRangeModifier = 2,
            },
            ElectronicWarfare = new ElectronicWarfareProfileDocument
            {
                TechnologyLevel = electronicWarfareTechnology.TechnologyLevel,
                JammingRangePenalty = electronicWarfareTechnology.TerminalEcmStrength,
                CounterJammingStrength = 0,
            },
            SensorMode = "Passive",
            JammingEnabled = jammingEnabled,
        };

    private static PriorTrackDocument CreatePriorTrack(
        string observerId,
        string targetId,
        CoordinateDocument coordinate) =>
        new()
        {
            ObserverId = observerId,
            TargetId = targetId,
            LastKnownPosition = CloneCoordinate(coordinate),
            UncertaintyRadius = 0,
        };

    private static MissileDocument CreateMissile(
        RepresentativeMissileProfileDocument profile,
        TechnologyLevelCalibrationDocument technology,
        TechnologyProfileCatalogDocument catalog,
        string datalinkCondition) =>
        new()
        {
            Id = "hostile-1",
            Side = "Enemy",
            LauncherId = "ship-enemy",
            TargetId = "ship-player",
            LaunchPosition = CloneCoordinate(LauncherCoordinate),
            EnteredCoordinates = new List<CoordinateDocument>
            {
                new() { Q = 10, R = 17 },
                new() { Q = 11, R = 17 },
                CloneCoordinate(MissileCoordinate),
            },
            Flight = new FlightProfileDocument
            {
                TechnologyLevel = technology.TechnologyLevel,
                MaximumRange = technology.MaximumRangeHexes,
                Speed = technology.FlightSpeedHexesPerTurn,
            },
            Datalink = new DatalinkProfileDocument
            {
                TechnologyLevel = technology.TechnologyLevel,
                IsInstalled = profile.DatalinkInstalled,
                RequiresLineOfSight = true,
                MaximumRetainedReportAgePhases =
                    technology.DatalinkRetainedReportAgePhases,
            },
            Sensor = new MissileSensorProfileDocument
            {
                TechnologyLevel = technology.TechnologyLevel,
                IsInstalled = profile.SensorInstalled,
                FirmRange = technology.SensorFirmRangeHexes,
                ApproximateRange = technology.SensorApproximateRangeHexes,
                RequiresLineOfSight = true,
                ActiveModeBonus = technology.SensorActiveModeBonusHexes,
                AllowsActiveMode = true,
                MaximumLocalTrackAgeEpochs =
                    technology.SensorMaximumLocalTrackAgeEpochs,
            },
            Terminal = new TerminalProfileDocument
            {
                GuidanceComputer = new GuidanceComputerDocument
                {
                    TechnologyLevel = technology.TechnologyLevel,
                    BaseHitChance = technology.GuidanceBaseHitChancePercent,
                    MinimumHitChance = catalog.MinimumHitChancePercent,
                    MaximumHitChance = catalog.MaximumHitChancePercent,
                },
                Seeker = new SeekerDocument
                {
                    TechnologyLevel = technology.TechnologyLevel,
                    IsInstalled = profile.SeekerInstalled,
                    BaseAcquisitionChance =
                        technology.SeekerBaseAcquisitionChancePercent,
                    TerminalEccmStrength = technology.SeekerEccmStrength,
                    AccuracyBonus = technology.SeekerAccuracyBonusPercent,
                    MinimumAcquisitionChance =
                        catalog.MinimumAcquisitionChancePercent,
                    MaximumAcquisitionChance =
                        catalog.MaximumAcquisitionChancePercent,
                },
                AcquisitionPenaltyPerNetEcm =
                    catalog.AcquisitionPenaltyPercentPerNetEcmStrength,
                StationarySearchFuelCost = 1,
            },
            Signature = new SignatureProfileDocument
            {
                Id = "missile-plume",
                BaselineRangeModifier = 1,
                ActiveEmissionRangeModifier = 0,
            },
            RetainedDatalink = new RetainedDatalinkDocument
            {
                LinkState = datalinkCondition == OccludedDatalink
                    ? "Blocked"
                    : "Live",
                Quality = "Current",
                GuidancePosition = CloneCoordinate(InitialTargetCoordinate),
                SourceObservationEpoch = 1,
                ReceivedGuidancePhase = 1,
                UncertaintyRadius = 0,
                AgePhases = 0,
            },
            InitialStatus = "InFlight",
            GuidancePhaseCount = 1,
        };

    private static IReadOnlyList<ActionDocument> CreateActions(
        int safetyTurnCap,
        string targetId,
        string missileId,
        string movementPolicy,
        int targetSpeed)
    {
        var actions = new List<ActionDocument>();
        CoordinateDocument targetPosition = CloneCoordinate(InitialTargetCoordinate);
        for (int turn = 1; turn <= safetyTurnCap; turn++)
        {
            CoordinateDocument next = MoveTarget(
                targetPosition,
                movementPolicy,
                targetSpeed,
                turn);
            if (next.Q != targetPosition.Q || next.R != targetPosition.R)
            {
                actions.Add(new ActionDocument
                {
                    Type = "moveShip",
                    ShipId = targetId,
                    Destination = CloneCoordinate(next),
                });
            }
            targetPosition = next;
            actions.Add(new ActionDocument { Type = "advancePhase" });
            actions.Add(new ActionDocument { Type = "advancePhase" });
            actions.Add(new ActionDocument { Type = "advancePhase" });
            actions.Add(new ActionDocument
            {
                Type = "advanceMissile",
                MissileId = missileId,
                NewInterceptionPhase = true,
            });
            actions.Add(new ActionDocument { Type = "advancePhase" });
            actions.Add(new ActionDocument { Type = "advancePhase" });
            actions.Add(new ActionDocument { Type = "advancePhase" });
        }
        return actions;
    }

    private static CoordinateDocument MoveTarget(
        CoordinateDocument current,
        string movementPolicy,
        int speed,
        int turn)
    {
        (int Dq, int Dr) = movementPolicy switch
        {
            StationaryPolicy => (0, 0),
            StraightRetreatPolicy => (1, -1),
            CrossingWeavePolicy => ((turn - 1) % 4) switch
            {
                0 => (0, 1),
                1 => (1, 0),
                2 => (0, -1),
                _ => (-1, 0),
            },
            TurnbackPolicy when turn % 2 == 1 => (1, -1),
            TurnbackPolicy => (-1, 1),
            _ => throw new InvalidOperationException(
                $"Unsupported target movement policy '{movementPolicy}'."),
        };
        return new CoordinateDocument
        {
            Q = checked(current.Q + (Dq * speed)),
            R = checked(current.R + (Dr * speed)),
        };
    }

    private static CoordinateDocument CloneCoordinate(CoordinateDocument source) =>
        new() { Q = source.Q, R = source.R };

    private static void RequireUnique<T>(
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
                $"Full-flight axis '{axisName}' contains duplicate value(s): " +
                string.Join(", ", duplicates));
        }
    }
}
