"""Text helpers: compare button labels without emoji or accents, and read numbers as the game writes them."""

from __future__ import annotations

import re
import unicodedata


def fold(s: str) -> str:
    """Lowercase and without accents, keeping everything else: 'Energía: -12' -> 'energia: -12'."""
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def norm(s: str) -> str:
    """Only letters, digits and single spaces: '🏗️ Edificios (3)' -> 'edificios 3'."""
    return " ".join("".join(c if c.isalnum() else " " for c in fold(s)).split())


_NUMBER = re.compile(r"-?\d[\d.,]*(?:\s*[km](?![a-z]))?", re.IGNORECASE)


def number(s: str) -> int | None:
    """'1.234.567' -> 1234567, '12,5k' -> 12500, '3M' -> 3000000, '-20' -> -20. None if there is no number."""
    m = _NUMBER.search(s)
    if not m:
        return None
    raw = m.group(0).replace(" ", "").lower()
    factor = 1
    if raw[-1] in "km":
        factor = 1000 if raw[-1] == "k" else 1_000_000
        raw = raw[:-1].replace(",", ".")
        if raw.count(".") > 1:  # '1.234k' is not a thing; keep the digits
            raw = raw.replace(".", "")
        return round(float(raw) * factor)
    return int(raw.replace(".", "").replace(",", ""))
