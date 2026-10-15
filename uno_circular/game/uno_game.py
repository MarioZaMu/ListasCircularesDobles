"""UNO game controller built on top of ``UnoTable``.

All turn handling (advance, skip, reverse, player leaving) is delegated to the
circular doubly linked list; this class only applies the card rules.
"""

from __future__ import annotations

import random
from collections import Counter
from collections.abc import Callable

from game.deck import Deck
from models.card import (COLOR_NAMES_ES, COLORS, DRAW_TWO, REVERSE, SKIP,
                         WILD_DRAW_FOUR, Card)
from models.player import Player
from models.uno_table import UnoTable

MIN_PLAYERS = 2
MAX_PLAYERS = 6
HAND_SIZE = 7


class GameError(Exception):
    """Raised when a move breaks the rules (wrong turn, unplayable card...)."""


class UnoGame:
    """Simplified but complete UNO game.

    Rules implemented:
        * play by matching color or value; wilds always playable;
        * Salta skips the next player; Reversa inverts the direction (acts as
          Salta with two players); +2 / +4 make the next player draw and lose
          the turn (no stacking);
        * if you cannot (or do not want to) play, draw one card; if it is
          playable you may play it, otherwise the turn passes;
        * a player with no cards leaves the table via ``remove_player`` and the
          game continues until only one player remains.

    Attributes:
        table: The circular doubly linked list of players.
        deck: Draw and discard piles.
        active_color: Color in force (chosen after a wild).
        rankings: Names in finishing order (1st, 2nd, ...).
        drawn_card: Card just drawn by the current player that may still be
            played this turn, or None.
    """

    def __init__(self, table: UnoTable, seed: int | None = None,
                 on_event: Callable[[str], None] | None = None) -> None:
        self.table = table
        self.rng = random.Random(seed)
        self.deck = Deck(self.rng)
        self.on_event = on_event
        self.active_color: str = COLORS[0]
        self.rankings: list[str] = []
        self.drawn_card: Card | None = None
        self.started = False

    # ---------------------------------------------------------------- helpers
    def _event(self, message: str) -> None:
        if self.on_event is not None:
            self.on_event(message)

    @property
    def current_player(self) -> Player | None:
        """Player whose turn it is (``table.current_turn``)."""
        return self.table.current_turn

    @property
    def top_card(self) -> Card | None:
        """Card on top of the discard pile."""
        return self.deck.top

    @property
    def is_over(self) -> bool:
        """True once fewer than two players remain at the table."""
        return self.started and len(self.table) < MIN_PLAYERS

    def _draw_cards(self, player: Player, amount: int) -> int:
        """Give ``amount`` cards to ``player``; return how many were drawn."""
        drawn = 0
        for _ in range(amount):
            card = self.deck.draw()
            if card is None:
                break
            player.hand.append(card)
            drawn += 1
        return drawn

    # ------------------------------------------------------------------ setup
    def start(self) -> None:
        """Deal the cards, flip the first card and give the turn to ``head``.

        Raises:
            GameError: If the number of players is outside 2..6.
        """
        if not MIN_PLAYERS <= len(self.table) <= MAX_PLAYERS:
            raise GameError(f"Se necesitan entre {MIN_PLAYERS} y {MAX_PLAYERS} jugadores.")
        for player in self.table.traverse_clockwise():
            player.hand.clear()
            self._draw_cards(player, HAND_SIZE)

        # The starting card must be a number card.
        card = self.deck.draw()
        while card is not None and not card.is_number:
            self.deck.put_back_bottom(card)
            card = self.deck.draw()
        assert card is not None and card.color is not None
        self.deck.discard(card)
        self.active_color = card.color

        self.table.direction = 1
        self.table.start_turns(self.table.head)
        self.started = True
        self._event(f"Se reparten {HAND_SIZE} cartas. Carta inicial: {card.label_es()}. "
                    f"Empieza {self.current_player.name}.")

    # ------------------------------------------------------------------ rules
    def is_playable(self, card: Card) -> bool:
        """Return True if ``card`` can be played on the current top card."""
        top = self.top_card
        return top is not None and card.can_be_played_on(top, self.active_color)

    def playable_indices(self, player: Player | None = None) -> list[int]:
        """Indices of the cards ``player`` may play right now.

        After drawing, only the drawn card may be played.
        """
        player = player or self.current_player
        if player is None or self.is_over:
            return []
        if self.drawn_card is not None and player is self.current_player:
            for index in range(len(player.hand) - 1, -1, -1):
                if player.hand[index] is self.drawn_card:
                    return [index] if self.is_playable(self.drawn_card) else []
            return []
        return [i for i, card in enumerate(player.hand) if self.is_playable(card)]

    def _require_turn(self, player: Player | None) -> Player:
        current = self.current_player
        if self.is_over or current is None:
            raise GameError("La partida ya terminó.")
        if player is not None and player is not current:
            raise GameError(f"No es el turno de {player.name}.")
        return current

    def play_card(self, index: int, chosen_color: str | None = None,
                  player: Player | None = None) -> str:
        """Current player plays ``hand[index]``.

        Args:
            index: Position of the card in the player's hand.
            chosen_color: Color for a wild card (required for wilds; a sensible
                default is picked if omitted).
            player: Optional check that it really is this player's turn.

        Returns:
            A Spanish description of the move.

        Raises:
            GameError: If it is not the player's turn or the card is not playable.
        """
        current = self._require_turn(player)
        if index not in self.playable_indices(current):
            raise GameError("Esa carta no se puede jugar ahora.")

        card = current.hand.pop(index)
        self.deck.discard(card)
        self.drawn_card = None

        if card.is_wild:
            if chosen_color not in COLORS:
                chosen_color = self.best_color(current)
            self.active_color = chosen_color
        else:
            assert card.color is not None
            self.active_color = card.color

        message = f"{current.name} juega {card.label_es()}"
        if card.is_wild:
            message += f" y elige {COLOR_NAMES_ES[self.active_color]}"
        self._event(message + ".")

        self._apply_effect(card)

        if len(current.hand) == 1:
            self._event(f"¡{current.name} grita UNO!")
        if not current.hand:
            self._player_wins(current)
        return message

    def _apply_effect(self, card: Card) -> None:
        """Move the turn according to ``card`` using the linked list operations."""
        table = self.table
        if card.value == SKIP:
            skipped = table.peek_next()
            self._event(f"{skipped.name} pierde el turno.")
            table.next_turn(skip=1)
        elif card.value == REVERSE:
            if len(table) == 2:
                self._event("Con 2 jugadores la Reversa actúa como Salta.")
                table.next_turn(skip=1)
            else:
                table.reverse_direction()
                table.next_turn()
        elif card.value in (DRAW_TWO, WILD_DRAW_FOUR):
            amount = 2 if card.value == DRAW_TWO else 4
            victim = table.peek_next()
            got = self._draw_cards(victim, amount)
            self._event(f"{victim.name} roba {got} cartas y pierde el turno.")
            table.next_turn(skip=1)
        else:
            table.next_turn()

    def _player_wins(self, player: Player) -> None:
        """Remove a player with no cards from the ring (``remove_player``)."""
        place = len(self.rankings) + 1
        self.rankings.append(player.name)
        self._event(f"{player.name} se queda sin cartas: puesto #{place}. Sale de la mesa.")
        self.table.remove_player(player.name)
        if len(self.table) == 1:
            last = self.table.head
            self.rankings.append(last.name)
            self._event(f"Partida terminada. {last.name} queda último.")

    def draw_card(self, player: Player | None = None) -> Card | None:
        """Current player draws one card.

        If the card is playable the player keeps the turn and may play it (or
        call ``pass_turn``); otherwise the turn passes automatically.

        Returns:
            The drawn card, or None if no cards were left.

        Raises:
            GameError: If it is not the player's turn or they already drew.
        """
        current = self._require_turn(player)
        if self.drawn_card is not None:
            raise GameError("Ya robaste una carta en este turno.")
        card = self.deck.draw()
        if card is None:
            self._event(f"{current.name} no puede robar: no quedan cartas. Pasa.")
            self.table.next_turn()
            return None
        current.hand.append(card)
        if self.is_playable(card):
            self.drawn_card = card
            self._event(f"{current.name} roba una carta (se puede jugar).")
        else:
            self._event(f"{current.name} roba una carta y pasa.")
            self.table.next_turn()
        return card

    def pass_turn(self, player: Player | None = None) -> None:
        """Pass after drawing a playable card that the player decides to keep.

        Raises:
            GameError: If the player has not drawn this turn.
        """
        current = self._require_turn(player)
        if self.drawn_card is None:
            raise GameError("Solo puedes pasar después de robar.")
        self.drawn_card = None
        self._event(f"{current.name} pasa.")
        self.table.next_turn()

    # --------------------------------------------------------------------- AI
    def best_color(self, player: Player) -> str:
        """Most frequent color in ``player``'s hand (random if none)."""
        counts = Counter(c.color for c in player.hand if c.color is not None)
        if not counts:
            return self.rng.choice(COLORS)
        return counts.most_common(1)[0][0]

    def choose_cpu_card(self, player: Player) -> int | None:
        """Pick the index of the card a CPU should play, or None.

        Strategy: when the next player is close to winning, attack (+4, +2,
        Salta, Reversa); otherwise keep wilds for later and dump cards of the
        active color first.
        """
        options = self.playable_indices(player)
        if not options:
            return None
        hand = player.hand
        nxt = self.table.peek_next()
        threatened = nxt is not None and nxt.card_count <= 2

        def score(i: int) -> float:
            card = hand[i]
            if threatened:
                attack = {WILD_DRAW_FOUR: 50, DRAW_TWO: 40, SKIP: 30, REVERSE: 25}
                if card.value in attack:
                    return attack[card.value]
            if card.value == WILD_DRAW_FOUR:
                return -20
            if card.is_wild:
                return -10
            base = 10 if card.color == self.active_color else 5
            return base + (3 if not card.is_number else 0) + self.rng.random()

        return max(options, key=score)

    def cpu_turn(self) -> str:
        """Play one full turn for the current CPU player.

        Returns:
            A short Spanish summary of what happened.
        """
        current = self._require_turn(None)
        index = self.choose_cpu_card(current)
        if index is not None:
            card = current.hand[index]
            return self.play_card(index, self.best_color(current) if card.is_wild else None)
        drawn = self.draw_card()
        if drawn is not None and self.drawn_card is drawn:
            index = self.playable_indices(current)[0]
            return self.play_card(index, self.best_color(current) if drawn.is_wild else None)
        return f"{current.name} roba y pasa"
