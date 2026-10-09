"""Entry point: python -m xnova_bot.main"""
from __future__ import annotations

import logging
import os
import sys

from .bot.handlers import build_application
from .config import load_settings
from .db import Database
from .game import Game

log = logging.getLogger("xnova_bot")


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = load_settings()
    if not settings.token:
        log.error("Falta la variable TELEGRAM_BOT_TOKEN con el token del bot (se pide a @BotFather).")
        sys.exit(1)
    if os.environ.get("RAILWAY_PROJECT_ID") and not (os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
                                                     or os.environ.get("DATA_DIR")):
        log.warning("⚠️ Sin volumen: las partidas se borran en cada despliegue. Conecta un volumen en Railway "
                    "(montado en /data) para guardarlas.")
    db = Database(settings.db_path)
    game = Game(db, settings)
    log.info("Base de datos en %s · universo %sx%s · economía x%s · flotas x%s", settings.db_path,
             settings.galaxies, settings.systems, settings.economy_speed, settings.fleet_speed)
    app = build_application(settings.token, game)
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
