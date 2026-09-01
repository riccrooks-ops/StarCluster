from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class TacticalPackageCandidate:
    id: str
    tactical_power: int
    offense_utility_milli: int
    defense_utility_milli: int
    funded_main_banks: int
    held_main_banks: int
    pds_reaction_capacity: int
    active_sensor: bool = False
    firm_track: bool = False

    def __post_init__(self) -> None:
        if not str(self.id).strip():
            raise ValueError("tactical package id is required")
        values = (self.tactical_power, self.offense_utility_milli, self.defense_utility_milli,
                  self.funded_main_banks, self.held_main_banks, self.pds_reaction_capacity)
        if any(int(v) < 0 for v in values):
            raise ValueError("tactical package inputs must be non-negative")
        if int(self.held_main_banks) > int(self.funded_main_banks):
            raise ValueError("held main banks cannot exceed funded main banks")

    @property
    def total_utility_milli(self) -> int:
        return int(self.offense_utility_milli) + int(self.defense_utility_milli)


def _score(candidate: TacticalPackageCandidate) -> tuple[int, int, int, int, int, int, int, int, str]:
    """CP147 deterministic package ordering.

    Primary objective is expected one-turn raw combat swing.  Exact ties favor
    continued offense, then defensive value, then a funded main bank, then lower
    TP consumption.  The final id key exists only to guarantee reproducibility.
    No component statistic is altered by this policy function.
    """
    return (
        candidate.total_utility_milli,
        int(candidate.offense_utility_milli),
        int(candidate.defense_utility_milli),
        int(candidate.funded_main_banks),
        int(bool(candidate.active_sensor)),
        int(bool(candidate.firm_track)),
        -int(candidate.held_main_banks),
        -int(candidate.tactical_power),
        str(candidate.id),
    )


def choose_tactical_package(
    candidates: Iterable[TacticalPackageCandidate],
    spendable_tactical_power: int,
) -> TacticalPackageCandidate:
    spendable_tactical_power = int(spendable_tactical_power)
    if spendable_tactical_power < 0:
        raise ValueError("spendable_tactical_power cannot be negative")
    feasible = [c for c in candidates if 0 <= int(c.tactical_power) <= spendable_tactical_power]
    if not feasible:
        raise ValueError("at least one feasible tactical package is required")
    return max(feasible, key=_score)


def decide_contract_case(case: dict) -> dict:
    candidates = [
        TacticalPackageCandidate(
            id=str(row["id"]),
            tactical_power=int(row["tacticalPower"]),
            offense_utility_milli=int(row["offenseUtilityMilli"]),
            defense_utility_milli=int(row["defenseUtilityMilli"]),
            funded_main_banks=int(row["fundedMainBanks"]),
            held_main_banks=int(row["heldMainBanks"]),
            pds_reaction_capacity=int(row["pdsReactionCapacity"]),
            active_sensor=bool(row.get("activeSensor", False)),
            firm_track=bool(row.get("firmTrack", False)),
        )
        for row in case["candidates"]
    ]
    selected = choose_tactical_package(candidates, int(case["spendableTacticalPower"]))
    return {
        "selectedId": selected.id,
        "totalUtilityMilli": selected.total_utility_milli,
        "offenseUtilityMilli": selected.offense_utility_milli,
        "defenseUtilityMilli": selected.defense_utility_milli,
        "tacticalPower": selected.tactical_power,
        "fundedMainBanks": selected.funded_main_banks,
        "heldMainBanks": selected.held_main_banks,
        "pdsReactionCapacity": selected.pds_reaction_capacity,
        "activeSensor": selected.active_sensor,
        "firmTrack": selected.firm_track,
    }
