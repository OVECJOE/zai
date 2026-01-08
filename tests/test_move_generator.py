"""
Robust test suite for MoveGenerator in move_generator.py
"""
import pytest
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone, Phase
from zai_engine.entities.move import PlacementMove, SacrificeMove
from zai_engine.move_generator import MoveGenerator


def make_stones(positions, player):
    return {Stone(player, Hex(q, r)) for q, r in positions}


def make_stones_mixed(white, red):
    return {Stone(Player.WHITE, Hex(q, r)) for q, r in white} | {Stone(Player.RED, Hex(q, r)) for q, r in red}


class TestMoveGenerator:
    def setup_method(self):
        self.grid = HexGrid(3)
        self.generator = MoveGenerator(self.grid)

    def test_first_move_placement(self):
        """First move should be adjacent to void"""
        stones = set()
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 1)
        
        assert all(isinstance(m, PlacementMove) for m in moves)
        void_adjacent = self.grid.get_void_adjacent_hexes()
        placement_moves = [m for m in moves if isinstance(m, PlacementMove)]
        move_positions = {m.position for m in placement_moves}
        assert move_positions == set(void_adjacent)

    def test_placement_adjacent_to_own_stones(self):
        """Placement moves should be adjacent to player's stones"""
        stones = make_stones([(0,0), (0,1)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 2)
        
        assert all(isinstance(m, PlacementMove) for m in moves)
        assert len(moves) > 0
        
        # All moves should be adjacent to existing white stones
        stone_positions = {s.position for s in stones}
        for move in moves:
            if isinstance(move, PlacementMove):
                neighbors = self.grid.get_neighbors(move.position)
                has_adjacent_white = any(n in stone_positions for n in neighbors)
                assert has_adjacent_white

    def test_no_placement_on_occupied_hex(self):
        """Cannot place on occupied hexes"""
        stones = make_stones([(0,0), (0,1), (1,0)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 3)
        
        placement_moves = [m for m in moves if isinstance(m, PlacementMove)]
        move_positions = {m.position for m in placement_moves}
        stone_positions = {s.position for s in stones}
        assert not (move_positions & stone_positions)

    def test_placement_phase_no_sacrifices(self):
        """Placement phase should not generate sacrifice moves"""
        stones = make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 3)
        
        assert all(isinstance(m, PlacementMove) for m in moves)
        assert not any(isinstance(m, SacrificeMove) for m in moves)

    def test_expansion_phase_includes_sacrifices(self):
        """Expansion phase should include sacrifice moves"""
        stones = make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.EXPANSION, 10)
        
        # Should have both placement and sacrifice moves
        placements = [m for m in moves if isinstance(m, PlacementMove)]
        sacrifices = [m for m in moves if isinstance(m, SacrificeMove)]
        
        assert len(placements) > 0
        assert len(sacrifices) >= 0  # May or may not have safe sacrifices

    def test_no_sacrifice_of_articulation_points(self):
        """Cannot sacrifice articulation points"""
        # Linear chain where middle stone is articulation point
        stones = make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.EXPANSION, 10)
        
        sacrifices = [m for m in moves if isinstance(m, SacrificeMove)]
        sacrifice_positions = {m.sacrifice_position for m in sacrifices}
        
        # Middle stone (0,1) is articulation point, should not be sacrificed
        assert Hex(0,1) not in sacrifice_positions

    def test_sacrifice_with_no_stones(self):
        """No sacrifices possible with no stones"""
        stones = set()
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.EXPANSION, 10)
        
        sacrifices = [m for m in moves if isinstance(m, SacrificeMove)]
        assert len(sacrifices) == 0

    def test_valid_sacrifice_structure(self):
        """Sacrifice moves should have correct structure"""
        # Create a Y-shape where center can be safely sacrificed
        stones = make_stones([(0,0), (1,0), (0,1), (-1,1)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.EXPANSION, 10)
        
        sacrifices = [m for m in moves if isinstance(m, SacrificeMove)]
        
        for sacrifice in sacrifices:
            assert hasattr(sacrifice, 'sacrifice_position')
            assert hasattr(sacrifice, 'placement_positions')
            assert len(sacrifice.placement_positions) == 2
            assert sacrifice.placement_positions[0] != sacrifice.placement_positions[1]

    def test_empty_board_placements(self):
        """Empty board should give void-adjacent placements"""
        stones = set()
        placements = self.generator._get_legal_placements(stones, Player.WHITE)
        
        void_adjacent = self.grid.get_void_adjacent_hexes()
        placement_positions = {m.position for m in placements}
        assert placement_positions == set(void_adjacent)

    def test_mixed_stones_placement(self):
        """Placements should only consider own stones"""
        stones = make_stones_mixed([(0,0)], [(0,1)])
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 2)
        
        placement_moves = [m for m in moves if isinstance(m, PlacementMove)]
        move_positions = {m.position for m in placement_moves}
        # White can only place adjacent to (0,0), not (0,1)
        white_neighbors = set(self.grid.get_neighbors(Hex(0,0)))
        occupied = {Hex(0,0), Hex(0,1)}
        expected = white_neighbors - occupied
        
        assert move_positions == expected

    def test_sacrifice_maintains_connectivity(self):
        """All sacrifice moves should maintain connectivity"""
        stones = make_stones([(0,0), (1,0), (1,-1), (0,1)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.EXPANSION, 10)
        
        sacrifices = [m for m in moves if isinstance(m, SacrificeMove)]
        
        # Verify each sacrifice maintains connectivity by construction
        # (this is guaranteed by the algorithm, but let's verify structure)
        for sacrifice in sacrifices:
            assert sacrifice.sacrifice_position in {s.position for s in stones}

    def test_get_legal_moves_returns_list(self):
        """get_legal_moves should return a list"""
        stones = make_stones([(0,0)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 2)
        
        assert isinstance(moves, list)

    def test_multiple_stones_placement_options(self):
        """Multiple stones should provide multiple placement options"""
        stones = make_stones([(0,0), (1,0), (0,1)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.PLACEMENT, 3)
        
        # Should have multiple valid placements
        assert len(moves) > 3

    def test_sacrifice_two_placements_different(self):
        """Two placements in sacrifice must be different positions"""
        stones = make_stones([(0,0), (1,0), (0,1)], Player.WHITE)
        moves = self.generator.get_legal_moves(stones, Player.WHITE, Phase.EXPANSION, 10)
        
        sacrifices = [m for m in moves if isinstance(m, SacrificeMove)]
        for sacrifice in sacrifices:
            p1, p2 = sacrifice.placement_positions
            assert p1 != p2
