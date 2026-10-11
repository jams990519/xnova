"""The shop: Telegram Stars only.

Telegram's rules for bot developers are explicit: "all transactions pertaining
to digital goods and services must be executed exclusively through the exchange
of Telegram Stars", and a bot caught using another payment system can be made
unreachable from the store versions of Telegram, or terminated. So the only
money that enters this game enters here, in Stars (currency tag XTR).

What a package *gives* is deliberately not decided in this file yet. The owner
is still choosing it, and a bonus bought with money is the one thing his own
research says drove players away, so it is not something to improvise. Until a
package has a price in Stars AND a list of grants, the shop shows it as closed.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Package:
    key: str                      # travels in the invoice payload, keep it short and stable
    title: str
    description: str
    stars: int = 0                # 0 means "not for sale yet"
    resources: tuple[int, int, int] = (0, 0, 0)
    officer_choices: int = 0      # how many officers this package lets you pick and max out
    once_per_player: bool = True

    @property
    def on_sale(self) -> bool:
        return self.stars > 0


# The three tiers the owner named. Prices and contents are still his decision:
# they stay at zero until he sets them, and the shop refuses to sell a package
# whose price is zero, so nothing can be bought by accident.
PACKAGES: dict[str, Package] = {
    "base": Package("base", "Paquete de apoyo",
                    "Solo recursos, para arrancar con impulso.",
                    once_per_player=False),
    "mando": Package("mando", "Paquete de mando",
                     "Un oficial a tu elección, al máximo.",
                     officer_choices=1),
    "flota": Package("flota", "Paquete de flota",
                     "Un oficial a tu elección, al máximo, y recursos.",
                     officer_choices=1),
}

# Hard ceiling, whatever the packages end up giving: nobody can buy their way
# past this many officers. Keeps the bought bonus small on purpose.
MAX_BOUGHT_OFFICERS = 2

# Only these can be bought, and this is the whole anti pay-to-win decision.
# The Geologist (+100% production at max) and the Admiral (+100% attack,
# shield and hull) are NOT here: buying either one doubles your game for good,
# which is exactly what the project research says drove players away. They are
# earned by playing, like the rest of Xnova's officers.
BUYABLE_OFFICERS = (611, 610, 613, 605, 606)  # Comandante, Espia, General, Constructor, Cientifico


def package(key: str) -> Package | None:
    return PACKAGES.get(key)


def on_sale() -> list[Package]:
    return [p for p in PACKAGES.values() if p.on_sale]
