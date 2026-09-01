namespace StarCluster.Core.Combat.InternalDamage;

public sealed record ShipComponentDefinition
{
    public ShipComponentDefinition(
        string id,
        ShipComponentKind kind,
        int criticalExposure,
        CriticalExposureGroup exposureGroup = CriticalExposureGroup.None,
        ShipComponentCapability capabilities = ShipComponentCapability.None)
    {
        if (string.IsNullOrWhiteSpace(id))
        {
            throw new ArgumentException("A stable component ID is required.", nameof(id));
        }
        if (!Enum.IsDefined(kind))
        {
            throw new ArgumentOutOfRangeException(nameof(kind));
        }
        if (criticalExposure < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(criticalExposure));
        }
        if (!Enum.IsDefined(exposureGroup))
        {
            throw new ArgumentOutOfRangeException(nameof(exposureGroup));
        }
        if (criticalExposure > 0 && exposureGroup != CriticalExposureGroup.None)
        {
            throw new ArgumentException(
                "A component cannot have both direct Critical Exposure and grouped exposure.",
                nameof(criticalExposure));
        }

        Id = id;
        Kind = kind;
        CriticalExposure = criticalExposure;
        ExposureGroup = exposureGroup;
        Capabilities = capabilities;
    }

    public string Id { get; }

    public ShipComponentKind Kind { get; }

    public int CriticalExposure { get; }

    public CriticalExposureGroup ExposureGroup { get; }

    public ShipComponentCapability Capabilities { get; }
}
