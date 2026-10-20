"""The pilot for @Xnova_Elite_bot, against a small fake of the game (no Telegram, no network)."""

import asyncio
import tomllib
from pathlib import Path

import pytest

from piloto import parse
from piloto import plan as P
from piloto.client import NotAllowed, check_allowed, screen_from
from piloto.config import DEFAULT_READING, from_dict
from piloto.explore import explore, safe
from piloto.pilot import Pilot
from piloto.screen import Screen
from piloto.text import norm, number

EXAMPLE = Path(__file__).resolve().parents[1] / "piloto" / "piloto.example.toml"


class FakeXnova:
    """A tiny stand-in for the game bot: a keyboard, screens with buttons, and what each tap does."""

    def __init__(self):
        self.keyboard = [["🏠 Menú", "🏗️ Edificios", "🚀 Flotas"], ["🔬 Investigación", "🌌 Galaxia", "👤 Mi cuenta"]]
        self.levels = {"Planta solar": 0, "Mina de metal": 0, "Mina de cristal": 0, "Sintetizador de deuterio": 0}
        self.research = {"Tecnología de energía": 0, "Motor de combustión": 0}
        self.energy = 0
        self.res = {"metal": 5000, "cristal": 3000, "deuterio": 1000}
        self.costs = {"Planta solar": {"metal": 75, "cristal": 30}, "Mina de metal": {"metal": 60, "cristal": 15},
                      "Mina de cristal": {"metal": 48, "cristal": 24},
                      "Sintetizador de deuterio": {"metal": 225, "cristal": 75},
                      "Tecnología de energía": {"cristal": 800, "deuterio": 400},
                      "Motor de combustión": {"metal": 400, "deuterio": 600}}
        self.cost_words = True  # False: the cost only with emoji, so the pilot cannot read it
        self.busy = False
        self.afford = True
        self.in_flight, self.max_fleets = 0, 2
        self.saved = {"Granja 1": "1:45:8", "Granja 2": "1:46:4"}
        self.shielded: set[str] = set()
        self.raids: list[str] = []
        self.sent: list[str] = []
        self.taps: list[str] = []
        self._kinds: dict[int, tuple] = {}
        self._id = 100

    def _screen(self, kind: tuple, text: str, buttons: list[list[str]], keyboard=None) -> Screen:
        self._id += 1
        self._kinds[self._id] = kind
        return Screen(text, buttons, keyboard or [], self._id)

    def buildings(self) -> Screen:
        r = self.res
        text = (f"🏗️ Edificios — Planeta Nova [1:20:5]\n🔩 Metal: {r['metal']} · 💎 Cristal: {r['cristal']} · "
                f"🧪 Deuterio: {r['deuterio']} · ⚡ Energía: {self.energy}")
        if self.busy:
            text += "\n🔨 En construcción: termina a las 12:30"
        icons = {"Mina de metal": "⛏️", "Mina de cristal": "💎", "Sintetizador de deuterio": "🧪", "Planta solar": "☀️"}
        rows = [[f"{icons[n]} {n} ({lv})"] for n, lv in self.levels.items()] + [["📋 Cola de construcción"]]
        return self._screen(("edificios",), text, rows)

    def labs(self) -> Screen:
        rows = [[f"🔬 {n} ({lv})"] for n, lv in self.research.items()]
        return self._screen(("investigacion",), "🔬 Investigación — Laboratorio de Investigación (2)", rows)

    def fleets(self) -> Screen:
        return self._screen(("flotas",), f"🚀 Flotas en vuelo: {self.in_flight}/{self.max_fleets}",
                            [["📂 Mis flotas", "➕ Crear una flota"], ["🔁 Repetir"]])

    async def send(self, text: str) -> Screen:
        check_allowed(text)
        self.sent.append(text)
        n = norm(text)
        if n == "start":
            return self._screen(("inicio",), "👋 Bienvenido a X.N.O.V.A", [], self.keyboard)
        if n == "menu":
            return self._screen(("menu",), "🏠 Menú", [["🏗️ Edificios", "🔬 Investigación"], ["🚀 Flotas", "🏆 Ranking"]])
        if n == "edificios":
            return self.buildings()
        if n == "investigacion":
            return self.labs()
        if n == "flotas":
            return self.fleets()
        return self._screen(("otro",), f"Pantalla {text}", [["📊 Estadísticas"], ["💣 Derribar algo"]])

    async def tap(self, screen: Screen, label: str) -> Screen:
        check_allowed(label)
        assert label in screen.labels, f"{label!r} no está en la pantalla"
        self.taps.append(label)
        kind = self._kinds[screen.msg_id]
        name = label.split(" ", 1)[1].rsplit(" (", 1)[0]
        if kind[0] == "menu":
            return await self.send(name)
        if kind[0] in ("edificios", "investigacion"):
            if "Cola" in label:
                return self._screen(("cola",), "📋 Cola vacía", [])
            lv = (self.levels if kind[0] == "edificios" else self.research)[name]
            verb = "🔨 Construir" if kind[0] == "edificios" else "🔬 Investigar"
            icons = {"metal": "🔩", "cristal": "💎", "deuterio": "🧪"}
            cost = " · ".join(f"{k.capitalize() if self.cost_words else icons[k]} {v}" for k, v in self.costs[name].items())
            return self._screen(("detalle", kind[0], name), f"{name} — nivel {lv}\nCoste: {cost}\nTiempo: 2 min",
                                [[f"{verb} nivel {lv + 1}"], ["💣 Derribar"]])
        if kind[0] == "detalle":
            cost = self.costs[kind[2]]
            if not self.afford or any(self.res[k] < v for k, v in cost.items()):
                return Screen(screen.text, screen.buttons, [], screen.msg_id, alert="❌ No tienes suficientes recursos.")
            for k, v in cost.items():
                self.res[k] -= v
            (self.levels if kind[1] == "edificios" else self.research)[kind[2]] += 1
            self.busy = kind[1] == "edificios"
            return self._screen(("hecho",), f"✅ {kind[2]} añadido a la cola.", [])
        if kind[0] == "flotas" and "Mis flotas" in label:
            return self._screen(("mis",), "📂 Tus flotas guardadas", [[f"⭐ {n} → {c}"] for n, c in self.saved.items()])
        if kind[0] == "mis":
            fleet = label[2:].split(" → ")[0]
            return self._screen(("flota", fleet), f"⭐ {fleet}\n10 Carguero", [["🚀 Enviar"], ["🗑️ Borrar"]])
        if kind[0] == "flota":
            coords = self.saved[kind[1]]
            if coords in self.shielded:
                return self._screen(("x",), "🛡️ Ese planeta tiene escudo por inactividad: no se puede atacar.", [])
            if self.in_flight >= self.max_fleets:
                return self._screen(("x",), "❌ No hay ranuras de flota libres.", [])
            self.in_flight += 1
            self.raids.append(coords)
            return self._screen(("x",), "✅ Flota enviada. Llega en 12 min.", [])
        return self._screen(("otro",), f"Dentro de {label}", [])


