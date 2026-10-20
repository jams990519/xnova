"""Reading the game's screens: resources, levels, whether something is already being built, and what a tap did.

The game's exact wording is not known yet, so everything here is lenient and the words come from the settings
(`[lectura]` in piloto.toml). `python -m piloto explorar` saves real screens to tune them.
"""

from __future__ import annotations

import re

from .text import fold, norm, number

_NUM = r"(-?\d[\d.,]*(?:\s*[km](?![a-z]))?)"


def resources(text: str, aliases: dict[str, list[str]]) -> dict[str, int]:
    """{'metal': 5000, 'cristal': 3000, 'deuterio': 1000, 'energia': -12} from lines like 'Metal: 5.000'.

    The number has to come right after the word (spaces, ':' or an emoji in between), so 'Mina de metal (5)'
    is not read as 5 of metal.
    """
    found: dict[str, int] = {}
    low = fold(text)
    for key, words in aliases.items():
        for word in words:
            m = re.search(re.escape(fold(word)) + r"[^\w\n(\[]{0,4}?" + _NUM, low)
            if m:
                found[key] = number(m.group(1))
                break
    return found


_LEVEL = (
    re.compile(r"\b(?:nivel|niv|nv|lvl|lv)\.?\s*:?\s*(\d+)"),  # 'Nivel 5', 'Nv. 5'
    re.compile(r"^[^\w]{0,4}(\d+)\b(?![.,]\d)"),  # right after the name: 'Mina de metal 5', '… (5)', '… · 5'
    re.compile(r"[(\[]\s*(\d+)\s*[)\]]"),  # '(5)' or '[5]' further on
)


def level_in(line: str, name: str) -> int | None:
    """The level written next to `name` in this line ('Mina de metal (5)', 'Mina de metal · Nv 5'), or None."""
    low = fold(line)
    n = norm(name)
    if f" {n} " not in f" {norm(line)} ":
        return None
    # look only after the name, so '3 Mina de metal' style counters are not taken as the level
    words = n.split()
    m = re.search(r"[^\w]*".join(re.escape(w) for w in words), low)
    tail = low[m.end():] if m else low
    for pattern in _LEVEL:
        found = pattern.search(tail)
        if found:
            return int(found.group(1))
    return 0  # the name is there with no level: not built yet


def levels(lines: list[str], names: list[str]) -> dict[str, int]:
    """For each name, its level in the first line that mentions it. Names that never appear are left out
    (probably not unlocked yet)."""
    result: dict[str, int] = {}
    for name in names:
        for line in lines:
            lvl = level_in(line, name)
            if lvl is not None:
                result[name] = lvl
                break
    return result


def screen_lines(text: str, labels: list[str]) -> list[str]:
    """Button labels first (they usually carry the level), then the lines of the text."""
    return [*labels, *text.splitlines()]


def contains_any(text: str, words: list[str]) -> bool:
    low = f" {norm(text)} "
    return any(f" {norm(w)} " in low or (len(norm(w)) > 5 and norm(w) in low) for w in words if norm(w))


def outcome(text: str, ok_words: list[str], fail_words: list[str], blocked_words: list[str]) -> str:
    """What a tap did: 'bloqueado' (the game will not allow it today), 'falta' (not enough resources, ships or
    room), 'ok', or '?' when the answer says nothing known."""
    if contains_any(text, blocked_words):
        return "bloqueado"
    if contains_any(text, fail_words):
        return "falta"
    if contains_any(text, ok_words):
        return "ok"
    return "?"


_SLOTS = re.compile(r"(\d+)\s*/\s*(\d+)")


def fleet_slots(text: str, words: list[str]) -> tuple[int, int] | None:
    """(in use, maximum) from a line like 'Flotas en vuelo: 2/4', looking only at lines with one of `words`."""
    for line in text.splitlines():
        if contains_any(line, words):
            m = _SLOTS.search(line)
            if m:
                return int(m.group(1)), int(m.group(2))
    return None
