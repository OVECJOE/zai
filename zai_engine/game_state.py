"""
Game state management.
Immutable game state with efficient cloning and hashing.
"""

from dataclasses import dataclass
from typing import Set, Optional, Tuple
import json
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone, Phase
from zai_engine.entities.move import Move, PlacementMove, SacrificeMove


@dataclass(frozen=True)
class GameState:
    """
    Immutable game state.
    All modifications return a new GameState instance.
    """
    stones: frozenset[Stone]
    turn: int
    phase: Phase
    active_player: Player
    move_history: Tuple
    winner: Optional[Player] = None

    def __hash__(self) -> int:
        """Hash for transposition table."""
        return hash((self.stones, self.turn, self.phase, self.active_player))
    
    def to_dict(self) -> dict:
        """Serialize game state to dictionary."""
        return {
            'stones': [
                {'player': s.player.value, 'q': s.position.q, 'r': s.position.r}
                for s in self.stones
            ],
            'turn': self.turn,
            'phase': self.phase.value,
            'active_player': self.active_player.value,
            'move_history': len(self.move_history),
            'winner': self.winner.value if self.winner else None
        }
    
    def to_json(self) -> str:
        """Seralize to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)
    
    def zobrist_hash(self, zobrist_table: dict) -> str:
        """
        Compute Zobrist hash for transposition tables.
        zobrist_table maps (position, player) to random int.
        """
        h = 0
        for stone in self.stones:
            key = (stone.position, stone.player)
            if key in zobrist_table:
                h ^= zobrist_table[key]
        
        # Include turn parity
        if self.active_player == Player.WHITE:
            h ^= zobrist_table.get('white_turn', 0)
        else:
            h ^= zobrist_table.get('red_turn', 0)
        
        return h
    
    def get_stone_at(self, position: Hex) -> Optional[Stone]:
        """Get stone at a position, if any."""
        for stone in self.stones:
            if stone.position == position:
                return stone
        return None
    
    def get_player_stones(self, player: Player) -> Set[Stone]:
        """Get all stones belonging to a player."""
        return {s for s in self.stones if s.player == player}
    
    def get_stone_count(self, player: Player) -> int:
        """Count stones for a player."""
        return sum(1 for s in self.stones if s.player == player)


class GameStateManager:
    """Manages game state transitions."""
    
    PLACEMENT_PHASE_TURNS = 12
    MAX_STONES_PER_PLAYER = 24

    def __init__(self, grid: HexGrid) -> None:
        self.grid = grid
    
    def create_initial_state(self) -> GameState:
        """Create initial game state with void stone."""
        void_stone = Stone(Player.VOID, self.grid.void_stone)

        return GameState(
            stones=frozenset([void_stone]),
            turn=1,
            phase=Phase.PLACEMENT,
            active_player=Player.WHITE,
            move_history=tuple(),
            winner=None
        )

    def apply_move(self, state: GameState, move: Move) -> GameState:
        """
        Apply a move and return new state.
        Validates move but does not check win conditions.
        """
        if state.winner is not None:
            raise ValueError("Game is already over.")
        
        new_stones = set(state.stones)

        if isinstance(move, PlacementMove):
            # Add stone
            new_stone = Stone(state.active_player, move.position)
            if any(s.position == move.position for s in new_stones):
                raise ValueError("Cannot place on occupied hex.")
            new_stones.add(new_stone)

        elif isinstance(move, SacrificeMove):
            new_stones = {s for s in new_stones if s.position != move.sacrifice_position}
            if len(new_stones) >= len(state.stones):
                raise ValueError("No stone to sacrifice at given position.")
            
            # Add two new stones
            new_stones.add(Stone(state.active_player, move.first_placement))
            new_stones.add(Stone(state.active_player, move.second_placement))
        
        # Update turn and player
        next_turn = state.turn + 1
        next_player = state.active_player.opponent()

        # Update phase
        next_phase = state.phase
        if state.phase == Phase.PLACEMENT and next_turn > self.PLACEMENT_PHASE_TURNS:
            next_phase = Phase.EXPANSION
        
        # Add to history
        new_history = tuple(list(state.move_history) + [move])

        return GameState(
            stones=frozenset(new_stones),
            turn=next_turn,
            phase=next_phase,
            active_player=next_player,
            move_history=new_history,
            winner=None
        )
    
    def set_winner(self, state: GameState, winner: Player) -> GameState:
        """Create new state with winner set."""
        return GameState(
            stones=state.stones,
            turn=state.turn,
            phase=state.phase,
            active_player=state.active_player,
            move_history=state.move_history,
            winner=winner
        )
    
    def can_place_stone(self, player: Player, state: GameState) -> bool:
        """Check if player has stones remaining."""
        current_count = state.get_stone_count(player)
        return current_count < self.MAX_STONES_PER_PLAYER
    
    def is_game_over(self, state: GameState) -> bool:
        """Check if game is over."""
        return state.winner is not None
    
    def clone_state(self, state: GameState) -> GameState:
        """
        Clone state (returns same instance since state is immutable).
        Provided for API consistency.
        """
        return state
