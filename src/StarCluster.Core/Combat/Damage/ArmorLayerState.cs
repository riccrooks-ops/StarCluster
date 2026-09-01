namespace StarCluster.Core.Combat.Damage;

public sealed class ArmorLayerState
{
    public ArmorLayerState(
        string id,
        int pristineProtection,
        int currentProtection,
        int pristineIntegrity,
        int currentIntegrity)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("Armor layer ID is required.", nameof(id));
        }
        ValidateCurrentAgainstPristine(
            pristineProtection,
            currentProtection,
            nameof(pristineProtection),
            nameof(currentProtection));
        ValidateCurrentAgainstPristine(
            pristineIntegrity,
            currentIntegrity,
            nameof(pristineIntegrity),
            nameof(currentIntegrity));

        Id = id;
        PristineProtection = pristineProtection;
        CurrentProtection = currentProtection;
        PristineIntegrity = pristineIntegrity;
        CurrentIntegrity = currentIntegrity;
    }

    public string Id { get; }

    public int PristineProtection { get; }

    public int CurrentProtection { get; private set; }

    public int PristineIntegrity { get; }

    public int CurrentIntegrity { get; private set; }

    internal void ApplyIntegrityDamage(int amount)
    {
        if (amount < 0 || amount > CurrentIntegrity)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        CurrentIntegrity -= amount;
    }

    internal void RestoreIntegrity(int amount)
    {
        if (amount < 0 || amount > PristineIntegrity - CurrentIntegrity)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        CurrentIntegrity += amount;
    }


    public ArmorLayerState Clone() => new(
        Id,
        PristineProtection,
        CurrentProtection,
        PristineIntegrity,
        CurrentIntegrity);

    private static void ValidateCurrentAgainstPristine(
        int pristine,
        int current,
        string pristineName,
        string currentName)
    {
        if (pristine < 0)
        {
            throw new ArgumentOutOfRangeException(
                pristineName,
                pristine,
                "A pristine armor value cannot be negative.");
        }
        if (current < 0 || current > pristine)
        {
            throw new ArgumentOutOfRangeException(
                currentName,
                current,
                "A current armor value must be between zero and its pristine value.");
        }
    }
}
