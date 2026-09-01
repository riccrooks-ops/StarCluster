using System;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;

namespace StarCluster.Game;

/// <summary>
/// Evaluates held direct-fire interception against current tactical sensors.
/// PDS systems use their own local acquisition and do not request this gate.
/// </summary>
public sealed class DemoMissileDefenseTrackProvider : IMissileDefenseTrackProvider
{
    private readonly DemoScenario _scenario;
    private readonly SensorProfile _sensorProfile;
    private readonly Func<SensorContactEvaluationContext>
        _evaluationContextProvider;

    public DemoMissileDefenseTrackProvider(
        DemoScenario scenario,
        SensorProfile sensorProfile,
        SensorContactEvaluationContext? evaluationContext = null)
        : this(
            scenario,
            sensorProfile,
            () => evaluationContext ?? SensorContactEvaluationContext.Neutral)
    {
    }

    public DemoMissileDefenseTrackProvider(
        DemoScenario scenario,
        SensorProfile sensorProfile,
        Func<SensorContactEvaluationContext> evaluationContextProvider)
    {
        _scenario = scenario ?? throw new ArgumentNullException(nameof(scenario));
        _sensorProfile = sensorProfile ??
            throw new ArgumentNullException(nameof(sensorProfile));
        _evaluationContextProvider = evaluationContextProvider ??
            throw new ArgumentNullException(nameof(evaluationContextProvider));
    }

    public bool HasUsableTrack(
        MissileDefenseSystem defenseSystem,
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate)
    {
        SensorContactEvaluationResult evaluation = SensorContactEvaluator.Evaluate(
            _scenario.Map,
            salvo.Id,
            defenseSystem.Coordinate,
            missileCoordinate,
            _sensorProfile,
            _evaluationContextProvider());
        return evaluation.Observation.Detected &&
            evaluation.Observation.Precise;
    }
}
