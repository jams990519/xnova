"""Text of battle, espionage and expedition reports (Telegram HTML)."""
from __future__ import annotations

from .data.elements import DEFENSE, ELEMENTS
from .db import Fleet, Planet, Player
from .engine.combat import BattleResult, ships_needed_for
from .engine.missions import SPY_BUILDINGS, SPY_DEFENSE, SPY_FLEET, SPY_RESEARCH, ExpeditionOutcome
from .texts import NAMES, RES_ICONS, clock, coords, duration, esc, num

MAX_LEN = 3900


def planet_label(planet: Planet) -> str:
    return f"<b>{esc(planet.name)}</b> {coords(*planet.coords, planet.is_moon)}"


def fmt_target(fleet: Fleet) -> str:
    return coords(*fleet.target, fleet.target_kind == 3)


def fmt_origin(fleet: Fleet) -> str:
    return coords(*fleet.origin, fleet.origin_kind == 3)


def cargo_text(cargo) -> str:
    parts = [f"{RES_ICONS[i]} {num(v)}" for i, v in enumerate(cargo) if v]
    return "Carga: " + (" · ".join(parts) if parts else "nada")


def units_text(units: dict[int, int]) -> str:
    items = [f"{num(n)} {NAMES[eid]}" for eid, n in units.items() if n > 0]
    return ", ".join(items) if items else "nada"


def incoming_attack(attacker: Player, target: Planet, fleet: Fleet, t: float, tz: str) -> str:
    ships = sum(fleet.ships.values())
    return (f"⚠️ <b>¡Ataque en camino!</b>\n"
            f"<b>{esc(attacker.name)}</b> envió {num(ships)} naves contra {planet_label(target)}.\n"
            f"Llega en {duration(fleet.arrive - t)} ({clock(fleet.arrive, tz)}).\n"
            f"Esconde tu flota y gasta tus recursos si no puedes defenderte.")


def battle(attacker: Player, defender: Player, target: Planet, result: BattleResult, loot, debris_mc,
           moon_chance: int, moon_created: bool, rebuilt: dict[int, int], t: float, tz: str) -> tuple[str, str]:
    title = f"Batalla en {target.name} {coords(*target.coords, target.is_moon)}"
    winner = {"attacker": f"🏆 Gana <b>{esc(attacker.name)}</b> (atacante).",
              "defender": f"🛡 Gana <b>{esc(defender.name)}</b> (defensor).",
              "draw": "🤝 Empate."}[result.winner]
    lines = [f"⚔️ <b>{esc(title)}</b>", f"<i>{clock(t, tz)}</i>", ""]

    def side(label: str, player: Player, start: dict[int, int], left: dict[int, int]) -> None:
        lines.append(f"<b>{label}: {esc(player.name)}</b>")
        if not start:
            lines.append("  sin naves ni defensas")
        for eid, n in sorted(start.items()):
            remain = left.get(eid, 0)
            extra = f" (se reconstruyen {num(rebuilt[eid])})" if eid in rebuilt else ""
            lines.append(f"  {NAMES[eid]}: {num(n)} → {num(remain)}{extra}")

    side("Atacante", attacker, result.attacker_start, result.attacker_left)
    side("Defensor", defender, result.defender_start, result.defender_left)
    if result.rounds:
        lines.append("")
    for i, r in enumerate(result.rounds, start=1):
        lines.append(f"Ronda {i}: el atacante dispara {num(r.attacker_shots)} veces "
                     f"({num(r.attacker_damage)} de daño); el defensor {num(r.defender_shots)} "
                     f"({num(r.defender_damage)}).")
    if result.scaled:
        lines.append("<i>Batalla muy grande: se simuló a escala.</i>")
    lines += ["", winner]
    if any(loot):
        lines.append("💰 Botín: " + " · ".join(f"{RES_ICONS[i]} {num(v)}" for i, v in enumerate(loot) if v))
    if any(debris_mc):
        lines.append(f"♻️ Escombros: 🔩 {num(debris_mc[0])} · 💎 {num(debris_mc[1])}")
    if moon_chance:
        lines.append(f"🌙 Probabilidad de luna: {moon_chance} %" + (" — <b>¡nació una luna!</b>" if moon_created else ""))
    body = "\n".join(lines)
    return title, body[:MAX_LEN]


