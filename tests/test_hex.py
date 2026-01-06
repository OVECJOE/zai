"""
Comprehensive test suite for Hex and HexGrid classes.
"""

import pytest
from core.hex import Hex, HexGrid


# =============================================================================
# Hex Class Tests
# =============================================================================

class TestHexCreation:
    """Tests for Hex instantiation and immutability."""

    def test_create_hex_with_positive_coords(self):
        h = Hex(1, 2)
        assert h.q == 1
        assert h.r == 2

    def test_create_hex_with_negative_coords(self):
        h = Hex(-3, -4)
        assert h.q == -3
        assert h.r == -4

    def test_create_hex_at_origin(self):
        h = Hex(0, 0)
        assert h.q == 0
        assert h.r == 0


class TestHexEquality:
    """Tests for Hex equality and hashing."""

    def test_equal_hexes(self):
        h1 = Hex(1, 2)
        h2 = Hex(1, 2)
        assert h1 == h2

    def test_unequal_hexes_different_q(self):
        h1 = Hex(1, 2)
        h2 = Hex(3, 2)
        assert h1 != h2

    def test_unequal_hexes_different_r(self):
        h1 = Hex(1, 2)
        h2 = Hex(1, 5)
        assert h1 != h2

    def test_hex_not_equal_to_non_hex(self):
        h = Hex(1, 2)
        assert h != (1, 2)
        assert h != [1, 2]
        assert h != "Hex(1, 2)"
        assert h != None
        assert h != 42

    def test_hex_hash_consistency(self):
        h1 = Hex(1, 2)
        h2 = Hex(1, 2)
        assert hash(h1) == hash(h2)

    def test_hex_usable_in_set(self):
        s = {Hex(1, 2), Hex(1, 2), Hex(3, 4)}
        assert len(s) == 2

    def test_hex_usable_as_dict_key(self):
        d = {Hex(1, 2): "a", Hex(3, 4): "b"}
        assert d[Hex(1, 2)] == "a"
        assert d[Hex(3, 4)] == "b"


class TestHexArithmetic:
    """Tests for Hex addition and subtraction."""

    def test_add_two_hexes(self):
        h1 = Hex(1, 2)
        h2 = Hex(3, 4)
        result = h1 + h2
        assert result == Hex(4, 6)

    def test_add_hex_with_origin(self):
        h = Hex(5, -3)
        origin = Hex(0, 0)
        assert h + origin == h

    def test_add_hex_with_negative(self):
        h1 = Hex(1, 2)
        h2 = Hex(-1, -2)
        assert h1 + h2 == Hex(0, 0)

    def test_subtract_two_hexes(self):
        h1 = Hex(5, 7)
        h2 = Hex(2, 3)
        result = h1 - h2
        assert result == Hex(3, 4)

    def test_subtract_hex_from_itself(self):
        h = Hex(3, 4)
        assert h - h == Hex(0, 0)

    def test_subtract_results_in_negative(self):
        h1 = Hex(1, 1)
        h2 = Hex(5, 3)
        assert h1 - h2 == Hex(-4, -2)

    def test_addition_is_commutative(self):
        h1 = Hex(1, 2)
        h2 = Hex(3, 4)
        assert h1 + h2 == h2 + h1

    def test_addition_is_associative(self):
        h1 = Hex(1, 2)
        h2 = Hex(3, 4)
        h3 = Hex(5, 6)
        assert (h1 + h2) + h3 == h1 + (h2 + h3)


class TestHexRepresentation:
    """Tests for Hex string representation."""

    def test_repr_positive_coords(self):
        h = Hex(1, 2)
        assert repr(h) == "Hex(q=1, r=2)"

    def test_repr_negative_coords(self):
        h = Hex(-3, -4)
        assert repr(h) == "Hex(q=-3, r=-4)"

    def test_repr_origin(self):
        h = Hex(0, 0)
        assert repr(h) == "Hex(q=0, r=0)"


