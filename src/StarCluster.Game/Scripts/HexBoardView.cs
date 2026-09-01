using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using StarCluster.Core.Movement;

namespace StarCluster.Game;

/// <summary>
/// Draws one logical <see cref="SystemMap"/> using simple prototype geometry.
/// No drawing calculation is authoritative game state.
/// </summary>
public partial class HexBoardView : Control
{
    private static readonly float SqrtThree = MathF.Sqrt(3.0f);

    private DemoScenario? _scenario;
    private DirectFireLineOfSightResult? _lineOfSight;
    private MissileRouteResult? _missileRoute;
    private IReadOnlyList<TacticalMissileContact> _missileContacts =
        Array.Empty<TacticalMissileContact>();
    private IReadOnlyList<MissileRouteProjection> _missileProjections =
        Array.Empty<MissileRouteProjection>();
    private IReadOnlyList<TacticalMapContact> _mapContacts =
        Array.Empty<TacticalMapContact>();
    private IReadOnlyList<TacticalResolutionCue> _resolutionCues =
        Array.Empty<TacticalResolutionCue>();
    private bool _showDirectFireLine;
    private string? _selectedMissileSalvoId;
    private bool _selectedMissileIsWeaponTarget;
    private bool _showStaticMissileRoute;
    private HashSet<HexCoord> _legalMovementDestinations = new();
    private ShipMovementResult? _movementPreview;
    private HexCoord? _hoveredCoordinate;
    private HexCoord? _inspectedCoordinate;
    private float _hexSize = 36.0f;
    private Vector2 _boardOffset;

    public event Action<HexCoord?>? HoveredHexChanged;

    public event Action<HexCoord>? HexClicked;

    public TargetingMode DisplayMode { get; set; } = TargetingMode.DirectFire;

    public bool ShowCoordinates { get; set; } = true;

    public override void _Ready()
    {
        MouseFilter = MouseFilterEnum.Stop;
        ClipContents = true;
        Resized += QueueRedraw;
        MouseExited += OnMouseExited;
    }

    public override Vector2 _GetMinimumSize() => new(420.0f, 420.0f);

    public void SetScenario(
        DemoScenario scenario,
        DirectFireLineOfSightResult lineOfSight,
        MissileRouteResult missileRoute)
    {
        _scenario = scenario ?? throw new ArgumentNullException(nameof(scenario));
        _lineOfSight = lineOfSight ??
            throw new ArgumentNullException(nameof(lineOfSight));
        _missileRoute = missileRoute ??
            throw new ArgumentNullException(nameof(missileRoute));
        _missileContacts = Array.Empty<TacticalMissileContact>();
        _missileProjections = Array.Empty<MissileRouteProjection>();
        _mapContacts = Array.Empty<TacticalMapContact>();
        _resolutionCues = Array.Empty<TacticalResolutionCue>();
        _showDirectFireLine = false;
        _selectedMissileSalvoId = null;
        _selectedMissileIsWeaponTarget = false;
        _showStaticMissileRoute = false;
        _legalMovementDestinations.Clear();
        _movementPreview = null;
        _hoveredCoordinate = null;
        _inspectedCoordinate = null;
        QueueRedraw();
    }

    public void SetMissileState(
        IEnumerable<TacticalMissileContact> contacts,
        IEnumerable<MissileRouteProjection> projections,
        string? selectedSalvoId,
        bool selectedAsWeaponTarget,
        bool showStaticRoute)
    {
        ArgumentNullException.ThrowIfNull(contacts);
        ArgumentNullException.ThrowIfNull(projections);
        _missileContacts = Array.AsReadOnly(contacts.ToArray());
        _missileProjections = Array.AsReadOnly(projections.ToArray());
        _selectedMissileSalvoId = selectedSalvoId;
        _selectedMissileIsWeaponTarget = selectedAsWeaponTarget;
        _showStaticMissileRoute = showStaticRoute;
        QueueRedraw();
    }

    public void SetInspectedCoordinate(HexCoord? coordinate)
    {
        _inspectedCoordinate = coordinate;
        QueueRedraw();
    }

    public void SetResolutionCues(
        IEnumerable<TacticalResolutionCue> cues)
    {
        ArgumentNullException.ThrowIfNull(cues);
        _resolutionCues = Array.AsReadOnly(cues.ToArray());
        QueueRedraw();
    }

    public void SetKnowledgeState(
        TacticalMapKnowledgeSnapshot snapshot,
        bool showDirectFireLine)
    {
        ArgumentNullException.ThrowIfNull(snapshot);
        _mapContacts = snapshot.Contacts;
        _showDirectFireLine = showDirectFireLine;
        QueueRedraw();
    }

