namespace StarCluster.Core.Combat.Damage;

public sealed record AttackPacket
{
    public AttackPacket(int damage, int shieldPenetration, int armorPenetration)
    {
        if (damage < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(damage),
                damage,
                "Damage cannot be negative.");
        }
        if (shieldPenetration < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(shieldPenetration),
                shieldPenetration,
                "Shield penetration cannot be negative.");
        }
        if (armorPenetration < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(armorPenetration),
                armorPenetration,
                "Armor penetration cannot be negative.");
        }

        Damage = damage;
        ShieldPenetration = shieldPenetration;
        ArmorPenetration = armorPenetration;
    }

    public int Damage { get; }

    public int ShieldPenetration { get; }

    public int ArmorPenetration { get; }
}
