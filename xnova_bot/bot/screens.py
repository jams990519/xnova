"""Screens: text and buttons for every menu. No Telegram objects here.

Each function returns ``(html_text, rows)`` where rows is a list of button
rows and each button is ``(label, callback_data)``. Callback data stays
under Telegram's 64-byte limit.
"""
from __future__ import annotations

from ..data.elements import DEFENSE, ELEMENTS, OFFICERS, SHIP
from ..db import MOON, PLANET, Planet, Player
from ..engine import formulas
from ..game import EXPEDITION_POSITION, Game, GameError
from ..texts import (ATTACK, COLONIZE, DEPLOY, DESCRIPTIONS, EXPEDITION, HELP, MISSION_ICONS, MISSIONS, NAMES,
                     OFFICER_EFFECTS, OFFICER_NAMES, RECYCLE, RES_ICONS, SHORT, SPY, TRANSPORT, clock, coords,
                     cost_line, duration, esc, num, short_num, units_line)

Rows = list[list[tuple[str, str]]]
Screen = tuple[str, Rows]

MENU = [["🪐 Planeta", "🏗 Edificios", "🔬 Investigar"],
        ["🚀 Hangar", "🛡 Defensa", "🛰 Flota"],
        ["🌌 Galaxia", "📨 Informes", "🏆 Ranking"],
        ["🤝 Alianza", "🎖 Oficiales", "⚙️ Ajustes"]]
MENU_ROUTES = {"🪐 Planeta": "ov", "🏗 Edificios": "bld", "🔬 Investigar": "res", "🚀 Hangar": "shp",
               "🛡 Defensa": "def", "🛰 Flota": "flt", "🌌 Galaxia": "gal", "📨 Informes": "rep",
               "🏆 Ranking": "rank", "🤝 Alianza": "ally", "🎖 Oficiales": "off", "⚙️ Ajustes": "set"}

ICONS = {1: "🔩", 2: "💎", 3: "🧪", 4: "☀️", 12: "⚛️", 14: "🤖", 15: "🔬", 21: "🛠", 22: "📦", 23: "📦", 24: "🛢",
         31: "🧫", 33: "🌍", 34: "🏛", 41: "🌙", 42: "📡", 43: "🌀", 44: "🚀"}


def _rows(buttons: list[tuple[str, str]], per_row: int = 2) -> Rows:
    return [buttons[i:i + per_row] for i in range(0, len(buttons), per_row)]


def _missing_text(missing: dict[int, int]) -> str:
    return ", ".join(f"{NAMES[k]} {v}" for k, v in missing.items())


def header(game: Game, player: Player, planet: Planet) -> str:
    rates = game.rates(planet, player)
    caps = game.storage(planet, player)
    res = (planet.metal, planet.crystal, planet.deuterium)
    parts = []
    for i, value in enumerate(res):
        full = " (lleno)" if value >= caps[i] and not planet.is_moon else ""
        parts.append(f"{RES_ICONS[i]} {short_num(value)}{full}")
    line = " · ".join(parts)
    if not planet.is_moon:
        line += f" · ⚡ {num(rates['energy_produced'] - rates['energy_needed'])}"
    icon = "🌙" if planet.is_moon else "🪐"
    return f"{icon} <b>{esc(planet.name)}</b> {coords(*planet.coords)}\n{line}"


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def overview(game: Game, player: Player, planet: Planet) -> Screen:
    t = game.now()
    rates = game.rates(planet, player)
    caps = game.storage(planet, player)
    used, total = game.fields(planet)
    lines = [f"{'🌙' if planet.is_moon else '🪐'} <b>{esc(planet.name)}</b> {coords(*planet.coords)}",
             f"Campos {used}/{total} · 🌡 {planet.temp_min} °C a {planet.temp_max} °C", ""]
    for i, key in enumerate(("metal", "crystal", "deuterium")):
        value = getattr(planet, key)
        per_hour = "" if planet.is_moon else f" ({'+' if rates[key] >= 0 else ''}{num(rates[key])}/h)"
        full = " — <b>almacén lleno</b>" if value >= caps[i] and not planet.is_moon else ""
        lines.append(f"{RES_ICONS[i]} {('Metal', 'Cristal', 'Deuterio')[i]}: {num(value)}{per_hour}{full}")
    if not planet.is_moon:
        energy_free = rates["energy_produced"] - rates["energy_needed"]
        warn = " ⚠️ falta energía" if energy_free < 0 else ""
        lines.append(f"⚡ Energía: {num(energy_free)} libre ({num(rates['energy_produced'])} producida){warn}")
    lines.append("")
    if planet.build_id:
        lines.append(f"🏗 {NAMES[planet.build_id]} {planet.build_level} — termina en {duration(planet.build_end - t)}")
    else:
        lines.append("🏗 Sin construcciones.")
    if player.research_id:
        lines.append(f"🔬 {NAMES[player.research_id]} {player.research_level} — termina en "
                     f"{duration(player.research_end - t)}")
    else:
        lines.append("🔬 Sin investigación.")
    if planet.shipyard:
        item = planet.shipyard[0]
        left = sum(i["count"] - i["done"] for i in planet.shipyard)
        lines.append(f"🛠 Hangar: {num(left)} unidades en cola (ahora {NAMES[item['id']]}).")
    if planet.ships:
        lines.append(f"🚀 Naves: {units_line(planet.ships, short=True)}")
    incoming = game.db.fleets_against(player.id)
    if incoming:
        lines.append("")
        for f in incoming:
            sender = game.db.get_player(f.owner_id)
            icon = MISSION_ICONS.get(f.mission, "")
            alert = "⚠️ " if f.mission in (ATTACK, SPY) else ""
            lines.append(f"{alert}{icon} <b>{esc(sender.name if sender else '?')}</b> hacia "
                         f"{coords(*f.target, f.target_kind == MOON)} — llega en {duration(f.arrive - t)}")
    own = game.db.fleets_of(player.id)
    if own:
        lines.append(f"🛰 {len(own)} flota(s) tuya(s) en vuelo.")
    if player.vacation:
        lines.append("\n🏖 <b>Estás en modo vacaciones.</b>")
    rows: Rows = []
    planets = game.db.planets_of(player.id)
    if len(planets) > 1:
        rows += _rows([(("🌙 " if p.is_moon else "🪐 ") + p.name[:18] + (" ✅" if p.id == planet.id else ""),
                        f"p:{p.id}") for p in planets], 2)
    extra = [("🔄 Actualizar", "m:ov")]
    if not planet.is_moon:
        extra.append(("⚡ Producción", "m:prod"))
    extra.append(("✏️ Renombrar", "s:ren"))
    rows.append(extra)
    return "\n".join(lines), rows