    public void SetMovementOverlay(
        IEnumerable<HexCoord> legalDestinations,
        ShipMovementResult? preview)
    {
        ArgumentNullException.ThrowIfNull(legalDestinations);
        _legalMovementDestinations = new HashSet<HexCoord>(legalDestinations);
        _movementPreview = preview;
        QueueRedraw();
    }

    public void RefreshDisplay() => QueueRedraw();

    public override void _GuiInput(InputEvent @event)
    {
        if (_scenario is null)
        {
            return;
        }

        if (@event is InputEventMouseMotion motion)
        {
            HexCoord? coordinate = PixelToHex(motion.Position);

            if (coordinate != _hoveredCoordinate)
            {
                _hoveredCoordinate = coordinate;
                HoveredHexChanged?.Invoke(coordinate);
                QueueRedraw();
            }

            return;
        }

        if (@event is InputEventMouseButton mouseButton &&
            mouseButton.ButtonIndex == MouseButton.Left &&
            mouseButton.Pressed)
        {
            HexCoord? coordinate = PixelToHex(mouseButton.Position);

            if (coordinate is HexCoord existing)
            {
                _inspectedCoordinate = existing;
                HexClicked?.Invoke(existing);
                QueueRedraw();
                AcceptEvent();
            }
        }
    }

    private void OnMouseExited()
    {
        _hoveredCoordinate = null;
        HoveredHexChanged?.Invoke(null);
        QueueRedraw();
    }

    public override void _Draw()
    {
        DrawRect(
            new Rect2(Vector2.Zero, Size),
            new Color(0.025f, 0.035f, 0.055f));

        if (_scenario is null)
        {
            return;
        }

        RecalculateLayout();
        DrawHexCells(_scenario.Map);

        switch (DisplayMode)
        {
            case TargetingMode.DirectFire:
                DrawDirectFireOverlay();
                break;
            case TargetingMode.Missile:
                break;
            case TargetingMode.Movement:
                DrawMovementOverlay();
                break;
        }

        DrawMissileOverlay();
        DrawObjects();
        DrawSelectionMarkers();
        DrawMissileMarkers();
        DrawResolutionCues();
        DrawPointerStatusOverlay();
    }

    private void DrawHexCells(SystemMap map)
    {
        foreach (MapCell cell in map.Cells)
        {
            Vector2 center = HexToPixel(cell.Coordinate);
            Vector2[] polygon = CreateHexPolygon(center, _hexSize);

            if (cell.Coordinate == _hoveredCoordinate)
            {
                DrawColoredPolygon(
                    polygon,
                    new Color(0.25f, 0.55f, 0.85f, 0.18f));
            }
            else if (cell.Coordinate == _inspectedCoordinate)
            {
                DrawColoredPolygon(
                    polygon,
                    new Color(0.95f, 0.80f, 0.25f, 0.12f));
            }

            Color outline = map.Geometry.IsBoundary(cell.Coordinate)
                ? new Color(0.45f, 0.55f, 0.70f, 0.90f)
                : new Color(0.25f, 0.33f, 0.45f, 0.72f);

            DrawPolyline(
                ClosePolygon(polygon),
                outline,
                map.Geometry.IsBoundary(cell.Coordinate) ? 2.0f : 1.0f,
                antialiased: true);

            if (ShowCoordinates && _hexSize >= 22.0f)
            {
                DrawCoordinateLabel(cell.Coordinate, center);
            }
        }
    }

    private void DrawDirectFireOverlay()
    {
        if (_scenario is null || _lineOfSight is null || !_showDirectFireLine)
        {
            return;
        }

        TacticalMapContact? player = _mapContacts.FirstOrDefault(contact =>
            string.Equals(
                contact.ObjectId,
                _scenario.PlayerShipId,
                StringComparison.Ordinal));
        TacticalMapContact? enemy = _mapContacts.FirstOrDefault(contact =>
            string.Equals(
                contact.ObjectId,
                _scenario.EnemyShipId,
                StringComparison.Ordinal));
        if (player is null || enemy is null)
        {
            return;
        }

        Color lineColor = _lineOfSight.Quality switch
        {
            LineOfSightQuality.Clear => new Color(0.30f, 0.95f, 0.55f),
            LineOfSightQuality.Grazing => new Color(1.00f, 0.72f, 0.22f),
            LineOfSightQuality.Blocked => new Color(1.00f, 0.30f, 0.30f),
            _ => Colors.White,
        };

        DrawLine(
            HexToPixel(player.Coordinate),
            HexToPixel(enemy.Coordinate),
            lineColor,
            4.0f,
            antialiased: true);

        foreach (LineOfSightGrazing grazing in _lineOfSight.Grazings)
        {
            DrawHexEmphasis(
                grazing.BlockedCoordinate,
                new Color(1.00f, 0.72f, 0.22f, 0.22f),
                new Color(1.00f, 0.72f, 0.22f),
                4.0f);
        }

        if (_lineOfSight.Blockage is not null)
        {
            foreach (LineOfSightBlocker blocker in _lineOfSight.Blockage.Blockers)
            {
                DrawHexEmphasis(
                    blocker.Coordinate,
                    new Color(1.00f, 0.20f, 0.20f, 0.20f),
                    new Color(1.00f, 0.28f, 0.28f),
                    4.0f);
            }
        }
    }