class Clock:
    def __init__(self):
        self.t = 1_800_000_000.0

    def __call__(self):
        return self.t


def settings(**over):
    raw = tomllib.loads(EXAMPLE.read_text(encoding="utf-8"))
    raw["telegram"].update(api_id=1, api_hash="x")
    for section, values in over.items():
        raw.setdefault(section, {}).update(values)
    return from_dict(raw)


def run(coro):
    return asyncio.run(coro)


# --- reading ---------------------------------------------------------------------------------------------

def test_numbers_and_labels():
    assert norm("🏗️ Edificios (3)") == "edificios 3" and norm("Investigación") == "investigacion"
    assert [number(x) for x in ("1.234.567", "12,5k", "3M", "-20", "Energía: -12")] == [1234567, 12500, 3000000, -20, -12]
    assert number("sin números") is None
    s = Screen("", [["🔁 Repetir", "🚀 Siguiente"], ["Sí"]])
    assert s.find("repetir") == "🔁 Repetir" and s.find("si") == "Sí" and s.find("guardar") is None


def test_reading_resources_and_levels():
    text = "🔩 Metal: 5.000 · 💎 Cristal: 3.000 · 🧪 Deuterio: 1,2k · ⚡ Energía: -12\n⛏️ Mina de metal (5)"
    assert parse.resources(text, DEFAULT_READING["recursos"]) == {
        "metal": 5000, "cristal": 3000, "deuterio": 1200, "energia": -12}
    assert parse.resources("⛏️ Mina de metal (5)", DEFAULT_READING["recursos"]) == {}  # not 5 of metal
    lines = ["Mina de metal · Nv 5", "Planta solar: nivel 4", "Mina de cristal 7 — 🔩 1.234 💎 567",
             "Sintetizador de deuterio", "Almacén de metal (3)", "Laboratorio de Investigación (2)"]
    assert parse.levels(lines, ["Mina de metal", "Planta solar", "Mina de cristal", "Sintetizador de deuterio",
                                "Laboratorio", "Hangar"]) == {
        "Mina de metal": 5, "Planta solar": 4, "Mina de cristal": 7, "Sintetizador de deuterio": 0, "Laboratorio": 2}
    r = DEFAULT_READING
    assert parse.outcome("✅ Flota enviada", r["exito"], r["falta"], r["bloqueado"]) == "ok"
    assert parse.outcome("❌ No tienes suficientes recursos", r["exito"], r["falta"], r["bloqueado"]) == "falta"
    assert parse.outcome("🛡️ Tiene escudo", r["exito"], r["falta"], r["bloqueado"]) == "bloqueado"
    assert parse.outcome("Hola", r["exito"], r["falta"], r["bloqueado"]) == "?"
    assert parse.fleet_slots("Planeta Nova\n🚀 Flotas en vuelo: 2/4", r["ranuras"]) == (2, 4)


