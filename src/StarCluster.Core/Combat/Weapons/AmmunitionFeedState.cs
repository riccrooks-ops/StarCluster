namespace StarCluster.Core.Combat.Weapons;

/// <summary>
/// One ready attack package plus an automatically loading reserve magazine.
/// The ready package is part of, not additional to, the total carried capacity.
/// </summary>
public sealed class AmmunitionFeedState
{
    public AmmunitionFeedState(int totalPackages, bool preloaded = true)
    {
        if (totalPackages < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(totalPackages));
        }

        ReadyPackages = preloaded && totalPackages > 0 ? 1 : 0;
        ReservePackages = totalPackages - ReadyPackages;
    }

    public int ReadyPackages { get; private set; }

    public int ReservePackages { get; private set; }

    public int TotalPackages => checked(ReadyPackages + ReservePackages);

    public bool CanConsume(int packageCount = 1) =>
        packageCount > 0 && ReadyPackages > 0 && TotalPackages >= packageCount;

    public void Consume(int packageCount = 1)
    {
        if (packageCount <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(packageCount));
        }
        if (!CanConsume(packageCount))
        {
            throw new InvalidOperationException(
                "The ammunition feed lacks a ready attack package or sufficient total packages.");
        }

        for (int index = 0; index < packageCount; index++)
        {
            ReadyPackages--;
            if (ReservePackages > 0)
            {
                ReservePackages--;
                ReadyPackages++;
            }
        }
    }
}
