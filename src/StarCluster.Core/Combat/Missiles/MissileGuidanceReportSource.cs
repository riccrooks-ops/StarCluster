namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Provenance of the report used for one missile guidance action.
/// Includes launcher copies, retained copies, future live peer-guidance reports, and missile-local onboard sensor reports.
/// </summary>
public enum MissileGuidanceReportSource
{
    None,
    FreshDatalink,
    RetainedDatalink,
    PeerGuidance,
    LocalSensor,
}
