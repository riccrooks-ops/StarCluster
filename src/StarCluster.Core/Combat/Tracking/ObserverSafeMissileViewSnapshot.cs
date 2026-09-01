using System;
using System.Collections.Generic;
using StarCluster.Core.Combat.Missiles;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// Complete missile presentation state that is safe for one observer. Unknown
/// salvos are absent, invalid selections are cleared, and route projections do
/// not expose hidden hostile guidance.
/// </summary>
public sealed class ObserverSafeMissileViewSnapshot
{
    internal ObserverSafeMissileViewSnapshot(
        IReadOnlyList<TacticalMissileContact> contacts,
        IReadOnlyList<MissileRouteProjection> projections,
        string? selectedSalvoId)
    {
        Contacts = contacts ?? throw new ArgumentNullException(nameof(contacts));
        Projections = projections ?? throw new ArgumentNullException(nameof(projections));
        SelectedSalvoId = selectedSalvoId;
    }

    public IReadOnlyList<TacticalMissileContact> Contacts { get; }

    public IReadOnlyList<MissileRouteProjection> Projections { get; }

    public string? SelectedSalvoId { get; }
}
