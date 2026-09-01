from __future__ import annotations

from typing import Any


def decide_contract_case(case: dict[str, Any]) -> dict[str, Any]:
    """Pure CP146 semantic contract mirrored by CombatResourceDoctrineService.cs.

    Fixture values are abstract policy inputs. The canonical Python combat planner
    maps concrete component/mode state into the same doctrine while retaining
    richer mechanics such as Energy Low/Standard/Overload and partial PDS power.
    """
    remaining = int(case["spendableTacticalPower"])
    banks = int(case["mainWeaponBanks"])
    bank_power = int(case["mainWeaponPowerPerBank"])
    minimum_weapon = banks * bank_power

    active = False
    active_cost = int(case["activeSensorPower"])
    if active_cost <= remaining and remaining - active_cost >= minimum_weapon:
        active = True
        remaining -= active_cost
    elif not bool(case["passiveSensorProvidesUsableTrack"]) and active_cost <= remaining:
        active = True
        remaining -= active_cost

    eccm = False
    eccm_cost = int(case["eccmPower"])
    if (bool(case["eccmAvailable"]) and bool(case["opponentEcmObserved"])
            and bool(case["firmTrackDegradedByObservedEcm"])
            and eccm_cost <= remaining and remaining - eccm_cost >= minimum_weapon):
        eccm = True
        remaining -= eccm_cost

    funded_banks = 0
    for _ in range(banks):
        if bank_power <= remaining:
            remaining -= bank_power
            funded_banks += 1

    capability = str(case["opponentCapability"])
    unknown = capability == "Unknown"
    imminent = int(case["imminentMissileSubflights"])
    missile_relevant = imminent > 0
    pds_ready = False
    funded_rc = 0
    pds_cost = int(case["pdsReadinessPower"])
    if bool(case["pdsAvailable"]) and (unknown or missile_relevant) and pds_cost <= remaining:
        pds_ready = True
        funded_rc = int(case["pdsReactionCapacity"])
        remaining -= pds_cost

    hardener_relevant = unknown or capability == "Energy"
    hardener = False
    hardener_cost = int(case["shieldHardenerPower"])
    if bool(case["shieldHardenerAvailable"]) and hardener_relevant and hardener_cost <= remaining:
        hardener = True
        remaining -= hardener_cost

    ecm = False
    ecm_cost = int(case["ecmPower"])
    if bool(case["ecmAvailable"]) and ecm_cost <= remaining:
        ecm = True
        remaining -= ecm_cost

    family = str(case["mainWeaponFamily"]).lower()
    can_hold = bool(case["firmTrackAvailable"]) and funded_banks > 0 and family in {"kinetic", "energy"}
    excess = max(0, imminent - funded_rc)
    legal_ship_attack = bool(case.get("legalMainWeaponShipAttack", True))
    held = 0
    if can_hold and excess > 0 and (not legal_ship_attack or funded_banks >= 2):
        held = 1

    return {
        "activeSensor": active,
        "fundedMainWeaponBanks": funded_banks,
        "pdsReady": pds_ready,
        "fundedPdsReactionCapacity": funded_rc,
        "shieldHardenerActive": hardener,
        "ecmActive": ecm,
        "eccmActive": eccm,
        "heldMainWeaponBanks": held,
        "tacticalPowerRemaining": remaining,
    }
