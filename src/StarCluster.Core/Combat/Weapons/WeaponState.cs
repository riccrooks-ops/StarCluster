using StarCluster.Core.Combat.Damage;
using StarCluster.Core.Combat.Power;

namespace StarCluster.Core.Combat.Weapons;

public sealed class WeaponState
{
    private readonly AmmunitionFeedState? _ammunitionFeed;

    public WeaponState(WeaponProfile profile, int? currentAmmunition = null)
    {
        ArgumentNullException.ThrowIfNull(profile);
        int? ammunition = currentAmmunition ?? profile.PristineAmmunition;
        if (ammunition is < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentAmmunition));
        }
        if (profile.PristineAmmunition is null && ammunition is not null)
        {
            throw new ArgumentException(
                "An ammunition-independent weapon cannot be assigned ammunition.",
                nameof(currentAmmunition));
        }
        if (profile.PristineAmmunition is int maximum &&
            ammunition is int current && current > maximum)
        {
            throw new ArgumentOutOfRangeException(
                nameof(currentAmmunition),
                current,
                "Current ammunition cannot exceed the weapon's pristine capacity.");
        }

        Profile = profile;
        if (ammunition is int finiteAmmunition)
        {
            _ammunitionFeed = new AmmunitionFeedState(finiteAmmunition);
        }
    }

    public WeaponProfile Profile { get; }

    public int? CurrentAmmunition => _ammunitionFeed?.TotalPackages;

    public int? ReadyAmmunition => _ammunitionFeed?.ReadyPackages;

    public int? ReserveAmmunition => _ammunitionFeed?.ReservePackages;


    public int? ConsumeAmmunitionForHeldFire()
    {
        if (_ammunitionFeed is not null &&
            !_ammunitionFeed.CanConsume(Profile.AmmunitionCost))
        {
            throw new InvalidOperationException(
                $"Weapon '{Profile.Id}' lacks the required ready ammunition package.");
        }

        if (_ammunitionFeed is not null)
        {
            _ammunitionFeed.Consume(Profile.AmmunitionCost);
        }
        return CurrentAmmunition;
    }

    public WeaponFireResult Fire(
        TacticalPowerLedger power,
        LayeredDefenseState target,
        bool hit)
    {
        ArgumentNullException.ThrowIfNull(power);
        ArgumentNullException.ThrowIfNull(target);

        if (_ammunitionFeed is not null &&
            !_ammunitionFeed.CanConsume(Profile.AmmunitionCost))
        {
            throw new InvalidOperationException(
                $"Weapon '{Profile.Id}' lacks the required ready ammunition package.");
        }

        if (Profile.TacticalPowerCost > 0)
        {
            power.Spend(Profile.TacticalPowerCost);
        }
        if (_ammunitionFeed is not null)
        {
            _ammunitionFeed.Consume(Profile.AmmunitionCost);
        }

        LayeredDamageResolution? damageResolution = hit
            ? LayeredDamageResolver.Resolve(target, Profile.Packet)
            : null;
        return new WeaponFireResult(
            Profile.Id,
            Profile.Mode,
            hit,
            Profile.TacticalPowerCost,
            Profile.AmmunitionCost,
            CurrentAmmunition,
            power.Snapshot(),
            damageResolution);
    }
}
