import pygame
import sys
import json
import time
import os
import math
import random
import colorsys
from typing import Dict, List, Tuple, Optional, Any, Union

from utils.constants import (
    WIDTH, HEIGHT, FPS, ENERGY_MAX, ENERGY_REGEN, FORCE_COST, FRICTION,
    GameState, WHITE, BLACK, RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, 
    CYAN, DARK_GRAY, GRAY, REQUIRED_STARS_TO_UNLOCK, MASTERY_METRICS, MASTERY_THRESHOLDS, MASTERY_REWARDS, MASTERY_LEVELS
)
from utils.constants import HIGHSCORE_FILE, LEVELS_FILE, SETTINGS_FILE
from utils.constants import TRANSPARENT_BLACK
from utils.sound import load_sounds, play_sound, set_sound_volume, set_music_volume
from utils.particle import ParticleSystem
from utils.helpers import distance, normalize_vector, clamp, lerp, circle_rect_collision, circle_circle_collision
from utils.tutorial import TutorialElement

# Define our own light gray color
LIGHT_GRAY = (200, 200, 200)

from entities.ball import Ball
from entities.wall import Wall
from entities.target import Target
from entities.surface import Surface, SURFACE_TYPES
from entities.powerup import PowerUp

from ui.button import Button
from ui.slider import Slider
from ui.toast import Toast

from levels.level_generator import generate_level

