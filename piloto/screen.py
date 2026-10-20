"""What the game bot is showing: its text, the buttons under the message and the keyboard at the bottom."""

from __future__ import annotations

from dataclasses import dataclass, field

from .text import norm


@dataclass
class Screen:
    text: str
    buttons: list[list[str]] = field(default_factory=list)  # inline buttons of the message, by rows
    keyboard: list[list[str]] = field(default_factory=list)  # the reply keyboard this message brought, if any
    msg_id: int = 0  # the message the inline buttons belong to
    alert: str = ""  # the little popup Telegram shows after tapping an inline button

    @property
    def labels(self) -> list[str]:
        return [b for row in self.buttons for b in row]

    @property
    def everything(self) -> str:
        """Text, popup and button labels together: the game may show levels or costs on the buttons."""
        return "\n".join([self.text, self.alert, *self.labels])

    def find(self, wanted: str) -> str | None:
        """The real label of the button that matches `wanted` ignoring emoji, accents and case.

        Exact match first, then a label that starts with it, then one that has it as whole words.
        """
        return find_label(self.labels, wanted)


def find_label(labels: list[str], wanted: str) -> str | None:
    w = norm(wanted)
    if not w:
        return None
    normalized = [(label, norm(label)) for label in labels]
    # whole words only: 'si' must not match 'siguiente'
    for test in (lambda n: n == w, lambda n: n.startswith(w + " "), lambda n: f" {w} " in f" {n} "):
        for label, n in normalized:
            if test(n):
                return label
    return None
