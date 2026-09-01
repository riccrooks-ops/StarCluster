namespace StarCluster.Core.Combat.Tactics;

public enum RangeOrder
{
    Hold,
    Close,
    Open,
    MaintainPreferredRange,
}

public enum RangeMovementDirection
{
    None,
    Close,
    Open,
}

public enum TacticalObjective
{
    Engage,
    HoldPosition,
    Withdraw,
}