class Game:
    """Main game class that handles all game states and logic."""
    
    def __init__(self) -> None:
        """Initialize the game."""
        # Initialize pygame and mixer
        pygame.init()
        pygame.mixer.init()
        
        # Create the game window
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Inertia Deluxe")
        
        # Set up the clock
        self.clock = pygame.time.Clock()
        self.dt = 0.0  # Delta time in seconds
        
        # Initialize last update time
        self.last_update_time = pygame.time.get_ticks()
        
        # Load game settings
        self._load_settings()
        
        # Set sound volumes from settings
        set_sound_volume(self.settings["sound_volume"])
        set_music_volume(self.settings["music_volume"])
        
        # Load sounds
        load_sounds()
        
        # Create particle system
        self.particle_system = ParticleSystem(max_particles=500)
        
        # Set up fonts
        self.title_font = pygame.font.Font(None, 64)
        self.subtitle_font = pygame.font.Font(None, 48)
        self.regular_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        # Initialize game state
        self.state = GameState.MAIN_MENU
        self.previous_state = None
        
        # Game objects
        self.ball = None
        self.walls = []
        self.targets = []
        self.surfaces = []
        self.powerups = []
        self.gravity_wells = []
        self.bounce_pads = []
        self.teleporters = []
        
        # Level data
        self.current_level = 1
        self.levels_data = self._load_levels_data()
        
        # UI elements
        self.buttons = {}
        self.sliders = {}
        self.toasts = []
        
        # Game metrics
        self.energy = ENERGY_MAX
        self.score = 0
        self.time_remaining = 0
        self.level_start_time = 0
        
        # Force application
        self.applying_force = False
        self.force_direction = (0, 0)
        self.force_magnitude = 0
        
        # Mastery system
        self.mastery_data = {metric: 0.0 for metric in MASTERY_METRICS}
        self.mastery_levels = {metric: 0 for metric in MASTERY_METRICS}
        self.active_rewards = {metric: None for metric in MASTERY_METRICS}
        self.precision_moves = []  # Track directional changes
        self.target_stats = {"hit": 0, "total": 0}
        
        # Create main menu buttons
        self._setup_main_menu()
    
    def _load_settings(self) -> None:
        """Load settings from file or use defaults."""
        # Default settings
        self.settings = {
            "sound_volume": 0.7,
            "music_volume": 0.5,
            "particles": True,
            "screen_shake": True,
            "show_fps": False,
            "fullscreen": False,
            "controls": {
                "up": pygame.K_UP,
                "down": pygame.K_DOWN,
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "pause": pygame.K_SPACE,
                "reset": pygame.K_r
            }
        }
        
        # Try to load settings from file
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r") as f:
                    loaded_settings = json.load(f)
                    # Update settings with loaded values
                    for key, value in loaded_settings.items():
                        if key in self.settings:
                            self.settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")
            print("Using default settings")
        
        # Apply settings
        set_sound_volume(self.settings["sound_volume"])
        set_music_volume(self.settings["music_volume"])
        
        # Apply fullscreen if enabled
        if self.settings.get("fullscreen", False):
            pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    
    def _load_levels_data(self) -> Dict[str, Any]:
        """Load levels data from file or use defaults."""
        # Default levels data
        levels_data = {
            "unlocked": 1,
            "stars": {},
            "times": {},
            "levels": {},
            "mastery": {
                "data": {metric: 0.0 for metric in MASTERY_METRICS},
                "levels": {metric: 0 for metric in MASTERY_METRICS},
                "rewards": {metric: None for metric in MASTERY_METRICS}
            }
        }
        
        # Try to load levels data from file
        try:
            if os.path.exists(LEVELS_FILE):
                with open(LEVELS_FILE, "r") as f:
                    loaded_data = json.load(f)
                    # Update levels data with loaded values
                    for key, value in loaded_data.items():
                        levels_data[key] = value
                    
                    # Ensure times key exists for older save files
                    if "times" not in levels_data:
                        levels_data["times"] = {}
                        
                    # Ensure mastery data exists
                    if "mastery" not in levels_data:
                        levels_data["mastery"] = {
                            "data": {metric: 0.0 for metric in MASTERY_METRICS},
                            "levels": {metric: 0 for metric in MASTERY_METRICS},
                            "rewards": {metric: None for metric in MASTERY_METRICS}
                        }
                    
                    # Load mastery data into instance variables
                    self.mastery_data = levels_data["mastery"]["data"]
                    self.mastery_levels = levels_data["mastery"]["levels"]
                    self.active_rewards = levels_data["mastery"]["rewards"]
        except Exception as e:
            print(f"Error loading levels data: {e}")
            print("Using default levels data")
        
        # Calculate total stars
        total_stars = sum(levels_data.get("stars", {}).values())
        levels_data["total_stars"] = total_stars
        
        return levels_data
    
    def _save_settings(self) -> None:
        """Save current settings to file."""
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def _save_levels_data(self) -> None:
        """Save current level data to file."""
        with open(LEVELS_FILE, 'w') as f:
            json.dump(self.levels_data, f, indent=4)
    
    def _setup_main_menu(self) -> None:
        """Create buttons for the main menu."""
        center_x = WIDTH // 2
        button_width = 200
        button_height = 50
        button_spacing = 60
        
        # Calculate starting y position to center the buttons vertically
        num_buttons = 4  # Play, Level Select, Settings, Quit
        total_height = num_buttons * button_height + (num_buttons - 1) * (button_spacing - button_height)
        start_y = (HEIGHT - total_height) // 2
        
        # Create buttons
        self.buttons["main_menu"] = {}
        
        # Play button
        self.buttons["main_menu"]["play"] = Button(
            center_x, start_y,
            button_width, button_height,
            "Play",
            self.regular_font,
            callback=lambda: self._start_level(1)
        )
        
        # Level select button
        self.buttons["main_menu"]["level_select"] = Button(
            center_x, start_y + button_spacing,
            button_width, button_height,
            "Level Select",
            self.regular_font,
            callback=lambda: self._change_state(GameState.LEVEL_SELECT)
        )
        
        # Settings button
        self.buttons["main_menu"]["settings"] = Button(
            center_x, start_y + 2 * button_spacing,
            button_width, button_height,
            "Settings",
            self.regular_font,
            callback=lambda: self._change_state(GameState.SETTINGS)
        )
        
        # Quit button
        self.buttons["main_menu"]["quit"] = Button(
            center_x, start_y + 3 * button_spacing,
            button_width, button_height,
            "Quit",
            self.regular_font,
            callback=self._quit_game
        )

    def _change_state(self, new_state: GameState) -> None:
        """Change the current game state and set up the new state."""
        # Set the new state
        self.state = new_state
        
        # Set up the new state
        if new_state == GameState.MAIN_MENU:
            self._setup_main_menu()
        elif new_state == GameState.LEVEL_SELECT:
            self._setup_level_select()
        elif new_state == GameState.SETTINGS:
            self._setup_settings()
        elif new_state == GameState.GAME:
            self._setup_game()
        elif new_state == GameState.PAUSED:
            self._setup_pause_menu()
        elif new_state == GameState.LEVEL_COMPLETE:
            self._setup_level_complete()
    
    def _quit_game(self) -> None:
        """Save game data and exit."""
        self._save_settings()
        self._save_levels_data()
        pygame.quit()
        sys.exit()
    
    def _start_level(self, level_num: int) -> None:
        """Start a specific level."""
        # Check if level is unlocked
        if level_num > self.levels_data["unlocked"]:
            self.toasts.append(Toast("Level locked! Complete previous levels first.", duration=2.0))
            return
        
        # Set current level and initialize it
        self.current_level = level_num
        self._setup_level(level_num)
        self._change_state(GameState.GAME)
    
    def _setup_level(self, level_num: int) -> None:
        """Set up a level with all entities."""
        # Clear existing entities
        self.walls = []
        self.targets = []
        self.surfaces = []
        self.powerups = []
        self.gravity_wells = []
        self.bounce_pads = []
        self.teleporters = []
        
        # Generate level data
        level_data = generate_level(level_num)
        
        # Store the full level data for tutorial elements and hints
        self.level_data = level_data
        
        # Create entities from level data
        self.walls = level_data["walls"]
        self.targets = level_data["targets"]
        self.surfaces = level_data["surfaces"]
        self.powerups = level_data["powerups"]
        self.gravity_wells = level_data.get("gravity_wells", [])
        self.bounce_pads = level_data.get("bounce_pads", [])
        self.teleporters = level_data.get("teleporters", [])
        
        # Initialize mastery system tracking for this level
        self.target_stats = {"hit": 0, "total": len(self.targets)}
        self.precision_moves = []
        
        # Initialize game state - Use "start_pos" instead of "ball_start"
        self.ball = Ball(level_data["start_pos"][0], level_data["start_pos"][1])
        self.energy = ENERGY_MAX
        self.score = 0
        self.time_remaining = self._get_level_time_limit(level_num)
        self.level_start_time = pygame.time.get_ticks()
        self.applying_force = False
        
        # Initialize energy drain from level data
        self.energy_drain = level_data.get("energy_drain", 0.0)
        
        # Store background color from level data
        self.background_color = level_data.get("background_color", (20, 20, 30))
    
    def process_events(self) -> bool:
        """
        Process all game events.
        Returns True if the game should continue, False if it should quit.
        """
        # Get mouse state
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        # Process events
        for event in pygame.event.get():
            # Always check for quit events
            if event.type == pygame.QUIT:
                self._quit_game()
                return False
            
            # Process events based on current state
            if self.state == GameState.MAIN_MENU:
                self._process_main_menu_events(event, mouse_pos, mouse_pressed)
            elif self.state == GameState.LEVEL_SELECT:
                self._process_level_select_events(event, mouse_pos, mouse_pressed)
            elif self.state == GameState.SETTINGS:
                self._process_settings_events(event, mouse_pos, mouse_pressed)
            elif self.state == GameState.GAME:
                self._process_game_events(event, mouse_pos, mouse_pressed)
            elif self.state == GameState.PAUSED:
                self._process_pause_events(event, mouse_pos, mouse_pressed)
            elif self.state == GameState.LEVEL_COMPLETE:
                self._process_level_complete_events(event, mouse_pos, mouse_pressed)
        
        return True

    def update(self) -> None:
        """Update the current game state."""
        # Calculate delta time
        self.dt = self.clock.tick(FPS) / 1000.0
        
        # Update based on current state
        if self.state == GameState.MAIN_MENU:
            self._update_main_menu()
        elif self.state == GameState.LEVEL_SELECT:
            self._update_level_select()
        elif self.state == GameState.GAME:
            self._update_game()
        elif self.state == GameState.PAUSED:
            self._update_pause_menu()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._update_level_complete()
            
        # Update particle system
        self.particle_system.update(self.dt)
        
        # Update toasts
        for toast in self.toasts[:]:
            toast.update(self.dt)
            if toast.done:
                self.toasts.remove(toast)

    def draw(self) -> None:
        """Draw the current game state."""
        # Clear the screen
        self.screen.fill((10, 10, 20))
        
        # Draw based on current state
        if self.state == GameState.MAIN_MENU:
            self._draw_main_menu()
        elif self.state == GameState.LEVEL_SELECT:
            self._draw_level_select()
        elif self.state == GameState.GAME:
            self._draw_game()
        elif self.state == GameState.PAUSED:
            self._draw_game()  # Draw the game in the background
            self._draw_pause_menu()
        elif self.state == GameState.SETTINGS:
            self._draw_settings()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._draw_game()  # Draw the game in the background
            self._draw_level_complete()
        
        # Update the display
        pygame.display.flip()

    def _process_main_menu_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], 
                                  mouse_pressed: Tuple[bool, bool, bool]) -> None:
        """Process events for the main menu state."""
        # Update all buttons with current mouse state
        for button in self.buttons["main_menu"].values():
            button.update(mouse_pos, mouse_pressed)
            
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._quit_game()
            elif event.key == pygame.K_RETURN:
                self._start_level(1)
    
    def _update_main_menu(self) -> None:
        """Update the main menu state."""
        # Add some particles for visual effect
        if random.random() < 0.05:
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            vel_x = random.uniform(-20, 20)
            vel_y = random.uniform(-20, 20)
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            size = random.uniform(2, 5)
            lifetime = random.uniform(1, 3)
            self.particle_system.add_particle(x, y, vel_x, vel_y, color, size, lifetime)
    
    def _draw_main_menu(self) -> None:
        """Draw the main menu state."""
        # Draw background grid
        self._draw_grid()
        
        # Draw title
        title_text = self.title_font.render("INERTIA DELUXE", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw subtitle
        subtitle_text = self.regular_font.render("A physics-based puzzle game", True, (200, 200, 200))
        subtitle_rect = subtitle_text.get_rect(center=(WIDTH//2, 150))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw total stars collected
        stars_text = self.small_font.render(f"Total Stars: {self.levels_data['total_stars']}", True, YELLOW)
        stars_rect = stars_text.get_rect(center=(WIDTH//2, HEIGHT - 50))
        self.screen.blit(stars_text, stars_rect)
        
        # Draw buttons
        for button in self.buttons["main_menu"].values():
            button.draw(self.screen)
        
        # Draw particles
        self.particle_system.draw(self.screen)
        
    def _draw_grid(self) -> None:
        """Draw a background grid."""
        # Draw a dark grid as background
        grid_color = (30, 30, 30)
        grid_spacing = 40
        
        # Draw horizontal grid lines
        for y in range(0, HEIGHT, grid_spacing):
            pygame.draw.line(self.screen, grid_color, (0, y), (WIDTH, y), 1)
            
        # Draw vertical grid lines
        for x in range(0, WIDTH, grid_spacing):
            pygame.draw.line(self.screen, grid_color, (x, 0), (x, HEIGHT), 1)

    def _setup_game(self) -> None:
        """Set up the game state."""
        # Reset game state
        self.applying_force = False
        self.force_direction = (0, 0)
        self.force_magnitude = 0
        
    def _setup_level_select(self) -> None:
        """Set up the level select screen."""
        # Create level select buttons
        self.buttons["level_select"] = {}
        
        # Calculate grid layout
        levels_per_row = 5
        button_width = 80
        button_height = 80
        horizontal_spacing = 100
        vertical_spacing = 100
        
        # Calculate starting position
        start_x = (WIDTH - (levels_per_row - 1) * horizontal_spacing) // 2
        start_y = 150
        
        # Add back button
        self.buttons["level_select"]["back"] = Button(
            100, 50,
            120, 40,
            "Back",
            self.regular_font,
            callback=lambda: self._change_state(GameState.MAIN_MENU)
        )
        
        # Add level buttons
        max_unlocked = self.levels_data["unlocked"]
        
        for level in range(1, 31):  # Up to 30 levels
            # Calculate position in the grid
            row = (level - 1) // levels_per_row
            col = (level - 1) % levels_per_row
            
            x = start_x + col * horizontal_spacing
            y = start_y + row * vertical_spacing
            
            # Create button
            button = Button(
                x, y,
                button_width, button_height,
                str(level),
                self.regular_font,
                callback=lambda l=level: self._start_level(l)
            )
            
            # Disable locked levels
            if level > max_unlocked:
                button.disabled = True
            
            self.buttons["level_select"][f"level_{level}"] = button
    
    def _process_level_select_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], 
                                     mouse_pressed: Tuple[bool, bool, bool]) -> None:
        """Process events for the level select screen."""
        # Update all buttons with current mouse state
        for button in self.buttons["level_select"].values():
            button.update(mouse_pos, mouse_pressed)
            
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._change_state(GameState.MAIN_MENU)
    
    def _update_level_select(self) -> None:
        """Update the level select screen."""
        # Add some particles for visual effect
        if random.random() < 0.02:
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            vel_x = random.uniform(-10, 10)
            vel_y = random.uniform(-10, 10)
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            size = random.uniform(1, 4)
            lifetime = random.uniform(1, 2)
            self.particle_system.add_particle(x, y, vel_x, vel_y, color, size, lifetime)
    
    def _draw_level_select(self) -> None:
        """Draw the level select screen."""
        # Draw background grid
        self._draw_grid()
        
        # Draw title
        title_text = self.subtitle_font.render("SELECT LEVEL", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        for button_key, button in self.buttons["level_select"].items():
            button.draw(self.screen)
            
            # Draw stars for completed levels
            if button_key.startswith("level_"):
                level_num = int(button_key.split("_")[1])
                if str(level_num) in self.levels_data["stars"]:
                    stars = self.levels_data["stars"][str(level_num)]
                    
                    # Draw stars below the button
                    star_y = button.y + button.height // 2 + 25
                    for i in range(3):
                        color = YELLOW if i < stars else (50, 50, 50)
                        star_x = button.x - 20 + i * 20
                        pygame.draw.polygon(self.screen, color, [
                            (star_x, star_y),
                            (star_x - 5, star_y + 15),
                            (star_x + 10, star_y + 5),
                            (star_x - 10, star_y + 5),
                            (star_x + 5, star_y + 15)
                        ])
        
        # Draw particles
        self.particle_system.draw(self.screen)
        
    def _setup_settings(self) -> None:
        """Set up the settings screen."""
        # Create settings buttons and sliders
        self.buttons["settings"] = {}
        self.sliders["settings"] = {}
        
        # Add back button
        self.buttons["settings"]["back"] = Button(
            100, 50,
            120, 40,
            "Back",
            self.regular_font,
            callback=lambda: self._on_settings_back()
        )
        
        # Add reset button
        self.buttons["settings"]["reset"] = Button(
            WIDTH - 100, 50,
            120, 40,
            "Reset",
            self.regular_font,
            callback=lambda: self._reset_settings()
        )
        
        # Add sound volume slider
        self.sliders["settings"]["sound"] = Slider(
            WIDTH // 2, 200,
            300, 20,
            0, 1,
            self.settings["sound_volume"],
            "Sound Volume",
            self.regular_font,
            callback=self._on_sound_volume_change
        )
        
        # Add music volume slider
        self.sliders["settings"]["music"] = Slider(
            WIDTH // 2, 260,
            300, 20,
            0, 1,
            self.settings["music_volume"],
            "Music Volume",
            self.regular_font,
            callback=self._on_music_volume_change
        )
        
        # Add fullscreen toggle
        self.buttons["settings"]["fullscreen"] = Button(
            WIDTH // 2, 320,
            200, 40,
            "Fullscreen: " + ("ON" if self.settings["fullscreen"] else "OFF"),
            self.regular_font,
            callback=self._toggle_fullscreen
        )
        
        # Add particles toggle
        self.buttons["settings"]["particles"] = Button(
            WIDTH // 2, 380,
            200, 40,
            "Particles: " + ("ON" if self.settings["particles"] else "OFF"),
            self.regular_font,
            callback=self._toggle_particles
        )
        
        # Add screen shake toggle
        self.buttons["settings"]["screen_shake"] = Button(
            WIDTH // 2, 440,
            200, 40,
            "Screen Shake: " + ("ON" if self.settings["screen_shake"] else "OFF"),
            self.regular_font,
            callback=self._toggle_screen_shake
        )

    def _process_settings_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], 
                                 mouse_pressed: Tuple[bool, bool, bool]) -> None:
        """Process events for the settings screen."""
        # Update all buttons with current mouse state
        for button in self.buttons["settings"].values():
            button.update(mouse_pos, mouse_pressed)
            
        # Update all sliders with current mouse state
        for slider in self.sliders["settings"].values():
            slider.update(mouse_pos, mouse_pressed)
            
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_settings_back()
    
    def _update_settings(self) -> None:
        """Update the settings screen."""
        # Add some particles for visual effect
        if random.random() < 0.02 and self.settings["particles"]:
            x = random.randint(0, WIDTH)
            y = random.randint(0, HEIGHT)
            vel_x = random.uniform(-10, 10)
            vel_y = random.uniform(-10, 10)
            color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            size = random.uniform(1, 4)
            lifetime = random.uniform(1, 2)
            self.particle_system.add_particle(x, y, vel_x, vel_y, color, size, lifetime)
    
    def _draw_settings(self) -> None:
        """Draw the settings screen."""
        # Draw background grid
        self._draw_grid()
        
        # Draw title
        title_text = self.subtitle_font.render("SETTINGS", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        for button in self.buttons["settings"].values():
            button.draw(self.screen)
            
        # Draw sliders
        for slider in self.sliders["settings"].values():
            slider.draw(self.screen)
        
        # Draw particles
        self.particle_system.draw(self.screen)
        
    def _on_settings_back(self) -> None:
        """Handle back button in settings."""
        # Save settings
        self._save_settings()
        
        # Return to previous state or main menu
        if self.previous_state:
            self._change_state(self.previous_state)
        else:
            self._change_state(GameState.MAIN_MENU)
    
    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        self.settings = {
            "music_volume": 0.5,
            "sound_volume": 0.7,
            "screen_shake": True,
            "particles": True,
            "fullscreen": False,
            "controls": {
                "up": pygame.K_UP,
                "down": pygame.K_DOWN,
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "pause": pygame.K_SPACE,
                "reset": pygame.K_r
            },
            "show_fps": False
        }
        
        # Update UI to reflect changes
        self.sliders["settings"]["sound"].set_value(self.settings["sound_volume"])
        self.sliders["settings"]["music"].set_value(self.settings["music_volume"])
        
        self.buttons["settings"]["fullscreen"].set_text("Fullscreen: " + ("ON" if self.settings["fullscreen"] else "OFF"))
        self.buttons["settings"]["particles"].set_text("Particles: " + ("ON" if self.settings["particles"] else "OFF"))
        self.buttons["settings"]["screen_shake"].set_text("Screen Shake: " + ("ON" if self.settings["screen_shake"] else "OFF"))
        
        # Apply settings
        set_sound_volume(self.settings["sound_volume"])
        set_music_volume(self.settings["music_volume"])
        
        # Show confirmation
        self.toasts.append(Toast("Settings reset to defaults", duration=2.0))
    
    def _on_sound_volume_change(self, value: float) -> None:
        """Handle sound volume slider change."""
        self.settings["sound_volume"] = value
        set_sound_volume(value)
    
    def _on_music_volume_change(self, value: float) -> None:
        """Handle music volume slider change."""
        self.settings["music_volume"] = value
        set_music_volume(value)
    
    def _toggle_fullscreen(self) -> None:
        """Toggle fullscreen setting."""
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        self.buttons["settings"]["fullscreen"].set_text("Fullscreen: " + ("ON" if self.settings["fullscreen"] else "OFF"))
        
        # Apply fullscreen setting
        if self.settings["fullscreen"]:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    def _toggle_particles(self) -> None:
        """Toggle particles setting."""
        self.settings["particles"] = not self.settings["particles"]
        self.buttons["settings"]["particles"].set_text("Particles: " + ("ON" if self.settings["particles"] else "OFF"))
        
        if not self.settings["particles"]:
            self.particle_system.clear()
    
    def _toggle_screen_shake(self) -> None:
        """Toggle screen shake setting."""
        self.settings["screen_shake"] = not self.settings["screen_shake"]
        self.buttons["settings"]["screen_shake"].set_text("Screen Shake: " + ("ON" if self.settings["screen_shake"] else "OFF"))

    def _process_game_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], 
                             mouse_pressed: Tuple[bool, bool, bool]) -> None:
        """Process events for the gameplay state."""
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            # Pause game
            if event.key == self.settings["controls"]["pause"]:
                self._change_state(GameState.PAUSED)
            
            # Reset level
            elif event.key == self.settings["controls"]["reset"]:
                self._setup_level(self.current_level)
        
        # Handle force application with keyboard
        keys = pygame.key.get_pressed()
        
        # Calculate force direction based on arrow keys
        force_x, force_y = 0, 0
        
        if keys[self.settings["controls"]["up"]]:
            force_y -= 1
        if keys[self.settings["controls"]["down"]]:
            force_y += 1
        if keys[self.settings["controls"]["left"]]:
            force_x -= 1
        if keys[self.settings["controls"]["right"]]:
            force_x += 1
        
        # Don't normalize the force - this allows diagonal input to be stronger
        # which matches the original game's behavior
        if force_x != 0 or force_y != 0:
            self.applying_force = True
            self.force_direction = (force_x, force_y)
        else:
            self.applying_force = False
    
    def _update_game(self) -> None:
        """Update the game state."""
        # Get time delta
        dt = self.dt
        
        # Update time remaining
        self.time_remaining -= dt
        
        # Check if time ran out
        if self.time_remaining <= 0:
            self._level_failed()
            return
        
        # Apply visual effects based on mastery rewards
        self._update_ball_visual_effects()
        
        # Handle time slow effect for star collection
        dt_multiplier = 1.0
        if hasattr(self, 'time_slow_effect') and self.time_slow_effect < 1.0:
            # Apply time slow effect
            dt_multiplier = self.time_slow_effect
            
            # Update time slow timer
            if hasattr(self, 'time_slow_timer'):
                self.time_slow_timer += self.dt
                
                # Gradually return to normal speed
                if self.time_slow_timer < self.time_slow_duration:
                    # Linear interpolation from slow effect to normal speed
                    progress = self.time_slow_timer / self.time_slow_duration
                    self.time_slow_effect = 0.3 + progress * 0.7  # Slowly return to 1.0
                else:
                    # Effect is over
                    self.time_slow_effect = 1.0
            
        # Apply time scale to delta time
        effective_dt = self.dt * dt_multiplier
            
        # Check input for force application
        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        # Apply force if mouse is pressed or keys are held
        self.applying_force = False
        
        # Apply force based on controls (keyboard or mouse)
        force_x, force_y = self._calculate_force(keys, mouse_pressed, mouse_pos)
        
        if force_x != 0 or force_y != 0:
            # Store force direction for drawing
            self.force_direction = (force_x, force_y)
            
            # Calculate force magnitude
            self.force_magnitude = min(math.sqrt(force_x**2 + force_y**2), 5)
            
            # Apply force if there's enough energy
            if self.energy > 0:
                self.applying_force = True
                self.ball.apply_force(force_x, force_y)

                # Add thrust effect particles
                self.particle_system.add_trail(
                    self.ball.x, self.ball.y,
                    (255, 255, 0),  # Yellow color
                    (-force_x, -force_y),  # Particles go opposite of force direction
                    count=3,  # Number of particles
                    speed=100,  # Speed
                    size_range=(2, 4),  # Size range
                    lifetime_range=(0.2, 0.5),  # Lifetime range
                    glow=True  # Enable glow effect
                )
                
                # Drain energy based on force magnitude
                self.energy -= FORCE_COST * self.force_magnitude
            
        # Regenerate energy when not applying force
        if not self.applying_force and self.energy < ENERGY_MAX:
            # Apply faster energy regeneration in early levels for gentler learning curve
            if self.current_level <= 3:
                energy_regen_multiplier = 1.5  # Faster energy regen in early levels
            else:
                energy_regen_multiplier = 1.0
                
            self.energy += ENERGY_REGEN * effective_dt * energy_regen_multiplier
        
        # Apply energy drain (for higher levels)
        if self.energy_drain > 0:
            self.energy = max(0, self.energy - self.energy_drain * effective_dt)
        
        # Update ball physics
        self.ball.update(effective_dt)
        
        # Update tutorial elements
        if hasattr(self, 'level_data') and 'tutorial_elements' in self.level_data:
            for element_data in self.level_data.get('tutorial_elements', []):
                # Create TutorialElement to update it
                element = TutorialElement(element_data['type'], element_data)
                element.update(effective_dt)
        
        # Update other entities
        # Walls are static and don't need to be updated
        
        for target in self.targets:
            target.update(effective_dt)
            
        # Surfaces are static and don't need to be updated
            
        for powerup in self.powerups:
            powerup.update(effective_dt)

        # Update new entity types
        for gravity_well in self.gravity_wells:
            gravity_well.update(effective_dt)
            gravity_well.apply_force(self.ball)
            
        for bounce_pad in self.bounce_pads:
            bounce_pad.update(effective_dt)
            if bounce_pad.check_collision(self.ball):
                self._apply_screen_shake(0.5)
                play_sound("bounce", 0.3)
                
        # Handle teleporter collisions and update
        for teleporter in self.teleporters:
            teleporter.update(effective_dt)
            if teleporter.check_collision(self.ball):
                teleporter.teleport_ball(self.ball)
                play_sound("teleport", 0.65)  # Increased from 0.5
                self._apply_screen_shake(0.7)
        
        # Update powerup effects
        for powerup in self.powerups:
            result = powerup.handle_collision(self.ball)
            if result:
                # Powerup was collected
                play_sound("powerup", 0.7)  # Added volume parameter
                
                # Apply powerup effect
                self._apply_powerup(result)
                
                # Add particles at powerup position
                if self.settings["particles"]:
                    self._create_powerup_effect(powerup.x, powerup.y, powerup.color)
        
        # Check collisions
        self._check_collisions()
        
        # Update remaining time - do this before level completion check
        self.time_remaining -= effective_dt
        
        # Check if level is failed
        if self.time_remaining <= 0:
            self._level_failed()
            return  # Stop updating once level is failed
        
        # Check if level is complete
        if self._check_level_complete():
            self._level_complete()
            return  # Stop updating once level is complete
    
    def _check_collisions(self) -> None:
        """Check for collisions between the ball and other objects."""
        # Check for collisions with targets
        for target in self.targets[:]:  # Use copy to safely remove
            if target.handle_collision(self.ball):
                # Target was hit
                play_sound("powerup", 0.8)  # Increased volume
                
                # Update target hit count for mastery system
                self.target_stats["hit"] += 1
                
                # Add score
                self.score += target.points
    
    def _apply_powerup(self, powerup_data: Dict[str, Any]) -> None:
        """Apply the effect of a collected powerup."""
        powerup_type = powerup_data["type"]
        value = powerup_data["value"]
        
        if powerup_type == "energy":
            # Make energy powerups more satisfying
            self.energy = min(ENERGY_MAX, self.energy + value)
            self.toasts.append(Toast(f"+{value} Energy!", duration=1.5, position="top"))
            
            # Add temporary boost effect
            self.ball.pulse_timer = 0  # Reset pulse
            self.ball.pulse_amount = 5  # Larger pulse effect
            
        elif powerup_type == "speed":
            # Actually implement speed boost
            self.ball.vel_x *= 1.5
            self.ball.vel_y *= 1.5
            self.toasts.append(Toast("Speed Boost!", duration=1.5, position="top"))
            
        elif powerup_type == "time":
            # Add time
            self.time_remaining += value
            self.toasts.append(Toast(f"+{value} Seconds", duration=1.5, position="top"))
    
    def _create_powerup_effect(self, x: float, y: float, color: Tuple[int, int, int]) -> None:
        """Create an enhanced visual effect when collecting a powerup."""
        # Add spiral burst effect for a more satisfying visual, but more subtle
        self.particle_system.add_spiral_burst(
            x, y,
            color=color,
            spiral_count=2,  # Reduced from 3
            particles_per_spiral=7,  # Reduced from 10
            radius=50,  # Reduced from 70
            lifetime=0.9  # Reduced from 1.2
        )
        
        # Also add the original energy burst for extra effect, but with fewer particles
        self.particle_system.add_energy_burst(
            x, y,
            color=color,
            count=20,  # Reduced count for subtlety
            speed=120  # Reduced speed
        )
        
        # Apply milder screen shake for better feedback
        if self.settings["screen_shake"]:
            self._apply_screen_shake(3.5)  # Reduced from 5
    
    def _check_level_complete(self) -> bool:
        """Check if all required targets have been hit."""
        for target in self.targets:
            if target.required and not target.hit:
                return False
        return True
    
    def _level_complete(self) -> None:
        """Handle level completion."""
        # Play level complete sound
        play_sound("level_complete", 1.0)
        
        # Calculate and store completion time
        self.completion_time = self._get_level_time_limit(self.current_level) - self.time_remaining
        
        # Calculate stars based on time remaining
        stars = self._calculate_stars(self.time_remaining)
        
        # Calculate performance scores
        performance_scores = self._calculate_performance_score()
        
        # Update mastery levels based on performance
        self._update_mastery_levels(performance_scores)
        
        # Update level data
        level_key = str(self.current_level)
        
        # Update best time if this is better
        if level_key not in self.levels_data["times"] or self.completion_time < self.levels_data["times"][level_key]:
            self.levels_data["times"][level_key] = self.completion_time
        
        # Update stars if this is better
        if level_key not in self.levels_data["stars"] or stars > self.levels_data["stars"][level_key]:
            self.levels_data["stars"][level_key] = stars
        
        # Always unlock the next level regardless of stars
        next_level = self.current_level + 1
        if next_level > self.levels_data["unlocked"]:
            self.levels_data["unlocked"] = next_level
            self.toasts.append(Toast(f"Level {next_level} unlocked!", duration=2.0))
        
        # Save level data
        self._save_levels_data()
        
        # Add celebratory particles
        if self.settings["particles"]:
            # Add multiple explosions around the screen
            for _ in range(10):
                x = random.randint(50, WIDTH - 50)
                y = random.randint(50, HEIGHT - 50)
                color = (
                    random.randint(200, 255),
                    random.randint(200, 255),
                    random.randint(50, 100)
                )
                self.particle_system.add_explosion(
                    x, y, color,
                    count=20,
                    speed=150,
                    size_range=(3, 8),
                    lifetime_range=(0.5, 1.5),
                    glow=True
                )
            
            # Add special star-shaped particles for each star earned
            for i in range(stars):
                delay = i * 0.3  # Stagger the star appearances
                # We'll simulate this with a burst at different positions
                x = WIDTH // 2 - 100 + i * 100
                y = HEIGHT // 2 - 50
                self.particle_system.add_energy_burst(
                    x, y,
                    color=(255, 255, 0),  # Gold
                    count=40,
                    speed=200
                )
        
        # Change to level complete state
        self._change_state(GameState.LEVEL_COMPLETE)
    
    def _level_failed(self) -> None:
        """Handle level failure due to time running out."""
        # Play failure sound
        play_sound("game_over", 0.5)
        
        # Add failure particles
        if self.settings["particles"]:
            # Add explosion at ball position
            self.particle_system.add_explosion(
                self.ball.x, self.ball.y,
                (255, 0, 0),  # Red color
                100,  # Particle count
                (50, 150),  # Speed range
                (2, 5),  # Size range
                (0.5, 1.5),  # Lifetime range
                glow=True  # Enable glow
            )
            
            # Add screen shake
            self._apply_screen_shake(5.0)
        
        # Show failure message
        self.toasts.append(
            Toast("Time's up! Level failed.", 3.0, self.regular_font)
        )
        
        # Change state to level select after a delay
        pygame.time.set_timer(pygame.USEREVENT, 3000)  # 3 second delay
        self.pending_state_change = GameState.LEVEL_SELECT
    
    def _calculate_stars(self, completion_time: float) -> int:
        """Calculate stars based on completion time."""
        # For MVP, simple calculation:
        # 3 stars if < 50% of time limit used
        # 2 stars if < 70% of time limit used
        # 1 star otherwise
        time_limit = self._get_level_time_limit(self.current_level)
        
        if completion_time < time_limit * 0.5:
            return 3
        elif completion_time < time_limit * 0.7:
            return 2
        else:
            return 1
    
    def _get_level_time_limit(self, level_num: int) -> float:
        """Get the time limit for a level."""
        # Generate level data to get time limit
        level_data = generate_level(level_num)
        return level_data.get("time_limit", 60)
    
    def _apply_screen_shake(self, intensity: float) -> None:
        """Apply a screen shake effect."""
        if not self.settings["screen_shake"]:
            return
            
        # Use the enhanced particle system's screen shake effect
        self.particle_system.add_screen_shake_particles(intensity * 1.25)  # Increased intensity
        
        # Store the shake intensity for the draw method with slightly longer duration
        self.screen_shake = intensity * 1.3  # Increased intensity and duration

    def _draw_game(self) -> None:
        """Draw the gameplay state."""
        # Create a temporary surface for the game (allows for screen shake)
        game_surface = pygame.Surface((WIDTH, HEIGHT))
        game_surface.fill(self.background_color)
        
        # Draw the grid on the game surface
        self._draw_grid()
        
        # Draw all entities on the game surface
        for wall in self.walls:
            wall.draw(game_surface)
            
        for surface in self.surfaces:
            surface.draw(game_surface)
            
        for target in self.targets:
            target.draw(game_surface)
            
        for powerup in self.powerups:
            powerup.draw(game_surface)
            
        for gravity_well in self.gravity_wells:
            gravity_well.draw(game_surface)
            
        for teleporter in self.teleporters:
            teleporter.draw(game_surface)
            
        for bounce_pad in self.bounce_pads:
            bounce_pad.draw(game_surface)
        
        # Draw tutorial elements if present
        self._draw_tutorial_elements(game_surface)
        
        # Draw trajectory preview line if applying force
        if self.applying_force and self.force_magnitude > 0:
            # Calculate endpoint of trajectory
            line_length = min(200, self.force_magnitude * 40)  # Longer line
            norm_x, norm_y = self.force_direction
            magnitude = math.sqrt(norm_x**2 + norm_y**2)
            if magnitude > 0:
                norm_x /= magnitude
                norm_y /= magnitude
                
            # Draw thicker initial line segment
            segment_length = line_length / 12  # 12 segments
            pygame.draw.line(
                game_surface,
                (255, 255, 0),  # Bright yellow
                (int(self.ball.x), int(self.ball.y)),
                (int(self.ball.x + norm_x * segment_length * 2), int(self.ball.y + norm_y * segment_length * 2)),
                max(3, int(self.force_magnitude * 1.4))  # Reduced from max(4, int(self.force_magnitude * 2))
            )
            
            # Draw dotted trajectory line with segments
            segments = 12  # Number of segments
            segment_length = line_length / segments
            
            for i in range(segments):
                # Calculate segment start and end
                start_x = self.ball.x + norm_x * i * segment_length
                start_y = self.ball.y + norm_y * i * segment_length
                end_x = self.ball.x + norm_x * (i + 0.7) * segment_length  # Leave gap between segments
                end_y = self.ball.y + norm_y * (i + 0.7) * segment_length
                
                # Gradient color from yellow to red
                color_r = min(255, 200 + int(55 * i / segments))
                color_g = max(0, 255 - int(255 * i / segments))
                color_b = 0
                
                # Draw segment
                pygame.draw.line(
                    game_surface,
                    (color_r, color_g, color_b),
                    (int(start_x), int(start_y)),
                    (int(end_x), int(end_y)),
                    max(1, 3 - i // 4)  # Thicker at start, thinner at end
                )
            
            # Draw arrow at the end of the trajectory
            end_x = self.ball.x + norm_x * line_length
            end_y = self.ball.y + norm_y * line_length
            
            # Arrow head
            arrow_size = 10
            arrow_angle1 = math.atan2(norm_y, norm_x) + math.radians(140)
            arrow_angle2 = math.atan2(norm_y, norm_x) + math.radians(220)
            
            arr_x1 = end_x + math.cos(arrow_angle1) * arrow_size
            arr_y1 = end_y + math.sin(arrow_angle1) * arrow_size
            arr_x2 = end_x + math.cos(arrow_angle2) * arrow_size
            arr_y2 = end_y + math.sin(arrow_angle2) * arrow_size
            
            # Draw arrow head
            pygame.draw.polygon(
                game_surface,
                (255, 50, 0),  # Red color for arrow
                [(int(end_x), int(end_y)), (int(arr_x1), int(arr_y1)), (int(arr_x2), int(arr_y2))]
            )
        
        # Draw the ball
        self.ball.draw(game_surface)
        
        # Draw the particle system
        self.particle_system.draw(game_surface)
        
        # Draw the temporary surface with shake offset
        shake_offset_x = 0
        shake_offset_y = 0
        
        if hasattr(self, 'screen_shake') and self.screen_shake > 0:
            # Calculate random shake offset
            shake_offset_x = random.uniform(-self.screen_shake, self.screen_shake)
            shake_offset_y = random.uniform(-self.screen_shake, self.screen_shake)
            
            # Reduce shake intensity for next frame
            self.screen_shake *= 0.9
            if self.screen_shake < 0.5:
                self.screen_shake = 0
        
        self.screen.blit(game_surface, (shake_offset_x, shake_offset_y))
        
        # Draw UI elements directly on the screen (no shake)
        self._draw_hud()

    def _draw_hud(self) -> None:
        """Draw game UI elements."""
        # Draw energy bar
        energy_bar_width = 200
        energy_bar_height = 20
        energy_bar_x = 20
        energy_bar_y = 20
        
        # Draw background with a subtle gradient
        for i in range(energy_bar_width):
            gradient_color = (
                max(20, min(50, 30 + int(20 * i / energy_bar_width))),
                max(20, min(50, 30 + int(20 * i / energy_bar_width))),
                max(20, min(50, 30 + int(20 * i / energy_bar_width)))
            )
            pygame.draw.line(
                self.screen,
                gradient_color,
                (energy_bar_x + i, energy_bar_y),
                (energy_bar_x + i, energy_bar_y + energy_bar_height)
            )
        
        # Draw filled portion
        energy_ratio = self.energy / ENERGY_MAX
        
        # Enhanced pulse effect when energy is low
        pulse_effect = 0
        if energy_ratio < 0.3:
            # Faster, more dramatic pulse when energy is very low
            pulse_speed = 0.015 if energy_ratio < 0.15 else 0.01
            pulse_intensity = 0.3 if energy_ratio < 0.15 else 0.2
            pulse_effect = math.sin(pygame.time.get_ticks() * pulse_speed) * pulse_intensity
            energy_ratio = max(0.05, energy_ratio + pulse_effect)  # Add pulsing effect
        
        fill_width = int(energy_bar_width * energy_ratio)
        
        # Create a more dynamic gradient for the filled portion
        for i in range(fill_width):
            # Position ratio within the filled area
            pos_ratio = i / energy_bar_width if energy_bar_width > 0 else 0
            
            # Enhanced gradient color calculation
            if energy_ratio > 0.6:  # High energy: blue-green to green
                r = int(max(0, min(255, 0 + (pos_ratio * 2) * 255)))
                g = 255
                b = int(max(0, min(255, 150 * (1 - pos_ratio * 2))))
            elif energy_ratio > 0.3:  # Medium energy: green to yellow-orange
                r = int(max(0, min(255, 100 + (pos_ratio * 3) * 155)))
                g = 255
                b = 0
            else:  # Low energy: orange to red with pulsing
                pulse_mod = abs(pulse_effect) * 255 if pulse_effect != 0 else 0
                r = 255
                g = int(max(0, min(255, 150 * pos_ratio * 2 - pulse_mod)))
                b = int(max(0, min(255, pulse_mod * 0.7)))  # Add some blue during pulse
            
            # Draw vertical line segment with calculated color
            pygame.draw.line(
                self.screen,
                (r, g, b),
                (energy_bar_x + i, energy_bar_y),
                (energy_bar_x + i, energy_bar_y + energy_bar_height)
            )
        
        # Add a highlight effect at the top of the bar
        if fill_width > 5:
            highlight_height = energy_bar_height // 4
            for i in range(fill_width - 2):
                alpha = 100 - int(90 * i / fill_width)
                highlight_color = (255, 255, 255, alpha)
                pygame.draw.line(
                    self.screen,
                    highlight_color,
                    (energy_bar_x + 1 + i, energy_bar_y + 1),
                    (energy_bar_x + 1 + i, energy_bar_y + highlight_height)
                )
        
        # Draw border with a slight glow effect when energy is low
        border_color = WHITE
        border_width = 2
        if energy_ratio < 0.3 and pulse_effect > 0.1:
            border_color = (255, 100, 100)  # Reddish glow
            border_width = 3
        
        pygame.draw.rect(
            self.screen,
            border_color,
            (energy_bar_x, energy_bar_y, energy_bar_width, energy_bar_height),
            border_width
        )
        
        # Draw energy label
        energy_text = self.small_font.render(f"Energy: {int(self.energy)}", True, WHITE)
        self.screen.blit(energy_text, (energy_bar_x + 10, energy_bar_y + energy_bar_height + 5))
        
        # Draw time remaining
        time_text = self.regular_font.render(f"Time: {int(self.time_remaining)}", True, WHITE)
        time_rect = time_text.get_rect(center=(WIDTH // 2, 30))
        self.screen.blit(time_text, time_rect)
        
        # Draw score
        score_text = self.regular_font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(topright=(WIDTH - 20, 20))
        self.screen.blit(score_text, score_rect)
        
        # Draw level number
        level_text = self.small_font.render(f"Level {self.current_level}", True, WHITE)
        level_rect = level_text.get_rect(topright=(WIDTH - 20, 60))
        self.screen.blit(level_text, level_rect)

    def _setup_pause_menu(self) -> None:
        """Set up the pause menu."""
        # Create pause menu buttons
        self.buttons["pause"] = {}
        
        center_x = WIDTH // 2
        button_width = 200
        button_height = 50
        button_spacing = 60
        
        # Calculate starting y position to center the buttons vertically
        num_buttons = 3  # Resume, Restart, Quit
        total_height = num_buttons * button_height + (num_buttons - 1) * (button_spacing - button_height)
        start_y = (HEIGHT - total_height) // 2
        
        # Resume button
        self.buttons["pause"]["resume"] = Button(
            center_x, start_y,
            button_width, button_height,
            "Resume",
            self.regular_font,
            callback=lambda: self._change_state(GameState.GAME)
        )
        
        # Restart button
        self.buttons["pause"]["restart"] = Button(
            center_x, start_y + button_spacing,
            button_width, button_height,
            "Restart Level",
            self.regular_font,
            callback=lambda: self._setup_level(self.current_level)
        )
        
        # Quit button
        self.buttons["pause"]["quit"] = Button(
            center_x, start_y + 2 * button_spacing,
            button_width, button_height,
            "Quit to Menu",
            self.regular_font,
            callback=lambda: self._change_state(GameState.MAIN_MENU)
        )
    
    def _process_pause_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], 
                              mouse_pressed: Tuple[bool, bool, bool]) -> None:
        """Process events for the pause menu."""
        # Update all buttons with current mouse state
        for button in self.buttons["pause"].values():
            button.update(mouse_pos, mouse_pressed)
            
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == self.settings["controls"]["pause"]:
                self._change_state(GameState.GAME)
    
    def _update_pause_menu(self) -> None:
        """Update the pause menu."""
        # No updates needed for static pause menu
        pass
    
    def _draw_pause_menu(self) -> None:
        """Draw the pause menu."""
        # First draw the game (darkened)
        self._draw_game()
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        
        # Draw title
        title_text = self.subtitle_font.render("PAUSED", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw buttons
        for button in self.buttons["pause"].values():
            button.draw(self.screen)
            
    def _setup_level_complete(self) -> None:
        """Set up the level complete screen."""
        # Create level complete buttons
        self.buttons["level_complete"] = {}
        
        center_x = WIDTH // 2
        button_width = 200
        button_height = 50
        button_spacing = 60
        
        # Add buttons at the bottom of the screen
        button_y_start = HEIGHT - 150
        
        # Next level button
        next_level = self.current_level + 1
        next_level_unlocked = next_level <= self.levels_data["unlocked"]
        
        self.buttons["level_complete"]["next"] = Button(
            center_x - button_width/2 - 10, button_y_start,
            button_width, button_height,
            "Next Level",
            self.regular_font,
            callback=lambda: self._start_level(next_level)
        )
        
        # Disable if next level is locked
        self.buttons["level_complete"]["next"].disabled = not next_level_unlocked
        
        # Replay button
        self.buttons["level_complete"]["replay"] = Button(
            center_x + button_width/2 + 10, button_y_start,
            button_width, button_height,
            "Replay Level",
            self.regular_font,
            callback=lambda: self._start_level(self.current_level)
        )
        
        # Menu button
        self.buttons["level_complete"]["menu"] = Button(
            center_x, button_y_start + button_spacing,
            button_width, button_height,
            "Main Menu",
            self.regular_font,
            callback=lambda: self._change_state(GameState.MAIN_MENU)
        )
    
    def _process_level_complete_events(self, event: pygame.event.Event, mouse_pos: Tuple[int, int], 
                                       mouse_pressed: Tuple[bool, bool, bool]) -> None:
        """Process events for the level complete screen."""
        # Update all buttons with current mouse state
        for button in self.buttons["level_complete"].values():
            button.update(mouse_pos, mouse_pressed)
            
        # Handle keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._change_state(GameState.MAIN_MENU)
            elif event.key == pygame.K_RETURN:
                # Start next level if unlocked
                next_level = self.current_level + 1
                if next_level <= self.levels_data["unlocked"]:
                    self._start_level(next_level)
    
    def _update_level_complete(self) -> None:
        """Update the level complete screen."""
        # Add victory particles
        if random.random() < 0.1 and self.settings["particles"]:
            # Random position at top of screen
            x = random.randint(WIDTH//4, 3*WIDTH//4)
            y = random.randint(-20, 20)
            
            # Random color
            colors = [YELLOW, GREEN, BLUE, PURPLE, (255, 165, 0)]
            color = random.choice(colors)
            
            # Add particle
            vel_x = random.uniform(-20, 20)
            vel_y = random.uniform(50, 100)
            size = random.uniform(2, 5)
            lifetime = random.uniform(1, 2)
            gravity = 20
            
            self.particle_system.add_particle(x, y, vel_x, vel_y, color, size, lifetime, gravity)

    def _draw_level_complete(self) -> None:
        """Draw the level complete screen."""
        # Draw background grid
        self._draw_grid()
        
        # Draw title
        title_text = self.title_font.render("LEVEL COMPLETE!", True, GREEN)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Draw level number
        level_text = self.subtitle_font.render(f"Level {self.current_level}", True, WHITE)
        level_rect = level_text.get_rect(center=(WIDTH//2, 160))
        self.screen.blit(level_text, level_rect)
        
        # Draw stars
        stars = self.levels_data["stars"].get(str(self.current_level), 0)
        self._draw_stars(WIDTH//2, 220, stars, 40)
        
        # Draw score
        score_text = self.regular_font.render(f"Score: {self.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH//2, 280))
        self.screen.blit(score_text, score_rect)
        
        # Draw time - use the stored completion time
        time_text = self.regular_font.render(f"Time: {self.completion_time:.2f}s", True, WHITE)
        time_rect = time_text.get_rect(center=(WIDTH//2, 320))
        self.screen.blit(time_text, time_rect)
        
        # Draw particles
        self.particle_system.draw(self.screen)
        
        # Draw buttons
        for button in self.buttons["level_complete"].values():
            button.draw(self.screen)
    
    def _draw_stars(self, x: int, y: int, count: int, size: int) -> None:
        """Draw stars for level completion."""
        # Draw 3 stars (filled based on count)
        for i in range(3):
            # Calculate star position
            star_x = x + (i - 1) * size * 2
            
            # Star color (yellow if earned, gray otherwise)
            color = YELLOW if i < count else (70, 70, 70)
            
            # Draw star
            self._draw_star(star_x, y, size, color)
    
    def _draw_star(self, x: int, y: int, size: int, color: Tuple[int, int, int]) -> None:
        """Draw a single star."""
        # Calculate star points
        points = []
        
        # Main points (5 outer points of the star)
        for i in range(5):
            # Outer point
            angle = math.pi/2 + i * 2*math.pi/5
            px = x + size * math.cos(angle)
            py = y - size * math.sin(angle)
            points.append((px, py))
            
            # Inner point
            angle += math.pi/5
            px = x + size/2 * math.cos(angle)
            py = y - size/2 * math.sin(angle)
            points.append((px, py))
        
        # Draw the star
        pygame.draw.polygon(self.screen, color, points)

    def _calculate_force(self, keys, mouse_pressed, mouse_pos) -> Tuple[float, float]:
        """Calculate force to apply to the ball based on input."""
        force_x = 0
        force_y = 0
        old_direction = (force_x, force_y)
        
        # Calculate force direction
        if keys[self.settings["controls"]["up"]]:
            force_y = -1
        if keys[self.settings["controls"]["down"]]:
            force_y = 1
        if keys[self.settings["controls"]["left"]]:
            force_x = -1
        if keys[self.settings["controls"]["right"]]:
            force_x = 1
            
        # Calculate force direction change for precision tracking
        new_direction = (force_x, force_y)
        if old_direction != (0, 0) and new_direction != (0, 0) and old_direction != new_direction:
            # Calculate dot product to measure direction similarity
            dot_product = old_direction[0] * new_direction[0] + old_direction[1] * new_direction[1]
            # Normalize to get value between -1 and 1
            magnitude1 = math.sqrt(old_direction[0]**2 + old_direction[1]**2)
            magnitude2 = math.sqrt(new_direction[0]**2 + new_direction[1]**2)
            if magnitude1 > 0 and magnitude2 > 0:
                similarity = dot_product / (magnitude1 * magnitude2)
                self.precision_moves.append(similarity)
                # Keep precision moves list at reasonable size
                if len(self.precision_moves) > 50:
                    self.precision_moves.pop(0)
            
        # Normalize diagonal movement
        if force_x != 0 and force_y != 0:
            force_x /= 1.414  # sqrt(2)
            force_y /= 1.414
            
        # Apply force scale
        force_scale = 0.5
        force_x *= force_scale
        force_y *= force_scale
        
        return force_x, force_y

    def _draw_tutorial_elements(self, surface):
        """Draw tutorial elements like arrows and hints."""
        # Check if we have tutorial elements
        if hasattr(self, 'level_data') and self.level_data.get('tutorial_elements'):
            for element_data in self.level_data['tutorial_elements']:
                # Create a TutorialElement instance and draw it
                element = TutorialElement(element_data['type'], element_data)
                element.draw(surface, self.regular_font)
            
            # Draw hint text if present
            if self.level_data.get('hint'):
                hint_text = self.level_data['hint']
                text_surface = self.small_font.render(hint_text, True, (200, 200, 200))
                surface.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, HEIGHT - 50))

    def run(self) -> None:
        """Run the game loop."""
        # Start the game
        self._change_state(GameState.MAIN_MENU)
        
        # Main game loop
        running = True
        while running:
            # Process events
            running = self.process_events()
            
            # Update game
            self.update()
            
            # Draw game
            self.draw()
            
            # Control frame rate
            self.clock.tick(60)
        
        # Save settings and level data when quitting
        self._save_settings()
        self._save_levels_data()
        
        # Quit pygame
        pygame.quit()

    def _calculate_performance_score(self) -> Dict[str, float]:
        """
        Calculate player performance scores across multiple metrics.
        Returns a dictionary of performance metrics normalized between 0.0 and 1.0.
        """
        # Calculate time efficiency
        time_limit = self._get_level_time_limit(self.current_level)
        completion_percent = (time_limit - self.time_remaining) / time_limit
        time_score = min(1.0, max(0.0, 1.0 - completion_percent * 0.8))
        
        # Calculate energy efficiency
        energy_efficiency = 1.0 - (self.energy / ENERGY_MAX)
        energy_score = min(1.0, max(0.0, energy_efficiency * 0.7))
        
        # Calculate precision score based on movement direction changes
        # A good player makes deliberate, controlled movements with few direction changes
        if len(self.precision_moves) > 0:
            unnecessary_changes = sum(1 for change in self.precision_moves if change < 0.3)
            precision_score = max(0.0, 1.0 - (unnecessary_changes / max(1, len(self.precision_moves))))
        else:
            precision_score = 0.0
            
        # Calculate target hit ratio
        if self.target_stats["total"] > 0:
            target_score = self.target_stats["hit"] / self.target_stats["total"]
        else:
            target_score = 0.0
            
        return {
            "time": time_score,
            "energy": energy_score,
            "precision": precision_score,
            "targets": target_score
        }

    def _update_mastery_levels(self, performance_scores: Dict[str, float]) -> None:
        """
        Update mastery levels based on performance scores.
        """
        # Update mastery data with exponential moving average
        alpha = 0.3  # Weight for new score (0-1)
        for metric, score in performance_scores.items():
            self.mastery_data[metric] = (alpha * score) + ((1 - alpha) * self.mastery_data[metric])
        
        # Update mastery levels based on thresholds
        for metric in MASTERY_METRICS:
            score = self.mastery_data[metric]
            thresholds = MASTERY_THRESHOLDS[metric]
            
            # Determine level based on thresholds
            level = 0
            for i, threshold in enumerate(thresholds):
                if score >= threshold:
                    level = i + 1
            
            # If player reached a new mastery level
            if level > self.mastery_levels[metric]:
                self.mastery_levels[metric] = level
                # Activate reward for this metric
                self.active_rewards[metric] = MASTERY_REWARDS[metric][level-1]
                # Show toast notification
                metric_name = metric.capitalize()
                level_name = MASTERY_LEVELS[level-1].capitalize()
                self.toasts.append(Toast(f"{metric_name} Mastery: {level_name}!", duration=2.5, text_color=YELLOW))
                
        # Save mastery data with level data
        self._save_mastery_data()

    def _save_mastery_data(self) -> None:
        """Save mastery data to the levels file."""
        if "mastery" not in self.levels_data:
            self.levels_data["mastery"] = {}
            
        self.levels_data["mastery"] = {
            "data": self.mastery_data,
            "levels": self.mastery_levels,
            "rewards": self.active_rewards
        }
        
        self._save_levels_data()

    def _update_ball_visual_effects(self) -> None:
        """Update ball visual effects based on active mastery rewards."""
        if not self.ball:
            return
            
        # Apply time mastery rewards (trails)
        time_reward = self.active_rewards.get("time")
        if time_reward:
            # Set trail color based on reward
            if time_reward == "blue_trail":
                self.ball.trail_color = BLUE
                self.ball.trail_enabled = True
            elif time_reward == "cyan_trail":
                self.ball.trail_color = CYAN
                self.ball.trail_enabled = True
            elif time_reward == "white_trail":
                self.ball.trail_color = WHITE
                self.ball.trail_enabled = True
            elif time_reward == "rainbow_trail":
                # Rainbow trail cycles through colors
                hue = (pygame.time.get_ticks() % 3000) / 3000
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                self.ball.trail_color = (int(r * 255), int(g * 255), int(b * 255))
                self.ball.trail_enabled = True
        
        # Apply energy mastery rewards (glows)
        energy_reward = self.active_rewards.get("energy")
        if energy_reward:
            # Set glow intensity based on reward
            if energy_reward == "small_glow":
                self.ball.glow_radius = 15
                self.ball.glow_color = (255, 255, 150, 80)
            elif energy_reward == "medium_glow":
                self.ball.glow_radius = 25
                self.ball.glow_color = (255, 255, 150, 100)
            elif energy_reward == "large_glow":
                self.ball.glow_radius = 35
                self.ball.glow_color = (255, 255, 150, 120)
            elif energy_reward == "energy_aura":
                # Pulsing energy aura
                pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
                self.ball.glow_radius = 25 + int(pulse * 15)
                self.ball.glow_color = (255, 255, 100, int(100 + pulse * 50))
        
        # Apply precision mastery rewards (impact sparks)
        precision_reward = self.active_rewards.get("precision")
        if precision_reward:
            self.ball.collision_particle_color = {
                "bronze_spark": (205, 127, 50),
                "silver_spark": (192, 192, 192),
                "gold_spark": (255, 215, 0),
                "diamond_spark": (185, 242, 255)
            }.get(precision_reward, (255, 255, 255))
            
            self.ball.collision_particles_enabled = True
            
        # Apply target hit mastery rewards (pulse effects)
        target_reward = self.active_rewards.get("targets")
        if target_reward:
            # Set pulse color and strength based on reward
            if target_reward == "green_pulse":
                self.ball.pulse_color = GREEN
                self.ball.pulse_strength = 1.5
            elif target_reward == "yellow_pulse":
                self.ball.pulse_color = YELLOW
                self.ball.pulse_strength = 2.0
            elif target_reward == "orange_pulse":
                self.ball.pulse_color = ORANGE
                self.ball.pulse_strength = 2.5
            elif target_reward == "red_pulse":
                self.ball.pulse_color = RED
                self.ball.pulse_strength = 3.0
