"""One round of the pilot: build, research and send the saved farming fleets, as the settings say."""

from __future__ import annotations

import json
import time
from pathlib import Path

from . import parse
from . import plan as P
from .client import GameBot, NotAllowed
from .config import Settings
from .screen import Screen, find_label

TITLES = {"edificios": ("🏗️", "Construyendo", "Construir"), "investigacion": ("🔬", "Investigando", "Investigar")}


class Pilot:
    def __init__(self, game: GameBot, cfg: Settings, state_path: Path | None = None, dry_run: bool = False,
                 now=time.time):
        self.game = game
        self.cfg = cfg
        self.state_path = state_path
        self.dry_run = dry_run
        self.now = now
        saved = json.loads(state_path.read_text()) if state_path and state_path.is_file() else {}
        self.book = P.RaidBook.from_json(saved.get("ataques", {}))
        self.resources: dict[str, int] = {}  # the last ones read
        self._warned: set[str] = set()  # problems already told once

    def resources_line(self) -> str:
        icons = {"metal": "🔩", "cristal": "💎", "deuterio": "🧪", "energia": "⚡"}
        parts = [f"{icons[k]} {self.resources[k]:,}".replace(",", ".") for k in icons if k in self.resources]
        return f"📦 Recursos: {' · '.join(parts)}" if parts else ""

    def save(self) -> None:
        if self.state_path:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps({"ataques": self.book.to_json()}, indent=1))

    # --- getting around ---------------------------------------------------------------------------------

    async def open_section(self, key: str) -> Screen:
        """Open Edificios, Investigación or Flotas: with its key at the bottom or, if it is not there, from
        the Menú."""
        name = self.cfg.labels[key]
        if not self.game.keyboard:
            await self.game.send("/start")  # brings the keyboard
        keys = [k for row in self.game.keyboard for k in row]
        direct = find_label(keys, name)
        if direct:
            return await self.game.send(direct)
        menu = await self.game.send(find_label(keys, self.cfg.labels["menu"]) or self.cfg.labels["menu"])
        button = menu.find(name)
        if button:
            return await self.game.tap(menu, button)
        raise LookupError(f"No encontré «{name}» ni en los botones de abajo ni en el Menú.")

    def _first(self, screen: Screen, key: str) -> str | None:
        for wanted in self.cfg.label_list(key):
            found = screen.find(wanted)
            if found:
                return found
        return None

    def _outcome(self, screen: Screen) -> str:
        r = self.cfg.reading
        return parse.outcome(screen.everything, r["exito"], r["falta"], r["bloqueado"])

    @staticmethod
    def _said(screen: Screen) -> str:
        line = next((x.strip() for x in (screen.alert, *screen.text.splitlines()) if x and x.strip()), "")
        return line[:120]

    # --- building and research ------------------------------------------------------------------------

    async def build(self, kind: str) -> str | None:
        """kind: 'edificios' or 'investigacion'. Looks at the resources and at what is still missing, and puts
        to build the first thing of the plan that can be paid now: if the most wanted one is not affordable
        yet, the next one goes instead of waiting."""
        s = self.cfg.build if kind == "edificios" else self.cfg.research
        if not s.on or not s.plan:
            return None
        emoji, doing, verb = TITLES[kind]
        reading = self.cfg.reading
        screen = await self.open_section(kind)
        if s.max_queue <= 1 and parse.contains_any(screen.text, reading["ocupado"]):
            return None  # something is already being built: nothing to do this round
        names = [g.name for g in s.plan] + ([s.power_plant] if s.power_plant else [])
        levels = parse.levels(parse.screen_lines(screen.text, screen.labels), names)
        have = parse.resources(screen.everything, reading["recursos"])
        if have:
            self.resources = have
        pending = P.pending_goals(s.plan, levels, have.get("energia"), s.power_plant)
        problem = None
        for goal in pending[:s.look]:
            button = screen.find(goal.name)
            if button is None:
                continue
            target = levels.get(goal.name, 0) + 1
            detail = await self.game.tap(screen, button)
            before, _ = parse.split_cost(detail.text, reading["coste"])
            mine = have or parse.resources(before, reading["recursos"])  # what you have, if this screen says it
            cost = parse.costs(detail.text, reading["recursos"], reading["coste"])
            known = bool(cost) and any(k in mine for k in P.PAID_WITH)
            action = self._first(detail, "construir" if kind == "edificios" else "investigar")
            if action is None and self._outcome(detail) != "falta" and goal.name not in self._warned:
                self._warned.add(goal.name)
                problem = f"{emoji} En «{goal.name}» no vi el botón para {verb.lower()}: «{self._said(detail)}»."
            if action is None or (known and not P.affordable(cost, mine)):
                screen = await self.open_section(kind)  # not this one: back to the list for the next
                continue
            if self.dry_run:
                return f"{emoji} (ensayo) {verb}ía {goal.name} al nivel {target}{' (alcanza)' if known else ''}."
            done = await self.game.tap(detail, action)
            result = self._outcome(done)
            if result == "?":
                confirm = self._first(done, "confirmar")
                if confirm:
                    done = await self.game.tap(done, confirm)
                    result = self._outcome(done)
            if result == "ok":
                return f"{emoji} {doing} {goal.name} al nivel {target}."
            if result != "falta":
                return f"{emoji} Toqué {verb} en {goal.name}; el bot dijo: «{self._said(done)}»."
            screen = await self.open_section(kind)  # it did not reach after all: try the next one
        return problem  # nothing affordable now: next round

    # --- farming -----------------------------------------------------------------------------------------

    async def farm(self) -> list[str]:
        f = self.cfg.farm
        if not f.on or not f.targets:
            return []
        due = P.due_targets(f.targets, self.book, self.now(), f.max_per_day)
        if not due:
            return []
        screen = await self.open_section("flotas")
        slots = parse.fleet_slots(screen.text, self.cfg.reading["ranuras"])
        free = slots[1] - slots[0] - f.keep_free if slots else 1  # unknown: one fleet per round
        lines = []
        for target in due[:max(0, free)]:
            line, stop = await self._raid(target)
            lines.append(line)
            if stop:
                break
        self.save()
        return lines

    async def _raid(self, t: P.Target) -> tuple[str, bool]:
        """Send one saved fleet. Returns (what happened, whether to stop sending this round)."""
        screen = await self.open_section("flotas")
        saved = screen.find(self.cfg.labels["mis_flotas"])
        if saved:
            screen = await self.game.tap(screen, saved)
        fleet = screen.find(t.fleet)
        if fleet is None:
            return f"⚠️ No encontré la flota guardada «{t.fleet}» (Flotas → Mis flotas).", False
        detail = await self.game.tap(screen, fleet)
        send = self._first(detail, "enviar")
        if send is None:
            return f"⚠️ En «{t.fleet}» no vi cómo enviarla: «{self._said(detail)}».", False
        if self.dry_run:
            return f"🚀 (ensayo) Mandaría «{t.fleet}» a {t.coords}.", False
        done = await self.game.tap(detail, send)
        result = self._outcome(done)
        if result == "?":
            confirm = self._first(done, "confirmar")
            if confirm:
                done = await self.game.tap(done, confirm)
                result = self._outcome(done)
        now = self.now()
        if result == "bloqueado":
            self.book.block(t.coords, now, self._said(done))
            return f"🛡️ {t.coords}: el juego no deja atacarlo ahora («{self._said(done)}»). Lo salto 24 h.", False
        if result == "falta":
            return f"⏳ «{t.fleet}»: no hay naves o ranuras libres ahora.", True
        self.book.record(t.coords, now)  # if unsure, it counts: never over the 6 a day
        hoy = len(self.book.last_day(t.coords, now))
        if result == "ok":
            return f"🚀 «{t.fleet}» va a {t.coords} ({hoy}/{self.cfg.farm.max_per_day} hoy).", False
        return f"❔ Mandé «{t.fleet}» a {t.coords}; el bot dijo: «{self._said(done)}».", False

    # --- the round -----------------------------------------------------------------------------------------

    async def round(self) -> list[str]:
        lines: list[str] = []
        for name, part in (("Edificios", lambda: self.build("edificios")),
                           ("Investigación", lambda: self.build("investigacion")),
                           ("Flotas", self.farm)):
            try:
                out = await part()
            except NotAllowed as e:
                out = f"⚠️ {e}"
            except (LookupError, TimeoutError, RuntimeError) as e:
                out = f"⚠️ {name}: {e}"
            if isinstance(out, list):
                lines += out
            elif out:
                lines.append(out)
        return lines
