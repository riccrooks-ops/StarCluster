namespace StarCluster.Core.Combat.DirectFire;

/// <summary>
/// One mutually exclusive commitment for a direct-fire weapon during a
/// tactical turn.
/// </summary>
public enum DirectFireOrderType
{
    FireAtShip,
    InterceptSpecificMissile,
    HoldForAnyMissile,
    HoldFire,
}
