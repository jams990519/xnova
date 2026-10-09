"""Game service: every rule that touches stored state goes through here.

The Telegram layer only calls these methods and shows what they return.
Time-based events (buildings, research, fleets) are processed in order by
``tick``; resources are computed lazily from ``last_update``.
"""
from __future__ import annotations

import functools
import random
import re
import secrets
import time
from dataclasses import dataclass, field
from math import floor

from . import reports
from .config import Settings
from .data.elements import (BUILDING, DEFENSE, ELEMENTS, MINER_XP_BUILDINGS, MISSILE, OFFICERS, ONE_PER_PLANET,
                            RESEARCH, SHIP)
from .db import MOON, PLANET, Database, Fleet, Planet, Player
from .engine import combat, formulas
from .engine import missions as rules
from .texts import (ATTACK, COLONIZE, DEPLOY, EXPEDITION, MISSIONS, NAMES, OFFICER_NAMES, RECYCLE, SPY, TRANSPORT,
                    duration, num)

DAY = 86_400
EXPEDITION_POSITION = 16
NAME_RE = re.compile(r"^[\w áéíóúÁÉÍÓÚñÑüÜ.\-]{3,20}$")
TAG_RE = re.compile(r"^[A-Za-z0-9]{2,8}$")
MAX_EVENTS_PER_TICK = 5000

# Planet size by position (Xnova RandomMin / RandomMax, before the random extra).
FIELDS_MIN = (40, 50, 55, 100, 95, 80, 115, 120, 125, 75, 80, 85, 60, 40, 50)
FIELDS_MAX = (90, 95, 95, 240, 240, 230, 180, 180, 190, 125, 120, 130, 160, 300, 150)
# Minimum temperature range by position group (max = min + 40).
TEMPS = ((0, 100), (-25, 75), (-50, 50), (-75, 25), (-100, 10))


class GameError(Exception):
    """A rule stopped the action. The message is shown to the player as is."""


@dataclass
class Notice:
    player_id: int
    text: str
    buttons: list[list[tuple[str, str]]] = field(default_factory=list)


@dataclass
class FleetPlan:
    ships: dict[int, int]
    origin: Planet
    target: tuple[int, int, int]
    target_kind: int
    mission: int
    speed: int
    distance: int
    seconds: float
    fuel: int
    capacity: int
    cargo: tuple[int, int, int]
    target_planet: Planet | None


def transactional(method):
    @functools.wraps(method)
    def wrapper(self: "Game", *args, **kwargs):
        with self.db.conn:
            return method(self, *args, **kwargs)
    return wrapper


