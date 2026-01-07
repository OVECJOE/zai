"""
Test suite for PositionEvaluator in evaluator.py
"""
import pytest
from core.hex import Hex, HexGrid
from core.entities.player import Player, Stone, Phase
from core.game_state import GameState
from core.evaluator import PositionEvaluator


def make_state(stones, turn=1, phase=Phase.PLACEMENT, active_player=Player.WHITE, winner=None):
    return GameState(
        stones=frozenset(stones),
        turn=turn,
        phase=phase,
        active_player=active_player,
        move_history=tuple(),
        winner=winner
    )


class TestPositionEvaluator:
    def setup_method(self):
        self.grid = HexGrid(3)
        self.evaluator = PositionEvaluator(self.grid)

    def test_evaluate_terminal_win(self):
        stones = {Stone(Player.VOID, Hex(0, 0))}
        state = make_state(stones, winner=Player.WHITE)
        score = self.evaluator.evaluate(state, Player.WHITE)
        assert score == 10000.0

    def test_evaluate_terminal_loss(self):
        stones = {Stone(Player.VOID, Hex(0, 0))}
        state = make_state(stones, winner=Player.RED)
        score = self.evaluator.evaluate(state, Player.WHITE)
        assert score == -10000.0

    def test_evaluate_material_equal(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.RED, Hex(0, 1))
        }
        state = make_state(stones)
        score = self.evaluator._evaluate_material(state, Player.WHITE, Player.RED)
        assert score == 0.0

    def test_evaluate_material_advantage(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.WHITE, Hex(1, -1)),
            Stone(Player.RED, Hex(0, 1))
        }
        state = make_state(stones)
        score = self.evaluator._evaluate_material(state, Player.WHITE, Player.RED)
        assert score == self.evaluator.WEIGHT_MATERIAL

    def test_evaluate_void_control_none(self):
        stones = {Stone(Player.VOID, Hex(0, 0))}
        state = make_state(stones)
        score = self.evaluator._evaluate_void_control(state, Player.WHITE, Player.RED)
        assert score == 0.0

    def test_evaluate_void_control_white_advantage(self):
        void_adj = self.grid.get_void_adjacent_hexes()
        stones = {Stone(Player.VOID, Hex(0, 0))}
        stones.add(Stone(Player.WHITE, void_adj[0]))
        stones.add(Stone(Player.WHITE, void_adj[1]))
        state = make_state(stones)
        score = self.evaluator._evaluate_void_control(state, Player.WHITE, Player.RED)
        assert score > 0

    def test_evaluate_void_control_near_win(self):
        void_adj = self.grid.get_void_adjacent_hexes()
        stones = {Stone(Player.VOID, Hex(0, 0))}
        for i in range(4):
            stones.add(Stone(Player.WHITE, void_adj[i]))
        state = make_state(stones)
        score = self.evaluator._evaluate_void_control(state, Player.WHITE, Player.RED)
        # Should have bonus for being close to winning
        assert score > 4 * self.evaluator.WEIGHT_VOID_CONTROL

    def test_evaluate_edge_progress_none(self):
        stones = {Stone(Player.VOID, Hex(0, 0))}
        state = make_state(stones)
        score = self.evaluator._evaluate_edge_progress(state, Player.WHITE, Player.RED)
        assert score == 0.0

    def test_evaluate_edge_progress_white_advantage(self):
        # Place white stones on multiple edges
        stones = {Stone(Player.VOID, Hex(0, 0))}
        stones.add(Stone(Player.WHITE, Hex(3, -3)))  # Edge stone
        stones.add(Stone(Player.WHITE, Hex(-3, 3)))  # Different edge
        state = make_state(stones)
        score = self.evaluator._evaluate_edge_progress(state, Player.WHITE, Player.RED)
        assert score > 0

    def test_count_edges_touched_empty(self):
        stones = set()
        count = self.evaluator._count_edges_touched(stones)
        assert count == 0

    def test_count_edges_touched_multiple(self):
        stones = {
            Stone(Player.WHITE, Hex(3, -3)),
            Stone(Player.WHITE, Hex(-3, 3))
        }
        count = self.evaluator._count_edges_touched(stones)
        assert count >= 1

    def test_evaluate_connectivity_equal(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.WHITE, Hex(1, -1)),
            Stone(Player.RED, Hex(0, 1)),
            Stone(Player.RED, Hex(0, 2))
        }
        state = make_state(stones)
        # Both players have similar connectivity
        score = self.evaluator._evaluate_connectivity(state, Player.WHITE, Player.RED)
        # Score should be relatively neutral
        assert abs(score) < 200

    def test_evaluate_encirclement_none(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.RED, Hex(0, 1))
        }
        state = make_state(stones)
        score = self.evaluator._evaluate_encirclement(state, Player.WHITE, Player.RED)
        # No disconnected components
        assert score == 0.0

    def test_evaluate_encirclement_opponent_split(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.RED, Hex(0, 1)),
            Stone(Player.RED, Hex(2, 2))  # Disconnected red stone
        }
        state = make_state(stones)
        score = self.evaluator._evaluate_encirclement(state, Player.WHITE, Player.RED)
        # Red has multiple components, good for white
        assert score > 0

    def test_quick_evaluate_terminal_win(self):
        stones = {Stone(Player.VOID, Hex(0, 0))}
        state = make_state(stones, winner=Player.WHITE)
        score = self.evaluator.quick_evaluate(state, Player.WHITE)
        assert score == 10000.0

    def test_quick_evaluate_terminal_loss(self):
        stones = {Stone(Player.VOID, Hex(0, 0))}
        state = make_state(stones, winner=Player.RED)
        score = self.evaluator.quick_evaluate(state, Player.WHITE)
        assert score == -10000.0

    def test_quick_evaluate_non_terminal(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.RED, Hex(0, 1))
        }
        state = make_state(stones)
        score = self.evaluator.quick_evaluate(state, Player.WHITE)
        # Should return some reasonable score
        assert -10000 < score < 10000

    def test_evaluate_full_position(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.WHITE, Hex(1, -1)),
            Stone(Player.RED, Hex(0, 1)),
            Stone(Player.RED, Hex(0, 2))
        }
        state = make_state(stones)
        score = self.evaluator.evaluate(state, Player.WHITE)
        # Should return some reasonable score
        assert -10000 < score < 10000

    def test_evaluate_symmetry(self):
        stones = {
            Stone(Player.VOID, Hex(0, 0)),
            Stone(Player.WHITE, Hex(1, 0)),
            Stone(Player.RED, Hex(0, 1))
        }
        state = make_state(stones)
        white_score = self.evaluator.evaluate(state, Player.WHITE)
        red_score = self.evaluator.evaluate(state, Player.RED)
        # Scores should be opposite
        assert abs(white_score + red_score) < 50  # Allow some asymmetry from void control
