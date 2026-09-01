using System;
using System.Collections.Generic;
using System.Linq;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Groups observer-visible missile contacts without merging their identities.
/// Friendly and hostile salvos at the same coordinate remain separate stacks.
/// </summary>
public static class TacticalMissileStackService
{
    public static IReadOnlyList<TacticalMissileContactStack> Build(
        IEnumerable<TacticalMissileContact> contacts)
    {
        ArgumentNullException.ThrowIfNull(contacts);

        TacticalMissileContactStack[] stacks = contacts
            .GroupBy(contact => new
            {
                contact.Coordinate,
                contact.OwnerSide,
            })
            .Select(group => new TacticalMissileContactStack(
                group.Key.Coordinate,
                group.Key.OwnerSide,
                group))
            .OrderBy(stack => stack.Coordinate.Q)
            .ThenBy(stack => stack.Coordinate.R)
            .ThenBy(stack => stack.OwnerSide)
            .ToArray();

        return Array.AsReadOnly(stacks);
    }
}
