using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Core.Combat.Tracking;

/// <summary>
/// One object safe for an observer's tactical presentation. Its coordinate is
/// charted or track-derived and is not automatically the authoritative truth.
/// </summary>
public sealed class TacticalMapContact
{
    internal TacticalMapContact(
        string objectId,
        string name,
        MapObjectKind kind,
        HexCoord coordinate,
        TacticalMapContactSource source,
        TacticalTrackQuality? trackQuality,
        int uncertaintyRadiusHexes)
    {
        ObjectId = objectId;
        Name = name;
        Kind = kind;
        Coordinate = coordinate;
        Source = source;
        TrackQuality = trackQuality;
        UncertaintyRadiusHexes = uncertaintyRadiusHexes;
    }

    public string ObjectId { get; }

    public string Name { get; }

    public MapObjectKind Kind { get; }

    public HexCoord Coordinate { get; }

    public TacticalMapContactSource Source { get; }

    public TacticalTrackQuality? TrackQuality { get; }

    public int UncertaintyRadiusHexes { get; }
}
