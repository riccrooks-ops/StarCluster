using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Player-visible group of tracked missile contacts that share one coordinate
/// and ownership side. The stack is a presentation aid; salvos remain distinct
/// authoritative entities and can be selected individually.
/// </summary>
public sealed class TacticalMissileContactStack
{
    internal TacticalMissileContactStack(
        HexCoord coordinate,
        TacticalSide ownerSide,
        IEnumerable<TacticalMissileContact> contacts)
    {
        ArgumentNullException.ThrowIfNull(contacts);
        if (ownerSide == TacticalSide.Unspecified)
        {
            throw new ArgumentOutOfRangeException(nameof(ownerSide));
        }

        TacticalMissileContact[] copied = contacts
            .OrderBy(contact => contact.SalvoId, StringComparer.Ordinal)
            .ToArray();
        if (copied.Length == 0)
        {
            throw new ArgumentException(
                "A missile-contact stack requires at least one contact.",
                nameof(contacts));
        }

        if (copied.Any(contact =>
                contact.Coordinate != coordinate ||
                contact.OwnerSide != ownerSide))
        {
            throw new ArgumentException(
                "Every contact in a stack must share its coordinate and owner side.",
                nameof(contacts));
        }

        Coordinate = coordinate;
        OwnerSide = ownerSide;
        Contacts = Array.AsReadOnly(copied);
    }

    public HexCoord Coordinate { get; }

    public TacticalSide OwnerSide { get; }

    public IReadOnlyList<TacticalMissileContact> Contacts { get; }

    public int Count => Contacts.Count;

    public bool IsStacked => Count > 1;

    public string DisplaySymbol => OwnerSide switch
    {
        TacticalSide.Player => "F",
        TacticalSide.Enemy => "E",
        _ => "M",
    };
}
