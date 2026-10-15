"""UNO deck: draw pile and discard pile.

Python lists are allowed here: the circular doubly linked list is reserved
for the players.
"""

from __future__ import annotations

import random

from models.card import ACTIONS, COLORS, NUMBERS, WILDS, Card


def build_standard_deck() -> list[Card]:
    """Return the 108 cards of a standard UNO deck (unshuffled)."""
    cards: list[Card] = []
    for color in COLORS:
        cards.append(Card(color, "0"))
        for value in NUMBERS[1:] + ACTIONS:
            cards.append(Card(color, value))
            cards.append(Card(color, value))
    for value in WILDS:
        cards.extend(Card(None, value) for _ in range(4))
    return cards


class Deck:
    """Draw pile plus discard pile, with automatic reshuffle.

    Attributes:
        draw_pile: Face-down cards; the top is the end of the list.
        discard_pile: Played cards; the top is the end of the list.
    """

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng or random.Random()
        self.draw_pile: list[Card] = build_standard_deck()
        self.discard_pile: list[Card] = []
        self.rng.shuffle(self.draw_pile)

    @property
    def top(self) -> Card | None:
        """Card on top of the discard pile."""
        return self.discard_pile[-1] if self.discard_pile else None

    def discard(self, card: Card) -> None:
        """Place ``card`` on top of the discard pile."""
        self.discard_pile.append(card)

    def draw(self) -> Card | None:
        """Take one card; reshuffles the discard pile if needed.

        Returns:
            The drawn card, or None when every card is in someone's hand.
        """
        if not self.draw_pile:
            self._recycle_discards()
        return self.draw_pile.pop() if self.draw_pile else None

    def put_back_bottom(self, card: Card) -> None:
        """Return ``card`` to the bottom of the draw pile."""
        self.draw_pile.insert(0, card)

    def _recycle_discards(self) -> None:
        """Shuffle every discard except the top one back into the draw pile."""
        if len(self.discard_pile) <= 1:
            return
        top = self.discard_pile.pop()
        self.draw_pile = self.discard_pile
        self.rng.shuffle(self.draw_pile)
        self.discard_pile = [top]

    def __len__(self) -> int:
        return len(self.draw_pile)
