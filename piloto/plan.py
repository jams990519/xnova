"""Decisions, without touching Telegram: what to build or research next, and which farm to raid now."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DAY = 24 * 3600


@dataclass(frozen=True)
class Goal:
    name: str
    level: int


def parse_plan(items: list[str]) -> list[Goal]:
    """['Mina de metal 4', 'Planta solar 2'] -> goals. The last number of each item is the level to reach."""
    goals = []
    for item in items:
        m = re.match(r"^\s*(.*?)\s+(\d+)\s*$", item)
        if not m:
            raise ValueError(f"En el plan, «{item}» no termina con el nivel (por ejemplo «Mina de metal 4»).")
        goals.append(Goal(m.group(1), int(m.group(2))))
    return goals


def next_goal(plan: list[Goal], levels: dict[str, int], energy: int | None = None,
              power_plant: str = "") -> Goal | None:
    """The first goal of the plan not reached yet. Goals whose name is not on the screen are skipped (not
    unlocked yet). With negative energy the mines produce less, so the power plant goes first."""
    if energy is not None and energy < 0 and power_plant in levels:
        return Goal(power_plant, levels[power_plant] + 1)
    for goal in plan:
        if goal.name in levels and levels[goal.name] < goal.level:
            return goal
    return None


# --- farming --------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Target:
    fleet: str  # name of the fleet saved in the game (Flotas → Mis flotas)
    coords: str  # planet it attacks, to count the attacks per planet


@dataclass
class RaidBook:
    """When each planet was attacked, and the ones the game refused (shield, protection…) until when."""
    attacks: dict[str, list[float]] = field(default_factory=dict)
    blocked: dict[str, dict] = field(default_factory=dict)  # coords -> {"until": ts, "why": text}

    def last_day(self, coords: str, now: float) -> list[float]:
        return [t for t in self.attacks.get(coords, []) if now - t < DAY]

    def record(self, coords: str, now: float) -> None:
        self.attacks[coords] = [*self.last_day(coords, now), now]

    def block(self, coords: str, now: float, why: str, hours: float = 24) -> None:
        self.blocked[coords] = {"until": now + hours * 3600, "why": why}

    def is_blocked(self, coords: str, now: float) -> bool:
        b = self.blocked.get(coords)
        return b is not None and b["until"] > now

    def to_json(self) -> dict:
        return {"attacks": self.attacks, "blocked": self.blocked}

    @classmethod
    def from_json(cls, data: dict) -> "RaidBook":
        return cls(dict(data.get("attacks", {})), dict(data.get("blocked", {})))


def due_targets(targets: list[Target], book: RaidBook, now: float, max_per_day: int) -> list[Target]:
    """Farms that can be raided now: under the daily limit and not refused by the game, the one attacked
    longest ago first."""
    ok = [t for t in targets if len(book.last_day(t.coords, now)) < max_per_day and not book.is_blocked(t.coords, now)]
    return sorted(ok, key=lambda t: max(book.last_day(t.coords, now), default=0))
