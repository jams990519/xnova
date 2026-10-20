"""Settings: piloto/piloto.toml (a copy of piloto.example.toml with your data). It never goes to GitHub."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .plan import Goal, Target, parse_plan

HERE = Path(__file__).resolve().parent
SETTINGS = HERE / "piloto.toml"
DATA = HERE / "datos"  # session, state and logs; ignored by git

# Labels the pilot must never tap, whatever the settings say (normalized words).
FORBIDDEN = ("derribar", "demoler", "cancelar", "abandonar", "borrar", "eliminar", "vacaciones", "reubicar",
             "destruir", "vender", "comprar", "contratar", "pagar", "canjear", "regresa", "regresar", "retirar",
             "disolver", "expulsar", "salir")

DEFAULT_READING = {
    "recursos": {"metal": ["metal"], "cristal": ["cristal"], "deuterio": ["deuterio"],
                 "energia": ["energia", "energía"]},
    "ocupado": ["en construccion", "construyendo", "en cola", "investigando", "en curso", "tiempo restante",
                "termina", "terminara"],
    "exito": ["en cola", "comenzo", "comienza", "empezo", "construyendo", "investigando", "enviada", "enviado",
              "en camino", "despego", "despega", "agregado", "anadido", "en marcha", "iniciado"],
    "falta": ["no tienes", "insuficiente", "no alcanza", "no hay suficiente", "sin naves", "no hay naves",
              "cola llena", "cola esta llena", "maximo de flotas", "no hay ranuras", "ranuras ocupadas",
              "ya se esta construyendo", "ya hay una construccion", "ya estas investigando", "requisitos",
              "no cumples"],
    "bloqueado": ["escudo", "proteccion", "vacaciones", "no puedes atacar", "no se puede atacar",
                  "maximo de ataques", "limite de ataques", "demasiado debil", "demasiado fuerte", "inactividad"],
    "ranuras": ["flotas", "flota", "ranuras", "misiones", "slots"],
    "coste": ["coste", "costo", "cuesta", "precio"],
}

DEFAULT_LABELS = {
    "menu": "Menú", "edificios": "Edificios", "investigacion": "Investigación", "flotas": "Flotas",
    "mis_flotas": "Mis flotas",
    "construir": ["Construir", "Mejorar", "Ampliar", "Subir"],
    "investigar": ["Investigar", "Mejorar", "Subir"],
    "enviar": ["Repetir", "Enviar", "Atacar", "Lanzar"],
    "confirmar": ["Confirmar", "Sí, enviar", "Enviar flota"],
}


@dataclass
class BuildSettings:
    on: bool
    plan: list[Goal]
    max_queue: int = 1
    power_plant: str = ""
    look: int = 6  # how many missing things it checks per round, looking for one that is affordable


@dataclass
class FarmSettings:
    on: bool
    targets: list[Target]
    max_per_day: int = 5
    keep_free: int = 0


@dataclass
class Settings:
    api_id: int
    api_hash: str
    bot: str = "Xnova_Elite_bot"
    every_minutes: float = 10
    pause: float = 2.5  # seconds between taps, so the bot is not flooded
    wait: float = 15  # seconds to wait for the bot's answer
    build: BuildSettings = field(default_factory=lambda: BuildSettings(False, []))
    research: BuildSettings = field(default_factory=lambda: BuildSettings(False, []))
    farm: FarmSettings = field(default_factory=lambda: FarmSettings(False, []))
    saved_messages: bool = True  # a summary of each round with news to your Saved Messages
    labels: dict = field(default_factory=lambda: dict(DEFAULT_LABELS))
    reading: dict = field(default_factory=lambda: dict(DEFAULT_READING))

    def label_list(self, key: str) -> list[str]:
        value = self.labels[key]
        return [value] if isinstance(value, str) else list(value)


def load(path: Path = SETTINGS) -> Settings:
    if not path.is_file():
        raise SystemExit(
            f"Falta {path.name}. Copia piloto.example.toml como piloto.toml (en la carpeta piloto) y pon tu "
            "api_id y tu api_hash de my.telegram.org.")
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return from_dict(raw)


def from_dict(raw: dict) -> Settings:
    tg = raw.get("telegram", {})
    if not tg.get("api_id") or not tg.get("api_hash"):
        raise SystemExit("En piloto.toml faltan api_id y api_hash (sección [telegram]), de my.telegram.org.")
    pace = raw.get("ritmo", {})
    build, research, farm = raw.get("construir", {}), raw.get("investigar", {}), raw.get("farmear", {})
    labels = {**DEFAULT_LABELS, **raw.get("etiquetas", {})}
    reading = {**DEFAULT_READING, **{k: v for k, v in raw.get("lectura", {}).items() if k != "recursos"}}
    reading["recursos"] = {**DEFAULT_READING["recursos"], **raw.get("lectura", {}).get("recursos", {})}
    max_per_day = int(farm.get("max_ataques_por_dia", 5))
    if not 1 <= max_per_day <= 6:
        raise SystemExit("max_ataques_por_dia va de 1 a 6: el juego no deja más de 6 ataques al mismo planeta en 24 h.")
    return Settings(
        api_id=int(tg["api_id"]),
        api_hash=str(tg["api_hash"]),
        bot=str(tg.get("bot", "Xnova_Elite_bot")).lstrip("@"),
        every_minutes=float(pace.get("cada_minutos", 10)),
        pause=max(1.0, float(pace.get("pausa_segundos", 2.5))),
        wait=float(pace.get("espera_respuesta", 15)),
        build=BuildSettings(bool(build.get("activo", True)), parse_plan(build.get("plan", [])),
                            int(build.get("max_en_cola", 1)), str(build.get("planta_de_energia", "")),
                            max(1, int(build.get("revisar", 6)))),
        research=BuildSettings(bool(research.get("activo", True)), parse_plan(research.get("plan", [])),
                               int(research.get("max_en_cola", 1)), look=max(1, int(research.get("revisar", 6)))),
        farm=FarmSettings(bool(farm.get("activo", False)),
                          [Target(str(t["flota"]), str(t["coordenadas"])) for t in farm.get("objetivo", [])],
                          max_per_day, int(farm.get("dejar_libres", 0))),
        saved_messages=bool(raw.get("avisos", {}).get("mensajes_guardados", True)),
        labels=labels,
        reading=reading,
    )
