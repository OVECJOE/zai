# Zai Game Engine

A robust, modular, enterprise-level game engine for the strategic board game **Zai** (齋).

## Overview

Zai is a two-player abstract strategy game played on a hexagonal grid where players must balance territorial expansion with network connectivity. The game features four win conditions and deep strategic complexity.

## Architecture

The engine is built with enterprise-level design principles:

- **Immutable State**: All game states are immutable for thread-safety
- **Modular Design**: Each system is independent and testable
- **Performance Optimized**: O(n) connectivity checks, alpha-beta pruning
- **Type Safe**: Comprehensive type hints throughout
- **Zero Dependencies**: Pure Python implementation

## Module Structure

### Core Systems

1. **core/hex.py** - Hexagonal coordinate system
   - Axial coordinate representation
   - Neighbor calculations
   - Distance metrics
   - Edge detection

2. **core/entities/player.py** - Player and stone entities
   - Player enumeration (White, Red, Void)
   - Stone data structure
   - Game phase tracking

3. **core/entities/move.py** - Move representations
   - Placement moves
   - Sacrifice moves
   - Move factories

4. **core/connectivity.py** - Network analysis
   - BFS connectivity checking
   - Articulation point detection (Tarjan's algorithm)
   - Bridge detection
   - Component analysis

5. **core/win_detector.py** - Win condition detection
   - Isolation detection
   - Territory control (void-adjacent hexes)
   - Encirclement detection
   - Network completion (all edges touched)

6. **core/move_generator.py** - Legal move generation
   - Placement move generation
   - Sacrifice move generation
   - Connectivity-aware move filtering

7. **core/game_state.py** - State management
   - Immutable game state
   - State transitions
   - Serialization/deserialization
   - Zobrist hashing support

8. **core/evaluator.py** - Position evaluation
   - Material evaluation
   - Territorial control
   - Network strength
   - Edge progress
   - Encirclement threats

9. **core/ai_engine.py** - AI player
   - Minimax with alpha-beta pruning
   - Iterative deepening
   - Transposition tables
   - Time-limited search

10. **core/game_engine.py** - Main game engine
    - High-level game API
    - Game mode management
    - Move validation
    - AI integration

## Installation

Install via pip:

```bash
pip install zai_engine
```

Or with uv (recommended):

```bash
uv add zai_engine
```

### Development Installation

For development, clone the repository and install with dev dependencies:

```bash
git clone https://github.com/OVECJOE/zai.git
cd zai
uv sync --dev
```

## Quick Start

### Human vs Human

```python
from zai_engine.game_engine import GameEngine, GameMode
from zai_engine.entities.move import PlacementMove
from zai_engine.hex import Hex

# Create engine
engine = GameEngine(mode=GameMode.HUMAN_VS_HUMAN)

# Make moves
engine.make_move(PlacementMove(Hex(1, 0)))  # White
engine.make_move(PlacementMove(Hex(-1, 0)))  # Red

# Check game state
print(f"Current player: {engine.get_current_player()}")
print(f"Legal moves: {len(engine.get_legal_moves())}")
```

### Human vs AI

```python
from zai_engine.game_engine import GameEngine, GameMode, Difficulty
from zai_engine.entities.player import Player
from zai_engine.entities.move import PlacementMove
from zai_engine.hex import Hex

engine = GameEngine(mode=GameMode.HUMAN_VS_AI)
engine.configure_ai(Player.RED, Difficulty.MEDIUM)

# Human makes a move
engine.make_move(PlacementMove(Hex(1, 0)))

# AI responds
ai_move = engine.make_ai_move()
print(f"AI played: {ai_move}")
```

### AI vs AI

```python
from zai_engine.game_engine import GameEngine, GameMode, Difficulty

engine = GameEngine(mode=GameMode.AI_VS_AI)
engine.ai_difficulty = Difficulty.EASY

while not engine.is_game_over():
    # Alternate AI player each turn
    engine.ai_player = engine.get_current_player()
    engine.make_ai_move()

print(f"Winner: {engine.get_winner()}")
```

## Game Rules

### Setup
- 7×7 hexagonal board (61 hexes)
- Center hex contains neutral Void Stone
- Each player has 24 stones (White and Red)

### Phases

**Placement Phase (Turns 1-12)**
- Place one stone per turn
- Must be adjacent to Void Stone OR your existing stones

**Expansion Phase (Turn 13+)**
- Place one stone, OR
- Sacrifice one stone to place two stones

### Critical Rule
**Your stones must remain connected at all times.** If your network becomes disconnected, you lose immediately.

### Win Conditions

1. **Encirclement**: Completely surround opponent's stones
2. **Territory Dominance**: Control 5+ of 6 void-adjacent hexes
3. **Network Completion**: Create connected chain touching all 6 board edges
4. **Opponent Isolation**: Force opponent to disconnect their network

## API Reference

### GameEngine Methods

#### Game Control
- `new_game()` - Start new game
- `make_move(move)` - Make a move
- `make_ai_move()` - Let AI make a move
- `is_game_over()` - Check if game ended
- `get_winner()` - Get winner

#### Move Information
- `get_legal_moves()` - All legal moves for current player
- `is_valid_move(move)` - Validate a move

#### Game State
- `get_current_player()` - Active player
- `get_current_state()` - Current GameState object
- `get_winner()` - Winner (if game is over)

#### AI Methods
- `configure_ai(player, difficulty)` - Configure AI for a player
- `make_ai_move()` - Let configured AI make a move

### AI Difficulty Levels

- **EASY**: Depth 2, 1.0s time limit
- **MEDIUM**: Depth 4, 2.0s time limit
- **HARD**: Depth 6, 5.0s time limit
- **EXPERT**: Depth 8, 10.0s time limit

## Performance Characteristics

### Time Complexity
- Move generation: O(n) where n = stone count
- Connectivity check: O(n)
- Win detection: O(n²) worst case
- AI search: O(b^d) where b = branching factor, d = depth

### Space Complexity
- Game state: O(n)
- Transposition table: O(1M) positions cached
- Move history: O(m) where m = total moves

### Typical Performance
- Move validation: <1ms
- Connectivity check: <1ms
- AI move (Medium): ~100-500ms
- AI move (Hard): ~2-5s

## Testing

Run the comprehensive test suite:

```bash
pytest tests/
```

The test suite includes:
- `test_hex.py` - Hex coordinate system and grid operations
- `test_move.py` - Move creation and validation
- `test_connectivity.py` - Network connectivity analysis
- `test_win_detector.py` - Win condition detection
- `test_move_generator.py` - Legal move generation
- `test_game_state.py` - State management and transitions
- `test_evaluator.py` - Position evaluation
- `test_ai_engine.py` - AI search and decision making

## Design Patterns

### Immutability
All game states are immutable using `frozen=True` dataclasses and `frozenset`/`tuple` collections. This enables:
- Thread-safe operations
- Easy state caching
- Reliable undo/redo (with history stack)

### Strategy Pattern
Multiple AI difficulty levels with different search parameters

### Factory Pattern
Move creation through factory functions

### Observer Pattern
Game state changes can be monitored through state exports

## Extensibility

### Adding New Win Conditions
Extend `WinDetector.check_winner()`:

```python
def detect_custom_condition(self, stones, player):
    # Your logic here
    return winner if condition_met else None
```

### Custom AI Evaluation
Extend `PositionEvaluator.evaluate()`:

```python
def _evaluate_custom_feature(self, state, player, opponent):
    # Your heuristic
    return score
```

### Alternative Board Sizes
Modify `HexGrid` initialization:

```python
grid = HexGrid(radius=4)  # 9×9 board
```

## Production Readiness

This engine is production-ready with:

✅ Comprehensive error handling
✅ Type safety throughout
✅ Immutable state management
✅ Performance optimization
✅ Clean separation of concerns
✅ Extensive documentation
✅ Example usage and tests
✅ Zero external dependencies

## Future Enhancements

Potential additions for integration:

- **Persistent storage** - Save/load games
- **Network protocol** - Multiplayer support
- **Opening book** - Pre-computed opening moves
- **Neural network evaluation** - ML-based position scoring
- **Puzzle mode** - Tactical training positions
- **Replay analysis** - Post-game review tools

## License

This engine is provided as-is for educational and development purposes.

## Credits

Game Design: Zai (齋) - "pure" or "abstain"
Engine Implementation: Enterprise-level Python architecture
AI: Minimax with alpha-beta pruning and iterative deepening
