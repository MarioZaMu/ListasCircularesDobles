"""Unit tests for UnoTable (circular doubly linked list).

Run from the project root:  python -m unittest discover -v
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from models.player import Player
from models.uno_table import CLOCKWISE, COUNTERCLOCKWISE, UnoTable


def names_cw(table: UnoTable) -> list[str]:
    return [p.name for p in table.traverse_clockwise()]


def names_ccw(table: UnoTable) -> list[str]:
    return [p.name for p in table.traverse_counterclockwise()]


def make_table(*names: str) -> UnoTable:
    table = UnoTable()
    for name in names:
        table.add_player_last(Player(name))
    return table


class TestEmptyTable(unittest.TestCase):
    def test_new_table_is_empty(self) -> None:
        table = UnoTable()
        self.assertTrue(table.is_empty())
        self.assertEqual(len(table), 0)
        self.assertIsNone(table.head)
        self.assertIsNone(table.current_turn)
        self.assertEqual(table.direction, CLOCKWISE)
        self.assertTrue(table.validate_links())

    def test_traversals_on_empty_table_yield_nothing(self) -> None:
        table = UnoTable()
        self.assertEqual(names_cw(table), [])
        self.assertEqual(names_ccw(table), [])

    def test_remove_from_empty_table(self) -> None:
        table = UnoTable()
        self.assertIsNone(table.remove_player("Ana"))
        self.assertTrue(table.validate_links())

    def test_next_turn_on_empty_table(self) -> None:
        self.assertIsNone(UnoTable().next_turn())

    def test_find_on_empty_table(self) -> None:
        self.assertIsNone(UnoTable().find_player("Ana"))

    def test_display_empty(self) -> None:
        self.assertEqual(UnoTable().display_table(to_console=False), "Mesa vacía")


class TestInsertion(unittest.TestCase):
    def test_add_first_into_empty_points_to_itself(self) -> None:
        table = UnoTable()
        ana = Player("Ana")
        table.add_player_first(ana)
        self.assertIs(table.head, ana)
        self.assertIs(ana.next, ana)
        self.assertIs(ana.prev, ana)
        self.assertEqual(len(table), 1)
        self.assertTrue(table.validate_links())

    def test_add_last_into_empty_points_to_itself(self) -> None:
        table = UnoTable()
        ana = Player("Ana")
        table.add_player_last(ana)
        self.assertIs(table.head, ana)
        self.assertIs(ana.next, ana)
        self.assertIs(ana.prev, ana)
        self.assertTrue(table.validate_links())

    def test_add_first_changes_head(self) -> None:
        table = make_table("Luis", "Sofía")
        ana = Player("Ana")
        table.add_player_first(ana)
        self.assertIs(table.head, ana)
        self.assertEqual(names_cw(table), ["Ana", "Luis", "Sofía"])
        self.assertIs(ana.prev, table.find_player("Sofía"))
        self.assertIs(table.head.prev.next, ana)
        self.assertTrue(table.validate_links())

    def test_add_last_keeps_head_and_becomes_head_prev(self) -> None:
        table = make_table("Ana", "Luis")
        sofia = Player("Sofía")
        table.add_player_last(sofia)
        self.assertEqual(table.head.name, "Ana")
        self.assertIs(table.head.prev, sofia)
        self.assertIs(sofia.next, table.head)
        self.assertIs(table.last, sofia)
        self.assertEqual(names_cw(table), ["Ana", "Luis", "Sofía"])
        self.assertTrue(table.validate_links())

    def test_mixed_insertions(self) -> None:
        table = UnoTable()
        table.add_player_last(Player("B"))
        table.add_player_first(Player("A"))
        table.add_player_last(Player("C"))
        table.add_player_first(Player("Z"))
        self.assertEqual(names_cw(table), ["Z", "A", "B", "C"])
        self.assertEqual(len(table), 4)
        self.assertTrue(table.validate_links())

    def test_duplicate_name_rejected(self) -> None:
        table = make_table("Ana")
        with self.assertRaises(ValueError):
            table.add_player_last(Player("Ana"))
        with self.assertRaises(ValueError):
            table.add_player_first(Player("Ana"))
        self.assertEqual(len(table), 1)
        self.assertTrue(table.validate_links())


class TestRemoval(unittest.TestCase):
    def test_remove_not_found(self) -> None:
        table = make_table("Ana", "Luis")
        self.assertIsNone(table.remove_player("Pedro"))
        self.assertEqual(len(table), 2)
        self.assertTrue(table.validate_links())

    def test_remove_only_player(self) -> None:
        table = make_table("Ana")
        table.start_turns()
        removed = table.remove_player("Ana")
        self.assertEqual(removed.name, "Ana")
        self.assertIsNone(removed.next)
        self.assertIsNone(removed.prev)
        self.assertTrue(table.is_empty())
        self.assertIsNone(table.current_turn)
        self.assertEqual(len(table), 0)
        self.assertTrue(table.validate_links())

    def test_remove_head(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.remove_player("Ana")
        self.assertEqual(table.head.name, "Luis")
        self.assertEqual(table.head.prev.name, "Sofía")
        self.assertIs(table.head.prev.next, table.head)
        self.assertEqual(names_cw(table), ["Luis", "Sofía"])
        self.assertTrue(table.validate_links())

    def test_remove_last(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.remove_player("Sofía")
        self.assertEqual(table.head.name, "Ana")
        self.assertEqual(table.head.prev.name, "Luis")
        self.assertIs(table.find_player("Luis").next, table.head)
        self.assertEqual(names_cw(table), ["Ana", "Luis"])
        self.assertTrue(table.validate_links())

    def test_remove_middle(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.remove_player("Luis")
        ana, sofia = table.find_player("Ana"), table.find_player("Sofía")
        self.assertIs(ana.next, sofia)
        self.assertIs(sofia.prev, ana)
        self.assertEqual(names_cw(table), ["Ana", "Sofía"])
        self.assertEqual(names_ccw(table), ["Sofía", "Ana"])
        self.assertTrue(table.validate_links())

    def test_remove_down_to_one_then_empty(self) -> None:
        table = make_table("Ana", "Luis")
        table.remove_player("Ana")
        luis = table.head
        self.assertIs(luis.next, luis)
        self.assertIs(luis.prev, luis)
        self.assertTrue(table.validate_links())
        table.remove_player("Luis")
        self.assertTrue(table.is_empty())
        self.assertTrue(table.validate_links())

    def test_remove_current_turn_clockwise_passes_to_next(self) -> None:
        table = make_table("Ana", "Luis", "Sofía", "Pedro")
        table.start_turns(table.find_player("Luis"))
        table.remove_player("Luis")
        self.assertEqual(table.current_turn.name, "Sofía")
        self.assertTrue(table.validate_links())

    def test_remove_current_turn_counterclockwise_passes_to_prev(self) -> None:
        table = make_table("Ana", "Luis", "Sofía", "Pedro")
        table.start_turns(table.find_player("Luis"))
        table.reverse_direction()
        table.remove_player("Luis")
        self.assertEqual(table.current_turn.name, "Ana")
        self.assertTrue(table.validate_links())

    def test_remove_current_turn_when_it_is_head(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.start_turns()
        table.remove_player("Ana")
        self.assertEqual(table.head.name, "Luis")
        self.assertEqual(table.current_turn.name, "Luis")
        self.assertTrue(table.validate_links())

    def test_remove_current_turn_when_it_is_last(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.start_turns(table.last)
        table.remove_player("Sofía")
        self.assertEqual(table.current_turn.name, "Ana")  # wraps to head
        self.assertTrue(table.validate_links())

    def test_remove_other_player_keeps_turn(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.start_turns()
        table.remove_player("Sofía")
        self.assertEqual(table.current_turn.name, "Ana")
        self.assertTrue(table.validate_links())


class TestTurnsAndDirection(unittest.TestCase):
    def setUp(self) -> None:
        self.table = make_table("Ana", "Luis", "Sofía", "Pedro")
        self.table.start_turns()

    def test_next_turn_wraps_around(self) -> None:
        order = [self.table.next_turn().name for _ in range(5)]
        self.assertEqual(order, ["Luis", "Sofía", "Pedro", "Ana", "Luis"])

    def test_next_turn_without_start_uses_head(self) -> None:
        table = make_table("Ana", "Luis")
        self.assertEqual(table.next_turn().name, "Ana")

    def test_skip(self) -> None:
        self.assertEqual(self.table.next_turn(skip=1).name, "Sofía")
        # From Sofía, skipping 2 moves 3 seats: Pedro, Ana, Luis.
        self.assertEqual(self.table.next_turn(skip=2).name, "Luis")

    def test_reverse_direction(self) -> None:
        self.assertEqual(self.table.reverse_direction(), COUNTERCLOCKWISE)
        self.assertEqual(self.table.direction_pointer, "prev")
        order = [self.table.next_turn().name for _ in range(5)]
        self.assertEqual(order, ["Pedro", "Sofía", "Luis", "Ana", "Pedro"])
        self.assertEqual(self.table.reverse_direction(), CLOCKWISE)
        self.assertEqual(self.table.next_turn().name, "Ana")

    def test_reverse_does_not_touch_links(self) -> None:
        before = names_cw(self.table)
        self.table.reverse_direction()
        self.assertEqual(names_cw(self.table), before)
        self.assertTrue(self.table.validate_links())

    def test_peek_next_does_not_move(self) -> None:
        self.assertEqual(self.table.peek_next().name, "Luis")
        self.assertEqual(self.table.current_turn.name, "Ana")

    def test_single_player_turn_stays(self) -> None:
        table = make_table("Ana")
        table.start_turns()
        self.assertEqual(table.next_turn().name, "Ana")
        table.reverse_direction()
        self.assertEqual(table.next_turn(skip=3).name, "Ana")


class TestTraversal(unittest.TestCase):
    def test_clockwise_one_full_lap(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        self.assertEqual(names_cw(table), ["Ana", "Luis", "Sofía"])

    def test_counterclockwise_is_reverse(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        self.assertEqual(names_ccw(table), ["Sofía", "Luis", "Ana"])

    def test_traversal_from_custom_start(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        luis = table.find_player("Luis")
        self.assertEqual([p.name for p in table.traverse_clockwise(luis)], ["Luis", "Sofía", "Ana"])
        self.assertEqual([p.name for p in table.traverse_counterclockwise(luis)],
                         ["Luis", "Ana", "Sofía"])

    def test_single_node_traversal_terminates(self) -> None:
        table = make_table("Ana")
        self.assertEqual(names_cw(table), ["Ana"])
        self.assertEqual(names_ccw(table), ["Ana"])

    def test_iter_and_contains(self) -> None:
        table = make_table("Ana", "Luis")
        self.assertEqual([p.name for p in table], ["Ana", "Luis"])
        self.assertIn("Luis", table)
        self.assertNotIn("Pedro", table)

    def test_find_player(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        self.assertEqual(table.find_player("Sofía").name, "Sofía")
        self.assertIsNone(table.find_player("Pedro"))

    def test_display_table_uses_self_head(self) -> None:
        table_a = make_table("Ana", "Luis")
        table_b = make_table("X", "Y", "Z")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            text_a = table_a.display_table()
            text_b = table_b.display_table()
        self.assertEqual(text_a, "Ana <-> Luis <-> (vuelve a Ana)")
        self.assertEqual(text_b, "X <-> Y <-> Z <-> (vuelve a X)")
        self.assertIn(text_a, buffer.getvalue())


class TestValidateLinks(unittest.TestCase):
    def test_detects_broken_next(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.find_player("Luis").next = table.head  # skips Sofía
        self.assertFalse(table.validate_links())

    def test_detects_broken_prev(self) -> None:
        table = make_table("Ana", "Luis", "Sofía")
        table.head.prev = table.find_player("Luis")
        self.assertFalse(table.validate_links())

    def test_detects_wrong_size(self) -> None:
        table = make_table("Ana", "Luis")
        table.size = 5
        self.assertFalse(table.validate_links())

    def test_detects_none_pointer(self) -> None:
        table = make_table("Ana", "Luis")
        table.head.next = None
        self.assertFalse(table.validate_links())

    def test_detects_current_turn_not_seated(self) -> None:
        table = make_table("Ana", "Luis")
        table.current_turn = Player("Fantasma")
        self.assertFalse(table.validate_links())

    def test_invariant_holds_through_random_operations(self) -> None:
        import random
        rng = random.Random(7)
        table = UnoTable()
        counter = 0
        for _ in range(500):
            op = rng.random()
            if op < 0.4 or table.is_empty():
                counter += 1
                player = Player(f"P{counter}")
                (table.add_player_first if rng.random() < 0.5 else table.add_player_last)(player)
                if table.current_turn is None:
                    table.start_turns()
            elif op < 0.7:
                target = rng.choice([p.name for p in table])
                table.remove_player(target)
            elif op < 0.85:
                table.next_turn(skip=rng.randint(0, 2))
            else:
                table.reverse_direction()
            self.assertTrue(table.validate_links())
            self.assertEqual(len(names_cw(table)), len(table))
            self.assertEqual(names_ccw(table), list(reversed(names_cw(table))))


class TestLogger(unittest.TestCase):
    def test_pointer_operations_are_logged(self) -> None:
        messages: list[str] = []
        table = UnoTable(logger=messages.append)
        for name in ("Ana", "Luis", "Sofía"):
            table.add_player_last(Player(name))
        table.remove_player("Luis")
        table.reverse_direction()
        self.assertTrue(any("Ana.next → Sofía" in m and "Sofía.prev → Ana" in m for m in messages))
        self.assertTrue(any("Reversa: dirección = prev" in m for m in messages))


if __name__ == "__main__":
    unittest.main()