def test_plan():
    goals = P.parse_plan(["Planta solar 1", "Mina de metal 2", "Laboratorio 1"])
    assert goals[1] == P.Goal("Mina de metal", 2)
    with pytest.raises(ValueError):
        P.parse_plan(["Mina de metal"])
    assert P.next_goal(goals, {"Planta solar": 0, "Mina de metal": 0}) == P.Goal("Planta solar", 1)
    assert P.next_goal(goals, {"Planta solar": 1, "Mina de metal": 1}) == P.Goal("Mina de metal", 2)
    assert P.next_goal(goals, {"Planta solar": 1, "Mina de metal": 2}) is None  # no lab on screen yet: skipped
    assert P.next_goal(goals, {"Planta solar": 3, "Mina de metal": 0}, energy=-5, power_plant="Planta solar") == \
        P.Goal("Planta solar", 4)  # negative energy: power first


# --- building and research ---------------------------------------------------------------------------------

def test_builds_the_plan_in_order_one_at_a_time():
    game = FakeXnova()
    pilot = Pilot(game, settings(investigar={"activo": False}))
    assert run(pilot.round()) == ["🏗️ Construyendo Planta solar al nivel 1."]
    assert "🔨 Construir nivel 1" in game.taps and game.sent[0] == "🏗️ Edificios"  # with the key at the bottom
    assert run(pilot.round()) == []  # something is being built: waits
    game.busy = False
    assert run(pilot.round()) == ["🏗️ Construyendo Mina de metal al nivel 1."]
    game.busy = False
    game.afford = False
    assert run(pilot.round()) == []  # not enough resources: tries again next round, no noise
    assert not any("Derribar" in t for t in game.taps)


