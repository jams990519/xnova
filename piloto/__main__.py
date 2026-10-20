"""Piloto para @Xnova_Elite_bot, desde tu computadora.

    python -m piloto entrar                  la primera vez: entra con tu número y el código de Telegram
    python -m piloto explorar                recorre los menús sin tocar nada y guarda las pantallas
    python -m piloto jugar --ensayo --una-vez  dice lo que haría, sin hacerlo
    python -m piloto jugar                   juega solo cada N minutos (Ctrl+C para parar)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime

from . import config
from .client import TelegramGame
from .explore import explore
from .pilot import Pilot


def say(line: str) -> None:
    stamp = datetime.now().strftime("%d/%m %H:%M")
    print(f"[{stamp}] {line}", flush=True)
    config.DATA.mkdir(parents=True, exist_ok=True)
    with (config.DATA / "registro.txt").open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {line}\n")


async def connect(cfg: config.Settings):
    from telethon import TelegramClient

    config.DATA.mkdir(parents=True, exist_ok=True)
    client = TelegramClient(str(config.DATA / "cuenta"), cfg.api_id, cfg.api_hash)
    # The first time it asks, here in the terminal, for your phone, the code Telegram sends you and your
    # two-step password if you have one. Then it remembers the session in datos/cuenta.session.
    await client.start()
    return client


async def play(client, cfg: config.Settings, dry_run: bool, once: bool) -> None:
    game = TelegramGame(client, cfg.bot, cfg.pause, cfg.wait)
    await game.start()
    pilot = Pilot(game, cfg, config.DATA / "estado.json", dry_run=dry_run)
    say(f"▶️ Piloto en marcha con @{cfg.bot}{' (ensayo: no toca nada)' if dry_run else ''}. "
        f"Una vuelta cada {cfg.every_minutes:g} min.")
    while True:
        try:
            lines = await pilot.round()
        except (ConnectionError, OSError) as e:
            lines = [f"⚠️ Sin conexión ({e}); pruebo en la próxima vuelta."]
        for line in lines or ["· Nada que hacer en esta vuelta."]:
            say(line)
        if lines and cfg.saved_messages and not dry_run:
            try:
                await client.send_message("me", "🛰️ Piloto Xnova\n" + "\n".join(lines))
            except Exception as e:  # the summary is a nicety: never stop the pilot for it
                say(f"(no pude mandarte el resumen: {e})")
        if once:
            return
        await asyncio.sleep(cfg.every_minutes * 60)


async def run(args) -> None:
    cfg = config.load()
    client = await connect(cfg)
    try:
        if args.comando == "entrar":
            me = await client.get_me()
            say(f"✅ Listo: el piloto entra como {me.first_name}. La sesión quedó en piloto/datos/cuenta.session "
                "(no se la pases a nadie: da acceso a tu Telegram).")
        elif args.comando == "explorar":
            game = TelegramGame(client, cfg.bot, cfg.pause, cfg.wait)
            await game.start()
            await explore(game, config.DATA, depth=3 if args.profundo else 2, limit=200 if args.profundo else 80,
                          say=say)
        else:
            await play(client, cfg, args.ensayo, args.una_vez)
    finally:
        await client.disconnect()


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m piloto", description="Piloto para @Xnova_Elite_bot.")
    p.add_argument("comando", choices=["entrar", "explorar", "jugar"])
    p.add_argument("--ensayo", action="store_true", help="decide pero no construye ni envía nada")
    p.add_argument("--una-vez", action="store_true", help="una sola vuelta y termina")
    p.add_argument("--profundo", action="store_true", help="explorar un nivel más de menús")
    args = p.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n⏹️ Piloto detenido.")
        sys.exit(0)


if __name__ == "__main__":
    main()