class TestHexCubeConversion:
    """Tests for axial to cube coordinate conversion."""

    def test_to_cube_origin(self):
        h = Hex(0, 0)
        x, y, z = h.to_cube()
        assert (x, y, z) == (0, 0, 0)

    def test_to_cube_positive_q(self):
        h = Hex(2, 0)
        x, y, z = h.to_cube()
        assert (x, y, z) == (2, -2, 0)

    def test_to_cube_positive_r(self):
        h = Hex(0, 2)
        x, y, z = h.to_cube()
        assert (x, y, z) == (0, -2, 2)

    def test_to_cube_mixed_coords(self):
        h = Hex(1, -2)
        x, y, z = h.to_cube()
        assert (x, y, z) == (1, 1, -2)

    def test_cube_coords_sum_to_zero(self):
        """Cube coordinates must always sum to zero."""
        test_cases = [Hex(0, 0), Hex(1, 2), Hex(-3, 5), Hex(2, -2)]
        for h in test_cases:
            x, y, z = h.to_cube()
            assert x + y + z == 0, f"Failed for {h}"

    def test_from_cube_origin(self):
        h = Hex.from_cube(0, 0, 0)
        assert h == Hex(0, 0)

    def test_from_cube_positive_x(self):
        h = Hex.from_cube(2, -2, 0)
        assert h == Hex(2, 0)

    def test_from_cube_roundtrip(self):
        """Converting to cube and back should yield the same hex."""
        original = Hex(3, -1)
        x, y, z = original.to_cube()
        restored = Hex.from_cube(x, y, z)
        assert restored == original

    @pytest.mark.parametrize("q,r", [
        (0, 0), (1, 0), (0, 1), (-1, 0), (0, -1),
        (2, -1), (-2, 3), (3, 3), (-3, -3)
    ])
    def test_cube_roundtrip_parametrized(self, q, r):
        original = Hex(q, r)
        x, y, z = original.to_cube()
        restored = Hex.from_cube(x, y, z)
        assert restored == original


# =============================================================================
# HexGrid Class Tests
# =============================================================================

class TestHexGridCreation:
    """Tests for HexGrid initialization."""

    def test_default_radius(self):
        grid = HexGrid()
        assert grid.radius == 3

    def test_custom_radius(self):
        grid = HexGrid(radius=5)
        assert grid.radius == 5

    def test_radius_zero(self):
        grid = HexGrid(radius=0)
        assert grid.radius == 0
        assert len(grid.all_hexes) == 1
        assert Hex(0, 0) in grid.all_hexes

    def test_radius_one(self):
        grid = HexGrid(radius=1)
        assert len(grid.all_hexes) == 7  # 1 center + 6 neighbors


class TestHexGridHexGeneration:
    """Tests for hex generation within the grid."""

    def test_all_hexes_returns_copy(self):
        grid = HexGrid(radius=2)
        hexes1 = grid.all_hexes
        hexes2 = grid.all_hexes
        assert hexes1 is not hexes2
        assert hexes1 == hexes2

    def test_center_hex_always_exists(self):
        for r in range(5):
            grid = HexGrid(radius=r)
            assert Hex(0, 0) in grid.all_hexes

    def test_hex_count_formula(self):
        """Hex count should be 3*r^2 + 3*r + 1 for radius r."""
        for r in range(6):
            grid = HexGrid(radius=r)
            expected = 3 * r * r + 3 * r + 1
            assert len(grid.all_hexes) == expected

    def test_hexes_within_radius(self):
        """All generated hexes should be within the specified radius."""
        grid = HexGrid(radius=3)
        for h in grid.all_hexes:
            distance = grid.get_distance(Hex(0, 0), h)
            assert distance <= 3

    def test_no_hexes_outside_radius(self):
        """Edge hexes should be exactly at radius distance."""
        grid = HexGrid(radius=3)
        # Check some specific edge hexes
        assert Hex(3, 0) in grid.all_hexes
        assert Hex(0, 3) in grid.all_hexes
        assert Hex(-3, 0) in grid.all_hexes
        # Check one outside radius
        assert Hex(4, 0) not in grid.all_hexes


class TestHexGridNeighbors:
    """Tests for neighbor computation."""

    def test_center_has_six_neighbors(self):
        grid = HexGrid(radius=3)
        neighbors = grid.get_neighbors(Hex(0, 0))
        assert len(neighbors) == 6

    def test_edge_hex_has_fewer_neighbors(self):
        grid = HexGrid(radius=3)
        neighbors = grid.get_neighbors(Hex(3, 0))
        assert len(neighbors) < 6

    def test_corner_hex_has_three_neighbors(self):
        grid = HexGrid(radius=3)
        # Corner hex at q=3, r=-3
        neighbors = grid.get_neighbors(Hex(3, -3))
        assert len(neighbors) == 3

    def test_neighbors_are_adjacent(self):
        grid = HexGrid(radius=3)
        center = Hex(0, 0)
        neighbors = grid.get_neighbors(center)
        for n in neighbors:
            assert grid.get_distance(center, n) == 1

    def test_neighbors_are_valid_hexes(self):
        grid = HexGrid(radius=3)
        for h in grid.all_hexes:
            for n in grid.get_neighbors(h):
                assert n in grid.all_hexes

    def test_neighbor_relationship_is_symmetric(self):
        grid = HexGrid(radius=3)
        h = Hex(1, 1)
        neighbors = grid.get_neighbors(h)
        for n in neighbors:
            assert h in grid.get_neighbors(n)


