import pygame
import math
import random
import time
from utils.sound import play_sound

class PowerUp:
    """A power-up with visual feedback and effects"""
    
    TYPES = {
        "energy": {
            "color": (255, 215, 0),  # Gold
            "description": "Restores energy",
            "duration": 0.1,  # Instant effect
            "icon": "E"
        },
        "speed": {
            "color": (0, 191, 255),   # Deep sky blue
            "description": "Increases speed",
            "duration": 5.0,
            "icon": "S"
        },
        "shield": {
            "color": (220, 220, 220), # Silver
            "description": "Protects from one collision",
            "duration": 8.0,
            "icon": "SH"
        },
        "gravity": {
            "color": (148, 0, 211),   # Dark violet
            "description": "Creates a gravity field",
            "duration": 6.0,
            "icon": "G"
        },
        "time": {
            "color": (255, 165, 0),   # Orange
            "description": "Slows down time",
            "duration": 5.0,
            "icon": "T"
        },
        "magnetic": {
            "color": (255, 0, 128),   # Magenta
            "description": "Attracts targets",
            "duration": 7.0,
            "icon": "M"
        }
    }
    
    def __init__(self, x, y, power_type="energy", game=None):
        self.x = x
        self.y = y
        self.radius = 15
        self.type = power_type
        self.active = True
        self.collected = False
        self.effect_start_time = 0
        self.game = game
        
        # Get properties from type
        type_info = self.TYPES.get(power_type, self.TYPES["energy"])
        self.color = type_info["color"]
        self.description = type_info["description"]
        self.duration = type_info["duration"]
        self.icon = type_info["icon"]
        
        # Visual properties
        self.pulse_timer = 0
        self.glow_radius = self.radius * 1.5
        self.glow_color = (*self.color, 100)  # Semi-transparent glow
        self.rotation = 0
        self.collected_time = 0
        self.collection_duration = 0.5
        
    def update(self, dt):
        """Update power-up animation"""
        if self.collected:
            # Update collection animation
            if time.time() - self.collected_time < self.collection_duration:
                # Still showing collection animation
                pass
            else:
                # Collection animation complete, can be removed
                self.active = False
            return
            
        # Update pulse animation
        self.pulse_timer += dt
        
        # Rotate gradually
        self.rotation += dt * 30  # 30 degrees per second
        if self.rotation >= 360:
            self.rotation -= 360
            
        # Check if effect is still active
        if self.effect_start_time > 0 and not self.is_effect_active():
            # Effect has ended, reset any game properties
            self._reset_effect()
            
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the power-up with enhanced visuals"""
        if not self.active:
            return
            
        # Calculate position with camera offset
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
            
        # Calculate pulse effect
        pulse = math.sin(self.pulse_timer * 3) * 0.1 + 0.9
        current_radius = int(self.radius * pulse)
        
        if self.collected:
            # Draw collection animation (expanding circle that fades out)
            elapsed = time.time() - self.collected_time
            progress = elapsed / self.collection_duration
            alpha = int(255 * (1 - progress))
            expand_radius = int(self.radius * (1 + progress * 3))
            
            if alpha > 0:
                glow_surface = pygame.Surface((expand_radius * 2, expand_radius * 2), pygame.SRCALPHA)
                glow_color = (*self.color, alpha)
                pygame.draw.circle(glow_surface, glow_color, 
                                  (expand_radius, expand_radius), expand_radius)
                surface.blit(glow_surface, (adjusted_x - expand_radius, adjusted_y - expand_radius), 
                            special_flags=pygame.BLEND_ADD)
            return
        
        # Draw glow
        glow_surface = pygame.Surface((self.glow_radius * 4, self.glow_radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, self.glow_color, 
                          (self.glow_radius * 2, self.glow_radius * 2), self.glow_radius * 2)
        surface.blit(glow_surface, (adjusted_x - self.glow_radius * 2, adjusted_y - self.glow_radius * 2), 
                    special_flags=pygame.BLEND_ADD)
        
        # Draw main power-up
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), current_radius)
        
        # Draw icon
        if self.game and hasattr(self.game, 'small_font'):
            icon_text = self.game.small_font.render(self.icon, True, (0, 0, 0))
            # Rotate the text
            rotated_text = pygame.transform.rotate(icon_text, self.rotation)
            text_rect = rotated_text.get_rect(center=(adjusted_x, adjusted_y))
            surface.blit(rotated_text, text_rect)
            
    def check_collision(self, ball):
        """Check if the ball is colliding with this power-up"""
        if not self.active or self.collected:
            return False
            
        # Calculate distance between centers
        dx = ball.x - self.x
        dy = ball.y - self.y
        distance_squared = dx**2 + dy**2
        
        # Check if collision occurred
        collision_distance = ball.radius + self.radius
        if distance_squared < collision_distance**2:
            self.collect()
            return True
        
        return False
    
    def collect(self):
        """Handle collection of the power-up"""
        if self.collected:
            return
            
        self.collected = True
        self.collected_time = time.time()
        
        # Apply effect immediately
        if self.game:
            self.apply_effect(self.game)
            
        # Create particle effect if game reference exists
        if self.game and hasattr(self.game, 'particle_system'):
            # Create particles at power-up position
            self.game.particle_system.create_particles(
                self.x, self.y,
                15,  # Number of particles
                self.color,  # Use power-up color
                min_speed=50,
                max_speed=150,
                min_lifetime=0.3,
                max_lifetime=1.0
            )
    
    def apply_effect(self, game):
        """Apply the power-up effect to the game"""
        # Check if game is valid and has required attributes
        if not game:
            print("Warning: Invalid game reference in PowerUp.apply_effect")
            return
            
        if not hasattr(game, 'level_manager'):
            print("Warning: Game missing level_manager in PowerUp.apply_effect")
            return
            
        # Check if level_manager has a ball
        ball = None
        if game.level_manager:
            ball = game.level_manager.get_ball()
            
        # Set effect start time
        self.effect_start_time = time.time()
        
        # Apply effect based on type
        if self.type == "energy":
            # Restore energy
            if hasattr(game, 'energy'):
                game.energy = min(game.energy + 50, game.max_energy)
                
            # Show floating text
            if hasattr(game, 'add_floating_text'):
                game.add_floating_text("+50 Energy", self.x, self.y, self.color)
                
        elif self.type == "speed":
            # Increase ball speed
            if ball:
                ball.speed_multiplier = 1.5
                
            # Show floating text
            if hasattr(game, 'add_floating_text'):
                game.add_floating_text("Speed Boost!", self.x, self.y, self.color)
                
        elif self.type == "shield":
            # Add shield to the ball
            if ball and hasattr(ball, 'has_shield'):
                ball.has_shield = True
                
            # Show floating text
            if hasattr(game, 'add_floating_text'):
                game.add_floating_text("Shield Active!", self.x, self.y, self.color)
                
        elif self.type == "gravity":
            # Enable gravity field
            if hasattr(game, 'gravity_field_active'):
                game.gravity_field_active = True
                
            # Show floating text
            if hasattr(game, 'add_floating_text'):
                game.add_floating_text("Gravity Field!", self.x, self.y, self.color)
                
        elif self.type == "time":
            # Slow down time
            if hasattr(game, 'time_slow_factor'):
                game.time_slow_factor = 0.5
                
            # Show floating text
            if hasattr(game, 'add_floating_text'):
                game.add_floating_text("Time Slow!", self.x, self.y, self.color)
                
        elif self.type == "magnetic":
            # Enable magnetic attraction
            if hasattr(game, 'magnetic_attraction'):
                game.magnetic_attraction = True
                
            # Show floating text
            if hasattr(game, 'add_floating_text'):
                game.add_floating_text("Target Magnet!", self.x, self.y, self.color)
    
    def is_effect_active(self):
        """Check if the power-up effect is still active"""
        if self.effect_start_time == 0:
            return False
            
        return time.time() - self.effect_start_time < self.duration
    
    def get_remaining_time(self):
        """Get the remaining time for the power-up effect"""
        if not self.is_effect_active():
            return 0
            
        return self.duration - (time.time() - self.effect_start_time)
    
    def get_position(self):
        """Return the current position of the power-up."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the power-up."""
        self.x, self.y = position
    
    def _reset_effect(self):
        """Reset any game properties changed by this power-up"""
        if not self.game:
            return
            
        if self.type == "speed" and self.game.level_manager.get_ball():
            self.game.level_manager.get_ball().speed_multiplier = 1.0
            
        elif self.type == "shield" and self.game.level_manager.get_ball():
            if hasattr(self.game.level_manager.get_ball(), 'has_shield'):
                self.game.level_manager.get_ball().has_shield = False
                
        elif self.type == "gravity":
            if hasattr(self.game, 'gravity_field_active'):
                self.game.gravity_field_active = False
                
        elif self.type == "time":
            if hasattr(self.game, 'time_slow_factor'):
                self.game.time_slow_factor = 1.0
                
        elif self.type == "magnetic":
            if hasattr(self.game, 'magnetic_attraction'):
                self.game.magnetic_attraction = False 