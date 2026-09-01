namespace StarCluster.Core.Combat.InternalDamage;

public sealed class InternalDamageTrack
{
    private readonly IReadOnlyList<int> _stratumCycle;

    public InternalDamageTrack(
        InternalCriticalDensity density,
        bool protectedCompartmentation,
        ulong seed,
        int originalHullSpan)
    {
        if (!Enum.IsDefined(density))
        {
            throw new ArgumentOutOfRangeException(nameof(density));
        }
        if (originalHullSpan <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(originalHullSpan));
        }

        Density = density;
        ProtectedCompartmentation = protectedCompartmentation;
        Seed = seed;
        OriginalHullSpan = originalHullSpan;
        _stratumCycle = density.StratumCycle();
    }

    public InternalCriticalDensity Density { get; }

    public bool ProtectedCompartmentation { get; }

    public ulong Seed { get; }

    public int OriginalHullSpan { get; }

    public InternalMarkerKind MarkerAt(int oneBasedPosition)
    {
        if (oneBasedPosition <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(oneBasedPosition));
        }

        StratumLocation location = Locate(oneBasedPosition);
        int criticalOffset = ProtectedCompartmentation
            ? ProtectedCriticalOffset(location)
            : OrdinaryCriticalOffset(location.StratumIndex, location.Length);
        return location.Offset == criticalOffset
            ? InternalMarkerKind.Critical
            : InternalMarkerKind.Hull;
    }

    public int CountCriticalMarkers(int positions)
    {
        if (positions < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(positions));
        }

        int count = 0;
        for (int position = 1; position <= positions; position++)
        {
            if (MarkerAt(position) == InternalMarkerKind.Critical)
            {
                count++;
            }
        }
        return count;
    }

    private int ProtectedCriticalOffset(StratumLocation location)
    {
        int ordinaryOffset = OrdinaryCriticalOffset(
            location.StratumIndex,
            location.Length);
        if (location.StartPosition > OriginalHullSpan)
        {
            return location.Length;
        }

        int visibleLength = Math.Min(
            location.Length,
            checked(OriginalHullSpan - location.StartPosition + 1));
        if (ordinaryOffset > visibleLength)
        {
            // The ordinary seeded marker lies beyond the original finite Hull
            // span. Preserve it at the full stratum end for any later Hull-repair
            // continuation rather than silently creating an extra original marker.
            return location.Length;
        }

        int protectedOffset = visibleLength;
        bool isOriginalTerminalPosition =
            checked(location.StartPosition + protectedOffset - 1) ==
            OriginalHullSpan;
        if (isOriginalTerminalPosition && protectedOffset > 1)
        {
            // A final-position X would resolve only as the ship reaches zero Hull.
            // Swap it with the adjacent H so Protected Compartmentation delays the
            // marker while preserving the ordinary finite-track X count.
            protectedOffset--;
        }
        return protectedOffset;
    }

    private int OrdinaryCriticalOffset(int stratumIndex, int length) =>
        checked((int)(StableSelectionHash.Compute(
            Seed,
            "internal-track",
            stratumIndex) % (ulong)length) + 1);

    private StratumLocation Locate(int oneBasedPosition)
    {
        int remaining = oneBasedPosition;
        int startPosition = 1;
        int stratumIndex = 0;
        while (true)
        {
            int length = _stratumCycle[stratumIndex % _stratumCycle.Count];
            if (remaining <= length)
            {
                return new StratumLocation(
                    stratumIndex,
                    remaining,
                    length,
                    startPosition);
            }

            remaining -= length;
            startPosition = checked(startPosition + length);
            stratumIndex++;
        }
    }

    private readonly record struct StratumLocation(
        int StratumIndex,
        int Offset,
        int Length,
        int StartPosition);
}
