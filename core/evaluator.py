"""
Position evaluation for AI.
Heuristic evaluation of game positions.
"""

from typing import Set
from core.hex import HexGrid
from core.entities.player import Stone, Player
from core.game_state import GameState
from core.connectivity import ConnectivityEngine


class PositionEvaluator:
    """Evaluates game positions for AI decision making."""

    # Evaluation weights
    WEIGHT_MATERIAL = 10.0
    WEIGHT_VOID_CONTROL = 50.0
    WEIGHT_EDGE_PROGRESS = 30.0
    WEIGHT_CONNECTIVITY = 40.0
    WEIGHT_ARTICULATION = -25.0
    WEIGHT_BRIDGE = 15.0
    WEIGHT_ENCIRCLEMENT = 100.0
    WEIGHT_EDGE_TOUCH = 20.0

    def __init__(self, grid: HexGrid):
        self.grid = grid
        self.connectivity = ConnectivityEngine(grid)
    
    def evaluate(self, state: GameState, maximizing_player: Player) -> float:
        """
        Evaluate position from maximizing player's perspective.
        Positive = good for maximizing player.
        Negative = good for opponent.
        """
        if state.winner is not None:
            # Terminal position
            if state.winner == maximizing_player:
                return 10000.0
            else:
                return -10000.0
        
        score = 0.0
        opponent = maximizing_player.opponent()
        
        # Material count
        score += self._evaluate_material(state, maximizing_player, opponent)
        
        # Void control
        score += self._evaluate_void_control(state, maximizing_player, opponent)
        
        # Edge progress
        score += self._evaluate_edge_progress(state, maximizing_player, opponent)
        
        # Connectivity strength
        score += self._evaluate_connectivity(state, maximizing_player, opponent)
        
        # Encirclement threats
        score += self._evaluate_encirclement(state, maximizing_player, opponent)
        
        return score
    
    def _evaluate_material(
        self,
        state: GameState,
        player: Player,
        opponent: Player
    ) -> float:
        """Evaluate stone count difference."""
        player_count = state.get_stone_count(player)
        opponent_count = state.get_stone_count(opponent)
        
        return (player_count - opponent_count) * self.WEIGHT_MATERIAL
    
    def _evaluate_void_control(
        self,
        state: GameState,
        player: Player,
        opponent: Player
    ) -> float:
        """Evaluate control of hexes adjacent to void stone."""
        void_adjacent = self.grid.get_void_adjacent_hexes()
        
        player_control = 0
        opponent_control = 0
        
        for hex_pos in void_adjacent:
            stone = state.get_stone_at(hex_pos)
            if stone:
                if stone.player == player:
                    player_control += 1
                elif stone.player == opponent:
                    opponent_control += 1
        
        control_diff = player_control - opponent_control
        
        # Bonus for being close to winning condition (5+ void control)
        if player_control >= 4:
            control_diff += 2
        if opponent_control >= 4:
            control_diff -= 2
        
        return control_diff * self.WEIGHT_VOID_CONTROL
    
    def _evaluate_edge_progress(
        self,
        state: GameState,
        player: Player,
        opponent: Player
    ) -> float:
        """Evaluate progress toward touching all edges."""
        player_stones = state.get_player_stones(player)
        opponent_stones = state.get_player_stones(opponent)
        
        player_edges = self._count_edges_touched(player_stones)
        opponent_edges = self._count_edges_touched(opponent_stones)
        
        score = (player_edges - opponent_edges) * self.WEIGHT_EDGE_PROGRESS
        
        # Bonus for touching many edges
        if player_edges >= 5:
            score += 100.0
        if opponent_edges >= 5:
            score -= 100.0
        
        return score
    
    def _count_edges_touched(self, stones: Set[Stone]) -> int:
        """Count how many edges are touched by stones."""
        if not stones:
            return 0
        
        positions = {s.position for s in stones}
        edges_touched = set()
        
        for pos in positions:
            edge_idx = self.grid.is_edge_hex(pos)
            if edge_idx >= 0:
                edges_touched.add(edge_idx)
        
        return len(edges_touched)
    
    def _evaluate_connectivity(
        self,
        state: GameState,
        player: Player,
        opponent: Player
    ) -> float:
        """
        Evaluate network strength.
        Fewer articulation points = stronger network.
        More bridges = stronger network.
        """
        score = 0.0
        
        # Player connectivity
        stones_set = set(state.stones)
        player_articulation = self.connectivity.find_articulation_points(
            stones_set, player
        )
        player_bridges = self.connectivity.find_bridges(
            stones_set, player
        )
        
        # Opponent connectivity
        opponent_articulation = self.connectivity.find_articulation_points(
            stones_set, opponent
        )
        opponent_bridges = self.connectivity.find_bridges(
            stones_set, opponent
        )
        
        # Fewer articulation points is better
        score += (len(opponent_articulation) - len(player_articulation)) * self.WEIGHT_ARTICULATION
        
        # More bridges is better
        score += (len(player_bridges) - len(opponent_bridges)) * self.WEIGHT_BRIDGE
        
        return score
    
    def _evaluate_encirclement(
        self,
        state: GameState,
        player: Player,
        opponent: Player
    ) -> float:
        """
        Evaluate encirclement threats.
        Check if either player has isolated opponent groups.
        """
        score = 0.0
        
        # Find components
        components = self.connectivity.find_components(set(state.stones))
        
        # Multiple opponent components is good (potential encirclement)
        opponent_components = components[opponent]
        player_components = components[player]
        
        if len(opponent_components) > 1:
            score += self.WEIGHT_ENCIRCLEMENT * 0.5
        
        if len(player_components) > 1:
            score -= self.WEIGHT_ENCIRCLEMENT * 0.5
        
        return score
    
    def quick_evaluate(self, state: GameState, player: Player) -> float:
        """
        Fast evaluation for move ordering.
        Only uses cheap heuristics.
        """
        if state.winner is not None:
            return 10000.0 if state.winner == player else -10000.0
        
        opponent = player.opponent()
        
        # Material and void control only
        score = 0.0
        score += self._evaluate_material(state, player, opponent)
        score += self._evaluate_void_control(state, player, opponent)
        
        return score
