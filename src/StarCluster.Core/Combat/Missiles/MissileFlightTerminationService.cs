using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;

namespace StarCluster.Core.Combat.Missiles;

public enum MissileGuidanceDependency
{
    CommandGuided = 0,
    Autonomous = 1,
    HybridWithAutonomousFallback = 2,
    HybridWithoutAutonomousFallback = 3,
}

public sealed record MissileDatalinkAvailability(
    bool CommunicationsAvailable,
    int FunctioningLauncherCount,
    bool Active);

public static class MissileFlightTerminationService
{
    public static MissileDatalinkAvailability EvaluateDatalink(
        ComponentCondition communicationsCondition,
        IEnumerable<ComponentCondition> launcherConditions)
    {
        ArgumentNullException.ThrowIfNull(launcherConditions);
        bool communications = ComponentPerformance.CommunicationsAvailable(
            communicationsCondition);
        int launchers = launcherConditions.Count(condition => condition is
            ComponentCondition.Operational or ComponentCondition.Degraded);
        return new MissileDatalinkAvailability(
            communications,
            launchers,
            communications && launchers > 0);
    }

    public static bool TryVoluntarySelfDestruct(
        GuidedMissileSalvo missile,
        bool hasLineOfSight,
        bool hasCurrentTrackOnFlight,
        bool hasActiveDatalink,
        bool terminalAttackCommitted)
    {
        ArgumentNullException.ThrowIfNull(missile);
        if (missile.IsTerminal ||
            terminalAttackCommitted ||
            !hasLineOfSight ||
            !hasCurrentTrackOnFlight ||
            !hasActiveDatalink)
        {
            return false;
        }

        missile.MarkSelfDestructed(
            "The owning ship transmitted a voluntary in-combat self-destruct command.");
        return true;
    }

    public static int TerminateForFtlPowerUp(
        IEnumerable<GuidedMissileSalvo> outboundMissiles)
    {
        ArgumentNullException.ThrowIfNull(outboundMissiles);
        int count = 0;
        foreach (GuidedMissileSalvo missile in outboundMissiles)
        {
            if (missile.IsTerminal)
            {
                continue;
            }
            missile.MarkSelfDestructed(
                "The launching ship began FTL power-up; security interlocks terminated every outbound Missile Flight.");
            count++;
        }
        return count;
    }

    public static int ResolveLaunchingShipDestroyed(
        IEnumerable<(GuidedMissileSalvo Missile, MissileGuidanceDependency Guidance)> flights)
    {
        ArgumentNullException.ThrowIfNull(flights);
        int terminated = 0;
        foreach ((GuidedMissileSalvo missile, MissileGuidanceDependency guidance) in flights)
        {
            if (missile.IsTerminal)
            {
                continue;
            }
            if (guidance is MissileGuidanceDependency.CommandGuided or
                MissileGuidanceDependency.HybridWithoutAutonomousFallback)
            {
                missile.MarkSelfDestructed(
                    "The launching ship was Destroyed and the Missile Flight lacked autonomous continuation.");
                terminated++;
            }
        }
        return terminated;
    }

    public static int RemoveInboundAfterSuccessfulDeparture(
        IEnumerable<GuidedMissileSalvo> inboundMissiles)
    {
        ArgumentNullException.ThrowIfNull(inboundMissiles);
        int removed = 0;
        foreach (GuidedMissileSalvo missile in inboundMissiles)
        {
            if (missile.IsTerminal)
            {
                continue;
            }
            missile.MarkSelfDestructed(
                "The target completed FTL departure; the Missile Flight cannot follow into strategic travel.");
            removed++;
        }
        return removed;
    }
}
