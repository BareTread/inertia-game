# Quantum Drift

A time-bending puzzle-strategy game where you control a quantum particle that exists in multiple timelines simultaneously.

## Game Concept

In Quantum Drift, every move you make creates a temporal "echo" that repeats your action after a set number of turns. You must use these echoes strategically to solve puzzles and complete levels.

## How to Play

1. Use arrow keys to move your quantum particle
2. Each move creates an echo that will repeat that exact move after N turns
3. Press Q, W, E, R to change your quantum state (each state has different properties)
4. Press Z to slow down echoes, X to speed them up
5. Complete objectives by activating switches, avoiding hazards, and reaching the goal

## Installation

1. Ensure you have Python 3.6+ installed
2. Install required packages: `pip install -r requirements.txt`
3. Run the game: `python quantum_drift.py`

## Controls

- Arrow Keys: Move
- Q/W/E/R: Change quantum state
- Z: Slow down echoes
- X: Speed up echoes
- ESC: Pause game
- R: Restart level

## Game Mechanics

- **Temporal Echoes**: Every move creates an echo that repeats after N turns
- **Quantum States**: Different states (Alpha, Beta, Gamma, Delta) have different properties
- **Timeline Manipulation**: Speed up or slow down specific echoes
- **Dimensional Puzzles**: Use echoes to solve increasingly complex challenges

---

# Inertia

A physics-based puzzle game where you control an object that obeys Newton's First Law—once set in motion, it keeps moving until something stops it.

## Game Concept

Inertia is a physics-based puzzle game where you control an object that obeys Newton's First Law—once set in motion, it keeps moving until something stops it. Your goal is to navigate through increasingly complex mazes using carefully timed pulses of force while managing your limited energy reserves. Special surfaces, gravity fields, and obstacles create an evolving challenge that's easy to understand but difficult to master.

The killer twist: unlike most games where you directly control movement, in Inertia you apply forces that set your object in motion—then deal with the consequences as momentum carries you forward. This creates a uniquely satisfying "skating on ice" feeling where planning your trajectory becomes as important as quick reactions.

## Gameplay Breakdown

The core gameplay loop is elegantly simple:

1. **Apply Forces**: Use arrow keys to apply directional pushes to your ball, with each push consuming energy from your limited reserve
2. **Manage Momentum**: Once moving, your ball continues in that direction, affected by friction and obstacles
3. **Navigate Challenges**: Deal with different surfaces (ice is slippery, mud slows you down, bouncy surfaces increase your velocity)
4. **Reach Targets**: Collect all targets in each level to progress
5. **Adapt Strategies**: As levels advance, avoid gravity fields that pull you off course, time your movements around moving obstacles, and find efficient paths through increasingly complex mazes
6. **Beat Your Records**: Track your completion time and aim to beat your personal best for each level

## Installation

1. Ensure you have Python 3.6+ installed
2. Install required packages: `pip install -r requirements.txt`
3. Run the game: `python inertia.py` or `py inertia.py` on Windows

## Controls

- Arrow Keys: Apply force in that direction
- P: Pause/Resume game
- R: Reset current level
- G: Toggle gravity field when the gravity power-up is active
- Each force application consumes energy
- Energy regenerates slowly over time

## Game Mechanics

- **Momentum**: Once in motion, your ball continues in that direction until stopped
- **Energy Management**: Each force application costs energy based on its magnitude
- **Surface Types**: Different surfaces affect your ball's movement (ice, mud, bouncy)
- **Obstacles**: Walls cause your ball to bounce realistically
- **Targets**: Collect all targets to advance to the next level
- **Time Tracking**: Each level tracks your completion time
- **High Scores**: The game saves your best times and scores for each level
- **Power-Ups System**: Collect various power-ups to gain temporary advantages:
  - **Energy Refill**: Restores 30% of your energy instantly
  - **Speed Boost**: Reduces friction by 50% for 5 seconds, allowing faster movement
  - **Gravity Field**: Enables a toggleable gravity field for 3 seconds that can pull or push objects
  - **Shield**: Absorbs one collision damage or allows passing through one wall
- **Enhanced Physics**: Navigate around gravity wells that can pull or push your ball based on proximity
- **Teleporters**: Transport instantly between linked teleporter pairs, maintaining momentum
- **Particle Effects**: Visual feedback for collisions, power-ups, and movement
- **Sound Effects**: Audio cues for game events and actions

## Features

- Physics-based movement with realistic momentum
- Multiple surface types with different friction coefficients
- Procedurally generated levels for endless gameplay
- Energy management system
- Time tracking for speedrunning
- High score system that saves your best times and scores
- Pause functionality
- Power-ups that provide strategic advantages
- Gravity wells that create dynamic movement challenges
- Visual effects including ball trails and power-up animations
- Player-controlled gravity field with the 'G' key when the gravity power-up is active
- Teleportation system with entrance and exit portals
- Screen shake effects for impacts and teleportation
- Particle system for visual polish
- Sound effects for game events (requires audio files in the sounds folder)
- Dynamic level design with increasing complexity

## Future Plans

- Level editor for creating and sharing custom levels
- Additional power-up types and obstacles
- Background music and improved sound effects
- Achievements and unlockable content
- Challenge modes with special conditions
