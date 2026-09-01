using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Charted system knowledge. All stars are included automatically so neither
/// the strategic star map nor a system map can hide a visible sun.
/// </summary>
public sealed class NavigationKnowledge
{
    private readonly Dictionary<string, KnownNavigationContact> _contacts =
        new(StringComparer.Ordinal);

    public IReadOnlyList<KnownNavigationContact> Contacts =>
        Array.AsReadOnly(_contacts.Values.ToArray());

    public static NavigationKnowledge FromSystemMap(
        SystemMap map,
        IEnumerable<string>? additionallyChartedObjectIds = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        var knowledge = new NavigationKnowledge();
        HashSet<string> additional = additionallyChartedObjectIds is null
            ? new HashSet<string>(StringComparer.Ordinal)
            : new HashSet<string>(
                additionallyChartedObjectIds,
                StringComparer.Ordinal);

        foreach (MapCell cell in map.Cells)
        {
            foreach (MapObject mapObject in cell.Occupants)
            {
                if (mapObject.Kind == MapObjectKind.Star ||
                    additional.Contains(mapObject.Id))
                {
                    knowledge._contacts[mapObject.Id] =
                        new KnownNavigationContact(
                            mapObject.Id,
                            mapObject.Name,
                            mapObject.Kind,
                            cell.Coordinate);
                }
            }
        }

        return knowledge;
    }

    public bool IsKnown(string objectId)
    {
        if (string.IsNullOrWhiteSpace(objectId))
        {
            throw new ArgumentException("An object ID is required.", nameof(objectId));
        }

        return _contacts.ContainsKey(objectId);
    }

    public KnownNavigationContact? Get(string objectId)
    {
        if (string.IsNullOrWhiteSpace(objectId))
        {
            throw new ArgumentException("An object ID is required.", nameof(objectId));
        }

        return _contacts.TryGetValue(objectId, out KnownNavigationContact? contact)
            ? contact
            : null;
    }
}
