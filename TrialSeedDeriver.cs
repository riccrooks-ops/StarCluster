using System.Text;

namespace StarCluster.ScenarioRunner;

public static class TrialSeedDeriver
{
    private const ulong OffsetBasis = 14695981039346656037UL;
    private const ulong Prime = 1099511628211UL;

    public static ulong Derive(
        ulong masterSeed,
        string variantId,
        int trialIndex,
        ulong streamId)
    {
        if (string.IsNullOrWhiteSpace(variantId))
        {
            throw new ArgumentException("A variant ID is required.", nameof(variantId));
        }
        if (trialIndex < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(trialIndex));
        }

        ulong hash = OffsetBasis;
        foreach (byte value in Encoding.UTF8.GetBytes(variantId))
        {
            hash ^= value;
            hash *= Prime;
        }

        hash = Mix(hash ^ masterSeed);
        hash = Mix(hash ^ checked((ulong)trialIndex));
        return Mix(hash ^ streamId);
    }

    private static ulong Mix(ulong value)
    {
        value ^= value >> 30;
        value *= 0xBF58476D1CE4E5B9UL;
        value ^= value >> 27;
        value *= 0x94D049BB133111EBUL;
        return value ^ (value >> 31);
    }
}