def spy(attacker: Player, defender: Player, target: Planet, depth: int, chance: int, destroyed: bool,
        debris_mc, inactive: bool, long_inactive: bool, t: float, tz: str) -> tuple[str, str]:
    mark = " (I)" if long_inactive else (" (i)" if inactive else "")
    title = f"Espionaje de {target.name} {coords(*target.coords, target.is_moon)}"
    res = (target.metal, target.crystal, target.deuterium)
    lines = [f"🔭 <b>{esc(title)}</b>", f"Jugador: <b>{esc(defender.name)}</b>{mark} · <i>{clock(t, tz)}</i>", "",
             " · ".join(f"{RES_ICONS[i]} {num(v)}" for i, v in enumerate(res))]
    loot = sum(v * 0.5 for v in res)
    if loot >= 1:
        lines.append(f"💰 Botín posible: {num(loot)} → {num(ships_needed_for(loot * 1.15, 25_000))} naves grandes "
                     f"o {num(ships_needed_for(loot * 1.15, 5000))} pequeñas de carga")
    if any(debris_mc):
        lines.append(f"♻️ Escombros: 🔩 {num(debris_mc[0])} · 💎 {num(debris_mc[1])}")

    def block(icon: str, label: str, need: int, items: dict[int, int]) -> None:
        if depth >= need:
            shown = {k: v for k, v in items.items() if v}
            lines.append(f"{icon} <b>{label}:</b> {units_text(shown) if shown else 'nada'}")
        else:
            lines.append(f"{icon} {label}: <i>no se vio (manda más sondas)</i>")

    lines.append("")
    block("🚀", "Flota", SPY_FLEET, target.ships)
    block("🛡", "Defensa", SPY_DEFENSE, {k: v for k, v in target.defense.items() if ELEMENTS[k].kind == DEFENSE})
    if depth >= SPY_BUILDINGS:
        lines.append("🏗 <b>Edificios:</b> " + (", ".join(f"{NAMES[k]} {v}" for k, v in sorted(target.buildings.items())
                                                        if v) or "ninguno"))
    else:
        lines.append("🏗 Edificios: <i>no se vieron</i>")
    if depth >= SPY_RESEARCH:
        lines.append("🔬 <b>Investigación:</b> " + (", ".join(f"{NAMES[k]} {v}" for k, v in
                                                            sorted(defender.research.items()) if v) or "ninguna"))
    else:
        lines.append("🔬 Investigación: <i>no se vio</i>")
    lines += ["", f"Probabilidad de que destruyeran tus sondas: {chance} %"]
    if destroyed:
        lines.append("💥 <b>Tus sondas fueron destruidas.</b>")
    return title, "\n".join(lines)[:MAX_LEN]


def expedition(outcome: ExpeditionOutcome, fleet: Fleet) -> str:
    head = f"🌠 <b>Expedición en {fmt_target(fleet)}</b>\n"
    if outcome.kind == "lost":
        if outcome.lost_share >= 1:
            return head + "La flota entró en un agujero negro. <b>Se perdió toda la flota.</b>"
        return head + f"Piratas atacaron la flota. Se perdió el {round(outcome.lost_share * 100)} % de las naves."
    if outcome.kind == "resources":
        return head + "Encontraste un campo de asteroides: " + " · ".join(
            f"{RES_ICONS[i]} {num(v)}" for i, v in enumerate(outcome.found) if v) + " (lo que quepa en la bodega)."
    if outcome.kind == "ships":
        return head + "Encontraste naves abandonadas que se unen a tu flota: " + units_text(outcome.ships_found) + "."
    return head + "La expedición no encontró nada."
