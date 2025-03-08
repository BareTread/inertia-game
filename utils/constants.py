from enum import Enum
import pygame

# Game Constants
WIDTH = 1280
HEIGHT = 720
FPS = 60
TITLE = "Inertia Deluxe"
FRICTION = 0.99
ENERGY_MAX = 100
ENERGY_REGEN = 0.5
FORCE_COST = 0.5
HIGHSCORE_FILE = "data/highscores.json"
LEVELS_FILE = "data/levels.json"
SETTINGS_FILE = "data/settings.json"
MAX_LEVELS = 30
REQUIRED_STARS_TO_UNLOCK = 2

# Physics constants
MIN_FORCE_THRESHOLD = 0.5
MAX_FORCE = 10.0
MAX_SHAKE = 0.5

# Game State Enum
class GameState(Enum):
    MAIN_MENU = 0
    LEVEL_SELECT = 1
    GAME = 2
    PAUSED = 3
    LEVEL_COMPLETE = 5
    GAME_OVER = 6
    SETTINGS = 4
    CREDITS = 7
    TUTORIAL = 8

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (20, 220, 20)    # More vibrant green
BLUE = (0, 120, 255)     # More vibrant blue
YELLOW = (255, 220, 0)   # More golden yellow
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
TRANSPARENT_BLACK = (0, 0, 0, 128)

# Surface types and their friction coefficients
SURFACES = {
    "normal": {"friction": 0.98, "color": (100, 100, 100)},
    "ice": {"friction": 0.995, "color": (200, 200, 255)},
    "rough": {"friction": 0.7, "color": (139, 69, 19)},
    "bouncy": {"friction": 0.98, "color": (255, 105, 180)},
    "sticky": {"friction": 0.5, "color": (50, 205, 50)},
    "deadly": {"friction": 0.98, "color": (255, 0, 0)}
}

# Default game settings
DEFAULT_SETTINGS = {
    "sound_volume": 0.7,
    "music_volume": 0.5,
    "fullscreen": False,
    "particles": True,
    "screen_shake": True,
    "controls": {
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "pause": pygame.K_SPACE,
        "reset": pygame.K_r
    }
}

# Level values
DEFAULT_LEVEL_TIME = 60  # Default time limit in seconds
DEFAULT_ENERGY_DRAIN = 0.0  # Default energy drain per second
MAX_STARS = 3  # Maximum stars per level 

# Progressive Mastery System
MASTERY_METRICS = ["time", "energy", "precision", "targets"]
MASTERY_LEVELS = ["beginner", "intermediate", "advanced", "master"]
MASTERY_THRESHOLDS = {
    "time": [0.4, 0.6, 0.8, 0.95],      # Time efficiency thresholds
    "energy": [0.3, 0.5, 0.7, 0.9],     # Energy efficiency thresholds
    "precision": [0.2, 0.4, 0.6, 0.8],  # Precision thresholds
    "targets": [0.7, 0.8, 0.9, 1.0]     # Target hit ratio thresholds
}
MASTERY_REWARDS = {
    "time": ["blue_trail", "cyan_trail", "white_trail", "rainbow_trail"],
    "energy": ["small_glow", "medium_glow", "large_glow", "energy_aura"],
    "precision": ["bronze_spark", "silver_spark", "gold_spark", "diamond_spark"],
    "targets": ["green_pulse", "yellow_pulse", "orange_pulse", "red_pulse"]
}

# Grid and background settings
GRID_SIZE = 40
GRID_COLOR = (40, 40, 50)  # Slightly lighter gray for better visibility
BACKGROUND_COLOR = (15, 15, 25)  # Very dark blue-black, slightly lighter for contrast
BOUNDARY_COLOR = (40, 40, 100)  # Blue-ish border
BOUNDARY_THICKNESS = 3

# Wall settings
WALL_BORDER_COLOR = (100, 100, 220)  # Light blue border
WALL_BORDER_WIDTH = 2 