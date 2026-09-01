using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Godot;
using StarCluster.Core.Combat;
using StarCluster.Core.Combat.DirectFire;
using StarCluster.Core.Diagnostics;
using StarCluster.Core.Combat.Missiles;
using StarCluster.Core.Combat.Tracking;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;
using StarCluster.Core.Movement;
using StarCluster.Game;

/// <summary>
/// Builds the Godot tactical prototype from standard controls and drawing
/// primitives. Authoritative movement, map, line-of-sight, missile ownership,
/// guidance, interception, and lifetime decisions remain in StarCluster.Core.
/// </summary>
public partial class Main : Node
{
    private const string PrototypeVersion = "tactical-prototype";

    private readonly MissileFlightProfile _missileProfile = new(
        technologyLevel: 2,
        maximumRange: 10,
        speedHexesPerTurn: 2);

    private readonly MissileDatalinkProfile _missileDatalinkProfile = new(
        technologyLevel: 2,
        isInstalled: true,
        requiresLineOfSight: true,
        maximumRetainedReportAgePhases: 3);

    private readonly MissileSensorProfile _missileSensorProfile = new(
        technologyLevel: 2,
        isInstalled: true,
        firmRangeHexes: 3,
        approximateRangeHexes: 5,
        requiresLineOfSight: true,
        activeModeRangeBonusHexes: 2,
        allowsActiveMode: true,
        maximumLocalTrackAgeEpochs: 2);

    private readonly MissileTerminalProfile _missileTerminalProfile = new(
        new MissileGuidanceComputerProfile(
            technologyLevel: 2,
            baseHitChancePercent: 65,
            minimumHitChancePercent: 5,
            maximumHitChancePercent: 95),
        new MissileTerminalSeekerProfile(
            technologyLevel: 2,
            isInstalled: true,
            baseAcquisitionChancePercent: 65,
            terminalEccmStrength: 2,
            accuracyBonusPercent: 15));

    private readonly MissileDefenseProfile _pointDefenseProfile = new(
        technologyLevel: 2,
        interceptionRangeHexes: 1,
        maximumAttemptsPerPhase: 2);

    private readonly DirectFireWeaponProfile _mainWeaponProfile = new(
        technologyLevel: 3,
        maximumRangeHexes: 3,
        canInterceptMissiles: true);

    private readonly SublightMovementProfile _playerMovementProfile = new(
        technologyLevel: 4,
        maximumHexesPerTurn: 3);

    private readonly SensorProfile _sensorProfile = new(
        technologyLevel: 3,
        firmRangeHexes: 6,
        approximateRangeHexes: 10,
        requiresLineOfSight: true,
        activeModeRangeBonusHexes: 2);

    private readonly SensorSignatureProfile _shipSignatureProfile = new(
        "standard-ship",
        baselineRangeModifierHexes: 0,
        activeEmissionRangeModifierHexes: 2);

    private readonly SensorSignatureProfile _missileSignatureProfile = new(
        "missile-plume",
        baselineRangeModifierHexes: 1);

    private readonly ElectronicWarfareProfile _playerElectronicWarfare = new(
        technologyLevel: 3,
        jammingRangePenaltyHexes: 3,
        counterJammingStrength: 1);

    private readonly ElectronicWarfareProfile _enemyElectronicWarfare = new(
        technologyLevel: 3,
        jammingRangePenaltyHexes: 3,
        counterJammingStrength: 1);

    private readonly SensorEnvironmentProfile _sensorEnvironment =
        SensorEnvironmentProfile.ClearSpace;

    private readonly ComputingProfile _computingProfile = new(
        technologyLevel: 3,
        staleRetentionUpdates: 3,
        uncertaintyGrowthPerMissedUpdate: 1);

    private TacticalTurnState _turnState = new();
    private MissileEngagementState _missileEngagement = new();
    private readonly Dictionary<string, GuidedMissileAdvanceResult>
        _lastAdvanceBySalvo = new(StringComparer.Ordinal);
    private readonly Dictionary<string, MissileAutonomousGuidanceResult>
        _lastAutonomousGuidanceBySalvo = new(StringComparer.Ordinal);
    private readonly HashSet<string> _salvosResolvedThisPhase =
        new(StringComparer.Ordinal);
    private readonly HashSet<string> _launchesResolvedThisPhase =
        new(StringComparer.Ordinal);

    private HexBoardView _board = null!;
    private OptionButton _scenarioSelector = null!;
    private OptionButton _modeSelector = null!;
    private CheckButton _coordinateToggle = null!;
    private CheckButton _interceptionSucceedsToggle = null!;
    private CheckButton _playerActiveSensorsToggle = null!;
    private CheckButton _enemyActiveSensorsToggle = null!;
    private CheckButton _playerJammingToggle = null!;
    private CheckButton _enemyJammingToggle = null!;
    private Button _resetScenarioButton = null!;
    private Button _fireAtShipButton = null!;
    private Button _interceptSelectedMissileButton = null!;
    private Button _holdForAnyMissileButton = null!;
    private Button _holdFireButton = null!;
    private Button _launchPlayerButton = null!;
    private Button _launchEnemyButton = null!;
    private Button _advanceMissilesButton = null!;
    private Button _commitMoveButton = null!;
    private Button _holdButton = null!;
    private Button _advancePhaseButton = null!;
    private Label _scenarioDescription = null!;
    private Label _hoverLabel = null!;
    private Label _inspectionLabel = null!;
    private Label _resultLabel = null!;
    private Label _directFireStateLabel = null!;
    private Label _missileStateLabel = null!;
    private Label _movementStateLabel = null!;
    private Label _turnStateLabel = null!;
    private Label _playerTargetLabel = null!;
    private Label _trackStateLabel = null!;
    private Label _sensorSummaryLabel = null!;
    private Label _diagnosticLogLabel = null!;
    private CheckButton _authoritativeMissileDebugToggle = null!;
    private Label _authoritativeMissileDebugLabel = null!;
    private VBoxContainer _movementCommandPanel = null!;
    private VBoxContainer _directFireCommandPanel = null!;
    private VBoxContainer _missileCommandPanel = null!;
    private Label _pointDefenseStatusLabel = null!;
    private Label _immediateFeedbackLabel = null!;
    private ScrollContainer _detailScroll = null!;

    private DemoScenario _scenario = null!;
    private DemoTrackState _trackState = null!;
    private DirectFireLineOfSightResult _lineOfSight = null!;
    private MissileRouteResult _playerMissileRoute = null!;
    private MissileRouteResult _enemyMissileRoute = null!;
    private ShipMovementResult? _movementPreview;
    private IReadOnlyList<HexCoord> _legalMovementDestinations =
        Array.Empty<HexCoord>();
    private ShipMovementTurnState _playerMovementState = null!;
    private MissileInterceptionPhaseContext? _interceptionContext;
    private IMissileTerminalRandomSource _terminalRandomSource =
        new SeededMissileTerminalRandomSource(1801);
    private bool _playerMovementResolved;
    private bool _directFireResolved;
    private bool _heldDirectFireOrderArmed;
    private bool _playerLaunchedThisPhase;
    private bool _enemyLaunchedThisPhase;
    private string? _selectedDirectFireShipTargetId;
    private string? _selectedPlayerTargetId;
    private string? _selectedMissileSalvoId;
    private DirectFireOrder? _directFireOrder;
    private string? _movementCommandMessage;
    private string? _directFireActionMessage;
    private string? _missileActionMessage;
    private int _currentScenarioIndex;
    private int _nextFriendlySalvoNumber = 1;
    private int _nextHostileSalvoNumber = 1;
    private int _encounterLogNumber;
    private AutomaticDiagnosticLog? _diagnosticLog;
    private string _lastMissileStackSignature = string.Empty;
    private IReadOnlyList<TacticalResolutionCue> _resolutionCues =
        Array.Empty<TacticalResolutionCue>();
    private readonly List<string> _persistentMissilePhaseFeedback = new();

    public override void _Ready()
    {
        GD.Print(
            $"Star Cluster tactical prototype starting. " +
            $"Game assembly: {typeof(Main).Assembly.GetName().Name}; " +
            $"Core assembly: {typeof(HexCoord).Assembly.GetName().Name}; " +
            $"viewport: {GetViewport().GetVisibleRect().Size}.");

        BuildInterface();
        LoadScenario(0);
    }

    public override void _ExitTree()
    {
        EndCurrentDiagnosticLog("Godot scene exiting.");
    }

    private void BuildInterface()
    {
        var root = new HBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ExpandFill,
        };
        root.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
        AddChild(root);

