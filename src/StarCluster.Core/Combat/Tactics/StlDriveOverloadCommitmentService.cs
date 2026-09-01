using StarCluster.Core.Combat.Components;

namespace StarCluster.Core.Combat.Tactics;

/// <summary>
/// Represents the pre-Movement commitment required to preserve the option to
/// execute an STL overload after movement order is known. Standing down does
/// not refund the committed Tactical Power and does not heal existing Strain.
/// </summary>
public sealed record StlDriveOverloadCommitment(
    bool Prepared,
    int TacticalPowerCommitted,
    string Reason);

public sealed record StlDriveOverloadStandDownResult(
    bool StoodDown,
    int TacticalPowerCommitted,
    int OverloadFuelSpent,
    int StrainApplied,
    int StrainRemoved,
    string Reason);

public static class StlDriveOverloadCommitmentService
{
    public static StlDriveOverloadCommitment Prepare(
        StlDriveOverloadProfile profile,
        ComponentCondition driveCondition,
        int availableTacticalPower)
    {
        ArgumentNullException.ThrowIfNull(profile);
        if (availableTacticalPower < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(availableTacticalPower));
        }
        if (driveCondition != ComponentCondition.Operational)
        {
            return new StlDriveOverloadCommitment(
                Prepared: false,
                TacticalPowerCommitted: 0,
                "Only an Operational STL Drive may prepare an overload.");
        }
        if (availableTacticalPower < profile.TacticalPowerCost)
        {
            return new StlDriveOverloadCommitment(
                Prepared: false,
                TacticalPowerCommitted: 0,
                "Insufficient Tactical Power to prepare STL overload.");
        }

        return new StlDriveOverloadCommitment(
            Prepared: true,
            TacticalPowerCommitted: profile.TacticalPowerCost,
            "STL overload power is committed before Movement; execution remains optional when the ship moves.");
    }

    public static StlDriveOverloadStandDownResult StandDown(
        StlDriveOverloadCommitment commitment,
        int currentStrain)
    {
        ArgumentNullException.ThrowIfNull(commitment);
        if (currentStrain < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(currentStrain));
        }
        if (!commitment.Prepared)
        {
            throw new InvalidOperationException(
                "An STL overload must be prepared before it can be stood down.");
        }

        return new StlDriveOverloadStandDownResult(
            StoodDown: true,
            TacticalPowerCommitted: commitment.TacticalPowerCommitted,
            OverloadFuelSpent: 0,
            StrainApplied: 0,
            StrainRemoved: 0,
            "Prepared STL overload was stood down: committed power remains locked, but no overload fuel or Strain is applied and existing Strain is unchanged.");
    }
}
