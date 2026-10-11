"""The numbers of every building, research, ship, defence, missile and officer.

Rebuilt from investigacion/02-reglas-y-numeros.md, which took them from
Xnova's own code. Where Xnova had a bug, the classic OGame rule is used
instead (see the table in the README) and the comment here says so.

Hull is never written down: Xnova derives it from the cost, (metal + crystal)
/ 10, so it is a property and cannot drift away from the price.
"""
from __future__ import annotations

from dataclasses import dataclass, field

BUILDING = "building"
RESEARCH = "research"
SHIP = "ship"
DEFENSE = "defense"
MISSILE = "missile"

# Drive researches. They are ordinary researches too, listed below.
COMBUSTION = 115
IMPULSE = 117
HYPERSPACE_DRIVE = 118


@dataclass(frozen=True)
class Drive:
    """One way a ship can fly. The first one the pilot has researched wins."""
    tech: int
    min_level: int
    speed: int
    fuel: int


@dataclass(frozen=True)
class Officer:
    id: int
    max_level: int
    requires: dict[int, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Element:
    id: int
    kind: str
    cost: tuple[int, int, int]
    factor: float = 1.0
    energy_cost: int = 0
    requires: dict[int, int] = field(default_factory=dict)
    # Buildings: where they may be built.
    planet: bool = True
    moon: bool = False
    # Ships and defences.
    shield: int = 0
    attack: int = 0
    cargo: int = 0
    drives: tuple[Drive, ...] = ()
    rapidfire: dict[int, int] = field(default_factory=dict)

    @property
    def hull(self) -> int:
        return (self.cost[0] + self.cost[1]) // 10


def _building(eid, cost, factor, requires=None, energy=0, planet=True, moon=False) -> Element:
    return Element(eid, BUILDING, cost, factor, energy, requires or {}, planet=planet, moon=moon)


def _research(eid, cost, requires=None, factor=2.0, energy=0) -> Element:
    return Element(eid, RESEARCH, cost, factor, energy, requires or {})


# Every ship carries rapid fire 5 against probes and solar satellites.
_VS_LIGHT = {210: 5, 212: 5}


def _ship(eid, cost, shield, attack, cargo, drives, requires, rapidfire=None) -> Element:
    return Element(eid, SHIP, cost, 1.0, 0, requires, shield=shield, attack=attack, cargo=cargo,
                   drives=drives, rapidfire={**_VS_LIGHT, **(rapidfire or {})})


def _defense(eid, cost, shield, attack, requires, kind=DEFENSE) -> Element:
    return Element(eid, kind, cost, 1.0, 0, requires, shield=shield, attack=attack)


_ALL = [
    # --- Buildings (18) ---------------------------------------------------
    _building(1, (60, 15, 0), 1.5),
    _building(2, (48, 24, 0), 1.6),
    _building(3, (225, 75, 0), 1.5),
    _building(4, (75, 30, 0), 1.5),
    _building(12, (900, 360, 180), 1.8, {3: 5, 113: 3}),
    _building(14, (400, 120, 200), 2.0, moon=True),
    _building(15, (1_000_000, 500_000, 100_000), 2.0, {14: 10, 108: 10}),
    _building(21, (400, 200, 100), 2.0, {14: 2}, moon=True),
    _building(22, (2000, 0, 0), 2.0, moon=True),
    _building(23, (2000, 1000, 0), 2.0, moon=True),
    _building(24, (2000, 2000, 0), 2.0, moon=True),
    _building(31, (200, 400, 200), 2.0),
    _building(33, (0, 50_000, 100_000), 2.0, {15: 1, 113: 12}, energy=1000),
    _building(34, (20_000, 40_000, 0), 2.0),
    _building(41, (20_000, 40_000, 20_000), 2.0, planet=False, moon=True),
    _building(42, (20_000, 40_000, 20_000), 2.0, {41: 1}, planet=False, moon=True),
    _building(43, (2_000_000, 4_000_000, 2_000_000), 2.0, {41: 1, 114: 7}, planet=False, moon=True),
    _building(44, (20_000, 20_000, 1000), 2.0),

    # --- Researches (16) --------------------------------------------------
    _research(106, (200, 1000, 200), {31: 3}),
    _research(108, (0, 400, 600), {31: 1}),
    _research(109, (800, 200, 0), {31: 4}),
    _research(110, (200, 600, 0), {113: 3, 31: 6}),
    _research(111, (1000, 0, 0), {31: 2}),
    _research(113, (0, 800, 400), {31: 1}),
    _research(114, (0, 4000, 2000), {113: 5, 110: 5, 31: 7}),
    _research(115, (400, 0, 600), {113: 1, 31: 1}),
    _research(117, (2000, 4000, 600), {113: 1, 31: 2}),
    _research(118, (10_000, 20_000, 6000), {114: 3, 31: 7}),
    _research(120, (200, 100, 0), {31: 1, 113: 2}),
    _research(121, (1000, 300, 100), {31: 4, 120: 5, 113: 4}),
    _research(122, (2000, 4000, 1000), {31: 5, 113: 8, 120: 10, 121: 5}),
    _research(123, (240_000, 400_000, 160_000), {31: 10, 108: 8, 114: 8}),
    _research(124, (4000, 8000, 4000), {31: 3, 108: 4, 117: 3}),
    # Graviton costs no resources, only 300,000 energy on one planet.
    _research(199, (0, 0, 0), {31: 12}, factor=3.0, energy=300_000),

    # --- Ships (14) -------------------------------------------------------
    # The small cargo and the bomber change drive: Xnova added the old bonus
    # to the new base (bug, see section 16); here each drive has its own base.
    _ship(202, (2000, 2000, 0), 10, 5, 5000,
          (Drive(IMPULSE, 5, 10_000, 40), Drive(COMBUSTION, 0, 5000, 20)), {21: 2, 115: 2}),
    _ship(203, (6000, 6000, 0), 25, 5, 25_000,
          (Drive(COMBUSTION, 0, 7500, 50),), {21: 4, 115: 6}),
    _ship(204, (3000, 1000, 0), 10, 50, 50,
          (Drive(COMBUSTION, 0, 12_500, 20),), {21: 1, 115: 1}, {202: 2}),
    _ship(205, (6000, 4000, 0), 25, 150, 100,
          (Drive(IMPULSE, 0, 10_000, 75),), {21: 3, 111: 2, 117: 2}, {202: 3}),
    _ship(206, (20_000, 7000, 2000), 50, 400, 800,
          (Drive(IMPULSE, 0, 15_000, 300),), {21: 5, 117: 4, 121: 2}, {204: 6, 401: 10}),
    _ship(207, (45_000, 15_000, 0), 200, 1000, 1500,
          (Drive(HYPERSPACE_DRIVE, 0, 10_000, 500),), {21: 7, 118: 4}, {401: 8}),
    _ship(208, (10_000, 20_000, 10_000), 100, 50, 7500,
          (Drive(IMPULSE, 0, 2500, 1000),), {21: 4, 117: 3}),
    _ship(209, (10_000, 6000, 2000), 10, 1, 20_000,
          (Drive(COMBUSTION, 0, 2000, 300),), {21: 4, 115: 6, 110: 2}),
    _ship(210, (0, 1000, 0), 0, 0, 5,
          (Drive(COMBUSTION, 0, 100_000_000, 1),), {21: 3, 115: 3, 106: 2}, {}),
    _ship(211, (50_000, 25_000, 15_000), 500, 1000, 500,
          (Drive(HYPERSPACE_DRIVE, 8, 5000, 1000), Drive(IMPULSE, 0, 4000, 1000)),
          {117: 6, 21: 8, 122: 5}, {401: 20, 402: 20, 403: 10, 405: 10}),
    # The solar satellite has no drive at all, so it can never be sent away.
    _ship(212, (0, 2000, 500), 10, 1, 0, (), {21: 1}, {}),
    _ship(213, (60_000, 50_000, 15_000), 500, 2000, 2000,
          (Drive(HYPERSPACE_DRIVE, 0, 5000, 1000),), {21: 9, 118: 6, 114: 5}, {215: 2, 402: 10}),
    _ship(214, (5_000_000, 4_000_000, 1_000_000), 50_000, 200_000, 1_000_000,
          (Drive(HYPERSPACE_DRIVE, 0, 100, 1),), {21: 12, 118: 7, 114: 6, 199: 1},
          {202: 250, 203: 250, 204: 200, 205: 100, 206: 33, 207: 30, 208: 250, 209: 250, 211: 25,
           213: 5, 215: 15, 401: 200, 402: 200, 403: 100, 404: 50, 405: 100}),
    _ship(215, (30_000, 40_000, 15_000), 400, 700, 750,
          (Drive(HYPERSPACE_DRIVE, 0, 10_000, 250),), {114: 5, 120: 12, 118: 5, 21: 8},
          {202: 3, 203: 3, 205: 4, 206: 4, 207: 7}),

    # --- Defences (8) -----------------------------------------------------
    _defense(401, (2000, 0, 0), 20, 80, {21: 1}),
    _defense(402, (1500, 500, 0), 25, 100, {113: 1, 21: 2, 120: 3}),
    _defense(403, (6000, 2000, 0), 100, 250, {113: 3, 21: 4, 120: 6}),
    _defense(404, (20_000, 15_000, 2000), 200, 1100, {21: 6, 113: 6, 109: 3, 110: 1}),
    _defense(405, (2000, 6000, 0), 500, 150, {21: 4, 121: 4}),
    _defense(406, (50_000, 50_000, 30_000), 300, 3000, {21: 8, 122: 7}),
    _defense(407, (10_000, 10_000, 0), 2000, 1, {110: 2, 21: 1}),
    _defense(408, (50_000, 50_000, 0), 2000, 1, {110: 6, 21: 6}),

    # --- Missiles (2): in the table, but the bot does not let them fly yet -
    _defense(502, (8000, 2000, 0), 1, 1, {44: 2}, kind=MISSILE),
    _defense(503, (12_500, 2500, 10_000), 1, 12_000, {44: 4}, kind=MISSILE),
]

ELEMENTS: dict[int, Element] = {element.id: element for element in _ALL}

# Only one of each per planet.
ONE_PER_PLANET = frozenset({407, 408})

# Finishing one of these gives miner experience (mines and storages).
MINER_XP_BUILDINGS = frozenset({1, 2, 3, 22, 23, 24})

# Expeditions that find ships add this share of what you took with you.
# The research only wrote down three of them (colony ship and heavy fighter
# 50 %, cargo ships 10 %); the rest are filled in by size.
EXPEDITION_SHIP_GAIN: dict[int, float] = {
    202: 0.1, 203: 0.1, 204: 0.3, 205: 0.5, 206: 0.3, 207: 0.2,
    208: 0.5, 209: 0.3, 210: 0.5, 211: 0.1, 213: 0.1, 215: 0.1,
}

# The 11 officers Xnova finished. Bunker, Destroyer, Raider and Emperor are
# left out: they only open things that do not exist in its data.
OFFICERS: dict[int, Officer] = {o.id: o for o in [
    Officer(601, 20),
    Officer(602, 20),
    Officer(603, 10, {601: 5}),
    Officer(604, 10, {602: 5}),
    Officer(605, 3, {601: 10, 603: 2}),
    Officer(606, 3, {601: 10, 603: 2}),
    Officer(607, 2, {605: 1}),
    Officer(608, 2, {606: 1}),
    Officer(610, 2, {602: 10, 604: 5}),
    Officer(611, 2, {602: 10, 604: 5}),
    Officer(613, 3, {611: 1}),
]}
