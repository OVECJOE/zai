
"""
Move generation engine.
Generates all legal moves for a given game state.
"""

from typing import List, Set
from zai_engine.hex import HexGrid
from zai_engine.entities.player import Player, Stone, Phase
from zai_engine.entities.move import Move, PlacementMove, SacrificeMove, create_placement_move, create_sacrifice_move
from zai_engine.connectivity import ConnectivityEngine


class MoveGenerator:
    """Generates legal moves for Zai."""

    def __init__(self, grid: HexGrid) -> None:
        self.grid = grid
        self.conn_engine = ConnectivityEngine(grid)
    
    def get_legal_moves(
        self,
        stones: Set[Stone],
        active_player: Player,
        phase: Phase,
        turn: int
    ) -> List[Move]:
        """
        Get all legal moves for the current position.
        
        Args:
            stones: Current stones on board
            active_player: Player whose turn it is
            phase: Current game phase
            turn: Current turn number
            
        Returns:
            List of legal moves
        """
        moves = []

        # Always generate placement moves
        placement_moves = self._get_legal_placements(stones, active_player)
        moves.extend(placement_moves)

        # Add sacrifice moves if in expansion phase
        if phase == Phase.EXPANSION:
            sacrifice_moves = self._get_legal_sacrifices(stones, active_player)
            moves.extend(sacrifice_moves)
        
        return moves
    
    def _get_legal_placements(self, stones: Set[Stone], active_player: Player) -> List[PlacementMove]:
        """Get all legal placement positions."""
        stone_positions = {s.position for s in stones}
        player_positions = {s.position for s in stones if s.player == active_player}

        legal_positions = set()

        # If player has no stones, can place adjacent to void
        if not player_positions:
            void_adjacent = self.grid.get_void_adjacent_hexes()
            for hex_pos in void_adjacent:
                if hex_pos not in stone_positions:
                    legal_positions.add(hex_pos)
        else:
            # Can place adjacent to any of the player's stones
            for player_pos in player_positions:
                for neighbor in self.grid.get_neighbors(player_pos):
                    if neighbor not in stone_positions:
                        legal_positions.add(neighbor)
        
        # Convert to moves
        return [create_placement_move(pos) for pos in legal_positions]
    
    def _get_legal_sacrifices(
        self,
        stones: Set[Stone],
        active_player: Player
    ) -> List[SacrificeMove]:
        """
        Get all legal sacrifice moves.
        A sacrifice is legal if:
        1. The sacrificed stone's removal doesn't disconnect the network
        2. Both placements are legal
        3. After both placements, network remains connected
        """
        sacrifice_moves = []
        player_positions = {s.position for s in stones if s.player == active_player}

        if len(player_positions) < 1:
            return sacrifice_moves  # No stones to sacrifice
        
        # Find safe stones to sacrifice (non-articulation points)
        articulation_points = self.conn_engine.find_articulation_points(stones, active_player)
        safe_sacrifices = player_positions - articulation_points

        # For each safe sacrifice candidate
        for sacrifice_pos in safe_sacrifices:
            # Create temporary state without this stone
            temp_stones = {s for s in stones if s.position != sacrifice_pos}

            # Get legal placements after sacrifice
            first_placements = self._get_legal_placements(temp_stones, active_player)

            for first_move in first_placements:
                first_pos = first_move.position

                # Add first placement temporarily
                temp_stones_2 = temp_stones | {Stone(active_player, first_pos)}

                # Get legal second placements
                second_placements = self._get_legal_placements(temp_stones_2, active_player)

                for second_move in second_placements:
                    second_pos = second_move.position

                    # Verify final state is connected
                    final_stones = temp_stones_2 | {Stone(active_player, second_pos)}
                    if self.conn_engine.is_connected(final_stones, active_player):
                        sacrifice_moves.append(
                            create_sacrifice_move(sacrifice_pos, first_pos, second_pos)
                        )
        return sacrifice_moves
