namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Identifies whether an interception opportunity comes from an installed
/// point-defense auxiliary or a direct-fire weapon deliberately held in
/// reserve during the preceding Direct Fire phase.
/// </summary>
public enum MissileDefenseSourceType
{
    PointDefenseSystem,
    HeldDirectFireWeapon,
}