def test_builds_what_the_resources_allow_when_the_first_is_not_affordable():
    game = FakeXnova()
    game.res = {"metal": 100, "cristal": 100, "deuterio": 0}
    game.costs["Planta solar"] = {"metal": 500, "cristal": 200}  # first of the plan, but it does not reach
    pilot = Pilot(game, settings(investigar={"activo": False}))
    assert run(pilot.round()) == ["🏗️ Construyendo Mina de metal al nivel 1."]
    assert not any("Construir" in t for t in game.taps[:-1])  # it saw the cost: did not even try the solar plant
    assert pilot.resources_line() == "📦 Recursos: 🔩 100 · 💎 100 · 🧪 0 · ⚡ 0"
    game.busy = False
    game.res = {"metal": 10, "cristal": 10, "deuterio": 0}
    assert run(pilot.round()) == []  # nothing reaches: waits, without noise
    assert game.levels["Mina de metal"] == 1


def test_when_the_cost_cannot_be_read_it_tries_in_order():
    game = FakeXnova()
    game.cost_words = False
    game.res = {"metal": 100, "cristal": 100, "deuterio": 0}
    game.costs["Planta solar"] = {"metal": 500, "cristal": 200}
    pilot = Pilot(game, settings(investigar={"activo": False}))
    assert run(pilot.round()) == ["🏗️ Construyendo Mina de metal al nivel 1."]
    assert [t for t in game.taps if "Construir" in t] == ["🔨 Construir nivel 1", "🔨 Construir nivel 1"]
    dry = Pilot(FakeXnova(), settings(investigar={"activo": False}), dry_run=True)
    assert run(dry.round()) == ["🏗️ (ensayo) Construiría Planta solar al nivel 1 (alcanza)."]


def test_negative_energy_builds_power_first():
    game = FakeXnova()
    game.levels.update({"Planta solar": 3, "Mina de metal": 4})
    game.energy = -20
    pilot = Pilot(game, settings(investigar={"activo": False}))
    assert run(pilot.round()) == ["🏗️ Construyendo Planta solar al nivel 4."]


def test_research_and_dry_run():
    game = FakeXnova()
    pilot = Pilot(game, settings(construir={"activo": False}), dry_run=True)
    assert run(pilot.round()) == ["🔬 (ensayo) Investigaría Tecnología de energía al nivel 1."]
    assert not any("Investigar" in t for t in game.taps)  # in a dry run nothing is pressed
    pilot.dry_run = False
    assert run(pilot.round()) == ["🔬 Investigando Tecnología de energía al nivel 1."]


def test_section_from_the_menu_when_the_key_is_not_at_the_bottom():
    game = FakeXnova()
    game.keyboard = [["🏠 Menú", "🌌 Galaxia"]]
    pilot = Pilot(game, settings(investigar={"activo": False}))
    assert run(pilot.round()) == ["🏗️ Construyendo Planta solar al nivel 1."]
    assert game.sent[0] == "🏠 Menú" and game.taps[0] == "🏗️ Edificios"


def test_it_never_taps_forbidden_buttons_even_if_told_to():
    for label in ("💣 Derribar", "Cancelar", "🏖️ Modo vacaciones", "Reubicar planeta actual", "Vender"):
        with pytest.raises(NotAllowed):
            check_allowed(label)
    check_allowed("🔨 Construir nivel 2")
    game = FakeXnova()
    cfg = settings(investigar={"activo": False}, etiquetas={"construir": ["Derribar"]})
    assert run(Pilot(game, cfg).round()) == ["⚠️ No toco «💣 Derribar»: es de las cosas que el piloto nunca hace."]
    assert game.levels["Planta solar"] == 0


# --- farming -------------------------------------------------------------------------------------------------

def farm_settings(**farm):
    targets = [{"flota": "Granja 1", "coordenadas": "1:45:8"}, {"flota": "Granja 2", "coordenadas": "1:46:4"}]
    return settings(construir={"activo": False}, investigar={"activo": False},
                    farmear={"activo": True, "objetivo": targets, **farm})


