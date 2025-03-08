import pygame
import math
import random
import time
from utils.sound import play_sound

class EnhancedPowerUp:
    """An enhanced power-up with more visual feedback and effects"""
    
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
        
        # Animation properties
        self.pulse_timer = 0
        self.rotation = 0
        self.particles = []
    
    def update(self, dt):
        """Update power-up animation"""
        if not self.active:
            return
            
        # Update pulse animation
        self.pulse_timer += dt
        
        # Update rotation
        self.rotation += 90 * dt  # 90 degrees per second
        if self.rotation >= 360:
            self.rotation -= 360
            
        # Occasionally add ambient particles
        if random.random() < 0.1:
            self.particles.append({
                "x": self.x + random.uniform(-self.radius, self.radius),
                "y": self.y + random.uniform(-self.radius, self.radius),
                "vel_x": random.uniform(-1, 1),
                "vel_y": random.uniform(-1, 1),
                "size": random.uniform(1, 3),
                "lifetime": random.uniform(0.3, 0.8),
                "age": 0
            })
            
        # Update particles
        particles_to_keep = []
        for p in self.particles:
            p["age"] += dt
            if p["age"] < p["lifetime"]:
                p["x"] += p["vel_x"]
                p["y"] += p["vel_y"]
                p["size"] *= 0.95
                particles_to_keep.append(p)
        self.particles = particles_to_keep
    
    def draw(self, surface, camera_offset=(0, 0)):
        """Draw the power-up with enhanced visuals"""
        if not self.active:
            return
            
        # Calculate adjusted position
        adjusted_x = self.x - camera_offset[0]
        adjusted_y = self.y - camera_offset[1]
            
        # Draw the power-up ambient particles
        for p in self.particles:
            alpha = int(255 * (1 - p["age"] / p["lifetime"]))
            pygame.draw.circle(
                surface,
                (*self.color, alpha),
                (int(p["x"] - camera_offset[0]), int(p["y"] - camera_offset[1])),
                int(p["size"])
            )
            
        # Draw pulsing effect
        pulse = math.sin(self.pulse_timer * 3) * 0.2 + 0.8
        current_radius = int(self.radius * pulse)
        
        # Draw glow
        glow_surface = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        glow_color = (*self.color, 100)  # Semi-transparent
        pygame.draw.circle(glow_surface, glow_color, (self.radius * 2, self.radius * 2), self.radius * 2)
        surface.blit(glow_surface, (adjusted_x - self.radius * 2, adjusted_y - self.radius * 2), special_flags=pygame.BLEND_ADD)
        
        # Draw main circle
        pygame.draw.circle(surface, self.color, (int(adjusted_x), int(adjusted_y)), current_radius)
        
        # Draw inner circle (rotating)
        inner_radius = current_radius * 0.7
        angle_rad = math.radians(self.rotation)
        inner_x = adjusted_x + math.cos(angle_rad) * (current_radius * 0.3)
        inner_y = adjusted_y + math.sin(angle_rad) * (current_radius * 0.3)
        pygame.draw.circle(surface, (255, 255, 255), (int(inner_x), int(inner_y)), int(inner_radius))
        
        # Draw icon
        font = pygame.font.SysFont(None, 20)
        text = font.render(self.icon, True, (0, 0, 0))
        text_rect = text.get_rect(center=(adjusted_x, adjusted_y))
        surface.blit(text, text_rect)
    
    def check_collision(self, ball):
        """Check if the ball collides with this power-up"""
        if not self.active:
            return False
            
        distance = math.sqrt((ball.x - self.x)**2 + (ball.y - self.y)**2)
        if distance < ball.radius + self.radius:
            self.collect()
            return True
        return False
    
    def collect(self):
        """Handle collection of the power-up"""
        self.active = False
        self.collected = True
        self.effect_start_time = time.time()
        
        # Add collection particle effect
        if self.game and hasattr(self.game, 'particle_system'):
            self.game.particle_system.add_explosion(
                self.x, self.y,
                self.color,
                count=30,
                speed_range=(2, 5),
                size_range=(3, 6),
                lifetime_range=(0.5, 1.0),
                glow=True
            )
        
        # Play sound
        play_sound("powerup", 1.0)
    
    def apply_effect(self, game):
        """Apply the power-up effect to the game"""
        if not self.collected:
            return False
            
        current_time = time.time()
        effect_time_remaining = self.duration - (current_time - self.effect_start_time)
        
        # If effect has expired, remove it
        if effect_time_remaining <= 0:
            self.collected = False
            return False
            
        # Apply effect based on type
        if self.type == "energy":
            # Energy refill (one-time effect)
            from utils.constants import ENERGY_MAX
            game.energy = min(ENERGY_MAX, game.energy + ENERGY_MAX * 0.5)
            self.collected = False  # One-time effect
            return True
            
        elif self.type == "speed":
            # Set speed multiplier instead of stacking velocity
            game.ball.speed_multiplier = 1.5
            return True
            
        elif self.type == "shield":
            # Shield (handled in collision detection)
            game.ball.has_shield = True
            return True
            
        elif self.type == "gravity":
            # Gravity field
            game.gravity_field_active = True
            game.gravity_field_radius = 150
            game.gravity_field_strength = 0.15  # Positive for pull
            return True
            
        elif self.type == "time":
            # Time slow - handled in game loop
            game.time_slow_factor = 0.5
            return True
            
        elif self.type == "magnetic":
            # Target attraction - pull all targets toward ball
            for target in game.targets:
                if target.active:
                    dx = game.ball.x - target.x
                    dy = game.ball.y - target.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        force = 0.5 / dist
                        target.x += dx * force
                        target.y += dy * force
            return True
            
        return False
    
    def is_effect_active(self):
        """Check if the power-up effect is still active"""
        if not self.collected:
            return False
            
        current_time = time.time()
        return (current_time - self.effect_start_time) < self.duration
        
    def get_remaining_time(self):
        """Get the remaining time for the effect in seconds"""
        if not self.collected:
            return 0
            
        current_time = time.time()
        return max(0, self.duration - (current_time - self.effect_start_time))
    
    def get_position(self):
        """Return the current position of the power-up."""
        return (self.x, self.y)
    
    def set_position(self, position):
        """Set the position of the power-up."""
        self.x, self.y = position 