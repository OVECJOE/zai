"""
Unit tests for ConnectivityEngine in connectivity.py
"""

import pytest
from zai_engine.hex import Hex, HexGrid
from zai_engine.entities.player import Player, Stone
from zai_engine.connectivity import ConnectivityEngine

class TestConnectivityEngine:
    def setup_method(self):
        self.grid = HexGrid(3)  # Small grid for tests
        self.engine = ConnectivityEngine(self.grid)

    def make_stones(self, positions, player):
        return {Stone(player, Hex(q, r)) for q, r in positions}

    def test_is_connected_true(self):
        stones = self.make_stones([(0,0), (0,1), (1,1)], Player.WHITE)
        assert self.engine.is_connected(stones, Player.WHITE)

    def test_is_connected_false(self):
        stones = self.make_stones([(0,0), (2,2)], Player.WHITE)
        assert not self.engine.is_connected(stones, Player.WHITE)

    def test_is_connected_empty(self):
        stones = set()
        assert self.engine.is_connected(stones, Player.WHITE)

    def test_find_components(self):
        stones = self.make_stones([(0,0), (0,1), (2,2)], Player.WHITE)
        comps = self.engine.find_components(stones)
        assert len(comps[Player.WHITE]) == 2
        sizes = sorted(len(c) for c in comps[Player.WHITE])
        assert sizes == [1,2]

    def test_find_articulation_points_none(self):
        stones = self.make_stones([(0,0), (0,1)], Player.WHITE)
        points = self.engine.find_articulation_points(stones, Player.WHITE)
        assert points == set()

    def test_find_articulation_points_some(self):
        stones = self.make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        points = self.engine.find_articulation_points(stones, Player.WHITE)
        assert Hex(0,1) in points

    def test_find_bridges_none(self):
        stones = self.make_stones([(0,0), (0,1)], Player.WHITE)
        bridges = self.engine.find_bridges(stones, Player.WHITE)
        expected = {(Hex(0,0), Hex(0,1))}
        assert bridges == expected

    def test_find_bridges_some(self):
        stones = self.make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        bridges = self.engine.find_bridges(stones, Player.WHITE)
        assert (Hex(0,1), Hex(0,2)) in bridges or (Hex(0,2), Hex(0,1)) in bridges

    def test_would_disconnect_true(self):
        stones = self.make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        assert self.engine.would_disconnect(stones, Player.WHITE, Hex(0,1))

    def test_would_disconnect_false(self):
        stones = self.make_stones([(0,0), (0,1), (0,2)], Player.WHITE)
        assert not self.engine.would_disconnect(stones, Player.WHITE, Hex(0,0))
