import pygame
import sys
import json
import os
import math
import random
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple

# Import managers
from state_manager import StateManager, GameState
from level_manager import LevelManager
from collision_manager import CollisionManager
from ui_manager import UIManager

# Import utils
from utils.constants import WIDTH, HEIGHT, FPS, BLACK, WHITE, RED, GREEN, BLUE, YELLOW, GRID_SIZE, GRID_COLOR, BACKGROUND_COLOR, BOUNDARY_COLOR, BOUNDARY_THICKNESS, DARK_GRAY, GRAY, ENERGY_MAX, FRICTION, ENERGY_REGEN, FORCE_COST
from utils.helpers import normalize_vector, clamp, distance, map_range
from utils.particle import ParticleSystem
from utils.enhanced_particle import EnhancedParticleSystem  # Import enhanced particle system
from utils.floating_text import FloatingText  # Import floating text
from utils.camera import Camera
from utils.screen_shake import ScreenShake

# Import entities - use consolidated entities only
from entities.ball import Ball
from entities.wall import Wall
from entities.target import Target
from entities.surface import Surface
from entities.powerup import PowerUp
from entities.gravity_well import GravityWell
from entities.bounce_pad import BouncePad
from entities.teleporter import Teleporter

# Import UI elements
from ui.button import Button
from ui.slider import Slider
from ui.toast import Toast

