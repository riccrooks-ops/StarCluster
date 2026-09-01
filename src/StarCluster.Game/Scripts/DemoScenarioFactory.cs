using System;
using System.Collections.Generic;
using StarCluster.Core.Geometry;
using StarCluster.Core.Maps;

namespace StarCluster.Game;

/// <summary>
/// Creates repeatable tactical arrangements for regression and focused Godot
/// demonstrations. These are presentation fixtures, not procedural game content.
/// </summary>
public static class DemoScenarioFactory
{
    private static readonly IReadOnlyList<string> ScenarioNames =
        Array.AsReadOnly(
            new[]
            {
                "Clear direct fire",
                "Single grazing",
                "Multiple grazings",
                "Blocked fire, indirect missile",
                "Sensor and jamming range gate",
                "Missile local-sensor occlusion",
                "Friendly missile route validation",
            });

    public static IReadOnlyList<string> Names => ScenarioNames;

    public static DemoScenario Create(int index) => index switch
    {
        0 => CreateClearScenario(),
        1 => CreateSingleGrazingScenario(),
        2 => CreateMultipleGrazingScenario(),
        3 => CreateBlockedScenario(),
        4 => CreateSensorAndJammingScenario(),
        5 => CreateMissileLocalSensorScenario(),
        6 => CreateFriendlyMissileRouteScenario(),
        _ => throw new ArgumentOutOfRangeException(
            nameof(index),
            index,
            $"Scenario index must be from 0 through {ScenarioNames.Count - 1}."),
    };

    private static DemoScenario CreateClearScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-3, 3);
        var enemy = new HexCoord(2, 3);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-clear", "Far World"),
            new HexCoord(2, -2));

        return new DemoScenario(
            ScenarioNames[0],
            "The ships share an unobstructed direct-fire line well above the central star.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static DemoScenario CreateSingleGrazingScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-2, 2);
        var enemy = new HexCoord(0, 1);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-graze", "Grazing World"),
            new HexCoord(-1, 2));

        return new DemoScenario(
            ScenarioNames[1],
            "The shot follows an exact hex boundary and grazes one planet on one side.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static DemoScenario CreateMultipleGrazingScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-3, 3);
        var enemy = new HexCoord(1, 1);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-near", "Near Grazing World"),
            new HexCoord(-2, 3));
        map.Place(
            MapObject.CreatePlanet("planet-far", "Far Grazing World"),
            new HexCoord(0, 1));

        return new DemoScenario(
            ScenarioNames[2],
            "Two separate boundary contacts are reported so a later combat rule can apply a cumulative penalty.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static DemoScenario CreateBlockedScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-4, 0);
        var enemy = new HexCoord(4, 0);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-route", "Outer World"),
            new HexCoord(2, -2));

        return new DemoScenario(
            ScenarioNames[3],
            "The central star blocks direct fire, while the missile planner finds a longer legal route around it.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static DemoScenario CreateSensorAndJammingScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-4, 4);
        var enemy = new HexCoord(4, 1);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-ew", "Quiet World"),
            new HexCoord(-2, -2));

        return new DemoScenario(
            ScenarioNames[4],
            "The ships are eight clear hexes apart. Passive neutral sensing is Approximate; player active sensing or enemy active emissions can make the contact Firm, while enemy jamming can shrink the effective envelope again.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static DemoScenario CreateMissileLocalSensorScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-2, -1);
        var enemy = new HexCoord(2, 3);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-local-sensor", "Reacquisition World"),
            new HexCoord(2, -2));

        return new DemoScenario(
            ScenarioNames[5],
            "The central star initially separates the launcher and target. Launch on the retained report, then maneuver so a missile can lose its datalink, acquire the target with its inferior onboard sensor, and replan after an entered hex.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static DemoScenario CreateFriendlyMissileRouteScenario()
    {
        SystemMap map = CreateBaseMap();
        var player = new HexCoord(-3, 3);
        var enemy = new HexCoord(2, 3);

        AddShips(map, player, enemy);
        map.Place(
            MapObject.CreatePlanet("planet-friendly-route", "Route Reference World"),
            new HexCoord(2, -2));

        return new DemoScenario(
            ScenarioNames[6],
            "A dedicated clear, Firm-track fixture for launching one player Missile Flight and validating its dashed planned route against the dotted observer-side estimate of a hostile flight.",
            map,
            PlayerId,
            EnemyId,
            player,
            enemy);
    }

    private static SystemMap CreateBaseMap()
    {
        MapObject star = MapObject.CreateStar("star-primary", "Primary Star");
        return SystemMap.Create(MapDefaults.SystemRadius, star);
    }

    private static void AddShips(
        SystemMap map,
        HexCoord playerPosition,
        HexCoord enemyPosition)
    {
        map.Place(
            MapObject.CreateShip(PlayerId, "Player Ship"),
            playerPosition);
        map.Place(
            MapObject.CreateShip(EnemyId, "Enemy Ship"),
            enemyPosition);
    }

    private const string PlayerId = "ship-player";
    private const string EnemyId = "ship-enemy";
}