    private void DrawMissileOverlay()
    {
        if (_showStaticMissileRoute &&
            _missileContacts.Count == 0 &&
            _missileRoute is { HasRoute: true } staticRoute)
        {
            DrawDashedRoutePath(
                staticRoute.Path,
                new Color(0.25f, 0.95f, 0.65f, 0.85f),
                3.0f);
        }

        foreach (TacticalMissileContact contact in _missileContacts)
        {
            if (!ShouldDrawObservedTrail(contact))
            {
                continue;
            }

            Color ownerColor = MissileOwnerColor(contact.OwnerSide);
            bool selectedTrail = string.Equals(
                contact.SalvoId,
                _selectedMissileSalvoId,
                StringComparison.Ordinal);
            // Selected trails retain a readable opacity while remaining absent
            // for every unselected Missile Flight.
            float observedTrailAlpha = contact.TrackQuality switch
            {
                TacticalTrackQuality.Stale => selectedTrail ? 0.52f : 0.28f,
                TacticalTrackQuality.Approximate => selectedTrail ? 0.66f : 0.34f,
                _ => selectedTrail ? 0.80f : 0.44f,
            };

            foreach (IReadOnlyList<HexCoord> segment in
                     contact.VisibleTravelSegments)
            {
                if (segment.Count < 2)
                {
                    continue;
                }

                DrawRoutePath(
                    segment,
                    new Color(
                        ownerColor.R,
                        ownerColor.G,
                        ownerColor.B,
                        observedTrailAlpha),
                    selectedTrail ? 4.0f : 2.0f);
            }

        }

        foreach (MissileRouteProjection projection in _missileProjections)
        {
            if (!projection.HasRoute || projection.RoutePlan is null)
            {
                continue;
            }

            TacticalMissileContact? contact = _missileContacts.FirstOrDefault(
                item => string.Equals(
                    item.SalvoId,
                    projection.SalvoId,
                    StringComparison.Ordinal));
            if (contact is null || !ShouldDrawMissileProjection(contact))
            {
                continue;
            }

            Color ownerColor = MissileOwnerColor(contact.OwnerSide);
            float alpha = projection.TrackQuality switch
            {
                TacticalTrackQuality.Firm => 0.95f,
                TacticalTrackQuality.Approximate => 0.72f,
                TacticalTrackQuality.Stale => 0.48f,
                _ => 0.35f,
            };
            Color projectedColor = new(
                ownerColor.R,
                ownerColor.G,
                ownerColor.B,
                alpha);
            if (contact.OwnerSide == TacticalSide.Player)
            {
                DrawDashedRoutePath(
                    projection.RoutePlan.Path,
                    projectedColor,
                    3.5f);
            }
            else
            {
                // Hostile projections are observer-side incoming-threat
                // estimates, not proof of an enemy guidance lock.
                DrawDottedRoutePath(
                    projection.RoutePlan.Path,
                    projectedColor,
                    4.5f);
            }
        }
    }

    private void DrawRoutePath(
        IReadOnlyList<HexCoord> path,
        Color color,
        float width)
    {
        if (path.Count < 2)
        {
            return;
        }

        Vector2[] points = path.Select(HexToPixel).ToArray();
        DrawPolyline(points, color, width, antialiased: true);
    }

    private void DrawDashedRoutePath(
        IReadOnlyList<HexCoord> path,
        Color color,
        float width)
    {
        if (path.Count < 2)
        {
            return;
        }

        for (int index = 0; index < path.Count - 1; index++)
        {
            Vector2 start = HexToPixel(path[index]);
            Vector2 end = HexToPixel(path[index + 1]);
            Vector2 delta = end - start;
            float length = delta.Length();
            if (length <= 0.001f)
            {
                continue;
            }

            Vector2 direction = delta / length;
            if (index == 0)
            {
                // Begin just outside the missile or ship marker so the first
                // projected segment remains visible instead of being hidden
                // beneath the marker drawn later.
                start += direction * (_hexSize * 0.27f);
            }

            if (index == path.Count - 2)
            {
                end -= direction * (_hexSize * 0.18f);
            }

            delta = end - start;
            const int dashCount = 6;

            for (int dash = 0; dash < dashCount; dash += 2)
            {
                float from = dash / (float)dashCount;
                float to = (dash + 1) / (float)dashCount;
                DrawLine(
                    start + delta * from,
                    start + delta * to,
                    color,
                    width,
                    antialiased: true);
            }
        }
    }

