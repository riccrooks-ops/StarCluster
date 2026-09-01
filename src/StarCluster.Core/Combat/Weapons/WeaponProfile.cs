using StarCluster.Core.Combat.Damage;

namespace StarCluster.Core.Combat.Weapons;

public sealed record WeaponProfile
{
    public WeaponProfile(
        string id,
        WeaponFamily family,
        string mode,
        AttackPacket packet,
        int tacticalPowerCost,
        int ammunitionCost,
        int? pristineAmmunition)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("Weapon ID is required.", nameof(id));
        }
        if (string.IsNullOrWhiteSpace(mode))
        {
            throw new ArgumentException("Weapon mode is required.", nameof(mode));
        }
        ArgumentNullException.ThrowIfNull(packet);
        if (tacticalPowerCost < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tacticalPowerCost));
        }
        if (ammunitionCost < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(ammunitionCost));
        }
        if (pristineAmmunition is < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(pristineAmmunition));
        }
        if (pristineAmmunition is null && ammunitionCost != 0)
        {
            throw new ArgumentException(
                "An ammunition-independent weapon cannot have an ammunition cost.",
                nameof(ammunitionCost));
        }

        Id = id;
        Family = family;
        Mode = mode;
        Packet = packet;
        TacticalPowerCost = tacticalPowerCost;
        AmmunitionCost = ammunitionCost;
        PristineAmmunition = pristineAmmunition;
    }

    public string Id { get; }

    public WeaponFamily Family { get; }

    public string Mode { get; }

    public AttackPacket Packet { get; }

    public int TacticalPowerCost { get; }

    public int AmmunitionCost { get; }

    public int? PristineAmmunition { get; }
}
