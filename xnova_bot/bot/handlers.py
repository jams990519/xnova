"""Telegram handlers: commands, buttons, typed answers and push notices."""
from __future__ import annotations

import asyncio
import functools
import logging
import re

from telegram import (BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update)
from telegram.constants import ChatType, ParseMode
from telegram.error import BadRequest, Forbidden, RetryAfter, TelegramError
from telegram.ext import (Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from ..data.elements import DEFENSE, SHIP
from ..db import MOON, PLANET
from ..game import EXPEDITION_POSITION, Game, GameError, Notice
from ..texts import (COLONIZE, DEPLOY, EXPEDITION, MISSIONS, NAMES, SPY, TRANSPORT, esc, num)
from . import screens as sc

log = logging.getLogger(__name__)

MAIN_KEYBOARD = ReplyKeyboardMarkup(sc.MENU, resize_keyboard=True, is_persistent=True)
COORDS_RE = re.compile(r"^\s*\[?(\d{1,3})\s*[:\s.,]\s*(\d{1,3})\s*[:\s.,]\s*(\d{1,2})\s*(l|L|luna|Luna)?\]?\s*$")
SYSTEM_RE = re.compile(r"^\s*\[?(\d{1,3})\s*[:\s.,]\s*(\d{1,3})\]?\s*$")
CARGO_MISSIONS = (TRANSPORT, DEPLOY, COLONIZE)
COMMANDS = [("start", "Empezar o volver al juego"), ("planeta", "Resumen del planeta"),
            ("edificios", "Construir"), ("investigar", "Investigar"), ("hangar", "Naves"),
            ("defensa", "Defensas"), ("flota", "Flotas en vuelo y enviar"), ("galaxia", "Ver la galaxia"),
            ("informes", "Informes de batalla y espionaje"), ("ranking", "Ranking"), ("alianza", "Alianza"),
            ("oficiales", "Oficiales"), ("ajustes", "Ajustes y vacaciones"), ("ayuda", "Cómo se juega")]
COMMAND_ROUTES = {"planeta": "ov", "menu": "ov", "edificios": "bld", "investigar": "res", "hangar": "shp",
                  "defensa": "def", "flota": "flt", "galaxia": "gal", "informes": "rep", "ranking": "rank",
                  "alianza": "ally", "oficiales": "off", "ajustes": "set", "ayuda": "help"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def game_of(context: ContextTypes.DEFAULT_TYPE) -> Game:
    return context.application.bot_data["game"]


def markup(rows) -> InlineKeyboardMarkup | None:
    if not rows:
        return None
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=data) for label, data in row]
                                 for row in rows if row])


def parse_amount(text: str) -> int:
    """'1.000', '1000', '2k', '1,5k', '3M' -> int."""
    raw = text.strip().lower().replace(" ", "")
    mult = 1
    if raw.endswith("k"):
        mult, raw = 1000, raw[:-1]
    elif raw.endswith("m"):
        mult, raw = 1_000_000, raw[:-1]
    if mult > 1:
        raw = raw.replace(",", ".")
        value = float(raw)
    else:
        value = float(raw.replace(".", "").replace(",", ""))
    if value < 0:
        raise ValueError
    return int(value * mult)


async def deliver(bot, game: Game, notices: list[Notice]) -> None:
    """Send notices to players. Players who blocked the bot are marked and skipped."""
    for notice in notices:
        player = game.player(notice.player_id)
        if not player or player.blocked:
            continue
        for attempt in range(2):
            try:
                await bot.send_message(player.chat_id, notice.text, parse_mode=ParseMode.HTML,
                                       reply_markup=markup(notice.buttons), disable_web_page_preview=True)
                break
            except RetryAfter as exc:
                await asyncio.sleep(exc.retry_after + 1)
            except Forbidden:
                game.set_blocked(player.id, True)
                break
            except TelegramError:
                log.exception("Could not send notice to %s", player.id)
                break
        await asyncio.sleep(0.04)


async def send(update: Update, text: str, rows=None, keyboard=None) -> None:
    reply_markup = markup(rows) if rows else keyboard
    await update.effective_chat.send_message(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup,
                                             disable_web_page_preview=True)


