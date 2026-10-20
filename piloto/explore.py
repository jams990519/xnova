"""Explorer: walks the game's menus WITHOUT building, attacking or spending anything, and saves every screen.

The saved file (datos/pantallas.txt) shows how the game really writes things, to tune the reading
(`[lectura]` and `[etiquetas]` in piloto.toml).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .client import GameBot, NotAllowed, check_allowed
from .screen import Screen
from .text import norm

# Buttons that do something (not just show): the explorer never taps them.
ACTIONS = ("construir", "investigar", "mejorar", "ampliar", "subir", "enviar", "atacar", "espiar", "fabricar",
           "producir", "repetir", "guardar", "crear", "colonizar", "transportar", "recolectar", "reciclar",
           "interceptar", "mantener", "expedicion", "lanzar", "confirmar", "aceptar", "si", "no", "usar",
           "activar", "cambiar", "unirse", "unir", "invitar", "publicar", "ofrecer", "intercambiar", "apostar",
           "reclamar", "recoger", "buscar", "volver", "atras", "cerrar", "elegir", "seleccionar", "tomar",
           "defender", "promo", "canjear", "mandar")


def safe(label: str) -> bool:
    words = norm(label).split()
    if not words or any(w in ACTIONS for w in words):
        return False
    try:
        check_allowed(label)
    except NotAllowed:
        return False
    return True


class Recorder:
    def __init__(self, folder: Path):
        folder.mkdir(parents=True, exist_ok=True)
        self.jsonl = folder / "pantallas.jsonl"
        self.txt = folder / "pantallas.txt"
        for f in (self.jsonl, self.txt):
            f.write_text("", encoding="utf-8")
        self.count = 0

    def add(self, path: list[str], s: Screen) -> None:
        self.count += 1
        with self.jsonl.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ruta": path, "texto": s.text, "botones": s.buttons, "teclado": s.keyboard,
                                "aviso": s.alert, "t": time.time()}, ensure_ascii=False) + "\n")
        with self.txt.open("a", encoding="utf-8") as f:
            f.write(f"=== {' › '.join(path)}\n{s.text}\n")
            if s.alert:
                f.write(f"[aviso] {s.alert}\n")
            for row in s.buttons:
                f.write(f"[botones] {' | '.join(row)}\n")
            for row in s.keyboard:
                f.write(f"[teclado] {' | '.join(row)}\n")
            f.write("\n")


async def replay(game: GameBot, path: list[str]) -> Screen:
    """The first step is a key of the keyboard (sent as text); the rest are taps."""
    screen = await game.send(path[0])
    for label in path[1:]:
        found = screen.find(label)
        if found is None:
            raise LookupError(f"Ya no está el botón «{label}».")
        screen = await game.tap(screen, found)
    return screen


async def explore(game: GameBot, folder: Path, depth: int = 2, limit: int = 80, say=print) -> int:
    """Visit the keyboard keys and, from each, the buttons that only show things, `depth` taps deep."""
    rec = Recorder(folder)
    start = await game.send("/start")
    rec.add(["/start"], start)
    keys = [k for row in game.keyboard for k in row if safe(k)]
    queue: list[list[str]] = [[k] for k in keys]
    seen: set[str] = {norm(start.text)}
    while queue and rec.count < limit:
        path = queue.pop(0)
        try:
            screen = await replay(game, path)
        except (LookupError, TimeoutError, NotAllowed) as e:
            say(f"   (salto {' › '.join(path)}: {e})")
            continue
        say(f"📸 {' › '.join(path)}")
        rec.add(path, screen)
        key = norm(screen.text + " ".join(screen.labels))
        if key in seen:
            continue
        seen.add(key)
        if len(path) <= depth:
            queue += [[*path, label] for label in screen.labels if safe(label)]
    say(f"Listo: {rec.count} pantallas guardadas en {rec.txt}")
    return rec.count