    private void DrawDottedRoutePath(
        IReadOnlyList<HexCoord> path,
        Color color,
        float width)
    {
        if (path.Count < 2)
        {
            return;
        }

        float spacing = Math.Max(8.0f, _hexSize * 0.18f);
        float radius = Math.Max(1.8f, width * 0.52f);
        for (int index = 0; index < path.Count - 1; index++)
        {
            Vector2 start = HexToPixel(path[index]);
            Vector2 end = HexToPixel(path[index + 1]);
            Vector2 delta = end - start;
            float length = delta.Length();
            if (length <= 0.001f)
            {
                continue;
            }

            Vector2 direction = delta / length;
            if (index == 0)
            {
                start += direction * (_hexSize * 0.27f);
            }

            if (index == path.Count - 2)
            {
                end -= direction * (_hexSize * 0.18f);
            }

            delta = end - start;
            length = delta.Length();
            int dotCount = Math.Max(1, (int)MathF.Floor(length / spacing));
            for (int dot = 0; dot <= dotCount; dot++)
            {
                float fraction = dotCount == 0
                    ? 0.0f
                    : dot / (float)dotCount;
                DrawCircle(
                    start + delta * fraction,
                    radius,
                    color);
            }
        }
    }

    private void DrawMovementOverlay()
    {
        if (_scenario is null)
        {
            return;
        }

        foreach (HexCoord coordinate in _legalMovementDestinations)
        {
            if (coordinate == _scenario.PlayerPosition)
            {
                continue;
            }

            bool immediateStep =
                coordinate.DistanceTo(_scenario.PlayerPosition) == 1;
            DrawHexEmphasis(
                coordinate,
                immediateStep
                    ? new Color(0.20f, 0.85f, 0.95f, 0.18f)
                    : new Color(0.20f, 0.75f, 0.95f, 0.08f),
                immediateStep
                    ? new Color(0.35f, 0.90f, 1.00f, 0.92f)
                    : new Color(0.25f, 0.72f, 0.95f, 0.48f),
                immediateStep ? 3.0f : 1.5f);
        }

        ShipMovementResult? preview = _movementPreview;
        if (preview?.Path is not { Count: > 0 } path)
        {
            return;
        }

        Vector2[] points = path.Select(HexToPixel).ToArray();
        Color routeColor = preview.CanMove
            ? new Color(0.25f, 0.95f, 0.65f)
            : new Color(1.00f, 0.48f, 0.28f);

        if (points.Length >= 2)
        {
            DrawPolyline(points, routeColor, 5.0f, antialiased: true);
        }

        DrawHexEmphasis(
            preview.Destination,
            new Color(routeColor.R, routeColor.G, routeColor.B, 0.20f),
            routeColor,
            4.0f);
    }

    private void DrawObjects()
    {
        foreach (TacticalMapContact contact in _mapContacts)
        {
            Vector2 center = HexToPixel(contact.Coordinate);

            switch (contact.Kind)
            {
                case MapObjectKind.Star:
                    DrawStar(center);
                    break;
                case MapObjectKind.Planet:
                    DrawPlanet(center);
                    break;
                case MapObjectKind.Ship:
                    DrawTrackedShip(center, contact);
                    break;
                case MapObjectKind.Station:
                    DrawStation(center);
                    break;
                case MapObjectKind.Anomaly:
                    DrawSymbol(center, "?", new Color(0.75f, 0.45f, 1.00f));
                    break;
                case MapObjectKind.Wreckage:
                    DrawSymbol(center, "x", new Color(0.65f, 0.65f, 0.68f));
                    break;
            }
        }
    }

    private void DrawSelectionMarkers()
    {
        if (_scenario is null)
        {
            return;
        }

        TacticalMapContact? player = _mapContacts.FirstOrDefault(contact =>
            string.Equals(
                contact.ObjectId,
                _scenario.PlayerShipId,
                StringComparison.Ordinal));
        if (player is not null)
        {
            DrawCircle(
                HexToPixel(player.Coordinate),
                _hexSize * 0.42f,
                new Color(0.25f, 0.95f, 0.65f),
                filled: false,
                width: 3.0f,
                antialiased: true);
        }

        TacticalMapContact? enemy = _mapContacts.FirstOrDefault(contact =>
            string.Equals(
                contact.ObjectId,
                _scenario.EnemyShipId,
                StringComparison.Ordinal));
        if (enemy is not null)
        {
            Color enemyRing = enemy.TrackQuality == TacticalTrackQuality.Stale
                ? new Color(1.00f, 0.35f, 0.35f, 0.45f)
                : new Color(1.00f, 0.35f, 0.35f);
            DrawCircle(
                HexToPixel(enemy.Coordinate),
                _hexSize * 0.42f,
                enemyRing,
                filled: false,
                width: 3.0f,
                antialiased: true);
        }
    }

