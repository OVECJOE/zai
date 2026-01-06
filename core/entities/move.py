"""
Move representation and move types.
Supports placement moves and sacrifice moves.
"""

from dataclasses import dataclass
from typing import Tuple
from core.hex import Hex


@dataclass(frozen=True)
class Move:
    """
    Base move class.
    All moves are immutable for thread-safety and caching.
    """

    def __repr__(self) -> str:
        return "Move()"


@dataclass(frozen=True)
class PlacementMove(Move):
    """Single ston placement move."""
    position: Hex

    def __repr__(self) -> str:
        return f"PlacementMove({self.position})"


@dataclass(frozen=True)
class SacrificeMove(Move):
    """
    Sacrifice move: remove one stone and place two stones.
    """
    sacrifice_position: Hex
    placement_positions: Tuple[Hex, Hex] # Tuple for immutability

    def __repr__(self) -> str:
        return f"SacrificeMove(sacrifice={self.sacrifice_position}, placements={self.placement_positions})"
    
    @property
    def first_placement(self) -> Hex:
        return self.placement_positions[0]
    
    @property
    def second_placement(self) -> Hex:
        return self.placement_positions[1]


def create_placement_move(position: Hex) -> PlacementMove:
    """Factory function for placement moves."""
    return PlacementMove(position)


def create_sacrifice_move(
    sacrifice_position: Hex,
    first_placement: Hex,
    second_placement: Hex
) -> SacrificeMove:
    """Factory function for sacrifice moves."""
    return SacrificeMove(
        sacrifice_position,
        (first_placement, second_placement)
    )
