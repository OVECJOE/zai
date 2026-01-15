"""
AI engine using minimax with alpha-beta pruning.
Supports iterative deepening and transposition tables.
"""

import time
import random
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from zai_engine.connectivity import ConnectivityEngine
from zai_engine.hex import HexGrid
from zai_engine.entities.player import Player
from zai_engine.game_state import GameState, GameStateManager
from zai_engine.entities.move import Move
from zai_engine.move_generator import MoveGenerator
from zai_engine.win_detector import WinDetector
from zai_engine.evaluator import PositionEvaluator


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
        self.connectivity = ConnectivityEngine(grid)
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
        
        # Initial legal moves
        moves = self.move_generator.get_legal_moves(
            set(state.stones),
            state.active_player,
            state.phase,
            state.turn
        )
        
        if not moves:
            return SearchResult(None, -float('inf'), 0, 0, 0)
            
        # FIX: Default to a random move to ensure we always return SOMETHING
        best_move = random.choice(moves)
        best_score = float('-inf')
        nodes_searched = 0
        depth_reached = 0
        
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
                
                # Only update if we completed the search for this depth
                if move:
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
            
            player_making_move = state.active_player
            new_state = self.state_manager.apply_move(state, move)
            
            stones_after = set(new_state.stones)
            if not self.connectivity.is_connected(stones_after, player_making_move):
                score = -10000.0
            else:
                winner = self.win_detector.check_winner(stones_after, player_making_move)
                
                if winner is not None:
                    new_state = self.state_manager.set_winner(new_state, winner)
                
                score, child_nodes = self._minimax(
                    new_state,
                    depth - 1,
                    alpha,
                    beta,
                    False,
                    player_making_move,
                    start_time,
                    time_limit
                )
                
                nodes += child_nodes
            
            nodes += 1
            
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
        """
        if time.time() - start_time > time_limit:
            raise TimeoutError()
        
        if state.winner is not None:
            eval_score = self.evaluator.evaluate(state, maximizing_player)
            return eval_score, 0
        
        if depth == 0:
            eval_score = self.evaluator.evaluate(state, maximizing_player)
            return eval_score, 0
        
        state_hash = hash(state)
        cached = self.transposition_table.get(state_hash, depth)
        if cached is not None:
            return cached[0], 0
        
        moves = self.move_generator.get_legal_moves(
            set(state.stones),
            state.active_player,
            state.phase,
            state.turn
        )
        
        if not moves:
            eval_score = self.evaluator.evaluate(state, maximizing_player)
            return eval_score, 0
        
        nodes = 0
        
        if maximizing:
            max_score = float('-inf')
            best_move = None
            
            for move in moves:
                player_making_move = state.active_player
                new_state = self.state_manager.apply_move(state, move)
                
                stones_after = set(new_state.stones)
                if not self.connectivity.is_connected(stones_after, player_making_move):
                    score = -10000.0
                else:
                    winner = self.win_detector.check_winner(stones_after, player_making_move)
                    
                    if winner is not None:
                        new_state = self.state_manager.set_winner(new_state, winner)
                    
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
                    
                    nodes += child_nodes
                
                nodes += 1
                
                if score > max_score:
                    max_score = score
                    best_move = move
                
                alpha = max(alpha, score)
                
                if beta <= alpha:
                    break
            
            if best_move:
                self.transposition_table.put(state_hash, depth, max_score, best_move)
            
            return max_score, nodes
        
        else:
            min_score = float('inf')
            best_move = None
            
            for move in moves:
                player_making_move = state.active_player
                new_state = self.state_manager.apply_move(state, move)
                
                stones_after = set(new_state.stones)
                if not self.connectivity.is_connected(stones_after, player_making_move):
                    score = 10000.0
                else:
                    winner = self.win_detector.check_winner(stones_after, player_making_move)
                    
                    if winner is not None:
                        new_state = self.state_manager.set_winner(new_state, winner)
                    
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
                    
                    nodes += child_nodes
                
                nodes += 1
                
                if score < min_score:
                    min_score = score
                    best_move = move
                
                beta = min(beta, score)
                
                if beta <= alpha:
                    break
            
            if best_move:
                self.transposition_table.put(state_hash, depth, min_score, best_move)
            
            return min_score, nodes
    
    def clear_cache(self):
        """Clear transposition table."""
        self.transposition_table.clear()
