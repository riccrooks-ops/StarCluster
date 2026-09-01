using StarCluster.Core.Combat.Damage;

namespace StarCluster.Core.Combat.InternalDamage;

public sealed record InternalDamageEvent(
    int InternalPosition,
    InternalMarkerKind Marker,
    CriticalExposureSelection? Selection,
    ComponentConditionTransition? Transition,
    bool PrecisionCritical);

public sealed record ShipDamageResolution(
    LayeredDamageResolution LayeredDamage,
    IReadOnlyList<InternalDamageEvent> InternalEvents,
    bool BecamePendingDestruction,
    ShipCondition ConditionAfterPacket);
