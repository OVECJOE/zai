"""
Test suite for Move, PlacementMove, SacrificeMove, and their factories.
"""

from core.entities.move import Move, PlacementMove, SacrificeMove, create_placement_move, create_sacrifice_move
from core.hex import Hex

class TestMoveBase:
    def test_move_repr(self):
        m = Move()
        assert repr(m) == "Move()"

class TestPlacementMove:
    def test_placement_move_fields(self):
        h = Hex(1, 2)
        m = PlacementMove(h)
        assert m.position == h

    def test_placement_move_repr(self):
        h = Hex(1, -1)
        m = PlacementMove(h)
        assert repr(m) == f"PlacementMove({h})"

    def test_create_placement_move_factory(self):
        h = Hex(0, 0)
        m = create_placement_move(h)
        assert isinstance(m, PlacementMove)
        assert m.position == h

class TestSacrificeMove:
    def test_sacrifice_move_fields(self):
        s = Hex(0, 0)
        p1 = Hex(1, 0)
        p2 = Hex(0, 1)
        m = SacrificeMove(s, (p1, p2))
        assert m.sacrifice_position == s
        assert m.placement_positions == (p1, p2)

    def test_sacrifice_move_repr(self):
        s = Hex(-1, 2)
        p1 = Hex(0, 0)
        p2 = Hex(1, -1)
        m = SacrificeMove(s, (p1, p2))
        assert repr(m) == f"SacrificeMove(sacrifice={s}, placements={(p1, p2)})"

    def test_sacrifice_move_properties(self):
        s = Hex(0, 0)
        p1 = Hex(1, 0)
        p2 = Hex(0, 1)
        m = SacrificeMove(s, (p1, p2))
        assert m.first_placement == p1
        assert m.second_placement == p2

    def test_create_sacrifice_move_factory(self):
        s = Hex(0, 0)
        p1 = Hex(1, 0)
        p2 = Hex(0, 1)
        m = create_sacrifice_move(s, p1, p2)
        assert isinstance(m, SacrificeMove)
        assert m.sacrifice_position == s
        assert m.placement_positions == (p1, p2)
