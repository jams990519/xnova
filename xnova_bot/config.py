"""Settings read from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _float(name: str, default: float) -> float:
    value = os.environ.get(name, "").strip()
    return float(value) if value else default


def _int(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    return int(value) if value else default


@dataclass(frozen=True)
class Settings:
    token: str = ""
    db_path: str = "data/xnova.db"
    admin_ids: frozenset[int] = field(default_factory=frozenset)
    timezone: str = "UTC"
    # Universe
    galaxies: int = 3
    systems: int = 100
    economy_speed: float = 1.0
    fleet_speed: float = 1.0
    max_planets: int = 9
    # Fair play
    noob_ratio: float = 5.0
    noob_points_limit: float = 50_000
    bash_limit: int = 6
    vacation_min_hours: float = 48
    inactive_days: int = 7
    # Battles
    debris_ships: float = 0.3
    debris_defense: float = 0.0
    defense_rebuild: float = 0.7
    expedition_hold_hours: float = 1.0
    # Loop
    tick_seconds: float = 3.0
    ranking_minutes: float = 10.0


def load_settings() -> Settings:
    # On Railway, a volume attached to the service sets RAILWAY_VOLUME_MOUNT_PATH automatically.
    data_dir = (os.environ.get("DATA_DIR", "").strip() or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "").strip()
                or "data")
    db_path = os.environ.get("DB_PATH", "").strip() or str(Path(data_dir) / "xnova.db")
    admins = frozenset(int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x)
    return Settings(
        token=os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(),
        db_path=db_path,
        admin_ids=admins,
        timezone=os.environ.get("TIMEZONE", "UTC").strip() or "UTC",
        galaxies=_int("GALAXIES", 3),
        systems=_int("SYSTEMS", 100),
        economy_speed=_float("ECONOMY_SPEED", 1.0),
        fleet_speed=_float("FLEET_SPEED", 1.0),
        max_planets=_int("MAX_PLANETS", 9),
        noob_ratio=_float("NOOB_RATIO", 5.0),
        noob_points_limit=_float("NOOB_POINTS_LIMIT", 50_000),
        bash_limit=_int("BASH_LIMIT", 6),
        vacation_min_hours=_float("VACATION_MIN_HOURS", 48),
        debris_ships=_float("DEBRIS_SHIPS", 0.3),
        debris_defense=_float("DEBRIS_DEFENSE", 0.0),
        tick_seconds=_float("TICK_SECONDS", 3.0),
    )