        _board = new HexBoardView
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ExpandFill,
        };
        _board.HoveredHexChanged += OnHoveredHexChanged;
        _board.HexClicked += OnHexClicked;
        root.AddChild(_board);

        // Keep the tactical board independent of changing label content in the
        // right panel. The fixed-width host participates in the HBox layout;
        // the anchored panel cannot enlarge the root when feedback text wraps.
        var sideHost = new Control
        {
            CustomMinimumSize = new Vector2(420.0f, 0.0f),
            SizeFlagsHorizontal = Control.SizeFlags.ShrinkEnd,
            SizeFlagsVertical = Control.SizeFlags.ExpandFill,
            ClipContents = true,
        };
        root.AddChild(sideHost);

        var sidePanel = new PanelContainer();
        sidePanel.SetAnchorsAndOffsetsPreset(Control.LayoutPreset.FullRect);
        sideHost.AddChild(sidePanel);

        var sideRoot = new VBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ExpandFill,
        };
        sideRoot.AddThemeConstantOverride("separation", 8);
        sidePanel.AddChild(sideRoot);

        var commandMargin = new MarginContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ShrinkBegin,
        };
        commandMargin.AddThemeConstantOverride("margin_left", 14);
        commandMargin.AddThemeConstantOverride("margin_top", 12);
        commandMargin.AddThemeConstantOverride("margin_right", 14);
        commandMargin.AddThemeConstantOverride("margin_bottom", 8);
        sideRoot.AddChild(commandMargin);

        var commandControls = new VBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ShrinkBegin,
        };
        commandControls.AddThemeConstantOverride("separation", 7);
        commandMargin.AddChild(commandControls);

        var title = new Label
        {
            Text = "Star Cluster - Tactical Prototype",
        };
        title.AddThemeFontSizeOverride("font_size", 21);
        commandControls.AddChild(title);

        _resetScenarioButton = new Button
        {
            Text = "Reset map / scenario",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _resetScenarioButton.Pressed += ResetCurrentScenario;
        commandControls.AddChild(_resetScenarioButton);

        _scenarioSelector = new OptionButton
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            FitToLongestItem = false,
            TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis,
            TooltipText = "Select the tactical validation scenario.",
        };
        foreach (string scenarioName in DemoScenarioFactory.Names)
        {
            _scenarioSelector.AddItem(scenarioName);
        }
        _scenarioSelector.ItemSelected += OnScenarioSelected;
        commandControls.AddChild(_scenarioSelector);

        commandControls.AddChild(CreateSectionLabel("Tactical command"));
        _turnStateLabel = CreateWrappedLabel(string.Empty);
        commandControls.AddChild(_turnStateLabel);

        _advancePhaseButton = new Button
        {
            Text = "Advance phase",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _advancePhaseButton.Pressed += AdvanceTacticalPhase;
        commandControls.AddChild(_advancePhaseButton);

        _movementCommandPanel = new VBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _movementCommandPanel.AddThemeConstantOverride("separation", 6);
        commandControls.AddChild(_movementCommandPanel);
        _movementCommandPanel.AddChild(CreateSectionLabel("Movement actions"));
        var movementButtons = new HBoxContainer();
        movementButtons.AddThemeConstantOverride("separation", 8);
        _movementCommandPanel.AddChild(movementButtons);
        _commitMoveButton = new Button
        {
            Text = "Move to destination",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _commitMoveButton.Pressed += CommitPlayerMovement;
        movementButtons.AddChild(_commitMoveButton);
        _holdButton = new Button
        {
            Text = "End movement",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _holdButton.Pressed += HoldPlayerPosition;
        movementButtons.AddChild(_holdButton);
        _movementStateLabel = CreateWrappedLabel(string.Empty);
        _movementCommandPanel.AddChild(_movementStateLabel);

        _directFireCommandPanel = new VBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _directFireCommandPanel.AddThemeConstantOverride("separation", 6);
        commandControls.AddChild(_directFireCommandPanel);
        _directFireCommandPanel.AddChild(CreateSectionLabel("Direct-fire commitment"));
        _fireAtShipButton = new Button
        {
            Text = "Fire main weapon at selected ship",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _fireAtShipButton.Pressed += ResolveDirectFireAtShip;
        _directFireCommandPanel.AddChild(_fireAtShipButton);
        _interceptSelectedMissileButton = new Button
        {
            Text = "Intercept selected missile",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _interceptSelectedMissileButton.Pressed += CommitSpecificMissileInterception;
        _directFireCommandPanel.AddChild(_interceptSelectedMissileButton);
        _holdForAnyMissileButton = new Button
        {
            Text = "Hold main weapon for any missile",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _holdForAnyMissileButton.Pressed += CommitHoldForAnyMissile;
        _directFireCommandPanel.AddChild(_holdForAnyMissileButton);
        _holdFireButton = new Button
        {
            Text = "Hold main weapon fire",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _holdFireButton.Pressed += ResolveHoldFire;
        _directFireCommandPanel.AddChild(_holdFireButton);
        _directFireStateLabel = CreateWrappedLabel(string.Empty);
        _directFireCommandPanel.AddChild(_directFireStateLabel);

        _missileCommandPanel = new VBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _missileCommandPanel.AddThemeConstantOverride("separation", 6);
        commandControls.AddChild(_missileCommandPanel);
        _missileCommandPanel.AddChild(CreateSectionLabel("Missile / interception actions"));
        _playerTargetLabel = CreateWrappedLabel(string.Empty);
        _missileCommandPanel.AddChild(_playerTargetLabel);
        var launchButtons = new HBoxContainer();
        launchButtons.AddThemeConstantOverride("separation", 8);
        _missileCommandPanel.AddChild(launchButtons);
        _launchPlayerButton = new Button
        {
            Text = "Launch player missile",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _launchPlayerButton.Pressed += LaunchPlayerMissile;
        launchButtons.AddChild(_launchPlayerButton);
        _launchEnemyButton = new Button
        {
            Text = "Launch enemy at player",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _launchEnemyButton.Pressed += LaunchEnemyMissile;
        launchButtons.AddChild(_launchEnemyButton);
        _advanceMissilesButton = new Button
        {
            Text = "Advance unresolved salvos once",
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _advanceMissilesButton.Pressed += AdvanceActiveMissiles;
        _missileCommandPanel.AddChild(_advanceMissilesButton);
        _interceptionSucceedsToggle = new CheckButton
        {
            Text = "Demonstration interception succeeds",
            ButtonPressed = false,
        };
        _missileCommandPanel.AddChild(_interceptionSucceedsToggle);

        _pointDefenseStatusLabel = CreateWrappedLabel(string.Empty);
        commandControls.AddChild(_pointDefenseStatusLabel);
        _immediateFeedbackLabel = CreateWrappedLabel("No tactical action has resolved yet.");
        commandControls.AddChild(_immediateFeedbackLabel);

        commandControls.AddChild(CreateSectionLabel("Development diagnostics"));
        _authoritativeMissileDebugToggle = CreateWrappedCheckButton(
            "Show AUTHORITATIVE DEBUG for selected missile",
            "Displays hidden selected-missile guidance state for focused validation only.");
        _authoritativeMissileDebugToggle.Toggled += OnAuthoritativeMissileDebugToggled;
        commandControls.AddChild(_authoritativeMissileDebugToggle);

        sideRoot.AddChild(new HSeparator());

        _detailScroll = new ScrollContainer
        {
            CustomMinimumSize = new Vector2(0.0f, 280.0f),
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ExpandFill,
            HorizontalScrollMode = ScrollContainer.ScrollMode.Disabled,
            VerticalScrollMode = ScrollContainer.ScrollMode.Auto,
            FollowFocus = true,
        };
        sideRoot.AddChild(_detailScroll);

        var detailMargin = new MarginContainer
        {
            CustomMinimumSize = Vector2.Zero,
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ShrinkBegin,
        };
        detailMargin.AddThemeConstantOverride("margin_left", 14);
        detailMargin.AddThemeConstantOverride("margin_top", 6);
        detailMargin.AddThemeConstantOverride("margin_right", 14);
        detailMargin.AddThemeConstantOverride("margin_bottom", 14);
        _detailScroll.AddChild(detailMargin);

        var details = new VBoxContainer
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
            SizeFlagsVertical = Control.SizeFlags.ShrinkBegin,
        };
        details.AddThemeConstantOverride("separation", 9);
        detailMargin.AddChild(details);

        details.AddChild(CreateWrappedLabel(
            "Observer-specific tracks control visibility, direct fire, and missile guidance. Track visibility is reevaluated after relevant events, but missed-track age advances at most once per tactical turn."));
        details.AddChild(CreateSectionLabel("Scenario"));
        _scenarioDescription = CreateWrappedLabel(string.Empty);
        details.AddChild(_scenarioDescription);

        details.AddChild(CreateSectionLabel("Sensor / EW status"));
        _sensorSummaryLabel = CreateWrappedLabel(string.Empty);
        details.AddChild(_sensorSummaryLabel);

        details.AddChild(CreateSectionLabel("Sensor / EW demonstration"));
        details.AddChild(CreateWrappedLabel(
            "These development controls trigger an immediate Track Update without advancing missed-track age more than once in the current tactical turn. Direction matters: each sensor or jammer affects one observer-target relationship."));
        details.AddChild(CreateWrappedLabel(
            "Player active sensors improve player detection and increase player emissions. Enemy active emissions make the enemy easier for the player to detect. Player jamming impairs enemy detection of the player. Enemy jamming impairs player detection of the enemy."));
        _playerActiveSensorsToggle = CreateWrappedCheckButton(
            "Player active sensors",
            "Improves player detection by +2 hexes and increases player emissions.");
        _playerActiveSensorsToggle.Toggled += OnSensorStateToggled;
        details.AddChild(_playerActiveSensorsToggle);
        _enemyActiveSensorsToggle = CreateWrappedCheckButton(
            "Enemy active emissions",
            "Makes the enemy easier for the player to detect by +2 hexes.");
        _enemyActiveSensorsToggle.Toggled += OnSensorStateToggled;
        details.AddChild(_enemyActiveSensorsToggle);
        _playerJammingToggle = CreateWrappedCheckButton(
            "Player jammer",
            "Imposes a raw -3 penalty on enemy detection of the player before counter-jamming.");
        _playerJammingToggle.Toggled += OnSensorStateToggled;
        details.AddChild(_playerJammingToggle);
        _enemyJammingToggle = CreateWrappedCheckButton(
            "Enemy jammer",
            "Imposes a raw -3 penalty on player detection of the enemy before counter-jamming.");
        _enemyJammingToggle.Toggled += OnSensorStateToggled;
        details.AddChild(_enemyJammingToggle);

        details.AddChild(CreateSectionLabel("Overlay"));
        _modeSelector = new OptionButton
        {
            SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
        };
        _modeSelector.AddItem("Direct fire");
        _modeSelector.AddItem("Missile route");
        _modeSelector.AddItem("Ship movement");
        _modeSelector.ItemSelected += OnModeSelected;
        details.AddChild(_modeSelector);
        _coordinateToggle = new CheckButton
        {
            Text = "Show axial coordinates",
            ButtonPressed = true,
        };
        _coordinateToggle.Toggled += OnCoordinateToggled;
        details.AddChild(_coordinateToggle);

        details.AddChild(CreateSectionLabel("Track quality"));
        _trackStateLabel = CreateWrappedLabel(string.Empty);
        details.AddChild(_trackStateLabel);

        details.AddChild(CreateSectionLabel("Missile and defense detail"));
        _missileStateLabel = CreateWrappedLabel(string.Empty);
        details.AddChild(_missileStateLabel);

        details.AddChild(CreateSectionLabel("Authoritative missile diagnostics"));
        details.AddChild(CreateWrappedLabel(
            "Development-only internal state. Use the always-visible toggle above the detail pane. Normal play must not expose enemy datalink, retained-report, or local-sensor truth."));
        _authoritativeMissileDebugLabel = CreateWrappedLabel(
            "AUTHORITATIVE DEBUG disabled.");
        _authoritativeMissileDebugLabel.Visible = false;
        details.AddChild(_authoritativeMissileDebugLabel);

        details.AddChild(CreateSectionLabel("Pointer inspection"));
        _hoverLabel = CreateWrappedLabel("Hover: outside map");
        _inspectionLabel = CreateWrappedLabel(
            "Click a hex to inspect its logical contents.");
        details.AddChild(_hoverLabel);
        details.AddChild(_inspectionLabel);

        details.AddChild(CreateSectionLabel("Core result"));
        _resultLabel = CreateWrappedLabel(string.Empty);
        details.AddChild(_resultLabel);

        details.AddChild(CreateSectionLabel("Automatic diagnostic journal"));
        details.AddChild(CreateWrappedLabel(
            "Authoritative JSONL and readable text logs are always created under user://logs. Filenames include the stable tactical-prototype identifier, UTC start time, and encounter number; every event is flushed immediately."));
        _diagnosticLogLabel = CreateWrappedLabel(string.Empty);
        details.AddChild(_diagnosticLogLabel);

        details.AddChild(CreateWrappedLabel(
            "Stacked missile markers show ownership and count. Click the same stack repeatedly to cycle individual salvos and inspect or target one specific missile. Historical trails are selected-only and never draw through an unseen gap."));
        details.AddChild(CreateWrappedLabel(
            "Line key: selecting a friendly Missile Flight shows its dashed current targeting plan. Hostile incoming-threat estimates use dots and do not prove an enemy lock, datalink, or actual guidance coordinate."));
        details.AddChild(CreateWrappedLabel(
            "Prototype symbols: star = circle, planet = small circle, ships = triangles, friendly missile = green F, enemy missile = red E."));
    }

    private void BeginDiagnosticLog(
        TrackUpdateTrigger initialTrigger,
        int scenarioIndex)
    {
        _encounterLogNumber++;
        string logDirectory = ProjectSettings.GlobalizePath("user://logs");
        _diagnosticLog = new AutomaticDiagnosticLog(
            logDirectory,
            PrototypeVersion,
            DateTimeOffset.UtcNow,
            _encounterLogNumber);
        _diagnosticLog.Record(
            DiagnosticEventType.SessionStarted,
            $"Automatic authoritative encounter logging started for scenario {scenarioIndex}: {_scenario.Name}.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            data: DiagnosticData(
                ("initialTrigger", initialTrigger.ToString()),
                ("scenarioIndex", scenarioIndex.ToString()),
                ("scenarioName", _scenario.Name),
                ("jsonlFile", _diagnosticLog.JsonlPath),
                ("textFile", _diagnosticLog.TextPath)));
        UpdateDiagnosticLogText();
    }

    private void EndCurrentDiagnosticLog(string reason)
    {
        if (_diagnosticLog is null)
        {
            return;
        }

        _diagnosticLog.Record(
            DiagnosticEventType.SessionEnded,
            reason,
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase);
        _diagnosticLog.Dispose();
        _diagnosticLog = null;
    }

    private void LogTrackUpdates(
        IReadOnlyList<TacticalTrackUpdateResult> results)
    {
        if (_diagnosticLog is null)
        {
            return;
        }

        foreach (TacticalTrackUpdateResult result in results)
        {
            string previous = result.PreviousQuality?.ToString() ?? "Unknown";
            string current = result.CurrentQuality?.ToString() ?? "Unknown";
            TacticalTrackRecord? record = result.Record;
            string coordinate = record?.EstimatedCoordinate is HexCoord estimated
                ? Format(estimated)
                : "none";
            bool sameEpochVisibilityLoss =
                !result.AgeAdvanced &&
                record?.LastObservedEpoch == result.ObservationEpoch &&
                result.CurrentQuality == TacticalTrackQuality.Stale &&
                result.PreviousQuality is
                    TacticalTrackQuality.Firm or
                    TacticalTrackQuality.Approximate;
            string ageNote = result.RemainsUnknown
                ? string.Empty
                : result.AgeAdvanced
                    ? $" Track age advanced once in epoch {result.ObservationEpoch}."
                    : sameEpochVisibilityLoss
                        ? $" Visibility was lost later in epoch {result.ObservationEpoch}; the track became Stale at the most recently observed coordinate without advancing tactical age."
                        : $" Track age held in epoch {result.ObservationEpoch}; this was a visibility reevaluation only.";
            string message = result.RemainsUnknown
                ? $"{result.ObserverId} still has no track on {result.TargetId}."
                : $"{result.ObserverId} track on {result.TargetId}: {previous} -> {current}.{ageNote}";

            List<KeyValuePair<string, string>> diagnosticData = DiagnosticData(
                ("trigger", result.Trigger.ToString()),
                ("created", result.Created.ToString()),
                ("previousQuality", previous),
                ("currentQuality", current),
                ("estimatedCoordinate", coordinate),
                ("observationEpoch", result.ObservationEpoch.ToString()),
                ("ageAdvanced", result.AgeAdvanced.ToString()),
                ("sameEpochVisibilityLoss", sameEpochVisibilityLoss.ToString()),
                ("lastObservedEpoch", record?.LastObservedEpoch?.ToString() ?? "none"),
                ("lastAgedEpoch", record?.LastAgedEpoch?.ToString() ?? "none"),
                ("missedUpdates", (record?.MissedUpdateCount ?? 0).ToString()),
                ("uncertaintyRadius", (record?.UncertaintyRadiusHexes ?? 0).ToString()))
                .ToList();
            SensorContactEvaluationResult? sensorEvaluation =
                _trackState.GetLastSensorEvaluation(
                    result.ObserverId,
                    result.TargetId);
            if (sensorEvaluation is not null)
            {
                diagnosticData.Add(new(
                    "sensorEvaluationStatus",
                    sensorEvaluation.Status.ToString()));
                diagnosticData.Add(new(
                    "observerSensorMode",
                    sensorEvaluation.Context.ObserverSensorMode.ToString()));
                diagnosticData.Add(new(
                    "targetSensorMode",
                    sensorEvaluation.Context.TargetSensorMode.ToString()));
                diagnosticData.Add(new(
                    "targetSignatureProfile",
                    sensorEvaluation.Context.TargetSignature.Id));
                diagnosticData.Add(new(
                    "targetJammingEnabled",
                    sensorEvaluation.Context.TargetJammingEnabled.ToString()));
                diagnosticData.Add(new(
                    "distanceHexes",
                    sensorEvaluation.DistanceHexes.ToString()));
                diagnosticData.Add(new(
                    "baseFirmRange",
                    sensorEvaluation.BaseFirmRangeHexes.ToString()));
                diagnosticData.Add(new(
                    "baseApproximateRange",
                    sensorEvaluation.BaseApproximateRangeHexes.ToString()));
                diagnosticData.Add(new(
                    "effectiveFirmRange",
                    sensorEvaluation.EffectiveFirmRangeHexes.ToString()));
                diagnosticData.Add(new(
                    "effectiveApproximateRange",
                    sensorEvaluation.EffectiveApproximateRangeHexes.ToString()));
                diagnosticData.Add(new(
                    "modeRangeModifier",
                    sensorEvaluation.ObserverModeRangeModifierHexes.ToString()));
                diagnosticData.Add(new(
                    "signatureRangeModifier",
                    sensorEvaluation.TargetSignatureRangeModifierHexes.ToString()));
                diagnosticData.Add(new(
                    "environmentProfile",
                    sensorEvaluation.Context.Environment.Id));
                diagnosticData.Add(new(
                    "environmentRangePenalty",
                    sensorEvaluation.EnvironmentRangePenaltyHexes.ToString()));
                diagnosticData.Add(new(
                    "rawJammingPenalty",
                    sensorEvaluation.RawJammingRangePenaltyHexes.ToString()));
                diagnosticData.Add(new(
                    "counterJamming",
                    sensorEvaluation.CounterJammingStrength.ToString()));
                diagnosticData.Add(new(
                    "netJammingPenalty",
                    sensorEvaluation.NetJammingRangePenaltyHexes.ToString()));
            }

            _diagnosticLog.Record(
                DiagnosticEventType.TrackUpdated,
                message,
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: result.ObserverId,
                targetId: result.TargetId,
                coordinateAfter: record?.EstimatedCoordinate,
                data: diagnosticData);
            LogObserverTrailLifecycleForTrackUpdate(result);
        }

        UpdateDiagnosticLogText();
    }

    private void LogObserverTrailLifecycleForTrackUpdate(
        TacticalTrackUpdateResult result)
    {
        if (_diagnosticLog is null ||
            !string.Equals(
                result.ObserverId,
                _scenario.PlayerShipId,
                StringComparison.Ordinal) ||
            _missileEngagement.Find(result.TargetId) is null ||
            result.Trigger is TrackUpdateTrigger.MissileLaunched or
                TrackUpdateTrigger.MissileMovementCompleted)
        {
            return;
        }

        bool wasDetected = result.PreviousQuality is
            TacticalTrackQuality.Firm or TacticalTrackQuality.Approximate;
        bool isDetected = result.CurrentQuality is
            TacticalTrackQuality.Firm or TacticalTrackQuality.Approximate;

        if (!wasDetected && isDetected &&
            result.Record?.EstimatedCoordinate is HexCoord acquired)
        {
            _diagnosticLog.Record(
                DiagnosticEventType.MissileContactAcquired,
                $"Player first observed or reacquired {result.TargetId} at {Format(acquired)} during {result.Trigger}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: result.ObserverId,
                targetId: result.TargetId,
                coordinateAfter: acquired,
                data: DiagnosticData(
                    ("segmentStarted", "True"),
                    ("trigger", result.Trigger.ToString()),
                    ("trackQuality", result.CurrentQuality?.ToString() ?? "none")));
            _diagnosticLog.Record(
                DiagnosticEventType.ObservedTrailSegmentStarted,
                $"Observed trail segment for {result.TargetId} started at {Format(acquired)} after {result.Trigger}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: result.ObserverId,
                targetId: result.TargetId,
                coordinateAfter: acquired,
                data: DiagnosticData(("trigger", result.Trigger.ToString())));
        }
        else if (wasDetected && !isDetected)
        {
            _diagnosticLog.Record(
                DiagnosticEventType.MissileContactLost,
                $"Player lost continuous observation of {result.TargetId} during {result.Trigger}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: result.ObserverId,
                targetId: result.TargetId,
                coordinateAfter: result.Record?.EstimatedCoordinate,
                data: DiagnosticData(
                    ("segmentClosed", "True"),
                    ("trigger", result.Trigger.ToString())));
            _diagnosticLog.Record(
                DiagnosticEventType.ObservedTrailSegmentClosed,
                $"Observed trail segment for {result.TargetId} closed after {result.Trigger}; later reacquisition must start a disconnected segment.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: result.ObserverId,
                targetId: result.TargetId,
                data: DiagnosticData(("trigger", result.Trigger.ToString())));
        }
    }

    private void UpdateDiagnosticLogText()
    {
        if (_diagnosticLogLabel is null)
        {
            return;
        }

        if (_diagnosticLog is null)
        {
            _diagnosticLogLabel.Text = "No active diagnostic journal.";
            return;
        }

        string recent = _diagnosticLog.RecentLines.Count == 0
            ? "No events recorded yet."
            : string.Join("\n", _diagnosticLog.RecentLines);
        _diagnosticLogLabel.Text =
            $"Session: {_diagnosticLog.SessionId}\n" +
            $"JSONL: {_diagnosticLog.JsonlPath}\n" +
            $"Text: {_diagnosticLog.TextPath}\n" +
            $"Recent events:\n{recent}";
    }

    private static IEnumerable<KeyValuePair<string, string>> DiagnosticData(
        params (string Key, string Value)[] items) =>
        items.Select(item =>
            new KeyValuePair<string, string>(item.Key, item.Value));

    private void LoadScenario(
        int index,
        TrackUpdateTrigger initialTrigger = TrackUpdateTrigger.SystemEntry)
    {
        EndCurrentDiagnosticLog(
            initialTrigger == TrackUpdateTrigger.ScenarioReset
                ? "Scenario reset requested; closing the previous encounter log."
                : "Scenario changed or reloaded; closing the previous encounter log.");
        _currentScenarioIndex = index;
        _scenario = DemoScenarioFactory.Create(index);
        _turnState = new TacticalTurnState();
        BeginDiagnosticLog(initialTrigger, index);
        _missileEngagement = new MissileEngagementState();
        _lastAdvanceBySalvo.Clear();
        _lastAutonomousGuidanceBySalvo.Clear();
        _salvosResolvedThisPhase.Clear();
        _launchesResolvedThisPhase.Clear();
        _interceptionContext = null;
        _terminalRandomSource = new SeededMissileTerminalRandomSource(
            180100 + index);
        _movementPreview = null;
        _playerMovementResolved = false;
        _playerMovementState = ShipMovementTurnService.Begin(
            _scenario.PlayerPosition,
            _playerMovementProfile);
        _directFireResolved = false;
        _heldDirectFireOrderArmed = false;
        _playerLaunchedThisPhase = false;
        _enemyLaunchedThisPhase = false;
        _selectedDirectFireShipTargetId = null;
        _selectedPlayerTargetId = null;
        _selectedMissileSalvoId = null;
        _directFireOrder = null;
        _movementCommandMessage = null;
        _directFireActionMessage = null;
        _missileActionMessage = null;
        _lastMissileStackSignature = string.Empty;
        _persistentMissilePhaseFeedback.Clear();
        if (_immediateFeedbackLabel is not null)
        {
            _immediateFeedbackLabel.Text = "Scenario initialized; no tactical action has resolved yet.";
        }
        _nextFriendlySalvoNumber = 1;
        _nextHostileSalvoNumber = 1;
        _trackState = new DemoTrackState(
            _scenario,
            _sensorProfile,
            _computingProfile,
            _shipSignatureProfile,
            _missileSignatureProfile,
            _playerElectronicWarfare,
            _enemyElectronicWarfare,
            _sensorEnvironment,
            _playerActiveSensorsToggle.ButtonPressed
                ? SensorMode.Active
                : SensorMode.Passive,
            _enemyActiveSensorsToggle.ButtonPressed
                ? SensorMode.Active
                : SensorMode.Passive,
            _playerJammingToggle.ButtonPressed,
            _enemyJammingToggle.ButtonPressed,
            initialTrigger);
        _diagnosticLog?.Record(
            initialTrigger == TrackUpdateTrigger.ScenarioReset
                ? DiagnosticEventType.ScenarioReset
                : DiagnosticEventType.ScenarioInitialized,
            $"Scenario {_scenario.Name} initialized before tactical presentation.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            data: DiagnosticData(
                ("description", _scenario.Description),
                ("playerShip", _scenario.PlayerShipId),
                ("enemyShip", _scenario.EnemyShipId),
                ("playerPosition", Format(_scenario.PlayerPosition)),
                ("enemyPosition", Format(_scenario.EnemyPosition)),
                ("playerSensorMode", _trackState.PlayerSensorMode.ToString()),
                ("enemySensorMode", _trackState.EnemySensorMode.ToString()),
                ("playerJammingEnabled", _trackState.PlayerJammingEnabled.ToString()),
                ("enemyJammingEnabled", _trackState.EnemyJammingEnabled.ToString()),
                ("trackSequence", _trackState.Sequence.ToString())));
        LogTrackUpdates(_trackState.InitialUpdateResults);

        RecalculateDerivedState(resetBoardScenario: true);

        _scenarioDescription.Text = _scenario.Description;
        _inspectionLabel.Text = "Click a hex to inspect its logical contents.";
        _hoverLabel.Text = "Hover: outside map";

        _board.ShowCoordinates = _coordinateToggle.ButtonPressed;
        EnterPhase(TacticalTurnPhase.Movement, resetTurnState: false);
        SyncMissileBoardState();

        UpdateAllTextAndControls();
    }

    private void RecalculateDerivedState(bool resetBoardScenario)
    {
        _lineOfSight = DirectFireLineOfSight.Evaluate(
            _scenario.Map,
            _scenario.PlayerPosition,
            _scenario.EnemyPosition);

        HexCoord playerGuidanceCoordinate =
            _trackState.PlayerTrackOnEnemy?.EstimatedCoordinate ??
            _scenario.PlayerPosition;
        HexCoord enemyGuidanceCoordinate =
            _trackState.GetTrackForSide(
                TacticalSide.Enemy,
                _scenario.PlayerShipId)?.EstimatedCoordinate ??
            _scenario.EnemyPosition;

        _playerMissileRoute = MissileRoutePlanner.FindRoute(
            _scenario.Map,
            _scenario.PlayerPosition,
            playerGuidanceCoordinate,
            _missileProfile.MaximumRange);

        _enemyMissileRoute = MissileRoutePlanner.FindRoute(
            _scenario.Map,
            _scenario.EnemyPosition,
            enemyGuidanceCoordinate,
            _missileProfile.MaximumRange);

        _legalMovementDestinations = _playerMovementResolved
            ? Array.Empty<HexCoord>()
            : ShipMovementTurnService.FindLegalDestinations(
                _scenario.Map,
                _playerMovementState);

        if (resetBoardScenario)
        {
            _board.SetScenario(
                _scenario,
                _lineOfSight,
                _playerMissileRoute);
        }

        _board.SetMovementOverlay(_legalMovementDestinations, _movementPreview);
        SyncKnowledgeBoardState();
        SyncMissileBoardState();
    }

    private void SyncKnowledgeBoardState()
    {
        TacticalTrackRecord? enemyTrack = _trackState.PlayerTrackOnEnemy;
        bool showDirectFireLine =
            _selectedDirectFireShipTargetId == _scenario.EnemyShipId &&
            DirectFireTrackEligibility.CanTarget(enemyTrack);
        _board.SetKnowledgeState(
            _trackState.PlayerMapSnapshot,
            showDirectFireLine);
    }

    private void SyncMissileBoardState()
    {
        ObserverSafeMissileViewSnapshot view =
            _trackState.BuildPlayerMissileView(
                _missileEngagement,
                _selectedMissileSalvoId);
        _selectedMissileSalvoId = view.SelectedSalvoId;

        GuidedMissileSalvo? selectedSalvo = view.SelectedSalvoId is null
            ? null
            : _missileEngagement.Find(view.SelectedSalvoId);
        bool selectedAsWeaponTarget =
            _turnState.Phase == TacticalTurnPhase.DirectFire &&
            !_directFireResolved &&
            selectedSalvo is not null &&
            EvaluateSpecificMissileDirectFireEligibility(selectedSalvo)
                .CanCommitSpecificMissileOrder;
        _board.SetMissileState(
            view.Contacts,
            view.Projections,
            view.SelectedSalvoId,
            selectedAsWeaponTarget,
            showStaticRoute:
                _selectedPlayerTargetId == _scenario?.EnemyShipId &&
                _trackState.PlayerTrackOnEnemy?.EstimatedCoordinate.HasValue == true);
        _board.SetResolutionCues(_resolutionCues);
        LogMissileStackChanges(view.Contacts);
    }

    private void LogMissileStackChanges(
        IReadOnlyList<TacticalMissileContact> missileContacts)
    {
        IReadOnlyList<TacticalMissileContactStack> stacks =
            TacticalMissileStackService.Build(missileContacts);
        string signature = string.Join(
            ";",
            stacks.Select(stack =>
                $"{stack.OwnerSide}:{Format(stack.Coordinate)}:" +
                string.Join(",", stack.Contacts.Select(contact => contact.SalvoId))));
        if (string.Equals(signature, _lastMissileStackSignature, StringComparison.Ordinal))
        {
            return;
        }

        bool previouslyHadStacks = _lastMissileStackSignature.Contains(",", StringComparison.Ordinal);
        _lastMissileStackSignature = signature;
        TacticalMissileContactStack[] collocated = stacks
            .Where(stack => stack.IsStacked)
            .ToArray();

        if (collocated.Length == 0)
        {
            if (previouslyHadStacks)
            {
                _diagnosticLog?.Record(
                    DiagnosticEventType.MissileStackChanged,
                    "No observer-visible missile contacts are currently collocated.",
                    turnNumber: _turnState.TurnNumber,
                    phase: _turnState.Phase,
                    data: DiagnosticData(("stackCount", "0")));
            }
            return;
        }

        foreach (TacticalMissileContactStack stack in collocated)
        {
            string salvoIds = string.Join(",", stack.Contacts.Select(contact => contact.SalvoId));
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileStackChanged,
                $"{stack.Count} {stack.OwnerSide} missile contacts are collocated at {Format(stack.Coordinate)}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                coordinateAfter: stack.Coordinate,
                data: DiagnosticData(
                    ("ownerSide", stack.OwnerSide.ToString()),
                    ("visibleCount", stack.Count.ToString()),
                    ("salvoIds", salvoIds)));
        }
    }

    private void UpdateAllTextAndControls()
    {
        UpdateResultText();
        UpdateTurnControls();
        UpdateMovementControls();
        UpdateDirectFireControls();
        UpdateMissileControls();
        UpdateDefenseReadiness();
        UpdateTrackText();
        UpdateAuthoritativeMissileDebugText();
        UpdateDiagnosticLogText();
        SyncKnowledgeBoardState();
        SyncMissileBoardState();
        _board.RefreshDisplay();
    }

    private void UpdateTrackText()
    {
        TacticalTrackRecord? enemyTrack = _trackState.PlayerTrackOnEnemy;
        string enemyState = enemyTrack is null
            ? "Unknown: no contact record exists."
            : enemyTrack.Quality == TacticalTrackQuality.Lost
                ? "Lost: no usable display coordinate remains."
                : $"{enemyTrack.Quality} at {Format(enemyTrack.EstimatedCoordinate!.Value)}; uncertainty radius {enemyTrack.UncertaintyRadiusHexes}; missed updates {enemyTrack.MissedUpdateCount}.";
        SensorContactEvaluationResult? playerEvaluation =
            _trackState.GetLastSensorEvaluation(
                _scenario.PlayerShipId,
                _scenario.EnemyShipId);
        SensorContactEvaluationResult? enemyEvaluation =
            _trackState.GetLastSensorEvaluation(
                _scenario.EnemyShipId,
                _scenario.PlayerShipId);

        _sensorSummaryLabel.Text =
            $"PLAYER -> ENEMY  {FormatCompactSensorEvaluation(playerEvaluation)}\n" +
            $"ENEMY -> PLAYER  {FormatCompactSensorEvaluation(enemyEvaluation)}";

        _trackStateLabel.Text =
            $"Track sequence {_trackState.Sequence}. Player track on enemy: {enemyState}\n" +
            $"Player sensing detail: {FormatSensorEvaluation(playerEvaluation)}\n" +
            $"Enemy sensing detail: {FormatSensorEvaluation(enemyEvaluation)}\n" +
            $"Sensors TL {_sensorProfile.TechnologyLevel}: base Firm {_sensorProfile.FirmRangeHexes}, base Approximate {_sensorProfile.ApproximateRangeHexes}, Active bonus +{_sensorProfile.ActiveModeRangeBonusHexes}; " +
            $"Computing TL {_computingProfile.TechnologyLevel}: retains Stale tracks for {_computingProfile.StaleRetentionUpdates} missed tactical turns. " +
            $"Current observation epoch: {_trackState.ObservationEpoch}. Every star is pre-known navigation data.";
    }

    private void UpdateResultText()
    {
        var text = new StringBuilder();
        TacticalTrackRecord? enemyTrack = _trackState.PlayerTrackOnEnemy;
        bool firmEnemyTrack = DirectFireTrackEligibility.CanTarget(enemyTrack);
        text.AppendLine(
            $"Player enemy track: {enemyTrack?.Quality.ToString() ?? "Unknown"}; precision direct fire {(firmEnemyTrack ? "eligible" : "not eligible")}.");

        if (firmEnemyTrack)
        {
            text.AppendLine($"Direct fire: {_lineOfSight.Quality}");
            text.AppendLine(
                $"Tracked distance: {_scenario.PlayerPosition.DistanceTo(enemyTrack!.EstimatedCoordinate!.Value)} hexes");
        }

        if (firmEnemyTrack && _lineOfSight.GrazingCount > 0)
        {
            text.AppendLine($"Grazings: {_lineOfSight.GrazingCount}");

            foreach (LineOfSightGrazing grazing in _lineOfSight.Grazings)
            {
                string names = string.Join(
                    ", ",
                    grazing.Blockers.Select(item => item.MapObject.Name));
                text.AppendLine(
                    $"  Range {grazing.RangeStep}: {names} at {Format(grazing.BlockedCoordinate)}");
            }
        }

        if (firmEnemyTrack && _lineOfSight.Blockage is not null)
        {
            string blockers = string.Join(
                ", ",
                _lineOfSight.Blockage.Blockers.Select(
                    item => $"{item.MapObject.Name} {Format(item.Coordinate)}"));
            text.AppendLine(
                $"Blockage at range {_lineOfSight.Blockage.RangeStep}: {blockers}");
        }

        text.AppendLine();
        text.AppendLine(
            $"Sublight: TL {_playerMovementProfile.TechnologyLevel}, allowance {_playerMovementProfile.MaximumHexesPerTurn}/turn, legal destinations {_legalMovementDestinations.Count}");
        text.AppendLine();
        if (enemyTrack is { IsVisibleOnTacticalMap: true })
        {
            text.AppendLine(
                $"Player launch projection: {_playerMissileRoute.Status}; routed {FormatNullable(_playerMissileRoute.RoutedDistance)} toward the {enemyTrack.Quality} track coordinate.");
        }
        else
        {
            text.AppendLine("Player launch projection: unavailable without a usable enemy track.");
        }

        text.AppendLine(
            "Enemy launch projection uses the enemy observer's own track and remains hidden from the player-facing tactical picture.");
        text.AppendLine(
            $"Missile profile: TL {_missileProfile.TechnologyLevel}, lifetime range {_missileProfile.MaximumRange}, speed {_missileProfile.SpeedHexesPerTurn}/phase; " +
            $"Guidance Computer hit {_missileTerminalProfile.GuidanceComputer.BaseHitChancePercent}% bounded " +
            $"{_missileTerminalProfile.GuidanceComputer.MinimumHitChancePercent}-{_missileTerminalProfile.GuidanceComputer.MaximumHitChancePercent}%; " +
            $"terminal seeker accuracy +{_missileTerminalProfile.Seeker.AccuracyBonusPercent}%.");
        text.AppendLine(
            $"Missile onboard sensor: TL {_missileSensorProfile.TechnologyLevel}, passive-first firm {_missileSensorProfile.Sensor.FirmRangeHexes}, approximate {_missileSensorProfile.Sensor.ApproximateRangeHexes}, active bonus +{_missileSensorProfile.Sensor.ActiveModeRangeBonusHexes}.");
        text.AppendLine(
            $"Main direct-fire weapon: TL {_mainWeaponProfile.TechnologyLevel}, range {_mainWeaponProfile.MaximumRangeHexes}; one mutually exclusive commitment per turn.");
        text.AppendLine(
            $"Point-defense auxiliary: TL {_pointDefenseProfile.TechnologyLevel}, range {_pointDefenseProfile.InterceptionRangeHexes}, reaction capacity {_pointDefenseProfile.MaximumAttemptsPerPhase}/phase; at most one attempt per defending ship in each terminal window; independent of the main weapon.");

        GuidedMissileSalvo? selected = SelectedSalvo();
        if (selected is not null &&
            _lastAdvanceBySalvo.TryGetValue(
                selected.Id,
                out GuidedMissileAdvanceResult? lastAdvance) &&
            lastAdvance is not null)
        {
            text.AppendLine();
            text.AppendLine(
                $"Selected {selected.Id}: last phase moved {lastAdvance.DistanceTraveledThisPhase}; interception attempts {lastAdvance.InterceptionAttempts.Count}; status {lastAdvance.Status}.");
        }

        _resultLabel.Text = text.ToString().TrimEnd();
    }

    private void UpdateTurnControls()
    {
        TacticalTurnPhase nextPhase = NextPhase(_turnState.Phase);
        bool unresolvedMovement =
            _turnState.IsMovementPhase && !_playerMovementResolved;
        bool unresolvedDirectFire =
            _turnState.Phase == TacticalTurnPhase.DirectFire &&
            !_directFireResolved;
        bool unresolvedMissiles =
            _turnState.Phase == TacticalTurnPhase.MissileAndInterception &&
            HasUnresolvedActiveSalvos();

        _advancePhaseButton.Text = $"Advance to {FormatPhase(nextPhase)}";
        _advancePhaseButton.Disabled =
            unresolvedMovement || unresolvedDirectFire || unresolvedMissiles;

        string gateMessage = unresolvedMovement
            ? "Move as desired, then end movement before advancing."
            : unresolvedDirectFire
                ? "Commit or hold the main direct-fire weapon before advancing."
                : unresolvedMissiles
                    ? "Advance every unresolved active salvo once before leaving this phase."
                    : "The next phase is available.";

        _turnStateLabel.Text =
            $"Turn {_turnState.TurnNumber}; phase: {FormatPhase(_turnState.Phase)}. " +
            gateMessage;

        _movementCommandPanel.Visible = _turnState.Phase == TacticalTurnPhase.Movement;
        _directFireCommandPanel.Visible = _turnState.Phase == TacticalTurnPhase.DirectFire;
        _missileCommandPanel.Visible =
            _turnState.Phase == TacticalTurnPhase.MissileAndInterception;
    }

    private void UpdateDefenseReadiness()
    {
        int pdsUsed = _interceptionContext?.AttemptsUsed("point-defense-player") ?? 0;
        int pdsRemaining = Math.Max(
            0,
            _pointDefenseProfile.MaximumAttemptsPerPhase - pdsUsed);
        int heldUsed = _interceptionContext?.AttemptsUsed("held-main-weapon-player") ?? 0;
        string mainLayer = _heldDirectFireOrderArmed
            ? $"Held main weapon: armed; attempts used {heldUsed}/1."
            : _directFireOrder is { CreatesHeldInterception: true }
                ? $"Held main weapon: order spent or expired; attempts used {heldUsed}/1."
                : "Held main weapon: not reserved this turn.";

        _pointDefenseStatusLabel.Text =
            $"Installed PDS auxiliary: TL {_pointDefenseProfile.TechnologyLevel}, " +
            $"range {_pointDefenseProfile.InterceptionRangeHexes}, automatic local acquisition. " +
            $"Attempts remaining this missile phase: {pdsRemaining}/{_pointDefenseProfile.MaximumAttemptsPerPhase}.\n" +
            mainLayer;
    }

    private void UpdateMovementControls()
    {
        bool movementPhase = _turnState.IsMovementPhase;
        bool validPreview = _movementPreview is { CanMove: true } preview &&
            preview.Destination != _playerMovementState.CurrentCoordinate;
        bool canIssueMovementCommand =
            movementPhase && !_playerMovementResolved;

        _commitMoveButton.Disabled = !canIssueMovementCommand || !validPreview;
        _holdButton.Disabled = !canIssueMovementCommand;

        if (!movementPhase)
        {
            _movementStateLabel.Text =
                $"Movement is closed during {FormatPhase(_turnState.Phase)}. " +
                (_movementCommandMessage ??
                    "Complete the turn to return to Movement, or reset the scenario.");
            return;
        }

        if (_playerMovementResolved)
        {
            _movementStateLabel.Text =
                _movementCommandMessage ??
                "The player ship has completed movement for this turn.";
            return;
        }

        string stateSummary =
            $"Player at {Format(_playerMovementState.CurrentCoordinate)}; " +
            $"movement {_playerMovementState.RemainingDistance}/{_playerMovementState.MaximumDistance} remains; " +
            $"{Math.Max(0, _legalMovementDestinations.Count - 1)} destinations are reachable.";

        if (_movementPreview is null)
        {
            _movementStateLabel.Text =
                stateSummary +
                " Select an adjacent hex for one step or any highlighted destination for automatic per-hex execution. You may then move again or end movement.";
            return;
        }

        _movementStateLabel.Text =
            stateSummary + "\n" +
            $"Preview {_movementPreview.Status}: {Format(_movementPreview.Origin)} to {Format(_movementPreview.Destination)}; " +
            $"direct {_movementPreview.DirectDistance}; routed {FormatNullable(_movementPreview.RoutedDistance)}; " +
            $"remaining allowance {_movementPreview.MaximumDistance}. Every intermediate hex will resolve separately.";
    }

    private void UpdateDirectFireControls()
    {
        bool directFirePhase =
            _turnState.Phase == TacticalTurnPhase.DirectFire;
        GuidedMissileSalvo? selectedSalvo = SelectedSalvo();
        TacticalTrackRecord? selectedMissileTrack = selectedSalvo is null
            ? null
            : _trackState.PlayerTrackOn(selectedSalvo.Id);
        bool selectedHostileMissile =
            selectedSalvo is not null &&
            selectedSalvo.OwnerSide == TacticalSide.Enemy &&
            !selectedSalvo.IsTerminal &&
            selectedMissileTrack is { IsVisibleOnTacticalMap: true };
        TacticalTrackRecord? enemyTrack = _trackState.PlayerTrackOnEnemy;
        bool selectedEnemyShip =
            _selectedDirectFireShipTargetId == _scenario.EnemyShipId;
        DirectFireTargetEligibilityResult shipEligibility =
            EvaluateEnemyShipDirectFireEligibility();
        DirectFireTargetEligibilityResult? missileEligibility =
            selectedSalvo is null
                ? null
                : EvaluateSpecificMissileDirectFireEligibility(selectedSalvo);
        bool canResolve = directFirePhase && !_directFireResolved;

        _fireAtShipButton.Disabled =
            !canResolve || !selectedEnemyShip || !shipEligibility.CanCommitNow;
        _interceptSelectedMissileButton.Disabled =
            !canResolve ||
            !selectedHostileMissile ||
            missileEligibility is null ||
            !missileEligibility.CanCommitSpecificMissileOrder;
        _interceptSelectedMissileButton.Text =
            missileEligibility?.IsReserveOnly == true
                ? "Reserve main weapon against selected missile"
                : "Intercept selected missile now";
        _holdForAnyMissileButton.Disabled = !canResolve;
        _holdFireButton.Disabled = !canResolve;

        var text = new StringBuilder();
        text.AppendLine(
            $"Main weapon: TL {_mainWeaponProfile.TechnologyLevel}; range {_mainWeaponProfile.MaximumRangeHexes}; missile-capable: {_mainWeaponProfile.CanInterceptMissiles}.");

        if (!directFirePhase)
        {
            text.AppendLine(
                $"Direct-fire commitment is closed during {FormatPhase(_turnState.Phase)}.");
        }
        else if (_directFireResolved)
        {
            text.AppendLine(
                _directFireActionMessage ??
                "The main direct-fire weapon has resolved its commitment this turn.");
        }
        else if (selectedHostileMissile)
        {
            text.AppendLine(
                $"Inspected hostile missile: {selectedSalvo!.Id}, " +
                $"{selectedMissileTrack!.Quality} track at " +
                $"{Format(selectedMissileTrack.EstimatedCoordinate!.Value)}.");
            text.AppendLine(DescribeSpecificMissileEligibility(
                missileEligibility!));
        }
        else if (selectedEnemyShip && enemyTrack is not null)
        {
            string coordinate = enemyTrack.EstimatedCoordinate.HasValue
                ? Format(enemyTrack.EstimatedCoordinate.Value)
                : "no usable coordinate";
            text.AppendLine(
                $"Inspected ship contact: Enemy Ship, {enemyTrack.Quality} at {coordinate}.");
            text.AppendLine(DescribeShipEligibility(shipEligibility));
        }
        else
        {
            text.AppendLine(
                "No direct-fire target selected. Click a tracked red contact for inspection, reserve the weapon for any incoming missile, or explicitly hold fire.");
        }

        if (_heldDirectFireOrderArmed &&
            _directFireOrder is { CreatesHeldInterception: true } heldOrder)
        {
            string target = heldOrder.TargetMissileSalvoId is null
                ? "the first eligible hostile missile"
                : heldOrder.TargetMissileSalvoId;
            text.AppendLine(
                $"Held order armed for {target}; it expires after the upcoming Missile / Interception phase if unused.");
        }

        _directFireStateLabel.Text = text.ToString().TrimEnd();
    }

    private DirectFireTargetEligibilityResult EvaluateEnemyShipDirectFireEligibility()
    {
        TacticalTrackRecord? track = _trackState.PlayerTrackOnEnemy;
        return DirectFireTargetEligibility.EvaluateShipAttack(
            track?.Quality ?? TacticalTrackQuality.Lost,
            track?.EstimatedCoordinate,
            _scenario.PlayerPosition,
            _mainWeaponProfile,
            _lineOfSight.Quality != LineOfSightQuality.Blocked);
    }

    private DirectFireTargetEligibilityResult EvaluateSpecificMissileDirectFireEligibility(
        GuidedMissileSalvo salvo)
    {
        TacticalTrackRecord? track = _trackState.PlayerTrackOn(salvo.Id);
        HexCoord? coordinate = track?.EstimatedCoordinate;
        bool hasLineOfSight = coordinate.HasValue &&
            HasDirectFireLineOfSightTo(coordinate.Value);
        return DirectFireTargetEligibility.EvaluateSpecificMissileOrder(
            track?.Quality ?? TacticalTrackQuality.Lost,
            coordinate,
            _scenario.PlayerPosition,
            _mainWeaponProfile,
            hasLineOfSight);
    }

    private static string DescribeShipEligibility(
        DirectFireTargetEligibilityResult eligibility) => eligibility.Status switch
    {
        DirectFireTargetEligibilityStatus.EligibleNow =>
            $"Ship attack available now at {eligibility.DistanceHexes} hexes with clear LOS.",
        DirectFireTargetEligibilityStatus.MissingFirmTrack =>
            "Ship attack unavailable: precision direct fire requires a current Firm track.",
        DirectFireTargetEligibilityStatus.BlockedLineOfSight =>
            "Ship attack unavailable: weapon LOS is blocked and ships will not move again this turn.",
        DirectFireTargetEligibilityStatus.OutOfRange =>
            $"Ship attack unavailable: target is out of range at {eligibility.DistanceHexes} hexes.",
        _ => "Ship attack unavailable: no usable current firing solution.",
    };

    private static string DescribeSpecificMissileEligibility(
        DirectFireTargetEligibilityResult eligibility) => eligibility.Status switch
    {
        DirectFireTargetEligibilityStatus.EligibleNow =>
            $"Specific interception available now at {eligibility.DistanceHexes} hexes with a Firm track and clear LOS.",
        DirectFireTargetEligibilityStatus.EligibleForSpecificMissileReserve =>
            $"Specific reserve available: Firm track and clear LOS are established, but the missile is out of range at {eligibility.DistanceHexes} hexes. The weapon may fire if it closes this turn.",
        DirectFireTargetEligibilityStatus.MissingFirmTrack =>
            "Specific interception unavailable: the contact is not Firm. Use Hold main weapon for any missile instead.",
        DirectFireTargetEligibilityStatus.BlockedLineOfSight =>
            "Specific interception unavailable: weapon LOS is blocked. Use Hold main weapon for any missile instead.",
        DirectFireTargetEligibilityStatus.WeaponCannotInterceptMissiles =>
            "Specific interception unavailable: this weapon cannot engage missiles.",
        _ => "Specific interception unavailable: no usable current firing solution. Use Hold main weapon for any missile instead.",
    };

    private void UpdateMissileControls()
    {
        bool missilePhase =
            _turnState.Phase == TacticalTurnPhase.MissileAndInterception;
        TacticalTrackRecord? playerEnemyTrack = _trackState.PlayerTrackOnEnemy;
        bool playerTargetSelected =
            _selectedPlayerTargetId == _scenario.EnemyShipId &&
            playerEnemyTrack is { IsVisibleOnTacticalMap: true };
        bool phaseHasActions =
            _playerLaunchedThisPhase ||
            _enemyLaunchedThisPhase ||
            _salvosResolvedThisPhase.Count > 0;

        _launchPlayerButton.Disabled =
            !missilePhase ||
            _playerLaunchedThisPhase ||
            !playerTargetSelected ||
            !_playerMissileRoute.CanLaunch;

        _launchEnemyButton.Disabled =
            !missilePhase ||
            _enemyLaunchedThisPhase ||
            !_enemyMissileRoute.CanLaunch;

        _advanceMissilesButton.Disabled =
            !missilePhase ||
            !HasUnresolvedActiveSalvos();

        _interceptionSucceedsToggle.Disabled = missilePhase && phaseHasActions;

        _playerTargetLabel.Text = playerTargetSelected
            ? $"Player missile target: Enemy Ship, {playerEnemyTrack!.Quality} track at {Format(playerEnemyTrack.EstimatedCoordinate!.Value)}."
            : "Player missile target: none or not currently visible. Select Missile route and click a tracked red enemy contact.";

        var text = new StringBuilder();
        text.AppendLine(
            $"Demonstration interception result: {(_interceptionSucceedsToggle.ButtonPressed ? "INTERCEPT" : "MISS")}. " +
            "A held main weapon and the point-defense auxiliary have separate one-attempt budgets; each budget is shared across all salvos in this missile phase.");
        ObserverSafeMissileViewSnapshot missileView =
            _trackState.BuildPlayerMissileView(
                _missileEngagement,
                _selectedMissileSalvoId);
        IReadOnlyList<TacticalMissileContact> missileContacts =
            missileView.Contacts;
        IReadOnlyDictionary<string, MissileRouteProjection> projections =
            missileView.Projections.ToDictionary(
                projection => projection.SalvoId,
                StringComparer.Ordinal);
        text.AppendLine(
            $"Known active salvos: {missileContacts.Count(contact => !contact.IsTerminal)}; known terminal salvos: {missileContacts.Count(contact => contact.IsTerminal)}.");

        if (missileContacts.Count == 0)
        {
            text.AppendLine(
                missilePhase
                    ? "No known salvos exist. Launch a selected player missile, an explicitly labeled enemy missile, or advance the phase without firing."
                    : "No known salvos exist. Reach Missile / Interception to launch.");
        }
        else
        {
            foreach (TacticalMissileContact contact in missileContacts)
            {
                string ownership = contact.OwnerSide == TacticalSide.Player
                    ? "Friendly F"
                    : contact.OwnerSide == TacticalSide.Enemy
                        ? "Enemy E"
                        : "Unspecified M";
                string resolved = !missilePhase || contact.IsTerminal
                    ? string.Empty
                    : _salvosResolvedThisPhase.Contains(contact.SalvoId)
                        ? "; resolved this phase"
                        : "; UNRESOLVED this phase";
                string interception =
                    contact.InterceptedByDefenseSystemId is null
                        ? string.Empty
                        : $"; intercepted by {contact.InterceptedByDefenseSystemId}";
                string projection = projections.TryGetValue(
                    contact.SalvoId,
                    out MissileRouteProjection? routeProjection)
                    ? routeProjection.Status ==
                        MissileRouteProjectionStatus.WithheldByObserverUncertainty
                        ? "; incoming-threat estimate withheld because the hostile contact is not Firm"
                        : contact.OwnerSide == TacticalSide.Player
                            ? $"; dashed friendly planned route {routeProjection.Status} via {routeProjection.TrackQuality?.ToString() ?? "no track"}"
                            : $"; dotted incoming-threat estimate {routeProjection.Status}; not a confirmed enemy lock"
                    : string.Empty;
                string trail = contact.HasUnobservedTravelGap
                    ? $"; observed trail has {contact.VisibleTravelSegments.Count} disconnected segments"
                    : contact.VisibleTravelSegments.Any(segment => segment.Count >= 2)
                        ? "; observed trail continuous"
                        : "; no observed travel segment";
                GuidedMissileSalvo? authoritativeSalvo =
                    _missileEngagement.Salvos.FirstOrDefault(item =>
                        string.Equals(
                            item.Id,
                            contact.SalvoId,
                            StringComparison.Ordinal));
                // Enemy datalink state is not added to normal player-visible contact summaries.
                string datalink = contact.OwnerSide == TacticalSide.Player &&
                    authoritativeSalvo is not null
                    ? $"; datalink {authoritativeSalvo.DatalinkState}; retained report age {authoritativeSalvo.RetainedDatalinkReport?.AgePhases.ToString() ?? "none"}; selected guidance {authoritativeSalvo.LastGuidanceSource}"
                    : string.Empty;

                text.AppendLine(
                    $"{ownership} {contact.SalvoId}: {contact.LauncherId} -> {contact.TargetId}; " +
                    $"observed at {Format(contact.Coordinate)} with {contact.TrackQuality} track; " +
                    $"moved {contact.DistanceTraveled}; fuel {contact.TotalFuelSpent}/{contact.MaximumRange}; " +
                    $"remaining {contact.RemainingRange}; status {contact.Status}{resolved}{interception}{projection}{trail}{datalink}.");
            }
        }

        if (!string.IsNullOrWhiteSpace(_missileActionMessage))
        {
            text.AppendLine();
            text.AppendLine(_missileActionMessage);
        }

        _missileStateLabel.Text = text.ToString().TrimEnd();
    }

    private void PreviewMovement(HexCoord destination)
    {
        if (!_turnState.IsMovementPhase || _playerMovementResolved)
        {
            return;
        }

        _movementPreview = ShipMovementTurnService.PlanDestination(
            _scenario.Map,
            _playerMovementState,
            destination);

        _board.SetMovementOverlay(_legalMovementDestinations, _movementPreview);
        UpdateMovementControls();
    }

    private void CommitPlayerMovement()
    {
        if (!_turnState.IsMovementPhase ||
            _playerMovementResolved ||
            _movementPreview is null ||
            !_movementPreview.CanMove ||
            _movementPreview.Path is not { Count: > 1 } path)
        {
            return;
        }

        HexCoord commandOrigin = _playerMovementState.CurrentCoordinate;
        int remainingBefore = _playerMovementState.RemainingDistance;
        HexCoord[] enteredCoordinates = path.Skip(1).ToArray();
        _diagnosticLog?.Record(
            DiagnosticEventType.ShipMovementDestinationCommitted,
            $"Player committed a route from {Format(commandOrigin)} to {Format(_movementPreview.Destination)}; every entered hex will resolve authoritatively.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: _scenario.PlayerShipId,
            coordinateBefore: commandOrigin,
            coordinateAfter: _movementPreview.Destination,
            data: DiagnosticData(
                ("plannedPath", FormatPath(path)),
                ("plannedDistance", enteredCoordinates.Length.ToString()),
                ("remainingBefore", remainingBefore.ToString())));

        _movementPreview = null;
        string? routeInterruptionMessage = null;
        foreach (HexCoord nextCoordinate in enteredCoordinates)
        {
            HashSet<string> visibleHostileMissilesBefore =
                VisibleHostileMissileIds();
            ShipMovementStepExecutionResult step =
                _scenario.MovePlayerShipOneHex(
                    nextCoordinate,
                    _playerMovementState);
            if (!step.WasCommitted)
            {
                _movementCommandMessage =
                    $"Movement stopped at {Format(_playerMovementState.CurrentCoordinate)} because step {Format(nextCoordinate)} was rejected as {step.Status}.";
                _immediateFeedbackLabel.Text = _movementCommandMessage;
                break;
            }

            _playerMovementState = step.State;
            _diagnosticLog?.Record(
                DiagnosticEventType.ShipMovementStepResolved,
                $"Player entered {Format(step.CoordinateAfter)}; {_playerMovementState.RemainingDistance} movement remains.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: _scenario.PlayerShipId,
                coordinateBefore: step.CoordinateBefore,
                coordinateAfter: step.CoordinateAfter,
                data: DiagnosticData(
                    ("distanceSpent", _playerMovementState.DistanceSpent.ToString()),
                    ("remainingMovement", _playerMovementState.RemainingDistance.ToString()),
                    ("stepStatus", step.Status.ToString())));
            LogTrackUpdates(_trackState.Refresh(
                TrackUpdateTrigger.ShipMovementStepCommitted,
                _missileEngagement.Salvos,
                _turnState.TurnNumber));
            RefreshLocalSensorsAfterTargetMovement();
            RecalculateDerivedState(resetBoardScenario: true);

            string[] newlyVisibleMissiles = VisibleHostileMissileIds()
                .Except(visibleHostileMissilesBefore, StringComparer.Ordinal)
                .OrderBy(id => id, StringComparer.Ordinal)
                .ToArray();
            if (newlyVisibleMissiles.Length > 0 &&
                nextCoordinate != enteredCoordinates[^1])
            {
                routeInterruptionMessage =
                    $"Automatic route paused at {Format(_playerMovementState.CurrentCoordinate)} after acquiring {string.Join(", ", newlyVisibleMissiles)}. {_playerMovementState.RemainingDistance} movement remains.";
                break;
            }
        }

        if (_playerMovementState.RemainingDistance == 0)
        {
            _playerMovementResolved = true;
            _movementCommandMessage =
                $"Movement allowance exhausted at {Format(_playerMovementState.CurrentCoordinate)} after {_playerMovementState.DistanceSpent} entered hexes.";
            RecordMovementCompletion("Movement allowance exhausted.");
        }
        else if (!string.IsNullOrWhiteSpace(routeInterruptionMessage))
        {
            _movementCommandMessage = routeInterruptionMessage;
        }
        else if (string.IsNullOrWhiteSpace(_movementCommandMessage) ||
            !_movementCommandMessage.StartsWith("Movement stopped", StringComparison.Ordinal))
        {
            _movementCommandMessage =
                $"Route completed at {Format(_playerMovementState.CurrentCoordinate)}. {_playerMovementState.RemainingDistance} movement remains; choose another destination or end movement.";
        }

        _immediateFeedbackLabel.Text = _movementCommandMessage;
        _board.DisplayMode = TargetingMode.Movement;
        UpdateAllTextAndControls();
    }

    private void HoldPlayerPosition()
    {
        if (!_turnState.IsMovementPhase || _playerMovementResolved)
        {
            return;
        }

        _movementPreview = null;
        _playerMovementState = ShipMovementTurnService.EndMovement(
            _playerMovementState);
        _playerMovementResolved = true;
        _movementCommandMessage =
            $"Movement ended at {Format(_playerMovementState.CurrentCoordinate)} with {_playerMovementState.RemainingDistance} movement unspent.";
        _immediateFeedbackLabel.Text = _movementCommandMessage;
        RecordMovementCompletion("Player ended movement.");
        _legalMovementDestinations = Array.Empty<HexCoord>();
        _board.SetMovementOverlay(_legalMovementDestinations, null);
        UpdateAllTextAndControls();
    }

    private HashSet<string> VisibleHostileMissileIds() =>
        _trackState.PlayerMissileContacts(_missileEngagement.Salvos)
            .Where(contact =>
                contact.OwnerSide == TacticalSide.Enemy &&
                !contact.IsTerminal)
            .Select(contact => contact.SalvoId)
            .ToHashSet(StringComparer.Ordinal);

    private void RecordMovementCompletion(string reason)
    {
        _diagnosticLog?.Record(
            DiagnosticEventType.ShipMovementResolved,
            reason,
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: _scenario.PlayerShipId,
            coordinateBefore: _playerMovementState.StartingCoordinate,
            coordinateAfter: _playerMovementState.CurrentCoordinate,
            data: DiagnosticData(
                ("movementAllowance", _playerMovementState.MaximumDistance.ToString()),
                ("distanceSpent", _playerMovementState.DistanceSpent.ToString()),
                ("remainingMovement", _playerMovementState.RemainingDistance.ToString()),
                ("executedPath", FormatPath(_playerMovementState.ExecutedPath))));
    }

    private void ResolveDirectFireAtShip()
    {
        if (_turnState.Phase != TacticalTurnPhase.DirectFire ||
            _directFireResolved ||
            _selectedDirectFireShipTargetId != _scenario.EnemyShipId)
        {
            return;
        }

        DirectFireTargetEligibilityResult eligibility =
            EvaluateEnemyShipDirectFireEligibility();
        if (!eligibility.CanCommitNow)
        {
            return;
        }

        _directFireOrder = DirectFireOrder.FireAtShip(
            $"direct-fire-turn-{_turnState.TurnNumber}",
            "player-main-weapon",
            _scenario.PlayerShipId,
            TacticalSide.Player,
            _scenario.PlayerPosition,
            _mainWeaponProfile,
            _scenario.EnemyShipId);
        _directFireResolved = true;
        _heldDirectFireOrderArmed = false;

        _directFireActionMessage =
            $"Main weapon committed to Enemy Ship; resolved with {_lineOfSight.Quality} LOS at {eligibility.DistanceHexes} hexes. The weapon cannot also intercept this turn.";
        LogDirectFireCommitment(_directFireActionMessage);
        UpdateAllTextAndControls();
    }

    private void CommitSpecificMissileInterception()
    {
        if (_turnState.Phase != TacticalTurnPhase.DirectFire ||
            _directFireResolved)
        {
            return;
        }

        GuidedMissileSalvo? salvo = SelectedSalvo();
        if (salvo is null ||
            salvo.OwnerSide != TacticalSide.Enemy ||
            salvo.IsTerminal)
        {
            return;
        }

        DirectFireTargetEligibilityResult eligibility =
            EvaluateSpecificMissileDirectFireEligibility(salvo);
        if (!eligibility.CanCommitSpecificMissileOrder)
        {
            return;
        }

        _directFireOrder = DirectFireOrder.InterceptSpecificMissile(
            $"direct-fire-turn-{_turnState.TurnNumber}",
            "player-main-weapon",
            _scenario.PlayerShipId,
            TacticalSide.Player,
            _scenario.PlayerPosition,
            _mainWeaponProfile,
            salvo.Id);
        _directFireResolved = true;

        if (eligibility.IsReserveOnly)
        {
            _heldDirectFireOrderArmed = true;
            _directFireActionMessage =
                $"Main weapon reserved for visible missile {salvo.Id}; current LOS is clear, but it is out of range at {eligibility.DistanceHexes} hexes. The order will fire if that same missile enters range during the upcoming Missile / Interception phase.";
            LogDirectFireCommitment(_directFireActionMessage);
            UpdateAllTextAndControls();
            return;
        }

        MissileDefenseSystem heldWeapon =
            _directFireOrder.CreateHeldDefenseSystem(
                "held-main-weapon-player",
                priority: 0);
        var immediateContext = new MissileInterceptionPhaseContext(
            new[] { heldWeapon },
            CreateInterceptionResolver(),
            _scenario.Map,
            new DemoMissileDefenseTrackProvider(
                _scenario,
                _sensorProfile,
                () => _trackState.CreatePlayerMissileEvaluationContext()));
        IReadOnlyList<MissileInterceptionAttemptResult> attempts =
            immediateContext.ResolveAt(
                salvo,
                salvo.CurrentCoordinate,
                isFinalApproach: false);
        _heldDirectFireOrderArmed = false;

        string result = attempts.Count > 0 && attempts[0].Intercepted
            ? "INTERCEPTED immediately during Direct Fire."
            : "interception attempted immediately and MISSED.";
        _directFireActionMessage =
            $"Main weapon committed to {salvo.Id}; {result} The weapon is spent for this turn.";
        LogDirectFireCommitment(_directFireActionMessage);
        LogInterceptionAttempts(attempts);
        SyncMissileBoardState();
        UpdateAllTextAndControls();
    }

    private void CommitHoldForAnyMissile()
    {
        if (_turnState.Phase != TacticalTurnPhase.DirectFire ||
            _directFireResolved)
        {
            return;
        }

        _directFireOrder = DirectFireOrder.HoldForAnyMissile(
            $"direct-fire-turn-{_turnState.TurnNumber}",
            "player-main-weapon",
            _scenario.PlayerShipId,
            TacticalSide.Player,
            _scenario.PlayerPosition,
            _mainWeaponProfile);
        _directFireResolved = true;
        _heldDirectFireOrderArmed = true;
        _directFireActionMessage =
            "Main weapon held for the first eligible hostile missile during the upcoming Missile / Interception phase. It may react to an existing salvo or one launched later this turn.";
        LogDirectFireCommitment(_directFireActionMessage);
        UpdateAllTextAndControls();
    }

    private void ResolveHoldFire()
    {
        if (_turnState.Phase != TacticalTurnPhase.DirectFire ||
            _directFireResolved)
        {
            return;
        }

        _directFireOrder = DirectFireOrder.HoldFire(
            $"direct-fire-turn-{_turnState.TurnNumber}",
            "player-main-weapon",
            _scenario.PlayerShipId,
            TacticalSide.Player,
            _scenario.PlayerPosition,
            _mainWeaponProfile);
        _directFireResolved = true;
        _heldDirectFireOrderArmed = false;
        _directFireActionMessage =
            "Main weapon explicitly held fire. Only the separate point-defense auxiliary may intercept this turn.";
        LogDirectFireCommitment(_directFireActionMessage);
        UpdateAllTextAndControls();
    }

    private bool HasDirectFireLineOfSightTo(HexCoord targetCoordinate)
    {
        if (_scenario.PlayerPosition == targetCoordinate)
        {
            return true;
        }

        DirectFireLineOfSightResult result = DirectFireLineOfSight.Evaluate(
            _scenario.Map,
            _scenario.PlayerPosition,
            targetCoordinate);
        return result.Quality != LineOfSightQuality.Blocked;
    }

    private void LogDirectFireCommitment(string message)
    {
        _immediateFeedbackLabel.Text = message;
        if (_diagnosticLog is null || _directFireOrder is null)
        {
            return;
        }

        string? targetId =
            _directFireOrder.TargetShipId ??
            _directFireOrder.TargetMissileSalvoId;
        _diagnosticLog.Record(
            DiagnosticEventType.DirectFireOrderCommitted,
            message,
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: _directFireOrder.DefenderShipId,
            targetId: targetId,
            coordinateBefore: _directFireOrder.OriginCoordinate,
            data: DiagnosticData(
                ("orderId", _directFireOrder.Id),
                ("weaponId", _directFireOrder.WeaponId),
                ("orderType", _directFireOrder.OrderType.ToString()),
                ("heldInterception", _directFireOrder.CreatesHeldInterception.ToString())));
    }

    private void LogInterceptionAttempts(
        IEnumerable<MissileInterceptionAttemptResult> attempts)
    {
        MissileInterceptionAttemptResult[] copied = attempts.ToArray();
        if (copied.Length == 0)
        {
            return;
        }

        var feedback = new List<string>();
        foreach (MissileInterceptionAttemptResult attempt in copied)
        {
            string layerName = string.Equals(
                attempt.DefenseSystemId,
                "held-main-weapon-player",
                StringComparison.Ordinal)
                ? "MAIN WEAPON"
                : string.Equals(
                    attempt.DefenseSystemId,
                    "point-defense-player",
                    StringComparison.Ordinal)
                    ? "PDS"
                    : attempt.DefenseSystemId;
            feedback.Add(
                $"{layerName} INTERCEPT - {attempt.SalvoId} - " +
                (attempt.Intercepted ? "INTERCEPTED" : "MISS"));

            _diagnosticLog?.Record(
                DiagnosticEventType.InterceptionTargetAcquired,
                $"{attempt.DefenseSystemId} acquired {attempt.SalvoId} for an interception attempt.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: attempt.DefenseSystemId,
                targetId: attempt.SalvoId,
                coordinateAfter: attempt.MissileCoordinate,
                data: DiagnosticData(
                    ("defenderShip", attempt.DefenderShipId),
                    ("acquisitionSource", layerName),
                    ("opportunity", attempt.Opportunity.ToString()),
                    ("finalApproach", attempt.IsFinalApproach.ToString())));

            _diagnosticLog?.Record(
                DiagnosticEventType.MissileInterceptionAttempted,
                $"{attempt.DefenseSystemId} attempted to intercept {attempt.SalvoId}: {attempt.Outcome}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: attempt.DefenseSystemId,
                targetId: attempt.SalvoId,
                coordinateAfter: attempt.MissileCoordinate,
                data: DiagnosticData(
                    ("defenderShip", attempt.DefenderShipId),
                    ("attemptNumber", attempt.AttemptNumberForSystemThisPhase.ToString()),
                    ("opportunity", attempt.Opportunity.ToString()),
                    ("finalApproach", attempt.IsFinalApproach.ToString()),
                    ("outcome", attempt.Outcome.ToString())));
        }

        foreach (string line in feedback)
        {
            if (!_persistentMissilePhaseFeedback.Contains(line))
            {
                _persistentMissilePhaseFeedback.Add(line);
            }
        }

        string currentFeedback = string.Join("\n", feedback);
        _immediateFeedbackLabel.Text =
            BuildPersistentMissilePhaseFeedback(string.Empty);
        _diagnosticLog?.Record(
            DiagnosticEventType.TacticalFeedback,
            currentFeedback,
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            data: DiagnosticData(("feedbackKind", "InterceptionResult")));
    }

    private string BuildPersistentMissilePhaseFeedback(string primary)
    {
        IEnumerable<string> lines = _persistentMissilePhaseFeedback;
        if (!string.IsNullOrWhiteSpace(primary))
        {
            lines = lines.Append(primary);
        }

        return string.Join("\n", lines);
    }

    private FixedMissileInterceptionResolver CreateInterceptionResolver()
    {
        MissileInterceptionOutcome outcome =
            _interceptionSucceedsToggle.ButtonPressed
                ? MissileInterceptionOutcome.Intercepted
                : MissileInterceptionOutcome.Missed;
        return new FixedMissileInterceptionResolver(outcome);
    }

    private void AdvanceTacticalPhase()
    {
        if ((_turnState.IsMovementPhase && !_playerMovementResolved) ||
            (_turnState.Phase == TacticalTurnPhase.DirectFire &&
             !_directFireResolved) ||
            (_turnState.Phase == TacticalTurnPhase.MissileAndInterception &&
             HasUnresolvedActiveSalvos()))
        {
            return;
        }

        int previousTurn = _turnState.TurnNumber;
        TacticalTurnPhase previousPhase = _turnState.Phase;
        _turnState.AdvancePhase();
        _diagnosticLog?.Record(
            DiagnosticEventType.PhaseAdvanced,
            $"Tactical phase advanced from Turn {previousTurn} {previousPhase} to Turn {_turnState.TurnNumber} {_turnState.Phase}.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            data: DiagnosticData(
                ("previousTurn", previousTurn.ToString()),
                ("previousPhase", previousPhase.ToString()),
                ("currentTurn", _turnState.TurnNumber.ToString()),
                ("currentPhase", _turnState.Phase.ToString())));
        _movementPreview = null;
        EnterPhase(_turnState.Phase, resetTurnState: true);
        UpdateAllTextAndControls();
    }

    private void EnterPhase(
        TacticalTurnPhase phase,
        bool resetTurnState)
    {
        _movementPreview = null;
        _selectedDirectFireShipTargetId = null;
        _selectedMissileSalvoId = null;
        bool preserveMissileResolutionCues =
            phase == TacticalTurnPhase.Damage && _resolutionCues.Count > 0;
        if (!preserveMissileResolutionCues)
        {
            _resolutionCues = Array.Empty<TacticalResolutionCue>();
            _board.SetResolutionCues(_resolutionCues);
        }
        _board.SetMovementOverlay(_legalMovementDestinations, null);

        switch (phase)
        {
            case TacticalTurnPhase.Movement:
                if (resetTurnState)
                {
                    _playerMovementResolved = false;
                    _playerMovementState = ShipMovementTurnService.Begin(
                        _scenario.PlayerPosition,
                        _playerMovementProfile);
                    _movementCommandMessage = null;
                    _directFireOrder = null;
                    _directFireResolved = false;
                    _heldDirectFireOrderArmed = false;
                    _directFireActionMessage = null;
                    _selectedPlayerTargetId = null;
                    _interceptionContext = null;
                    RecalculateDerivedState(resetBoardScenario: false);
                }

                _modeSelector.Select((int)TargetingMode.Movement);
                _board.DisplayMode = TargetingMode.Movement;
                _board.SetMovementOverlay(
                    _legalMovementDestinations,
                    preview: null);
                break;

            case TacticalTurnPhase.ElectronicWarfare:
                _diagnosticLog?.Record(
                    DiagnosticEventType.PhaseAdvanced,
                    "Electronic Warfare phase entered; ECM declarations and bounded ECCM response resolve before Direct Fire.",
                    turnNumber: _turnState.TurnNumber,
                    phase: phase);
                _modeSelector.Select((int)TargetingMode.DirectFire);
                _board.DisplayMode = TargetingMode.DirectFire;
                break;

            case TacticalTurnPhase.DirectFire:
                _directFireResolved = false;
                _heldDirectFireOrderArmed = false;
                _directFireOrder = null;
                _directFireActionMessage = null;
                _modeSelector.Select((int)TargetingMode.DirectFire);
                _board.DisplayMode = TargetingMode.DirectFire;
                break;

            case TacticalTurnPhase.MissileAndInterception:
                BeginMissilePhase();
                _modeSelector.Select((int)TargetingMode.Missile);
                _board.DisplayMode = TargetingMode.Missile;
                break;

            case TacticalTurnPhase.Damage:
                _diagnosticLog?.Record(
                    DiagnosticEventType.DamagePhaseEntered,
                    "Damage phase entered; detailed damage resolution remains deferred.",
                    turnNumber: _turnState.TurnNumber,
                    phase: phase);
                _modeSelector.Select((int)TargetingMode.DirectFire);
                _board.DisplayMode = TargetingMode.DirectFire;
                break;

            case TacticalTurnPhase.DamageControl:
                _diagnosticLog?.Record(
                    DiagnosticEventType.DamageControlPhaseEntered,
                    "Damage Control phase entered; detailed damage-control resolution remains deferred.",
                    turnNumber: _turnState.TurnNumber,
                    phase: phase);
                _modeSelector.Select((int)TargetingMode.DirectFire);
                _board.DisplayMode = TargetingMode.DirectFire;
                break;
        }

        SyncMissileBoardState();
    }

    private void BeginMissilePhase()
    {
        _salvosResolvedThisPhase.Clear();
        _launchesResolvedThisPhase.Clear();
        _playerLaunchedThisPhase = false;
        _enemyLaunchedThisPhase = false;
        _interceptionContext = null;
        _missileActionMessage = null;
        _persistentMissilePhaseFeedback.Clear();
        _immediateFeedbackLabel.Text =
            "Missile / Interception phase ready. Standard PDS may fire once on terminal entry and once immediately before a surviving Missile Flight attacks.";
    }

    private void LaunchPlayerMissile()
    {
        if (_turnState.Phase != TacticalTurnPhase.MissileAndInterception ||
            _playerLaunchedThisPhase ||
            _selectedPlayerTargetId != _scenario.EnemyShipId ||
            !_playerMissileRoute.CanLaunch)
        {
            return;
        }

        string salvoId = $"friendly-{_nextFriendlySalvoNumber++}";
        GuidedMissileAutonomousLaunchResult launch =
            MissileLaunchService.LaunchAndAdvanceAutonomousOnePhase(
                _scenario.Map,
                salvoId,
                TacticalSide.Player,
                _scenario.PlayerShipId,
                _scenario.EnemyShipId,
                _scenario.PlayerPosition,
                _missileProfile,
                _missileDatalinkProfile,
                MissileTargetTrackSnapshot.FromTacticalTrack(
                    _scenario.EnemyShipId,
                    _trackState.PlayerTrackOnEnemy),
                _trackState.GetGuidanceSourceObservationEpoch(
                    TacticalSide.Player,
                    _scenario.EnemyShipId),
                _missileSensorProfile,
                _scenario.EnemyPosition,
                _shipSignatureProfile,
                _trackState.EnemySensorMode,
                _enemyElectronicWarfare,
                _trackState.EnemyJammingEnabled,
                _sensorEnvironment,
                interceptionContext: GetOrCreateInterceptionContext(),
                terminalProfile: _missileTerminalProfile,
                terminalRandomSource: _terminalRandomSource);

        _missileEngagement.Add(launch.Salvo);
        RecordMissileDatalinkUpdate(
            launch.Salvo,
            launch.DatalinkUpdateResult);
        RecordAutonomousMissileAction(
            launch.Salvo,
            launch.AutonomousGuidanceResult,
            DiagnosticEventType.MissileLaunchResolved,
            "Player launch");
        RefreshAndLogDatalinkStateAfterMovement(launch.Salvo);
        LogTrackUpdates(_trackState.Refresh(
            TrackUpdateTrigger.MissileLaunched,
            _missileEngagement.Salvos,
            _turnState.TurnNumber));
        _playerLaunchedThisPhase = true;
        _selectedMissileSalvoId = launch.Salvo.Id;
        _resolutionCues = BuildResolutionCues(new[]
        {
            (launch.Salvo, launch.AdvanceResult),
        });
        _missileActionMessage = BuildMissileActionMessage(
            "Player launch",
            launch.Salvo,
            launch.AdvanceResult);
        ShowMissileOverlay();
        UpdateAllTextAndControls();
    }

    private void LaunchEnemyMissile()
    {
        if (_turnState.Phase != TacticalTurnPhase.MissileAndInterception ||
            _enemyLaunchedThisPhase ||
            !_enemyMissileRoute.CanLaunch)
        {
            return;
        }

        string salvoId = $"hostile-{_nextHostileSalvoNumber++}";
        GuidedMissileAutonomousLaunchResult launch =
            MissileLaunchService.LaunchAndAdvanceAutonomousOnePhase(
                _scenario.Map,
                salvoId,
                TacticalSide.Enemy,
                _scenario.EnemyShipId,
                _scenario.PlayerShipId,
                _scenario.EnemyPosition,
                _missileProfile,
                _missileDatalinkProfile,
                MissileTargetTrackSnapshot.FromTacticalTrack(
                    _scenario.PlayerShipId,
                    _trackState.GetTrackForSide(
                        TacticalSide.Enemy,
                        _scenario.PlayerShipId)),
                _trackState.GetGuidanceSourceObservationEpoch(
                    TacticalSide.Enemy,
                    _scenario.PlayerShipId),
                _missileSensorProfile,
                _scenario.PlayerPosition,
                _shipSignatureProfile,
                _trackState.PlayerSensorMode,
                _playerElectronicWarfare,
                _trackState.PlayerJammingEnabled,
                _sensorEnvironment,
                interceptionContext: GetOrCreateInterceptionContext(),
                terminalProfile: _missileTerminalProfile,
                terminalRandomSource: _terminalRandomSource);

        _missileEngagement.Add(launch.Salvo);
        RecordMissileDatalinkUpdate(
            launch.Salvo,
            launch.DatalinkUpdateResult);
        RecordAutonomousMissileAction(
            launch.Salvo,
            launch.AutonomousGuidanceResult,
            DiagnosticEventType.MissileLaunchResolved,
            "Enemy launch");
        RefreshAndLogDatalinkStateAfterMovement(launch.Salvo);
        bool launchObservedAtOrigin =
            _trackState.PlayerTrackOnEnemy is
            { Quality: TacticalTrackQuality.Firm, EstimatedCoordinate: HexCoord launcherCoordinate } &&
            launcherCoordinate == launch.Salvo.LaunchCoordinate;
        ObserveAndLogPlayerMissileAction(
            launch.Salvo,
            launch.AdvanceResult,
            TrackUpdateTrigger.MissileLaunched,
            launchObservedAtOrigin);
        LogTrackUpdates(_trackState.Refresh(
            TrackUpdateTrigger.MissileLaunched,
            _missileEngagement.Salvos,
            _turnState.TurnNumber));
        _enemyLaunchedThisPhase = true;
        _resolutionCues = BuildResolutionCues(new[]
        {
            (launch.Salvo, launch.AdvanceResult),
        });
        // Enemy launches never force-select authoritative salvo state. The
        // observer-safe view will expose the new contact only if the player
        // actually acquired it.
        _missileActionMessage = BuildMissileActionMessage(
            "Enemy launch",
            launch.Salvo,
            launch.AdvanceResult);
        ShowMissileOverlay();
        UpdateAllTextAndControls();
    }

    private void AdvanceActiveMissiles()
    {
        if (_turnState.Phase != TacticalTurnPhase.MissileAndInterception)
        {
            return;
        }

        GuidedMissileSalvo[] unresolved = _missileEngagement.ActiveSalvos
            .Where(salvo => !_salvosResolvedThisPhase.Contains(salvo.Id))
            .ToArray();

        if (unresolved.Length == 0)
        {
            _missileActionMessage =
                "No unresolved salvos remain in this missile phase.";
            _immediateFeedbackLabel.Text = _missileActionMessage;
            UpdateAllTextAndControls();
            return;
        }

        var advances = new List<(
            GuidedMissileSalvo Salvo,
            GuidedMissileAdvanceResult Result)>();
        Exception? resolutionFailure = null;

        try
        {
            MissileInterceptionPhaseContext context =
                GetOrCreateInterceptionContext();

            foreach (GuidedMissileSalvo salvo in unresolved)
            {
                MissileDatalinkUpdateResult datalinkUpdate =
                    MissileDatalinkService.UpdateForGuidancePhase(
                        _scenario.Map,
                        salvo,
                        _missileDatalinkProfile,
                        GetLauncherCoordinate(salvo),
                        _trackState.CreateGuidanceSnapshot(salvo),
                        _trackState.GetGuidanceSourceObservationEpoch(salvo));
                RecordMissileDatalinkUpdate(salvo, datalinkUpdate);

                MissileAutonomousGuidanceResult autonomous =
                    AdvanceAutonomousGuidance(
                        salvo,
                        datalinkUpdate,
                        context);
                GuidedMissileAdvanceResult result = autonomous.AdvanceResult;
                RecordAutonomousMissileAction(
                    salvo,
                    autonomous,
                    DiagnosticEventType.MissileGuidanceResolved,
                    "Guidance");
                RefreshAndLogDatalinkStateAfterMovement(salvo);
                if (salvo.OwnerSide == TacticalSide.Enemy)
                {
                    ObserveAndLogPlayerMissileAction(
                        salvo,
                        result,
                        TrackUpdateTrigger.MissileMovementCompleted,
                        launchObservedAtOrigin: false);
                }
                advances.Add((salvo, result));
            }
        }
        catch (Exception exception)
        {
            resolutionFailure = exception;
            GD.PushError($"Missile batch resolution failed: {exception}");
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileBatchFinalizationFailed,
                $"Missile batch resolution raised {exception.GetType().Name}: {exception.Message}",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                data: DiagnosticData(
                    ("failureStage", "AuthoritativeResolution"),
                    ("exceptionType", exception.GetType().FullName ?? exception.GetType().Name),
                    ("message", exception.Message)));
        }
        finally
        {
            FinalizeMissileBatch(advances, resolutionFailure);
        }
    }

    private void FinalizeMissileBatch(
        IReadOnlyList<(
            GuidedMissileSalvo Salvo,
            GuidedMissileAdvanceResult Result)> advances,
        Exception? resolutionFailure)
    {
        ObserverSafeMissileViewSnapshot? view = null;
        Exception? finalizationFailure = null;

        try
        {
            LogTrackUpdates(_trackState.Refresh(
                TrackUpdateTrigger.MissileMovementCompleted,
                _missileEngagement.Salvos,
                _turnState.TurnNumber));

            view = _trackState.BuildPlayerMissileView(
                _missileEngagement,
                _selectedMissileSalvoId);
            _selectedMissileSalvoId = view.SelectedSalvoId;
            TacticalMissileContact? selectedContact = view.Contacts.FirstOrDefault(
                contact => string.Equals(
                    contact.SalvoId,
                    view.SelectedSalvoId,
                    StringComparison.Ordinal));
            _board.SetInspectedCoordinate(selectedContact?.Coordinate);
            _resolutionCues = BuildResolutionCues(advances);
            _missileActionMessage = resolutionFailure is null
                ? BuildObserverSafeBatchSummary(advances, view)
                : "MISSILE PHASE RESULT — resolution stopped after an internal error; " +
                  "the observer-safe view was still finalized. See the automatic journal.";
            _immediateFeedbackLabel.Text =
                BuildPersistentMissilePhaseFeedback(_missileActionMessage);

            int launchesResolved = _launchesResolvedThisPhase.Count;
            int existingSalvosAdvanced = advances.Count;
            int totalMissileActionsResolved = checked(
                launchesResolved + existingSalvosAdvanced);
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileBatchResolved,
                $"Missile batch advanced {existingSalvosAdvanced} existing salvos; {launchesResolved} launches were resolved separately earlier in this phase.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                data: DiagnosticData(
                    ("salvosResolved", totalMissileActionsResolved.ToString()),
                    ("launchesResolved", launchesResolved.ToString()),
                    ("existingSalvosAdvanced", existingSalvosAdvanced.ToString()),
                    ("totalMissileActionsResolved", totalMissileActionsResolved.ToString()),
                    ("playerVisibleContacts", view.Contacts.Count.ToString()),
                    ("playerHits", advances.Count(item =>
                        item.Salvo.OwnerSide == TacticalSide.Enemy &&
                        IsTerminalHit(item.Result)).ToString()),
                    ("enemyHits", advances.Count(item =>
                        item.Salvo.OwnerSide == TacticalSide.Player &&
                        IsTerminalHit(item.Result)).ToString()),
                    ("terminalMisses", advances.Count(item =>
                        GetTerminalOutcome(item.Result) == MissileTerminalOutcome.Miss).ToString()),
                    ("terminalDuds", advances.Count(item =>
                        GetTerminalOutcome(item.Result) == MissileTerminalOutcome.Dud).ToString()),
                    ("resolutionFailure", resolutionFailure?.GetType().Name ?? "none")));
            _diagnosticLog?.Record(
                DiagnosticEventType.TacticalViewRefreshed,
                "Observer-safe missile markers, stacks, routes, selection, and impact cues refreshed after batch resolution.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                data: DiagnosticData(
                    ("visibleContactIds", string.Join(",", view.Contacts.Select(contact => contact.SalvoId))),
                    ("selectedSalvoId", view.SelectedSalvoId ?? "none"),
                    ("resolutionCueCount", _resolutionCues.Count.ToString())));
        }
        catch (Exception exception)
        {
            finalizationFailure = exception;
            GD.PushError($"Missile batch finalization failed: {exception}");
            _selectedMissileSalvoId = null;
            _board.SetInspectedCoordinate(null);
            _resolutionCues = BuildResolutionCues(advances);
            _missileActionMessage =
                "MISSILE PHASE RESULT — authoritative movement resolved, but tactical-view finalization failed. See the automatic journal.";
            _immediateFeedbackLabel.Text =
                BuildPersistentMissilePhaseFeedback(_missileActionMessage);
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileBatchFinalizationFailed,
                $"Mandatory missile-batch finalization raised {exception.GetType().Name}: {exception.Message}",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                data: DiagnosticData(
                    ("failureStage", "ObserverViewFinalization"),
                    ("exceptionType", exception.GetType().FullName ?? exception.GetType().Name),
                    ("message", exception.Message),
                    ("salvosResolved", advances.Count.ToString())));
        }
        finally
        {
            try
            {
                ShowMissileOverlay();
                UpdateAllTextAndControls();
            }
            catch (Exception presentationException)
            {
                GD.PushError($"Final missile presentation refresh failed: {presentationException}");
                _diagnosticLog?.Record(
                    DiagnosticEventType.MissileBatchFinalizationFailed,
                    $"Final redraw raised {presentationException.GetType().Name}: {presentationException.Message}",
                    turnNumber: _turnState.TurnNumber,
                    phase: _turnState.Phase,
                    data: DiagnosticData(
                        ("failureStage", "GodotRedraw"),
                        ("priorFinalizationFailure", finalizationFailure?.GetType().Name ?? "none"),
                        ("exceptionType", presentationException.GetType().FullName ?? presentationException.GetType().Name),
                        ("message", presentationException.Message)));
            }
        }
    }

    private static MissileTerminalOutcome GetTerminalOutcome(
        GuidedMissileAdvanceResult result) =>
        result.TerminalResolution?.Outcome ?? MissileTerminalOutcome.None;

    private static bool IsTerminalHit(
        GuidedMissileAdvanceResult result) =>
        GetTerminalOutcome(result) is
            MissileTerminalOutcome.Hit or
            MissileTerminalOutcome.CriticalHit;

    private IReadOnlyList<TacticalResolutionCue> BuildResolutionCues(
        IReadOnlyList<(GuidedMissileSalvo Salvo, GuidedMissileAdvanceResult Result)>
            advances)
    {
        var cues = new List<TacticalResolutionCue>();
        int playerHits = advances.Count(item =>
            item.Salvo.OwnerSide == TacticalSide.Enemy &&
            IsTerminalHit(item.Result));
        int enemyHits = advances.Count(item =>
            item.Salvo.OwnerSide == TacticalSide.Player &&
            IsTerminalHit(item.Result));
        int playerCriticals = advances.Count(item =>
            item.Salvo.OwnerSide == TacticalSide.Enemy &&
            GetTerminalOutcome(item.Result) == MissileTerminalOutcome.CriticalHit);
        int enemyCriticals = advances.Count(item =>
            item.Salvo.OwnerSide == TacticalSide.Player &&
            GetTerminalOutcome(item.Result) == MissileTerminalOutcome.CriticalHit);

        if (playerHits > 0)
        {
            string label = playerCriticals > 0
                ? playerHits == 1 ? "CRITICAL IMPACT" : $"IMPACT x{playerHits} ({playerCriticals} critical)"
                : playerHits == 1 ? "IMPACT" : $"IMPACT x{playerHits}";
            cues.Add(new TacticalResolutionCue(
                _scenario.PlayerPosition,
                TacticalSide.Enemy,
                label));
        }

        if (enemyHits > 0)
        {
            string label = enemyCriticals > 0
                ? enemyHits == 1 ? "CRITICAL IMPACT" : $"IMPACT x{enemyHits} ({enemyCriticals} critical)"
                : enemyHits == 1 ? "IMPACT" : $"IMPACT x{enemyHits}";
            cues.Add(new TacticalResolutionCue(
                _scenario.EnemyPosition,
                TacticalSide.Player,
                label));
        }

        foreach ((GuidedMissileSalvo salvo, GuidedMissileAdvanceResult result) in advances)
        {
            string? label = result.Status switch
            {
                GuidedMissileStatus.Intercepted => "INTERCEPTED",
                GuidedMissileStatus.Dud => "DUD",
                GuidedMissileStatus.SelfDestructed => "SELF-DESTRUCTED",
                GuidedMissileStatus.Searching => "SEARCHING",
                GuidedMissileStatus.Expended
                    when GetTerminalOutcome(result) == MissileTerminalOutcome.Miss =>
                    "MISS",
                _ => null,
            };
            if (label is null)
            {
                continue;
            }

            bool observable =
                salvo.OwnerSide == TacticalSide.Player ||
                result.EndingCoordinate == _scenario.PlayerPosition ||
                result.EndingCoordinate == _scenario.EnemyPosition;
            if (observable)
            {
                cues.Add(new TacticalResolutionCue(
                    result.EndingCoordinate,
                    salvo.OwnerSide,
                    label));
            }
        }

        return Array.AsReadOnly(cues.ToArray());
    }

    private string BuildObserverSafeBatchSummary(
        IReadOnlyList<(GuidedMissileSalvo Salvo, GuidedMissileAdvanceResult Result)>
            advances,
        ObserverSafeMissileViewSnapshot view)
    {
        int playerHits = advances.Count(item =>
            item.Salvo.OwnerSide == TacticalSide.Enemy &&
            IsTerminalHit(item.Result));
        int enemyHits = advances.Count(item =>
            item.Salvo.OwnerSide == TacticalSide.Player &&
            IsTerminalHit(item.Result));
        int misses = advances.Count(item =>
            GetTerminalOutcome(item.Result) == MissileTerminalOutcome.Miss);
        int duds = advances.Count(item =>
            GetTerminalOutcome(item.Result) == MissileTerminalOutcome.Dud);
        int interceptions = advances.Count(item =>
            item.Result.Status == GuidedMissileStatus.Intercepted);
        int selfDestructions = advances.Count(item =>
            item.Result.Status == GuidedMissileStatus.SelfDestructed);
        int searchingVisible = view.Contacts.Count(contact =>
            contact.Status == GuidedMissileStatus.Searching);
        int waitingVisible = view.Contacts.Count(contact =>
            contact.Status is GuidedMissileStatus.WaitingForTrack or
                GuidedMissileStatus.WaitingForRoute);
        int visibleActive = view.Contacts.Count(contact => !contact.IsTerminal);

        var parts = new List<string>();
        if (playerHits > 0)
        {
            parts.Add($"{playerHits} hostile missile{(playerHits == 1 ? string.Empty : "s")} hit the player ship");
        }
        if (enemyHits > 0)
        {
            parts.Add($"{enemyHits} friendly missile{(enemyHits == 1 ? string.Empty : "s")} hit the enemy ship");
        }
        if (misses > 0)
        {
            parts.Add($"{misses} terminal attack{(misses == 1 ? string.Empty : "s")} missed");
        }
        if (duds > 0)
        {
            parts.Add($"{duds} dud{(duds == 1 ? string.Empty : "s")}");
        }
        if (interceptions > 0)
        {
            parts.Add($"{interceptions} missile{(interceptions == 1 ? string.Empty : "s")} intercepted");
        }
        if (selfDestructions > 0)
        {
            parts.Add($"{selfDestructions} missile{(selfDestructions == 1 ? string.Empty : "s")} self-destructed");
        }

        parts.Add($"{visibleActive} observer-visible active salvo{(visibleActive == 1 ? string.Empty : "s")} remain");
        if (searchingVisible > 0)
        {
            parts.Add($"{searchingVisible} visible salvo{(searchingVisible == 1 ? string.Empty : "s")} searching");
        }
        if (waitingVisible > 0)
        {
            parts.Add($"{waitingVisible} visible salvo{(waitingVisible == 1 ? string.Empty : "s")} waiting for track or route");
        }

        return "MISSILE PHASE RESULT - " + string.Join("; ", parts) + ".";
    }

    private void ObserveAndLogPlayerMissileAction(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result,
        TrackUpdateTrigger trigger,
        bool launchObservedAtOrigin)
    {
        MissileMovementObservationResult observation =
            _trackState.ObservePlayerMissileMovement(
                salvo,
                result,
                trigger,
                launchObservedAtOrigin);

        foreach (MissileMovementObservationStep step in observation.Steps)
        {
            if (step.Detected)
            {
                DiagnosticEventType contactType = step.SegmentStarted
                    ? DiagnosticEventType.MissileContactAcquired
                    : DiagnosticEventType.MissileContactMaintained;
                string detectionReason = step.IsLaunchOrigin
                    ? "the Firm-tracked launcher made the launch observable"
                    : "the missile was detected after entering this hex";
                _diagnosticLog?.Record(
                    contactType,
                    $"Player observed {salvo.Id} at {Format(step.Coordinate)} because {detectionReason}.",
                    turnNumber: _turnState.TurnNumber,
                    phase: _turnState.Phase,
                    actorId: _scenario.PlayerShipId,
                    targetId: salvo.Id,
                    coordinateAfter: step.Coordinate,
                    data: DiagnosticData(
                        ("isLaunchOrigin", step.IsLaunchOrigin.ToString()),
                        ("segmentStarted", step.SegmentStarted.ToString()),
                        ("segmentExtended", step.SegmentExtended.ToString()),
                        ("trackQuality", step.TrackQuality?.ToString() ?? "none")));

                _diagnosticLog?.Record(
                    step.SegmentStarted
                        ? DiagnosticEventType.ObservedTrailSegmentStarted
                        : DiagnosticEventType.ObservedTrailSegmentExtended,
                    step.SegmentStarted
                        ? $"Observed trail segment for {salvo.Id} started at {Format(step.Coordinate)}."
                        : $"Observed trail segment for {salvo.Id} extended through {Format(step.Coordinate)}.",
                    turnNumber: _turnState.TurnNumber,
                    phase: _turnState.Phase,
                    actorId: _scenario.PlayerShipId,
                    targetId: salvo.Id,
                    coordinateAfter: step.Coordinate);
            }
            else if (step.SegmentClosed)
            {
                _diagnosticLog?.Record(
                    DiagnosticEventType.MissileContactLost,
                    $"Player lost continuous observation of {salvo.Id} before or at {Format(step.Coordinate)}.",
                    turnNumber: _turnState.TurnNumber,
                    phase: _turnState.Phase,
                    actorId: _scenario.PlayerShipId,
                    targetId: salvo.Id,
                    coordinateAfter: step.Coordinate);
                _diagnosticLog?.Record(
                    DiagnosticEventType.ObservedTrailSegmentClosed,
                    $"Observed trail segment for {salvo.Id} closed; later reacquisition must start a disconnected segment.",
                    turnNumber: _turnState.TurnNumber,
                    phase: _turnState.Phase,
                    actorId: _scenario.PlayerShipId,
                    targetId: salvo.Id);
            }
        }
    }

    private MissileAutonomousGuidanceResult AdvanceAutonomousGuidance(
        GuidedMissileSalvo salvo,
        MissileDatalinkUpdateResult datalinkUpdate,
        MissileInterceptionPhaseContext context)
    {
        HexCoord targetCoordinate = GetTargetCoordinate(salvo);
        bool targetIsPlayer = string.Equals(
            salvo.TargetId,
            _scenario.PlayerShipId,
            StringComparison.Ordinal);
        return MissileAutonomousGuidanceService.AdvanceOnePhase(
            _scenario.Map,
            salvo,
            datalinkUpdate,
            _missileSensorProfile,
            targetCoordinate,
            _shipSignatureProfile,
            targetIsPlayer
                ? _trackState.PlayerSensorMode
                : _trackState.EnemySensorMode,
            targetIsPlayer
                ? _playerElectronicWarfare
                : _enemyElectronicWarfare,
            targetIsPlayer
                ? _trackState.PlayerJammingEnabled
                : _trackState.EnemyJammingEnabled,
            _sensorEnvironment,
            _trackState.ObservationEpoch,
            context,
            _terminalRandomSource);
    }

    private HexCoord GetTargetCoordinate(GuidedMissileSalvo salvo)
    {
        if (string.Equals(
                salvo.TargetId,
                _scenario.PlayerShipId,
                StringComparison.Ordinal))
        {
            return _scenario.PlayerPosition;
        }

        if (string.Equals(
                salvo.TargetId,
                _scenario.EnemyShipId,
                StringComparison.Ordinal))
        {
            return _scenario.EnemyPosition;
        }

        return salvo.LastKnownTargetCoordinate ?? salvo.CurrentCoordinate;
    }

    private void RefreshLocalSensorsAfterTargetMovement() =>
        RefreshLocalSensorsForAllActive(
            MissileGuidanceObservationOpportunity.TargetMovement);

    private void RefreshLocalSensorsForAllActive(
        MissileGuidanceObservationOpportunity opportunity)
    {
        foreach (GuidedMissileSalvo salvo in _missileEngagement.ActiveSalvos)
        {
            bool targetIsPlayer = string.Equals(
                salvo.TargetId,
                _scenario.PlayerShipId,
                StringComparison.Ordinal);
            MissileLocalSensorObservationResult observation =
                MissileAutonomousGuidanceService.ObserveAfterTargetMovement(
                    _scenario.Map,
                    salvo,
                    _missileSensorProfile,
                    GetTargetCoordinate(salvo),
                    _shipSignatureProfile,
                    targetIsPlayer
                        ? _trackState.PlayerSensorMode
                        : _trackState.EnemySensorMode,
                    targetIsPlayer
                        ? _playerElectronicWarfare
                        : _enemyElectronicWarfare,
                    targetIsPlayer
                        ? _trackState.PlayerJammingEnabled
                        : _trackState.EnemyJammingEnabled,
                    _sensorEnvironment,
                    _trackState.ObservationEpoch);
            RecordLocalSensorObservation(
                salvo,
                salvo.CurrentCoordinate,
                opportunity,
                observation);
        }
    }

    private void RecordAutonomousMissileAction(
        GuidedMissileSalvo salvo,
        MissileAutonomousGuidanceResult autonomous,
        DiagnosticEventType completionEventType,
        string actionName)
    {
        _lastAutonomousGuidanceBySalvo[salvo.Id] = autonomous;
        GuidedMissileAdvanceResult result = autonomous.AdvanceResult;
        _lastAdvanceBySalvo[salvo.Id] = result;
        _salvosResolvedThisPhase.Add(salvo.Id);
        if (completionEventType == DiagnosticEventType.MissileLaunchResolved)
        {
            _launchesResolvedThisPhase.Add(salvo.Id);
        }

        MissileAutonomousGuidanceStep? actionStart = autonomous.Steps
            .FirstOrDefault(step =>
                step.Opportunity ==
                MissileGuidanceObservationOpportunity.ActionStart);
        if (actionStart is not null)
        {
            RecordAutonomousGuidanceStep(salvo, actionStart);
        }

        RecordMissileGuidanceStarted(
            salvo,
            result,
            autonomous.InitialDecision,
            actionStart?.RoutePlan,
            actionName);

        var remainingAttempts = result.InterceptionAttempts.ToList();
        HexCoord priorCoordinate = result.StartingCoordinate;
        foreach (MissileAutonomousGuidanceStep step in autonomous.Steps
                     .Where(item => item.Opportunity ==
                         MissileGuidanceObservationOpportunity.AfterEnteredHex)
                     .OrderBy(item => item.MovementSpentThisAction))
        {
            RecordMissileMovementEdge(
                salvo,
                result,
                priorCoordinate,
                step);
            RecordAutonomousGuidanceStep(salvo, step);

            MissileInterceptionAttemptResult[] edgeAttempts =
                remainingAttempts
                    .Where(attempt =>
                        attempt.MissileCoordinate == step.MissileCoordinate)
                    .ToArray();
            LogInterceptionAttempts(edgeAttempts);
            foreach (MissileInterceptionAttemptResult attempt in edgeAttempts)
            {
                remainingAttempts.Remove(attempt);
            }

            priorCoordinate = step.MissileCoordinate;
        }

        // Stationary final-approach or wait-state attempts have no entered edge.
        LogInterceptionAttempts(remainingAttempts);
        RecordMissileTerminalResolution(salvo, result);
        RecordMissileMovementSummary(salvo, result);
        RecordMissileGuidanceCompletion(
            salvo,
            result,
            autonomous.FinalDecision,
            completionEventType,
            actionName);
    }

    private void RecordMissileTerminalResolution(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result)
    {
        MissileTerminalResolution? terminal = result.TerminalResolution;
        if (!salvo.HasTerminalOpportunity && terminal is null)
        {
            return;
        }

        HexCoord coordinate = salvo.TerminalOpportunityCoordinate ??
            result.EndingCoordinate;
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileTerminalOpportunity,
            $"{salvo.Id} entered or retained a terminal opportunity at {Format(coordinate)}.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateAfter: coordinate,
            data: DiagnosticData(
                ("terminalState", salvo.TerminalState.ToString()),
                ("entryDefenseResolved", salvo.TerminalEntryDefenseResolved.ToString()),
                ("reportSource", terminal?.ReportSource.ToString() ?? salvo.LastGuidanceSource.ToString()),
                ("reportQuality", terminal?.ReportQuality.ToString() ?? salvo.LastTrackQuality?.ToString() ?? "none"),
                ("targetCoLocated", terminal?.TargetCoLocated.ToString() ?? "unknown")));

        if (result.StationarySearchFuelSpentThisPhase > 0 ||
            result.Status == GuidedMissileStatus.Searching)
        {
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileSearchActivated,
                $"{salvo.Id} resolved a terminal search activation at {Format(coordinate)}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: salvo.Id,
                targetId: salvo.TargetId,
                coordinateAfter: coordinate,
                data: DiagnosticData(
                    ("searchFuelSpentThisPhase", result.StationarySearchFuelSpentThisPhase.ToString()),
                    ("searchFuelSpentTotal", salvo.StationarySearchFuelSpent.ToString()),
                    ("remainingRange", salvo.RemainingRange.ToString()),
                    ("status", result.Status.ToString())));
        }

        if (terminal is null)
        {
            return;
        }

        _diagnosticLog?.Record(
            DiagnosticEventType.MissileTerminalAcquisitionResolved,
            $"{salvo.Id} terminal acquisition: " +
            (terminal.HasFirmSolution ? "Firm solution acquired." : "no Firm solution."),
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateAfter: coordinate,
            data: DiagnosticData(
                ("reportSource", terminal.ReportSource.ToString()),
                ("reportQuality", terminal.ReportQuality.ToString()),
                ("targetCoLocated", terminal.TargetCoLocated.ToString()),
                ("usedSeekerAcquisition", terminal.UsedSeekerAcquisition.ToString()),
                ("acquisitionRoll", terminal.AcquisitionRoll?.ToString() ?? "none"),
                ("acquisitionChancePercent", terminal.AcquisitionChancePercent?.ToString() ?? "none"),
                ("hasFirmSolution", terminal.HasFirmSolution.ToString()),
                ("reason", terminal.Reason)));

        if (terminal.AttackWasResolved)
        {
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileTerminalAttackResolved,
                $"{salvo.Id} terminal attack resolved as {terminal.Outcome}.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: salvo.Id,
                targetId: salvo.TargetId,
                coordinateAfter: coordinate,
                data: DiagnosticData(
                    ("attackRoll", terminal.AttackRoll?.ToString() ?? "none"),
                    ("effectiveHitChancePercent", terminal.EffectiveHitChancePercent?.ToString() ?? "none"),
                    ("seekerAccuracyApplied", terminal.SeekerAccuracyApplied.ToString()),
                    ("outcome", terminal.Outcome.ToString()),
                    ("critical", terminal.IsCriticalHit.ToString()),
                    ("reason", terminal.Reason)));
        }

        if (terminal.Outcome == MissileTerminalOutcome.SelfDestructed)
        {
            _diagnosticLog?.Record(
                DiagnosticEventType.MissileSelfDestructed,
                $"{salvo.Id} self-destructed safely after terminal search fuel was exhausted.",
                turnNumber: _turnState.TurnNumber,
                phase: _turnState.Phase,
                actorId: salvo.Id,
                targetId: salvo.TargetId,
                coordinateAfter: coordinate,
                data: DiagnosticData(
                    ("totalFuelSpent", salvo.TotalFuelSpent.ToString()),
                    ("maximumRange", salvo.Profile.MaximumRange.ToString()),
                    ("reason", terminal.Reason)));
        }
    }

    private void RecordAutonomousGuidanceStep(
        GuidedMissileSalvo salvo,
        MissileAutonomousGuidanceStep step)
    {
        RecordLocalSensorObservation(
            salvo,
            step.MissileCoordinate,
            step.Opportunity,
            step.LocalObservation);

        string candidates = string.Join(
            ",",
            step.Decision.Candidates.Select(candidate =>
                $"{candidate.Source}:{candidate.Snapshot.Quality}:" +
                $"{(candidate.Snapshot.GuidanceCoordinate.HasValue ? Format(candidate.Snapshot.GuidanceCoordinate.Value) : "none")}:" +
                $"epoch{candidate.SourceObservationEpoch}:u{candidate.UncertaintyRadiusHexes}"));
        string selectedCoordinate =
            step.Decision.SelectedSnapshot.GuidanceCoordinate.HasValue
                ? Format(step.Decision.SelectedSnapshot.GuidanceCoordinate.Value)
                : "none";
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileGuidanceArbitrated,
            $"{salvo.Id} selected {step.Decision.SelectedSource} guidance at {step.Opportunity}: {step.Decision.Reason}",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateAfter: step.MissileCoordinate,
            data: DiagnosticData(
                ("opportunity", step.Opportunity.ToString()),
                ("selectedSource", step.Decision.SelectedSource.ToString()),
                ("selectedQuality", step.Decision.SelectedSnapshot.Quality.ToString()),
                ("selectedCoordinate", selectedCoordinate),
                ("candidateCount", step.Decision.Candidates.Count.ToString()),
                ("candidates", string.IsNullOrEmpty(candidates) ? "none" : candidates),
                ("guidanceChanged", step.GuidanceChanged.ToString()),
                ("reason", step.Decision.Reason)));

        if (!step.GuidanceChanged)
        {
            return;
        }

        string route = step.RoutePlan is { HasRoute: true }
            ? FormatPath(step.RoutePlan.Path)
            : "none";
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileGuidanceReplanned,
            $"{salvo.Id} immediately replanned after {step.Opportunity}; movement already spent was not refunded.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateAfter: step.MissileCoordinate,
            data: DiagnosticData(
                ("selectedSource", step.Decision.SelectedSource.ToString()),
                ("selectedCoordinate", selectedCoordinate),
                ("remainingMovementThisAction",
                    Math.Max(
                        0,
                        salvo.Profile.SpeedHexesPerTurn -
                        step.MovementSpentThisAction)
                    .ToString()),
                ("replannedRoute", route),
                ("movementRefunded", "False")));
    }

    private void RecordMissileMovementEdge(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result,
        HexCoord priorCoordinate,
        MissileAutonomousGuidanceStep step)
    {
        int distanceBeforeAction =
            salvo.DistanceTraveled - result.DistanceTraveledThisPhase;
        int distanceAfterEdge =
            distanceBeforeAction + step.MovementSpentThisAction;
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileMovementEdgeResolved,
            $"{salvo.Id} entered {Format(step.MissileCoordinate)} on movement edge {step.MovementSpentThisAction}.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateBefore: priorCoordinate,
            coordinateAfter: step.MissileCoordinate,
            data: DiagnosticData(
                ("edgeNumber", step.MovementSpentThisAction.ToString()),
                ("movementSpentThisAction", step.MovementSpentThisAction.ToString()),
                ("remainingMovementThisAction",
                    Math.Max(
                        0,
                        salvo.Profile.SpeedHexesPerTurn -
                        step.MovementSpentThisAction)
                    .ToString()),
                ("distanceTraveled", distanceAfterEdge.ToString()),
                ("remainingRange",
                    Math.Max(
                        0,
                        salvo.Profile.MaximumRange - distanceAfterEdge)
                    .ToString())));
    }

    private void RecordMissileGuidanceStarted(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result,
        MissileGuidanceDecision initialDecision,
        MissileRouteResult? initialRoute,
        string actionName)
    {
        string guidanceCoordinate =
            initialDecision.SelectedSnapshot.GuidanceCoordinate.HasValue
                ? Format(initialDecision.SelectedSnapshot.GuidanceCoordinate.Value)
                : "none";
        string routeStatus = initialRoute?.Status.ToString() ?? "none";
        string routePath = initialRoute is { HasRoute: true }
            ? FormatPath(initialRoute.Path)
            : "none";
        string guidanceStartLabel = string.Equals(
            actionName,
            "Guidance",
            StringComparison.Ordinal)
            ? "Guidance"
            : $"{actionName} guidance";
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileGuidanceStarted,
            $"{guidanceStartLabel} started for {salvo.Id} toward {guidanceCoordinate} using {initialDecision.SelectedSnapshot.Quality} {initialDecision.SelectedSource} data.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateBefore: result.StartingCoordinate,
            data: DiagnosticData(
                ("ownerSide", salvo.OwnerSide.ToString()),
                ("launcherId", salvo.LauncherId),
                ("targetTrackQuality", initialDecision.SelectedSnapshot.Quality.ToString()),
                ("guidanceSource", initialDecision.SelectedSource.ToString()),
                ("datalinkState", salvo.DatalinkState.ToString()),
                ("retainedReportAgePhases",
                    salvo.RetainedDatalinkReport?.AgePhases.ToString() ?? "none"),
                ("guidanceCoordinate", guidanceCoordinate),
                ("routeStatus", routeStatus),
                ("plannedRoute", routePath)));
    }

    private void RecordMissileMovementSummary(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result)
    {
        string movementPath = result.EnteredCoordinates.Count > 0
            ? FormatPath(result.EnteredCoordinates)
            : "none";
        string movementOutcome = GetMovementOutcome(salvo, result);
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileMoved,
            $"{salvo.Id} moved {FormatHexCount(result.DistanceTraveledThisPhase)} during this missile action.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateBefore: result.StartingCoordinate,
            coordinateAfter: result.EndingCoordinate,
            data: DiagnosticData(
                ("movementOutcome", movementOutcome),
                ("actualMovementPath", movementPath),
                ("movedThisPhase", result.DistanceTraveledThisPhase.ToString()),
                ("stationarySearchFuelSpentThisPhase", result.StationarySearchFuelSpentThisPhase.ToString()),
                ("distanceTraveled", salvo.DistanceTraveled.ToString()),
                ("stationarySearchFuelSpent", salvo.StationarySearchFuelSpent.ToString()),
                ("totalFuelSpent", salvo.TotalFuelSpent.ToString()),
                ("remainingRange", salvo.RemainingRange.ToString())));
    }

    private void RecordMissileGuidanceCompletion(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result,
        MissileGuidanceDecision finalDecision,
        DiagnosticEventType completionEventType,
        string actionName)
    {
        string routeStatus = result.RoutePlan?.Status.ToString() ?? "none";
        string routePath = result.RoutePlan is { HasRoute: true }
            ? FormatPath(result.RoutePlan.Path)
            : "none";
        string movementPath = result.EnteredCoordinates.Count > 0
            ? FormatPath(result.EnteredCoordinates)
            : "none";
        string guidanceCoordinate =
            finalDecision.SelectedSnapshot.GuidanceCoordinate.HasValue
                ? Format(finalDecision.SelectedSnapshot.GuidanceCoordinate.Value)
                : "none";
        string movementOutcome = GetMovementOutcome(salvo, result);
        string waitReason = GetMissileWaitReason(result, finalDecision);
        DiagnosticEventType completionType =
            completionEventType == DiagnosticEventType.MissileLaunchResolved
                ? DiagnosticEventType.MissileLaunchResolved
                : DiagnosticEventType.MissileGuidanceCompleted;
        _diagnosticLog?.Record(
            completionType,
            $"{actionName} completed for {salvo.Id}: final status {result.Status}.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateBefore: result.StartingCoordinate,
            coordinateAfter: result.EndingCoordinate,
            data: DiagnosticData(
                ("ownerSide", salvo.OwnerSide.ToString()),
                ("launcherId", salvo.LauncherId),
                ("finalStatus", result.Status.ToString()),
                ("targetTrackQuality", finalDecision.SelectedSnapshot.Quality.ToString()),
                ("guidanceSource", finalDecision.SelectedSource.ToString()),
                ("datalinkState", salvo.DatalinkState.ToString()),
                ("retainedReportAgePhases",
                    salvo.RetainedDatalinkReport?.AgePhases.ToString() ?? "none"),
                ("guidanceCoordinate", guidanceCoordinate),
                ("routeStatus", routeStatus),
                ("plannedRoute", routePath),
                ("actualMovementPath", movementPath),
                ("movementOutcome", movementOutcome),
                ("waitReason", waitReason),
                ("movedThisPhase", result.DistanceTraveledThisPhase.ToString()),
                ("stationarySearchFuelSpentThisPhase", result.StationarySearchFuelSpentThisPhase.ToString()),
                ("distanceTraveled", salvo.DistanceTraveled.ToString()),
                ("stationarySearchFuelSpent", salvo.StationarySearchFuelSpent.ToString()),
                ("totalFuelSpent", salvo.TotalFuelSpent.ToString()),
                ("maximumRange", salvo.Profile.MaximumRange.ToString()),
                ("remainingRange", salvo.RemainingRange.ToString()),
                ("interceptionAttempts", result.InterceptionAttempts.Count.ToString())));

        string completionFeedback =
            $"{salvo.Id}: {movementOutcome}; moved {result.DistanceTraveledThisPhase}; " +
            $"search fuel {result.StationarySearchFuelSpentThisPhase}; status {result.Status}; " +
            $"remaining range {salvo.RemainingRange}.";
        _immediateFeedbackLabel.Text =
            BuildPersistentMissilePhaseFeedback(completionFeedback);

        if (_heldDirectFireOrderArmed &&
            _interceptionContext is not null &&
            _interceptionContext.AttemptsUsed("held-main-weapon-player") > 0)
        {
            _heldDirectFireOrderArmed = false;
        }
    }

    private static string GetMovementOutcome(
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result) =>
        result.DistanceTraveledThisPhase == 0
            ? result.Status switch
            {
                GuidedMissileStatus.WaitingForTrack => "HeldForTrack",
                GuidedMissileStatus.WaitingForRoute => "HeldForRoute",
                GuidedMissileStatus.Searching =>
                    result.StationarySearchFuelSpentThisPhase > 0
                        ? "StationarySearch"
                        : "EnteredSearchWait",
                GuidedMissileStatus.Expended or
                GuidedMissileStatus.Dud => "TerminalAttackResolved",
                GuidedMissileStatus.SelfDestructed => "SearchSelfDestruct",
                _ => "Stationary",
            }
            : result.Status switch
            {
                GuidedMissileStatus.Searching => "EnteredSearchWait",
                GuidedMissileStatus.Expended or
                GuidedMissileStatus.Dud => "AdvancedAndResolvedTerminalAttack",
                GuidedMissileStatus.Intercepted => "AdvancedAndIntercepted",
                _ when result.Status == GuidedMissileStatus.WaitingForTrack =>
                    salvo.LastTrackQuality switch
                    {
                        MissileTargetTrackQuality.Approximate =>
                            "MovedToApproximateCoordinate",
                        MissileTargetTrackQuality.Stale =>
                            "MovedToLastKnownCoordinate",
                        _ => "MovedToGuidanceCoordinate",
                    },
                _ => "Advanced",
            };

    private static string GetMissileWaitReason(
        GuidedMissileAdvanceResult result,
        MissileGuidanceDecision finalDecision)
    {
        if (result.Status == GuidedMissileStatus.Searching)
        {
            return result.TerminalResolution?.Reason ??
                "The Missile Flight is co-located with its candidate hex but lacks a Current/Firm terminal solution.";
        }

        MissileTargetTrackQuality quality =
            finalDecision.SelectedSnapshot.Quality;
        return result.Status switch
        {
            GuidedMissileStatus.WaitingForTrack
                when result.DistanceTraveledThisPhase > 0 &&
                     quality == MissileTargetTrackQuality.Approximate =>
                "Reached the Approximate guidance coordinate without a Current/Firm terminal solution.",
            GuidedMissileStatus.WaitingForTrack
                when result.DistanceTraveledThisPhase > 0 &&
                     quality == MissileTargetTrackQuality.Stale =>
                "Reached the Stale last-known coordinate without reacquisition.",
            GuidedMissileStatus.WaitingForTrack
                when result.DistanceTraveledThisPhase > 0 =>
                "Reached the available guidance coordinate without terminal resolution.",
            GuidedMissileStatus.WaitingForTrack
                when result.GuidanceCoordinate.HasValue &&
                     result.GuidanceCoordinate.Value ==
                     result.StartingCoordinate =>
                "Already at the selected guidance coordinate; waiting for a fresh report or missile-local reacquisition.",
            GuidedMissileStatus.WaitingForTrack =>
                "No usable target coordinate was available.",
            GuidedMissileStatus.WaitingForRoute =>
                "No legal route currently exists.",
            _ => "none",
        };
    }

    private void RecordLocalSensorObservation(
        GuidedMissileSalvo salvo,
        HexCoord missileCoordinate,
        MissileGuidanceObservationOpportunity opportunity,
        MissileLocalSensorObservationResult observation)
    {
        SensorContactEvaluationResult? evaluation =
            observation.FinalEvaluation;
        MissileLocalTrackReport? report = observation.TrackReport;
        string quality = report?.Quality.ToString() ??
            MissileTargetTrackQuality.Lost.ToString();
        string coordinate = report is null
            ? "none"
            : Format(report.GuidanceCoordinate);
        string status = evaluation?.Status.ToString() ?? "NotInstalled";
        _diagnosticLog?.Record(
            DiagnosticEventType.MissileLocalSensorUpdated,
            $"{salvo.Id} local sensor at {opportunity}: {status}; local track {quality} at {coordinate}.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateAfter: missileCoordinate,
            data: DiagnosticData(
                ("opportunity", opportunity.ToString()),
                ("missileCoordinate", Format(missileCoordinate)),
                ("sensorMode", observation.SensorMode.ToString()),
                ("activeEscalated", observation.ActiveEscalated.ToString()),
                ("evaluationStatus", status),
                ("localTrackQuality", quality),
                ("localTrackCoordinate", coordinate),
                ("localTrackUncertainty",
                    report?.UncertaintyRadiusHexes.ToString() ?? "none"),
                ("localTrackAgeEpochs",
                    report?.AgeEpochs.ToString() ?? "none"),
                ("sameEpochVisibilityLoss",
                    observation.SameEpochVisibilityLoss.ToString()),
                ("ageAdvanced", observation.AgeAdvanced.ToString())));
    }

    private HexCoord GetLauncherCoordinate(GuidedMissileSalvo salvo)
    {
        if (string.Equals(
                salvo.LauncherId,
                _scenario.PlayerShipId,
                StringComparison.Ordinal))
        {
            return _scenario.PlayerPosition;
        }

        if (string.Equals(
                salvo.LauncherId,
                _scenario.EnemyShipId,
                StringComparison.Ordinal))
        {
            return _scenario.EnemyPosition;
        }

        return salvo.LaunchCoordinate;
    }

    private void RefreshAndLogDatalinkStateAfterMovement(
        GuidedMissileSalvo salvo)
    {
        MissileDatalinkLinkEvaluation finalEvaluation =
            MissileDatalinkService.RefreshLinkState(
                _scenario.Map,
                salvo,
                _missileDatalinkProfile,
                GetLauncherCoordinate(salvo));
        MissileDatalinkReport? retained = salvo.RetainedDatalinkReport;
        MissileTargetTrackQuality effectiveQuality = retained is null
            ? MissileTargetTrackQuality.Lost
            : retained.GetEffectiveQuality(
                _missileDatalinkProfile.MaximumRetainedReportAgePhases);
        string lineOfSightQuality =
            finalEvaluation.LineOfSightQuality?.ToString() ??
            (finalEvaluation.State == MissileDatalinkState.Live
                ? "SameHexOrNotRequired"
                : "none");

        _diagnosticLog?.Record(
            DiagnosticEventType.MissileDatalinkUpdated,
            $"{salvo.Id} ended its missile action with datalink {finalEvaluation.State}; no additional report delivery or aging occurred after movement.",
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateBefore: finalEvaluation.LauncherCoordinate,
            coordinateAfter: finalEvaluation.MissileCoordinate,
            data: DiagnosticData(
                ("evaluationStage", "ActionEnd"),
                ("launcherId", salvo.LauncherId),
                ("datalinkState", finalEvaluation.State.ToString()),
                ("datalinkLineOfSight", lineOfSightQuality),
                ("reportDelivered", "False"),
                ("retainedReportAged", "False"),
                ("retainedReportAgePhases", retained?.AgePhases.ToString() ?? "none"),
                ("retainedReceivedQuality", retained?.ReceivedQuality.ToString() ?? "none"),
                ("retainedCoordinate", retained is null ? "none" : Format(retained.GuidanceCoordinate)),
                ("sourceObservationEpoch", retained?.SourceObservationEpoch.ToString() ?? "none"),
                ("effectiveGuidanceQuality", effectiveQuality.ToString())));
    }

    private void RecordMissileDatalinkUpdate(
        GuidedMissileSalvo salvo,
        MissileDatalinkUpdateResult update)
    {
        MissileDatalinkReport? retained = update.RetainedReport;
        string retainedCoordinate = retained is null
            ? "none"
            : Format(retained.GuidanceCoordinate);
        string effectiveQuality = update.GuidanceSnapshot.Quality.ToString();
        string guidanceCoordinate = update.GuidanceSnapshot.GuidanceCoordinate.HasValue
            ? Format(update.GuidanceSnapshot.GuidanceCoordinate.Value)
            : "none";
        string lineOfSightQuality =
            update.LinkEvaluation.LineOfSightQuality?.ToString() ??
            (update.State == MissileDatalinkState.Live
                ? "SameHexOrNotRequired"
                : "none");
        string message = update.ReportDelivered
            ? $"{salvo.LauncherId} delivered a fresh {update.LauncherTrackQuality} report to {salvo.Id} over a Live datalink."
            : update.GuidanceSource == MissileGuidanceReportSource.RetainedDatalink
                ? $"{salvo.Id} received no fresh report through its {update.State} datalink and retained an age-{retained!.AgePhases} {effectiveQuality} guidance copy."
                : update.RetainedReportExpired
                    ? $"{salvo.Id}'s retained datalink report expired after age {retained!.AgePhases}; no usable guidance coordinate remains."
                    : $"{salvo.Id} has no usable datalink report; link state is {update.State}.";

        _diagnosticLog?.Record(
            DiagnosticEventType.MissileDatalinkUpdated,
            message,
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: salvo.Id,
            targetId: salvo.TargetId,
            coordinateBefore: update.LinkEvaluation.LauncherCoordinate,
            coordinateAfter: update.LinkEvaluation.MissileCoordinate,
            data: DiagnosticData(
                ("evaluationStage", "ActionStart"),
                ("launcherId", salvo.LauncherId),
                ("datalinkState", update.State.ToString()),
                ("datalinkLineOfSight", lineOfSightQuality),
                ("guidancePhaseNumber", update.GuidancePhaseNumber.ToString()),
                ("launcherTrackQuality", update.LauncherTrackQuality.ToString()),
                ("reportDelivered", update.ReportDelivered.ToString()),
                ("retainedReportAged", update.RetainedReportAged.ToString()),
                ("retainedReportExpired", update.RetainedReportExpired.ToString()),
                ("retainedReportAgePhases", retained?.AgePhases.ToString() ?? "none"),
                ("retainedReceivedQuality", retained?.ReceivedQuality.ToString() ?? "none"),
                ("retainedCoordinate", retainedCoordinate),
                ("sourceObservationEpoch", retained?.SourceObservationEpoch.ToString() ?? "none"),
                ("guidanceSource", update.GuidanceSource.ToString()),
                ("effectiveGuidanceQuality", effectiveQuality),
                ("guidanceCoordinate", guidanceCoordinate)));
    }

    private MissileInterceptionPhaseContext GetOrCreateInterceptionContext()
    {
        if (_interceptionContext is not null)
        {
            return _interceptionContext;
        }

        var defenses = new List<MissileDefenseSystem>();

        if (_heldDirectFireOrderArmed &&
            _directFireOrder is { CreatesHeldInterception: true } heldOrder)
        {
            defenses.Add(heldOrder.CreateHeldDefenseSystem(
                "held-main-weapon-player",
                priority: 0));
        }

        defenses.Add(new MissileDefenseSystem(
            "point-defense-player",
            _scenario.PlayerShipId,
            TacticalSide.Player,
            _scenario.PlayerPosition,
            _pointDefenseProfile,
            priority: 10,
            sourceType: MissileDefenseSourceType.PointDefenseSystem));
        defenses.Add(new MissileDefenseSystem(
            "point-defense-enemy",
            _scenario.EnemyShipId,
            TacticalSide.Enemy,
            _scenario.EnemyPosition,
            _pointDefenseProfile,
            priority: 10,
            sourceType: MissileDefenseSourceType.PointDefenseSystem));

        _interceptionContext = new MissileInterceptionPhaseContext(
            defenses,
            CreateInterceptionResolver(),
            _scenario.Map,
            new DemoMissileDefenseTrackProvider(
                _scenario,
                _sensorProfile,
                () => _trackState.CreatePlayerMissileEvaluationContext()));
        return _interceptionContext;
    }

    private bool HasUnresolvedActiveSalvos() =>
        _missileEngagement.ActiveSalvos.Any(
            salvo => !_salvosResolvedThisPhase.Contains(salvo.Id));

    private string BuildMissileActionMessage(
        string actionName,
        GuidedMissileSalvo salvo,
        GuidedMissileAdvanceResult result)
    {
        if (salvo.OwnerSide == TacticalSide.Enemy)
        {
            ObserverSafeMissileViewSnapshot view =
                _trackState.BuildPlayerMissileView(
                    _missileEngagement,
                    requestedSelectedSalvoId: null);
            TacticalMissileContact? contact = view.Contacts.FirstOrDefault(
                item => string.Equals(
                    item.SalvoId,
                    salvo.Id,
                    StringComparison.Ordinal));

            if (contact is null)
            {
                return
                    $"{actionName}: enemy missile activity resolved; no new hostile missile contact was acquired.";
            }

            string projection = view.Projections.FirstOrDefault(item =>
                string.Equals(
                    item.SalvoId,
                    salvo.Id,
                    StringComparison.Ordinal))?.Status.ToString() ?? "none";
            return
                $"{actionName}: hostile contact {salvo.Id} observed at {Format(contact.Coordinate)} " +
                $"with {contact.TrackQuality} track; status {contact.Status}; " +
                $"observer-side route display {projection}.";
        }

        string movement = result.DistanceTraveledThisPhase == 0
            ? "moved 0 hexes"
            : $"moved {FormatHexCount(result.DistanceTraveledThisPhase)} from " +
              $"{Format(result.StartingCoordinate)} to {Format(result.EndingCoordinate)}";
        string attempts = result.InterceptionAttempts.Count == 0
            ? "no interception attempt"
            : string.Join(
                ", ",
                result.InterceptionAttempts.Select(attempt =>
                    $"{attempt.DefenseSystemId}:{attempt.Outcome}"));

        MissileTerminalOutcome terminalOutcome = GetTerminalOutcome(result);
        string outcome = result.Status switch
        {
            GuidedMissileStatus.Expended
                when terminalOutcome == MissileTerminalOutcome.CriticalHit =>
                "CRITICAL IMPACT after both PDS opportunities.",
            GuidedMissileStatus.Expended
                when terminalOutcome == MissileTerminalOutcome.Hit =>
                "IMPACT after both PDS opportunities.",
            GuidedMissileStatus.Expended
                when terminalOutcome == MissileTerminalOutcome.Miss =>
                "TERMINAL MISS; the attack package was expended.",
            GuidedMissileStatus.Dud =>
                "DUD on a natural 01; the inert package remains potentially recoverable.",
            GuidedMissileStatus.Searching =>
                "SEARCHING at the candidate hex; no Current/Firm terminal solution exists yet.",
            GuidedMissileStatus.InFlight =>
                "IN FLIGHT; later missile phases were not simulated.",
            GuidedMissileStatus.WaitingForRoute =>
                "WAITING; no legal route exists, so no movement fuel was spent.",
            GuidedMissileStatus.WaitingForTrack =>
                "WAITING for a usable datalink, peer, or missile-local report.",
            GuidedMissileStatus.RangeExhausted =>
                "RANGE EXHAUSTED without a terminal opportunity.",
            GuidedMissileStatus.Intercepted =>
                "INTERCEPTED and terminal.",
            GuidedMissileStatus.SelfDestructed =>
                "SELF-DESTRUCTED safely after search fuel was exhausted.",
            GuidedMissileStatus.Destroyed =>
                "DESTROYED and terminal.",
            _ => result.Status.ToString(),
        };

        return
            $"{actionName}: friendly {salvo.Id}, {salvo.LauncherId} -> {salvo.TargetId}; " +
            $"{movement}; selected guidance {salvo.LastGuidanceSource}; {attempts}; " +
            $"fuel {salvo.TotalFuelSpent}/{salvo.Profile.MaximumRange}; {outcome}";
    }

    private void ShowMissileOverlay()
    {
        _modeSelector.Select((int)TargetingMode.Missile);
        _board.DisplayMode = TargetingMode.Missile;
        SyncMissileBoardState();
    }

    private GuidedMissileSalvo? SelectedSalvo() =>
        _selectedMissileSalvoId is null
            ? null
            : _missileEngagement.Find(_selectedMissileSalvoId);

    private void OnSensorStateToggled(bool _)
    {
        if (_trackState is null)
        {
            return;
        }

        SensorMode playerMode = _playerActiveSensorsToggle.ButtonPressed
            ? SensorMode.Active
            : SensorMode.Passive;
        SensorMode enemyMode = _enemyActiveSensorsToggle.ButtonPressed
            ? SensorMode.Active
            : SensorMode.Passive;
        _trackState.SetSensorState(
            playerMode,
            enemyMode,
            _playerJammingToggle.ButtonPressed,
            _enemyJammingToggle.ButtonPressed);

        string message =
            $"Sensor state changed: player {playerMode}, enemy {enemyMode}; " +
            $"player jammer {(_playerJammingToggle.ButtonPressed ? "ON" : "off")}, " +
            $"enemy jammer {(_enemyJammingToggle.ButtonPressed ? "ON" : "off")}. " +
            "Track Update completed without reopening any resolved command.";
        _immediateFeedbackLabel.Text = message;
        _diagnosticLog?.Record(
            DiagnosticEventType.SensorStateChanged,
            message,
            turnNumber: _turnState.TurnNumber,
            phase: _turnState.Phase,
            actorId: _scenario.PlayerShipId,
            data: DiagnosticData(
                ("playerSensorMode", playerMode.ToString()),
                ("enemySensorMode", enemyMode.ToString()),
                ("playerJammingEnabled", _playerJammingToggle.ButtonPressed.ToString()),
                ("enemyJammingEnabled", _enemyJammingToggle.ButtonPressed.ToString()),
                ("observationEpoch", _turnState.TurnNumber.ToString())));
        LogTrackUpdates(_trackState.Refresh(
            TrackUpdateTrigger.SensorStateChanged,
            _missileEngagement.Salvos,
            _turnState.TurnNumber));
        RefreshLocalSensorsForAllActive(
            MissileGuidanceObservationOpportunity.SensorStateChanged);
        RecalculateDerivedState(resetBoardScenario: false);
        UpdateAllTextAndControls();
    }

    private void ResetCurrentScenario() => LoadScenario(
        _currentScenarioIndex,
        TrackUpdateTrigger.ScenarioReset);

    private void OnScenarioSelected(long index) => LoadScenario((int)index);

    private void OnModeSelected(long index)
    {
        _board.DisplayMode = (TargetingMode)index;
        SyncMissileBoardState();
        _board.RefreshDisplay();
    }

    private void OnAuthoritativeMissileDebugToggled(bool enabled)
    {
        _authoritativeMissileDebugLabel.Visible = enabled;
        UpdateAuthoritativeMissileDebugText();

        if (enabled)
        {
            CallDeferred(nameof(ScrollAuthoritativeMissileDebugIntoView));
        }
    }

    private void ScrollAuthoritativeMissileDebugIntoView()
    {
        if (_detailScroll is null ||
            _authoritativeMissileDebugLabel is null ||
            !_authoritativeMissileDebugLabel.Visible)
        {
            return;
        }

        float labelOffset =
            _authoritativeMissileDebugLabel.GlobalPosition.Y -
            _detailScroll.GlobalPosition.Y;
        int targetScroll = Math.Max(
            0,
            _detailScroll.ScrollVertical + (int)labelOffset - 12);
        _detailScroll.ScrollVertical = targetScroll;
    }

    private void UpdateAuthoritativeMissileDebugText()
    {
        if (_authoritativeMissileDebugToggle is null ||
            _authoritativeMissileDebugLabel is null ||
            !_authoritativeMissileDebugToggle.ButtonPressed)
        {
            return;
        }

        GuidedMissileSalvo? salvo = SelectedSalvo();
        if (salvo is null)
        {
            _authoritativeMissileDebugLabel.Text =
                "AUTHORITATIVE DEBUG\nNo missile is selected.";
            return;
        }

        MissileDatalinkReport? retained = salvo.RetainedDatalinkReport;
        MissileLocalTrackReport? local = salvo.LocalSensorTrack;
        _lastAutonomousGuidanceBySalvo.TryGetValue(
            salvo.Id,
            out MissileAutonomousGuidanceResult? autonomous);
        string localCoordinate = local is null
            ? "none"
            : Format(local.GuidanceCoordinate);
        string retainedCoordinate = retained is null
            ? "none"
            : Format(retained.GuidanceCoordinate);
        string guidanceCoordinate = salvo.LastTrackQuality switch
        {
            MissileTargetTrackQuality.Current =>
                salvo.CurrentTrackedTargetCoordinate.HasValue
                    ? Format(salvo.CurrentTrackedTargetCoordinate.Value)
                    : "none",
            MissileTargetTrackQuality.Approximate or
            MissileTargetTrackQuality.Stale =>
                salvo.LastKnownTargetCoordinate.HasValue
                    ? Format(salvo.LastKnownTargetCoordinate.Value)
                    : "none",
            _ => "none",
        };

        _authoritativeMissileDebugLabel.Text =
            "AUTHORITATIVE DEBUG - NOT PLAYER KNOWLEDGE\n" +
            $"{salvo.Id} actual {Format(salvo.CurrentCoordinate)}; " +
            $"status {salvo.Status}; fuel {salvo.TotalFuelSpent}/" +
            $"{salvo.Profile.MaximumRange}\n" +
            $"Datalink now {salvo.DatalinkState}; retained " +
            $"{retained?.ReceivedQuality.ToString() ?? "none"} " +
            $"at {retainedCoordinate}; age " +
            $"{retained?.AgePhases.ToString() ?? "none"}; uncertainty " +
            $"{retained?.EffectiveUncertaintyRadiusHexes.ToString() ?? "none"}\n" +
            $"Local sensor {local?.SensorMode.ToString() ?? "none"}; " +
            $"track {local?.Quality.ToString() ?? "none"} at " +
            $"{localCoordinate}; uncertainty " +
            $"{local?.UncertaintyRadiusHexes.ToString() ?? "none"}\n" +
            $"Selected guidance {salvo.LastGuidanceSource} " +
            $"{salvo.LastTrackQuality?.ToString() ?? "none"} at " +
            $"{guidanceCoordinate}\n" +
            $"Terminal {salvo.TerminalState}; opportunity " +
            $"{(salvo.TerminalOpportunityCoordinate.HasValue ? Format(salvo.TerminalOpportunityCoordinate.Value) : "none")}; " +
            $"entry PDS resolved {salvo.TerminalEntryDefenseResolved}\n" +
            $"Acquisition seeker {salvo.LastTerminalResolution?.UsedSeekerAcquisition.ToString() ?? "none"}; " +
            $"roll {salvo.LastTerminalResolution?.AcquisitionRoll?.ToString() ?? "none"}/" +
            $"{salvo.LastTerminalResolution?.AcquisitionChancePercent?.ToString() ?? "none"}; " +
            $"Firm {salvo.LastTerminalResolution?.HasFirmSolution.ToString() ?? "none"}\n" +
            $"Attack roll {salvo.LastTerminalResolution?.AttackRoll?.ToString() ?? "none"}/" +
            $"{salvo.LastTerminalResolution?.EffectiveHitChancePercent?.ToString() ?? "none"}; " +
            $"outcome {salvo.LastTerminalResolution?.Outcome.ToString() ?? "none"}\n" +
            $"Reason: {salvo.LastTerminalResolution?.Reason ?? salvo.LastGuidanceDecisionReason}\n" +
            $"Last action replans: {autonomous?.ReplanCount.ToString() ?? "none"}.\n" +
            $"Observation steps: {FormatAutonomousObservationSteps(autonomous)}.";
    }

    private static string FormatAutonomousObservationSteps(
        MissileAutonomousGuidanceResult? autonomous)
    {
        if (autonomous is null || autonomous.Steps.Count == 0)
        {
            return "none";
        }

        return string.Join(
            ", ",
            autonomous.Steps.Select(step =>
                $"{step.Opportunity}@{Format(step.MissileCoordinate)}" +
                (step.GuidanceChanged ? "[replan]" : string.Empty)));
    }

    private void OnCoordinateToggled(bool enabled)
    {
        _board.ShowCoordinates = enabled;
        _board.RefreshDisplay();
    }

    private void OnHoveredHexChanged(HexCoord? coordinate)
    {
        if (coordinate is not HexCoord existing)
        {
            _hoverLabel.Text = "Hover: outside map";
            return;
        }

        IEnumerable<string> mapContacts = _trackState.PlayerMapSnapshot.Contacts
            .Where(contact => contact.Coordinate == existing)
            .Select(contact =>
                $"{contact.Name}: {contact.TrackQuality?.ToString() ?? "navigation"}");
        TacticalMissileContact[] missiles = _trackState
            .PlayerMissileContacts(_missileEngagement.Salvos)
            .Where(contact => contact.Coordinate == existing)
            .OrderBy(contact => contact.SalvoId, StringComparer.Ordinal)
            .ToArray();
        IEnumerable<string> missileContacts = missiles.Select(contact =>
            $"{contact.SalvoId}: {contact.TrackQuality}, {contact.Status}");
        string contacts = string.Join("; ", mapContacts.Concat(missileContacts));
        string stack = missiles.Length > 1
            ? $"; missile stack x{missiles.Length}"
            : string.Empty;
        _hoverLabel.Text =
            $"Hover: {Format(existing)}{stack}" +
            (string.IsNullOrWhiteSpace(contacts) ? "; no known contacts" : $"; {contacts}");
    }

    private void OnHexClicked(HexCoord coordinate)
    {
        MapCell cell = _scenario.Map.GetCell(coordinate);
        TacticalMapContact[] visibleContacts = _trackState.PlayerMapSnapshot.Contacts
            .Where(contact => contact.Coordinate == coordinate)
            .ToArray();
        TacticalMissileContact[] missileContacts = _trackState
            .PlayerMissileContacts(_missileEngagement.Salvos)
            .Where(contact => contact.Coordinate == coordinate)
            .ToArray();
        IEnumerable<string> contactDescriptions = visibleContacts.Select(contact =>
            $"{contact.Name} ({contact.Kind}; {contact.TrackQuality?.ToString() ?? "navigation"})")
            .Concat(missileContacts.Select(contact =>
                $"{(contact.OwnerSide == TacticalSide.Player ? "Friendly" : "Enemy")} {contact.SalvoId} " +
                $"(Missile; {contact.TrackQuality}; {contact.Status}; " +
                $"fuel {contact.TotalFuelSpent}/{contact.MaximumRange})"));
        string occupants = string.Join(", ", contactDescriptions);
        if (string.IsNullOrWhiteSpace(occupants))
        {
            occupants = "no known contacts";
        }

        _inspectionLabel.Text =
            $"Selected {Format(coordinate)}; terrain: {cell.Terrain}; known contacts: {occupants}.";

        if (_board.DisplayMode == TargetingMode.Movement)
        {
            PreviewMovement(coordinate);
            return;
        }

        TacticalMissileContact[] selectableMissiles = missileContacts
            .Where(contact => !contact.IsTerminal)
            .OrderBy(contact => contact.SalvoId, StringComparer.Ordinal)
            .ToArray();
        TacticalMissileContact? missileContactAtCoordinate = null;
        bool deselectSingleMissile = false;
        if (selectableMissiles.Length > 0)
        {
            int currentIndex = Array.FindIndex(
                selectableMissiles,
                contact => string.Equals(
                    contact.SalvoId,
                    _selectedMissileSalvoId,
                    StringComparison.Ordinal));
            deselectSingleMissile =
                selectableMissiles.Length == 1 && currentIndex == 0;
            if (!deselectSingleMissile)
            {
                int nextIndex = currentIndex < 0
                    ? 0
                    : (currentIndex + 1) % selectableMissiles.Length;
                missileContactAtCoordinate = selectableMissiles[nextIndex];
            }
        }

        GuidedMissileSalvo? salvoAtCoordinate =
            missileContactAtCoordinate is null
                ? null
                : _missileEngagement.Find(
                    missileContactAtCoordinate.SalvoId);

        if (_board.DisplayMode == TargetingMode.DirectFire)
        {
            if (_turnState.Phase != TacticalTurnPhase.DirectFire ||
                _directFireResolved)
            {
                return;
            }

            if (deselectSingleMissile)
            {
                _selectedMissileSalvoId = null;
                _directFireActionMessage =
                    $"Deselected the hostile missile at {Format(coordinate)}.";
            }
            else if (salvoAtCoordinate is not null &&
                salvoAtCoordinate.OwnerSide == TacticalSide.Enemy)
            {
                _selectedMissileSalvoId = salvoAtCoordinate.Id;
                _selectedDirectFireShipTargetId = null;
                _directFireActionMessage =
                    $"Selected hostile missile {salvoAtCoordinate.Id} at {Format(coordinate)} with {missileContactAtCoordinate!.TrackQuality} track for direct-fire interception" +
                    (selectableMissiles.Length > 1
                        ? $"; click again to cycle {selectableMissiles.Length} collocated salvos."
                        : ".");
            }
            else if (_trackState.PlayerTrackOnEnemy is
                     { IsVisibleOnTacticalMap: true } directFireEnemyTrack &&
                     coordinate == directFireEnemyTrack.EstimatedCoordinate)
            {
                bool deselectShip = string.Equals(
                    _selectedDirectFireShipTargetId,
                    _scenario.EnemyShipId,
                    StringComparison.Ordinal);
                _selectedDirectFireShipTargetId =
                    deselectShip ? null : _scenario.EnemyShipId;
                _selectedMissileSalvoId = null;
                _directFireActionMessage = deselectShip
                    ? $"Deselected Enemy Ship at {Format(coordinate)}."
                    : $"Selected Enemy Ship {directFireEnemyTrack.Quality} contact at {Format(coordinate)} as the direct-fire target.";
            }

            SyncMissileBoardState();
            UpdateAllTextAndControls();
            return;
        }

        if (_board.DisplayMode != TargetingMode.Missile)
        {
            return;
        }

        if (deselectSingleMissile)
        {
            _selectedMissileSalvoId = null;
            _missileActionMessage =
                $"Deselected the missile at {Format(coordinate)}.";
        }
        else if (salvoAtCoordinate is not null)
        {
            _selectedMissileSalvoId = salvoAtCoordinate.Id;
            _missileActionMessage =
                $"Selected {salvoAtCoordinate.Id} at {Format(coordinate)} with {missileContactAtCoordinate!.TrackQuality} track" +
                (selectableMissiles.Length > 1
                    ? $"; click again to cycle {selectableMissiles.Length} collocated salvos."
                    : ".");
        }
        else if (_trackState.PlayerTrackOnEnemy is
                 { IsVisibleOnTacticalMap: true } missileEnemyTrack &&
                 coordinate == missileEnemyTrack.EstimatedCoordinate)
        {
            bool deselectShip = string.Equals(
                _selectedPlayerTargetId,
                _scenario.EnemyShipId,
                StringComparison.Ordinal);
            _selectedPlayerTargetId =
                deselectShip ? null : _scenario.EnemyShipId;
            _selectedMissileSalvoId = null;
            _missileActionMessage = deselectShip
                ? $"Deselected Enemy Ship at {Format(coordinate)}."
                : $"Selected Enemy Ship {missileEnemyTrack.Quality} contact at {Format(coordinate)} as the player missile target.";
        }

        SyncMissileBoardState();
        UpdateAllTextAndControls();
    }

    private static Label CreateSectionLabel(string text)
    {
        var label = CreateWrappedLabel(text);
        label.AddThemeFontSizeOverride("font_size", 17);
        return label;
    }

    private static Label CreateWrappedLabel(string text) => new()
    {
        Text = text,
        AutowrapMode = TextServer.AutowrapMode.WordSmart,
        ClipText = false,
        CustomMinimumSize = Vector2.Zero,
        SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
    };

    private static CheckButton CreateWrappedCheckButton(
        string text,
        string tooltip) => new()
    {
        Text = text,
        TooltipText = tooltip,
        ButtonPressed = false,
        AutowrapMode = TextServer.AutowrapMode.WordSmart,
        TextOverrunBehavior = TextServer.OverrunBehavior.TrimEllipsis,
        CustomMinimumSize = Vector2.Zero,
        SizeFlagsHorizontal = Control.SizeFlags.ExpandFill,
    };

    private static string FormatCompactSensorEvaluation(
        SensorContactEvaluationResult? evaluation)
    {
        if (evaluation is null)
        {
            return "no sensor evaluation";
        }

        return
            $"{evaluation.Status}; d={evaluation.DistanceHexes}; " +
            $"F {evaluation.BaseFirmRangeHexes}->{evaluation.EffectiveFirmRangeHexes}, " +
            $"A {evaluation.BaseApproximateRangeHexes}->{evaluation.EffectiveApproximateRangeHexes}; " +
            $"mode {FormatSigned(evaluation.ObserverModeRangeModifierHexes)}, " +
            $"sig {FormatSigned(evaluation.TargetSignatureRangeModifierHexes)}, " +
            $"env -{evaluation.EnvironmentRangePenaltyHexes}, " +
            $"jam -{evaluation.NetJammingRangePenaltyHexes} " +
            $"({evaluation.RawJammingRangePenaltyHexes}-{evaluation.CounterJammingStrength}).";
    }

    private static string FormatSensorEvaluation(
        SensorContactEvaluationResult? evaluation)
    {
        if (evaluation is null)
        {
            return "direct owner knowledge or no sensor evaluation recorded.";
        }

        return
            $"{evaluation.Status} at {evaluation.DistanceHexes} hexes; " +
            $"effective Firm {evaluation.EffectiveFirmRangeHexes}, " +
            $"Approximate {evaluation.EffectiveApproximateRangeHexes}; " +
            $"mode {FormatSigned(evaluation.ObserverModeRangeModifierHexes)}, " +
            $"signature {FormatSigned(evaluation.TargetSignatureRangeModifierHexes)}, " +
            $"environment -{evaluation.EnvironmentRangePenaltyHexes}, " +
            $"jamming -{evaluation.NetJammingRangePenaltyHexes} " +
            $"(raw {evaluation.RawJammingRangePenaltyHexes}, counter {evaluation.CounterJammingStrength}).";
    }

    private static string FormatSigned(int value) =>
        value >= 0 ? $"+{value}" : value.ToString();

    private static string FormatHexCount(int count) =>
        $"{count} hex{(count == 1 ? string.Empty : "es")}";

    private static string Format(HexCoord coordinate) =>
        $"({coordinate.Q},{coordinate.R})";

    private static string FormatPath(IEnumerable<HexCoord> path) =>
        string.Join(" -> ", path.Select(Format));

    private static string FormatNullable(int? value) =>
        value?.ToString() ?? "none";

    private static TacticalTurnPhase NextPhase(TacticalTurnPhase phase) => phase switch
    {
        TacticalTurnPhase.Movement => TacticalTurnPhase.ElectronicWarfare,
        TacticalTurnPhase.ElectronicWarfare => TacticalTurnPhase.DirectFire,
        TacticalTurnPhase.DirectFire => TacticalTurnPhase.MissileAndInterception,
        TacticalTurnPhase.MissileAndInterception => TacticalTurnPhase.Damage,
        TacticalTurnPhase.Damage => TacticalTurnPhase.DamageControl,
        _ => TacticalTurnPhase.Movement,
    };

    private static string FormatPhase(TacticalTurnPhase phase) => phase switch
    {
        TacticalTurnPhase.MissileAndInterception => "Missile / Interception",
        TacticalTurnPhase.ElectronicWarfare => "Electronic Warfare",
        TacticalTurnPhase.DirectFire => "Direct Fire",
        TacticalTurnPhase.DamageControl => "Damage Control",
        _ => phase.ToString(),
    };
}
