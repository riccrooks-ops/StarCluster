using System;
using System.Collections.Generic;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Converts authoritative salvos into observer-safe missile contacts. Own
/// salvos retain exact history; hostile salvos use only the observer's track.
/// </summary>
public static class TacticalMissileKnowledgeService
{
    public static IReadOnlyList<TacticalMissileContact> Build(
        IEnumerable<GuidedMissileSalvo> salvos,
        TacticalTrackRepository repository,
        string observerId,
        TacticalSide observerSide)
    {
        ArgumentNullException.ThrowIfNull(salvos);
        ArgumentNullException.ThrowIfNull(repository);

        if (string.IsNullOrWhiteSpace(observerId))
        {
            throw new ArgumentException(
                "An observer ID is required.",
                nameof(observerId));
        }

        var contacts = new List<TacticalMissileContact>();
        foreach (GuidedMissileSalvo salvo in salvos)
        {
            // Terminal salvos are represented by resolution cues and journal
            // events, not retained as active tactical-map missile markers.
            if (salvo.IsTerminal)
            {
                continue;
            }

            if (salvo.OwnerSide == observerSide)
            {
                contacts.Add(CreateOwnContact(salvo));
                continue;
            }

            TacticalTrackRecord? track = repository.Get(observerId, salvo.Id);
            if (track is not { IsVisibleOnTacticalMap: true })
            {
                continue;
            }

            contacts.Add(new TacticalMissileContact(
                salvo.Id,
                salvo.OwnerSide,
                salvo.LauncherId,
                salvo.TargetId,
                track.EstimatedCoordinate!.Value,
                track.Quality,
                track.UncertaintyRadiusHexes,
                salvo.Status,
                salvo.DistanceTraveled,
                salvo.TotalFuelSpent,
                salvo.Profile.MaximumRange,
                salvo.InterceptedByDefenseSystemId,
                visibleTravelHistory: track.ObservedCoordinateHistory,
                visibleTravelSegments: ObservedTravelTrailService.BuildSegments(
                    track.ObservedSamples),
                visibleLastExecutedRoute: null));
        }

        return Array.AsReadOnly(contacts.ToArray());
    }

    private static TacticalMissileContact CreateOwnContact(
        GuidedMissileSalvo salvo) =>
        new(
            salvo.Id,
            salvo.OwnerSide,
            salvo.LauncherId,
            salvo.TargetId,
            salvo.CurrentCoordinate,
            TacticalTrackQuality.Firm,
            uncertaintyRadiusHexes: 0,
            salvo.Status,
            salvo.DistanceTraveled,
            salvo.TotalFuelSpent,
            salvo.Profile.MaximumRange,
            salvo.InterceptedByDefenseSystemId,
            salvo.TravelHistory,
            visibleTravelSegments: new[]
            {
                Array.AsReadOnly(new List<HexCoord>(salvo.TravelHistory).ToArray()),
            },
            salvo.LastRoutePlan);
}