    private void DrawMissileMarkers()
    {
        IReadOnlyList<TacticalMissileContactStack> stacks =
            TacticalMissileStackService.Build(_missileContacts);
        foreach (TacticalMissileContactStack stack in stacks)
        {
            bool mixedOwnershipAtCoordinate = stacks.Any(other =>
                other.Coordinate == stack.Coordinate &&
                other.OwnerSide != stack.OwnerSide);
            float ownershipOffset = !mixedOwnershipAtCoordinate
                ? 0.0f
                : stack.OwnerSide == TacticalSide.Player
                    ? -_hexSize * 0.16f
                    : _hexSize * 0.16f;
            Vector2 center = HexToPixel(stack.Coordinate) +
                new Vector2(ownershipOffset, 0.0f);
            Color ownerColor = MissileOwnerColor(stack.OwnerSide);
            bool selected = stack.Contacts.Any(contact => string.Equals(
                contact.SalvoId,
                _selectedMissileSalvoId,
                StringComparison.Ordinal));
            TacticalMissileContact representative = selected
                ? stack.Contacts.First(contact => string.Equals(
                    contact.SalvoId,
                    _selectedMissileSalvoId,
                    StringComparison.Ordinal))
                : stack.Contacts[0];

            int maximumUncertainty = stack.Contacts.Max(
                contact => contact.UncertaintyRadiusHexes);
            if (stack.Contacts.Any(contact =>
                    contact.TrackQuality == TacticalTrackQuality.Approximate))
            {
                float approximateRadius =
                    _hexSize * (0.42f + 0.08f * maximumUncertainty);
                Color approximateColor = new(
                    ownerColor.R,
                    ownerColor.G,
                    ownerColor.B,
                    0.72f);
                DrawSegmentedRing(
                    center,
                    approximateRadius,
                    approximateColor,
                    3.0f);
                DrawApproximateTag(
                    center,
                    approximateRadius,
                    approximateColor);
            }

            if (selected)
            {
                Color selectionColor = _selectedMissileIsWeaponTarget
                    ? new Color(1.00f, 0.88f, 0.25f)
                    : new Color(0.72f, 0.82f, 0.94f, 0.72f);
                DrawCircle(
                    center,
                    _hexSize * 0.40f,
                    selectionColor,
                    filled: false,
                    width: _selectedMissileIsWeaponTarget ? 3.0f : 2.0f,
                    antialiased: true);
            }

            bool allStale = stack.Contacts.All(contact =>
                contact.TrackQuality == TacticalTrackQuality.Stale);
            Color markerColor = allStale
                ? new Color(ownerColor.R, ownerColor.G, ownerColor.B, 0.52f)
                : ownerColor;
            bool allTerminal = stack.Contacts.All(contact => contact.IsTerminal);
            bool anySearching = stack.Contacts.Any(contact =>
                contact.Status == GuidedMissileStatus.Searching);

            if (allTerminal)
            {
                DrawSymbol(center, "x", markerColor, 27);
                continue;
            }

            if (anySearching && stack.Count == 1)
            {
                DrawCircle(
                    center,
                    _hexSize * 0.32f,
                    markerColor,
                    filled: false,
                    width: 3.0f,
                    antialiased: true);
                DrawSymbol(center, "?", markerColor, 26);
                continue;
            }

            DrawCircle(
                center,
                _hexSize * (stack.IsStacked ? 0.29f : 0.24f),
                new Color(markerColor.R, markerColor.G, markerColor.B, 0.22f));
            string symbol = stack.IsStacked
                ? $"{stack.DisplaySymbol}x{stack.Count}"
                : stack.DisplaySymbol;
            DrawSymbol(
                center,
                symbol,
                markerColor,
                stack.IsStacked ? 16 : 21);

            if (stack.IsStacked)
            {
                DrawCircle(
                    center,
                    _hexSize * 0.34f,
                    new Color(markerColor.R, markerColor.G, markerColor.B, 0.75f),
                    filled: false,
                    width: 2.0f,
                    antialiased: true);
            }
        }
    }

