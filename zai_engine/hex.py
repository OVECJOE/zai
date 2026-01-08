"""
Hexagonal coordinate system using axial coordinates.
Provides core geometric operations for hex-based board games.
"""

from dataclasses import dataclass
from typing import List, Set, Tuple, Any

@dataclass(frozen=True)
class Hex:
    """Immutable hexagonal coordinate using axial system (q, r)."""
    q: int
    r: int

    def __hash__(self) -> int:
        return hash((self.q, self.r))
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Hex):
            return False
        return self.q == other.q and self.r == other.r

    def __add__(self, other: 'Hex') -> 'Hex':
        return Hex(self.q + other.q, self.r + other.r)
    
    def __sub__(self, other: 'Hex') -> 'Hex':
        return Hex(self.q - other.q, self.r - other.r)
    
    def __repr__(self) -> str:
        return f"Hex(q={self.q}, r={self.r})"

    def to_cube(self) -> Tuple[int, int, int]:
        """Convert axial to cube coordinates for certain operations."""
        x = self.q
        z = self.r
        y = -x - z
        return (x, y, z)
    
    @staticmethod
    def from_cube(x: int, y: int, z: int) -> 'Hex':
        """Convert cube coordinates back to axial."""
        return Hex(x, z)


class HexGrid:
    """Hexagonal grid operations and utilities."""

    # Six directional offsets for neighbors
    DIRECTIONS = [
        Hex(1, 0), Hex(1, -1), Hex(0, -1),
        Hex(-1, 0), Hex(-1, 1), Hex(0, 1)
    ]

    def __init__(self, radius: int = 3) -> None:
        """
        Initialize hex grid.

        Args:
            radius (int): Distance from center to edge (7x7 board has radius 3)
        """
        self.radius = radius
        self._hexes = self._generate_hexes()
        self._edges = self._compute_edges()

    def _generate_hexes(self) -> Set[Hex]:
        """Generate all hexes within radius."""
        hexes = set()
        for q in range(-self.radius, self.radius + 1):
            r1 = max(-self.radius, -q - self.radius)
            r2 = min(self.radius, -q + self.radius)
            for r in range(r1, r2 + 1):
                hexes.add(Hex(q, r))
        return hexes
    
    def _compute_edges(self) -> List[Set[Hex]]:
        """Compute the 6 edge groups of the board."""
        edges = [set() for _ in range(6)]

        for hex in self._hexes:
            x, y, z = hex.to_cube()

            # Top edge (z == -radius)
            if z == -self.radius:
                edges[0].add(hex)
            # Top-right edge (y == -radius)
            if y == -self.radius:
                edges[1].add(hex)
            # Bottom-right edge (x == radius)
            if x == self.radius:
                edges[2].add(hex)
            # Bottom edge (z == radius)
            if z == self.radius:
                edges[3].add(hex)
            # Bottom-left edge (y == radius)
            if y == self.radius:
                edges[4].add(hex)
            # Top-left edge (x == -radius)
            if x == -self.radius:
                edges[5].add(hex)

        return edges
    
    def get_neighbors(self, hex: Hex) -> List[Hex]:
        """Get all valid neighboring hexes."""
        neighbors = []
        for direction in self.DIRECTIONS:
            neighbor = hex + direction
            if neighbor in self._hexes:
                neighbors.append(neighbor)
        return neighbors
    
    def get_distance(self, a: Hex, b: Hex) -> int:
        """Calculate hex distance between two hexes."""
        x1, y1, z1 = a.to_cube()
        x2, y2, z2 = b.to_cube()
        return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) // 2
    
    def is_edge_hex(self, hex: Hex) -> int:
        """
        Check if hex is on an edge and return edge index.
        Returns -1 if not on any edge.
        """
        for i, edge in enumerate(self._edges):
            if hex in edge:
                return i
        return -1
    
    def get_void_adjacent_hexes(self) -> List[Hex]:
        """Get the 6 hexes adjacent to the center (void stone)."""
        center = Hex(0, 0)
        return self.get_neighbors(center)
    
    @property
    def all_hexes(self) -> Set[Hex]:
        """Return all valid hexes on the board."""
        return self._hexes.copy()
    
    @property
    def edges(self) -> List[Set[Hex]]:
        """Return all edge groups."""
        return [edge.copy() for edge in self._edges]
    
    @property
    def void_stone(self) -> Hex:
        """Return the center hex (void stone position)."""
        return Hex(0, 0)
    
    def touches_edge(self, hexes: Set[Hex], edge_index: int) -> bool:
        """Check if a set of hexes touches a specific edge."""
        return bool(hexes & self._edges[edge_index])
    
    def touches_all_edges(self, hexes: Set[Hex]) -> bool:
        """Check if a set of hexes touches all 6 edges."""
        return all(self.touches_edge(hexes, i) for i in range(6))