def production_screen(game: Game, player: Player, planet: Planet) -> Screen:
    rates = game.rates(planet, player)
    lines = [header(game, player, planet), "",
             "<b>Producción</b>: baja una mina para ahorrar energía o deuterio.",
             f"Las minas trabajan al {round(rates['factor'] * 100)} % por la energía.", ""]
    rows: Rows = []
    for eid in (1, 2, 3, 4, 12, 212):
        level = planet.ships.get(212, 0) if eid == 212 else planet.level(eid)
        if not level:
            continue
        pct = planet.production.get(eid, 100)
        lines.append(f"{ICONS.get(eid, '🛰')} {NAMES[eid]} ({num(level)}): {pct} %")
        rows.append([(f"{NAMES[eid][:14]} −", f"pr:{eid}:{max(0, pct - 10)}"),
                     (f"{pct} %", "noop"), ("+", f"pr:{eid}:{min(100, pct + 10)}")])
    rows.append([("↩️ Volver", "m:ov")])
    return "\n".join(lines), rows


# ---------------------------------------------------------------------------
# Buildings and research
# ---------------------------------------------------------------------------

def _level_list(title: str, options: list[dict], current: tuple[int, int, float] | None, game: Game,
                prefix: str) -> tuple[list[str], list[tuple[str, str]]]:
    t = game.now()
    lines, buttons, locked = [title, ""], [], []
    if current:
        eid, level, end = current
        lines.append(f"⏳ <b>{NAMES[eid]} {level}</b> — termina en {duration(end - t)}")
        lines.append("")
    for o in options:
        if o["missing"]:
            locked.append(f"{NAMES[o['id']]} ({_missing_text(o['missing'])})")
            continue
        state = "✅" if o["affordable"] else "💸"
        if current and current[0] == o["id"]:
            state = "⏳"
        lines.append(f"{state} <b>{NAMES[o['id']]}</b> {o['level']} → {o['next']}\n"
                     f"    {cost_line(o['cost'], o['energy'])} · ⏱ {duration(o['seconds'])}")
        if not current:
            buttons.append((f"⬆️ {NAMES[o['id']][:20]} {o['next']}", f"{prefix}:{o['id']}"))
    if locked:
        lines += ["", "🔒 <b>Bloqueados:</b> " + "; ".join(locked)]
    return lines, buttons


def buildings(game: Game, player: Player, planet: Planet) -> Screen:
    options = game.building_options(player, planet)
    current = (planet.build_id, planet.build_level, planet.build_end) if planet.build_id else None
    used, total = game.fields(planet)
    lines, buttons = _level_list(f"{header(game, player, planet)}\n🏗 <b>Edificios</b> · campos {used}/{total}",
                                 options, current, game, "b")
    rows = _rows(buttons, 2)
    if current:
        rows.append([("✖️ Cancelar construcción", "bc")])
    rows.append([("🔄 Actualizar", "m:bld"), ("ℹ️ Qué hace cada uno", "info:b")])
    return "\n".join(lines), rows


