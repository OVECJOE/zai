"""
Connectivity analysis engine.
Validates stone networks and detects critical structures.
"""

from typing import Set, List, Dict, Tuple
from collections import deque
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone


class ConnectivityEngine:
    """Analyzes connectivity of stone networks."""

    def __init__(self, grid: HexGrid):
        self.grid = grid
    
    def is_connected(self, stones: Set[Stone], player: Player) -> bool:
        """
        Check if all stones of a player form a connected network.
        Uses BFS for O(n) performance.
        """
        player_stones = {s.position for s in stones if s.player == player}
        if not player_stones:
            return True  # No stones means trivially connected
        
        # Start BFS from an arbitrary stone
        start = next(iter(player_stones))
        visited = {start}
        queue = deque([start])

        while queue:
            current = queue.popleft()
            for neighbor in self.grid.get_neighbors(current):
                if neighbor in player_stones and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # All stones must be reachable
        return len(visited) == len(player_stones)

    def find_components(self, stones: Set[Stone]) -> Dict[Player, List[Set[Hex]]]:
        """
        Find all connected components for each player.
        Returns dict mapping player to list of component sets (positions).
        """

        components = {Player.WHITE: [], Player.RED: []}

        for player in components.keys():
            player_positions = {s.position for s in stones if s.player == player}
            unvisited = player_positions.copy()

            while unvisited:
                # Start a new component
                start = unvisited.pop()
                component = {start}
                queue = deque([start])

                while queue:
                    current = queue.popleft()
                    for neighbor in self.grid.get_neighbors(current):
                        if neighbor in unvisited:
                            unvisited.remove(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
                        
                components[player].append(component)
            
        return components
    
    def find_articulation_points(
        self,
        stones: Set[Stone],
        player: Player
    ):
        """
        Find critical stones whose removal would disconnect the network.
        Uses Tarjan's algorithm with DFS.
        """
        player_positions = {s.position for s in stones if s.player == player}

        if len(player_positions) <= 1:
            return set()

        articulation_points = set()
        visited = set()
        discovery_time = {}
        low = {}
        parent = {}
        time = [0]  # Mutable time counter

        def dfs(u: Hex):
            children = 0
            visited.add(u)
            discovery_time[u] = low[u] = time[0]
            time[0] += 1
            
            for v in self.grid.get_neighbors(u):
                if v not in player_positions:
                    continue
                
                if v not in visited:
                    children += 1
                    parent[v] = u
                    dfs(v)
                    
                    low[u] = min(low[u], low[v])
                    
                    # Check articulation point conditions
                    if parent.get(u) is None and children > 1:
                        articulation_points.add(u)
                    
                    if parent.get(u) is not None and low[v] >= discovery_time[u]:
                        articulation_points.add(u)
                
                elif v != parent.get(u):
                    low[u] = min(low[u], discovery_time[v])
        
        start = next(iter(player_positions))
        parent[start] = None
        dfs(start)

        return articulation_points
    
    def find_bridges(
        self, 
        stones: Set[Stone], 
        player: Player
    ) -> Set[Tuple[Hex, Hex]]:
        """
        Find critical edges whose removal would disconnect the network.
        """
        player_positions = {s.position for s in stones if s.player == player}
        
        if len(player_positions) <= 1:
            return set()
        
        bridges = set()
        visited = set()
        discovery_time = {}
        low = {}
        parent = {}
        time = [0]
        
        def dfs(u: Hex):
            visited.add(u)
            discovery_time[u] = low[u] = time[0]
            time[0] += 1
            
            for v in self.grid.get_neighbors(u):
                if v not in player_positions:
                    continue
                
                if v not in visited:
                    parent[v] = u
                    dfs(v)
                    
                    low[u] = min(low[u], low[v])
                    
                    # Bridge condition
                    if low[v] > discovery_time[u]:
                        bridge = tuple(sorted([u, v], key=lambda h: (h.q, h.r)))
                        bridges.add(bridge)
                
                elif v != parent.get(u):
                    low[u] = min(low[u], discovery_time[v])
        
        start = next(iter(player_positions))
        parent[start] = None
        dfs(start)
        
        return bridges
    
    def would_disconnect(
        self,
        stones: Set[Stone],
        player: Player,
        removal_position: Hex
    ) -> bool:
        """
        Check if removing a stone would disconnect the network.
        Optimized check without full articulation point algorithm.
        """
        player_positions = {s.position for s in stones if s.player == player}
        
        if removal_position not in player_positions:
            return False
        
        if len(player_positions) <= 1:
            return False
        
        # Create temporary network without the stone
        temp_positions = player_positions - {removal_position}
        
        if not temp_positions:
            return False
        
        # BFS from arbitrary remaining stone
        start = next(iter(temp_positions))
        visited = {start}
        queue = deque([start])
        
        while queue:
            current = queue.popleft()
            
            for neighbor in self.grid.get_neighbors(current):
                if neighbor in temp_positions and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) != len(temp_positions)
