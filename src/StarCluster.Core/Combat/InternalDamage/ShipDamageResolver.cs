using StarCluster.Core.Combat.Damage;

namespace StarCluster.Core.Combat.InternalDamage;

public static class ShipDamageResolver
{
    public static ShipDamageResolution ResolvePacket(
        ShipDamageState ship,
        AttackPacket packet,
        bool precisionCritical = false)
    {
        ArgumentNullException.ThrowIfNull(ship);
        ArgumentNullException.ThrowIfNull(packet);
        if (ship.IsDestroyed)
        {
            throw new InvalidOperationException(
                "A finalized Destroyed ship cannot receive another combat packet.");
        }

        bool wasPending = ship.IsPendingDestruction;
        LayeredDamageResolution layered = LayeredDamageResolver.Resolve(
            ship.Defense,
            packet);
        var events = new List<InternalDamageEvent>();
        for (int point = 0; point < layered.HullDamage; point++)
        {
            int position = ship.AdvanceInternalPosition();
            InternalMarkerKind marker = ship.InternalTrack.MarkerAt(position);
            if (marker == InternalMarkerKind.Critical)
            {
                var result = ship.ApplyCritical("internal-critical");
                events.Add(new InternalDamageEvent(
                    position,
                    marker,
                    result.Selection,
                    result.Transition,
                    PrecisionCritical: false));
            }
            else
            {
                events.Add(new InternalDamageEvent(
                    position,
                    marker,
                    null,
                    null,
                    PrecisionCritical: false));
            }
        }

        if (precisionCritical)
        {
            var result = ship.ApplyCritical("precision-critical");
            events.Add(new InternalDamageEvent(
                ship.InternalPositionsCrossed,
                InternalMarkerKind.Critical,
                result.Selection,
                result.Transition,
                PrecisionCritical: true));
        }

        if (ship.Defense.CurrentHull == 0)
        {
            ship.MarkPendingDestruction();
        }

        return new ShipDamageResolution(
            layered,
            events.AsReadOnly(),
            !wasPending && ship.IsPendingDestruction,
            ship.CapabilitySnapshot.Condition);
    }
}
