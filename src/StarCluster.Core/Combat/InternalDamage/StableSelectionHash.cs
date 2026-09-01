namespace StarCluster.Core.Combat.InternalDamage;

internal static class StableSelectionHash
{
    public static ulong Compute(
        ulong seed,
        string streamId,
        int sequence,
        int salt = 0)
    {
        ArgumentNullException.ThrowIfNull(streamId);
        ulong hash = 1469598103934665603UL ^ seed;
        foreach (char character in streamId)
        {
            hash ^= (byte)(character & 0xff);
            hash *= 1099511628211UL;
            hash ^= (byte)(character >> 8);
            hash *= 1099511628211UL;
        }

        MixInt(ref hash, sequence);
        MixInt(ref hash, salt);
        hash ^= hash >> 33;
        hash *= 0xff51afd7ed558ccdUL;
        hash ^= hash >> 33;
        hash *= 0xc4ceb9fe1a85ec53UL;
        hash ^= hash >> 33;
        return hash;
    }

    private static void MixInt(ref ulong hash, int value)
    {
        unchecked
        {
            uint unsigned = (uint)value;
            for (int shift = 0; shift < 32; shift += 8)
            {
                hash ^= (byte)(unsigned >> shift);
                hash *= 1099511628211UL;
            }
        }
    }
}