class TestHexGridDistance:
    """Tests for hex distance calculation."""

    def test_distance_to_self_is_zero(self):
        grid = HexGrid(radius=3)
        h = Hex(1, 2)
        assert grid.get_distance(h, h) == 0

    def test_distance_to_neighbor_is_one(self):
        grid = HexGrid(radius=3)
        center = Hex(0, 0)
        for direction in HexGrid.DIRECTIONS:
            neighbor = center + direction
            assert grid.get_distance(center, neighbor) == 1

    def test_distance_is_symmetric(self):
        grid = HexGrid(radius=3)
        h1 = Hex(1, 2)
        h2 = Hex(-2, 3)
        assert grid.get_distance(h1, h2) == grid.get_distance(h2, h1)

    def test_distance_across_grid(self):
        grid = HexGrid(radius=3)
        h1 = Hex(3, 0)
        h2 = Hex(-3, 0)
        assert grid.get_distance(h1, h2) == 6

    def test_distance_diagonal(self):
        grid = HexGrid(radius=3)
        h1 = Hex(0, 0)
        h2 = Hex(2, 1)
        assert grid.get_distance(h1, h2) == 3

    @pytest.mark.parametrize("h1,h2,expected", [
        (Hex(0, 0), Hex(0, 0), 0),
        (Hex(0, 0), Hex(1, 0), 1),
        (Hex(0, 0), Hex(2, 0), 2),
        (Hex(0, 0), Hex(0, 3), 3),
        (Hex(1, 1), Hex(-1, -1), 4),
    ])
    def test_distance_parametrized(self, h1, h2, expected):
        grid = HexGrid(radius=5)
        assert grid.get_distance(h1, h2) == expected


class TestHexGridEdges:
    """Tests for edge detection and computation."""

    def test_six_edge_groups(self):
        grid = HexGrid(radius=3)
        assert len(grid.edges) == 6

    def test_edges_returns_copies(self):
        grid = HexGrid(radius=3)
        edges1 = grid.edges
        edges2 = grid.edges
        assert edges1 is not edges2
        for i in range(6):
            assert edges1[i] is not edges2[i]

    def test_edge_hexes_at_boundary(self):
        grid = HexGrid(radius=3)
        for edge in grid.edges:
            for h in edge:
                # Each edge hex should be at distance radius from center
                assert grid.get_distance(Hex(0, 0), h) == 3

    def test_is_edge_hex_returns_correct_index(self):
        grid = HexGrid(radius=3)
        # Hex at (0, -3) should be on the top edge (index 0)
        assert grid.is_edge_hex(Hex(0, -3)) == 0

    def test_is_edge_hex_returns_minus_one_for_center(self):
        grid = HexGrid(radius=3)
        assert grid.is_edge_hex(Hex(0, 0)) == -1

    def test_is_edge_hex_returns_minus_one_for_interior(self):
        grid = HexGrid(radius=3)
        assert grid.is_edge_hex(Hex(1, 0)) == -1
        assert grid.is_edge_hex(Hex(0, 1)) == -1

    def test_corner_hexes_on_two_edges(self):
        """Corner hexes should appear in exactly two edge groups."""
        grid = HexGrid(radius=3)
        corner = Hex(3, -3)  # A corner hex
        count = sum(1 for edge in grid.edges if corner in edge)
        assert count == 2

    def test_all_edges_nonempty(self):
        grid = HexGrid(radius=3)
        for edge in grid.edges:
            assert len(edge) > 0


class TestHexGridVoidStone:
    """Tests for void stone (center) operations."""

    def test_void_stone_is_center(self):
        grid = HexGrid(radius=3)
        assert grid.void_stone == Hex(0, 0)

    def test_void_adjacent_hexes_count(self):
        grid = HexGrid(radius=3)
        adjacent = grid.get_void_adjacent_hexes()
        assert len(adjacent) == 6

    def test_void_adjacent_hexes_are_neighbors(self):
        grid = HexGrid(radius=3)
        center = grid.void_stone
        adjacent = grid.get_void_adjacent_hexes()
        for h in adjacent:
            assert grid.get_distance(center, h) == 1


