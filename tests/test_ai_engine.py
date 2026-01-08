"""
Test suite for AIEngine in ai_engine.py
"""
import pytest
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone, Phase
from zai_engine.entities.move import PlacementMove, SacrificeMove
from zai_engine.game_state import GameState, GameStateManager
from zai_engine.ai_engine import AIEngine, TranspositionTable, SearchResult


def make_state(stones, turn=1, phase=Phase.PLACEMENT, active_player=Player.WHITE, winner=None):
    return GameState(
        stones=frozenset(stones),
        turn=turn,
        phase=phase,
        active_player=active_player,
        move_history=tuple(),
        winner=winner
    )


class TestTranspositionTable:
    def test_create_table(self):
        table = TranspositionTable(max_size=100)
        assert table.max_size == 100
        assert len(table.table) == 0

    def test_put_and_get(self):
        table = TranspositionTable()
        move = PlacementMove(Hex(1, 0))
        table.put(12345, 3, 100.0, move)
        
        result = table.get(12345, 3)
        assert result is not None
        assert result[0] == 100.0
        assert result[1] == move

    def test_get_insufficient_depth(self):
        table = TranspositionTable()
        move = PlacementMove(Hex(1, 0))
        table.put(12345, 2, 100.0, move)
        
        # Request deeper search than cached
        result = table.get(12345, 3)
        assert result is None

    def test_get_sufficient_depth(self):
        table = TranspositionTable()
        move = PlacementMove(Hex(1, 0))
        table.put(12345, 5, 100.0, move)
        
        # Request shallower search than cached
        result = table.get(12345, 3)
        assert result is not None

    def test_get_miss(self):
        table = TranspositionTable()
        result = table.get(99999, 3)
        assert result is None
        assert table.misses == 1

    def test_get_hit(self):
        table = TranspositionTable()
        move = PlacementMove(Hex(1, 0))
        table.put(12345, 3, 100.0, move)
        
        result = table.get(12345, 3)
        assert result is not None
        assert table.hits == 1

    def test_clear(self):
        table = TranspositionTable()
        move = PlacementMove(Hex(1, 0))
        table.put(12345, 3, 100.0, move)
        table.get(12345, 3)
        
        table.clear()
        assert len(table.table) == 0
        assert table.hits == 0
        assert table.misses == 0

    def test_eviction(self):
        table = TranspositionTable(max_size=2)
        move1 = PlacementMove(Hex(1, 0))
        move2 = PlacementMove(Hex(2, 0))
        move3 = PlacementMove(Hex(3, 0))
        
        table.put(1, 3, 100.0, move1)
        table.put(2, 3, 200.0, move2)
        table.put(3, 3, 300.0, move3)  # Should trigger eviction
        
        # Table should still have some entries
        assert len(table.table) <= table.max_size