def test_farming_sends_saved_fleets_and_respects_slots_and_daily_limit(tmp_path):
    game, clock = FakeXnova(), Clock()
    state = tmp_path / "estado.json"
    pilot = Pilot(game, farm_settings(max_ataques_por_dia=2), state, now=clock)
    assert run(pilot.round()) == ["🚀 «Granja 1» va a 1:45:8 (1/2 hoy).", "🚀 «Granja 2» va a 1:46:4 (1/2 hoy)."]
    assert game.raids == ["1:45:8", "1:46:4"] and "🚀 Enviar" in game.taps
    assert run(pilot.round()) == []  # both slots busy
    game.in_flight = 0
    clock.t += 3600
    run(pilot.round())
    game.in_flight = 0
    clock.t += 3600
    assert run(pilot.round()) == []  # 2 a day each: done for today
    assert game.raids.count("1:45:8") == 2
    # the count survives a restart of the pilot
    again = Pilot(game, farm_settings(max_ataques_por_dia=2), state, now=clock)
    assert run(again.round()) == []
    clock.t += 24 * 3600
    assert len(run(again.round())) == 2


def test_farming_skips_a_planet_the_game_protects():
    game, clock = FakeXnova(), Clock()
    game.shielded.add("1:45:8")
    pilot = Pilot(game, farm_settings(), now=clock)
    lines = run(pilot.round())
    assert lines[0].startswith("🛡️ 1:45:8: el juego no deja atacarlo ahora") and lines[1].startswith("🚀 «Granja 2»")
    game.in_flight = 0
    assert run(pilot.round()) == ["🚀 «Granja 2» va a 1:46:4 (2/5 hoy)."]  # the shielded one waits 24 h
    assert "1:45:8" not in game.raids


def test_farming_stops_when_there_are_no_free_slots_and_dry_run_sends_nothing():
    game = FakeXnova()
    game.max_fleets = 5
    game.in_flight = 0
    pilot = Pilot(game, farm_settings(dejar_libres=4), now=Clock())
    assert len(run(pilot.round())) == 1  # 5 slots, 4 kept free for the player
    game2 = FakeXnova()
    dry = Pilot(game2, farm_settings(), dry_run=True, now=Clock())
    assert run(dry.round())[0] == "🚀 (ensayo) Mandaría «Granja 1» a 1:45:8."
    assert game2.raids == [] and "🚀 Enviar" not in game2.taps


# --- explorer, settings and the Telegram glue -----------------------------------------------------------------

def test_explorer_only_looks(tmp_path):
    game = FakeXnova()
    count = run(explore(game, tmp_path, depth=2, limit=40, say=lambda _: None))
    assert count > 5
    actions = ("Construir", "Investigar", "Derribar", "Enviar", "Borrar", "Repetir", "Crear")
    assert not [t for t in game.taps if any(a in t for a in actions)]
    saved = (tmp_path / "pantallas.txt").read_text(encoding="utf-8")
    assert "=== 🏗️ Edificios" in saved and "[botones] ⛏️ Mina de metal (0)" in saved
    assert not safe("🔨 Construir nivel 1") and not safe("Sí, derribar Mina de metal") and safe("📂 Mis flotas")


def test_settings():
    cfg = settings()
    assert cfg.build.plan[0] == P.Goal("Planta solar", 1) and cfg.build.power_plant == "Planta solar"
    assert cfg.bot == "Xnova_Elite_bot" and not cfg.farm.on and cfg.pause >= 1
    with pytest.raises(SystemExit):
        settings(farmear={"max_ataques_por_dia": 7})  # the game allows 6
    with pytest.raises(SystemExit):
        from_dict({"telegram": {"api_id": 0}})


