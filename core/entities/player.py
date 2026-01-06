"""
Player and Stone data structures.
Defines the core game entities.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Any
from core.hex import Hex


class Player(Enum):
    """Player enumeration."""
    WHITE = 'white'
    RED = 'red'
    VOID = 'void'

    def opponent(self) -> 'Player':
        """Get the opposing player."""
        if self == Player.WHITE:
            return Player.RED
        elif self == Player.RED:
            return Player.WHITE
        return Player.VOID

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Stone:
    """Immutable stone placement."""
    player: Player
    position: Hex

    def __hash__(self) -> int:
        return hash((self.player, self.position))
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Stone):
            return False
        return self.player == other.player and self.position == other.position
    
    def __repr__(self) -> str:
        return f"Stone({self.player.value}, {self.position})"


class Phase(Enum):
    """Game phase enumeration."""
    PLACEMENT = 'placement'
    EXPANSION = 'expansion'

    def __str__(self) -> str:
        return self.value