async def show(update: Update, screen: sc.Screen, edit: bool = False) -> None:
    text, rows = screen
    if edit and update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup(rows),
                                                          disable_web_page_preview=True)
            return
        except BadRequest as exc:
            if "not modified" in str(exc).lower():
                return
            log.debug("Edit failed, sending a new message: %s", exc)
    await send(update, text, rows)


def build_screen(game: Game, player_id: int, route: str) -> sc.Screen:
    if route == "help":
        return sc.help_screen()
    player, planet = game.view_planet(player_id)
    if route == "ov":
        return sc.overview(game, player, planet)
    if route == "prod":
        return sc.production_screen(game, player, planet)
    if route == "bld":
        return sc.buildings(game, player, planet)
    if route == "res":
        return sc.research(game, player, planet)
    if route == "shp":
        return sc.units(game, player, planet, SHIP)
    if route == "def":
        return sc.units(game, player, planet, DEFENSE)
    if route == "flt":
        return sc.fleets(game, player)
    if route == "gal":
        return sc.galaxy(game, player, planet.galaxy, planet.system)
    if route == "rep":
        return sc.reports_list(game, player)
    if route == "rank":
        return sc.ranking(game, player, max(0, (player.rank - 1) // 15))
    if route == "ally":
        return sc.alliance(game, player)
    if route == "off":
        return sc.officers(game, player)
    if route == "set":
        return sc.settings_screen(game, player)
    return sc.overview(game, player, planet)


def private_only(handler):
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        if chat is None:
            return
        if chat.type != ChatType.PRIVATE:
            if update.message:
                await update.message.reply_text("Este juego se juega por privado: ábreme y escribe /start.")
            return
        game = game_of(context)
        user = update.effective_user
        if user and game.player(user.id):
            game.mark_active(user.id)
        try:
            await handler(update, context)
        except GameError as exc:
            if update.callback_query:
                await update.callback_query.answer(str(exc)[:190], show_alert=True)
            else:
                await send(update, f"⚠️ {esc(exc)}")
        finally:
            await deliver(context.bot, game, game.take_notices())
    return wrapper


# ---------------------------------------------------------------------------
# Commands and typed text
# ---------------------------------------------------------------------------

@private_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = game_of(context)
    user = update.effective_user
    context.user_data.pop("await", None)
    if game.player(user.id):
        await send(update, "🚀 ¡De vuelta al mando!", keyboard=MAIN_KEYBOARD)
        await show(update, build_screen(game, user.id, "ov"))
        return
    context.user_data["await"] = {"kind": "register"}
    await send(update, "🌌 <b>Bienvenido a Xnova</b>\n\nUn juego de estrategia espacial por texto: construye minas, "
                       "investiga, arma flotas, espía y saquea a tus vecinos.\n\n"
                       "¿Cómo se llamará tu comandante? Escribe un nombre de 3 a 20 letras.")


@private_only
async def cmd_route(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = game_of(context)
    command = update.message.text.split()[0].lstrip("/").split("@")[0].lower()
    game.require_player(update.effective_user.id)
    context.user_data.pop("await", None)
    await show(update, build_screen(game, update.effective_user.id, COMMAND_ROUTES.get(command, "ov")))


@private_only
async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = game_of(context)
    if update.effective_user.id not in game.s.admin_ids:
        return
    stats = game.stats()
    await send(update, "🛠 <b>Estado del servidor</b>\n" + "\n".join(f"{k}: {num(v)}" for k, v in stats.items()))


@private_only
async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = game_of(context)
    if update.effective_user.id not in game.s.admin_ids:
        return
    text = update.message.text.partition(" ")[2].strip()
    if not text:
        await send(update, "Uso: /aviso texto para todos los jugadores")
        return
    notices = [Notice(p.id, f"📢 <b>Aviso</b>\n{esc(text)}") for p in game.db.all_players()]
    await send(update, f"Enviando a {len(notices)} jugadores…")
    await deliver(context.bot, game, notices)


@private_only
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = game_of(context)
    user = update.effective_user
    text = (update.message.text or "").strip()
    pending = context.user_data.get("await")
    if text.lower() in ("cancelar", "/cancelar"):
        context.user_data.pop("await", None)
        await send(update, "Cancelado.")
        return
    if text in sc.MENU_ROUTES:
        context.user_data.pop("await", None)
        game.require_player(user.id)
        await show(update, build_screen(game, user.id, sc.MENU_ROUTES[text]))
        return
    if pending:
        await handle_answer(update, context, pending, text)
        return
    player = game.player(user.id)
    if not player:
        await send(update, "Escribe /start para empezar.")
        return
    match = COORDS_RE.match(text)
    if match:
        g, s, p = (int(match.group(i)) for i in (1, 2, 3))
        await show(update, sc.position(game, player, g, s, p))
        return
    await send(update, "Usa el menú de abajo, o escribe unas coordenadas como <code>1:23:8</code>.",
               keyboard=MAIN_KEYBOARD)


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE, pending: dict, text: str) -> None:
    game = game_of(context)
    user = update.effective_user
    kind = pending["kind"]
    if kind == "register":
        player, planet = game.register(user.id, update.effective_chat.id, text)
        context.user_data.pop("await", None)
        await send(update, f"✅ Comandante <b>{esc(player.name)}</b>, tu planeta está en "
                           f"[{planet.galaxy}:{planet.system}:{planet.position}].\n\n"
                           f"Empieza subiendo la <b>Mina de metal</b> y la <b>Planta de energía solar</b>. "
                           f"Toca ❓ en ⚙️ Ajustes para ver cómo se juega.", keyboard=MAIN_KEYBOARD)
        await show(update, build_screen(game, user.id, "bld"))
        return
    if kind == "unit_amount":
        try:
            count = parse_amount(text)
        except ValueError:
            await send(update, "Escribe un número, por ejemplo 25.")
            return
        context.user_data.pop("await", None)
        player = game.require_player(user.id)
        planet, done = game.order_units(user.id, player.current_planet, pending["id"], count)
        await send(update, f"🛠 En cola: {num(done)} {NAMES[pending['id']]}.")
        route = "shp" if pending["id"] < 400 else "def"
        await show(update, build_screen(game, user.id, route))
        return
    if kind == "fleet_amount":
        try:
            count = parse_amount(text)
        except ValueError:
            await send(update, "Escribe un número, por ejemplo 25.")
            return
        context.user_data.pop("await", None)
        state = context.user_data.get("fleet")
        if not state:
            return
        origin = game.select_planet(user.id, state["planet"])
        state["ships"][str(pending["id"])] = min(count, origin.ships.get(pending["id"], 0))
        await show(update, fleet_screen(game, user.id, context, "ships"))
        return
    if kind == "fleet_target":
        match = COORDS_RE.match(text)
        if not match:
            await send(update, "Escribe las coordenadas así: <code>1:23:8</code> (o <code>1:23:8L</code> para luna).")
            return
        context.user_data.pop("await", None)
        state = context.user_data.get("fleet")
        if not state:
            return
        state["target"] = [int(match.group(i)) for i in (1, 2, 3)]
        state["kind"] = MOON if match.group(4) else PLANET
        if state["target"][2] == EXPEDITION_POSITION:
            state["mission"] = EXPEDITION
            await show(update, fleet_screen(game, user.id, context, "speed"))
        else:
            state.pop("mission", None)
            await show(update, fleet_screen(game, user.id, context, "mission"))
        return
    if kind == "fleet_cargo":
        parts = re.split(r"[\s;/]+", text.strip())
        try:
            values = [parse_amount(p) for p in parts if p]
        except ValueError:
            await send(update, "Escribe tres números: metal cristal deuterio. Ejemplo: <code>5000 2000 0</code>")
            return
        values = (values + [0, 0, 0])[:3]
        context.user_data.pop("await", None)
        state = context.user_data.get("fleet")
        if not state:
            return
        state["cargo"] = values
        await show(update, fleet_screen(game, user.id, context, "confirm"))
        return
    if kind == "galaxy":
        match = SYSTEM_RE.match(text) or COORDS_RE.match(text)
        if not match:
            await send(update, "Escribe galaxia y sistema así: <code>1:23</code>")
            return
        context.user_data.pop("await", None)
        player = game.require_player(user.id)
        await show(update, sc.galaxy(game, player, int(match.group(1)), int(match.group(2))))
        return
    if kind == "rename":
        context.user_data.pop("await", None)
        player = game.require_player(user.id)
        planet = game.rename_planet(user.id, pending.get("planet") or player.current_planet, text)
        await send(update, f"✏️ Ahora se llama <b>{esc(planet.name)}</b>.")
        return
    if kind == "ally_create":
        tag, _, name = text.partition(" ")
        context.user_data.pop("await", None)
        alliance = game.create_alliance(user.id, tag, name or tag)
        await send(update, f"🤝 Alianza <b>[{esc(alliance['tag'])}] {esc(alliance['name'])}</b> creada.\n"
                           f"Código para invitar: <code>{esc(alliance['invite_code'])}</code>")
        return
    if kind == "ally_join":
        context.user_data.pop("await", None)
        alliance, notices = game.join_alliance(user.id, text)
        await deliver(context.bot, game, notices)
        await send(update, f"🤝 Ahora eres parte de <b>[{esc(alliance['tag'])}] {esc(alliance['name'])}</b>.")
        return
    if kind == "ally_msg":
        context.user_data.pop("await", None)
        notices = game.alliance_broadcast(user.id, text)
        await deliver(context.bot, game, notices)
        await send(update, f"📣 Mensaje enviado a {len(notices)} miembros.")
        return
    if kind == "private_msg":
        context.user_data.pop("await", None)
        notice = game.private_message(user.id, pending["to"], text)
        await deliver(context.bot, game, [notice])
        await send(update, "✉️ Mensaje enviado.")
        return
    context.user_data.pop("await", None)


# ---------------------------------------------------------------------------
# Fleet dispatch flow
# ---------------------------------------------------------------------------

def fleet_screen(game: Game, player_id: int, context, step: str) -> sc.Screen:
    state = context.user_data.get("fleet")
    player = game.require_player(player_id)
    if not state:
        return sc.fleets(game, player)
    planet = game.db.get_planet(state["planet"])
    if not planet or planet.owner_id != player_id:
        context.user_data.pop("fleet", None)
        return sc.fleets(game, player)
    game.refresh(planet, game.now(), player)
    if step == "ships":
        return sc.fleet_ships(game, player, planet, state)
    if step == "target":
        context.user_data["await"] = {"kind": "fleet_target"}
        return sc.fleet_target(game, player, planet, state)
    if step == "mission":
        return sc.fleet_mission(game, player, planet, state)
    if step == "speed":
        return sc.fleet_speed(game, player, planet, state)
    if step == "cargo":
        context.user_data["await"] = {"kind": "fleet_cargo"}
        return sc.fleet_cargo(game, player, planet, state)
    return sc.fleet_confirm(game, player, planet, state)


def _ships_of(state: dict) -> dict[int, int]:
    return {int(k): int(v) for k, v in state.get("ships", {}).items() if int(v)}


async def fleet_action(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list[str]) -> str | None:
    game = game_of(context)
    user = update.effective_user
    query = update.callback_query
    action = parts[1]
    player = game.require_player(user.id)
    if action == "new":
        context.user_data["fleet"] = {"planet": player.current_planet, "ships": {}}
        await show(update, fleet_screen(game, user.id, context, "ships"), edit=True)
        return None
    state = context.user_data.get("fleet")
    if not state:
        await show(update, sc.fleets(game, player), edit=True)
        return "Ese envío ya no está abierto."
    planet = game.db.get_planet(state["planet"])
    game.refresh(planet, game.now(), player)
    if action == "x":
        context.user_data.pop("fleet", None)
        context.user_data.pop("await", None)
        await show(update, sc.fleets(game, player), edit=True)
        return "Envío cancelado."
    if action == "s":
        await show(update, sc.fleet_pick(game, player, planet, int(parts[2])), edit=True)
        return None
    if action == "a":
        eid, count = int(parts[2]), int(parts[3])
        state["ships"][str(eid)] = min(count, planet.ships.get(eid, 0))
        await show(update, fleet_screen(game, user.id, context, "ships"), edit=True)
        return None
    if action == "i":
        context.user_data["await"] = {"kind": "fleet_amount", "id": int(parts[2])}
        await query.message.reply_text(f"Escribe cuántas {NAMES[int(parts[2])]} envías.")
        return None
    if action == "all":
        state["ships"] = {str(k): v for k, v in sc._flyable(planet).items()}
        await show(update, fleet_screen(game, user.id, context, "ships"), edit=True)
        return None
    if action == "none":
        state["ships"] = {}
        await show(update, fleet_screen(game, user.id, context, "ships"), edit=True)
        return None
    if action == "ships":
        context.user_data.pop("await", None)
        await show(update, fleet_screen(game, user.id, context, "ships"), edit=True)
        return None
    if not _ships_of(state):
        return "Elige al menos una nave."
    if action == "next":
        if state.get("target") and state.get("mission"):
            await show(update, fleet_screen(game, user.id, context, "speed"), edit=True)
        elif state.get("target"):
            await show(update, fleet_screen(game, user.id, context, "mission"), edit=True)
        else:
            await show(update, fleet_screen(game, user.id, context, "target"), edit=True)
        return None
    if action == "t":
        context.user_data.pop("await", None)
        state["target"] = [int(parts[2]), int(parts[3]), int(parts[4])]
        state["kind"] = int(parts[5])
        if state["target"][2] == EXPEDITION_POSITION:
            state["mission"] = EXPEDITION
            await show(update, fleet_screen(game, user.id, context, "speed"), edit=True)
        else:
            state.pop("mission", None)
            await show(update, fleet_screen(game, user.id, context, "mission"), edit=True)
        return None
    if action == "mis":
        await show(update, fleet_screen(game, user.id, context, "mission"), edit=True)
        return None
    if action == "mi":
        state["mission"] = int(parts[2])
        await show(update, fleet_screen(game, user.id, context, "speed"), edit=True)
        return None
    if action == "spd":
        context.user_data.pop("await", None)
        await show(update, fleet_screen(game, user.id, context, "speed"), edit=True)
        return None
    if action == "sp":
        state["speed"] = int(parts[2])
        step = "cargo" if state.get("mission") in CARGO_MISSIONS else "confirm"
        state.pop("cargo", None)
        await show(update, fleet_screen(game, user.id, context, step), edit=True)
        return None
    if action == "cg":
        context.user_data.pop("await", None)
        plan = game.plan_fleet(player, planet, _ships_of(state), tuple(state["target"]), state.get("kind", PLANET),
                               state["mission"], state["speed"])
        mode = parts[2]
        state["cargo"] = [0, 0, 0] if mode == "none" else list(
            sc.fill_cargo(planet, plan.capacity - plan.fuel, mode, plan.fuel))
        await show(update, fleet_screen(game, user.id, context, "confirm"), edit=True)
        return None
    if action == "go":
        fleet, notices = game.send_fleet(user.id, state["planet"], _ships_of(state), tuple(state["target"]),
                                         state.get("kind", PLANET), state["mission"], state.get("speed", 100),
                                         tuple(state.get("cargo", (0, 0, 0))))
        context.user_data.pop("fleet", None)
        context.user_data.pop("await", None)
        await deliver(context.bot, game, notices)
        await show(update, sc.fleets(game, game.require_player(user.id)), edit=True)
        return f"🚀 Flota enviada: {MISSIONS[fleet.mission]}."
    return None


# ---------------------------------------------------------------------------
# Buttons
# ---------------------------------------------------------------------------

@private_only
async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    game = game_of(context)
    query = update.callback_query
    user = update.effective_user
    data = query.data or ""
    parts = data.split(":")
    head = parts[0]
    toast: str | None = None
    if data == "noop":
        await query.answer()
        return
    game.require_player(user.id)
    if head == "m":
        context.user_data.pop("await", None)
        await show(update, build_screen(game, user.id, parts[1]), edit=True)
    elif head == "p":
        planet = game.select_planet(user.id, int(parts[1]))
        toast = f"Planeta: {planet.name}"
        await show(update, build_screen(game, user.id, "ov"), edit=True)
    elif head == "b":
        player = game.require_player(user.id)
        game.start_build(user.id, player.current_planet, int(parts[1]))
        toast = f"Construyendo {NAMES[int(parts[1])]}."
        await show(update, build_screen(game, user.id, "bld"), edit=True)
    elif head == "bc":
        player = game.require_player(user.id)
        game.cancel_build(user.id, player.current_planet)
        toast = "Construcción cancelada. Se devolvieron los recursos."
        await show(update, build_screen(game, user.id, "bld"), edit=True)
    elif head == "r":
        player = game.require_player(user.id)
        game.start_research(user.id, player.current_planet, int(parts[1]))
        toast = f"Investigando {NAMES[int(parts[1])]}."
        await show(update, build_screen(game, user.id, "res"), edit=True)
    elif head == "rc":
        game.cancel_research(user.id)
        toast = "Investigación cancelada. Se devolvieron los recursos."
        await show(update, build_screen(game, user.id, "res"), edit=True)
    elif head == "info":
        await show(update, sc.info(parts[1]), edit=True)
    elif head == "u":
        player, planet = game.view_planet(user.id)
        await show(update, sc.unit_picker(game, player, planet, int(parts[1])), edit=True)
    elif head == "uq":
        player = game.require_player(user.id)
        eid = int(parts[1])
        _, done = game.order_units(user.id, player.current_planet, eid, int(parts[2]))
        toast = f"En cola: {num(done)} {NAMES[eid]}."
        await show(update, build_screen(game, user.id, "shp" if eid < 400 else "def"), edit=True)
    elif head == "ui":
        context.user_data["await"] = {"kind": "unit_amount", "id": int(parts[1])}
        await query.message.reply_text(f"Escribe cuántas unidades de {NAMES[int(parts[1])]} quieres.")
    elif head == "pr":
        player = game.require_player(user.id)
        game.set_production(user.id, player.current_planet, int(parts[1]), int(parts[2]))
        await show(update, build_screen(game, user.id, "prod"), edit=True)
    elif head == "fr":
        game.recall_fleet(user.id, int(parts[1]))
        toast = "La flota vuelve a casa."
        await show(update, sc.fleets(game, game.require_player(user.id)), edit=True)
    elif head == "f":
        toast = await fleet_action(update, context, parts)
    elif head == "fs":
        g, s, p, kind, mission = (int(x) for x in parts[1:6])
        player = game.require_player(user.id)
        context.user_data["fleet"] = {"planet": player.current_planet, "ships": {}, "target": [g, s, p],
                                      "kind": kind, "mission": mission}
        await show(update, fleet_screen(game, user.id, context, "ships"), edit=False)
    elif head == "spy":
        g, s, p, kind, count = (int(x) for x in parts[1:6])
        player, planet = game.view_planet(user.id)
        probes = min(count, planet.ships.get(210, 0))
        if not probes:
            raise GameError("No tienes sondas de espionaje en este planeta. Constrúyelas en el 🚀 Hangar.")
        fleet, notices = game.send_fleet(user.id, planet.id, {210: probes}, (g, s, p), kind, SPY, 100)
        await deliver(context.bot, game, notices)
        toast = f"🔭 {probes} sonda(s) en camino. El informe llega en unos segundos."
    elif head == "g":
        player, planet = game.view_planet(user.id)
        if parts[1] == "ask":
            context.user_data["await"] = {"kind": "galaxy"}
            await query.message.reply_text("Escribe galaxia y sistema, por ejemplo 1:23")
        else:
            await show(update, sc.galaxy(game, player, int(parts[1]), int(parts[2])), edit=True)
    elif head == "ga":
        player = game.require_player(user.id)
        await show(update, sc.position(game, player, int(parts[1]), int(parts[2]), int(parts[3])), edit=True)
    elif head == "rp":
        player = game.require_player(user.id)
        report = game.db.get_report(int(parts[1]))
        if not report or report["player_id"] != user.id:
            raise GameError("Ese informe ya no existe.")
        await show(update, sc.report_view(game, player, report), edit=True)
    elif head == "qr":
        fleet, notices = game.quick_raid(user.id, int(parts[1]))
        await deliver(context.bot, game, notices)
        toast = f"⚡ Saqueo en camino con {num(sum(fleet.ships.values()))} naves de carga."
    elif head == "rk":
        player = game.require_player(user.id)
        screen = sc.alliance_ranking(game, player) if parts[1] == "a" else sc.ranking(game, player, int(parts[1]))
        await show(update, screen, edit=True)
    elif head == "al":
        toast = await alliance_action(update, context, parts)
    elif head == "o":
        game.hire_officer(user.id, int(parts[1]))
        toast = "Oficial contratado."
        await show(update, build_screen(game, user.id, "off"), edit=True)
    elif head == "s":
        toast = await settings_action(update, context, parts[1])
    elif head == "msg":
        target = game.player(int(parts[1]))
        if not target:
            raise GameError("Ese jugador no existe.")
        context.user_data["await"] = {"kind": "private_msg", "to": target.id}
        await query.message.reply_text(f"Escribe el mensaje para {target.name} (o 'cancelar').")
    await query.answer(toast[:190] if toast else None)


async def alliance_action(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list[str]) -> str | None:
    game = game_of(context)
    user = update.effective_user
    query = update.callback_query
    action = parts[1]
    if action == "create":
        context.user_data["await"] = {"kind": "ally_create"}
        await query.message.reply_text("Escribe la etiqueta (2 a 8 letras o números) y el nombre. "
                                       "Ejemplo: NOVA Imperio Nova")
    elif action == "join":
        context.user_data["await"] = {"kind": "ally_join"}
        await query.message.reply_text("Escribe el código de invitación.")
    elif action == "msg":
        context.user_data["await"] = {"kind": "ally_msg"}
        await query.message.reply_text("Escribe el mensaje para toda la alianza.")
    elif action == "leave":
        notices = game.leave_alliance(user.id)
        await deliver(context.bot, game, notices)
        await show(update, build_screen(game, user.id, "ally"), edit=True)
        return "Saliste de la alianza."
    elif action == "code":
        game.new_invite_code(user.id)
        await show(update, build_screen(game, user.id, "ally"), edit=True)
        return "Código nuevo creado. El anterior ya no sirve."
    elif action == "kick":
        await show(update, sc.alliance_kick(game, game.require_player(user.id)), edit=True)
    elif action == "k":
        notices = game.kick_member(user.id, int(parts[2]))
        await deliver(context.bot, game, notices)
        await show(update, build_screen(game, user.id, "ally"), edit=True)
        return "Jugador expulsado."
    return None


async def settings_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> str | None:
    game = game_of(context)
    user = update.effective_user
    if action == "vac":
        player = game.require_player(user.id)
        player = game.set_vacation(user.id, not player.vacation)
        await show(update, build_screen(game, user.id, "set"), edit=True)
        return "Modo vacaciones activado." if player.vacation else "Bienvenido de vuelta."
    if action == "ntf":
        player = game.toggle_notifications(user.id)
        await show(update, build_screen(game, user.id, "set"), edit=True)
        return "Avisos activados." if player.notify_builds else "Avisos desactivados."
    if action == "ren":
        player = game.require_player(user.id)
        context.user_data["await"] = {"kind": "rename", "planet": player.current_planet}
        await update.callback_query.message.reply_text("Escribe el nuevo nombre del planeta.")
    return None


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Unhandled error", exc_info=context.error)
    if isinstance(update, Update) and update.effective_chat:
        try:
            await update.effective_chat.send_message("😵 Algo salió mal. Ya quedó registrado; intenta de nuevo.")
        except TelegramError:
            pass


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

async def _ticker(app: Application) -> None:
    game: Game = app.bot_data["game"]
    while True:
        try:
            notices = game.tick()
            if notices:
                await deliver(app.bot, game, notices)
        except asyncio.CancelledError:
            raise
        except Exception:  # keep the universe running
            log.exception("Tick failed")
        await asyncio.sleep(game.s.tick_seconds)


async def _post_init(app: Application) -> None:
    try:
        await app.bot.set_my_commands([BotCommand(c, d) for c, d in COMMANDS])
    except TelegramError:
        log.warning("Could not set the command list")
    app.bot_data["ticker"] = asyncio.get_running_loop().create_task(_ticker(app))
    log.info("Xnova bot started")


async def _post_shutdown(app: Application) -> None:
    task = app.bot_data.get("ticker")
    if task:
        task.cancel()
    game: Game = app.bot_data.get("game")
    if game:
        game.db.close()


def build_application(token: str, game: Game, request=None) -> Application:
    """Wire the handlers. ``request`` lets tests plug in a fake Telegram API."""
    builder = ApplicationBuilder().token(token).post_init(_post_init).post_shutdown(_post_shutdown)
    if request is not None:
        builder = builder.request(request).get_updates_request(request)
    app = builder.build()
    app.bot_data["game"] = game
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("aviso", cmd_broadcast))
    app.add_handler(CommandHandler(list(COMMAND_ROUTES), cmd_route))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    return app