def research(game: Game, player: Player, planet: Planet) -> Screen:
    if planet.is_moon or planet.level(31) < 1:
        return (f"{header(game, player, planet)}\n\n🔬 Necesitas un <b>Laboratorio</b> en este planeta para "
                f"investigar.", [[("🏗 Edificios", "m:bld")]])
    options = game.research_options(player, planet)
    current = None
    if player.research_id:
        current = (player.research_id, player.research_level, player.research_end)
    lines, buttons = _level_list(f"{header(game, player, planet)}\n🔬 <b>Investigación</b> "
                                 f"(laboratorio {game.lab_level(player, planet)})", options, current, game, "r")
    rows = _rows(buttons, 2)
    if current:
        rows.append([("✖️ Cancelar investigación", "rc")])
    rows.append([("🔄 Actualizar", "m:res"), ("ℹ️ Qué hace cada una", "info:r")])
    return "\n".join(lines), rows


def info(kind: str) -> Screen:
    ids = [e.id for e in ELEMENTS.values() if e.kind == ("building" if kind == "b" else "research")]
    lines = [f"ℹ️ <b>{'Edificios' if kind == 'b' else 'Investigaciones'}</b>", ""]
    lines += [f"• <b>{NAMES[i]}</b>: {DESCRIPTIONS.get(i, '')}" for i in ids]
    return "\n".join(lines), [[("↩️ Volver", "m:bld" if kind == "b" else "m:res")]]


# ---------------------------------------------------------------------------
# Shipyard
# ---------------------------------------------------------------------------

def units(game: Game, player: Player, planet: Planet, kind: str) -> Screen:
    title = "🚀 <b>Hangar: naves</b>" if kind == SHIP else "🛡 <b>Defensa</b>"
    lines = [header(game, player, planet), title, ""]
    if planet.level(21) < 1:
        lines.append("Necesitas un <b>Hangar</b> en este planeta.")
        return "\n".join(lines), [[("🏗 Edificios", "m:bld")]]
    if planet.shipyard:
        left = 0.0
        for i, item in enumerate(planet.shipyard):
            remaining = item["count"] - item["done"]
            left += remaining * item["unit"] - (item.get("progress", 0.0) if i == 0 else 0)
        first = planet.shipyard[0]
        lines.append("⏳ En cola: " + ", ".join(f"{num(i['count'] - i['done'])} {SHORT.get(i['id'], NAMES[i['id']])}"
                                               for i in planet.shipyard))
        lines.append(f"    siguiente {NAMES[first['id']]} en "
                     f"{duration(first['unit'] - first.get('progress', 0.0))}, todo en {duration(left)}")
        lines.append("")
    if kind == DEFENSE and planet.level(44):
        used, total = game.missile_slots(planet)
        lines.append(f"Silo: {used}/{total} espacios.")
    buttons, locked = [], []
    for o in game.unit_options(player, planet, kind):
        if o["missing"]:
            locked.append(f"{NAMES[o['id']]} ({_missing_text(o['missing'])})")
            continue
        element = ELEMENTS[o["id"]]
        stats = f"⚔️ {num(element.attack)} 🛡 {num(element.shield)} ❤️ {num(element.hull)}"
        if element.cargo and kind == SHIP:
            stats += f" 📦 {short_num(element.cargo)}"
        lines.append(f"<b>{NAMES[o['id']]}</b> · tienes {num(o['have'])}\n"
                     f"    {cost_line(o['cost'])} · ⏱ {duration(o['seconds'])}\n    {stats}")
        buttons.append((f"➕ {SHORT.get(o['id'], NAMES[o['id']])[:18]} (máx {short_num(o['max'])})",
                        f"u:{o['id']}"))
    if locked:
        lines += ["", "🔒 <b>Bloqueados:</b> " + "; ".join(locked)]
    rows = _rows(buttons, 2)
    rows.append([("🔄 Actualizar", "m:shp" if kind == SHIP else "m:def")])
    return "\n".join(lines), rows


def unit_picker(game: Game, player: Player, planet: Planet, element_id: int) -> Screen:
    most = game.max_units(planet, element_id)
    text = (f"{header(game, player, planet)}\n\n¿Cuántas unidades de <b>{NAMES[element_id]}</b>?\n"
            f"Cada una: {cost_line(ELEMENTS[element_id].cost)} · ⏱ "
            f"{duration(game.unit_time(player, planet, element_id))}\nPuedes pagar hasta <b>{num(most)}</b>.")
    options = [n for n in (1, 5, 10, 50, 100, 500, 1000) if n <= most]
    buttons = [(num(n), f"uq:{element_id}:{n}") for n in options]
    if most and most not in options:
        buttons.append((f"Máx ({short_num(most)})", f"uq:{element_id}:{most}"))
    rows = _rows(buttons, 4)
    rows.append([("✏️ Otra cantidad", f"ui:{element_id}"),
                 ("↩️ Volver", "m:shp" if ELEMENTS[element_id].kind == SHIP else "m:def")])
    return text, rows


