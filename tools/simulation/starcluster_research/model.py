from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class Build:
    id: str
    selections: dict[str, str]
    used_space: int
    capacity: int
    max_tl: int
    advanced_count: int
    info_advanced_count: int
    main_weapons: int
    reactors: int
    family: str
    composition: str
    space_class: str
    option_payloads: dict[str, dict[str, Any]]

    @property
    def free_space(self) -> int:
        return self.capacity - self.used_space


@dataclass(slots=True, frozen=True)
class PopulationCell:
    key: str
    composition: str
    progression: str
    space_pair: str
    population: int
    weight: float


@dataclass(slots=True, frozen=True)
class Pairing:
    id: str
    bundle_id: str
    orientation: str
    source: str
    side_a: Build
    side_b: Build
    population_cell: str = ''
    population_count: int = 0
    representative_weight: float = 0.0


@dataclass(slots=True, frozen=True)
class Variant:
    id: str
    pairing_id: str
    bundle_id: str
    orientation: str
    source: str
    movement_order: str
    initial_range: int
    side_a: Build
    side_b: Build
    population_cell: str = ''
    population_count: int = 0
    representative_weight: float = 0.0


@dataclass(slots=True)
class SideState:
    build: Build
    hull: int
    armor_integrity: int
    armor_protection: int
    shield: int
    shield_max: int
    shield_recharge: int
    weapon_ammo: int | None
    pds_ammo: int | None
    missiles_launched: int = 0
    direct_shots: int = 0
    direct_hits: int = 0
    missile_hits: int = 0
    pds_attempts: int = 0
    pds_intercepts: int = 0
    power_shortfall_events: int = 0
    power_spent_total: int = 0
    active_sensor_turns: int = 0
    high_sensor_turns: int = 0
    firm_track_turns: int = 0


@dataclass(slots=True)
class Missile:
    owner: str
    eta: int
    damage: int
    spen: int
    apen: int
    guidance: int


@dataclass(slots=True, frozen=True)
class TrialResult:
    winner: str
    turns: int
    final_range: int
    hull_a: int
    hull_b: int
    direct_shots_a: int
    direct_shots_b: int
    missile_launches_a: int
    missile_launches_b: int
    pds_attempts_a: int
    pds_attempts_b: int
    power_shortfalls_a: int
    power_shortfalls_b: int
    firm_track_turns_a: int
    firm_track_turns_b: int
    trial_error: str = ''
