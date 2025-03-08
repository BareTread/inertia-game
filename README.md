# Inertia Deluxe

A physics-based puzzle game where you control a ball using inertia to hit targets and complete levels.

## Game Features

- Physics-based ball movement with inertia
- Multiple level types with increasing difficulty
- Various game elements:
  - Walls for collision
  - Targets to hit
  - Power-ups for special abilities
  - Surfaces with different friction properties
  - Teleporters for instant movement
  - Gravity wells that attract or repel the ball
  - Bounce pads for redirecting the ball
- Energy management system
- Star rating system for level completion
- Level progression and unlocking
- Settings for customizing the game experience

## Controls

- Arrow keys or WASD to apply force to the ball
- Space to brake
- Escape to pause the game
- Mouse to interact with UI elements

## Architecture

The game has been refactored to use a modular architecture with manager classes:

### Manager Classes

- **StateManager**: Handles game states and transitions between them
- **LevelManager**: Manages level loading, setup, and completion
- **CollisionManager**: Handles collision detection and response
- **UIManager**: Manages UI elements and user interaction

### Utility Classes

- **Camera**: Follows the ball with smooth motion
- **ParticleSystem**: Creates visual effects for collisions and events
- **ScreenShake**: Adds screen shake effects for impacts
- **Toast**: Displays temporary notifications

### Entity Classes

- **EnhancedBall**: The player-controlled ball with physics
- **EnhancedWall**: Walls for collision
- **EnhancedTarget**: Targets to hit for level completion
- **EnhancedPowerUp**: Power-ups for special abilities
- **Surface**: Areas with different friction properties
- **Teleporter**: Instantly moves the ball to another location
- **GravityWell**: Attracts or repels the ball
- **BouncePad**: Redirects the ball's movement

## Refactoring

The codebase has been refactored to improve:

1. **Modularity**: Separated concerns into manager classes
2. **Maintainability**: Reduced code duplication and improved organization
3. **Extensibility**: Made it easier to add new features and levels
4. **Readability**: Improved code structure and documentation

## Data Structure

The game uses JSON files for data storage:

- **levels.json**: Stores level data, completion status, and stars
- **settings.json**: Stores game settings
- **high_score.json**: Stores high scores

## Future Improvements

- Add more levels with unique challenges
- Implement additional power-ups and game elements
- Add sound effects and music
- Create a level editor for custom levels
- Add achievements and leaderboards

## Game Overview

In Inertia Deluxe, you control a ball by applying directional forces. Your goal is to navigate through obstacles, collect targets, and reach the exit within the time limit. The game features multiple levels with increasing difficulty, power-ups, and a star rating system.

## Features

- Physics-based ball movement with momentum and inertia
- Multiple levels with increasing difficulty
- Power-ups (energy boost, speed boost, time extension)
- Star rating system based on completion time
- Level progression and unlocking system
- Settings for sound, music, particles, and screen shake
- Pause functionality and level restart options
- Visual feedback with particle effects

## Controls

- **Arrow Keys**: Apply force to the ball in the corresponding direction
- **Space**: Pause the game
- **R**: Restart the current level
- **Esc**: Return to the main menu / Exit game

## Installation

### Prerequisites

- Python 3.6 or higher
- Pygame 2.0.0 or higher

### Setup

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Run the game:

```bash
python main.py
```

## Project Structure

```
inertia-deluxe/
├── assets/             # Game assets
│   ├── fonts/          # Font files
│   ├── images/         # Images and sprites
│   ├── levels/         # Level data files
│   └── sounds/         # Sound effects and music
├── data/               # Game data
│   ├── levels.json     # Level configuration
│   ├── settings.json   # User settings
│   └── highscores.json # Player progress
├── entities/           # Game entity classes
├── ui/                 # User interface components
├── utils/              # Utility modules
├── game.py             # Main game class
├── main.py             # Entry point
├── README.md           # This file
└── requirements.txt    # Dependencies
```

For detailed information about the project structure and development guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

## Development

The game is built using:

- **Python** - Primary programming language
- **Pygame** - Game development library for Python
- **JSON** - For storing level and game data

## License

This project is open source and available under the MIT License.

## Credits

- Developed as a Python learning project
- Inspired by classic physics-based puzzle games
