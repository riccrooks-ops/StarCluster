using System;
using System.Collections.Generic;
using System.Linq;
using StarCluster.Core.Combat;

namespace StarCluster.Core.Combat.Missiles;

/// <summary>
/// Authoritative collection of all retained missile salvos in one tactical
/// encounter. Terminal salvos remain available for history and presentation;
/// active queries exclude them.
/// </summary>
public sealed class MissileEngagementState
{
    private readonly List<GuidedMissileSalvo> _salvos = new();
    private readonly IReadOnlyList<GuidedMissileSalvo> _salvosView;

    public MissileEngagementState()
    {
        _salvosView = _salvos.AsReadOnly();
    }

    public IReadOnlyList<GuidedMissileSalvo> Salvos => _salvosView;

    public IReadOnlyList<GuidedMissileSalvo> ActiveSalvos =>
        Array.AsReadOnly(_salvos.Where(salvo => !salvo.IsTerminal).ToArray());

    public bool HasActiveSalvos => _salvos.Any(salvo => !salvo.IsTerminal);

    public GuidedMissileSalvo Add(GuidedMissileSalvo salvo)
    {
        ArgumentNullException.ThrowIfNull(salvo);

        if (_salvos.Any(existing =>
                string.Equals(existing.Id, salvo.Id, StringComparison.Ordinal)))
        {
            throw new ArgumentException(
                $"A missile salvo with ID '{salvo.Id}' already exists.",
                nameof(salvo));
        }

        _salvos.Add(salvo);
        return salvo;
    }

    public GuidedMissileSalvo Add(GuidedMissileLaunchResult launchResult)
    {
        ArgumentNullException.ThrowIfNull(launchResult);
        return Add(launchResult.Salvo);
    }

    public GuidedMissileSalvo? Find(string salvoId)
    {
        if (string.IsNullOrWhiteSpace(salvoId))
        {
            throw new ArgumentException(
                "A stable non-empty salvo ID is required.",
                nameof(salvoId));
        }

        return _salvos.FirstOrDefault(salvo =>
            string.Equals(salvo.Id, salvoId, StringComparison.Ordinal));
    }

    public IReadOnlyList<GuidedMissileSalvo> ForSide(TacticalSide side)
    {
        if (!Enum.IsDefined(side))
        {
            throw new ArgumentOutOfRangeException(nameof(side), side, null);
        }

        return Array.AsReadOnly(
            _salvos.Where(salvo => salvo.OwnerSide == side).ToArray());
    }

    public void Clear() => _salvos.Clear();
}
