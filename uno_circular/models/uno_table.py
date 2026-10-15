"""The UNO table: a circular doubly linked list of Player nodes.

This is the core of the assignment. No Python ``list``/``deque`` is used to
store the players: every player is reachable only through ``head`` and the
``prev`` / ``next`` pointers.

Invariant kept by every operation (non-empty table)::

    head.prev  -> last player
    last.next  -> head
    node.next.prev is node   and   node.prev.next is node   for every node
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

from models.player import Player

CLOCKWISE = 1
COUNTERCLOCKWISE = -1


class UnoTable:
    """Circular doubly linked list where each node is a seated ``Player``.

    Attributes:
        head: Reference player ("first" seat). In a circular list there is no
            real beginning; ``head`` is only an entry point.
        current_turn: Player who must play now.
        direction: 1 = clockwise (follow ``next``), -1 = counter-clockwise
            (follow ``prev``).
        size: Number of seated players.
        logger: Optional callback that receives a Spanish description of every
            pointer operation (used by the "Estructura de datos" panel).
    """

    def __init__(self, logger: Callable[[str], None] | None = None) -> None:
        self.head: Player | None = None
        self.current_turn: Player | None = None
        self.direction: int = CLOCKWISE
        self.size: int = 0
        self.logger = logger

    # ------------------------------------------------------------------ utils
    def _log(self, message: str) -> None:
        """Send a pointer-operation message to the logger, if any."""
        if self.logger is not None:
            self.logger(message)

    def is_empty(self) -> bool:
        """Return True when no player is seated (``head is None``)."""
        return self.head is None

    def __len__(self) -> int:
        return self.size

    def __iter__(self) -> Iterator[Player]:
        return self.traverse_clockwise()

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.find_player(name) is not None

    @property
    def last(self) -> Player | None:
        """Last player, which in a circular doubly linked list is ``head.prev``."""
        return self.head.prev if self.head is not None else None

    @property
    def direction_pointer(self) -> str:
        """Name of the pointer followed by the turn: 'next' or 'prev'."""
        return "next" if self.direction == CLOCKWISE else "prev"

    def _check_new_player(self, player: Player) -> None:
        if self.find_player(player.name) is not None:
            raise ValueError(f"Ya existe un jugador llamado '{player.name}'.")

    # -------------------------------------------------------------- insertion
    def add_player_first(self, player: Player) -> None:
        """Seat ``player`` at the beginning of the table (``insert_at_beginning``).

        The new player becomes ``head``; the old last player now points to it.

        Raises:
            ValueError: If a player with the same name is already seated.
        """
        self._check_new_player(player)
        if self.head is None:
            # Single node: it points to itself in both directions.
            player.next = player
            player.prev = player
            self.head = player
            self._log(f"Insertar al inicio {player.name}: lista vacía → "
                      f"{player.name}.next = {player.name}.prev = {player.name}, head = {player.name}")
        else:
            last = self.head.prev
            player.next = self.head
            player.prev = last
            self.head.prev = player
            last.next = player
            self._log(f"Insertar al inicio {player.name}: {player.name}.next → {self.head.name}, "
                      f"{player.name}.prev → {last.name}, {self.head.name}.prev → {player.name}, "
                      f"{last.name}.next → {player.name}, head = {player.name}")
            self.head = player
        self.size += 1

    def add_player_last(self, player: Player) -> None:
        """Seat ``player`` at the end of the table (``insert_at_end``).

        The new player is placed between the current last player and ``head``;
        ``head`` does not change.

        Raises:
            ValueError: If a player with the same name is already seated.
        """
        self._check_new_player(player)
        if self.head is None:
            player.next = player
            player.prev = player
            self.head = player
            self._log(f"Insertar al final {player.name}: lista vacía → "
                      f"{player.name}.next = {player.name}.prev = {player.name}, head = {player.name}")
        else:
            last = self.head.prev
            last.next = player
            player.prev = last
            player.next = self.head
            self.head.prev = player
            self._log(f"Insertar al final {player.name}: {last.name}.next → {player.name}, "
                      f"{player.name}.prev → {last.name}, {player.name}.next → {self.head.name}, "
                      f"{self.head.name}.prev → {player.name} (nuevo último)")
        self.size += 1

    # ---------------------------------------------------------------- removal
    def remove_player(self, name: str) -> Player | None:
        """Remove the player called ``name`` without breaking the ring.

        Cases handled:
            * empty table → returns None;
            * player not found → returns None;
            * only player → table becomes empty;
            * removing ``head`` → ``head`` moves to ``head.next``;
            * removing the last (``head.prev``) or a middle player → neighbours
              are relinked.
        If the removed player had the turn, the turn passes to the neighbour
        in the current ``direction``.

        Returns:
            The removed ``Player`` (with its pointers cleared) or None.
        """
        if self.head is None:
            self._log(f"Eliminar {name}: la lista está vacía, no hay nada que eliminar")
            return None

        node = self.find_player(name)
        if node is None:
            self._log(f"Eliminar {name}: no se encontró en la mesa")
            return None

        if self.size == 1:
            # Only player: the ring disappears.
            self.head = None
            self.current_turn = None
            self._log(f"Eliminado {name}: era el único nodo → head = None (lista vacía)")
        else:
            before, after = node.prev, node.next
            # Turn successor must be computed before relinking.
            successor = after if self.direction == CLOCKWISE else before

            before.next = after
            after.prev = before

            if node is self.head:
                self.head = after
                case = f" (era head → head = {after.name})"
            elif after is self.head:  # node was head.prev
                case = f" (era el último → nuevo último = {before.name})"
            else:
                case = " (nodo del medio)"
            self._log(f"Eliminado {name}: {before.name}.next → {after.name}, "
                      f"{after.name}.prev → {before.name}{case}")

            if node is self.current_turn:
                self.current_turn = successor
                self._log(f"El turno pasa de {name} a {successor.name} "
                          f"(siguiendo {self.direction_pointer})")

        node.next = None
        node.prev = None
        self.size -= 1
        return node

    # ------------------------------------------------------------------ turns
    def start_turns(self, player: Player | None = None) -> Player | None:
        """Set ``current_turn`` to ``player`` (default: ``head``)."""
        self.current_turn = player if player is not None else self.head
        if self.current_turn is not None:
            self._log(f"current_turn = {self.current_turn.name}")
        return self.current_turn

    def peek_next(self, steps: int = 1) -> Player | None:
        """Return the player ``steps`` seats away in the current direction (no move)."""
        node = self.current_turn or self.head
        if node is None:
            return None
        for _ in range(steps):
            node = node.next if self.direction == CLOCKWISE else node.prev
        return node

    def next_turn(self, skip: int = 0) -> Player | None:
        """Advance the turn ``1 + skip`` seats following ``direction``.

        Args:
            skip: Number of players to jump over (e.g. 1 for "Salta").

        Returns:
            The new ``current_turn`` (None if the table is empty).
        """
        if self.head is None:
            return None
        if self.current_turn is None:
            return self.start_turns()
        previous = self.current_turn
        self.current_turn = self.peek_next(1 + skip)
        jumped = f", saltando {skip}" if skip else ""
        self._log(f"Turno: {previous.name}.{self.direction_pointer} → "
                  f"current_turn = {self.current_turn.name}{jumped}")
        return self.current_turn

    def reverse_direction(self) -> int:
        """Invert the direction of play and return the new ``direction``."""
        self.direction *= -1
        self._log(f"Reversa: dirección = {self.direction_pointer} "
                  f"({'horario ↻' if self.direction == CLOCKWISE else 'antihorario ↺'})")
        return self.direction

    # ----------------------------------------------------------------- search
    def find_player(self, name: str) -> Player | None:
        """Return the player called ``name`` or None (one lap, no infinite loop)."""
        for player in self.traverse_clockwise():
            if player.name == name:
                return player
        return None

    # --------------------------------------------------------------- traversal
    def traverse_clockwise(self, start: Player | None = None) -> Iterator[Player]:
        """Yield every player once following ``next``.

        Starts at ``start`` (default ``head``) and stops when it comes back to
        the starting node, so it never loops forever.
        """
        if self.head is None:
            return
        first = start if start is not None else self.head
        node = first
        while True:
            yield node
            node = node.next
            if node is first:
                break

    def traverse_counterclockwise(self, start: Player | None = None) -> Iterator[Player]:
        """Yield every player once following ``prev``.

        Starts at ``start`` (default ``head.prev``, the last player) so the
        output is the exact reverse of ``traverse_clockwise()``.
        """
        if self.head is None:
            return
        first = start if start is not None else self.head.prev
        node = first
        while True:
            yield node
            node = node.prev
            if node is first:
                break

    def display_table(self, to_console: bool = True) -> str:
        """Return (and optionally print) the table, like ``print_list`` in class.

        Note: the lecture's ``print_list`` reads the global ``my_list.head``
        instead of ``self.head``; that only works for one specific instance.
        This version uses ``self.head`` so it works for any table.
        """
        if self.head is None:
            text = "Mesa vacía"
        else:
            names = " <-> ".join(p.name for p in self.traverse_clockwise())
            text = f"{names} <-> (vuelve a {self.head.name})"
        if to_console:
            print(text)
        return text

    # -------------------------------------------------------------- invariant
    def validate_links(self) -> bool:
        """Check the circular doubly linked invariant.

        Verifies that ``size`` matches the nodes reachable through ``next``
        and through ``prev``, that ``node.next.prev is node`` and
        ``node.prev.next is node`` for every node, that ``head.prev.next`` is
        ``head`` and that ``current_turn`` (if set) is seated.
        """
        if self.head is None:
            return self.size == 0 and self.current_turn is None

        if self.head.prev is None or self.head.prev.next is not self.head:
            return False

        # Walk forward with an upper bound so a broken ring cannot hang us.
        count = 0
        node = self.head
        found_current = self.current_turn is None
        while True:
            if node.next is None or node.prev is None:
                return False
            if node.next.prev is not node or node.prev.next is not node:
                return False
            if node is self.current_turn:
                found_current = True
            count += 1
            if count > self.size:
                return False
            node = node.next
            if node is self.head:
                break
        if count != self.size or not found_current:
            return False

        back = 0
        node = self.head
        while True:
            back += 1
            if back > self.size:
                return False
            node = node.prev
            if node is self.head:
                break
        return back == self.size
