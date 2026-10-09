"""SQLite storage: schema, migrations and small dataclass models.

All game state lives here. JSON columns hold dicts keyed by element id
(buildings, research, ships...). Migrations only add; they never drop data.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Iterable

PLANET = 1
MOON = 3

MIGRATIONS: list[str] = [
    # 1: initial schema
    """
    CREATE TABLE players (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER NOT NULL,
        name TEXT NOT NULL UNIQUE COLLATE NOCASE,
        created_at REAL NOT NULL,
        last_active REAL NOT NULL,
        research TEXT NOT NULL DEFAULT '{}',
        research_id INTEGER, research_level INTEGER, research_planet INTEGER,
        research_start REAL, research_end REAL,
        officers TEXT NOT NULL DEFAULT '{}',
        officer_points INTEGER NOT NULL DEFAULT 0,
        xp_miner REAL NOT NULL DEFAULT 0, lvl_miner INTEGER NOT NULL DEFAULT 1,
        xp_raid INTEGER NOT NULL DEFAULT 0, lvl_raid INTEGER NOT NULL DEFAULT 1,
        vacation INTEGER NOT NULL DEFAULT 0, vacation_since REAL,
        alliance_id INTEGER, alliance_rank TEXT,
        current_planet INTEGER,
        points REAL NOT NULL DEFAULT 0, points_buildings REAL NOT NULL DEFAULT 0,
        points_research REAL NOT NULL DEFAULT 0, points_fleet REAL NOT NULL DEFAULT 0,
        points_defense REAL NOT NULL DEFAULT 0, rank INTEGER NOT NULL DEFAULT 0,
        notify_builds INTEGER NOT NULL DEFAULT 1,
        blocked INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE planets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        galaxy INTEGER NOT NULL, system INTEGER NOT NULL, position INTEGER NOT NULL,
        kind INTEGER NOT NULL DEFAULT 1,
        base_fields INTEGER NOT NULL,
        temp_min INTEGER NOT NULL, temp_max INTEGER NOT NULL,
        metal REAL NOT NULL DEFAULT 0, crystal REAL NOT NULL DEFAULT 0, deuterium REAL NOT NULL DEFAULT 0,
        last_update REAL NOT NULL,
        buildings TEXT NOT NULL DEFAULT '{}',
        ships TEXT NOT NULL DEFAULT '{}',
        defense TEXT NOT NULL DEFAULT '{}',
        production TEXT NOT NULL DEFAULT '{}',
        build_id INTEGER, build_level INTEGER, build_start REAL, build_end REAL,
        shipyard TEXT NOT NULL DEFAULT '[]',
        shipyard_ts REAL,
        created_at REAL NOT NULL,
        UNIQUE (galaxy, system, position, kind)
    );
    CREATE INDEX planets_owner ON planets(owner_id);
    CREATE TABLE fleets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner_id INTEGER NOT NULL,
        mission INTEGER NOT NULL,
        origin_id INTEGER NOT NULL,
        origin_galaxy INTEGER NOT NULL, origin_system INTEGER NOT NULL, origin_position INTEGER NOT NULL,
        origin_kind INTEGER NOT NULL,
        target_galaxy INTEGER NOT NULL, target_system INTEGER NOT NULL, target_position INTEGER NOT NULL,
        target_kind INTEGER NOT NULL,
        target_owner_id INTEGER,
        ships TEXT NOT NULL,
        metal REAL NOT NULL DEFAULT 0, crystal REAL NOT NULL DEFAULT 0, deuterium REAL NOT NULL DEFAULT 0,
        fuel REAL NOT NULL DEFAULT 0,
        speed INTEGER NOT NULL DEFAULT 100,
        depart REAL NOT NULL, arrive REAL NOT NULL, hold_until REAL, return_at REAL NOT NULL,
        state TEXT NOT NULL DEFAULT 'out'
    );
    CREATE INDEX fleets_owner ON fleets(owner_id);
    CREATE INDEX fleets_target_owner ON fleets(target_owner_id);
    CREATE TABLE debris (
        galaxy INTEGER NOT NULL, system INTEGER NOT NULL, position INTEGER NOT NULL,
        metal REAL NOT NULL DEFAULT 0, crystal REAL NOT NULL DEFAULT 0,
        PRIMARY KEY (galaxy, system, position)
    );
    CREATE TABLE reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        kind TEXT NOT NULL,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        data TEXT NOT NULL DEFAULT '{}',
        created_at REAL NOT NULL
    );
    CREATE INDEX reports_player ON reports(player_id, created_at);
    CREATE TABLE alliances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT NOT NULL UNIQUE COLLATE NOCASE,
        name TEXT NOT NULL,
        leader_id INTEGER NOT NULL,
        invite_code TEXT NOT NULL UNIQUE,
        created_at REAL NOT NULL
    );
    CREATE TABLE attack_log (
        attacker_id INTEGER NOT NULL,
        target_planet_id INTEGER NOT NULL,
        at REAL NOT NULL
    );
    CREATE INDEX attack_log_idx ON attack_log(attacker_id, target_planet_id, at);
    CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """,
]


def _load_map(text: str | None) -> dict[int, Any]:
    if not text:
        return {}
    return {int(k): v for k, v in json.loads(text).items()}


def _dump(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"))


@dataclass
class Player:
    id: int
    chat_id: int
    name: str
    created_at: float
    last_active: float
    research: dict[int, int] = field(default_factory=dict)
    research_id: int | None = None
    research_level: int | None = None
    research_planet: int | None = None
    research_start: float | None = None
    research_end: float | None = None
    officers: dict[int, int] = field(default_factory=dict)
    officer_points: int = 0
    xp_miner: float = 0.0
    lvl_miner: int = 1
    xp_raid: int = 0
    lvl_raid: int = 1
    vacation: int = 0
    vacation_since: float | None = None
    alliance_id: int | None = None
    alliance_rank: str | None = None
    current_planet: int | None = None
    points: float = 0.0
    points_buildings: float = 0.0
    points_research: float = 0.0
    points_fleet: float = 0.0
    points_defense: float = 0.0
    rank: int = 0
    notify_builds: int = 1
    blocked: int = 0

    JSON = ("research", "officers")

    def officer(self, officer_id: int) -> int:
        return self.officers.get(officer_id, 0)

    def tech(self, element_id: int) -> int:
        return self.research.get(element_id, 0)


@dataclass
class Planet:
    id: int
    owner_id: int
    name: str
    galaxy: int
    system: int
    position: int
    kind: int
    base_fields: int
    temp_min: int
    temp_max: int
    metal: float
    crystal: float
    deuterium: float
    last_update: float
    buildings: dict[int, int] = field(default_factory=dict)
    ships: dict[int, int] = field(default_factory=dict)
    defense: dict[int, int] = field(default_factory=dict)
    production: dict[int, int] = field(default_factory=dict)
    build_id: int | None = None
    build_level: int | None = None
    build_start: float | None = None
    build_end: float | None = None
    shipyard: list[dict] = field(default_factory=list)
    shipyard_ts: float | None = None
    created_at: float = 0.0

    JSON = ("buildings", "ships", "defense", "production")

    @property
    def coords(self) -> tuple[int, int, int]:
        return self.galaxy, self.system, self.position

    @property
    def is_moon(self) -> bool:
        return self.kind == MOON

    def level(self, element_id: int) -> int:
        return self.buildings.get(element_id, 0)


@dataclass
class Fleet:
    id: int
    owner_id: int
    mission: int
    origin_id: int
    origin_galaxy: int
    origin_system: int
    origin_position: int
    origin_kind: int
    target_galaxy: int
    target_system: int
    target_position: int
    target_kind: int
    target_owner_id: int | None
    ships: dict[int, int]
    metal: float
    crystal: float
    deuterium: float
    fuel: float
    speed: int
    depart: float
    arrive: float
    hold_until: float | None
    return_at: float
    state: str = "out"

    JSON = ("ships",)

    @property
    def origin(self) -> tuple[int, int, int]:
        return self.origin_galaxy, self.origin_system, self.origin_position

    @property
    def target(self) -> tuple[int, int, int]:
        return self.target_galaxy, self.target_system, self.target_position

    @property
    def cargo(self) -> tuple[float, float, float]:
        return self.metal, self.crystal, self.deuterium

    def next_event(self) -> float:
        if self.state == "out":
            return self.arrive
        if self.state == "hold":
            return self.hold_until or self.arrive
        return self.return_at


def _from_row(cls, row: sqlite3.Row):
    data = dict(row)
    for name in cls.JSON:
        data[name] = _load_map(data[name])
    if cls is Planet:
        data["shipyard"] = json.loads(data["shipyard"] or "[]")
    return cls(**data)


def _to_values(obj) -> dict[str, Any]:
    out = {}
    for f in fields(obj):
        value = getattr(obj, f.name)
        if f.name in obj.JSON or f.name == "shipyard":
            value = _dump(value)
        out[f.name] = value
    return out


class Database:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.migrate()

    # --- Schema ---------------------------------------------------------------

    def migrate(self) -> None:
        version = self.conn.execute("PRAGMA user_version").fetchone()[0]
        for number, script in enumerate(MIGRATIONS[version:], start=version + 1):
            with self.conn:
                self.conn.executescript(script)
                self.conn.execute(f"PRAGMA user_version = {number}")

    def close(self) -> None:
        self.conn.close()

    def transaction(self):
        return self.conn

    # --- Generic --------------------------------------------------------------

    def _insert(self, table: str, values: dict[str, Any]) -> int:
        cols = ",".join(values)
        marks = ",".join("?" for _ in values)
        cur = self.conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", list(values.values()))
        return int(cur.lastrowid)

    def _update(self, table: str, obj) -> None:
        values = _to_values(obj)
        key = values.pop("id")
        sets = ",".join(f"{c}=?" for c in values)
        self.conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", [*values.values(), key])

    # --- Players --------------------------------------------------------------

    def get_player(self, player_id: int) -> Player | None:
        row = self.conn.execute("SELECT * FROM players WHERE id=?", (player_id,)).fetchone()
        return _from_row(Player, row) if row else None

    def player_by_name(self, name: str) -> Player | None:
        row = self.conn.execute("SELECT * FROM players WHERE name=?", (name,)).fetchone()
        return _from_row(Player, row) if row else None

    def insert_player(self, player: Player) -> None:
        self._insert("players", _to_values(player))

    def save_player(self, player: Player) -> None:
        self._update("players", player)

    def all_players(self) -> list[Player]:
        return [_from_row(Player, r) for r in self.conn.execute("SELECT * FROM players")]

    def players_by_rank(self, limit: int, offset: int = 0) -> list[Player]:
        rows = self.conn.execute("SELECT * FROM players ORDER BY points DESC, id LIMIT ? OFFSET ?", (limit, offset))
        return [_from_row(Player, r) for r in rows]

    def count_players(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]

    def players_with_research_due(self, now: float) -> list[Player]:
        rows = self.conn.execute(
            "SELECT * FROM players WHERE research_end IS NOT NULL AND research_end <= ? ORDER BY research_end",
            (now,))
        return [_from_row(Player, r) for r in rows]

    def alliance_members(self, alliance_id: int) -> list[Player]:
        rows = self.conn.execute("SELECT * FROM players WHERE alliance_id=? ORDER BY points DESC", (alliance_id,))
        return [_from_row(Player, r) for r in rows]

    # --- Planets --------------------------------------------------------------

    def get_planet(self, planet_id: int) -> Planet | None:
        row = self.conn.execute("SELECT * FROM planets WHERE id=?", (planet_id,)).fetchone()
        return _from_row(Planet, row) if row else None

    def planet_at(self, galaxy: int, system: int, position: int, kind: int = PLANET) -> Planet | None:
        row = self.conn.execute(
            "SELECT * FROM planets WHERE galaxy=? AND system=? AND position=? AND kind=?",
            (galaxy, system, position, kind)).fetchone()
        return _from_row(Planet, row) if row else None

    def planets_of(self, owner_id: int) -> list[Planet]:
        rows = self.conn.execute("SELECT * FROM planets WHERE owner_id=? ORDER BY kind, id", (owner_id,))
        return [_from_row(Planet, r) for r in rows]

    def planets_in_system(self, galaxy: int, system: int) -> list[Planet]:
        rows = self.conn.execute("SELECT * FROM planets WHERE galaxy=? AND system=? ORDER BY position, kind",
                                 (galaxy, system))
        return [_from_row(Planet, r) for r in rows]

    def count_planets_in_system(self, galaxy: int, system: int) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM planets WHERE galaxy=? AND system=? AND kind=1",
                                 (galaxy, system)).fetchone()[0]

    def insert_planet(self, planet: Planet) -> int:
        values = _to_values(planet)
        values.pop("id")
        planet.id = self._insert("planets", values)
        return planet.id

    def save_planet(self, planet: Planet) -> None:
        self._update("planets", planet)

    def planets_with_build_due(self, now: float) -> list[Planet]:
        rows = self.conn.execute(
            "SELECT * FROM planets WHERE build_end IS NOT NULL AND build_end <= ? ORDER BY build_end", (now,))
        return [_from_row(Planet, r) for r in rows]

    def all_planets(self) -> list[Planet]:
        return [_from_row(Planet, r) for r in self.conn.execute("SELECT * FROM planets")]

    # --- Fleets ---------------------------------------------------------------

    def insert_fleet(self, fleet: Fleet) -> int:
        values = _to_values(fleet)
        values.pop("id")
        fleet.id = self._insert("fleets", values)
        return fleet.id

    def save_fleet(self, fleet: Fleet) -> None:
        self._update("fleets", fleet)

    def delete_fleet(self, fleet_id: int) -> None:
        self.conn.execute("DELETE FROM fleets WHERE id=?", (fleet_id,))

    def get_fleet(self, fleet_id: int) -> Fleet | None:
        row = self.conn.execute("SELECT * FROM fleets WHERE id=?", (fleet_id,)).fetchone()
        return _from_row(Fleet, row) if row else None

    def fleets_of(self, owner_id: int) -> list[Fleet]:
        rows = self.conn.execute("SELECT * FROM fleets WHERE owner_id=? ORDER BY id", (owner_id,))
        return [_from_row(Fleet, r) for r in rows]

    def fleets_against(self, owner_id: int) -> list[Fleet]:
        rows = self.conn.execute(
            "SELECT * FROM fleets WHERE target_owner_id=? AND owner_id<>? AND state='out' ORDER BY arrive",
            (owner_id, owner_id))
        return [_from_row(Fleet, r) for r in rows]

    def fleets_to(self, galaxy: int, system: int, position: int) -> list[Fleet]:
        rows = self.conn.execute(
            "SELECT * FROM fleets WHERE (target_galaxy=? AND target_system=? AND target_position=?) "
            "OR (origin_galaxy=? AND origin_system=? AND origin_position=?)",
            (galaxy, system, position, galaxy, system, position))
        return [_from_row(Fleet, r) for r in rows]

    def due_fleets(self, now: float) -> list[Fleet]:
        rows = self.conn.execute(
            "SELECT * FROM fleets WHERE (state='out' AND arrive<=?) OR (state='hold' AND hold_until<=?) "
            "OR (state='back' AND return_at<=?)", (now, now, now))
        fleets = [_from_row(Fleet, r) for r in rows]
        return sorted(fleets, key=lambda f: (f.next_event(), f.id))

    def all_fleets(self) -> list[Fleet]:
        return [_from_row(Fleet, r) for r in self.conn.execute("SELECT * FROM fleets")]

    # --- Debris ---------------------------------------------------------------

    def get_debris(self, galaxy: int, system: int, position: int) -> tuple[float, float]:
        row = self.conn.execute("SELECT metal, crystal FROM debris WHERE galaxy=? AND system=? AND position=?",
                                (galaxy, system, position)).fetchone()
        return (row["metal"], row["crystal"]) if row else (0.0, 0.0)

    def set_debris(self, galaxy: int, system: int, position: int, metal: float, crystal: float) -> None:
        if metal <= 0 and crystal <= 0:
            self.conn.execute("DELETE FROM debris WHERE galaxy=? AND system=? AND position=?",
                              (galaxy, system, position))
            return
        self.conn.execute(
            "INSERT INTO debris (galaxy, system, position, metal, crystal) VALUES (?,?,?,?,?) "
            "ON CONFLICT(galaxy, system, position) DO UPDATE SET metal=excluded.metal, crystal=excluded.crystal",
            (galaxy, system, position, metal, crystal))

    def debris_in_system(self, galaxy: int, system: int) -> dict[int, tuple[float, float]]:
        rows = self.conn.execute("SELECT position, metal, crystal FROM debris WHERE galaxy=? AND system=?",
                                 (galaxy, system))
        return {r["position"]: (r["metal"], r["crystal"]) for r in rows}

    # --- Reports --------------------------------------------------------------

    def insert_report(self, player_id: int, kind: str, title: str, body: str, data: dict | None,
                      created_at: float) -> int:
        return self._insert("reports", {"player_id": player_id, "kind": kind, "title": title, "body": body,
                                        "data": _dump(data or {}), "created_at": created_at})

    def reports_of(self, player_id: int, limit: int = 10) -> list[sqlite3.Row]:
        return list(self.conn.execute(
            "SELECT id, kind, title, created_at FROM reports WHERE player_id=? ORDER BY id DESC LIMIT ?",
            (player_id, limit)))

    def get_report(self, report_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        if not row:
            return None
        out = dict(row)
        out["data"] = json.loads(out["data"] or "{}")
        return out

    def prune_reports(self, keep_per_player: int = 50) -> None:
        self.conn.execute(
            "DELETE FROM reports WHERE id IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER "
            "(PARTITION BY player_id ORDER BY id DESC) AS n FROM reports) WHERE n > ?)", (keep_per_player,))

    # --- Alliances ------------------------------------------------------------

    def insert_alliance(self, tag: str, name: str, leader_id: int, code: str, now: float) -> int:
        return self._insert("alliances", {"tag": tag, "name": name, "leader_id": leader_id,
                                          "invite_code": code, "created_at": now})

    def get_alliance(self, alliance_id: int) -> dict | None:
        row = self.conn.execute("SELECT * FROM alliances WHERE id=?", (alliance_id,)).fetchone()
        return dict(row) if row else None

    def alliance_by_tag(self, tag: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM alliances WHERE tag=?", (tag,)).fetchone()
        return dict(row) if row else None

    def alliance_by_code(self, code: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM alliances WHERE invite_code=?", (code,)).fetchone()
        return dict(row) if row else None

    def update_alliance(self, alliance_id: int, **values: Any) -> None:
        sets = ",".join(f"{k}=?" for k in values)
        self.conn.execute(f"UPDATE alliances SET {sets} WHERE id=?", [*values.values(), alliance_id])

    def delete_alliance(self, alliance_id: int) -> None:
        self.conn.execute("DELETE FROM alliances WHERE id=?", (alliance_id,))

    def alliances_by_points(self, limit: int) -> list[sqlite3.Row]:
        return list(self.conn.execute(
            "SELECT a.id, a.tag, a.name, COUNT(p.id) AS members, COALESCE(SUM(p.points),0) AS points "
            "FROM alliances a LEFT JOIN players p ON p.alliance_id=a.id GROUP BY a.id "
            "ORDER BY points DESC LIMIT ?", (limit,)))

    def alliance_tags(self, ids: Iterable[int]) -> dict[int, str]:
        ids = [i for i in set(ids) if i]
        if not ids:
            return {}
        marks = ",".join("?" for _ in ids)
        rows = self.conn.execute(f"SELECT id, tag FROM alliances WHERE id IN ({marks})", ids)
        return {r["id"]: r["tag"] for r in rows}

    # --- Attack log (bash limit) ----------------------------------------------

    def log_attack(self, attacker_id: int, target_planet_id: int, at: float) -> None:
        self._insert("attack_log", {"attacker_id": attacker_id, "target_planet_id": target_planet_id, "at": at})

    def attacks_since(self, attacker_id: int, target_planet_id: int, since: float) -> int:
        return self.conn.execute(
            "SELECT COUNT(*) FROM attack_log WHERE attacker_id=? AND target_planet_id=? AND at>=?",
            (attacker_id, target_planet_id, since)).fetchone()[0]

    def prune_attack_log(self, before: float) -> None:
        self.conn.execute("DELETE FROM attack_log WHERE at<?", (before,))

    # --- Meta -----------------------------------------------------------------

    def get_meta(self, key: str, default: str | None = None) -> str | None:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute("INSERT INTO meta (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                          (key, value))


def now() -> float:
    return time.time()
