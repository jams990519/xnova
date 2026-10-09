"""Pure game formulas (Xnova / classic OGame).

Every function here is deterministic and has no side effects, so it can be
tested on its own. Where Xnova had a bug (see investigacion/02 §16), the
classic OGame rule is used instead and the docstring says so.
"""
from __future__ import annotations

from math import ceil, floor, sqrt

from ..data.elements import COMBUSTION, ELEMENTS, HYPERSPACE_DRIVE, IMPULSE

Resources = tuple[float, float, float]

DRIVE_BONUS = {COMBUSTION: 0.1, IMPULSE: 0.2, HYPERSPACE_DRIVE: 0.3}

BASE_INCOME = (20.0, 10.0, 0.0)  # free metal / crystal / deuterium per hour on every planet
HOME_PLANET_FIELDS = 163
MOON_BASE_FIELDS = 1
TERRAFORMER_FIELDS = 5  # per level
LUNAR_BASE_FIELDS = 3  # per level


# --- Costs -----------------------------------------------------------------

def level_cost(element_id: int, level: int) -> tuple[int, int, int]:
    """Cost of building or researching ``level`` (going from level-1 to level)."""
    element = ELEMENTS[element_id]
    mult = element.factor ** (level - 1)
    return tuple(floor(c * mult) for c in element.cost)  # type: ignore[return-value]


def level_energy_cost(element_id: int, level: int) -> int:
    element = ELEMENTS[element_id]
    if not element.energy_cost:
        return 0
    return floor(element.energy_cost * element.factor ** (level - 1))


def units_cost(element_id: int, count: int) -> tuple[int, int, int]:
    element = ELEMENTS[element_id]
    return tuple(c * count for c in element.cost)  # type: ignore[return-value]


def cumulative_cost(element_id: int, level: int) -> float:
    """Total metal + crystal + deuterium spent to reach ``level`` (for points)."""
    element = ELEMENTS[element_id]
    total = sum(element.cost)
    if level <= 0 or total == 0:
        return 0.0
    if element.factor == 1:
        return float(total * level)
    return total * (element.factor ** level - 1) / (element.factor - 1)


# --- Times (seconds) --------------------------------------------------------

def building_seconds(cost: tuple[int, int, int], robots: int, nanites: int, economy_speed: float,
                     constructor: int = 0) -> float:
    hours = (cost[0] + cost[1]) / (2500 * (1 + robots)) * 0.5 ** nanites / economy_speed
    hours *= max(0.0, 1 - 0.1 * constructor)
    return max(1.0, hours * 3600)


def research_seconds(cost: tuple[int, int, int], lab_level: int, economy_speed: float,
                     scientist: int = 0) -> float:
    """Classic OGame research time (Xnova divided by 5000 instead of 1000, see §16)."""
    hours = (cost[0] + cost[1]) / (1000 * (1 + lab_level)) / economy_speed
    hours *= max(0.0, 1 - 0.1 * scientist)
    return max(1.0, hours * 3600)


def unit_seconds(element_id: int, shipyard: int, nanites: int, economy_speed: float,
                 technocrat: int = 0, defender: int = 0, is_defense: bool = False) -> float:
    cost = ELEMENTS[element_id].cost
    hours = (cost[0] + cost[1]) / (2500 * (1 + shipyard)) * 0.5 ** nanites / economy_speed
    if is_defense:
        hours *= max(0.0, 1 - 0.375 * defender)
    else:
        hours *= max(0.0, 1 - 0.05 * technocrat)
    return max(1.0, hours * 3600)


# --- Production -------------------------------------------------------------

def _growth(base: float, level: int) -> float:
    return base * level * 1.1 ** level


def satellite_energy(temp_max: int) -> float:
    return max(0.0, temp_max / 4 + 20)