    private void DrawResolutionCues()
    {
        foreach (TacticalResolutionCue cue in _resolutionCues)
        {
            Vector2 center = HexToPixel(cue.Coordinate);
            Color color = MissileOwnerColor(cue.Side);
            DrawCircle(
                center,
                _hexSize * 0.46f,
                new Color(color.R, color.G, color.B, 0.88f),
                filled: false,
                width: 4.0f,
                antialiased: true);
            DrawString(
                ThemeDB.FallbackFont,
                center + new Vector2(-_hexSize * 0.42f, -_hexSize * 0.52f),
                cue.Text,
                HorizontalAlignment.Left,
                -1.0f,
                14,
                color);
        }
    }

    // Historical travel is selected-only to keep the normal tactical map uncluttered.
    private bool ShouldDrawObservedTrail(
        TacticalMissileContact contact) =>
        string.Equals(
            contact.SalvoId,
            _selectedMissileSalvoId,
            StringComparison.Ordinal) &&
        contact.VisibleTravelSegments.Any(segment => segment.Count >= 2);

    private bool ShouldDrawMissileProjection(TacticalMissileContact contact)
    {
        bool selected = string.Equals(
            contact.SalvoId,
            _selectedMissileSalvoId,
            StringComparison.Ordinal);
        if (contact.OwnerSide == TacticalSide.Player)
        {
            return selected;
        }

        int collocatedCount = _missileContacts.Count(item =>
            item.Coordinate == contact.Coordinate &&
            item.OwnerSide == contact.OwnerSide);
        return collocatedCount <= 1 || selected;
    }

    private void DrawSegmentedRing(
        Vector2 center,
        float radius,
        Color color,
        float width)
    {
        const int segmentCount = 12;
        float segmentAngle = 2.0f * MathF.PI / segmentCount;
        float paintedAngle = segmentAngle * 0.58f;

        for (int index = 0; index < segmentCount; index++)
        {
            float startAngle = index * segmentAngle;
            DrawArc(
                center,
                radius,
                startAngle,
                startAngle + paintedAngle,
                6,
                color,
                width,
                antialiased: true);
        }
    }

    private void DrawApproximateTag(
        Vector2 center,
        float radius,
        Color color)
    {
        DrawString(
            ThemeDB.FallbackFont,
            center + new Vector2(-_hexSize * 0.42f, -radius - 3.0f),
            "APPROX",
            HorizontalAlignment.Left,
            -1.0f,
            12,
            color);
    }

    private static Color MissileOwnerColor(TacticalSide side) => side switch
    {
        TacticalSide.Player => new Color(0.25f, 0.95f, 0.65f),
        TacticalSide.Enemy => new Color(1.00f, 0.35f, 0.35f),
        _ => new Color(0.75f, 0.80f, 0.90f),
    };

    private void DrawStar(Vector2 center)
    {
        DrawCircle(center, _hexSize * 0.31f, new Color(1.00f, 0.78f, 0.16f));
        DrawCircle(
            center,
            _hexSize * 0.39f,
            new Color(1.00f, 0.86f, 0.35f, 0.72f),
            filled: false,
            width: 3.0f,
            antialiased: true);
    }

    private void DrawPlanet(Vector2 center)
    {
        DrawCircle(center, _hexSize * 0.24f, new Color(0.55f, 0.66f, 0.82f));
        DrawLine(
            center + new Vector2(-_hexSize * 0.22f, 0.0f),
            center + new Vector2(_hexSize * 0.22f, 0.0f),
            new Color(0.82f, 0.88f, 0.96f),
            2.0f,
            antialiased: true);
    }

    private void DrawTrackedShip(
        Vector2 center,
        TacticalMapContact contact)
    {
        if (contact.TrackQuality == TacticalTrackQuality.Approximate)
        {
            float approximateRadius =
                _hexSize * (0.46f + 0.08f * contact.UncertaintyRadiusHexes);
            Color approximateColor = new(1.00f, 0.72f, 0.22f, 0.82f);
            DrawSegmentedRing(
                center,
                approximateRadius,
                approximateColor,
                3.0f);
            DrawApproximateTag(
                center,
                approximateRadius,
                approximateColor);
        }
        else if (contact.TrackQuality == TacticalTrackQuality.Stale)
        {
            DrawCircle(
                center,
                _hexSize * (0.48f + 0.08f * contact.UncertaintyRadiusHexes),
                new Color(0.75f, 0.80f, 0.90f, 0.34f),
                filled: false,
                width: 2.0f,
                antialiased: true);
        }

        DrawShip(
            center,
            contact.ObjectId,
            contact.TrackQuality == TacticalTrackQuality.Stale ? 0.42f : 1.0f);
    }