# ---------------------------------------------------------------------------
# Fleets
# ---------------------------------------------------------------------------

def fleets(game: Game, player: Player) -> Screen:
    t = game.now()
    own = game.db.fleets_of(player.id)
    used, total = game.fleet_slots(player)
    lines = [f"🛰 <b>Flotas</b> · {used} de {total} en vuelo", ""]
    rows: Rows = []
    for i, f in enumerate(own, start=1):
        icon = MISSION_ICONS.get(f.mission, "")
        if f.state == "out":
            when = f"llega en {duration(f.arrive - t)}"
        elif f.state == "hold":
            when = f"explorando, termina en {duration((f.hold_until or t) - t)}"
        else:
            when = f"volviendo, llega en {duration(f.return_at - t)}"
        lines.append(f"{i}. {icon} {MISSIONS.get(f.mission, '?')} → {coords(*f.target, f.target_kind == MOON)} — {when}")
        lines.append(f"    {units_line(f.ships, short=True)}")
        cargo = (f.metal, f.crystal, f.deuterium)
        if any(cargo):
            lines.append("    " + " · ".join(f"{RES_ICONS[k]} {short_num(v)}" for k, v in enumerate(cargo) if v))
        if f.state in ("out", "hold"):
            rows.append([(f"↩️ Hacer volver la {i}", f"fr:{f.id}")])
    if not own:
        lines.append("No tienes flotas en vuelo.")
    incoming = game.db.fleets_against(player.id)
    if incoming:
        lines += ["", "<b>Flotas de otros jugadores que vienen hacia ti:</b>"]
        for f in incoming:
            attacker = game.db.get_player(f.owner_id)
            lines.append(f"{MISSION_ICONS.get(f.mission, '')} {esc(attacker.name if attacker else '?')} → "
                         f"{coords(*f.target, f.target_kind == MOON)} — {num(sum(f.ships.values()))} naves, "
                         f"llega en {duration(f.arrive - t)}")
    rows.insert(0, [("🚀 Enviar flota", "f:new")])
    rows.append([("🔄 Actualizar", "m:flt")])
    return "\n".join(lines), rows


def _flyable(planet: Planet) -> dict[int, int]:
    return {eid: n for eid, n in sorted(planet.ships.items()) if n > 0 and eid != 212}


def fleet_ships(game: Game, player: Player, planet: Planet, state: dict) -> Screen:
    available = _flyable(planet)
    chosen = state.get("ships", {})
    lines = [header(game, player, planet), "", "🚀 <b>Enviar flota · 1/4: elige las naves</b>"]
    target = state.get("target")
    if target:
        lines.append(f"Destino: {coords(*target, state.get('kind') == MOON)}"
                     + (f" · {MISSIONS[state['mission']]}" if state.get("mission") else ""))
    lines.append("")
    if not available:
        lines.append("No tienes naves en este planeta.")
        return "\n".join(lines), [[("✖️ Cancelar", "f:x")]]
    buttons = []
    for eid, have in available.items():
        pick = chosen.get(str(eid), chosen.get(eid, 0))
        lines.append(f"{'✅' if pick else '▫️'} {NAMES[eid]}: {num(pick)} de {num(have)}")
        buttons.append((f"{SHORT.get(eid, NAMES[eid])} {short_num(pick)}/{short_num(have)}", f"f:s:{eid}"))
    total = sum(int(v) for v in chosen.values())
    if total:
        ships = {int(k): int(v) for k, v in chosen.items() if int(v)}
        speed = formulas.fleet_speed(ships, player.research, player.officer(613))
        lines += ["", f"Carga: {num(formulas.cargo_capacity(ships))} · velocidad {num(speed)}"]
    rows = _rows(buttons, 2)
    rows.append([("Todas", "f:all"), ("Ninguna", "f:none")])
    rows.append([("✖️ Cancelar", "f:x"), ("➡️ Siguiente", "f:next")])
    return "\n".join(lines), rows


def fleet_pick(game: Game, player: Player, planet: Planet, element_id: int) -> Screen:
    have = planet.ships.get(element_id, 0)
    text = f"¿Cuántas <b>{NAMES[element_id]}</b> envías? Tienes {num(have)}."
    options = sorted({n for n in (1, 5, 10, 50, 100, 1000) if n < have} | {have})
    rows = _rows([(num(n) if n != have else f"Todas ({short_num(n)})", f"f:a:{element_id}:{n}") for n in options], 4)
    rows.append([("Ninguna", f"f:a:{element_id}:0"), ("✏️ Otra cantidad", f"f:i:{element_id}")])
    rows.append([("↩️ Volver", "f:ships")])
    return text, rows


