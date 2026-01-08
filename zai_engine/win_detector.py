"""
Win condition detection system.
Implements all four win conditions efficiently.
"""

from typing import Optional, Set, List
from collections import deque
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone
from zai_engine.connectivity import ConnectivityEngine


class WinDetector:
    """Detects all win conditions on a Hex board."""

    def __init__(self, grid: HexGrid) -> None:
        self.grid = grid
        self.conn_engine = ConnectivityEngine(grid)
    
    def check_winner(self, stones: Set[Stone], active_player: Player) -> Optional[Player]:
        """
        Check all win conditions and return winner if any.
        Checks in order of computational efficiency.
        """
        # Check isolation first (fastest)
        winner = self.detect_isolation(stones)
        if winner:
            return winner
        
        # Check territory control (fast)
        winner = self.detect_territory_control(stones)
        if winner:
            return winner
        
        # Check encirclement (medium)
        winner = self.detect_encirclement(stones, active_player)
        if winner:
            return winner
        
        # Check network completion (slower)
        winner = self.detect_network_completion(stones)
        if winner:
            return winner
        
        return None
    
    def detect_isolation(self, stones: Set[Stone]) -> Optional[Player]:
        """
        Detect if a player's network is disconnected.
        The opponent wins if a player self-isolates.
        """
        for player in [Player.WHITE, Player.RED]:
            if not self.conn_engine.is_connected(stones, player):
                # Player is disconnected, opponent wins
                return Player.opponent(player)
    
    def detect_territory_control(self, stones: Set[Stone]) -> Optional[Player]:
        """
        Detect if a player controls 5+ of the 6 void-adjacent hexes.
        """
        void_adjacent = self.grid.get_void_adjacent_hexes()

        white_control = 0
        red_control = 0

        for hex_pos in void_adjacent:
            for stone in stones:
                if stone.position == hex_pos:
                    if stone.player == Player.WHITE:
                        white_control += 1
                    elif stone.player == Player.RED:
                        red_control += 1
                    break
        
        if white_control >= 5:
            return Player.WHITE
        if red_control >= 5:
            return Player.RED
        
        return None
    
    def detect_encirclement(
        self,
        stones: Set[Stone],
        active_player: Player
    ) -> Optional[Player]:
        """
        Detect if active player has completely surrounded opponent stones.
        """
        opponent = active_player.opponent()

        # Get opponent components
        components = self.conn_engine.find_components(stones)
        opponent_components: List[Set[Hex]] = components.get(opponent, [])
        
        # Check each opponent component (already Set[Hex])
        for component in opponent_components:
            if self._is_encircled(stones, component, active_player):
                return active_player
        
        return None

    def _is_encircled(
        self,
        stones: Set[Stone],
        component: Set[Hex],
        encircling_player: Player
    ) -> bool:
        """
        Check if a component is completely encircled.
        All empty neighbors must be controlled by encircling player.
        """
        stone_positions = {s.position for s in stones}
        
        # Find all empty hexes adjacent to the component
        adjacent_empty = set()
        for hex_pos in component:
            for neighbor in self.grid.get_neighbors(hex_pos):
                if neighbor not in stone_positions:
                    adjacent_empty.add(neighbor)
        
        if not adjacent_empty:
            # Component has no empty neighbors (shouldn't happen normally)
            return False
        
        # Check if all adjacent empty hexes are surrounded by encircling player
        for empty_hex in adjacent_empty:
            # Check if this empty hex can reach the edge without crossing encircling stones
            if self._can_reach_edge_without_crossing(
                empty_hex, 
                stones, 
                encircling_player
            ):
                return False
        
        return True
    
    def _can_reach_edge_without_crossing(
        self,
        start: Hex,
        stones: Set[Stone],
        blocking_player: Player
    ) -> bool:
        """
        Check if a hex can reach any board edge without crossing blocking player's stones.
        Uses BFS on empty hexes and opponent hexes.
        """
        stone_positions = {s.position: s.player for s in stones}
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            
            # Check if reached edge
            if self.grid.is_edge_hex(current) >= 0:
                return True
            
            for neighbor in self.grid.get_neighbors(current):
                if neighbor in visited:
                    continue
                
                # Can move through empty hexes or opponent's stones
                neighbor_player = stone_positions.get(neighbor)
                if neighbor_player is None or neighbor_player != blocking_player:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return False
    
    def detect_network_completion(self, stones: Set[Stone]) -> Optional[Player]:
        """
        Detect if a player has a connected chain touching all 6 edges.
        """
        for player in [Player.WHITE, Player.RED]:
            if self._touches_all_edges(stones, player):
                return player
        
        return None

    def _touches_all_edges(self, stones: Set[Stone], player: Player) -> bool:
        """
        Check if player's connected network touches all 6 edges.
        """
        player_positions = {s.position for s in stones if s.player == player}
        
        if not player_positions:
            return False
        
        # BFS from each stone to find its connected component
        visited_global = set()
        
        for start_pos in player_positions:
            if start_pos in visited_global:
                continue
            
            # Find this component
            component = {start_pos}
            visited_global.add(start_pos)
            queue = deque([start_pos])
            
            while queue:
                current = queue.popleft()
                
                for neighbor in self.grid.get_neighbors(current):
                    if neighbor in player_positions and neighbor not in visited_global:
                        visited_global.add(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
            
            # Check which edges this component touches
            component_edges = set()
            for hex_pos in component:
                edge_idx = self.grid.is_edge_hex(hex_pos)
                if edge_idx >= 0:
                    component_edges.add(edge_idx)
            
            # If this component touches all 6 edges, player wins
            if len(component_edges) == 6:
                return True
        
        return False
