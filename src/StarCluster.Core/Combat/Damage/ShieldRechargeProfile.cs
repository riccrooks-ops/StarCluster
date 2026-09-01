using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Damage;

public sealed record ShieldRechargeProfile
{
    public ShieldRechargeProfile(
        int operationalBaseRecharge,
        int tacticalRechargePerPower,
        int operationalTacticalPowerCap,
        int degradedBaseRecharge,
        int degradedTacticalPowerCap)
    {
        if (operationalBaseRecharge < 0 || tacticalRechargePerPower <= 0 ||
            operationalTacticalPowerCap < 0 || degradedBaseRecharge < 0 ||
            degradedTacticalPowerCap < 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(operationalBaseRecharge),
                "Shield recharge values must be non-negative and the tactical rate must be positive.");
        }

        OperationalBaseRecharge = operationalBaseRecharge;
        TacticalRechargePerPower = tacticalRechargePerPower;
        OperationalTacticalPowerCap = operationalTacticalPowerCap;
        DegradedBaseRecharge = degradedBaseRecharge;
        DegradedTacticalPowerCap = degradedTacticalPowerCap;
    }

    public int OperationalBaseRecharge { get; }

    public int TacticalRechargePerPower { get; }

    public int OperationalTacticalPowerCap { get; }

    public int DegradedBaseRecharge { get; }

    public int DegradedTacticalPowerCap { get; }

    public int BaseRechargeFor(ComponentCondition condition) => condition switch
    {
        ComponentCondition.Operational => OperationalBaseRecharge,
        ComponentCondition.Degraded => DegradedBaseRecharge,
        ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
        _ => throw new ArgumentOutOfRangeException(nameof(condition)),
    };

    public int TacticalPowerCapFor(ComponentCondition condition) => condition switch
    {
        ComponentCondition.Operational => OperationalTacticalPowerCap,
        ComponentCondition.Degraded => DegradedTacticalPowerCap,
        ComponentCondition.Disabled or ComponentCondition.Destroyed => 0,
        _ => throw new ArgumentOutOfRangeException(nameof(condition)),
    };
}
