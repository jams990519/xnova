import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from xnova_bot.config import Settings  # noqa: E402
from xnova_bot.db import Database  # noqa: E402
from xnova_bot.game import Game  # noqa: E402


class Clock:
    def __init__(self, start: float = 1_800_000_000.0):
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def settings():
    # Newbie protection off by default; test_noob_protection turns it on.
    return Settings(galaxies=2, systems=20, economy_speed=1.0, fleet_speed=1.0, noob_points_limit=0)


@pytest.fixture
def game(clock, settings):
    db = Database(":memory:")
    g = Game(db, settings, clock=clock, rng=random.Random(42))
    yield g
    db.close()


def give(game: Game, planet_id: int, metal=0, crystal=0, deuterium=0, buildings=None, ships=None, defense=None):
    """Test helper: put resources, levels or units on a planet."""
    with game.db.conn:
        planet = game.db.get_planet(planet_id)
        game.refresh(planet, game.now())
        planet.metal += metal
        planet.crystal += crystal
        planet.deuterium += deuterium
        planet.buildings.update(buildings or {})
        for eid, n in (ships or {}).items():
            planet.ships[eid] = planet.ships.get(eid, 0) + n
        for eid, n in (defense or {}).items():
            planet.defense[eid] = planet.defense.get(eid, 0) + n
        game.db.save_planet(planet)
    return planet


def research(game: Game, player_id: int, **levels):
    with game.db.conn:
        player = game.db.get_player(player_id)
        for key, lvl in levels.items():
            player.research[int(key.lstrip("t"))] = lvl
        game.db.save_player(player)
    return player
