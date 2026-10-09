"""Pure rules for espionage and expeditions (Xnova)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..data.elements import ELEMENTS, EXPEDITION_SHIP_GAIN

# What a spy report shows, by depth (Xnova thresholds).
SPY_RESOURCES = 1
SPY_FLEET = 2
SPY_DEFENSE = 3
SPY_BUILDINGS = 5
SPY_RESEARCH = 7


def spy_depth(probes: int, attacker_level: int, defender_level: int) -> int:
    """Xnova: probes plus (or minus) the square of the espionage level difference.

    When both levels are equal Xnova used the attacker's level instead of the
    probe count; here it is the probe count, like the other two cases.
    """
    diff = attacker_level - defender_level
    if diff > 0:
        return probes + diff * diff
    if diff < 0:
        return probes - diff * diff
    return probes


def spy_detected(defender_ships: int, probes: int, rng: random.Random) -> tuple[bool, int]:
    """Xnova counter-espionage. Returns (probes destroyed, chance shown in the report)."""
    force = min(100, int(defender_ships * probes / 4))
    if force <= 0:
        return False, 0
    target_roll = rng.randint(0, force)
    spy_roll = rng.randint(0, 100)
    return target_roll >= spy_roll, force


@dataclass
class ExpeditionOutcome:
    kind: str  # "lost", "nothing", "resources", "ships"
    lost_share: float = 0.0
    found: tuple[int, int, int] = (0, 0, 0)
    ships_found: dict[int, int] = field(default_factory=dict)


def expedition(ships: dict[int, int], rng: random.Random) -> ExpeditionOutcome:
    """Xnova expedition: a number from 0 to 10, all equally likely.

    0-2: lose 34 %, 67 % or 100 % of the fleet; 3 and 7: nothing;
    4-6: resources; 8-10: ships. The free cargo is counted with one ship of
    each type, as in Xnova: it keeps the finds bounded.
    """
    roll = rng.randint(0, 10)
    if roll < 3:
        return ExpeditionOutcome("lost", lost_share=((roll + 1) * 33 + 1) / 100)
    if roll in (3, 7):
        return ExpeditionOutcome("nothing")
    if roll < 7:
        capacity = sum(ELEMENTS[eid].cargo for eid, n in ships.items() if n > 0)
        if capacity <= 5000:
            return ExpeditionOutcome("nothing")
        goods = rng.randint(capacity - 5000, capacity)
        return ExpeditionOutcome("resources", found=(goods // 2, goods // 4, goods // 6))
    found = {}
    for eid, n in ships.items():
        gain = round(n * EXPEDITION_SHIP_GAIN.get(eid, 0))
        if gain > 0:
            found[eid] = gain
    if not found:
        return ExpeditionOutcome("nothing")
    return ExpeditionOutcome("ships", ships_found=found)
