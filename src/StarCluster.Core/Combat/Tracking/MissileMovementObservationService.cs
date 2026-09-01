using System;
using System.Collections.Generic;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Applies observer detection checks at the launch origin when the launch was
/// observed and after every entered missile hex. The first detected coordinate
/// begins a visible trail segment; a missed coordinate closes it; reacquisition
/// starts a new segment even within the same tactical turn.
/// </summary>
public static class MissileMovementObservationService
{
    public static MissileMovementObservationResult Apply(
        SystemMap map,
        TacticalTrackRepository repository,
        string observerId,
        HexCoord observerCoordinate,
        GuidedMissileSalvo salvo,
        IReadOnlyList<HexCoord> enteredCoordinates,
        SensorProfile sensorProfile,
        ComputingProfile computingProfile,
        long startingSequence,
        TrackUpdateTrigger trigger,
        int observationEpoch,
        bool launchObservedAtOrigin,
        SensorContactEvaluationContext? evaluationContext = null,
        ISensorContactResolutionPolicy? resolutionPolicy = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(repository);
        ArgumentNullException.ThrowIfNull(salvo);
        ArgumentNullException.ThrowIfNull(enteredCoordinates);
        ArgumentNullException.ThrowIfNull(sensorProfile);
        ArgumentNullException.ThrowIfNull(computingProfile);

        if (string.IsNullOrWhiteSpace(observerId))
        {
            throw new ArgumentException("An observer ID is required.", nameof(observerId));
        }

        if (startingSequence < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(startingSequence));
        }

        if (observationEpoch <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(observationEpoch));
        }

        var points = new List<(HexCoord Coordinate, bool IsLaunchOrigin)>();
        if (launchObservedAtOrigin)
        {
            points.Add((salvo.LaunchCoordinate, true));
        }
        foreach (HexCoord coordinate in enteredCoordinates)
        {
            points.Add((coordinate, false));
        }

        var steps = new List<MissileMovementObservationStep>();
        var updates = new List<TacticalTrackUpdateResult>();
        long sequence = startingSequence;

        foreach ((HexCoord coordinate, bool isLaunchOrigin) in points)
        {
            TacticalTrackRecord? before = repository.Get(observerId, salvo.Id);
            bool segmentWasOpen = before?.HasOpenObservedSegment == true;
            TacticalTrackObservation observation = isLaunchOrigin
                ? TacticalTrackObservation.Firm(
                    salvo.Id,
                    coordinate,
                    TacticalTrackSourceType.ObservedLaunch)
                : SensorContactEvaluator.Evaluate(
                    map,
                    salvo.Id,
                    observerCoordinate,
                    coordinate,
                    sensorProfile,
                    evaluationContext ?? SensorContactEvaluationContext.Neutral,
                    resolutionPolicy).Observation;

            sequence++;
            TacticalTrackUpdateResult update = TacticalTrackUpdateService.Apply(
                repository,
                observerId,
                observation,
                computingProfile,
                sequence,
                trigger,
                observationEpoch);
            updates.Add(update);

            TacticalTrackRecord? after = repository.Get(observerId, salvo.Id);
            bool segmentIsOpen = after?.HasOpenObservedSegment == true;
            bool segmentStarted = observation.Detected && !segmentWasOpen && segmentIsOpen;
            bool segmentExtended = observation.Detected && segmentWasOpen && segmentIsOpen;
            bool segmentClosed = !observation.Detected && segmentWasOpen && !segmentIsOpen;

            steps.Add(new MissileMovementObservationStep(
                coordinate,
                isLaunchOrigin,
                observation.Detected,
                segmentStarted,
                segmentExtended,
                segmentClosed,
                observation.Detected ? after?.Quality : null));
        }

        return new MissileMovementObservationResult(steps, updates, sequence);
    }
}
