"""Tests for the game rules built on top of UnoTable."""

from __future__ import annotations

import unittest

from game.deck import build_standard_deck
from game.uno_game import GameError, UnoGame
from models.card import BLUE, DRAW_TWO, RED, REVERSE, SKIP, WILD, Card
from models.player import Player
from models.uno_table import COUNTERCLOCKWISE, UnoTable


def make_game(*names: str, seed: int = 1) -> UnoGame:
    table = UnoTable()
    for i, name in enumerate(names):
        table.add_player_last(Player(name, is_human=(i == 0)))
    game = UnoGame(table, seed=seed)
    game.start()
    return game


def force_top(game: UnoGame, card: Card) -> None:
    game.deck.discard(card)
    game.active_color = card.color or RED


class TestDeck(unittest.TestCase):
    def test_standard_deck_has_108_cards(self) -> None:
        self.assertEqual(len(build_standard_deck()), 108)


class TestGameRules(unittest.TestCase):
    def test_start_deals_seven(self) -> None:
        game = make_game("Tú", "Ana", "Luis")
        for player in game.table:
            self.assertEqual(len(player.hand), 7)
        self.assertTrue(game.top_card.is_number)
        self.assertEqual(game.current_player.name, "Tú")

    def test_start_needs_two_players(self) -> None:
        table = UnoTable()
        table.add_player_last(Player("Solo"))
        with self.assertRaises(GameError):
            UnoGame(table).start()

    def test_skip(self) -> None:
        game = make_game("A", "B", "C")
        force_top(game, Card(RED, "5"))
        game.current_player.hand.insert(0, Card(RED, SKIP))
        game.play_card(0)
        self.assertEqual(game.current_player.name, "C")

    def test_reverse_with_three(self) -> None:
        game = make_game("A", "B", "C")
        force_top(game, Card(RED, "5"))
        game.current_player.hand.insert(0, Card(RED, REVERSE))
        game.play_card(0)
        self.assertEqual(game.table.direction, COUNTERCLOCKWISE)
        self.assertEqual(game.current_player.name, "C")

    def test_reverse_with_two_acts_as_skip(self) -> None:
        game = make_game("A", "B")
        force_top(game, Card(RED, "5"))
        game.current_player.hand.insert(0, Card(RED, REVERSE))
        game.play_card(0)
        self.assertEqual(game.current_player.name, "A")

    def test_draw_two(self) -> None:
        game = make_game("A", "B", "C")
        force_top(game, Card(RED, "5"))
        game.current_player.hand.insert(0, Card(RED, DRAW_TWO))
        game.play_card(0)
        self.assertEqual(len(game.table.find_player("B").hand), 9)
        self.assertEqual(game.current_player.name, "C")

    def test_wild_sets_color(self) -> None:
        game = make_game("A", "B")
        game.current_player.hand.insert(0, Card(None, WILD))
        game.play_card(0, chosen_color=BLUE)
        self.assertEqual(game.active_color, BLUE)

    def test_unplayable_card_rejected(self) -> None:
        game = make_game("A", "B")
        force_top(game, Card(RED, "5"))
        game.current_player.hand.insert(0, Card(BLUE, "7"))
        with self.assertRaises(GameError):
            game.play_card(0)

    def test_wrong_turn_rejected(self) -> None:
        game = make_game("A", "B")
        with self.assertRaises(GameError):
            game.draw_card(player=game.table.find_player("B"))

    def test_winner_leaves_table_and_game_continues(self) -> None:
        game = make_game("A", "B", "C")
        force_top(game, Card(RED, "5"))
        a = game.current_player
        a.hand[:] = [Card(RED, "3")]
        game.play_card(0)
        self.assertNotIn("A", game.table)
        self.assertEqual(len(game.table), 2)
        self.assertEqual(game.rankings, ["A"])
        self.assertFalse(game.is_over)
        self.assertTrue(game.table.validate_links())

    def test_full_cpu_games_finish(self) -> None:
        for seed in range(30):
            game = make_game("A", "B", "C", "D", "E", "F", seed=seed)
            for _ in range(5000):
                if game.is_over:
                    break
                game.cpu_turn()
                self.assertTrue(game.table.validate_links())
            self.assertTrue(game.is_over, f"seed {seed} did not finish")
            self.assertEqual(len(game.rankings), 6)
            self.assertEqual(len(set(game.rankings)), 6)


if __name__ == "__main__":
    unittest.main()
