# Inertia Deluxe

A physics-based puzzle game built with Python and Pygame where you control a ball using directional forces.

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
