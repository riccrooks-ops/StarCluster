using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Builds a player-safe map snapshot from navigation data, own assets, and
/// observer-specific tracks. Unknown and Lost contacts do not leak through.
/// </summary>
public static class TacticalMapKnowledgeService
{
    public static TacticalMapKnowledgeSnapshot Build(
        SystemMap map,
        NavigationKnowledge navigationKnowledge,
        TacticalTrackRepository trackRepository,
        string observerId,
        IEnumerable<string> ownObjectIds,
        long trackSequence)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(navigationKnowledge);
        ArgumentNullException.ThrowIfNull(trackRepository);
        ArgumentNullException.ThrowIfNull(ownObjectIds);

        var ownIds = new HashSet<string>(ownObjectIds, StringComparer.Ordinal);
        var authoritative = new Dictionary<string, (MapObject Object, HexCoord Coordinate)>(
            StringComparer.Ordinal);

        foreach (MapCell cell in map.Cells)
        {
            foreach (MapObject mapObject in cell.Occupants)
            {
                authoritative[mapObject.Id] = (mapObject, cell.Coordinate);
            }
        }

        var contacts = new Dictionary<string, TacticalMapContact>(
            StringComparer.Ordinal);

        foreach (KnownNavigationContact known in navigationKnowledge.Contacts)
        {
            contacts[known.ObjectId] = new TacticalMapContact(
                known.ObjectId,
                known.Name,
                known.Kind,
                known.Coordinate,
                TacticalMapContactSource.NavigationKnowledge,
                trackQuality: null,
                uncertaintyRadiusHexes: 0);
        }

        foreach (string ownId in ownIds)
        {
            if (authoritative.TryGetValue(ownId, out var own))
            {
                contacts[ownId] = new TacticalMapContact(
                    ownId,
                    own.Object.Name,
                    own.Object.Kind,
                    own.Coordinate,
                    TacticalMapContactSource.OwnAsset,
                    TacticalTrackQuality.Firm,
                    uncertaintyRadiusHexes: 0);
            }
        }

        foreach (TacticalTrackRecord record in trackRepository.ForObserver(observerId))
        {
            if (!record.IsVisibleOnTacticalMap ||
                !authoritative.TryGetValue(record.TargetId, out var target))
            {
                continue;
            }

            contacts[record.TargetId] = new TacticalMapContact(
                record.TargetId,
                target.Object.Name,
                target.Object.Kind,
                record.EstimatedCoordinate!.Value,
                TacticalMapContactSource.SensorTrack,
                record.Quality,
                record.UncertaintyRadiusHexes);
        }

        return new TacticalMapKnowledgeSnapshot(
            observerId,
            contacts.Values,
            trackSequence);
    }
}
