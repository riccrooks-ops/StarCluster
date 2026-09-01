namespace StarCluster.Core.Combat.Power;

public sealed record PoweredSystemSnapshot(
    string SystemId,
    int LockedPower,
    bool IsActive,
    bool ReactivationProhibited);

public sealed record PowerEarmarkSnapshot(
    string EarmarkId,
    int Power);

public sealed record TacticalPowerSnapshot(
    int Envelope,
    int Available,
    int Spendable,
    int Powered,
    int Spent,
    int Earmarked,
    IReadOnlyList<PoweredSystemSnapshot> Systems,
    IReadOnlyList<PowerEarmarkSnapshot> Earmarks);
