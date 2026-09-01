namespace StarCluster.Core.Combat.Tactics;

public sealed record TacticalPackageCandidate(
    string Id,
    int TacticalPower,
    int OffenseUtilityMilli,
    int DefenseUtilityMilli,
    int FundedMainBanks,
    int HeldMainBanks,
    int PdsReactionCapacity,
    bool ActiveSensor = false,
    bool FirmTrack = false)
{
    public int TotalUtilityMilli => checked(OffenseUtilityMilli + DefenseUtilityMilli);

    public void Validate()
    {
        if (string.IsNullOrWhiteSpace(Id))
            throw new ArgumentException("Tactical package id is required.", nameof(Id));
        if (TacticalPower < 0 || OffenseUtilityMilli < 0 || DefenseUtilityMilli < 0 ||
            FundedMainBanks < 0 || HeldMainBanks < 0 || PdsReactionCapacity < 0)
            throw new ArgumentOutOfRangeException(nameof(TacticalPower), "Tactical package inputs must be non-negative.");
        if (HeldMainBanks > FundedMainBanks)
            throw new ArgumentException("Held Main banks cannot exceed funded Main banks.", nameof(HeldMainBanks));
    }
}

/// <summary>
/// CP147 bounded tactical-package selector.  Candidate utilities are supplied by
/// the combat caller from player-observable/current-state mechanics.  The selector
/// itself knows nothing about hidden enemy build data and changes no component
/// statistics.  Exact ties favor continued offense before defensive value and TP
/// efficiency, preventing defensive deadlock while preserving deterministic parity.
/// </summary>
public static class TacticalPackageUtilityService
{
    public static TacticalPackageCandidate Choose(
        IEnumerable<TacticalPackageCandidate> candidates,
        int spendableTacticalPower)
    {
        if (spendableTacticalPower < 0)
            throw new ArgumentOutOfRangeException(nameof(spendableTacticalPower));
        ArgumentNullException.ThrowIfNull(candidates);

        TacticalPackageCandidate? best = null;
        foreach (TacticalPackageCandidate candidate in candidates)
        {
            candidate.Validate();
            if (candidate.TacticalPower > spendableTacticalPower)
                continue;
            if (best is null || Compare(candidate, best) > 0)
                best = candidate;
        }
        return best ?? throw new InvalidOperationException("At least one feasible tactical package is required.");
    }

    private static int Compare(TacticalPackageCandidate a, TacticalPackageCandidate b)
    {
        int cmp = a.TotalUtilityMilli.CompareTo(b.TotalUtilityMilli);
        if (cmp != 0) return cmp;
        cmp = a.OffenseUtilityMilli.CompareTo(b.OffenseUtilityMilli);
        if (cmp != 0) return cmp;
        cmp = a.DefenseUtilityMilli.CompareTo(b.DefenseUtilityMilli);
        if (cmp != 0) return cmp;
        cmp = a.FundedMainBanks.CompareTo(b.FundedMainBanks);
        if (cmp != 0) return cmp;
        cmp = a.ActiveSensor.CompareTo(b.ActiveSensor);
        if (cmp != 0) return cmp;
        cmp = a.FirmTrack.CompareTo(b.FirmTrack);
        if (cmp != 0) return cmp;
        cmp = b.HeldMainBanks.CompareTo(a.HeldMainBanks); // fewer held banks wins exact tie
        if (cmp != 0) return cmp;
        cmp = b.TacticalPower.CompareTo(a.TacticalPower); // lower TP wins exact tie
        if (cmp != 0) return cmp;
        return string.CompareOrdinal(a.Id, b.Id);
    }
}
