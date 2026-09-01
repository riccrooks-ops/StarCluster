namespace StarCluster.ScenarioRunner;

public sealed class ScenarioDocument
{
    public int SchemaVersion { get; set; } = 1;
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int RandomSeed { get; set; } = 180100;
    public int InitialTurnNumber { get; set; } = 1;
    public string InitialPhase { get; set; } = "Movement";
    public int ObservationEpoch { get; set; } = 1;
    public long InitialSequence { get; set; }
    public bool StopWhenAllMissilesTerminal { get; set; }
    public int? OperationalTurnLimit { get; set; }
    public MapDocument Map { get; set; } = new();
    public List<ShipDocument> Ships { get; set; } = new();
    public List<PriorTrackDocument> PriorTracks { get; set; } = new();
    public List<MissileDocument> Missiles { get; set; } = new();
    public List<DefenseDocument> Defenses { get; set; } = new();
    public List<string> InterceptionOutcomes { get; set; } = new();
    public List<int> TerminalRolls { get; set; } = new();
    public List<ActionDocument> Actions { get; set; } = new();
    public ExpectationsDocument Expect { get; set; } = new();
}

public sealed class MapDocument
{
    public int Radius { get; set; } = 6;
    public string StarId { get; set; } = "star-primary";
    public string StarName { get; set; } = "Primary Star";
    public string EnvironmentId { get; set; } = "clear-space";
    public int EnvironmentRangePenalty { get; set; }
    public List<MapObjectDocument> Objects { get; set; } = new();
}

public sealed class MapObjectDocument
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Kind { get; set; } = "Planet";
    public CoordinateDocument Position { get; set; } = new();
}

public sealed class CoordinateDocument
{
    public int Q { get; set; }
    public int R { get; set; }
}

public sealed class ShipDocument
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Side { get; set; } = "Player";
    public CoordinateDocument Position { get; set; } = new();
    public MovementProfileDocument Movement { get; set; } = new();
    public SensorProfileDocument Sensor { get; set; } = new();
    public ComputingProfileDocument Computing { get; set; } = new();
    public SignatureProfileDocument Signature { get; set; } = new();
    public ElectronicWarfareProfileDocument ElectronicWarfare { get; set; } = new();
    public string SensorMode { get; set; } = "Passive";
    public bool JammingEnabled { get; set; }
}

public sealed class MovementProfileDocument
{
    public int TechnologyLevel { get; set; } = 3;
    public int MaximumHexesPerTurn { get; set; } = 3;
}

public sealed class SensorProfileDocument
{
    public int TechnologyLevel { get; set; } = 3;
    public int FirmRange { get; set; } = 6;
    public int ApproximateRange { get; set; } = 10;
    public bool RequiresLineOfSight { get; set; } = true;
    public int ActiveModeBonus { get; set; } = 2;
}

public sealed class ComputingProfileDocument
{
    public int TechnologyLevel { get; set; } = 3;
    public int StaleRetentionUpdates { get; set; } = 3;
    public int UncertaintyGrowthPerMissedUpdate { get; set; } = 1;
}

public sealed class SignatureProfileDocument
{
    public string Id { get; set; } = "standard-signature";
    public int BaselineRangeModifier { get; set; }
    public int ActiveEmissionRangeModifier { get; set; }
}

public sealed class ElectronicWarfareProfileDocument
{
    public int TechnologyLevel { get; set; }
    public int JammingRangePenalty { get; set; }
    public int CounterJammingStrength { get; set; }
}

public sealed class PriorTrackDocument
{
    public string ObserverId { get; set; } = string.Empty;
    public string TargetId { get; set; } = string.Empty;
    public CoordinateDocument LastKnownPosition { get; set; } = new();
    public int UncertaintyRadius { get; set; } = 1;
}

public sealed class MissileDocument
{
    public string Id { get; set; } = string.Empty;
    public string Side { get; set; } = "Enemy";
    public string LauncherId { get; set; } = string.Empty;
    public string TargetId { get; set; } = string.Empty;
    public CoordinateDocument LaunchPosition { get; set; } = new();
    public List<CoordinateDocument> EnteredCoordinates { get; set; } = new();
    public FlightProfileDocument Flight { get; set; } = new();
    public DatalinkProfileDocument Datalink { get; set; } = new();
    public MissileSensorProfileDocument Sensor { get; set; } = new();
    public TerminalProfileDocument Terminal { get; set; } = new();
    public SignatureProfileDocument Signature { get; set; } = new()
    {
        Id = "missile-plume",
        BaselineRangeModifier = 1,
    };
    public RetainedDatalinkDocument? RetainedDatalink { get; set; }
    public LocalTrackDocument? LocalTrack { get; set; }
    public string InitialStatus { get; set; } = "InFlight";
    public int GuidancePhaseCount { get; set; }
}

public sealed class FlightProfileDocument
{
    public int TechnologyLevel { get; set; } = 2;
    public int MaximumRange { get; set; } = 10;
    public int Speed { get; set; } = 2;
}