class TestHexGridTouchesEdge:
    """Tests for edge touching detection."""

    def test_single_edge_hex_touches_edge(self):
        grid = HexGrid(radius=3)
        hexes = {Hex(0, -3)}  # Top edge
        assert grid.touches_edge(hexes, 0) is True

    def test_interior_hex_does_not_touch_edge(self):
        grid = HexGrid(radius=3)
        hexes = {Hex(0, 0)}
        for i in range(6):
            assert grid.touches_edge(hexes, i) is False

    def test_empty_set_does_not_touch_edge(self):
        grid = HexGrid(radius=3)
        hexes = set()
        for i in range(6):
            assert grid.touches_edge(hexes, i) is False

    def test_touches_all_edges_with_spanning_set(self):
        grid = HexGrid(radius=3)
        # Create a set that touches all edges
        hexes = set()
        for edge in grid.edges:
            hexes.add(next(iter(edge)))  # Add one hex from each edge
        assert grid.touches_all_edges(hexes) is True

    def test_touches_all_edges_false_for_partial(self):
        grid = HexGrid(radius=3)
        # Only touching 5 edges, avoid corners (hexes that appear in more than one edge)
        hexes = set()
        for i in range(5):
            for h in grid.edges[i]:
                count = sum(1 for edge in grid.edges if h in edge)
                if count == 1:
                    hexes.add(h)
                    break
        assert grid.touches_all_edges(hexes) is False

    def test_touches_all_edges_false_for_empty(self):
        grid = HexGrid(radius=3)
        assert grid.touches_all_edges(set()) is False


class TestHexGridDirections:
    """Tests for the DIRECTIONS constant."""

    def test_six_directions(self):
        assert len(HexGrid.DIRECTIONS) == 6

    def test_directions_are_hex_objects(self):
        for d in HexGrid.DIRECTIONS:
            assert isinstance(d, Hex)

    def test_directions_unique(self):
        directions_set = set(HexGrid.DIRECTIONS)
        assert len(directions_set) == 6

    def test_directions_are_unit_distance(self):
        grid = HexGrid(radius=1)
        origin = Hex(0, 0)
        for d in HexGrid.DIRECTIONS:
            assert grid.get_distance(origin, d) == 1

    def test_opposite_directions_cancel(self):
        """Opposite directions should sum to zero."""
        # Directions are paired: 0-3, 1-4, 2-5
        assert HexGrid.DIRECTIONS[0] + HexGrid.DIRECTIONS[3] == Hex(0, 0)
        assert HexGrid.DIRECTIONS[1] + HexGrid.DIRECTIONS[4] == Hex(0, 0)
        assert HexGrid.DIRECTIONS[2] + HexGrid.DIRECTIONS[5] == Hex(0, 0)


# =============================================================================
# Integration Tests
# =============================================================================

class TestHexGridIntegration:
    """Integration tests combining multiple features."""

    def test_walking_from_center_to_edge(self):
        """Walking in any direction from center should reach edge."""
        grid = HexGrid(radius=3)
        center = Hex(0, 0)
        
        for direction in HexGrid.DIRECTIONS:
            current = center
            for step in range(3):
                current = current + direction
            assert current in grid.all_hexes
            assert grid.is_edge_hex(current) != -1

    def test_path_connectivity(self):
        """Any two hexes should be reachable via neighbors."""
        grid = HexGrid(radius=2)
        start = Hex(2, 0)
        end = Hex(-2, 0)
        
        # Simple BFS to verify connectivity
        visited = {start}
        frontier = [start]
        while frontier:
            current = frontier.pop(0)
            if current == end:
                break
            for neighbor in grid.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    frontier.append(neighbor)
        
        assert end in visited

    def test_large_grid_performance(self):
        """Ensure large grids can be created without issues."""
        grid = HexGrid(radius=10)
        expected_hexes = 3 * 10 * 10 + 3 * 10 + 1  # 331 hexes
        assert len(grid.all_hexes) == expected_hexes

    def test_distance_triangle_inequality(self):
        """Distance should satisfy triangle inequality."""
        grid = HexGrid(radius=3)
        hexes = list(grid.all_hexes)[:10]  # Sample 10 hexes
        
        for a in hexes:
            for b in hexes:
                for c in hexes:
                    dist_ab = grid.get_distance(a, b)
                    dist_bc = grid.get_distance(b, c)
                    dist_ac = grid.get_distance(a, c)
                    assert dist_ac <= dist_ab + dist_bc