def fleet_target(game: Game, player: Player, planet: Planet, state: dict) -> Screen:
    lines = ["🚀 <b>Enviar flota · 2/4: destino</b>", "",
             "Escribe las coordenadas, por ejemplo <code>1:23:8</code>.",
             "Para una luna agrega una L: <code>1:23:8L</code>. Para una expedición usa la posición 16.",
             "", "O elige uno de tus planetas:"]
    buttons = [(("🌙 " if p.is_moon else "🪐 ") + f"{p.name[:16]} {p.galaxy}:{p.system}:{p.position}",
                f"f:t:{p.galaxy}:{p.system}:{p.position}:{p.kind}")
               for p in game.db.planets_of(player.id) if p.id != planet.id]
    if player.tech(124):
        buttons.append((f"🌠 Expedición {planet.galaxy}:{planet.system}:16",
                        f"f:t:{planet.galaxy}:{planet.system}:16:{PLANET}"))
    rows = _rows(buttons, 1)
    rows.append([("↩️ Naves", "f:ships"), ("✖️ Cancelar", "f:x")])
    return "\n".join(lines), rows


def fleet_mission(game: Game, player: Player, planet: Planet, state: dict) -> Screen:
    ships = {int(k): int(v) for k, v in state["ships"].items() if int(v)}
    target, kind = tuple(state["target"]), state.get("kind", PLANET)
    options = game.missions_for(player, planet, ships, target, kind)
    dest = game.target_planet(target, kind)
    lines = ["🚀 <b>Enviar flota · 3/4: misión</b>", "", f"Destino: {coords(*target, kind == MOON)}"]
    if dest:
        owner = game.db.get_player(dest.owner_id)
        lines.append(f"{esc(dest.name)} de <b>{esc(owner.name if owner else '?')}</b>")
    elif target[2] == EXPEDITION_POSITION:
        lines.append("Espacio profundo")
    else:
        lines.append("Posición vacía")
    if not options:
        lines += ["", "No hay ninguna misión posible con esas naves en ese destino.",
                  "Para espiar se necesitan sondas; para colonizar, un colonizador; para reciclar, recicladores "
                  "y escombros."]
    rows = _rows([(f"{MISSION_ICONS[m]} {MISSIONS[m]}", f"f:mi:{m}") for m in options], 2)
    rows.append([("↩️ Destino", "f:next"), ("✖️ Cancelar", "f:x")])
    return "\n".join(lines), rows


def fleet_speed(game: Game, player: Player, planet: Planet, state: dict) -> Screen:
    ships = {int(k): int(v) for k, v in state["ships"].items() if int(v)}
    target, kind = tuple(state["target"]), state.get("kind", PLANET)
    lines = ["🚀 <b>Enviar flota · 4/4: velocidad</b>", "",
             "Más lento gasta mucho menos deuterio.", ""]
    buttons = []
    for speed in (100, 70, 50, 30, 10):
        try:
            plan = game.plan_fleet(player, planet, ships, target, kind, state["mission"], speed)
        except GameError as exc:
            return str(exc), [[("↩️ Volver", "f:ships")]]
        lines.append(f"{speed} %: ida {duration(plan.seconds)} · 🧪 {num(plan.fuel)}")
    for speed in range(100, 0, -10):
        buttons.append((f"{speed} %", f"f:sp:{speed}"))
    rows = _rows(buttons, 5)
    rows.append([("↩️ Misión", "f:mis"), ("✖️ Cancelar", "f:x")])
    return "\n".join(lines), rows


def fleet_cargo(game: Game, player: Player, planet: Planet, state: dict) -> Screen:
    ships = {int(k): int(v) for k, v in state["ships"].items() if int(v)}
    plan = game.plan_fleet(player, planet, ships, tuple(state["target"]), state.get("kind", PLANET),
                           state["mission"], state["speed"])
    free = plan.capacity - plan.fuel
    text = (f"{header(game, player, planet)}\n\n📦 <b>Carga</b>\nBodega libre: {num(free)} "
            f"(el combustible ocupa {num(plan.fuel)}).\n\n"
            f"Escribe la carga como <code>metal cristal deuterio</code>, por ejemplo <code>5000 2000 0</code>, "
            f"o elige:")
    rows = [[("Todo lo que quepa", "f:cg:all"), ("Nada", "f:cg:none")],
            [("Solo metal y cristal", "f:cg:mc")],
            [("↩️ Velocidad", "f:spd"), ("✖️ Cancelar", "f:x")]]
    return text, rows


def fill_cargo(planet: Planet, free: float, mode: str, fuel: float) -> tuple[int, int, int]:
    """Load resources in metal, crystal, deuterium order up to ``free`` capacity."""
    deut_available = max(0.0, planet.deuterium - fuel)
    available = [planet.metal, planet.crystal, deut_available if mode == "all" else 0.0]
    out = []
    left = max(0.0, free)
    for value in available:
        take = int(min(left, max(0.0, value)))
        out.append(take)
        left -= take
    return out[0], out[1], out[2]


