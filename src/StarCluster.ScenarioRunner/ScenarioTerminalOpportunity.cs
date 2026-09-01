using StarCluster.Core.Geometry;

namespace StarCluster.ScenarioRunner;

public enum ScenarioTerminalOpportunitySource
{
    MissileEnteredTargetHex = 0,
    TargetEnteredMissileHex = 1,
    ActionBeganColocated = 2,
    StationarySearchRetry = 3,
}

public sealed record ScenarioTerminalOpportunity(
    string MissileId,
    string TargetId,
    HexCoord Coordinate,
    ScenarioTerminalOpportunitySource Source,
    int TurnNumber);
