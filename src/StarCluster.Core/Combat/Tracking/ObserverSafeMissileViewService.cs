using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Creates the only missile state that normal tactical presentation should
/// consume. The service filters Unknown contacts, normalizes selection, and
/// withholds exact hostile route projections unless the observer has a Firm
/// missile track.
/// </summary>
public static class ObserverSafeMissileViewService
{
    public static ObserverSafeMissileViewSnapshot Build(
        SystemMap map,
        IEnumerable<GuidedMissileSalvo> salvos,
        TacticalTrackRepository repository,
        string observerId,
        TacticalSide observerSide,
        HexCoord observerCoordinate,
        string? requestedSelectedSalvoId)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(salvos);
        ArgumentNullException.ThrowIfNull(repository);

        GuidedMissileSalvo[] salvoArray = salvos.ToArray();
        IReadOnlyList<TacticalMissileContact> contacts =
            TacticalMissileKnowledgeService.Build(
                salvoArray,
                repository,
                observerId,
                observerSide);

        string? selectedSalvoId = requestedSelectedSalvoId is not null &&
            contacts.Any(contact => string.Equals(
                contact.SalvoId,
                requestedSelectedSalvoId,
                StringComparison.Ordinal))
                ? requestedSelectedSalvoId
                : null;

        var projections = new List<MissileRouteProjection>();
        foreach (TacticalMissileContact contact in contacts)
        {
            GuidedMissileSalvo? salvo = salvoArray.FirstOrDefault(item =>
                string.Equals(item.Id, contact.SalvoId, StringComparison.Ordinal));
            if (salvo is null)
            {
                continue;
            }

            if (contact.OwnerSide == observerSide)
            {
                TacticalTrackQuality? guidanceQuality =
                    salvo.LastTrackQuality switch
                    {
                        MissileTargetTrackQuality.Current =>
                            TacticalTrackQuality.Firm,
                        MissileTargetTrackQuality.Approximate =>
                            TacticalTrackQuality.Approximate,
                        MissileTargetTrackQuality.Stale =>
                            TacticalTrackQuality.Stale,
                        _ => null,
                    };
                HexCoord? guidanceCoordinate = salvo.LastTrackQuality switch
                {
                    MissileTargetTrackQuality.Current =>
                        salvo.CurrentTrackedTargetCoordinate,
                    MissileTargetTrackQuality.Approximate or
                    MissileTargetTrackQuality.Stale =>
                        salvo.LastKnownTargetCoordinate,
                    _ => null,
                };
                projections.Add(MissileRouteProjectionService.Project(
                    map,
                    salvo,
                    contact.Coordinate,
                    guidanceQuality,
                    guidanceCoordinate));
                continue;
            }

            if (contact.TrackQuality != TacticalTrackQuality.Firm)
            {
                projections.Add(new MissileRouteProjection(
                    salvo.Id,
                    MissileRouteProjectionStatus.WithheldByObserverUncertainty,
                    contact.TrackQuality,
                    guidanceCoordinate: null,
                    routePlan: null));
                continue;
            }

            // This is explicitly an observer-side threat estimate from the
            // confirmed missile coordinate toward the observer's own known
            // coordinate. It is not the hostile missile's hidden guidance plan.
            projections.Add(MissileRouteProjectionService.Project(
                map,
                salvo,
                contact.Coordinate,
                TacticalTrackQuality.Firm,
                observerCoordinate));
        }

        return new ObserverSafeMissileViewSnapshot(
            contacts,
            Array.AsReadOnly(projections.ToArray()),
            selectedSalvoId);
    }
}