    private void DrawShip(Vector2 center, string objectId, float alpha = 1.0f)
    {
        bool isPlayer = string.Equals(
            objectId,
            _scenario?.PlayerShipId,
            StringComparison.Ordinal);

        Color color = isPlayer
            ? new Color(0.25f, 0.95f, 0.65f)
            : new Color(1.00f, 0.35f, 0.35f);

        float radius = _hexSize * 0.25f;
        Vector2[] triangle =
        {
            center + new Vector2(radius, 0.0f),
            center + new Vector2(-radius * 0.75f, -radius * 0.70f),
            center + new Vector2(-radius * 0.75f, radius * 0.70f),
        };

        DrawColoredPolygon(
            triangle,
            new Color(color.R, color.G, color.B, 0.80f * alpha));
        DrawPolyline(
            ClosePolygon(triangle),
            new Color(color.R, color.G, color.B, alpha),
            2.0f,
            antialiased: true);
    }

    private void DrawStation(Vector2 center)
    {
        float half = _hexSize * 0.20f;
        DrawRect(
            new Rect2(center - new Vector2(half, half), new Vector2(half * 2.0f, half * 2.0f)),
            new Color(0.75f, 0.80f, 0.88f),
            filled: false,
            width: 3.0f,
            antialiased: true);
    }

    private void DrawSymbol(
        Vector2 center,
        string symbol,
        Color color,
        int fontSize = 22)
    {
        float width = _hexSize * 1.2f;
        DrawString(
            ThemeDB.FallbackFont,
            center + new Vector2(-width / 2.0f, fontSize * 0.34f),
            symbol,
            HorizontalAlignment.Center,
            width,
            fontSize,
            color);
    }

    private void DrawCoordinateLabel(HexCoord coordinate, Vector2 center)
    {
        string text = $"{coordinate.Q},{coordinate.R}";
        float width = _hexSize * 1.45f;
        int fontSize = Math.Max(9, (int)(_hexSize * 0.25f));

        DrawString(
            ThemeDB.FallbackFont,
            center + new Vector2(-width / 2.0f, _hexSize * 0.48f),
            text,
            HorizontalAlignment.Center,
            width,
            fontSize,
            new Color(0.66f, 0.73f, 0.84f, 0.82f));
    }

    private void DrawHexEmphasis(
        HexCoord coordinate,
        Color fill,
        Color outline,
        float outlineWidth)
    {
        Vector2[] polygon = CreateHexPolygon(HexToPixel(coordinate), _hexSize);
        DrawColoredPolygon(polygon, fill);
        DrawPolyline(
            ClosePolygon(polygon),
            outline,
            outlineWidth,
            antialiased: true);
    }

    private void DrawPointerStatusOverlay()
    {
        if (_scenario is null)
        {
            return;
        }

        string status;

        if (_hoveredCoordinate is HexCoord hovered)
        {
            status = $"Hover {FormatCellSummary(hovered)}";
        }
        else if (_inspectedCoordinate is HexCoord selected)
        {
            status = $"Selected {FormatCellSummary(selected)}";
        }
        else
        {
            status = "Hover a hex to inspect its coordinate, terrain, and occupants.";
        }

        float margin = 12.0f;
        float height = 34.0f;
        float width = MathF.Max(1.0f, Size.X - (margin * 2.0f));
        var rect = new Rect2(new Vector2(margin, 10.0f), new Vector2(width, height));

        DrawRect(rect, new Color(0.02f, 0.03f, 0.05f, 0.88f));
        DrawRect(
            rect,
            new Color(0.35f, 0.48f, 0.68f, 0.90f),
            filled: false,
            width: 1.0f);

        DrawString(
            ThemeDB.FallbackFont,
            rect.Position + new Vector2(10.0f, 23.0f),
            status,
            HorizontalAlignment.Left,
            MathF.Max(1.0f, rect.Size.X - 20.0f),
            15,
            new Color(0.88f, 0.92f, 0.98f));
    }

    private string FormatCellSummary(HexCoord coordinate)
    {
        if (_scenario is null)
        {
            return $"({coordinate.Q},{coordinate.R})";
        }

        MapCell cell = _scenario.Map.GetCell(coordinate);
        IEnumerable<string> mapContacts = _mapContacts
            .Where(contact => contact.Coordinate == coordinate)
            .Select(contact =>
                $"{contact.Name} ({contact.Kind}; {contact.TrackQuality?.ToString() ?? "navigation"})");
        IEnumerable<string> missileContacts = _missileContacts
            .Where(contact => contact.Coordinate == coordinate)
            .Select(contact => contact.OwnerSide == TacticalSide.Player
                ? $"Friendly {contact.SalvoId} (Missile; {contact.Status}; target {contact.TargetId}; range {contact.RemainingRange}/{contact.MaximumRange})"
                : $"Enemy {contact.SalvoId} (Missile; {contact.TrackQuality}; {contact.Status})");
        string contacts = string.Join(", ", mapContacts.Concat(missileContacts));

        return $"({coordinate.Q},{coordinate.R}) | terrain: {cell.Terrain} | known contacts: " +
            (string.IsNullOrWhiteSpace(contacts) ? "none" : contacts);
    }

