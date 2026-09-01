namespace StarCluster.Core.Combat.InternalDamage;

public sealed record CriticalExposureSelection(
    string ComponentId,
    CriticalExposureGroup SelectedGroup,
    int TopLevelTicketIndex,
    int TopLevelTicketCount,
    int? GroupMemberIndex,
    int? GroupMemberCount);
