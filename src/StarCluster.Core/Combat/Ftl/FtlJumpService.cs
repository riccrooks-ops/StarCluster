using StarCluster.Core.Combat.Components;
using StarCluster.Core.Combat.InternalDamage;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Power;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Ftl;

public enum FtlJumpType
{
    Regular = 0,
    Emergency = 1,
}

public sealed record FtlPowerUpSignature(
    bool DetectedByEveryoneOnMap,
    bool RevealsLocation,
    bool RevealsIdentity,
    bool RevealsDestination,
    bool RevealsJumpType);

public sealed record FtlJumpDeclarationResult(
    FtlJumpType JumpType,
    HexCoord Origin,
    int DedicatedTacticalPower,
    int OutboundMissileFlightsSelfDestructed,
    FtlPowerUpSignature Signature,
    bool ExecutesAtNextTurnRefresh,
    bool OnlyShipOrFtlDestructionCanCancel);

public sealed class PoweredFtlJump
{
    internal PoweredFtlJump(FtlJumpDeclarationResult declaration)
    {
        Declaration = declaration;
    }

    public FtlJumpDeclarationResult Declaration { get; }

    public bool IsResolved { get; private set; }

    public bool Succeeded { get; private set; }

    public bool Execute(bool shipDestroyed, ComponentCondition ftlCondition)
    {
        if (IsResolved)
        {
            throw new InvalidOperationException("The powered FTL jump is already resolved.");
        }
        IsResolved = true;
        Succeeded = !shipDestroyed &&
            ftlCondition != ComponentCondition.Destroyed;
        return Succeeded;
    }
}

public static class FtlJumpService
{
    public static PoweredFtlJump Declare(
        FtlJumpType jumpType,
        HexMap map,
        HexCoord origin,
        IEnumerable<HexCoord> celestialBodies,
        bool knowinglyEngaged,
        ComponentCondition ftlCondition,
        bool isPlayerShip,
        TacticalPowerLedger power,
        IEnumerable<GuidedMissileSalvo> outboundMissiles)
    {
        ArgumentNullException.ThrowIfNull(map);
        ArgumentNullException.ThrowIfNull(celestialBodies);
        ArgumentNullException.ThrowIfNull(power);
        ArgumentNullException.ThrowIfNull(outboundMissiles);
        if (!Enum.IsDefined(jumpType))
        {
            throw new ArgumentOutOfRangeException(nameof(jumpType));
        }
        if (!Enum.IsDefined(ftlCondition))
        {
            throw new ArgumentOutOfRangeException(nameof(ftlCondition));
        }
        if (!map.Contains(origin))
        {
            throw new ArgumentOutOfRangeException(nameof(origin));
        }
        if (ftlCondition == ComponentCondition.Destroyed)
        {
            throw new InvalidOperationException("A Destroyed FTL drive cannot jump.");
        }
        if (jumpType == FtlJumpType.Regular)
        {
            if (knowinglyEngaged)
            {
                throw new InvalidOperationException(
                    "A known contested departure requires an Emergency FTL jump.");
            }
            if (ftlCondition == ComponentCondition.Disabled)
            {
                throw new InvalidOperationException(
                    "A Disabled FTL drive can perform only the player Emergency Egress jump.");
            }
            if (!JumpPerimeterService.IsLegalRegularJumpHex(
                    map,
                    origin,
                    celestialBodies))
            {
                throw new InvalidOperationException(
                    "A regular FTL jump must begin from a legal Jump Perimeter hex.");
            }
        }
        else if (ftlCondition == ComponentCondition.Disabled && !isPlayerShip)
        {
            throw new InvalidOperationException(
                "The one-hex Disabled-drive Emergency Egress rule is player-only.");
        }

        if (power.PoweredPower != 0 ||
            power.SpentPower != 0 ||
            power.EarmarkedPower != 0)
        {
            throw new InvalidOperationException(
                "FTL power-up must be declared before allocating Tactical Power elsewhere.");
        }

        int dedicated = power.AvailablePower;
        if (dedicated <= 0)
        {
            throw new InvalidOperationException(
                "FTL power-up requires at least one available Tactical Power point.");
        }
        power.IncreasePoweredSystem("ftl-jump", dedicated);
        int terminated = MissileFlightTerminationService.TerminateForFtlPowerUp(
            outboundMissiles);
        var declaration = new FtlJumpDeclarationResult(
            jumpType,
            origin,
            dedicated,
            terminated,
            new FtlPowerUpSignature(
                DetectedByEveryoneOnMap: true,
                RevealsLocation: false,
                RevealsIdentity: false,
                RevealsDestination: false,
                RevealsJumpType: false),
            ExecutesAtNextTurnRefresh: true,
            OnlyShipOrFtlDestructionCanCancel: true);
        return new PoweredFtlJump(declaration);
    }
}
