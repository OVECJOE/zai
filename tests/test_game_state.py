"""
Robust test suite for GameState and GameStateManager classes in game_state.py
"""
import pytest
import json
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone, Phase
from zai_engine.entities.move import PlacementMove, SacrificeMove
from zai_engine.game_state import GameState, GameStateManager


class TestGameState:
    def setup_method(self):
        self.void_stone = Stone(Player.VOID, Hex(0, 0))
        self.white_stone = Stone(Player.WHITE, Hex(1, 0))
        self.red_stone = Stone(Player.RED, Hex(0, 1))

    def test_game_state_creation(self):
        state = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        assert state.turn == 1
        assert state.phase == Phase.PLACEMENT
        assert state.active_player == Player.WHITE
        assert state.winner is None

    def test_game_state_immutable(self):
        state = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        with pytest.raises(AttributeError):
            state.turn = 2

    def test_game_state_hash(self):
        state1 = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        state2 = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        assert hash(state1) == hash(state2)

    def test_game_state_different_hash(self):
        state1 = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        state2 = GameState(
            stones=frozenset([self.void_stone]),
            turn=2,
            phase=Phase.PLACEMENT,
            active_player=Player.RED,
            move_history=tuple(),
            winner=None
        )
        assert hash(state1) != hash(state2)

    def test_to_dict(self):
        state = GameState(
            stones=frozenset([self.void_stone, self.white_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        d = state.to_dict()
        assert d['turn'] == 1
        assert d['phase'] == 'placement'
        assert d['active_player'] == 'white'
        assert len(d['stones']) == 2

    def test_to_json(self):
        state = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        json_str = state.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed['turn'] == 1

    def test_zobrist_hash(self):
        zobrist_table = {
            (Hex(0, 0), Player.VOID): 12345,
            'white_turn': 67890
        }
        state = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        h = state.zobrist_hash(zobrist_table)
        assert h == (12345 ^ 67890)

    def test_get_stone_at_found(self):
        state = GameState(
            stones=frozenset([self.void_stone, self.white_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        stone = state.get_stone_at(Hex(1, 0))
        assert stone == self.white_stone

    def test_get_stone_at_not_found(self):
        state = GameState(
            stones=frozenset([self.void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        stone = state.get_stone_at(Hex(5, 5))
        assert stone is None

    def test_get_player_stones(self):
        state = GameState(
            stones=frozenset([self.void_stone, self.white_stone, self.red_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        white_stones = state.get_player_stones(Player.WHITE)
        assert len(white_stones) == 1
        assert self.white_stone in white_stones

    def test_get_stone_count(self):
        state = GameState(
            stones=frozenset([self.void_stone, self.white_stone, self.red_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        assert state.get_stone_count(Player.WHITE) == 1
        assert state.get_stone_count(Player.RED) == 1
        assert state.get_stone_count(Player.VOID) == 1


class TestGameStateManager:
    def setup_method(self):
        self.grid = HexGrid(3)
        self.manager = GameStateManager(self.grid)

    def test_create_initial_state(self):
        state = self.manager.create_initial_state()
        assert state.turn == 1
        assert state.phase == Phase.PLACEMENT
        assert state.active_player == Player.WHITE
        assert len(state.stones) == 1
        assert state.winner is None

    def test_apply_placement_move(self):
        state = self.manager.create_initial_state()
        move = PlacementMove(Hex(1, 0))
        new_state = self.manager.apply_move(state, move)
        
        assert new_state.turn == 2
        assert new_state.active_player == Player.RED
        assert len(new_state.stones) == 2
        assert new_state.get_stone_at(Hex(1, 0)) is not None

    def test_apply_move_invalid_occupied(self):
        state = self.manager.create_initial_state()
        move = PlacementMove(Hex(0, 0))  # Void stone position
        
        with pytest.raises(ValueError, match="Cannot place on occupied hex"):
            self.manager.apply_move(state, move)

    def test_apply_move_game_over(self):
        state = self.manager.create_initial_state()
        state = self.manager.set_winner(state, Player.WHITE)
        move = PlacementMove(Hex(1, 0))
        
        with pytest.raises(ValueError, match="Game is already over"):
            self.manager.apply_move(state, move)

    def test_phase_transition(self):
        state = self.manager.create_initial_state()
        
        # Apply 12 moves to reach turn 13
        for i in range(12):
            move = PlacementMove(Hex(i % 3, i // 3))
            try:
                state = self.manager.apply_move(state, move)
            except ValueError:
                # Skip if position occupied
                move = PlacementMove(Hex(i % 3 + 1, i // 3))
                state = self.manager.apply_move(state, move)
        
        assert state.phase == Phase.EXPANSION

    def test_apply_sacrifice_move(self):
        state = self.manager.create_initial_state()
        # Add some stones first
        state = self.manager.apply_move(state, PlacementMove(Hex(1, 0)))  # WHITE
        state = self.manager.apply_move(state, PlacementMove(Hex(0, 1)))  # RED
        state = self.manager.apply_move(state, PlacementMove(Hex(1, 1)))  # WHITE
        state = self.manager.apply_move(state, PlacementMove(Hex(-1, 1)))  # RED
        
        initial_count = len(state.stones)
        # Now WHITE's turn, sacrifice WHITE's stone at (1,0)
        sacrifice_move = SacrificeMove(Hex(1, 0), (Hex(2, 0), Hex(2, 1)))
        new_state = self.manager.apply_move(state, sacrifice_move)
        
        # Should have 1 less (removed) + 2 (added) = net +1
        assert len(new_state.stones) == initial_count + 1
        assert new_state.get_stone_at(Hex(1, 0)) is None
        assert new_state.get_stone_at(Hex(2, 0)) is not None

    def test_set_winner(self):
        state = self.manager.create_initial_state()
        new_state = self.manager.set_winner(state, Player.WHITE)
        
        assert new_state.winner == Player.WHITE
        assert new_state.turn == state.turn
        assert new_state.stones == state.stones

    def test_can_place_stone_true(self):
        state = self.manager.create_initial_state()
        assert self.manager.can_place_stone(Player.WHITE, state)

    def test_can_place_stone_false(self):
        # Create state with max stones
        stones = {Stone(Player.VOID, Hex(0, 0))}
        for i in range(24):
            stones.add(Stone(Player.WHITE, Hex(i % 5, i // 5)))
        
        state = GameState(
            stones=frozenset(stones),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )
        assert not self.manager.can_place_stone(Player.WHITE, state)

    def test_is_game_over_false(self):
        state = self.manager.create_initial_state()
        assert not self.manager.is_game_over(state)

    def test_is_game_over_true(self):
        state = self.manager.create_initial_state()
        state = self.manager.set_winner(state, Player.WHITE)
        assert self.manager.is_game_over(state)

    def test_clone_state(self):
        state = self.manager.create_initial_state()
        cloned = self.manager.clone_state(state)
        assert cloned is state  # Should be same instance (immutable)

    def test_move_history_tracking(self):
        state = self.manager.create_initial_state()
        move1 = PlacementMove(Hex(1, 0))
        state = self.manager.apply_move(state, move1)
        
        assert len(state.move_history) == 1
        assert state.move_history[0] == move1
        
        move2 = PlacementMove(Hex(0, 1))
        state = self.manager.apply_move(state, move2)
        
        assert len(state.move_history) == 2
        assert state.move_history[1] == move2

    def test_player_alternation(self):
        state = self.manager.create_initial_state()
        assert state.active_player == Player.WHITE
        
        state = self.manager.apply_move(state, PlacementMove(Hex(1, 0)))
        assert state.active_player == Player.RED
        
        state = self.manager.apply_move(state, PlacementMove(Hex(0, 1)))
        assert state.active_player == Player.WHITE