def production(buildings: dict[int, int], percent: dict[int, int], satellites: int, temp_max: int,
               economy_speed: float, geologist: int = 0, engineer: int = 0) -> dict[str, float]:
    """Hourly production of a planet.

    Returns metal, crystal and deuterium per hour (deuterium already net of
    the fusion reactor), energy produced, energy needed and the production
    factor (share of the energy the mines get).
    """
    def lvl(eid):
        return buildings.get(eid, 0)

    def pct(eid):
        return percent.get(eid, 100) / 100

    metal = _growth(30, lvl(1)) * pct(1)
    crystal = _growth(20, lvl(2)) * pct(2)
    deuterium = _growth(10, lvl(3)) * (1.28 - 0.002 * temp_max) * pct(3)
    energy_needed = (_growth(10, lvl(1)) * pct(1) + _growth(10, lvl(2)) * pct(2)
                     + _growth(30, lvl(3)) * pct(3))
    energy_produced = (_growth(20, lvl(4)) * pct(4) + _growth(50, lvl(12)) * pct(12)
                       + satellites * satellite_energy(temp_max) * pct(212))
    energy_produced *= 1 + 0.05 * engineer
    fusion_burn = _growth(10, lvl(12)) * pct(12)

    factor = 1.0 if energy_needed <= 0 else min(1.0, energy_produced / energy_needed)
    bonus = 1 + 0.05 * geologist
    return {
        "metal": (metal * factor * bonus + BASE_INCOME[0]) * economy_speed,
        "crystal": (crystal * factor * bonus + BASE_INCOME[1]) * economy_speed,
        "deuterium": (max(0.0, deuterium) * factor * bonus + BASE_INCOME[2] - fusion_burn) * economy_speed,
        "energy_produced": energy_produced,
        "energy_needed": energy_needed,
        "factor": factor,
    }


def storage_capacity(level: int, storer: int = 0) -> float:
    """Classic OGame storage: 100,000 + 50,000 x (ceil(1.6^level) - 1). Xnova used 10 million x 1.5^level."""
    return (100_000 + 50_000 * (ceil(1.6 ** level) - 1)) * (1 + 0.5 * storer)


def max_fields(base_fields: int, buildings: dict[int, int], is_moon: bool) -> int:
    if is_moon:
        return base_fields + LUNAR_BASE_FIELDS * buildings.get(41, 0)
    return base_fields + TERRAFORMER_FIELDS * buildings.get(33, 0)


def used_fields(buildings: dict[int, int]) -> int:
    return sum(buildings.values())


# --- Fleets -----------------------------------------------------------------

def distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    if a[0] != b[0]:
        return 20_000 * abs(a[0] - b[0])
    if a[1] != b[1]:
        return 2700 + 95 * abs(a[1] - b[1])
    if a[2] != b[2]:
        return 1000 + 5 * abs(a[2] - b[2])
    return 5


def ship_drive(element_id: int, research: dict[int, int]) -> tuple[float, int]:
    """Base speed (with drive research) and fuel use of one ship.

    Classic OGame formula: base x (1 + bonus x level). Xnova added the bonus of
    the old drive to the new base for small cargos and bombers (§16).
    """
    element = ELEMENTS[element_id]
    for drive in element.drives:
        level = research.get(drive.tech, 0)
        if level >= drive.min_level:
            return drive.speed * (1 + DRIVE_BONUS[drive.tech] * level), drive.fuel
    return 0.0, 0


def ship_speed(element_id: int, research: dict[int, int], general: int = 0) -> float:
    speed, _ = ship_drive(element_id, research)
    return speed * (1 + 0.25 * general)


def fleet_speed(ships: dict[int, int], research: dict[int, int], general: int = 0) -> float:
    speeds = [ship_speed(eid, research, general) for eid, n in ships.items() if n > 0]
    return min(speeds) if speeds else 0.0


def flight_seconds(dist: int, speed: float, percent: int, fleet_speed_factor: float) -> float:
    """One-way flight time. ``percent`` is 10..100."""
    if speed <= 0:
        return float("inf")
    raw = 35_000 / (percent / 10) * sqrt(dist * 10 / speed) + 10
    return max(1.0, raw / fleet_speed_factor)


def fuel_cost(ships: dict[int, int], research: dict[int, int], dist: int, seconds: float,
              fleet_speed_factor: float, general: int = 0) -> int:
    """Deuterium burned by the whole mission (Xnova/OGame formula)."""
    raw_seconds = seconds * fleet_speed_factor
    total = 0.0
    for eid, count in ships.items():
        if count <= 0:
            continue
        speed = ship_speed(eid, research, general)
        _, fuel = ship_drive(eid, research)
        if speed <= 0:
            continue
        spd = 35_000 / max(1.0, raw_seconds - 10) * sqrt(dist * 10 / speed)
        total += fuel * count * dist / 35_000 * (spd / 10 + 1) ** 2
    return round(total) + 1


def cargo_capacity(ships: dict[int, int]) -> int:
    return sum(ELEMENTS[eid].cargo * n for eid, n in ships.items())


def fleet_slots(computer: int, commander: int = 0) -> int:
    return 1 + computer + 3 * commander


# --- Points -----------------------------------------------------------------

def points_for_levels(levels: dict[int, int]) -> float:
    return sum(cumulative_cost(eid, lvl) for eid, lvl in levels.items()) / 1000


def points_for_units(units: dict[int, int]) -> float:
    return sum(sum(ELEMENTS[eid].cost) * n for eid, n in units.items() if eid in ELEMENTS) / 1000
