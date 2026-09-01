namespace StarCluster.Core.Combat.Missiles;

public enum MissileRouteProjectionStatus
{
    Available,
    WaitingForTrack,
    WaitingForRoute,
    RangeExhausted,
    Terminal,
    WithheldByObserverUncertainty,
}