class Game:
    def __init__(self):
        """Initialize the game."""
        # Initialize Pygame
        pygame.init()
        pygame.mixer.init()
        
        # Create game window
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | pygame.HWSURFACE)
        pygame.display.set_caption("Inertia Deluxe")
        
        # For alpha effects
        self.alpha_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Initialize fonts
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 18)
        
        # Load logo
        try:
            self.logo = pygame.image.load(os.path.join("assets", "images", "logo.png")).convert_alpha()
        except:
            # Create a fallback text logo if image can't be loaded
            font = pygame.font.Font(None, 72)
            self.logo = font.render("Inertia Deluxe", True, (255, 255, 255))
        
        # Clock and timing
        self.clock = pygame.time.Clock()
        self.dt = 0
        self.fps_counter = 0
        self.fps_timer = 0
        self.current_fps = 0
        
        # Load settings
        self.settings = self._load_settings()
        
        # Create enhanced particle system
        self.particle_system = ParticleSystem()
        
        # Power-up effects
        self.energy = 100
        self.max_energy = 100
        self.time_slow_factor = 1.0
        self.gravity_field_active = False
        self.magnetic_attraction = False
        
        # Create managers without passing self
        self.state_manager = StateManager(GameState.MAIN_MENU)
        self.level_manager = LevelManager()
        self.collision_manager = CollisionManager()
        self.ui_manager = UIManager()
        
        # Set game reference in each manager
        self.state_manager.set_game(self)
        self.level_manager.set_game(self)
        self.collision_manager.set_game(self)
        self.ui_manager.set_game(self)
        
        # Game objects - these should come from level_manager now
        self.ball = None  # Will be set by level_manager
        self.entities = []  # Will be managed by level_manager
        
        # Initialize level properties
        self.level_start_time = 0
        self.level_playable = False  # Flag to indicate if level can be completed
        self.level_playable_delay = 3.0  # Seconds before level can be completed
        self.level_complete = False
        
        # Scoring and level stats
        self.score = 0
        self.energy_used = 0
        self.moves_made = 0
        self.completion_time = 0
        self.level_stars = 0      # Stars earned in current level
        self.level_completion_time = 0  # Time taken to complete the level
        
        # Camera system for larger playing field
        self.camera = Camera(WIDTH, HEIGHT)
        self.camera.set_deadzone(0.2, 0.2)  # 20% of screen size deadzone
        
        # World dimensions
        self.world_width = WIDTH * 3  # Larger world than screen
        self.world_height = HEIGHT * 3  # Larger world than screen
        
        # Keyboard control states
        self.key_states = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False,
            pygame.K_SPACE: False  # For braking
        }
        
        # Force settings
        self.force_amount = 500.0  # Base force amount per second
        self.braking_force = 0.8   # Braking force multiplier
        
        # Aiming properties (for mouse control - now optional)
        self.use_mouse_controls = False  # Set to False to use keyboard controls
        self.aiming = False
        self.aim_start_pos = None
        self.aim_current_pos = None
        self.aim_end_pos = None
        
        # Debug flags
        self.show_debug = False
        
        # Screen shake effect
        self.screen_shake_amount = 0
        
        # Force application
        self.applying_force = False
        self.force_direction = [0, 0]
        self.force_magnitude = 0
        
        # Energy system
        self.energy_regen_rate = ENERGY_REGEN  # Energy regeneration per second
        
        # Floating text system
        self.floating_texts = []
        
        # Power-up tracking
        self.active_power_ups = []
        
        # Time limit for level
        self.time_limit = 60.0  # Default time limit in seconds
        self.high_score = self._load_high_score()
        
        # Set up the initial game state
        self._setup_main_menu()
        
        # No longer load the demo level automatically
        # self._start_demo_level()
    
    def _load_settings(self):
        """Load settings from file or use defaults."""
        # Default settings
        settings = {
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
                "pause": pygame.K_ESCAPE,
                "reset": pygame.K_r
            }
        }
        
        # Try to load from file
        try:
            if os.path.exists("data/settings.json"):
                with open("data/settings.json", "r") as f:
                    loaded = json.load(f)
                    for key, value in loaded.items():
                        settings[key] = value
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return settings
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/settings.json", "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def _change_state(self, new_state):
        """Change the game state."""
        self.previous_state = self.state_manager.current_state
        self.state_manager.change_state(new_state)
        
        # Set up new state
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
    
    def _setup_level(self, level_num):
        """Set up a level based on its data."""
        # Clear existing entities
        self.entities = []
        
        # Reset camera
        self.camera.reset()
        
        # Store current level
        self.level_manager.current_level = level_num
        
        # Get level data - try both the original level_num and as a string
        level = None
        
        # First try with the original format
        level = self.level_manager.levels_data.get(level_num, None)
        
        # If not found and level_num is an integer, try as a string
        if level is None and isinstance(level_num, int):
            level = self.level_manager.levels_data.get(str(level_num), None)
        
        # If not found and level_num is a string but could be an integer, try as an integer
        if level is None and isinstance(level_num, str) and level_num.isdigit():
            level = self.level_manager.levels_data.get(int(level_num), None)
        
        if not level:
            print(f"Error: Level {level_num} not found")
            return
            
        # Clear active power-ups
        self.active_power_ups = []
        
        # Reset time slow factor
        self.time_slow_factor = 1.0
        
        # Create ball using EnhancedBall
        ball_data = level.get("ball", {"x": 100, "y": 100})
        self.ball = EnhancedBall(ball_data.get("x", 100), ball_data.get("y", 100))
        self.ball.game = self  # Give ball a reference to the game
        
        # Create walls using EnhancedWall
        for wall_data in level.get("walls", []):
            wall = EnhancedWall(
                wall_data.get("x", 0),
                wall_data.get("y", 0),
                wall_data.get("width", 100),
                wall_data.get("height", 100)
            )
            self.entities.append(wall)
        
        # Create targets using EnhancedTarget
        for target_data in level.get("targets", []):
            target = EnhancedTarget(
                target_data.get("x", 0),
                target_data.get("y", 0),
                target_data.get("radius", 20),
                target_data.get("points", 100),
                target_data.get("required", True)
            )
            target.game = self  # Give target a reference to the game
            self.entities.append(target)
        
        # Create power-ups using EnhancedPowerUp
        for powerup_data in level.get("powerups", []):
            powerup = EnhancedPowerUp(
                powerup_data.get("x", 0),
                powerup_data.get("y", 0),
                powerup_data.get("type", "energy"),
                self  # Pass game reference
            )
            self.entities.append(powerup)
        
        # Create surfaces
        for surface_data in level.get("surfaces", []):
            surface = Surface(
                surface_data.get("x", 0),
                surface_data.get("y", 0),
                surface_data.get("width", 100),
                surface_data.get("height", 100),
                surface_data.get("friction", 0.95),
                surface_data.get("color", (150, 150, 150))
            )
            self.entities.append(surface)
        
        # Create gravity wells
        for gw_data in level.get("gravity_wells", []):
            gw = GravityWell(
                gw_data.get("x", 0),
                gw_data.get("y", 0),
                gw_data.get("radius", 100),
                gw_data.get("strength", 1.0),
                gw_data.get("repel", False)
            )
            self.entities.append(gw)
            
        # Create bounce pads
        for bp_data in level.get("bounce_pads", []):
            bp = BouncePad(
                bp_data.get("x", 0),
                bp_data.get("y", 0),
                bp_data.get("width", 100),
                bp_data.get("height", 20),
                bp_data.get("strength", 1.5),
                bp_data.get("angle", 90)
            )
            self.entities.append(bp)
            
        # Create teleporters
        for tp_data in level.get("teleporters", []):
            tp = Teleporter(
                tp_data.get("x", 0),
                tp_data.get("y", 0),
                tp_data.get("target_x", 0),
                tp_data.get("target_y", 0),
                tp_data.get("radius", 30),
                tp_data.get("color", None)
            )
            self.entities.append(tp)
        
        # Reset energy
        self.energy = ENERGY_MAX
        
        # Reset game state
        self.level_complete = False
        self.level_start_time = pygame.time.get_ticks() / 1000
        
        # Clear floating texts
        self.floating_texts = []
        
        # Clear any active particle effects
        if self.particle_system:
            self.particle_system = EnhancedParticleSystem()
    
    def _setup_main_menu(self):
        """Set up the main menu."""
        self.ui_manager.setup_for_state(GameState.MAIN_MENU)
    
    def _setup_level_select(self):
        """Set up the level select screen."""
        self.ui_manager.setup_for_state(GameState.LEVEL_SELECT)
    
    def _setup_settings(self):
        """Set up the settings screen."""
        self.ui_manager.setup_for_state(GameState.SETTINGS)
    
    def _setup_game(self):
        """Set up the game screen."""
        self.ui_manager.setup_for_state(GameState.GAME)
    
    def _setup_pause_menu(self):
        """Set up the pause menu."""
        self.ui_manager.setup_for_state(GameState.PAUSED)
    
    def _setup_level_complete(self):
        """Set up the level complete screen."""
        self.ui_manager.setup_for_state(GameState.LEVEL_COMPLETE)
    
    def _start_level(self, level_num):
        """Start a new level."""
        # Reset level stats
        self.score = 0
        self.energy_used = 0
        self.moves_made = 0
        self.energy = self.max_energy
        
        # Reset camera
        self.camera.set_target_position((0, 0))
        
        # Store current level
        self.current_level = level_num
        
        # Set up the level
        self.level_manager.setup_level(level_num)
        
        # Set level start time
        self.level_start_time = time.time()
        self.level_playable = False  # Will be set to True after delay
        self.level_complete = False
        
        # Show level start message
        self.ui_manager.add_toast(f"Level {level_num}", 2.0, (0, 200, 255))
    
    def _restart_level(self):
        """Restart the current level."""
        # Reset level stats
        self.energy = self.max_energy
        self.energy_used = 0
        self.moves_made = 0
        self.level_complete = False
        
        # Reset camera
        self.camera.set_target_position((0, 0))
        
        # Restart level through level manager
        current_level = self.level_manager.current_level
        self.level_manager.setup_level(current_level)
        
        # Reset level start time
        self.level_start_time = time.time()
        self.level_playable = False
        
        # Change state to game if not already
        if self.state_manager.current_state != GameState.GAME:
            self.state_manager.change_state(GameState.GAME)
            
        # Add notification
        self.ui_manager.add_toast(f"Level {current_level} Restarted", 2.0, (0, 200, 255))
    
    def _set_sound_volume(self, volume):
        """Set sound volume."""
        self.settings["sound_volume"] = volume
        self._save_settings()
    
    def _set_music_volume(self, volume):
        """Set music volume."""
        self.settings["music_volume"] = volume
        self._save_settings()
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        self.settings["fullscreen"] = not self.settings.get("fullscreen", False)
        
        if self.settings["fullscreen"]:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        
        self._save_settings()
        
        # Update button text
        for element in self.ui_manager.ui_elements:
            if hasattr(element, 'text') and isinstance(element.text, str) and element.text.startswith("Fullscreen:"):
                element.text = f"Fullscreen: {'On' if self.settings['fullscreen'] else 'Off'}"
    
    def _toggle_particles(self):
        """Toggle particle effects."""
        self.settings["particles"] = not self.settings.get("particles", True)
        
        # Update button text
        self.ui_manager.setup_for_state(GameState.SETTINGS)
        
        if not self.settings["particles"]:
            self.particle_system.clear()
        
        self._save_settings()
    
    def _toggle_screen_shake(self):
        """Toggle screen shake effect."""
        self.settings["screen_shake"] = not self.settings.get("screen_shake", True)
        
        # Update button text
        self.ui_manager.setup_for_state(GameState.SETTINGS)
        
        self._save_settings()
    
    def _quit_game(self):
        """Save and quit the game."""
        self._save_settings()
        pygame.quit()
        sys.exit()
    
    def _check_level_complete(self):
        """Check if all required targets are hit."""
        # Safety check - don't complete level if it's not playable yet
        if not self.level_playable:
            return
            
        if self.level_manager.is_level_complete():
            self._complete_level()
    
    def _complete_level(self):
        """Handle level completion."""
        if not self.level_complete:
            # Calculate completion time
            self.completion_time = time.time() - self.level_start_time
            self.level_completion_time = self.completion_time
            
            # Calculate stars based on performance
            stars = self.level_manager.calculate_stars(
                self.level_manager.current_level,
                self.energy,
                self.completion_time
            )
            self.level_stars = stars
            
            # Save progress
            self.level_manager.save_levels_data()
            
            # Get star text representation
            star_text = "★" * stars + "☆" * (3 - stars)
            
            # Create an appropriate message based on star rating
            if stars == 3:
                message = f"Perfect! {star_text}"
                color = (255, 255, 0)  # Gold
            elif stars == 2:
                message = f"Great job! {star_text}"
                color = (200, 200, 0)  # Dark yellow
            elif stars == 1:
                message = f"Level Complete {star_text}"
                color = (150, 150, 150)  # Silver
            else:
                message = f"Try again for stars! {star_text}"
                color = (100, 100, 100)  # Gray
                
            # Show completion message with appropriate styling
            self.ui_manager.add_toast(message, 3.0, color)
            
            # Store level completion time for animations
            self.level_complete_time = time.time()
            
            # Mark level as complete
            self.level_complete = True
            
            # Change state to level complete screen
            self.state_manager.change_state(GameState.LEVEL_COMPLETE)
    
    def _check_collisions(self):
        """Check for collisions between game objects."""
        # Skip if no ball
        if not self.level_manager.ball:
            return
        
        # Skip level completion if level isn't playable yet
        if not self.level_playable:
            # Just do collision detection without level completion
            self.collision_manager.check_collisions(self.level_manager.ball, self.level_manager.level_entities, check_completion=False)
            return
            
        # Use collision manager to handle collisions
        collision_result = self.collision_manager.check_collisions(self.level_manager.ball, self.level_manager.level_entities)
        
        # Process collision results
        if collision_result.get('level_complete', False):
            self._complete_level()
    
    def _apply_force(self):
        """Apply force to the ball based on arrow keys."""
        if not self.level_manager.ball:
            return
        
        # Skip if no force direction
        if not self.applying_force or not any(self.force_direction):
            return
        
        # Apply force
        self.level_manager.ball.apply_force(self.force_direction)
        
        # Reduce energy
        self.energy -= 0.5
        if self.energy < 0:
            self.energy = 0
    
    def process_events(self):
        """Process all events and return False if the user wants to quit."""
        # Reset force direction each frame
        self.force_direction = [0, 0]
        self.applying_force = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Process UI element events
            self.ui_manager.process_events([event])
            
            # Get current state
            current_state = self.state_manager.current_state
            
            if current_state == GameState.GAME:
                # Handle keyboard input for ball movement
                if event.type == pygame.KEYDOWN:
                    if self.level_manager.ball:
                        if event.key == pygame.K_SPACE:
                            self.level_manager.ball.brake()
                            
        # Handle continuous key presses for movement
        if self.state_manager.current_state == GameState.GAME and self.level_manager.ball:
            keys = pygame.key.get_pressed()
            force_x, force_y = 0, 0
            
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                force_y = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                force_y = 1
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                force_x = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                force_x = 1
                
            if force_x != 0 or force_y != 0:
                self.applying_force = True
                self.force_direction = [force_x, force_y]
                
                # Apply force immediately for responsive controls
                self.level_manager.ball.apply_force(force_x, force_y)
                
                # Reduce energy when applying force
                self.energy -= 0.5
                if self.energy < 0:
                    self.energy = 0
        
        # Process mouse for UI
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        for element in self.ui_manager.ui_elements:
            if hasattr(element, 'update'):
                element.update(mouse_pos, mouse_pressed)
        
        return True
    
    def _update_camera(self):
        """Update camera position to follow the ball."""
        if not self.level_manager.get_ball():
            return
 
        # Get the ball's position
        ball_x, ball_y = self.level_manager.get_ball().get_position()
        
        # Ensure camera bounds are set
        if not hasattr(self.camera, 'bounds') or self.camera.bounds is None:
            # Set camera bounds based on world dimensions
            self.camera.set_bounds((0, 0, self.world_width, self.world_height))
        
        # Set target position to ball's position
        self.camera.set_target_position((ball_x, ball_y))
        
        # Update camera
        self.camera.update(self.dt)
    
    def _reset_power_up_effects(self):
        """Reset all power-up effects to default values."""
        if self.ball:
            self.ball.speed_multiplier = 1.0
            self.ball.has_shield = False
        self.time_slow_factor = 1.0
        self.gravity_field_active = False

    def update(self, dt):
        """Update game state and objects."""
        # Update the game clock
        self.dt = dt
        
        # Update FPS counter
        self.fps_counter += 1
        self.fps_timer += dt
        if self.fps_timer >= 1.0:
            self.current_fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = 0
            
        # Update particle system
        if self.particle_system:
            self.particle_system.update(dt)
        
        # Update game depending on state
        current_state = self.state_manager.current_state
        
        if current_state == GameState.GAME:
            # Regenerate energy
            self.energy = min(self.max_energy, self.energy + self.energy_regen_rate * dt)
            
            # Process keyboard controls
            ball = self.level_manager.get_ball()
            if ball and not self.use_mouse_controls:
                self._apply_keyboard_controls(ball, dt)
            
            # Update ball
            if self.level_manager.get_ball():
                self.level_manager.get_ball().update(dt)
            
            # Update entities
            for entity in self.level_manager.get_entities():
                if hasattr(entity, 'update'):
                    entity.update(dt)
            
            # Check collisions
            if self.level_manager.get_ball():
                collision_result = self.collision_manager.check_collisions(
                    self.level_manager.get_ball(), 
                    self.level_manager.get_entities()
                )
                
                # Check if level is complete
                if collision_result.get('level_complete', False) and self.level_playable:
                    self.level_complete = True
                    self.state_manager.change_state(GameState.LEVEL_COMPLETE)
                    
            # Update level playable flag
            current_time = time.time()
            if not self.level_playable and current_time - self.level_start_time > self.level_playable_delay:
                self.level_playable = True
                self.ui_manager.add_toast("Level Ready! Hit the targets to complete the level.", 3.0, (0, 255, 0))
            
            # Update camera position based on ball position
            self._update_camera()
            
            # Reset power-up effects to default values
            self._reset_power_up_effects()
            
            # Apply active power-up effects
            for powerup in [p for p in self.level_manager.level_entities if hasattr(p, 'collected') and p.collected]:
                if hasattr(powerup, 'apply_effect'):
                    powerup.apply_effect(self)
            
            # Apply force to ball if force is being applied
            if self.applying_force and any(self.force_direction):
                self._apply_force()
        
        # Call our new boundary checking method
        self._enforce_ball_boundaries()
        
        # Update UI manager
        self.ui_manager.update(dt)
        
        # Update floating texts
        for text in self.floating_texts[:]:
            text.update(dt)
            if text.lifetime <= 0:
                self.floating_texts.remove(text)
        
        # Update UI manager if we haven't already
        if not hasattr(self, 'ui_manager_updated'):
            self.ui_manager.update(dt)
    
    def _apply_keyboard_controls(self, ball, dt):
        """Apply forces to the ball based on keyboard input."""
        # Calculate base force for this frame (force per second * dt)
        base_force = self.force_amount * dt
        
        # Initialize force components
        force_x = 0
        force_y = 0
        
        # Calculate force based on key states
        if self.key_states[pygame.K_UP]:
            force_y -= base_force
        if self.key_states[pygame.K_DOWN]:
            force_y += base_force
        if self.key_states[pygame.K_LEFT]:
            force_x -= base_force
        if self.key_states[pygame.K_RIGHT]:
            force_x += base_force
        
        # Apply braking if space is pressed
        if self.key_states[pygame.K_SPACE]:
            # Use the new brake method for better control and visual effect
            if hasattr(ball, 'brake'):
                ball.brake()
            else:
                # Fallback to old method if brake method not available
                ball.vel_x *= self.braking_force
                ball.vel_y *= self.braking_force
        
        # Apply force to the ball if any directional keys are pressed
        if force_x != 0 or force_y != 0:
            # Check if we have enough energy
            energy_cost = max(1, base_force * 0.01)  # Small energy cost per update
            
            if self.energy >= energy_cost:
                # Apply force
                ball.apply_force(force_x, force_y)
                
                # Reduce energy
                self.energy -= energy_cost
                self.energy_used += energy_cost
                
                # Count as a move if significant force is applied
                if base_force > 1.0:
                    self.moves_made += 1
                
                # Create thrust particles
                if self.particle_system:
                    # Calculate direction
                    magnitude = math.sqrt(force_x**2 + force_y**2)
                    if magnitude > 0:
                        direction = (-force_x / magnitude, -force_y / magnitude)
                        self.particle_system.create_particles(
                            ball.x, ball.y,
                            3,  # Fewer particles per frame for continuous effect
                            (100, 100, 255),  # Blue thrust
                            min_speed=50,
                            max_speed=150,
                            min_lifetime=0.1,
                            max_lifetime=0.3,
                            direction=direction,
                            spread=0.3
                        )
        else:
            # Not enough energy - show notification less frequently and with less aggressive styling
            # Track last time we showed the message
            current_time = time.time()
            if not hasattr(self, '_last_energy_warning_time'):
                self._last_energy_warning_time = 0
                
            # Only show the warning every 5 seconds at most
            if current_time - self._last_energy_warning_time > 5.0:
                # Use a more subtle color and longer duration
                soft_orange = (255, 180, 100)
                self.ui_manager.add_toast("Energy Low", 2.0, soft_orange)
                self._last_energy_warning_time = current_time
    
    def draw(self):
        """Draw the game based on the current state."""
        # Clear screen
        self.screen.fill(BACKGROUND_COLOR)
        
        # Get current state
        current_state = self.state_manager.current_state
        
        # Draw grid background (for all states)
        self._draw_grid()
        
        # Draw based on state
        if current_state == GameState.GAME:
            # Apply camera offset
            camera_offset = self.camera.position
                
            # Draw world boundary
            self._draw_world_boundary(camera_offset)
            
            # Draw entities
            for entity in self.level_manager.get_entities():
                if hasattr(entity, 'draw'):
                    entity.draw(self.screen, camera_offset)
            
            # Draw ball
            if self.level_manager.get_ball():
                self.level_manager.get_ball().draw(self.screen, camera_offset)
            
            # Draw particles
            if self.particle_system:
                self.particle_system.draw(self.screen)
            
            # Draw HUD
            self._draw_hud()
            
        elif current_state == GameState.LEVEL_COMPLETE:
            # Draw the completed level in the background
            
            # Apply camera offset
            camera_offset = self.camera.position
            
            # Draw world boundary
            self._draw_world_boundary(camera_offset)
            
            # Draw entities
            for entity in self.level_manager.get_entities():
                if hasattr(entity, 'draw'):
                    entity.draw(self.screen, camera_offset)
            
            # Draw ball
            if self.level_manager.get_ball():
                self.level_manager.get_ball().draw(self.screen, camera_offset)
            
            # Draw particles
            if self.particle_system:
                self.particle_system.draw(self.screen)
                
            # Draw overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            # Draw "Level Complete" text
            level_complete_text = self.large_font.render("Level Complete!", True, (255, 255, 255))
            level_complete_rect = level_complete_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
            self.screen.blit(level_complete_text, level_complete_rect)
            
            # Draw level number
            level_text = self.font.render(f"Level {self.level_manager.current_level}", True, (200, 200, 255))
            level_rect = level_text.get_rect(center=(WIDTH // 2, HEIGHT // 4 + 50))
            self.screen.blit(level_text, level_rect)
            
            # Calculate metrics for visual display
            time_efficiency = min(1.0, 0.6 * 60.0 / max(0.1, self.level_completion_time))
            energy_efficiency = self.energy / 100.0
            
            # Draw time performance (green bar for good, yellow for medium, red for poor)
            time_label = self.font.render("Time:", True, (255, 255, 255))
            self.screen.blit(time_label, (WIDTH // 2 - 150, HEIGHT // 4 + 80))
            
            time_text = self.font.render(f"{self.level_completion_time:.2f}s", True, (255, 255, 255))
            self.screen.blit(time_text, (WIDTH // 2 + 150 - time_text.get_width(), HEIGHT // 4 + 80))
            
            # Time efficiency bar
            bar_width = 200
            filled_width = int(bar_width * time_efficiency)
            pygame.draw.rect(self.screen, (50, 50, 50), (WIDTH // 2 - 100, HEIGHT // 4 + 105, bar_width, 15))
            
            # Color gradient based on efficiency
            if time_efficiency > 0.75:
                time_color = (0, 255, 0)  # Green for excellent
            elif time_efficiency > 0.5:
                time_color = (255, 255, 0)  # Yellow for good
            elif time_efficiency > 0.25:
                time_color = (255, 150, 0)  # Orange for average
            else:
                time_color = (255, 0, 0)  # Red for poor
                
            pygame.draw.rect(self.screen, time_color, (WIDTH // 2 - 100, HEIGHT // 4 + 105, filled_width, 15))
            
            # Draw energy performance
            energy_label = self.font.render("Energy:", True, (255, 255, 255))
            self.screen.blit(energy_label, (WIDTH // 2 - 150, HEIGHT // 4 + 130))
            
            energy_text = self.font.render(f"{int(self.energy)}/{100}", True, (255, 255, 255))
            self.screen.blit(energy_text, (WIDTH // 2 + 150 - energy_text.get_width(), HEIGHT // 4 + 130))
            
            # Energy efficiency bar
            filled_width = int(bar_width * energy_efficiency)
            pygame.draw.rect(self.screen, (50, 50, 50), (WIDTH // 2 - 100, HEIGHT // 4 + 155, bar_width, 15))
            
            # Color gradient based on efficiency
            if energy_efficiency > 0.75:
                energy_color = (0, 255, 0)  # Green for excellent
            elif energy_efficiency > 0.5:
                energy_color = (255, 255, 0)  # Yellow for good
            elif energy_efficiency > 0.25:
                energy_color = (255, 150, 0)  # Orange for average
            else:
                energy_color = (255, 0, 0)  # Red for poor
                
            pygame.draw.rect(self.screen, energy_color, (WIDTH // 2 - 100, HEIGHT // 4 + 155, filled_width, 15))
            
            # Calculate overall score (same formula as in level_manager.calculate_stars)
            overall_score = (time_efficiency * 0.5) + (energy_efficiency * 0.5)
            score_text = self.font.render(f"Overall Score: {int(overall_score * 100)}%", True, (255, 255, 255))
            self.screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 4 + 180))
            
            # Draw star requirements explanation
            req_text = self.small_font.render("Stars: 75%+ = ★★★, 50%+ = ★★, 25%+ = ★", True, (200, 200, 200))
            self.screen.blit(req_text, (WIDTH // 2 - req_text.get_width() // 2, HEIGHT // 4 + 205))
            
            # Draw stars with animation
            star_size = 40
            total_stars_width = star_size * 3 + 20  # 3 stars with 10px spacing between
            start_x = (WIDTH - total_stars_width) // 2
            star_y = HEIGHT // 4 + 240
            
            # Animation timing
            current_time = pygame.time.get_ticks() / 1000
            animation_duration = 0.3  # How long each star takes to appear
            delay_between_stars = 0.5  # Delay between stars appearing
            
            # Draw stars
            for i in range(3):
                # Determine if this star should be shown based on animation timing
                star_reveal_time = self.level_completion_time + (i * delay_between_stars)
                time_since_reveal = current_time - star_reveal_time
                
                # Skip stars that haven't reached their reveal time yet
                if time_since_reveal < 0:
                    continue
                
                # Determine animation progress (0.0 to 1.0)
                animation_progress = min(1.0, time_since_reveal / animation_duration)
                
                # Scale effect - stars grow from small to full size
                scaled_size = int(star_size * animation_progress)
                if scaled_size <= 0:
                    continue
                
                # Color with fade-in effect
                star_color = (255, 215, 0) if i < self.level_stars else (100, 100, 100)
                alpha = int(255 * animation_progress)
                current_color = (star_color[0], star_color[1], star_color[2], alpha)
                
                # Calculate star center
                star_center_x = start_x + i * (star_size + 10) + star_size // 2
                star_center_y = star_y + star_size // 2
                
                # Draw star with current size and alpha
                points = []
                for j in range(5):
                    # Calculate outer point of the star (with current size)
                    angle = math.pi * (0.5 - 2 * j / 5)
                    outer_radius = scaled_size // 2
                    points.append((
                        star_center_x + outer_radius * math.cos(angle),
                        star_center_y - outer_radius * math.sin(angle)
                    ))
                    
                    # Calculate inner point of the star (with current size)
                    angle = math.pi * (0.5 - (2 * j + 1) / 5)
                    inner_radius = scaled_size // 5
                    points.append((
                        star_center_x + inner_radius * math.cos(angle),
                        star_center_y - inner_radius * math.sin(angle)
                    ))
                
                # Draw filled star with current color
                if len(points) >= 3:  # Need at least 3 points to draw a polygon
                    # Create a temporary surface with alpha
                    star_surface = pygame.Surface((scaled_size, scaled_size), pygame.SRCALPHA)
                    
                    # Adjust points to draw on this surface
                    adjusted_points = [(p[0] - (star_center_x - scaled_size // 2),
                                      p[1] - (star_center_y - scaled_size // 2)) for p in points]
                    
                    # Draw the star on the temporary surface
                    pygame.draw.polygon(star_surface, current_color, adjusted_points)
                    
                    # Add a glow effect for earned stars
                    if i < self.level_stars and animation_progress == 1.0:
                        # Pulse effect based on time
                        glow_size = 5 + int(2 * math.sin(current_time * 4))
                        glow_surface = pygame.Surface((scaled_size + glow_size*2, scaled_size + glow_size*2), pygame.SRCALPHA)
                        
                        # Draw expanded star for glow
                        pygame.draw.polygon(glow_surface, (255, 255, 100, 50), 
                                          [(p[0] + glow_size, p[1] + glow_size) for p in adjusted_points])
                        
                        # Blit the glow first, then the star
                        self.screen.blit(glow_surface, (star_center_x - scaled_size // 2 - glow_size, 
                                                     star_center_y - scaled_size // 2 - glow_size))
                    
                    # Blit the star to the screen
                    self.screen.blit(star_surface, (star_center_x - scaled_size // 2, star_center_y - scaled_size // 2))
            
            # Draw UI elements
            self.ui_manager.draw(self.screen)
        
        elif current_state == GameState.MAIN_MENU:
            # Draw main menu background
            self._draw_main_menu_background()
            
            # Draw title
            if hasattr(self, 'logo') and self.logo:
                logo_rect = self.logo.get_rect(center=(WIDTH // 2, HEIGHT // 4))
                self.screen.blit(self.logo, logo_rect)
            else:
                # Fallback to text title
                title_text = self.large_font.render("Inertia Deluxe", True, (255, 255, 255))
                title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
                self.screen.blit(title_text, title_rect)
            
            # Draw UI elements
            self.ui_manager.draw(self.screen)
        
        elif current_state == GameState.LEVEL_SELECT:
            # Draw title
            title_text = self.large_font.render("Select Level", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(WIDTH // 2, 60))
            self.screen.blit(title_text, title_rect)
            
            # Draw UI elements (level buttons)
            self.ui_manager.draw(self.screen)
        
        elif current_state == GameState.SETTINGS:
            # Draw title
            title_text = self.large_font.render("Settings", True, (255, 255, 255))
            title_rect = title_text.get_rect(center=(WIDTH // 2, 60))
            self.screen.blit(title_text, title_rect)
            
            # Draw UI elements
            self.ui_manager.draw(self.screen)
            
            # Draw settings
            self._draw_settings()
        
        elif current_state == GameState.PAUSED:
            # Draw the game in the background
            camera_offset = self.camera.position
            
            # Draw world boundary
            self._draw_world_boundary(camera_offset)
            
            # Draw entities
            for entity in self.level_manager.get_entities():
                if hasattr(entity, 'draw'):
                    entity.draw(self.screen, camera_offset)
            
            # Draw ball
            if self.level_manager.get_ball():
                self.level_manager.get_ball().draw(self.screen, camera_offset)
            
            # Draw overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            # Draw "PAUSED" text
            paused_text = self.large_font.render("PAUSED", True, (255, 255, 255))
            paused_rect = paused_text.get_rect(center=(WIDTH // 2, HEIGHT // 4))
            self.screen.blit(paused_text, paused_rect)
            
            # Draw UI elements
            self.ui_manager.draw(self.screen)
        
        # Update the display
        pygame.display.flip()
    
    def _draw_main_menu_background(self):
        """Draw an animated background for the main menu."""
        # Fill the background with a dark color
        self.screen.fill((20, 30, 50))
        
        # Draw a grid of dots
        dot_spacing = 30
        dot_size = 2
        time_offset = pygame.time.get_ticks() / 1000
        
        for x in range(0, WIDTH, dot_spacing):
            for y in range(0, HEIGHT, dot_spacing):
                # Calculate dot color based on position and time
                color_value = int(128 + 127 * math.sin(x * 0.01 + y * 0.01 + time_offset))
                dot_color = (color_value // 4, color_value // 2, color_value)
                
                # Draw dot
                pygame.draw.circle(self.screen, dot_color, (x, y), dot_size)
    
    def _draw_settings(self):
        """Draw the settings screen."""
        self.alpha_surface.fill((0, 0, 0, 0))
        
        # Draw a grid in the background for the settings screen
        for x in range(0, WIDTH, 50):
            pygame.draw.line(self.alpha_surface, (30, 30, 50, 50), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, 50):
            pygame.draw.line(self.alpha_surface, (30, 30, 50, 50), (0, y), (WIDTH, y))
        
        # Draw heading
        font = pygame.font.SysFont(None, 60)
        text = font.render("SETTINGS", True, WHITE)
        self.alpha_surface.blit(text, (WIDTH // 2 - text.get_width() // 2, 50))
        
        self.screen.blit(self.alpha_surface, (0, 0))
        
        # Draw UI elements (settings controls)
        self.ui_manager.draw(self.screen)
    
    def _draw_hud(self):
        """Draw the heads-up display."""
        # Draw energy meter
        energy_x = 10
        energy_y = 10
        energy_width = 200
        energy_height = 20
        
        # Draw energy background
        pygame.draw.rect(self.screen, DARK_GRAY, (energy_x, energy_y, energy_width, energy_height))
        
        # Draw energy fill
        energy_fill = int(energy_width * (self.energy / self.max_energy))
        if self.energy > 70:
            energy_color = GREEN
        elif self.energy > 30:
            energy_color = YELLOW
        else:
            energy_color = RED
        pygame.draw.rect(self.screen, energy_color, (energy_x, energy_y, energy_fill, energy_height))
        
        # Draw energy text
        energy_text = f"Energy: {int(self.energy)}/{int(self.max_energy)}"
        energy_surface = self.font.render(energy_text, True, WHITE)
        self.screen.blit(energy_surface, (energy_x + 10, energy_y + energy_height + 5))
        
        # Draw level information
        level_text = f"Level: {self.level_manager.current_level}"
        level_surface = self.font.render(level_text, True, WHITE)
        self.screen.blit(level_surface, (WIDTH - level_surface.get_width() - 20, 10))
        
        # Draw controls help
        controls_text = "Controls: " + ("Mouse" if self.use_mouse_controls else "Keyboard")
        controls_surface = self.small_font.render(controls_text, True, WHITE)
        self.screen.blit(controls_surface, (WIDTH - controls_surface.get_width() - 20, 40))
        
        controls_help_text = "Press T to toggle controls"
        controls_help_surface = self.small_font.render(controls_help_text, True, WHITE)
        self.screen.blit(controls_help_surface, (WIDTH - controls_help_surface.get_width() - 20, 60))
        
        # Draw keyboard controls help if using keyboard
        if not self.use_mouse_controls:
            key_controls = [
                "Arrows: Move",
                "Space: Brake",
                "R: Restart level"
            ]
            
            for i, text in enumerate(key_controls):
                surface = self.small_font.render(text, True, WHITE)
                self.screen.blit(surface, (WIDTH - surface.get_width() - 20, 80 + i * 20))
        
        # Draw FPS if debug is enabled
        if self.show_debug:
            fps_text = f"FPS: {self.current_fps}"
            fps_surface = self.small_font.render(fps_text, True, WHITE)
            self.screen.blit(fps_surface, (10, energy_y + energy_height + 30))
            
            # Draw additional debug info
            ball = self.level_manager.get_ball()
            if ball:
                velocity = math.sqrt(ball.vel_x**2 + ball.vel_y**2)
                debug_text = f"Ball Velocity: {velocity:.2f}"
                debug_surface = self.small_font.render(debug_text, True, WHITE)
                self.screen.blit(debug_surface, (10, energy_y + energy_height + 50))
                
                pos_text = f"Ball Position: ({ball.x:.1f}, {ball.y:.1f})"
                pos_surface = self.small_font.render(pos_text, True, WHITE)
                self.screen.blit(pos_surface, (10, energy_y + energy_height + 70))
            
            # Draw entity count
            entities_text = f"Entities: {len(self.level_manager.get_entities())}"
            entities_surface = self.small_font.render(entities_text, True, WHITE)
            self.screen.blit(entities_surface, (10, energy_y + energy_height + 90))
        
        # Draw aiming line when aiming
        if self.aiming and self.aim_start_pos and self.aim_current_pos and self.use_mouse_controls:
            # Draw line from aim start to current position
            pygame.draw.line(
                self.screen,
                WHITE,
                self.aim_start_pos,
                self.aim_current_pos,
                2
            )
            
            # Calculate force magnitude
            force_x = (self.aim_start_pos[0] - self.aim_current_pos[0]) * 0.1
            force_y = (self.aim_start_pos[1] - self.aim_current_pos[1]) * 0.1
            force_magnitude = math.sqrt(force_x**2 + force_y**2)
            
            # Draw force indicator
            if force_magnitude > 0:
                force_text = f"Force: {force_magnitude:.1f}"
                force_surface = self.small_font.render(force_text, True, WHITE)
                self.screen.blit(force_surface, (self.aim_current_pos[0] + 10, self.aim_current_pos[1] + 10))
            
            # Draw direction indicator
            pygame.draw.circle(
                self.screen,
                RED,
                self.aim_start_pos,
                5
            )
    
    def add_floating_text(self, text, x, y, color=(255, 255, 255), size=20, lifetime=1.0, velocity=(0, -50)):
        """Add floating text at the given position."""
        if hasattr(self, 'floating_text'):
            self.floating_text.add_text(text, x, y, color=color, size=size, lifetime=lifetime, velocity=velocity)
        else:
            # Create a temporary text rendering
            font = pygame.font.SysFont(None, size)
            text_surface = font.render(text, True, color)
            # Calculate position adjusted for camera
            camera_pos = (0, 0) if not hasattr(self, 'camera') else self.camera.position
            adjusted_x = x - camera_pos[0]
            adjusted_y = y - camera_pos[1]
            # Draw directly on screen
            self.screen.blit(text_surface, (adjusted_x - text_surface.get_width() // 2, adjusted_y - text_surface.get_height() // 2))
    
    def _start_demo_level(self):
        """Start a demo level for testing."""
        self.level_manager.current_level = "demo"
        self._setup_level("demo")
        self.state_manager.change_state(GameState.GAME)
    
    def run(self):
        """Main game loop."""
        running = True
        
        # Initialize the first level
        self.level_manager.setup_level(1)
        
        # Start the game loop
        while running:
            # Calculate delta time
            self.dt = self.clock.tick(FPS) / 1000.0
            
            # Process events
            running = self._process_events()
            
            # Update game logic
            self.update(self.dt)
            
            # Draw the game
            self.draw()
            
            # Draw UI elements
            self.ui_manager.draw(self.screen)
            
            # Update the display
            pygame.display.flip()
        
        # Quit Pygame when the loop ends
        pygame.quit()
    
    def _process_events(self):
        """Process all game events."""
        # Get current state
        current_state = self.state_manager.current_state
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            # Quit event
            if event.type == pygame.QUIT:
                return False
                
            # Process UI events first
            ui_handled = self.ui_manager.handle_event(event)
            if ui_handled:
                continue
                
            # Key down events
            if event.type == pygame.KEYDOWN:
                # Global key events
                if event.key == pygame.K_ESCAPE:
                    if current_state == GameState.GAME:
                        self.state_manager.change_state(GameState.PAUSED)
                    elif current_state == GameState.PAUSED:
                        self.state_manager.change_state(GameState.GAME)
                    elif current_state in [GameState.LEVEL_SELECT, GameState.SETTINGS, GameState.CREDITS]:
                        self.state_manager.change_state(GameState.MAIN_MENU)
                    
                # Debug keys
                elif event.key == pygame.K_F3:
                    self.show_debug = not self.show_debug
                
                # Update key state
                if event.key in self.key_states:
                    self.key_states[event.key] = True
                
                # Game state specific keys
                if current_state == GameState.GAME:
                    self._handle_game_keydown(event)
            
            # Key up events
            elif event.type == pygame.KEYUP:
                # Update key state
                if event.key in self.key_states:
                    self.key_states[event.key] = False
                
            # Mouse events
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Game state specific mouse events
                if current_state == GameState.GAME and self.use_mouse_controls:
                    self._handle_game_mousedown(event, mouse_pos)
                
            # Mouse motion events
            elif event.type == pygame.MOUSEMOTION:
                # Game state specific mouse motion
                if current_state == GameState.GAME and self.use_mouse_controls:
                    self._handle_game_mousemotion(event, mouse_pos)
                    
            # Mouse button up events
            elif event.type == pygame.MOUSEBUTTONUP:
                # Game state specific mouse up events
                if current_state == GameState.GAME and self.use_mouse_controls:
                    self._handle_game_mouseup(event, mouse_pos)
        
        return True
        
    def _handle_game_keydown(self, event):
        """Handle key down events in the game state."""
        if event.key == pygame.K_r:
            # Reset level
            self.level_manager.setup_level(self.level_manager.current_level)
            self.level_start_time = time.time()
            self.level_playable = False
        
        # Toggle control scheme
        elif event.key == pygame.K_t:
            self.use_mouse_controls = not self.use_mouse_controls
            control_type = "Mouse Aiming" if self.use_mouse_controls else "Keyboard"
            self.ui_manager.add_toast(f"Controls: {control_type}", 2.0, BLUE)
    
    def _handle_game_mousedown(self, event, mouse_pos):
        """Handle mouse down events in the game state."""
        if event.button == 1:  # Left mouse button
            # Start aiming
            self.aiming = True
            self.aim_start_pos = mouse_pos
            
    def _handle_game_mousemotion(self, event, mouse_pos):
        """Handle mouse motion events in the game state."""
        if self.aiming:
            # Update aim direction
            self.aim_current_pos = mouse_pos
            
    def _handle_game_mouseup(self, event, mouse_pos):
        """Handle mouse up events in the game state."""
        if event.button == 1 and self.aiming:  # Left mouse button
            # Apply force to ball
            self.aim_end_pos = mouse_pos
            self.aiming = False
            
            # Get ball
            ball = self.level_manager.get_ball()
            if ball:
                # Calculate force direction and magnitude
                force_x = (self.aim_start_pos[0] - self.aim_end_pos[0]) * 0.1
                force_y = (self.aim_start_pos[1] - self.aim_end_pos[1]) * 0.1
                force_magnitude = math.sqrt(force_x**2 + force_y**2)
                
                # Check if we have enough energy
                energy_cost = force_magnitude * FORCE_COST
                if self.energy >= energy_cost:
                    # Apply force to ball
                    ball.apply_force(force_x, force_y)
                    
                    # Reduce energy
                    self.energy -= energy_cost
                    self.energy_used += energy_cost
                    
                    # Count as a move
                    self.moves_made += 1
                    
                    # Create force trail particles
                    if self.particle_system:
                        direction = normalize_vector(force_x, force_y)
                        if direction:  # Check if direction is not None
                            self.particle_system.create_particles(
                                ball.x, ball.y,
                                int(force_magnitude * 2),  # More particles for stronger forces
                                (200, 200, 255),
                                min_speed=force_magnitude * 5,
                                max_speed=force_magnitude * 10,
                                min_lifetime=0.2,
                                max_lifetime=0.5,
                                direction=(-direction[0], -direction[1]),  # Opposite of force direction
                                spread=0.5
                            )
                else:
                    # Not enough energy - show notification
                    self.ui_manager.add_toast("Not enough energy!", 1.5, RED)

    def _draw_background(self, camera_offset):
        """Draw the background grid and boundaries."""
        # Only print debug info if debugging is enabled
        if self.settings.get("debug_mode", False):
            print(f"Drawing background with camera offset: {camera_offset}")
            
            # Debug output for entity positions
            if self.state_manager.current_state == GameState.GAME:
                print(f"Ball position: {self.level_manager.ball.get_position() if self.level_manager.ball else 'No ball'}")
                for i, entity in enumerate(self.entities[:3]):  # Print first 3 entities to avoid clutter
                    if hasattr(entity, 'get_position'):
                        print(f"Entity {i} position: {entity.get_position()}")
                    elif hasattr(entity, 'rect'):
                        print(f"Entity {i} rect: {entity.rect}")
        
        # Fill the background with dark color
        self.screen.fill((20, 20, 30))
        
        # Draw grid
        grid_size = 50
        
        # Calculate visible grid area based on camera position
        start_x = int(camera_offset[0] // grid_size) * grid_size
        start_y = int(camera_offset[1] // grid_size) * grid_size
        
        # Draw vertical grid lines
        for x in range(start_x, start_x + self.screen_width + grid_size, grid_size):
            adjusted_x = x - camera_offset[0]
            pygame.draw.line(self.screen, (40, 40, 50), (adjusted_x, 0), (adjusted_x, self.screen_height), 1)
        
        # Draw horizontal grid lines
        for y in range(start_y, start_y + self.screen_height + grid_size, grid_size):
            adjusted_y = y - camera_offset[1]
            pygame.draw.line(self.screen, (40, 40, 50), (0, adjusted_y), (self.screen_width, adjusted_y), 1)

    def _load_high_score(self):
        """Load high score from file."""
        try:
            if os.path.exists("data/high_score.json"):
                with open("data/high_score.json", "r") as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
        except Exception as e:
            print(f"Error loading high score: {e}")
        
        return 0

    def _draw_grid(self):
        """Draw a grid on the background."""
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(
                self.screen, 
                GRID_COLOR, 
                (x, 0), 
                (x, HEIGHT), 
                1
            )
            
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.line(
                self.screen, 
                GRID_COLOR, 
                (0, y), 
                (WIDTH, y), 
                1
            )
            
    def _draw_world_boundary(self, camera_offset):
        """Draw the world boundary."""
        # Draw world boundary
        world_rect = pygame.Rect(
            -camera_offset[0],
            -camera_offset[1],
            self.world_width,
            self.world_height
        )
        
        # Draw boundary with a thick line
        pygame.draw.rect(
            self.screen,
            BOUNDARY_COLOR,
            world_rect,
            BOUNDARY_THICKNESS
        )

    def _enforce_ball_boundaries(self):
        """Keep the ball within the game world and camera view."""
        if not self.level_manager.get_ball():
            return
            
        ball = self.level_manager.get_ball()
        
        # Define world boundaries with some padding
        padding = ball.radius * 2
        min_x = padding
        min_y = padding
        max_x = self.world_width - padding
        max_y = self.world_height - padding
        
        # Check if ball is outside boundaries
        if ball.x < min_x or ball.x > max_x or ball.y < min_y or ball.y > max_y:
            # If ball is outside valid area, reset to a safe position
            if ball.x < min_x: ball.x = min_x
            if ball.x > max_x: ball.x = max_x
            if ball.y < min_y: ball.y = min_y
            if ball.y > max_y: ball.y = max_y
            
            # Stop ball movement
            ball.vel_x = 0
            ball.vel_y = 0
            
            # Update camera
            self.camera.set_target_position((ball.x, ball.y))
            
            # Show toast notification
            if hasattr(self, 'ui_manager'):
                self.ui_manager.add_toast("Ball out of bounds!", 2.0, (255, 100, 100))

    def reset_for_state_change(self, new_state):
        """Reset game objects when changing state."""
        # Clear any floating text
        if hasattr(self, 'floating_texts'):
            self.floating_texts = []
        
        # Reset screen shake
        if hasattr(self, 'screen_shake_amount'):
            self.screen_shake_amount = 0
        
        # Clear cached render surfaces
        if hasattr(self, 'alpha_surface'):
            self.alpha_surface.fill((0, 0, 0, 0))
        
        # Reset camera for certain state changes
        if new_state == GameState.GAME:
            if hasattr(self, 'camera'):
                self.camera.reset()
            
            # If we have a ball, update camera to focus on it
            if self.level_manager and self.level_manager.get_ball():
                ball_pos = self.level_manager.get_ball().get_position()
                if hasattr(self, 'camera'):
                    self.camera.set_target_position((ball_pos[0] - WIDTH/2, ball_pos[1] - HEIGHT/2))
        
        # Reset game-specific properties based on state
        if new_state == GameState.GAME:
            # Reset game state for gameplay
            self.level_playable = False
            self.level_complete = False
            self.level_start_time = time.time()
            
        elif new_state == GameState.MAIN_MENU:
            # Reset for main menu
            pass
            
        elif new_state == GameState.LEVEL_COMPLETE:
            # Specific handling for level complete
            pass
            
        print(f"Game reset for state change to {new_state}")