using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Resolves the pre-combat Electronic Warfare sub-phase in two causal steps:
/// simultaneous ECM declarations first, then ECCM responses. The resolver has
/// no initiative input; movement order is already complete before this window.
/// Tactical Power commitment decisions remain the caller's responsibility.
/// </summary>
public sealed record PreCombatElectronicWarfareParticipant(
    SensorEwFoundationProfile SensorProfile,
    SensorMode SensorMode,
    bool ActiveSensorOverloaded,
    bool ActiveSensorsEnabled,
    int EcmRating,
    int EccmRating,
    bool HasLineOfSight = true);

public sealed record PreCombatElectronicWarfareTrackPair(
    SensorEwFoundationEvaluationResult SideA,
    SensorEwFoundationEvaluationResult SideB);

public static class PreCombatElectronicWarfareResolver
{
    public static PreCombatElectronicWarfareTrackPair ResolveAfterEcmDeclarations(
        int distanceHexes,
        PreCombatElectronicWarfareParticipant sideA,
        PreCombatElectronicWarfareParticipant sideB)
    {
        return Resolve(distanceHexes, sideA, sideB, includeEccmResponses: false);
    }

    public static PreCombatElectronicWarfareTrackPair ResolveAfterEccmResponses(
        int distanceHexes,
        PreCombatElectronicWarfareParticipant sideA,
        PreCombatElectronicWarfareParticipant sideB)
    {
        return Resolve(distanceHexes, sideA, sideB, includeEccmResponses: true);
    }

    private static PreCombatElectronicWarfareTrackPair Resolve(
        int distanceHexes,
        PreCombatElectronicWarfareParticipant sideA,
        PreCombatElectronicWarfareParticipant sideB,
        bool includeEccmResponses)
    {
        if (distanceHexes < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(distanceHexes));
        }
        ArgumentNullException.ThrowIfNull(sideA);
        ArgumentNullException.ThrowIfNull(sideB);
        ValidateParticipant(sideA, nameof(sideA));
        ValidateParticipant(sideB, nameof(sideB));

        SensorEwFoundationEvaluationResult observationA = EvaluateObserver(
            distanceHexes,
            sideA,
            sideB,
            includeEccmResponses ? sideA.EccmRating : 0);
        SensorEwFoundationEvaluationResult observationB = EvaluateObserver(
            distanceHexes,
            sideB,
            sideA,
            includeEccmResponses ? sideB.EccmRating : 0);

        return new PreCombatElectronicWarfareTrackPair(observationA, observationB);
    }

    private static SensorEwFoundationEvaluationResult EvaluateObserver(
        int distanceHexes,
        PreCombatElectronicWarfareParticipant observer,
        PreCombatElectronicWarfareParticipant target,
        int observerEccmRating)
    {
        return SensorEwFoundationResolver.Evaluate(
            distanceHexes,
            observer.SensorProfile,
            target.SensorProfile,
            new SensorEwFoundationEvaluationContext(
                observer.SensorMode,
                ObserverActiveSensorOverloaded: observer.ActiveSensorOverloaded,
                TargetActiveSensorsEnabled: target.ActiveSensorsEnabled,
                TargetActiveSensorOverloaded: target.ActiveSensorOverloaded,
                TargetEcmRating: target.EcmRating,
                ObserverEccmRating: observerEccmRating,
                HasLineOfSight: observer.HasLineOfSight));
    }

    private static void ValidateParticipant(
        PreCombatElectronicWarfareParticipant participant,
        string parameterName)
    {
        ArgumentNullException.ThrowIfNull(participant.SensorProfile);
        if (!Enum.IsDefined(participant.SensorMode))
        {
            throw new ArgumentOutOfRangeException(parameterName);
        }
        if (participant.EcmRating < 0 || participant.EccmRating < 0)
        {
            throw new ArgumentOutOfRangeException(parameterName);
        }
    }
}
