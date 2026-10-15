"""Player node of the circular doubly linked list."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.card import Card


class Player:
    """A node of the UNO table (circular doubly linked list).

    Equivalent to the ``Node`` class from the lecture: ``data`` is split into
    domain fields (``name``, ``hand``, ``is_human``) and the two pointers
    ``prev`` and ``next`` link it to its neighbours at the table.

    Attributes:
        name: Unique player name (acts as the node key).
        hand: Cards held by the player. A Python list is allowed here; only
            the players themselves must live in the circular list.
        is_human: True for the person using the interface, False for a CPU.
        prev: Player sitting to the left (counter-clockwise neighbour).
        next: Player sitting to the right (clockwise neighbour).
    """

    def __init__(self, name: str, is_human: bool = False) -> None:
        self.name: str = name
        self.hand: list[Card] = []
        self.is_human: bool = is_human
        self.prev: Player | None = None
        self.next: Player | None = None

    @property
    def card_count(self) -> int:
        """Number of cards in the player's hand."""
        return len(self.hand)

    def __repr__(self) -> str:
        kind = "human" if self.is_human else "cpu"
        prev_name = self.prev.name if self.prev else None
        next_name = self.next.name if self.next else None
        return f"Player({self.name!r}, {kind}, prev={prev_name!r}, next={next_name!r})"