class Game:
    def __init__(self, db: Database, settings: Settings, clock=time.time, rng: random.Random | None = None):
        self.db = db
        self.s = settings
        self.clock = clock
        self.rng = rng or random.Random()
        self._pending: list[Notice] = []

    def now(self) -> float:
        return self.clock()

    # ======================================================================
    # Players
    # ======================================================================

    def player(self, player_id: int) -> Player | None:
        return self.db.get_player(player_id)

    def require_player(self, player_id: int) -> Player:
        player = self.db.get_player(player_id)
        if not player:
            raise GameError("Primero crea tu cuenta con /start.")
        return player

    @transactional
    def register(self, player_id: int, chat_id: int, name: str) -> tuple[Player, Planet]:
        name = " ".join(name.split())
        if self.db.get_player(player_id):
            raise GameError("Ya tienes una cuenta.")
        if not NAME_RE.match(name):
            raise GameError("El nombre debe tener de 3 a 20 letras, números, espacios, puntos o guiones.")
        if self.db.player_by_name(name):
            raise GameError("Ese nombre ya está en uso. Elige otro.")
        t = self.now()
        player = Player(id=player_id, chat_id=chat_id, name=name, created_at=t, last_active=t)
        self.db.insert_player(player)
        galaxy, system, position = self._free_home_slot()
        planet = self._new_planet(player_id, "Planeta principal", galaxy, system, position, t, home=True)
        planet.metal, planet.crystal = 500.0, 500.0
        self.db.save_planet(planet)
        player.current_planet = planet.id
        self.db.save_player(player)
        return player, planet

    def _free_home_slot(self) -> tuple[int, int, int]:
        """Fill systems in order, up to 3 home planets each, at a random free position 4-12."""
        for galaxy in range(1, self.s.galaxies + 1):
            for system in range(1, self.s.systems + 1):
                if self.db.count_planets_in_system(galaxy, system) >= 3:
                    continue
                taken = {p.position for p in self.db.planets_in_system(galaxy, system)}
                free = [p for p in range(4, 13) if p not in taken]
                if free:
                    return galaxy, system, self.rng.choice(free)
        for galaxy in range(1, self.s.galaxies + 1):  # universe crowded: any free slot
            for system in range(1, self.s.systems + 1):
                taken = {p.position for p in self.db.planets_in_system(galaxy, system)}
                free = [p for p in range(1, 16) if p not in taken]
                if free:
                    return galaxy, system, self.rng.choice(free)
        raise GameError("El universo está lleno. Avisa al administrador.")

    def _new_planet(self, owner_id: int, name: str, galaxy: int, system: int, position: int, t: float,
                    home: bool = False) -> Planet:
        lo, hi = TEMPS[(position - 1) // 3]
        temp_min = self.rng.randint(lo, hi)
        if home:
            fields = formulas.HOME_PLANET_FIELDS
        else:
            fields = self.rng.randint(FIELDS_MIN[position - 1], FIELDS_MAX[position - 1])
            fields = max(30, fields + self.rng.randint(0, 110) - self.rng.randint(0, 100))
        planet = Planet(id=0, owner_id=owner_id, name=name, galaxy=galaxy, system=system, position=position,
                        kind=PLANET, base_fields=fields, temp_min=temp_min, temp_max=temp_min + 40,
                        metal=0.0, crystal=0.0, deuterium=0.0, last_update=t, created_at=t, shipyard_ts=t)
        self.db.insert_planet(planet)
        return planet

    def touch(self, player: Player) -> None:
        player.last_active = self.now()

    def mark_active(self, player_id: int) -> None:
        """Any message or button counts as activity (and unblocks a player who came back)."""
        with self.db.conn:
            self.db.conn.execute("UPDATE players SET last_active=?, blocked=0 WHERE id=?", (self.now(), player_id))

    def is_inactive(self, player: Player, days: int | None = None) -> bool:
        days = self.s.inactive_days if days is None else days
        return player.last_active < self.now() - days * DAY

    # ======================================================================
    # Planets, resources and the shipyard queue
    # ======================================================================

    def rates(self, planet: Planet, owner: Player) -> dict[str, float]:
        if planet.is_moon:
            return {"metal": 0.0, "crystal": 0.0, "deuterium": 0.0, "energy_produced": 0.0,
                    "energy_needed": 0.0, "factor": 1.0}
        return formulas.production(planet.buildings, planet.production, planet.ships.get(212, 0), planet.temp_max,
                                   self.s.economy_speed, owner.officer(601), owner.officer(603))

    def storage(self, planet: Planet, owner: Player) -> tuple[float, float, float]:
        storer = owner.officer(607)
        return tuple(formulas.storage_capacity(planet.level(b), storer) for b in (22, 23, 24))  # type: ignore

    def refresh(self, planet: Planet, t: float, owner: Player | None = None) -> None:
        """Bring resources and the shipyard queue up to time ``t`` (in memory)."""
        owner = owner or self.db.get_player(planet.owner_id)
        dt = t - planet.last_update
        if dt > 0 and owner and not owner.vacation and not planet.is_moon:
            rates = self.rates(planet, owner)
            caps = self.storage(planet, owner)
            for i, key in enumerate(("metal", "crystal", "deuterium")):
                current = getattr(planet, key)
                gain = rates[key] * dt / 3600
                if gain >= 0:
                    if current < caps[i]:
                        current = min(caps[i], current + gain)
                else:
                    current = max(0.0, current + gain)
                setattr(planet, key, current)
        planet.last_update = max(planet.last_update, t)
        self._advance_shipyard(planet, t)

    def _advance_shipyard(self, planet: Planet, t: float) -> None:
        start = planet.shipyard_ts or t
        available = t - start
        queue = planet.shipyard
        while queue and available > 0:
            item = queue[0]
            unit = item["unit"]
            left = item["count"] - item["done"]
            need = unit - item.get("progress", 0.0)
            if available < need:
                item["progress"] = item.get("progress", 0.0) + available
                available = 0
                break
            available -= need
            done = 1 + min(left - 1, int(available // unit))
            available -= (done - 1) * unit
            item["done"] += done
            item["progress"] = 0.0
            target = planet.ships if ELEMENTS[item["id"]].kind == SHIP else planet.defense
            target[item["id"]] = target.get(item["id"], 0) + done
            if item["done"] >= item["count"]:
                queue.pop(0)
        planet.shipyard_ts = t

    def planets(self, player: Player, t: float | None = None) -> list[Planet]:
        t = self.now() if t is None else t
        out = self.db.planets_of(player.id)
        for p in out:
            self.refresh(p, t, player)
            self.db.save_planet(p)
        return out

    @transactional
    def view_planet(self, player_id: int, planet_id: int | None = None) -> tuple[Player, Planet]:
        self._tick_unlocked()  # finish anything already due before showing it
        player = self.require_player(player_id)
        planet = self._own_planet(player, planet_id or player.current_planet)
        self.touch(player)
        self.db.save_player(player)
        return player, planet

    def _own_planet(self, player: Player, planet_id: int | None) -> Planet:
        planet = self.db.get_planet(planet_id) if planet_id else None
        if not planet or planet.owner_id != player.id:
            planets = self.db.planets_of(player.id)
            if not planets:
                raise GameError("No tienes planetas.")
            planet = planets[0]
            player.current_planet = planet.id
            self.db.save_player(player)
        self.refresh(planet, self.now(), player)
        self.db.save_planet(planet)
        return planet

    @transactional
    def select_planet(self, player_id: int, planet_id: int) -> Planet:
        player = self.require_player(player_id)
        planet = self.db.get_planet(planet_id)
        if not planet or planet.owner_id != player.id:
            raise GameError("Ese planeta no es tuyo.")
        player.current_planet = planet.id
        self.db.save_player(player)
        self.refresh(planet, self.now(), player)
        self.db.save_planet(planet)
        return planet

    @transactional
    def rename_planet(self, player_id: int, planet_id: int, name: str) -> Planet:
        player = self.require_player(player_id)
        planet = self._own_planet(player, planet_id)
        name = " ".join(name.split())
        if not NAME_RE.match(name):
            raise GameError("El nombre debe tener de 3 a 20 letras, números, espacios, puntos o guiones.")
        planet.name = name
        self.db.save_planet(planet)
        return planet

    @transactional
    def set_production(self, player_id: int, planet_id: int, element_id: int, percent: int) -> Planet:
        player = self.require_player(player_id)
        planet = self._own_planet(player, planet_id)
        if element_id not in (1, 2, 3, 4, 12, 212) or percent not in range(0, 101, 10):
            raise GameError("Valor no válido.")
        planet.production[element_id] = percent
        self.db.save_planet(planet)
        return planet

    def fields(self, planet: Planet) -> tuple[int, int]:
        used = formulas.used_fields(planet.buildings) + (1 if planet.build_id else 0)
        return used, formulas.max_fields(planet.base_fields, planet.buildings, planet.is_moon)

    # ======================================================================
    # Requirements, buildings and research
    # ======================================================================

    def missing(self, player: Player, planet: Planet, element_id: int) -> dict[int, int]:
        out = {}
        for req, level in ELEMENTS[element_id].requires.items():
            have = player.tech(req) if ELEMENTS[req].kind == RESEARCH else planet.level(req)
            if have < level:
                out[req] = level
        return out

    def can_build_here(self, planet: Planet, element_id: int) -> bool:
        element = ELEMENTS[element_id]
        return element.moon if planet.is_moon else element.planet

    def building_options(self, player: Player, planet: Planet) -> list[dict]:
        out = []
        for element in ELEMENTS.values():
            if element.kind != BUILDING or not self.can_build_here(planet, element.id):
                continue
            level = planet.level(element.id)
            cost = formulas.level_cost(element.id, level + 1)
            seconds = formulas.building_seconds(cost, planet.level(14), planet.level(15), self.s.economy_speed,
                                                player.officer(605))
            out.append({"id": element.id, "level": level, "next": level + 1, "cost": cost,
                        "energy": formulas.level_energy_cost(element.id, level + 1), "seconds": seconds,
                        "missing": self.missing(player, planet, element.id),
                        "affordable": self._affordable(planet, cost)})
        return out

    @staticmethod
    def _affordable(planet: Planet, cost) -> bool:
        return planet.metal >= cost[0] and planet.crystal >= cost[1] and planet.deuterium >= cost[2]

    @staticmethod
    def _pay(planet: Planet, cost) -> None:
        planet.metal -= cost[0]
        planet.crystal -= cost[1]
        planet.deuterium -= cost[2]

    @staticmethod
    def _refund(planet: Planet, cost, share: float = 1.0) -> None:
        planet.metal += cost[0] * share
        planet.crystal += cost[1] * share
        planet.deuterium += cost[2] * share

    def _check_active(self, player: Player) -> None:
        if player.vacation:
            raise GameError("Estás en modo vacaciones. Desactívalo en ⚙️ Ajustes para jugar.")

    @transactional
    def start_build(self, player_id: int, planet_id: int, element_id: int) -> Planet:
        self._tick_unlocked()
        player = self.require_player(player_id)
        self._check_active(player)
        planet = self._own_planet(player, planet_id)
        element = ELEMENTS.get(element_id)
        if not element or element.kind != BUILDING or not self.can_build_here(planet, element_id):
            raise GameError("Ese edificio no se puede construir aquí.")
        if planet.build_id:
            raise GameError(f"Ya se está construyendo {NAMES[planet.build_id]}. Espera a que termine.")
        if self.missing(player, planet, element_id):
            raise GameError("Todavía no cumples los requisitos.")
        used, total = self.fields(planet)
        if used >= total:
            raise GameError("No quedan campos libres en este planeta.")
        if element_id in (15, 21) and planet.shipyard:
            raise GameError("No se puede mejorar el hangar ni los nanobots mientras el hangar trabaja.")
        if element_id == 31 and player.research_id and player.research_planet == planet.id:
            raise GameError("No se puede mejorar el laboratorio mientras investiga.")
        level = planet.level(element_id) + 1
        cost = formulas.level_cost(element_id, level)
        energy = formulas.level_energy_cost(element_id, level)
        if energy:
            rates = self.rates(planet, player)
            if rates["energy_produced"] - rates["energy_needed"] < energy:
                raise GameError(f"Necesitas {num(energy)} de energía libre.")
        if not self._affordable(planet, cost):
            raise GameError("No tienes recursos suficientes.")
        self._pay(planet, cost)
        t = self.now()
        planet.build_id, planet.build_level = element_id, level
        planet.build_start = t
        planet.build_end = t + formulas.building_seconds(cost, planet.level(14), planet.level(15),
                                                         self.s.economy_speed, player.officer(605))
        self.db.save_planet(planet)
        self.touch(player)
        self.db.save_player(player)
        return planet

    @transactional
    def cancel_build(self, player_id: int, planet_id: int) -> Planet:
        player = self.require_player(player_id)
        planet = self._own_planet(player, planet_id)
        if not planet.build_id:
            raise GameError("No hay nada en construcción.")
        self._refund(planet, formulas.level_cost(planet.build_id, planet.build_level))
        planet.build_id = planet.build_level = planet.build_start = planet.build_end = None
        self.db.save_planet(planet)
        return planet

    def lab_level(self, player: Player, planet: Planet) -> int:
        level = planet.level(31)
        network = player.tech(123)
        if network:
            others = sorted((p.level(31) for p in self.db.planets_of(player.id) if p.id != planet.id), reverse=True)
            level += sum(others[:network])
        return level

    def research_options(self, player: Player, planet: Planet) -> list[dict]:
        lab = self.lab_level(player, planet)
        out = []
        for element in ELEMENTS.values():
            if element.kind != RESEARCH:
                continue
            level = player.tech(element.id)
            cost = formulas.level_cost(element.id, level + 1)
            out.append({"id": element.id, "level": level, "next": level + 1, "cost": cost,
                        "energy": formulas.level_energy_cost(element.id, level + 1),
                        "seconds": formulas.research_seconds(cost, lab, self.s.economy_speed, player.officer(606)),
                        "missing": self.missing(player, planet, element.id),
                        "affordable": self._affordable(planet, cost)})
        return out

    @transactional
    def start_research(self, player_id: int, planet_id: int, element_id: int) -> Player:
        self._tick_unlocked()
        player = self.require_player(player_id)
        self._check_active(player)
        planet = self._own_planet(player, planet_id)
        element = ELEMENTS.get(element_id)
        if not element or element.kind != RESEARCH:
            raise GameError("Esa investigación no existe.")
        if planet.is_moon or planet.level(31) < 1:
            raise GameError("Necesitas un laboratorio en este planeta.")
        if player.research_id:
            raise GameError(f"Ya se está investigando {NAMES[player.research_id]}.")
        if planet.build_id == 31:
            raise GameError("El laboratorio se está mejorando.")
        if self.missing(player, planet, element_id):
            raise GameError("Todavía no cumples los requisitos.")
        level = player.tech(element_id) + 1
        cost = formulas.level_cost(element_id, level)
        energy = formulas.level_energy_cost(element_id, level)
        if energy and self.rates(planet, player)["energy_produced"] < energy:
            raise GameError(f"Este planeta debe producir {num(energy)} de energía.")
        if not self._affordable(planet, cost):
            raise GameError("No tienes recursos suficientes.")
        self._pay(planet, cost)
        t = self.now()
        player.research_id, player.research_level, player.research_planet = element_id, level, planet.id
        player.research_start = t
        player.research_end = t + formulas.research_seconds(cost, self.lab_level(player, planet),
                                                            self.s.economy_speed, player.officer(606))
        self.db.save_planet(planet)
        self.touch(player)
        self.db.save_player(player)
        return player

    @transactional
    def cancel_research(self, player_id: int) -> Player:
        player = self.require_player(player_id)
        if not player.research_id:
            raise GameError("No hay ninguna investigación en curso.")
        planet = self.db.get_planet(player.research_planet) if player.research_planet else None
        if planet:
            self.refresh(planet, self.now(), player)
            self._refund(planet, formulas.level_cost(player.research_id, player.research_level))
            self.db.save_planet(planet)
        player.research_id = player.research_level = player.research_planet = None
        player.research_start = player.research_end = None
        self.db.save_player(player)
        return player

    # ======================================================================
    # Shipyard: ships, defenses and missiles
    # ======================================================================

    def missile_slots(self, planet: Planet) -> tuple[int, int]:
        """(used, total) silo slots. An interplanetary missile takes 2."""
        queued = {}
        for item in planet.shipyard:
            queued[item["id"]] = queued.get(item["id"], 0) + item["count"] - item["done"]
        used = (planet.defense.get(502, 0) + queued.get(502, 0)
                + 2 * (planet.defense.get(503, 0) + queued.get(503, 0)))
        return used, 10 * planet.level(44)

    def max_units(self, planet: Planet, element_id: int) -> int:
        cost = ELEMENTS[element_id].cost
        limits = [int(have // c) for have, c in zip((planet.metal, planet.crystal, planet.deuterium), cost) if c]
        count = min(limits) if limits else 0
        if element_id in ONE_PER_PLANET:
            queued = any(item["id"] == element_id for item in planet.shipyard)
            count = 0 if planet.defense.get(element_id, 0) or queued else min(count, 1)
        if ELEMENTS[element_id].kind == MISSILE:
            used, total = self.missile_slots(planet)
            count = min(count, (total - used) // (2 if element_id == 503 else 1))
        return max(0, count)

    def unit_options(self, player: Player, planet: Planet, kind: str) -> list[dict]:
        kinds = (DEFENSE,) if kind == DEFENSE else (SHIP,)  # missiles: not launchable yet, hidden
        out = []
        for element in ELEMENTS.values():
            if element.kind not in kinds:
                continue
            have = (planet.ships if element.kind == SHIP else planet.defense).get(element.id, 0)
            out.append({"id": element.id, "have": have, "cost": element.cost,
                        "seconds": self.unit_time(player, planet, element.id),
                        "missing": self.missing(player, planet, element.id),
                        "max": self.max_units(planet, element.id)})
        return out

    def unit_time(self, player: Player, planet: Planet, element_id: int) -> float:
        return formulas.unit_seconds(element_id, planet.level(21), planet.level(15), self.s.economy_speed,
                                     player.officer(604), player.officer(608),
                                     ELEMENTS[element_id].kind != SHIP)

    @transactional
    def order_units(self, player_id: int, planet_id: int, element_id: int, count: int) -> tuple[Planet, int]:
        self._tick_unlocked()
        player = self.require_player(player_id)
        self._check_active(player)
        planet = self._own_planet(player, planet_id)
        element = ELEMENTS.get(element_id)
        if not element or element.kind not in (SHIP, DEFENSE):
            raise GameError("Esa unidad no existe." if not element or element.kind != MISSILE
                            else "Los misiles llegan en una próxima versión.")
        if planet.level(21) < 1:
            raise GameError("Necesitas un hangar en este planeta.")
        if planet.build_id in (15, 21):
            raise GameError("El hangar no puede trabajar mientras se mejora.")
        if self.missing(player, planet, element_id):
            raise GameError("Todavía no cumples los requisitos.")
        if len(planet.shipyard) >= 10:
            raise GameError("La cola del hangar está llena (10 órdenes).")
        count = min(int(count), self.max_units(planet, element_id))
        if count <= 0:
            raise GameError("No te alcanza para ninguna unidad." if element_id not in ONE_PER_PLANET
                            else "Ya tienes esa cúpula o no te alcanza.")
        self._pay(planet, formulas.units_cost(element_id, count))
        if not planet.shipyard:
            planet.shipyard_ts = self.now()
        planet.shipyard.append({"id": element_id, "count": count, "done": 0, "progress": 0.0,
                                "unit": self.unit_time(player, planet, element_id)})
        self.db.save_planet(planet)
        self.touch(player)
        self.db.save_player(player)
        return planet, count

    # ======================================================================
    # Fleets
    # ======================================================================

    def fleet_slots(self, player: Player) -> tuple[int, int]:
        used = sum(1 for f in self.db.fleets_of(player.id))
        return used, formulas.fleet_slots(player.tech(108), player.officer(611))

    def target_planet(self, target: tuple[int, int, int], kind: int) -> Planet | None:
        return self.db.planet_at(*target, kind)

    def missions_for(self, player: Player, origin: Planet, ships: dict[int, int], target: tuple[int, int, int],
                     kind: int) -> list[int]:
        """Missions that make sense for this fleet and target (before deeper checks)."""
        g, s, p = target
        if p == EXPEDITION_POSITION:
            return [EXPEDITION] if player.tech(124) >= 1 else []
        dest = self.target_planet(target, kind)
        out = []
        only_probes = set(k for k, n in ships.items() if n) == {210}
        if dest is None:
            if kind == PLANET and ships.get(208):
                out.append(COLONIZE)
        elif dest.owner_id == player.id:
            if (dest.id != origin.id):
                out += [TRANSPORT, DEPLOY]
        else:
            if ships.get(210):
                out.append(SPY)
            if not only_probes:
                out += [ATTACK, TRANSPORT]
        if ships.get(209) and any(self.db.get_debris(g, s, p)):
            out.append(RECYCLE)
        return out

    def check_attackable(self, attacker: Player, defender: Player) -> None:
        if defender.vacation:
            raise GameError("Ese jugador está en modo vacaciones.")
        if defender.id == attacker.id:
            raise GameError("No puedes atacarte a ti mismo.")
        if self.is_inactive(defender):
            return
        ratio, limit = self.s.noob_ratio, self.s.noob_points_limit
        if defender.points < limit and attacker.points > defender.points * ratio:
            raise GameError("Ese jugador está protegido como novato: tiene menos de la quinta parte de tus puntos.")
        if attacker.points < limit and defender.points > attacker.points * ratio:
            raise GameError("Estás protegido como novato: no puedes atacar a alguien con más de 5 veces tus puntos.")

    def plan_fleet(self, player: Player, origin: Planet, ships: dict[int, int], target: tuple[int, int, int],
                   kind: int, mission: int, speed: int, cargo: tuple[float, float, float] = (0, 0, 0)) -> FleetPlan:
        ships = {int(k): int(v) for k, v in ships.items() if int(v) > 0}
        if not ships:
            raise GameError("Elige al menos una nave.")
        for eid, n in ships.items():
            if ELEMENTS[eid].kind != SHIP or eid == 212:
                raise GameError("Los satélites solares no pueden volar.")
            if origin.ships.get(eid, 0) < n:
                raise GameError(f"No tienes {num(n)} {NAMES[eid]} en este planeta.")
        g, s, p = target
        max_pos = EXPEDITION_POSITION if mission == EXPEDITION else 15
        if not (1 <= g <= self.s.galaxies and 1 <= s <= self.s.systems and 1 <= p <= max_pos):
            raise GameError(f"Coordenadas fuera del universo (galaxias 1-{self.s.galaxies}, "
                            f"sistemas 1-{self.s.systems}, posiciones 1-15).")
        if mission == EXPEDITION and p != EXPEDITION_POSITION:
            raise GameError("Las expediciones van a la posición 16 de un sistema.")
        if (target, kind) == (origin.coords, origin.kind):
            raise GameError("La flota ya está ahí.")
        if speed not in range(10, 101, 10):
            raise GameError("La velocidad va de 10 % a 100 %.")
        if mission not in MISSIONS:
            raise GameError("Misión no válida.")
        dist = formulas.distance(origin.coords, target)
        speed_value = formulas.fleet_speed(ships, player.research, player.officer(613))
        seconds = formulas.flight_seconds(dist, speed_value, speed, self.s.fleet_speed)
        fuel = formulas.fuel_cost(ships, player.research, dist, seconds, self.s.fleet_speed, player.officer(613))
        capacity = formulas.cargo_capacity(ships)
        cargo = tuple(max(0, int(c)) for c in cargo)
        if mission in (ATTACK, SPY, RECYCLE, EXPEDITION):
            cargo = (0, 0, 0)
        return FleetPlan(ships, origin, target, kind, mission, speed, dist, seconds, fuel, capacity,
                         cargo, self.target_planet(target, kind))  # type: ignore[arg-type]

    def validate_plan(self, player: Player, plan: FleetPlan) -> None:
        used, total = self.fleet_slots(player)
        if used >= total:
            raise GameError(f"Tienes {used} de {total} flotas en vuelo. Investiga Computación para tener más.")
        if plan.mission not in self.missions_for(player, plan.origin, plan.ships, plan.target, plan.target_kind):
            raise GameError(f"No se puede {MISSIONS[plan.mission].lower()} ese destino con esas naves.")
        dest = plan.target_planet
        if plan.mission in (ATTACK, SPY):
            defender = self.db.get_player(dest.owner_id)
            self.check_attackable(player, defender)
            if plan.mission == SPY and set(plan.ships) != {210}:
                raise GameError("Para espiar envía solo sondas de espionaje.")
            if plan.mission == ATTACK:
                since = self.now() - DAY
                sent = self.db.attacks_since(player.id, dest.id, since) + sum(
                    1 for f in self.db.fleets_of(player.id)
                    if f.mission == ATTACK and f.state == "out" and (f.target, f.target_kind) == (dest.coords, dest.kind))
                if sent >= self.s.bash_limit:
                    raise GameError(f"Ya atacaste ese planeta {sent} veces en 24 horas (máximo {self.s.bash_limit}).")
        if plan.mission == TRANSPORT and dest and dest.owner_id != player.id:
            owner = self.db.get_player(dest.owner_id)
            if owner and owner.vacation:
                raise GameError("Ese jugador está en modo vacaciones.")
        if plan.mission == COLONIZE:
            count = sum(1 for p in self.db.planets_of(player.id) if p.kind == PLANET)
            if count >= self.s.max_planets:
                raise GameError(f"Ya tienes el máximo de {self.s.max_planets} planetas.")
        total_cargo = sum(plan.cargo)
        if total_cargo + plan.fuel > plan.capacity:
            raise GameError(f"No cabe: la bodega es de {num(plan.capacity)} y el combustible ocupa {num(plan.fuel)}.")
        origin = plan.origin
        if (origin.metal < plan.cargo[0] or origin.crystal < plan.cargo[1]
                or origin.deuterium < plan.cargo[2] + plan.fuel):
            raise GameError(f"No tienes recursos para la carga y el combustible ({num(plan.fuel)} de deuterio).")

    @transactional
    def preview_fleet(self, player_id: int, planet_id: int, ships: dict[int, int], target: tuple[int, int, int],
                      kind: int, mission: int, speed: int, cargo=(0, 0, 0)) -> FleetPlan:
        player = self.require_player(player_id)
        origin = self._own_planet(player, planet_id)
        return self.plan_fleet(player, origin, ships, target, kind, mission, speed, cargo)

    @transactional
    def send_fleet(self, player_id: int, planet_id: int, ships: dict[int, int], target: tuple[int, int, int],
                   kind: int, mission: int, speed: int, cargo=(0, 0, 0)) -> tuple[Fleet, list[Notice]]:
        self._tick_unlocked()
        player = self.require_player(player_id)
        self._check_active(player)
        origin = self._own_planet(player, planet_id)
        plan = self.plan_fleet(player, origin, ships, target, kind, mission, speed, cargo)
        self.validate_plan(player, plan)
        for eid, n in plan.ships.items():
            origin.ships[eid] -= n
            if not origin.ships[eid]:
                del origin.ships[eid]
        origin.metal -= plan.cargo[0]
        origin.crystal -= plan.cargo[1]
        origin.deuterium -= plan.cargo[2] + plan.fuel
        t = self.now()
        hold = self.s.expedition_hold_hours * 3600 / self.s.fleet_speed if mission == EXPEDITION else 0
        arrive = t + plan.seconds
        fleet = Fleet(
            id=0, owner_id=player.id, mission=mission, origin_id=origin.id,
            origin_galaxy=origin.galaxy, origin_system=origin.system, origin_position=origin.position,
            origin_kind=origin.kind, target_galaxy=target[0], target_system=target[1], target_position=target[2],
            target_kind=kind, target_owner_id=plan.target_planet.owner_id if plan.target_planet else None,
            ships=dict(plan.ships), metal=plan.cargo[0], crystal=plan.cargo[1], deuterium=plan.cargo[2],
            fuel=plan.fuel, speed=speed, depart=t, arrive=arrive, hold_until=arrive + hold if hold else None,
            return_at=arrive + hold + plan.seconds)
        self.db.insert_fleet(fleet)
        self.db.save_planet(origin)
        self.touch(player)
        self.db.save_player(player)
        notices = []
        if mission == ATTACK and plan.target_planet:
            notices.append(Notice(plan.target_planet.owner_id, reports.incoming_attack(
                player, plan.target_planet, fleet, t, self.s.timezone)))
        return fleet, notices

    @transactional
    def recall_fleet(self, player_id: int, fleet_id: int) -> Fleet:
        self._tick_unlocked()
        fleet = self.db.get_fleet(fleet_id)
        if not fleet or fleet.owner_id != player_id:
            raise GameError("Esa flota no es tuya.")
        t = self.now()
        if fleet.state == "out":
            fleet.return_at = t + (t - fleet.depart)
        elif fleet.state == "hold":
            fleet.return_at = t + (fleet.arrive - fleet.depart)
        else:
            raise GameError("La flota ya está volviendo.")
        fleet.state = "back"
        self.db.save_fleet(fleet)
        return fleet

    def quick_raid(self, player_id: int, report_id: int) -> tuple[Fleet, list[Notice]]:
        """Attack the planet of a spy report with just enough cargo ships to carry the loot."""
        report = self.db.get_report(report_id)
        if not report or report["player_id"] != player_id or report["kind"] != "spy":
            raise GameError("Ese informe no existe.")
        data = report["data"]
        if data.get("depth", 0) < rules.SPY_DEFENSE:
            raise GameError("Ese informe no muestra la flota ni las defensas. Espía con más sondas o usa ⚔️ Atacar.")
        if data.get("fleet") or data.get("defense"):
            raise GameError("Ese planeta tiene flota o defensas: el saqueo rápido solo manda naves de carga. "
                            "Usa ⚔️ Atacar y elige naves de guerra.")
        player = self.require_player(player_id)
        origin = self.db.get_planet(data.get("origin_id") or 0)
        if not origin or origin.owner_id != player_id:
            origin = self.db.get_planet(player.current_planet)
        self.refresh(origin, self.now(), player)
        loot_total = sum(x * 0.5 for x in data["resources"])
        if loot_total < 1:
            raise GameError("Ese planeta no tiene recursos para saquear.")
        capacity = loot_total
        while sum(combat.plunder(capacity, data["resources"])) < int(loot_total) and capacity < loot_total * 3:
            capacity *= 1.05
        ships: dict[int, int] = {}
        need = capacity
        for eid in (203, 202):
            have = origin.ships.get(eid, 0)
            take = min(have, -(-int(need) // ELEMENTS[eid].cargo))
            if take > 0:
                ships[eid] = take
                need -= take * ELEMENTS[eid].cargo
            if need <= 0:
                break
        if not ships:
            raise GameError("No tienes naves de carga en ese planeta.")
        return self.send_fleet(player_id, origin.id, ships, tuple(data["target"]), data["kind"], ATTACK, 100)

    # ======================================================================
    # Events
    # ======================================================================

    def tick(self, t: float | None = None) -> list[Notice]:
        """Process every due event and return all notices waiting to be sent."""
        with self.db.conn:
            self._tick_unlocked(t)
        return self.take_notices()

    def _tick_unlocked(self, t: float | None = None) -> list[Notice]:
        t = self.now() if t is None else t
        notices: list[Notice] = []
        for _ in range(MAX_EVENTS_PER_TICK):
            event = self._next_event(t)
            if not event:
                break
            when, kind, ident = event
            if kind == "build":
                self._finish_build(ident, when, notices)
            elif kind == "research":
                self._finish_research(ident, when, notices)
            else:
                self._fleet_event(ident, when, notices)
        self._pending.extend(notices)
        if float(self.db.get_meta("ranking_at", "0")) < t - self.s.ranking_minutes * 60:
            self.update_ranking(t)
        return notices

    def take_notices(self) -> list[Notice]:
        """Notices produced by events (also those processed inside player actions), not yet sent."""
        out, self._pending = self._pending, []
        return out

    def _next_event(self, t: float):
        conn = self.db.conn
        candidates = []
        row = conn.execute("SELECT id, build_end FROM planets WHERE build_end IS NOT NULL AND build_end<=? "
                           "ORDER BY build_end LIMIT 1", (t,)).fetchone()
        if row:
            candidates.append((row[1], "build", row[0]))
        row = conn.execute("SELECT id, research_end FROM players WHERE research_end IS NOT NULL AND research_end<=? "
                           "ORDER BY research_end LIMIT 1", (t,)).fetchone()
        if row:
            candidates.append((row[1], "research", row[0]))
        row = conn.execute(
            "SELECT id, CASE state WHEN 'out' THEN arrive WHEN 'hold' THEN hold_until ELSE return_at END AS ev "
            "FROM fleets WHERE (CASE state WHEN 'out' THEN arrive WHEN 'hold' THEN hold_until ELSE return_at END)<=? "
            "ORDER BY ev, id LIMIT 1", (t,)).fetchone()
        if row:
            candidates.append((row[1], "fleet", row[0]))
        return min(candidates) if candidates else None

    def _finish_build(self, planet_id: int, t: float, notices: list[Notice]) -> None:
        planet = self.db.get_planet(planet_id)
        owner = self.db.get_player(planet.owner_id)
        self.refresh(planet, t, owner)
        element_id, level = planet.build_id, planet.build_level
        planet.buildings[element_id] = level
        planet.build_id = planet.build_level = planet.build_start = planet.build_end = None
        self.db.save_planet(planet)
        if element_id in MINER_XP_BUILDINGS:
            owner.xp_miner += sum(formulas.level_cost(element_id, level)) / 1000
            self._level_up(owner, notices)
        self.db.save_player(owner)
        if owner.notify_builds:
            notices.append(Notice(owner.id, f"🏗 <b>{NAMES[element_id]}</b> nivel {level} terminado en "
                                            f"{reports.planet_label(planet)}."))

    def _finish_research(self, player_id: int, t: float, notices: list[Notice]) -> None:
        player = self.db.get_player(player_id)
        element_id, level = player.research_id, player.research_level
        player.research[element_id] = level
        player.research_id = player.research_level = player.research_planet = None
        player.research_start = player.research_end = None
        self.db.save_player(player)
        if player.notify_builds:
            notices.append(Notice(player.id, f"🔬 <b>{NAMES[element_id]}</b> nivel {level} investigado."))

    def _fleet_event(self, fleet_id: int, t: float, notices: list[Notice]) -> None:
        fleet = self.db.get_fleet(fleet_id)
        if fleet.state == "back":
            self._fleet_home(fleet, t, notices)
        elif fleet.state == "hold":
            self._expedition_result(fleet, t, notices)
        else:
            handler = {ATTACK: self._arrive_attack, TRANSPORT: self._arrive_transport, DEPLOY: self._arrive_deploy,
                       SPY: self._arrive_spy, COLONIZE: self._arrive_colonize, RECYCLE: self._arrive_recycle,
                       EXPEDITION: self._arrive_expedition}.get(fleet.mission)
            if handler:
                handler(fleet, t, notices)
            else:
                self._send_back(fleet)

    def _send_back(self, fleet: Fleet) -> None:
        if not any(fleet.ships.values()):
            self.db.delete_fleet(fleet.id)
            return
        fleet.state = "back"
        self.db.save_fleet(fleet)

    def _fleet_home(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        planet = self.db.get_planet(fleet.origin_id)
        self.db.delete_fleet(fleet.id)
        if not planet or planet.owner_id != fleet.owner_id:
            planets = self.db.planets_of(fleet.owner_id)
            if not planets:
                return
            planet = planets[0]
        owner = self.db.get_player(fleet.owner_id)
        self.refresh(planet, t, owner)
        for eid, n in fleet.ships.items():
            planet.ships[eid] = planet.ships.get(eid, 0) + n
        planet.metal += fleet.metal
        planet.crystal += fleet.crystal
        planet.deuterium += fleet.deuterium
        self.db.save_planet(planet)
        cargo = fleet.metal + fleet.crystal + fleet.deuterium
        text = (f"🛬 Volvió tu flota a {reports.planet_label(planet)} "
                f"({MISSIONS.get(fleet.mission, '').lower()} a {reports.fmt_target(fleet)}).")
        if cargo:
            text += "\n" + reports.cargo_text((fleet.metal, fleet.crystal, fleet.deuterium))
        notices.append(Notice(fleet.owner_id, text))

    # --- Missions ---------------------------------------------------------

    def _tech(self, player: Player) -> combat.Tech:
        return combat.Tech(player.tech(109), player.tech(110), player.tech(111), player.officer(602))

    def _arrive_attack(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        target = self.db.planet_at(*fleet.target, fleet.target_kind)
        attacker = self.db.get_player(fleet.owner_id)
        if not target or target.owner_id == fleet.owner_id:
            notices.append(Notice(fleet.owner_id, f"⚔️ Tu flota llegó a {reports.fmt_target(fleet)} y no había "
                                                  f"nada que atacar. Vuelve a casa."))
            self._send_back(fleet)
            return
        defender = self.db.get_player(target.owner_id)
        if defender.vacation:
            notices.append(Notice(fleet.owner_id, f"⚔️ {reports.esc(defender.name)} entró en modo vacaciones. "
                                                  f"Tu flota vuelve."))
            self._send_back(fleet)
            return
        self.refresh(target, t, defender)
        def_units = {**{k: v for k, v in target.ships.items() if v}, **{
            k: v for k, v in target.defense.items() if v and ELEMENTS[k].kind == DEFENSE}}
        result = combat.simulate(fleet.ships, self._tech(attacker), def_units, self._tech(defender), self.rng)
        att_lost, def_lost = result.attacker_lost, result.defender_lost
        metal, crystal = combat.debris({**att_lost}, self.s.debris_ships, self.s.debris_defense)
        m2, c2 = combat.debris(def_lost, self.s.debris_ships, self.s.debris_defense)
        metal, crystal = metal + m2, crystal + c2
        rebuilt = combat.rebuild_defense(def_lost, self.rng, self.s.defense_rebuild)
        target.ships = {k: v for k, v in result.defender_left.items() if ELEMENTS[k].kind == SHIP}
        missiles = {k: v for k, v in target.defense.items() if ELEMENTS[k].kind == MISSILE}
        defense = {k: v for k, v in result.defender_left.items() if ELEMENTS[k].kind == DEFENSE}
        for k, v in rebuilt.items():
            defense[k] = defense.get(k, 0) + v
        target.defense = {**defense, **missiles}
        fleet.ships = dict(result.attacker_left)
        loot = (0, 0, 0)
        if result.winner == "attacker":
            free = formulas.cargo_capacity(fleet.ships) - (fleet.metal + fleet.crystal + fleet.deuterium)
            loot = combat.plunder(free, (target.metal, target.crystal, target.deuterium))
            target.metal -= loot[0]
            target.crystal -= loot[1]
            target.deuterium -= loot[2]
            fleet.metal += loot[0]
            fleet.crystal += loot[1]
            fleet.deuterium += loot[2]
        if metal or crystal:
            old = self.db.get_debris(*fleet.target)
            self.db.set_debris(*fleet.target, old[0] + metal, old[1] + crystal)
        chance = combat.moon_chance(metal + crystal)
        moon_created = None
        if chance and target.kind == PLANET and not self.db.planet_at(*fleet.target, MOON):
            if self.rng.randint(1, 100) <= chance:
                moon_created = Planet(
                    id=0, owner_id=target.owner_id, name="Luna", galaxy=target.galaxy, system=target.system,
                    position=target.position, kind=MOON, base_fields=formulas.MOON_BASE_FIELDS,
                    temp_min=target.temp_min - 20, temp_max=target.temp_max - 20, metal=0.0, crystal=0.0,
                    deuterium=0.0, last_update=t, created_at=t, shipyard_ts=t)
                self.db.insert_planet(moon_created)
        self.db.save_planet(target)
        self.db.log_attack(attacker.id, target.id, t)
        attacker.xp_raid += 1
        self._level_up(attacker, notices)
        self.db.save_player(attacker)
        title, body = reports.battle(attacker, defender, target, result, loot, (metal, crystal), chance,
                                     moon_created is not None, rebuilt, t, self.s.timezone)
        for pid in (attacker.id, defender.id):
            rid = self.db.insert_report(pid, "battle", title, body, {"target": list(fleet.target)}, t)
            notices.append(Notice(pid, body, [[("📨 Informes", "m:rep")]] if rid else []))
        self._send_back(fleet)

    def _arrive_transport(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        target = self.db.planet_at(*fleet.target, fleet.target_kind)
        if target:
            owner = self.db.get_player(target.owner_id)
            self.refresh(target, t, owner)
            target.metal += fleet.metal
            target.crystal += fleet.crystal
            target.deuterium += fleet.deuterium
            self.db.save_planet(target)
            cargo = (fleet.metal, fleet.crystal, fleet.deuterium)
            fleet.metal = fleet.crystal = fleet.deuterium = 0.0
            notices.append(Notice(fleet.owner_id, f"📦 Tu transporte llegó a {reports.planet_label(target)}.\n"
                                                  f"{reports.cargo_text(cargo)}"))
            if target.owner_id != fleet.owner_id:
                sender = self.db.get_player(fleet.owner_id)
                notices.append(Notice(target.owner_id, f"📦 <b>{reports.esc(sender.name)}</b> te envió recursos a "
                                                       f"{reports.planet_label(target)}.\n{reports.cargo_text(cargo)}"))
        else:
            notices.append(Notice(fleet.owner_id, f"📦 No hay planeta en {reports.fmt_target(fleet)}. "
                                                  f"Tu transporte vuelve con la carga."))
        self._send_back(fleet)

    def _arrive_deploy(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        target = self.db.planet_at(*fleet.target, fleet.target_kind)
        if not target or target.owner_id != fleet.owner_id:
            notices.append(Notice(fleet.owner_id, "🛬 El destino ya no es tuyo. La flota vuelve."))
            self._send_back(fleet)
            return
        owner = self.db.get_player(fleet.owner_id)
        self.refresh(target, t, owner)
        for eid, n in fleet.ships.items():
            target.ships[eid] = target.ships.get(eid, 0) + n
        target.metal += fleet.metal
        target.crystal += fleet.crystal
        target.deuterium += fleet.deuterium
        self.db.save_planet(target)
        self.db.delete_fleet(fleet.id)
        notices.append(Notice(fleet.owner_id, f"🛬 Tu flota se quedó en {reports.planet_label(target)}: "
                                              f"{reports.units_text(fleet.ships)}."))

    def _arrive_spy(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        target = self.db.planet_at(*fleet.target, fleet.target_kind)
        if not target or target.owner_id == fleet.owner_id:
            notices.append(Notice(fleet.owner_id, f"🔭 No había nada que espiar en {reports.fmt_target(fleet)}."))
            self._send_back(fleet)
            return
        attacker = self.db.get_player(fleet.owner_id)
        defender = self.db.get_player(target.owner_id)
        self.refresh(target, t, defender)
        self.db.save_planet(target)
        probes = fleet.ships.get(210, 0)
        depth = rules.spy_depth(probes, attacker.tech(106) + 5 * attacker.officer(610),
                                defender.tech(106) + 5 * defender.officer(610))
        destroyed, chance = rules.spy_detected(sum(target.ships.values()), probes, self.rng)
        title, body = reports.spy(attacker, defender, target, depth, chance, destroyed,
                                  self.db.get_debris(*target.coords), self.is_inactive(defender),
                                  self.is_inactive(defender, 28), t, self.s.timezone)
        data = {"target": list(target.coords), "kind": target.kind, "origin_id": fleet.origin_id, "depth": depth,
                "resources": [target.metal, target.crystal, target.deuterium],
                "fleet": sum(target.ships.values()), "defense": sum(
                    v for k, v in target.defense.items() if ELEMENTS[k].kind == DEFENSE)}
        rid = self.db.insert_report(attacker.id, "spy", title, body, data, t)
        buttons = [[("⚡ Saqueo rápido", f"qr:{rid}"),
                    ("⚔️ Atacar", f"fs:{target.galaxy}:{target.system}:{target.position}:{target.kind}:{ATTACK}")]]
        notices.append(Notice(attacker.id, body, buttons))
        alert = (f"🔭 <b>{reports.esc(attacker.name)}</b> espió {reports.planet_label(target)} desde "
                 f"{reports.fmt_origin(fleet)}. Probabilidad de destruir sus sondas: {chance} %.")
        if destroyed:
            alert += f"\nTus naves destruyeron {num(probes)} sondas."
            old = self.db.get_debris(*target.coords)
            self.db.set_debris(*target.coords, old[0], old[1] + probes * 1000 * self.s.debris_ships)
            self.db.delete_fleet(fleet.id)
        else:
            self._send_back(fleet)
        notices.append(Notice(defender.id, alert))

    def _arrive_colonize(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        g, s, p = fleet.target
        planets = [x for x in self.db.planets_of(fleet.owner_id) if x.kind == PLANET]
        if self.db.planet_at(g, s, p, PLANET):
            notices.append(Notice(fleet.owner_id, f"🌱 La posición {reports.fmt_target(fleet)} ya está ocupada. "
                                                  f"Tu flota vuelve."))
            self._send_back(fleet)
            return
        if len(planets) >= self.s.max_planets:
            notices.append(Notice(fleet.owner_id, f"🌱 Ya tienes el máximo de {self.s.max_planets} planetas. "
                                                  f"Tu flota vuelve."))
            self._send_back(fleet)
            return
        colony = self._new_planet(fleet.owner_id, "Colonia", g, s, p, t)
        colony.metal, colony.crystal, colony.deuterium = fleet.metal, fleet.crystal, fleet.deuterium
        self.db.save_planet(colony)
        fleet.metal = fleet.crystal = fleet.deuterium = 0.0
        fleet.ships[208] -= 1
        if not fleet.ships[208]:
            del fleet.ships[208]
        notices.append(Notice(fleet.owner_id, f"🌱 ¡Nueva colonia en {reports.planet_label(colony)}! "
                                              f"Tiene {colony.base_fields} campos y "
                                              f"{colony.temp_min} °C a {colony.temp_max} °C."))
        self._send_back(fleet)

    def _arrive_recycle(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        metal, crystal = self.db.get_debris(*fleet.target)
        capacity = fleet.ships.get(209, 0) * ELEMENTS[209].cargo - (fleet.metal + fleet.crystal + fleet.deuterium)
        total = metal + crystal
        share = 1.0 if total <= capacity else max(0.0, capacity) / total if total else 0.0
        got_m, got_c = int(metal * share), int(crystal * share)
        self.db.set_debris(*fleet.target, metal - got_m, crystal - got_c)
        fleet.metal += got_m
        fleet.crystal += got_c
        notices.append(Notice(fleet.owner_id, f"♻️ Tus recicladores recogieron en {reports.fmt_target(fleet)}: "
                                              f"{reports.cargo_text((got_m, got_c, 0))}"))
        self._send_back(fleet)

    def _arrive_expedition(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        fleet.state = "hold"
        self.db.save_fleet(fleet)

    def _expedition_result(self, fleet: Fleet, t: float, notices: list[Notice]) -> None:
        outcome = rules.expedition(fleet.ships, self.rng)
        text = reports.expedition(outcome, fleet)
        if outcome.kind == "lost":
            for eid in list(fleet.ships):
                lost = round(fleet.ships[eid] * outcome.lost_share)
                fleet.ships[eid] -= lost
                if fleet.ships[eid] <= 0:
                    del fleet.ships[eid]
        elif outcome.kind == "resources":
            free = formulas.cargo_capacity(fleet.ships) - (fleet.metal + fleet.crystal + fleet.deuterium)
            share = min(1.0, max(0.0, free) / max(1, sum(outcome.found)))
            fleet.metal += int(outcome.found[0] * share)
            fleet.crystal += int(outcome.found[1] * share)
            fleet.deuterium += int(outcome.found[2] * share)
        elif outcome.kind == "ships":
            for eid, n in outcome.ships_found.items():
                fleet.ships[eid] = fleet.ships.get(eid, 0) + n
        self.db.insert_report(fleet.owner_id, "expedition", "Expedición", text, {}, t)
        notices.append(Notice(fleet.owner_id, text))
        if not fleet.ships:
            self.db.delete_fleet(fleet.id)
            return
        fleet.state = "back"
        self.db.save_fleet(fleet)

    # ======================================================================
    # Experience and officers (Xnova)
    # ======================================================================

    def _level_up(self, player: Player, notices: list[Notice]) -> None:
        while player.lvl_miner + player.lvl_raid < 100 and player.xp_miner >= player.lvl_miner * 5000:
            player.lvl_miner += 1
            player.officer_points += 1
            notices.append(Notice(player.id, f"⛏ Subiste a minero nivel {player.lvl_miner}. "
                                             f"Ganaste 1 punto de oficial."))
        while player.lvl_miner + player.lvl_raid < 100 and player.xp_raid >= player.lvl_raid * 10:
            player.lvl_raid += 1
            player.officer_points += 1
            notices.append(Notice(player.id, f"🏴‍☠️ Subiste a saqueador nivel {player.lvl_raid}. "
                                             f"Ganaste 1 punto de oficial."))

    def officer_missing(self, player: Player, officer_id: int) -> dict[int, int]:
        return {req: lvl for req, lvl in OFFICERS[officer_id].requires.items() if player.officer(req) < lvl}

    @transactional
    def hire_officer(self, player_id: int, officer_id: int) -> Player:
        player = self.require_player(player_id)
        officer = OFFICERS.get(officer_id)
        if not officer:
            raise GameError("Ese oficial no existe.")
        if player.officer_points < 1:
            raise GameError("No tienes puntos de oficial. Se ganan subiendo de nivel de minero o de saqueador.")
        if player.officer(officer_id) >= officer.max_level:
            raise GameError("Ese oficial ya está al nivel máximo.")
        if self.officer_missing(player, officer_id):
            raise GameError("Todavía no cumples los requisitos de ese oficial.")
        player.officers[officer_id] = player.officer(officer_id) + 1
        player.officer_points -= 1
        self.db.save_player(player)
        return player

    # ======================================================================
    # Vacation mode and settings
    # ======================================================================

    @transactional
    def set_vacation(self, player_id: int, on: bool) -> Player:
        self._tick_unlocked()
        player = self.require_player(player_id)
        t = self.now()
        if on:
            if player.vacation:
                raise GameError("Ya estás en modo vacaciones.")
            if self.db.fleets_of(player.id):
                raise GameError("No puedes tener flotas en vuelo para entrar en vacaciones.")
            if self.db.fleets_against(player.id):
                raise GameError("Hay flotas enemigas en camino. Espera a que lleguen.")
            if player.research_id:
                raise GameError("Termina o cancela la investigación primero.")
            for planet in self.planets(player, t):
                if planet.build_id or planet.shipyard:
                    raise GameError(f"{planet.name} tiene construcciones en curso.")
            player.vacation, player.vacation_since = 1, t
        else:
            if not player.vacation:
                raise GameError("No estás en modo vacaciones.")
            until = (player.vacation_since or t) + self.s.vacation_min_hours * 3600
            if t < until:
                raise GameError(f"El modo vacaciones dura al menos {num(self.s.vacation_min_hours)} horas. "
                                f"Podrás salir en {duration(until - t)}.")
            for planet in self.db.planets_of(player.id):
                planet.last_update = t  # nothing was produced while away
                planet.shipyard_ts = t
                self.db.save_planet(planet)
            player.vacation, player.vacation_since = 0, None
        self.db.save_player(player)
        return player

    @transactional
    def toggle_notifications(self, player_id: int) -> Player:
        player = self.require_player(player_id)
        player.notify_builds = 0 if player.notify_builds else 1
        self.db.save_player(player)
        return player

    @transactional
    def set_blocked(self, player_id: int, blocked: bool) -> None:
        player = self.db.get_player(player_id)
        if player:
            player.blocked = 1 if blocked else 0
            self.db.save_player(player)

    # ======================================================================
    # Ranking
    # ======================================================================

    def update_ranking(self, t: float | None = None) -> None:
        t = self.now() if t is None else t
        players = {p.id: p for p in self.db.all_players()}
        for p in players.values():
            p.points_buildings = p.points_fleet = p.points_defense = 0.0
            p.points_research = formulas.points_for_levels(p.research)
        for planet in self.db.all_planets():
            owner = players.get(planet.owner_id)
            if not owner:
                continue
            owner.points_buildings += formulas.points_for_levels(planet.buildings)
            owner.points_fleet += formulas.points_for_units(planet.ships)
            owner.points_defense += formulas.points_for_units(planet.defense)
        for fleet in self.db.all_fleets():
            owner = players.get(fleet.owner_id)
            if owner:
                owner.points_fleet += formulas.points_for_units(fleet.ships)
        ordered = sorted(players.values(), key=lambda p: (-(p.points_buildings + p.points_research + p.points_fleet
                                                            + p.points_defense), p.id))
        for rank, p in enumerate(ordered, start=1):
            p.points = p.points_buildings + p.points_research + p.points_fleet + p.points_defense
            p.rank = rank
            self.db.save_player(p)
        self.db.set_meta("ranking_at", str(t))
        self.db.prune_attack_log(t - DAY)
        self.db.prune_reports()

    # ======================================================================
    # Galaxy
    # ======================================================================

    def galaxy(self, galaxy: int, system: int) -> dict:
        galaxy = max(1, min(self.s.galaxies, galaxy))
        system = max(1, min(self.s.systems, system))
        bodies = self.db.planets_in_system(galaxy, system)
        planets = {b.position: b for b in bodies if b.kind == PLANET}
        moons = {b.position: b for b in bodies if b.kind == MOON}
        owners = {pid: self.db.get_player(pid) for pid in {b.owner_id for b in bodies}}
        tags = self.db.alliance_tags(p.alliance_id for p in owners.values() if p and p.alliance_id)
        return {"galaxy": galaxy, "system": system, "planets": planets, "moons": moons, "owners": owners,
                "tags": tags, "debris": self.db.debris_in_system(galaxy, system)}

    def status_marks(self, player: Player, viewer: Player | None) -> str:
        marks = []
        if player.vacation:
            marks.append("v")
        if self.is_inactive(player, 28):
            marks.append("I")
        elif self.is_inactive(player):
            marks.append("i")
        if viewer and viewer.id != player.id and not self.is_inactive(player) and not player.vacation:
            ratio, limit = self.s.noob_ratio, self.s.noob_points_limit
            if player.points < limit and viewer.points > player.points * ratio:
                marks.append("n")
            elif viewer.points < limit and player.points > viewer.points * ratio:
                marks.append("f")
        return f"({','.join(marks)})" if marks else ""

    # ======================================================================
    # Alliances and messages
    # ======================================================================

    @transactional
    def create_alliance(self, player_id: int, tag: str, name: str) -> dict:
        player = self.require_player(player_id)
        if player.alliance_id:
            raise GameError("Ya estás en una alianza. Sal primero.")
        tag, name = tag.strip(), " ".join(name.split())
        if not TAG_RE.match(tag):
            raise GameError("La etiqueta debe tener de 2 a 8 letras o números, sin espacios.")
        if not 3 <= len(name) <= 30:
            raise GameError("El nombre de la alianza debe tener de 3 a 30 caracteres.")
        if self.db.alliance_by_tag(tag):
            raise GameError("Esa etiqueta ya existe.")
        alliance_id = self.db.insert_alliance(tag, name, player.id, self._new_code(), self.now())
        player.alliance_id, player.alliance_rank = alliance_id, "leader"
        self.db.save_player(player)
        return self.db.get_alliance(alliance_id)

    def _new_code(self) -> str:
        while True:
            code = secrets.token_hex(3).upper()
            if not self.db.alliance_by_code(code):
                return code

    @transactional
    def join_alliance(self, player_id: int, code: str) -> tuple[dict, list[Notice]]:
        player = self.require_player(player_id)
        if player.alliance_id:
            raise GameError("Ya estás en una alianza. Sal primero.")
        alliance = self.db.alliance_by_code(code.strip().upper())
        if not alliance:
            raise GameError("Ese código de invitación no existe.")
        members = self.db.alliance_members(alliance["id"])
        player.alliance_id, player.alliance_rank = alliance["id"], "member"
        self.db.save_player(player)
        notices = [Notice(m.id, f"🤝 <b>{reports.esc(player.name)}</b> se unió a la alianza.") for m in members]
        return alliance, notices

    @transactional
    def leave_alliance(self, player_id: int) -> list[Notice]:
        player = self.require_player(player_id)
        if not player.alliance_id:
            raise GameError("No estás en ninguna alianza.")
        alliance_id = player.alliance_id
        player.alliance_id = player.alliance_rank = None
        self.db.save_player(player)
        members = self.db.alliance_members(alliance_id)
        notices = [Notice(m.id, f"🤝 <b>{reports.esc(player.name)}</b> dejó la alianza.") for m in members]
        if not members:
            self.db.delete_alliance(alliance_id)
        elif not any(m.alliance_rank == "leader" for m in members):
            heir = members[0]
            heir.alliance_rank = "leader"
            self.db.save_player(heir)
            self.db.update_alliance(alliance_id, leader_id=heir.id)
            notices.append(Notice(heir.id, "👑 Ahora eres el líder de la alianza."))
        return notices

    @transactional
    def kick_member(self, leader_id: int, member_id: int) -> list[Notice]:
        leader = self.require_player(leader_id)
        member = self.db.get_player(member_id)
        if leader.alliance_rank != "leader" or not member or member.alliance_id != leader.alliance_id:
            raise GameError("No puedes expulsar a ese jugador.")
        if member.id == leader.id:
            raise GameError("Para irte, usa Salir de la alianza.")
        member.alliance_id = member.alliance_rank = None
        self.db.save_player(member)
        return [Notice(member.id, "🤝 Te expulsaron de la alianza.")]

    @transactional
    def new_invite_code(self, leader_id: int) -> dict:
        leader = self.require_player(leader_id)
        if leader.alliance_rank != "leader":
            raise GameError("Solo el líder puede cambiar el código.")
        self.db.update_alliance(leader.alliance_id, invite_code=self._new_code())
        return self.db.get_alliance(leader.alliance_id)

    def alliance_broadcast(self, player_id: int, text: str) -> list[Notice]:
        player = self.require_player(player_id)
        if not player.alliance_id:
            raise GameError("No estás en ninguna alianza.")
        text = text.strip()[:1000]
        if not text:
            raise GameError("El mensaje está vacío.")
        alliance = self.db.get_alliance(player.alliance_id)
        body = f"📣 <b>[{reports.esc(alliance['tag'])}] {reports.esc(player.name)}</b>:\n{reports.esc(text)}"
        return [Notice(m.id, body) for m in self.db.alliance_members(player.alliance_id) if m.id != player.id]

    def private_message(self, player_id: int, to_id: int, text: str) -> Notice:
        player = self.require_player(player_id)
        target = self.db.get_player(to_id)
        if not target:
            raise GameError("Ese jugador no existe.")
        text = text.strip()[:1000]
        if not text:
            raise GameError("El mensaje está vacío.")
        return Notice(target.id, f"✉️ <b>{reports.esc(player.name)}</b> te escribe:\n{reports.esc(text)}",
                      [[("↩️ Responder", f"msg:{player.id}")]])

    # ======================================================================
    # Admin
    # ======================================================================

    def stats(self) -> dict:
        conn = self.db.conn
        return {
            "players": self.db.count_players(),
            "active_24h": conn.execute("SELECT COUNT(*) FROM players WHERE last_active>=?",
                                       (self.now() - DAY,)).fetchone()[0],
            "planets": conn.execute("SELECT COUNT(*) FROM planets WHERE kind=1").fetchone()[0],
            "moons": conn.execute("SELECT COUNT(*) FROM planets WHERE kind=3").fetchone()[0],
            "fleets": conn.execute("SELECT COUNT(*) FROM fleets").fetchone()[0],
            "alliances": conn.execute("SELECT COUNT(*) FROM alliances").fetchone()[0],
        }


def officer_name(officer_id: int) -> str:
    return OFFICER_NAMES.get(officer_id, str(officer_id))


def floor_int(value: float) -> int:
    return int(floor(value))