    private void RecalculateLayout()
    {
        if (_scenario is null)
        {
            return;
        }

        float minX = float.PositiveInfinity;
        float maxX = float.NegativeInfinity;
        float minY = float.PositiveInfinity;
        float maxY = float.NegativeInfinity;

        foreach (HexCoord coordinate in _scenario.Map.Geometry.Cells)
        {
            Vector2 unitCenter = AxialToUnitPixel(coordinate);
            minX = MathF.Min(minX, unitCenter.X - (SqrtThree / 2.0f));
            maxX = MathF.Max(maxX, unitCenter.X + (SqrtThree / 2.0f));
            minY = MathF.Min(minY, unitCenter.Y - 1.0f);
            maxY = MathF.Max(maxY, unitCenter.Y + 1.0f);
        }

        float unitWidth = MathF.Max(1.0f, maxX - minX);
        float unitHeight = MathF.Max(1.0f, maxY - minY);

        const float sidePadding = 18.0f;
        const float topStatusArea = 54.0f;
        const float bottomPadding = 18.0f;

        float availableWidth = MathF.Max(1.0f, Size.X - (sidePadding * 2.0f));
        float availableHeight = MathF.Max(
            1.0f,
            Size.Y - topStatusArea - bottomPadding);

        float fittedSize = MathF.Min(
            availableWidth / unitWidth,
            availableHeight / unitHeight);

        // Never impose a lower bound that can force the board outside its control.
        // Large windows are capped only to keep prototype labels and symbols readable.
        _hexSize = MathF.Max(1.0f, MathF.Min(fittedSize, 58.0f));

        Vector2 unitBoundsCenter = new(
            (minX + maxX) / 2.0f,
            (minY + maxY) / 2.0f);

        Vector2 contentCenter = new(
            Size.X / 2.0f,
            topStatusArea + (availableHeight / 2.0f));

        _boardOffset = contentCenter - (unitBoundsCenter * _hexSize);
    }

    private Vector2 HexToPixel(HexCoord coordinate) =>
        _boardOffset + (AxialToUnitPixel(coordinate) * _hexSize);

    private static Vector2 AxialToUnitPixel(HexCoord coordinate) =>
        new(
            SqrtThree * (coordinate.Q + (coordinate.R / 2.0f)),
            1.5f * coordinate.R);

    private HexCoord? PixelToHex(Vector2 pixel)
    {
        if (_scenario is null)
        {
            return null;
        }

        RecalculateLayout();

        Vector2 unit = (pixel - _boardOffset) / _hexSize;
        float q = ((SqrtThree / 3.0f) * unit.X) - ((1.0f / 3.0f) * unit.Y);
        float r = (2.0f / 3.0f) * unit.Y;
        HexCoord rounded = RoundAxial(q, r);

        return _scenario.Map.Geometry.Contains(rounded)
            ? rounded
            : null;
    }

    private static HexCoord RoundAxial(float q, float r)
    {
        float s = -q - r;
        int roundedQ = (int)MathF.Round(q);
        int roundedR = (int)MathF.Round(r);
        int roundedS = (int)MathF.Round(s);

        float qDifference = MathF.Abs(roundedQ - q);
        float rDifference = MathF.Abs(roundedR - r);
        float sDifference = MathF.Abs(roundedS - s);

        if (qDifference > rDifference && qDifference > sDifference)
        {
            roundedQ = -roundedR - roundedS;
        }
        else if (rDifference > sDifference)
        {
            roundedR = -roundedQ - roundedS;
        }

        return new HexCoord(roundedQ, roundedR);
    }

    private static Vector2[] CreateHexPolygon(Vector2 center, float radius)
    {
        var points = new Vector2[6];

        for (int index = 0; index < points.Length; index++)
        {
            float angle = MathF.PI / 180.0f * ((60.0f * index) + 30.0f);
            points[index] = center + new Vector2(
                radius * MathF.Cos(angle),
                radius * MathF.Sin(angle));
        }

        return points;
    }

    private static Vector2[] ClosePolygon(IReadOnlyList<Vector2> polygon)
    {
        var closed = new Vector2[polygon.Count + 1];

        for (int index = 0; index < polygon.Count; index++)
        {
            closed[index] = polygon[index];
        }

        closed[^1] = polygon[0];
        return closed;
    }
}
