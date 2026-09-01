using System.Text.Json.Serialization;

namespace StarCluster.ScenarioRunner.TL1PhaseB;

public sealed class Tl1PhaseBScenarioDocument
{
    public string SchemaVersion { get; set; } = "star-cluster-tl1-phase-b-v1";
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string BaselineSha256 { get; set; } = string.Empty;
    public List<Tl1PhaseBCaseDocument> Cases { get; set; } = new();
}

public sealed class Tl1PhaseBCaseDocument
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public Tl1PhaseBOperation Operation { get; set; }

    // Baseline is the default source. Explicit fixtures must opt out.
    public string ProfileSource { get; set; } = "baseline";
    public string WeaponFamily { get; set; } = "kinetic";
    public string TargetingCondition { get; set; } = "operational";

    public int? WeaponAccuracy { get; set; }
    public int? ComputerBonus { get; set; }
    public int RangeHexes { get; set; }
    public bool ShooterEvasive { get; set; }
    public bool TargetEvasive { get; set; }
    public int RollA { get; set; }
    public int RollB { get; set; }
    public int? HullA { get; set; }
    public int? HullB { get; set; }
    public int? DamageA { get; set; }
    public int? DamageB { get; set; }

    // Qualitative expectations remain explicit. Baseline-derived numerical
    // expectations are calculated by the runner unless an explicit fixture
    // supplies an override.
    public int? ExpectedChance { get; set; }
    public string ExpectedOutcomeA { get; set; } = string.Empty;
    public string ExpectedOutcomeB { get; set; } = string.Empty;
    public int? ExpectedHullA { get; set; }
    public int? ExpectedHullB { get; set; }
    public bool ExpectedMutualDestruction { get; set; }
    public int TurnCap { get; set; } = 12;
    public List<int> RollsA { get; set; } = new();
    public List<int> RollsB { get; set; } = new();
    public string ExpectedDuelOutcome { get; set; } = string.Empty;
    public int? ExpectedTurnsResolved { get; set; }
}

public enum Tl1PhaseBOperation
{
    Accuracy,
    Roll,
    SimultaneousVolley,
    KineticMirrorDuel,
}
