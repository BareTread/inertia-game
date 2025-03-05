# Development Guidelines for Inertia Deluxe

This document outlines development standards and practices for contributing to the Inertia Deluxe project.

## Project Structure

The project follows a modular architecture with clear separation of concerns:

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
│   ├── ball.py         # Player-controlled ball
│   ├── powerup.py      # Powerup items
│   ├── surface.py      # Game surfaces
│   ├── target.py       # Target objects
│   └── wall.py         # Wall objects
├── levels/             # Level management
│   └── level_generator.py # Level generation utilities
├── ui/                 # User interface components
│   ├── button.py       # Button component
│   ├── slider.py       # Slider component
│   └── toast.py        # Toast notifications
├── utils/              # Utility modules
│   ├── constants.py    # Game constants
│   ├── helpers.py      # Helper functions
│   ├── particle.py     # Particle system
│   └── sound.py        # Sound management
├── game.py             # Main game class
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

## Code Style Guidelines

1. **PEP 8**: Follow PEP 8 style guidelines for Python code.
2. **Type Hints**: Use type hints for all function parameters and return values.
3. **Docstrings**: Include docstrings for all classes and functions.
4. **Comments**: Add comments for complex logic or non-obvious code.
5. **Variable Names**: Use descriptive variable names.

## Class Responsibilities

Each class should have a single responsibility:

1. **Game**: Main class that handles the game loop, state management, and screen transitions.
2. **Entities**: Each entity class (Ball, Surface, Target, etc.) manages its own state and rendering.
3. **UI Components**: Button, Slider, and Toast handle their own interactions and rendering.
4. **Utilities**: Helper functions and particle system provide reusable functionality.

## Adding New Features

When adding new features:

1. **Entity Classes**: For new game objects, add a class in the entities directory.
2. **UI Components**: For new UI elements, add a class in the ui directory.
3. **Game Logic**: Extend the Game class with new methods for handling game states.
4. **Assets**: Add new assets to the appropriate subdirectory in assets/.

## Testing

Test your changes thoroughly:

1. **Functionality**: Ensure that new features work as expected.
2. **Performance**: Check for performance issues, especially with particle effects or large numbers of objects.
3. **Edge Cases**: Test boundary conditions and error cases.
4. **Cross-platform**: Verify that the game works on different operating systems.

## Contributing

1. Fork the repository.
2. Create a feature branch.
3. Make your changes.
4. Test thoroughly.
5. Submit a pull request.

## Dependencies

The game has minimal dependencies:

- **pygame**: Core game library
- **numpy**: Used for certain math operations

When adding new dependencies, update requirements.txt with specific versions.

## Asset Guidelines

1. **Fonts**: Use open-source fonts and include attribution.
2. **Images**: Use original or freely licensed images.
3. **Sounds**: Use original or freely licensed sound effects and music.
4. **Attribution**: Include attribution for all third-party assets.

## Performance Considerations

1. **Object Pools**: Reuse objects rather than creating new ones repeatedly.
2. **Batched Rendering**: Group similar draw calls together.
3. **Particles**: Limit the number of active particles.
4. **Collision Detection**: Use spatial partitioning for many objects.

## Documentation

Keep documentation up to date:

1. **README.md**: Overview, installation, and usage instructions.
2. **DEVELOPMENT.md**: Development guidelines and project structure.
3. **Inline Documentation**: Update docstrings and comments when changing code.

## Version Control

1. **Commit Messages**: Write clear, descriptive commit messages.
2. **Branches**: Use feature branches for development.
3. **Tags**: Tag releases with version numbers.

By following these guidelines, we ensure that Inertia Deluxe remains maintainable, extensible, and fun to play. 