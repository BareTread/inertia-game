import os
import json
import random
import pygame
from typing import Dict, List, Any, Optional
from entities.wall import Wall
from entities.enhanced_wall import EnhancedWall
from entities.target import Target
from entities.enhanced_target import EnhancedTarget
from entities.enhanced_ball import EnhancedBall
from entities.enhanced_powerup import EnhancedPowerUp
from entities.powerup import PowerUp
from entities.surface import Surface
from entities.teleporter import Teleporter
from entities.bounce_pad import BouncePad
from entities.gravity_well import GravityWell

class LevelManager:
    def __init__(self, game):
        """Initialize the level manager."""
        self.game = game
        self.current_level = None
        self.level_entities = []  # All level entities
        self.ball = None  # Reference to the current ball
        self.max_level = 30  # Maximum level available
        self.is_demo = False
        self.completed_levels = set()
        self.levels_data = self.load_levels_data()
    
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
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Save levels data
            with open("data/levels.json", "w") as f:
                json.dump(self.levels_data, f, indent=4)
                
        except Exception as e:
            print(f"Error saving levels data: {e}")
    
    def setup_level(self, level_number):
        """Set up entities for a level."""
        from levels.level_generator import generate_level
        
        self.current_level = level_number
        # Clear game entities and reset ball
        self.game.entities = []
        self.level_entities = []
        self.ball = None
        
        # Demo level handling
        if level_number == "demo":
            self._setup_demo_level()
            return
        
        try:
            # Generate or load level data
            level_data = generate_level(level_number)
            
            # Create a ball
            if "start_pos" in level_data:
                self.ball = EnhancedBall(level_data["start_pos"][0], level_data["start_pos"][1], 15)
                self.ball.game = self.game  # Set game reference
                
            # Add walls
            if "walls" in level_data:
                for wall_data in level_data["walls"]:
                    if isinstance(wall_data, Wall) or isinstance(wall_data, EnhancedWall):
                        wall = wall_data
                    else:
                        wall = EnhancedWall(wall_data["x"], wall_data["y"], wall_data["width"], wall_data["height"])
                    self.game.entities.append(wall)
                    self.level_entities.append(wall)
            
            # Add targets
            if "targets" in level_data:
                for target_data in level_data["targets"]:
                    if isinstance(target_data, Target) or isinstance(target_data, EnhancedTarget):
                        target = target_data
                    else:
                        target = EnhancedTarget(
                            target_data["x"], target_data["y"], 
                            target_data.get("radius", 20),
                            target_data.get("points", 100),
                            target_data.get("required", True)
                        )
                    target.game = self.game  # Set game reference
                    target.hit = False  # Ensure it starts as not hit
                    self.game.entities.append(target)
                    self.level_entities.append(target)
            
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
                    if isinstance(powerup_data, PowerUp) or isinstance(powerup_data, EnhancedPowerUp):
                        powerup = powerup_data
                    else:
                        powerup = EnhancedPowerUp(
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
        self.ball = EnhancedBall(300, 300, 15)
        self.ball.game = self.game  # Set game reference
        
        # Create walls (border)
        walls = [
            # Top wall
            EnhancedWall(100, 100, 600, 20),
            # Bottom wall
            EnhancedWall(100, 500, 600, 20),
            # Left wall
            EnhancedWall(100, 100, 20, 420),
            # Right wall
            EnhancedWall(700, 100, 20, 420),
            # Middle obstacle
            EnhancedWall(300, 300, 200, 20),
        ]
        
        # Add walls to entities
        for wall in walls:
            self.game.entities.append(wall)
            self.level_entities.append(wall)
        
        # Create a target
        target = EnhancedTarget(600, 400, 20, 100, True)
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
        powerup = EnhancedPowerUp(200, 200, "energy")
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
        Calculate stars earned for a level based on completion time and energy.
        
        Args:
            level: Level number or identifier
            energy: Remaining energy
            completion_time: Time taken to complete the level in seconds
            
        Returns:
            Number of stars earned (0-3)
        """
        # Convert level to string for dictionary key
        level_key = str(level)
        
        # Default values
        max_time = 60.0  # Default max time in seconds
        
        # Default star thresholds
        time_threshold_3 = max_time * 0.5  # 50% of max time for 3 stars
        time_threshold_2 = max_time * 0.7  # 70% of max time for 2 stars
        time_threshold_1 = max_time        # 100% of max time for 1 star
        
        # Ensure completion_time is a float
        try:
            completion_time = float(completion_time)
        except (ValueError, TypeError):
            completion_time = float('inf')  # If conversion fails, no stars
        
        # Calculate stars based on time
        if completion_time <= time_threshold_3:
            stars = 3
        elif completion_time <= time_threshold_2:
            stars = 2
        elif completion_time <= time_threshold_1:
            stars = 1
        else:
            stars = 0
            
        # Initialize stars dictionary if it doesn't exist
        if "stars" not in self.levels_data:
            self.levels_data["stars"] = {}
            
        current_stars = self.levels_data["stars"].get(level_key, 0)
        
        # Only update if new stars are higher
        if stars > current_stars:
            self.levels_data["stars"][level_key] = stars
            self.save_levels_data()
            
        # Unlock next level if needed
        if isinstance(level, int) and stars > 0:
            next_level = level + 1
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
            is_target = isinstance(entity, Target) or isinstance(entity, EnhancedTarget)
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
            return self.setup_level(next_level)
        else:
            # Default to level 1 if current level is not a number
            return self.setup_level(1) 
    
    def _ensure_level_has_required_targets(self):
        """Verify that the level has at least one required target. Add one if needed."""
        # Check if we have any required targets
        has_required_target = False
        for entity in self.level_entities:
            if (isinstance(entity, Target) or isinstance(entity, EnhancedTarget)) and hasattr(entity, 'required') and entity.required:
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
            target = EnhancedTarget(center_x, center_y, 25, 100, True)
            target.game = self.game
            target.hit = False
            self.game.entities.append(target)
            self.level_entities.append(target)
            print(f"Added required target at position ({center_x}, {center_y})")
            
        return has_required_target 