def fleet_confirm(game: Game, player: Player, planet: Planet, state: dict) -> Screen:
    ships = {int(k): int(v) for k, v in state["ships"].items() if int(v)}
    target, kind = tuple(state["target"]), state.get("kind", PLANET)
    plan = game.plan_fleet(player, planet, ships, target, kind, state["mission"], state["speed"],
                           tuple(state.get("cargo", (0, 0, 0))))
    t = game.now()
    hold = game.s.expedition_hold_hours * 3600 / game.s.fleet_speed if plan.mission == EXPEDITION else 0
    lines = ["🚀 <b>Confirmar envío</b>", "",
             f"{MISSION_ICONS[plan.mission]} <b>{MISSIONS[plan.mission]}</b> → {coords(*target, kind == MOON)}",
             f"Naves: {units_line(ships)}",
             f"Velocidad {plan.speed} % · distancia {num(plan.distance)}",
             f"Llega en {duration(plan.seconds)} ({clock(t + plan.seconds, game.s.timezone)})",
             f"Vuelve en {duration(plan.seconds * 2 + hold)}" + (" (explora 1 h)" if hold else ""),
             f"Combustible: 🧪 {num(plan.fuel)}"]
    if any(plan.cargo):
        lines.append("Carga: " + " · ".join(f"{RES_ICONS[i]} {num(v)}" for i, v in enumerate(plan.cargo) if v))
    if plan.mission == DEPLOY:
        lines.append("Las naves se quedan en el destino.")
    rows = [[("🚀 Enviar", "f:go")], [("↩️ Velocidad", "f:spd"), ("✖️ Cancelar", "f:x")]]
    return "\n".join(lines), rows


# ---------------------------------------------------------------------------
# Galaxy
# ---------------------------------------------------------------------------

def galaxy(game: Game, player: Player, g: int, s: int) -> Screen:
    view = game.galaxy(g, s)
    g, s = view["galaxy"], view["system"]
    lines = [f"🌌 <b>Galaxia {g} · Sistema {s}</b>", "<pre>"]
    buttons = []
    for pos in range(1, 16):
        planet = view["planets"].get(pos)
        moon = "🌙" if pos in view["moons"] else ""
        debris = "♻️" if pos in view["debris"] else ""
        if planet:
            owner = view["owners"].get(planet.owner_id)
            name = esc(planet.name[:12])
            who = esc(owner.name[:12]) if owner else "?"
            tag = f"[{esc(view['tags'][owner.alliance_id])}]" if owner and owner.alliance_id in view["tags"] else ""
            marks = game.status_marks(owner, player) if owner else ""
            me = "★" if planet.owner_id == player.id else ""
            lines.append(f"{pos:>2} {name:<12}{moon}{debris} {me}{who}{tag}{marks}")
            buttons.append((f"{pos}", f"ga:{g}:{s}:{pos}"))
        elif debris:
            lines.append(f"{pos:>2} · {debris}")
            buttons.append((f"{pos}", f"ga:{g}:{s}:{pos}"))
        else:
            lines.append(f"{pos:>2} ·")
    lines.append("</pre>")
    lines.append("(i) 7 días inactivo · (I) 28 días · (v) vacaciones · (n) novato · (f) demasiado fuerte · ★ tú")
    rows = _rows(buttons, 8)
    rows.append([("⏪", f"g:{g - 1}:{s}"), ("◀️", f"g:{g}:{s - 1}"), ("🏠", "m:gal"),
                 ("▶️", f"g:{g}:{s + 1}"), ("⏩", f"g:{g + 1}:{s}")])
    extra = [("🔢 Ir a…", "g:ask")]
    if player.tech(124):
        extra.append(("🌠 Expedición", f"fs:{g}:{s}:{EXPEDITION_POSITION}:{PLANET}:{EXPEDITION}"))
    rows.append(extra)
    return "\n".join(lines), rows


