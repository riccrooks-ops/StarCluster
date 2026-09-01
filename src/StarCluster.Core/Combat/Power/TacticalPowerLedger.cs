namespace StarCluster.Core.Combat.Power;

public sealed class TacticalPowerLedger
{
    private sealed class PoweredSystemEntry
    {
        public PoweredSystemEntry(string systemId, int lockedPower)
        {
            SystemId = systemId;
            LockedPower = lockedPower;
            IsActive = true;
        }

        public string SystemId { get; }

        public int LockedPower { get; set; }

        public bool IsActive { get; set; }

        public bool ReactivationProhibited { get; set; }
    }

    private readonly Dictionary<string, PoweredSystemEntry> _systems =
        new(StringComparer.Ordinal);
    private readonly Dictionary<string, int> _earmarks =
        new(StringComparer.Ordinal);

    public int Envelope { get; private set; }

    public int PoweredPower => _systems.Values.Sum(item => item.LockedPower);

    public int SpentPower { get; private set; }

    public int EarmarkedPower => _earmarks.Values.Sum();

    public int AvailablePower => checked(Envelope - PoweredPower - SpentPower);

    public int SpendablePower => checked(AvailablePower - EarmarkedPower);

    public void BeginTurn(int envelope)
    {
        if (envelope < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(envelope));
        }

        Envelope = envelope;
        SpentPower = 0;
        _systems.Clear();
        _earmarks.Clear();
    }

    public void ClearForFtlTransition()
    {
        Envelope = 0;
        SpentPower = 0;
        _systems.Clear();
        _earmarks.Clear();
    }

    public void AddGeneratedPower(int amount)
    {
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }
        Envelope = checked(Envelope + amount);
    }

    public void IncreasePoweredSystem(string systemId, int additionalPower)
    {
        ValidateId(systemId, nameof(systemId));
        if (additionalPower <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(additionalPower),
                additionalPower,
                "Powered-system increases must be positive.");
        }
        RequireSpendable(additionalPower);

        if (_systems.TryGetValue(systemId, out PoweredSystemEntry? existing))
        {
            if (!existing.IsActive || existing.ReactivationProhibited)
            {
                throw new InvalidOperationException(
                    $"Powered system '{systemId}' cannot reactivate this turn.");
            }
            existing.LockedPower = checked(existing.LockedPower + additionalPower);
            return;
        }

        _systems.Add(systemId, new PoweredSystemEntry(systemId, additionalPower));
    }

    public void ShutdownSystem(string systemId)
    {
        PoweredSystemEntry entry = GetPoweredSystem(systemId);
        if (!entry.IsActive)
        {
            throw new InvalidOperationException(
                $"Powered system '{systemId}' is already inactive.");
        }
        entry.IsActive = false;
        entry.ReactivationProhibited = true;
    }

    public void DisableSystem(string systemId)
    {
        PoweredSystemEntry entry = GetPoweredSystem(systemId);
        entry.IsActive = false;
        entry.ReactivationProhibited = true;
    }

    public void Spend(int amount)
    {
        if (amount <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(amount),
                amount,
                "Spent power must be positive.");
        }
        RequireSpendable(amount);
        SpentPower = checked(SpentPower + amount);
    }

    public void Earmark(string earmarkId, int amount)
    {
        ValidateId(earmarkId, nameof(earmarkId));
        if (amount <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(amount),
                amount,
                "Earmarked power must be positive.");
        }
        if (_earmarks.ContainsKey(earmarkId))
        {
            throw new InvalidOperationException(
                $"Power earmark '{earmarkId}' already exists.");
        }
        RequireSpendable(amount);
        _earmarks.Add(earmarkId, amount);
    }

    public int TriggerEarmark(string earmarkId)
    {
        int amount = GetEarmark(earmarkId);
        _earmarks.Remove(earmarkId);
        SpentPower = checked(SpentPower + amount);
        return amount;
    }

    public int ReleaseEarmark(string earmarkId)
    {
        int amount = GetEarmark(earmarkId);
        _earmarks.Remove(earmarkId);
        return amount;
    }

    public TacticalPowerSnapshot Snapshot() => new(
        Envelope,
        AvailablePower,
        SpendablePower,
        PoweredPower,
        SpentPower,
        EarmarkedPower,
        _systems.Values
            .OrderBy(item => item.SystemId, StringComparer.Ordinal)
            .Select(item => new PoweredSystemSnapshot(
                item.SystemId,
                item.LockedPower,
                item.IsActive,
                item.ReactivationProhibited))
            .ToArray(),
        _earmarks
            .OrderBy(item => item.Key, StringComparer.Ordinal)
            .Select(item => new PowerEarmarkSnapshot(item.Key, item.Value))
            .ToArray());

    private PoweredSystemEntry GetPoweredSystem(string systemId)
    {
        ValidateId(systemId, nameof(systemId));
        if (!_systems.TryGetValue(systemId, out PoweredSystemEntry? entry))
        {
            throw new InvalidOperationException(
                $"Powered system '{systemId}' does not exist.");
        }
        return entry;
    }

    private int GetEarmark(string earmarkId)
    {
        ValidateId(earmarkId, nameof(earmarkId));
        if (!_earmarks.TryGetValue(earmarkId, out int amount))
        {
            throw new InvalidOperationException(
                $"Power earmark '{earmarkId}' does not exist.");
        }
        return amount;
    }

    private void RequireSpendable(int amount)
    {
        if (amount > SpendablePower)
        {
            throw new InvalidOperationException(
                $"Required {amount} Tactical Power but only {SpendablePower} is spendable.");
        }
    }

    private static void ValidateId(string value, string parameterName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException("A stable ID is required.", parameterName);
        }
    }
}
