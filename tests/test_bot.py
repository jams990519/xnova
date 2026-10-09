"""End-to-end test of the Telegram bot against a fake Telegram API.

Every update goes through the real handlers. Each message the bot sends is
checked: valid Telegram HTML, at most 4096 characters, and callback data of
at most 64 bytes.
"""
import json
import random
from html.parser import HTMLParser

import pytest
from telegram import Update
from telegram.request import BaseRequest

from conftest import give, research
from xnova_bot.bot.handlers import build_application
from xnova_bot.db import Database
from xnova_bot.game import Game

ALLOWED_TAGS = {"b", "i", "u", "s", "code", "pre", "a"}


class TelegramHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        assert tag in ALLOWED_TAGS, f"tag not allowed by Telegram: <{tag}>"
        self.stack.append(tag)

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag, f"unbalanced </{tag}>"
        self.stack.pop()


def check_message(params: dict) -> None:
    text = params.get("text", "")
    assert len(text) <= 4096, f"message too long ({len(text)})"
    if params.get("parse_mode") == "HTML":
        parser = TelegramHTML()
        parser.feed(text)
        parser.close()
        assert not parser.stack, f"unclosed tags {parser.stack}"
    markup = params.get("reply_markup")
    if markup:
        markup = json.loads(markup) if isinstance(markup, str) else markup
        for row in markup.get("inline_keyboard", []):
            for button in row:
                assert len(button["callback_data"].encode()) <= 64, button


class FakeTelegram(BaseRequest):
    def __init__(self):
        self.calls = []
        self.message_id = 100

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    async def do_request(self, url, method, request_data=None, read_timeout=None, write_timeout=None,
                         connect_timeout=None, pool_timeout=None):
        endpoint = url.rsplit("/", 1)[-1]
        params = request_data.parameters if request_data else {}
        self.calls.append((endpoint, params))
        if endpoint in ("sendMessage", "editMessageText"):
            check_message(params)
            self.message_id += 1
            result = {"message_id": self.message_id, "date": 0,
                      "chat": {"id": int(params.get("chat_id", 1)), "type": "private"}, "text": params.get("text", "")}
        elif endpoint == "getMe":
            result = {"id": 999, "is_bot": True, "first_name": "Xnova", "username": "xnova_test_bot",
                      "can_join_groups": False, "can_read_all_group_messages": False,
                      "supports_inline_queries": False}
        else:
            result = True
        return 200, json.dumps({"ok": True, "result": result}).encode()

    def texts(self, chat_id=None):
        return [p.get("text", "") for e, p in self.calls if e in ("sendMessage", "editMessageText")
                and (chat_id is None or int(p.get("chat_id", 0)) == chat_id)]

    def answers(self):
        return [p.get("text") for e, p in self.calls if e == "answerCallbackQuery"]

    def clear(self):
        self.calls.clear()