def position(game: Game, player: Player, g: int, s: int, p: int) -> Screen:
    planet = game.db.planet_at(g, s, p, PLANET)
    moon = game.db.planet_at(g, s, p, MOON)
    debris = game.db.get_debris(g, s, p)
    lines = [f"📍 <b>Posición {coords(g, s, p)}</b>", ""]
    rows: Rows = []
    if planet:
        owner = game.db.get_player(planet.owner_id)
        tag = ""
        if owner and owner.alliance_id:
            alliance = game.db.get_alliance(owner.alliance_id)
            tag = f" [{esc(alliance['tag'])}]" if alliance else ""
        lines.append(f"🪐 {esc(planet.name)}")
        marks = game.status_marks(owner, player) if owner else ""
        lines.append(f"👤 <b>{esc(owner.name if owner else '?')}</b>{tag} {marks} · "
                     f"puesto {owner.rank if owner else '?'} · {num(owner.points if owner else 0)} puntos")
        if moon:
            lines.append(f"🌙 {esc(moon.name)}")
    else:
        lines.append("Posición vacía.")
    if any(debris):
        lines.append(f"♻️ Escombros: 🔩 {num(debris[0])} · 💎 {num(debris[1])}")
    if planet and planet.owner_id != player.id:
        rows.append([("🔭 Espiar (1 sonda)", f"spy:{g}:{s}:{p}:{PLANET}:1"),
                     ("🔭 5 sondas", f"spy:{g}:{s}:{p}:{PLANET}:5")])
        rows.append([("⚔️ Atacar", f"fs:{g}:{s}:{p}:{PLANET}:{ATTACK}"),
                     ("📦 Transportar", f"fs:{g}:{s}:{p}:{PLANET}:{TRANSPORT}")])
        if moon:
            rows.append([("🔭 Espiar luna", f"spy:{g}:{s}:{p}:{MOON}:1"),
                         ("⚔️ Atacar luna", f"fs:{g}:{s}:{p}:{MOON}:{ATTACK}")])
        rows.append([("✉️ Mensaje", f"msg:{planet.owner_id}")])
    elif planet:
        rows.append([("📦 Transportar", f"fs:{g}:{s}:{p}:{PLANET}:{TRANSPORT}"),
                     ("🛬 Desplegar", f"fs:{g}:{s}:{p}:{PLANET}:{DEPLOY}")])
    else:
        rows.append([("🌱 Colonizar", f"fs:{g}:{s}:{p}:{PLANET}:{COLONIZE}")])
    if any(debris):
        rows.append([("♻️ Reciclar", f"fs:{g}:{s}:{p}:{PLANET}:{RECYCLE}")])
    rows.append([("↩️ Volver al sistema", f"g:{g}:{s}")])
    return "\n".join(lines), rows


# ---------------------------------------------------------------------------
# Reports, ranking, alliance, officers, settings
# ---------------------------------------------------------------------------

def reports_list(game: Game, player: Player) -> Screen:
    rows_db = game.db.reports_of(player.id, 10)
    icons = {"battle": "⚔️", "spy": "🔭", "expedition": "🌠"}
    lines = ["📨 <b>Informes</b> (los 10 últimos)", ""]
    if not rows_db:
        lines.append("Todavía no tienes informes.")
    buttons = []
    for r in rows_db:
        label = f"{icons.get(r['kind'], '📄')} {r['title'][:40]}"
        lines.append(f"{label} — {clock(r['created_at'], game.s.timezone)}")
        buttons.append((label[:40], f"rp:{r['id']}"))
    rows = _rows(buttons, 1)
    rows.append([("🔄 Actualizar", "m:rep")])
    return "\n".join(lines), rows


def report_view(game: Game, player: Player, report: dict) -> Screen:
    rows: Rows = []
    if report["kind"] == "spy":
        g, s, p = report["data"]["target"]
        kind = report["data"]["kind"]
        rows.append([("⚡ Saqueo rápido", f"qr:{report['id']}"), ("⚔️ Atacar", f"fs:{g}:{s}:{p}:{kind}:{ATTACK}")])
        rows.append([("🔭 Espiar otra vez", f"spy:{g}:{s}:{p}:{kind}:1")])
    rows.append([("↩️ Informes", "m:rep")])
    return report["body"], rows


def ranking(game: Game, player: Player, page: int = 0) -> Screen:
    per = 15
    players = game.db.players_by_rank(per, page * per)
    tags = game.db.alliance_tags(p.alliance_id for p in players if p.alliance_id)
    lines = ["🏆 <b>Ranking de jugadores</b>", "<pre>"]
    for p in players:
        tag = f"[{tags[p.alliance_id]}]" if p.alliance_id in tags else ""
        me = "★" if p.id == player.id else " "
        lines.append(f"{p.rank:>3}{me}{esc(p.name[:14]):<14}{esc(tag):<8}{short_num(p.points):>7}")
    lines.append("</pre>")
    lines.append(f"Tú: puesto {player.rank} · {num(player.points)} puntos "
                 f"(🏗 {num(player.points_buildings)} · 🔬 {num(player.points_research)} · "
                 f"🚀 {num(player.points_fleet)} · 🛡 {num(player.points_defense)})")
    lines.append("<i>1 punto por cada 1.000 recursos gastados. Se actualiza cada pocos minutos.</i>")
    nav = []
    if page > 0:
        nav.append(("◀️", f"rk:{page - 1}"))
    if len(players) == per:
        nav.append(("▶️", f"rk:{page + 1}"))
    rows: Rows = [nav] if nav else []
    rows.append([("🤝 Alianzas", "rk:a"), ("🔄", f"rk:{page}")])
    return "\n".join(lines), rows


def alliance_ranking(game: Game, player: Player) -> Screen:
    lines = ["🤝 <b>Ranking de alianzas</b>", "<pre>"]
    for i, a in enumerate(game.db.alliances_by_points(15), start=1):
        lines.append(f"{i:>3} [{esc(a['tag']):<8}] {a['members']:>3} miembros {short_num(a['points']):>7}")
    lines.append("</pre>")
    return "\n".join(lines), [[("🏆 Jugadores", "rk:0")]]


