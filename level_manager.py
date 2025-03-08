import os
import json
import random
import pygame
import time
from typing import Dict, List, Any, Optional
from state_manager import GameState
from entities.wall import Wall
from entities.target import Target
from entities.ball import Ball
from entities.powerup import PowerUp
from entities.surface import Surface
from entities.teleporter import Teleporter
from entities.bounce_pad import BouncePad
from entities.gravity_well import GravityWell

class LevelManager:
    def __init__(self):
        """Initialize the level manager without game reference."""
        self.game = None  # Will be set later via set_game
        self.current_level = None
        self.level_entities = []  # All level entities
        self.ball = None  # Reference to the current ball
        self.max_level = 30  # Maximum level available
        self.is_demo = False
        self.completed_levels = set()
        self.levels_data = None  # Will be loaded after game reference is set
    
    def set_game(self, game):
        """Set the game reference after initialization."""
        self.game = game
        self.levels_data = self.load_levels_data()
    
    def add_entity(self, entity):
        """Add entity to the level and set its game reference."""
        self.level_entities.append(entity)
        if hasattr(entity, 'game') and self.game is not None:
            entity.game = self.game
        return entity
    
    def get_entities(self):
        """Get all entities in the level."""
        return self.level_entities
    
    def get_ball(self):
        """Get the player's ball."""
        return self.ball
    
    def clear_entities(self):
        """Clear all entities in the level."""
        self.level_entities.clear()
        self.ball = None
    
    def load_levels_data(self):
        """Load levels data from file."""
        default_data = {
            "unlocked": 1,
            "stars": {},
            "max_level": self.max_level
        }
        
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Try to load levels data
            if os.path.exists("data/levels.json"):
                with open("data/levels.json", "r") as f:
                    levels_data = json.load(f)
                    print("Loaded levels data!")
                    return levels_data
            else:
                # Create default levels data
                with open("data/levels.json", "w") as f:
                    json.dump(default_data, f, indent=4)
                print("Created default levels data!")
                return default_data
                
        except Exception as e:
            print(f"Error loading levels data: {e}")
            return default_data  # Return default data in case of error
    
    def save_levels_data(self):
        """Save levels data to file."""
        try:
            with open("data/levels.json", "w") as f:
                json.dump(self.levels_data, f, indent=4)
            print("Saved levels data!")
        except Exception as e:
            print(f"Error saving levels data: {e}")
            
    def save_level_completion(self, level_num):
        """Save level completion data."""
        if not isinstance(level_num, int):
            print(f"Invalid level number: {level_num}")
            return
            
        # Update unlocked levels
        if "unlocked" in self.levels_data:
            if level_num + 1 > self.levels_data["unlocked"]:
                self.levels_data["unlocked"] = min(level_num + 1, self.max_level)
        
        # Save to file
        self.save_levels_data()
    
    def setup_level(self, level_number):
        """Set up entities for a level."""
        from levels.level_generator import generate_level
        
        self.current_level = level_number
        # Clear all entities
        self.clear_entities()
        
        # Make sure game's entity list is also cleared
        if self.game:
            self.game.entities = []
        
        # Demo level handling
        if level_number == "demo":
            self._setup_demo_level()
            return
        
        try:
            # Generate or load level data
            level_data = generate_level(level_number)
            
            # Create a ball
            if "start_pos" in level_data:
                self.ball = Ball(level_data["start_pos"][0], level_data["start_pos"][1], 15)
                self.ball.game = self.game  # Set game reference
                self.add_entity(self.ball)
                
                # Update game's ball reference
                if self.game:
                    self.game.ball = self.ball
                
            # Add walls
            if "walls" in level_data:
                for wall_data in level_data["walls"]:
                    if isinstance(wall_data, Wall):
                        wall = wall_data
                    else:
                        wall = Wall(wall_data["x"], wall_data["y"], wall_data["width"], wall_data["height"])
                    self.add_entity(wall)
                    # Keep adding to game.entities for now for backward compatibility
                    if self.game:
                        self.game.entities.append(wall)
            
            # Add targets
            if "targets" in level_data:
                for target_data in level_data["targets"]:
                    if isinstance(target_data, Target):
                        target = target_data
                    else:
                        target = Target(
                            target_data["x"], target_data["y"], 
                            target_data.get("radius", 20),
                            target_data.get("points", 100),
                            target_data.get("required", True)
                        )
                    target.game = self.game  # Set game reference
                    target.hit = False  # Ensure it starts as not hit
                    self.add_entity(target)
                    # Keep adding to game.entities for now for backward compatibility
                    if self.game:
                        self.game.entities.append(target)
            
            # Add surfaces
            if "surfaces" in level_data:
                for surface_data in level_data["surfaces"]:
                    if isinstance(surface_data, Surface):
                        surface = surface_data
                    else:
                        surface = Surface(
                            surface_data["x"], surface_data["y"], 
                            surface_data["width"], surface_data["height"],
                            surface_data.get("friction", 0.95),
                            surface_data.get("color", None)
                        )
                    self.game.entities.append(surface)
                    self.level_entities.append(surface)
            
            # Add power-ups
            if "powerups" in level_data:
                for powerup_data in level_data["powerups"]:
                    if isinstance(powerup_data, PowerUp):
                        powerup = powerup_data
                    else:
                        powerup = PowerUp(
                            powerup_data["x"], powerup_data["y"],
                            powerup_data.get("type", "energy")
                        )
                    self.game.entities.append(powerup)
                    self.level_entities.append(powerup)
            
            # Add teleporters
            if "teleporters" in level_data:
                for teleporter_data in level_data["teleporters"]:
                    if isinstance(teleporter_data, Teleporter):
                        teleporter = teleporter_data
                    else:
                        teleporter = Teleporter(
                            teleporter_data["x"], teleporter_data["y"],
                            teleporter_data.get("target_x", 0),
                            teleporter_data.get("target_y", 0)
                        )
                    self.game.entities.append(teleporter)
                    self.level_entities.append(teleporter)
            
            # Add gravity wells
            if "gravity_wells" in level_data:
                for well_data in level_data["gravity_wells"]:
                    if isinstance(well_data, GravityWell):
                        well = well_data
                    else:
                        well = GravityWell(
                            well_data["x"], well_data["y"],
                            well_data.get("radius", 100),
                            well_data.get("strength", 0.5),
                            well_data.get("repel", False)
                        )
                    self.game.entities.append(well)
                    self.level_entities.append(well)
            
            # Add bounce pads
            if "bounce_pads" in level_data:
                for pad_data in level_data["bounce_pads"]:
                    if isinstance(pad_data, BouncePad):
                        pad = pad_data
                    else:
                        pad = BouncePad(
                            pad_data["x"], pad_data["y"],
                            pad_data.get("width", 60),
                            pad_data.get("height", 20),
                            pad_data.get("angle", 0),
                            pad_data.get("strength", 2.0)
                        )
                    self.game.entities.append(pad)
                    self.level_entities.append(pad)
            
            # Set level-specific settings
            if "energy_drain_rate" in level_data:
                self.game.energy_drain_rate = level_data["energy_drain_rate"]
            else:
                self.game.energy_drain_rate = 1.0  # Default value
            
            # Initialize level timer
            self.game.level_start_time = pygame.time.get_ticks()
            
            # Reset game state
            self.game.energy = 100.0  # Full energy
            self.game.level_complete = False
            self.game.level_playable = False  # Reset level playable flag
            
            # Ensure level has required targets
            self._ensure_level_has_required_targets()
            
            # Add a level start visual effect
            if self.game and hasattr(self.game, 'particle_system') and self.ball:
                # Create a more impressive burst of particles around the ball
                self.game.particle_system.add_spiral_burst(
                    self.ball.x, self.ball.y,
                    color=(50, 200, 255),  # Light blue
                    spiral_count=4,        # More spirals
                    particles_per_spiral=20,
                    radius=120,
                    lifetime=1.5
                )
                
                # Highlight important elements with particles
                # Add bursts to each target to make them more noticeable
                for entity in self.level_entities:
                    if isinstance(entity, Target) and entity.required:
                        self.game.particle_system.create_particles(
                            entity.x, entity.y,
                            15,  # Number of particles
                            (255, 100, 100),  # Red for targets
                            min_speed=30,
                            max_speed=80,
                            min_lifetime=0.5,
                            max_lifetime=1.0,
                            size_range=(2, 4),
                            glow=True
                        )
                
                # Display level start toast with more information
                if hasattr(self.game, 'ui_manager'):
                    # Main level start message
                    self.game.ui_manager.add_toast(f"Level {level_number}: Get Ready!", 2.5, (0, 200, 0))
                    
                    # Add a tip specific to the level after a short delay
                    level_tips = {
                        1: "Tutorial: Use arrow keys to move the ball and hit targets",
                        2: "Tip: Watch your energy - braking costs energy!",
                        3: "Tip: Hit all the red targets to complete the level",
                        4: "Tip: Green gravity wells attract, red ones repel",
                        5: "Tip: Teleporters can help you reach distant areas"
                    }
                    
                    if level_number in level_tips and hasattr(self.game, 'ui_manager'):
                        # Schedule tip to appear after main message
                        delay = 1.0
                        tip = level_tips[level_number]
                        
                        # We need to delay this tip - let's use a simple timer approach
                        def show_delayed_tip():
                            self.game.ui_manager.add_toast(tip, 3.0, (200, 200, 0))
                        
                        # Schedule tip using threading if available
                        import threading
                        threading.Timer(delay, show_delayed_tip).start()
            
            print(f"Level {level_number} setup with {len(self.game.entities)} entities")
        except Exception as e:
            print(f"Error setting up level {level_number}: {e}")
            # Fall back to demo level
            self._setup_demo_level()
    
    def _setup_demo_level(self):
        """Create a simple demo level with basic elements."""
        # Clear existing entities
        self.game.entities = []
        self.level_entities = []
        self.ball = None
        
        # Create a ball
        self.ball = Ball(300, 300, 15)
        self.ball.game = self.game  # Set game reference
        
        # Create walls (border)
        walls = [
            # Top wall
            Wall(100, 100, 600, 20),
            # Bottom wall
            Wall(100, 500, 600, 20),
            # Left wall
            Wall(100, 100, 20, 420),
            # Right wall
            Wall(700, 100, 20, 420),
            # Middle obstacle
            Wall(300, 300, 200, 20),
        ]
        
        # Add walls to entities
        for wall in walls:
            self.game.entities.append(wall)
            self.level_entities.append(wall)
        
        # Create a target
        target = Target(600, 400, 20, 100, True)
        target.game = self.game  # Set game reference
        target.hit = False  # Explicitly set to False to ensure it's not completed yet
        print(f"Demo target created at (600, 400) with hit={target.hit}, required={target.required}")
        self.game.entities.append(target)
        self.level_entities.append(target)
        
        # Create an ice surface
        surface = Surface(120, 120, 560, 380, 0.98, (100, 100, 200))
        self.game.entities.append(surface)
        self.level_entities.append(surface)
        
        # Create a power-up
        powerup = PowerUp(200, 200, "energy")
        self.game.entities.append(powerup)
        self.level_entities.append(powerup)
        
        print(f"Demo level created with {len(self.game.entities)} entities")
        
        # Set up camera
        self.game.camera_offset = [0, 0]
        
        # Reset level start time
        self.game.level_start_time = pygame.time.get_ticks()
        
        # Reset game state
        self.game.energy = 100.0  # Full energy
        self.game.level_complete = False
        self.game.level_playable = False  # Reset level playable flag
        
        # Set game to demo mode
        self.game.is_demo = True
        
        # Ensure level has required targets
        self._ensure_level_has_required_targets()
    
    def calculate_stars(self, level, energy, completion_time):
        """
        Calculate stars earned for a level based on completion time and energy efficiency.
        
        Args:
            level: Level number or identifier
            energy: Remaining energy at level completion
            completion_time: Time taken to complete the level in seconds
            
        Returns:
            Number of stars earned (0-3)
        """
        # Convert level to string for dictionary key
        level_key = str(level)
        
        # Get level-specific parameters
        level_data = {}
        if isinstance(level, int) or level_key.isdigit():
            from levels.level_generator import generate_level
            try:
                level_data = generate_level(int(level_key))
            except Exception:
                # Use defaults if level data not available
                pass
        
        # Get level-specific parameters or use defaults
        max_time = level_data.get("time_limit", 60.0)  # Default 60 seconds max time
        par_time = level_data.get("par_time", max_time * 0.6)  # Default par time is 60% of max
        max_energy = 100.0  # Maximum possible energy
        starting_energy = max_energy  # Assume starting with max energy
        
        # Energy efficiency (percentage of energy conserved)
        energy_efficiency = energy / starting_energy
        
        # Time efficiency (percentage of par time used, capped at 100%)
        time_efficiency = min(1.0, par_time / max(0.1, completion_time))  # Avoid division by zero
        
        # Combined score (weighted 50/50 between time and energy)
        combined_score = (energy_efficiency * 0.5) + (time_efficiency * 0.5)
        
        # Star thresholds (adjusted to be more intuitive)
        threshold_3_stars = 0.75  # 75% combined efficiency for 3 stars
        threshold_2_stars = 0.50  # 50% combined efficiency for 2 stars
        threshold_1_star = 0.25   # 25% combined efficiency for 1 star
        
        # Determine stars based on combined score
        if combined_score >= threshold_3_stars:
            stars = 3
        elif combined_score >= threshold_2_stars:
            stars = 2
        elif combined_score >= threshold_1_star:
            stars = 1
        else:
            stars = 0
            
        # Debug info (can be removed in production)
        print(f"Level {level_key} - Time: {completion_time:.1f}s, Energy: {energy:.0f}, " +
              f"Score: {combined_score:.2f}, Stars: {stars}")
            
        # Initialize stars dictionary if it doesn't exist
        if "stars" not in self.levels_data:
            self.levels_data["stars"] = {}
            
        current_stars = self.levels_data["stars"].get(level_key, 0)
        
        # Only update if new stars are higher
        if stars > current_stars:
            self.levels_data["stars"][level_key] = stars
            self.save_levels_data()
            
        # Unlock next level if needed
        if (isinstance(level, int) or level_key.isdigit()) and stars > 0:
            next_level = int(level_key) + 1
            current_unlocked = self.levels_data.get("unlocked", 1)
            if next_level > current_unlocked:
                self.levels_data["unlocked"] = next_level
                self.save_levels_data()
            
        return stars
    
    def is_level_complete(self):
        """Check if all required targets in the level are hit."""
        if not self.level_entities:
            # Only print in debug mode
            if self.game.settings.get("debug_mode", False):
                print("No level entities found, level cannot be complete")
            return False
        
        # Find all required targets (hit or not)
        all_required_targets = []
        # Find all required targets that are not hit
        unhit_required_targets = []
        
        for entity in self.level_entities:
            is_target = isinstance(entity, Target)
            if is_target:
                has_required = hasattr(entity, 'required')
                is_required = entity.required if has_required else False
                has_hit = hasattr(entity, 'hit')
                is_hit = entity.hit if has_hit else False
                
                # Only print in debug mode
                if self.game.settings.get("debug_mode", False):
                    print(f"Target at {entity.x}, {entity.y}: " + 
                          f"is_target={is_target}, " +
                          f"has_required={has_required}, is_required={is_required}, " +
                          f"has_hit={has_hit}, is_hit={is_hit}")
                
                if is_target and has_required and is_required:
                    all_required_targets.append(entity)
                    if has_hit and not is_hit:
                        unhit_required_targets.append(entity)
        
        # If there are no required targets at all, the level is not complete
        if not all_required_targets:
            # Only print in debug mode
            if self.game.settings.get("debug_mode", False):
                print("No required targets found at all, level is not complete")
            return False
            
        # Level is complete if all required targets exist and have been hit
        level_complete = len(unhit_required_targets) == 0
        
        # Simple status message - always show this one
        if level_complete:
            print(f"LEVEL COMPLETE! All {len(all_required_targets)} targets hit.")
        else:
            print(f"Level progress: {len(all_required_targets) - len(unhit_required_targets)}/{len(all_required_targets)} targets hit")
            
        return level_complete
    
    def restart_level(self):
        """Restart the current level."""
        return self.setup_level(self.current_level)
    
    def next_level(self):
        """Advance to the next level."""
        if isinstance(self.current_level, int):
            next_level = self.current_level + 1
            if next_level > self.max_level:
                # Reset to level 1 if we reached the max
                next_level = 1
            
            # Store next level number for clarity
            next_level_num = next_level
            
            # Clear current level
            self.clear_entities()
            
            # Reset ball reference
            self.ball = None
            
            # Reset level stats in game if available
            if self.game:
                self.game.energy = self.game.max_energy
                self.game.energy_used = 0
                self.game.moves_made = 0
                self.game.level_complete = False
                
                # Reset camera if available
                if hasattr(self.game, 'camera'):
                    self.game.camera.reset()
            
            print(f"Transitioning to level {next_level_num}")
            
            # Change game state to GAME (this will trigger reset_for_state_change)
            if self.game and hasattr(self.game, 'state_manager'):
                self.game.state_manager.change_state(GameState.GAME)
            
            # Now set up the next level
            success = self.setup_level(next_level_num)
            
            # Set level start time
            if self.game:
                self.game.level_start_time = time.time()
                self.game.level_playable = False
                
                # Show level started toast
                if hasattr(self.game, 'ui_manager'):
                    self.game.ui_manager.add_toast(f"Level {next_level_num}", 2.0, (0, 200, 255))
            
            print(f"Advanced to level {next_level_num} (success: {success})")
            return success
        else:
            # Default to level 1 if current level is not a number
            print("Current level not a number, defaulting to level 1")
            return self.setup_level(1)
    
    def _ensure_level_has_required_targets(self):
        """Verify that the level has at least one required target. Add one if needed."""
        # Check if we have any required targets
        has_required_target = False
        for entity in self.level_entities:
            if isinstance(entity, Target) and hasattr(entity, 'required') and entity.required:
                has_required_target = True
                break
        
        # If no required targets, add one
        if not has_required_target:
            print("Warning: Level has no required targets. Adding one to make level completable.")
            
            # Find center of level or use fallback position
            center_x, center_y = 400, 300  # Default center
            if self.ball:
                # Place target further away from ball
                center_x = self.ball.x + 300
                center_y = self.ball.y + 200
            
            # Create and add a required target
            target = Target(center_x, center_y, 25, 100, True)
            target.game = self.game
            target.hit = False
            self.game.entities.append(target)
            self.level_entities.append(target)
            print(f"Added required target at position ({center_x}, {center_y})")
            
        return has_required_target 