class Driver:
    def __init__(self, app, fake):
        self.app, self.fake = app, fake
        self.update_id = 0

    def _user(self, uid):
        return {"id": uid, "is_bot": False, "first_name": f"U{uid}"}

    async def text(self, uid, text):
        self.update_id += 1
        message = {"message_id": self.update_id, "date": 0, "chat": {"id": uid, "type": "private"},
                   "from": self._user(uid), "text": text}
        if text.startswith("/"):
            message["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
        await self.app.process_update(Update.de_json({"update_id": self.update_id, "message": message},
                                                     self.app.bot))

    async def press(self, uid, data):
        self.update_id += 1
        payload = {"update_id": self.update_id, "callback_query": {
            "id": str(self.update_id), "from": self._user(uid), "chat_instance": "x", "data": data,
            "message": {"message_id": 1, "date": 0, "chat": {"id": uid, "type": "private"},
                        "from": {"id": 999, "is_bot": True, "first_name": "Xnova"}, "text": "menu"}}}
        await self.app.process_update(Update.de_json(payload, self.app.bot))


@pytest.fixture
async def bot(clock, settings):
    db = Database(":memory:")
    game = Game(db, settings, clock=clock, rng=random.Random(7))
    fake = FakeTelegram()
    app = build_application("123:TEST", game, request=fake)
    await app.initialize()
    yield Driver(app, fake), game
    await app.shutdown()


async def test_full_game_through_telegram(bot, clock):
    drv, game = bot
    fake = drv.fake
    # Registration
    await drv.text(1, "/start")
    assert "comandante" in fake.texts(1)[-1]
    await drv.text(1, "Ana")
    assert game.player(1) is not None
    assert any("Mina de metal" in t for t in fake.texts(1))
    # Every menu renders
    for route in ("ov", "bld", "res", "shp", "def", "flt", "gal", "rep", "rank", "ally", "off", "set", "help",
                  "prod"):
        await drv.press(1, f"m:{route}")
    for label in ("🪐 Planeta", "🏗 Edificios", "🌌 Galaxia", "🏆 Ranking", "⚙️ Ajustes"):
        await drv.text(1, label)
    for command in ("/planeta", "/flota", "/ayuda", "/galaxia"):
        await drv.text(1, command)
    # Build a mine
    await drv.press(1, "b:1")
    assert any(a and "Construyendo" in a for a in fake.answers())
    clock.advance(3600)
    game.tick()
    # Second player and a fight
    await drv.text(2, "/start")
    await drv.text(2, "Beto")
    a = game.db.planets_of(1)[0]
    b = game.db.planets_of(2)[0]
    research(game, 1, t115=6, t106=2, t108=5, t31=0)
    give(game, a.id, 50_000, 50_000, 50_000, buildings={21: 4, 14: 2}, ships={210: 5, 203: 10, 204: 20})
    give(game, b.id, 80_000, 40_000, 10_000)
    fake.clear()
    await drv.press(1, f"ga:{b.galaxy}:{b.system}:{b.position}")
    assert "Beto" in fake.texts(1)[-1]
    await drv.press(1, f"spy:{b.galaxy}:{b.system}:{b.position}:1:1")
    clock.advance(600)
    await drv.press(1, "m:rep")  # any update delivers pending notices
    assert any("Espionaje" in t for t in fake.texts(1))
    assert any("espió" in t for t in fake.texts(2))
    report = game.db.reports_of(1)[0]
    await drv.press(1, f"rp:{report['id']}")
    await drv.press(1, f"qr:{report['id']}")
    assert any(a and "Saqueo" in a for a in fake.answers())
    assert any("Ataque en camino" in t for t in fake.texts(2))
    clock.advance(3 * 3600)
    for notice_text in [n.text for n in game.tick()]:
        pass
    await drv.press(2, "m:ov")
    assert game.db.reports_of(2)  # defender got the battle report
    # Fleet flow with buttons and typed answers: transport to Beto
    fake.clear()
    await drv.press(1, "f:new")
    await drv.press(1, "f:s:203")
    await drv.press(1, "f:a:203:2")
    await drv.press(1, "f:next")
    await drv.text(1, f"{b.galaxy}:{b.system}:{b.position}")
    await drv.press(1, "f:mi:3")
    await drv.press(1, "f:sp:50")
    await drv.text(1, "1000 500 0")
    assert "Confirmar envío" in fake.texts(1)[-1]
    await drv.press(1, "f:go")
    assert any(a and "Flota enviada" in a for a in fake.answers())
    fleets = game.db.fleets_of(1)
    assert any(f.mission == 3 and f.metal == 1000 for f in fleets)
    await drv.press(1, f"fr:{fleets[-1].id}")
    # Shipyard order with typed amount
    await drv.press(1, "u:204")
    await drv.press(1, "ui:204")
    await drv.text(1, "3")
    assert game.db.get_planet(a.id).shipyard
    # Alliance
    await drv.press(1, "al:create")
    await drv.text(1, "NOVA Imperio Nova")
    code = game.db.alliance_by_tag("NOVA")["invite_code"]
    await drv.press(2, "al:join")
    await drv.text(2, code)
    assert game.player(2).alliance_id == game.player(1).alliance_id
    await drv.press(2, "al:msg")
    await drv.text(2, "hola equipo <b>")
    assert any("hola equipo &lt;b&gt;" in t for t in fake.texts(1))
    # Private message and settings
    await drv.press(2, "msg:1")
    await drv.text(2, "¿tregua?")
    assert any("¿tregua?" in t for t in fake.texts(1))
    await drv.press(1, "s:ntf")
    await drv.press(1, "s:ren")
    await drv.text(1, "Nueva Tierra")
    assert game.db.get_planet(a.id).name == "Nueva Tierra"
    # Galaxy navigation and coordinates typed directly
    await drv.press(1, "g:1:2")
    await drv.text(1, "1:1:5")
    # Errors become alerts, not crashes
    await drv.press(1, "b:43")
    assert fake.calls[-1][0] == "answerCallbackQuery"
    # Groups are refused
    await drv.app.process_update(Update.de_json({"update_id": 9999, "message": {
        "message_id": 1, "date": 0, "chat": {"id": -5, "type": "group"},
        "from": {"id": 1, "is_bot": False, "first_name": "Ana"}, "text": "hola"}}, drv.app.bot))
    assert "privado" in fake.texts(-5)[-1]


async def test_ranking_and_officers_screens(bot, clock):
    drv, game = bot
    await drv.text(1, "/start")
    await drv.text(1, "Ana")
    with game.db.conn:
        p = game.player(1)
        p.officer_points = 2
        game.db.save_player(p)
    await drv.press(1, "m:off")
    await drv.press(1, "o:601")
    assert game.player(1).officer(601) == 1
    await drv.press(1, "rk:0")
    await drv.press(1, "rk:a")
