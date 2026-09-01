using System;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Observer- and target-specific state supplied to one sensor evaluation.
/// Profiles remain immutable while active modes and jammer state may change
/// during an encounter and trigger a normal Track Update.
/// </summary>
public sealed class SensorContactEvaluationContext
{
    public SensorContactEvaluationContext(
        SensorMode observerSensorMode,
        SensorSignatureProfile targetSignature,
        SensorMode targetSensorMode = SensorMode.Passive,
        ElectronicWarfareProfile? observerElectronicWarfare = null,
        ElectronicWarfareProfile? targetElectronicWarfare = null,
        bool targetJammingEnabled = false,
        SensorEnvironmentProfile? environment = null)
    {
        if (!Enum.IsDefined(observerSensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(observerSensorMode));
        }

        if (!Enum.IsDefined(targetSensorMode))
        {
            throw new ArgumentOutOfRangeException(nameof(targetSensorMode));
        }

        ObserverSensorMode = observerSensorMode;
        TargetSignature = targetSignature ??
            throw new ArgumentNullException(nameof(targetSignature));
        TargetSensorMode = targetSensorMode;
        ObserverElectronicWarfare = observerElectronicWarfare ??
            ElectronicWarfareProfile.None;
        TargetElectronicWarfare = targetElectronicWarfare ??
            ElectronicWarfareProfile.None;
        TargetJammingEnabled = targetJammingEnabled;
        Environment = environment ?? SensorEnvironmentProfile.ClearSpace;
    }

    public static SensorContactEvaluationContext Neutral { get; } =
        new(SensorMode.Passive, SensorSignatureProfile.Neutral);

    public SensorMode ObserverSensorMode { get; }

    public SensorSignatureProfile TargetSignature { get; }

    public SensorMode TargetSensorMode { get; }

    public ElectronicWarfareProfile ObserverElectronicWarfare { get; }

    public ElectronicWarfareProfile TargetElectronicWarfare { get; }

    public bool TargetJammingEnabled { get; }

    public SensorEnvironmentProfile Environment { get; }
}
