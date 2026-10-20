"""Talking to the game bot from your own Telegram account (Telethon): send a key of the keyboard, tap a button,
and wait for what the bot answers."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Protocol

from .config import FORBIDDEN
from .screen import Screen
from .text import norm

log = logging.getLogger(__name__)


class NotAllowed(Exception):
    """The pilot tried to tap something it must never tap (derribar, cancelar, vacaciones…)."""


def check_allowed(label: str) -> None:
    words = f" {norm(label)} "
    for bad in FORBIDDEN:
        if f" {bad} " in words:
            raise NotAllowed(f"No toco «{label}»: es de las cosas que el piloto nunca hace.")


class GameBot(Protocol):
    keyboard: list[list[str]]  # the last reply keyboard the bot sent

    async def send(self, text: str) -> Screen: ...

    async def tap(self, screen: Screen, label: str) -> Screen: ...


def _rows(markup) -> list[list[str]]:
    return [[b.text for b in row.buttons] for row in getattr(markup, "rows", [])]


def screen_from(messages: list) -> Screen:
    """One screen from the bot's new messages (oldest first): all their text, the inline buttons of the last
    one that has them, and the reply keyboard if one came."""
    text = "\n".join(m.message or "" for m in messages if m.message)
    buttons, keyboard, msg_id = [], [], messages[-1].id if messages else 0
    for m in messages:
        kind = type(m.reply_markup).__name__
        if kind == "ReplyInlineMarkup":
            buttons, msg_id = _rows(m.reply_markup), m.id
        elif kind == "ReplyKeyboardMarkup":
            keyboard = _rows(m.reply_markup)
    return Screen(text, buttons, keyboard, msg_id)


class TelegramGame:
    """The real thing: a logged-in Telethon client talking to @Xnova_Elite_bot."""

    def __init__(self, client, bot: str, pause: float = 2.5, wait: float = 15):
        self.client = client
        self.bot_name = bot
        self.pause = pause
        self.wait = wait
        self.keyboard: list[list[str]] = []
        self._entity = None
        self._last_id = 0
        self._last_action = 0.0

    async def start(self) -> None:
        self._entity = await self.client.get_entity(self.bot_name)
        recent = await self.client.get_messages(self._entity, limit=30)
        self._last_id = max((m.id for m in recent), default=0)
        for m in recent:  # newest first: the most recent reply keyboard is the one on screen
            if type(m.reply_markup).__name__ == "ReplyKeyboardMarkup":
                self.keyboard = _rows(m.reply_markup)
                break

    async def _breathe(self) -> None:
        """At least `pause` seconds between actions: the bot (and Telegram) must not be flooded."""
        left = self._last_action + self.pause - time.monotonic()
        if left > 0:
            await asyncio.sleep(left)
        self._last_action = time.monotonic()

    async def send(self, text: str) -> Screen:
        check_allowed(text)
        await self._breathe()
        sent = await self._flood_safe(self.client.send_message, self._entity, text)
        self._last_id = max(self._last_id, sent.id)
        return await self._answer(edited=None)

    async def tap(self, screen: Screen, label: str) -> Screen:
        check_allowed(label)
        await self._breathe()
        msg = await self.client.get_messages(self._entity, ids=screen.msg_id)
        if msg is None:
            raise RuntimeError("Ese mensaje del bot ya no existe.")
        before = (msg.edit_date, msg.message)
        answer = await self._flood_safe(msg.click, text=label)
        alert = getattr(answer, "message", None) or ""
        result = await self._answer(edited=(msg.id, before), quiet_ok=bool(alert))
        result.alert = alert
        if not result.text and not result.buttons:  # only a popup: the message stayed as it was
            result.text, result.buttons, result.msg_id = screen.text, screen.buttons, screen.msg_id
        return result

    async def _answer(self, edited: tuple | None, quiet_ok: bool = False) -> Screen:
        """Wait for new messages from the bot, or for the tapped message to change."""
        start = time.monotonic()
        deadline = start + self.wait
        while time.monotonic() < deadline:
            await asyncio.sleep(0.8)
            new = [m for m in await self.client.get_messages(self._entity, limit=6)
                   if m.id > self._last_id and not m.out]
            if new:
                await asyncio.sleep(0.8)  # the bot may answer with more than one message
                new = [m for m in await self.client.get_messages(self._entity, limit=10)
                       if m.id > self._last_id and not m.out]
                new.sort(key=lambda m: m.id)
                self._last_id = new[-1].id
                screen = screen_from(new)
                if screen.keyboard:
                    self.keyboard = screen.keyboard
                return screen
            if edited is not None:
                msg = await self.client.get_messages(self._entity, ids=edited[0])
                if msg is not None and (msg.edit_date, msg.message) != edited[1]:
                    return screen_from([msg])
                if quiet_ok and time.monotonic() - start > 3:  # only a popup came, and nothing else did
                    return Screen("")
        if edited is not None:
            return Screen("")
        raise TimeoutError("El bot no contestó a tiempo.")

    async def _flood_safe(self, fn, *args, **kwargs):
        from telethon.errors import FloodWaitError

        try:
            return await fn(*args, **kwargs)
        except FloodWaitError as e:  # Telegram asks to slow down: wait what it says, once
            log.warning("Telegram pide esperar %s s", e.seconds)
            await asyncio.sleep(e.seconds + 1)
            return await fn(*args, **kwargs)
