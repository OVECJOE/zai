"""
Robust test suite for WinDetector class in win_detector.py
"""

from core.hex import Hex, HexGrid
from core.entities.player import Player, Stone
from core.win_detector import WinDetector


def make_stones(positions, player):
    return {Stone(player, Hex(q, r)) for q, r in positions}

def make_stones_mixed(white, red):
    return {Stone(Player.WHITE, Hex(q, r)) for q, r in white} | {Stone(Player.RED, Hex(q, r)) for q, r in red}

class TestWinDetector:
    def setup_method(self):
        self.grid = HexGrid(3)
        self.detector = WinDetector(self.grid)

    def test_no_winner_empty(self):
        stones = set()
        assert self.detector.check_winner(stones, Player.WHITE) is None

    def test_isolation_win(self):
        stones = make_stones([(0,0), (0,1)], Player.WHITE)
        # White is disconnected, Red wins
        assert self.detector.check_winner(stones, Player.WHITE) == Player.RED

    def test_territory_control_white(self):
        void_adj = self.grid.get_void_adjacent_hexes()
        stones = {Stone(Player.WHITE, Hex(h.q, h.r)) for h in void_adj[:5]}
        assert self.detector.check_winner(stones, Player.WHITE) == Player.WHITE

    def test_territory_control_red(self):
        void_adj = self.grid.get_void_adjacent_hexes()
        stones = {Stone(Player.RED, Hex(h.q, h.r)) for h in void_adj[:5]}
        assert self.detector.check_winner(stones, Player.RED) == Player.RED

    def test_encirclement(self):
        # Red surrounds a single white stone
        stones = make_stones([(0,0)], Player.WHITE) | make_stones([(1,0), (1,-1), (0,-1), (-1,0), (-1,1), (0,1)], Player.RED)
        assert self.detector.check_winner(stones, Player.RED) == Player.RED

    def test_no_encirclement(self):
        # White stone not fully surrounded
        stones = make_stones([(0,0)], Player.WHITE) | make_stones([(1,0), (1,-1), (0,-1), (-1,0), (0,1)], Player.RED)
        assert self.detector.check_winner(stones, Player.RED) is None

    def test_network_completion_white(self):
        # White stones on all 6 edges, connected
        edge_hexes = set()
        for i in range(6):
            edge_hexes |= self.grid.edges[i]
        stones = {Stone(Player.WHITE, Hex(h.q, h.r)) for h in list(edge_hexes)[:6]}
        assert self.detector.check_winner(stones, Player.WHITE) == Player.WHITE

    def test_network_completion_red(self):
        edge_hexes = set()
        for i in range(6):
            edge_hexes |= self.grid.edges[i]
        stones = {Stone(Player.RED, Hex(h.q, h.r)) for h in list(edge_hexes)[:6]}
        assert self.detector.check_winner(stones, Player.RED) == Player.RED

    def test_no_network_completion(self):
        stones = make_stones([(0,0), (1,0), (2,0)], Player.WHITE)
        assert self.detector.check_winner(stones, Player.WHITE) is None

    def test_detect_isolation(self):
        stones = make_stones([(0,0), (2,2)], Player.WHITE)
        assert self.detector.detect_isolation(stones) == Player.RED

    def test_detect_territory_control_none(self):
        stones = make_stones_mixed([(1,0), (0,1)], [(0,-1), (-1,0)])
        assert self.detector.detect_territory_control(stones) is None

    def test_detect_encirclement_none(self):
        stones = make_stones_mixed([(0,0)], [(1,0), (0,1)])
        assert self.detector.detect_encirclement(stones, Player.WHITE) is None

    def test_detect_network_completion_none(self):
        stones = make_stones([(0,0), (1,0)], Player.WHITE)
        assert self.detector.detect_network_completion(stones) is None
