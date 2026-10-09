"""Battle simulation, classic OGame style.

Every unit fires every round at a random enemy unit. A shot below 1 % of the
target's shield is lost; shields absorb damage first and recharge each round;
a unit with less than 70 % hull may explode; rapid fire gives a chance of
firing again. Xnova used a cruder group model with known bugs (§16 of the
research), so the classic rules are used instead.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from math import ceil

from ..data.elements import ELEMENTS

ROUNDS = 6
DEFAULT_MAX_UNITS = 20_000  # above this the battle is simulated on a scaled-down copy


@dataclass(frozen=True)
class Tech:
    weapons: int = 0
    shielding: int = 0
    armour: int = 0
    admiral: int = 0  # Xnova officer: +5 % attack, shield and hull per level

    @property
    def attack_mult(self) -> float:
        return 1 + 0.1 * self.weapons + 0.05 * self.admiral

    @property
    def shield_mult(self) -> float:
        return 1 + 0.1 * self.shielding + 0.05 * self.admiral

    @property
    def hull_mult(self) -> float:
        return 1 + 0.1 * self.armour + 0.05 * self.admiral


@dataclass
class RoundStats:
    attacker_units: int
    defender_units: int
    attacker_shots: int = 0
    attacker_damage: float = 0.0
    defender_shots: int = 0
    defender_damage: float = 0.0
    absorbed_by_attacker: float = 0.0
    absorbed_by_defender: float = 0.0


@dataclass
class BattleResult:
    winner: str  # "attacker", "defender" or "draw"
    rounds: list[RoundStats]
    attacker_start: dict[int, int]
    defender_start: dict[int, int]
    attacker_left: dict[int, int]
    defender_left: dict[int, int]
    scaled: bool = False

    @property
    def attacker_lost(self) -> dict[int, int]:
        return _diff(self.attacker_start, self.attacker_left)

    @property
    def defender_lost(self) -> dict[int, int]:
        return _diff(self.defender_start, self.defender_left)


def _diff(start: dict[int, int], left: dict[int, int]) -> dict[int, int]:
    return {k: n - left.get(k, 0) for k, n in start.items() if n - left.get(k, 0) > 0}


@dataclass
class _Side:
    types: list[int]
    hull: list[float]
    shield: list[float]
    max_hull: dict[int, float]
    max_shield: dict[int, float]
    attack: dict[int, float]
    stats: dict = field(default_factory=dict)

    @classmethod
    def build(cls, units: dict[int, int], tech: Tech) -> "_Side":
        types: list[int] = []
        max_hull, max_shield, attack = {}, {}, {}
        for eid, n in units.items():
            if n <= 0:
                continue
            element = ELEMENTS[eid]
            max_hull[eid] = element.hull * tech.hull_mult
            max_shield[eid] = element.shield * tech.shield_mult
            attack[eid] = element.attack * tech.attack_mult
            types.extend([eid] * n)
        hull = [max_hull[t] for t in types]
        return cls(types, hull, [0.0] * len(types), max_hull, max_shield, attack)

    def alive(self) -> int:
        return len(self.types)

    def counts(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for t in self.types:
            out[t] = out.get(t, 0) + 1
        return out


def _fire(shooter: _Side, target: _Side, rng: random.Random) -> tuple[int, float, float]:
    """All units of ``shooter`` fire once (plus rapid fire). Returns shots, damage, absorbed."""
    shots = 0
    damage = 0.0
    absorbed = 0.0
    n_targets = len(target.types)
    if n_targets == 0:
        return 0, 0.0, 0.0
    for stype in shooter.types:
        power = shooter.attack[stype]
        if power <= 0:
            continue
        rapid = ELEMENTS[stype].rapidfire
        while True:
            i = rng.randrange(n_targets)
            ttype = target.types[i]
            shots += 1
            if target.hull[i] > 0 and power >= 0.01 * target.max_shield[ttype]:
                shield = target.shield[i]
                if power <= shield:
                    target.shield[i] = shield - power
                    absorbed += power
                else:
                    absorbed += shield
                    target.shield[i] = 0.0
                    target.hull[i] -= power - shield
                    damage += power - shield
                    max_hull = target.max_hull[ttype]
                    if 0 < target.hull[i] < 0.7 * max_hull and rng.random() < 1 - target.hull[i] / max_hull:
                        target.hull[i] = 0.0
            rf = rapid.get(ttype, 0)
            if rf <= 1 or rng.random() >= 1 - 1 / rf:
                break
    return shots, damage, absorbed


def _cleanup(side: _Side) -> None:
    keep = [i for i, h in enumerate(side.hull) if h > 0]
    side.types = [side.types[i] for i in keep]
    side.hull = [side.hull[i] for i in keep]
    side.shield = [0.0] * len(keep)


def _scale(units: dict[int, int], k: float) -> dict[int, int]:
    return {eid: max(1, round(n / k)) for eid, n in units.items() if n > 0}


def simulate(attacker: dict[int, int], attacker_tech: Tech, defender: dict[int, int], defender_tech: Tech,
             rng: random.Random | None = None, max_units: int = DEFAULT_MAX_UNITS) -> BattleResult:
    rng = rng or random.Random()
    attacker = {k: v for k, v in attacker.items() if v > 0}
    defender = {k: v for k, v in defender.items() if v > 0}
    total = sum(attacker.values()) + sum(defender.values())
    scaled = total > max_units
    if scaled:
        k = total / max_units
        sim_att, sim_def = _scale(attacker, k), _scale(defender, k)
    else:
        sim_att, sim_def = attacker, defender

    att = _Side.build(sim_att, attacker_tech)
    dfn = _Side.build(sim_def, defender_tech)
    rounds: list[RoundStats] = []
    for _ in range(ROUNDS):
        if not att.alive() or not dfn.alive():
            break
        stats = RoundStats(att.alive(), dfn.alive())
        for side in (att, dfn):
            side.shield = [side.max_shield[t] for t in side.types]
        stats.attacker_shots, stats.attacker_damage, stats.absorbed_by_defender = _fire(att, dfn, rng)
        stats.defender_shots, stats.defender_damage, stats.absorbed_by_attacker = _fire(dfn, att, rng)
        _cleanup(att)
        _cleanup(dfn)
        rounds.append(stats)

    if att.alive() and not dfn.alive():
        winner = "attacker"
    elif dfn.alive() and not att.alive():
        winner = "defender"
    else:
        winner = "draw"

    att_left, def_left = att.counts(), dfn.counts()
    if scaled:
        att_left = {e: min(attacker[e], round(attacker[e] * att_left.get(e, 0) / sim_att[e])) for e in attacker}
        def_left = {e: min(defender[e], round(defender[e] * def_left.get(e, 0) / sim_def[e])) for e in defender}
        att_left = {k: v for k, v in att_left.items() if v > 0}
        def_left = {k: v for k, v in def_left.items() if v > 0}
    return BattleResult(winner, rounds, attacker, defender, att_left, def_left, scaled)


# --- After the battle -------------------------------------------------------

def debris(lost_units: dict[int, int], ship_share: float, defense_share: float) -> tuple[int, int]:
    """Metal and crystal left floating. Deuterium never becomes debris."""
    metal = crystal = 0.0
    for eid, n in lost_units.items():
        element = ELEMENTS[eid]
        share = defense_share if element.kind == "defense" else ship_share
        metal += element.cost[0] * n * share
        crystal += element.cost[1] * n * share
    return int(metal), int(crystal)


def rebuild_defense(lost: dict[int, int], rng: random.Random, chance: float = 0.7) -> dict[int, int]:
    """Each destroyed defense unit comes back with ``chance`` (classic OGame: 70 %)."""
    rebuilt: dict[int, int] = {}
    for eid, n in lost.items():
        if ELEMENTS[eid].kind != "defense" or n <= 0:
            continue
        if n <= 1000:
            back = sum(1 for _ in range(n) if rng.random() < chance)
        else:
            back = round(n * chance + rng.gauss(0, (n * chance * (1 - chance)) ** 0.5))
            back = max(0, min(n, back))
        if back:
            rebuilt[eid] = back
    return rebuilt


def moon_chance(debris_total: int, max_chance: int = 20) -> int:
    """Percent chance of a moon: 1 % per 100,000 debris, at most 20 %."""
    if debris_total < 100_000:
        return 0
    return min(max_chance, debris_total // 100_000)


def plunder(capacity: float, available: tuple[float, float, float], share: float = 0.5) -> tuple[int, int, int]:
    """Classic OGame loot: up to half of each resource, filled in metal/crystal/deuterium order.

    Xnova stopped after the first pass; OGame fills the space left with a second pass.
    """
    m_av, c_av, d_av = (max(0.0, x) * share for x in available)
    cap = max(0.0, capacity)
    metal = min(cap / 3, m_av)
    cap -= metal
    crystal = min(cap / 2, c_av)
    cap -= crystal
    deut = min(cap, d_av)
    cap -= deut
    extra = min(cap / 2, m_av - metal)
    metal += extra
    cap -= extra
    extra = min(cap, c_av - crystal)
    crystal += extra
    return int(metal), int(crystal), int(deut)


def ships_needed_for(loot: float, cargo_per_ship: int) -> int:
    return max(1, ceil(loot / cargo_per_ship)) if loot > 0 else 0