class TestAIEngine:
    def setup_method(self):
        self.grid = HexGrid(3)
        self.engine = AIEngine(self.grid)

    def test_create_engine(self):
        assert self.engine.grid == self.grid
        assert self.engine.state_manager is not None
        assert self.engine.move_generator is not None
        assert self.engine.win_detector is not None
        assert self.engine.evaluator is not None
        assert self.engine.transposition_table is not None

    def test_find_best_move_initial_position(self):
        state = self.engine.state_manager.create_initial_state()
        result = self.engine.find_best_move(state, max_depth=2, time_limit=1.0)
        
        assert isinstance(result, SearchResult)
        assert result.best_move is not None
        assert isinstance(result.best_move, PlacementMove)
        assert result.nodes_searched > 0
        assert result.depth_reached > 0
        assert result.time_elapsed > 0

    def test_find_best_move_respects_time_limit(self):
        state = self.engine.state_manager.create_initial_state()
        result = self.engine.find_best_move(state, max_depth=10, time_limit=0.1)
        
        # Should stop before reaching max depth due to time limit
        assert result.time_elapsed <= 0.5  # Some tolerance
        assert result.best_move is not None

    def test_find_best_move_mid_game(self):
        state = self.engine.state_manager.create_initial_state()
        # Play a few moves
        state = self.engine.state_manager.apply_move(state, PlacementMove(Hex(1, 0)))
        state = self.engine.state_manager.apply_move(state, PlacementMove(Hex(0, 1)))
        
        result = self.engine.find_best_move(state, max_depth=2, time_limit=1.0)
        
        assert result.best_move is not None
        assert result.nodes_searched > 0

    def test_find_best_move_no_moves(self):
        # Create a state where no moves are possible (shouldn't happen in real game)
        stones = {Stone(Player.VOID, Hex(0, 0))}
        # Fill all adjacent hexes
        void_adj = self.grid.get_void_adjacent_hexes()
        for hex_pos in void_adj:
            stones.add(Stone(Player.RED, hex_pos))
        
        state = make_state(stones, active_player=Player.WHITE)
        result = self.engine.find_best_move(state, max_depth=2, time_limit=1.0)
        
        # Should handle gracefully
        assert result.best_move is None

    def test_clear_cache(self):
        state = self.engine.state_manager.create_initial_state()
        # Run search to populate cache
        self.engine.find_best_move(state, max_depth=2, time_limit=1.0)
        
        # Clear cache
        self.engine.clear_cache()
        assert len(self.engine.transposition_table.table) == 0

    def test_iterative_deepening(self):
        state = self.engine.state_manager.create_initial_state()
        result = self.engine.find_best_move(state, max_depth=3, time_limit=2.0)
        
        # Should reach some depth
        assert result.depth_reached >= 1
        assert result.depth_reached <= 3

    def test_search_result_structure(self):
        state = self.engine.state_manager.create_initial_state()
        result = self.engine.find_best_move(state, max_depth=1, time_limit=1.0)
        
        assert hasattr(result, 'best_move')
        assert hasattr(result, 'score')
        assert hasattr(result, 'nodes_searched')
        assert hasattr(result, 'depth_reached')
        assert hasattr(result, 'time_elapsed')

    def test_alpha_beta_pruning_efficiency(self):
        state = self.engine.state_manager.create_initial_state()
        
        # Search with depth 2
        result = self.engine.find_best_move(state, max_depth=2, time_limit=2.0)
        
        # Should search fewer nodes than full minimax would
        # (hard to test precisely, but should complete quickly)
        assert result.time_elapsed < 2.0

    def test_winning_move_detection(self):
        # Create a position where white can win
        void_adj = self.grid.get_void_adjacent_hexes()
        stones = {Stone(Player.VOID, Hex(0, 0))}
        # Place 4 white stones around void
        for i in range(4):
            stones.add(Stone(Player.WHITE, void_adj[i]))
        
        state = make_state(stones, active_player=Player.WHITE)
        result = self.engine.find_best_move(state, max_depth=1, time_limit=1.0)
        
        # Should find the winning move
        assert result.best_move is not None
        # The move should place on one of the remaining void-adjacent hexes
        if isinstance(result.best_move, PlacementMove):
            assert result.best_move.position in void_adj

    def test_transposition_table_usage(self):
        state = self.engine.state_manager.create_initial_state()
        
        # Run two searches
        self.engine.find_best_move(state, max_depth=2, time_limit=1.0)
        initial_hits = self.engine.transposition_table.hits
        
        # Second search should use cache
        self.engine.find_best_move(state, max_depth=2, time_limit=1.0)
        final_hits = self.engine.transposition_table.hits
        
        # Should have more cache hits
        assert final_hits > initial_hits


class TestSearchResult:
    def test_create_search_result(self):
        move = PlacementMove(Hex(1, 0))
        result = SearchResult(
            best_move=move,
            score=100.0,
            nodes_searched=50,
            depth_reached=3,
            time_elapsed=0.5
        )
        
        assert result.best_move == move
        assert result.score == 100.0
        assert result.nodes_searched == 50
        assert result.depth_reached == 3
        assert result.time_elapsed == 0.5

    def test_search_result_none_move(self):
        result = SearchResult(
            best_move=None,
            score=0.0,
            nodes_searched=0,
            depth_reached=0,
            time_elapsed=0.0
        )
        
        assert result.best_move is None
