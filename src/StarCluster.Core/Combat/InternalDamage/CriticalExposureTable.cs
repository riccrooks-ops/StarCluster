namespace StarCluster.Core.Combat.InternalDamage;

public sealed class CriticalExposureTable
{
    private sealed record ExposureTicket(
        string? ComponentId,
        CriticalExposureGroup Group);

    private readonly IReadOnlyList<ShipComponentState> _components;
    private readonly IReadOnlyList<ExposureTicket> _tickets;

    public CriticalExposureTable(IEnumerable<ShipComponentState> components)
    {
        ArgumentNullException.ThrowIfNull(components);
        ShipComponentState[] ordered = components
            .OrderBy(component => component.Definition.Id, StringComparer.Ordinal)
            .ToArray();
        if (ordered.Length == 0)
        {
            throw new ArgumentException(
                "At least one damageable component is required.",
                nameof(components));
        }
        if (ordered.Select(item => item.Definition.Id)
            .Distinct(StringComparer.Ordinal).Count() != ordered.Length)
        {
            throw new ArgumentException(
                "Component IDs must be unique.",
                nameof(components));
        }

        var tickets = new List<ExposureTicket>();
        foreach (ShipComponentState component in ordered)
        {
            for (int ticket = 0;
                 ticket < component.Definition.CriticalExposure;
                 ticket++)
            {
                tickets.Add(new ExposureTicket(
                    component.Definition.Id,
                    CriticalExposureGroup.None));
            }
        }

        foreach (CriticalExposureGroup group in ordered
            .Select(component => component.Definition.ExposureGroup)
            .Where(group => group != CriticalExposureGroup.None)
            .Distinct()
            .OrderBy(group => group))
        {
            tickets.Add(new ExposureTicket(null, group));
        }

        if (tickets.Count == 0)
        {
            throw new ArgumentException(
                "The installed components provide no Critical Exposure tickets.",
                nameof(components));
        }

        _components = Array.AsReadOnly(ordered);
        _tickets = tickets.AsReadOnly();
    }

    public int TopLevelTicketCount => _tickets.Count;

    public CriticalExposureSelection Select(
        ulong seed,
        int criticalSequence,
        string streamId = "internal-critical")
    {
        if (criticalSequence < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(criticalSequence));
        }
        if (string.IsNullOrWhiteSpace(streamId))
        {
            throw new ArgumentException("A stream ID is required.", nameof(streamId));
        }

        int topIndex = checked((int)(StableSelectionHash.Compute(
            seed,
            streamId,
            criticalSequence) % (ulong)_tickets.Count));
        ExposureTicket ticket = _tickets[topIndex];
        if (ticket.ComponentId is not null)
        {
            return new CriticalExposureSelection(
                ticket.ComponentId,
                CriticalExposureGroup.None,
                topIndex,
                _tickets.Count,
                null,
                null);
        }

        ShipComponentState[] members = _components
            .Where(component => component.Definition.ExposureGroup == ticket.Group)
            .OrderBy(component => component.Definition.Id, StringComparer.Ordinal)
            .ToArray();
        int memberIndex = checked((int)(StableSelectionHash.Compute(
            seed,
            streamId,
            criticalSequence,
            salt: 1) % (ulong)members.Length));
        return new CriticalExposureSelection(
            members[memberIndex].Definition.Id,
            ticket.Group,
            topIndex,
            _tickets.Count,
            memberIndex,
            members.Length);
    }
}