public sealed class DatalinkProfileDocument
{
    public int TechnologyLevel { get; set; } = 2;
    public bool IsInstalled { get; set; } = true;
    public bool RequiresLineOfSight { get; set; } = true;
    public int MaximumRetainedReportAgePhases { get; set; } = 3;
}

public sealed class MissileSensorProfileDocument
{
    public int TechnologyLevel { get; set; } = 2;
    public bool IsInstalled { get; set; } = true;
    public int FirmRange { get; set; } = 3;
    public int ApproximateRange { get; set; } = 5;
    public bool RequiresLineOfSight { get; set; } = true;
    public int ActiveModeBonus { get; set; } = 2;
    public bool AllowsActiveMode { get; set; } = true;
    public int MaximumLocalTrackAgeEpochs { get; set; } = 2;
}

public sealed class TerminalProfileDocument
{
    public GuidanceComputerDocument GuidanceComputer { get; set; } = new();
    public SeekerDocument Seeker { get; set; } = new();
    public int AcquisitionPenaltyPerNetEcm { get; set; } = 10;
    public int StationarySearchFuelCost { get; set; } = 1;
}

public sealed class GuidanceComputerDocument
{
    public int TechnologyLevel { get; set; } = 2;
    public int BaseHitChance { get; set; } = 65;
    public int MinimumHitChance { get; set; } = 5;
    public int MaximumHitChance { get; set; } = 95;
}

public sealed class SeekerDocument
{
    public int TechnologyLevel { get; set; } = 2;
    public bool IsInstalled { get; set; } = true;
    public int BaseAcquisitionChance { get; set; } = 65;
    public int TerminalEccmStrength { get; set; } = 2;
    public int AccuracyBonus { get; set; } = 15;
    public int MinimumAcquisitionChance { get; set; } = 5;
    public int MaximumAcquisitionChance { get; set; } = 95;
}

public sealed class RetainedDatalinkDocument
{
    public string LinkState { get; set; } = "Blocked";
    public string Quality { get; set; } = "Current";
    public CoordinateDocument GuidancePosition { get; set; } = new();
    public int SourceObservationEpoch { get; set; } = 1;
    public int ReceivedGuidancePhase { get; set; } = 1;
    public int UncertaintyRadius { get; set; }
    public int AgePhases { get; set; }
}

public sealed class LocalTrackDocument
{
    public string Quality { get; set; } = "Current";
    public CoordinateDocument GuidancePosition { get; set; } = new();
    public int SourceObservationEpoch { get; set; } = 1;
    public int UncertaintyRadius { get; set; }
    public string SensorMode { get; set; } = "Passive";
    public int AgeEpochs { get; set; }
    public int? LastAgedObservationEpoch { get; set; }
}

public sealed class DefenseDocument
{
    public string Id { get; set; } = string.Empty;
    public string DefenderShipId { get; set; } = string.Empty;
    public string Side { get; set; } = "Player";
    public string SourceType { get; set; } = "PointDefenseSystem";
    public int TechnologyLevel { get; set; } = 2;
    public int Range { get; set; } = 1;
    public int MaximumAttemptsPerPhase { get; set; } = 2;
    public int InterceptionChancePercent { get; set; }
    public int Priority { get; set; }
    public bool RequiresLineOfSight { get; set; }
    public bool RequiresFirmTrack { get; set; }
}

public sealed class ActionDocument
{
    public string Type { get; set; } = string.Empty;
    public string? ShipId { get; set; }
    public string? MissileId { get; set; }
    public CoordinateDocument? Destination { get; set; }
    public bool NewInterceptionPhase { get; set; }
}

public sealed class ExpectationsDocument
{
    public List<ShipExpectationDocument> Ships { get; set; } = new();
    public List<MissileExpectationDocument> Missiles { get; set; } = new();
    public List<TrackExpectationDocument> Tracks { get; set; } = new();
    public List<string> InterceptionOpportunities { get; set; } = new();
    public List<string> RequiredEventsInOrder { get; set; } = new();
}

public sealed class ShipExpectationDocument
{
    public string Id { get; set; } = string.Empty;
    public CoordinateDocument? Position { get; set; }
}

public sealed class MissileExpectationDocument
{
    public string Id { get; set; } = string.Empty;
    public string? Status { get; set; }
    public string? TerminalOutcome { get; set; }
    public CoordinateDocument? Position { get; set; }
    public int? DistanceTraveled { get; set; }
    public int? StationarySearchFuelSpent { get; set; }
    public int? TotalFuelSpent { get; set; }
    public int? AttackRoll { get; set; }
    public int? AcquisitionRoll { get; set; }
}

public sealed class TrackExpectationDocument
{
    public string ObserverId { get; set; } = string.Empty;
    public string TargetId { get; set; } = string.Empty;
    public string Quality { get; set; } = string.Empty;
    public CoordinateDocument? Position { get; set; }
}