def alliance(game: Game, player: Player) -> Screen:
    if not player.alliance_id:
        text = ("🤝 <b>Alianza</b>\n\nNo estás en ninguna alianza. Una alianza permite organizarse, "
                "avisarse ataques y mandar mensajes a todos.\n\nPara entrar a una, pide el código de invitación "
                "a un miembro.")
        return text, [[("➕ Crear alianza", "al:create"), ("🔑 Unirme con código", "al:join")]]
    data = game.db.get_alliance(player.alliance_id)
    members = game.db.alliance_members(player.alliance_id)
    lines = [f"🤝 <b>[{esc(data['tag'])}] {esc(data['name'])}</b>", f"{len(members)} miembros", ""]
    for m in members:
        crown = "👑 " if m.alliance_rank == "leader" else ""
        marks = game.status_marks(m, None)
        lines.append(f"{crown}{esc(m.name)} {marks} · {num(m.points)} puntos · {coords(*_home(game, m))}")
    rows: Rows = [[("📣 Mensaje a todos", "al:msg")]]
    if player.alliance_rank == "leader":
        lines += ["", f"🔑 Código de invitación: <code>{esc(data['invite_code'])}</code>",
                  "Compártelo con quien quieras sumar."]
        rows.append([("🔁 Nuevo código", "al:code"), ("👢 Expulsar", "al:kick")])
    rows.append([("🚪 Salir de la alianza", "al:leave")])
    return "\n".join(lines), rows


def _home(game: Game, player: Player) -> tuple[int, int, int]:
    planets = game.db.planets_of(player.id)
    return planets[0].coords if planets else (0, 0, 0)


def alliance_kick(game: Game, player: Player) -> Screen:
    members = [m for m in game.db.alliance_members(player.alliance_id) if m.id != player.id]
    rows = _rows([(f"👢 {m.name}", f"al:k:{m.id}") for m in members], 2)
    rows.append([("↩️ Volver", "m:ally")])
    return "¿A quién expulsas?", rows


def officers(game: Game, player: Player) -> Screen:
    lines = ["🎖 <b>Oficiales</b>", "",
             f"⛏ Minero nivel {player.lvl_miner} · experiencia {num(player.xp_miner)}/{num(player.lvl_miner * 5000)}",
             f"🏴‍☠️ Saqueador nivel {player.lvl_raid} · ataques {num(player.xp_raid)}/{num(player.lvl_raid * 10)}",
             f"🎟 Puntos de oficial: <b>{player.officer_points}</b>", "",
             "<i>La experiencia de minero sube al terminar minas y almacenes (1 por cada 1.000 recursos). "
             "La de saqueador, con cada ataque.</i>", ""]
    buttons = []
    for officer in OFFICERS.values():
        level = player.officer(officer.id)
        missing = game.officer_missing(player, officer.id)
        req = f" — requiere {', '.join(f'{OFFICER_NAMES[k]} {v}' for k, v in missing.items())}" if missing else ""
        lines.append(f"<b>{OFFICER_NAMES[officer.id]}</b> {level}/{officer.max_level}: "
                     f"{OFFICER_EFFECTS[officer.id]}{req}")
        if not missing and level < officer.max_level and player.officer_points > 0:
            buttons.append((f"➕ {OFFICER_NAMES[officer.id]}", f"o:{officer.id}"))
    rows = _rows(buttons, 2)
    rows.append([("🔄 Actualizar", "m:off")])
    return "\n".join(lines), rows


def settings_screen(game: Game, player: Player) -> Screen:
    vacation = "activado 🏖" if player.vacation else "desactivado"
    lines = ["⚙️ <b>Ajustes</b>", "",
             f"👤 {esc(player.name)}",
             f"🏖 Modo vacaciones: {vacation}",
             f"   Mínimo {num(game.s.vacation_min_hours)} horas. Nadie te puede atacar, pero no produces.",
             f"🔔 Avisos de construcciones e investigaciones: {'sí' if player.notify_builds else 'no'}",
             "   Los avisos de ataques y flotas llegan siempre.", "",
             f"🌌 Universo: {game.s.galaxies} galaxias × {game.s.systems} sistemas · economía ×{game.s.economy_speed:g}"
             f" · flotas ×{game.s.fleet_speed:g}"]
    rows = [[("🏖 Salir de vacaciones" if player.vacation else "🏖 Entrar en vacaciones", "s:vac")],
            [("🔔 Cambiar avisos", "s:ntf"), ("✏️ Renombrar planeta", "s:ren")],
            [("❓ Cómo se juega", "m:help")]]
    return "\n".join(lines), rows


def help_screen() -> Screen:
    return HELP, [[("🪐 Ir a mi planeta", "m:ov")]]
