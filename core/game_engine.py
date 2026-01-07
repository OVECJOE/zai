"""
Main game engine coordinating all systems.
Provides high-level API for game management.
"""

from typing import Optional, List, Set
from enum import Enum
from hex import HexGrid, Hex
from core.entities.player import Player, Phase
from game_state import GameState, GameStateManager
from core.entities.move import Move, PlacementMove, SacrificeMove
from move_generator import MoveGenerator
from win_detector import WinDetector
from connectivity import ConnectivityEngine
from ai_engine import AIEngine, SearchResult


class GameMode(Enum):
    """Game mode enumeration."""
    HUMAN_VS_HUMAN = "human_vs_human"
    HUMAN_VS_AI = "human_vs_ai"
    AI_VS_AI = "ai_vs_ai"


class Difficulty(Enum):
    """AI difficulty levels."""
    EASY = (2, 1.0)      # depth, time_limit
    MEDIUM = (4, 2.0)
    HARD = (6, 5.0)
    EXPERT = (8, 10.0)
    
    def __init__(self, depth: int, time_limit: float):
        self.depth = depth
        self.time_limit = time_limit


class GameEngine:
    """
    Main game engine for Zai.
    Coordinates all game systems and provides clean API.
    """
    
    def __init__(self, mode: GameMode = GameMode.HUMAN_VS_HUMAN):
        """
        Initialize game engine.
        
        Args:
            mode: Game mode (human vs human, human vs AI, etc.)
        """
        self.grid = HexGrid(radius=3)
        self.state_manager = GameStateManager(self.grid)
        self.move_generator = MoveGenerator(self.grid)
        self.win_detector = WinDetector(self.grid)
        self.connectivity = ConnectivityEngine(self.grid)
        self.ai = AIEngine(self.grid)
        
        self.mode = mode
        self.ai_player: Optional[Player] = None
        self.ai_difficulty = Difficulty.MEDIUM
        
        # Initialize game
        self.state = self.state_manager.create_initial_state()
        
    def configure_ai(self, ai_player: Player, difficulty: Difficulty = Difficulty.MEDIUM):
        """Configure AI player and difficulty."""
        self.ai_player = ai_player
        self.ai_difficulty = difficulty
    
    def new_game(self):
        """Start a new game."""
        self.state = self.state_manager.create_initial_state()
        self.ai.clear_cache()
    
    def make_move(self, move: Move) -> bool:
        """
        Make a move for the current player.
        
        Args:
            move: Move to make
            
        Returns:
            True if move was successful, False if invalid
        """
        if self.state.winner is not None:
            return False
        
        # Validate move
        if not self.is_valid_move(move):
            return False
        
        # Apply move
        self.state = self.state_manager.apply_move(self.state, move)
        
        # Check win condition
        winner = self.win_detector.check_winner(
            set(self.state.stones),
            self.get_previous_player()
        )
        
        if winner is not None:
            self.state = self.state_manager.set_winner(self.state, winner)
        
        return True
    
    def make_ai_move(self) -> Optional[Move]:
        """
        Make AI move if it's AI's turn.
        
        Returns:
            The move made, or None if not AI's turn or game is over
        """
        if self.state.winner is not None:
            return None
        
        if self.ai_player != self.state.active_player:
            return None
        
        # Search for best move
        result = self.ai.find_best_move(
            self.state,
            max_depth=self.ai_difficulty.depth,
            time_limit=self.ai_difficulty.time_limit
        )
        
        if result.best_move:
            self.make_move(result.best_move)
            return result.best_move
        
        return None
    
    def is_valid_move(self, move: Move) -> bool:
        """Check if a move is valid."""
        legal_moves = self.get_legal_moves()
        return move in legal_moves
    
    def get_legal_moves(self) -> List[Move]:
        """Get all legal moves for current player."""
        return self.move_generator.get_legal_moves(
            set(self.state.stones),
            self.state.active_player,
            self.state.phase,
            self.state.turn
        )
    
    def get_legal_placements(self) -> List[Hex]:
        """Get all legal placement positions."""
        moves = self.get_legal_moves()
        positions = []
        
        for move in moves:
            if isinstance(move, PlacementMove):
                positions.append(move.position)
        
        return positions
    
    def can_sacrifice(self) -> bool:
        """Check if current player can make a sacrifice move."""
        if self.state.phase != Phase.EXPANSION:
            return False
        
        moves = self.get_legal_moves()
        return any(isinstance(m, SacrificeMove) for m in moves)
    
    def get_stone_at(self, position: Hex) -> Optional[Player]:
        """Get player of stone at position, or None if empty."""
        stone = self.state.get_stone_at(position)
        return stone.player if stone else None
    
    def get_current_player(self) -> Player:
        """Get the current active player."""
        return self.state.active_player
    
    def get_previous_player(self) -> Player:
        """Get the player who just moved."""
        return self.state.active_player.opponent()
    
    def get_winner(self) -> Optional[Player]:
        """Get the winner if game is over."""
        return self.state.winner
    
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.state.winner is not None
    
    def get_turn_number(self) -> int:
        """Get current turn number."""
        return self.state.turn
    
    def get_phase(self) -> Phase:
        """Get current game phase."""
        return self.state.phase
    
    def get_stone_count(self, player: Player) -> int:
        """Get stone count for a player."""
        return self.state.get_stone_count(player)
    
    def get_board_state(self) -> dict:
        """
        Get complete board state for rendering.
        
        Returns:
            Dictionary with:
                - stones: list of {player, position}
                - turn: current turn
                - phase: current phase
                - active_player: current player
                - winner: winner if any
        """
        return self.state.to_dict()
    
    def get_move_history(self) -> List[Move]:
        """Get history of all moves."""
        return list(self.state.move_history)
    
    def export_game(self) -> str:
        """Export game state as JSON."""
        return self.state.to_json()
    
    def get_ai_analysis(self) -> Optional[SearchResult]:
        """
        Get AI analysis of current position.
        Returns search result without making a move.
        """
        if self.state.winner is not None:
            return None
        
        return self.ai.find_best_move(
            self.state,
            max_depth=self.ai_difficulty.depth,
            time_limit=self.ai_difficulty.time_limit
        )
    
    def undo_move(self) -> bool:
        """
        Undo last move (not implemented in immutable design).
        Would require storing state history.
        """
        # Not implemented - would need state history stack
        return False
    
    def get_connectivity_info(self, player: Player) -> dict:
        """
        Get connectivity information for analysis.
        
        Returns:
            Dictionary with:
                - is_connected: bool
                - articulation_points: list of critical positions
                - bridges: list of critical edges
                - components: number of separate components
        """
        stones = set(self.state.stones)
        
        is_connected = self.connectivity.is_connected(stones, player)
        articulation_points = list(
            self.connectivity.find_articulation_points(stones, player)
        )
        bridges = list(self.connectivity.find_bridges(stones, player))
        
        components = self.connectivity.find_components(stones)
        component_count = len(components[player])
        
        return {
            'is_connected': is_connected,
            'articulation_points': [{'q': h.q, 'r': h.r} for h in articulation_points],
            'bridges': [
                [{'q': h1.q, 'r': h1.r}, {'q': h2.q, 'r': h2.r}]
                for h1, h2 in bridges
            ],
            'component_count': component_count
        }
