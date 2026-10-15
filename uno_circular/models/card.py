"""UNO card model."""

from __future__ import annotations

from dataclasses import dataclass

# Card colors (internal identifiers). Wild cards have color None.
RED = "red"
YELLOW = "yellow"
GREEN = "green"
BLUE = "blue"
COLORS: tuple[str, ...] = (RED, YELLOW, GREEN, BLUE)

# Action values.
SKIP = "skip"
REVERSE = "reverse"
DRAW_TWO = "draw2"
WILD = "wild"
WILD_DRAW_FOUR = "wild4"
NUMBERS: tuple[str, ...] = tuple(str(n) for n in range(10))
ACTIONS: tuple[str, ...] = (SKIP, REVERSE, DRAW_TWO)
WILDS: tuple[str, ...] = (WILD, WILD_DRAW_FOUR)

# Spanish names shown in the interface.
COLOR_NAMES_ES: dict[str, str] = {
    RED: "Rojo",
    YELLOW: "Amarillo",
    GREEN: "Verde",
    BLUE: "Azul",
}
VALUE_NAMES_ES: dict[str, str] = {
    SKIP: "Salta",
    REVERSE: "Reversa",
    DRAW_TWO: "+2",
    WILD: "Comodín",
    WILD_DRAW_FOUR: "Comodín +4",
}
# Short symbols used on the card buttons.
VALUE_SYMBOLS: dict[str, str] = {
    SKIP: "⊘",
    REVERSE: "⇄",
    DRAW_TWO: "+2",
    WILD: "★",
    WILD_DRAW_FOUR: "+4",
}


@dataclass(frozen=True)
class Card:
    """A single UNO card.

    Attributes:
        color: One of COLORS, or None for wild cards.
        value: "0".."9", or one of the action / wild identifiers.
    """

    color: str | None
    value: str

    @property
    def is_wild(self) -> bool:
        """Return True for Comodín and Comodín +4."""
        return self.value in WILDS

    @property
    def is_number(self) -> bool:
        """Return True for number cards 0-9."""
        return self.value in NUMBERS

    def can_be_played_on(self, top: Card, active_color: str) -> bool:
        """Return True if this card may be played over ``top``.

        Args:
            top: Card currently on top of the discard pile.
            active_color: Color in force (differs from ``top.color`` after a wild).
        """
        if self.is_wild:
            return True
        return self.color == active_color or self.value == top.value

    @property
    def symbol(self) -> str:
        """Short text drawn on the card button."""
        return VALUE_SYMBOLS.get(self.value, self.value)

    def label_es(self) -> str:
        """Human readable Spanish label, e.g. 'Rojo 7' or 'Comodín +4'."""
        value = VALUE_NAMES_ES.get(self.value, self.value)
        if self.color is None:
            return value
        return f"{COLOR_NAMES_ES[self.color]} {value}"

    def __str__(self) -> str:
        return self.label_es()
