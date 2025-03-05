Fonts for Inertia Deluxe
=====================

This game uses the default Pygame fonts for simplicity. If you want to use custom fonts:

1. Download free fonts from Google Fonts or another source
2. Place .ttf files in this directory
3. Update the `_load_fonts` method in game.py to use these font files:

```python
def _load_fonts(self) -> None:
    """Load fonts for the game."""
    # Get the font path
    font_path = os.path.join("assets", "fonts", "your_font.ttf")
    
    # Load fonts in different sizes
    self.title_font = pygame.font.Font(font_path, 48)
    self.subtitle_font = pygame.font.Font(font_path, 36)
    self.regular_font = pygame.font.Font(font_path, 24)
    self.small_font = pygame.font.Font(font_path, 18)
```

Recommended Free Fonts:
- Press Start 2P (for pixel/retro style)
- Roboto (for clean modern look)
- Ubuntu (for good readability)
- Montserrat (for modern style) 