def test_screen_from_telethon_messages():
    class Btn:
        def __init__(self, text):
            self.text = text

    class Row:
        def __init__(self, *labels):
            self.buttons = [Btn(x) for x in labels]

    class ReplyInlineMarkup:
        def __init__(self, *rows):
            self.rows = list(rows)

    class ReplyKeyboardMarkup(ReplyInlineMarkup):
        pass

    class Msg:
        def __init__(self, id, message, reply_markup=None):
            self.id, self.message, self.reply_markup = id, message, reply_markup

    s = screen_from([Msg(5, "Hola", ReplyKeyboardMarkup(Row("🏠 Menú", "🚀 Flotas"))),
                     Msg(6, "🏗️ Edificios", ReplyInlineMarkup(Row("⛏️ Mina de metal (2)")))])
    assert s.text == "Hola\n🏗️ Edificios" and s.msg_id == 6
    assert s.keyboard == [["🏠 Menú", "🚀 Flotas"]] and s.buttons == [["⛏️ Mina de metal (2)"]]


# --- the Telethon side, against a fake Telegram client ---------------------------------------------------------

class _Btn:
    def __init__(self, text):
        self.text = text


class _Row:
    def __init__(self, labels):
        self.buttons = [_Btn(x) for x in labels]


class ReplyInlineMarkup:
    def __init__(self, rows):
        self.rows = [_Row(r) for r in rows]


class ReplyKeyboardMarkup(ReplyInlineMarkup):
    pass


class FakeTelegram:
    """Just what TelegramGame uses of a Telethon client: messages with ids, sending text and clicking buttons."""

    def __init__(self):
        self.msgs = []
        self.clicks = []
        self._id = 0
        self.add("👋 Bienvenido", ReplyKeyboardMarkup([["🏠 Menú", "🏗️ Edificios"]]))

    def add(self, text, markup=None, out=False):
        self._id += 1
        game = self

        class Msg:
            id, message, reply_markup, edit_date = self._id, text, markup, None

            async def click(self, text=None):
                game.clicks.append(text)
                if text == "🔨 Construir":  # the bot only answers with a popup
                    return type("Answer", (), {"message": "❌ No tienes suficientes recursos."})()
                self.message, self.edit_date = f"Detalle de {text}", 1
                self.reply_markup = ReplyInlineMarkup([["🔨 Construir"]])
                return None

        Msg.out = out
        m = Msg()
        self.msgs.append(m)
        return m

    async def get_entity(self, name):
        return name

    async def get_messages(self, entity, limit=None, ids=None):
        if ids is not None:
            return next((m for m in self.msgs if m.id == ids), None)
        return list(reversed(self.msgs))[:limit]

    async def send_message(self, entity, text):
        sent = self.add(text, out=True)
        if text == "🏗️ Edificios":
            self.add("🏗️ Edificios\n⚡ Energía: 10", ReplyInlineMarkup([["⛏️ Mina de metal (0)"]]))
        return sent


def test_telegram_game_sends_taps_and_reads_answers(monkeypatch):
    from piloto import client as C

    ticks = iter(range(0, 10_000))
    monkeypatch.setattr(C.time, "monotonic", lambda: next(ticks))

    async def no_wait(_):
        return None

    monkeypatch.setattr(C.asyncio, "sleep", no_wait)

    async def go():
        tg = FakeTelegram()
        game = C.TelegramGame(tg, "Xnova_Elite_bot", pause=1, wait=30)
        await game.start()
        assert game.keyboard == [["🏠 Menú", "🏗️ Edificios"]]
        screen = await game.send("🏗️ Edificios")
        assert screen.text.startswith("🏗️ Edificios") and screen.labels == ["⛏️ Mina de metal (0)"]
        detail = await game.tap(screen, "⛏️ Mina de metal (0)")  # the bot edits its message
        assert detail.text == "Detalle de ⛏️ Mina de metal (0)" and detail.labels == ["🔨 Construir"]
        popup = await game.tap(detail, "🔨 Construir")  # only a popup: the screen stays, with the alert
        assert popup.alert == "❌ No tienes suficientes recursos." and popup.labels == ["🔨 Construir"]
        with pytest.raises(NotAllowed):
            await game.tap(detail, "💣 Derribar")
        with pytest.raises(TimeoutError):
            await game.send("nadie contesta esto")
        assert tg.clicks == ["⛏️ Mina de metal (0)", "🔨 Construir"]

    asyncio.run(go())
