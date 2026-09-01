using System;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Creates a guided salvo and resolves exactly one Missile / Interception
/// movement advance. The service deliberately performs no fast-forward loop.
/// </summary>
public static class MissileLaunchService
{
    /// <summary>
    /// Compatibility overload for pre-ownership callers.
    /// </summary>
    public static GuidedMissileLaunchResult LaunchAndAdvanceOnePhase(
        SystemMap map,
        string salvoId,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile profile,
        MissileTargetTrackSnapshot targetTrack) =>
        LaunchAndAdvanceOnePhase(
            map,
            salvoId,
            TacticalSide.Unspecified,
            launcherId,
            targetId,
            launchCoordinate,
            profile,
            targetTrack,
            interceptionContext: null);

    public static GuidedMissileLaunchResult LaunchAndAdvanceOnePhase(
        SystemMap map,
        string salvoId,
        TacticalSide ownerSide,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile profile,
        MissileTargetTrackSnapshot targetTrack,
        MissileInterceptionPhaseContext? interceptionContext = null,
        MissileTerminalProfile? terminalProfile = null,
        IMissileTerminalRandomSource? terminalRandomSource = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(targetTrack);

        var salvo = new GuidedMissileSalvo(
            salvoId,
            ownerSide,
            launcherId,
            targetId,
            launchCoordinate,
            profile,
            terminalProfile ?? MissileTerminalProfile.Prototype);

        GuidedMissileAdvanceResult advanceResult =
            MissileGuidanceService.AdvanceOnePhase(
                map,
                salvo,
                targetTrack,
                interceptionContext,
                terminalRandomSource);

        return new GuidedMissileLaunchResult(salvo, advanceResult);
    }

    /// <summary>
    /// Creates a salvo, copies any report delivered through the launcher's
    /// datalink, and guides only from the missile-owned retained copy.
    /// </summary>
    public static GuidedMissileLaunchResult LaunchAndAdvanceOnePhase(
        SystemMap map,
        string salvoId,
        TacticalSide ownerSide,
        string launcherId,
        string targetId,
        HexCoord launchCoordinate,
        MissileFlightProfile profile,
        MissileDatalinkProfile datalinkProfile,
        MissileTargetTrackSnapshot launcherTrack,
        int sourceObservationEpoch,
        MissileInterceptionPhaseContext? interceptionContext = null,
        MissileTerminalProfile? terminalProfile = null,
        IMissileTerminalRandomSource? terminalRandomSource = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(datalinkProfile);
        ArgumentNullException.ThrowIfNull(launcherTrack);

        var salvo = new GuidedMissileSalvo(
            salvoId,
            ownerSide,
            launcherId,
            targetId,
            launchCoordinate,
            profile,
            terminalProfile ?? MissileTerminalProfile.Prototype);

        MissileDatalinkUpdateResult datalinkUpdateResult =
            MissileDatalinkService.UpdateForGuidancePhase(
                map,
                salvo,
                datalinkProfile,
                launchCoordinate,
                launcherTrack,
                sourceObservationEpoch);
        GuidedMissileAdvanceResult advanceResult =
            MissileGuidanceService.AdvanceOnePhase(
                map,
                salvo,
                datalinkUpdateResult.GuidanceSnapshot,
                interceptionContext,
                terminalRandomSource);

        return new GuidedMissileLaunchResult(
            salvo,
            advanceResult,
            datalinkUpdateResult);
    }

    /// <summary>
    /// Creates a salvo with a launcher datalink and onboard navigation sensor,
    /// then resolves one per-entered-hex autonomous guidance action.
    /// </summary>
    public static GuidedMissileAutonomousLaunchResult
        LaunchAndAdvanceAutonomousOnePhase(
            SystemMap map,
            string salvoId,
            TacticalSide ownerSide,
            string launcherId,
            string targetId,
            HexCoord launchCoordinate,
            MissileFlightProfile profile,
            MissileDatalinkProfile datalinkProfile,
            MissileTargetTrackSnapshot launcherTrack,
            int sourceObservationEpoch,
            MissileSensorProfile sensorProfile,
            HexCoord targetCoordinate,
            SensorSignatureProfile targetSignature,
            SensorMode targetSensorMode,
            ElectronicWarfareProfile targetElectronicWarfare,
            bool targetJammingEnabled,
            SensorEnvironmentProfile environment,
            MissileInterceptionPhaseContext? interceptionContext = null,
            MissileTerminalProfile? terminalProfile = null,
            IMissileTerminalRandomSource? terminalRandomSource = null)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(datalinkProfile);
        ArgumentNullException.ThrowIfNull(launcherTrack);
        ArgumentNullException.ThrowIfNull(sensorProfile);
        ArgumentNullException.ThrowIfNull(targetSignature);
        ArgumentNullException.ThrowIfNull(targetElectronicWarfare);
        ArgumentNullException.ThrowIfNull(environment);

        var salvo = new GuidedMissileSalvo(
            salvoId,
            ownerSide,
            launcherId,
            targetId,
            launchCoordinate,
            profile,
            terminalProfile ?? MissileTerminalProfile.Prototype);
        MissileDatalinkUpdateResult datalinkUpdate =
            MissileDatalinkService.UpdateForGuidancePhase(
                map,
                salvo,
                datalinkProfile,
                launchCoordinate,
                launcherTrack,
                sourceObservationEpoch);
        MissileAutonomousGuidanceResult autonomous =
            MissileAutonomousGuidanceService.AdvanceOnePhase(
                map,
                salvo,
                datalinkUpdate,
                sensorProfile,
                targetCoordinate,
                targetSignature,
                targetSensorMode,
                targetElectronicWarfare,
                targetJammingEnabled,
                environment,
                sourceObservationEpoch,
                interceptionContext,
                terminalRandomSource);

        return new GuidedMissileAutonomousLaunchResult(
            salvo,
            datalinkUpdate,
            autonomous);
    }

}
