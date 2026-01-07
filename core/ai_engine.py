"""
AI engine using minimax with alpha-beta pruning.
Supports iterative deepening and transposition tables.
"""

import time
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from core.hex import HexGrid
from core.entities.player import Player
from core.game_state import GameState, GameStateManager
from core.entities.move import Move
from core.move_generator import MoveGenerator
from core.win_detector import WinDetector
from core.evaluator import PositionEvaluator


@dataclass
class SearchResult:
    """Result of AI search."""
    best_move: Optional[Move]
    score: float
    nodes_searched: int
    depth_reached: int
    time_elapsed: float


class TranspositionTable:
    """Cache for previously evaluated positions."""
    
    def __init__(self, max_size: int = 1000000):
        self.max_size = max_size
        self.table: Dict[int, Tuple[float, int, Move]] = {}
        self.hits = 0
        self.misses = 0
    
    def get(self, state_hash: int, depth: int) -> Optional[Tuple[float, Move]]:
        """Get cached evaluation if available and deep enough."""
        if state_hash in self.table:
            score, cached_depth, move = self.table[state_hash]
            if cached_depth >= depth:
                self.hits += 1
                return (score, move)
        
        self.misses += 1
        return None
    
    def put(self, state_hash: int, depth: int, score: float, move: Move):
        """Store evaluation in cache."""
        if len(self.table) >= self.max_size:
            # Simple eviction: clear half the table
            items = list(self.table.items())
            self.table = dict(items[len(items)//2:])
        
        self.table[state_hash] = (score, depth, move)
    
    def clear(self):
        """Clear the table."""
        self.table.clear()
        self.hits = 0
        self.misses = 0


class AIEngine:
    """AI player using minimax search."""
    
    def __init__(self, grid: HexGrid):
        self.grid = grid
        self.state_manager = GameStateManager(grid)
        self.move_generator = MoveGenerator(grid)
        self.win_detector = WinDetector(grid)
        self.evaluator = PositionEvaluator(grid)
        self.transposition_table = TranspositionTable()
    
    def find_best_move(
        self,
        state: GameState,
        max_depth: int = 4,
        time_limit: float = 5.0
    ) -> SearchResult:
        """
        Find best move using iterative deepening.
        
        Args:
            state: Current game state
            max_depth: Maximum search depth
            time_limit: Time limit in seconds
            
        Returns:
            SearchResult with best move and statistics
        """
        start_time = time.time()
        best_move = None
        best_score = float('-inf')
        nodes_searched = 0
        depth_reached = 0
        
        # Iterative deepening
        for depth in range(1, max_depth + 1):
            if time.time() - start_time > time_limit:
                break
            
            try:
                score, move, nodes = self._search_root(
                    state,
                    depth,
                    start_time,
                    time_limit
                )
                
                best_move = move
                best_score = score
                nodes_searched += nodes
                depth_reached = depth
                
            except TimeoutError:
                break
        
        time_elapsed = time.time() - start_time
        
        return SearchResult(
            best_move=best_move,
            score=best_score,
            nodes_searched=nodes_searched,
            depth_reached=depth_reached,
            time_elapsed=time_elapsed
        )
    
    def _search_root(
        self,
        state: GameState,
        depth: int,
        start_time: float,
        time_limit: float
    ) -> Tuple[float, Optional[Move], int]:
        """Search at root level with move ordering."""
        moves = self.move_generator.get_legal_moves(
            set(state.stones),
            state.active_player,
            state.phase,
            state.turn
        )
        
        if not moves:
            return 0.0, None, 0
        
        best_score = float('-inf')
        best_move = None
        nodes = 0
        alpha = float('-inf')
        beta = float('inf')
        
        for move in moves:
            if time.time() - start_time > time_limit:
                raise TimeoutError()
            
            # Apply move
            new_state = self.state_manager.apply_move(state, move)
            
            # Check for immediate win
            winner = self.win_detector.check_winner(
                set(new_state.stones),
                state.active_player
            )
            
            if winner is not None:
                new_state = self.state_manager.set_winner(new_state, winner)
            
            # Search
            score, child_nodes = self._minimax(
                new_state,
                depth - 1,
                alpha,
                beta,
                False,
                state.active_player,
                start_time,
                time_limit
            )
            
            nodes += child_nodes + 1
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, score)
        
        return best_score, best_move, nodes
    
    def _minimax(
        self,
        state: GameState,
        depth: int,
        alpha: float,
        beta: float,
        maximizing: bool,
        maximizing_player: Player,
        start_time: float,
        time_limit: float
    ) -> Tuple[float, int]:
        """
        Minimax with alpha-beta pruning.
        
        Returns:
            (score, nodes_searched)
        """
        # Check timeout
        if time.time() - start_time > time_limit:
            raise TimeoutError()
        
        # Terminal conditions
        if state.winner is not None:
            eval_score = self.evaluator.evaluate(state, maximizing_player)
            return eval_score, 0
        
        if depth == 0:
            eval_score = self.evaluator.evaluate(state, maximizing_player)
            return eval_score, 0
        
        # Check transposition table
        state_hash = hash(state)
        cached = self.transposition_table.get(state_hash, depth)
        if cached is not None:
            return cached[0], 0
        
        # Generate moves
        moves = self.move_generator.get_legal_moves(
            set(state.stones),
            state.active_player,
            state.phase,
            state.turn
        )
        
        if not moves:
            # No legal moves (shouldn't happen normally)
            eval_score = self.evaluator.evaluate(state, maximizing_player)
            return eval_score, 0
        
        nodes = 0
        
        if maximizing:
            max_score = float('-inf')
            best_move = None
            
            for move in moves:
                # Apply move
                new_state = self.state_manager.apply_move(state, move)
                
                # Check win
                winner = self.win_detector.check_winner(
                    set(new_state.stones),
                    state.active_player
                )
                
                if winner is not None:
                    new_state = self.state_manager.set_winner(new_state, winner)
                
                # Recurse
                score, child_nodes = self._minimax(
                    new_state,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    maximizing_player,
                    start_time,
                    time_limit
                )
                
                nodes += child_nodes + 1
                
                if score > max_score:
                    max_score = score
                    best_move = move
                
                alpha = max(alpha, score)
                
                if beta <= alpha:
                    break  # Beta cutoff
            
            # Cache result
            if best_move:
                self.transposition_table.put(state_hash, depth, max_score, best_move)
            
            return max_score, nodes
        
        else:
            min_score = float('inf')
            best_move = None
            
            for move in moves:
                # Apply move
                new_state = self.state_manager.apply_move(state, move)
                
                # Check win
                winner = self.win_detector.check_winner(
                    set(new_state.stones),
                    state.active_player
                )
                
                if winner is not None:
                    new_state = self.state_manager.set_winner(new_state, winner)
                
                # Recurse
                score, child_nodes = self._minimax(
                    new_state,
                    depth - 1,
                    alpha,
                    beta,
                    True,
                    maximizing_player,
                    start_time,
                    time_limit
                )
                
                nodes += child_nodes + 1
                
                if score < min_score:
                    min_score = score
                    best_move = move
                
                beta = min(beta, score)
                
                if beta <= alpha:
                    break  # Alpha cutoff
            
            # Cache result
            if best_move:
                self.transposition_table.put(state_hash, depth, min_score, best_move)
            
            return min_score, nodes
    
    def clear_cache(self):
        """Clear transposition table."""
        self.transposition_table.clear()
